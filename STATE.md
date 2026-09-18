# STATE: rev2 redo complete (2026-09-18)

**Rev2 outcome: CLOSURE finding at zero cells.**
- Binding axis: positive supply (14 element systems) under a channel effect that is heterogeneous across chemistries.
- P7 provisional: MDE 0.265 > delta 0.169, and N_min is 35 clusters.
- I2 closes the FM prior and lifts FM-weighted XRD. Neither reaches an unlifted arm.

Run 1 (skill rev1) is kept below and in `REPORT.html` section "Run 1". Its 300 cells are the evidence rev2 was written from.

## Rev2 stage table (restart at D4)

| Stage | Disposition | Artifact |
|---|---|---|
| D1–D3, P3 contamination | carried over unchanged | discovery/, supply/recall_probe |
| D4 amendment | A-04 B_EQE 5→3 from seed S2; A-05 lift and uptake bands; A-06 102 items burned | rev2/discovery/manifest_rev2.json |
| I1 floors at B=3 | PASS: chance 0.468, cls_gp 0.493, cls_xrd 0.561, fm_prior 0.447, fm_xrd 0.566 | rev2/instrument/floors_B3.csv |
| I2 channel lift | fm_prior **CLOSE**; fm_xrd, MEGNet, MACE **LIFT** | rev2/instrument/lift_*.json |
| I4 | MACE, MEGNet: **PROXY**, carried to I2 | rev2/instrument/certification_rev2.json |
| P2 per item | zero-headroom 14% (was 30% at B=5); noise floor 20% | rev2/supply/p2_headroom.json |
| P4 (8 axes) | **CLOSE**, binding positive supply under heterogeneity | rev2/supply/axis_ledger_rev2.json |
| P7 provisional | **CLOSE_UNRESOLVABLE** (MDE 0.265, N_min 35) | rev2/supply/power_provisional.json |
| R3 pilot, P7 final, R5, cells | not run: closed upstream (refusals 18, 19) | – |

**Open for the user (D5, cost of action):** a per-episode budget of 5 would make the lifted comparison resolvable (cohort MDE 0.14), at the price of 30% of items at ceiling. It is not adopted here, because picking a budget to pass a gate is tuning to the gate.
