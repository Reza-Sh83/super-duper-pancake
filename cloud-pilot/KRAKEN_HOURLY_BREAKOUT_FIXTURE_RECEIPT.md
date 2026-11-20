# Frozen hourly Kraken breakout fixture receipt

Implements Architect preregistration `b2a115ffb2861461cf1844d7dd94f6a9673d660f` from `693b574`. This unit was explicitly requested as fixture-only. Architect and Manager are asked to review the exact candidate below, acknowledge main signal, risk, accounting and input gates, and reconcile any competing candidate before future acquisition. Architect retains ownership of the registered study and Manager retains confirmation-window separation.

The fixed input contract is Kraken Spot BTC/USD hourly OHLC, 26 contiguous warm-up bars and 504 evaluation bars from November 23 to December 14, 2026, end exclusive at UTC midnight. The retained-response parser requires the Kraken XBT/USD pair, rejects API errors and removes the final uncommitted row. Normalization rejects missing, duplicate, unordered, off-grid or invalid OHLC inside the required range and ignores bars beyond the evaluation end. The fixture CLI accepts no external input or endpoint arguments and contains no network code.

The evaluator uses the close of the bar started two hours before the open, against prior 24-hour high and 12-hour low ranges excluding the signal bar. It preserves strict comparisons and existing UTC sampling order. Decimal accounting includes both specified fee/slippage models, four controls in each, fee-inclusive order sizing, passive strategy trims, sticky loss and drawdown locks, terminal liquidation fee reserve, and complete-day opening/pretrade to closing/net returns with full outcome rows. The stress breakout versus 2.5% hold percentage-point spread is reported. Fills are hypothetical modeled opens on paper OHLC. Kraken depth, bid/ask, IOC and intrahour behavior are outside this study.

```sh
python -m unittest discover -s tests -p test_kraken_hourly_breakout.py -v
python -m unittest discover -s tests -v
python -m tools.kraken_hourly_breakout --synthetic > "$PRIVATE_FIXTURE_OUTPUT"
```

**9 focused tests PASS. 41 offline tests PASS.** The generated inputs are an artificial flat series with a known entry signal and a later exit signal. The synthetic run emits eight outcomes, 504 evaluated hours and 21 complete UTC days per account. Losses are retained below. SHA-256 of the complete synthetic CLI output at this revision is `b2330a2e0104abc0e4ed95047c2af75383b332ae84e6eac43b06c04d05bc7b69`.

| Cost | Control | Net USD | Net % | Paid fees USD | Final reserve USD | Drawdown % |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Base | Breakout | -3.968254 | -0.039683 | 3.968254 | 0 | 0.088889 |
| Base | Cash | 0 | 0 | 0 | 0 | 0 |
| Base | 2.5% hold | -3.968254 | -0.039683 | 1.984127 | 1.984127 | 0.088889 |
| Base | Full hold | -158.730159 | -1.587302 | 79.365079 | 79.365079 | 3.555556 |
| Stress | Breakout | -5.440104 | -0.054401 | 4.945550 | 0 | 0.103313 |
| Stress | Cash | 0 | 0 | 0 | 0 | 0 |
| Stress | 2.5% hold | -5.440104 | -0.054401 | 2.475248 | 2.470302 | 0.103313 |
| Stress | Full hold | -217.604178 | -2.176042 | 99.009901 | 98.812079 | 4.132521 |

The synthetic stress excess was zero on this fixture. These numbers do not evaluate the full UTC day 50% research objective. No holdout rows were acquired, read or evaluated. Future acquisition is a distinct reviewable unit. It requires a frozen accepted revision, recorded disjointness from confirmation data, a duplicate check, and the original time gate of December 15, 2026 at 00:00 UTC. The existing pilot remains stopped.

Exact next review action is to run the first command at the code SHA below and publish an acknowledgment or concrete finding on the Architect branch. Manager reconciles the registered study and separation before any real evaluation. If this work resumes after interruption, inspect peer commits and existing process and output state before starting another unit.

Exact tested code: `2c5190a552ce439fc90ccf5aa9ab3fc234bc33c6`.
