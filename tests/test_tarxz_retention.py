import io
import json
import tarfile
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from crypto_paper.data import NANO
from crypto_paper.pilot_report import HOUR
from tools import tarxz_retention as proof
import test_capture_report as fixtures


class TarXZRetentionTests(unittest.TestCase):
    def test_ret_cap_01_strict_boundaries(self):
        working = proof.WORK_MAX
        charge = proof.INTAKE - working
        free = proof.FREE + working
        proof.admit(charge - 1, free + 1, working)
        for c, f in ((charge, free + 1), (charge + 1, free + 1),
                     (charge - 1, free), (charge - 1, free - 1)):
            with self.assertRaises(proof.Refused):
                proof.admit(c, f, working)

    def test_ret_cap_and_restore_local_fixture(self):
        with TemporaryDirectory(dir="/dev/shm") as tmp:
            root = Path(tmp)
            manifest = fixtures.CaptureReportTests().fixture(root, operator_stop=True)
            manifest.parent.rename(root / "sealed")
            end = fixtures.T + 600 * NANO
            result = proof.run(root, end - 6 * HOUR, end)
            self.assertEqual((result["RET-CAP-01"], result["RET-RESTORE-01"]), ("PASS", "PASS"))
            self.assertEqual(result["orders"], [["restore", "archive"], ["archive", "restore"]])
            self.assertEqual(result["durability"], ["persist", 2])
            self.assertEqual(result["exit"], 0)
            self.assertGreater(result["events"], 0)
            self.assertEqual(result["frames"], 5)
            self.assertEqual(result["final_account"]["cash"], "10000")
            self.assertTrue(result["thread_workers_joined"])
            self.assertLessEqual(result["shutdown_bytes"], result["seal_reserve"])
            print("RETENTION_RESULT", json.dumps(result, sort_keys=True))

    def test_ret_restore_01_rejects_wrong_inventory_and_links(self):
        for members in (("a", "a"), ("../a",), ("b",), ("a", "b", "c"), ("b", "a")):
            with self.subTest(members=members), TemporaryDirectory() as tmp:
                root = Path(tmp)
                archive = root / "test.tar.xz"
                output = root / "restored"
                output.mkdir()
                (output / "a").touch()
                (output / "b").touch()
                with tarfile.open(archive, "w:xz", preset=6, format=tarfile.PAX_FORMAT) as bundle:
                    for name in members:
                        item = tarfile.TarInfo(name)
                        item.size = 1
                        bundle.addfile(item, io.BytesIO(b"x"))
                expected = {"a": [1, ""], "b": [1, ""]}
                with self.assertRaisesRegex(ValueError, "inventory"):
                    proof.restore(archive, output, expected, {"a": 4096, "b": 4096})

        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "link.tar.xz"
            with tarfile.open(archive, "w:xz", preset=6, format=tarfile.PAX_FORMAT) as bundle:
                item = tarfile.TarInfo("a")
                item.type = tarfile.SYMTYPE
                item.linkname = "../target"
                bundle.addfile(item)
            with self.assertRaisesRegex(ValueError, "inventory"):
                proof.restore(archive, root, {"a": [0, ""]}, {"a": 4096})
