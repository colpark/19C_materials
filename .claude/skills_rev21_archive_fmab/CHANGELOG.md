# CHANGELOG

## Revision 2.1 (2026-09-18): route on closure

Source: the revision 2 redo of the materials instance closed at zero cells and ended with "open for the user". Nothing mapped the binding axis to the moves that could unbind it. Revision 2.1 adds one orchestration stage and the mandate it runs under.

### O1 route on closure
- `references/router.md`: the orchestrator's mandate (what the executing agent decides alone, what it brings to the human), the resource envelope in the programme's own units with a soft ceiling and one tolerance factor per resource, the remedy table keyed by what closed, three loop guards, the portfolio rule for the D4 alternatives, the decision record and card.
- `scripts/router.py`: the table as data with re-entry stage, preconditions and projected cost per move; `route` launches delegated moves that fit the hard limit, cards reserved ones, refuses on guards and preconditions, writes the decision record; `next` starts the highest-ranked active candidate; `card` renders the human's part.
- `scripts/simulate_router.py`: 1000 synthetic closures per set through the router, a stop-and-ask baseline and a naive retry policy. Router: 89 to 90 percent resolved in five to six rounds with 1.2 human decisions, zero preregistration violations, zero hard-limit breaches, zero loop caps. Stop-and-ask: 77 to 78 percent in sixteen rounds with 4.9 decisions. Naive retry: loops in half of all worlds and breached the hard limit 58,000 times on an exhausted envelope. With the human absent the router resolved 75 percent alone and parked the rest on cards.
- Manifest slots: resource envelope and decision rights at D5; the portfolio at D4. Graph: O1's bounded re-entries are the second cycle class. Loop: rung 7 passes through O1. Global refusals 21 to 23. Schemas `decision_record` and `portfolio`; validator checks for both.
- Replay cases K28M (must fire, the materials closure: launch the sibling search and the explain candidate, card the budget) and N16M (must not fire: nothing to launch, card and wait). Suite at 44 cases, 15 sealed.

### The two budgets, stated once
The task's measurement budget (picks per line) is a design parameter priced by cost of action and belongs to the PI. The resource envelope (GPU, storage, tokens, wall clock) is what the orchestrator spends. The envelope buys episodes, precompute and reading; it never buys chemistries, and the router routes a cluster-bound closure to data acquisition and to the explain candidate, not to more cells.


## Revision 2 (2026-09-18): close at the count, not after the cells

Source: the first independent replay of the skill, the materials instance at github.com/colpark/19C_materials. That run measured a zero mechanical lift for both foundation-model channels at I2, recorded PROXY-grade construct validity at I4, and then spent 300 scored cells to return a null the count had already stated. Four repairs, each reusing machinery the skill already had.

### 1. I2 gets a disposition (the culprit)
- `references/stages/instrument.md`: the lift is a number with an interval, read against a band declared at D4. Interval covering zero with its upper bound below delta closes the channel: CLOSE for a channel on a fixed input, LIFT for a channel on an agent-built input. No third option, and no unlifted agent arm runs on a closed channel.
- `scripts/lift.py`: computes the paired interval from the I1 per-item variance and prints the ruling. Dry run on the materials floors: CLOSE for the FM prior, LIFT for FM-weighted XRD, both before the first cell.
- `schemas/lift_record.schema.json`, `validate.py --kind lift_record`.
- I4 now records PASS, FAIL or PROXY. PROXY travels to I2 and needs a lift ruling beside it (`certification_record` schema, validator).
- P3 gains the eighth axis, channel lift. P4 rules provisionally on the seven corpus axes and finally on eight. A provisional ruling licenses I1 and I2 only.
- Graph edges: I2 → P4, I2 → R5. Global refusal 18.

### 2. P7 has two passes
- `references/stages/supply.md`, `references/manifest.md`: the free paired variance is a lower bound. R3 step 2 runs a pilot cohort of at least ten items outside the arm cohort in every arm, `power.py --scope final --provisional <record> --cohort-clusters <csv>` projects the pilot's item-level arm variance onto the cohort's cluster structure, and the final record carries the larger MDE. Rulings: RESOLVABLE, ESCALATE_ENLARGE_PILOT (to twenty, once), RUN_AT_LIMIT, CLOSE_UNRESOLVABLE (only when the 80 percent lower bound of the arm variance still prices the MDE above delta), UNDEMONSTRATED. R5 arms nothing on a provisional record.
- Simulation chose this rule. A five-item pilot closing on its point estimate closed half of all runs, including one in eight real effects. See `references/simulation_rev2.md`.
- Graph edge: R3 → P7 (not a cycle, P7 points forward to A4 on both passes). Global refusal 19. `power_record` schema and validator.

### 3. R8 counts uptake
- `references/stages/runtime.md`: one row per arm, channel uptake in the pilot cohort against a D4 band. Below the band the grant is opt in and the comparison is intention to treat: A1 preregisters it as such, or the run takes the LIFT route.
- `references/shape.md`: fourth Gate 1 lift, required consultation with a written verdict. Global refusal 20.

### 4. P2 counts headroom per item
- `references/stages/supply.md`: items where the floor already takes the ceiling form a zero-headroom stratum carried into P6, never filtered.

### Replay suite
- Four cases suffixed M with sealed rulings: K26M and N14M (I2), K27M and N15M (P7). Suite is now 42 cases, 27 must fire, 15 must not, 14 sealed. `replay.py audit` passes.

### Simulation
- `scripts/simulate_rev2.py`, 1000 instances per set, three plausible seeds and two stress seeds: the I2 gate lost no findable effect; the P7 pilot pass stops about one findable effect per 300 plausible instances; type I claims fall to zero or one per thousand; scored runs on true nulls fall by three quarters; cells fall by 27 to 40 percent; no cycle in the graph and no run past 10 of 60 transitions. Table and reading in `references/simulation_rev2.md`.

### Backward compatibility
- Ledgers without a `scope` field validate as provisional and receive a note, not a failure. Existing axis ledgers keep their seven axes. Existing power records keep their fields.
