# supply — P1 to P7

**Private evidence:** the corpus and the similarity measure. Never reads implementation code, traces or labels.
**Sole writer of:** candidate queue, prior floor record, axis ledger, strata record, power record.
**Cost:** zero model calls at every stage.

---

## P1 read sources, list queue
Read each source completely. A first pass on summaries produced three wrong conventions and one wrong headline in the record, and a full read forced five corrections. Enumerate candidates from documents already held before searching for more.
**Advances when** every candidate traces to a source read in full, with a locator.

## P2 prior floor estimate
From evidence already held, state what share of the achievable signal a mechanical composition already captures. In the record a structure predictor with no sequence model reached 92 percent of the best combined result, which reframed the whole project.
State headroom per item as well as in aggregate. Items where the floor already reaches the ceiling form a zero-headroom stratum, carried into P6 like measured depth and never filtered. A floor that passes in aggregate and takes the ceiling on a third of the items carries a third less resolving power than the aggregate says. In the materials instance the floor sat at 0.74 of ceiling and passed, while 34 percent of items sat at 1.0 and 20 percent at the noise floor, and nobody saw it before A3.
**Advances when** the floor's share of the ceiling is stated with its provenance record, in aggregate and per item.
**Closes the candidate when** the floor already takes the ceiling.

## P3 count every axis, one pass
Cluster by the manifest measure, then count. Never count rows.

| Axis | Typical failure |
|---|---|
| positive supply | counted at the abundant unit |
| negative supply | assumed abundant, never counted |
| contamination exposure by the exposure key | all units predate all subjects |
| tool coverage | one channel structurally unavailable |
| cluster structure, raw beside clustered | raw reported as effective n |
| split integrity, split key against the cut | a near-duplicate straddles the split |
| unprocessable units | silently repaired or silently dropped |
| channel lift, from I2 | reported as a sentence rather than an interval, and the run proceeds to cells to confirm a null the count already stated |

Report raw beside clustered with the overstatement percentage. Record unprocessable units as a documented defect and do not repair them here.

Seven axes come from the corpus and are counted here at zero cost. The eighth, channel lift, comes from I2 and stays UNDEMONSTRATED until I2 reports. P4 rules provisionally on the seven so that I1 can build, and finally on all eight.
**Advances when** all seven corpus axes carry a number, and the eighth carries a number or UNDEMONSTRATED.

## P4 rule against declared bands
Bands are declared before the count, not after. Name the binding axis in the ruling or the stage does not exit.
Do not widen a definition to make a count pass. In the record 78 disjoint clusters passed a gate while 19 carried the binding label, and the 19 fell in the declared stop region.
**Refuses to rule at all** when any of the seven corpus axes in P3 is missing a number. In the record a ruling was issued on positive supply while negative supply and contamination exposure sat uncounted, and each would have closed the candidate alone.
**Refuses a final ruling** while channel lift sits UNDEMONSTRATED. A provisional ruling licenses I1 and I2. Only a final ruling licenses an arm, and a channel closed at I2 reaches an arm only under a recorded lift.
**Advances when** PROCEED, CLOSE or ESCALATE is written with the binding axis named and its scope, provisional or final, recorded. No arm runs on a provisional ruling.

## P5 derive queue from yield
Re-derive Q from the observed free-tier pass rate using `scripts/queue.py`. Record the interval width.
**Returns to P1** when the survivor count is below S and supply remains.
**Escapes** when the survivor count reaches S, or when the optimistic bound on remaining supply falls below S.
**Refuses** to derive a queue from a batch whose interval is wider than the estimate.
**Sizes the next batch rather than capping the loop.** The queue is not a declared number. Take the batch `queue.py` sizes from the observed rate, count it, re-derive. Enumeration runs long where the answer is genuinely in doubt and stops early where it is not.
**Escapes to UNDEMONSTRATED** when the projected count to settle would consume the pool. `queue.py` prints how many more counts settle it and by which route, and that number is weighed against the budget rather than against a cap. What is recorded is a bound on yield, never a zero, reported as `s of n, upper 95% h`. A null reached under a small queue licenses nothing, since zero of twenty excludes almost no yield at all, so never report a survivor count without the count behind it and its bound.

## P6 per-item separation, strata
Requires I1. Compute the chance baseline and the per-item difference between the two compositions.
**Stratify, never filter.** Filtering items where the compositions do not separate selects on the outcome variable and rebuilds the circularity the record closed a candidate over. Report per stratum and keep every item.
**Advances when** strata are defined and no item has been removed on its outcome.

## P7 resolution, MDE and N_min
Requires I1. Run `scripts/power.py`. Publish sigma_d, MDE at the available cohort, and N_min at the manifest delta.

Two passes, and the record is not final after the first.

| Pass | Variance source | Scope | Licenses |
|---|---|---|---|
| first | the free paired difference between the I1 compositions | provisional, a lower bound on arm variance | I2 to R4 |
| second | the item-level arm differences in the R3 pilot cohort, projected onto the arm cohort's cluster structure by `power.py --scope final` | final, the larger of the two MDEs | R5 and every scored cell |

The free variance is the variance of two fixed compositions. Agents add their own within-item noise, and the pilot prices it: `var_cluster = var_between(free) + var_item(pilot) × mean(1/m_c)` over the cohort's clusters, so a small cluster in the cohort is priced as small. The second pass rules on that point estimate and on the 80% lower bound of the pilot variance, in this order.

| Second-pass ruling | Condition | Licenses |
|---|---|---|
| RESOLVABLE | point MDE at or below delta | R5 and every scored cell |
| ESCALATE_ENLARGE_PILOT | point MDE above delta on a pilot below 20 items | enlarge the pilot to 20 and re-run once, never twice |
| RUN_AT_LIMIT | pilot at 20, point MDE above delta, lower bound at or below it | the run, reported at its resolution limit; claims still need effect above the point MDE |
| CLOSE_UNRESOLVABLE | the lower bound itself sits above delta | nothing |
| UNDEMONSTRATED | pilot below 10 items | nothing; scope stays provisional |

A pilot of about one item per cluster cannot separate between-cluster heterogeneity of the agent effect from noise, so the second pass does not price it. A4 reports the observed MDE for that reason, and in the materials instance that is where the 0.225 against a free 0.089 came from: one chemistry, two noise-floor episodes, a +0.92 cluster mean. The gate that would have stopped that run is I2, not this one.
**Closes the candidate when** the provisional MDE exceeds delta, or the final lower bound does. Close here, before any agent runs, or at R3, before any scored cell.
In the record both numbers were computable on day one and neither was computed for fourteen stages.
