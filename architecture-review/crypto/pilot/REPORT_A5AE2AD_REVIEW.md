# Independent local report restart review

**PASS for process restart and one local artifact per report ID in a single persistent directory.** Architect reviewed exact patch `a5ae2add7544dbf8c1497c6abd3ace316fcaa6eb` against Implementer handoff `8f0ada7571902f4e96773ecb73775ea44d853d5e` and Manager queue `c218e8e444c4b11a60ea0bdb91b5e22e20a0532e`.

Ran the three focused tests on the exact checkout with the locked Python environment. All three passed, including preservation of a conflicting existing artifact. Independently interrupted separate synthetic CLI processes at fsync boundaries using a sealed fixture. A clean publication established the control ID and bytes.

| Interruption point | State after process exit | Three concurrent retries |
| --- | --- | --- |
| After staging fsync, before final publication | One staging file and no final artifact | One published and two reused |
| After the final link, before directory fsync | One final artifact and one staging file | All three reused, even with a later requested generation time |

Each directory ended with one final artifact, the same ID and bytes as the control. The source inventory and bytes matched before and after. Coverage remained incomplete and the explicit clock-unverified reason survived. Interval and inception USD/percent and observed maximum drawdown remained null, current drawdown UNKNOWN, and delivery NOT_ATTEMPTED.

The result covers local process interruption and concurrent cooperating workers using the same directory. The before-publication byte comparison uses the same generation argument. Once published, the original artifact survives retries with a later generation argument. Scheduler recovery, recipient-side deduplication, transport acknowledgment and replacement-executor durability remain separate evidence gaps.

Manager owns queue reconciliation and acceptance of any future delivery evidence. Implementer can record this scoped PASS against the exact patch. The next reporting action is to review an existing linked schedule, sender and recipient receipt if it becomes accessible. Capture retains ownership of the guarded diagnostic. The weekly study retains its published freeze at `18bc016`.
