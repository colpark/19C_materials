# Skill findings (defects met while running the skill)

Each entry gives the stage, the input that exposed the defect, and what the brief should have said.

| # | Skill rev | Stage | Input | What the brief should have said |
|---|---|---|---|---|
| F1 | 2.1 | O1 | Decision 003 routed after moves had reported | `router.py` must release commitments on report. **Fixed in 2.2** (`report`, `void`). |
| F2 | 2.1 | O1 | Decision 003 re-launched a search that had succeeded | Satisfied moves are never re-launched. **Fixed in 2.2.** |
| F3 | 2.1 | O1 | Decision record with nothing refused failed validation | Empty `refused` must validate. **Fixed in 2.2.** |
| F4 | 2.3 | O1 (settlement) | A rev 2.1 portfolio whose guard_state has no `launched_history`, `completed` or `guard_delta` | There is no migration path from pre-2.2 router state. The brief should say to replay the decision records through the new router with `report` between them (what this pass did), or ship `router.py migrate`. |
| F5 | 2.3 | O1 (replay) | Replaying decision 002 launched `advance_next_candidate`, which the live decision did not | `spin_explain_candidate` opens a candidate, but the router never sets that candidate `active`; the orchestrator edits the portfolio by hand. The brief should say that opening a candidate is written by the router, so replay order cannot change a decision. |
| F6 | 2.3 | D5 (envelope) | "Spend is measured, never estimated" for `tokens_m` | The orchestrator cannot observe its own token use, and a probe run with `--output-format json` does not retain usage unless the harness saves it. The brief should name the meter per resource, and say unmetered consumers are listed, not estimated. |
| F7 | 2.3 | D5 | A standing approval whose rationale says the change "predates every pooled number" | Pooled mechanical floors (I1/I2/P7 provisional) existed before the ruling; no pooled *arm* outcome did. The brief should define "outcomes seen" as arm outcomes, versus mechanical counts, so the rationale can be checked. |
