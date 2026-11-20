"""Preregistered exploratory Kraken Spot BTC/USD hourly bar proxy."""
import argparse
from datetime import datetime, timezone
from decimal import Decimal as D, getcontext
import hashlib
import json
from pathlib import Path
import unittest
from urllib.request import urlopen

getcontext().prec = 34
HOUR = 3600
DAY = 24 * HOUR
START = int(datetime(2026, 11, 23, tzinfo=timezone.utc).timestamp())
END = int(datetime(2026, 12, 14, tzinfo=timezone.utc).timestamp())
URL = 'https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=60'
COSTS = {'base': (D('.008'), D(0)), 'stress': (D('.01'), D('.001'))}
ARMS = ('breakout', 'cash', 'hold_small', 'hold_full')
INITIAL = D(10000)


def prices(rows, start=START, end=END):
    selected = [row for row in rows if start - 26 * HOUR <= row[0] < end]
    ticks = [row[0] for row in selected]
    if any(type(t) is not int for t in ticks) or ticks != list(range(start - 26 * HOUR, end, HOUR)):
        raise ValueError('incomplete, duplicate or off-grid hourly input')
    result = []
    for _, o, h, l, c, *_ in selected:
        o, h, l, c = map(D, (o, h, l, c))
        if not all(p.is_finite() and p > 0 for p in (o, h, l, c)) or not l <= min(o, c) <= max(o, c) <= h:
            raise ValueError('invalid OHLC')
        result.append((o, h, l, c))
    return result


def signals(bars, i):
    close = bars[i - 2][3]
    return (close > max(row[1] for row in bars[i-26:i-2]),
            close < min(row[2] for row in bars[i-14:i-2]))


class Account:
    def __init__(self, fee, slip, stops):
        self.fee, self.slip, self.stops = fee, slip, stops
        self.cash, self.btc = INITIAL, D(0)
        self.peak, self.drawdown = INITIAL, D(0)
        self.fees = self.turnover = D(0)
        self.fills = 0
        self.daily_lock = self.drawdown_lock = False
        self.exposures = []
        self.days = []

    def mark_per_btc(self, price):
        return price * (1 - self.slip) * (1 - self.fee)

    def sample(self, price, day_open):
        nav = self.cash + self.btc * self.mark_per_btc(price)
        self.peak = max(self.peak, nav)
        self.drawdown = max(self.drawdown, 100 * (1 - nav / self.peak))
        self.exposures.append(100 * self.btc * price / nav)
        if self.stops:
            self.daily_lock |= nav <= D('.99') * day_open
            self.drawdown_lock |= nav <= D('.96') * self.peak
        return nav

    def buy(self, qty, price, *, spend=None):
        if qty <= 0:
            return
        gross = qty * price * (1 + self.slip)
        fee = gross * self.fee
        self.cash -= gross + fee if spend is None else spend
        self.btc += qty
        self.fees += fee
        self.turnover += gross
        self.fills += 1

    def sell(self, qty, price):
        if qty <= 0:
            return
        gross = qty * price * (1 - self.slip)
        fee = gross * self.fee
        self.cash += qty * self.mark_per_btc(price)
        self.btc -= qty
        self.fees += fee
        self.turnover += gross
        self.fills += 1


def evaluate(bars, arm, fee, slip, start=START):
    account = Account(fee, slip, arm == 'breakout')
    day_open = INITIAL
    for i in range(26, len(bars)):
        t = start + (i - 26) * HOUR
        opening, _, _, close = bars[i]
        if t % DAY == 0:
            day_open = account.cash + account.btc * account.mark_per_btc(opening)
        nav = account.sample(opening, day_open)
        cost = opening * (1 + slip) * (1 + fee)
        mark = account.mark_per_btc(opening)
        if arm == 'breakout':
            enter, leave = signals(bars, i)
            if account.daily_lock or account.drawdown_lock or (account.btc and leave):
                account.sell(account.btc, opening)
            elif account.btc:
                account.sell(max(D(0), account.btc - D('.10') * nav / opening), opening)
            elif enter:
                qty = min(account.cash / cost, D('.025') * nav / cost,
                          D('.10') * nav / (cost + D('.10') * (cost - mark)))
                account.buy(qty, opening)
        elif i == 26 and arm in ('hold_small', 'hold_full'):
            spend = INITIAL * (D('.025') if arm == 'hold_small' else D(1))
            account.buy(spend / cost, opening, spend=spend)
        account.sample(opening, day_open)
        nav = account.sample(close, day_open)
        if (t + HOUR) % DAY == 0:
            account.days.append({
                'day_utc': datetime.fromtimestamp(t, timezone.utc).date().isoformat(),
                'net_usd': nav - day_open,
                'net_pct': 100 * (nav / day_open - 1),
            })
    daily = [d['net_pct'] for d in account.days]
    return {
        'net_usd': nav - INITIAL, 'net_pct': 100 * (nav / INITIAL - 1),
        'paid_fees_usd': account.fees, 'turnover_usd': account.turnover, 'fills': account.fills,
        'exit_reserve_usd': account.btc * (close - account.mark_per_btc(close)),
        'sampled_max_drawdown_pct': account.drawdown,
        'mean_exposure_pct': sum(account.exposures) / len(account.exposures),
        'peak_exposure_pct': max(account.exposures),
        'daily_lock': account.daily_lock, 'drawdown_lock': account.drawdown_lock,
        'complete_day_returns': account.days, 'at_least_50_pct_modeled_days': sum(x >= 50 for x in daily),
        'best_day_pct': max(daily, default=None), 'worst_day_pct': min(daily, default=None),
        'coverage_hours': len(bars) - 26,
    }


def run(output):
    if datetime.now(timezone.utc).timestamp() < END + DAY:
        raise ValueError('fixed acquisition date has not arrived')
    output.mkdir(mode=0o700)
    with urlopen(URL, timeout=20) as response:
        payload = response.read(2 * 1024 * 1024 + 1)
    if len(payload) > 2 * 1024 * 1024:
        raise ValueError('oversize OHLC response')
    (output / 'source.private.json').write_bytes(payload)
    data = json.loads(payload)
    if data['error']:
        raise ValueError('Kraken OHLC error')
    bars = prices(data['result']['XXBTZUSD'][:-1])
    accounts = {name: {arm: evaluate(bars, arm, *costs) for arm in ARMS}
                for name, costs in COSTS.items()}
    comparisons = {name: {arm: values['breakout']['net_pct'] - values[arm]['net_pct']
                          for arm in ('hold_small', 'hold_full', 'cash')}
                   for name, values in accounts.items()}
    report = {'start_utc': datetime.fromtimestamp(START, timezone.utc).isoformat(),
              'end_exclusive_utc': datetime.fromtimestamp(END, timezone.utc).isoformat(),
              'accounts': accounts, 'breakout_minus_controls_pp': comparisons,
              'acquired_utc': datetime.now(timezone.utc).isoformat(),
              'input_sha256': hashlib.sha256(payload).hexdigest(),
              'validated_execution_target': 'NOT_EVALUATED_BAR_PROXY_ONLY'}
    (output / 'result.private.json').write_text(json.dumps(report, default=str, indent=2) + '\n')


class SyntheticTests(unittest.TestCase):
    def test_prior_range_and_strict_boundaries(self):
        flat = (D(100),) * 4
        bars = [flat] * 29
        self.assertEqual(signals(bars, 26), (False, False))
        bars[24] = (D(100), D(250), D(25), D(101))
        self.assertEqual(signals(bars, 26), (True, False))
        bars[25] = bars[26] = (D(999),) * 4
        self.assertEqual(signals(bars, 26), (True, False))
        bars[24] = (D(99),) * 4
        self.assertEqual(signals(bars, 26), (False, True))

    def test_input_grid_and_cutoff(self):
        rows = [[START+i*HOUR, '100', '100', '100', '100'] for i in range(-26, 505)]
        result = prices(rows)
        self.assertEqual(len(result), 530)
        self.assertEqual(result, prices(rows[:-1]))
        for invalid in (rows[1:], rows[:27]+rows[28:], rows[:2]+rows[1:]):
            with self.assertRaises(ValueError):
                prices(invalid)

    def test_cash_fees_reserve_and_midnight(self):
        flat = [(D(100),)*4] * 74
        for name, (fee, slip) in COSTS.items():
            cash = evaluate(flat, 'cash', fee, slip)
            self.assertEqual((cash['turnover_usd'], cash['net_pct'], cash['fills']), (0, 0, 0))
            r = evaluate(flat, 'hold_small', fee, slip)
            qty = D(250) / (100 * (1 + fee) * (1 + slip))
            self.assertAlmostEqual(r['paid_fees_usd'], qty * 100 * (1 + slip) * fee, places=26)
            self.assertAlmostEqual(r['exit_reserve_usd'], qty * 100 * (1 - (1-slip)*(1-fee)), places=26)
            self.assertEqual(len(r['complete_day_returns']), 2)
            self.assertEqual(r['complete_day_returns'][1]['net_pct'], 0)

    def test_boundary_marks_separate_close_from_next_open(self):
        bars = [(D(100),) * 4] * 74
        bars[50:] = [(D(200),) * 4] * 24
        result = evaluate(bars, 'hold_full', D(0), D(0))
        first, second = result['complete_day_returns']
        self.assertEqual((first['day_utc'], second['day_utc']), ('2026-11-23', '2026-11-24'))
        self.assertEqual((first['net_pct'], second['net_pct']), (0, 0))
        self.assertEqual(result['net_pct'], 100)

    def test_inclusive_locks(self):
        acct = Account(D(0), D(0), True)
        acct.cash = D(9900)
        acct.sample(D(100), INITIAL)
        self.assertTrue(acct.daily_lock)
        acct.cash = D(9600)
        acct.sample(D(100), D(9600))
        self.assertTrue(acct.drawdown_lock)

    def test_breakout_entry_exit_and_lock_precedence(self):
        bars = [(D(100),)*4] * 50
        bars[24] = (D(101),)*4
        bars[25] = (D(99),)*4
        result = evaluate(bars, 'breakout', *COSTS['base'])
        self.assertEqual(result['fills'], 2)
        self.assertLess(result['net_usd'], 0)
        self.assertEqual(result['exit_reserve_usd'], 0)
        bars[25] = (D(100),)*4
        bars[26] = (D(100), D(100), D(50), D(50))
        result = evaluate(bars, 'breakout', *COSTS['base'])
        self.assertTrue(result['daily_lock'])
        self.assertEqual(result['fills'], 2)
        self.assertEqual(result['exit_reserve_usd'], 0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--test', action='store_true')
    parser.add_argument('--verified-disjoint', action='store_true')
    parser.add_argument('--out', type=Path)
    args = parser.parse_args()
    if args.test:
        unittest.main(argv=[__file__], verbosity=2)
    elif args.verified_disjoint and args.out:
        run(args.out)
    else:
        parser.error('evaluation requires a fresh private output path and verified date separation')
