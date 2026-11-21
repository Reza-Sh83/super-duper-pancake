from dataclasses import replace
import hashlib
import unittest

from tools.kraken_march_archive import (
    DEVELOPMENT, DEVELOPMENT_WARMUP, canonical, decoded_rows,
)


class MarchArchiveTests(unittest.TestCase):
    def test_development_coverage_and_exact_decimal_strings(self):
        for binding, count in ((DEVELOPMENT_WARMUP, 26), (DEVELOPMENT, 288)):
            rows = [[str(t), "1234.56789001", "1500", "1200", "1300", "0.001", "12"]
                    for t in binding.grid()]
            payload = canonical(rows)
            bound = replace(binding, digest=hashlib.sha256(payload).hexdigest())
            result = decoded_rows(payload, bound)
            self.assertEqual(len(result), count)
            self.assertEqual(result[0], [binding.grid().start, *rows[0][1:5]])
            self.assertEqual(result[-1][0] + 3600, binding.grid().stop)
        self.assertEqual(DEVELOPMENT_WARMUP.grid().stop, DEVELOPMENT.grid().start)

    def test_rejects_corrupt_and_invalid_slices(self):
        original = [[str(t), "100", "103", "99", "102", "0.01", "2"]
                    for t in DEVELOPMENT_WARMUP.grid()]
        for column, value in ((0, original[1][0]), (1, "NaN"), (2, "90"), (3, "bad"),
                              (5, "-1"), (6, "2.5")):
            with self.subTest(column=column, value=value):
                rows = [row.copy() for row in original]
                rows[0][column] = value
                payload = canonical(rows)
                binding = replace(DEVELOPMENT_WARMUP, digest=hashlib.sha256(payload).hexdigest())
                with self.assertRaises(ValueError):
                    decoded_rows(payload, binding)
        for payload in (canonical(original[:-1]), canonical(original) + b" "):
            binding = replace(DEVELOPMENT_WARMUP, digest=hashlib.sha256(payload).hexdigest())
            with self.assertRaises(ValueError):
                decoded_rows(payload, binding)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            decoded_rows(canonical(original), DEVELOPMENT_WARMUP)
