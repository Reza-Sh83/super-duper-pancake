"""Run the native OFI feature transcript on deterministic synthetic frames."""

import argparse
from pathlib import Path
from tempfile import TemporaryDirectory

from crypto_paper.data import D, NANO, dump, parse_time
from crypto_paper.engine import Ledger
from crypto_paper.runtime import Capture
from crypto_paper.verify import META, market
from tools.ofi_replay_features import FeatureSession


def check(oracle):
    start = parse_time("2026-01-01T00:00:00Z")
    end = start + 86400 * NANO
    with TemporaryDirectory() as tmp:
        ledger = Ledger(":memory:")
        session = FeatureSession(ledger, "ofi-fixture", start, end, oracle)
        capture = Capture(Path(tmp), "ofi-fixture")

        def emit(kind, elapsed=0, body=None, epoch=1, **fields):
            frame = capture.put(kind, b"" if body is None else dump(body).encode(),
                                epoch=epoch, mono=elapsed, utc=start + elapsed, **fields)
            session.handle(frame)
            return frame

        def book(elapsed, *, snapshot=False, qty="2", epoch=1):
            payload = market(utc=start + elapsed, asks={"101": "2"}, bids={"100": qty})
            payload["type"] = "snapshot" if snapshot else "update"
            return emit("ws", elapsed, payload, epoch=epoch)

        try:
            emit("clock", offset_ms=["0", "0", "0"])
            emit("connect")
            emit("ws", body={"channel": "instrument", "data": {
                "pairs": [META | {"symbol": "BTC/USD"}]}})
            snapshot = book(0, snapshot=True)
            for _ in range(19):
                book(100_000_000)
            assert not session.observations
            trigger = book(100_000_000, qty="4")
            observation, = session.observations
            assert (observation["first_index"], observation["receive_index"]) == (
                snapshot["idx"], trigger["idx"])
            assert observation["static_imbalance"] > D(".20")
            assert observation["ofi"] > 0
            session.handle(trigger)
            book(100_000_000, qty="200")
            assert session.observations == [observation]
            second = book(NANO)
            assert len(session.observations) == 2
            assert session.observations[-1]["receive_index"] == second["idx"]

            # Jump in freshness without changing the venue epoch.
            stale_gap = book(4 * NANO)
            assert [q.receive_index for q in session.window] == [stale_gap["idx"]]
            assert len(session.observations) == 2
            emit("overflow", 4 * NANO)
            assert not session.window
            emit("connect", 4 * NANO, epoch=2)
            emit("ws", 4 * NANO, {"channel": "instrument", "data": {
                "pairs": [META | {"symbol": "BTC/USD"}]}}, epoch=2)
            book(4 * NANO, snapshot=True, epoch=2)
            assert len(session.window) == 1 and len(session.observations) == 2
            emit("ws", 4 * NANO, {"channel": "instrument", "data": {
                "pairs": [META | {"symbol": "BTC/USD", "price_increment": D(".2")}]}
            }, epoch=2)
            assert not session.window and len(session.observations) == 2
            book(4 * NANO, epoch=2)
            assert len(session.window) == 1
            emit("sample", 86400 * NANO, epoch=2)
            book(4 * NANO, epoch=2)  # A late clock regression cannot reopen the partition.

            assert not session.window and len(session.observations) == 2
            assert ledger.reconcile()
            assert ledger.db.execute(
                "SELECT count(*) FROM events WHERE kind IN ('intent','fill')"
            ).fetchone()[0] == 0
            print(f"PASS: trigger indices {trigger['idx']}, {second['idx']}; "
                  f"snapshot index {snapshot['idx']}; no intents or fills")
        finally:
            capture.close()
            session.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("oracle", type=Path)
    check(parser.parse_args().oracle)


if __name__ == "__main__":
    main()
