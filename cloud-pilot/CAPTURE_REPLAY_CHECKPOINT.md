# Capture and replay checkpoint

Scope: Kraken Spot BTC/USD public data, simulation only, zero incremental spend. No main merge authorized. The 168-hour exploratory pilot remains STOPPED; the separate 180-day confirmation protocol is unchanged.

## Reviewed handoffs

- cloud-pilot/status: 100ffe7e099adc4f6bb6bfc45d78c63b176b52e8
- cloud-pilot/architecture-handoff: 0e463a8b9f789ab2587086adde9108b6d83ead54
- implementer/reproducible-install: 886589b757d9c0aa968dab9d7d5ceeb0ea344f89
- implementer/six-hour-report: c0003b80e4730687421b9e50e6dbcf4d496f1420

Work continues on a separate capture/replay branch based on the report implementation. This document contains project decisions and synthetic test summaries only. Raw market data, runtime logs, operational hashes and deployment details stay outside this repository.

## Implemented bounded unit

An explicit capture-only diagnostic option permits retention when the sole failed preflight is the independent UTC reference. It preserves invalid-clock behavior, observation-only policy, disk gates and BLOCKED operational acceptance. Other preflight errors still block collection. Collection has a duration-plus-ten-second monotonic timeout. The default capture and paper preflight criteria remain intact.

A separate read-only adapter projects sealed observe ledgers into the existing report schema in dry-run mode. It checks segment and payload hashes, every committed frame digest, capture identity, exact replay events, frame count/cursor and final account state. Active COLLECTING inputs are rejected. It retains original receive timestamps and cutoff rules. Source files are unchanged; output creation is exclusive.

Missing interval history or unverified clock suppress numeric returns and current drawdown. A diagnostic cash balance is not a validated trading result. Failed source integrity or replay also suppresses numeric returns in the underlying projector.

Current adapter scope is sealed observe ledgers only. It does not certify live committed-prefix snapshots, multiple strategy/scenario ledgers, independent accounting review, durable retention, a scheduler, delivery, or a running pilot. The requested diagnostic reporting interval does not assign a pilot T0. All outputs have pilot_started=false and operational_ready=false.

## Synthetic verification

Twenty-one report/integration tests passed: sealed readback, source immutability, segment/frame/account tampering, collection preflight separation, missing history, stale/missing mark, fees and liquidation reserve, cutoff boundaries, missing seconds, invalid-integrity suppression, report identity and exclusive output. Synthetic one-hour segment rotation and disk-floor safe-stop preserved ordered readback. Existing data and execution fixture suites passed. These are synthetic software receipts, not operational acceptance or independently reviewed paper profits.

## Measured limitations and next work

The diagnostic attempt is bounded and its operational evidence is retained privately. Clock readiness, operational acceptance, storage/recovery and actual report delivery remain release gates. A checksum-good stream does not prove UTC correctness. Clock rejection invalidates the production book; periodic failed clock refresh can therefore cause diagnostic reconnects. Classify these separately from remote transport failures before changing reconnect logic. Preserve trading halts.

Priorities:
1. Establish a supported no-cost path for all three unchanged NTP references; do not substitute HTTP time or relax thresholds.
2. Compare measured raw+journal growth with the unchanged capture cap and seven-day retention needs; prove bounded-capacity safe-stop/recovery. Available disk alone is insufficient.
3. Independently review the sealed adapter; add consistent committed-prefix snapshots and separately reconciled strategy/scenario ledgers before live six-hour reporting.
4. Verify a no-cost durable scheduler and acknowledged dry-run delivery including outage/restart behavior.
5. Only after all gates pass, assign T0 and run the approved operational acceptance and exploratory release sequence. A >=50% full-UTC-day result remains a candidate until independent review and Manager approval. The confirmation protocol remains separate.

Exact next action after the bounded diagnostic ends: verify its sealed segment and ledger hashes, reconstruct and compare the committed ledger, generate a dry-run unavailable six-hour report, and retain the complete metric/readback receipt privately. If any check fails, preserve the evidence and report the failure without claiming an interval return.

Quota allowances and reset times are unknown. Checkpoints permit explicit resumption; no automatic wake after reset is promised. No indefinite polling or unattended runtime is established by this work.

## Primary-source research

Reviewed Kraken's current [v2 checksum guide](https://docs.kraken.com/exchange/guides/websockets/book-checksum-v2) and [book schema](https://docs.kraken.com/exchange/api-reference/spot-websocket-v2/book). The guide specifies top-ten CRC verification after all price-level changes, preserving decimal precision and truncating subscribed depth. The published book schema has timestamps and checksums but no exchange sequence counter. Local frame contiguity and CRC evidence therefore cannot prove an exact count of exchange messages lost. Report transport/resynchronization gaps, sampled missing time and local index gaps separately; label exchange sequence loss unobservable.

## Completed diagnostic disposition

The bounded public-feed diagnostic completed and remained explicitly clock-unverified. Private segment/payload/frame readback and both sealed-ledger adapter reconstruction and the separate existing replay command passed. Operational acceptance remains BLOCKED. A six-hour dry-run report was generated from committed data with unavailable return and current drawdown; no complete validated trading interval exists. The observed storage rate exceeds the unchanged capture cap when projected across the pilot. No raw data, hashes, financial evidence or logs are published here.

Focused tests: 21 PASS. Existing data checks D01/D02/F01/T02 and execution checks X01/X02/R01/R02: PASS. These software checks do not constitute independent operational review. The harness evolved during diagnostic collection; this run is not an immutable acceptance-build receipt.

Next exact implementation action: introduce a separate diagnostic CRC/book observer with synthetic tests showing that invalid NTP refreshes leave diagnostic transport measurements interpretable while production READY and all order gates remain closed. Do not relax Session's trading-clock behavior. Separately, a supported no-cost UDP clock capability and private retention/recovery/report-delivery proofs are still needed before release. Do not start the pilot or assign T0.
