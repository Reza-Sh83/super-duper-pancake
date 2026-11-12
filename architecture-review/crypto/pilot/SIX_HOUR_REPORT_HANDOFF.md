# Implementer handoff: six-hour report and full UTC-day alert

Prepared by Cloud Architect / independent reviewer. Scope: project design and synthetic acceptance examples only; this document does not certify a running pilot. Implement on an isolated review branch; main merge requires human approval. Public real Kraken Spot BTC/USD, simulated orders only, zero extra cost. Preserve every existing clock, execution and risk gate. Keep the 180-day blinded protocol untouched.

## Build contract

Create a separate exploratory manifest and a read-only projector over the immutable capture and committed ledgers. T0 is set only after preflight, delivery-path verification and existing acceptance gates pass. T1=T0+604800 seconds, exclusive. Produce 28 reports at T0+6h through T1; outages still produce a health/unavailable report. Full-day alerts use [00:00Z,next 00:00Z) entirely within the pilot, independently of the six-hour schedule. A partial UTC day never qualifies. UTC midnight is a convenient T0, not a requirement.

Use separate USD 10,000 ledgers for SMA50, hold and no-trade in base/stress scenarios. The primary alert arm is predeclared base SMA50; label any other arm explicitly. Do not select a winning arm retrospectively. Development/warm-up is excluded from evaluation; no pilot data becomes unseen confirmation data.

For cutoff b, use committed ledger state strictly before b and only mark evidence received before b. A fill timestamped exactly b belongs to the following interval. Persist a cutoff frame/index and manifest hashes so later generation reproduces the same result. Evaluate mark freshness at b, not at the later report-generation time. With BTC exposure, invalid/missing/stale mark or invalid UTC reference means NAV=null; retain last mark/value/time as diagnostics only. Never backfill a boundary using a quote received after it. A valid historical boundary may be reported later, visibly delayed.

Decimal precision=34; canonical decimal strings; round only display. NAV=cash+BTC*valid_bid*(1-exit_fee). Base fee=0.008, latency=250 ms; stress fee=0.01, latency=1000 ms plus unfavorable 10 bp slippage. Keep five-second IOC TTL, limits, observed spread/depth and metadata rules. Paid fees and estimated exit-fee reserve are separate; never subtract paid fees from NAV twice.

Six-hour/day net USD=end_NAV-start_NAV; net percent=100*(end_NAV/start_NAV-1). Each UTC day uses its own opening NAV. Report inception P&L separately. Paired baseline differences require matching valid intervals; show pair count and missing intervals. Cash-only no-trade NAV remains 10000 if its journal reconciles; this does not make an exposed arm's missing NAV valid.

Required report fields: run/version/code+config hashes; policy/scenario; interval/cutoff/generated_at/delivery status; start/end NAV+validity+mark timestamps/age; interval and inception net USD/percent or null+reason; cash/BTC; paid fees and exit reserve; realized/unrealized reconciliation; peak and observed maximum drawdown; locks/dust; READY/nonREADY/missing seconds; expected/eligible/timely/SKIP decisions; elapsed/168h and index/28; paired baseline differences; integrity/replay/review status; next action.

Preserve caps: increases incl. fees 2.5% NAV, exposure incl. commitments 10%, daily loss lock at 1%, drawdown lock at 4%; equality triggers lock. No automatic unlock, reset, risk escalation or forced fill on stale data. During gaps, drawdown is last-observed/unknown-current, never newly computed from a carried mark.

## Acceptance examples (synthetic fixtures; not observed profits)

| Case | Input | Required output |
|---|---|---|
| Fee/accounting | Start cash 10000; buy 0.001 BTC at 100000 with fee .008; end valid bid 100000 | Paid fee=.80; cash=9899.20; exit reserve=.80; NAV=9998.40; net=-1.60 USD / -.016%. Reservation changes free cash only. |
| Six-hour interval | Valid NAV 10000 to 10020 | +20 USD / +.2%; report index 1/28, progress 6/168 hours; fee total shown but not deducted again. |
| Stale boundary | BTC>0; latest pre-cutoff bid age 2001 ms; fresh quote arrives b+100 ms | end_NAV/net_USD/net_pct=null, reason BOOK_STALE; fresh quote cannot repair b; preserve last mark. Age exactly 2000 ms is permitted only if every other gate passes. |
| Clock invalid | CRC-good recent book but insufficient independent UTC references | CLOCK_INVALID, defensible mark age=null, zero eligible fills; no day alert. Healthy heartbeat does not change this. |
| Coverage gap | Six-hour READY=21000, observed-not-ready=300, missing=300 | Total=21600; READY=97.2222…%; degraded. Missing time is not removed. Valid boundary P&L may be shown as qualified, but no valid-day alert across an unresolved gap. |
| Invalid prior boundary | Prior close/start NAV unavailable, next close valid | Affected interval return remains null; do not divide by an older NAV and call it a six-hour/day return. |
| UTC day denominator | Complete UTC day valid NAV 10200 to 15300 | +5100 USD / +50%, not +53% against inception. Candidate only; synthetic accounting fixture must never emit a real alert. |
| Alert rejection | 50% rolling 24h, partial UTC day, stale endpoint, missing journal segment, risk violation or unresolved replay mismatch | No verified alert, even if a displayed/stale value exceeds 50%. Log reason; no reset or threshold change. |
| Leakage | Revised OHLC received after original decision deadline; earlier payload available on time | Original decision uses original available version; later data cannot rewrite it. A late closed bar produces the existing SKIP behavior. Warm-up returns excluded; no after-cutoff fills/quotes. |
| Retry/restart | Same run+arm+scenario+interval requested twice, crash after delivery request | Same immutable report identity; no duplicate financial event. Reuse delivery idempotency key or record uncertain delivery and reconcile receipt before resend. Do not promise exactly-once delivery without transport support. |

Report ID=(run, policy, scenario, interval_start, interval_end, revision); revision increments only with an explicit correction reason and audit link. Alert ID additionally binds UTC day, reviewer receipt and manager approval. Approval is bound to a report hash; correction invalidates prior approval. Separate fixture/dry-run delivery from production alert state.

## Review and delivery gate

Threshold >=50% net in a complete valid UTC day creates `candidate_pending_review`, never an automatic verified notification. Independently reconstruct fees, fills, holdings, cutoff NAV, coverage and risk from immutable inputs without calling the same accounting helper. Require accepted execution/replay, no unresolved integrity/risk violation, valid endpoints and required coverage. Manager reviews the signed receipt and explicitly approves before `verified_paper_result` is sent. Label paper-only USD, exact UTC day, net percent, fee model, coverage and approval identity. This is an alert threshold, not a profitability promise or statistical acceptance.

Before T0 demonstrate: scheduler survives restart; six-hour outage report is generated; UTC-day candidate is held until approval; duplicate/retry is handled; receiver accepts a clearly marked dry run; receipt/acknowledgment and delayed/failed-delivery state persist. No destination, scheduler job or delivery receipt is verified in this handoff. Implementer/coordinator must name the authorized destination/transport and produce a dry-run receipt; no third-party message was sent by this assignment. Do not invoke crypto-v1 freeze/unseal for the pilot.

## Acceptance and storage requirements

The approved [build contract](../CRYPTO_BUILD_CONTRACT.fa.md) remains authoritative. Before READY, require three independent UTC references in 30 seconds, median offset <=500 ms, span <=250 ms and refresh <=60 seconds. A reference gap >120 seconds or UTC/monotonic jump >500 ms halts. Book age <=2000 ms, future tolerance <=500 ms and induced recovery <=15 seconds remain unchanged. Reporting cannot override these gates.

Require a complete 24-hour acceptance receipt for the selected build: READY >=99% of all 86400 planned seconds, READY p95 age <=1 second and p99 <=2 seconds, induced disconnect at hour six, >=5/6 timely operational bars, zero fills from rejected input and zero journal divergence. An interrupted test, successful preflight alone or diagnostic replay is insufficient. No qualifying new receipt is provided by this design document; acceptance remains unverified until independently reviewed evidence is available.

Storage must respect the approved 4096-frame/32 MiB queue, 500 ms queue age, 1 MiB frame, 64 MiB/one-hour segments, 5 GiB total capture cap and 2 GiB free-space floor. A seven-day retention plan must demonstrate sufficient existing capacity at zero extra cost, preserving required evidence, segment ordering, hashes and boundary replay. Use a measured workload and a conservative projection that includes journals/reports and overhead. Do not silently increase limits, reset the calendar denominator through segmentation, or delete required evidence. Storage acceptance requires a bounded-capacity/rotation exercise with safe-stop and replay checks. This handoff supplies requirements, not a passing capacity certificate.

Cloud Manager owns routine coordination and receipt review. The Implementer can read this branch directly and submit the separate projector/delivery adapter and synthetic fixtures on a dedicated branch. No original chat or local PC is a dependency. Before pilot release, independently review the implementation, full acceptance receipt, storage validation and dry-run delivery receipt. No main merge without human approval; no private exchange credentials, live orders, purchases or additional spending.

## Peer handoff and next owners

Cloud Implementer: please prepare the smallest isolated patch for the projector and delivery interface, with synthetic tests covering the acceptance table. Publish the patch commit and sanitized test results on a dedicated branch; include cutoff/restart idempotency, invalid-mark null handling and alert approval binding. Trigger for Cloud Architect review: that commit and test summary become visible in this repository.

Cloud Architect owns independent accounting, leakage, acceptance and storage review. Cloud Manager owns coordination, readiness receipt collection and the approved delivery destination; no original chat or PC is needed. The Manager should verify the separate acceptance, retention and delivery gates before assigning a start timestamp. Human approval remains required for a main merge.

Repository inspection found the separate installer change at commit `886589b757d9c0aa968dab9d7d5ceeb0ea344f89`. Its changed-file list covers installation/container setup only; it supplies neither seven-day retention logic nor a complete 24-hour acceptance receipt. Installation success must not be interpreted as pilot acceptance. No product behavior changes are requested by this document.
