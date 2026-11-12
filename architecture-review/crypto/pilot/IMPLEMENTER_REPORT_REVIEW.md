# Six-hour projector: request for independent review

To Cloud Architect and Cloud Manager. Architecture handoff acknowledged at commit **13fb02492b358392089d2a151a1f57cf6efb309a**, document `SIX_HOUR_REPORT_HANDOFF.md` on `cloud-pilot/architecture-handoff`.

The installer and container setup are preserved separately on `implementer/reproducible-install` at **886589b757d9c0aa968dab9d7d5ceeb0ea344f89**. This review branch adds a small standalone projector and synthetic tests. It does not release or start the pilot.

## Scope of this patch

`crypto_paper.pilot_report` reads an explicitly normalized snapshot JSON and creates a report without writing its source. It accepts only `fixture` and `dry_run` modes. It never opens a network connection, places an order, unlocks risk, freezes confirmation research or sends an alert. Every result has `operational_ready=false`, `review=PENDING` and `delivery_status=NOT_ATTEMPTED`. A threshold result is at most `candidate_pending_review`; no verified result can be sent by this module.

Derived fields: strict pre-cutoff boundary liquidation NAV, paid fees, exit reserve, interval/inception return, observed drawdown, coverage against all planned seconds, six-hour index and immutable report identity. UTC-day calculations use the day's own opening NAV. A delayed generation uses the original cutoff. Late snapshots and fills cannot repair it. Decimal precision is 34 and JSON decimal values are canonical strings.

Required input timestamps are integer UTC nanoseconds. Snapshot state/receive times, mark/mark-receive times and committed frame identify availability. Latest eligible state is selected by frame. Missing/stale/invalid exposed marks produce unavailable returns. Caller-supplied `unresolved_gaps`, integrity, replay and risk status gate candidate eligibility. These statuses are synthetic assertions in this patch, not independent evidence.

Inputs `reconciliation`, `paired_baselines`, `decisions`, locks, dust and completed work are carried through, not independently derived or certified. The source adapter must produce those from all three separate policy ledgers in both scenarios and bind the code/config/manifest hashes. This patch does not yet satisfy the full reporting or delivery release contract.

The output is created exclusively, so retries cannot overwrite a prior report. Identity is stable across regeneration times; corrections need a revision, reason and audit link. Crash-safe publication and uncertain delivery reconciliation remain adapter responsibilities, with no exactly-once claim.

## Reproducible synthetic validation

```sh
python -m unittest discover -s tests -p test_pilot_report.py -v
```

Thirteen synthetic tests pass on Python 3.12, including in the existing non-root container with network disabled. Existing data, execution and research-development suites also pass. Raw test output is intentionally excluded from this handoff. Tests assert independent expected values for the fee example, six-hour return, stale/clock/missing boundaries, coverage gap, day denominator, rejection gates, strict fill/receive cutoff, retries, correction audit, observed drawdown and source/output immutability. No observed market return is represented by these fixtures.

The source adapter, revised-bar leakage and warm-up isolation, full six-arm baseline pairing, independent reconciliation, durable report publication, approval binding, scheduler restart/outage behavior and acknowledged dry-run delivery still need integration tests. Existing engine risk/clock behavior is unchanged.

## Ownership and next actions

| Item | Single owner | Next action | Trigger |
|---|---|---|---|
| Projector independent review | Cloud Architect | Review this branch against handoff 13fb024; acknowledge its exact commit and return findings | Review branch visible |
| Normalized snapshot adapter contract | Cloud Architect | Confirm or revise integer timestamp/frame availability schema, inherited peak semantics, and required reconciliation/pairing provenance | Projector review |
| Adapter implementation and tests | Cloud Implementer | Derive input from immutable capture and committed separate ledgers, then add real-prefix consistency and leakage tests | Architect findings/contract available |
| Operational readiness and coordination | Cloud Manager | Own existing preflight, acceptance, storage and delivery gates; collect reviewer acknowledgment | Sanitized implementation handoff visible |

Please use the agreed dedicated handoff branch for the review response and name the reviewed commit. Repository publication establishes availability; peer receipt and approval remain unverified until acknowledged. No original coordinating chat or personal computer is required for these actions. The pilot remains stopped, and main still requires human merge approval.
