# The replay suite

Forty-two cases with their rulings sealed. Twenty-seven must fire, fifteen must not.

Twenty-eight are extracted from a single construction record. Four, suffixed M, are extracted from the first independent replay, the materials instance of 2026-09-17. Four of the ten discovery cases are marked **SYNTHETIC** in their text, because the record contains no instance of a corpus being curated from seeds under these rules. Synthetic cases carry less weight than extracted ones and should be the first replaced when a real instance appears.

The must-not-fire half is not decoration. Without it a stage that flags everything scores full marks, and the escalation ladder becomes the stall it was built to prevent.

## Files

| File | Who may read it |
|---|---|
| `cases/cases.csv` | the stage under test |
| `cases/RULINGS_SEALED.csv` | held out until the stage is finished |

Fourteen cases are marked sealed. Develop on the other twenty-eight. Open the sealed set once, then reseal.

## Running

```bash
python scripts/replay.py audit
python scripts/replay.py emit  --set development --module supply
python scripts/replay.py score --verdicts verdicts.json --set sealed
```

Three numbers per module, and the third is the interesting one. Must-fire rate, must-not-fire rate, and cases that passed through a global refusal rather than the owning stage's own. A validator-only pass means the stage has no refusal of its own, and the case converts into one.

## First executed pass

| Set | Result | Note |
|---|---|---|
| suite shape audit | 1 finding | the escalation ladder had no must-not-fire case |
| development, 19 cases | 19 of 19 | a clean sweep usually means the suite is too easy |
| sealed, 9 cases | 9 of 9 polarity, 2 unearned | two passed through a global refusal, not the stage |
| after repair | 0 unearned | P4 now refuses an incomplete axis ledger, A1 now owns item burning |
| discovery, development 7 | 7 of 7 | five of seven extracted from the record |
| discovery, sealed 3 | 3 of 3 | two extracted, one synthetic |

Read the development sweep with suspicion. The stage briefs and the cases come from one record, so the sweep measures internal consistency and not capability.

## Extending

Two rules. One control per refusal must derive from a real prior failure, because generated controls drift toward the trivial. And add must-not-fire cases at the same rate as refusals, because every new refusal is a new chance to over-fire.

## The limit that matters

The suite and the stages come from one project. Reproducing its rulings says nothing about a case outside it. Replay against an independent corpus that shares no stages before treating any of this as evidence of generality. Until then it is a regression test on known failures.

A procedural seal held by the party that wrote the spec proves nothing. Have someone else hold the rulings file.

## Second replay, an independent corpus

The materials instance (antimonate photoanode library, 14 element systems, 100 paired episodes, three arms) ran all 29 stages to a scored comparison and returned NO CLAIM. Reading the record against the briefs found four places where a stage held the number that decided the outcome and no rule acted on it.

| Stage | What the record held | What the brief did | Repair in revision 2 |
|---|---|---|---|
| I2 | lift +0.003 and −0.004, interval covering zero | advanced on "both measurements exist" | closure clause, `lift.py`, eighth axis, cases K26M and N14M |
| I4 | both cards "none" on the scored quantity, passed on proxies | counted a proxy as a pass | PROXY status, carried to I2 |
| P7 | free MDE 0.089, arm MDE 0.225, delta 0.17 | published the free number as the estimate | two passes, pilot variance at R3, cases K27M and N15M |
| R8 | FM arm called its channel in 19 of 100 episodes | ruled the grant as treatment | uptake row against a D4 band, intention-to-treat route, fourth Gate 1 lift |

The four M cases replay these rulings. They were written by the same party that wrote the repair, so they carry the same limit as the original twenty-eight: internal consistency, not capability. The record itself lives at github.com/colpark/19C_materials.
