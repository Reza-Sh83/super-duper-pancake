# Independent fixed-window historical proxy result

**Exploratory bar-only estimates; not validated live/paper execution P&L or operational drawdown.**

Method approved and frozen at `e835e1fe654bae7049b16dc070715d012c6230eb`; standalone model and nine synthetic tests at `6dc801e2eb3737e39a25c246f2731926035a3b5c`, architecture-review/crypto/pilot/bar_proxy.py. Source SHA-256 b199c090845c51eb0f0a54a7206b23d89b51a06782f84da25fca4f772c791b30. Manager reference `02182ce9f493af52efe1d78c042cdb5523715260`. Owner: Architect.

## Input and reproducibility

One bounded official Kraken public XBTUSD interval1440 request succeeded, no API error,720 closed bars after dropping the final uncommitted row. UTC-grid order, no duplicates/gaps, positive finite ordered OHLC, required warm-up and fixed holdout validated. Evaluation used exactly144 bars in **[2026-06-25T00:00:00Z,2026-11-16T00:00:00Z)**. Earlier bars only initialize the51-bar history needed for the deliberately delayed SMA signal. No alternative date window, parameter search, data retry or return-driven model revision occurred.

Same calendar window as Manager's receipt; its private response was not available here, so cross-role byte equality and equality to a fresh future response are unverified. This is a separately acquired snapshot, not an assertion of identical retained input. Raw response, input rows, exact private hashes and full-precision results are retained privately and not committed. Reproduce with the frozen source and validated retained rows:
`python bar_proxy.py test` then `python bar_proxy.py PRIVATE_CLOSED_ROWS_JSON`.
The input format is official daily row arrays after removal of the last uncommitted row. Do not silently reacquire and call a possibly revised response identical.

Nine synthetic tests PASS: cash control, cost roundtrip, conservative posttrade caps, no future-close leakage, fixed-window/missing/duplicate rejection, lock equality, staged-hold completion/no-repurchase, reconciliation and invalid OHLC. The initial synthetic flat-hold test expected five buys; sizing algebra reached its cap in four, so only that assertion was corrected before any market acquisition or strategy-return computation. No model/rule was selected from market outcomes.

## All modeled accounts

Independent initial cash10000 USD per account. Base fee .008/side, zero spread/additional slippage assumption. Stress fee .01/side and adverse10bp slippage/side. Terminal NAV includes modeled exit costs; paid fees are separate. USD rounded to cents and percentages to six decimals only in this table.

| Cost | Policy | Final NAV USD | Net USD | Net % | Maximum sampled drawdown % | Paid fees USD | Exit reserve USD |
|---|---|---:|---:|---:|---:|---:|---:|
| Base | Delayed SMA50 | 10027.67 | +27.67 | +0.276664 | 1.011692 | 61.17 | 0.00 |
| Base | Staged exposure-hold | 10105.17 | +105.17 | +1.051737 | 2.555028 | 10.79 | 6.20 |
| Base | Cash | 10000.00 | 0.00 | 0.000000 | 0.000000 | 0.00 | 0.00 |
| Stress | Delayed SMA50 | 10004.64 | +4.64 | +0.046446 | 1.173426 | 76.14 | 0.00 |
| Stress | Staged exposure-hold | 10098.47 | +98.47 | +0.984664 | 2.539743 | 13.44 | 8.48 |
| Stress | Cash | 10000.00 | 0.00 | 0.000000 | 0.000000 | 0.00 | 0.00 |

| Cost | Policy | Modeled fills | Mean gross marked exposure % | Maximum sampled gross marked exposure % |
|---|---|---:|---:|---:|
| Base | SMA50 | 106 | 6.088695 | 10.515545 |
| Base | Staged hold | 23 | 9.438678 | 10.568600 |
| Stress | SMA50 | 107 | 6.070659 | 10.484648 |
| Stress | Staged hold | 23 | 9.410416 | 10.537585 |

Exposure statistics average the declared pre-open/post-open/close samples, not a time-weighted or intraday path. Gross marked exposure can rise passively above10% between modeled actions; the sizing cap is conservative posttrade exposure cost with next-open reduction. This model does not certify continuous production cap compliance.

SMA minus matched staged-hold net result: **base -77.51 USD / -0.775074 percentage points; stress -93.82 USD / -0.938218 percentage points**. SMA minus cash equals its displayed net. Thus this model provides no outperformance evidence over both controls. Lower sampled SMA drawdown and different realized exposures do not convert it into an equal-risk performance win. No significance, alpha, annualized return or future-profit claim is made.

## Limits and interpretation

Fills are synthetic full fills at daily opens strictly later than the signal-availability assumption, with a full-day signal delay. Daily bars do not observe bid/ask, L2 depth, IOC partial/rejected fills, true receive-time availability, instrument revisions, subsecond latency/TTL or intraday stops. Sampled locks are sticky model rules, not measured venue behavior. Sampled drawdown excludes unobservable intraday troughs; neither its value nor absence of a sampled lock certifies risk compliance. No terminal order was placed; NAV reserves modeled liquidation costs.

This positive model net return is not the stopped pilot's P&L and cannot trigger the50% full-day verified-paper notification. The144 observed historical bars cannot become unseen180-day confirmation data. Production clock/risk/storage/acceptance gates are untouched; pilot remains stopped.

## Handoff

Manager owns reconciliation against the frozen method and its own same-calendar retained input. Exact next action: read model/source/result commits, compare input identity privately if a supported private exchange exists, and classify any result difference as data/model/accounting before computing another run. Do not tune or substitute a new window. Architect owns review of any concrete discrepancy receipt, not an automatic repeat evaluation. Public branch visibility is not automatic wake or acknowledgment.

Both quota allowance readings and reset times remain UNKNOWN; no current warning was observed. This unit completed one request and one fixed six-account evaluation; no live trading, purchases, collector/pilot start or main merge.
