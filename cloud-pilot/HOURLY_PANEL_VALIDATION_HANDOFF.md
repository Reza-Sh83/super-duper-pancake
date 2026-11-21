# November panel validation admission

**PASS, synthetic-only.** Exact probe `f639fa75e71649539794b5fbce3b2e2eb88f6b40` tested wrapper `7fea8fd8b3fbe5b738d06e0ece74df9c03f43656` and frozen model `06469335b9342bc9a32459462a7a3a4b15167200`. The probe injected time and a fake response. One second before the cutoff, missing disjointness attestation, an unapproved retained-source argument and an existing attempt path all refused before requesting data. At the boundary a complete fixture produced 48/48 evaluation hours, 26/26 warm-up and two days for each of 12 cost/account combinations. A missing-hour fixture retained the response, produced no results and refused a same-path retry before a further request. Probe output SHA-256 is `2e93bc3e1bfb85460686406aaba344fe0a72da80eaf2de75d7d2618917f658e5`. External requests and actual validation rows opened: zero.

```sh
PYTHONPATH="$REFERENCE_DIR" python -m tools.check_kraken_panel_admission
```

The source names and extraction commands are in `HOURLY_STRATEGY_PANEL_INDEPENDENT.md`. Architect `bb93758e973411ddd10746d94a0da7761c20b6e3` independently reconciled the real development paths, daily marks and costs. Manager `2e16fbe` retains two separately completed daily SMA runs. Implementer review is in `113b1c1`. Capture `4d1f286` has superseding March Q1 partitions. The previous Q1 slices overlap completed daily research and are retired from that experiment. No reviewed model or adapter binding for the replacement March partitions was found at this checkpoint, and no price data were opened.

**Next action.** Fetch current peer heads, inspect jobs and existing attempt outputs, and reconcile the sole validation executor. The user requested Implementer ownership. Architect's latest receipt still names Architect, and Manager owns resolving the queue and confirming separation from the 180-day dataset. Reconcile any already-started or completed attempt. Once that check passes and the registered cutoff **November 23, 2026 at 00:00 UTC (03:30 Tehran)** arrives, the named executor can run once:

```sh
python "$REFERENCE_DIR/strategy_panel.py" --mode validation --verified-disjoint --out "$FRESH_PRIVATE_PANEL_VALIDATION_DIR"
```

Publish all 12 outcomes and daily rows, including misses, under both costs. Until cutoff and queue separation, keep real validation closed. If the March design is frozen first, Implementer can prepare and test the exact reviewed adapter on synthetic input before any eligible evaluation. The registered December study, 180-day confirmation and all pilot entry gates remain in force.
