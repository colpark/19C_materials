# Orchestration: O1 route on closure

The stages decide whether a candidate lives. This module decides what happens when one dies, and it is the only place in the skill that reads across modules.

## The orchestrator

The executing agent is the orchestrator. It holds a written mandate, the `decision_rights` slot in the manifest, and it acts inside a written resource envelope. It reads ledgers and rulings only. It never reads labels, traces or design rationale, so the adjudication module's blindness survives it. Everything it decides is an amendment with the five provenance fields, and every decision leaves a decision record.

What it may decide alone: which stage runs next, which autonomous remedy to launch on a closure, whether to run candidates in parallel, when to enlarge a pilot or a cohort inside the envelope, which checkpoint to precompute, which sibling libraries to read, when to open an alternative candidate from the D4 shape record.

What it must bring to the human: the per-item measurement budget and anything else priced by cost of action, a change to delta, the unit, the scored quantity or the arm design after outcomes were seen, acceptance of a proxy grader, new experiments or data from collaborators, spend beyond the envelope's hard limit, and the ladder's rung 7.

That split is the whole of the mandate. A decision that changes what counts as evidence after evidence exists is never delegated, however cheap. A decision that only spends compute, reads more, or starts a candidate already listed as an alternative is delegated, however expensive, up to the hard limit.

## The resource envelope

Declared at D5 beside the budget slot, in the units the programme actually meters.

| Resource | Ceiling | What it bounds |
|---|---|---|
| gpu_hours | soft | precompute, floors, ablations |
| storage_gb | soft | caches, traces, corpora |
| tokens_m | soft | agent cells, reading, cards |
| wall_hours | soft | the calendar |
| tolerance | one factor, default 3 | hard limit = ceiling × tolerance, per resource |

A move is launched autonomously only when its projected cumulative spend stays under the hard limit on every resource. Above the soft ceiling and under the hard limit it launches and is flagged. Above the hard limit it goes to the human with the projection. Spent and committed are carried per resource; a launched move commits its cost until it reports.

The envelope buys episodes, precompute and reading. It does not buy chemistries, and the router knows the difference: a closure bound by cluster supply routes to data acquisition and to the explain candidate, never to more cells.

## The remedy table

Keyed by what closed. Supply closures split on the variance decomposition P7 already computes: when the between-cluster share is at least 0.3, or N_min in clusters exceeds the clusters on hand, the closure is cluster bound; otherwise it is item bound and more episodes per cluster help.

| Closure | Autonomous, in order | Reserved to the human |
|---|---|---|
| I2 CLOSE, channel dead on a fixed input | swap the checkpoint or family and re-run I2; move the channel to scorer on agent-built inputs with a lift, before A1; advance the next candidate | a task whose scored quantity the FM measures |
| I4 FAIL | swap the checkpoint; advance the next candidate | a different scored quantity; accept a disclosed proxy |
| supply, cluster bound (P4, P7 provisional, A4 at limit) | search sibling libraries and read them whole; pool them under a fresh tau; open the explain candidate on the per-cluster effect, graded by the ablation floors at zero cells; advance the next candidate | new libraries or experiments; the per-item budget |
| supply, item bound (P7) | buy episodes per cluster from unburned supply and re-run the final pass; forced-consultation lift before A1; advance the next candidate | the per-item budget |
| P2, floor at the ceiling | advance the next candidate | the per-item budget |
| P3, contamination | filter by the exposure key and recount; advance the next candidate | later data |
| R-stage stall | the ladder, then advance the next candidate | rung 7 |

`scripts/router.py` holds the same table as data with each move's re-entry stage, preconditions and cost, and it is the copy that runs.

## Guards

Three, and they are what make the router's re-entries bounded rather than a second stall.

- Depth: at most three remedies chained on one candidate. The fourth closure closes it.
- Re-entry: a stage is re-entered at most twice for the same candidate.
- Retirement: a move that failed twice for a candidate is never offered for it again.

And one refusal above all three: no autonomous move changes a preregistered element after outcomes were seen. The table marks those moves, and after A1 they are carded, never launched.

## The portfolio

At D4 the shape record's alternatives stop being commentary. Each becomes a candidate with a status, a resolving power (yield over the MDE that yield implies) and a cost class. The lead runs first. When it closes, `router.py next` starts the highest-ranked active candidate without waiting for a card to be answered. With compute to spare, candidates whose stages share no edge in `graph.md` run in parallel. The survivor target S caps the portfolio.

## The decision record and the card

Every routing writes one JSON record: the closure, its key, the moves launched with their projections, the moves carded with the reason they are the human's, the moves refused with the guard or precondition that refused them, the guard state, the envelope after commitment, and the amendments. `router.py card` renders the human's part as a short card: running now, your decisions, not taken. The card never blocks: the record is complete before the human reads it.

## What the simulation showed

`scripts/simulate_router.py` drives synthetic closures through the router, a stop-and-ask baseline, and a naive retry policy on identical worlds with a slow human who says no half the time. Over 1000 worlds per set the router resolved 89 to 90 percent of closures in five to six rounds with 1.2 human decisions each, against 77 to 78 percent in sixteen rounds with 4.9 decisions for stop-and-ask. It launched no move that changed a preregistered element after outcomes, breached no hard limit, and hit no loop cap. With the human absent it still resolved 75 percent and left the rest waiting on a card rather than spinning. With the envelope exhausted it launched 0.09 moves per world and carded the rest, where naive retry breached the hard limit 58,000 times. Naive retry looped past the round cap in about half of all worlds.

## What it is not

A router with a remedy table is not judgment. It is the part of judgment that can be written down before the closure happens, so that the part that cannot reaches the human with the options already priced and the cheap ones already running.
