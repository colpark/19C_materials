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
**Advances when** the floor's share of the ceiling is stated with its provenance record.
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

Report raw beside clustered with the overstatement percentage. Record unprocessable units as a documented defect and do not repair them here.
**Advances when** all seven axes carry a number.

## P4 rule against declared bands
Bands are declared before the count, not after. Name the binding axis in the ruling or the stage does not exit.
Do not widen a definition to make a count pass. In the record 78 disjoint clusters passed a gate while 19 carried the binding label, and the 19 fell in the declared stop region.
**Refuses to rule at all** when any of the seven axes in P3 is missing a number. In the record a ruling was issued on positive supply while negative supply and contamination exposure sat uncounted, and each would have closed the candidate alone.
**Advances when** PROCEED, CLOSE or ESCALATE is written with the binding axis named and the axis ledger is complete.

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
**Closes the candidate when** MDE exceeds delta. Close here, before any agent runs.
In the record both numbers were computable on day one and neither was computed for fourteen stages.
