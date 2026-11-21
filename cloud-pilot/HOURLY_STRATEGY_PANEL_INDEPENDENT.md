# Frozen hourly panel independent fixture check

**PASS on synthetic fixtures.** Tested Implementer code `bde2f39053da768669d3db908de202d54b69ec5c`. Architect plan `3b5d9af`, runner `7fea8fd`, evaluator `0646933`. The comparator independently implements both delayed signals and checks their resulting account and daily metrics against the exact frozen source. Every cost/arm matched across the 72-hour development and 48-hour validation-shaped synthetic fixtures. Coverage, selected-row digest, fees, net return denominator and deterministic repeated output matched. The two Architect wrapper tests and 41 offline repository tests passed. Both source digests are pinned. Synthetic output SHA-256 is `68e85831de6470fabbdc7d2ab5ca290bcebdd4b145890f8ce4625edf6b5347f3`.

```sh
git show 06469335b9342bc9a32459462a7a3a4b15167200:architecture-review/crypto/pilot/hourly_breakout.py > "$REFERENCE_DIR/frozen_model.py"
git show 7fea8fd8b3fbe5b738d06e0ece74df9c03f43656:architecture-review/crypto/pilot/strategy_panel.py > "$REFERENCE_DIR/strategy_panel.py"
python "$REFERENCE_DIR/strategy_panel.py" --test
python -m tools.check_kraken_strategy_panel "$REFERENCE_DIR/frozen_model.py" "$REFERENCE_DIR/strategy_panel.py"
python -m unittest discover -s tests -v
```

Acknowledged Architect development receipt `a97c7bef27dece0c876b40ea72b3566669f148ee`. Its retained response covered 72/72 evaluation hours and 26/26 warm-up, with selected-row digest matching Capture `ed1f48f`. These exploratory estimates are the single completed development panel. All six arms, both costs and full daily distributions are in the Architect receipt. Trend net USD was -20.96 base and -23.83 stress, with four fills each. Pullback was -6.73 and -8.18, with one fill each. Both trailed flat cash and breakout and lost less than both hold controls. No modeled day reached 50%. Implementer did not acquire data or repeat the market evaluation.

Next, Manager verifies the validation separation in the project ledger. A single named executor checks peer job/output state and uses the frozen runner once at or after November 23, 2026 at 00:00 UTC (03:30 Tehran). Evaluation rows are disjoint from development. The frozen plan allows preceding development closes as warm-up. Implementer will reconcile the user assignment with Architect's published ownership before any run. The registered December study and 180-day confirmation remain separate. No validation rows were opened. In parallel, Implementer takes the Manager daily SMA receipt review at `2e16fbe`; Q1 archive use requires a distinct frozen design and pinned adapter review.
