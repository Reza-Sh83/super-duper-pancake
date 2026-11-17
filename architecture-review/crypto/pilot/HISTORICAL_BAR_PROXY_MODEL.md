# Method decision: historical daily-bar proxy v1

Decision: APPROVED WITH PRECISE ASSUMPTIONS for exploratory modeling only. Reference: Manager `02182ce9f493af52efe1d78c042cdb5523715260`, cloud-pilot/HISTORICAL_BASELINE.md. This model is distinct from daily-sma50-v1/hold-v1 execution and does not validate the live paper engine.

Freeze before any strategy-return computation: holdout [2026-06-25T00:00:00Z,2026-11-16T00:00:00Z), exactly 144 contiguous daily bars; prior bars supply SMA warm-up only. Require at least 51 consecutive preceding bars, positive finite ordered OHLC and unique UTC starts. Fetch one official Kraken XBTUSD daily response, drop its final uncommitted row and select this exact interval; no shifting or shortening if inaccessible. Reacquisition of the same calendar window is not byte identity with Manager's private response; explicitly disclose unavailable cross-role input equality. No randomized split, tuning, parameter selection, alternative-window retry or return-driven changes.

## Exact modeled execution

Each of six independent accounts starts cash=10000 USD, BTC=0. Policies SMA50, staged exposure-hold control and cash, under base/stress costs. For a fill at daily open with start t, SMA uses 50 closes whose start dates are t-51 days through t-2 days inclusive. Latest used bar closes at t-1 day: this deliberately waits a full day after that close before the synthetic fill. Strict latest-close > arithmetic SMA means target-on; equality means off. No future close/high/low enters sizing or signals.

All fills are hypothetical full fills at that later daily open, no volume/queue/depth claim, no spread estimate and no participation inference. Base fee per side f=.008, unfavorable slippage s=0. Stress f=.01 and s=.001 per side. Buy executed price O*(1+s), sell O*(1-s); fee is executed notional*f. Spread assumption is zero beyond stated slippage. No native tick/quantity/minimum metadata, partial IOC, 250/1000ms latency or five-second TTL can be verified with bars. Fractional BTC with Decimal precision34; display only rounded. These are explicit model deviations, never production changes.

Let a=O*(1+s)*(1+f) (buy cash cost per BTC), m=O*(1-s)*(1-f) (net liquidation proxy per BTC), N=cash+BTC*m. Define conservative exposure cost as BTC*a. At each open:
1. If sticky sampled daily-loss/drawdown lock or off signal: sell all at net m, target zero.
2. Otherwise, if BTC*a>.10*N, sell max(0,BTC-.10*N/a) at m. This is modeled next-open cap reduction, not an observed intraday fill.
3. When increases are allowed, quantity x=max(0,min(cash/a,.025*N/a,(.10*N-a*BTC)/(a+.10*(a-m)))). It enforces order cost<=2.5% pretrade N and exposure cost<=10% posttrade N. One increase maximum per daily open; recalculate N after any reduction. No borrowing or shorting.
SMA may increase on each on-signal day. The staged-hold control follows the same increases until first reaching the conservative 10% posttrade exposure boundary (absolute USD tolerance 1e-20), then never buys again, including after a risk-driven reduction. A sampled loss lock stops both traded policies permanently in this exploratory version; there is no automatic release. Cash never trades. These controls have equal initial cash, caps, costs, fill times and sampled lock definitions; realized exposures may differ and must be reported. Staged hold is not a 100% BTC benchmark or an assertion of identical production hold-v1 behavior.

NAV at open/close P is cash+BTC*P*(1-s)*(1-f), including estimated liquidation costs. Paid fees separate from this exit reserve; no double subtraction. Report final NAV, net USD=NAV-10000, percent=100*(NAV/10000-1), paid fees, estimated exit reserve, modeled turnover/fills and mean/max sampled marked exposure. Do not force terminal liquidation; final close liquidation reserve is already included.

Sample NAV immediately before each open trade, after each open trade and at each daily close. Peak starts10000; sampled maximum drawdown=max(1-NAV/peak) across these ordered samples. Opening pretrade NAV is that day's sampled loss base. If close NAV<=.99*opening NAV or any sampled NAV<=.96*peak, latch the respective lock. At an opening sample a drawdown lock prevents buying and targets immediate modeled reduction; after-trade loss effects and closing locks affect the next permitted trade. Locks persist. Daily OHLC cannot observe intraday stop timing, trough drawdown, gaps, after-signal availability history or true account liquidation prices. Report sample-based drawdown explicitly as a lower-information path statistic; it is not a bound on actual intraday drawdown or loss.

## Required tests before the single evaluation

- Flat-price 100, buy1 BTC with f=.008/s=0 gives cash899.2 from1000, mark99.2 and NAV998.4; fee .8, exit reserve .8. Sell1 at same price returns cash998.4; do not subtract fee again.
- Cash account remains10000, zero fees/drawdown; positive-return signal does not affect it.
- Modifying the fill-day or immediately preceding day's close cannot affect that day's signal. Changing the latest eligible t-2 close may affect it. Strict equality is off.
- 10000-cash increase costs at most250; conservative posttrade exposure never exceeds10% within Decimal tolerance. No negative cash/BTC. Both traded arms use the same sizing routine.
- Missing/duplicate/off-grid/wrong-window bars cause a blocked input result; no imputation or boundary substitution.
- Sampled 1% day-loss and4% drawdown equality latch; no reset. No fill is synthesized at daily high/low to make an intraday stop pass.
- Staged hold cannot repurchase after completion/reduction. End NAV includes exit cost reserve; interval result reconciles cash and BTC.
- Report all six accounts, costs and matched comparisons on the same144 bars, including losses. No selecting a scenario after results.

Architect owns one independent bounded reproduction after publishing this model and tests; Manager owns reconciliation/comparison against its exact private data if accessible. Raw rows and private input identities stay outside public Git. Public source, synthetic tests and aggregate model outcomes are permitted. If the fixed window cannot be obtained, return BLOCKED_INPUT with cash control only, not another date window.

All production clock, order, risk, storage and acceptance criteria remain unchanged. The 168-hour pilot stays stopped. The 180-day protocol is untouched; this observed historical holdout is exploratory and cannot become unseen confirmation evidence.
