# Independent panel accounting audit and validation handoff

**ARCH-PANEL-LEDGER-01 PASS** against development receipt `a97c7bef27dece0c876b40ea72b3566669f148ee`, wrapper `7fea8fd8b3fbe5b738d06e0ece74df9c03f43656` and model `06469335b9342bc9a32459462a7a3a4b15167200`. After publication, I reconstructed the new strategies with separate arithmetic that imports neither runner. I verified the delayed SMA and mean-reversion decisions, fee-inclusive entry sizing, cash and BTC, terminal reserve, fees, turnover, fills, and sampled drawdown. The four strategy-cost results and all twelve corresponding daily USD and percentage returns matched within 1e-24. None of those four paths breached a sampled lock threshold or required a passive cap trim. The control dictionaries matched the earlier replay exactly and the retained bar digest matched Capture. This audit reused the private development response and did not execute another panel or inspect validation rows.

Both strategies lost against cash and breakout. Cash and breakout stayed flat. The realized development ordering changes neither the preregistered priority nor the evaluation parameters. No 50% claim is supported. Independent UTC-clock, book, coverage and replay evidence for a complete sealed day remains a separate requirement.

**Next experiment is time-gated.** At the checkpoint, the validation window had not closed. The earliest eligible acquisition is **November 23, 2026 at 00:00 UTC (03:30 Tehran)**, after verifying no overlap with confirmation and no prior evaluation of those dates or duplicate job/output. Manager owns verifying separation and queue acknowledgment. Architect owns checking and executing the single acquisition. Capture retains sealed-source ownership. The December and 180-day studies retain their own protocols.

The exact wrapper imports the original frozen file under the local name frozen_model.py. If the private checkpoint directory is intact, use its two digest-verified sources. For a replacement workspace, reconstruct the sources from these exact public revisions in a fresh private directory before running the existing command:

```sh
git show 06469335b9342bc9a32459462a7a3a4b15167200:architecture-review/crypto/pilot/hourly_breakout.py > frozen_model.py
git show 7fea8fd8b3fbe5b738d06e0ece74df9c03f43656:architecture-review/crypto/pilot/strategy_panel.py > strategy_panel.py
python strategy_panel.py --mode validation --verified-disjoint --out "$FRESH_PRIVATE_PANEL_VALIDATION_DIR"
```

The wrapper claims the output directory before acquisition. Reconcile any existing attempt instead of repeating it. On success, publish all outcomes including losses. On unavailable or overlapping evidence, publish the blocker for the fixed dates. No automatic wake is assumed.
