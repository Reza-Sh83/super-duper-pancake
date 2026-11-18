# Bounded tar+xz retention proof

Exact tested code **0ffd360fdee99060673933aedd9468f882586b4b**, based on `13b7d95`. Contract `b67630a6716ccf0605edfc7d8a88183d27e1d804` and Capture sizing/protocol `e50657c` and `2c9ccb6`. **RET-CAP-01 PASS and RET-RESTORE-01 PASS for one reduced local synthetic fixture.** Seven-day retention and independent restore remain blocked as recorded in Architect `610cd00`.

Run on Linux x86-64 with the locked environment, supported read-only namespace, and sufficient free space on `/dev/shm`. Observed Python 3.12.14, SQLite 3.53.1, websockets 15.0.1. The test uses verified tmpfs for the synthetic filesystem allocation model. It exercises fsync and readback during the invocation. It does not establish power-loss persistence or validate an unknown copy-on-write storage backend.

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p test_tarxz_retention.py -v
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -v
```

Three focused tests and all 37 offline tests passed. The focused suite emits a `RETENTION_RESULT` JSON line. Archive lengths can vary slightly with fresh synthetic manifest timestamps. Figures below are from the final full suite.

## RET-CAP-01

Strict admission tested at full candidate W for equality, one byte outside and one byte inside each cap and free-space boundary. The executed fixture uses reduced reservations. It charges retained data plus logical or allocated bytes, whichever is greater per entry, and recounts provisioned slots before starting. The 5 GiB cap, 2 GiB floor, 16 MiB writer headroom and 256 MiB global shutdown reserve come from the bound contract.

| Incremental reservation | Bytes |
| --- | ---: |
| Active raw | 4,096 |
| SQLite database and PERSIST journal, two 65,536-byte slots | 131,072 |
| Completed archive and compression staging, two 32,768-byte slots | 65,536 |
| Restore slots rounded per member to 4 KiB | 57,344 |
| Directory/setup allowance inside W | 65,536 |
| **Total reduced working W** | **323,584** |
| Separate reserved shutdown receipt slot within the global shutdown reserve | 4,096 |

The retained root charged **53,508 bytes**. With working and shutdown reservations, the conservative fixture envelope is **381,188 bytes**. The measured incremental charge was **262,484 bytes**, including 258,048 working file bytes, 4,096 shutdown file bytes and 340 bytes of incremental directory/setup charge. The read-only namespace fixes the directory inventory throughout the guarded writes. Compression, restored members and raw writes check their own fixed slots before each write. Kernel file limits and the reviewed extent protections from `ef66fe7` constrain the actual SQLite database and journal. SQLite temporary state uses memory and undeclared disk files are denied. Replay uses an in-memory Session. Worker logs go to the parent pipe and consume no evidence directory slots.

| Census | Logical bytes | Allocated bytes | Greater-of charge |
| --- | ---: | ---: | ---: |
| Slots allocated, before worker writes | 45,698 | 315,392 | 315,992 |
| Restore-first reservation overlap | 85,574 | 315,392 | 315,992 |
| Archive-first overlap after restore and partial write | 130,696 | 315,392 | 315,992 |
| Before SQLite commit | 130,696 | 315,392 | 315,992 |
| After SQLite close | 130,696 | 315,392 | 315,992 |
| Verified shutdown receipt and directory sync | **130,854** | **315,392** | **315,992** |

Both contender orders held archive and restore reservations concurrently and refused an additional 4 KiB request before any write. The archive-first case exercised actual restore and partial compression while the real SQLite transaction and journal were active. An oversized staging write was refused before writing and latched the stop against further intake. Already admitted restore finished within its slots. The 24-byte partial archive was synced and preserved without promotion. This bounds compressor shutdown growth at zero for the abandoned stream. SQLite committed with PERSIST and synchronous=FULL and closed inside the existing database and journal extents. Its committed events passed readback. Replay and inventory checks completed before the 158-byte immutable shutdown receipt was written and synced in its own slot. Directory sync added no file data. Stop-to-seal logical growth was **158 bytes** with **zero allocated or charge growth**, within the enforced extents. The parent recounted capacity and verified process exit **0** after both thread workers joined. No worker survived.

## RET-RESTORE-01

The completed **2,440-byte** tar+xz archive used PAX format, XZ preset 6 and sorted relative regular-file members. Restore wrote **45,098 bytes across five members** into fresh, bounded slots. Exact path/size/hash inventories matched and source and completed archive identity were unchanged. Negative cases rejected symlinks, traversal, missing, extra, duplicate and out-of-order members. The existing sealed observe adapter checked **five committed frames, three ordered ledger events** and the final account through replay. Final synthetic cash/NAV was USD 10,000, BTC zero and the manual stop state matched. Invalid clock and incomplete interval metadata survived, with interval returns and drawdown unavailable.

Architect owns independent review of the exact code and fixture limits. Manager owns any larger format-specific binding and the storage destination decision. Capture retains private evidence and guarded diagnostic ownership. These local proofs leave the pilot stopped and make no seven-day, production-storage or replacement-executor claim.
