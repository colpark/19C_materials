# C1x explain candidate: declarations before any computation (2026-09-18)

- **Unit:** one chemistry (element system M in M–Sb–O), the cluster.
- **Label:** the sign of the mean over that chemistry's episodes of fm_xrd − cls_xrd at B=3 (mechanical ablation floors, zero cells). An item is scored only if the grader is reliable (below).
- **Grader certification (I4 for a grader):** split-half. Split each chemistry's episodes by electrolyte run (`anals`: first half vs second half in sorted order) and correlate the per-chemistry mean effect across halves.
  - A Spearman correlation ≥ 0.5 across chemistries with both halves present → grader PASS.
  - Otherwise → FAIL. The candidate then closes at Gate 2 and routes as I4_FAIL.
- **Mechanical explain floor (features fixed now):** leave-one-chemistry-out logistic regression on three FM-summary features per chemistry:
  1. the number of ternary MP phases within 50 meV/atom of the MACE hull;
  2. the share of those phases with MEGNet HSE gap in [0.5, 3.5] eV;
  3. the Sb-fraction span of those phases.
- **Chance:** predict the base rate (leave-one-out).
- **Disclosure:** the orchestrator saw per-chemistry effects in the rev2 report (Al, Mg help; Co, Fe hurt) before this declaration. The features above are chosen from FM-channel content, not from those labels, and are not revised after the computation.

## Amendment C1x-A1 (2026-09-18, before any pooled floor exists)

- **Cause:** the delta slot was UNDEMONSTRATED (no seed gives an acted-on effect for a sign call).
- **Change:** C1x is graded by the **consequence** of its call, in C1's units.
  - **Item:** one chemistry.
  - **Decision:** trust the FM channel (run fm_xrd) or not (run cls_xrd).
  - **Realized value:** the mean over that chemistry's episodes of the chosen composition's floor score, at B=3.
- **Delta:** 0.169, inherited from C1's manifest in the same units and from the same seed source (S3, 2× acceleration). **No new delta is introduced.**
- **Floors:**
  - always-classical (cls_xrd)
  - always-FM (fm_xrd)
  - the predeclared feature logistic, choosing per chemistry, leave-one-chemistry-out
- **Ceiling:** the adaptive oracle, the per-chemistry max of the two.
- **Chance:** a random choice per chemistry (the mean of the two).
- **Resolution:** paired over chemistries; P7 via power.py on (policy value − always-classical), cluster = chemistry.
- **Grader:** the mechanical ablation floors. Split-half certified at rho 0.70 on the base set, and re-certified on the pooled set with the same 0.5 threshold.
