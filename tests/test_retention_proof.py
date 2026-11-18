import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tools import retention_proof as proof


class RetentionProofTests(unittest.TestCase):
    def setUp(self):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.retained = self.root / "retained"
        self.retained.mkdir()
        self.before = {}
        for name in ("sealed.raw", "ledger.sqlite3", "journal", "archive.xz", "restore.tmp"):
            file = self.retained / name
            file.write_bytes(hashlib.sha256(name.encode()).digest())
            self.before[file] = file.read_bytes()
        self.output = self.root / "proof"
        self.output.mkdir()
        self.options = dict(cap=18 * proof.MIB, data_limit=proof.MIB, shutdown_limit=4096)

    def test_twice_busy_minute_burst_stops_and_seals_committed_prefix(self):
        def burst():
            for sequence in range(4):
                yield bytes([sequence + 1]) * proof.BURST_RECORD
            self.fail("writer requested another record after the budget stop")

        self.assertEqual(proof.ARCHIVE_CAP, 4_249_426_967)
        self.assertGreaterEqual(proof.BURST_RECORD * 60, 2 * proof.BUSY_MINUTE)
        result = proof.prove_retention(self.root, self.output, burst(), **self.options)
        data = (self.output / "data.slot").read_bytes()
        committed = b"".join(bytes([i]) * proof.BURST_RECORD for i in (1, 2, 3))
        self.assertEqual(result["status"], "BUDGET_STOP")
        self.assertEqual(result["records"], 3)
        self.assertEqual(result["rejected_bytes"], proof.BURST_RECORD)
        self.assertEqual(data[:result["committed_bytes"]], committed)
        self.assertEqual(data[len(committed):], bytes(proof.MIB - len(committed)))
        self.assertEqual(result["committed_sha256"], hashlib.sha256(committed).hexdigest())
        seal = (self.output / "shutdown.slot").read_bytes()
        self.assertEqual(json.loads(seal.rstrip(b"\0")), result)
        self.assertEqual(len(seal), 4096)
        self.assertLessEqual(proof.charge(self.root) + proof.HEADROOM, self.options["cap"])
        self.assertEqual(self.before, {p: p.read_bytes() for p in self.retained.iterdir()})

    def test_shutdown_still_fits_with_data_slot_exactly_full(self):
        result = proof.prove_retention(self.root, self.output, [b"x" * proof.MIB, b"!"],
                                       **self.options)
        self.assertEqual(result["committed_bytes"], proof.MIB)
        self.assertEqual(result["status"], "BUDGET_STOP")
        self.assertEqual(result["rejected_bytes"], 1)
        self.assertEqual(json.loads((self.output / "shutdown.slot").read_bytes().rstrip(b"\0")),
                         result)

    def test_admission_fails_before_new_files_if_cap_or_floor_is_short(self):
        needed = proof.charge(self.root) + proof.MIB + 4096 + proof.HEADROOM
        with self.assertRaisesRegex(ValueError, "exceed cap"):
            proof.prove_retention(self.root, self.output, iter(()),
                                  **(self.options | {"cap": needed - 1}))
        disk = proof.shutil.disk_usage(self.root)
        free = proof.FLOOR + proof.HEADROOM + proof.MIB + 4096 - 1
        with patch.object(proof.shutil, "disk_usage", return_value=disk._replace(free=free)):
            with self.assertRaisesRegex(ValueError, "free-space floor"):
                proof.prove_retention(self.root, self.output, iter(()), **self.options)
        self.assertEqual(list(self.output.iterdir()), [])
        self.assertEqual(self.before, {p: p.read_bytes() for p in self.retained.iterdir()})
