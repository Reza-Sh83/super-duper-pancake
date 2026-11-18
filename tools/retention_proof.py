"""Offline fixed-slot retention proof for synthetic byte records."""

import hashlib
import json
import os
from pathlib import Path
import shutil
import stat

MIB = 1024**2
CAP = 5 * 1024 * MIB
FLOOR = 2 * 1024 * MIB
HEADROOM = 16 * MIB

# Capture's e50657c census, allowance and observed busy-minute raw bytes.
RETAINED = 627_154_944
WORKING = 492_127_209
BUSY_MINUTE = 8_961_460
BURST_RECORD = (2 * BUSY_MINUTE + 59) // 60
ARCHIVE_CAP = CAP - RETAINED - WORKING


def charge(root):
    total = 0
    for path in (root, *root.rglob("*")):
        entry = path.lstat()
        if not (stat.S_ISREG(entry.st_mode) or stat.S_ISDIR(entry.st_mode)):
            raise ValueError("retention proof requires a regular file and directory census")
        total += max(entry.st_size, entry.st_blocks * 512)
    return total


def prove_retention(root, output, records, *, cap, data_limit, shutdown_limit):
    """Exercise an isolated, single-writer fixture with two preallocated files."""
    root, output = Path(root).resolve(strict=True), Path(output).resolve(strict=True)
    if output == root or not output.is_relative_to(root) or any(output.iterdir()):
        raise ValueError("use an existing empty output directory inside the evidence root")
    if not (0 < cap <= CAP and 0 < data_limit <= 2 * MIB and 0 < shutdown_limit <= MIB):
        raise ValueError("the offline fixture requires small, positive slot sizes")
    allocated = data_limit + shutdown_limit
    if charge(root) + allocated + HEADROOM > cap:
        raise ValueError("retained evidence and reservation exceed cap")
    if shutil.disk_usage(root).free < FLOOR + HEADROOM + allocated:
        raise ValueError("reservation would cross free-space floor or writer headroom")

    # Use fixed slots, including the seal. No new output is opened in the
    # write loop or on shutdown. The fixture owns this directory exclusively.
    with (output / "data.slot").open("x+b", buffering=0) as data, (
        output / "shutdown.slot"
    ).open("x+b", buffering=0) as shutdown:
        for stream, size in ((data, data_limit), (shutdown, shutdown_limit)):
            os.posix_fallocate(stream.fileno(), 0, size)
            info = os.fstat(stream.fileno())
            if info.st_size != size or info.st_blocks * 512 < size:
                raise ValueError("filesystem did not allocate the fixture slot")
            os.fsync(stream.fileno())
        if charge(root) + HEADROOM > cap or shutil.disk_usage(root).free < FLOOR + HEADROOM:
            raise ValueError("allocated reservation fails admission")

        digest = hashlib.sha256()
        used = count = rejected = 0
        for record in records:
            if not isinstance(record, bytes) or not record:
                raise ValueError("fixture records must be nonempty bytes")
            if len(record) > data_limit - used:
                rejected = len(record)
                break
            if data.write(record) != len(record):
                raise OSError("short fixture write")
            digest.update(record)
            used += len(record)
            count += 1

        os.fsync(data.fileno())
        receipt = {
            "status": "BUDGET_STOP" if rejected else "INPUT_ENDED",
            "records": count,
            "rejected_bytes": rejected,
            "committed_bytes": used,
            "committed_sha256": digest.hexdigest(),
        }
        seal = (json.dumps(receipt, sort_keys=True) + "\n").encode()
        if len(seal) > shutdown_limit or shutdown.write(seal) != len(seal):
            raise OSError("fixture shutdown receipt does not fit its reserved slot")
        os.fsync(shutdown.fileno())

    fd = os.open(output, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)
    if charge(root) + HEADROOM > cap or shutil.disk_usage(root).free < FLOOR + HEADROOM:
        raise ValueError("fixture exceeded admitted budget")
    return receipt
