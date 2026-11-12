"""Write-ahead capture and a shared live/replay event loop."""
import base64
import hashlib
import os
import platform
import shutil
import sqlite3
import time
from pathlib import Path

from .data import Bars, Book, D, MAX_FRAME, NANO, SYMBOL, dump, in_window, instrument, load, sha, stamp
from .engine import Engine, Ledger

PACKAGE = Path(__file__).resolve().parent
MIB = 1024**2
CAP = 5*1024*MIB


def digest_file(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    with temp.open("w", encoding="utf-8") as stream:
        stream.write(dump(value) + "\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, path)


def versions():
    from importlib.metadata import PackageNotFoundError, version
    try:
        ws = version("websockets")
    except PackageNotFoundError:
        ws = None
    return {"python": platform.python_version(), "sqlite": sqlite3.sqlite_version, "websockets": ws}


def code_hashes():
    return {p.name: digest_file(p) for p in sorted(PACKAGE.iterdir())
            if p.suffix in (".py", ".lock", ".json")}


def report(path, run_id, checks, started, hashes, **extra):
    write_json(path, {"schema_version": 1, "run_id": run_id, "checks": checks,
                      "input_hashes": hashes, "started_utc": stamp(started),
                      "finished_utc": stamp(time.time_ns()), "versions": versions(),
                      "code_hashes": code_hashes(), **extra})
    return 0 if all(check["status"] == "PASS" for check in checks) else 1


def accepted_reports(paths):
    approved, hashes = set(), {}
    build = code_hashes()
    for path in paths:
        if not path.is_file():
            continue
        receipt = load(path.read_bytes())
        if receipt.get("code_hashes") == build:
            approved |= {c["id"] for c in receipt["checks"] if c["status"] == "PASS"}
            hashes[str(path)] = digest_file(path)
    return approved, hashes


def check(identity, status, expected, observed):
    return {"id": identity, "status": status, "expected": expected, "observed": observed,
            **({"reason": str(observed)} if status != "PASS" else {})}


class Capture:
    def __init__(self, out, capture_id, index=0):
        self.out, self.capture_id, self.idx = out, capture_id, index
        self.raw = out / "raw"
        self.raw.mkdir(exist_ok=True)
        self.stream = None
        self.total = sum(p.stat().st_size for p in self.raw.glob("*.jsonl"))
        self.part = len(list(self.raw.glob("*.jsonl")))

    def put(self, kind, wire=b"", *, epoch=0, utc=None, mono=None, channel=None, **info):
        if kind == "ws" and len(wire) > MAX_FRAME:
            raise ValueError("frame exceeds 1 MiB")
        if utc is None:
            utc = time.time_ns()
        frame = {"schema_version": 1, "capture_id": self.capture_id, "idx": self.idx + 1,
                 "receive_index": self.idx + 1, "kind": kind, "venue": "kraken",
                 "instrument": SYMBOL, "connection_epoch": epoch,
                 "received_utc": stamp(info.get("queue_received_utc",utc)),
                 "utc": utc, "mono": mono if mono is not None else time.monotonic_ns(),
                 "channel": channel or kind, "payload_bytes": base64.b64encode(wire).decode("ascii"),
                 "sha256": sha(wire), **info}
        frame["received_monotonic_ns"] = info.get("queue_received_mono",frame["mono"])
        line = dump(frame).encode() + b"\n"
        other = sum(p.stat().st_size for p in self.out.iterdir() if p.is_file())
        if self.total + other + len(line) >= CAP - 16*MIB or shutil.disk_usage(self.out).free < 2048*MIB + 16*MIB:
            raise OSError("capture safety disk threshold")
        if (self.stream is None or self.stream.tell()+len(line) > 64*MIB or
                frame["mono"]-self.part_start >= 3600*NANO):
            self.close()
            self.part += 1
            self.part_start = frame["mono"]
            self.stream = (self.raw / f"{self.part:06d}.jsonl").open("xb")
        self.stream.write(line)
        self.stream.flush()
        os.fsync(self.stream.fileno())
        self.total += len(line)
        self.idx += 1
        return frame

    def close(self):
        if self.stream:
            self.stream.close()
            self.stream = None


def frames(out, parts=None):
    previous = 0
    for path in sorted((out / "raw").glob("*.jsonl")) if parts is None else parts:
        with path.open("rb") as stream:
            for line in stream:
                if not line.endswith(b"\n"):
                    raise ValueError(f"torn raw frame at {path}")
                frame = load(line)
                if frame["idx"] != previous + 1:
                    raise ValueError("capture index gap")
                previous = frame["idx"]
                yield frame


def payload(frame):
    wire = base64.b64decode(frame["payload_bytes"], validate=True)
    if sha(wire) != frame["sha256"]:
        raise ValueError("raw payload hash mismatch")
    if not wire:
        return None
    try:
        return load(wire)
    except (ValueError, UnicodeError):
        if frame["kind"] != "ws":
            raise
        return None


class Session:
    def __init__(self, out, run_id, policy, *, ledger=None, stress=False, stats=True):
        self.run_id, self.policy = run_id, policy
        self.book, self.bars = Book(), Bars()
        self.ledger = ledger or Ledger(out / "ledger.sqlite3")
        self.engine = Engine(self.ledger, stress)
        self.meta = None
        self.clock = False
        self.last_clock = None
        self.clock_anchor = None
        self.ready_ages = []
        self.stats = stats
        self.run_begin = None
        self.run_duration = None
        self.last_sample_slot = -1
        self.samples = 0
        self.samples_by_day = {}
        self.resync = None
        self.forced = None
        self.force_utc = None
        self.boundaries = {}
        self.last = None
        self.bar_log = (out / "bars.jsonl").open("w", encoding="utf-8") if out else None

    def ready(self, frame):
        return (self.clock and self.last_clock is not None and
                frame["mono"] - self.last_clock <= 120*NANO and self.book.fresh(frame["utc"])
                and self.meta is not None and self.meta["status"] == "online")

    def discontinuity(self, reason):
        self.book.invalidate()
        self.engine.interrupt(reason)

    def handle(self, frame):
        obj = payload(frame)
        with self.ledger.transaction(frame["idx"], sha(dump(frame).encode())) as new:
            if not new:
                return
            self.process(frame, obj)
        self.last = frame

    def process(self, f, obj):
        kind, epoch, utc, mono = (f[k] for k in ("kind", "connection_epoch", "utc", "mono"))
        book, engine = self.book, self.engine
        if self.clock_anchor and kind != "restart":
            t, m = self.clock_anchor
            if abs((utc-t)-(mono-m)) > 500_000_000 or mono < m:
                self.clock = False
                self.discontinuity("UTC jump")
        self.clock_anchor = (utc, mono)
        if self.last_clock is not None and mono-self.last_clock > 120*NANO:
            self.clock = False
            self.discontinuity("clock reference expired")
        if self.clock:
            engine.roll_day(utc)
        engine.expire(mono)
        if kind == "clock":
            values = [D(value) for value in f["offset_ms"]]
            median = sorted(values)[len(values)//2] if values else None
            self.clock = bool(len(values) >= 3 and abs(median) <= 500 and max(values)-min(values) <= 250)
            self.last_clock = mono
            if not self.clock:
                self.discontinuity("invalid UTC reference")
        elif kind == "run_begin":
            self.run_begin, self.run_duration = utc, f["duration"]
            self.last_sample_slot = -1
            self.samples = 0
            self.ready_ages.clear()
            self.samples_by_day.clear()
            self.forced = self.force_utc = self.resync = None
        elif kind == "connect":
            engine.interrupt("new epoch")
            book.connect(epoch)
            self.meta = None
        elif kind in ("disconnect", "restart", "overflow", "shutdown"):
            self.discontinuity(f.get("reason", kind))
            if kind == "restart":
                self.clock, self.last_clock = False, None
                engine.s["last_exit"] = None
            if f.get("forced"):
                self.forced = f.get("force_mono",mono)
                self.force_utc = f.get("force_utc",utc)
        elif kind == "operator":
            if f["action"] == "stop":
                engine.s["manual"] = True
                engine.interrupt("operator stop", buys_only=True)
                engine.exit_target(f"manual/{f['idx']}", D(0))
                engine.log(f"operator/{f['idx']}", "stop", reason=f["note"])
            else:
                if f["action"] == "daily" and not self.clock:
                    raise ValueError("daily unlock requires trusted UTC")
                engine.acknowledge(f["action"], f["note"], utc)
        elif kind == "ws" and epoch == book.epoch:
            if not isinstance(obj, dict):
                self.discontinuity("malformed websocket JSON")
                engine.log(f"reject/{f['idx']}", "reject", reason="malformed websocket JSON")
                return
            channel = obj.get("channel")
            if channel == "instrument":
                try:
                    new = instrument(obj)
                except (ValueError, KeyError, TypeError, ArithmeticError):
                    new = None
                    self.discontinuity("invalid instrument metadata")
                    self.meta = None
                if new and new != self.meta:
                    engine.interrupt("metadata changed")
                    self.meta = new
                    engine.log(f"metadata/{f['idx']}", "metadata", **new)
            elif channel == "status" and any(s.get("system") != "online" for s in obj.get("data", [])):
                self.discontinuity("venue offline")
            elif channel == "book":
                try:
                    accepted = book.apply(epoch, f["idx"], obj)
                except (ValueError, KeyError, TypeError, ArithmeticError) as exc:
                    self.discontinuity(str(exc))
                    engine.log(f"reject/{f['idx']}", "reject", reason=str(exc))
                else:
                    if accepted and book.age(utc) < -500_000_000:
                        self.discontinuity("book timestamp too far in future")
                        engine.log(f"reject/{f['idx']}", "reject", reason="future book timestamp")
                        accepted = False
                    if accepted and self.clock and book.fresh(utc):
                        engine.on_book(book, self.meta, f)
                        if self.policy == "hold-v1" and engine.s["target"] and self.meta:
                            self.hold_complete()
        elif kind == "sample" and self.stats and self.run_begin is not None:
            slot = (utc-self.run_begin)//NANO
            if self.last_sample_slot < slot < self.run_duration:
                self.last_sample_slot = slot
                self.samples += 1
                day = utc//(86400*NANO)
                count = self.samples_by_day.setdefault(day, [0, 0])
                count[0] += 1
                if self.ready(f):
                    self.ready_ages.append(max(0, book.age(utc)))
                    count[1] += 1
        elif kind == "ohlc":
            self.on_bars(f, obj)
        elif (kind == "deadline" and utc >= (f["end"]+60)*NANO
              and (f["interval"], f["end"]) not in self.boundaries):
            self.decision(f, "no timely eligible candle", None)
        if self.forced is not None and self.resync is None and self.ready(f):
            self.resync = mono-self.forced

    def on_bars(self, f, obj):
        interval = f["interval"]
        try:
            versions = self.bars.accept(obj, interval, f["utc"], f["pair"])
        except (ValueError, KeyError, TypeError, ArithmeticError):
            return
        if self.bar_log:
            for version in versions:
                self.bar_log.write(dump(version) + "\n")
        end = f.get("end")
        if end is None or (interval, end) in self.boundaries or not in_window(end, f["utc"]):
            return
        closes = self.bars.closes(interval, end, 1 if interval == 240 else 50)
        if not closes or not self.ready(f):
            return
        target = None
        if self.policy == "paper-alternating-v1" and interval == 240:
            target = D(".02") if (end//14400)%2 == 0 else D(0)
        elif self.policy == "daily-sma50-v1" and interval == 1440:
            target = D(".10") if closes[-1]*50 > sum(closes) else D(0)
        elif self.policy == "hold-v1" and interval == 1440 and not self.engine.s.get("hold_complete"):
            target = D(".10")
            if self.hold_complete():
                target = None
        self.decision(f, None, target)

    def hold_complete(self):
        nav, btc = self.engine.val("nav"), self.engine.val("btc")
        gap = nav*D(".10") - btc*self.book.bid
        min_cost = max(self.meta["qty_min"]*self.book.ask, self.meta["cost_min"])
        if gap < min_cost:
            self.engine.s["hold_complete"] = True
        return self.engine.s.get("hold_complete",False)

    def decision(self, f, reason, target):
        interval, end = f["interval"], f["end"]
        self.boundaries[interval, end] = not reason
        key = f"{self.run_id}/{self.policy}/{SYMBOL}/{interval}/{end}"
        self.engine.decide(key, target, reason, self.book, self.meta, f)

    def close(self):
        if self.bar_log:
            self.bar_log.close()
        self.ledger.close()

    def metrics(self):
        ages = sorted(self.ready_ages)
        quantile = lambda p: (ages[(len(ages)*p+99)//100-1]/1_000_000 if ages else None)
        mark = self.engine.s["mark_ns"]
        expected = self.run_duration or 0
        return {"interval_started_utc": stamp(self.run_begin) if self.run_begin is not None else None,
                "last_mark_utc": stamp(mark) if mark is not None else None,
                "last_mark_age_ms": (self.last["utc"]-mark)/1_000_000 if mark is not None and self.last else None,
                "expected_seconds": expected, "missing_seconds": expected-self.samples,
                "invalid_seconds": expected-len(ages),
                "forced_utc": stamp(self.force_utc) if self.force_utc is not None else None,
                "seconds_sampled": self.samples, "ready_seconds": len(ages),
                "ready_fraction": len(ages)/expected if expected else 0,
                "p50_age_ms": quantile(50), "p95_age_ms": quantile(95), "p99_age_ms": quantile(99),
                "resync_ms": self.resync/1_000_000 if self.resync is not None else None,
                "bar_boundaries": sum(interval == 240 for interval, end in self.boundaries),
                "timely_bars": sum(ok for (interval, end), ok in self.boundaries.items() if interval == 240)}


def manifest(out, run_id, policy, started, **info):
    value = {"schema_version": 1, "run_id": run_id, "policy": policy, "started_utc": stamp(started),
             "versions": versions(), "code_hashes": code_hashes(),
             "parts": {str(p.relative_to(out).as_posix()): digest_file(p)
                       for p in sorted((out / "raw").glob("*.jsonl"))},
             **info}
    if value.get("state") != "COLLECTING" and (out/"ledger.sqlite3").is_file():
        value["ledger_sha256"] = digest_file(out/"ledger.sqlite3")
    write_json(out / "manifest.json", value)
    return value


def verified_parts(source):
    info = load(source.read_bytes())
    if (info["schema_version"] != 1 or info["code_hashes"] != code_hashes()
            or info["policy"] not in ("observe","paper-alternating-v1")):
        raise ValueError("capture requires the recorded code and settings")
    parts = []
    for rel, digest in sorted(info["parts"].items()):
        part = source.parent / rel
        if part.resolve().parent != (source.parent / "raw").resolve() or digest_file(part) != digest:
            raise ValueError(f"invalid manifest part {rel}")
        parts.append(part)
    return info, parts


def compare(left, right):
    from itertools import zip_longest
    first = next(((a, b) for a, b in zip_longest(left.sequence(), right.sequence()) if a != b), None)
    return {"equal": first is None, "first_difference": first}
