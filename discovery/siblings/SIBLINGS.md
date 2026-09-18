# Sibling libraries: router move `search_sibling_libraries` (stage D2), 2026-09-18

**Why this ran.** The environment in 42gwd-8wg77 has 14 X-Sb-O chemistries (Ag Al Bi Co Cr Cu Fe In La Mg Ni Pb Y Zn, each with Sb). N_min is 35 chemistries, so the benchmark closed. This move searched for public composition libraries that have both an XRD pattern and a photoelectrochemical (PEC) figure of merit at each point, so they could be pooled with the current set.

**Full ledger.** `discovery/siblings/sibling_ledger.json` has the queries, 94 library entries with facts and locators, a roll-up by chemistry, and a completeness statement. The per-plate census for MEAD (the Materials Experiment and Analysis Database from JCAP/Caltech) is in `discovery/siblings/census/` (`mead_plates_final.csv` and the raw JSON census files). That folder also holds the scripts that did the census. They read the `.ana` and `.csv` members of the CaltechDATA zips through HTTP range requests.

## Headline counts

| | count |
|---|---|
| Library entries classed ADMIT | 36: 3 curated deposits and 33 MEAD plates |
| **New chemistries, ADMIT** (none of the 14 X-Sb systems) | **23** |
| New chemistries with at least 15 XRD patterns and PEC points but no XRF composition analysis in MEAD (ADMIT_NEEDS_XRF) | 9 |
| New chemistries, PARTIAL | 20. Five of these reach 15 XRD points only when plates are pooled: Cr-V, Hf-V, Ta-V, Ti-V, La-Sr-Ta |
| 14 base chemistries + 23 ADMIT | **37, which is at least N_min = 35** |
| 14 + 23 + 9 conditional | 46 |

Two caveats apply to that sum. First, it counts element sets, and several of the new sets are pseudo-ternary spreads rather than binary lines (Bi-Cu-V, Cr-Fe-V, Cu-Fe-V, Fe-Ni-V, Bi-Fe-V, Ca-Fe-Mn, Ca-Co-Mn, Ca-Cu-V). Second, the MEAD merit is a photocurrent (`I.A_photo`) measured with mixed electrolytes and LEDs. It is not the 4-LED EQE that 42gwd uses. Only Cr-Fe-V (q9zpw) and Ca-Cu-V (0hj2v) carry 4-LED EQE, and Cr-Fe-V uses exactly the same 3.2/2.7/2.4/2.1 eV LEDs at pH 9.

## ADMIT chemistries (new)

| chemistry | XRD patterns | PEC merit rows | source plates |
|---|---|---|---|
| Ag-V | 98 | 64 | MEAD 3212, 3214, 3215 (3218 partial) |
| Ba-Mn | 85 | 33 | MEAD 3046 |
| Bi-Cu | 21 | 19 | MEAD 3933 = dekcc 3933 |
| Bi-Cu-V | 1204 | 940 | MEAD 2783, 3925, 3928, 4376; dekcc 3928 |
| Bi-Fe-V | 332 | 218 | MEAD 3592 (SSRL) |
| Bi-V | 35 | 30 (plus 1809 on inkjet plate 4045, which has only 2D XRD frames) | MEAD 3202, 3459 |
| Ca-Co-Mn | 317 | 191 | MEAD 4135 |
| Ca-Cu-V | 186 | 202 (EQE) | 0hj2v-qwv46 + ehp06-pcf04, plate 3557 |
| Ca-Fe-Mn | 332 | 190 | MEAD 3108 |
| Ca-Mn | 157 | 59 | MEAD 3050, 3199 |
| Co-V | 16 | 16 | MEAD 3455 |
| Cr-Fe-V | 649 | 428 (218 as EQE) | q9zpw-g8s64 + MEAD 7qy17 (3594); MEAD 3102 |
| Cu-Fe-V | 332 | 297 | MEAD 3588 |
| Cu-V | 72 | 79 | MEAD 1381, 1401, 3930 = dekcc 3930 |
| Fe-Ni-V | 466 | 428 | MEAD 3106, 3574 |
| Ge-Mn | 37 | 46 | MEAD 3071 (3213 partial) |
| Mg-Mn | 215 | 29 | MEAD 3059 |
| **Mn-Sb** | 45 | 93 | MEAD 3072 (3216 has 11 XRD; 3279 has 2D frames only) |
| Mn-Sr | 79 | 29 | MEAD 3051 |
| Mn-Y | 53 | 59 | MEAD 3067, 3112 |
| Nb-V | 18 | 16 | MEAD 3224 |
| Ni-V | 35 | 31 | MEAD 3448, 3454 |
| V-Zr | 30 | 32 | MEAD 3446 (3534 partial) |

The 9 ADMIT_NEEDS_XRF chemistries are Bi-Cu-Mn-Sm, Co-Ni, Cr-Mn, La-N-Ta, Mn-Ni, Mn-Sn, Mn-Ti, Mn-V and Mn-W.

## Rejected or partial curated deposits

| record | status | reason |
|---|---|---|
| gd1bc-gs332 (Cu2V2O7 alloys) | REJECT | no XRD; dopants at 1.65 at.% or less |
| bfap4-h2m21 (Ni-Sb) | REJECT | same plate (2283) as the current environment |
| tg041-j4g80 (Mn-Sb-Sn-Ti-Co) | REJECT | dark acid OER, not PEC |
| g1tyb-nje27, ksy2t, km8xg, vt2ec | REJECT | optical data only |
| figshare 21737198 (Bi2WO6-Fe) | REJECT | 4 CIF files only |
| Ludwig ACS SI PDFs (M-V-O, Fe-V-O, Cu-W-X) | PARTIAL | tables and figures only |
| kjenewein GitHub (Fe-Ti-W) | REJECT | no XRD |
| 0hj2v plates 3577/3589/3590 | PARTIAL | EQE at every point, XRD for 1 to 3 samples per plate |
| MEAD 4045, 4021, 4022, 4226, 3279 | PARTIAL | XRD only as Bruker .gfrm 2D frames |
| MPS aeffy-dcr62 | PARTIAL | 4.5 GB PostgreSQL dump, not downloaded |
| HTEM (NREL) | REJECT | host does not resolve |

No library from outside JCAP/Caltech had per-point XRD and PEC data in a public deposit.

## What a loader needs, by source

1. **q9zpw + MEAD 7qy17 (Cr-Fe-V).**
   - EQE comes from `data/Fig3/SLF9_EQE_comp.csv`.
   - XRD patterns are 332 `ana__1_35941_NNNN_integrated.csv` files (columns `q.nm,intensity.counts`). Map each file to its sample number with the `.ana` line `ssrl_csv_pattern_file;...;<sample_no>`.
   - XRD compositions are in `data/Fig1/xrd_sample_comp.xlsx`.
   - Match XRD to EQE by nearest composition.
2. **0hj2v + ehp06 (Ca-Cu-V).**
   - The `.udi` file already parses with `bench/data.py::parse_udi`.
   - EQE comes from `Fig2_3_4_eqe_scatterplot.csv` with `plate==3557`. A value of -9 means invalid.
   - Match by nearest (Ca, Cu, V) composition.
3. **dekcc (Bi-Cu-V, Bi-Cu, Cu-V).**
   - Read `base_plates&samples.pck` and `IilldiffCV3_cathodic.pck` with pandas.
   - XRD patterns come from the MEAD xrds analysis CSVs (`q.nm,two_theta.deg,intensity.counts`). Sample numbers match exactly: 288/288, 15/15 and 19/19.
   - The 3928 zip is 1.5 GB, so fetch its members by range request. Alternatively, use DRNets `XRD.npy` (307x1197) with `composition.npy` in column order (Bi, V, Cu).
4. **MEAD plates.** Each plate needs three pieces:
   - (a) the XRD analysis CSVs. Get the sample number from the last field of the pattern-file line in the `.ana`.
   - (b) the eche analysis photo FOM CSV (`sample_no,runint,plate_id,I.A_photo,I.A_photo_ill,I.A_photo_dark`). It has a YAML-ish header, and the data starts at the `sample_no` line.
   - (c) the XRF analysis CSV (`*.AtPerc` or `*.AtFrac`).

   The XRD, PEC and XRF grids differ. On plate 3212 only 2 XRD samples share a sample number with an XRF sample. The loader must interpolate composition by platemap x,y (`0057-04-1110-mp.txt`, which is in the tg041 zip). pH and LED wavelength are read per run from the eche `.rcp` that each `.ana`'s `experiment_path` points to.

## Not resolved from the sources read

- The electrolyte and LED for most MEAD plates. They were read only for the 14 bundle plates.
- The Matter 2020 (Cu-V-X) paper and the J. Mater. Chem. A 2020 "29 photoanodes" paper. Their publisher and preprint PDFs returned 403.
- Whether the MEAD photocurrents are comparable across plates without normalising by lamp power.
