"""Rehearse the frozen hourly acquisition gates with an injected clock and response."""

import argparse
from datetime import datetime, timedelta, timezone
from decimal import localcontext
import hashlib
import io
import json
from pathlib import Path
import runpy
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch

from tools.check_hourly_breakout_parity import ARCHITECT_SHA256
from tools.kraken_hourly_breakout import END, HOUR, NOT_BEFORE, WARMUP, synthetic_rows


def expect_error(call, error_type, message=None):
    try:
        call()
    except error_type as error:
        if message is not None and str(error) != message:
            raise
    else:
        raise AssertionError(f"expected {error_type.__name__}")


def check(reference):
    if hashlib.sha256(reference.read_bytes()).hexdigest() != ARCHITECT_SHA256:
        raise ValueError("Architect source must match the published 0646933 digest")
    gate = datetime.fromisoformat(NOT_BEFORE)
    with TemporaryDirectory() as temp, localcontext():
        root = Path(temp)
        run = runpy.run_path(str(reference), run_name="frozen_architect_gate")["run"]
        state = run.__globals__
        assert gate.timestamp() == state["END"] + state["DAY"]

        # The CLI must reject absent attestation before invoking the runner.
        missing = root / "missing-attestation"
        process = subprocess.run(
            [sys.executable, str(reference), "--out", str(missing)],
            capture_output=True, text=True, check=False,
        )
        assert process.returncode == 2 and "verified date separation" in process.stderr
        assert not missing.exists()

        clock = Mock(wraps=datetime)
        clock.now.return_value = gate - timedelta(seconds=1)
        request = Mock(side_effect=AssertionError("unexpected request"))
        with patch.dict(state, datetime=clock, urlopen=request):
            early = root / "early"
            expect_error(lambda: run(early), ValueError, "fixed acquisition date has not arrived")
            assert not early.exists()
            clock.now.return_value = gate

            prior = root / "incomplete-prior"
            prior.mkdir()
            (prior / "source.private.json").write_bytes(b"preserve partial evidence")
            expect_error(lambda: run(prior), FileExistsError)
            assert (prior / "source.private.json").read_bytes() == b"preserve partial evidence"
            assert not (prior / "result.private.json").exists()
            request.assert_not_called()

            full_rows = synthetic_rows()
            endpoint = [END + 24 * HOUR]
            for rows, label in ((full_rows, "complete"),
                                (full_rows[:WARMUP + 1] + full_rows[WARMUP + 2:], "gapped")):
                payload = json.dumps({
                    "error": [], "result": {"XXBTZUSD": rows + [endpoint], "last": END},
                }).encode()
                request.reset_mock()
                request.side_effect = None
                request.return_value = io.BytesIO(payload)
                output = root / label
                if label == "gapped":
                    expect_error(lambda: run(output), ValueError,
                                 "incomplete, duplicate or off-grid hourly input")
                    assert not (output / "result.private.json").exists()
                    expect_error(lambda: run(output), FileExistsError)
                else:
                    run(output)
                    report = json.loads((output / "result.private.json").read_text())
                    assert report["input_sha256"] == hashlib.sha256(payload).hexdigest()
                    assert report["validated_execution_target"] == "NOT_EVALUATED_BAR_PROXY_ONLY"
                    assert report["acquired_utc"] == gate.astimezone(timezone.utc).isoformat()
                    assert sum(map(len, report["accounts"].values())) == 8
                    for arms in report["accounts"].values():
                        for account in arms.values():
                            assert account["coverage_hours"] == 504
                            assert len(account["complete_day_returns"]) == 21
                assert (output / "source.private.json").read_bytes() == payload
                request.assert_called_once_with(state["URL"], timeout=20)
    return {"status": "PASS", "scope": "OFFLINE_SYNTHETIC_ONLY",
            "cases": ["missing_attestation", "early_clock", "existing_output",
                      "complete_at_gate", "missing_hour_and_same_path_refusal"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("architect_source", type=Path)
    args = parser.parse_args()
    print(json.dumps(check(args.architect_source), sort_keys=True))


if __name__ == "__main__":
    main()
