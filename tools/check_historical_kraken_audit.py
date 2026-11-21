"""Test the artifact auditor against the pinned evaluator on synthetic bars."""

from copy import deepcopy
import hashlib
from pathlib import Path
import runpy
import sys
from unittest.mock import patch

import tools.audit_historical_kraken as audit


def main():
    reference = Path(sys.argv[1])
    assert hashlib.sha256(reference.read_bytes()).hexdigest() == "24944c5935d438d143c1912bc342e594e17ac12ad67c1e08ceb64d145d974df7"
    source = runpy.run_path(str(reference))
    for window in audit.WINDOWS:
        start, stop = map(audit.utc_bound, audit.WINDOWS[window])
        rows = []
        for i, t in enumerate(range(start - 26 * audit.HOUR, stop, audit.HOUR)):
            p = 100 + i % 41 if i < 55 else 60 + i % 31
            rows.append([t, str(p), str(p + 1), str(p - 3), str(p + 1)])
        response = {"error": [], "result": {"XXBTZUSD": rows + [[stop]], "last": stop}}
        bars = source["prices"](rows, start, stop)
        accounts, marks = {}, {}
        sample = source["Account"].sample
        for cost, values in audit.COSTS.items():
            def collect(account, price, day_open):
                nav = sample(account, price, day_open)
                marks[cost].append(str(nav))
                return nav
            marks[cost] = []
            with patch.object(source["Account"], "sample", collect):
                breakout = source["evaluate"](bars, "breakout", *values, start)
            accounts[cost] = {arm: source["evaluate"](bars, arm, *values, start)
                              for arm in audit.ARMS - {"breakout"}}
            accounts[cost]["breakout"] = breakout
            assert breakout["fills"] > 0
        result = audit.audit(response, accounts, window, marks)
        assert set(result["breakout_drawdown"].values()) == {"NAV_PATH_RECONCILED"}
        assert set(audit.audit(response, accounts, window)["breakout_drawdown"].values()) == {
            "BOUNDS_ONLY_PATH_UNAVAILABLE"}
        for target in ("gap", "unclosed", "fee", "hold", "cash", "marks"):
            r, a, m = map(deepcopy, (response, accounts, marks))
            if target == "gap":
                del r["result"]["XXBTZUSD"][27]
            elif target == "unclosed":
                r["result"]["XXBTZUSD"][-1] = [stop - audit.HOUR]
            elif target == "fee":
                a["base"]["breakout"]["paid_fees_usd"] = "0"
            elif target == "hold":
                a["stress"]["hold_small"]["sampled_max_drawdown_pct"] = "100"
            elif target == "cash":
                a["base"]["cash"]["fills"] = 1
            else:
                m["stress"][20] = "1"
            try:
                audit.audit(r, a, window, m)
            except ValueError:
                pass
            else:
                raise AssertionError(target)
        print(window, result["evaluation_hours"], "hours: eight accounts, drawdown paths and six refusals PASS")


if __name__ == "__main__":
    main()
