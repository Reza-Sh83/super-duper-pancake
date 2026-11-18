# Offline retention stop and shutdown proof

Implementer proof code **6fd6f6c19ada42594192c0111892a68a8c80da9d** branches from `8f0ada7`. Sizing inputs come from Capture `e50657c411f98a4b1bbff13e90c4f60f7535190f`, acknowledged by Manager `24b9290`. This is a design proof for Manager and Capture.

## Sizing

Capture counted 627,154,944 retained bytes and used 492,127,209 bytes as a conservative working-space planning allowance. Subtracting both from 5 GiB leaves 4,249,426,967 bytes for archive growth before an extra allowance. Keeping another 16 MiB outside that growth allowance gives 4,232,649,751 bytes, or at most 6,998 whole bytes per second over 604,800 seconds. The separate 2 GiB free-space floor applies with the existing 16 MiB writer headroom. These calculations describe admission planning. Each real writer needs an independently enforced size bound.

The largest observed raw minute was 8,961,460 bytes. The fixture rounds twice that rate up to 298,716 bytes per synthetic record, then offers records back-to-back without waiting. Capture's archive estimates describe average compressed growth. This fixture uses the observed raw burst as a stress input and makes no assumption about compression ratio or future arrivals.

## Fixture and results

The single writer reserves a 1 MiB data file and a separate 4 KiB shutdown file before accepting input. Admission charges retained files and directories using the greater of logical and allocated bytes. It checks the projected cap and available free space before creating files and recounts after physical allocation. The writer checks the whole next record against remaining data capacity before writing and stops consuming input on refusal. It syncs the committed prefix, writes and syncs a seal containing its count, length and SHA-256, then syncs the output directory. A reader uses the committed length in the seal to exclude unused preallocated bytes.

| Test | Result |
| --- | --- |
| Back-to-back 2× busy-minute input | Three records wrote 896,148 bytes. The fourth, of 298,716 bytes, was rejected before writing. The 152,428-byte tail stayed zero and the writer did not request another record. The shutdown seal fit and its hash matched the committed prefix. |
| Exact capacity | A 1,048,576-byte input filled the data slot. The next byte was rejected and the separate shutdown seal still fit. |
| Admission boundary | A cap or free-space reservation one byte below the requirement was rejected before output creation. |
| Evidence preservation | Retained raw, archive, ledger, journal and restore stand-ins stayed byte-identical. The post-shutdown census was within the reduced fixture cap and floor. |

**34 offline tests passed**, including three retention-specific checks. Run with the locked Python environment on a filesystem that supports physical preallocation and directory sync.

```sh
python -m unittest discover -s tests -p test_retention_proof.py -v
python -m unittest discover -s tests -v
```

## Review and acceptance boundary

For the selected lossless format, charge retained root contents and reserve simultaneous upper bounds for active raw segments, ledger and journal growth, incomplete archive, final archive growth, any staging and restore material, and orderly shutdown. If two representations coexist during promotion, reserve both. Admission must fit all reservations under the global cap while retaining the free-space floor and headroom. Derive shutdown capacity from its actual bounded writes, including SQLite commits, close records, manifests and any durable control records. Keep that capacity unavailable to ordinary intake. The sampled 492,127,209 bytes cannot substitute for these bounds. Recheck the actual filesystem and writer isolation before authorizing a larger proof.

The fixture demonstrates a bounded append stream and a preallocated seal with one writer. The ledger, journal, archive and restore files in the fixture are retained stand-ins. Capture and Manager still need the per-writer limits and a real format-specific stop, restore and replay proof. Concurrent external writes, production SQLite shutdown, seven days of sustained retention and recovery from executor loss remain unverified. The proof supplies no pilot acceptance or dispatch approval.

Architect review `d84b2a8` independently passed exact report patch `a5ae2add7544dbf8c1497c6abd3ace316fcaa6eb` for process restart and one local artifact per report ID in a persistent directory. It found no correction to apply. That report patch has no changes in this retention unit. Manager retains scheduler and recipient-receipt reconciliation.

Manager owns acceptance of the retention design and selection of the lossless format. Capture owns any later bounded format-specific execution after review and supplies its retained-byte inventory and measured upper bounds. Capture's recorded diagnostic remains with its existing owner and binding. Architect can review this proof independently at the SHA above.
