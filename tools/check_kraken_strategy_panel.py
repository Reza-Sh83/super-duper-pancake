"""Independently check Architect’s frozen hourly panel on generated fixtures."""

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path
import runpy
import sys

from tools.audit_historical_kraken import COSTS, DAY, HOUR, closed_window, close_to, utc_bound
from tools.check_hourly_breakout_parity import ARCHITECT_SHA256
from unittest.mock import patch

D = Decimal
WINDOWS = {"development": ("2026-11-18", "2026-11-21"),
           "validation": ("2026-11-21", "2026-11-23")}
CONTROLS = ("breakout", "cash", "hold_small", "hold_full")


def sma_trend(bars, index):
    last = index - 2
    short = sum(row[3] for row in bars[last-7:last+1]) / 8
    long = sum(row[3] for row in bars[last-23:last+1]) / 24
    return short > long, short < long


def pullback(bars, index):
    last = index - 2
    mean = sum(row[3] for row in bars[last-12:last]) / 12
    close = bars[last][3]
    return close < D(".97") * mean, close >= mean


CANDIDATES = {"trend": sma_trend, "pullback": pullback}
PANEL_SHA256 = "84cb149c5a75672f93b45246beeb03834454233aec26acc62fe4724d9692005b"


def load_reference(path):
    if hashlib.sha256(path.read_bytes()).hexdigest() != ARCHITECT_SHA256:
        raise ValueError("reference does not match frozen commit 0646933")
    return runpy.run_path(str(path), run_name="frozen_panel_reference")


def panel(reference, response, window):
    start, end = map(utc_bound, WINDOWS[window])
    evaluation, _ = closed_window(response, start, end)
    pair = response["result"]["XXBTZUSD"][:-1]
    with localcontext() as ctx:
        ctx.prec = 34
        source = load_reference(reference)
        bars = source["prices"](pair, start, end)
        evaluate = source["evaluate"]
        results = {}
        for cost, (fee, slip) in COSTS.items():
            accounts = {arm: evaluate(bars, arm, fee, slip, start) for arm in CONTROLS}
            for name, signal in CANDIDATES.items():
                with patch.dict(evaluate.__globals__, signals=signal):
                    accounts[name] = evaluate(bars, "breakout", fee, slip, start)
                accounts[name]["strategy"] = name
            for arm, account in accounts.items():
                if account["coverage_hours"] != len(evaluation):
                    raise ValueError(f"{cost}/{arm} missing evaluation hours")
                daily = account["complete_day_returns"]
                days = [datetime.fromtimestamp(t, timezone.utc).date().isoformat()
                        for t in range(start, end, DAY)]
                if [row["day_utc"] for row in daily] != days:
                    raise ValueError(f"{cost}/{arm} UTC-day mismatch")
                close_to(account["paid_fees_usd"], account["turnover_usd"] * fee,
                         f"{cost}/{arm} paid fees")
                close_to(account["net_pct"], account["net_usd"] / 100,
                         f"{cost}/{arm} net percentage")
                account["sorted_daily_net_pct"] = sorted(day["net_pct"] for day in daily)
            results[cost] = accounts
        stress = results["stress"]
        return {"scope": "EXPLORATORY_BAR_PROXY_ONLY", "window": window,
                "start_utc": WINDOWS[window][0], "end_exclusive_utc": WINDOWS[window][1],
                "coverage_hours": len(evaluation), "warmup_hours": len(bars) - len(evaluation),
                "accounts": results,
                "stress_net_percentage_point_spreads": {
                    name: {control: stress[name]["net_pct"] - stress[control]["net_pct"]
                           for control in ("cash", "breakout")}
                    for name in CANDIDATES}}


def compare(reference, upstream_path):
    if hashlib.sha256(upstream_path.read_bytes()).hexdigest() != PANEL_SHA256:
        raise ValueError("Architect panel must match commit 7fea8fd")
    if hashlib.sha256(reference.read_bytes()).hexdigest() != ARCHITECT_SHA256:
        raise ValueError("reference must match commit 0646933")
    if reference.parent != upstream_path.parent or reference.name != "frozen_model.py":
        raise ValueError("place the pinned reference beside the Architect panel as frozen_model.py")
    sys.path.insert(0, str(reference.parent))
    try:
        upstream = runpy.run_path(str(upstream_path), run_name="architect_panel_fixture")
    finally:
        sys.path.pop(0)
    # Evaluation windows are disjoint. The plan expressly allows development
    # closes to supply validation warm-up.
    assert WINDOWS["development"][1] == WINDOWS["validation"][0]
    assert utc_bound(WINDOWS["validation"][1]) == upstream["model"].START
    output = {}
    for window, interval in WINDOWS.items():
        start, stop = map(utc_bound, interval)
        rows = []
        for index, timestamp in enumerate(range(start - 26 * HOUR, stop, HOUR)):
            price = 100 + (index * 3) % 37 - (15 if index >= 52 else 0)
            rows.append([timestamp, str(price), str(price + 4), str(price - 5), str(price + 2)])
        fixture = {"error": [], "result": {"XXBTZUSD": rows + [[stop]]}}
        ours = panel(reference, fixture, window)
        expected = upstream["evaluate"](json.dumps(fixture), window)
        if ours != panel(reference, fixture, window):
            raise AssertionError("repeatability failure")
        selected = rows[26:]
        encoded = (json.dumps(selected, separators=(",", ":")) + "\n").encode()
        if hashlib.sha256(encoded).hexdigest() != expected["selected_rows_sha256"]:
            raise AssertionError("selected-row digest mismatch")
        if ours["coverage_hours"] != expected["hours"]:
            raise AssertionError("coverage mismatch")
        for cost, accounts in ours["accounts"].items():
            for name, metrics in accounts.items():
                other = expected["accounts"][cost][name]
                if any(metrics[key] != value for key, value in other.items()):
                    raise AssertionError(f"{window}/{cost}/{name} metric mismatch")
                if name == "cash" and (metrics["fills"] or metrics["net_usd"]):
                    raise AssertionError("non-flat cash")
        output[window] = ours
    return {"scope": "SYNTHETIC_ONLY", "status": "PASS", "windows": output}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("reference", type=Path)
    parser.add_argument("architect_panel", type=Path)
    args = parser.parse_args()
    print(json.dumps(compare(args.reference, args.architect_panel), default=str, sort_keys=True))


if __name__ == "__main__":
    main()
