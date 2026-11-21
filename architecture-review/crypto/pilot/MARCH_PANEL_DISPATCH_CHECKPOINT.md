# March and 48-hour dispatch checkpoint

## March

Frozen plan `32fe442132770f6f48385d56cefd9348cc08644a` and tested adapter `1f3275059d49fd2db3f3746a6d0c368e35bca671` bind exact Capture receipt `4d1f286a0880fdf44afbcc9fa648701a5ee7e6e1`. Adapter SHA-256 is `aaa48bcbcbda6303577c3c91666adec6b8a85c9da39c59e51c849b748d11a4c3`. The synthetic test passed for final closed bar retention, digest mismatch rejection, duplicate-hour rejection and six-arm output. It used the hashed frozen evaluator and signal sources listed in the plan.

**BLOCKED_INPUT before scoring.** A bounded request for the public Kraken ZIP member returned HTTP 403 at the first range. No archive member was recovered. No matching prepared member was visible in the shared workspace or through an exposed authorized storage tool. No March prices or results were opened and no March result directory was created.

Capture owns one read-only handoff of the already verified member through an existing authorized private location. The plan carries its expected member digest and all four slice digests. Implementer owns independent review of the exact adapter and synthetic gate. Architect is the single scorer and will reconcile Implementer's review. From a private directory containing the three exact sources, after checking existing jobs and absence of prior output, run:

```sh
# Materialize these names from the exact public commits if the private checkout is unavailable.
git show 06469335b9342bc9a32459462a7a3a4b15167200:architecture-review/crypto/pilot/hourly_breakout.py > frozen_model.py
git show 7fea8fd8b3fbe5b738d06e0ece74df9c03f43656:architecture-review/crypto/pilot/strategy_panel.py > frozen_panel.py
git show 1f3275059d49fd2db3f3746a6d0c368e35bca671:architecture-review/crypto/pilot/march_panel.py > march_panel.py
python march_panel.py --test
python march_panel.py --member "$PRIVATE_VERIFIED_MEMBER" --out "$FRESH_PRIVATE_MARCH_OUTPUT"
```

The code verifies the member and partition identities before any scoring. Preserve both complete result files privately and publish all outcomes including losses. In a checkout with the private sources already intact, use the final two commands. Do not substitute a new window or an unmatched file.

## Separate November and operational attempts

The November validation period has not closed. The earliest eligible acquisition remains **November 23, 2026 at 00:00 UTC (03:30 Tehran)**. Latest user direction assigns Architect the single run. Manager should reconcile ownership with the conditional Implementer handoff `d6f419f` and verify confirmation separation. Architect checks peer receipts and existing output before using the exact `bb93758` command. No November validation rows were opened and no duplicate was dispatched.

**48-hour data and operational capture BLOCKED at prerequisites.** The current receipts still lack verified independent UTC clock, a compatible reviewed runtime and a bounded persistence/rotation path within the cap. Existing short-run evidence cannot establish a 48-hour storage bound. The visible tool surface supplies no independently verified authorized Drive or GCS access for this path. Capture owns collection after Manager binds a qualifying runtime and storage plan. Codex Cloud is the runtime and Drive is the proposed archive. There is no GCS destination verified here. No long-run job or output was created. This gate is separate from historical scoring. The December study and 180-day confirmation retain their existing rules.
