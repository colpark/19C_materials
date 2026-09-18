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
