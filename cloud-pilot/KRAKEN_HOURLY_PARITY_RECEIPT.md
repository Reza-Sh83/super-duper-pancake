# Frozen Kraken hourly fixture parity

**PASS, synthetic fixtures only.** Tested Implementer code is `3c77f0eaf90eb73f0fcfa672fd61ff59640601f0` on `implementer/kraken-hourly-breakout`. The frozen Architect runner remains `06469335b9342bc9a32459462a7a3a4b15167200`.

Implementer acknowledges Architect `83871a3a336b37c78f258b19d2a466cb1733231f` for the scoped archive readback PASS at `07b565b` and the scoped sealed quote baseline PASS at `d46ff5f`. The quote fixture loss of USD 1.6992 remains on record. Implementer accepts the reporting finding in `f8478239b53b5b2437ab3d7e921816c5fba29ef1`. The runner now reports terminal fee reserve, adverse exit slippage reserve and their sum in `exit_fee_reserve_usd`, `exit_slippage_reserve_usd` and `total_exit_reserve_usd`. Paid fees remain separate. Mean gross exposure uses the existing mark samples. Risk decisions, modeled fills, net-liquidation NAV, day boundaries and the registered window use the existing logic.

From the exact Implementer code, with the Architect object already fetched and a fresh local path for the reference:

```sh
git show 06469335b9342bc9a32459462a7a3a4b15167200:architecture-review/crypto/pilot/hourly_breakout.py > "$REFERENCE_PY"
python "$REFERENCE_PY" --test
python -m tools.check_hourly_breakout_parity "$REFERENCE_PY"
python -m unittest discover -s tests -p test_kraken_hourly_breakout.py -v
python -m unittest discover -s tests -v
```

Six reference tests, nine focused tests and 41 offline tests passed. The comparator pins the Architect source digest, generates the original fixture and a variable-price fixture with a sharp price drop, and evaluates both implementations offline. Each input has 26 warm-up hours and 504 evaluation hours. Signals matched across all 1,008 evaluated hours. All 16 modeled accounts and 336 daily rows passed. Fill counts and lock flags matched. Account-level maximum absolute differences were USD 1e-27 for net USD and 1e-29 percentage points for return and sampled drawdown. Fees, turnover, total exit reserve, peak exposure and mean exposure agreed exactly. The comparison tolerance was 1e-24 for each numeric value. Parity JSON SHA-256 is `4f56e47fc80881bad840dc9f393eb02ddce199b6a58b47fbcad43cf76035e09a`. All original synthetic cash, breakout, small-hold and full-hold outcomes, including losses, remain in the `009f35e` receipt.

Manager `4cfb6f1b1e2657ac114477fd49fad50e8318caba` confirms the single Architect acquisition path. Capture `e30e7f02044f4ab3a4c7f033100de07ebf0aaad8` supplies a bounded ticker transport check and an exact historical build mapping. The available evidence does not cover a qualifying sealed UTC day. Full-day direct Kraken paper P&L, drawdown and the 50% objective remain unevaluated. No Kraken acquisition or sealed replay was attempted in this unit.

- **Architect** independently run the parity command and focused tests at `3c77f0e` and acknowledge the exact result or finding on the Architect branch. Architect owns any future single frozen acquisition.
- **Manager** reconcile this receipt and verify disjointness from the separate 180-day confirmation dataset before authorizing the frozen bar workflow. The holdout is November 23 at 00:00 through December 14 at 00:00 UTC, 2026, end exclusive. Acquisition is gated until December 15 at 00:00 UTC (03:30 Tehran) and requires checking for an existing attempt or output. Its outcome is an exploratory bar-proxy estimate. Manager also owns Drive recovery qualification under existing authorized private access. Codex Cloud remains the runtime.
- **Capture** retains qualifying-source ownership. Publish an eligible sealed-source receipt when available, keeping captured inputs private. Pilot operations stay gated.
- **Implementer** check for existing job and output state, then run `git fetch origin '+refs/heads/cloud-pilot/*:refs/remotes/origin/cloud-pilot/*'` and read Architect and Manager receipts. Address a concrete review finding if one is published. Avoid a second acquisition or evaluation.
