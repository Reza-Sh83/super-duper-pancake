# Replay index and isolated queue validation

Resume base: 43e8963. Scope remains public Kraken Spot BTC/USD, simulated orders only, zero additional spend, private raw evidence, no main merge, unchanged 180-day protocol. The pilot remains STOPPED.

## Completed bounded index experiment

The experimental tool times the complete original sealed snapshot reconstruction and verification call, including index creation and symmetric ordered-event/frame/account audits. It creates an index only in the rebuilt in-memory ledger. It does not change production code, the read-only source ledger, original build verification or default reporting behavior. This timing excludes the final formatted report projection and ordinary replay CLI.

On the same retained sealed input, baseline 74.201 seconds versus indexed 12.133 seconds (6.12x ratio). All 72,097 committed frames, 54,375 ordered events, final accounts, normalized snapshots and metrics match. Input hashes were unchanged. The actual diagnostic ledger has no fills; these results establish replay invariance, not nonzero observed profit accounting. A separate synthetic buy/sell/fee/rollback case verifies identical accounts and literal expectations: total fees 1.5992 USD, final cash/NAV 9998.3008 USD, zero BTC/cost, realized -1.6992 USD. All 27 focused tests passed.

One sequential baseline-then-candidate pair can be affected by cache/order and host load. Do not advertise a speedup to ordinary CLI replay or strategy returns. Independent Architect review is recorded privately with precise scope.

## Next bounded queue experiment

Use the unchanged collector build for one 600-second diagnostic with an induced disconnect at 300 seconds. Stop project compression, replay, benchmark and test jobs during collection. Keep all queue, clock and trading limits intact. Compare disconnect origins, sample completeness, first CRC recovery, arrival/processing ages and throughput against the retained loaded run. Different market traffic prevents a definitive causal claim about host load.

## Independent clock/storage findings

The contemporaneous three-reference NTP probe still fails. No clock criterion was relaxed or replaced. Both earlier reconstructed SQLite ledger files are byte-identical to sealed sources. An experimental reversible removal of recomputable raw-envelope fields restored the exact original raw hash and reduced the raw sample to 3.67 MB. However, its 2x raw-only weekly projection plus active buffers is about 7.52 GB before complete archive overhead, exceeding the unchanged 5 GiB cap. This is not an approved archive format, global-cap lifecycle, or week-long recovery proof; originals are retained.

The existing six-hour reporting-only test is unchanged. Do not inspect its run state before its due time. Scheduled execution, report generation and user receipt remain separate checks. No regular pilot schedule or automatic quota wake is claimed.

Quota: five-hour allowance UNKNOWN; weekly allowance UNKNOWN; reset times UNKNOWN. No supported usage signal is exposed and no warning was observed. Use bounded units and save checkpoints; stop new work at any visible 15% allowance or warning.

Exact next action: complete the isolated capture on its frozen source, verify sealed readback and recovered financial-event/account equality, then compare queue/freshness/sample metrics with the loaded diagnostic. Leave all pilot gates closed.

## Completed isolated capture checkpoint

Experimental benchmark and tests are committed at ac61332. The isolated collector used that commit while its market-data/trading package stayed identical to the preceding measured capture. All package hashes matched the launch record through final readback. The 600-second diagnostic completed; no compression/replay/benchmark/test jobs ran during collection. Detailed before/after measurements and their limits are in ARCHITECTURE_CHANGELOG.md; private receipts retain input hashes, reference failures and ordered-ledger audits.

Outcome: zero queue failures versus two, zero missing samples versus five, 99.6667% planned checksum-book availability versus 97.5%, and induced CRC recovery 2.795192 s. Twelve rejected clock checks persist; operational READY remains 0%. Same-source readback/accounting passed using the isolated memory index; no strategy return or cross-window accounting equality is claimed. Architect independent review passed within this scope. All 27 tests passed before collection.

No collector/replay/compression jobs remain. Both quota allowances and reset times remain UNKNOWN; no supported signal or warning was visible. Do not assume quota reset wakes the chat. The existing delivery test is not yet due: leave it unchanged and check execution, report generation and actual receipt separately only when due. Full operational acceptance, week-long private retention and delivery remain unaccepted; pilot T0 stays unset and P&L/drawdown remain unavailable.

Exact next action: create a separate queue-load harness branch from this checkpoint and replay the same retained arrival schedule with and without bounded background load. Preserve all queue/clock/trading checks, freeze the input and test configuration, and compare per-stage service times and lost/aged frames. Inspect the existing private receipt before dispatch to avoid repeating completed captures. Continue the supported-UDP clock capability and cap-compliant recovery work independently. No main merge or additional spend.
