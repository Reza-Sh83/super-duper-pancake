# One recorded-input idle profiling pass

Execution owner: Capture. Exact profiler code/test commit: `128f3bea71959ad1d160c3c2576d8fd275f65079`. Implementer handoff: `03434a1d23ff13bdba96e0c20150540721722cc1`. This is a separately checkpointed descriptive profile, not the prepared comparative pair, a default optimization, or operational acceptance.

## Version, scope and validation

Resumed from published checkpoint `3d3ff64796c48bfdbafde224cfb9cc51414abc6d` after the user explicitly verified renewed allowance. No fresh usage API is exposed; the supplied dashboard check is retained privately rather than inferred from the reset time. No current warning was observed. The previous stop was not cleared merely because a clock reset elapsed.

A detached exact profiler checkout was clean. All prepared source-file, manifest, raw-part, ledger, collector-package and harness hashes matched before and after execution. The unchanged selector verified the same 60-second recorded arrival plan of 10,062 WS messages and committed source horizon. Five focused profiler tests passed locally, including preservation of real writes/fsync/FULL commits, failure cleanup, failed-send timing and synthetic nonzero accounting. Implementer's broader synthetic receipt is separate evidence.

Exactly one idle profile ran, using normal foreground SQLite locking, PERSIST journal and synchronous=FULL. Neither --loaded nor --exclusive-ledger was supplied. No capture fsync, commit, queue/clock/risk check or source calculation was removed. The parent deadline was 150 seconds; the command exited normally after 66.067 seconds, including preparation, the 61-second foreground sample window and verification. No measured pair or other project workload overlapped it. No retry was performed to seek a passing result.

## Delivery and validity

- Sent and processed: **10,062 / 10,062**; complete framing, zero early sends and no failed sends.
- Samples: **61 / 61**. Application frame/byte/age threshold failures: **0 / 0 / 0**.
- Three send starts exceeded the unchanged **50 ms** driver criterion. Maximum send-start lateness **63.882 ms**; send-completion lateness **63.904 ms**.
- Maximum planned-to-read/dequeue lateness: **131.622 / 131.655 ms**. Maximum application queue age was **6.680 ms**; it does not include all upstream delay.
- Status DONE, but **condition_scope=UNINTERPRETABLE and full_window_valid=false** because producer timing fidelity failed. Complete frame count alone is not a passing timing-qualified run.
- The unchanged periodic failed-clock service was observed after 50 seconds. No valid UTC reference or production readiness follows; operational READY remained zero.
- Source hashes remained unchanged, own captured-raw ordered events/committed frames/final account reconstructed exactly, and all children exited zero without forced termination or survivors. The observation-only ledger has zero fills; no validated P&L or drawdown is established.

## Measured foreground stages

Totals cover 10,129 foreground raw/ledger frames, including WS data, samples and control frames. CPU is process CPU, not device service time. Capture sub-stages are nested in Capture total; commit is nested in Session. Do not add a parent total to its children.

| Stage | Wall total, seconds | Process CPU total, seconds | Median wall, ms | p99 wall, ms |
| --- | ---: | ---: | ---: | ---: |
| Capture write | 0.025723 | 0.024387 | 0.001850 | 0.003424 |
| Capture flush | 0.139961 | 0.141021 | 0.008169 | 0.071477 |
| Capture fsync | 5.420469 | 0.789573 | 0.461006 | 1.511245 |
| Capture total | 7.182664 | 2.536297 | 0.629270 | 1.856534 |
| Session total | 16.526291 | 4.691835 | 1.499821 | 3.779542 |
| SQLite FULL commit (within Session) | 14.016259 | 2.191037 | 1.252411 | 3.410590 |

Capture residual after write/flush/fsync subtraction was **1.596510 s**, including serialization, bookkeeping and instrumentation overhead. Fsync accounts for **75.47%** of measured Capture wall time; commit accounts for **84.81%** of Session wall time in this one run. Successful send blocking median/p99/max was **0.008995 / 0.136600 / 3.498407 ms**. Failed-send blocking count was zero; the profiler's ability to retain failed calls is covered separately by its synthetic test.

Durability calls dominate these scoped wall totals, but wall time includes scheduler pauses and process CPU can include other process threads. This does not isolate filesystem latency from scheduling or prove the exact cause of historical backpressure. Instrumentation adds overhead. Different runs/traffic/hosts and the socket model's missing native WebSocket buffers prevent a comparative load or performance claim. No default exclusive locking or other optimization is adopted.

## Storage, gates and handoff

Observed output was 16.30 MB, within the predeclared 512 MiB single-idle reservation. Retained private-root logical usage was 626.24 MB after execution, below the unchanged 5 GiB cap; the 2 GiB free floor held. These before/after checks are not a sampled transient peak, global lifecycle certificate or week-long retention proof. Source captures and detailed timing/receipts stay private.

Latest Manager `a356281d48d0f3781a851725a3861aaf18791acd` conditionally binds the separate pair to exact `265ca75`. Latest Architect `b48f52045c22e4ad7fc111d9a9d17b80828325f6` explicitly BLOCKS its load protocol pending numeric worker attainment/input/scratch bounds and adequate measurement. This profile does not substitute for that pair, alter its target or activate its dispatch condition. The prepared pair output remains absent.

Next owners:

- Architect: independently review exact profiler measurement scope, nested-stage and scheduler interpretation, durability/concurrent-reader implications and this recorded receipt. No independent approval of this new result is presumed.
- Implementer: use these recorded stage costs to propose the smallest evidence-backed measurement/performance correction; compare on identical input with ordered economic events/accounting, fees/cutoffs/staleness and unchanged durability. Do not disable fsync/FULL or default to exclusive locking from these data.
- Capture: preserve input/job/quota checks and prepare the separate numeric load/input/scratch addendum requested by b48f520; do not launch the pair without its actual approval.
- Manager: reconcile this exact profiling result separately from the conditional pair and unchanged release gates.

No quota warning occurred during this bounded pass. Any new warning or applicable <=15% allowance stops new work. Current live remaining allowance/reset is not guessed. No new wake or scheduler action was created. The pilot remains STOPPED; no financial result, main merge, added spend, live order or change to the separate 180-day protocol.
