# Persistent tar+xz test preparation

Exact preparation code **b1ae1de17b7e39a3e39a82d468758e36cc1bc91f**, based on published receipt `b205bf7`. Architect `14da13e` independently passed `0ffd360f` for the reduced tmpfs scope and requested no correction. Manager `29c20c1` requires a verified authorized backend and a separate exact binding. Capture `ab4ec93` documents the private sealed-window inventory and build mismatch. The accepted writer and its fixture were left intact and the full proof was not repeated.

**Preparation PASS. Persistent execution BLOCKED before provisioning.** The available workspace reports OverlayFS. Its backing allocation and copy-on-write behavior have not been established under the contract. The shared-memory filesystem only supports the prior tmpfs scope. No current receipt designates a verified compatible persistent backend.

## Read-only tools and evidence

```sh
PYTHONDONTWRITEBYTECODE=1 python -m unittest discover -s tests -p test_tarxz_persistent.py -v
PYTHONDONTWRITEBYTECODE=1 python -m tools.tarxz_persistent preflight "$APPROVED_EVIDENCE_ROOT" --working-bytes 323584
PYTHONDONTWRITEBYTECODE=1 python -m tools.tarxz_persistent readback "$COMPLETED_PROOF_ROOT" "$START_NS" "$END_NS"
```

The preflight is a candidate screen for direct ext4 with 4 KiB allocation units. It applies the original strict inequalities to the complete counted root and supplied proposed working bound. This narrows the proof to one inspectable filesystem candidate. A screen PASS alone supplies neither backend authorization nor checked journal and extent semantics. The actual workspace screen returned exit **2** before writes.

**Three focused tests passed.** The unit tests exercised OverlayFS rejection, strict equality refusal and one-byte-inside acceptance, and a fresh interpreter reading a completed synthetic five-member artifact set. The reader checked the completed archive against the shutdown seal, matched the source and restored inventories by path, length and hash, and called the sealed observer for report replay. It also checked both final active SQLite events and invalid-clock/incomplete-interval suppression. Tampering with the archive caused a nonzero exit. The before/after inventories were unchanged on both paths. This fixture tested the reader and did not repeat the bounded writer experiment.

## Smallest later persistent proof

1. Manager identifies an already authorized private backend at zero added cost. Screen its complete evidence root with the proposed reduced W, retain the filesystem and free-space evidence privately and confirm that no unrelated writer is active.
2. Qualify that backend's fixed extents and metadata before binding the guarded writer. Use only small synthetic files in a fresh counted location. Confirm actual KEEP_SIZE extent charge, in-range writes and fsync/readback under the existing namespace, rejection of undeclared files and growth beyond the slot, and journal initialization, PERSIST/FULL commit and close within provisioned database and journal extents. Keep the existing 5 GiB cap, strict free threshold, working cap and shutdown reserve. Any unknown or unbounded allocation remains BLOCKED.
3. Implementer then adapts only the filesystem admission for that verified backend. Architect reviews the exact revision and Manager binds one reduced five-member synthetic PAX tar+xz run, XZ preset 6. Keep the original working slots and shutdown slot separate, recount before dispatch, and retain the source and all outputs. No larger fixture is needed for this proof.
4. After both contenders and writer exit, run the independent reader above in a fresh process on the same backend. Compare the source and restored inventories, archive identity and shutdown receipt, ordered replay and final ledger. Publish only sanitized totals and the verdict. Same-backend process readback has a separate scope from power-loss or replacement-executor recovery.

Capture's mapped ten-member private window is a separate later proposal. Its published `capture_report.py` build mismatch must be resolved by replay on the recorded build or by a separately reviewed binding that attests both identities. Preserve sealed hashes, current size limits and private input. The pilot, guarded diagnostic and independent recovery gates remain with their existing owners.
