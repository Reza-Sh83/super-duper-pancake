# RET-MAP-01: sealed-window eligibility for persistent storage

Capture checked one existing clock-unverified observe window against the
input inventory in Implementer receipt b205bf7 and exact runner
0ffd360fdee99060673933aedd9468f882586b4b. Input identity and strict admission
arithmetic pass. Direct execution of that runner remains blocked.

The source has 10 regular members, one ordered raw part and 72,179,809
logical bytes. All files matched the sealed inventory before and after the
read-only check. Manifest hashes matched the raw part and ledger. An immutable
SQLite quick check passed with a contiguous 72,097-frame committed ledger and
54,375 event rows. Existing RET-AUD-02 verified all ten members of the full
9,895,756-byte archive. This unit created no archive, restore or trial output.

| Sorted archive and restore inventory | Files | Logical bytes |
| --- | ---: | ---: |
| Raw segment | 1 | 61,344,218 |
| Sealed ledger and cleared journal | 2 | 10,424,904 |
| Bars, manifest, metrics, report and writer marker | 5 | 385,591 |
| Storage-probe database and journal | 2 | 25,096 |
| Total | 10 | 72,179,809 |

Preserve these members by relative path with exact bytes and hashes. The
source ledger, journal and source-side metadata belong to the archive and
restore inventory. The proof's active raw, database and journal are separate
working outputs. At 4 KiB rounding per restored file the total is 72,200,192
bytes, including a largest slot of 61,345,792 bytes. The plain sorted PAX stream
models to 72,192,000 bytes including tar padding. The historical archive size
provides a local comparison point. The PAX calculation supplies no upper
bound for streaming XZ output.

## Proposed one-window reservations

| Simultaneous output | Candidate hard slot |
| --- | ---: |
| Active raw | 64 MiB |
| Active database and journal | 32 MiB each |
| Completed archive and overlapping compressor stage | 96 MiB each |
| Restored inventory | 72,200,192 bytes |
| Setup and metadata allowance | 8 MiB |
| Working total | 416,133,120 bytes |

These are proposed limits for a later one-window validation. The archive
and active writer sizes are budget ceilings that must fail closed on overflow.
Actual output and SQLite close behavior under these ceilings remain unverified.
The model assumes SQLite temp and replay in memory, pipe logs and a separately
reserved shutdown slot. Otherwise charge those allocations explicitly.

The complete retained root charged 627,175,424 bytes at census. Its charge
plus the modeled working total was 1,043,308,544 bytes, leaving 4,056,965,120
bytes below the 4.75 GiB intake stop. Both strict Manager inequalities also
passed using the entire 512 MiB envelope, including the free-space check
above 2,969,567,232 bytes. Recount with target allocation granularity and
measured project occupancy before admission. Keep the existing 256 MiB
shutdown reserve and the 2 GiB floor plus writer headroom. Recount actual
allocated blocks after provisioning before allowing writes.

## Exact handoff

- **Implementer** owns a format-specific candidate. The 10-member count
  fits the existing limit of 16, but the 64 KiB per-member and 128 KiB total
  limits refuse this inventory. The exact runner requires tmpfs and this
  evidence root reports overlayfs. Generalize only under a reviewed
  persistent-filesystem allocation and isolation model. Measure provisioned
  charge and bound overlapping archive stages, SQLite journal/commit/close,
  restore and shutdown. Preserve the reviewed strict comparisons and
  demonstrate failure containment before using the private window.
- **Implementer and Architect** must resolve the build identity boundary.
  The pinned runtime versions match the manifest. The candidate package
  differs from the sealed manifest inventory in capture_report.py alone.
  The runner's verified_parts check hashes the whole package, so its direct
  report path would reject this source. Isolate verification/replay in the
  recorded sealed build or bind a separately reviewed adapter that checks
  the sealed build and candidate identities explicitly. Do not edit or
  reseal the source or weaken verification.
- **Manager** owns persistent target, test scope and exact binding after
  review. The current Manager b67630a binds synthetic scope only. A later
  test must verify durability across a separately invoked reader and
  reproduce the complete file inventory, ordered events, committed frames
  and final account from archive plus pinned code. Independent replacement
  recovery additionally requires an existing authorized private destination
  and synthetic checksum readback at zero incremental cost.
- **Capture** retains the source and sole guarded diagnostic ownership.
  No compatible reviewed runtime binding was present in Manager b67630a
  or Architect 610cd00. No guarded attempt or substitute probe ran.

This source covers roughly ten minutes, with 585/600 planned CRC-book seconds,
five missing samples and zero operational READY. A six-hour diagnostic wrapper
must preserve clock-unverified and incomplete coverage. The window can test
exact recovery of this inventory. Seven-day sizing, validated returns and pilot
readiness remain unresolved.
