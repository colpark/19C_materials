# Decisions needed (end of the rev 2.3 autonomous pass, 2026-09-19)

The run is **not halted** (halt_on: none). The pass ended in a terminal state: A4 was written, and the portfolio has no active candidate.

## A4 result
- **NO CLAIM.** fm_forced − classical = +0.062 at the cluster level, 95% CI [+0.002, +0.121].
- The interval excludes 0, but the effect is below the final MDE of 0.163 and the observed MDE of 0.084.

## Your decisions (deferred by your standing rulings until A4, now due)

1. **request_new_libraries** (card from decision 005). This is the only move that adds independent clusters.
   - Rev 2.3 used 26 tau-0.5 clusters, and all public JCAP/MEAD PEC+XRD libraries found by the search are already pooled.
   - Reaching the effect size seen here (0.06) at 80% power needs roughly 150–200 clusters by the observed cluster SD (0.15). Alternatively, relax the claim rule to the observed MDE.
2. **different_scored_quantity** (deferred until A4). It is surfaced by hand: the router's A4 table omits it (SKILL_FINDINGS F10).
   - Both FM channels stay PROXY for EQE and photocurrent.
   - A task scored on a quantity MACE or MEGNet measures (phase stability, identity or band gap) would give the FM channel construct validity. That is a change of scientific question.

## Denied by your standing rulings (not re-asked)
change_task_budget (B_EQE stays 3), accept_proxy_grader, later_data.
