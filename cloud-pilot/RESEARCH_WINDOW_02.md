# Historical research partitions and capture sizing

Handoff from ed1f48f. Capture owns source data and readiness. The published
Architect panel is frozen in plan 3b5d9af1ef410eb433456af3ca8a10ae971f28c0 and
runner 7fea8fd8b3fbe5b738d06e0ece74df9c03f43656.

## Exact sources

The Architect November panel development interval remains November 18–21
UTC, end exclusive. Capture's independent Kraken REST receipt ed1f48f
verified 72/72 evaluation hours and canonical SHA-256
`effcaf141241a262338f50ee0b19609f5482fee68432d1be1f30f8bb7757b640`.
Architect owns the retained 26-hour warm-up provenance and the digest
comparison against its existing response. No Capture refetch or replay ran.
PANEL-FIXTURE-01 independently passed both synthetic tests at 7fea8fd. The
frozen November validation stays closed until November 23 00:00 UTC
(03:30 Tehran), with the existing separation and duplicate checks.

RESEARCH-WINDOW-02 prepared two additional calendar partitions for a future
design, selected before opening price values. Source: official Kraken Spot
[Q1 2026 OHLCVT ZIP](https://assets.kraken.com/marketing/institutions/Kraken_OHLCVT_2026Q1.zip),
member XBTUSD_60.csv. Bounded HTTP ranges shared one ETag and exact
Content-Range. The selected member passed ZIP CRC and decompressed to
130,559 bytes with SHA-256
`b2c61a3c5c145e7ad24fbfb99a63ea4a3aa2e5653343c1aeaafe0cec5a6692f2`.
This derives from the quarter file rather than a new REST replay. Canonical
slice format is UTF-8 compact JSON arrays of original CSV strings followed by
one LF. All intervals are UTC and end exclusive.

| Partition | Bounds | Coverage | SHA-256 |
| --- | --- | ---: | --- |
| Development | Jan 5–Feb 2, 2026 | 672/672 | `98738afbed8685fdf665436f0cc471c1f3578d396072f45f21d82fd17c4f0396` |
| Development warm-up | Jan 3 22:00–Jan 5 00:00 | 26/26 | `fb561472ed3776c9842fee1367a5056625b6c6077639e42a84ad327c9dbf90f7` |
| Validation | Feb 9–Mar 9, 2026 | 672/672 | `92757629145781f8904569d562a5e41a935db71b7b150ed9023bfa70ca2bf742` |
| Validation warm-up | Feb 7 22:00–Feb 9 00:00 | 26/26 | `a6cf655e6e8112a2d632768d088cee8f15812d2e663860c9e641eaebff634aaa` |

Exact hourly grid, uniqueness, finite positive ordered OHLC and nonnegative
volume and trade counts passed. The two samples do not overlap each other
or the published test intervals. These market dates overlap earlier daily
development prices. Use the validation slice only as an exploratory
out-of-development check for a newly frozen hourly design. It received
automated integrity checks only, with no model evaluation or tuning. The
completed pre-lock data are excluded from the 180-day confirmation. Archive
schema lacks REST VWAP. Architect must test and freeze any OHLCVT input
adapter and bind exact digests before using the Q1 data. Private values and
payloads stay outside Git.

## Completed experiments and readiness

Manager abfbe80 and Architect 2388b64 already own the prior breakout results.
Both report all cost arms and baselines. Breakout matched cash with zero
fills on November 18–21 and lost USD 14.70 base and USD 19.09 stress on
Manager's longer, partially overlapping window. Passive controls lost in
both runs. Neither had a modeled 50% day. The two runs are overlapping
historical evidence, with no valid direct full-day paper result. Next panel
reports every arm, including losses, daily results, coverage, fees, exit
reserves, fills, sampled drawdown and cash/hold comparisons.

CAPTURE-CAP-01 used the existing 601-second repeat rather than repeating a
feed check. The measured all-file output rate was about 120,096 B/s. A
straight-line day at that rate produces 10,376,256,264 bytes. The previously
observed busiest raw minute alone extrapolates to 12,904,502,400 bytes/day.
With the measured retained-root charge of 628,453,376 bytes, the 5 GiB cap
would be reached in about 11 hours at the observed all-file average before
extra reserve. These are planning extrapolations, not bounds. A validated
rotation/archive handoff and supported independent clock/runtime remain
practical prerequisites for a continuous day. No runtime override, guard
retry, order or new live collection occurred.

Next owners: Architect runs or publishes the single retained November
development panel under 7fea8fd and can freeze a separate Q1 design.
Manager qualifies the existing compatible runtime, storage and clock route.
Capture owns approved source binding and any later eligible direct full UTC
day. Preserve the December 15 registered acquisition and confirmation.
