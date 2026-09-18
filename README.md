# 19C_materials: FM-advantage benchmark, materials-science instance

This project runs the `fm-advantage-benchmark` skill (vendored in `.claude/skills/`) on materials science. It follows the guideline in `discovery/seeds/seed00_guideline.md`: tasks sit only at inverse steps (branch points), and a densely measured combinatorial library is a replayable environment for the *intervene* root.

The question: does an agent (claude-opus-5) holding materials foundation-model tools (a universal ML interatomic potential) make better decisions than
1. the same agent holding only classical tools, and
2. a fixed mechanical composition of those tools with no agent in the loop?

Progress is tracked in `STATE.md` (one row per stage: PASS / FAIL / UNDEMONSTRATED) and `RUN_LOG.md` (chronological). Every ledger is a JSON record validated by `.claude/skills/fm-advantage-benchmark/scripts/validate.py`.
