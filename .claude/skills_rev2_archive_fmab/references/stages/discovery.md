# discovery — D1 to D5

**Private evidence:** the seed materials you supply, papers, decks, reports, internal notes. No other module reads them.
**Sole writer of:** the seed ledger, the corpus and its exclusion ledger, the cut curve, the derived manifest.
**Cost:** reading time. Zero model calls beyond reading.

This module turns a handful of references into a corpus and a manifest. Everything downstream depends on it, and nothing downstream can detect its errors, so its refusals are strict.

---

## D1 read each seed in full
One source at a time, completely. **Never curate from summaries or search snippets.**

In the record a first pass on snippets produced three adopted surface conventions and one adopted headline, all wrong. A single complete read of the same source forced five corrections to a specification already written. Breadth was the failure and depth was the fix.

Every extracted fact carries a locator: document, section, table or line. A fact with no locator does not enter the ledger.
**Refuses** any extraction sourced from an abstract, a snippet, a summary or a recollection.
**Advances when** every seed is marked read-in-full and every extracted fact resolves to a locator.
**A seed that contributes nothing is recorded as read with zero contribution.** That is a result, not a reason to search wider.

While reading, census the branch points: the places where the text shows a person choosing among alternatives with a reason. The chain between them is the pipeline and becomes the mechanical floor at I1, so only the branches can carry a task. Census evidence depth in the same pass: where the text combines channels to reach a conclusion, record which channels the authors claim they needed. `references/shape.md` holds both censuses and what each one sets.

## D2 assemble the corpus
Write inclusion and exclusion rules, freeze them, then apply them. Publish the corpus with an exclusion ledger naming what was dropped and under which rule.

**A rule that changes after a count invalidates the count.** Re-register the corpus and rerun the counting stages. This is the same discipline as a stale freeze and it is not paid for in items.

**Completeness is an inventory, not a claim.** State which seeds were read, what each contributed, and which questions could not be resolved from them. A curated corpus cannot assert completeness and should not try.

**Refuses** to admit an item whose answer appears in the text of its own source, unless the exposure key places that source after every subject's cutoff and the exposure ruling is written. The exposure key covers whether the data was visible. An item lifted from a paper carries a worse problem: the answer sits in text the subject already read.
**Advances when** the corpus, the frozen rules and the exclusion ledger are published together.

## D3 measure tau from the corpus
Do not adopt a conventional cut. Sweep it.

Cluster at a range of cuts and record cluster count at each. Where two mechanical compositions exist, record their per-item separation at each cut too. Publish the curve.

Choose the cut by measurement. Two signals bound it. Cluster count saturates above some cut, so tighter buys nothing. Separation collapses below some cut, because units too similar to each other land in the band where retrieval saturates and no arm can separate. The record demoted a proposed relaxation on exactly that ground.

Run `scripts/tau.py`.
**Refuses** a cut chosen to increase unit count.
**Advances when** the curve is published and the chosen cut is justified from it, with one looser and one tighter reported for sensitivity.

## D4 derive the remaining slots
Each slot becomes a record with the same five provenance fields as any other number, plus a proposed value.

| Slot | Derive from |
|---|---|
| decision shape | the action the seeds show practitioners taking once the reasoning step returns, ruled against the three gates in `references/shape.md` |
| k | how many candidates seeds commit per experimental round |
| label source | methods sections, classifying measured truth against annotation derived from other predictions |
| exposure key | the data's own deposition or release metadata |
| tool inventory | seeds for what exists, local code for what runs, with a readiness census |
| subject set | availability, plus any stated rung the collaboration requires |
| delta prior | effect sizes the seeds show practitioners acting on |

The label distinction is load-bearing and the record raises it explicitly. Measured truth from an experimental loop and annotation read off another model's output are different objects, and the second inherits whatever defect the annotation pipeline carries.

Derive the shape before `k` and before `delta`. Both presuppose a shape, and a shape adopted by habit passes an unstated assumption into every slot beneath it. The shape carries its own disposition, PROCEED, CLOSE or ESCALATE with the binding gate named, and may close the candidate here at zero cost.

**Refuses** a slot whose source field reads assumed, conventional or standard.
**Refuses** a shape record with no alternatives considered, or a root whose grader is not in the tool inventory.
**Refuses** a target stated without a feasibility count behind it. The record flagged three such targets as aspirations with the same posture the project held before its first counting stage.
**Advances when** every slot carries a proposed value and five resolving provenance fields.

## D5 ratification
Present each derived slot with its derivation, its provenance, and an explicit invitation to override.

Two quantities cannot come from the corpus and must come from you. Your available budget, in hours or cells, because that is a fact about your programme. And the cost of the action the task governs, because the seeds show what other people act on and not what you would act on. The survivor target S follows from budget divided by measured hours per workflow.

Every override enters the amendment ledger with its reason. Ratification is not supplying. It is accepting or correcting a derivation that is already on the page with its evidence.
**Advances when** every slot is ratified or overridden, and the manifest is frozen and hashed.
