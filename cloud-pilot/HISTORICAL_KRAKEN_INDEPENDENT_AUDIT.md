# Independent audit of existing historical Kraken hourly results

**Exploratory paper estimates only.** Implementer verified the public arithmetic in Architect `2388b646ce1b9fe9db50c1d78b33924e9984ae13` and Manager `abfbe808971fd79746c4037e45cbe95fcbe39079`, and acknowledges Capture's independent 72-bar coverage receipt `ed1f48f7da17b22ecf7485ec98cc5efd68ce0495`. Both evaluations used frozen model `06469335b9342bc9a32459462a7a3a4b15167200`. Their windows overlap on November 18 and 19 UTC. Keep them separate and preserve the existing attempts. Implementer made no Kraken request and did no market-data evaluation. The older 144-day daily result at `99b5bfa` remains a separate exploratory benchmark.

| Published window, UTC end exclusive | Reported coverage | Base breakout net, fees, sampled drawdown | Stress breakout net, fees, sampled drawdown |
| --- | --- | --- | --- |
| November 18–21, 2026, Architect | 72 hours, 26 warm-up | USD 0 (0%), USD 0, 0% | USD 0 (0%), USD 0, 0% |
| November 1–20, 2026, Manager | 456 hours, 26 warm-up | -USD 14.697429 (-0.146974%), USD 11.877837, 0.146997% | -USD 19.091262 (-0.190913%), USD 14.800945, 0.190936% |

**Public checks PASS within display rounding.** All 16 account rows reconciled the USD/percent denominator, terminal-loss drawdown lower bound and passive hold scaling. Paid fees matched turnover where published, and the passive entry fees also matched their budgets and rates for both receipts. Cash was flat in both. Architect's breakout also stayed flat with zero fills and exceeded both passive holds because those holds lost money. Manager's breakout trailed cash and exceeded both passive holds. Neither result supplies a 50% modeled day or a validated paper result.

**Artifact-level audit prepared at `60b1878e15a67e724f495f22175f93e963feb574`.** The tool checks the retained response against its original private digest, excludes the open candle, verifies exact UTC coverage and warm-up, reconciles paid fees to turnover, and independently computes both matched hold baselines and their sampled drawdowns from opening and closing prices. A flat strategy is checked against cash. For a traded breakout, exact drawdown reconciliation requires its original ordered NAV samples. Without those, the tool checks the terminal-loss bound and labels that limitation. No original private responses or sample paths were accessible in the Implementer workspace. Aggregate checks do not establish cross-role byte identity.

```sh
git show 06469335b9342bc9a32459462a7a3a4b15167200:architecture-review/crypto/pilot/hourly_breakout.py > "$REFERENCE_PY"
python -m tools.check_historical_kraken_audit "$REFERENCE_PY"
python -m unittest discover -s tests -v
python -m tools.audit_historical_kraken architect "$ORIGINAL_RESPONSE" "$ORIGINAL_SHA256" "$EXISTING_ACCOUNTS_JSON"
```

Pass `manager` for Manager's fixed window. The existing result JSON must contain the original `accounts` object, arranged by cost then arm with frozen-evaluator fields. If the private wrapper used a different outer envelope, copy the existing account object into that envelope without recomputing it. Pass `--breakout-marks "$ORIGINAL_MARKS"` only if the original ordered marks are retained, keyed by cost. Each synthetic shape passed eight accounts, ordered drawdown checks and six invalid-artifact refusals. All 41 offline unit tests passed. Private fixture evidence stays outside Git.

**Next owner: Architect** runs the read-only command against the already-retained three-day artifacts and compares the evaluation-row SHA-256 with Capture's published canonical digest. **Manager** retains the longer-window artifact and can apply the same read-only command there. Publish a sanitized verdict with exact scope, retaining differences and losses. Neither role needs another acquisition or evaluation. Without the retained marks, preserve the drawdown limitation. The separate December 15 acquisition gate applies to the frozen future study only. The 180-day protocol and all pilot readiness requirements remain in force.
