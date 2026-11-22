"""Bounded synthetic rotation proof. No production retention or deletion entry point."""

import hashlib
import json
import os
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest

from crypto_paper.capture_report import capture_report
from crypto_paper.data import NANO, dump
from crypto_paper.pilot_report import HOUR
from tools.retention_proof import charge
from tools.tarxz_persistent import verify_archive
from tools.tarxz_retention import (
    ARCHIVE_SLOT, FREE, INTAKE, PAGE, Bounded, Refused, Reservations, admit,
    archive, inventory, restore,
)
import test_capture_report as fixtures


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def sync_directory(path):
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def ready_to_retire(local, downloaded, ack, expected):
    """Validate a durable acknowledgment against byte readback and sealed inventory."""
    receipt = json.loads(ack.read_bytes())
    archive_hash = digest(local)
    if (receipt != {"archive_sha256": archive_hash, "readback": "verified"}
            or digest(downloaded) != archive_hash):
        raise Refused("archive readback acknowledgment does not match")
    verify_archive(downloaded, expected)


class RetentionRolloverTests(unittest.TestCase):
    def exercise(self, acknowledge):
        with TemporaryDirectory() as temp:
            parent = Path(temp)
            root = parent / "capture"
            root.mkdir()
            recovery = parent / "synthetic-readback"
            recovery.mkdir()
            sealed = fixtures.CaptureReportTests().fixture(root, operator_stop=True).parent
            original = inventory(sealed)
            local = root / "retained.tar.xz"
            local.touch()
            archive(sealed, original, local)
            verify_archive(local, original)

            # Non-writing retained charge is modeled just under the real intake
            # boundary. Physical files stay small. All candidate writes share
            # the existing reservation ledger and a fixed-size output extent.
            extent = ARCHIVE_SLOT
            reservations = Reservations({"archive": extent, "restore": extent}, extent)
            working = extent + PAGE  # one bounded archive and directory growth
            initial_charge = charge(root)
            baseline = INTAKE - initial_charge - working
            reserve = parent / "reserved-stop.json"
            with reserve.open("xb") as stream:
                os.posix_fallocate(stream.fileno(), 0, PAGE)
                os.fsync(stream.fileno())
            sync_directory(parent)
            prior_archive = digest(local)
            before = inventory(root)

            remote = recovery / "readback.tar.xz"
            receipt_path = recovery / "ack.json"
            if acknowledge:
                with remote.open("xb") as stream:
                    stream.write(local.read_bytes())
                    stream.flush()
                    os.fsync(stream.fileno())
                with receipt_path.open("x") as stream:
                    json.dump({"archive_sha256": "0" * 64, "readback": "verified"}, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                sync_directory(recovery)
                with self.assertRaisesRegex(Refused, "acknowledgment"):
                    ready_to_retire(local, remote, receipt_path, original)
                self.assertEqual(inventory(root), before)
                # A separate completed acknowledgment replaces the rejected one.
                receipt_path = recovery / "verified-ack.json"
                with receipt_path.open("x") as stream:
                    json.dump({"archive_sha256": digest(remote), "readback": "verified"}, stream)
                    stream.flush()
                    os.fsync(stream.fileno())
                sync_directory(recovery)
                with remote.open("ab") as stream:
                    stream.write(b"tamper")
                    stream.flush()
                    os.fsync(stream.fileno())
                with self.assertRaisesRegex(Refused, "acknowledgment"):
                    ready_to_retire(local, remote, receipt_path, original)
                self.assertEqual(inventory(root), before)
                with remote.open("wb") as stream:
                    stream.write(local.read_bytes())
                    stream.flush()
                    os.fsync(stream.fileno())
                ready_to_retire(local, remote, receipt_path, original)
                local.unlink()  # Only the disposable synthetic local archive.
                sync_directory(root)
                admit(baseline + charge(root), FREE + working + 1, working)
                with reservations.take("archive", extent):
                    with self.assertRaisesRegex(Refused, "reservation"):
                        with reservations.take("restore", extent):
                            self.fail("competing write was admitted")
                    next_archive = root / "fixed-next.tar.xz"
                    with next_archive.open("xb") as stream:
                        os.posix_fallocate(stream.fileno(), 0, extent)
                        os.fsync(stream.fileno())
                    # Use the fixed extent as the sole write destination.
                    archive(sealed, original, next_archive)
                    verify_archive(next_archive, original)
                    self.assertLessEqual(charge(next_archive), extent)
                    self.assertLess(baseline + charge(root), INTAKE)
                rollback = remote
            else:
                with self.assertRaisesRegex(Refused, "aggregate"):
                    admit(baseline + charge(root), FREE + working + 1, working)
                reservations.stop()
                with self.assertRaisesRegex(Refused, "reservation"):
                    with reservations.take("archive", extent):
                        self.fail("stopped intake accepted an archive")
                self.assertEqual(inventory(root), before)
                self.assertEqual(digest(local), prior_archive)
                rollback = local

            # Shutdown writes only through its independently allocated extent.
            with reserve.open("r+b", buffering=0) as stream:
                Bounded(stream, PAGE).write(b'{"status":"STOPPED"}\n')
                os.fsync(stream.fileno())
            self.assertEqual(charge(reserve), PAGE)
            self.assertEqual(reservations.active, {})
            self.assertEqual(inventory(sealed), original)

            restored = recovery / "restored"
            restored.mkdir()
            for name in original:
                destination = restored / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.touch()
            restore(rollback, restored, original, {name: size for name, (size, _) in original.items()})
            end = fixtures.T + 600 * NANO
            start = end - 6 * HOUR
            result = capture_report(restored / "manifest.json", start, end, end)
            original_result = capture_report(sealed / "manifest.json", start, end, end)
            self.assertEqual(dump(result), dump(original_result))
            self.assertEqual(result["replay"], "PASS")
            self.assertIn("CLOCK_UNVERIFIED", result["validation_reasons"])
            self.assertIsNone(result["interval_net"]["usd"])
            print(json.dumps({"verified_ack": acknowledge, "members": len(original),
                              "retained_charge_before": initial_charge,
                              "retained_charge_after": charge(root),
                              "rollover_reserved": working, "shutdown_extent": charge(reserve),
                              "replay": result["replay"]}, sort_keys=True))

    def test_unacknowledged_backlog_refuses_and_preserves_evidence(self):
        self.exercise(acknowledge=False)

    def test_wrong_ack_preserves_then_verified_readback_allows_rollover(self):
        self.exercise(acknowledge=True)
