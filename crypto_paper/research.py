"""Locked crypto-v1 protocol. Performance is projected only after the window closes."""
import random
import time
from contextlib import ExitStack
from pathlib import Path

from .data import D, DAY, NANO, dump, load, parse_time, stamp
from .engine import Ledger
from .runtime import Session, accepted_reports, check, code_hashes, digest_file, frames, report, verified_parts, versions, write_json

POLICIES = ("daily-sma50-v1", "hold-v1", "observe")
REQUIRED = {"D01","D02","T01","T02","X01","X02","R01","R02","O01","P01"}
DAYS = 180
SAMPLES = 20000
SEED = 20261107


def circular(differences, length, samples=SAMPLES):
    n = len(differences[0])
    rng = random.Random(SEED)
    columns = [[] for _ in differences]
    # Integer offsets retain calendar positions, including unavailable days.
    blocks = []
    for values in differences:
        doubled = values + values
        sums, counts = [D(0)], [0]
        for value in doubled:
            sums.append(sums[-1] + (value if value is not None else D(0)))
            counts.append(counts[-1] + (value is not None))
        blocks.append((sums, counts))
    sizes = [min(length,n-start) for start in range(0,n,length)]
    for _ in range(samples):
        indices = [rng.randrange(n) for size in sizes]
        for (sums,counts), column in zip(blocks,columns):
            available = sum(counts[i+size]-counts[i] for i,size in zip(indices,sizes))
            if not available:
                raise ValueError("bootstrap resample has no paired observations")
            total = sum(sums[i+size]-sums[i] for i,size in zip(indices,sizes))
            column.append(total/available)
    rank = (samples+79)//80-1
    return [sorted(column)[rank] for column in columns]


def daily_returns(navs):
    previous = D(10000)
    result = []
    for value in navs:
        result.append(value/previous-1 if value is not None and previous else None)
        previous = value
    return result


def development(out):
    from .runtime import Capture
    from .verify import META, UTC, market
    baseline = out / "fixture"
    baseline.mkdir()
    cap = Capture(baseline,"research-development")
    end = UTC//(DAY*NANO)*DAY
    moment = end*NANO+2*NANO
    rows = [[end-(50-i)*DAY,"100","110","90","100" if i < 49 else "101","100","1",1]
            for i in range(50)] + [[end,"100","110","90","100","100","1",1]]
    candle = {"error":[],"result":{"XXBTZUSD":rows}}
    with ExitStack() as stack:
        arms = {}
        for cost in ("base","stress"):
            for policy in POLICIES:
                ledger = Ledger(out/f"{cost}-{policy}.sqlite3")
                arm = Session(None,"research-development",policy,ledger=ledger,stress=cost=="stress")
                stack.callback(arm.close)
                arms[cost,policy] = arm
        stack.callback(cap.close)

        def event(kind, value=None, delay=0, **fields):
            frame = cap.put(kind,dump(value).encode() if value else b"",epoch=1,
                            utc=moment+delay,mono=delay,**fields)
            for arm in arms.values():
                arm.handle(frame)

        event("clock",offset_ms=["0","0","0"])
        event("connect")
        event("ws",{"channel":"instrument","data":{"pairs":[META | {"symbol":"BTC/USD"}]}})
        event("ws",market(utc=moment,asks={"100":"10"}))
        event("ohlc",candle,interval=1440,end=end,pair="XXBTZUSD")
        update = market(utc=moment+NANO,asks={"100":"10"})
        update["type"] = "update"
        event("ws",update,delay=NANO)
        targets, positions = {}, {}
        for (cost,policy),arm in arms.items():
            key = f"{cost}/{policy}"
            targets[key] = arm.boundaries.get((1440,end))
            positions[key] = arm.engine.val("btc")
        if not (all(targets.values()) and
                positions["base/observe"] == positions["stress/observe"] == 0 and
                positions["base/daily-sma50-v1"] == positions["base/hold-v1"] > 0 and
                positions["stress/daily-sma50-v1"] == positions["stress/hold-v1"] > 0 and
                circular([[D(1)]*180]*4,14,80) == [D(1)]*4):
            raise ValueError("research fixture mismatch")
    return {"scope":"development fixture", "positions":positions,
            "independent_ledgers":6, "synthetic_input":"fixture/raw/000001.jsonl"}


def evidence(out):
    # Contract command uses runs/F. Acceptance reports are sibling phase outputs.
    paths = [out.parent/phase/"report.json" for phase in ("A","B","C","D-replay","E")]
    approved, hashes = accepted_reports(paths)
    return REQUIRED-approved, hashes


def freeze(out, started):
    missing, hashes = evidence(out)
    if missing:
        return check("P02","BLOCKED","accepted operational and development gates",
                     {"missing":sorted(missing)}), hashes
    start = started//(DAY*NANO)+1
    value = {"schema_version":1,"protocol":"crypto-v1","code_hashes":code_hashes(),
             "versions":versions(),"locked_utc":stamp(started),"start_day":start,
             "end_day":start+DAYS,"start_utc":stamp(start*DAY*NANO),"end_utc":stamp((start+DAYS)*DAY*NANO),
             "source":"Kraken Spot BTC/USD native public capture, depth 10",
             "captures":"captures/*/manifest.json","fees":["0.008","0.01"],
             "latency_ms":[250,1000],"stress_slippage":"0.001","policies":POLICIES,
             "bootstrap":{"lengths":[14,7,28],"replications":SAMPLES,"seed":SEED,"percentile":"0.0125"},
             "coverage":{"nav_days":175,"sma_decisions":170,"nonzero_pairs":30,"ready_fraction":"0.99"},
             "acceptance_hashes":hashes}
    write_json(out/"manifest.json",value)
    digest = digest_file(out/"manifest.json")
    write_json(out/"lock.json",{"manifest_sha256":digest,"locked_utc":value["locked_utc"]})
    return check("P02","BLOCKED","end of locked 180 UTC days and coverage",
                 {"state":"LOCKED","start_utc":value["start_utc"],"end_utc":value["end_utc"]}), hashes


def project(source, capture_paths, out):
    start, end = source["start_day"], source["end_day"]
    sessions = {}
    daily_nav = {}
    samples = {}
    idx = epoch_offset = 0
    last_utc = None
    locked_utc = parse_time(source["locked_utc"])
    with ExitStack() as stack:
        for cost in ("base","stress"):
            for policy in POLICIES:
                key = (cost,policy)
                ledger = Ledger(out/f"{cost}-{policy}.sqlite3")
                s = Session(None,"crypto-v1",policy,ledger=ledger,stress=cost=="stress",stats=False)
                stack.callback(s.close)
                sessions[key] = s
                daily_nav[key] = {}

        for capture_path in capture_paths:
            info, parts = verified_parts(capture_path)
            if info["policy"] != "observe" or parse_time(info["started_utc"]) < locked_utc:
                raise ValueError("confirmatory capture must use observe")
            for original in frames(capture_path.parent,parts):
                utc = original["utc"]
                if original["capture_id"] != info["run_id"]:
                    raise ValueError("capture identity mismatch")
                if last_utc is not None and utc < last_utc:
                    raise ValueError("overlapping or regressing confirmatory capture")
                day = utc//(DAY*NANO)
                if day >= end:
                    break
                last_utc = utc
                idx += 1
                frame = original | {"idx":idx,"connection_epoch":original["connection_epoch"]+epoch_offset}
                if frame["kind"] == "ohlc" and frame.get("end") is not None:
                    if frame["end"]//DAY < start or frame.get("interval") != 1440:
                        frame["end"] = None
                if frame["kind"] == "deadline" and (frame["end"]//DAY < start or frame["interval"] != 1440):
                    frame["kind"] = "ignored"
                if frame["kind"] == "operator":
                    raise ValueError("operator control in confirmatory source")
                for key,s in sessions.items():
                    s.handle(frame)
                    if start <= day and (day+1)*DAY*NANO-utc <= 2*NANO:
                        day_end = (day+1)*DAY*NANO
                        mark = s.engine.s["mark_ns"]
                        if (s.ready(frame) and s.book.fresh(day_end) and mark is not None
                                and mark < day_end and day_end-mark <= 2*NANO):
                            daily_nav[key][day] = s.engine.val("nav")
                        else:
                            daily_nav[key].pop(day,None)
                if start <= day and frame["kind"] == "sample":
                    sec = utc//NANO
                    count,last_sec = samples.get(day,(0,None))
                    if (sec != last_sec and frame["mono"]-frame.get("scheduled_mono",frame["mono"]) < NANO
                            and next(iter(sessions.values())).ready(frame)):
                        samples[day] = count+1,sec
            epoch_offset = max(s.book.epoch for s in sessions.values())

        valid = {day for day, (count,_) in samples.items() if count >= DAY*.99}
        navs = {key:[values.get(day) if day in valid else None for day in range(start,end)]
                for key,values in daily_nav.items()}
        decisions = min(sum(ok and interval == 1440 and e//DAY in valid
                            for (interval,e),ok in s.boundaries.items())
                        for (cost,policy),s in sessions.items() if policy == POLICIES[0])
        drawdown = {}
        for cost in ("base","stress"):
            peak = D(10000)
            worst = D(0)
            for _,_,kind,payload in sessions[cost,POLICIES[0]].ledger.sequence():
                if kind == "state":
                    nav = D(load(payload)["nav"])
                    peak = max(peak,nav)
                    worst = max(worst,1-nav/peak)
            drawdown[cost] = worst
        coverage = {"valid_days":len(valid),"sma_decisions":decisions,
                    "nav_days":{"/".join(key):sum(v is not None for v in seq) for key,seq in navs.items()}}
        if min(coverage["nav_days"].values()) < 175 or decisions < 170:
            return "BLOCKED", {"coverage":coverage}
        returns = {key:daily_returns(values) for key,values in navs.items()}
        comparisons = [[a-b if a is not None and b is not None else None
                        for a,b in zip(returns[cost,POLICIES[0]],returns[cost,baseline])]
                       for cost in ("base","stress") for baseline in POLICIES[1:]]
        counts = [sum(v is not None and v != 0 for v in values) for values in comparisons]
        if min(counts) < 30:
            return "BLOCKED",{"coverage":coverage,"nonzero_pairs":counts}
        lower = {str(length):circular(comparisons,length) for length in (14,7,28)}
        passed = all(bound > 0 for bounds in lower.values() for bound in bounds)
        return ("PASS" if passed and max(drawdown.values()) <= D(".04") else "FAIL",
                {"coverage":coverage,"nonzero_pairs":counts,"lower_bounds":lower,"drawdown":drawdown})


def research(args, started):
    if args.stage == "unseal" and not args.manifest:
        raise ValueError("--manifest required for unseal")
    out = args.out or (args.manifest.parent / "unsealed" if args.manifest else None)
    if out is None:
        raise ValueError("--out required")
    hashes = {}
    if args.stage != "unseal":
        out.mkdir(parents=True,exist_ok=False)
    if args.stage == "development":
        try:
            result = check("P01","PASS","three policies on common fixture at both costs",development(out))
        except (OSError,ValueError) as exc:
            result = check("P01","FAIL","three policies on common fixture at both costs",str(exc))
    elif args.stage == "freeze":
        result, hashes = freeze(out,started)
    else:
        from .__main__ import writer
        parent = args.manifest.parent
        with writer(parent):
            source = load(args.manifest.read_bytes())
            locked = load((parent/"lock.json").read_bytes())
            digest = digest_file(args.manifest)
            hashes = {"lock":digest}
            if (locked["manifest_sha256"] != digest or source["code_hashes"] != code_hashes() or
                    source["versions"] != versions()):
                raise ValueError("locked research inputs changed")
            expected = "one-time evaluation after 180 UTC days"
            if started < source["end_day"]*DAY*NANO:
                result = check("P02","BLOCKED",expected,"window still locked")
                # Leave the canonical one-time output path untouched before the deadline.
                out = parent / "unseal-blocked"
            else:
                audit = parent/"unseal-audit.json"
                if audit.exists():
                    raise ValueError("unseal already attempted")
                captures = sorted((parent/"captures").glob("*/manifest.json"),
                                  key=lambda p:load(p.read_bytes())["started_utc"])
                if not captures:
                    result = check("P02","BLOCKED",expected,"no locked capture")
                else:
                    out.mkdir(parents=True,exist_ok=False)
                    hashes.update({str(p):digest_file(p) for p in captures})
                    write_json(audit,{"started_utc":stamp(started),"input_hashes":hashes})
                    try:
                        status, observed = project(source,captures,out)
                    except (OSError,ValueError,KeyError) as exc:
                        status, observed = "BLOCKED",str(exc)
                    result = check("P02",status,expected,observed)
    return report(out/"report.json","crypto-v1", [result],started,hashes)
