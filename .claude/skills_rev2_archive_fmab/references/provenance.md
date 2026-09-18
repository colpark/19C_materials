# Provenance: the five fields

Every failure in the source record reduces to one omission. A number entered a decision without a record of what it measures. The surrounding process was not weak, which is why the failures survived.

State five fields. No number decides anything until all five resolve.

| Field | Question | Fails when |
|---|---|---|
| referent | what quantity does this claim to measure | it measures something adjacent and available |
| source | which specification or code path produced it, by identifier | it came from an observation, a paper, or memory |
| population | which unit is it computed over, and does that unit bind | the count runs over the abundant unit |
| adjudicator | what is the strongest existing alternative | the gain is priced against the weakest denominator |
| falsifier | what observation would show it is wrong | absent, which is why the error never self-corrects |

Against the ten recorded factual errors: five source failures, three referent, one population, one adjudicator. None carried a falsifier. That field is what makes the other four checkable.

## Worked

| Failure | Field |
|---|---|
| a gate passed on 78 disjoint clusters while 19 carried the binding label | population |
| a watchdog gated on device utilisation and aborted the success signal | referent |
| a thermal threshold was rounded up from one observation of 84.4 | source |
| an endpoint served a checkpoint 81 times smaller than its own baseline | adjudicator |
| a dependency licence was asserted from memory and was wrong | source |
| a tool card documented a confidence cutoff absent from the code | source |
| a frozen prompt was 973 bytes while the runner emitted 2,023 | source |
| a headline was priced against the weakest of three denominators | adjudicator |
| a context gate hashed raw text and claimed semantic stability | referent |
| a receipt that resolved was read as evidence that was relevant | referent |

## Record shape

```json
{"id":"pr-014","value":0.2185,
 "referent":"precision at k over admitted items, instrument composition",
 "source":"scripts/compose.py::rank_ensemble, commit a1b2c3d, revision 08e4846e",
 "population":"146 clustered units, one row per cluster",
 "adjudicator":"classical composition at 0.1753 on the same rows, paired",
 "falsifier":"a label permutation that leaves this unchanged, or a rerun outside the paired interval"}
```

Run `scripts/validate.py provenance`. If a case passes only because the validator caught it, the owning stage has no refusal of its own. Convert it into one.
