# Fixed historical Kraken hourly replay

Architect owns one immediate exploratory replay on the completed interval **[2026-11-18 00:00, 2026-11-21 00:00) UTC**. Freeze this plan before opening prices or outcomes. The 72 evaluation bars and 26 contiguous warm-up bars beginning November 16 at 22:00 UTC avoid the previously evaluated 144-day window, both registered windows starting November 23, and the separate confirmation protocol, which has no active run in the visible project queue. The latest Manager receipt is `fe2ba96`. The dates were selected by calendar and data boundaries.

Use the exact `prices` and `evaluate` functions from Architect commit `06469335b9342bc9a32459462a7a3a4b15167200` with only the historical boundaries supplied as arguments. The evaluator, account rules, signal delay and 24h entry/12h exit remain fixed. The separate future-date gate still applies to the registered workflow. This user-authorized historical replay has its own output directory and acquisition wrapper.

Make one bounded request to the official public Kraken Spot XBT/USD hourly OHLC endpoint. Require the exact pair, no API error, discard the final uncommitted row and validate the fixed interval and warm-up. No other provider, alternative dates or parameter search. Keep raw response, hash and precise outputs private. Claim a fresh private directory before requesting data. Missing eligibility produces a blocker receipt.

Report every arm and every modeled UTC day. Base uses a 0.8% fee per side. Stress uses 1% per side and 10 bp adverse slippage per side. Each reports breakout, cash, 2.5% budget hold and full hold on matched input. Include net USD and percent, fees, final reserve, turnover, fills, sampled drawdown and 50% modeled-day count. These are historical exploratory paper estimates.

Acknowledge Capture `b10bc8f`: BOOK-SOURCE-01 supports short CRC and readback evidence and SOURCE-SCREEN-01 found no qualifying sealed day. Capture retains sealed-source ownership. This direct public OHLC request is separate from Capture's source acquisition and guards. Manager owns queue reconciliation. No live or operational financial claim follows from this replay.
