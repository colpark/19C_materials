# Schemas

Every artifact is a record, not prose. Reports read current values from these ledgers rather than restating them, so drift becomes impossible rather than detectable.

| File | Written by |
|---|---|
| provenance_record.schema.json | every stage, for any number that decides something |
| domain_manifest.schema.json | a human, plus the derived block |
| axis_ledger.schema.json | P3 and P4 |
| power_record.schema.json | P5 and P7 |
| tool_card.schema.json | I3 |
| certification_record.schema.json | I4 and I5 |
| gate_register.schema.json | R5, R6 and R7 |
| grant_record.schema.json | R4 and R8 |
| score_record.schema.json | A1 through A4 |

Every ledger carries `completeness`, an assertion over the manifest naming what was covered and what was not. A ledger without it blocks the stage, because a stage that declines to rule otherwise scores the same as one that rules correctly.


## lift_record (added, revision 2)

Written by I2, one per channel. Carries the paired lift of the composition at C channels over C-1, its 95% interval from the I1 per-item variance, the manifest delta, the channel's role (fixed_input or agent_input) and the ruling ADVANCE, CLOSE or LIFT. `scripts/lift.py` writes it. `validate.py --kind lift_record` checks that a channel whose interval covers zero below delta did not ADVANCE, and that LIFT was recorded only for an agent_input channel.

Two records gained a `scope` field in the same revision: `axis_ledger` (final requires the channel_lift axis) and `power_record` (final requires pilot arm variance and carries the larger MDE). Records without `scope` validate as provisional.
