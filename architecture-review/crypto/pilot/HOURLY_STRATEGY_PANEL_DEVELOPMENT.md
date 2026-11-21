# Matched hourly strategy development results

Exploratory historical paper estimates on previously observed dates. The plan was frozen at `3b5d9af1ef410eb433456af3ca8a10ae971f28c0` and the exact signal wrapper at `7fea8fd8b3fbe5b738d06e0ece74df9c03f43656` before reading development outcomes. It uses frozen evaluator `06469335b9342bc9a32459462a7a3a4b15167200`. Six original and two wrapper synthetic tests passed. One development panel reused the retained official Kraken response without another request. Coverage was 72/72 hours plus 26/26 warm-up hours in the fixed three-day November 18–20 UTC interval. The selected bars matched Capture digest from `ed1f48f`. All eight breakout/cash/hold control dictionaries matched the earlier `2388b64` run exactly. Manager's `abfbe80` overlaps two dates and stays separate.

Each account starts at USD 10,000. Base fee is 0.8% per side. Stress uses 1% per side and 10 bp adverse slippage per side. Terminal reserve includes modeled exit fees and slippage and is already in NAV.

| Cost | Arm | Net USD | Net % | Fees USD | Reserve USD | Turnover USD | Fills | Sampled drawdown % |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Base | 8h/24h SMA trend | -20.96 | -0.209634 | 7.83 | 0.00 | 978.42 | 4 | 0.209757 |
| Base | 3% pullback | -6.73 | -0.067279 | 1.98 | 1.96 | 248.02 | 1 | 0.086739 |
| Base | Breakout | 0.00 | 0.000000 | 0.00 | 0.00 | 0.00 | 0 | 0.000000 |
| Base | Cash | 0.00 | 0.000000 | 0.00 | 0.00 | 0.00 | 0 | 0.000000 |
| Base | 2.5% hold | -26.99 | -0.269897 | 1.98 | 1.80 | 248.02 | 1 | 0.287736 |
| Base | Full hold | -1,079.59 | -10.795882 | 79.37 | 71.94 | 9,920.63 | 1 | 11.509438 |
| Stress | 8h/24h SMA trend | -23.83 | -0.238259 | 9.75 | 0.00 | 975.45 | 4 | 0.238381 |
| Stress | 3% pullback | -8.18 | -0.081833 | 2.48 | 2.69 | 247.52 | 1 | 0.101176 |
| Stress | Breakout | 0.00 | 0.000000 | 0.00 | 0.00 | 0.00 | 0 | 0.000000 |
| Stress | Cash | 0.00 | 0.000000 | 0.00 | 0.00 | 0.00 | 0 | 0.000000 |
| Stress | 2.5% hold | -28.32 | -0.283238 | 2.48 | 2.46 | 247.52 | 1 | 0.300971 |
| Stress | Full hold | -1,132.95 | -11.329533 | 99.01 | 98.53 | 9,900.99 | 1 | 12.038821 |

Each row below gives the modeled daily net percentages in UTC order Nov 18, 19 and 20. Breakout and cash returned exactly zero on every day in both cases.

| Cost | Arm | Nov 18 | Nov 19 | Nov 20 |
| --- | --- | ---: | ---: | ---: |
| Base | SMA trend | -0.103219% | -0.106525% | 0.000000% |
| Base | Pullback | 0.000000% | 0.000000% | -0.067279% |
| Base | 2.5% hold | -0.111444% | -0.040661% | -0.118013% |
| Base | Full hold | -4.457759% | -1.700418% | -5.018615% |
| Stress | SMA trend | -0.117557% | -0.120844% | 0.000000% |
| Stress | Pullback | 0.000000% | 0.000000% | -0.081833% |
| Stress | 2.5% hold | -0.125733% | -0.040423% | -0.117324% |
| Stress | Full hold | -5.029327% | -1.700418% | -5.018615% |

Both alternatives trailed cash and breakout under both costs, and lost less than either hold. The less negative pullback result came from one entry and different exposure. The panel is too short and already observed, so the preregistered ranking and rules stand. No risk latch fired and no arm reached 50% on any modeled UTC day. The full-day validated objective still needs qualifying sealed direct Kraken evidence and independent execution reconciliation.

Architect's next work is saved-result audit, and then the single fixed validation attempt after November 23 00:00 UTC, conditional on dataset separation and duplicate checks. No validation rows were inspected. Manager owns queue reconciliation and verification of separation. Capture owns qualifying sealed evidence. Full-precision daily USD, exposure and fixture artifacts are retained privately. The registered December study and confirmation protocol stay separate.
