# Historical exploratory SMA50 comparison

Manager owned both evaluations and reused the retained official Kraken Spot XBT/USD daily OHLC response. There was no acquisition in either experiment. Both windows were fixed before scoring. A covers September 1 to October 27, 2025 UTC. B covers January 5 to March 2, 2026 UTC. End dates are exclusive. Each passed 56/56 complete evaluation days and 51/51 preceding warm-up rows. These windows come from older development-era input and precede the earlier June–November daily evaluation, its warm-up, and all registered future windows. This is retrospective research with fixed rules and no parameter tuning or selection between windows.

Base costs are 0.8% per side and stress costs are 1% per side plus 10 bp adverse slippage. Start at $10,000. Daily and Monday-weekly delayed SMA50, staged hold and cash share the frozen accounting in `bcebdd068e9bf23cb9ca0a2bf712ea6b65ed6887`. Modeled open fills, sampled daily locks and liquidation marks apply. Only a passive recorder for pretrade-open-to-close returns was added. Paid fees and closing exit reserves are separate. The daily distributions cover complete UTC bars under the model. A bar model cannot establish exchange execution, intraday drawdown or validated paper results.

## HIST-SMA-A

| Costs | Arm | Net USD | Net % | Sampled drawdown % | Fees USD | Exit reserve USD | Fills | Daily min % | Daily median % | Daily max % | Up | Down | Flat | Days ≥50% |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| base | sma50 | -151.581929 | -1.515819 | 1.515819 | 40.330634 | 0.000000 | 28 | -0.705321 | 0.000000 | 0.150952 | 9 | 15 | 32 | 0 |
| base | weekly | -129.429170 | -1.294292 | 1.674284 | 33.437018 | 0.000000 | 24 | -0.705321 | 0.000000 | 0.383633 | 9 | 12 | 35 | 0 |
| base | hold | 26.949080 | 0.269491 | 1.444688 | 8.611170 | 7.363309 | 16 | -0.687815 | 0.004201 | 0.387908 | 30 | 26 | 0 | 0 |
| base | cash | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | 0.000000 | 0.000000 | 0.000000 | 0 | 0 | 56 | 0 |
| stress | sma50 | -166.033222 | -1.660332 | 1.660332 | 50.223577 | 0.000000 | 29 | -0.701810 | 0.000000 | 0.148599 | 9 | 15 | 32 | 0 |
| stress | weekly | -141.408586 | -1.414086 | 1.791355 | 41.635801 | 0.000000 | 24 | -0.701810 | 0.000000 | 0.380272 | 9 | 12 | 35 | 0 |
| stress | hold | 20.894210 | 0.208942 | 1.436045 | 10.734896 | 10.078648 | 16 | -0.683690 | 0.004176 | 0.385582 | 30 | 26 | 0 | 0 |
| stress | cash | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | 0.000000 | 0.000000 | 0.000000 | 0 | 0 | 56 | 0 |

## HIST-SMA-B

| Costs | Arm | Net USD | Net % | Sampled drawdown % | Fees USD | Exit reserve USD | Fills | Daily min % | Daily median % | Daily max % | Up | Down | Flat | Days ≥50% |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| base | sma50 | -49.586848 | -0.495868 | 0.913619 | 17.241380 | 0.000000 | 20 | -0.452157 | 0.000000 | 0.449711 | 6 | 11 | 39 | 0 |
| base | weekly | -80.414802 | -0.804148 | 1.103589 | 17.059300 | 0.000000 | 25 | -0.452157 | 0.000000 | 0.449711 | 8 | 13 | 35 | 0 |
| base | hold | -316.655411 | -3.166554 | 3.459542 | 13.662353 | 0.000000 | 9 | -1.056226 | 0.000000 | 0.449711 | 12 | 20 | 24 | 0 |
| base | cash | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | 0.000000 | 0.000000 | 0.000000 | 0 | 0 | 56 | 0 |
| stress | sma50 | -55.856899 | -0.558569 | 0.913084 | 21.475404 | 0.000000 | 18 | -0.450072 | 0.000000 | 0.447020 | 6 | 11 | 39 | 0 |
| stress | weekly | -86.505967 | -0.865060 | 1.102165 | 21.248939 | 0.000000 | 23 | -0.450072 | 0.000000 | 0.447020 | 8 | 13 | 35 | 0 |
| stress | hold | -320.629244 | -3.206292 | 3.438846 | 17.020307 | 0.000000 | 9 | -1.049751 | 0.000000 | 0.447020 | 12 | 20 | 24 | 0 |
| stress | cash | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0 | 0.000000 | 0.000000 | 0.000000 | 0 | 0 | 56 | 0 |

Both SMA rules lost money and trailed cash in both windows. Weekly lost less in A and daily lost less in B. Hold beat the rules in A and trailed them in B. No modeled day crossed 50%. No strategy is selected for validation from these outcomes.

## Review and resume

Implementer owns read-only independent review of this receipt and the wrapper. Check coverage, the initial NAV denominator, fee/exit treatment, fill counts, daily distribution and close sampling. Reconcile against retained results only if the approved private evidence is accessible. No fresh acquisition or repeat evaluation is needed for the review.

For provenance and interrupted-run resumption only, on the original authorized executor check the single experiment output directory first. A completed or partial output must be reconciled before any further dispatch. The runner requires the exact two source modules, retained Kraken response and full digest from the existing private receipt.

```sh
git show bcebdd068e9bf23cb9ca0a2bf712ea6b65ed6887:architecture-review/crypto/pilot/bar_proxy.py > "$PRIVATE_RUN_DIR/bar_proxy.py"
git show bcebdd068e9bf23cb9ca0a2bf712ea6b65ed6887:architecture-review/crypto/pilot/weekly_bar_proxy.py > "$PRIVATE_RUN_DIR/weekly_bar_proxy.py"
cp cloud-pilot/research/historical_sma_comparison.py "$PRIVATE_RUN_DIR/run.py"
python "$PRIVATE_RUN_DIR/run.py" "$ABSENT_EXPERIMENT_ID" "$RETAINED_RESPONSE" "$ORIGINAL_SHA256"
```

Both A and B completed on the original executor. No new request was made, no independent review of the two new results is claimed, and no further Manager experiment is active. Private bytes and all per-day rows remain retained privately.
