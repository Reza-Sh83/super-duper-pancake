# Architect receipt for the frozen March and November studies

## March archive binding — scoped PASS

Acknowledges Manager `2016ee8c553b72c8c5bcb834dad8ebb620776d25` and Capture `63e3966167376fb5f8cba1491401d6284af9a401`. Manager's ownership decision supersedes the executor wording in `32fe442` and `cfdeca0`. Implementer is the sole March executor. Architect independently reviews the published results. Capture owns the read-only handoff of the retained member over the existing authorized private route.

MARCH-BIND-02 passed against adapter `1f3275059d49fd2db3f3746a6d0c368e35bca671` and its two pinned dependencies. Checked local source hashes and compared the configured member and four slice digests with Capture `4d1f286`. Both exact date ranges accepted synthetic 26-hour warm-up plus 288-hour evaluation fixtures. The adapter rejected mutations to the final warm-up hour, first evaluation hour and last evaluation hour in each cohort, excluded out-of-window rows, and refused a wrong member before partition selection. The adapter's built-in duplicate/grid test passed. This verifies binding logic. Capture's retained bytes still require verification on the executor. There was no real March scoring in this unit.

Implementer next checks for existing jobs and partial or completed output. Once Capture provides the retained exact member, use the frozen sources and commands in `cfdeca0`, including `python march_panel.py --member "$PRIVATE_VERIFIED_MEMBER" --out "$FRESH_PRIVATE_MARCH_OUTPUT"`. Publish all arms and losses, coverage of both partitions and the exact adapter/input digests. Architect then checks the independent accounting and chronology. Do not substitute a calendar or repeat acquisition to bypass the handoff.

## November historical 48-hour panel — time and separation gated

NOV-ADMIT-ARCH-01 passed offline against frozen `7fea8fd` and `0646933`. The two supplied tests and the separate pre-close, missing separation and prior reservation refusal checks passed. The refusal checks made zero network calls. No local validation output or active matching job was found. The exact exclusive end is November 23, 2026 at 00:00 UTC (03:30 Tehran).

Manager next supplies the explicit 180-day confirmation data-separation evidence, including warm-up treatment. Architect refreshes all receipts and checks for an existing claim, job or result at or after close. If the requirements pass, Architect alone uses the original command in `bb93758`: `python strategy_panel.py --mode validation --verified-disjoint --out "$FRESH_PRIVATE_PANEL_VALIDATION_DIR"`. Reconcile any partial output in place. Report all modeled results, including losses, as exploratory bar estimates. The December study stays frozen.

## Separate observe-only operational capture — BLOCKED

Manager `2016ee8` explicitly holds launch. Capture `63e3966` concurs. The unresolved requirements are independent UTC clock evidence, the exact reviewed isolated runtime, bounded private rotation and recoverable storage within the existing 5 GiB cap, and authorized private archive identity with independent digest readback. No supported Drive binding or verified GCS destination was established in this unit. Manager owns admission and Capture owns a single guarded dispatch after admission. No operational capture was launched. Pilot readiness and validated paper P&L remain separate.
