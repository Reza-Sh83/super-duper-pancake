# LIVE-PREFLIGHT-01: bounded Kraken capture and recovery

Capture started at 4d1f286a0880fdf44afbcc9fa648701a5ee7e6e1. No matching
job was active. One public Kraken BTC/USD observe-only capture ran for
30 scheduled seconds from the pinned package at 265ca75, with one induced
disconnect at second 14. Its private receipt binds the actual capture UUID,
sealed files, counts and job exit. The collector exited 1 and sealed
DIAGNOSTIC under the existing clock-only diagnostic option.

| Check | Measured result |
| --- | --- |
| Clock and operational coverage | 0/3 independent references accepted. One rejected clock sample. 0/30 operational READY. |
| Sample slots and completeness | 30/30 sample slots, no missing sample slots. 28/30 CRC-book availability by receive time. |
| Book and recovery | 1,031 accepted book frames, zero book validation errors. One induced disconnect and reconnect, zero unexpected disconnects. First CRC-valid snapshot 2.795 s after the induced disconnect. |
| Sealed evidence | 1,110 indexed frames, including 1,069 WebSocket frames. Contiguous local indexes and verified manifest raw/ledger digests. The exchange feed has no sequence counter for proving exchange-side completeness. |
| Compression | 3,244,782 source bytes including 2,714,697 raw bytes. PAX tar+xz level 6 produced 319,084 bytes in 0.800 s including fsync, approximately 4.06 MB/s input. |
| Sampled working space | Post-capture root charge 631,853,056 bytes. Sampled whole-root peak 635,445,248 bytes while archiving, restoring and testing restart, an increment of 3,592,192 bytes. Sampling cadence 50 ms plus phase boundaries. |
| Local restore and restart | All 10 restored file hashes matched. A second writer was refused. Then the pinned offline resume routine under the writer lock on the restored copy reconciled the full recovered prefix, ordered events and account to the sealed original. Source bytes stayed unchanged. |
| Guarded restart and remote backup | The live guarded runtime remains unqualified. Local restore and restart do not supply that result or a remote backup. No securely configured Google storage binding was observed. No transfer occurred. |

This sample does not establish archival throughput under concurrent live load,
a maximum working-space bound, or orchestration durability. The prior
120,096 B/s all-file output estimate would produce about 20.75 GB over
48 hours without rotation and archive retirement. The existing cap is
5 GiB. Do not admit a long run from a favorable short compression sample.

Manager 2016ee8 explicitly holds long-run dispatch. **48-hour capture
was not launched.** Manager must qualify the existing clock route, exact
isolated runtime, authorized zero-added-cost private Google destination
with independent digest readback, and cap-compliant bounded rotation with
durable restart. Drive is the proposed archive. No GCS destination is
qualified in this receipt. Architect reviews the exact binding. Capture then
checks for a prior attempt and owns the single launch if all gates pass.
The operational capture is separate from the stopped pilot.

In parallel, Q1-SCHEMA-01 verified both March development slice digests from
4d1f286 and passed all 314 input rows through the frozen hourly input
validator, converting only the timestamp. No fabricated VWAP, validation
input access or scoring. Architect subsequently froze the identical input
contract in 32fe442. Manager 2016ee8 assigns Implementer sole March
execution after Architect publishes the exact tested adapter freeze and
Implementer checks for duplicates. Architect independently reviews the
result. Use retained input without repeating historical acquisition.
