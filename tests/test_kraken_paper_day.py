"""Short synthetic UTC-shaped slices exercise the sealed-day ledger path."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from crypto_paper.data import D, DAY, NANO, dump, parse_time
from crypto_paper.runtime import Capture, Session, manifest
from crypto_paper.verify import META, market
from tools import kraken_paper_day as paper

START = parse_time("2026-01-01T00:00:00Z")


class PaperDayTests(unittest.TestCase):
    def fixture(self, root, *, close_bid="99.9", close_depth="20", skip=None,
                diagnostic=False, late=False):
        cap = Capture(root, "synthetic-day")
        session = Session(root, "synthetic-day", "observe")

        def emit(kind, offset, data=None, **fields):
            frame = cap.put(kind, dump(data).encode() if data else b"", epoch=1,
                            utc=START+offset, mono=2*NANO+offset, **fields)
            session.handle(frame)

        def quote(offset, bid="99.9", depth="20", initial=False, **fields):
            payload = market(utc=START+offset, asks={"100":"1", "100.1":"20"},
                             bids={bid:depth})
            emit("ws", offset, payload | {"type":"snapshot" if initial else "update"}, **fields)

        try:
            emit("clock", -NANO, offset_ms=["0","0","0"])
            emit("connect", -NANO)
            emit("ws", -NANO, {"channel":"instrument", "data":{"pairs":[META | {"symbol":"BTC/USD"}]}})
            quote(-NANO, initial=True)
            emit("run_begin", 0, duration=4)
            for second in range(4):
                quote(second*NANO, close_bid if second == 3 else "99.9",
                      close_depth if second == 3 else "20",
                      **({"queue_received_utc":START+4*NANO} if late and second == 3 else {}))
                if second != skip:
                    emit("sample", second*NANO)
            emit("shutdown", 4*NANO)
        finally:
            cap.close()
            session.close()
        manifest(root, "synthetic-day", "observe", START, state="DONE",
                 clock_unverified_diagnostic=diagnostic)
        return root / "manifest.json"

    def test_cash_and_fee_adjusted_loss_only_fill_at_top_level(self):
        with TemporaryDirectory() as tmp, patch.object(paper, "DAY", 4):
            path = self.fixture(Path(tmp))
            original = {p: p.read_bytes() for p in path.parent.rglob("*") if p.is_file()}
            result = paper.evaluate(path, START)
            self.assertEqual(result["cash_control"]["nav_usd"], D(10000))
            self.assertEqual(result["cash_control"]["fees_paid_usd"], 0)
            baseline = result["best_quote_paper"]
            self.assertEqual(baseline["buy_fills"], 1)
            self.assertEqual(baseline["btc"], 1)
            self.assertEqual(baseline["fees_paid_usd"], D(".8"))
            self.assertEqual(baseline["exit_fee_reserve_usd"], D(".7992"))
            self.assertEqual(baseline["cash_usd"], D("9899.2"))
            self.assertEqual(baseline["nav_usd"], D("9998.3008"))
            self.assertEqual(baseline["net_usd"], D("-1.6992"))
            self.assertEqual(baseline["net_percent"], D("-.016992"))
            self.assertEqual(baseline["max_drawdown_percent"], D(".016992"))
            self.assertFalse(result["target_50_percent_candidate"])
            self.assertEqual(original, {p: p.read_bytes() for p in original})

    def test_full_day_requirement_and_gap(self):
        with TemporaryDirectory() as tmp:
            path = self.fixture(Path(tmp))
            with self.assertRaisesRegex(paper.Blocked, "capture discontinuity"):
                paper.evaluate(path, START)
            self.assertEqual(paper.DAY, DAY)
        with TemporaryDirectory() as tmp, patch.object(paper, "DAY", 4):
            with self.assertRaisesRegex(paper.Blocked, "sample slot"):
                paper.evaluate(self.fixture(Path(tmp), skip=2), START)

    def test_diagnostic_late_and_insufficient_depth_block_metrics(self):
        for options, reason in (({"diagnostic":True}, "verified clock"),
                                ({"late":True}, "cutoff"),
                                ({"close_depth":".5"}, "displayed bid depth")):
            with self.subTest(options=options), TemporaryDirectory() as tmp, patch.object(paper, "DAY", 4):
                with self.assertRaisesRegex(paper.Blocked, reason):
                    paper.evaluate(self.fixture(Path(tmp), **options), START)

    def test_tampered_sealed_frame_is_rejected(self):
        with TemporaryDirectory() as tmp, patch.object(paper, "DAY", 4):
            path = self.fixture(Path(tmp))
            raw, = (path.parent / "raw").glob("*.jsonl")
            with raw.open("ab") as stream:
                stream.write(b"modified\n")
            with self.assertRaisesRegex(ValueError, "invalid manifest part"):
                paper.evaluate(path, START)
