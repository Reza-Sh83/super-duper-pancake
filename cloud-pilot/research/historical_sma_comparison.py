"""Two locked historical research windows. This wrapper has no network access."""
from datetime import date, datetime, timezone
from decimal import Decimal
import hashlib
import json
from pathlib import Path
from statistics import median
import sys

ROOT = Path(__file__).resolve().parent
WINDOWS = {"HIST-SMA-A": ("2025-09-01", "2025-10-27"),
           "HIST-SMA-B": ("2026-01-05", "2026-03-02")}
POLICIES = ("sma50", "weekly", "hold", "cash")

def epoch(value):
    return int(datetime.combine(date.fromisoformat(value), datetime.min.time(),
                                tzinfo=timezone.utc).timestamp())

def main():
    name, source, expected_digest = sys.argv[1:]
    start_day, end_day = WINDOWS[name]
    start, end = epoch(start_day), epoch(end_day)
    assert (end - start) == 56 * 86400 and end < epoch("2026-06-25")
    output = ROOT / name
    output.mkdir(mode=0o700)
    payload = Path(source).read_bytes()
    if hashlib.sha256(payload).hexdigest() != expected_digest:
        raise ValueError("retained response identity mismatch")
    data = json.loads(payload)
    if data["error"] != []:
        raise ValueError("Kraken API error in retained response")
    rows = data["result"]["XXBTZUSD"][:-1]
    rows = [row for row in rows if start - 51 * 86400 <= row[0] < end]
    source_file = ROOT / "weekly_bar_proxy.py"
    code = source_file.read_text()
    needle = "        ending=sample(close)\n"
    assert code.count(needle) == 1
    env = {"__file__": str(source_file), "__name__": "historical_observation"}
    marks = []
    env["record_return"] = lambda opening, ending: marks.append(100 * (ending / opening - 1))
    exec(compile(code.replace(needle, needle + "        record_return(opening, ending)\n"),
                 str(source_file), "exec"), env)
    env["validate"](rows, start, end)
    result = []
    public = []
    for cost, (fee, slip) in env["COSTS"].items():
        for policy in POLICIES:
            marks.clear()
            r = env["evaluate"](rows, policy, fee, slip, start=start, end=end)
            assert len(marks) == 56
            dd = Decimal(r["sampled_drawdown_pct"])
            assert dd >= max(Decimal(0), -Decimal(r["net_pct"]))
            assert abs(Decimal(r["net_usd"]) / 100 - Decimal(r["net_pct"])) < Decimal("1e-29")
            if policy == "cash":
                assert r["fills"] == 0 and all(x == 0 for x in marks)
            up = sum(x > 0 for x in marks)
            down = sum(x < 0 for x in marks)
            dist = (min(marks), median(marks), max(marks), up, down, len(marks)-up-down,
                    sum(x >= 50 for x in marks))
            result.append({"cost": cost, **r, "daily_percent": list(marks)})
            fmt = lambda x: f"{Decimal(x):.6f}"
            public.append("| " + " | ".join([cost, policy, *(fmt(r[k]) for k in (
                "net_usd", "net_pct", "sampled_drawdown_pct", "paid_fees", "exit_reserve")),
                str(r["fills"]), *(fmt(x) for x in dist[:3]), *(str(x) for x in dist[3:])]) + " |")
    (output / "result.private.json").write_text(json.dumps(result,default=str,indent=2) + "\n")
    (output / "aggregate.md").write_text("\n".join(public) + "\n")
    print("\n".join(public))

if __name__ == "__main__":
    main()
