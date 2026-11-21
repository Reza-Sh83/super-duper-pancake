"""Rehearse the frozen Kraken panel admission with no real requests."""

from datetime import datetime, timedelta, timezone
import hashlib
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock, patch

import strategy_panel as runner

from tools.check_kraken_strategy_panel import ARCHITECT_SHA256, PANEL_SHA256

def refuse(call, error):
    try:
        call()
    except error:
        return
    raise AssertionError(f"expected {error.__name__}")


def main():
    for module, digest in ((runner, PANEL_SHA256), (runner.model, ARCHITECT_SHA256)):
        if hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest() != digest:
            raise ValueError("unexpected frozen source digest")
    start, stop = runner.WINDOWS["validation"]
    boundary = datetime.fromtimestamp(stop, timezone.utc)
    rows = [[t, "100", "100", "100", "100"] for t in range(start - 26 * 3600, stop, 3600)]
    with TemporaryDirectory() as directory:
        root = Path(directory)
        now = Mock(wraps=datetime)
        now.now.return_value = boundary - timedelta(seconds=1)
        network = Mock(side_effect=AssertionError("unexpected request"))
        with patch.object(runner, "datetime", now), patch.object(runner, "urlopen", network):
            args = SimpleNamespace(mode="validation", source=None, verified_disjoint=True, out=root / "early")
            refuse(lambda: runner.run(args), ValueError)
            assert not args.out.exists()
            now.now.return_value = boundary
            args.verified_disjoint = False
            refuse(lambda: runner.run(args), ValueError)
            assert not args.out.exists()
            args.verified_disjoint = True
            args.source = root / "retained"
            refuse(lambda: runner.run(args), ValueError)
            assert not args.out.exists()
            args.source = None
            args.out = root / "previous"
            args.out.mkdir()
            sentinel = args.out / "source.private.json"
            sentinel.write_bytes(b"retained prior evidence")
            refuse(lambda: runner.run(args), FileExistsError)
            assert sentinel.read_bytes() == b"retained prior evidence"
            network.assert_not_called()
            for case, selected in (("complete", rows), ("missing", rows[:32] + rows[33:])):
                network.reset_mock()
                network.side_effect = None
                payload = json.dumps({"error": [], "result": {"XXBTZUSD": selected + [[stop]]}}).encode()
                network.return_value = BytesIO(payload)
                args.out = root / case
                if case == "complete":
                    runner.run(args)
                    result = json.loads((args.out / "result.private.json").read_bytes())
                    assert result["hours"] == 48
                    assert sum(len(v) for v in result["accounts"].values()) == 12
                    assert all(len(a["complete_day_returns"]) == 2 for v in result["accounts"].values() for a in v.values())
                else:
                    refuse(lambda: runner.run(args), ValueError)
                    assert not (args.out / "result.private.json").exists()
                assert (args.out / "source.private.json").read_bytes() == payload
                refuse(lambda: runner.run(args), FileExistsError)
                network.assert_called_once()
    print("PASS: early clock, missing attestation, retained-source refusal, path collision, complete and missing synthetic coverage. External requests: zero.")


if __name__ == "__main__":
    main()
