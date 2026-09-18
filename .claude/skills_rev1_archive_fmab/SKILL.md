---
name: fm-advantage-benchmark
description: Build and run a controlled benchmark that isolates whether an agent holding domain foundation-model tools makes measurably better decisions than the same agent with only classical tools, and than a fixed mechanical composition of those tools with no agent at all. Use this whenever the user wants to construct a scientific task set, dataset, eval or benchmark for agents; wants to know whether a foundation model, simulator or predictor actually helps; asks about ablation arms, mechanical floors, kill gates, contamination, cohort sizing, statistical power for an eval, tool certification or construct validity; or is about to spend engineering effort on a task set before checking whether that task set can resolve anything. Use it even when the request sounds like ordinary dataset construction or benchmark design, because the expensive failures in this work happen during construction and are invisible afterwards.
---

# FM-advantage benchmark construction

## What this returns

Given a domain manifest and a corpus, answer one question.

> Does an agent granted domain foundation-model tools produce measurably better decisions than the same agent granted only classical tools, and than a fixed mechanical composition of the same tools with no agent in the loop?

Return one of two artifacts. Both count as success.

1. **A closure finding.** The axis that fails, the count that fails it, the condition it violates.
2. **A runnable benchmark and a scored comparison**, carrying its own resolution limit.

Closure is the primary product by volume. In the record this derives from, four of six candidates closed on counting alone at zero compute.

## Load first, every time

`references/provenance.md` holds the five fields that govern every number. `references/manifest.md` describes the manifest, which the discovery module derives from your seeds rather than asking you to supply. `references/loop.md` holds the stage contract and the escape rules. Load all three before stage R1.

`references/shape.md` holds the four task roots and the three gates that rule among them. Load it at D4, before `k`.

`references/graph.md` holds the cross-module preconditions. Consult it before starting any stage.

## The 29 stages

Five modules, partitioned by private evidence. Ordered here by execution, which is cost order and not module order.

| # | Stage | Module | Cost | Advances when |
|---|---|---|---|---|
| 1 | D1 read each seed in full | discovery | reading | every seed read whole, every fact located |
| 2 | D2 assemble the corpus | discovery | hours | corpus, frozen rules and exclusion ledger published |
| 3 | D3 measure tau from the corpus | discovery | hours | the cut curve is published and the cut justified from it |
| 4 | D4 derive the remaining slots | discovery | hours | every slot carries a value and five provenance fields |
| 5 | D5 ratification | discovery | your time | every slot ratified or overridden, manifest frozen |
| 6 | R1 harness control | runtime | one cell | a known-good subject completes on a synthetic item |
| 7 | P1 read sources, list queue | supply | low | every candidate read from source, not summary |
| 8 | P2 prior floor estimate | supply | zero | floor share of ceiling stated |
| 9 | P3 count every axis, one pass | supply | zero | all seven axes carry a number |
| 10 | P4 rule against declared bands | supply | zero | PROCEED, CLOSE or ESCALATE, binding axis named |
| 11 | P5 derive queue from yield | supply | zero | Q re-derived, interval width recorded |
| 12 | I1 build compositions blinded | instrument | afternoon | both published and hashed before any arm |
| 13 | I2 measure channel count | instrument | afternoon | C-1 and C both measured |
| 14 | P6 per-item separation, strata | supply | zero | strata defined, no item filtered on outcome |
| 15 | P7 resolution, MDE and N_min | supply | zero | sigma_d, MDE, N_min published |
| 16 | I3 tool cards from code | instrument | days | disagreements listed, not reconciled |
| 17 | I4 construct validity first | instrument | days | each tool measures the scored quantity, or does not |
| 18 | I5 functional certification | instrument | weeks | CERTIFIED, BLOCKED or SUBSTITUTED, never ready |
| 19 | R2 isolating probe, one tool | runtime | minutes | one real call, value read back, forged id rejected |
| 20 | R3 load ladder, declared steps | runtime | hours | each step reports before the next is added |
| 21 | R4 verify grant, model side | runtime | one cell | the catalog the model received, with canaries |
| 22 | R5 author gates, both controls | runtime | zero | armed or refused, per gate |
| 23 | R6 hash what the runner emits | runtime | per cell | emitted hash recorded beside declared |
| 24 | R7 classify cosmetic or not | runtime | per cell | difference classified before any action |
| 25 | R8 arm symmetry table | runtime | zero | every per-arm difference ruled or the stage does not exit |
| 26 | A1 preregister as records | adjudication | zero | metric order fixed with an amendment chain |
| 27 | A2 hash blind files | adjudication | zero | hashes recorded before any label opens |
| 28 | A3 score once, paired | adjudication | zero | paired, coverage as coverage |
| 29 | A4 report with chance and MDE | adjudication | zero | claim, or no claim |

Stage briefs live in `references/stages/`. Read one when its stage arrives, not before.

## Loops, and how each one exits

Four loops. Every one has a written escape.

| Loop | Exits when |
|---|---|
| stage loop, prompt to disposition to ruling | the ruling is close, or the stage advances the frontier |
| queue loop, P5 back to P1 | survivor count reaches S, or the optimistic bound on remaining supply falls below S |
| surface loop, R1 back to instrument | the known-good subject completes, which indicts the subject rather than the surface |
| amendment loop, session changes its own rule | the amendment is recorded in the ledger with its cause |

The queue loop is the only cycle in the dependency graph. Everything else points forward.

## Staying unstuck

Progress means a criterion moved from UNDEMONSTRATED to PASS or FAIL, or a candidate closed. Not stages run, not time spent, not calls made. A stage that grinds for an hour and settles one criterion is advancing. A stage that returns in a minute with nothing demonstrated is not.

When a stage does not advance, the next action depends on the signature, never on a retry count. Full ladder in `references/loop.md`.

| Signature | Wrong move | Exit |
|---|---|---|
| blocked on a parameter, not the threat it protects | retry | ruling, escalate now |
| same symptom after two distinct repairs | a third repair | reclassify the diagnosis |
| surface and subject both suspected | another repair | run the known-good control |
| second failure on the same fixture | another attempt | re-select the fixture from the median |
| declared blocked with no edge from the blocker | wait | check `graph.md`, then run now |

The ladder itself is a gate and arms only with both controls run. Its must-not-fire case is a long legitimate stage. Without that control the anti-stall mechanism becomes the stall.

## Global refusals

1. Refuse a number whose five provenance fields do not all resolve.
2. Refuse to arm any check whose must-fire and must-not-fire controls have not both run.
3. Refuse a stop condition written over a name rather than a named threat.
4. Refuse an aggregate across unequal denominators.
5. Refuse a directional claim at or below the minimum detectable effect.
6. Refuse to score an unparsed answer as zero. It is a coverage failure.
7. Refuse to read a grant from configuration.
8. Refuse to act on a declared-versus-emitted difference before classifying it.
9. Refuse to widen a definition after a low count.
10. Refuse to filter items on the outcome variable. Stratify instead.
11. Record an interrupted run as UNDEMONSTRATED, never zero.
12. Refuse to emit a ledger without its completeness assertion.
13. Refuse to curate from a summary, an abstract, a snippet or a recollection. Read each seed whole.
14. Refuse an item whose answer appears in the text of its own source, unless the exposure key places that source after every subject's cutoff and the ruling is written.
15. Refuse a manifest slot whose source field reads assumed, conventional or standard.
16. Refuse a similarity cut chosen to increase unit count.
17. Refuse to count an axis before the decision shape is ratified, and refuse a shape whose alternatives field is empty.

## Scripts

- `scripts/tau.py` sweeps the similarity cut and chooses it by measurement, refusing when the curve does not bound one.
- `scripts/queue.py` derives Q from observed yield with an exact interval, and states when the interval is too wide to license a queue.
- `scripts/power.py` computes chance, sigma_d, MDE and N_min from two columns of per-item composition scores.
- `scripts/validate.py` checks provenance records and module ledgers.
- `scripts/replay.py` runs the case suite and reports must-fire and must-not-fire separately.

## Before trusting any of this

`references/replay.md` describes the suite. Thirty-eight cases with their rulings sealed. Most are extracted from a single construction record. Those covering the discovery module are marked SYNTHETIC where the record contains no instance, and they carry less weight than the extracted ones.

Two limits stand and belong in any write-up. The suite and the stages come from one project, so reproducing its rulings says nothing about a case outside it, and an independent corpus must be replayed before this counts as evidence of generality. And a procedural seal held by the same party that wrote the spec proves nothing, so have someone else hold `cases/RULINGS_SEALED.csv`.
