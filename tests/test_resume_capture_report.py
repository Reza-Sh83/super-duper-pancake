"""Restart checks for local publication using the sealed capture test fixture."""

import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest

from crypto_paper.data import NANO, load, stamp
from crypto_paper.pilot_report import HOUR
import test_capture_report as fixtures


class ResumeCaptureReportTests(unittest.TestCase):
    def setUp(self):
        tmp = TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        self.manifest = fixtures.CaptureReportTests().fixture(root)
        self.output = root / "reports"
        self.output.mkdir()
        self.end = fixtures.T + 600 * NANO
        self.original = {p: p.read_bytes() for p in self.manifest.parent.rglob("*") if p.is_file()}

    def invoke(self, generated=None, crash=None):
        args = ["--manifest", str(self.manifest), "--start", stamp(self.end - 6 * HOUR),
                "--end", stamp(self.end), "--generated-at", stamp(generated or self.end),
                "--out-dir", str(self.output)]
        cmd = [sys.executable, "-m", "tools.resume_capture_report"]
        if crash:
            # Exit without finally handlers to leave genuine recovery state on disk.
            script = """
import os,sys
from tools import resume_capture_report as report
link = os.link
mode = sys.argv.pop(1)
def interrupt(*args):
    if mode == 'after':
        link(*args)
    os._exit(73)
os.link = interrupt
report.main()
"""
            cmd = [sys.executable, "-c", script, crash]
        return subprocess.run(cmd + args, capture_output=True, check=False)

    def check_report(self, path):
        report = load(path.read_bytes())
        self.assertEqual(report["report_id"], path.stem)
        self.assertEqual(report["interval_start"], stamp(self.end - 6 * HOUR))
        self.assertEqual(report["cutoff"], stamp(self.end))
        self.assertEqual(report["coverage"]["expected"], 21600)
        self.assertIn("INTERVAL_INCOMPLETE", report["validation_reasons"])
        self.assertIn("CLOCK_UNVERIFIED", report["validation_reasons"])
        for metric in ("interval_net", "inception_net"):
            self.assertIsNone(report[metric]["usd"])
            self.assertIsNone(report[metric]["percent"])
        self.assertIsNone(report["observed_max_drawdown_percent"])
        self.assertEqual(report["delivery_status"], "NOT_ATTEMPTED")
        self.assertFalse(report["real_alert_sent"])
        self.assertEqual(self.original, {p: p.read_bytes() for p in self.original})

    def test_resume_before_publication(self):
        self.assertEqual(self.invoke(crash="before").returncode, 73)
        self.assertEqual(list(self.output.glob("*.json")), [])
        self.assertEqual(len(list(self.output.glob("*.pending"))), 1)
        result = self.invoke(generated=self.end + NANO)
        self.assertEqual(result.returncode, 0, result.stderr)
        files = list(self.output.iterdir())
        self.assertEqual(len(files), 1)
        self.assertEqual(load(result.stdout)["status"], "published")
        self.check_report(files[0])

    def test_resume_after_publication_preserves_original_bytes(self):
        self.assertEqual(self.invoke(crash="after").returncode, 73)
        path, = self.output.glob("*.json")
        first = path.read_bytes()
        retry = self.invoke(generated=self.end + NANO)
        self.assertEqual(retry.returncode, 0, retry.stderr)
        self.assertEqual(load(retry.stdout), {"report_id": path.stem, "status": "reused"})
        self.assertEqual(list(self.output.iterdir()), [path])
        self.assertEqual(path.read_bytes(), first)
        self.check_report(path)

    def test_conflicting_existing_report_is_preserved(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stderr)
        path, = self.output.glob("*.json")
        path.write_bytes(b'{"invalid":true}')
        retry = self.invoke()
        self.assertNotEqual(retry.returncode, 0)
        self.assertIn(b"conflicts", retry.stderr)
        self.assertEqual(path.read_bytes(), b'{"invalid":true}')
        self.assertEqual(list(self.output.iterdir()), [path])


if __name__ == "__main__":
    unittest.main()
