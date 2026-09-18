# Seed 00: the guideline given to the user (verbatim, supplied 2026-09-17)

Yes, and materials science has a cleaner chain and branch separation than biology does.

**The general anatomy.** The forward direction is always the chain. Composition to structure to property to performance runs through simulators that nobody argues with, so an agent adds nothing there and I1 will build exactly that pipeline as the mechanical floor. Every branch in materials sits on an inverse step, where a measurement underdetermines the answer and a person picks among candidates. Find the inverse and you have found the only place a task can sit.

**Five families, and where the branch actually is.**

*Structure solution from spectra.* Chain: measure, compare to reference, report. Branches: which candidate phases enter the comparison set, how many shells and which scattering paths go into an EXAFS fit, whether to float or fix coordination number, and when to declare amorphous instead of forcing a phase. This family has a property almost nothing else in science has. EXAFS fit tables and Rietveld refinements publish the rejected models with their R factors, by convention, in supplementary information. The found negative is already written down. Nobody has mined those tables.

*Computational screening.* Chain: query Materials Project, filter, relax, rank, take the top N. That is the floor, and Guang's testbed sits close to it. The real branches are the thresholds: energy above hull at 0 versus 25 versus 50 meV per atom, which descriptor, and when to escalate from a machine-learned potential to DFT. That last one is an intervene branch wearing a screening costume, because it spends a scarce resource on a chosen candidate.

*Synthesis and process optimization.* Branch-rich and almost entirely unpublished. Text-mined failed inorganic synthesis sets exist and are the exception worth chasing.

*Failure and degradation analysis.* Battery post-mortem is the canonical case. Root is explain, subtype anomaly diagnosis, and a held-out repeat measurement can serve as the grader without a judge.

*Multimodal constraint satisfaction.* Deyu's TiZnO wafer is a worked example and he described the branch without naming it. XRD gives sharp lines in some composition regions and amorphous elsewhere. You go to XAS to find the motif that matches, then carry that structure back to XRD and check consistency. Candidates that satisfy one constraint and fail the other get rejected with a reason. That is a branch point with a native negative, and it exists because two modalities must agree on one atomic structure. A single modality cannot produce it. That is also the real answer to why SEM plus XAS kept failing to yield a question while XRD plus XAS yields one immediately.

**The asset I would not overlook.** A densely measured combinatorial library is a replayable environment. Deyu's wafer carries XRD, XAS and optical gap across the whole gradient, which means the outcome of the action not taken is recorded. Hold out the map, ask an agent where to measure next under a budget, then reveal. That is the selective-labels problem that shape.md says leaves intervene empty across every surveyed benchmark, and a combinatorial wafer solves it by construction. Kevin Yager runs autonomous experimentation at CFN and CMS, so the logs of past campaigns are the same thing at larger scale. Graham has already met him.

If I were spending this week, I would run the branch census on twenty EXAFS and Rietveld papers in the TiZnO or battery space and count how many publish a rejected structural model with a number attached. That count decides whether you build from found negatives or constructed ones, and it costs reading time.
