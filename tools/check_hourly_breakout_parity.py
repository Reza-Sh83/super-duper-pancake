"""Compare the frozen Architect runner with the local evaluator on fixtures only."""

import argparse
from decimal import Decimal, localcontext
import hashlib
from pathlib import Path
import runpy

from crypto_paper.data import dump
from tools import kraken_hourly_breakout as local

ARCHITECT_SHA256 = "24944c5935d438d143c1912bc342e594e17ac12ad67c1e08ceb64d145d974df7"
TOLERANCE = Decimal("1e-24")
ARMS = {"breakout": "breakout", "cash": "cash", "hold_2_5_percent": "hold_small",
        "hold_full": "hold_full"}
METRICS = {"net_usd": "net_usd", "net_percent": "net_pct", "fees_usd": "paid_fees_usd",
           "turnover_usd": "turnover_usd", "total_exit_reserve_usd": "exit_reserve_usd",
           "sampled_drawdown_percent": "sampled_max_drawdown_pct",
           "max_sampled_gross_exposure_percent": "peak_exposure_pct",
           "mean_sampled_gross_exposure_percent": "mean_exposure_pct"}


def scenarios():
    yield local.synthetic_rows()
    rows = local.synthetic_rows()
    for index in range(local.WARMUP, len(rows)):
        opening = 100 + index % 17
        close = opening + (index % 7 - 3)
        rows[index][1:] = [str(opening), str(max(opening, close) + 1),
                           str(min(opening, close) - 1), str(close)]
    rows[local.WARMUP + 8][1:] = ["110", "110", "40", "40"]
    yield rows


def compare(reference):
    if hashlib.sha256(reference.read_bytes()).hexdigest() != ARCHITECT_SHA256:
        raise ValueError("Architect source must match the published 0646933 digest")
    maxima = {}
    with localcontext() as ctx:
        ctx.prec = 34
        upstream = runpy.run_path(str(reference), run_name="frozen_architect_fixture")
        for rows in scenarios():
            source = upstream["prices"](rows)
            ours = local.fixed_bars(rows)
            for index in range(local.WARMUP, len(ours)):
                if local.signals(ours, index) != upstream["signals"](source, index):
                    raise AssertionError(f"signal mismatch at {index}")
            result = local.evaluate_fixture(rows)
            for cost, arms in result["arms"].items():
                for name, actual in arms.items():
                    expected = upstream["evaluate"](source, ARMS[name], *local.COSTS[cost])
                    for new, old in METRICS.items():
                        difference = abs(actual[new] - expected[old])
                        maxima[new] = max(maxima.get(new, Decimal(0)), difference)
                        if difference > TOLERANCE:
                            raise AssertionError(f"{cost}/{name}/{new}: difference {difference}")
                    if (len(actual["fills"]) != expected["fills"] or
                            actual["days_at_least_50_percent"] != expected["at_least_50_pct_modeled_days"] or
                            ("daily_loss" in actual["locks"]) != expected["daily_lock"] or
                            ("drawdown" in actual["locks"]) != expected["drawdown_lock"] or
                            len(actual["daily_outcomes"]) != len(expected["complete_day_returns"])):
                        raise AssertionError(f"{cost}/{name}: fill, lock or coverage mismatch")
                    for day, other in zip(actual["daily_outcomes"], expected["complete_day_returns"]):
                        if (local.stamp(day["start"]*local.NANO)[:10] != other["day_utc"] or
                                abs(day["net_usd"] - other["net_usd"]) > TOLERANCE or
                                abs(day["net_percent"] - other["net_pct"]) > TOLERANCE):
                            raise AssertionError(f"{cost}/{name}: UTC-day parity mismatch")
    return {"status": "PASS", "scope": "SYNTHETIC_FIXTURES_ONLY", "fixtures": 2,
            "account_comparisons": 16, "day_comparisons": 336,
            "tolerance": TOLERANCE, "max_absolute_differences": maxima}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("architect_source", type=Path)
    args = parser.parse_args()
    print(dump(compare(args.architect_source)))


if __name__ == "__main__":
    main()
