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

## Completed acquisition receipt

HIST-HOURLY-01 passed at 2026-11-21 21:30:49 UTC (November 22 01:00:49
Tehran). One request returned HTTP 200, no Kraken API error and pair XXBTZUSD.
Selected 72/72 closed hourly bars (100%), with exact UTC-grid order, zero
missing starts and zero duplicates. Discarded one final uncommitted row and
21 other closed rows outside the interval. Checked finite positive prices,
OHLC ordering and nonnegative volume/trade counts. Readback matched SHA-256
of the canonical selected arrays (compact JSON plus final newline):

`effcaf141241a262338f50ee0b19609f5482fee68432d1be1f30f8bb7757b640`

The raw response, raw digest and all bar values stay private. This receipt
establishes source coverage, with no return evaluation in Capture's unit.

The post-acquisition refresh found Architect b1e7a8893a99decf497a9e5e4b432df63351ea93
independently fixed the same 72 evaluation hours and official endpoint. Its
separately frozen replay requires 26 preceding warm-up hours and owns that
acquisition and evaluation. Capture's artifact excludes warm-up and will not
be refetched. Architect can compare its canonical 72 evaluation rows to this
digest, record any revisions or discrepancy, and label results exploratory
paper estimates. Manager fe2ba96 retains runtime qualification ownership.
No newly authorized preflight appeared, no guarded output was created, and
no matching job was observed.
