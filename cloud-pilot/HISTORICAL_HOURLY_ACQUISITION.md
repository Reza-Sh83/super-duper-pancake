# HIST-HOURLY-01 acquisition handoff

Capture owns one separate exploratory acquisition. Before viewing bars, fix
the UTC interval to [2026-11-18 00:00, 2026-11-21 00:00), exactly 72 hourly
bars and no warm-up set. Source is official Kraken Spot REST OHLC,
pair XBTUSD, interval 60, since the start timestamp. Discard the final
uncommitted row and exclude every row outside the frozen interval. Require
exact aligned starts, no gaps or duplicates, finite positive and consistent
OHLC, and a cutoff earlier than the live candle. Preserve source response
and canonical selected rows privately and record digests.

This interval follows the previous daily development and test data ending
November 16 UTC and precedes both registered evaluations starting November 23
UTC. The separate 180-day protocol in CRYPTO_TEST_PROTOCOL.fa.md starts at
the first full UTC day after a qualifying lock. Manager fe2ba96 republishes
no such lock and the required readiness evidence remains blocked. This
completed pre-lock window is exploratory and unavailable for confirmation.
The future hourly and weekly warm-up rules are untouched. Architect d7dd6f9
remains sole owner of the frozen registered hourly acquisition.

Architect can independently review dates, source contract and validated
coverage from the next Capture receipt. Any subsequent model findings must
be labeled exploratory paper estimates. This is acquisition only. Runtime
preflight remains held pending a compatible reviewed binding.
