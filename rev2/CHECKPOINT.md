# Rev2 redo: reflection and restart checkpoint (2026-09-18)

## What rev2 says the first run did wrong

| Rev2 repair | What happened in run 1 | What rev2 would have done |
|---|---|---|
| **I2 gets a disposition** | Lift of +0.003 (fm_xrd) and −0.004 (fm_prior) was recorded as "both measurements exist", and the stage advanced. 300 cells then confirmed it. | `lift.py`, dry run on the same floors: fm_prior **CLOSE** (CI −0.046 to +0.037); fm_xrd **LIFT** (−0.040 to +0.045). No unlifted arm runs. |
| **I4 PROXY** | MACE/MEGNet construct validity (hull membership, gap ≤ photon energy) was recorded as PASS. | PROXY, which travels to I2. That is where the answer was already written. |
| **P7 two passes** | P7 ran once from the free floor variance: MDE 0.089. Observed was 0.225. | Provisional pass, then an R3 pilot of ≥10 items in every arm, then a final pass before R5 arms. |
| **R8 uptake** | FM tools were granted as optional and called in 19 of 100 episodes. The null could not separate "no signal" from "not consulted". | Uptake band declared at D4. Below it, the run is either intention-to-treat or the LIFT route (required consultation with a written verdict). |
| **P2 per-item headroom** | The aggregate floor of 0.74 passed. Per item, **30% at ceiling** and **20% at the noise floor**, unseen until A3. | Zero-headroom and noise-floor strata carried into P6. |

## Beyond rev2: my own upstream error

The per-episode budget (5 EQE of about 29) was declared at I1 authoring, with no seed source. The manifest even recorded the seeds bracketing it lower: S2 reached its optimum at 19/177 = 11%, and S3 hits a top candidate at about 5%. 5 of 29 is 17%. That unsourced slot is why the GP-UCB floor saturates on 30% of items and leaves an agent little room. The skill's own refusal 15 (a slot sourced by convention or design) should have caught it at D4.

## Restart checkpoint: D4

- **Kept, unchanged by rev2:** D1 census, D2 corpus and exclusion ledger, D3 unit (A-01), the P3 contamination probe, the FM precompute cache, tool cards, and the harness (R1, R2, R4 checks re-run only where the server changes).
- **Re-opened at D4:**
  - (a) Declare the channel-lift band and the uptake band. New slots.
  - (b) Re-derive the per-episode EQE budget from the seeds. Amendment A-04, cause: provenance failure.
  - (c) The item ledger burns the 100 run-1 cohort items and the 3 run-1 pilot items. A scored element (budget, arm design) changes in response to them.
- **Everything downstream re-runs under rev2 gates:** I1 at the new budget → I2 lift rulings → P2 per-item → P4 on 8 axes → P7 provisional → R3 pilot (≥10 items, every arm) → P7 final → R8 uptake → R5 → cells, only if every gate licenses them.

The skill is vendored as rev2 in `.claude/skills/fm-advantage-benchmark`. Rev1 is archived in `.claude/skills_rev1_archive_fmab`.
