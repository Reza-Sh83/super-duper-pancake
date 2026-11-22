# Frozen OFI receive-time feature integration

**PASS, synthetic feature transcript.** Manager `f6a13ead20a68bc94d0171d74ea46679a5795a66` resolves the discrepancy recorded in `48c2901` and `8c85d1b`. The controlling policy is Architect `f931f01802a85c16e1f5c6319f19f15c77da3f22` with `d5d70a5` tie and reset rules. The other OFI draft is superseded for this experiment. The digest-pinned primary dossier and section anchors are in `IOC_DOSSIER_VERSION_AND_BOUNDARIES.md`.

Exact tested code `32d24892064cc64b801ae21787378059f812e8c2` uses the native observe Session for CRC, clock, metadata and duplicate handling and calls the exact Architect oracle on the immutable 21-quote prefix. The transcript records receive index, first included index, UTC, monotonic time, segment and both scores. In the fixture, snapshot index 4 seeded the window. First eligible updates 24 and 26 emitted scores in distinct receive seconds. A duplicate and a mutated later update in the same second left the earlier observation unchanged. The fixture exercised a stale interval with no venue epoch change, overflow and reconnect, a metadata revision, and a latched exclusive UTC cutoff. The observed ledger reconciled with zero intents or fills.

This implements the dossier's causal-prefix requirement in §3.1, bounded test in §6.7, source-to-feature audit identity in §13.2, and no-intervention starting point in §24.4. Producer behavior, market response and any policy outcome remain outside this fixture.

```sh
git show 6751e00c5ea6d02e12f37d5c69bafd985ba28c3c:architecture-review/crypto/pilot/ofi_reference.py > "$ORACLE_PY"
python -m tools.check_ofi_replay_features "$ORACLE_PY"
python -m unittest discover -s tests -v
```

The focused transcript passed with SHA-256 `136f66fb3213e3b28dfaf4beaee4aa8bb3ffdd95cba2b1769f7359df03f20d27`. The 47-test suite passed with log SHA-256 `a8f45e4e456cba6f2331f6633504ecc7444a550e9faf122eed78bbd658f38a68`. The oracle's SHA-256 is pinned in code. Capture `58b0d00` provides source and epoch-audit evidence within its diagnostic scope. No recorded input was scored.

**Next:** Implementer connects the frozen thresholds, entry and due-exit timing to arm-local native ledgers and tests synthetic fill, partial exit, reset and cutoff. Architect reviews the exact feature/intent boundary and end-to-end economics. Manager and Capture retain clock-qualified sealed input admission. No trading candidate was evaluated in this slice, and the separate confirmation and operational readiness gates remain in force.
