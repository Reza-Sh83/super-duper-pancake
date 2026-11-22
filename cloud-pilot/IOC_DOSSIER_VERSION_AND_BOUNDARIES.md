# Consolidated research dossier and IOC boundary verification

The user’s complete Persian research dossier at commit `ff49de13abcd363ef62d968b879c79b67f97b065` on `research/fa-html` is the primary research reference. The extracted HTML SHA-256 matched `03c014dc26f81b9ead914a0fd813c50d77dae681c32d904e7d10ec00fda27874`. This source pin supersedes the earlier Markdown citations for ongoing research interpretation. The existing crypto decision, build and confirmation contracts remain binding for their engineering and evaluation rules.

| Pinned HTML section | Concrete decision for this work |
| --- | --- |
| [§3.1, rolling chronology and overlap](https://github.com/Reza-Sh83/super-duper-pancake/blob/ff49de13abcd363ef62d968b879c79b67f97b065/RESEARCH.fa.html#section-11) | Admit only frames available by the decision, in recorded receive order. Preserve the first eligible post-latency event and the exclusive expiry cutoff. For later validation, purge by each actual feature-to-label/match interval, with an embargo only as an additional guard. |
| [§6.7, small simulator protocol](https://github.com/Reza-Sh83/super-duper-pancake/blob/ff49de13abcd363ef62d968b879c79b67f97b065/RESEARCH.fa.html#section-32) | Test the exact before/at latency and TTL boundaries, repeat visible depth after a fill, and reconcile cash, BTC and ordered ledger effects on each path. |
| [§13.2, deliverables](https://github.com/Reza-Sh83/super-duper-pancake/blob/ff49de13abcd363ef62d968b879c79b67f97b065/RESEARCH.fa.html#section-66) | Pin code, fixture and oracle identities. Record which numeric effects passed and which data and policy gates remain open. |
| [§19.7, market microstructure and OFI](https://github.com/Reza-Sh83/super-duper-pancake/blob/ff49de13abcd363ef62d968b879c79b67f97b065/RESEARCH.fa.html#section-126) | Retain only causally available displayed book states for OFI, and distinguish eventual forecast or markout from executable net return. No scoring is inferred from the common single-transition and quote-window tests. |
| [§24.1, three forms of backtesting](https://github.com/Reza-Sh83/super-duper-pancake/blob/ff49de13abcd363ef62d968b879c79b67f97b065/RESEARCH.fa.html#section-165), [§24.4, controlled design](https://github.com/Reza-Sh83/super-duper-pancake/blob/ff49de13abcd363ef62d968b879c79b67f97b065/RESEARCH.fa.html#section-168) | Feed the traded and no-intervention books the same accepted updates and require identical displayed state. Only the traded arm debits its executable depth budget. Repeating the unchanged quote supplies no additional fill. This tests mechanical matching, with later market messages fixed. |

Exact tested code `4787671bf3e5758116395230ab72c42d1c00802d`. Four focused and 47 offline tests passed. A valid base frame at 249 ms filled zero. At 250 ms it filled 1.50 BTC and charged USD 1.2004. At exactly 5 s, an otherwise matchable frame yielded a TTL cancellation and preserved USD 10,000 cash and zero inventory. In a separate fixture, a trade consumed 1 BTC and paid USD 0.80. The repeated quote produced zero new fill. The no-intervention book retained its independent capacity, both displayed books matched, and the traded ledger reconciled to USD 9,899.20 cash and 1 BTC.

```sh
git show ff49de13abcd363ef62d968b879c79b67f97b065:RESEARCH.fa.html | sha256sum
python -m unittest discover -s tests -p test_ioc_ledger_replay.py -v
python -m unittest discover -s tests -v
```

Focused log SHA-256 `48c244c936e2765a810a392a3eb6a632b1ab3933e83ffb5dca13404ceea74983`. Offline log SHA-256 `bc951d80ab8164cf37ded825502972e8e1d5312849179375a5cf3954aed97440`.

**Next owners.** Architect reconciles the OFI aggregation and decision policy described in `48c2901`, then Manager acknowledges the exact winning contract in the queue. Implementer adds the isolated policy only after the reconciled freeze. The checks here are synthetic. Recorded scoring still requires clock-qualified sealed data. The 180-day protocol, candle controls and launch gates retain their existing scope.
