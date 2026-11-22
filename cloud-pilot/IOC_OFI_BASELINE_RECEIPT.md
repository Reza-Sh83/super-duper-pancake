# Kraken L2 IOC and shared OFI feature baseline

**PASS, bounded offline scope.** Tested code `a021bee8aeabaac9c36689b1843f967b25576a2d` on `implementer/ioc-ofi-baseline`. This uses the existing CRC Book, Capture, Session, Engine, SQLite ledger and sealed replay. The adapter checkout inherits March receipt `728dddd`. Core engine, book, runtime and input fixtures match the exact `2ab79aa` baseline. The checkout has existing diagnostics/reporting changes. All eight CLI checks passed on each checkout independently. No production policy code was changed.

The research dossier requires receive-time availability and purged chronological evaluation (§3.1), event-by-event cash, fees and inventory checks (§6.7), a pinned OFI baseline and source identity (§13.2), and separation of mechanical depth replay from market response (§24). The decision brief and build contract prioritize public direct Kraken L2, valid metadata and clock, and atomic IOC accounting. Candle outcomes remain preliminary controls. Replay cannot supply behavioral market response or hidden depth. The confirmation protocol keeps its existing 180-day design.

| Test source | Outcome |
| --- | --- |
| Captured IOC reference, code SHA-256 `1e0bf6c15bb741d7b4ce24014f399ed5f343ccc8ca8eb372f3ec2e79b731e938`, public source fixture `fixtures/crypto/kraken-crc-probe.json` SHA-256 `8ffd362b49a21c859afa7a30da1cebff4f5508c9ef55b0ad9ffdb4ee94b50135` | Three reference assertions passed and output SHA-256 matched `60f5d0301c1be6d8fbdec96c1073c5b41a606ba58eae2bc1e85f4faec28cc2b1`. Recorded stale input yielded zero fill. A synthetic freshness control yielded 0.30231883 BTC and cancelled 0.01000000 BTC using its own hypothetical fee convention. |
| Synthetic native sealed replay, fresh post-intent frame at 250 ms | Frames 1–5 seed clock, epoch, metadata, book and intent. Frame 6 fills 1.50 of 2.00 BTC across two levels and cancels 0.50 BTC. Gross USD 150.05, paid fee USD 1.2004, cash USD 9,848.7496, inventory 1.50 BTC, liquidation NAV USD 9,997.4008. |
| Synthetic stale and overflow arms | Stale frame 6 arrived with age exactly 2,000,000,001 ns and an increasing exchange timestamp. It filled zero and the order expired at the inclusive five-second TTL on frame 7. Overflow on frame 6 cancelled before the following frame. Both preserved USD 10,000 cash, zero BTC and zero paid fees. All three native ledgers replayed exact ordered effects with no reservations left. O01 stayed BLOCKED. |
| Synthetic stress engine timing | Frame 2 at 999 ms filled zero. Frame 3 at 1,000 ms filled 1 BTC at USD 100.1 after adverse rounding, excluded the next level above the fixed USD 100.2 limit, and cancelled 1 BTC. Fee USD 1.001, cash USD 9,898.899. |
| OFI feature bridge | Architect oracle `6751e00`, source SHA-256 `57dc5d309e42bbe45c030340d31a13a1314c6cb45219c669125068ac690acc35`, passed four tests. Six public captured frames reproduced their CRCs and provided no score. Synthetic accepted quotes produced +3, unchanged top produced zero, and the oracle matched normalization at exactly five seconds. Same-timestamp prefix stayed unchanged and a new epoch reset warm-up. Neither trading policy was run. |

```sh
python architecture-review/crypto/reference-captured-ioc.py < fixtures/crypto/kraken-crc-probe.json
python -m crypto_paper verify --suite data --fixtures fixtures/crypto --out "$FRESH_DATA_REPORT"
python -m crypto_paper verify --suite execution --fixtures fixtures/crypto --out "$FRESH_EXECUTION_REPORT"
git show 6751e00c5ea6d02e12f37d5c69bafd985ba28c3c:architecture-review/crypto/pilot/ofi_reference.py > "$ORACLE_PY"
python "$ORACLE_PY"
python -m tools.check_ofi_quote_bridge "$ORACLE_PY" fixtures/crypto/kraken-crc-probe.json
python -m unittest discover -s tests -p test_ioc_ledger_replay.py -v
python -m unittest discover -s tests -v
```

Two focused and 45 offline tests passed. Exact-base report digests D01/D02/F01/T02 `49eba06a065897e0a5b77057d16ec0208fff32153d8c5ce5b18084bcf985789a`, X01/X02/R01/R02 `9eadb441e50484d559d7ef26b443b55b9c048c2066a49b56323ea5874c32bf5d`. Bridge output SHA-256 `34ab873a74b073e80e2afed50c20d3b2b5de724f779a7c53a941d2f951f3e9eb`.

**One policy binding needed.** Architect `f931f01` and `d5d70a5` specify 20 normalized update transitions, a first-eligible update per UTC second, static imbalance and cash controls, and threshold/timed exits. Manager `5aaaf51` specifies five completed receive-time buckets, a five-second decision grid, sign-driven 2% targets, midpoint direction and cash controls. Those produce different causal prefixes and intents. Architect should issue one exact reconciled contract and identify superseded rules. Manager should acknowledge that contract in the execution queue. Implementer then adds the isolated decision/exit adapter and fixtures against that version. Keep the already verified common Book, fee, and IOC checks. Preserve all data, confirmation and launch gates.

Capture `10aede0` independently reconstructed 91,397 committed frames and 76,009 ordered events on the 600-second diagnostic. All twelve clock checks were rejected and operational READY was zero. The recording is negative-control evidence and is ineligible for OFI scoring. Manager retains eligible data admission. Capture retains the sealed read-only handoff. No private capture, paid service, live order, market scoring or pilot operation was used.
