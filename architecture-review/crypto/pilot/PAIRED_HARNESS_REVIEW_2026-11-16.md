# Independent paired-harness review — 2026-11-16

Reviewed commit: `45cee7deb93d7944c78ae277b8a15200e7f58318` on `cloud-pilot/queue-load-harness`. Capture/replay reference: `03cef5db2c1823cd272b6090a327b8fecae19147`. Manager reference: `100ffe7e099adc4f6bb6bfc45d78c63b176b52e8`. Owner: Cloud Architect. This receipt contains source findings and synthetic test outcomes only.

## Manager receipt

| Scoped check | Outcome | Evidence and next owner/action |
|---|---|---|
| Saved focused tests | PASS | All eight tests in tests/test_replay_queue_load.py rerun with Python 3.12 and hash-pinned websockets 15.0.1. |
| Original application queue gates and cleanup | PASS, synthetic scope | Tests exercise frame/byte/age gates, no resnapshot restart, factory restoration and child cleanup. Native WebSocket buffering is expressly not modeled. Capture must preserve that limitation. |
| Complete-window arrival fidelity | FAIL as a complete-window acceptance contract | R1 below. Implementer owns source-span validation and explicit prefix/full-window outcomes before a comparative acceptance claim. |
| Comparable background load | BLOCKED | R2 below. Worker activity is established, representative sustained overlap is not. Capture owns a declared load protocol and private overlap/throughput receipts. |
| Own-raw event/accounting replay | PASS, narrow scope | Each trial rebuilds its journal and compares ordered events, committed frames and final account. Zero fills are deliberately required. |
| Nontrivial cross-arm accounting equivalence | BLOCKED | R3 below. No series-level equality gate; zero-fill trial equality is not validation of trading P&L. Implementer owns comparable-prefix/cross-arm assertions and synthetic nonzero-fill oracle evidence. |
| Existing index accounting tests | PASS, separate scope | Four tests in tests/test_benchmark_replay_index.py rerun, including literal buy/sell fees and rollback. This validates index invariance, not a real-data paired run. |
| Recorded-data paired effect | BLOCKED | No recorded-data paired result supplied at this revision. Capture owns execution after findings are addressed or explicitly qualified. |
| Unchanged clock acceptance | BLOCKED | No working supported no-cost route to all three approved independent NTP references established. Do not substitute exchange time, HTTP Date, heartbeat or synthetic clock. |
| Seven-day private storage and recovery | BLOCKED | No complete measured peak/recovery receipt or cap-compliant seven-day projection supplied. S1 below. |
| 24-hour operational acceptance | BLOCKED | Existing capture checkpoint reports rejected clock checks and zero operational READY. Diagnostic book availability is a different metric. Pilot stays STOPPED. |

Tests run: `python -m unittest discover -s tests -p test_replay_queue_load.py -v` (8 PASS); `python -m unittest discover -s tests -p test_benchmark_replay_index.py -v` (4 PASS). These are synthetic tests, not real market performance.

## Concrete findings

### R1 — distinguish offered-prefix fidelity from full-window eligibility

tools/replay_queue_load.py:54–58 excludes unsent rows and checks only excessive positive send-start lateness. Its own receipt correctly labels this “attempted prefix only,” but condition_interpretable at lines 401–403 does not require a complete offered schedule or a successful status. Full-send/full-process fields are reported separately, not enforced by the series. A legitimate first queue failure can still be interpreted on a matched offered prefix; it must not be promoted to full-window success or an equal-exposure comparison.

select_input at lines 61–96 verifies selected frames but never proves capture coverage through the requested cutoff. Reusing the saved two-message synthetic fixture, select_input(manifest,60) accepts a source spanning just 0.01 seconds. Thus a claimed 60-second experiment can contain only an initial burst and silence; short defaults also do not exercise periodic clock refresh. live.py schedules that refresh after 50 seconds, so require a verified source window and actual refresh-phase event/service evidence for the intended longer trial.

Independent synthetic probes:
- driver_fidelity([{planned_ns:100,send_start_ns:100},{planned_ns:200,send_start_ns:0}]) returns schedule_faithful=True.
- A send preceding its planned time also returns True. Current producer waits until target, so this second result is a missing verifier guard, not evidence that the producer actually sends early.
- The saved 0.01-second source is accepted for a 60-second request.

Requested fix/tests: persist verified source observation end independently of last WS message (quiet periods are valid only when observation is proven); reject insufficient source coverage before children start; separate full-window validity, first-failure matched-prefix validity and driver/other errors; validate no early sends, complete send framing and measured send-end/read/dequeue delay. Retain unsent/rejected/missing denominators. Add insufficient source span, short-write, unexpected error and first-failure classification tests. No queue limit change.

### R2 — activity is weaker than comparable load

At lines 401–403 worker_valid requires only compression input_bytes>0 and replay processed_frames>0. Both can become true with negligible or delayed overlap. Ready signals precede common start, and work start timestamps/CPU/throughput are recorded, which is useful, but no representative duty/overlap criterion is declared or tested. Compression loops over all source parts and replay loops over the whole source while foreground uses a selected prefix; document and freeze that load identity too.

Before comparison, Capture must predeclare loaded worker count, compression codec/index mode, input identities, intended overlap and acceptable workload bounds. Report actual start lag, active overlap, bytes/frames processed and CPU/service distributions per arm. Compare matched offered prefixes when a queue failure ends an arm early; do not compare total completed work over unequal exposure as if equal. Add delayed-start/early-exit workers to tests. This need not enforce identical CPU throughput: contention may itself reduce throughput, which must be reported rather than normalized away.

### R3 — self-replay is not pairwise financial equivalence

lines 367–386 compare each trial with its own raw replay and reject any fill/READY; experiment at lines 439–455 only appends receipts, with no cross-arm accounting comparison. Different runtime timestamps and failure prefixes mean full raw ordered-event hashes need not match across arms. Compare exact canonical economic state/events only over identical eligible common input, explicitly distinguishing provenance/diagnostic differences and unmatched suffixes. When no fill exists, state “zero-fill accounting control,” not validated P&L/drawdown.

Retain the existing independent literal accounting oracle from the index tests (two synthetic fills; total fees 1.5992, realized -1.6992, final cash/NAV 9998.3008), and supply a queue-harness-specific financial regression if any future change claims financial-path equivalence. Keep synthetic fresh-clock financial controls separate from the recorded-data invalid-clock experiment. Do not grant production readiness to make that experiment trade.

## S1 — storage measurement and recovery protocol

Capture.put in crypto_paper/runtime.py:80–98 counts raw/*.jsonl plus immediate output files. It is not a global recursive budget for multiple runs, nested archives, staging, restored copies or concurrent workers. Merely rotating into another directory does not establish compliance with the unchanged 5 GiB total cap. Free disk availability is not permission to exceed that cap.

Capture owns private measurement using the retained representative samples: record logical and allocated bytes for raw segments, manifest, SQLite and journals, bars/metrics, compressed archive, temporary compressor outputs, replay index and restore workspace. Sample peak during simultaneous collect+seal+compress and restore/verify; include source+archive+restored copy coexistence. Declare crash points before archive close, before checksum verification and before atomic promotion; never remove the only verified recoverable representation.

Compute a conservative 168-hour upper projection from multiple representative windows, with explicit burst/safety margin and complete overhead. Report both steady-state retained total and peak including active buffers/staging. A small compressed envelope or byte-identical core SQLite reconstruction alone does not establish full-directory recovery. Close SQLite before final verification; verify every manifest-required file, replay ordered economic events/account state, and test interruption/resume without duplicate frames or data loss. Off-environment recovery requires its own private durable-storage proof at no additional cost. No raw data or private receipts belong in this repository.

No representative private captures are available to this review assignment for a fresh rate/peak measurement; no numerical seven-day capacity PASS is claimed. Existing capture checkpoints already withhold weekly retention acceptance. Implementer owns a global lifecycle budget proposal; Capture owns peak/recovery measurements; Architect reviews them.

## Clock capability conclusion

The approved code requires actual independently validated NTP responses; all original reference, freshness, refresh and halt criteria remain intact. A fresh bounded call to the three approved references produced no valid samples. Detailed connection evidence is private; this public receipt contains no infrastructure configuration or network logs.

Primary sources: [Codex network proxy documentation](https://github.com/openai/codex/blob/main/codex-rs/network-proxy/README.md) describes configurable SOCKS5 UDP in applicable Codex deployments; [Cloud configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference) distinguishes portable cloud policy from unsupported managed listener settings. Generic proxy support does not establish a configured, supported UDP route in this managed project. No supported no-cost Cloud NTP route was verified here. Manager owns platform capability clarification for UDP/123 to the existing references, including no-extra-cost confirmation; then Capture reruns the unchanged preflight. Do not configure an unapproved relay, use the user's PC, weaken the clock gate or buy a service.

## Evidence interpretation and next owners

The user has confirmed a dry-run report was generated in managed cloud and seen in Work on the web. Exact scheduled timing and continuous PC-offline status remain unverified. Public feed/diagnostic readback/sealed replay success, delivery visibility, operational readiness and validated P&L/drawdown are separate facts. No financial validation or pilot start follows.

Implementer: fix/qualify R1 and add tests; provide exact patch commit plus sanitized results on its dedicated branch. Trigger: this review is visible.
Capture: after the revised harness is reviewed, run one bounded recorded-schedule pair with frozen input/load configuration, verify driver fidelity and refresh-phase coverage, then reverse order only if interpretable and allowance permits. Do not duplicate prior captures. Publish sanitized outcomes and retain detailed receipts privately.
Architect: when that result commit appears on an actual supported invocation, check consistency across AB/BA, common-prefix accounting, load overlap and failures. Repeated same-input effects with faithful timing can support a scoped concurrency finding; different traffic, producer lateness, cache/order or host scheduling prevent a causal conclusion. Do not generalize to native WebSocket buffering.
Manager: acknowledge each scoped result and keep readiness gates closed pending clock, global storage/recovery, delivery checks and 24-hour operational acceptance. Branch updates do not automatically wake any chat; direct messaging was unavailable at review.

No product patch or main merge performed. This is an independent review receipt, not a release approval.
