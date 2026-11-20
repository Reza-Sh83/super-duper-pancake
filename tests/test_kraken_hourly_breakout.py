import json
import unittest
from decimal import Decimal, localcontext

from tools import kraken_hourly_breakout as study

D = Decimal
I = study.WARMUP


class HourlyBreakoutTests(unittest.TestCase):
    def test_fixed_window_and_excluded_endpoint(self):
        rows = study.synthetic_rows()
        baseline = study.evaluate_fixture(rows)
        self.assertEqual(baseline, study.evaluate_fixture(
            rows + [[study.END, "999999", "999999", "1", "1"]]))
        self.assertEqual(baseline["coverage"], {"hours": 504, "warmup_hours": 26,
                                              "complete_utc_days": 21})
        self.assertEqual(baseline["scope"], "SYNTHETIC_FIXTURE_ONLY")

    def test_kraken_response_drops_uncommitted_row_and_requires_pair(self):
        rows = study.synthetic_rows()
        response = {"error": [], "result": {"XXBTZUSD": rows + [[study.END]], "last": study.END}}
        self.assertEqual(study.kraken_closed_rows(json.dumps(response)), rows)
        response["result"]["ETHUSD"] = response["result"].pop("XXBTZUSD")
        with self.assertRaisesRegex(study.BlockedInput, "unexpected Kraken pair"):
            study.kraken_closed_rows(json.dumps(response))

    def test_incomplete_duplicate_off_grid_and_invalid_rows(self):
        original = study.synthetic_rows()
        for rows in (original[1:], original[:I] + original[I+1:],
                     original[:-1], original[:I] + original[I-1:]):
            with self.subTest(length=len(rows)), self.assertRaises(study.BlockedInput):
                study.fixed_bars(rows)
        for column, value in ((0, study.START+1), (1, "NaN"), (1, "0"),
                              (1, 100.0), (2, "90"), (3, "Infinity")):
            rows = study.synthetic_rows()
            rows[I][column] = value
            with self.subTest(column=column, value=value), self.assertRaises(study.BlockedInput):
                study.fixed_bars(rows)

    def test_strict_ranges_exclude_signal_bar_high_and_low(self):
        rows = study.synthetic_rows()
        bars = study.fixed_bars(rows)
        self.assertEqual(study.signals(bars, I), (True, False))
        self.assertEqual(study.signals(bars, I+2), (False, True))
        rows[I-2][2:4] = ["1000", "1"]
        self.assertEqual(study.signals(study.fixed_bars(rows), I), (True, False))
        rows[I-2][4] = "101"
        self.assertEqual(study.signals(study.fixed_bars(rows), I), (False, False))
        rows[I-2][4] = "99"
        self.assertEqual(study.signals(study.fixed_bars(rows), I), (False, False))

    def test_known_entry_exit_and_no_open_lookahead(self):
        original = study.synthetic_rows()
        base = study.evaluate_fixture(original)["arms"]["base"]["breakout"]["fills"]
        self.assertEqual([(f["utc"], f["side"], f["reason"]) for f in base[:2]],
                         [(study.START, "buy", "breakout"), (study.START+2*study.HOUR, "sell", "range_exit")])
        rows = study.synthetic_rows()
        rows[I-1][1:5] = ["700", "900", "1", "800"]
        rows[I][2:5] = ["1000", "1", "900"]
        self.assertEqual(study.signals(study.fixed_bars(rows), I), (True, False))
        changed = study.evaluate_fixture(rows)["arms"]["base"]["breakout"]["fills"][0]
        self.assertEqual(changed, base[0])
        rows[I][1] = "200"
        changed = study.evaluate_fixture(rows)["arms"]["base"]["breakout"]["fills"][0]
        self.assertEqual(changed["execution_usd"], D(200))
        self.assertNotEqual(changed["qty_btc"], base[0]["qty_btc"])

    def test_hand_checked_fees_and_liquidation_reserve_in_both_models(self):
        result = study.evaluate_fixture(study.synthetic_rows())["arms"]
        with localcontext() as ctx:
            ctx.prec = 34
            for name, fee, slip in (("base", D(".008"), D(0)),
                                    ("stress", D(".01"), D(".001"))):
                arm = result[name]["hold_2_5_percent"]
                quantity = D(250)/(100*(1+slip)*(1+fee))
                expected_fee = quantity * (100*(1+slip)) * fee
                expected_reserve = quantity * (100*(1-slip)) * fee
                self.assertAlmostEqual(arm["fees_usd"], expected_fee, places=27)
                self.assertAlmostEqual(arm["exit_fee_reserve_usd"], expected_reserve, places=27)
                expected_nav = D(9750) + quantity*(100*(1-slip)) - expected_reserve
                self.assertAlmostEqual(arm["nav_usd"], expected_nav, places=27)
                self.assertEqual([fill["side"] for fill in arm["fills"]], ["buy"])
                strategy = result[name]["breakout"]
                self.assertLessEqual(strategy["fills"][0]["gross_usd"] + strategy["fills"][0]["fee_usd"], D(250))
                self.assertEqual(strategy["fees_usd"],
                                 sum(fill["fee_usd"] for fill in strategy["fills"]))
                cash = result[name]["cash"]
                self.assertEqual((cash["turnover_usd"], cash["fees_usd"], cash["net_usd"],
                                  cash["days_at_least_50_percent"]), (0, 0, 0, 0))
                self.assertEqual(len(cash["daily_outcomes"]), 21)

    def test_utc_midnight_uses_previous_close_then_next_open(self):
        rows = study.synthetic_rows()
        rows[I+23][1:5] = ["100", "121", "99", "120"]
        rows[I+24][1:5] = ["130", "131", "99", "100"]
        hold = study.evaluate_fixture(rows)["arms"]["base"]["hold_full"]
        first, second = hold["daily_outcomes"][:2]
        self.assertEqual(first["end_exclusive"], second["start"])
        self.assertEqual(second["start"], study.START + study.DAY)
        self.assertGreater(second["opening_nav_usd"], first["closing_nav_usd"])
        self.assertEqual(hold["daily_outcomes"][-1]["end_exclusive"], study.END)

    def test_loss_and_drawdown_thresholds_inclusive_and_risk_precedes_entry(self):
        daily = study.Account(D(0), D(0), cash=D(9800), btc=D(1))
        daily.observe(D(100), study.START, "pre_open", True)
        self.assertEqual(set(daily.locks), {"daily_loss"})
        daily.act(D(100), study.START, (True, False))
        daily.act(D(105), study.START+study.HOUR, (True, False))
        self.assertEqual([f["reason"] for f in daily.fills], ["risk_lock"])
        drawdown = study.Account(D(0), D(0), cash=D(9500), btc=D(1), day_open=D(9600))
        drawdown.observe(D(100), study.START, "close", True)
        self.assertEqual(set(drawdown.locks), {"drawdown"})
        self.assertEqual(drawdown.btc, 1)
        drawdown.act(D(90), study.START+study.HOUR, (True, True))
        self.assertEqual(drawdown.fills[-1]["reason"], "risk_lock")
        self.assertEqual(drawdown.btc, 0)

    def test_passive_trim_only_for_strategy_and_no_same_open_reentry(self):
        account = study.Account(D(".008"), D(0), cash=D(9500), btc=D(30))
        price = D(100)
        account.act(price, study.START, (True, False))
        self.assertEqual(account.fills[-1]["reason"], "exposure_trim")
        self.assertAlmostEqual(account.btc*price, D(".10")*account.nav(price), places=20)
        account.act(price, study.START+study.HOUR, (True, True))
        self.assertEqual([row["side"] for row in account.fills], ["sell", "sell"])
        self.assertEqual(account.btc, 0)
