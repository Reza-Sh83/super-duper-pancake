"""Fixed matched historical Kraken comparison. See HOURLY_STRATEGY_PANEL_PLAN.md."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal as D
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch
from urllib.request import urlopen

import frozen_model as model

DIGEST = '24944c5935d438d143c1912bc342e594e17ac12ad67c1e08ceb64d145d974df7'
DAY = 86400
CAP = 2 * 1024 * 1024


def midnight(day):
    return int(datetime(2026, 11, day, tzinfo=timezone.utc).timestamp())


WINDOWS = {'development': (midnight(18), midnight(21)),
           'validation': (midnight(21), midnight(23))}


def trend(bars, i):
    short = sum(row[3] for row in bars[i-9:i-1]) / 8
    long = sum(row[3] for row in bars[i-25:i-1]) / 24
    return short > long, short < long


def pullback(bars, i):
    close = bars[i-2][3]
    average = sum(row[3] for row in bars[i-14:i-2]) / 12
    return close < D('.97') * average, close >= average


def closed_rows(payload):
    data = json.loads(payload)
    if data['error'] or set(data['result']) - {'last'} != {'XXBTZUSD'}:
        raise ValueError('Kraken API error or unexpected pair')
    return data['result']['XXBTZUSD'][:-1]


def evaluate(payload, mode):
    start, end = WINDOWS[mode]
    rows = closed_rows(payload)
    selected = [r for r in rows if start <= r[0] < end]
    chunk = json.dumps(selected, separators=(',', ':')).encode() + b'\n'
    bars = model.prices(rows, start=start, end=end)
    results = {}
    for scenario, costs in model.COSTS.items():
        arms = {arm: model.evaluate(bars, arm, *costs, start=start)
                for arm in model.ARMS}
        for name, signal in [('trend', trend), ('pullback', pullback)]:
            with patch.object(model, 'signals', signal):
                arms[name] = model.evaluate(bars, 'breakout', *costs, start=start)
        results[scenario] = arms
    return {'scope': 'EXPLORATORY_BAR_PROXY', 'mode': mode, 'start_utc_epoch': start,
            'end_exclusive_utc_epoch': end, 'hours': len(bars)-26,
            'selected_rows_sha256': hashlib.sha256(chunk).hexdigest(), 'accounts': results}


class Tests(unittest.TestCase):
    def test_rules_and_delay(self):
        bars = [(D(100),)*4] * 27
        bars[25] = bars[26] = (D(500),)*4
        self.assertEqual(trend(bars, 26), (False, False))
        self.assertEqual(pullback(bars, 26), (False, True))
        bars[24] = (D(97),)*4
        self.assertEqual(pullback(bars, 26), (False, False))
        bars[24] = (D(96),)*4
        self.assertEqual(pullback(bars, 26), (True, False))
        self.assertEqual(trend(bars, 26), (False, True))
        bars[24] = (D(104),)*4
        self.assertEqual(trend(bars, 26), (True, False))

    def test_panel_repeatable_and_dates_disjoint(self):
        start, end = WINDOWS['development']
        self.assertEqual(end, WINDOWS['validation'][0])
        self.assertEqual(WINDOWS['validation'][1], model.START)
        rows = [[t, '100', '100', '100', '100'] for t in range(start-26*3600,end+3600,3600)]
        payload = json.dumps({'error': [], 'result': {'XXBTZUSD': rows}}).encode()
        result = evaluate(payload, 'development')
        self.assertEqual(result, evaluate(payload, 'development'))
        for arms in result['accounts'].values():
            self.assertEqual(len(arms), 6)
            self.assertTrue(all(len(a['complete_day_returns']) == 3 for a in arms.values()))
            self.assertEqual(arms['cash']['net_usd'], 0)


def run(args):
    if args.mode == 'validation':
        if datetime.now(timezone.utc).timestamp() < WINDOWS['validation'][1]:
            raise ValueError('validation days have not ended')
        if not args.verified_disjoint or args.source:
            raise ValueError('require verified dataset separation and single public acquisition')
    elif args.source is None:
        raise ValueError('development requires existing retained Kraken response')
    args.out.mkdir(mode=0o700)
    if args.source:
        payload = args.source.read_bytes()
    else:
        with (args.out / 'source.private.json').open('xb') as destination:
            with urlopen(model.URL, timeout=20) as response:
                payload = response.read(CAP + 1)
            if len(payload) > CAP:
                raise ValueError('oversize Kraken response')
            destination.write(payload)
    result = evaluate(payload, args.mode)
    with (args.out / 'result.private.json').open('x') as f:
        json.dump(result, f, indent=2, default=str)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--mode', choices=WINDOWS)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--verified-disjoint', action='store_true')
    args = parser.parse_args()
    if hashlib.sha256(Path(model.__file__).read_bytes()).hexdigest() != DIGEST:
        parser.error('frozen reference digest mismatch')
    if args.test:
        unittest.main(argv=[__file__], verbosity=2)
    if not args.mode or not args.out:
        parser.error('require mode and a fresh private output directory')
    run(args)
