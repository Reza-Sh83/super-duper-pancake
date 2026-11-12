"""Read-only exploratory report projection; never trades or sends notifications.

Inputs are normalized committed snapshots, not operational acceptance receipts.
The capture-to-snapshot adapter and independent review remain separate gates.
"""
import argparse
from decimal import localcontext
from pathlib import Path

from .data import D, DAY, NANO, dump, load, parse_time, sha, stamp

HOUR = 3600 * NANO


def exact(value):
    if not isinstance(value, str):
        raise ValueError("decimal input must be a string")
    result = D(value)
    if not result.is_finite():
        raise ValueError("decimal input must be finite")
    return result


def boundary(snapshot, cutoff, fee):
    """Select only committed information available strictly before cutoff."""
    if snapshot is None:
        return {"nav": None, "reason": "BOUNDARY_MISSING", "mark_age_ms": None}
    if snapshot["utc"] >= cutoff or snapshot["received_utc"] >= cutoff:
        return {"nav": None, "reason": "AFTER_CUTOFF", "mark_age_ms": None}
    cash, btc = exact(snapshot["cash"]), exact(snapshot["btc"])
    result = {"cash": cash, "btc": btc, "nav": None, "reason": None,
              "mark_utc": snapshot.get("mark_utc"), "mark_age_ms": None,
              "last_observed_nav": snapshot.get("last_observed_nav"),
              "frame": snapshot["frame"], "exit_reserve_usd": None}
    if not snapshot["journal_reconciled"]:
        result["reason"] = "JOURNAL_INVALID"
    elif btc == 0:
        result.update(nav=cash, exit_reserve_usd=D(0))
    elif not snapshot["clock_valid"]:
        result["reason"] = "CLOCK_INVALID"
    elif not snapshot.get("mark_utc") or not snapshot.get("bid"):
        result["reason"] = "BOOK_MISSING"
    elif snapshot.get("mark_received_utc", cutoff) >= cutoff:
        result["reason"] = "AFTER_CUTOFF"
    else:
        age = D(cutoff-snapshot["mark_utc"]) / 1000000
        result["mark_age_ms"] = age
        if not snapshot["book_valid"]:
            result["reason"] = "BOOK_INVALID"
        elif age > 2000:
            result["reason"] = "BOOK_STALE"
        elif age < -500:
            result["reason"] = "BOOK_FUTURE"
        else:
            bid = exact(snapshot["bid"])
            if bid <= 0 or btc < 0:
                raise ValueError("invalid spot position or bid")
            reserve = btc*bid*fee
            result.update(nav=cash+btc*bid-reserve, exit_reserve_usd=reserve)
    return result


def change(start, end):
    if start is None or end is None or start <= 0:
        return {"usd": None, "percent": None, "reason": "BOUNDARY_UNAVAILABLE"}
    return {"usd": end-start, "percent": 100*(end/start-1), "reason": None}


def project(source, generated_at):
    with localcontext() as context:
        context.prec = 34
        return _project(source, generated_at)


def _project(s, generated_at):
    if s["schema_version"] != "pilot-snapshot-v1":
        raise ValueError("unsupported snapshot schema")
    if s["mode"] not in ("fixture", "dry_run"):
        raise ValueError("operational adapter not yet reviewed; fixture/dry_run only")
    t0, a, b = (s[key] for key in ("pilot_start", "interval_start", "interval_end"))
    if not all(isinstance(v, int) and not isinstance(v, bool) for v in (t0,a,b,generated_at)):
        raise ValueError("timestamps must be integer nanoseconds")
    if not t0 <= a < b <= t0+168*HOUR or generated_at < b:
        raise ValueError("invalid exploratory interval or generation time")
    if s["kind"] == "six_hour":
        if b-a != 6*HOUR or (a-t0) % (6*HOUR):
            raise ValueError("six-hour interval must align with pilot start")
    elif s["kind"] == "utc_day":
        if b-a != DAY*NANO or a % (DAY*NANO):
            raise ValueError("complete UTC day required")
    else:
        raise ValueError("unknown interval kind")
    if s["scenario"] not in ("base", "stress") or s["policy"] not in (
            "daily-sma50-v1", "hold-v1", "observe"):
        raise ValueError("unknown report arm")
    fee = D(".008") if s["scenario"] == "base" else D(".01")
    if type(s["revision"]) is not int or s["revision"] < 0:
        raise ValueError("invalid revision")
    snapshots = s["snapshots"]
    if len({x["frame"] for x in snapshots}) != len(snapshots):
        raise ValueError("duplicate snapshot frame")
    if any(x["frame"] < 1 for x in snapshots):
        raise ValueError("invalid committed frame")
    def at(cutoff):
        candidates = [x for x in snapshots if x["utc"] < cutoff and x["received_utc"] < cutoff]
        last = max(candidates,key=lambda x:x["frame"],default=None)
        return boundary(last,cutoff,fee)
    opening, closing, initial = at(a), at(b), at(t0)
    net = change(opening["nav"],closing["nav"])
    inception = change(initial["nav"],closing["nav"])
    expected = (b-a)//NANO
    ready, nonready, missing = (s["coverage"][k] for k in ("ready", "nonready", "missing"))
    if any(type(v) is not int or v < 0 for v in (ready,nonready,missing)) or ready+nonready+missing != expected:
        raise ValueError("coverage must include every planned second")
    coverage = {"ready":ready,"nonready":nonready,"missing":missing,"expected":expected,
                "ready_percent":100*D(ready)/expected,"degraded":ready < D(".99")*expected}
    paid = D(0)
    for fill in s["fills"]:
        if a <= fill["utc"] < b and fill["received_utc"] < b:
            if fill["frame"] > s["committed_frame"]:
                raise ValueError("uncommitted fill")
            amount = exact(fill["fee_usd"])
            if amount < 0:
                raise ValueError("negative fee")
            paid += amount
    if any(x["frame"] > s["committed_frame"] for x in snapshots):
        raise ValueError("uncommitted snapshot")
    # Observe marks individually. Never carry a stale value through a gap.
    peak = exact(s["opening_peak"])
    maximum = D(0)
    for snapshot in sorted(snapshots,key=lambda x:x["frame"]):
        if a <= snapshot["utc"] < b and snapshot["received_utc"] < b:
            marked = boundary(snapshot,snapshot["utc"]+1,fee)
            if marked["nav"] is not None:
                peak = max(peak,marked["nav"])
                if peak > 0:
                    maximum = max(maximum,100*(1-marked["nav"]/peak))
    # Completeness is a review gate, not an inference from a high displayed return.
    reasons = []
    if s["kind"] != "utc_day": reasons.append("NOT_FULL_UTC_DAY")
    if net["percent"] is None or net["percent"] < 50: reasons.append("THRESHOLD_NOT_MET")
    if missing or s["unresolved_gaps"] or coverage["degraded"]: reasons.append("COVERAGE_UNRESOLVED")
    if s["integrity"] != "PASS": reasons.append("INTEGRITY_UNVERIFIED")
    if s["replay"] != "PASS": reasons.append("REPLAY_UNVERIFIED")
    if s["risk_violations"]: reasons.append("RISK_VIOLATION")
    if s["policy"] != "daily-sma50-v1" or s["scenario"] != "base": reasons.append("NOT_PRIMARY_ARM")
    if not all(x.get("clock_valid",False) for x in snapshots if a <= x["utc"] < b):
        reasons.append("CLOCK_INVALID")
    identity = [s["run_id"],s["policy"],s["scenario"],a,b,s["revision"]]
    if s["revision"] != 0 and not (s.get("correction_reason") and s.get("audit_link")):
        raise ValueError("correction requires reason and audit link")
    return {"schema_version":"pilot-report-v1","report_id":sha(dump(identity).encode()),
            "identity":identity,"source_sha256":sha(dump(s).encode()),"code_hashes":s["code_hashes"],
            "config_hash":s["config_hash"],"manifest_hash":s["manifest_hash"],"fee_rate":fee,"cutoff":stamp(b),"generated_at":stamp(generated_at),
            "delayed":generated_at > b,"interval_start":stamp(a),"start":opening,"end":closing,
            "interval_net":net,"inception_net":inception,"paid_fees_usd":paid,
            "coverage":coverage,"peak_usd":peak,"observed_max_drawdown_percent":maximum,
            "drawdown_current":"UNKNOWN" if closing["nav"] is None else "OBSERVED",
            "locks":s["locks"],"dust":s["dust"],"decisions":s["decisions"],
            "reconciliation":s["reconciliation"],"paired_baselines":s["paired_baselines"],
            "completed_work":s["completed_work"],"elapsed_hours":D(b-t0)/HOUR,
            "pilot_hours":168,"report_index":(b-t0)//(6*HOUR) if s["kind"]=="six_hour" else None,
            "report_count":28,"integrity":s["integrity"],"replay":s["replay"],
            "review":"PENDING","operational_ready":False,"candidate_status":"candidate_pending_review" if not reasons else "INELIGIBLE",
            "candidate_reasons":reasons,"real_alert_sent":False,"mode":s["mode"],
            "delivery_status":"NOT_ATTEMPTED","next_action":"Independent review; no automatic delivery"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = project(load(args.snapshot.read_bytes()),parse_time(args.generated_at))
    # Exclusive creation: never silently replace a prior report or delivery receipt.
    with args.out.open("x",encoding="utf-8") as output:
        output.write(dump(result)+"\n")


if __name__ == "__main__":
    main()
