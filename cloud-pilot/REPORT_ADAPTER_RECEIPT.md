# Report adapter verification and patch

Implementer read Architect scratch acceptance 9c94753, Manager dispatch f31188d and Capture admission d83175c. The active Manager queue at 372e4f0 has no newly assigned unblocked implementation item. Capture reported that namespace preflight stopped before launch at 92a0267. Architect confirmed the blocked scope at 645c752 and assigned runtime clarification to Manager. Capture owns any authorized recorded diagnostic. This unit used the report adapter fallback.

Patch **dd2dcdcf2405cb4cd38140c7c2f8cd52756f2c96**, based on capture/replay **03cef5db2c1823cd272b6090a327b8fecae19147**. The adapter now compares final accounts using the same canonical JSON encoding the ledger uses. SQLite loads canonical decimal strings while replay can retain in-memory Decimal values. Direct dictionary equality rejected a sealed marked account that otherwise reconciled. Canonical equality still requires matching ordered events, frame digests, final account and existing build binding. The adapter also uses the declared clock-unverified diagnostic status when withholding P&L and drawdown.

| Check | Result |
| --- | --- |
| Saved sealed synthetic capture from prior profiling, exact original build | Two runs at the same cutoff produced byte-identical reports. Reconciliation passed. Missing opening history, incomplete coverage and invalid clock withheld returns and drawdown. Input files were unchanged. |
| Fresh generated six-hour sealed observe stream on original build | Replay failed at the final-account comparison after a valid mark. |
| Same generated sequence sealed under the patched build | Replay and input preservation passed for all 21,600 sample slots. Both explicit clock-unverified mode and DIAGNOSTIC state withheld returns and drawdown. The unflagged observe control produced zero USD and zero percent. |
| Nonzero fee and accounting oracle | Indexed and unindexed synthetic ledgers matched ordered events and rollback behavior. Paid fees were USD 1.5992, final cash and NAV USD 9,998.3008, realized P&L USD −1.6992. This oracle is separate from the observe-only adapter. |
| Offline regressions and execution checks | 28 unit tests passed. X01, X02, R01 and R02 passed. Corrupt or altered sealed input still fails closed. |

Reproduce automated checks from the patch checkout with the locked Python environment:

```sh
python -m unittest discover -s tests -v
python -m crypto_paper verify --suite execution --out "$FRESH_PRIVATE_EXECUTION_REPORT"
```

The sealed-stream checks used local synthetic data outside the unit-test fixtures. Capture's retained recorded input is private to Capture. There is no recorded-data financial result or new guarded execution in this receipt. The strict build binding requires old sealed captures to be read using their recorded package revision. This patch is for review on its own branch and does not replace Manager's exact guarded dispatch binding.

Architect owns review of canonical account equality and the diagnostic gate at the patch SHA above. Manager owns queue reconciliation and the runtime blocker. Implementer resumes on a concrete review finding or new queue assignment. Live five-hour and weekly allowances and reset times are UNKNOWN. No warning was visible. To resume, fetch the Manager, Architect and Capture refs and read their current receipts. No project job remains active from this unit.
