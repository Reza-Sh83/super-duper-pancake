"""Decimal market data, checksum, and UTC bar versioning."""
import hashlib
import json
import zlib
from datetime import datetime, timezone
from decimal import Decimal, getcontext

getcontext().prec = 34
D = Decimal
SYMBOL = "BTC/USD"
NANO = 10**9
DAY = 86400
MAX_FRAME = 1024**2


def stamp(ns):
    seconds, fraction = divmod(ns, NANO)
    return datetime.fromtimestamp(seconds, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S") + f".{fraction:09d}Z"


def parse_time(value):
    dt = datetime.fromisoformat(value)
    if dt.utcoffset() is None:
        raise ValueError("timestamp lacks offset")
    dt = dt.astimezone(timezone.utc)
    return int(dt.replace(microsecond=0).timestamp()) * NANO + dt.microsecond * 1000


def number(value, zero=False):
    if isinstance(value, (bool, float)):
        raise ValueError("expected exact decimal")
    value = D(value)
    if not value.is_finite() or value < 0 or (not zero and not value):
        raise ValueError("invalid decimal")
    return value


def decimal_text(value):
    if not value:
        return "0"
    result = format(value, "f")
    return result.rstrip("0").rstrip(".") if "." in result else result


def dump(value):
    return json.dumps(value, default=decimal_text, sort_keys=True, separators=(",", ":"), allow_nan=False)


def load(value):
    def invalid(token):
        raise ValueError(f"nonfinite JSON token {token}")
    return json.loads(value, parse_float=D, parse_constant=invalid)


def sha(value):
    return hashlib.sha256(value).hexdigest()


def crc(sides):
    def digits(value):
        return format(value, "f").replace(".", "").lstrip("0")
    text = "".join(digits(price) + digits(qty)
                   for side in ("asks", "bids") for price, qty in sides[side].items())
    return zlib.crc32(text.encode("ascii"))


class Book:
    def __init__(self):
        self.epoch = 0
        self.invalidate("DISCONNECTED")

    def invalidate(self, state="STALE"):
        self.state = state
        self.sides = {"asks": {}, "bids": {}}
        self.used = {"asks": {}, "bids": {}}
        self.revisions = {"asks": {}, "bids": {}}
        self.event_ns = None
        self.index = None

    def connect(self, epoch):
        if epoch <= self.epoch:
            raise ValueError("epoch must increase")
        self.epoch = epoch
        self.invalidate("SYNCING")

    def apply(self, epoch, index, message):
        if epoch != self.epoch:
            return False
        try:
            kind = message["type"]
            if ((kind == "snapshot" and self.state != "SYNCING") or
                    (kind == "update" and self.state != "READY") or
                    kind not in ("snapshot", "update")):
                raise ValueError("unexpected book message")
            if self.index is not None and index <= self.index:
                raise ValueError("receive order")
            item, = message["data"]
            if item["symbol"] != SYMBOL:
                raise ValueError("wrong instrument")
            event_ns = parse_time(item["timestamp"])
            if self.event_ns is not None and event_ns < self.event_ns:
                raise ValueError("regressing book time")
            for side in self.sides:
                levels = self.sides[side]
                used = self.used[side]
                revisions = self.revisions[side]
                for ordinal, level in enumerate(item[side]):
                    price, qty = number(level["price"]), number(level["qty"], zero=True)
                    if qty:
                        if levels.get(price) != qty:
                            revisions[price] = (index, ordinal)
                        # Retain the wire's scale for CRC even when the number compares equal.
                        levels.pop(price, None)
                        levels[price] = qty
                        used[price] = min(used.get(price, D(0)), qty)
                    else:
                        levels.pop(price, None)
                        used.pop(price, None)
                        revisions.pop(price, None)
                best = sorted(levels, reverse=side == "bids")[:10]
                self.sides[side] = {price: levels[price] for price in best}
                self.used[side] = {price: used[price] for price in best}
                self.revisions[side] = {price: revisions[price] for price in best}
            if (not all(self.sides.values()) or self.bid >= self.ask or
                    type(item["checksum"]) is not int or crc(self.sides) != item["checksum"]):
                raise ValueError("invalid depth or checksum")
        except (ValueError, KeyError, TypeError, ArithmeticError):
            self.invalidate()
            raise
        self.event_ns, self.index, self.state = event_ns, index, "READY"
        return True

    def age(self, ns):
        return ns - self.event_ns if self.event_ns is not None else None

    def fresh(self, ns):
        age = self.age(ns)
        return self.state == "READY" and age is not None and -500_000_000 <= age <= 2*NANO

    @property
    def bid(self):
        return next(iter(self.sides["bids"]))

    @property
    def ask(self):
        return next(iter(self.sides["asks"]))


def instrument(message):
    for pair in message["data"].get("pairs", []):
        if pair.get("symbol") == SYMBOL:
            result = {key: number(pair[key]) for key in
                      ("price_increment", "qty_increment", "qty_min", "cost_min")}
            status = pair["status"]
            if not isinstance(status, str) or result["qty_min"] % result["qty_increment"]:
                raise ValueError("inconsistent instrument metadata")
            return result | {"status": status}
    return None


class Bars:
    def __init__(self):
        self.latest = {}
        self.history = []

    def accept(self, payload, interval, received_ns, pair):
        if payload["error"]:
            raise ValueError("Kraken OHLC error")
        rows = payload["result"][pair]
        if not rows:
            raise ValueError("missing OHLC rows")
        seconds = interval * 60
        closed = {}
        for row in rows[:-1]:
            start, o, h, lo, c, vwap, volume, count = row
            if (type(start) is not int or start % seconds or start in closed or
                    (start + seconds) * NANO > received_ns):
                raise ValueError("invalid closed bar timestamp")
            o, h, lo, c, vwap = map(number, (o, h, lo, c, vwap))
            volume = number(volume, zero=True)
            if not (lo <= min(o, c) <= max(o, c) <= h and lo <= vwap <= h and
                    type(count) is int and count >= 0):
                raise ValueError("invalid OHLC values")
            closed[start] = [o, h, lo, c, vwap, volume, count]
        versions = []
        for start, row in sorted(closed.items()):
            key = (interval, start + seconds)
            digest = sha(dump(row).encode())
            prev = self.latest.get(key)
            if prev is None or prev["sha256"] != digest:
                version = {"interval_min": interval, "end": key[1], "row": row,
                           "available_at": stamp(received_ns), "sha256": digest,
                           "previous_sha256": prev["sha256"] if prev else None}
                self.latest[key] = version
                versions.append(version)
                self.history.append(version)
        return versions

    def closes(self, interval, end, count):
        keys = [(interval, end - interval*60*i) for i in reversed(range(count))]
        if all(key in self.latest for key in keys):
            return [self.latest[key]["row"][3] for key in keys]


def in_window(end, received_ns):
    return (end + 2)*NANO <= received_ns <= (end + 60)*NANO
