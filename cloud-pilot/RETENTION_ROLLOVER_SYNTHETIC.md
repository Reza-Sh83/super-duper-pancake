# Bounded synthetic rollover and backlog refusal

**PASS, local synthetic scope.** Implementer answers Manager `8c7176105ebafa88148dfb56b48c37906dea9d14` and Capture `49ea8bd9fe59fbf504a1075bedaa0ee2c1823ed4`. Exact code `f013e07d8be21281f6f33c3afe060bc3ef3b569c` extends the accepted archive readback branch `0302ace`. No collector, remote storage, production rotation or evidence-retirement path was changed. The test removes only a disposable generated archive after verified synthetic readback. The sealed source stays unchanged in both arms.

```sh
python -m unittest discover -s tests -p test_retention_rollover.py -v
python -m unittest discover -s tests -v
```

Two focused tests and 42 repository tests passed. The prior lossless tar+xz proof also reported PASS with PERSIST/FULL. Focused evidence SHA-256 `3f4ddf699c22159d9353033ec804583f6896bc931023953f6c88ff6d91ba5067`. Full suite evidence SHA-256 `ad3d053dbaa6c222a98e09ac4baca1142dfc9575c272564c8c16849aff4d93c5`.

- **Backlog arm.** A synthetic retained charge brings aggregate admission to the existing strict intake equality. Intake refuses before allocating a new writer and stays stopped. The local archive and original five-member sealed source match their initial inventories. Physical retained charge stays at 69,632 bytes.
- **Readback arm.** A wrong acknowledgment and a correct claimed hash with changed downloaded bytes both preserve the original. A separately synced receipt and matching readback pass SHA-256 and sealed member checks. After removing only the acknowledged synthetic local archive, the gate admits a 32,768-byte preallocated archive extent plus 4,096 bytes of fixture directory allowance. A competing reservation refuses while that extent is active. Actual fixture retained charge goes from 69,632 to 98,304 bytes and remains strictly below the intake threshold including the modeled retained charge.
- **Stop and restore.** Both arms synchronize a shutdown receipt in an independent 4,096-byte extent, with no active reservation remaining. All five archive members restore and sealed replay matches the original, including the invalid clock and null paper P&L. The original 5 GiB cap, 2 GiB floor, strict checks and reserved shutdown policy remain in force.

This fixture verifies a bounded single rollover at the admission boundary. Filesystem observations describe this generated layout. The acknowledgment uses a second local directory and supplies no cross-executor storage acceptance. Continuous rotation, production writer bounds, guarded restart and independent remote readback still need a reviewed binding.

Next Architect independently reviews the exact tests and receipt. Manager continues independent clock, guarded runtime and authorized storage qualification, then binds the production rotation only after its actual requirements are verified. Capture checks prior attempts and owns the single guarded collection after admission. No 48-hour capture is active from this unit.
