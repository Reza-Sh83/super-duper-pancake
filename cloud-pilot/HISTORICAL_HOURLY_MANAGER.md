# Completed historical Kraken hourly exploration

Manager run `mgr-hourly-20261101-20261120-v1` evaluated **[2026-11-01 00:00, 2026-11-20 00:00) UTC**. The window and 26 warm-up hours were fixed before acquisition. One official public Kraken Spot XBT/USD hourly OHLC response supplied 456/456 evaluation hours, 26/26 warm-up hours and 19 complete modeled UTC days. Pair and API status passed; the final uncommitted row was removed. The exact `prices` and `evaluate` functions at `06469335b9342bc9a32459462a7a3a4b15167200` were used with explicit historical bounds. No parameters were tuned. Raw data, digest and full daily outcomes stay private.

These are **exploratory paper estimates** from hourly bars, delayed signals and assumed full later-open fills. Base costs are 0.8% per side and stress costs are 1% plus 10 bp adverse slippage per side. Initial NAV is USD 10,000 per account. Closing NAV includes modeled exit costs and sampled drawdown omits intrahour behavior.

| Costs | Strategy | Net USD | Net % | Paid fees USD | Exit reserve USD | Sampled max drawdown % |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Base | Breakout | -14.697429 | -0.146974 | 11.877837 | 0 | 0.146997 |
| Base | Cash | 0 | 0 | 0 | 0 | 0 |
| Base | 2.5% budget hold | -53.289554 | -0.532896 | 1.984127 | 1.586375 | 0.608388 |
| Base | Full hold | -2131.582145 | -21.315821 | 79.365079 | 63.454983 | 23.759044 |
| Stress | Breakout | -19.091262 | -0.190913 | 14.800945 | 0 | 0.190936 |
| Stress | Cash | 0 | 0 | 0 | 0 | 0 |
| Stress | 2.5% budget hold | -54.466346 | -0.544663 | 2.475248 | 2.172794 | 0.604841 |
| Stress | Full hold | -2178.653853 | -21.786539 | 99.009901 | 86.911754 | 23.759044 |

Breakout trailed cash and exceeded both hold controls. Its best modeled UTC day was +0.028069% base and +0.012945% stress. No arm reached 50% on any modeled day. The qualifying direct Kraken sealed UTC-day objective remains unevaluated.

## Separation and ownership

The entire hourly evaluation and warm-up precede both registered November 23 studies. It overlaps November 1–15 with the earlier 144-day exploratory daily-bar study. Treat it as historical exploration on partly reused market dates, with no unseen or independent confirmation claim. The visible project queue shows no active 180-day lock or accepted prerequisites. Confirmation requires post-lock direct native capture starting the next complete UTC day. These historical bars are excluded from it. Keep the future hourly acquisition gate on December 15 at 00:00 UTC (03:30 Tehran).

Manager checked the visible Git refs, local attempt and active process state before claiming one fresh private output. The later refresh found Architect plan `b1e7a8893a99decf497a9e5e4b432df63351ea93` and Capture plan `fd76b5d27a44a772c7ba4a0a14e066abac2f4ff9`, both covering November 18–21 UTC. Their publications were observed after the Manager result. Their planned window overlaps this completed historical evaluation on November 18–19. To honor the single-run request, **hold both additional historical acquisitions**. If a peer already acquired data or produced output, retain it and report the existing attempt for reconciliation. Do not start another request or evaluation. Architect owns independent review of this receipt, with raw and daily-output reconciliation only through an existing approved private handoff. Capture retains its separate qualifying sealed-source role.

Checkpoint: started clean on cloud-pilot/status at `fe2ba96`. Completed one evaluation and rechecked peer refs before publication. No Manager run remains active. Resume by fetching the peer refs and inspecting existing output and review receipts.
