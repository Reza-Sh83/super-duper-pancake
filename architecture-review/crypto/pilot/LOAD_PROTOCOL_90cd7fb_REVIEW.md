# Bounded pre-run load-protocol review

**Outcome: BLOCKED for pre-run load-protocol approval as currently documented.**

Exact execution code: `265ca75b94f1acb0248d142876654f3b7dd29599`.
Exact Capture preparation: `90cd7fb0d759193de83ec6d4d06b1ace0b26e6df`, cloud-pilot/PREPARED_PAIR.md.
Manager request/binding: `a356281d48d0f3781a851725a3861aaf18791acd`.
Existing safeguard review: `f88ab50f6c5844a2b689e7f113e18699899562e2`.
Owner: Architect. No pair, worker, profiler or collector was executed by this review.

This decision is about the missing declared load-attainment and scratch protocol, not a failure of the previously reviewed completion safeguards. It does not activate Manager's PASS-dependent dispatch condition.

## Evidence and scoped decisions

| Check | Result | Evidence |
|---|---|---|
| Version/command binding | PASS, preparation-receipt scope | Preparation binds exact 265ca75, 60-second schedule, one idle/loaded pair, no indexed-background flag, fresh exclusive output and retained 10,062-payload plan. Capture reports matching private copies and selected uninterrupted horizon. Architect has not accessed those private copies. |
| Worker algorithm declaration | PASS, narrow stress-workload definition | Two ready-gated independent workers: LZMA preset 6 over the ordered original raw parts and unindexed in-memory Session reconstruction plus per-frame event lookup over the full source. No adaptive worker count or codec/index substitution is declared. This is a named diagnostic stress load, not a calibrated production archive/report duty cycle. |
| Worker input identity binding | BLOCKED for complete attestation | Foreground source schedule is declared fixed; private receipt must also bind the compression ordered part-hash list and replay source directory's entire required-file inventory, policy and hashes. Code verifies raw/manifest/ledger around trial, but replay_worker reads frames(source) over the source directory. A schedule hash alone does not freeze every background input or prove absence of extra segments. |
| Start lag and sustained overlap/duty | BLOCKED | Preparation says “intended overlap” and says actual evidence “must be qualified,” without numeric acceptance bounds or an attainment rule. Worker ready signals are before common start. Code records work_started_mono_ns, aggregate work/CPU/cycles, but no periodic work/CPU samples or work-stop/foreground-stop timestamps sufficient to prove sustained measured duty. See code lines 178–234. |
| Timing/completion safeguards | PASS, existing exact-version review retained | No early sends; producer start lateness <=50 ms; complete framing and full send/process flags; timeout/error and first-failure-prefix separation; actual periodic refresh for a 60-second full window. Full-run assertions must use full_window_valid/full_window_series_valid, not condition_interpretable alone. No new blanket safeguard review is required. |
| Scratch bound and cleanup | BLOCKED for pre-dispatch capacity approval | Preparation has no quantified scratch reservation, peak formula, stop margin or cap-monitor/abort procedure. Clean child exit is checked, but compression output is appended in a loop without a byte ceiling; trial Capture's local directory check is not a global budget across source copies and pair outputs. |
| Actual worker attainment and pair effect | BLOCKED, not yet measured | No prepared pair executed in this review or supplied preparation. No passing measured overlap, representative load, timing or performance is invented. |

## Minimal corrections and acceptance contract

Capture owns a protocol-only addendum first. Do not launch the pair to discover whether an undeclared budget or overlap criterion is acceptable.

1. **Freeze all inputs privately.** Record exact code plus this protocol receipt, foreground schedule identity, compression ordered part-hash list, replay policy/full source inventory and hashes, unchanged metadata, queue/socket configuration and worker count. Verify them immediately before dispatch and after cleanup. Public notes need attestations and project revisions only, not private paths or raw input hashes/content.

2. **Declare numeric load-attainment bounds before results exist.** Specify maximum worker start lag from common start, intended duty, required overlap with the foreground offer/processing window, how a stall is detected and how each value is measured. Architect's proposed starting criteria for this bounded stress diagnostic are: no worker starts early; start lag <=50 ms; each worker's verified active interval covers >=95% of the actual foreground interval. If claiming sustained duty, additionally provide timestamped per-worker work/CPU observations at a declared cadence (for example one second) and a predeclared stall rule. CPU or useful-work progress can establish activity; process existence alone cannot. These are proposed diagnostic load-quality criteria, not alterations to production clock/risk/queue criteria. Capture may propose a justified different bound for review before dispatch.

   Current aggregate receipts can show start lag and total work, but cannot by themselves certify sustained duty. Distinguish “ready,” “alive,” “running CPU,” “making work progress,” and “attempting continuous work.” If sustained-duty measurement requires code changes, Implementer owns the smallest measurement-only patch plus synthetic delayed-start/stall/early-exit tests; bind a new SHA and regenerate preparation. Alternatively Manager can explicitly narrow the experiment to descriptive activity-only load with no sustained-overlap/representativeness claim; that is a changed scope requiring an exact updated binding, not implicit approval here. An independently versioned symmetric observer is another option only after its method, overhead, private-output bound and identity are reviewed.

3. **Keep measurement scopes literal.** Compression reports input/output bytes, complete cycles and partial-cycle input; replay reports frames, full/partial cycles and indexed=false. Their CPU totals begin at work start and include cooperative flush/close; initialization CPU is separate. Do not divide cleanup-inclusive CPU by foreground elapsed and call it foreground duty. Record actual foreground start/stop, worker work-stop and cleanup completion if claiming interval utilization; split cleanup time/CPU or clearly retain its inclusion. Full cycles are not mandatory in a bounded stress run, but partial work cannot be presented as complete archival/replay throughput.

4. **Declare scratch reservation and global peak before dispatch.** Include existing retained originals and read-only copies, both arm directories, raw/SQLite/journals, manifests/receipts/timing rows, compression partial output, temporary/restore material and any observer output. State current counted total, conservative incremental upper allowance and peak, plus safety reserve. Whole experiment remains within the unchanged 5 GiB cap and >=2 GiB free-space floor; keep existing stricter writer headroom. Memory replay is not disk-free process overhead, so report memory separately rather than folding it into disk capacity.

   An ample filesystem or a prior weekly compression estimate is not this budget. Without a proven conservative byte bound, a bounded watcher/enforced reservation must stop new work safely before the limit, with evidence preserved. Declare monitor cadence, worst growth during that cadence and stop/flush reserve; do not rely solely on a final output size. Any new limiter/observer that affects scheduling needs identical treatment across arms, an explicit scope and a reviewed version. No deleting the sole verified input or failed receipt. Aborted capacity trials are incomplete.

5. **Preserve timing and cleanup interpretation.** One idle then loaded pair only; stop after an uninterpretable first arm, with no manual loaded-arm override/reversal. Record offered/sent/read/dequeued/processed denominators, send-end/read/dequeue delay separately, actual refresh evidence and all rejected/missing data. Native WebSocket framing/max_queue buffering remains unmodeled. Require all children exit zero with no forced termination or survivor, receipts complete, source hashes unchanged and own-raw ordered replay equal. First-failure prefixes require matched eligible exposure; they are not complete pair results. Pair launch remains Capture's responsibility, never Architect's.

## Wider qualifications

R3 cross-arm financial equivalence remains NOT_EVALUATED by this harness. Zero-fill own-raw replay can pass without validating nonzero P&L or drawdown. Do not make completion wait on proving a nonzero trading result; keep that claim unavailable. Representative-load attainment is a diagnostic quality gate, not evidence of full operational readiness.

Clock access, cap-compliant week-long retention/recovery, delivery readiness and 24-hour acceptance are separate unresolved release gates. This 60-second diagnostic cannot release the stopped 168-hour pilot or change the separate 180-day protocol. No main merge, added cost or live trading is authorized.

## Receipt and next owner

Capture owns the next action: publish the numeric protocol/input/scratch addendum, including whether existing receipts suffice or additional bounded instrumentation is required. Trigger: this BLOCKED receipt is visible on an actual supported invocation. Implementer owns a smallest patch only if Capture identifies a measurement or limiter gap that cannot be resolved by declaration/verified existing evidence. Architect then reviews that exact addendum/code scope; Manager reconciles any revised execution binding. No peer acknowledgment or automatic branch wake is assumed.

Supported five-hour and weekly usage values were unavailable (UNKNOWN); reset time UNKNOWN, no current warning observed. This was a bounded source/document review; no experiment was launched. Private review checkpoint is separate from public project notes.
