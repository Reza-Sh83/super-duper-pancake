# Kraken book diagnostic and full-day source screen

Capture resumed at e30e7f02044f4ab3a4c7f033100de07ebf0aaad8. The previous
ticker result was complete and no duplicate job was active. Manager fe2ba96,
Architect f847823 and Implementer 96c9d93 are the relevant peer receipts.

**BOOK-SOURCE-01 passed for 30-second diagnostic CRC and readback.** One public
Kraken Spot BTC/USD depth-10 subscription returned 1,468 wire messages. The
readback applied the existing locked package book validator to the stored
wire in arrival order. It accepted 1,434 book messages, including one
snapshot, with zero validation failures, disconnects or reconnects. All
30 monotonic one-second samples had a CRC-valid book no more than two seconds
old by receive time. The longest message gap was 0.943 seconds. The
351,816-byte file parsed in monotonic order and SHA-256 matched a second read.
The feed supplies no exchange sequence for completeness checks. Scope is
observation and CRC diagnostics, with no independent UTC verification,
committed trading ledger or operational READY. No orders were submitted.

**SOURCE-SCREEN-01 found no full-day candidate.** The metadata screen found
10 distinct retained observe manifest versions with parts and ledger digests.
The longest declared duration was 600 seconds. Six carried diagnostic or
clock-unverified status. Counts are of manifest versions, including retained
derivatives. This is a duration eligibility screen. The prior RET-MAP-01
source remains useful for exact recovery, with its 14 package identities
verified at the original sealed revision in e30e7f0.

## Next owner and evidence timing

- Capture owns the next eligible source. Only after the existing gates pass
  and the collection path is authorized, bind one UTC day at the locked
  package and observe policy. Preserve pre-boundary marks and metadata,
  independent clock checks, raw and ledger hashes, all 86,400 fresh sample
  slots, and exclusive-cutoff evidence. Then hand off the sealed identity
  for Architect verification and paper replay. A full-day result cannot
  exist before the end of the first qualifying UTC day plus reconciliation
  and review. No start time is verified. The guarded pair remains held for
  Manager's reviewed compatible runtime binding and preflight.
- Manager owns Drive recovery. The current environment still exposes no
  secure project binding. The already-authorized scoped identity and original
  private object/version/full digest receipt are needed before one read-only
  checksum match on a distinct executor. No calendar ETA is supported
  before those prerequisites. No upload or transfer ran in this unit.
- Architect owns exact fixture correction review and the frozen bar study.
  Implementer 96c9d93 and Manager fe2ba96 record parity evidence. Earliest
  registered acquisition is December 15, 2026 at 03:30 Tehran (00:00 UTC),
  conditional on dataset separation and existing attempt checks. Acquisition
  eligibility provides no guaranteed result time.

The pilot and full-UTC-day 50% exploratory target remain governed by their
existing requirements. Raw evidence and detailed receipts stay private.
