# Recorded-data queue comparison — inconclusive timing

Execution owner: Cloud Pilot. Measured harness: `45cee7deb93d7944c78ae277b8a15200e7f58318`. Independent fast-drain control: `7eca207`. The collector package and all queue, clock and risk thresholds stayed unchanged. Raw input, captures, detailed receipts and infrastructure metadata remain private.

All seven requested remote branches were fetched. Their supplied starting commits remain current: Manager `100ffe7`, Architect `0e463a8`, installer `886589b`, fixture report `c0003b8`, capture/replay `03cef5d`, paired harness `45cee7d`, and baseline main. Historical readiness statements do not supersede the measured findings or user's receipt acknowledgment below.

## Actual experiment

The old private sealed input remains accessible; no fresh capture was needed. All eight focused harness tests passed on the exact saved version. The saved Architect review was read, including its input-binding, timing, cleanup and native-WebSocket limitations. The implemented safeguards were preserved. This is not a new independent Architect approval of the final results.

The planned 60-second arrival schedule contained 10,062 messages. Both full-path arms used identical payload/order/relative-offset identity, build, queue settings and socket buffers. One condition ran without background work; the other used bounded LZMA6 compression and the original memory-replay workload. The same planned sample window was 61 seconds.

| Measurement | No background load | Compression + replay load |
| --- | --- | --- |
| Frames sent and processed / planned | 7,174 / 10,062 | 6,069 / 10,062 |
| Sample coverage / planned seconds | 48 / 61 | 48 / 61 |
| Application frame/byte/age threshold failures | 0 / 0 / 0 | 0 / 0 / 0 |
| Maximum application queue age, accepted frames | 14.540 ms | 36.208 ms |
| Maximum planned-to-processing lateness | 1.614 s | 7.272 s |
| Maximum producer send lateness | 1.417 s | 6.459 s |
| Frames beyond predeclared 50 ms producer limit | 2,380 | 5,679 |
| Actual timing fidelity | FAIL | FAIL |
| Trial termination | Harness socket timeout | Harness socket timeout |
| Own captured-raw ordered-event/frame/account replay | PASS | PASS |

The background workers actually processed 62,783,488 compression input bytes and 38,203 replay frames before cooperative cleanup. No child survived cleanup. Both arms stopped on the first harness transport failure and retained the unsent/unprocessed remainder. The small application queue age excludes upstream socket/producer delay and cannot establish healthy end-to-end delivery. Neither arm reached the 50-second periodic clock refresh, despite the planned longer window.

Outcome: **INCONCLUSIVE for causal attribution of the earlier live queue failures**. Different actual deliveries violate the timing-fidelity requirement. The expected sequential pair stopped after the invalid idle arm; the loaded arm was then explicitly attempted separately on the same frozen plan, without overriding its failure status. A reversed invalid pair was not run. Zero application threshold failures is not a passing capture/acceptance result.

## Independent control

A fast-drain receiver, deliberately omitting Capture/fsync/SQLite/Session, received all 10,062 messages from the same producer and schedule. Maximum send lateness was 46.145 ms; maximum read lateness was 46.327 ms. No message exceeded the unchanged 50 ms driver criterion. Payload order/hashes matched, the source stayed unchanged and cleanup completed.

This PASS demonstrates producer/socket feasibility for this one control window. It is not a collector performance fix, native WebSocket test or causal proof about the earlier live run. It motivates profiling the full capture/session path and upstream backpressure before changing production code. The original collector was not modified to manufacture a passing result.

## Accounting and release gates

Each trial's own sealed raw reproduced its ledger and account. Final accounts match across the arms, but the observation-only data has zero fills; no nonzero strategy result is established. Net paper P&L and drawdown remain unavailable. No diagnostic or synthetic result is reported as profit.

A contemporaneous approved-reference clock probe remains blocked. All ten files in the prior recovered sample still match their retained expected hashes; this is readback of a prior local recovery, not a new environment-loss restore. Conservative week-long storage remains over the approved cap. Full 24-hour operational acceptance has not passed. The 168-hour pilot remains STOPPED, and the separate 180-day protocol is unchanged.

Delivery facts are now separated: managed-cloud execution and report generation were observed in the dry-run evidence; the user confirms seeing the report in Work on the web. Exact scheduled timing and continuous PC-offline status remain UNVERIFIED. Current scheduler lookup has no linked run/result record and reports delivery status unknown; it does not override the user's receipt. Nothing was rescheduled.

## Owner handoff

- Implementer owns the next technical step: profile per-frame Capture/fsync/Session service and upstream backpressure on this fixed input, then propose one bounded change while preserving durability and all queue/clock/risk checks.
- Architect owns independent review of this result's interpretation, receipt completeness and any proposed timing-model change. No acknowledgment or approval is invented.
- Manager owns reconciliation of the exact result version and the clock, storage, acceptance and delivery gates. Web receipt must not be treated as proof of timing or offline-PC behavior.

Coordination uses this dedicated branch; direct cross-chat messaging is unavailable. Branch visibility does not wake a peer. Review/acknowledgment requires an actual supported invocation. No additional spend or main merge occurred.

Quota checks before each bounded unit found no supported usage signal. Five-hour allowance, weekly allowance and reset time are UNKNOWN; no current warning was observed. No wake was scheduled without a verified reset. Stop new work at the first warning or applicable 15% threshold; the private checkpoint records exact evidence paths and next commands.
