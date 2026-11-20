# Offline Kraken BTC/USD paper baseline

Code **d46ff5f2597b8d51b574868f1292c5ea220c5420**, based on the sealed report adapter receipt `90c3dda`. Implementer owns this offline exploratory unit. Architect is requested to independently verify the input gates, top-level fill restriction, fees, exact UTC cutoff and drawdown arithmetic and acknowledge this exact code SHA. Manager owns any input access binding and pilot gates.

The tool audits the original observe ledger, frame and part hashes, canonical account, and ordered replay under the recorded package identity. For a UTC-midnight start it requires all 86,400 one-second sample slots, clock-valid fresh CRC books and online BTC/USD metadata. Within the window it rejects discontinuities, gaps, invalid clock, stale books, late arrivals, unresolved orders and insufficient observed top bid depth for the marked position. Continuous valid samples are the required evidence grid. Book checksums are not an exchange sequence-number guarantee.

The two controls start with USD 10,000. Cash stays idle. The quote baseline submits one capped synthetic buy request from the first eligible book in the interval. It reuses Engine price limits, risk caps, instrument increments, latency, IOC expiry, liquidation marking and ledger events. Each matched order may use only the displayed best ask or bid and unused depth. An absent eligible entry blocks the comparison. Existing risk-driven exits use the same top-level restriction. The terminal BTC position is marked at the fresh bid with a 0.8% exit fee reserve. Paid fees are separately reconciled against fills. The report supplies net USD, percent and maximum marked peak-to-trough drawdown. The exit reserve models valuation and does not represent an observed final sell. Even validated quotes cannot prove execution in a real Kraken account. No unsupported fee, slippage or strategy scenario is selectable.

```sh
python -m unittest discover -s tests -v
python -m crypto_paper verify --suite data --out "$FRESH_PRIVATE_DATA_RECEIPT"
python -m crypto_paper verify --suite execution --out "$FRESH_PRIVATE_EXECUTION_RECEIPT"
python -m tools.kraken_paper_day --manifest "$PRIVATE_SEALED_MANIFEST" --day "$UTC_DAY"
```

**32 offline tests passed**, including four targeted sealed-ledger tests, plus the four data and four execution checks. The four-second synthetic coverage fixture exercises the day logic with a test-only duration patch. The CLI always uses a complete UTC day. Synthetic results:

| Control | Final NAV | Fees paid | Estimated exit fee | Net USD | Net % | Max drawdown % |
|---|---:|---:|---:|---:|---:|---:|
| Cash | 10,000 | 0 | 0 | 0 | 0 | 0 |
| Best quote | 9,998.3008 | 0.8000 | 0.7992 | -1.6992 | -0.016992 | 0.016992 |

A one-BTC top offer with deeper levels verified depth restriction and retained-source byte preservation. Other fixtures reject gaps, the diagnostic clock flag, a quote received at the exclusive cutoff, insufficient bid depth and tampered raw evidence.

**Retained real-data evaluation BLOCKED.** The available public CRC excerpt `fixtures/crypto/kraken-crc-probe.json` returned exit 2 because it has no full-day sealed capture manifest and ledger. Its recorded quotes passed existing CRC checks. The local sealed synthetic sample failed recorded-package identity. Capture's mapped private window `a626cbc` is clock-unverified, about ten minutes long, and has missing samples. No qualified real Kraken P&L, fees, return or drawdown was produced. Capture owns its source. The 50% exploratory threshold is a flag on a validated full UTC day and requires independent review. No result meets that threshold here.

## TradingView research cross-check

Reviewed MIT-licensed `atilaahmettaner/tradingview-mcp` at **04deaefba514738f297aed0a887e240ca61d746b**. The pinned indicator source computes a trailing arithmetic SMA and returns no value before the window fills. An offline 1-to-51 close check reproduced its SMA50 values 25.5 and 26.5 using the project's Decimal arithmetic. The project still supplies its own closed-bar and signal timing rules. The upstream backtest service fetches Yahoo chart data and labels the source Yahoo Finance. Its indicators are suitable as research cross-checks when inputs and timestamps match. The backtests supply no direct Kraken CRC, clock, depth, bid/ask or ledger evidence. No MCP was installed or hosted service used.

Architect can run the listed tests and review this branch next. For a real run, Capture and Manager would need to identify a qualifying retained full UTC day with independently verified clocks, a sealed ledger, source identity, and appropriate private access. Keep all input and detailed output private. This does not authorize data collection, trading, spend, dispatch, pilot launch or a main merge.
