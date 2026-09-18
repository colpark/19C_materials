# Simulation of the revision 2 gates

`scripts/simulate_rev2.py` runs synthetic benchmark instances through the original pipeline and revision 2 on the same data, and prices each instance with an oracle (the cohort run replicated 60 times) so that "premature" can be measured against what a run could truly find.

## Setting

Each instance draws: 60 to 400 items, 4 to 40 clusters, floor level 0.55 to 0.90, per-item free variance 0.05 to 0.30, agent variance 1 to 3 times the free variance, a true mechanical lift (zero in 45 percent of instances, else 0.01 to 0.30), a true agent-only lift for channels that score an agent-built input (zero half the time, else 0.05 to 0.30), uptake 0.1 to 1.0, delta 0.08 to 0.25, a ceiling share 0 to 0.5, a noise share 0 to 0.3, and a cell budget of 50 to 200 episodes. Stress sets widen every range to its edge: 12 items, 2 clusters, agents five times noisier than the floor, libraries 90 percent saturated.

Pipelines: the original (I2 reports only, P7 one pass from the free variance, grant ruled as use) and revision 2 (I2 rules CLOSE, LIFT or ADVANCE; P7 two passes with a ten-item pilot enlarged once to twenty, closing only when the 80 percent lower bound of the arm variance still prices the MDE above delta; R8 uptake row; P2 per-item headroom).

## Result, 1000 instances per set

| set | I2 closes (findable lost) | P7 pilot closes (false) | strict premature stops | type I old → new | wasted null runs old → new | findable found old → new (oracle) | claims below true MDE old → new | cells old → new | max transitions |
|---|---|---|---|---|---|---|---|---|---|
| plausible_1 | 295 (0) | 40 (6) | 2 of 87 {'P4_close_supply': 1, 'P7_close_pilot': 1} | 17/354 → 0/354 | 345 → 85 | 84/127 → 62/127 (63.2) | 83 → 9 | 332,385 → 240,705 | 10 of 60 |
| plausible_2 | 283 (0) | 37 (7) | 0 of 84 {} | 13/338 → 0/338 | 328 → 84 | 72/123 → 60/123 (57.4) | 85 → 23 | 341,571 → 249,384 | 10 of 60 |
| plausible_3 | 280 (0) | 26 (4) | 4 of 76 {'P4_close_supply': 2, 'P7_close_pilot': 2} | 17/336 → 0/336 | 327 → 87 | 77/128 → 57/128 (56.8) | 85 → 23 | 342,984 → 256,710 | 10 of 60 |
| stress_11 | 244 (0) | 68 (29) | 4 of 14 {'P4_close_supply': 3, 'P7_close_free': 1} | 2/354 → 0/354 | 229 → 71 | 14/142 → 11/142 (12.1) | 14 → 1 | 86,325 → 51,900 | 10 of 60 |
| stress_12 | 239 (0) | 64 (22) | 2 of 22 {'P4_close_supply': 1, 'P7_close_free': 1} | 6/366 → 1/366 | 239 → 73 | 14/114 → 7/114 (14.0) | 17 → 1 | 82,611 → 50,256 | 10 of 60 |

"Findable" means the oracle finds the effect in at least half of its replications. "Strict premature stops" counts findable effects the revision stopped before scored cells, by stage. P4 supply and P7 free are rules the original already had.

## Reading

- The I2 gate lost no findable effect in 5000 instances. Every I2 closure that carried an effect above delta sat on a saturated or noise-floor library where the oracle's power was at most 0.02.
- The P7 pilot pass stops a findable effect about once per 300 plausible instances and never under stress. Its false closures (oracle MDE at or below delta) run 0.4 to 0.7 percent under plausible settings.
- Revision 2 finds what a correctly priced run can find: 62 against an oracle 63.2, 60 against 57.4, 57 against 56.8. The original's higher counts come from claims made below the true MDE, 83 to 85 per thousand, which revision 2 cuts to 9 to 23.
- Type I claims fall from the nominal 5 percent to zero or one per thousand. Scored runs spent on true nulls fall by three quarters. Cells fall by 27 percent under plausible settings and 40 percent under stress.
- Termination: the static graph carries no cycle after the three new edges, and no run used more than 10 of a 60-transition budget. The one enlargement at R3 is the only added step.

## What the second P7 pass does not catch

Run on the materials instance's own numbers, the provisional pass gives MDE 0.057 over 196 items and 14 clusters, and a pilot of the first ten or twenty scored episodes projects 0.03 to 0.04. Both say RESOLVABLE. The observed MDE of 0.225 came from one chemistry with two noise-floor episodes and a +0.92 cluster mean, a between-cluster component that a pilot with one item per cluster cannot see. The gate that stops that run is I2, which closes both FM channels at instrument cost before any cell.
