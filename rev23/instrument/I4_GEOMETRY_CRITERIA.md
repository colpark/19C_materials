# I4 certification of mechanical compositions per geometry (declared before computing, 2026-09-19)

- **Geometries:** *line* (2 cations; 1D coordinate) and *spread* (≥ 3 cations; composition vector).
- **Compositions:** cls_gp, cls_xrd, fm_prior, fm_xrd (and the ablations fm_xrd_nogap, fm_xrd_nomace).

A composition is **PASS** on a geometry when both hold:
1. **Functional:** on every episode of that geometry it returns B_EQE = 3 distinct valid candidate indices.
2. **Construct:** the paired 95% interval of (composition − chance) over that geometry's episodes is not entirely below 0. The composition must not do reliably worse than random allocation.

Otherwise it is **FAIL**.

**PI ruling (2026-09-19):** the XRD composition is recorded FAIL on spreads, and it is not repaired in this pass. The IDW interpolation of XRD evidence between 5 farthest-point XRD positions is an unvalidated extension of the run-1 1D linspace.
- This applies to cls_xrd and to the compositions built on the same XRD evidence (fm_xrd, fm_xrd_nogap, fm_xrd_nomace). **The FAIL is recorded regardless of criterion 2.**
- Spread episodes stay in the cohort as a stratum (geometry). A floor that FAILs on a geometry is reported for that stratum and marked uncertified. It is not used as the bar there.
