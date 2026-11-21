"""Offline frozen March panel for Capture 4d1f286."""
import argparse
import csv
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import frozen_model as model
import frozen_panel as panel

INPUT = 'b2c61a3c5c145e7ad24fbfb99a63ea4a3aa2e5653343c1aeaafe0cec5a6692f2'
DEPS = ('24944c5935d438d143c1912bc342e594e17ac12ad67c1e08ceb64d145d974df7',
        '84cb149c5a75672f93b45246beeb03834454233aec26acc62fe4724d9692005b')
PARTITIONS = {
    'development': ('2026-03-04', '2026-03-16',
        '7362346f6f5aa10d8d3a13230afc824f9af205b26f492e0b15f3e6d3e2c6cb1c',
        '06752e942790711b27028a6ba4748ab1918f98966b55faabc0fdbe0b2821b8d2'),
    'validation': ('2026-03-20', '2026-04-01',
        '15660324ac687d9b9a727c3ec84a6fc5331e885d5e9eff13ca84ca3133aca38e',
        'ae9d903bc5ec01f6eea61ca8a331ea2c96d4b19e6e12da22bfc41a2d32802387'),
}


def epoch(date):
    return int(datetime.fromisoformat(date).replace(tzinfo=timezone.utc).timestamp())


def sha(payload):
    return hashlib.sha256(payload).hexdigest()


def canonical(rows):
    return (json.dumps(rows, separators=(',', ':')) + '\n').encode()


def select(payload, start, end, warm_hash, data_hash):
    warm, data = [], []
    for row in csv.reader(io.StringIO(payload.decode('utf-8'))):
        timestamp = int(row[0])
        if start - 26 * 3600 <= timestamp < end:
            if len(row) != 7:
                raise ValueError('expected seven OHLCVT columns')
            (warm if timestamp < start else data).append(row)
    if (sha(canonical(warm)), sha(canonical(data))) != (warm_hash, data_hash):
        raise ValueError('Capture partition digest differs')
    rows = []
    for row in warm + data:
        volume = Decimal(row[5])
        if not volume.is_finite() or volume < 0 or int(row[6]) < 0:
            raise ValueError('invalid volume or trades')
        rows.append([int(row[0]), *row[1:]])
    return model.prices(rows, start=start, end=end)


def score(bars, start):
    results = {}
    for cost, terms in model.COSTS.items():
        group = {arm: model.evaluate(bars, arm, *terms, start=start) for arm in model.ARMS}
        for arm, signal in [('trend', panel.trend), ('pullback', panel.pullback)]:
            with patch.object(model, 'signals', signal):
                group[arm] = model.evaluate(bars, 'breakout', *terms, start=start)
        results[cost] = group
    return results


class Tests(unittest.TestCase):
    def test_exact_grid_and_final_closed_bar(self):
        start = epoch('2026-03-04')
        end = start + 86400
        rows = [[str(t), '100', '100', '100', '100', '1', '1']
                for t in range(start - 26*3600, end, 3600)]
        def csv_bytes():
            return ('\n'.join(','.join(r) for r in rows) + '\n').encode()
        expected = (sha(canonical(rows[:26])), sha(canonical(rows[26:])))
        bars = select(csv_bytes(), start, end, *expected)
        self.assertEqual(len(bars), 50)
        self.assertEqual(len(score(bars, start)['stress']), 6)
        rows[-1][0] = rows[-2][0]
        with self.assertRaisesRegex(ValueError, 'digest'):
            select(csv_bytes(), start, end, *expected)
        with self.assertRaisesRegex(ValueError, 'duplicate'):
            select(csv_bytes(), start, end, expected[0], sha(canonical(rows[26:])))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--member', type=Path)
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if tuple(sha(Path(m.__file__).read_bytes()) for m in (model, panel)) != DEPS:
        parser.error('frozen dependency hash mismatch')
    if args.test:
        unittest.main(argv=[__file__], verbosity=2)
        return
    if args.member is None or args.out is None:
        parser.error('provide exact private member and fresh private output directory')
    payload = args.member.read_bytes()
    if sha(payload) != INPUT:
        raise ValueError('Kraken archive member differs from Capture')
    prepared = {}
    for name, (first, last, warm, data) in PARTITIONS.items():
        start, end = epoch(first), epoch(last)
        prepared[name] = (start, select(payload, start, end, warm, data))
    args.out.mkdir(mode=0o700)
    for name, (start, bars) in prepared.items():
        result = {'hours': len(bars)-26, 'accounts': score(bars, start)}
        with (args.out / (name + '.private.json')).open('x') as stream:
            json.dump(result, stream, default=str, indent=2)


if __name__ == '__main__':
    main()
