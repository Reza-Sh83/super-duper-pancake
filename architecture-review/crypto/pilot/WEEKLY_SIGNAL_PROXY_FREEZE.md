# Weekly SMA50 proxy freeze and synthetic receipt

Candidate `bcebdd068e9bf23cb9ca0a2bf712ea6b65ed6887` implements preregistration `c2170cb7164f3a611b7d6697d6435239d4d661df`. The runner uses the original Decimal arithmetic, costs and account rules. A Monday UTC update uses the original delayed 50-close signal and retains its Boolean through Sunday. Daily sizing, reductions and sampled risk locks still apply.

| File | SHA-256 |
| --- | --- |
| weekly_bar_proxy.py | ec229f2ce7c78e23f597eb05b247932659c61e016651a6a657c950c87ccd9ec2 |
| bar_proxy.py | b199c090845c51eb0f0a54a7206b23d89b51a06782f84da25fca4f772c791b30 |

Ran `python architecture-review/crypto/pilot/weekly_bar_proxy.py --test` in the isolated checkout. **15 synthetic tests passed**, including the nine original controls and six follow-up checks. They cover Monday and midweek signal timing, latest eligible close, cutoff and input rejection, midweek sticky-lock exit, hand-calculated base/stress fees and exit reserve, and exact daily/hold/cash equality against the original evaluator at both costs. The first synthetic lock fixture used an overnight drop with insufficient drawdown to trigger the declared stops. The corrected fixture uses an intraday sampled loss that crosses the daily threshold. No strategy rule changed in response to a fixture.

**Evaluation is time-gated.** The fixed UTC window is `[2026-11-23, 2027-01-18)`. The frozen runner refuses acquisition before 2027-01-19 00:00 UTC and requires explicit disjointness attestation. No evaluation rows were acquired or opened. Architect owns one evaluation after that date, only after confirming separation from the 180-day confirmation dataset, checking existing output/job state and applying the shared quota policy. From a clean detached checkout of the exact candidate:

```sh
python architecture-review/crypto/pilot/weekly_bar_proxy.py --test
python architecture-review/crypto/pilot/weekly_bar_proxy.py --verified-disjoint --out "$FRESH_PRIVATE_WEEKLY_RESULT_DIR"
```

Use the second command once, with an absolute private path that does not exist. Supply the attestation only after checking the project ledger. The runner claims that directory before the public data request. Preserve an incomplete output directory as evidence. If the date separation or fixed input fails, publish the blocker and retain the registered dates. Publish all eight exploratory account results and predeclared differences after a valid run. Manager owns queue reconciliation. Production and confirmation criteria remain in force.
