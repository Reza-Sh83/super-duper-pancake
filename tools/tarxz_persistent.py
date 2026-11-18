"""Read-only checks for a follow-up to the bounded tar+xz proof."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess

from crypto_paper.capture_report import capture_report
from crypto_paper.engine import Ledger
from crypto_paper.data import dump
from crypto_paper.pilot_report import HOUR
from crypto_paper.runtime import digest_file
from tools.retention_proof import charge
from tools.tarxz_retention import PAGE, Refused, admit, inventory


def preflight(parent, working):
    parent = Path(parent).resolve(strict=True)
    filesystem = subprocess.check_output(["stat", "-f", "-c", "%T", parent], text=True).strip()
    if filesystem != "ext2/ext3" or subprocess.check_output(
            ["findmnt", "-n", "-o", "FSTYPE", "-T", parent], text=True).strip() != "ext4":
        raise Refused("persistent proof requires a verified direct ext4 mount")
    if os.statvfs(parent).f_frsize != PAGE:
        raise Refused("persistent proof requires 4 KiB allocation units")
    admit(charge(parent), shutil.disk_usage(parent).free, working)
    return parent


def readback(root, start, end):
    """Reopen a completed local proof in a fresh process without writing files."""
    if end - start != 6 * HOUR:
        raise ValueError("expected a six-hour report interval")
    root = Path(root)
    before = inventory(root)
    seal = json.loads((root / "shutdown.json").read_bytes())
    archive_hash = digest_file(root / "complete.tar.xz")
    if (seal.get("status") != "STOPPED" or seal.get("sqlite_commit") != "verified" or
            seal.get("archive_sha256") != archive_hash):
        raise ValueError("shutdown receipt or completed archive identity differs")
    source, restored = root / "sealed", root / "restored"
    expected = inventory(source)
    if not expected or inventory(restored) != expected:
        raise ValueError("restored members differ from sealed source")
    original = capture_report(source / "manifest.json", start, end, end)
    recovered = capture_report(restored / "manifest.json", start, end, end)
    if (dump(original) != dump(recovered) or recovered["replay"] != "PASS" or
            not {"CLOCK_UNVERIFIED", "INTERVAL_INCOMPLETE"} <= set(recovered["validation_reasons"]) or
            recovered["interval_net"]["usd"] is not None or
            recovered["observed_max_drawdown_percent"] is not None):
        raise ValueError("restored replay or invalid-interval evidence differs")
    ledger = Ledger(root / "active.sqlite3", readonly=True)
    try:
        if (not ledger.reconcile() or
                [row[0] for row in ledger.sequence()] != ["evidence/1", "evidence/2"]):
            raise ValueError("active SQLite shutdown commit differs")
    finally:
        ledger.close()
    if inventory(root) != before:
        raise ValueError("readback changed retained evidence")
    return {"status": "PASS", "members": len(expected), "replay": recovered["replay"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    actions = parser.add_subparsers(dest="action", required=True)
    check = actions.add_parser("preflight")
    check.add_argument("parent", type=Path)
    check.add_argument("--working-bytes", type=int, required=True)
    verify = actions.add_parser("readback")
    verify.add_argument("root", type=Path)
    verify.add_argument("start", type=int)
    verify.add_argument("end", type=int)
    args = parser.parse_args()
    try:
        if args.action == "preflight":
            preflight(args.parent, args.working_bytes)
            result = {"status": "SCREEN_PASS"}
        else:
            result = readback(args.root, args.start, args.end)
    except Refused as error:
        print(json.dumps({"status": "BLOCKED", "reason": str(error)}))
        raise SystemExit(2) from None
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
