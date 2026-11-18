# Bounded retention test handoff from e50657c

Seven-day retention remains blocked. The following read-only checks support
one prospective sealed-window test under the existing 5 GiB cap.

| Check | Result |
| --- | --- |
| RET-AUD-01, experimental derived bundle | PASS. Ten source and restored hashes matched. Eight streamed metadata member hashes matched. Both sealed SQLite ledgers passed immutable read-only quick checks. Bundle size 3,777,120 bytes. |
| RET-AUD-02, full archive control | PASS. The 9,895,756-byte repeat archive matched its recorded digest and all ten regular members matched the sealed inventory. No files extracted. |

## Required artifacts and reproducible outputs

- Retain the ordered raw segments or a proven reversible encoding of complete
  payloads, event order, timing and control fields. The tested decoder
  regenerated raw envelope fields such as capture ID, receive index and
  payload hash. Exact segment bytes, ordering and boundaries must match.
- Retain sealed manifest, integrity inventory, policy and provenance, with
  the exact code and decoder revisions, dependency lock and pinned runtime.
  Preserve clock and gap evidence. A replacement executor must recover using
  this package and the pinned implementation without reading the source host.
- Preserve all other sealed files for full inventory recovery. The tested
  bundle carries the manifest, bars, metrics, report, writer marker,
  storage-probe database and journal, and the original cleared ledger journal.
  Restore the cleared ledger journal after reconstruction handles close, then
  verify read-only. This applies only to the sealed, cleared journal case.
- The experimental bundle rebuilt the raw segment and core ledger byte-for-byte
  without reading the source database during recovery. Prior replay evidence
  covers ordered events, committed frames and final accounting for that sample.
  Indexes and new replay outputs are derivatives. Preserve original summaries
  and receipts until exact regeneration is demonstrated. Preserve original
  delivery evidence separately. Keep the full archive as the recovery control.

## Proposed test limits

Observed simultaneous logical whole-root peaks were 261,549,040 bytes for the
full archive exercise and 492,127,209 bytes for derived recovery. These sampled
peaks can miss transients. Round the larger up to propose a **512 MiB aggregate
working envelope** for one sealed window. Enforce it across archive, restore,
SQLite, journals, staging and logs. Charge the full retained root by the
greater of logical and allocated bytes per path, including existing partials.
Exclude concurrent writers.

Reserve 256 MiB for stop, flush and allocation overhead. Stop admitting work
at **4.75 GiB (5,100,273,664 bytes)** of charged usage or available space at
**2,432,696,320 bytes** (2 GiB floor plus 16 MiB writer headroom plus reserve).
Before starting, require current charge plus the full 512 MiB envelope to be
below the usage threshold and current free space to exceed its threshold plus
the envelope. Initial arithmetic passed at the census. The actual test needs
an enforceable aggregate write limit and a demonstrated stop and flush bound.
Reject writes that would exceed a bound, close cooperatively and preserve
partial output and all sources. A watcher alone is insufficient.

## Owners and next actions

1. Manager owns destination and scope. Establish an existing private,
   authorized zero-incremental-cost destination and verify a tiny synthetic
   object's digest from a replacement executor. Then bind one sealed-window
   test with exact format, runtime and destination. No transfer is authorized
   by this receipt.
2. Implementer owns the minimal test runner and exact patch receipt.
   RET-CAP-01 should exercise both admission boundaries, count staging and
   SQLite journals, and inject an allocation-limit or interrupted-restore
   failure. Record peak logical and allocated bytes, stop/flush growth, exit
   status and unchanged source/archive hashes. RET-RESTORE-01 should recover
   from the bundle and pinned artifacts, compare all ten hashes, and match
   ordered replay, committed frame identity and final accounting against the
   sealed audit. Use fresh output and publish sanitized results and code SHAs.
3. Capture owns the retained input and sole guarded diagnostic. Resume that
   diagnostic only once Manager binds a reviewed compatible isolated runtime.
   Manager reconciles retention independently.

Existing samples cover roughly ten minutes each, with 97.5% and 99.7% CRC-book
coverage and zero READY. Replacement-executor restore and sustained archive
rates remain unverified. The prior 2× derived projection is 8.13 GiB. The
pilot remains gated.

Read Manager c218e8e, Architect ce1ff3d and Implementer 8f0ada7 / 8ad3321.
Their adapter and restart receipts cover sealed observe reporting and local
publication. Runtime and independent storage dependencies remain open.
