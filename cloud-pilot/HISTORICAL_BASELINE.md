# Bounded historical baseline: cash control and execution-input blocker

Owner: Manager. This is exploratory historical modeling only, not validated live paper P&L, pilot acceptance or the separate 180-day protocol. No strategy parameters were fitted or selected.

## Input and chronological partition

One bounded request to Kraken's official public endpoint `https://api.kraken.com/0/public/OHLC?pair=XBTUSD&interval=1440` returned HTTP 200, no API errors and pair XXBTZUSD. The response was retained privately; no market rows or raw response hashes are published. Its 720 closed daily bars cover [2024-11-26T00:00:00Z, 2026-11-16T00:00:00Z), with 719 consecutive daily differences, no duplicate timestamps and no gaps. Positive finite OHLC values and low/open/close/high ordering were checked. This validates internal daily coverage, not independent truth or subdaily execution coverage. The fetched response ends at that stated cutoff; no later coverage is implied.

Fixed chronological 80/20 split, chosen without strategy-return inspection: first 576 bars are development/warm-up, last 144 bars are holdout [2026-06-25T00:00:00Z, 2026-11-16T00:00:00Z). Holdout daily-bar coverage 144/144, 100%. No randomized split, parameter sweep or future-close signal is permitted. A subsequent strategy evaluation must use only closed preceding bars for SMA50 and fill strictly after signal availability. This exploratory holdout is not unseen 180-day confirmation data.

## Existing rules retained

Reference policies: daily-sma50-v1 (10% target when the latest closed daily close is strictly above SMA50, otherwise zero), hold-v1 (existing initial 10% exposure behavior), and observe/no-trade. Initial independent cash USD 10,000. Base fee 0.008, stress fee 0.01 plus unfavorable 10 bp slippage; original latency 250/1000 ms, five-second IOC TTL, 2.5% increase budget including fees, 10% exposure cap, 1% daily loss lock and 4% drawdown lock remain authoritative. No automatic unlock, invented fresh clock or manufactured depth/fill is introduced.

## Completed control and precise missing-input blocker

The existing observe/no-trade cash control requires no orders or market fills. Across the 144-day holdout its modeled initial/final NAV is USD 10,000/10,000, net simulated historical return **USD 0 / 0%**, paid fees **USD 0**, and cash-NAV maximum drawdown **0%**. Fill assumption: no orders and no fills; no exit reserve because holdings are zero. This arithmetic control is not evidence of an economic edge or a successful traded strategy. It is not a live account result.

**Traded SMA50 and hold returns/drawdown: UNAVAILABLE / BLOCKED_INPUT.** No approved retained multi-day historical book/metadata/receive-time execution input was found in Manager's accessible project files. Peer diagnostic inputs are retained privately on separate role machines, are short observation-only samples with invalid clock, and cannot be assumed accessible or sufficient for this chronological holdout. Public daily OHLC provides no bid/ask spread, depth, IOC partial/rejected fills, subsecond availability, instrument revisions or intraday risk-lock path. A daily candle cannot verify five-second IOC, 250/1000 ms latency, depth-constrained fills or daily/drawdown lock triggering. Volume is not available depth. Model fees alone cannot repair these omissions.

No 100%-fill-at-close/open assumption was silently substituted. Such a bar-only proxy would be a separate execution model with materially different risk observability and requires explicit methodological review; it cannot be called the unchanged project's traded baseline. The bounded unit therefore returns an honest control plus precise missing execution input, not fabricated strategy P&L.

## Next owner and acceptance

Architect owns one next action: approve or reject a narrowly labeled bar-only execution proxy for exploratory research, explicitly specifying after-signal fills, spread/slippage/depth assumptions and unresolved intraday risk behavior, or identify an approved accessible historical execution dataset meeting the original rules. Do not change production gates to make research run. Publish the exact model/input decision on architecture-handoff. Manager then owns one fixed, non-tuned chronological baseline under the approved model with fees, coverage and limitations; no original-chat routine approval is needed. Acquisition must remain public, authorized and zero extra cost; raw historical input stays private. A methodological approval does not open the live pilot gates.

Checkpoint: bounded official input request and validations completed; cash control evaluated; no traded backtest, pilot, collector or 180-day freeze/unseal started. Detailed response and result remain private. Five-hour/weekly live allowances and reset are UNKNOWN; the user's last account snapshot is historical, not a current API reading. No warning appeared during this unit. Resume only on supported invocation after quota/job/checkpoint checks. No guessed reset or wake-up.
