# runtime — R1 to R8

**Private evidence:** traces and runtime state. Never reads labels or design rationale.
**Sole writer of:** control record, gate register, grant record, provenance chain, symmetry table.

---

## R1 harness control
First stage in the workflow. A known-good subject, a synthetic item, a stub composition. Nothing domain-specific, one cell.
A failure inside a harness is otherwise ambiguous between surface, subject and task. In the record that ambiguity ran eight stages and one cell settled it. Write three dispositions before the run so the result cannot be reinterpreted.
**Advances when** the known-good subject completes.
**Sends work back to the instrument module** when it does not. That is the only edge in the funnel that does not remove a candidate.

## R2 isolating probe, one tool
One server, one tool, a prompt under two hundred tokens, explicitly not a real item. In the record a probe fired on a full task prompt and conflated a parser test with a load test.
**Advances when** one real call completes, the value reads back, the receipt resolves, and a forged identifier is rejected.

## R3 load ladder, declared steps
Grow load in declared steps, reporting after each addition before the next. Servers mount one at a time.
**Advances when** every step reports its own numbers.

## R4 verify grant, model side
Never read a grant from configuration. Enumerate the catalog the model actually receives. Subtract rather than allow, because allow lists behave additively and hidden capabilities surface one layer at a time. Canary every excluded capability.
A subject invoking a helper model on every turn is not a single model and belongs in the write-up.
**Advances when** the model-side catalog and its canary results are recorded.

## R5 author gates, both controls
A gate measures the quantity it claims to protect, from a specification. It names a threat, never a thing. It does not duplicate a protection the platform already provides. A safety gate and a validity gate are different, and a validity gate does not bind on an unscored run.
Generate both controls from the declaration: the input that must trip it and the input that must not. Require at least one control derived from a real prior failure.
When a specification is unreadable, say so, invent nothing, and ask what the gate was protecting.
**Advances when** every gate is armed or refused, with both controls run.

## R6 hash what the runner emits
Hash the emitted artifact, not the declared one, at every cell. In the record a declared 973-byte prompt against an emitted 2,023-byte one sent two harnesses at different tasks for a full stage.
**Advances when** declared and emitted hashes sit side by side.

## R7 classify cosmetic or not
Classify any difference before acting on it. A normalisation for cosmetic differences ships with its own must-fire controls rejecting a changed instruction, developer message, version or policy.
Without this stage, R6 reproduces the failure it fixes. One capital letter in a heading discarded three valid cells and roughly 2,800 seconds of frontier model time.
**Advances when** the difference is classified and the action follows the classification.

## R8 arm symmetry table
Before any scored cell, print per arm: prompt bytes, function count, output cap, presentation mode, reference material supplied. Any difference gets an explicit ruling or the stage does not exit.
Seven of the nine recorded confounds appear in that table. Reference file paths are necessary for a tool-using arm and are fabrication bait for a tool-free one, so prompt symmetry across arms is not prompt neutrality and the trade-off needs a ruling.
**Advances when** every difference carries a ruling.
