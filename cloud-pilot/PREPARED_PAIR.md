# Private paired input and execution preparation

Owner: Capture. Outcome: **INPUT/COMMAND PREPARED; EXECUTION BLOCKED ON REVIEW BINDING**. This is a diagnostic preparation receipt, not a new paired result or pilot approval.

## Exact versions received

- Architect latest: `f88ab50f6c5844a2b689e7f113e18699899562e2`. It gives scoped R1 classification PASS for exact `265ca75`, while load comparability, cross-arm financial scope and release acceptance remain open. The earlier `37e4fa7` review of old `45cee7d` is historical context.
- Manager latest: `bf6419a1fdc51a4f427cabd0398ae32732b4a575`. It names exact candidate `265ca75`, still explicitly requires scoped review/protocol approval before execution, and has not acknowledged the new Architect receipt or this declared protocol.
- Implementer latest handoff: `382f20acf86aee542b4487bf2b9a1529c008b7f3`. It explicitly requires independent review of correction `265ca75b94f1acb0248d142876654f3b7dd29599` and a declared load protocol before the pair.
- Prepared execution candidate: `265ca75b94f1acb0248d142876654f3b7dd29599`. Its tools/tests/collector files are identical to the latest Implementer handoff; later handoff changes are documentation only.

Both records now name the same candidate SHA, but the Manager execution/protocol binding remains pending. Capture will not transfer the scoped R1 PASS to unreviewed load/accounting conditions or infer approval from branch visibility and tests.

## Preparation completed

The retained private source is accessible; no fresh capture was needed. A separate read-only input copy was made and every source-file hash matched. The revised selector verified committed frame identity, the uninterrupted observation horizon and the complete requested 60-second source window. The selected plan contains 10,062 original WS payloads with fixed ordering and relative arrival offsets. Detailed manifest, file/schedule hashes and private paths stay outside Git.

All 14 focused harness tests passed from the isolated exact candidate checkout. A separate baseline test log is retained and is not mislabeled as the candidate run. The collector package and all queue/clock/risk thresholds remain unchanged.

A private command file binds the exact candidate checkout, verified sealed manifest, fresh exclusive output, 60-second schedule and one idle/loaded pair. The public command shape is:

```sh
python tools/replay_queue_load.py --manifest "$SEALED_MANIFEST" --out "$FRESH_PAIR_OUT" --seconds 60 --pairs 1
```

The existing worker protocol is declared for review: two independent ready-gated processes, LZMA6 compression of the same raw segments and unindexed memory Session reconstruction/per-frame lookup of the same full source. Intended overlap is the shared start through foreground completion. Actual start lag, overlap evidence, CPU scope, bytes/frames, partial/full cycles, scratch budget and cleanup must be qualified. Activity alone does not close Architect R2; series-level financial equivalence remains separately NOT_EVALUATED by the harness (R3).

## Conditional execution and verification

Architect has completed scoped R1 review and owns remaining measurement-scope qualification. Manager owns acknowledgment of that review, the explicit execution/protocol binding and readiness reconciliation. Once both identify the reviewed execution commit, Capture refreshes refs, verifies that the private preparation matches that commit, checks quota/job/output state, and executes the single bounded pair. If they bind another version, regenerate preparation instead of silently reusing this command.

For both arms require complete framing/delivery/processing of the same plan, no timeout or unexpected error, correct payload/order identity, no early sends, measured producer fidelity and actual failed-clock-refresh phase evidence. Inspect send completion, read/dequeue lateness and all missing denominators separately. If either arm times out or misses input, retain the failure, stop comparative claims and draw no load conclusion. Own-raw ordered-event/frame/account replay must match; cross-arm economic comparison needs matched eligible input and explicit zero-fill scope. Diagnostic or synthetic values are not validated P&L/drawdown.

No pair was executed by this preparation. Earlier timing-invalid trials and independent driver control remain historical evidence; they are not rerun or relabeled. Native WebSocket buffering, clock readiness, week-long retention and 24-hour acceptance are not certified. The pilot stays STOPPED; no main merge, new spend or 180-day protocol change.

## Receipt and next owners

- Architect: R1 PASS received at `f88ab50`; qualify the declared measurement/load/accounting scope on architecture-handoff and retain all limitations.
- Manager: acknowledge `f88ab50`, identify exact `265ca75` as the reviewed execution version on status, and bind the declared protocol/remaining conditions before Capture dispatches.
- Capture: only then execute the prepared command once and return complete timing/coverage/queue/accounting evidence.

Direct cross-chat send is unavailable; this dedicated branch is the receipt channel. Publication does not wake or acknowledge another chat. Quota five-hour/weekly allowances and reset remain UNKNOWN; no current warning was visible. No guessed wake was scheduled. The private checkpoint records exact paths, command, hashes and job state for supported resumption.
