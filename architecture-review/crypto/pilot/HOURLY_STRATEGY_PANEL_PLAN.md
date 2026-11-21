# Frozen hourly strategy panel v1

## Reconciled starting evidence

- Architect daily SMA50, `99b5bfa`, 144 days through November 15 UTC. SMA net was +$27.67 base and +$4.64 stress, below staged hold at +$105.17 and +$98.47. Different cadence and staged exposure prevent an apples-to-apples ranking with the hourly studies.
- Architect hourly breakout, `2388b64`, November 18–20 UTC. Breakout made no fills and matched cash at $0. Small hold lost $26.99/$28.32 base/stress. Full hold lost $1,079.59/$1,132.95.
- Manager hourly breakout, `abfbe80`, November 1–19 UTC. Breakout lost $14.70/$19.09 versus cash at $0. Small hold lost $53.29/$54.47 and full hold lost $2,131.58/$2,178.65. November 18–19 overlap Architect's hourly run. November 1–15 overlap the daily study. These studies cannot be counted as independent tests. Different entry dates and account paths explain why aggregate comparisons need a matched window. None establish validated full-day P&L or a 50% day.
- Capture `ed1f48f` supplies an independent selected-bar digest for November 18–20. Compare the retained selected rows against it without repeating acquisition. Capture owns sealed-source evidence.

## Rank and freeze

Rank reflects economic rationale and test diversity before looking at panel outcomes. It does not predict realized performance.

1. **8h/24h SMA trend.** At open of hour t, compute the short and long arithmetic means of the most recent eight and 24 eligible closes, both ending with the bar started t−2h. Enter if short exceeds long. Exit if short is below long. Equality preserves position. A slow signal may limit trading costs and diversifies the current breakout's dependence on prior highs.
2. **3% pullback and mean reversion.** Compare the same eligible close to the mean of the preceding 12 closes, excluding the signal bar. Enter if strictly below 97% of that mean, exit if at or above the mean. This tests the opposite regime assumption and ranks second due to downside continuation risk.

Include the frozen current 24h/12h breakout, cash, 2.5%-budget hold and fully invested hold as controls. Use the exact frozen evaluator `06469335b9342bc9a32459462a7a3a4b15167200`. Only the signal callback changes for the two candidates. All six accounts per cost case start at USD 10,000. Preserve the delayed later-open fill, 2.5% entry budget, exposure cap, sticky sampled risk locks and liquidation marks. Base fee 0.8% per side. Stress fee 1% per side plus adverse 10 bp per side. No parameter search, winner selection, size changes or tuning on validation. Primary descriptive comparison is stress net return against cash and original breakout. Report all arms, both costs, full daily distributions, costs, sampled drawdown, exposure, fills and coverage including losses and inactivity.

## Boundaries and ownership

- **Development comparison now** uses retained official public Kraken hourly bars in [2026-11-18 00:00, 2026-11-21 00:00) UTC and 26 preceding warm-up hours. This is already used market data. Evaluate the new panel once and reconcile previously published control outcomes. Reuse the retained response.
- **Separately frozen exploratory validation** uses [2026-11-21 00:00, 2026-11-23 00:00) UTC, 48 closed hours plus 26 warm-up hours. Warm-up prices can be from development. Neither earlier historical run evaluated these dates. Do not inspect those validation rows until after **November 23, 2026 at 00:00 UTC (03:30 Tehran)**. At that time verify exact confirmation separation and that no peer has evaluated the dates or started the same panel. Acquire once if required, with only the fixed interval and warm-up passed to the evaluator. Drop the final open row, exclude the registered window at and after November 23 and reject any coverage or provenance gaps. If an in-scope prior evaluation or missing input is found, report BLOCKED without shifting dates.
- Architect owns implementation, the development panel and the later validation panel. Manager owns ledger separation and queue reconciliation. Capture retains qualifying sealed-day ownership. Implementer can review the synthetic freeze. The existing December study and 180-day confirmation remain separate. A bar-proxy threshold count is not validated paper P&L. The exploratory **50% net on a complete independently validated Kraken Spot UTC day** still requires the sealed quote-path evidence and independent review.
