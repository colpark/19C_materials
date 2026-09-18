# The loop, and how to leave it

## The stage contract

Every stage prompt carries five things.

1. A cap, in calls and GPU hours.
2. Dispositions with bands, declared before the work.
3. An anti-widening instruction. A low count is reported low.
4. A tuning-set rule naming what may change afterwards and what may not.
5. For any gate, the control that would fire it.

Every stage response carries one disposition and nothing softer. **PASS**, **FAIL**, or **UNDEMONSTRATED**. An interrupted run is undemonstrated, never zero.

The stage's first action is to read every artifact the prompt asserts about and report disagreements before doing the work. Six of the ten recorded planning errors were assertions about artifacts that one read would have settled.

## Rulings

| Ruling | Effect |
|---|---|
| accept | advance to the next stage |
| amend | change the rule, record the cause in the ledger, re-run |
| close | write the finding, end the candidate |
| supersede | re-register a stale freeze, do not pay for it in items |

## What counts as progress

A criterion moved from UNDEMONSTRATED to PASS or FAIL, or a candidate closed. Nothing else.

Not stages run. Not wall-clock time. Not calls spent. A stage that grinds for an hour and settles one criterion is advancing. A stage that returns in a minute with nothing demonstrated is not.

A counter keyed to elapsed stages would measure the convenient quantity rather than the protected one, which is exactly the failure that occurred nine times in the source record. The counter counts criteria moved.

## The escalation ladder

Each rung fires on a different signature. This is not five retries with a delay, and if the rungs are not tied to signatures it degenerates into one.

| Rung | Signature | Wrong move | Exit |
|---|---|---|---|
| 1 | first non-advance | none | the specific repair |
| 2 | blocked on a parameter rather than the threat it protects | retry | ruling, escalate now |
| 3 | same symptom after two distinct repairs | a third repair | reclassify the diagnosis |
| 4 | surface and subject both suspected | another repair | run the known-good control |
| 5 | second failure on the same fixture | another attempt | re-select the fixture from the median of the distribution |
| 6 | declared blocked with no edge in graph.md from the blocker | wait | run now, in parallel |
| 6b | a seed is unreadable or a slot cannot be derived | guess a conventional value | mark the slot UNDEMONSTRATED, name which stages cannot run, escalate |
| 6c | a refusal whose only instruction is to gather more evidence, with the interval not narrowing | keep gathering, or cap the loop at a declared count | derive the stop from the pool. Escape when counting everything left would still not settle it, and record UNDEMONSTRATED with the bound. A counter stops on itself rather than on the threat, and a null under a small count licenses nothing |
| 7 | none of the above | anything automatic | escalate to the human |

Evidence for each rung, all from the source record. Rung 2: six consecutive stages blocked on a parameter, each resolved by a ruling and none by a retry. Rung 3: two schema repairs relocated the same failure twice before anyone concluded it was not a schema problem. Rung 4: eight stages alternating between suspecting surface and subject, settled by one cell with a capable model. Rung 5: eight stages of debugging ran on a diagnostic item with zero usable homologs out of 199. Rung 6: a track was listed as blocked on reachability when it was a script needing no subject model at all.

## Arming the ladder

The ladder is a gate. It arms only with both controls run.

**Must fire.** Six consecutive stages each blocking on a parameter rather than on the threat it protects. The ladder must reach rung 2 and escalate.

**Must not fire.** A thirty-minute sustained envelope passing with a duty cycle of 0.952 and 430 of 430 turns completed. The ladder must stay silent. Without this control the anti-stall mechanism becomes the stall.
