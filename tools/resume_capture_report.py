"""Publish a resumable offline six-hour report to an existing local directory."""

import argparse
import fcntl
import os
from pathlib import Path

from crypto_paper.capture_report import capture_report
from crypto_paper.data import dump, load, parse_time


def publish_report(directory, report):
    """Return the single artifact path and whether this call published it."""
    directory = Path(directory)
    target = directory / (report["report_id"] + ".json")
    staging = target.with_suffix(".pending")
    payload = dump(report) + "\n"
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        # Serialize publication and orphan cleanup across workers using this directory.
        fcntl.flock(fd, fcntl.LOCK_EX)
        staging.unlink(missing_ok=True)
        try:
            previous = load(target.read_bytes())
        except FileNotFoundError:
            try:
                with staging.open("x", encoding="utf-8") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.link(staging, target)
                os.fsync(fd)
            finally:
                staging.unlink(missing_ok=True)
            os.fsync(fd)
            return target, True

        if (not isinstance(previous, dict) or
                not isinstance(previous.get("generated_at"), str) or
                not isinstance(previous.get("delayed"), bool)):
            raise ValueError("existing report conflicts with the requested interval evidence")
        proposed = load(payload)
        for field in ("generated_at", "delayed"):
            proposed.pop(field)
            previous.pop(field)
        if previous != proposed:
            raise ValueError("existing report conflicts with the requested interval evidence")
        # A prior worker may have exited immediately after linking the report.
        os.fsync(fd)
        return target, False
    finally:
        os.close(fd)


def resume_report(manifest, start, end, generated, directory):
    report = capture_report(manifest, start, end, generated)
    return publish_report(directory, report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--generated-at", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    path, created = resume_report(args.manifest, parse_time(args.start),
                                  parse_time(args.end), parse_time(args.generated_at),
                                  args.out_dir)
    print(dump({"report_id": path.stem, "status": "published" if created else "reused"}))


if __name__ == "__main__":
    main()
