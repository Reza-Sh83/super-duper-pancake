# Paired queue experiment — quota-stop checkpoint

Base: 03cef5d. Dedicated branch: cloud-pilot/queue-load-harness. The measured crypto_paper package is unchanged. Public data and simulated orders only; no added spend, main merge or changes to the separate 180-day protocol.

## Completed work

An experimental same-arrival harness and synthetic tests are saved in tools/replay_queue_load.py and tests/test_replay_queue_load.py. It uses an independent producer process, bounded compression/replay workers and the original application queue path. Planned/send/read/dequeue timing, coverage, per-stage service, child cleanup and own-raw accounting audits are recorded. The socket substitute does not emulate native WebSocket protocol buffering.

The saved focused-test log reports eight passing tests. Final role handoff/review was interrupted by usage-limit errors; validate the exact saved files again before execution. No actual recorded-data paired trial has run, no paired measurements exist, and no queue improvement is claimed. The planned longer trials must exercise the original failed-clock refresh phase, rather than only startup.

The current approved NTP probe remains blocked. A separate experimental storage bundle regenerated the core SQLite file byte-identically without storing the original database. The initial full-directory check caught a rewritten cleared journal. After closing and verifying the rebuilt database, restoring its archived cleared journal produced exact hashes for all ten files. Initial and corrected receipts are retained privately. The conservative weekly capacity estimate still exceeds the unchanged 5 GiB cap; week-long retention and off-environment recovery remain unaccepted.

## Quota stop and exact next action

Project role agents reported a usage-limit warning. Which quota window, remaining percentage and an unambiguous reset timestamp are not exposed. A reset notice stated 4:46 AM without a verified timezone. Stop new experiments; do not purchase capacity or assume automatic restart.

On a supported invocation with allowance available: verify the branch/checkpoint, rerun the focused harness tests, finish independent review, then freeze the harness and execute one bounded same-schedule pair with representative background load. Repeat in reversed order only if timing fidelity and quota allow. Keep all queue, clock and risk thresholds fixed. No collector or load job is running.

The reporting-path dry run is separate from experimental acceptance. Cloud execution, report generation and actual user receipt must be recorded independently. No exact delivery timing, offline-PC state or pilot start is certified by a report appearing in chat. The pilot remains STOPPED and financial results remain unavailable.
