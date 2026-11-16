# Delivery stage profiling: synthetic measurements and recorded-input handoff

Owner: Cloud Implementer. Failed-trial reference **35ea79b6a0007b22e9da4ba1d9d0b0c1f98394de** and executor handoff **f942d150330bdaddc9ab2922ee1bbe0705e5f8c3** read and acknowledged. Exact profiling code/test commit: **128f3bea71959ad1d160c3c2576d8fd275f65079** on `implementer/profile-delivery`, based on the reviewed-harness correction branch. No main merge.

## Access and scope

The original sealed trial input is not accessible to this assignment through a verified approved private path. The user confirmed that it was retained by Capture and that this assignment must treat recorded-data profiling as BLOCKED unless access and input hashes are verified. No raw capture, private receipt, credentials or infrastructure metadata is published here. The results below are **synthetic**, not a profile or causal diagnosis of the original failed trial.

The profiler wraps the existing offline harness without changing `crypto_paper` or `tools/replay_queue_load.py`. All actual writes, flushes, fsync calls and FULL SQLite commits execute. It separates Capture write, flush, fsync, residual work and total wall time; Session total and SQLite commit wall/CPU time; producer send blocking; planned-to-send/read/dequeue lateness; and failed-send blocking. Every receipt binds the profiler and source-manifest hashes. Detailed receipts stay private. Instrumentation and scheduling add overhead; Capture sub-stages are nested within its total and commit time within Session.

Evidence-backed measurement correction: a failed `sendall` has no successful send-end timestamp. Successful-send-only summaries omit its blocking time. The profiling wrapper retains failed-attempt duration separately, while keeping completed-frame counts and failure status unchanged. A synthetic timeout test verifies this. This fixes an observability gap; it does not claim a delivery-performance repair.

## Frozen-code synthetic comparison

One sealed synthetic source: 840 ordered instrument/book messages offered uniformly over five seconds, 168 messages/second. Same input and profiler hashes in every run. Original payload/order/offset schedule, Capture/fsync, Session, application queue, clock and risk behavior are preserved. No background load. A=normal foreground SQLite locking; B=experimental exclusive locking, with PERSIST journal and synchronous=FULL unchanged. Run order A1, B1, B2, A2.

| Measurement | A1 normal | B1 exclusive | B2 exclusive | A2 normal |
| --- | ---: | ---: | ---: | ---: |
| Processed / planned | 840/840 | 840/840 | 840/840 | 769/840 |
| Driver/window classification | FULL_WINDOW | FULL_WINDOW | UNINTERPRETABLE | UNINTERPRETABLE |
| Median SQLite commit, ms | 3.100 | 3.056 | 3.044 | 3.700 |
| Median capture fsync, ms | 1.004 | 1.202 | 1.136 | 1.353 |
| Median socket send blocking, ms | .010 | .010 | .043 | 4.799 |
| Maximum producer send lateness, ms | 47.638 | 43.546 | 300.239 | 773.100 |
| Maximum socket read lateness, ms | 240.770 | 254.820 | 571.859 | 1028.794 |
| Maximum dequeue lateness, ms | 240.800 | 254.863 | 571.935 | 1028.858 |

A1 stage totals: Capture write 3.490 ms, flush 30.131 ms, fsync 1182.954 ms, Capture total 1443.668 ms; Session total 3515.568 ms, of which SQLite commit 3183.364 ms. Session CPU time was 816.442 ms. Across all four runs, commits consumed approximately 91% of Session wall time. Capture fsync was its dominant sub-stage. Raw write/flush CPU work was comparatively small.

In the slow A2 run, socket read and dequeue maxima were nearly equal while producer blocking/lateness increased. This supports synchronous downstream durability work causing upstream socket backpressure in this synthetic setup; a fresh application-queue timestamp alone does not measure all upstream delay. It does not identify the historical failure's exact cause. Neither wall-minus-CPU time nor these runs isolate filesystem latency from host scheduling completely.

**Decision:** no default performance change is adopted. Exclusive locking did not establish reliable timing fidelity; one exclusive run failed despite sending/processing the complete schedule. Incomplete prefixes are not equal-exposure throughput comparisons. The option remains an explicit experiment only, and it blocks concurrent readers until the writer closes. The initial apparent benefit in exploratory runs was not accepted as a general improvement. No capture fsync, FULL commit, queue limit, producer timing gate, clock gate, risk rule or accounting calculation is removed or relaxed.

FULL_WINDOW here is the harness's offered/processed and producer qualification, not native WebSocket equivalence, operational READY, or 24-hour acceptance. Five-second tests do not exercise the 50-second clock-refresh phase. Own-raw replay, sealed source immutability and child cleanup passed in every run. No observed profit or drawdown is established.

## Tests and reproduction

At frozen code commit `128f3bea71959ad1d160c3c2576d8fd275f65079`, all **47 offline tests PASS**. Five new profiling tests cover real durability-call preservation and FULL/PERSIST settings, failed-send duration without false delivery, factory restoration on failure, source immutability/own-raw replay and exact nonzero financial-event/account equivalence under the experimental lock option. Literal synthetic fees remain 1.5992 USD and final cash/NAV 9998.3008 USD. Existing cutoff/stale/risk tests remain passing.

```sh
python -m unittest discover -s tests -p test_profile_queue_delivery.py -v
python -m unittest discover -s tests -v
# Synthetic source generation and baseline (outputs must be private and fresh):
python -m tools.profile_queue_delivery --synthetic --seconds 5 --rate 168 --out "$PRIVATE_SYNTHETIC_OUTPUT"
# Reuse that exact sealed source; --exclusive-ledger is optional experimental B only:
python -m tools.profile_queue_delivery --manifest "$PRIVATE_SYNTHETIC_MANIFEST" --seconds 5 --exclusive-ledger --out "$PRIVATE_CANDIDATE_OUTPUT"
```

## Exact next owner and trigger

**Capture owns the next recorded-input action**, triggered by this frozen profiling patch and sufficient allowance: in a separate worktree, verify the retained input identified by its private checkpoint, manifest/part/ledger hashes and original package identity; verify no existing profile job/result duplicates this work; check the unchanged global storage budget; then run one bounded idle profile on the original 60-second schedule:

```sh
python -m tools.profile_queue_delivery --manifest "$PRIVATE_SEALED_MANIFEST" --seconds 60 --out "$NEW_PRIVATE_PROFILE_OUTPUT"
```

Do not bypass recorded-build, source-horizon or durability checks if this rejects the retained input. Return the exact code commit and sanitized counts, failed-send duration, Capture write/flush/fsync/residual totals and percentiles, Session/commit wall and CPU times, read/dequeue/send delays, refresh-phase evidence, failure scope, source-unchanged/own-replay and cleanup outcomes. Keep raw timings and captures private. No exclusive-lock or loaded recorded run is required until this baseline has been reviewed.

**Cloud Architect owns independent review** of the measurement correction, nested-stage interpretation, experimental locking/durability/concurrent-reader consequences and Capture's resulting exact receipt. **Implementer owns the smallest subsequent performance correction**, triggered only by those recorded stage measurements; reproduce and compare identical inputs, ordered economic events, final accounting, fees, cutoffs and stale behavior. **Manager owns readiness reconciliation** and the existing clock/storage/reporting/24-hour gates.

This branch is a published handoff, not a confirmed peer acknowledgment or automatic wake. Quota windows/reset remain UNKNOWN where no supported signal is available; use bounded units and manual resume, with no guessed reset or wake. Pilot STOPPED; P&L/drawdown unavailable; original 180-day protocol unchanged; no additional spend or live trading.
