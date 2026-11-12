"""Executable acceptance fixtures using the product engine and event pipeline."""
import asyncio
import copy
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from .data import Bars, Book, D, NANO, crc, dump, in_window, load, parse_time, sha, stamp
from .engine import Engine, Ledger
from .live import candle_window, host_checks, sample_window
from .runtime import Capture, Session, check, compare, digest_file, frames

UTC = parse_time("2026-01-01T04:00:02Z")
META = {"price_increment": D(".1"), "qty_increment": D(".01"),
        "qty_min": D(".01"), "cost_min": D(".5"), "status": "online"}


def market(idx=1, utc=UTC, asks=None, bids=None):
    asks = asks if asks is not None else {"100": "1", "100.1": ".5", "100.3": "10"}
    bids = bids if bids is not None else {"99.9": ".4"}
    sides = {side: {D(p): D(q) for p,q in levels.items()}
             for side, levels in (("asks", asks), ("bids", bids))}
    return {"channel": "book", "type": "snapshot", "data": [{
        "symbol": "BTC/USD", "timestamp": stamp(utc), "checksum": crc(sides),
        **{side: [{"price": p, "qty": q} for p,q in levels.items()] for side,levels in sides.items()}
    }]}


def book_at(idx=1, **kw):
    b = Book()
    b.connect(1)
    b.apply(1, idx, market(**kw))
    return b


class Fixtures(unittest.TestCase):
    def setUp(self):
        self.observed = None
        self.fixture = load((self.folder / "build-contract-fixture.json").read_bytes())
        self.probe = load((self.folder / "kraken-crc-probe.json").read_bytes())
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.out = Path(temporary.name)

    def test_D01(self):
        b = Book()
        b.connect(1)
        for i, (raw, expected) in enumerate(zip(self.probe["raw"], self.probe["checks"], strict=True), 1):
            msg = load(raw["wire"])
            self.assertTrue(b.apply(1, i, msg))
            self.assertEqual(crc(b.sides), expected["checksum"])
            self.assertEqual([b.ask, b.sides["asks"][b.ask]], list(map(D, expected["ask"])))
            self.assertEqual([b.bid, b.sides["bids"][b.bid]], list(map(D, expected["bid"])))
            self.assertLessEqual(len(b.sides["asks"]), 10)
            if i == 2:
                self.assertNotIn(D("75751.4"), b.sides["asks"])
        official = {"asks": {}, "bids": {}}
        values = (
            "45285.2:0.00100000 45286.4:1.54571953 45286.6:1.54571109 45289.6:1.54560911 45290.2:0.15890660 45291.8:1.54553491 45294.7:0.04454749 45296.1:0.35380000 45297.5:0.09945542 45299.5:0.18772827",
            "45283.5:0.10000000 45283.4:1.54582015 45282.1:0.10000000 45281.0:0.10000000 45280.3:1.54592586 45279.0:0.07990000 45277.6:0.03310103 45277.5:0.30000000 45277.3:1.54602737 45276.6:0.15445238",
        )
        for side, levels in zip(official, values):
            official[side] = dict(tuple(map(D, level.split(":"))) for level in levels.split())
        self.assertEqual(crc(official), 3310070434)
        self.observed = {"captured_crcs":[c["checksum"] for c in self.probe["checks"]],
                         "official_crc":crc(official)}

    def test_D02(self):
        b = Book()
        b.connect(1)
        raw = self.probe["raw"]
        snapshot, update = (load(raw[i]["wire"]) for i in (0, 1))
        with self.assertRaises(ValueError):
            b.apply(1, 1, update)
        self.assertFalse(b.fresh(UTC))
        b.connect(2)
        self.assertFalse(b.apply(1, 2, snapshot))
        bad = copy.deepcopy(snapshot)
        bad["data"][0]["checksum"] ^= 1
        with self.assertRaises(ValueError):
            b.apply(2, 3, bad)
        with self.assertRaises(ValueError):
            b.apply(2, 4, snapshot)
        b.connect(3)
        self.assertTrue(b.apply(3, 5, snapshot))
        cap = Capture(self.out, "test")
        s = Session(None, "test", "observe", ledger=Ledger(":memory:"))
        self.addCleanup(s.close)
        self.addCleanup(cap.close)
        s.handle(cap.put("connect", epoch=1))
        s.handle(cap.put("ws", raw[0]["wire"].encode(), epoch=1))
        s.handle(cap.put("overflow", epoch=1))
        self.assertEqual(s.book.state, "STALE")
        self.assertEqual(s.ledger.db.execute("SELECT count(*) FROM events WHERE kind='fill'").fetchone()[0], 0)
        s.handle(cap.put("connect", epoch=2))
        s.handle(cap.put("ws", raw[0]["wire"].encode(), epoch=2))
        self.assertEqual(s.book.state, "READY")

    def test_T02(self):
        b = book_at()
        for age, expected in [(1999, True), (2000, True), (2001, False), (-500, True), (-501, False)]:
            self.assertEqual(b.fresh(UTC+age*1_000_000), expected)
        cap = Capture(self.out, "clock")
        self.addCleanup(cap.close)
        s = Session(None, "clock", "observe", ledger=Ledger(":memory:"))
        self.addCleanup(s.close)
        def emit(kind, offset=0, wire=b"", **kw):
            s.handle(cap.put(kind, wire, epoch=1, utc=UTC+offset, mono=offset, **kw))
        emit("clock", offset_ms=["10","20","30"])
        emit("connect")
        emit("ws", wire=dump(market()).encode())
        emit("ws", 2*NANO+1, b'{"channel":"heartbeat"}')
        self.assertFalse(s.book.fresh(s.last["utc"]))
        s.handle(cap.put("sample", utc=UTC+4*NANO, mono=2*NANO+2))
        self.assertFalse(s.clock)
        self.assertEqual(s.book.state, "STALE")
        s.handle(cap.put("clock", utc=UTC+4*NANO, mono=2*NANO+2, offset_ms=["0","251","0"]))
        self.assertFalse(s.clock)

        start = UTC+6*NANO
        s.handle(cap.put("run_begin",utc=start,mono=3*NANO,duration=8))
        times = []

        async def after_suspend(target):
            return target if target == start else max(target,start+5*NANO)

        with patch("crypto_paper.live.wait_utc",side_effect=after_suspend):
            asyncio.run(sample_window(start,start+8*NANO,times.append))
        self.assertEqual(times,[start,start+5*NANO,start+6*NANO,start+7*NANO])
        # Isolate UTC accounting from book readiness, already checked above.
        with patch.object(s,"ready",return_value=True), patch.object(s.book,"age",return_value=0):
            for i,utc in enumerate(times+[times[-1],times[0],start+8*NANO]):
                s.handle(cap.put("sample",utc=utc,mono=(4+i)*NANO))
        m = s.metrics()
        self.assertEqual((m["expected_seconds"],m["seconds_sampled"],m["missing_seconds"],
                          m["invalid_seconds"],m["ready_seconds"],m["ready_fraction"]),
                         (8,4,4,4,4,.5))

        s.handle(cap.put("run_begin",utc=start+10*NANO,mono=20*NANO,duration=86400))
        self.assertEqual(host_checks(s,"DONE","fixture",86400,21600)["status"],"FAIL")
        ideal = s.metrics() | {"ready_seconds":86400,"p95_age_ms":500,"p99_age_ms":800,
                               "resync_ms":1000,"bar_boundaries":6,"timely_bars":5}
        with patch.object(s,"metrics",return_value=ideal):
            s.force_utc = s.run_begin+21600*NANO
            self.assertEqual(host_checks(s,"DONE","fixture",86400,21600)["status"],"PASS")
            s.force_utc += NANO
            self.assertEqual(host_checks(s,"DONE","fixture",86400,21600)["status"],"FAIL")

    def test_F01(self):
        fixture = self.fixture["utc"]
        end = parse_time(fixture["bar_end"])//NANO
        start = parse_time(fixture["bar_start"])//NANO
        open_start = parse_time(fixture["open_row_start"])//NANO
        body = {"error": [], "result": {"XXBTZUSD": [
            [start, "100","101","99","100","100","1",1],
            [open_start, "100","101","99","100","100","1",1]]}}
        bars = Bars()
        for index, received in enumerate(fixture["accept"]):
            t = parse_time(received)
            self.assertTrue(in_window(end,t))
            self.assertEqual(len(bars.accept(body,240,t,"XXBTZUSD")), 1-index)
        self.assertIsNone(bars.closes(240,end+14400,1))
        self.assertFalse(in_window(end,parse_time(fixture["reject"])))
        body["result"]["XXBTZUSD"][0][4] = "100.5"
        self.assertEqual(bars.accept(body,240,UTC+NANO,"XXBTZUSD")[0]["previous_sha256"],
                         sha(dump([D(100),D(101),D(99),D(100),D(100),D(1),1]).encode()))

        cap = Capture(self.out, "bar")
        self.addCleanup(cap.close)
        s = Session(None, "bar", "paper-alternating-v1", ledger=Ledger(":memory:"))
        self.addCleanup(s.close)
        for kind, wire, fields in [
            ("clock", b"", {"offset_ms": ["0","0","0"]}), ("connect", b"", {}),
            ("ws", dump({"channel":"instrument","data":{"pairs":[META | {"symbol":"BTC/USD"}]}}).encode(), {}),
            ("ws", dump(market()).encode(), {}),
            ("ohlc", dump(body).encode(), {"interval":240, "end":end, "pair":"XXBTZUSD"}),
            ("ohlc", dump(body).encode(), {"interval":240, "end":end, "pair":"XXBTZUSD"}),
        ]:
            s.handle(cap.put(kind, wire, epoch=1, utc=UTC, mono=0, **fields))
        decisions, = s.ledger.db.execute("SELECT count(*) FROM events WHERE kind='decision'").fetchone()
        self.assertEqual(decisions,1)
        intents, = s.ledger.db.execute("SELECT count(*) FROM events WHERE kind='intent'").fetchone()
        self.assertEqual(intents-1,fixture["repeat_intents"])
        self.observed = {"decisions":decisions,"intents":intents,"repeat_intents":intents-1}
        skipped = Session(None,"suspended","paper-alternating-v1",ledger=Ledger(":memory:"))
        self.addCleanup(skipped.close)
        with tempfile.TemporaryDirectory() as temp:
            late_cap = Capture(Path(temp),"suspended")
            self.addCleanup(late_cap.close)
            later = end+14400
            resumed = (later+61)*NANO
            async def wait_after_suspend(target):
                return max(resumed,target)

            async def fetch_expired(bar_end):
                self.fail(f"polled expired boundary {bar_end}")

            def emit_deadline(kind, **fields):
                skipped.handle(late_cap.put(kind,mono=0,**fields))

            # A deadline recorded before the inclusive +60s boundary cannot suppress a decision.
            emit_deadline("deadline",interval=240,end=end,utc=(end+59)*NANO)
            self.assertFalse(skipped.boundaries)
            with patch("crypto_paper.live.wait_utc",side_effect=wait_after_suspend):
                asyncio.run(candle_window(240,(end-1)*NANO,later*NANO,skipped.boundaries,
                                          fetch_expired,emit_deadline))
            self.assertEqual(skipped.boundaries,{(240,end):False,(240,later):False})
            skipped.handle(late_cap.put("ohlc",dump(body).encode(),utc=resumed,mono=0,
                                        interval=240,end=end,pair="XXBTZUSD"))
            self.assertIsNotNone(skipped.bars.closes(240,end,1))
            self.assertEqual(skipped.ledger.db.execute(
                "SELECT count(*) FROM events WHERE kind='intent'").fetchone()[0],0)
            late_cap.close()
        self.observed["missed_boundaries"] = len(skipped.boundaries)

    def engine(self):
        ledger = Ledger(self.out / "ledger.sqlite3")
        self.addCleanup(ledger.close)
        return Engine(ledger)

    def test_X01(self):
        f = self.fixture["ioc"]
        b = book_at(asks=dict(f["ask_levels"]), bids={f["bid"]: f["partial_exit"]["qty"]})
        e = self.engine()
        frame = {"idx": 1, "utc": UTC, "mono": 0}
        with e.ledger.transaction(1, "one"):
            e.mark(b, UTC)
            e.order("buy", D(".10"), b, META, frame)
            order = e.s["orders"]["buy/order"]
            self.assertEqual(order["limit"], D(f["limit"]))
            self.assertEqual(order["qty"], D(f["requested"]))
            e.on_book(b, META, frame | {"mono": NANO})
            self.assertEqual(e.val("btc"), 0)
        b.index = 2
        with e.ledger.transaction(2, "two"):
            e.on_book(b, META, frame | {"idx":2, "mono":250_000_000})
            for key in ("cash", "nav"):
                self.assertEqual(e.val(key), D(f["expected"][key]))
            row = e.ledger.db.execute("SELECT payload FROM events WHERE id='buy/order/end'").fetchone()
            observed = load(row[0])
            for key in ("filled","cancelled","gross","fee"):
                self.assertEqual(D(observed[key]), D(f["expected"][key]))
            e.order("sell", D(0), b, META, frame | {"idx":2, "mono":250_000_000})
        b.index = 3
        with e.ledger.transaction(3, "three"):
            e.on_book(b, META, frame | {"idx":3,"mono":500_000_000})
        for key in ("cash","btc","nav"):
            self.assertEqual(e.val(key), D(f["partial_exit"][key]))
        actual = e.ledger.db.execute("SELECT payload FROM events WHERE kind='fill' ORDER BY seq DESC").fetchone()
        self.assertEqual(load(actual[0])["fee"], f["partial_exit"]["fee"])
        self.assertEqual(e.val("btc"), D("1.1"))
        self.observed = {"ioc":observed,"partial_exit":{k:e.val(k) for k in ("cash","btc","nav")},
                         "partial_exit_fee":load(actual[0])["fee"]}

    def test_X02(self):
        b = book_at(asks={"100":"1"})
        e = self.engine()
        frame = {"idx":1,"utc":UTC,"mono":0}
        with e.ledger.transaction(1, "one"):
            for oid in ("a","b"):
                e.order(oid, D(".1"), b, META, frame)
        b.index = 2
        with self.assertRaisesRegex(RuntimeError,"crash"):
            with e.ledger.transaction(2, "two"):
                e.on_book(b,META,frame | {"idx":2,"mono":NANO})
                raise RuntimeError("crash")
        self.assertEqual(e.val("cash"), 10000)
        b = book_at(2, asks={"100":"1"})
        with e.ledger.transaction(2, "two"):
            e.on_book(b,META,frame | {"idx":2,"mono":NANO})
        resumed = Ledger(self.out / "ledger.sqlite3")
        self.addCleanup(resumed.close)
        with resumed.transaction(2,"two") as new:
            self.assertFalse(new)
        self.assertEqual(D(resumed.state["cash"]), D("9899.2"))
        self.assertEqual(D(resumed.state["btc"]), 1)
        self.assertTrue(resumed.reconcile())
        self.assertEqual(resumed.db.execute("SELECT count(*) FROM events WHERE kind='fill'").fetchone()[0], 1)
        same = market(asks={"100":"1"})
        same["type"] = "update"
        b.apply(1, 3, same)
        self.assertEqual(b.used["asks"][D(100)], 1)
        lower = market(asks={"100":".6"})
        lower["type"] = "update"
        b.apply(1,4,lower)
        b.apply(1,5,same)
        self.assertEqual(b.used["asks"][D(100)], D(".6"))
        self.capture_recovery()

    def capture_recovery(self):
        from argparse import Namespace
        from .__main__ import replay, resume_session
        from .runtime import manifest
        out = self.out / "restart"
        out.mkdir()
        s = Session(out,"restart","paper-alternating-v1")
        cap = Capture(out,"restart")
        end = (UTC//NANO//14400+1)*14400
        end += 14400 if end//14400%2 else 0
        now = (end+2)*NANO
        def add(kind, wire=None, offset=0, **fields):
            return cap.put(kind,dump(wire).encode() if wire else b"",epoch=1,
                           utc=now+offset,mono=offset,**fields)
        s.handle(add("clock",offset_ms=["0","0","0"]))
        s.handle(add("connect"))
        s.handle(add("ws",{"channel":"instrument","data":{"pairs":[META | {"symbol":"BTC/USD"}]}}))
        s.handle(add("ws",market(utc=now)))
        rows = [[start,"100","101","99","100","100","1",1] for start in (end-14400,end)]
        s.handle(add("ohlc",{"error":[],"result":{"XXBTZUSD":rows}},
                     interval=240,end=end,pair="XXBTZUSD"))
        self.assertEqual(len(s.engine.s["orders"]),1)
        update = market(utc=now+NANO)
        update["type"] = "update"
        captured = add("ws",update,offset=NANO)
        cap.close()
        s.close()
        info = {"run_id":"restart","policy":"paper-alternating-v1"}
        s = resume_session(out,info)
        self.assertEqual(s.engine.val("btc"), D("1.5"))
        s.handle(captured)
        self.assertEqual(s.engine.val("btc"), D("1.5"))
        self.assertEqual(s.ledger.db.execute("SELECT count(*) FROM events WHERE kind='fill'").fetchone()[0],2)
        cap = Capture(out,"restart",captured["idx"])
        s.handle(cap.put("restart",epoch=1,utc=now+2*NANO,mono=2*NANO))
        self.assertEqual(s.engine.val("cash"),D("9848.7496"))
        self.assertFalse(s.engine.s["orders"])
        cap.close()
        s.close()
        manifest(out,"restart","paper-alternating-v1",now,state="fixture")
        replay_out = self.out/"replayed"
        self.assertEqual(replay(Namespace(out=replay_out,manifest=out/"manifest.json")),1)
        difference = load((replay_out/"comparison.json").read_bytes())
        self.assertTrue(difference["equal"])
        result = load((replay_out/"report.json").read_bytes())
        self.assertEqual(next(c for c in result["checks"] if c["id"] == "O01")["status"],"BLOCKED")

    def test_R01(self):
        b = book_at()
        e = self.engine()
        with e.ledger.transaction(1,"risk"):
            e.order("a", D(".1"), b, META, {"idx":1,"mono":0})
            self.assertLessEqual(e.s["orders"]["a/order"]["reserve"], 250)
            for i in range(5):
                e.order(f"b{i}",D(".1"),b,META,{"idx":1,"mono":0})
            self.assertLessEqual(sum(o["qty"]*o["limit"] for o in e.s["orders"].values()),1000)
            e.interrupt("test")
            e.s.update(cash=D(".1"), nav=D("10000"))
            self.assertLess(e.buy_capacity(D("100.2"),b),META["qty_min"])
            e.s.update(cash=D(1000), btc=D(20))
            e.mark(b,UTC)
            self.assertIsNotNone(e.s["exit"])

    def test_R02(self):
        b = book_at()
        e = self.engine()
        with e.ledger.transaction(1,"locks"):
            e.mark(b,UTC)
            e.s["cash"] = "9900"
            e.mark(b,UTC+1)
            self.assertIsNotNone(e.s["daily"])
            e.s["cash"] = "9600"
            e.mark(b,UTC+2)
            self.assertTrue(e.s["drawdown"])
        restored = Ledger(self.out / "ledger.sqlite3")
        self.addCleanup(restored.close)
        e = Engine(restored)
        with restored.transaction(2,"next day"):
            with self.assertRaises(ValueError):
                e.acknowledge("daily","reconciled",UTC+2)
            e.acknowledge("daily","reconciled",UTC+86400*NANO)
            self.assertTrue(e.locked())
            self.assertEqual(e.val("day_nav"),9600)
            e.s["btc"] = ".001"
            e.retry_exit(b,META,{"idx":2,"mono":NANO})
            self.assertIsNone(e.s["exit"])
        self.assertEqual(restored.db.execute("SELECT count(*) FROM events WHERE kind='DUST'").fetchone()[0],1)
        self.assertEqual(restored.db.execute("SELECT count(*) FROM events WHERE kind='fill'").fetchone()[0],0)


def run_suite(suite, folder):
    ids = {"data": ("D01","D02","F01","T02"), "execution": ("X01","X02","R01","R02")}[suite]
    hashes = {p.name:digest_file(p) for p in folder.glob("*.json")}
    checks = []
    for identity in ids:
        test = Fixtures(f"test_{identity}")
        test.folder = folder
        result = unittest.TestResult()
        test.run(result)
        errors = [message for _,message in result.failures+result.errors]
        expected = test.fixture["ioc"] if identity == "X01" else "product fixture assertions"
        checks.append(check(identity, "FAIL" if errors else "PASS", expected,
                            errors or test.observed or f"{result.testsRun} fixture case passed"))
    return checks, hashes
