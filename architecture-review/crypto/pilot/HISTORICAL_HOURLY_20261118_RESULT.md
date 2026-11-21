# Completed historical Kraken hourly replay

**Exploratory paper estimates.** Fixed plan `b1e7a8893a99decf497a9e5e4b432df63351ea93`. The single official Kraken Spot BTC/USD request supplied all 72 required closed hourly bars in **[November 18, November 21) UTC, 2026** and all 26 preceding warm-up bars after removing the final uncommitted row. The replay used `prices` and `evaluate` from exact frozen model `06469335b9342bc9a32459462a7a3a4b15167200`, passing the published historical dates and leaving model rules fixed. One request and one replay completed. Raw response, wrapper and full-precision result remain private.

Each account started at USD 10,000. Base charges 0.8% per side. Stress charges 1% per side plus 10 bp adverse slippage. Exit reserve includes modeled liquidation fee and slippage and is already reflected in NAV. Drawdown is the maximum across sampled marks. Hold refers to either the 2.5% entry budget or the fully invested passive control.

| Cost | Account | Net USD | Net % | Fees paid USD | Exit reserve USD | Turnover USD | Fills | Sampled drawdown % |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | Breakout | 0.00 | 0.0000 | 0.00 | 0.00 | 0.00 | 0 | 0.0000 |
| Base | Cash | 0.00 | 0.0000 | 0.00 | 0.00 | 0.00 | 0 | 0.0000 |
| Base | 2.5% hold | -26.99 | -0.2699 | 1.98 | 1.80 | 248.02 | 1 | 0.2877 |
| Base | Full hold | -1,079.59 | -10.7959 | 79.37 | 71.94 | 9,920.63 | 1 | 11.5094 |
| Stress | Breakout | 0.00 | 0.0000 | 0.00 | 0.00 | 0.00 | 0 | 0.0000 |
| Stress | Cash | 0.00 | 0.0000 | 0.00 | 0.00 | 0.00 | 0 | 0.0000 |
| Stress | 2.5% hold | -28.32 | -0.2832 | 2.48 | 2.46 | 247.52 | 1 | 0.3010 |
| Stress | Full hold | -1,132.95 | -11.3295 | 99.01 | 98.53 | 9,900.99 | 1 | 12.0388 |

## Daily results

Each cell is net USD / net %. Dates are UTC in November 2026. The breakout and cash accounts returned 0.00 / 0.0000% on each of the three days in both cost scenarios.

| Cost | Account | Nov 18 | Nov 19 | Nov 20 |
| --- | --- | ---: | ---: | ---: |
| Base | 2.5% hold | -11.14 / -0.1114% | -4.06 / -0.0407% | -11.78 / -0.1180% |
| Base | Full hold | -445.78 / -4.4578% | -162.46 / -1.7004% | -471.34 / -5.0186% |
| Stress | 2.5% hold | -12.57 / -0.1257% | -4.04 / -0.0404% | -11.71 / -0.1173% |
| Stress | Full hold | -502.93 / -5.0293% | -161.49 / -1.7004% | -468.52 / -5.0186% |

Breakout placed no modeled fill and matched cash. Its net percentage was 0.2699 points above the small hold in base and 0.2832 points above it in stress. That spread comes from staying flat while passive holdings lost value. The study supplies no observation of profitability when the breakout actually trades. No risk latch fired. All eight accounts had zero modeled days at or above 50% net. Any difference between summed daily P&L and inception P&L follows the predeclared distinction between one day's closing mark and the next day's opening mark.

Capture's receipt `b10bc8f` still provides short diagnostic evidence and no eligible sealed full day. These bar estimates cannot validate bid/ask, depth, recorded fills, UTC clock or intrahour stops. The full-day 50% research objective awaits qualifying sealed direct Kraken evidence under the existing gates.

Manager owns receipt reconciliation. Capture owns any future qualifying sealed source. Architect completed this historical attempt and retains the original future-window study at `83871a3`, with its December 15 acquisition gate and confirmation-separation check. Preserve the historical artifacts privately and use this receipt rather than repeating the attempt. No active replay job remains.
