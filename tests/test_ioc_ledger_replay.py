"""Replay identical IOC intents through fresh, stale and discontinuous books."""

from argparse import Namespace
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from crypto_paper.__main__ import replay
from crypto_paper.data import D, NANO, dump, load, parse_time
from crypto_paper.engine import Engine, Ledger
from crypto_paper.runtime import Capture, Session, manifest
from crypto_paper.verify import META, UTC, book_at, market


class IOCLedgerReplayTests(unittest.TestCase):
    def test_fresh_partial_and_rejected_book_paths(self):
        end = parse_time("2026-01-01T08:00:00Z") // NANO
        now = (end + 2) * NANO
        policy = "paper-alternating-v1"
        for case in ("fresh", "stale", "gap"):
            with self.subTest(case=case), TemporaryDirectory() as temp:
                root = Path(temp)
                source = root / "source"
                source.mkdir()
                session = Session(source, case, policy)
                capture = Capture(source, case)

                def emit(kind, *, offset=0, body=None, **fields):
                    wire = b"" if body is None else dump(body).encode()
                    frame = capture.put(kind, wire, utc=now + offset, mono=offset,
                                        epoch=1, **fields)
                    session.handle(frame)

                def update(offset, age=0):
                    body = market(utc=now + offset - age)
                    body["type"] = "update"
                    emit("ws", offset=offset, body=body)

                try:
                    emit("clock", offset_ms=["0", "0", "0"])
                    emit("connect")
                    emit("ws", body={"channel": "instrument", "data": {"pairs": [
                        META | {"symbol": "BTC/USD"}]}})
                    emit("ws", body=market(utc=now))
                    rows = [[t, "100", "101", "99", "100", "100", "1", 1]
                            for t in (end - 14400, end)]
                    emit("ohlc", body={"error": [], "result": {"XXBTZUSD": rows}},
                         interval=240, end=end, pair="XXBTZUSD")
                    order_id, order = next(iter(session.engine.s["orders"].items()))
                    self.assertEqual(order["qty"], D("2"))
                    self.assertEqual(order["limit"], D("100.2"))
                    self.assertEqual(session.engine.val("btc"), 0)
                    if case == "gap":
                        emit("overflow", offset=249_000_000)
                    if case == "stale":
                        arrival = 2 * NANO + 250_000_000
                        update(arrival, 2 * NANO + 1)
                        self.assertFalse(session.book.fresh(now + arrival))
                        self.assertIn(order_id, session.engine.s["orders"])
                        emit("sample", offset=5 * NANO)  # Exact inclusive TTL.
                    else:
                        update(250_000_000)
                    if case == "gap":
                        self.assertEqual(session.book.state, "STALE")
                    self.assertFalse(session.engine.s["orders"])
                finally:
                    capture.close()
                    session.close()

                manifest(source, case, policy, now, state="fixture")
                output = root / "replay"
                self.assertEqual(replay(Namespace(out=output, manifest=source / "manifest.json")), 1)
                self.assertTrue(load((output / "comparison.json").read_bytes())["equal"])
                checks = load((output / "report.json").read_bytes())["checks"]
                self.assertEqual({check["id"]: check["status"] for check in checks},
                                 {"replay": "PASS", "O01": "BLOCKED"})
                with self.subTest(case=case, ledger="replayed"):
                    ledger = Ledger(output / "ledger.sqlite3", readonly=True)
                    try:
                        self.assertTrue(ledger.reconcile())
                        fills = ledger.db.execute(
                            "SELECT payload FROM events WHERE kind='fill' ORDER BY seq"
                        ).fetchall()
                        terminal = ledger.db.execute(
                            "SELECT kind,payload FROM events WHERE id=?", (order_id + "/end",)
                        ).fetchone()
                        state = ledger.state
                        if case == "fresh":
                            self.assertEqual(len(fills), 2)
                            self.assertEqual(sum(D(load(row[0])["fee"]) for row in fills), D("1.2004"))
                            result = load(terminal[1])
                            self.assertEqual(tuple(D(result[key]) for key in ("filled", "cancelled", "gross")),
                                             (D("1.5"), D("0.5"), D("150.05")))
                            self.assertEqual(tuple(D(state[k]) for k in ("cash", "btc", "nav")),
                                             (D("9848.7496"), D("1.5"), D("9997.4008")))
                        else:
                            self.assertEqual(fills, [])
                            self.assertEqual((terminal[0], load(terminal[1])["reason"]),
                                             ("cancel", "TTL" if case == "stale" else "overflow"))
                            self.assertEqual(tuple(D(state[k]) for k in ("cash", "btc", "nav")),
                                             (D(10000), D(0), D(10000)))
                        self.assertFalse(state["orders"])
                    finally:
                        ledger.close()

    def test_stress_latency_and_limit_after_adverse_rounding(self):
        ledger = Ledger(":memory:")
        self.addCleanup(ledger.close)
        engine = Engine(ledger, stress=True)
        book = book_at()
        with ledger.transaction(1, "intent"):
            engine.order("stress", D(".02"), book, META, {"idx": 1, "mono": 0})
            order = engine.s["orders"]["stress/order"]
            self.assertEqual(order["limit"], D("100.2"))
            self.assertEqual(order["qty"], D(2))
        for index, offset, btc in ((2, 999_000_000, D(0)), (3, NANO, D(1))):
            book.index = index
            with ledger.transaction(index, str(index)):
                engine.on_book(book, META, {"idx": index, "mono": offset, "utc": UTC + offset})
                self.assertEqual(engine.val("btc"), btc)
        rows = ledger.db.execute("SELECT payload FROM events WHERE kind='fill'").fetchall()
        self.assertEqual(len(rows), 1)
        fill = load(rows[0][0])
        self.assertEqual((D(fill["price"]), D(fill["fee"])), (D("100.1"), D("1.001")))
        end = load(ledger.db.execute(
            "SELECT payload FROM events WHERE id='stress/order/end'").fetchone()[0])
        self.assertEqual(D(end["cancelled"]), D(1))
        self.assertEqual(engine.val("cash"), D("9898.899"))
        self.assertTrue(ledger.reconcile())

    def test_base_ioc_matches_at_latency_and_expires_before_equal_ttl_frame(self):
        for before, boundary, expected in ((249_000_000, 250_000_000, D("1.5")),
                                           (249_000_000, 5 * NANO, D(0))):
            with self.subTest(boundary=boundary):
                ledger = Ledger(":memory:")
                self.addCleanup(ledger.close)
                engine = Engine(ledger)
                book = book_at()
                with ledger.transaction(1, "intent"):
                    engine.order("base", D(".02"), book, META, {"idx": 1, "mono": 0})
                for index, offset, expected_btc in ((2, before, D(0)), (3, boundary, expected)):
                    body = market(utc=UTC + offset)
                    body["type"] = "update"
                    self.assertTrue(book.apply(1, index, body))
                    with ledger.transaction(index, str(index)):
                        engine.on_book(book, META, {"idx": index, "mono": offset, "utc": UTC + offset})
                    self.assertEqual(engine.val("btc"), expected_btc)
                self.assertFalse(engine.s["orders"])
                kind, terminal = ledger.db.execute(
                    "SELECT kind,payload FROM events WHERE id='base/order/end'"
                ).fetchone()
                if expected:
                    self.assertEqual((kind, D(load(terminal)["fee"])), ("ioc", D("1.2004")))
                else:
                    self.assertEqual((kind, load(terminal)["reason"]), ("cancel", "TTL"))
                    self.assertEqual(engine.val("cash"), D(10000))
                self.assertTrue(ledger.reconcile())

    def test_consumed_depth_is_arm_local_and_repeated_quote_cannot_refill(self):
        ledger = Ledger(":memory:")
        self.addCleanup(ledger.close)
        engine = Engine(ledger)
        book = book_at(asks={"100": "1"})
        control = book_at(asks={"100": "1"})
        with ledger.transaction(1, "initial intent"):
            engine.order("first", D(".02"), book, META, {"idx": 1, "mono": 0})
        for index, offset in ((2, 250_000_000), (3, 500_000_000)):
            body = market(utc=UTC + offset, asks={"100": "1"})
            body["type"] = "update"
            for candidate in (book, control):
                self.assertTrue(candidate.apply(1, index, body))
            with ledger.transaction(index, str(index)):
                engine.on_book(book, META, {"idx": index, "mono": offset, "utc": UTC + offset})
                if index == 2:
                    engine.order("second", D(".02"), book, META, {"idx": index, "mono": offset})
            self.assertEqual(book.sides, control.sides)
            self.assertEqual(book.used["asks"][D(100)], D(1))
            self.assertEqual(control.used["asks"][D(100)], D(0))
            self.assertEqual(engine.val("btc"), D(1))
            self.assertEqual(engine.val("cash"), D("9899.2"))
        self.assertFalse(engine.s["orders"])
        kind, terminal = ledger.db.execute(
            "SELECT kind,payload FROM events WHERE id='second/order/end'"
        ).fetchone()
        self.assertEqual((kind, load(terminal)["reason"]),
                         ("cancel", "IOC below executable minimum"))
        self.assertEqual(ledger.db.execute(
            "SELECT count(*) FROM events WHERE kind='fill'").fetchone()[0], 1)
        self.assertTrue(ledger.reconcile())
