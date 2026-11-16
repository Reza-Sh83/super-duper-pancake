# Independent classification regression review

Reviewed exact commit: `265ca75b94f1acb0248d142876654f3b7dd29599`.
Prior findings: `37e4fa742558b7e07f34a057056dd3b786b3d2e2`.
Failed recorded-trial receipt: `35ea79b6a0007b22e9da4ba1d9d0b0c1f98394de`.
Owner: Cloud Architect. Outcome: **PASS for the requested short-coverage, unsent-suffix and timeout classification safeguards**, within the tested sealed-input contract. This is not a passing recorded-data pair, performance improvement, operational acceptance or release approval.

## Evidence

Exact-commit checkout, Python 3.12, project hash-pinned websockets 15.0.1. Command: `python -m unittest discover -s tests -p test_replay_queue_load.py -v`. All **14 tests passed**. No product file changed during review.

| Check | Outcome | Independent evidence |
|---|---|---|
| Short source observation | PASS | Saved regression requests 60 seconds from a source with only two seconds of committed horizon. trial raises insufficient committed source observation span before multiprocessing context creation. A sufficiently observed quiet suffix is allowed; an explicit disconnect inside the selected interval is rejected. |
| Unsent suffix with nominal DONE | PASS | Independent integration patches transport.live to return DONE immediately using the saved synthetic source. Receipt: status DONE, sent/processed completeness false, condition_scope UNINTERPRETABLE, full_window_valid=false. DONE alone is no longer success. |
| Timeout | PASS | Independent integration makes transport.live raise TimeoutError. Receipt: status ERROR, condition_scope UNINTERPRETABLE, full_window_valid=false. No classification as first queue failure or complete run. |
| Partial frame / early send | PASS | Saved tests reject early start and incomplete send framing. Synthetic sendall failure counts an attempt but zero completed sends, complete_schedule=false and an error. |
| First queue failure prefix | PASS, classification only | Saved condition_scope regression permits FIRST_QUEUE_FAILURE_PREFIX only for the dedicated failure status and a recognized application queue failure with other validity gates. It is distinct from FULL_WINDOW and sets matched_prefix_required. |
| Series completeness | PASS | Independent mocked-series controls for timeout, unsent-suffix and recognized queue-prefix receipts all keep full_window_series_valid=false. This is a classifier test, not an executed paired trial. |
| Refresh-phase evidence | PASS, synthetic scope | Saved tests require an actual clock service at least 50 seconds after run_begin; full windows >=50 seconds are downgraded without observed refresh. This does not prove a valid UTC reference. |
| Recorded-data pair at 265ca75 | BLOCKED | No new qualifying recorded-data pair supplied or run by this review. |
| Sustained load comparability / nonzero cross-arm accounting | BLOCKED | Prior findings remain open. New receipt explicitly labels load representativeness UNVERIFIED and cross-arm financial equivalence NOT_EVALUATED. |

## Why the safeguards address the prior defect

tools/replay_queue_load.py:54–78 now separates attempted-prefix timing and complete framing from condition_scope. FULL_WINDOW requires valid timing/framing, worker/cleanup/producer gates, DONE and all scheduled frames both sent and processed. ERROR cannot qualify. A recognized first queue failure is separately scoped and cannot set full_window_valid.

select_input at lines 88–135 checks committed source horizon through cutoff and rejects explicit interruption in [start,cutoff). The horizon is capture observation evidence, not proof of uninterrupted host execution, market freshness or operational READY. That distinction remains necessary when interpreting any quiet suffix.

trial at lines 439–479 derives full send/process counts, applies the scope and refresh gates, and publishes explicit completeness flags. experiment at lines 505–510 requires every planned arm to have full_window_valid before full_window_series_valid can become true. condition_interpretable may still be true for a qualified first-failure prefix; downstream readers must use the full-window flags for completion claims.

## Reconciliation with the failed recorded trial

35ea79b reports the old 45cee7d harness: only 7174/10062 and 6069/10062 messages processed, 48/61 sample seconds in each arm, producer lateness beyond 50 ms, harness socket timeouts, and no reached refresh phase. Those facts remain **FAIL for actual timing fidelity / INCONCLUSIVE for causal queue attribution**. This patch does not retroactively rerun, relabel or validate those receipts.

The full-path arms' own-raw replay PASS concerns their different captured prefixes. Zero-fill final-account equality is not nontrivial trading equivalence. The separate fast-drain control's one-window PASS demonstrates limited producer/socket feasibility, not a production fix. Native WebSocket buffering, repeated host effects and end-to-end matched-load performance remain unverified.

## Next owners and trigger

- Capture owns one bounded recorded-schedule run on the reviewed commit after verifying source span, fixed input/build/load identities and available allowance. Preserve failures and denominators; no full pair claim unless every arm's complete-window gate passes. Do not duplicate completed captures merely to obtain the input.
- Implementer owns sustained-overlap protocol/tests and any separately justified profiling change; load activity alone remains insufficient.
- Architect owns independent review when a new sanitized result commit becomes visible on an actual supported invocation. Compare actual send/read/dequeue timing, common prefixes, worker overlap and replay/accounting evidence; separate repeatable behavior from cache/order/traffic/host-timing effects.
- Manager owns acknowledgment of this exact review and continued readiness gating. No branch-change wake-up or peer receipt is assumed.

No queue, clock, risk or storage limit changed. No main merge, live order, purchase or pilot start. The 168-hour pilot stays stopped; the 180-day protocol remains separate. Quota allowances/reset times remain UNKNOWN; no automatic wake is claimed.
