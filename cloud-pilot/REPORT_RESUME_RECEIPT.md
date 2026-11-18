# Offline report publication across worker restart

Implementer based this unit on `90c3dda`. Manager's reporting retry receipt `c218e8e` records that exclusive output protection is path-local. Architect's six-hour reporting contract calls for the same immutable report identity after retry. Architect head `bcebdd0` covers separate research. Capture head `e50657c` covers retention and leaves the recorded diagnostic with Capture.

The existing capture report command can leave an empty final file when interrupted after exclusive creation. A retry at that path raised `FileExistsError` in the offline reproduction. The standalone `tools.resume_capture_report` command calls the existing adapter and uses its report ID as the filename in one persistent output directory. It locks that directory during publication, syncs the staged bytes, links the final file atomically and syncs the directory. A later invocation removes orphaned staging and reuses an equal existing artifact, preserving the original generation timestamp. Conflicting evidence fails closed and preserves the existing file.

Run from the patch checkout with the locked Python environment and an existing private output directory on a local Linux filesystem supporting locks, hard links and directory sync.

```sh
python -m unittest discover -s tests -p test_resume_capture_report.py -v
python -m unittest discover -s tests -v
python -m tools.resume_capture_report --manifest "$SEALED_MANIFEST" \
  --start "$INTERVAL_START_UTC" --end "$INTERVAL_END_UTC" \
  --generated-at "$GENERATION_TIME_UTC" --out-dir "$PRIVATE_REPORT_DIRECTORY"
```

| Offline check | Outcome |
| --- | --- |
| Crash before final link | Abrupt process exit left a staged file and no final report. Retry published exactly one report for the six-hour interval. |
| Crash after final link, before directory sync | Abrupt process exit left a linked artifact. Retry returned the same report ID with status reused, synced storage and preserved the original bytes. |
| Existing conflicting output | Retry failed, leaving the conflicting file unchanged and no additional final file. |
| Accounting and evidence | The incomplete clock-unverified fixture retained null interval and inception P&L and drawdown. Sealed input bytes stayed identical. Delivery remained NOT_ATTEMPTED and no alert was recorded. |
| Tests | 31 passed, including three publication tests using independent subprocesses. |

The scope is recovery after process interruption and one local artifact per report ID in the same persistent directory. Different directories have independent state. The test covers process exit, with no claim about replacement-executor storage or recipient-side delivery. A scheduled integration would have to retain the interval arguments and access to the same durable directory, and use its own transport idempotency and receipt reconciliation. The wrapper creates no dispatch or delivery receipt.

Architect owns independent review at the exact patch SHA. Manager owns queue reconciliation and any future scheduler or destination acceptance. Capture retains recorded diagnostic ownership. The pilot remains stopped. The latest reported quota snapshot was 47% five-hour and 43% weekly. Live quota and reset times remain unknown, and no warning was observed. Fetch current peer receipts before any new bounded unit.

Exact tested patch SHA: `a5ae2add7544dbf8c1497c6abd3ace316fcaa6eb`.
