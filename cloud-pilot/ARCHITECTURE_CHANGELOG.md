# Exploratory architecture change log

Changes affect diagnostics and reliability, not demonstrated strategy returns. The 180-day confirmation protocol and production risk/UTC thresholds remain unchanged. Raw evidence and operational receipts remain private.

## Clock-independent diagnostic observer

Base: `8ca2e03`. Implementation: `8bf869afb527cac88275fd63f705a4e861695602` on cloud-pilot/capture-replay; source remained fixed throughout capture and recovered replay.

Problem: failed periodic clock checks invalidated the production book, and the diagnostic collector treated this as a reason to reconnect. This conflated clock rejection with feed/transport failure.

Change: an isolated diagnostic observer processes the same raw events using the book checksum parser. UTC failures are counted without modifying this observer's book. Diagnostic reconnect decisions use this observer; production Session retains its clock invalidation, readiness and order gates. Disconnects record induced, transport, queue, feed-validation or production-validation origin. Recovery-to-checksum-book uses monotonic time and never certifies operational READY.

Controlled comparison: identical synthetic connect/snapshot/invalid-clock/update stream. Prior production path becomes STALE and remains unable to trade; diagnostic observer stays READY, accepts both checksum-valid book events, records no disconnect, and grants no production readiness. Corrupted checksums still invalidate the diagnostic book. Synthetic disconnect/reconnect reconstructs the book and measures recovery. All 23 focused tests and eight existing data/execution checks pass.

Real-data comparison: repeat a bounded ten-minute public capture on the frozen implementation with a five-minute induced disconnect. Compare against the retained prior diagnostic. Traffic rates and market conditions differ between captures, so raw frame throughput is not a causal performance comparison. Evaluate reconnect origin, recovered book, rejected UTC checks, sample coverage, storage rate and exact ledger replay; do not infer a strategy-return improvement.

Outcome: repeat capture, sealed readback, byte-exact archive recovery and replay completed. The original measured source was retained without editing during capture or verification. Pilot remains STOPPED pending valid UTC, full operational acceptance, private seven-day retention/recovery and acknowledged no-PC report delivery. Quota/reset wake and unattended runtime are not established.


## Measured diagnostic outcome

Common observer was applied to both retained streams. These are diagnostics, not validated trading intervals. Market traffic differed, and archive/replay checks ran concurrently during part of the repeat; this is not a controlled throughput benchmark.

| Measurement | Prior capture | Frozen repeat |
| --- | --- | --- |
| Rejected clock frames | 12 | 12 |
| Book-STALE reconnects in old coupled path | 11 | No clock-triggered reconnects |
| Unexpected queue failures | Not classified in old receipt | 2 |
| Unexpected transport failures | Legacy events unclassified | 0 |
| Intentionally induced disconnects | 0 | 1 |
| Monotonic checksum-book availability / planned seconds | 380/600 (63.33%) | 585/600 (97.5%) |
| Planned seconds without a sample | 0 | 5 |
| Operational READY | 0% | 0% |
| Recovery to first CRC-valid snapshot after induced disconnect | Not tested | 2.7208 s received; 2.7213 s validated |

The isolated observer improves diagnostic continuity and failure attribution. It does not fix UTC, certify operational recovery, eliminate queue pressure or demonstrate better strategy returns. Exact snapshot identity, raw hashes, gap evidence and receipts remain private. Full 24-hour operational acceptance was not started: the clock and storage gates are blocked.

## Storage and reporting findings

Lossless archival restored both diagnostic captures byte-for-byte; replay ran against the separately extracted copies and reproduced the ledgers. The repeat compressed-evidence rate projects above the unchanged weekly cap before safety margin. Sampled simultaneous usage covered active raw segments, journals, both archives and temporary restore/replay copies; the private receipt includes category totals, peak and monitoring scope. Earlier transient peaks were not sampled. This bounded local test is not a week-long or off-environment recovery proof.

One reporting-only six-hour delivery test is scheduled. The user committed to keep the PC offline and acknowledge from mobile/web. Scheduled cloud attachment is verified; cloud execution, report generation and actual receipt remain three separate pending checks. Do not restart or reschedule this test. No regular pilot reporting or automatic quota wake is claimed.

## Separate candidate research

On an isolated memory copy of the same recorded ledger, an index on events(frame) reduced 501 lookup queries from 1.236 s to 0.00120 s with identical rows. This is a query microbenchmark under concurrent load, not an end-to-end improvement. No indexing change was applied to the measured source or source ledger; no implementation commit or strategy-return improvement is claimed for it.

Next exact implementation action: develop and benchmark a transient replay index on a separate candidate branch against the same retained ledger, preserving source-build verification and identical accounting outputs; investigate the two queue-age failures without increasing queue limits or relaxing the 500 ms age gate. Then address global archive-cap lifecycle and recovery before repeating acceptance. A supported no-cost path for all three unchanged NTP references remains necessary. Keep the pilot STOPPED.
