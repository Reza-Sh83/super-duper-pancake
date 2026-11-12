"""Public paper-trading CLI."""
import argparse
import asyncio
import os
import sqlite3
import time
import uuid
from contextlib import contextmanager
from pathlib import Path

from .data import NANO, dump, load, parse_time, stamp
from .engine import Ledger
from .live import host_checks, live, preflight
from .runtime import (Capture, Session, accepted_reports, check, code_hashes, compare, digest_file, frames, manifest,
                      report, verified_parts, versions, write_json)
from .verify import run_suite


def unique(out):
    out.mkdir(parents=True, exist_ok=False)


@contextmanager
def writer(out):
    with (out / ".writer.lock").open("a+b") as lock:
        lock.seek(0)
        if lock.read(1) == b"":
            lock.write(b"0")
            lock.flush()
        lock.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        yield


def paper_gate(session, host):
    counts = dict(session.ledger.db.execute("SELECT kind,count(*) FROM events GROUP BY kind"))
    directions = set()
    for _, _, kind, payload in session.ledger.sequence():
        if kind == "intent":
            target = load(payload)["target"]
            directions.add("entry" if target != "0" else "exit")
    status = ("BLOCKED" if host["status"] != "PASS" else
              "PASS" if directions == {"entry","exit"} and counts.get("fill",0) else "FAIL")
    return check("paper_live", status, "T01, entry + exit intent, at least one valid fill",
                 {"host":host["status"],"directions":sorted(directions),"events":counts})


def reconstruct(out, info):
    rebuilt = Session(None, info["run_id"], info["policy"], ledger=Ledger(":memory:"))
    for frame in frames(out):
        if frame["capture_id"] != info["run_id"]:
            raise ValueError("capture identity mismatch")
        rebuilt.handle(frame)
    return rebuilt


def resume_session(out, info):
    rebuilt = reconstruct(out, info)
    saved = Ledger(out / "ledger.sqlite3")
    try:
        cursor, = saved.db.execute("SELECT coalesce(max(idx),0) FROM frames").fetchone()
        if cursor > (rebuilt.last["idx"] if rebuilt.last else 0):
            raise ValueError("ledger extends beyond raw capture")
        expected = (event for event in rebuilt.ledger.sequence() if event[1] <= cursor)
        from itertools import zip_longest
        if not saved.reconcile() or any(a != b for a,b in zip_longest(saved.sequence(), expected)):
            raise ValueError("persisted ledger does not reconcile with capture")
        if rebuilt.last and cursor < rebuilt.last["idx"]:
            # Reconciled prefix is preserved. Import only committed, deterministic suffix effects.
            for frame_id, digest in rebuilt.ledger.db.execute("SELECT idx,digest FROM frames WHERE idx>? ORDER BY idx",(cursor,)):
                with saved.transaction(frame_id,digest):
                    events = rebuilt.ledger.db.execute(
                        "SELECT id,kind,payload FROM events WHERE frame=? ORDER BY seq", (frame_id,))
                    for identity, kind, data in events:
                        if kind == "state":
                            saved.state = load(data)
                        else:
                            saved.event(identity,kind,load(data))
            if not compare(saved, rebuilt.ledger)["equal"]:
                raise ValueError("restored financial effects differ")
    finally:
        saved.close()
    rebuilt.ledger.close()
    rebuilt.ledger = Ledger(out / "ledger.sqlite3")
    rebuilt.engine.ledger = rebuilt.ledger
    staged = out/"bars.rebuilt.tmp"
    with staged.open("w",encoding="utf-8") as stream:
        for version in rebuilt.bars.history:
            stream.write(dump(version)+"\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(staged,out/"bars.jsonl")
    rebuilt.bar_log = (out/"bars.jsonl").open("a",encoding="utf-8")
    return rebuilt


def collect(args):
    out = args.out
    started = time.time_ns()
    policy = getattr(args, "policy", "observe")
    if not args.resume:
        unique(out)
    with writer(out):
        if args.resume:
            info = load((out / "manifest.json").read_bytes())
            if info["policy"] != policy or info["code_hashes"] != code_hashes():
                raise ValueError("resume requires recorded policy and code")
            session = resume_session(out, info)
            run_id = info["run_id"]
        else:
            run_id = uuid.uuid4().hex
            session = Session(out, run_id, policy)
        cap = Capture(out, run_id, session.last["idx"] if session.last else 0)
        manifest(out, run_id, policy, started, state="COLLECTING", duration_sec=args.duration_sec,
                 force_reconnect_at_sec=args.force_reconnect_at_sec)
        status, reason = "BLOCKED", "interrupted"
        try:
            if args.resume:
                session.handle(cap.put("restart", epoch=session.book.epoch))
            problems = preflight(session, cap)
            if problems:
                status, reason = "BLOCKED", "; ".join(problems)
            else:
                status, reason = asyncio.run(live(session,cap,args.duration_sec,args.force_reconnect_at_sec))
        except KeyboardInterrupt:
            reason = "operator interrupted process"
        except Exception as exc:
            status, reason = "FAIL", repr(exc)
        finally:
            try:
                session.handle(cap.put("shutdown", reason=reason, epoch=session.book.epoch))
            except (OSError, ValueError) as exc:
                status, reason = "FAIL", f"shutdown capture: {exc}"
            cap.close()
            metrics = session.metrics()
            write_json(out / "metrics.json", metrics)
            host = host_checks(session, status, reason, args.duration_sec, args.force_reconnect_at_sec)
            if args.resume and host["status"] == "PASS":
                host = check("T01","BLOCKED","fresh uninterrupted acceptance run","resumed diagnostic")
            checks = [host]
            if args.command == "paper":
                checks += [paper_gate(session, host),
                           check("O01","BLOCKED","compare complete paper capture with replay","run replay")]
            session.close()
            info = manifest(out, run_id, policy, started, state=status, collection_reason=reason,
                            duration_sec=args.duration_sec, force_reconnect_at_sec=args.force_reconnect_at_sec,
                            host=host, paper=checks[1] if args.command == "paper" else None)
            return report(out/"report.json",run_id,checks,started,info["parts"])


def replay(args):
    started = time.time_ns()
    out = args.out
    unique(out)
    run_id = uuid.uuid4().hex
    hashes = {}
    try:
        info, parts = verified_parts(args.manifest)
        run_id, hashes = info["run_id"], info["parts"]
        rebuilt = Session(out, run_id, info["policy"])
        source_path = args.manifest.parent / "ledger.sqlite3"
        if info.get("ledger_sha256") != digest_file(source_path):
            rebuilt.close()
            raise ValueError("sealed source ledger hash mismatch")
        source = Ledger(source_path,readonly=True)
        try:
            for frame in frames(args.manifest.parent, parts):
                if frame["capture_id"] != run_id:
                    raise ValueError("capture identity mismatch")
                rebuilt.handle(frame)
            difference = compare(source, rebuilt.ledger)
            if not source.reconcile() or not rebuilt.ledger.reconcile():
                raise ValueError("ledger reconciliation failed")
        finally:
            source.close()
            rebuilt.close()
        phases = args.manifest.parent.parent
        accepted, receipt_hashes = accepted_reports(phases/phase/"report.json" for phase in ("A","B","C"))
        required = {"D01","D02","T01","T02","X01","X02","R01","R02"}
        missing = required-accepted
        hashes = hashes | receipt_hashes
        full = info.get("paper") and info["paper"]["status"] == "PASS" and not missing
        checks = [check("replay", "PASS" if difference["equal"] else "FAIL",
                        "identical ordered effects", difference)]
        checks.append(check("O01", "FAIL" if not difference["equal"] else "PASS" if full else "BLOCKED",
                            "24h paper, valid entry/exit and fill, exact replay",
                            difference if full else {"paper":info.get("paper"),"replay":difference,
                                                     "missing_prerequisites":sorted(missing)}))
        write_json(out/"comparison.json",difference)
    except (OSError, ValueError, KeyError, sqlite3.Error) as exc:
        checks = [check("O01","BLOCKED","valid capture and replay",str(exc))]
    return report(out/"report.json",run_id,checks,started,hashes)


def operator(args):
    out = args.run
    started = time.time_ns()
    info = load((out/"manifest.json").read_bytes())
    with writer(out):
        if info["code_hashes"] != code_hashes():
            raise ValueError("operator action requires recorded code")
        s = resume_session(out, info)
        cap = Capture(out, info["run_id"], s.last["idx"] if s.last else 0)
        try:
            if args.action != "stop":
                e = s.engine
                if args.action == "daily":
                    if e.s["daily"] is None or time.time_ns()//(86400*NANO) <= e.s["daily"]:
                        raise ValueError("daily lock requires next UTC day")
                elif not e.s[args.action]:
                    raise ValueError("lock is not active")
            if args.action == "daily":
                preflight(s,cap)
                if not s.clock:
                    raise ValueError("daily unlock requires independent UTC samples")
            s.handle(cap.put("operator", action=args.action, note=args.reason, epoch=s.book.epoch))
        finally:
            cap.close()
            s.close()
        info = manifest(out,info["run_id"],info["policy"],parse_time(info["started_utc"]),
                        state="OPERATOR",host=None,paper=None)
        return report(args.out,info["run_id"],
                      [check("operator","PASS","reconciled and audited",args.action)],started,info["parts"])


def main():
    parser = argparse.ArgumentParser(prog="python -m crypto_paper")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("capture","paper"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--duration-sec", type=int, required=True)
        cmd.add_argument("--force-reconnect-at-sec", type=int)
        cmd.add_argument("--out", type=Path, required=True)
        cmd.add_argument("--resume", action="store_true")
        if name == "paper":
            cmd.add_argument("--policy",choices=("observe","paper-alternating-v1"),default="observe")
    cmd = sub.add_parser("verify")
    cmd.add_argument("--suite", choices=("data","execution","candidate"),required=True)
    cmd.add_argument("--fixtures",type=Path,default=Path("fixtures/crypto"))
    cmd.add_argument("--candidate")
    cmd.add_argument("--manifest",type=Path)
    cmd.add_argument("--out",type=Path,required=True)
    cmd = sub.add_parser("replay")
    cmd.add_argument("--manifest",type=Path,required=True)
    cmd.add_argument("--out",type=Path,required=True)
    cmd = sub.add_parser("operator")
    cmd.add_argument("--run",type=Path,required=True)
    cmd.add_argument("--out",type=Path,required=True)
    cmd.add_argument("--action",choices=("stop","daily","drawdown","manual"),required=True)
    cmd.add_argument("--reason",required=True)
    cmd = sub.add_parser("research")
    cmd.add_argument("--protocol",choices=("crypto-v1",),required=True)
    cmd.add_argument("--stage",choices=("development","freeze","unseal"),required=True)
    cmd.add_argument("--manifest",type=Path)
    cmd.add_argument("--out",type=Path)
    args = parser.parse_args()
    started = time.time_ns()
    if args.command in ("capture","paper"):
        if args.duration_sec < 1 or (args.force_reconnect_at_sec is not None and
                not 0 <= args.force_reconnect_at_sec < args.duration_sec):
            parser.error("invalid duration or reconnect offset")
        return collect(args)
    if args.command == "replay":
        return replay(args)
    if args.command == "operator":
        if not args.reason.strip():
            parser.error("operator reason required")
        return operator(args)
    if args.command == "research":
        from .research import research
        return research(args, started)
    if args.suite == "candidate":
        checks = [check("M01","BLOCKED","pinned candidate and accepted O01 capture",
                        {"candidate":args.candidate,"reason":"candidate adapter and accepted capture unavailable"})]
        hashes = {}
    else:
        checks, hashes = run_suite(args.suite,args.fixtures)
    return report(args.out,uuid.uuid4().hex,checks,started,hashes)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, KeyError, sqlite3.Error) as exc:
        raise SystemExit(str(exc)) from exc
