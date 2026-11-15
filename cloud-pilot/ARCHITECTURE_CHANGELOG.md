# Exploratory architecture change log

Changes affect diagnostics and reliability, not demonstrated strategy returns. The 180-day confirmation protocol and production risk/UTC thresholds remain unchanged. Raw evidence and operational receipts remain private.

## Clock-independent diagnostic observer

Base: `8ca2e03`. Implementation: commit titled `Separate diagnostic book continuity from production clock halts` on cloud-pilot/capture-replay; exact commit is bound in the private capture launch receipt and the completed checkpoint.

Problem: failed periodic clock checks invalidated the production book, and the diagnostic collector treated this as a reason to reconnect. This conflated clock rejection with feed/transport failure.

Change: an isolated diagnostic observer processes the same raw events using the book checksum parser. UTC failures are counted without modifying this observer's book. Diagnostic reconnect decisions use this observer; production Session retains its clock invalidation, readiness and order gates. Disconnects record induced, transport, queue, feed-validation or production-validation origin. Recovery-to-checksum-book uses monotonic time and never certifies operational READY.

Controlled comparison: identical synthetic connect/snapshot/invalid-clock/update stream. Prior production path becomes STALE and remains unable to trade; diagnostic observer stays READY, accepts both checksum-valid book events, records no disconnect, and grants no production readiness. Corrupted checksums still invalidate the diagnostic book. Synthetic disconnect/reconnect reconstructs the book and measures recovery. All 23 focused tests and eight existing data/execution checks pass.

Real-data comparison: repeat a bounded ten-minute public capture on the frozen implementation with a five-minute induced disconnect. Compare against the retained prior diagnostic. Traffic rates and market conditions differ between captures, so raw frame throughput is not a causal performance comparison. Evaluate reconnect origin, recovered book, rejected UTC checks, sample coverage, storage rate and exact ledger replay; do not infer a strategy-return improvement.

Outcome at implementation checkpoint: real capture pending. Pilot remains STOPPED pending valid UTC, full operational acceptance, private seven-day retention/recovery and acknowledged no-PC report delivery. Quota/reset wake and unattended runtime are not established.
