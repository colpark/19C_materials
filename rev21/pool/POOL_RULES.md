# Pooling admission rules (D2 re-entry), frozen 2026-09-18, before any sibling floor or count

- **P-I1 (modalities):** the plate carries a 1D-integrated XRD pattern and a photoelectrochemical merit (EQE or photocurrent) at composition points of the same plate.
- **P-I2 (episode):** plate × electrolyte run × illumination. Each episode holds exactly one LED and one electrolyte.
  - Score = best merit found ÷ best merit in the episode. At fixed photon flux within an episode, photocurrent and EQE rank identically, so the scored quantity is unchanged.
  - Episodes mixing lamps or electrolytes are excluded.
- **P-I3 (composition):** the cation fraction vector per merit point comes from XRF, or from platemap x,y interpolation of XRF.
  - Each merit point takes the XRD pattern nearest in composition, within 0.05 (L1/2 over cation fractions).
  - Merit points without such a pattern are dropped and logged.
- **P-I4 (size):** at least 15 candidate merit points per episode.
- **P-I5 (geometry):** 1D lines and 2D spreads are both admitted. The candidate coordinate is the cation fraction vector. Floors use the same GP with an RBF on Euclidean composition distance; on a line this reduces to the run-1 kernel.
- **P-I6 (unit):** chemistry = cation element set. Every plate with the same set is one cluster.
- **P-E1:** exclude plates already in the base environment (e.g. bfap4 plate 2283).
- **P-E2:** exclude XRD available only as 2D frames.
- **P-E3:** exclude ADMIT_NEEDS_XRF plates (no composition).
- **Budget:** B_EQE = 3 per episode, as in the rev2 manifest. **Not re-derived for pooled plates.** The per-item budget is reserved to the user.
- **Channel definitions:** the FM channel (MACE-MP-0 medium hull, MEGNet gap) and classical channels are unchanged. Phases are those of the plate's cation set plus O from MP via OPTIMADE: ternary/quaternary ≤ 80 sites, binaries ≤ 30 sites (A-02).

## Rulings after the loader reported (no rule changed)
- **R-P1:** the 3 episodes lit by "Doric LEDc2 388+W35" (an LED plus a white LED) are EXCLUDED under the literal P-I2, "exactly one LED". Admitting them would widen the definition after the count (refusal 9). This loses Cu-V (its only episode). Pooled supply: 89 episodes, 22 new chemistries, 36 in total. The admitted variant is reported as a sensitivity check only.
- **R-P2:** the loader's measurement rulings stand as recorded in `pool_ledger.json`: XRF raster renumbering on 3046/3050/3051/3199, line interpolation, the 1 mm edge tolerance, negative photocurrents kept (clipped at 0 by the score, as in the base), and a fixed bias or CV merit within an episode.
