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
