# The decision shape

Derived at D4 before `k`. Consulted at P3, I1, P6 and A3.

## Why this slot rules the others

The shape fixes what a unit is, what a mechanical floor can be built from, what chance is, and how many scored scalars one labeled unit yields. Each of those is an input to a closure condition somewhere downstream. A shape adopted by habit therefore decides the outcome before any counting starts, and leaves no record when it does.

`k` presupposes a shape. So does the chance baseline, `k` over candidates per item. Derive the shape first or the slots beneath it inherit an unstated assumption.

In the record every candidate that survived to an arm was a selection task, and no ruling anywhere states that another shape was weighed and rejected. An unconsidered option and a considered rejection are indistinguishable once the queue is written. This file exists to force the second.

## The four roots

| Root | Answer object | Wrong when | Grader | Role floor |
|---|---|---|---|---|
| infer | a claim about the world as it is | it misses the true value | an answer key | predictor |
| explain | a mechanism or a cause | it fits the data and names the wrong cause | a certified judge, or likelihood under a frozen model | scorer |
| generate | a new object meeting constraints | the object fails the constraints | a certified oracle: simulator, execution harness or assay | generator |
| intervene | the next action to spend a scarce resource on | the resource is wasted | the outcome that follows the action | simulator |

Two candidates share a root only when all five columns match. Differing in resolution alone is not a different root. Classify, estimate, rank, pick k of M and calibrated forecast are all infer, read at different resolutions.

Four is the minimum set. Collapsing any two merges tasks whose graders differ, and a grader that cannot be shared is the definition of a separate root.

## Gate 1, the role floor

`manifest.md` places the line after predictor: a task needing only encoder and predictor needs no agent, because the agent does not construct the input.

Read the table against that line. Infer's role floor sits **on** the line. A bare infer candidate therefore cannot register agent value at any accuracy, because the mechanical composition is the whole task and the agent is decoration on a sort. Explain, generate and intervene sit below the line natively.

An infer candidate is lifted or closed. A lift adds a constraint the agent must construct against, and there are only three honest kinds.

| Lift | What it forces |
|---|---|
| a budget spanning more than one criterion | generation of alternatives, then comparison |
| a required rejection with a written reason | explicit evaluation rather than a sort |
| a declared stopping rule | a decision about when evidence suffices |

A lift is honest only when I1 rebuilds the mechanical floor against the lifted task. Lifting the task and floor-testing the original inflates every downstream effect.

**Closes the candidate when** the role floor does not fall below the predictor line and no lift applies.

EXTERNAL, weaker than the record: a published protein-design benchmark reports that agents select tools competently and evaluate shallowly, invoking evaluation tools at roughly a seventh of expert intensity, and that forcing depth improves outcomes. If that holds generally, agent value concentrates in the roles below the line and a benchmark sitting on the line measures the wrong thing. Treat as a hypothesis, not as a count.

## Gate 2, the grader

| Grader | Cost before first item | Available from |
|---|---|---|
| answer key | zero | the corpus |
| frozen generative model, scored by likelihood | days | the tool inventory |
| certified oracle, simulator or harness | weeks at I4 and I5 | the tool inventory |
| certified judge | weeks, plus its own construct validity | nothing in the corpus |

A grader is admissible only when it is in the tool inventory at D4 or acquirable inside the budget supplied at D5. Name it. A shape whose grader is aspirational is not a candidate.

A judge is an instrument and carries I4 and I5 like any other. Certify it against the scored quantity, with a wording perturbation as its must-not-fire control, or it is not a grader.

**Closes the candidate when** no admissible grader exists for the shape.

## Gate 3, the yield

State how many independently scored scalars one labeled unit produces, and whether each is graded or thresholded. One line of arithmetic, five provenance fields, like any other number.

| Readout | Scalars per unit | Thresholded |
|---|---|---|
| a single pick, scored correct or not | one | yes |
| precision at k over one round | k | yes |
| a rank over M | one rank statistic | partly |
| a point estimate | one | no |
| a calibrated probability per candidate under a proper score | one per candidate | no |

Thresholding discards the margin, which is where the variance reduction lives. A candidate reading one thresholded binary per unit against a strong floor should expect P7 to close it. In the record MDE was computable on day one and went uncomputed for fourteen stages. This gate is the zero-cost forecast of that closure, taken before the corpus is built rather than after.

**Escalates when** the yield is one thresholded binary per unit and P2 reports a floor above half the ceiling.

## Deriving the shape from the corpus

Three observations, all from sources already read in full at D1. No new search.

1. **The action.** Read methods and discussion. What does the practitioner do once the reasoning step returns? Commit a scarce resource, publish a value, publish a cause, or publish an object they made. The action names the root, and it is the only one of the three that comes from the world rather than from our convenience.
2. **The grader.** From the tool inventory derived in the same stage, list which graders in Gate 2 exist for this domain today.
3. **The road not taken.** Name every root the corpus supports, not only the one that fits first. A root eliminated without a named binding gate is unconsidered, not rejected.

**Rule all four roots in one pass.** Write the four rulings together, then choose among the survivors. Re-opening a root that closed at a shape gate is an amendment, recorded in the ledger with its cause, never a free retry. Without this the shape stage can cycle roots at zero cost and report motion as progress.

### The chain and the branch

A methods section reports the path that worked. It is a surviving trajectory, not a process, and the candidates abandoned along the way are absent by convention. So a workflow extracted from papers is a pipeline, and a pipeline is what I1 builds as the mechanical floor. Site a task on the chain and the floor becomes the answer key, which produces a null before any agent runs.

Only branch points can carry a task. A branch point is a place where the text shows a person choosing among alternatives with a reason: a selection under a stated criterion, a discarded candidate, a changed parameter, a stopping decision, a substituted tool. Census them at D1, where the seeds are already being read whole.

| Count, per seed | What it sets |
|---|---|
| chain length, operations from input to reported result | execution difficulty, which is a runtime question |
| branch points with an alternative visible | the only positions a task can occupy |
| branch points with the rejected option named | the only positions that carry a negative |
| branches per episode | a task is multi-turn only when two branches sit inside one episode |

A long chain holding one branch is a single-decision task in a workflow costume. Report chain length beside branch count and never read one as the other.

The kind of choice at the branch names the root. Which candidate to spend the instrument on is intervene. Which cause accounts for the observation is explain. Which object to build under a constraint is generate. Which value the data implies is infer.

A branch whose rejected alternative was never written down still carries a root, but it carries no found negative. Publishing convention hides rejections, so treating that silence as disqualifying routes almost everything to infer. **Construct the negative instead, and disclose it.** A constructed negative is admissible only when the mechanical composition would itself select the rival, which is what stops it being a strawman, and it enters its own stratum. Report the headline over found negatives and over both, never over the constructed ones alone. Where the two disagree, the constructed rival was weak and the effect it produced is not a result.

**Refuses** to site a task on a chain with no branch point. That chain is the floor.

### Evidence depth, the second census

Branch count measures decisions. Depth measures how many channels the answer needs. They are independent, and a candidate may be rich in one and empty in the other.

Depth is the construct that makes a task hard for the right reason, because a channel the arm lacks caps it however well it reasons. It is also where tool advantage should live, so I2 already measures C and C-1.

Census at D1, alongside the branches. The locator is the sentence or composite figure where the authors combine channels to reach a conclusion, not the workflow that produced them.

| Count, per candidate conclusion | What it sets |
|---|---|
| channels the authors claim they needed | a hypothesis, never the variable |
| channels the mechanical composition still reaches the conclusion without | measured depth, by leave-one-out |
| conclusions a subset of channels supports wrongly | the only items that separate a shallow arm from a deep one |
| independent systems measured at this depth | supply, which falls as depth rises |

**Measured depth is the variable, claimed depth is not.** Where one channel alone reaches the conclusion, the second instrument confirmed rather than inferred. Stratify those as depth one. Never drop them, and never trust the claim in their place.

Depth and supply pull against each other, because few systems are measured three ways. Run P3 at each depth level and report where the count dies, rather than choosing a depth first and discovering its supply later.

Two constraints bind harder here than elsewhere, and how they resolve is a local judgement, not a rule this file can fix.

| Constraint | What it forces |
|---|---|
| the conclusion sits in the text of its own source | D2's exposure refusal applies. Either the source postdates every subject cutoff, or the measurements are unpublished |
| the channels the corpus reports are not the channels the inventory holds | rule at D4 whether a substitute measures the scored quantity, per I4, or leave the channel unmounted |

Where the seeds are thin, the honest moves are to read further sources, to hold the item at UNDEMONSTRATED, or to close on the binding count. Inferring a depth the corpus does not show is none of these.

**Carry measured depth into P6 as a stratum.** It yields a preregisterable prediction: advantage should rise with depth and vanish at depth one, where the classical arm holds the channel too. A profile flat across depth strata indicts the depth or the tool, and reading it costs nothing after the ablation the census already ran.

### Extrapolating from examples

Do not generalise a root from a handful of extracted items. Extrapolation regresses to the modal shape in the extractor's own distribution, and that mode is selection. Left free, the extrapolation step rebuilds the monoculture that the alternatives field exists to expose.

Extrapolate inside a root and subtype already ruled at D4, never across them. A new root opens only when a branch-point census finds the branch that supports it, never because an item resembles one already written.

### The record

Write the shape record with the surviving set, the chosen root and subtype, both censuses behind them, the binding gate for each root that fell, and the alternatives considered. The alternatives field is not commentary. It is the evidence that the funnel was inspected rather than obeyed.

## Subtypes

Three levels, and only the first is closed.

| Level | Status | Chosen where |
|---|---|---|
| root | closed, exactly four, partitioned by grader kind | D4 |
| subtype | open, the lists below are seeds | D4 |
| item template | never enumerated here | the shape record, per candidate |

**Run the three gates at subtype level, not at root level.** Grader and yield differ between siblings of the same root, and the gates bind on the difference. Ruling at root level hides the only choice that changes cost.

**A subtype absent from these lists is admissible** when its action appears in the corpus and it passes all three gates. Record it as derived, with its provenance, exactly like a listed one. These are seeds, not an enumeration.

**Item templates stay out of this file.** The question wording, the modality, the option count and the presentation follow from the domain and the tool inventory, so fixing them here would rebuild one level down the same monoculture this file exists to break. Derive them per candidate and record them with the shape.

### infer, a ladder rather than siblings

Each coarser rung is a finer rung thresholded, so climbing never changes the governed decision and yield rises monotonically. **Climb to the finest rung the label source supports, then threshold to report the pick.** Descending is a reporting choice, never a design choice.

| Rung | Grader | Yield per labeled unit |
|---|---|---|
| pick k of M | answer key | k thresholded binaries per round |
| rank all M | answer key | one rank statistic, partly thresholded |
| point estimate | answer key | one graded scalar |
| calibrated probability per candidate | answer key under a proper score | one graded scalar per candidate, none thresholded |

Every rung holds the same role floor, on the predictor line, so the lift in Gate 1 is required at every rung. Climbing raises yield. It does not by itself admit an agent.

### explain, generate and intervene, siblings rather than rungs

Siblings do not substitute for one another. Choose one, and record the others with their binding gate.

| Root | Subtype | Grader | Role floor | Yield per labeled unit |
|---|---|---|---|---|
| explain | mechanism attribution | certified judge | scorer | one rubric score per case |
| explain | anomaly diagnosis | certified judge, or a held-out repeat measurement | scorer | one score, plus the repeat where it exists |
| explain | hypothesis set under a frozen likelihood | frozen generative model | scorer and generator | one graded log-likelihood per hypothesis |
| generate | inverse problem | the forward model already in the inventory | generator | one graded residual per item |
| generate | object design | certified oracle, simulator or assay | generator | pass or fail, plus any continuous metric the oracle returns |
| generate | procedure or code | execution harness | generator | one binary per test, several tests per item |
| intervene | choose the next measurement | a replayable environment, or a held-out outcome | simulator | one realized value per episode |
| intervene | allocate a budget across rounds | a replayable environment | simulator | one trajectory value, plus one per round |
| intervene | decide when to stop | a replayable environment | simulator | value and cost per episode, two graded scalars |

**Intervene is unreachable from a corpus alone.** Every subtype needs a replayable environment or a held-out outcome for the action not taken, and no published benchmark surveyed occupies this root. Treat it as a build, budgeted at D5 as an instrument, or close it at the grader gate and record that as the finding. Do not carry it as a live option it cannot be.

Read the grader column against Gate 2 and the yield column against Gate 3 before choosing. Hypothesis set and inverse problem are the two subtypes whose grader already exists in a typical inventory, which makes them the cheapest doors out of infer. Every intervene subtype needs an environment or a held-out outcome, which is the binding gate that leaves that root empty across the published benchmarks.

Where two subtypes pass all three gates, rank them on resolving power, yield divided by the MDE that yield implies, and use grader cost only to break a tie. Record the other as an alternative considered.

Ranking on cost first is a greedy step on the wrong quantity. In simulation over the rule structure it routed the choice to the cheapest grader in almost every scenario and left generate effectively unreachable; ranking on resolving power cut the gap between the root chosen and the root carrying the advantage by more than half, at no other cost.

## What the root changes downstream

Consult this table at the named stage. No other file changes when the root changes.

| Stage | infer | explain | generate | intervene |
|---|---|---|---|---|
| P3 positive supply | labeled units after clustering | cases with an adjudicated cause | specifications with an admissible oracle | episodes with a recorded outcome |
| P3 negative supply | labeled negatives | rival causes that were ruled out | specifications that must fail | actions not taken, with outcomes |
| P3 contamination | the answer appears in the item's source | the cause is stated in the literature the subject read | the object is published and indexed | the historical policy is recoverable from the data |
| I1 mechanical floor | sort on the predictor score, take k | copy the cause of the nearest labeled case | run the generator at defaults, keep the best on one metric | the historical policy, or a fixed greedy rule |
| P6 chance | k over candidates per item | the prior over the cause set | the pass rate of unconditioned generation | random allocation under the same budget |
| A3 score | paired per item against the key | rubric with a certified judge, or likelihood | the oracle's verdict, coverage as coverage | realized value per unit of resource, paired per episode |

Intervene carries a further condition and it is why no benchmark occupies it. Scoring an action requires the outcome of the action not taken, which the corpus supplies only for the historical policy. Either hold an environment that can be replayed, or restrict the claim to slices where the outcome is recorded for every arm. Selective labels are not a nuisance here, they are the binding axis.

## Refusals

1. Refuse to count any axis at P3 before the shape is ratified.
2. Refuse a root whose grader is not in the tool inventory or acquirable inside the D5 budget.
3. Refuse an infer candidate that sits on the predictor line with no lift recorded.
4. Refuse to rebuild a floor against the unlifted task after a lift.
5. Refuse a shape record whose alternatives field is empty. Four roots exist; at least three were rejected, each by a named gate.
6. Refuse to change the root after P3 has counted. Re-register and recount, as with any stale freeze.
7. Refuse to read subtype substitution as free. Only infer has a ladder.
8. Refuse a subtype ruled only at root level. Grader and yield are counted per subtype.
9. Refuse an item template lifted from this file. Templates are derived per candidate and recorded with the shape.
10. Refuse to site a task on a chain with no branch point, and refuse to open a root by extrapolation rather than by census.
11. Refuse to stratify on claimed depth. Measure it by leave-one-out or record the item as depth one.
12. Refuse to rank subtypes on grader cost before resolving power.
13. Refuse a constructed negative the mechanical composition would not itself select, and refuse to report a headline over constructed negatives alone.
14. Refuse to re-open a closed root outside the amendment ledger.

## Advances when

The shape record carries a root, a subtype, an admissible named grader, a yield with arithmetic, a role floor below the predictor line or a recorded lift, and a binding gate for every root that fell. Disposition is PROCEED, CLOSE or ESCALATE, with the binding gate named, as at P4.
