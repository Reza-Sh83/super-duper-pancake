# Recorded-input pair: protocol addendum and gated handoff

Owner: Capture. This supersedes the load-quality and scratch declarations in
`PREPARED_PAIR.md`; it does not authorize execution. Starting checkpoint:
`df447221814d77af9487f7a0b9d265b50fd0edef`. Architect request:
`b48f52045c22e4ad7fc111d9a9d17b80828325f6`; Manager conditional binding:
`a356281d48d0f3781a851725a3861aaf18791acd`.

**Exact existing execution SHA: `265ca75b94f1acb0248d142876654f3b7dd29599`.**
No execution-code change is included here. The pair remains BLOCKED pending
Architect acceptance and Manager's explicit updated scope binding. A necessary
limiter change would require its own exact revision and review before dispatch.

## Private identity attestation

Capture revalidated the retained input against its prepared binding, rather
than selecting a new recording. The private attestation binds:

- all 11 source files, byte sizes, permissions and SHA-256 values, including
  SQLite and journals; exact directory inventory; no symlinks or extra raw parts;
- foreground: the same uninterrupted 60-second schedule, ordered schedule hash
  and 10,062 offered messages;
- compression: the ordered hashes and sizes of both complete original raw parts,
  LZMA preset 6, 64 KiB reads, one repeating worker;
- replay: the complete source inventory, observe policy, unindexed in-memory
  Session reconstruction and per-frame event lookup, one repeating worker;
- execution/harness/package identities, Python/SQLite/WebSocket versions,
  queue thresholds, socket buffers and producer lead time.

The copies are read-only; this is not a claim of hardware immutability. Repeat
the exact inventory/hash/configuration comparison immediately before dispatch
and after cleanup. Reject added, missing, modified or symlinked input. All three
consumers must use that binding. Any change requires a new preparation receipt.
Raw identities, paths and receipts remain private. This turn attested inputs;
it did not execute a pair or validate a new accounting interval.

## Explicit changed scope: DESCRIPTIVE_ACTIVITY_ONLY

Manager must accept this narrower scope explicitly. It is a named diagnostic
stress workload, with no claim of representative production duty, sustained
overlap, stall freedom or a causal estimate of load impact.

For each loaded worker require ready before release, no early work start and
work-start lag in **[0, 50 ms]** from the common start. Require positive recorded
useful work and positive work CPU, zero exit status, complete receipt and no
forced cleanup or survivor. Report actual start lag, bytes/frames, complete
cycles and partial-cycle work individually. Missing receipts fail acceptance.

Active-overlap percentage, duty percentage, maximum stall duration and
foreground-only worker CPU are **UNMEASURED**. There is no numeric active-overlap
or stall pass criterion in this descriptive scope: aggregate counters do not
observe those quantities. Do not substitute process lifetime or ready status.
Worker CPU includes cooperative flush/close; do not divide it by foreground
wall time and label it duty. Partial cycles are not completed archive/replay
throughput. A future sustained-load scope would need a separately reviewed
timestamped observer; none is requested for this scope.

Keep one idle then one loaded arm only. Stop after an uninterpretable first arm;
no manual loaded-arm override or reversal. Retain all existing delivery,
framing, queue-age, start-lateness, periodic-refresh and full-window checks.
Report offered/sent/read/dequeued/processed coverage, send-end and subsequent
delays separately. A timeout, missed input or failed fidelity gate means no load
conclusion. Native WebSocket buffering is still not modeled.

Require unchanged source hashes and own-raw ordered replay/accounting equality
for each completed arm. Existing cross-arm financial equivalence remains
NOT_EVALUATED, not inferred from zero fills. No diagnostic P&L or drawdown claim.

## Global scratch reservation and safe-stop contract

All numbers are binary units. Count the entire private evidence root, including
retained originals/copies, both arms, journals, compression output, temporary or
restore space and control receipts. Charge each regular file at the greater of
logical and allocated bytes; include directory allocation. No concurrent
project writer, profiler, restore or measured experiment is permitted.

| Quantity | Required bound |
|---|---:|
| Global evidence cap G | 5 GiB = 5,368,709,120 bytes |
| Free-space floor F | 2 GiB = 2,147,483,648 bytes |
| Proposed per-output-file hard cap L | 64 MiB = 67,108,864 bytes |
| Output envelope | 20 files/arm × 2 + 8 common + 8 temporary = 56 files |
| Maximum incremental file allowance W | 56 × L = 3,758,096,384 bytes |
| Additional stop/flush/allocation reserve R | 256 MiB = 268,435,456 bytes |
| Total reservation S | W + R = 4,026,531,840 bytes |

Admission requires **current charge + S <= G** and **current free >= F + S**,
plus the existing stricter writer floor/headroom checks (including 16 MiB).
Recount after protocol/control files exist and immediately before dispatch.
Do not treat an earlier count as a reservation against unrelated writers.
The private snapshot passed these admission inequalities; it is not a measured
peak or proof that the output envelope is enforced. The selected foreground's
conservative raw allowance is below L, but that does not bound SQLite or the
unbounded repeating compressor by itself.

Proposed hard enforcement is an inherited `RLIMIT_FSIZE=L`, core dumps disabled,
isolated declared temporary directory and a reviewed finite-output census.
The 20 arm slots cover raw, SQLite/journal, bars, manifest/receipt/producer
temporary replacements, compression, replay and cleanup-failure receipts with
spare slots. The common/temporary slots are reservation allowances, **not a
verified file-count bound**. Byte caps alone cannot enforce an aggregate cap
when additional files can be created. Therefore this protocol explicitly
**withholds scratch PASS and dispatch** until that gap is resolved.

With a proven/enforced finite envelope, reserve the entire W before starting;
no polling-rate or guessed write-throughput assumption is needed. Any file cap,
budget violation, source change, timeout, nonzero exit, incomplete receipt or
forced cleanup invalidates the arm and prevents the next arm. Stop workers
cooperatively; bound the whole invocation with a 180-second process-group
deadline, INT then at most 20 seconds to forced termination. Forced termination
is failure, never successful cleanup. Inspect for survivors and preserve partial
outputs and the sole input. Do not reclaim input to make admission pass.

Synthetic checks in this turn verified a 1 MiB inherited file limit rejects an
oversize write at the cap, and a 0.2-second standard timeout delivers cooperative
INT (timeout status 124). These checks prove neither aggregate enforcement nor
pair cleanup. No runtime observer or pair was launched.

## Small isolated Implementer handoff: scratch envelope only

Concrete gap: exact 265ca75 repeats compression without a byte ceiling and does
not enforce/prove the global output-file census, including SQLite temporary
files. Implementer owns only a bounded scratch-enforcement item: first audit
whether the declared finite census plus inherited per-file cap can be proved
for this exact command/runtime. If not, provide the smallest enforcing change
with a demonstrable aggregate bound. Do not add duty/stall telemetry, indexes,
queue tuning or strategy changes. Do not substitute a polling watcher without
a proved maximum intervening growth and stop/flush reserve.

Deliver exact code/launcher SHA, enumerated write destinations and bounds,
synthetic boundary/extra-output/temporary-file/cleanup tests, and proof that a
budget stop cannot dispatch the next arm or remove evidence. Apply identical
enforcement to both arms. If an enforceable bound cannot be supplied within
scope, return BLOCKED with evidence; do not run the pair to test capacity.

## Receipt and next owners

Completed: full private identity attestation; descriptive-only declaration;
numeric reservation/admission calculation; tiny OS safety-primitive checks.
No pair, profiling pass, collector or pilot was started. No new performance,
retention, return or acceptance result is claimed.

Next: Implementer resolves only the scratch-envelope gap above; Architect reviews
this exact protocol and the resulting exact enforcement version; Manager binds
the accepted descriptive scope and execution version explicitly. Capture then
rechecks allowance, jobs, inputs, capacity and approvals before the existing
single-pair command. Until those receipts exist, that command is gated.
Branch publication is a handoff, not evidence that another chat has awakened.

Live quota/reset signals are UNKNOWN; use short checkpointed units and stop at
the first warning or applicable allowance <=15%. No automatic wake is assumed.
The 168-hour pilot remains stopped; clock, storage/recovery, reporting and
24-hour acceptance gates and the separate 180-day protocol are unchanged.
