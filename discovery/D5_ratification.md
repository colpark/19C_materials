# D5 ratification (frozen 2026-09-18 00:25)

Manifest: `discovery/manifest.json`, sha256-of-content `c40cbec648bff14cf6d0546d7f4b7b728e76f27a81379143cb4b0b11da789dfd`.

| Slot | Value | Ratified by |
|---|---|---|
| budget | about 300 agent episodes | **user** (plan-mode answer) |
| subject_set | claude-opus-5 | **user** (plan-mode answer) |
| cost of action | not supplied, so delta comes from the seeds | user may override |
| tau | element system, 14 units (amendment A-01) | delegate, open to user override |
| decision shape | intervene / choose next measurement (C1). C2–C5 are closed with their gates named | delegate, open to user override |
| k, per-episode budget, label source, exposure key, tool inventory, delta = 0.17, S = 100 | see the manifest | delegate, open to user override |

The user asked for an autonomous run after one plan-mode exchange, so every slot not supplied is **delegate-ratified**. Each one carries its derivation and five provenance fields, and any of them can be overridden. An override enters the amendment ledger.

**Disclosed ordering deviation.** R1, the harness control on a synthetic stub item, ran before D5 was frozen. graph.md orders D5 → R1. R1 touched no domain item, spent one cell ($0.09), and its result does not depend on any manifest slot. Recorded here rather than re-run.

## Amendment ledger

| ID | Stage | Change | Cause |
|---|---|---|---|
| A-01 | D3 | unit changed from XRD-cut clusters to element system | XRD similarity measures the substrate (FTO vs Pt), and tau.py refused an unbounded curve |
| A-02 | I1 | binary-oxide polymorphs capped at 30 sites for the MACE hull | compute: 914 structures at about 10 s each. Hull ground states of these oxides sit in cells of 30 sites or fewer. Ternaries stay capped at 80 |
| A-03 | data | LED energies corrected from the source column (CA3 2.4 eV, CA4 2.1 eV) | a hard-coded guess was wrong. Fixed before any FM floor ran |
