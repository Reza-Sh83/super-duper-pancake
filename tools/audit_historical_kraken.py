"""Check an existing hourly Kraken result and its retained response offline."""

import argparse
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import hashlib
import json
from pathlib import Path

D = Decimal
HOUR = 3600
DAY = 24 * HOUR
INITIAL = D(10000)
COSTS = {"base": (D(".008"), D(0)), "stress": (D(".01"), D(".001"))}
BUDGETS = {"hold_small": D(250), "hold_full": INITIAL}
ARMS = {"breakout", "cash", *BUDGETS}
WINDOWS = {"architect": ("2026-11-18", "2026-11-21"),
           "manager": ("2026-11-01", "2026-11-20")}
TOLERANCE = D("1e-24")


def require(condition, message):
    if not condition:
        raise ValueError(message)


def decimal(value):
    require(type(value) in (str, int, Decimal), "expected exact decimal input")
    parsed = D(value)
    require(parsed.is_finite(), "nonfinite numeric input")
    return parsed


def utc_bound(day):
    return int(datetime.fromisoformat(day).replace(tzinfo=timezone.utc).timestamp())


def closed_window(response, start, stop):
    require(response["error"] == [], "Kraken API error")
    pairs = response["result"]
    require(set(pairs) - {"last"} == {"XXBTZUSD"}, "unexpected Kraken pair")
    source = pairs["XXBTZUSD"]
    require(isinstance(source, list) and len(source) >= 2, "missing OHLC rows")
    require(type(source[-1][0]) is int and source[-1][0] >= stop
            and source[-1][0] % HOUR == 0, "cutoff reaches uncommitted candle")
    rows = [row for row in source[:-1] if start - 26 * HOUR <= row[0] < stop]
    require(all(type(row[0]) is int for row in rows)
            and [row[0] for row in rows] == list(range(start - 26 * HOUR, stop, HOUR)),
            "missing, duplicate, unordered or off-grid evaluation/warm-up bars")
    prices = []
    for row in rows:
        opening, high, low, close = map(decimal, row[1:5])
        require(0 < low <= min(opening, close) <= max(opening, close) <= high,
                "invalid OHLC")
        prices.append((opening, close))
    return rows[26:], prices[26:]


def close_to(value, expected, label):
    require(abs(value - expected) <= TOLERANCE, f"{label} mismatch")


def drawdown(marks):
    peak = INITIAL
    maximum = D(0)
    for mark in marks:
        peak = max(peak, mark)
        maximum = max(maximum, (peak - mark) / peak * 100)
    return maximum


def audit(response, accounts, window, breakout_marks=None):
    start, stop = map(utc_bound, WINDOWS[window])
    rows, prices = closed_window(response, start, stop)
    days = range(start, stop, DAY)
    day_labels = [datetime.fromtimestamp(t, timezone.utc).date().isoformat() for t in days]
    require(set(accounts) == set(COSTS), "cost scenarios mismatch")
    breakout_drawdown = {}
    with localcontext() as ctx:
        ctx.prec = 48
        for cost, (fee, slip) in COSTS.items():
            require(set(accounts[cost]) == ARMS, "account set mismatch")
            for arm, result in accounts[cost].items():
                label = f"{cost}/{arm}"
                net, pct, paid, turnover, reserve, dd = map(decimal, (result[field] for field in (
                    "net_usd", "net_pct", "paid_fees_usd", "turnover_usd", "exit_reserve_usd",
                    "sampled_max_drawdown_pct")))
                require(result["coverage_hours"] == len(rows), f"{label} coverage mismatch")
                require([day["day_utc"] for day in result["complete_day_returns"]] == day_labels,
                        f"{label} UTC days mismatch")
                close_to(pct, net / INITIAL * 100, f"{label} net percent")
                close_to(paid, turnover * fee, f"{label} paid fees")
                require(0 <= min(turnover, paid, reserve) and max(0, -pct) - TOLERANCE <= dd <= 100,
                        f"{label} invalid metrics")
                fills = result["fills"]
                require(type(fills) is int and fills >= 0, f"{label} invalid fills")
                if arm in BUDGETS:
                    budget = BUDGETS[arm]
                    qty = budget / (prices[0][0] * (1 + slip) * (1 + fee))
                    mark_factor = (1 - slip) * (1 - fee)
                    marks = [INITIAL - budget + qty * price * mark_factor
                             for pair in prices for price in pair]
                    close_to(turnover, budget / (1 + fee), f"{label} hold turnover")
                    close_to(reserve, qty * prices[-1][1] * (1 - mark_factor), f"{label} hold reserve")
                    close_to(net, marks[-1] - INITIAL, f"{label} hold net USD")
                    close_to(dd, drawdown(marks), f"{label} hold drawdown")
                    require(fills == 1, f"{label} expected one hold fill")
                if arm == "cash" or (arm == "breakout" and fills == 0):
                    require((net, pct, paid, turnover, reserve, dd, fills) == (0,) * 7,
                            f"{label} flat account mismatch")
                if arm == "breakout":
                    status = "FLAT_RECONCILED" if not fills else "BOUNDS_ONLY_PATH_UNAVAILABLE"
                    if breakout_marks is not None and fills:
                        path = list(map(decimal, breakout_marks[cost]))
                        require(len(path) == 3 * len(rows) and min(path) > 0,
                                f"{label} invalid NAV sample coverage")
                        close_to(path[-1], INITIAL + net, f"{label} final NAV")
                        close_to(dd, drawdown(path), f"{label} sampled drawdown")
                        status = "NAV_PATH_RECONCILED"
                    breakout_drawdown[cost] = status
    # Match Capture's compact JSON plus final newline for the selected evaluation rows.
    canonical = (json.dumps(rows, separators=(",", ":"), ensure_ascii=True) + "\n").encode()
    return {"scope": "EXPLORATORY_BAR_ESTIMATES_ONLY", "window": window,
            "evaluation_hours": len(rows), "warmup_hours": 26, "utc_days": len(days),
            "closed_evaluation_sha256": hashlib.sha256(canonical).hexdigest(),
            "accounts_checked": 8, "hold_drawdown": "RECONCILED_FROM_BARS",
            "breakout_drawdown": breakout_drawdown}


def load(path):
    return json.loads(path.read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("window", choices=WINDOWS)
    parser.add_argument("kraken_response", type=Path)
    parser.add_argument("original_sha256", help="SHA-256 from the original private response receipt")
    parser.add_argument("existing_results", type=Path, help="Existing JSON containing the accounts object")
    parser.add_argument("--breakout-marks", type=Path, help="Optional original ordered sample arrays by cost")
    args = parser.parse_args()
    payload = args.kraken_response.read_bytes()
    require(hashlib.sha256(payload).hexdigest() == args.original_sha256,
            "retained response does not match the original receipt")
    existing = load(args.existing_results)
    marks = load(args.breakout_marks) if args.breakout_marks else None
    print(json.dumps(audit(json.loads(payload), existing["accounts"], args.window, marks),
                     sort_keys=True))


if __name__ == "__main__":
    main()
