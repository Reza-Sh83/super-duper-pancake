# Native Kraken L2 evidence and development replay

Source direction follows RESEARCH.fa.md §§3.1, 6.7, 13.2 and 24 and
architecture-review/crypto/CRYPTO_DECISION_BRIEF.fa.md, CRYPTO_BUILD_CONTRACT.fa.md
and CRYPTO_TEST_PROTOCOL.fa.md. Use receive order and availability, freeze
inputs and code before outcomes, purge overlapping feature-to-outcome
intervals, and reconstruct the book without intervention before testing
simulated IOC. Keep candle results as preliminary price controls. Native
message replay can consume displayed depth against a fixed subsequent tape.
It cannot identify hidden quantity, passive queue priority or market response.

## Retained source inventory

L2-INVENTORY-01 found 11 distinct raw-part identities across 16 private
manifest locations. One representative per identity passed part hash and
local ordinal checks. Seven contained books: four native recordings and
three derived harness tapes, which are not independent market samples.
Four streams contained no valid book (blocked capture and clock probes).
No retained sealed stream contained a trade-channel message or trade row.
The collector subscribes to instrument and book v2 depth 10. The separate
30-second standalone book check and 25-second ticker have no trade tape
either. OHLC trade counts cannot reconstruct prints.

| Native recording | Exchange-stamped accepted book range, UTC | Accepted / reject | Fresh CRC book / planned second slots | Disconnects |
| --- | --- | ---: | ---: | --- |
| Initial diagnostic | Nov 15 00:03:12.998726–00:13:11.965997 | 34,770 / 0 | 380/600 | 11 unclassified |
| Repeat | Nov 15 01:20:24.361951–01:30:23.698867 | 70,824 / 0 | 585/600 (595 sampled) | 1 induced, 2 queue |
| Isolated queue recording | Nov 15 02:05:10.677298–02:15:09.760837 | 90,115 / 0 | 598/600 | 1 induced |
| LIVE-PREFLIGHT-01 | Nov 21 22:26:20.356864–22:26:48.252843 | 1,031 / 0 | 28/30 | 1 induced |

All dates are 2026. All accepted states had 10 reconstructed bid and 10 ask
levels. This is displayed depth coverage, without order identities or full
venue depth. Raw manifests and WS rows separate exchange timestamps, received
UTC and receive monotonic time. Local UTC is clock-unverified. The isolated
recording's accepted receive-UTC range was 02:05:10.736169423 through
02:15:09.997004941. Longest same-epoch WS silence was 0.579 s. Its single
induced break took 2.795 s to the next CRC-valid snapshot. Local ordinal
continuity and CRC do not establish exchange-side sequence completeness.
The private inventory retains full per-stream denominators, times and
duplicate locations. Standalone BOOK-SOURCE-01 had 30/30 fresh CRC-book
samples and TICKER-01 had 25/25 seconds of transport. Neither was a sealed
ledger or a clock acceptance run.

## Bound development replay

L2-REPLAY-01 passed on the isolated 600-second native observe recording.
Exact runner package 265ca75b94f1acb0248d142876654f3b7dd29599 matched the
recorded package and dependency versions through its seal. It read both
raw parts in committed order, checked each frame digest against the source
ledger and reconstructed a memory ledger without intervention. All **91,397
committed frames and 76,009 ordered events** reconciled. Final account was
identical, zero fills, and original manifest, raw and ledger hashes stayed
unchanged.

- Manifest identity: 01309b4dcc72f8ae020d7e0cda197da1e211e0176092b6d4d5ba51091ecf3ccf
- Ordered frame identity SHA-256: 41c12678dfe5b5f22e93c121f0b2b9e93cd71386b45642660876dca7de4d7ef3
- Digest encoding: newline-delimited deterministic ledger JSON of each
  [index, canonical frame SHA-256], in index order.
- The pinned execution suite also passed X01, X02, R01 and R02. Run
  `python -m crypto_paper verify --suite execution --fixtures fixtures/crypto --out "$PRIVATE_TEST_REPORT"`
  from the recorded package. The new read-only inventory command is
  `python -m tools.inventory_kraken_recordings "$PRIVATE_ROOT" "$FRESH_PRIVATE_RECEIPT"`.
  Keep both detailed receipts private.

Scope is no-intervention development reconstruction and a negative control
for clock admission. All 12 recorded clock checks were rejected and READY
was zero. This window is ineligible for recorded OFI scoring under Manager
5aaaf51 and Architect f931f01. Implementer owns the frozen fixture-only
OFI/IOC adapter, including causal prefixes, partial fills and cancellation,
cost/depth/latency bounds and exact accounting. A later authorized native
collector can preserve trade IDs, exchange and receive timestamps and epoch
alongside the book for separate trade-flow tests. This needs reviewed schema,
queue and storage bounds before dispatch. Do not infer aggressive prints
from L2 quantity changes or synthesize clock evidence.

## Clock, archival and launch gates

Latest measured preflight still accepted 0/3 independent UTC references.
No supported replacement route was established. Manager owns qualifying a
supported route for the original references and then running the unchanged
clock check. The current environment has no managed private Google archive
binding. Manager owns authorized readback on a distinct executor.

ROLLOVER-CHECK-01 independently passed both focused tests at
f013e07d8be21281f6f33c3afe060bc3ef3b569c. Wrong and missing acknowledgments
kept evidence charged, successful local readback permitted a bounded
synthetic rollover, and both stopped archives replayed. This closes a local
fixture check. Production rotation and off-executor restore remain blocked.
Architect reviews exact production candidates. Capture launches only under
Manager's later reviewed binding with duplicate and admission checks. No
new collection, order, transfer or 48-hour launch ran. The 180-day protocol,
pilot and readiness checks retain their original scope.
