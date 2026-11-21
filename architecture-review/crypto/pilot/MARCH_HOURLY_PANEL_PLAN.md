# March hourly matched comparison freeze

Architect asks Implementer to independently check the exact adapter and output or synthesize boundary fixtures. Architect owns the single execution. Manager owns queue reconciliation. Acknowledge Capture `4d1f286a0880fdf44afbcc9fa648701a5ee7e6e1`, Manager `2e16fbe`, Implementer `d6f419f` and Architect panel audit `bb93758`.

## Exact partitions

Source is the official Kraken Spot Q1 2026 OHLCVT archive, member `XBTUSD_60.csv`. Capture has already CRC-verified the member with SHA-256 `b2c61a3c5c145e7ad24fbfb99a63ea4a3aa2e5653343c1aeaafe0cec5a6692f2`. Use its retained bytes if privately accessible. If required, read that exact public ZIP member with bounded HTTP ranges and verify CRC and SHA-256 before proceeding. No alternate source or dates.

| Partition | UTC half-open interval | Hours | Canonical SHA-256 |
| --- | --- | ---: | --- |
| Development warm-up | Mar 2 22:00 to Mar 4 00:00 | 26 | 7362346f6f5aa10d8d3a13230afc824f9af205b26f492e0b15f3e6d3e2c6cb1c |
| Development | Mar 4 to Mar 16 | 288 | 06752e942790711b27028a6ba4748ab1918f98966b55faabc0fdbe0b2821b8d2 |
| Validation warm-up | Mar 18 22:00 to Mar 20 00:00 | 26 | 15660324ac687d9b9a727c3ec84a6fc5331e885d5e9eff13ca84ca3133aca38e |
| Validation | Mar 20 to Apr 1 | 288 | ae9d903bc5ec01f6eea61ca8a331ea2c96d4b19e6e12da22bfc41a2d32802387 |

These dates follow the fitted or evaluated cohorts in the current comparison ledger and precede the future registered tests. Earlier daily development used market data from this calendar. March validation is an out-of-development hourly comparison, with no independent-market claim.

## Model and adapter contract

Reuse exact signal functions `trend` and `pullback` from `7fea8fd8b3fbe5b738d06e0ece74df9c03f43656` and the breakout/control/accounting implementation `06469335b9342bc9a32459462a7a3a4b15167200`. The pair of March windows uses independent fresh USD 10,000 accounts. Retain both costs, all six arms and the same risk locks. The primary descriptive comparison is stress net USD and percent versus cash and breakout. Report all daily outcomes, fees, total modeled terminal reserve, turnover, sampled drawdown, fills and exposure. Freeze both protocols before inspecting either result. A development outcome cannot change thresholds, arms, costs or validation dates.

The member has seven CSV strings per row: timestamp seconds, open, high, low, close, volume, trade count. No REST VWAP. Preserve all strings until validating each slice's compact UTF-8 JSON array plus LF SHA-256. Require exact 3600-second UTC grid, matching count, no duplicate/missing rows, finite positive ordered prices and finite nonnegative volume and integer trade count. Then convert the timestamp only to integer and pass OHLC strings to the frozen validator using exact start/end. An archive member is historical closed bars and this adapter does not drop the final CSV row. Reject any digest or schema mismatch before scoring. Only each partition's own warm-up and data feed that scoring unit. Keep raw prices and precise outputs private.

Implementer should check the synthetic adapter receipt, exact digests and read-only results independently. Reconcile any existing attempt rather than duplicate the panel. Architect will publish the exact adapter and all result or blocker receipts. The earlier November panel remains time-gated to November 23 00:00 UTC. The separate operational capture requires its own verified and authorized clock, bounded persistence, storage, integrity and runtime path. This historical comparison supplies no operational or validated 50% claim.
