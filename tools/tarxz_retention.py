"""Bounded, local synthetic proof of the full lossless tar+xz contract."""

from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import errno
import json
import lzma
import os
from pathlib import Path
import resource
import shutil
import signal
import subprocess
import sys
import tarfile
import threading

from crypto_paper.capture_report import capture_report
from crypto_paper.data import NANO, dump
from crypto_paper.engine import Ledger
from crypto_paper.pilot_report import HOUR
from crypto_paper.runtime import digest_file, versions
from tools.retention_extents import preallocate, protect_extents
from tools.retention_proof import CAP, FLOOR, HEADROOM, MIB, charge

RESERVE = 256 * MIB
WORK_MAX = 512 * MIB
INTAKE = CAP - RESERVE
FREE = FLOOR + HEADROOM + RESERVE
PAGE = 4096
SQL_SLOT = 16 * PAGE
ARCHIVE_SLOT = 8 * PAGE
# Post-allocation directory growth is denied by the read-only namespace.
DIRECTORY_ALLOWANCE = 16 * PAGE


class Refused(ValueError):
    pass


def admit(retained, free, working):
    if not 0 <= working <= WORK_MAX or retained + working >= INTAKE or free <= FREE + working:
        raise Refused("strict aggregate admission refused")


def inventory(directory):
    # charge rejects links and irregular entries before any path is opened.
    charge(directory)
    return {p.relative_to(directory).as_posix(): [p.stat().st_size, digest_file(p)]
            for p in sorted(directory.rglob("*"), key=lambda item: item.as_posix()) if p.is_file()}


class Bounded:
    def __init__(self, stream, limit):
        self.stream = stream
        self.limit = limit

    def write(self, data):
        if len(data) > self.limit - self.stream.tell():
            raise Refused("write would exceed its reserved extent")
        if self.stream.write(data) != len(data):
            raise OSError("short write")
        return len(data)


class Reservations:
    """Admit cooperating transient writers to a fixed set of reserved slots."""
    def __init__(self, limits, total):
        self.limits = limits
        self.lock = threading.Lock()
        self.active = {}
        self.total = total
        self.stopped = False

    @contextmanager
    def take(self, name, size):
        with self.lock:
            if (self.stopped or size <= 0 or name in self.active or size > self.limits.get(name, 0) or
                    sum(self.active.values()) + size > self.total):
                raise Refused("transient reservation refused before write")
            self.active[name] = size
        try:
            yield
        finally:
            with self.lock:
                del self.active[name]


    def stop(self):
        with self.lock:
            self.stopped = True


def archive(source, expected, output):
    with output.open("r+b", buffering=0) as stream:
        with lzma.LZMAFile(Bounded(stream, ARCHIVE_SLOT), "w", preset=6) as xz:
            with tarfile.open(fileobj=xz, mode="w|", format=tarfile.PAX_FORMAT) as tar:
                for name, (size, _) in expected.items():
                    member = tarfile.TarInfo(name)
                    member.size = size
                    with (source / name).open("rb") as payload:
                        tar.addfile(member, payload)
        os.fsync(stream.fileno())


def restore(archive_path, destination, expected, limits):
    names = iter(expected)
    with tarfile.open(archive_path, mode="r|xz") as tar:
        for member in tar:
            # Exact expected name and sequence also exclude traversal and duplicates.
            name = next(names, None)
            if (name is None or member.name != name or not member.isreg() or
                    member.size != expected[name][0]):
                raise ValueError("archive member does not match sealed inventory")
            with tar.extractfile(member) as source, (destination / name).open("r+b", buffering=0) as dest:
                shutil.copyfileobj(source, Bounded(dest, limits[name]))
                os.fsync(dest.fileno())
    if next(names, None) is not None or inventory(destination) != expected:
        raise ValueError("restored inventory or hash mismatch")


def census(root):
    rows = [p.stat() for p in (root, *root.rglob("*"))]
    return {"logical": sum(p.st_size for p in rows),
            "allocated": sum(p.st_blocks * 512 for p in rows),
            "charge": sum(max(p.st_size, p.st_blocks * 512) for p in rows)}


def worker(plan):
    root = Path(plan["root"])
    source, restored = root / "sealed", root / "restored"
    paths = {name: root / name for name in plan["slots"]}
    limits = plan["restore"]
    expected = plan["inventory"]
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (SQL_SLOT, SQL_SLOT))
    protect_extents()
    samples = {"pre_write": census(root)}
    try:
        with (root / "undeclared.tmp").open("xb"):
            raise ValueError("undeclared file creation unexpectedly succeeded")
    except PermissionError:
        pass
    except OSError as error:
        if error.errno != errno.EROFS:
            raise
    db = Ledger(root / "active.sqlite3")
    db.db.execute("PRAGMA temp_store=MEMORY")
    with db.transaction(1, "working-commit"):
        db.event("evidence/1", "proof", {"sample": 1})
    mode = db.db.execute("PRAGMA journal_mode").fetchone()[0]
    synchronous = db.db.execute("PRAGMA synchronous").fetchone()[0]
    if (mode, synchronous) != ("persist", 2):
        raise ValueError("unexpected SQLite durability settings")
    journal = paths["active.sqlite3-journal"]
    shutdown = paths["shutdown.json"]
    final = paths["complete.tar.xz"]
    partial = paths["partial.tar.xz"]

    with paths["active.raw"].open("r+b", buffering=0) as stream:
        Bounded(stream, PAGE).write(b"active synthetic raw prefix\n")
        os.fsync(stream.fileno())

    try:
        # The transaction modifies an existing page, so the journal is active
        # through archive creation, staging and restored output.
        with db.transaction(2, "shutdown-commit"):
            db.event("evidence/2", "proof", {"sample": 2})
            if not journal.stat().st_size:
                raise ValueError("expected a live persistent journal")
            archive(source, expected, final)
            archive_hash = digest_file(final)

            restore_size = sum(limits.values())
            transient = Reservations(
                {"archive": ARCHIVE_SLOT, "restore": restore_size, "additional": PAGE},
                total=ARCHIVE_SLOT + restore_size,
            )
            orders = []
            for first, second in (("restore", "archive"), ("archive", "restore")):
                entered = threading.Event()
                other_entered = threading.Event()
                completed = threading.Barrier(2, timeout=5)

                def contender(name):
                    with transient.take(name, transient.limits[name]):
                        if name == first:
                            entered.set()
                            if not other_entered.wait(5):
                                raise TimeoutError("overlap not reached")
                        else:
                            if not entered.wait(5):
                                raise TimeoutError("first contender did not start")
                            try:
                                with transient.take("additional", PAGE):
                                    raise AssertionError("unexpected admission")
                            except Refused:
                                other_entered.set()
                        # Inject the write stop in the final overlap. The
                        # already-admitted restore may finish in its own slots.
                        if first == "archive" and name == "archive":
                            with partial.open("r+b", buffering=0) as stream:
                                slot = Bounded(stream, ARCHIVE_SLOT)
                                slot.write(lzma.LZMACompressor(preset=6).compress(b"staged prefix"))
                                try:
                                    slot.write(b"x" * ARCHIVE_SLOT)
                                except Refused:
                                    transient.stop()
                                    os.fsync(stream.fileno())
                                else:
                                    raise AssertionError("oversize staging write admitted")
                        if first == "archive" and name == "restore":
                            restore(final, restored, expected, limits)
                        completed.wait()
                        if name == first:
                            samples["overlap_" + first] = census(root)
                        completed.wait()

                # Acquire the first reservation before launching the second worker.
                with ThreadPoolExecutor(max_workers=2) as pool:
                    start = pool.submit(contender, first)
                    if not entered.wait(5):
                        raise TimeoutError("first reservation not acquired")
                    finish = pool.submit(contender, second)
                    start.result(timeout=8)
                    finish.result(timeout=8)
                if transient.active:
                    raise AssertionError("reservation still active")
                orders.append([first, second])

            try:
                with transient.take("archive", ARCHIVE_SLOT):
                    raise AssertionError("new intake admitted after stop")
            except Refused:
                pass
            if not 0 < partial.stat().st_size < ARCHIVE_SLOT:
                raise ValueError("partial archive was not preserved")
            samples["pre_commit"] = census(root)
    finally:
        db.close()

    samples["post_close"] = census(root)
    with LedgerRead(root / "active.sqlite3") as closed:
        if not closed.reconcile() or [row[0] for row in closed.sequence()] != ["evidence/1", "evidence/2"]:
            raise ValueError("final SQLite commit failed readback")

    start, end = plan["start"], plan["end"]
    original = capture_report(source / "manifest.json", start, end, end)
    recovered = capture_report(restored / "manifest.json", start, end, end)
    if dump(original) != dump(recovered) or original["replay"] != "PASS":
        raise ValueError("restored ordered replay or account differs")
    if not {"CLOCK_UNVERIFIED", "INTERVAL_INCOMPLETE"} <= set(recovered["validation_reasons"]):
        raise ValueError("missing invalid-clock or gap evidence")
    if recovered["interval_net"]["usd"] is not None or recovered["observed_max_drawdown_percent"] is not None:
        raise ValueError("invalid interval has financial results")
    with LedgerRead(restored / "ledger.sqlite3") as sealed:
        frames_count = sealed.db.execute("SELECT count(*) FROM frames").fetchone()[0]
        events_count = sum(1 for _ in sealed.sequence())
        if frames_count < 1 or events_count < 1:
            raise ValueError("fixture did not exercise both frame and event replay")
        account = sealed.state
    if inventory(source) != expected or digest_file(final) != archive_hash:
        raise ValueError("source or archive changed")

    # This is the only writer allowed to use the separate shutdown slot.
    seal = (json.dumps({"status": "STOPPED", "archive_sha256": archive_hash,
                        "partial_bytes": partial.stat().st_size, "sqlite_commit": "verified"},
                       sort_keys=True) + "\n").encode()
    with shutdown.open("r+b", buffering=0) as stream:
        Bounded(stream, PAGE).write(seal)
        os.fsync(stream.fileno())
    directories = {root, *(path.parent for path in paths.values())}
    for path in sorted(directories, key=lambda item: (-len(item.parts), item.as_posix())):
        directory = os.open(path, os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    if shutdown.read_bytes() != seal:
        raise ValueError("shutdown readback failed")
    samples["post_shutdown"] = census(root)
    for name, size in plan["slots"].items():
        info = paths[name].stat()
        if info.st_blocks * 512 != size or info.st_size > size:
            raise ValueError("slot allocation changed")
    return {"RET-CAP-01": "PASS", "RET-RESTORE-01": "PASS", "samples": samples,
            "archive_bytes": final.stat().st_size, "members": len(expected),
            "restore_bytes": sum(size for size, _ in expected.values()), "orders": orders,
            "partial_bytes": partial.stat().st_size, "shutdown_bytes": len(seal),
            "durability": [mode, synchronous], "thread_workers_joined": True,
            "frames": frames_count, "events": events_count, "final_account": account,
            "runtime": versions()}


@contextmanager
def LedgerRead(path):
    db = Ledger(path, readonly=True)
    try:
        yield db
    finally:
        db.close()


def run(root, start, end):
    """Run one isolated fixture. The caller supplies the existing sealed fixture."""
    root = root.resolve(strict=True)
    # Confirm a filesystem with preallocated, ordinary non-CoW page extents.
    filesystem = subprocess.check_output(["stat", "-f", "-c", "%T", root], text=True).strip()
    if filesystem != "tmpfs":
        raise Refused("fixture requires independently bounded tmpfs allocation")
    if (sys.version_info[:2] != (3, 12) or versions()["websockets"] != "15.0.1" or
            set(root.iterdir()) != {root / "sealed"}):
        raise ValueError("expected Python 3.12 and fresh synthetic output paths")
    expected = inventory(root / "sealed")
    if not 1 <= len(expected) <= 16 or end - start != 6 * HOUR:
        raise ValueError("expected one bounded six-hour fixture")
    restore_limits = {name: max(PAGE, (size + PAGE - 1) // PAGE * PAGE)
                      for name, (size, _) in expected.items()}
    if max(restore_limits.values()) > SQL_SLOT or sum(restore_limits.values()) > 2 * SQL_SLOT:
        raise Refused("fixture member limit")
    slots = {"active.raw": PAGE, "active.sqlite3": SQL_SLOT,
             "active.sqlite3-journal": SQL_SLOT, "complete.tar.xz": ARCHIVE_SLOT,
             "partial.tar.xz": ARCHIVE_SLOT, "shutdown.json": PAGE}
    slots.update({f"restored/{name}": size for name, size in restore_limits.items()})
    # The global reserve already includes the separate 4 KiB seal slot.
    working = sum(slots.values()) - PAGE + DIRECTORY_ALLOWANCE
    retained = charge(root)
    admit(retained, shutil.disk_usage(root).free, working)

    for name, size in slots.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        preallocate(path, size)
    actual = charge(root)
    if actual > retained + working + PAGE:
        raise Refused("allocation census exceeds declared budget")
    # Credit the already allocated seal once. All other reserve remains free.
    admit(actual - PAGE, shutil.disk_usage(root).free + PAGE, 0)

    plan = {"root": str(root), "slots": slots, "restore": restore_limits,
            "inventory": expected, "start": start, "end": end}
    command = ["bwrap", "--unshare-user", "--unshare-pid", "--unshare-net",
               "--die-with-parent", "--cap-drop", "ALL", "--ro-bind", "/", "/", "--proc", "/proc"]
    for name in slots:
        path = str(root / name)
        command.extend(["--bind", path, path])
    command.extend(["--setenv", "SQLITE_TMPDIR", str(root), "--setenv", "TMPDIR", str(root)])
    command.extend(["--", sys.executable, "-B", "-m", "tools.tarxz_retention", json.dumps(plan)])
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          start_new_session=True) as process:
        try:
            stdout, stderr = process.communicate(timeout=25)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            process.communicate()
            raise
    if process.returncode:
        raise RuntimeError(f"guarded worker exit {process.returncode}: {stderr.decode()}")
    result = json.loads(stdout)
    final = census(root)
    admit(final["charge"] - PAGE, shutil.disk_usage(root).free + PAGE, 0)
    if final != result["samples"]["post_shutdown"] or final["charge"] != actual:
        raise ValueError("namespace or physical allocation changed during execution")
    return result | {"exit": process.returncode, "working_bound": working,
                     "seal_reserve": PAGE, "slots": slots, "retained_charge": retained,
                     "filesystem": filesystem}


if __name__ == "__main__":
    print(json.dumps(worker(json.loads(sys.argv[1])), sort_keys=True))
