"""Frozen, exploratory weekly versus daily SMA50. Accounting from bar_proxy.py."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import unittest
from urllib.request import urlopen

import bar_proxy as prior
from bar_proxy import D, DAY, latch, nav, signal, size

START = int(datetime(2026, 11, 23, tzinfo=timezone.utc).timestamp())
END = int(datetime(2027, 1, 18, tzinfo=timezone.utc).timestamp())
EARLIEST_ACQUISITION = END + DAY
URL = 'https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1440'
COSTS = {'base': (D('.008'), D(0)), 'stress': (D('.01'), D('.001'))}


def validate(rows, start, end):
    times = [row[0] for row in rows]
    if times != sorted(set(times)) or any(type(t) is not int or t % DAY for t in times):
        raise ValueError('duplicate, unordered or off-grid bars')
    required = [row for row in rows if start - 51 * DAY <= row[0] < end]
    if [row[0] for row in required] != list(range(start - 51 * DAY, end, DAY)):
        raise ValueError('fixed window or warmup unavailable')
    for row in required:
        opening, high, low, close = map(D, row[1:5])
        if (not all(p.is_finite() and p > 0 for p in (opening, high, low, close))
                or not low <= min(opening, close) <= max(opening, close) <= high):
            raise ValueError('invalid OHLC')
    return times.index(start)


class WeeklySignal:
    def __init__(self, rows):
        self.rows = rows
        self.cached = None

    def at(self, index):
        if datetime.fromtimestamp(self.rows[index][0], timezone.utc).weekday() == 0:
            self.cached = signal(self.rows, index)
        if self.cached is None:
            raise ValueError('weekly evaluation must start on Monday UTC')
        return self.cached


def evaluate(rows, policy, f, s, *, start=START, end=END):
    first=validate(rows,start,end);c=D(10000);q=D(0);peak=D(10000);dd=D(0);fees=D(0);turn=D(0);fills=0;buys=0;locked=False;built=False;weights=[]
    def sample(p):
        nonlocal peak,dd,locked
        n=nav(c,q,p,f,s);peak=max(peak,n);dd=max(dd,1-n/peak)
        if latch(n,peak):locked=True
        weights.append(q*p/n)
        return n
    def sell(x,p):
        nonlocal c,q,fees,turn,fills
        if x<=0:return
        notional=x*p*(1-s);c+=notional*(1-f);q-=x;fees+=notional*f;turn+=notional;fills+=1
    last = first + (end - start) // DAY
    weekly = WeeklySignal(rows)
    for i in range(first, last):
        signal_on = (weekly.at(i) if policy == 'weekly' else
                     signal(rows, i) if policy == 'sma50' else False)
        p=D(rows[i][1]);close=D(rows[i][4]);opening=sample(p)
        on=(policy=='hold' or (policy in ('sma50', 'weekly') and signal_on)) and not locked
        a=p*(1+s)*(1+f)
        if policy!='cash':
            if not on:sell(q,p)
            else:
                n=nav(c,q,p,f,s)
                sell(max(D(0),q-D('.10')*n/a),p)
                if policy in ('sma50', 'weekly') or not built:
                    x=size(c,q,p,f,s)
                    if x>0:
                        notional=x*p*(1+s);c-=notional*(1+f);q+=x;fees+=notional*f;turn+=notional;fills+=1;buys+=1
                    if policy=='hold' and abs(D('.10')*nav(c,q,p,f,s)-q*a)<=D('1e-20'):built=True
        sample(p)
        ending=sample(close)
        if ending<=D('.99')*opening:locked=True
    final=nav(c,q,D(rows[last-1][4]),f,s)
    return dict(policy=policy,final_nav=str(final),net_usd=str(final-10000),net_pct=str(100*(final/10000-1)),sampled_drawdown_pct=str(dd*100),paid_fees=str(fees),exit_reserve=str(q*D(rows[last-1][4])*(1-(1-s)*(1-f))),turnover=str(turn),fills=fills,buy_fills=buys,mean_gross_marked_weight_pct=str(sum(weights)/len(weights)*100),max_gross_marked_weight_pct=str(max(weights)*100),locked=locked,hold_built=built,cash=str(c),btc=str(q))


def run(output):
    if datetime.now(timezone.utc).timestamp() < EARLIEST_ACQUISITION:
        raise ValueError('evaluation acquisition date has not arrived')
    output.mkdir()
    with urlopen(URL, timeout=20) as response:
        payload = response.read(2 * 1024 * 1024 + 1)
    if len(payload) > 2 * 1024 * 1024:
        raise ValueError('oversize OHLC response')
    (output / 'source.private.json').write_bytes(payload)
    data = json.loads(payload)
    if data['error']:
        raise ValueError('Kraken API error')
    closed_rows = data['result']['XXBTZUSD'][:-1]
    validate(closed_rows, START, END)
    results = {}
    for scenario, (fee, slippage) in COSTS.items():
        accounts = {arm: evaluate(closed_rows, arm, fee, slippage)
                    for arm in ('weekly', 'sma50', 'hold', 'cash')}
        results[scenario] = {
            'accounts': accounts,
            'weekly_minus': {
                arm: {'net_usd': str(D(accounts['weekly']['net_usd']) - D(accounts[arm]['net_usd'])),
                      'net_pp': str(D(accounts['weekly']['net_pct']) - D(accounts[arm]['net_pct'])),
                      'turnover_usd': str(D(accounts['weekly']['turnover']) - D(accounts[arm]['turnover']))}
                for arm in ('sma50', 'hold', 'cash')
            }
        }
    result = {'model': 'weekly-signal-bar-proxy', 'closed_bars': 56,
              'start_utc': '2026-11-23T00:00:00Z', 'end_exclusive_utc': '2027-01-18T00:00:00Z',
              'input_sha256': hashlib.sha256(payload).hexdigest(), 'results': results}
    (output / 'result.private.json').write_text(json.dumps(result, indent=2) + chr(10))


class WeeklyTests(unittest.TestCase):
    def fixture(self):
        return [[START + i * DAY, '100', '100', '100', '100'] for i in range(-51, 56)]

    def test_monday_leakage(self):
        rows = self.fixture()
        rows[50][4] = rows[51][4] = '200'
        self.assertFalse(WeeklySignal(rows).at(51))
        rows[49][4] = '101'
        self.assertTrue(WeeklySignal(rows).at(51))

    def test_cache_ignores_midweek_crossover(self):
        rows = self.fixture()
        weekly = WeeklySignal(rows)
        self.assertFalse(weekly.at(51))
        for i in range(52, 58):
            rows[i - 2][4] = '101'
            self.assertTrue(signal(rows, i))
            self.assertFalse(weekly.at(i))
        rows[56][4] = '102'
        self.assertTrue(weekly.at(58))

    def test_midweek_lock_overrides_cached_signal(self):
        rows = self.fixture()
        rows[49][2] = rows[49][4] = '101'
        rows[52][3:5] = ['40', '40']
        for i in range(53, len(rows)):
            rows[i][1:5] = ['40'] * 4
        result = evaluate(rows, 'weekly', *COSTS['base'])
        self.assertTrue(result['locked'])
        self.assertEqual(D(result['btc']), 0)
        self.assertEqual(result['buy_fills'], 2)

    def test_cutoff_and_warmup(self):
        rows = self.fixture()
        baseline = evaluate(rows, 'weekly', *COSTS['base'])
        self.assertEqual(baseline, evaluate(rows + [[END, '200', '200', '200', '200']],
                                            'weekly', *COSTS['base']))
        self.assertEqual(D(baseline['final_nav']), 10000)
        self.assertEqual(baseline['fills'], 0)
        for bad in (rows[:-1], rows[1:], rows + [rows[-1]],
                    rows[:-1] + [[rows[-1][0] + 1, *rows[-1][1:]]]):
            with self.assertRaises(ValueError):
                evaluate(bad, 'weekly', *COSTS['base'])

    def test_baselines_exactly_match_frozen_evaluator(self):
        rows = prior.Tests().fixture()
        for i, row in enumerate(rows):
            value = str(100 + i % 17)
            row[1:5] = [value] * 4
        for fee, slippage in COSTS.values():
            for arm in ('sma50', 'hold', 'cash'):
                self.assertEqual(evaluate(rows, arm, fee, slippage, start=prior.START, end=prior.END),
                                 prior.evaluate(rows, arm, fee, slippage))

    def test_fees_and_exit_reserve(self):
        rows = self.fixture()[:52]
        rows[49][2] = rows[49][4] = '101'
        for scenario, cost in COSTS.items():
            result = evaluate(rows, 'weekly', *cost, end=START + DAY)
            qty = D(result['btc'])
            buy_price, liquidation = ((D(100), D('99.2')) if scenario == 'base'
                                      else (D('100.1'), D('98.901')))
            expected_fee = D(250) - qty * buy_price
            self.assertEqual(result['buy_fills'], 1)
            self.assertAlmostEqual(D(result['cash']), D(9750), places=25)
            self.assertAlmostEqual(D(result['paid_fees']), expected_fee, places=25)
            self.assertAlmostEqual(D(result['exit_reserve']), qty * (100 - liquidation), places=25)
            self.assertAlmostEqual(D(result['final_nav']), 9750 + qty * liquidation, places=25)


if __name__ == '__main__':
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--test', action='store_true')
    cli.add_argument('--verified-disjoint', action='store_true',
                     help='attest that the project ledger verifies separation from confirmation')
    cli.add_argument('--out', type=Path, help='fresh private output directory')
    args = cli.parse_args()
    if args.test:
        suite = unittest.TestSuite(unittest.defaultTestLoader.loadTestsFromTestCase(case)
                                  for case in (prior.Tests, WeeklyTests))
        raise SystemExit(not unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful())
    if not args.verified_disjoint or args.out is None:
        cli.error('evaluation requires verified date separation and a fresh private output directory')
    run(args.out)
