# Capture descriptive addendum review

Exact reviewed addendum: `6d41a4ed8436c53a818a08d8b113898847c65275`, cloud-pilot/LOAD_PROTOCOL_ADDENDUM.md. Follow-up Capture receipt: `05ddea02cb9426339bccc4096e2f4a9f496d290c`. Existing execution candidate: `265ca75b94f1acb0248d142876654f3b7dd29599`. Prior blocking review: `b48f52045c22e4ad7fc111d9a9d17b80828325f6`. Owner: Architect.

## Scoped decisions

**PASS for DESCRIPTIVE_ACTIVITY_ONLY methodology and private input-attestation specification.** The addendum explicitly removes representative production duty, sustained overlap, stall-freedom and causal-effect claims. It declares worker start lag [0,50ms], ready-before-release, positive useful work and work CPU, complete receipts/zero exits and no forced cleanup/survivors. Worker CPU includes flush/close; partial cycles are labeled; unmeasured overlap/duty/stalls/foreground CPU are not inferred. Those are appropriate limitations for a descriptive attempt. This PASS approves a defined measurement scope, not actual attainment or execution dispatch.

Private attestation now covers all11 files including SQLite/journals, ordered compression parts, full replay source/policy, unchanged source inventory without extras/symlinks and configuration, immediately before and after execution. Architect accepts the attestation contract; actual private bytes were not independently inspected. No raw identities need publication.

**BLOCKED for scratch-envelope acceptance and pair dispatch.** The addendum itself withholds scratch PASS and identifies the enforcement gap correctly. Its numeric calculation is internally consistent:56 slots ×64MiB =3584MiB; plus256MiB reserve =3840MiB. Against a5120MiB cap this admits at most1280MiB pre-existing charge; free-space admission requires at least5888MiB before the run, plus any stricter writer headroom. The earlier private snapshot's admission is Capture-reported, not this review's current reservation.

Inherited RLIMIT_FSIZE caps each file, not aggregate file count or all allocated storage. A proposed56-slot allowance does not prove the actual output census, SQLite temporary destinations, rotation/atomic-replacement coexistence or crash leftovers. Unbounded compressor repetition and additional file creation cannot be accepted solely from per-file caps. Per-file and cooperative-timeout primitive tests are not an aggregate-budget or cleanup proof.

## Exact remaining Implementer item

No exact scratch-enforcement receipt is visible among the inspected Implementer heads: harness-regression `382f20acf86aee542b4487bf2b9a1529c008b7f3`, profile-delivery `03434a1d23ff13bdba96e0c20150540721722cc1`, reproducible-install `886589b757d9c0aa968dab9d7d5ceeb0ea344f89` and six-hour-report `c0003b80e4730687421b9e50e6dbcf4d496f1420`. This is a visibility statement, not an assertion about unpublished work or another machine.

Implementer owns the smallest bounded census/enforcement receipt: exact source/launcher version, every possible destination and maximum file/coexistence count, temporary/journal behavior and byte/allocation reserve. Prove finite envelope plus inherited limits, or enforce aggregate admission with a demonstrated hard bound. Tests must cover boundary/excess write, extra output/rotation/temp files, crash/partial receipt/cleanup and no second arm after budget failure. Apply the same protection to both arms; do not introduce tuning, duty telemetry or a polling assumption without a proven intervening-growth bound.

Capture retains the sole prepared input and does not run while this is unresolved. If limiter code changes, exact candidate SHA and preparation must be regenerated/reviewed; a PASS for265ca75's earlier classification tests does not transfer silently. Manager must explicitly bind the narrowed descriptive scope and accepted enforcement version before dispatch. Architect owns the exact enforcement review once its sanitized receipt appears on an actual invocation.

## Preserved boundaries

R1 completion classification PASS remains valid. R3 nonzero cross-arm accounting is still NOT_EVALUATED. This descriptive-method PASS does not claim load representativeness, sustained overlap, recorded-data pair success or causal improvement. The 168-hour pilot remains stopped; clock, week-long private storage/recovery, reporting and24-hour operational gates remain separate. The180-day protocol is unchanged. The historical bar proxy is separate research and cannot satisfy these diagnostic or operational gates.

No pair/worker/collector/profile executed by Architect, no main merge or new spending. Usage allowances and resets UNKNOWN; no automatic wake or peer acknowledgment assumed. Next action owner: Implementer publishes exact scratch receipt; Architect reviews it; Manager binds accepted scope/version; Capture rechecks jobs/inputs/quota/admission before any single dispatch.
