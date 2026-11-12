"""Transactional simulation. Every projection is recoverable from committed events."""
import sqlite3
from contextlib import contextmanager
from decimal import ROUND_CEILING, ROUND_FLOOR

from .data import D, DAY, NANO, dump, load

BASE = D(".008")
STRESS = D(".01")
ORDER_CAP = D(".025")
EXPOSURE = D(".10")


def step(value, increment, rounding=ROUND_FLOOR):
    return (value / increment).to_integral_value(rounding=rounding) * increment


class Ledger:
    def __init__(self, path, *, readonly=False):
        location = path.resolve().as_uri()+"?mode=ro&immutable=1" if readonly else path
        self.db = sqlite3.connect(location, isolation_level=None, uri=readonly)
        self.db.execute("PRAGMA foreign_keys=ON")
        if not readonly:
            self.db.execute("PRAGMA journal_mode=PERSIST")
            self.db.execute("PRAGMA synchronous=FULL")
            self.db.executescript("""
            CREATE TABLE IF NOT EXISTS frames (idx INTEGER PRIMARY KEY, digest TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS events (
                seq INTEGER PRIMARY KEY, id TEXT UNIQUE NOT NULL, frame INTEGER NOT NULL
                    REFERENCES frames(idx), kind TEXT NOT NULL, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS account (id INTEGER PRIMARY KEY CHECK(id=1), state TEXT NOT NULL);
        """)
        state = self.db.execute("SELECT state FROM account WHERE id=1").fetchone()
        self.state = load(state[0]) if state else {
            "cash": "10000", "btc": "0", "cost": "0", "realized": "0", "nav": "10000",
            "high": "10000", "day_nav": "10000", "day": None, "mark_ns": None,
            "daily": None, "drawdown": False, "manual": False, "orders": {},
            "target": None, "exit": None, "last_exit": None, "attempt": 0,
        }
        self.frame = None

    @contextmanager
    def transaction(self, idx, digest):
        self.db.execute("BEGIN IMMEDIATE")
        before = dump(self.state)
        try:
            exists = self.db.execute("SELECT digest FROM frames WHERE idx=?", (idx,)).fetchone()
            if exists and exists[0] != digest:
                raise ValueError("frame identity changed")
            if not exists:
                last, = self.db.execute("SELECT coalesce(max(idx),0) FROM frames").fetchone()
                if idx != last + 1:
                    raise ValueError("noncontiguous ledger frame")
                self.db.execute("INSERT INTO frames VALUES (?,?)", (idx, digest))
            self.frame = idx
            yield not exists
            if not exists and before != dump(self.state):
                self.db.execute("INSERT OR REPLACE INTO account VALUES (1,?)", (dump(self.state),))
                self.event(f"state/{idx}", "state", self.state)
            self.db.commit()
        except BaseException:
            self.db.rollback()
            self.state = load(before)
            raise
        finally:
            self.frame = None

    def event(self, identity, kind, payload):
        cursor = self.db.execute("INSERT OR IGNORE INTO events(id,frame,kind,payload) VALUES(?,?,?,?)",
                                 (identity, self.frame, kind, dump(payload)))
        if not cursor.rowcount:
            old = self.db.execute("SELECT kind,payload FROM events WHERE id=?", (identity,)).fetchone()
            if old != (kind, dump(payload)):
                raise ValueError("event identity changed")
        return bool(cursor.rowcount)

    def sequence(self):
        return self.db.execute("SELECT id,frame,kind,payload FROM events ORDER BY seq")

    def reconcile(self):
        integrity, = self.db.execute("PRAGMA quick_check").fetchone()
        last = self.db.execute("SELECT payload FROM events WHERE kind='state' ORDER BY seq DESC LIMIT 1").fetchone()
        return integrity == "ok" and (last is None or dump(self.state) == last[0])

    def close(self):
        self.db.close()


class Engine:
    def __init__(self, ledger, stress=False):
        self.ledger = ledger
        self.fee = STRESS if stress else BASE
        self.latency = 1_000_000_000 if stress else 250_000_000
        self.slip = D(".001") if stress else D(0)

    @property
    def s(self):
        return self.ledger.state

    def val(self, key):
        return D(self.s[key])

    def log(self, suffix, kind, **payload):
        return self.ledger.event(suffix, kind, payload)

    def cancel(self, order_id, reason):
        order = self.s["orders"].pop(order_id)
        self.log(f"{order_id}/end", "cancel", reason=reason, qty=order["qty"])

    def interrupt(self, reason, buys_only=False):
        for oid, order in list(self.s["orders"].items()):
            if not buys_only or order["side"] == "buy":
                self.cancel(oid, reason)

    def roll_day(self, ns):
        day = ns // (DAY*NANO)
        if self.s["day"] is None or day > self.s["day"]:
            mark = self.s["mark_ns"]
            if mark is None or mark < day*DAY*NANO:
                self.s.update(day=day, day_nav=self.s["nav"])
                self.log(f"day/{day}", "day", nav=self.s["nav"], source_mark_ns=mark,
                         age_ns=None if mark is None else day*DAY*NANO-mark)

    def mark(self, book, utc):
        self.roll_day(utc)
        nav = self.val("cash") + self.val("btc")*book.bid*(1-self.fee)
        high = max(nav, self.val("high"))
        self.s.update(nav=nav, high=high, mark_ns=utc)
        if nav <= self.val("day_nav") * D(".99") and self.s["daily"] is None:
            self.s["daily"] = self.s["day"]
            self.log(f"risk/daily/{self.ledger.frame}", "lock", nav=nav, lock="daily")
        if nav <= high * D(".96") and not self.s["drawdown"]:
            self.s["drawdown"] = True
            self.log(f"risk/drawdown/{self.ledger.frame}", "lock", nav=nav, lock="drawdown")
        locked = self.locked()
        if locked or self.val("btc")*book.bid > nav*EXPOSURE:
            self.interrupt("risk", buys_only=True)
            goal = D(0) if locked else EXPOSURE
            if self.s["exit"] is None or D(self.s["exit"]["target"]) > goal:
                self.exit_target(f"risk/{self.ledger.frame}", goal)

    def locked(self):
        return self.s["daily"] is not None or self.s["drawdown"] or self.s["manual"]

    def acknowledge(self, lock, note, ns):
        if not note.strip():
            raise ValueError("operator reason required")
        if lock == "daily":
            self.roll_day(ns)
            if self.s["daily"] is None or self.s["day"] <= self.s["daily"]:
                raise ValueError("daily lock requires the next UTC day")
            self.s["daily"] = None
        elif lock in ("drawdown", "manual") and self.s[lock]:
            self.s[lock] = False
        else:
            raise ValueError("lock is not active")
        self.s["target"] = None
        self.log(f"ack/{self.ledger.frame}", "ack", lock=lock, note=note)

    def exit_target(self, identity, target):
        self.s["exit"] = {"id": identity, "target": target}
        self.s["attempt"] = 0
        self.log(f"{identity}/target", "exit_target", target=target)

    def order(self, identity, target, book, meta, frame, *, exit_only=False):
        if not meta:
            return
        nav, btc = self.val("nav"), self.val("btc")
        open_orders = self.s["orders"].values()
        open_buys = sum(D(o["qty"]) for o in open_orders if o["side"] == "buy")
        open_sells = sum(D(o["qty"]) for o in open_orders if o["side"] == "sell")
        delta = nav*target/book.bid - btc - open_buys + open_sells
        side = "buy" if delta > 0 else "sell"
        tick = meta["price_increment"]
        limit = (step(book.ask*D("1.002"), tick) if side == "buy"
                 else step(book.bid*D(".998"), tick, ROUND_CEILING))
        if side == "buy":
            if exit_only or self.locked() or meta["status"] != "online" or not limit:
                return
            delta = min(delta, self.buy_capacity(limit, book))
        else:
            delta = min(-delta, btc-open_sells)
        qty = step(max(D(0), delta), meta["qty_increment"])
        if qty < meta["qty_min"] or qty*limit < meta["cost_min"]:
            if exit_only and D(0) < btc < meta["qty_min"]:
                self.log(f"{identity}/dust", "DUST", btc=btc)
                self.s["exit"] = None
            return
        oid = f"{identity}/order"
        order = {"side": side, "limit": limit, "qty": qty, "epoch": book.epoch,
                 "trigger": book.index, "created": frame["mono"], "index": frame["idx"],
                 "reserve": qty*limit*(1+self.fee) if side == "buy" else qty}
        self.log(oid, "reserve", **order)
        self.s["orders"][oid] = order

    def buy_capacity(self, limit, book, exclude=None):
        buys = [o for oid, o in self.s["orders"].items() if oid != exclude and o["side"] == "buy"]
        free = self.val("cash") - sum(D(o["reserve"]) for o in buys)
        nav = self.val("nav")
        exposure = self.val("btc")*max(limit, book.bid) + sum(D(o["qty"])*D(o["limit"]) for o in buys)
        return min((nav*EXPOSURE-exposure)/limit, min(free, nav*ORDER_CAP)/(limit*(1+self.fee)))

    def decide(self, key, target, reason, book, meta, frame):
        event = {"status": "SKIP" if reason else "DECIDED", "reason": reason, "target": target}
        if not self.ledger.event(key, "decision", event) or reason or target is None:
            return
        if self.locked() or (self.s["exit"] and D(self.s["exit"]["target"]) < target):
            return
        self.log(f"{key}/intent", "intent", target=target, bid=book.bid, ask=book.ask)
        self.s["target"] = target
        if self.val("btc")*book.bid > self.val("nav")*target:
            self.interrupt("reduce target", buys_only=True)
            self.exit_target(key, target)
            self.retry_exit(book, meta, frame)
        else:
            self.order(f"{key}/intent", target, book, meta, frame)

    def retry_exit(self, book, meta, frame):
        target = self.s["exit"]
        if not target or self.s["orders"]:
            return
        if self.val("btc")*book.bid <= self.val("nav")*D(target["target"]):
            self.s["exit"] = None
            return
        last = self.s["last_exit"]
        if last and (frame["mono"] - last[0] < NANO or book.index == last[1]):
            return
        self.s["attempt"] += 1
        self.s["last_exit"] = [frame["mono"], book.index]
        self.order(f"{target['id']}/exit/{self.s['attempt']}", D(target["target"]),
                   book, meta, frame, exit_only=True)

    def expire(self, mono):
        for oid, order in list(self.s["orders"].items()):
            if mono >= order["created"] + 5*NANO:
                self.cancel(oid, "TTL")

    def on_book(self, book, meta, frame):
        self.expire(frame["mono"])
        self.mark(book, frame["utc"])
        # Reductions have priority, then decision receive order and identifier.
        orders = sorted(self.s["orders"].items(),
                        key=lambda pair: (pair[1]["side"] == "buy", pair[1]["index"], pair[0]))
        for oid, order in orders:
            if oid not in self.s["orders"]:
                continue
            if book.epoch != order["epoch"]:
                self.cancel(oid, "epoch")
                continue
            if book.index <= order["trigger"] or frame["mono"] - order["created"] < self.latency:
                continue
            if meta is None:
                self.cancel(oid, "unknown metadata")
                continue
            if order["side"] == "buy" and (self.locked() or meta["status"] != "online" or
                    D(order["qty"]) > self.buy_capacity(D(order["limit"]), book, exclude=oid)):
                self.cancel(oid, "pre-fill risk")
                continue
            if order["side"] == "sell" and self.s["exit"]:
                self.s["last_exit"] = [frame["mono"],book.index]
            self.match(oid, order, book, meta, frame)
            self.mark(book, frame["utc"])
        self.retry_exit(book, meta, frame)

    def match(self, oid, order, book, meta, frame):
        buy = order["side"] == "buy"
        side = "asks" if buy else "bids"
        qty, limit = D(order["qty"]), D(order["limit"])
        remaining, gross = qty, D(0)
        fills = []
        for price, volume in book.sides[side].items():
            execution = price
            if self.slip:
                execution = step(price*(1+self.slip if buy else 1-self.slip),
                                 meta["price_increment"], ROUND_CEILING if buy else ROUND_FLOOR)
            if (buy and execution > limit) or (not buy and execution < limit):
                break
            size = step(min(remaining, volume-book.used[side][price]), meta["qty_increment"])
            if size:
                fills.append((price, execution, size))
                gross += execution*size
                remaining -= size
            if not remaining:
                break
        total = qty - remaining
        if total < meta["qty_min"] or gross < meta["cost_min"]:
            self.cancel(oid, "IOC below executable minimum")
            return
        for level, price, size in fills:
            amount, fee = price*size, price*size*self.fee
            fill_id = f"{oid}/fill/{level:f}"
            if not self.log(fill_id, "fill", order=oid, side=order["side"], frame_id=book.index,
                            qty=size, price=price, gross=amount, fee=fee, fee_currency="USD",
                            level=str(level), level_revision=book.revisions[side][level], epoch=book.epoch,
                            fee_model="stress-v1" if self.slip else "kraken-spot-tier1-2026-11-07",
                            created_mono=order["created"], filled_utc=frame["utc"]):
                continue
            book.used[side][level] += size
            cash, btc, cost = (self.val(k) for k in ("cash", "btc", "cost"))
            if buy:
                self.s.update(cash=cash-amount-fee, btc=btc+size, cost=cost+amount+fee)
            else:
                removed = cost if size == btc else cost*(size/btc)
                self.s.update(cash=cash+amount-fee, btc=btc-size, cost=cost-removed,
                              realized=self.val("realized")+amount-fee-removed)
            if self.val("cash") < 0 or self.val("btc") < 0:
                raise ValueError("negative balance")
        del self.s["orders"][oid]
        self.log(f"{oid}/end", "ioc", filled=total, cancelled=remaining, gross=gross,
                 fee=gross*self.fee)
