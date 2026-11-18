# Seven-day retention budget from existing diagnostics

**Retention BLOCKED under the existing 5 GiB cap.** Capture audited existing
receipts and counted bytes from two sealed raw recordings. No collector,
compression, recovery, replay or guarded run was repeated.

| Existing sample, roughly 600 s each | Measured archive bytes | Archive bytes/s over 600 s | Projected seven-day total at 1× | At 2× |
| --- | ---: | ---: | ---: | ---: |
| Baseline full tar+xz | 4,682,300 | 7,804 | 5.44 GiB | 9.83 GiB |
| Repeat full tar+xz | 9,895,756 | 16,493 | 10.33 GiB | 19.62 GiB |
| Repeat experimental derived bundle | 3,777,120 | 6,295 | 4.59 GiB | 8.13 GiB |

Each total is current retained root charge (627,154,944 bytes, summing the
greater of allocated and logical bytes per entry) plus a working allowance
of 492,127,209 bytes plus the projected archive growth. The working allowance
charges the entire highest previously sampled simultaneous root peak again
on top of the current census. This deliberately double-counts some retained
evidence and gives a conservative planning scenario. The sampled peak is not
an enforced upper bound. The remaining archive budget is 4,249,426,967 bytes
or about 7,026 bytes/s for seven days. At 2× the derived sample rate, that
leaves about 93.8 hours of modeled retention. The 2× case is a sensitivity
scenario, with no claim that future rates stay below it. The 2 GiB filesystem
free-space floor and writer headroom remain additional admission checks.

The full archive exercise sampled 293 times. Its recorded simultaneous peak
was 261,549,040 logical bytes, including 61,344,218 active raw, 93,872 journal,
14,578,056 compressed archives, 56,853,049 other evidence and ledgers, and
128,679,845 temporary restore and replay bytes. Earlier transients were
outside its sampling window. The derived recovery receipt recorded a separate
sampled root peak of 492,127,209 bytes. Full restore file hashes and replay
passed locally. The derived bundle recovered all 10 files byte-for-byte after
restoring the archived cleared journal, using the pinned runtime and without
reading the original database during recovery. Its evidence covers one source
window on the same executor.

The two read-only scans measured 61,344,218 and 75,094,413 raw bytes across
about 601 seconds each. Across ten complete monotonic 60-second bins per
source, the busiest byte bins were 7,975,107 and 8,961,460 bytes
(about 133 and 149 kB/s). The busiest message bins were 9,886 and 10,647
WS messages. These are observed one-minute raw rates. Compressed busy-minute
rates are unmeasured. In the full repeat diagnostic, CRC-book coverage was
585/600 planned seconds (97.5%), with five missing samples, one induced
disconnect, two queue failures and zero unexpected transport failures.
Operational READY coverage was zero. The separate queue-only diagnostic
recorded 598/600 CRC-book seconds and zero operational READY. These short
windows do not cover day/week traffic variation or clock-verified operation.

## Exact handoff

Manager owns retention readiness. Keep it blocked until an approved format
can sustain a measured archive rate within a complete concurrent cap budget,
including active segments, ledger/journal, staging and restore. Establish a
hard write budget and verify a bounded restore and replay on an independent,
authorized zero-incremental-cost destination before claiming week retention.
Recompute the available archive budget on that setup before sizing a trial.
No retained evidence was removed.

Capture retains sole guarded diagnostic ownership at `92a0267`. Refreshed
Manager `c5f2b3988f20ea58cb8cd273637fa1d4dd0516fb`, Architect
`645c752a190d09563d9bfd7a99c444da2619177a`, and Implementer
`8ad33216082b952934ee3c2766f9101663860529` before this checkpoint. The runtime
gate is still blocked. Resume only after Manager binds a reviewed compatible
isolated runtime. No matching diagnostic process was observed. Pilot stopped.
Live quota and reset times remain UNKNOWN.
