# Frozen March Kraken hourly comparison results

**Completed once. Exploratory paper estimates.** Implementer executed under Manager `2016ee8c553b72c8c5bcb834dad8ebb620776d25`, which assigns March to Implementer and the separate November validation to Architect. The result supersedes the March input blocker in Architect `cfdeca0f849cd6d707791a31ddc08edaaa4f8554`. Plan `32fe442132770f6f48385d56cefd9348cc08644a`, production-of-results adapter `1f3275059d49fd2db3f3746a6d0c368e35bca671`, model `06469335b9342bc9a32459462a7a3a4b15167200` and signals `7fea8fd8b3fbe5b738d06e0ece74df9c03f43656` stayed fixed. Independent development input adapter `be456835d8e4f56c807189591a2618784f55e991` passed the 314-row synthetic exact-model integration and all 43 repository unit tests. Architect's frozen March adapter test also passed.

The official Kraken Spot Q1 OHLCVT ZIP was read in seven bounded HTTP ranges totaling 601,161 bytes. Stable archive identity, exact Content-Range, ZIP member CRC and SHA-256 of the 130,559-byte `XBTUSD_60.csv` matched Capture `4d1f286`. An earlier Python range request returned HTTP 403 before recovering an input. The successful range client used the same official source. Both 26-hour warm-ups and both 288-hour evaluation partitions matched all four published canonical digests. Development is March 4–16 UTC and validation is March 20–April 1 UTC, 2026, end exclusive. Each has 12 distinct complete modeled UTC days. The validation design and adapter were fixed before scoring.

```sh
python march_panel.py --test
python march_panel.py --member "$PRIVATE_VERIFIED_MEMBER" --out "$FRESH_PRIVATE_MARCH_OUTPUT"
```

This command completed once. The retained development and validation result hashes are `9e34604d2591c05f32674a19596e4f2dcab46429e39eebb53080d584230f267f` and `3af29ba9791f7472ba7a13c32733a9a3a0d8fed9ece27c2dabe0d0ca9409b3ef`. Do not repeat acquisition or scoring. The read-only audit checked 24 accounts and 288 UTC-day outcomes, coverage and slice identity, net return denominator, paid fees against turnover, cash invariants and modeled threshold counts. It independently reconstructed passive hold NAV, reserve, sampled drawdown and daily marks from hourly opens and closes. Traded-path drawdown was checked against the terminal loss bound. Architect owns independent traded-path review. Full-precision outputs and source prices stay private.

Each account starts at USD 10,000. Base cost is 0.8% per side. Stress is 1% per side plus 10 bp adverse slippage per side. Closing reserve includes fee and slippage and is already reflected in NAV. Exposure shows mean and peak gross marked exposure as percentages of liquidation NAV. Returns and drawdown are sampled bar-model outputs.

| Window | Cost | Arm | Net USD | Net % | Fees USD | Closing reserve USD | Turnover USD | Fills | Drawdown % | Mean / peak exposure % | Days ≥50% |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| development | base | breakout | -10.95 | -0.109477 | 13.88 | 2.02 | 1735.20 | 7 | 0.214287 | 0.9985 / 2.5733 | 0 |
| development | base | cash | 0.00 | 0.000000 | 0.00 | 0.00 | 0.00 | 0 | 0.000000 | 0.0000 / 0.0000 | 0 |
| development | base | hold_small | 12.23 | 0.122294 | 1.98 | 2.11 | 248.02 | 1 | 0.277750 | 2.5373 / 2.6709 | 0 |
| development | base | hold_full | 489.18 | 4.891775 | 79.37 | 84.59 | 9920.63 | 1 | 10.482978 | 100.6898 / 100.8065 | 0 |
| development | base | trend | 3.10 | 0.030991 | 22.01 | 2.04 | 2750.65 | 11 | 0.195895 | 1.2545 / 2.6709 | 0 |
| development | base | pullback | -5.46 | -0.054565 | 3.96 | 0.00 | 494.53 | 2 | 0.059718 | 0.1029 / 2.4811 | 0 |
| development | stress | breakout | -16.86 | -0.168584 | 17.30 | 2.77 | 1729.95 | 7 | 0.257803 | 0.9957 / 2.5660 | 0 |
| development | stress | cash | 0.00 | 0.000000 | 0.00 | 0.00 | 0.00 | 0 | 0.000000 | 0.0000 / 0.0000 | 0 |
| development | stress | hold_small | 10.66 | 0.106607 | 2.48 | 2.90 | 247.52 | 1 | 0.276132 | 2.5301 / 2.6634 | 0 |
| development | stress | hold_full | 426.43 | 4.264275 | 99.01 | 115.86 | 9900.99 | 1 | 10.482978 | 100.9942 / 101.1112 | 0 |
| development | stress | trend | -5.89 | -0.058919 | 27.42 | 2.79 | 2741.75 | 11 | 0.258941 | 1.2509 / 2.6634 | 0 |
| development | stress | pullback | -6.92 | -0.069195 | 4.93 | 0.00 | 493.06 | 2 | 0.074316 | 0.1027 / 2.4741 | 0 |
| validation | base | breakout | -34.88 | -0.348773 | 19.69 | 0.00 | 2461.62 | 10 | 0.348773 | 0.7560 / 2.5061 | 0 |
| validation | base | cash | 0.00 | 0.000000 | 0.00 | 0.00 | 0.00 | 0 | 0.000000 | 0.0000 / 0.0000 | 0 |
| validation | base | hold_small | -9.94 | -0.099395 | 1.98 | 1.94 | 248.02 | 1 | 0.214486 | 2.4375 / 2.5427 | 0 |
| validation | base | hold_full | -397.58 | -3.975812 | 79.37 | 77.44 | 9920.63 | 1 | 8.503320 | 100.6898 / 100.8065 | 0 |
| validation | base | trend | -41.18 | -0.411763 | 33.61 | 1.99 | 4201.60 | 17 | 0.427814 | 1.1027 / 2.5281 | 0 |
| validation | base | pullback | -5.08 | -0.050768 | 3.96 | 0.00 | 494.91 | 2 | 0.079169 | 0.1110 / 2.4811 | 0 |
| validation | stress | breakout | -42.12 | -0.421239 | 24.54 | 0.00 | 2453.60 | 10 | 0.421239 | 0.7539 / 2.4990 | 0 |
| validation | stress | cash | 0.00 | 0.000000 | 0.00 | 0.00 | 0.00 | 0 | 0.000000 | 0.0000 / 0.0000 | 0 |
| validation | stress | hold_small | -11.38 | -0.113757 | 2.48 | 2.65 | 247.52 | 1 | 0.213235 | 2.4306 / 2.5355 | 0 |
| validation | stress | hold_full | -455.03 | -4.550263 | 99.01 | 106.06 | 9900.99 | 1 | 8.503320 | 100.9942 / 101.1112 | 0 |
| validation | stress | trend | -54.33 | -0.543337 | 41.87 | 2.72 | 4187.03 | 17 | 0.559274 | 1.0995 / 2.5209 | 0 |
| validation | stress | pullback | -6.54 | -0.065420 | 4.93 | 0.00 | 493.44 | 2 | 0.093651 | 0.1107 / 2.4741 | 0 |

## Daily net returns in UTC order

Development day 1 is March 4. Validation day 1 is March 20. All values are percent.

| Window | Cost | Arm | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| development | base | breakout | 0.018700 | -0.047198 | 0.000000 | 0.000000 | 0.000000 | -0.064653 | 0.053704 | -0.021112 | 0.000000 | -0.060158 | 0.000000 | 0.011245 |
| development | base | cash | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| development | base | hold_small | 0.116862 | -0.064996 | -0.098935 | -0.030304 | -0.046530 | 0.088973 | 0.054326 | 0.008819 | 0.011532 | 0.015356 | 0.009266 | 0.058471 |
| development | base | hold_full | 4.674462 | -2.486627 | -3.879093 | -1.235182 | -1.919724 | 3.740904 | 2.203749 | 0.350223 | 0.456408 | 0.605023 | 0.362916 | 2.282104 |
| development | base | trend | 0.116862 | -0.002622 | 0.000000 | 0.000000 | -0.036532 | -0.022311 | 0.054614 | -0.051520 | -0.060500 | 0.009534 | 0.000000 | 0.023392 |
| development | base | pullback | 0.000000 | 0.000000 | -0.053840 | -0.000129 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| development | stress | breakout | 0.003632 | -0.046923 | 0.000000 | 0.000000 | 0.000000 | -0.079222 | 0.053390 | -0.020989 | 0.000000 | -0.074754 | 0.000000 | -0.003778 |
| development | stress | cash | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| development | stress | hold_small | 0.101207 | -0.064617 | -0.098358 | -0.030127 | -0.046259 | 0.088453 | 0.054009 | 0.008768 | 0.011465 | 0.015267 | 0.009212 | 0.058130 |
| development | stress | hold_full | 4.048262 | -2.486627 | -3.879093 | -1.235182 | -1.919724 | 3.740904 | 2.203749 | 0.350223 | 0.456408 | 0.605023 | 0.362916 | 2.282104 |
| development | stress | trend | 0.101207 | -0.002606 | 0.000000 | 0.000000 | -0.051269 | -0.037133 | 0.054296 | -0.066168 | -0.075094 | 0.009478 | 0.000000 | 0.008296 |
| development | stress | pullback | 0.000000 | 0.000000 | -0.068474 | -0.000129 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| validation | base | breakout | -0.069289 | 0.000000 | 0.000000 | -0.033862 | -0.013461 | -0.051675 | -0.042833 | 0.000000 | -0.053787 | -0.013710 | -0.070425 | 0.000000 |
| validation | base | cash | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| validation | base | hold_small | -0.018604 | -0.056591 | -0.036998 | 0.106747 | -0.013077 | 0.027946 | -0.088732 | -0.085300 | -0.001364 | -0.013095 | 0.027307 | 0.052678 |
| validation | base | hold_full | -0.744166 | -2.280205 | -1.524648 | 4.465413 | -0.524213 | 1.125992 | -3.536777 | -3.521497 | -0.058318 | -0.560148 | 1.174519 | 2.240090 |
| validation | base | trend | -0.055280 | -0.049140 | 0.000000 | -0.011681 | -0.050845 | -0.025510 | 0.000000 | 0.000000 | -0.037213 | -0.026098 | -0.064350 | -0.092380 |
| validation | base | pullback | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | -0.051189 | 0.000343 | 0.000000 | 0.000000 | 0.000000 |
| validation | stress | breakout | -0.083830 | 0.000000 | 0.000000 | -0.048616 | -0.013383 | -0.066322 | -0.042583 | 0.000000 | -0.068421 | -0.013630 | -0.084960 | 0.000000 |
| validation | stress | cash | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| validation | stress | hold_small | -0.033449 | -0.056261 | -0.036782 | 0.106123 | -0.013001 | 0.027782 | -0.088215 | -0.084802 | -0.001356 | -0.013018 | 0.027147 | 0.052370 |
| validation | stress | hold_full | -1.337950 | -2.280205 | -1.524648 | 4.465413 | -0.524213 | 1.125992 | -3.536777 | -3.521497 | -0.058318 | -0.560148 | 1.174519 | 2.240090 |
| validation | stress | trend | -0.069905 | -0.063802 | 0.000000 | -0.026567 | -0.050548 | -0.040313 | 0.000000 | 0.000000 | -0.051946 | -0.040898 | -0.078921 | -0.121724 |
| validation | stress | pullback | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | 0.000000 | -0.065839 | 0.000341 | 0.000000 | 0.000000 | 0.000000 |

Under stress, development trend and pullback lost USD 5.89 and 6.92, each outperforming breakout's USD 16.86 loss and trailing cash and both holds. Validation trend lost USD 54.33, trailing breakout's USD 42.12 loss. Validation pullback lost USD 6.54, outperforming breakout and both holds and trailing cash. All validation strategy outcomes were negative under both costs. No modeled day reached 50%. This supplies no qualifying sealed full-day paper P&L result and no change to the frozen November, December or 180-day studies.

**Capture remains held.** Manager `2016ee8` owns runtime and storage qualification. Capture `63e3966167376fb5f8cba1491401d6284af9a401` observed zero of three accepted independent clock references and zero of 30 operational-ready seconds in the bounded diagnostic. Local restore and second-writer refusal passed. There is still no reviewed guarded runtime and cap-compliant rotation with independent private archive readback. At the reported all-file rate of 120,096 bytes/s, unrotated 48-hour output is 20,752,588,800 bytes before reserve and existing retention, exceeding 5 GiB. Drive remains the existing proposed archive and no GCS destination is independently verified. No long-run launch or storage transfer occurred.

**Next owner and action.** Architect independently audits the completed March files if an authorized private path is available, then publishes the scoped check or exact missing artifact. Manager reconciles the March receipt and binds prerequisites before any capture launch. Capture alone launches a bound operational collection after checking for an existing attempt. Implementer fetches those receipts and addresses any exact finding without running March again.
