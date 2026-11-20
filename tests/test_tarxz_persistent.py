"""Follow-up checks only. The exact published tmpfs proof is unchanged."""

import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
from tempfile import TemporaryDirectory
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from crypto_paper.data import NANO
from crypto_paper.engine import Ledger
from crypto_paper.pilot_report import HOUR
from crypto_paper.runtime import digest_file
from tools import tarxz_persistent as persistent
from tools.tarxz_retention import FREE, WORK_MAX, archive, inventory
import test_capture_report as fixtures


class PersistentRetentionTests(unittest.TestCase):
    def test_overlay_rejected_before_census_or_writes(self):
        with TemporaryDirectory() as tmp, patch.object(
            persistent.subprocess, "check_output", return_value="overlayfs\n"
        ), patch.object(persistent, "charge") as census:
            with self.assertRaisesRegex(persistent.Refused, "direct ext4"):
                persistent.preflight(tmp, 323584)
            census.assert_not_called()
            self.assertEqual(list(Path(tmp).iterdir()), [])

    def test_candidate_screen_uses_strict_shared_budget(self):
        with TemporaryDirectory() as tmp, patch.object(
            persistent.subprocess, "check_output", side_effect=["ext2/ext3\n", "ext4\n"] * 2
        ), patch.object(persistent.os, "statvfs", return_value=SimpleNamespace(f_frsize=4096)):
            disk = SimpleNamespace(free=FREE + WORK_MAX)
            with patch.object(persistent.shutil, "disk_usage",
                              return_value=disk):
                with self.assertRaisesRegex(persistent.Refused, "strict aggregate"):
                    persistent.preflight(tmp, WORK_MAX)
            with patch.object(persistent.shutil, "disk_usage",
                              return_value=SimpleNamespace(free=disk.free + 1)):
                self.assertEqual(persistent.preflight(tmp, WORK_MAX), Path(tmp).resolve())

    def test_fresh_process_readback_preserves_and_validates_completed_artifacts(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = fixtures.CaptureReportTests().fixture(root, operator_stop=True).parent
            source.rename(root / "sealed")
            source = root / "sealed"
            shutil.copytree(source, root / "restored")
            complete = root / "complete.tar.xz"
            complete.touch()
            archive(source, inventory(source), complete)
            (root / "shutdown.json").write_text(json.dumps(
                {"status": "STOPPED", "sqlite_commit": "verified",
                 "archive_sha256": digest_file(complete)}
            ))
            ledger = Ledger(root / "active.sqlite3")
            try:
                for number in (1, 2):
                    with ledger.transaction(number, str(number)):
                        ledger.event(f"evidence/{number}", "proof", {"sample": number})
            finally:
                ledger.close()
            before = inventory(root)
            end = fixtures.T + 600 * NANO
            cmd = [sys.executable, "-B", "-m", "tools.tarxz_persistent", "readback",
                   str(root), str(end - 6 * HOUR), str(end)]
            result = subprocess.run(cmd, capture_output=True, check=True, timeout=10)
            self.assertEqual(json.loads(result.stdout), {"status": "PASS", "members": 5, "replay": "PASS"})
            self.assertEqual(inventory(root), before)

            with tarfile.open(complete, "w:xz", format=tarfile.PAX_FORMAT, preset=6) as tar:
                member = tarfile.TarInfo("unrelated")
                member.size = 1
                tar.addfile(member, io.BytesIO(b"x"))
            seal = root / "shutdown.json"
            seal.write_text(json.dumps({"status": "STOPPED", "sqlite_commit": "verified",
                                       "archive_sha256": digest_file(complete)}))
            unrelated = inventory(root)
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b"member inventory differs", result.stderr)
            self.assertEqual(inventory(root), unrelated)

            # Same ordered members and lengths, but one changed payload.
            with tarfile.open(complete, "w:xz", format=tarfile.PAX_FORMAT, preset=6) as tar:
                for name in inventory(source):
                    data = (source / name).read_bytes()
                    if name == "manifest.json":
                        data = b"!" + data[1:]
                    member = tarfile.TarInfo(name)
                    member.size = len(data)
                    tar.addfile(member, io.BytesIO(data))
            seal.write_text(json.dumps({"status": "STOPPED", "sqlite_commit": "verified",
                                       "archive_sha256": digest_file(complete)}))
            changed = inventory(root)
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b"member content differs", result.stderr)
            self.assertEqual(inventory(root), changed)

            with complete.open("ab") as stream:
                stream.write(b"altered")
            altered = inventory(root)
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn(b"archive identity differs", result.stderr)
            self.assertEqual(inventory(root), altered)
