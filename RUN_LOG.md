# RUN LOG

- 2026-09-17 22:40. Plan approved. D5 inputs from the user: budget of about 300 agent episodes, subject claude-opus-5.
- 2026-09-17 22:45. Data probe results. HTEM is unreachable (DNS). Europe PMC full-text XML works. Libraries downloaded:
  - CAMEO Fe-Ga-Pd: 278 points, XRD + magnetization.
  - Caltech CC0 XRD libraries: Cu-Ca-V (186 points), Fe-Cr-V, metal antimonates.
  - No public Zn-Ti-O combinatorial library exists, and the Zn-Ti-O EXAFS literature is thin (1 open-access paper).
- 22:55 R0 replay: polarity 38 of 38. This is not blind, because `emit` shows polarity next to each case. 1 disposition misruled (K06), 6 rulings incomplete. See `replay/REPORT.md`.
- 23:05 D1 census complete. 30 papers.
  - 4 publish a numbered rejected structural model.
  - 2 have both a numbered negative and raw data.
  - The found-negative premise fails, so C3 moves to constructed negatives or a replayable environment. See `discovery/census/CENSUS_RESULT.md`.
- 23:05 Replay environment built (`bench/data.py`): antimonate photoanode plates, CaltechDATA 42gwd-8wg77 (CC0).
  - 196 episodes = 22 plates × electrolyte runs × 4 LEDs, covering 14 elements.
  - About 29 compositions per episode, with XRD at every point.
  - Data sha256 677fefa7…
- 23:08 FM channels run on the GB10 GPU: MACE-MP-0 medium (float64, FIRE relaxation with cell filter) and MEGNet-BandGap-mfi.
  - Ni-Sb-O check: MACE ranks NiSb2O6 (mp-505271) as the most stable ternary, and that is the phase the dataset labels photoactive.
  - MEGNet predicts a gap of 0.0 eV for NiSb2O6. That is an I4 construct-validity flag.
- 23:30 R1 PASS. Stub cell with opus-5, MCP connected, 7 calls, submitted the correct index. Found `ReadMcpResourceDirTool` in the native catalog and added it to the deny list. R4 will canary it.
- 23:40 D1 dataset seeds S0-S3 read in full (`discovery/seeds/seed_ledger.json`, 56 facts with locators). S1's SI returned 403.
  - Label source: EQE is measured truth. Phase labels are human XRD annotation and are not scored.
  - Delta source: S3 reports 2-5× acceleration for finding any top candidate. S2 reports 31% vs 10% of runs within 1% of the optimum.
- 23:45 LED map corrected from the file's LED_eV column: CA3 = 2.4 eV, CA4 = 2.1 eV (earlier 2.3/1.8 eV were wrong). The FM floors had not yet run, so no downstream number used the wrong values.
- 23:50 D3: plate XRD-map similarity clusters by substrate (FTO vs Pt), not by chemistry. That is a referent failure.
  - `tau.py` REFUSES: the curve is unbounded up to cut 0.99.
  - Amendment A-01: the independent unit is the element system (categorical, 14 units). Cause: the XRD similarity measures the substrate, and the FM prior is a function of the element alone.
- 23:55 D2 corpus frozen: 196 episodes, 7 excluded under E1 (answer in the S1 main text), 189 included, arm cohort of 100 (LED-stratified hash sample, 14 elements).
- 00:05 P3 contamination probe (opus-5, no tools, 28 prompts per framing). Recall 3/28 within 0.05 (MAE 0.230), predict 4/28 (MAE 0.246). No memorization signal. Exposure is disclosed, not binding.
- 00:40 R2 isolating probe via a direct MCP client: PASS (`runtime/r2/*/r2_result.json`).
  - One FM call read back correctly: MACE AlSbO3 ehull 0.347, MEGNet HSE gap 0.093.
  - A forged phase id returned a structured error, and a 6th EQE call was refused.
  - Defect found and fixed: `mace_stability` crashed on a hypothetical containing an element outside the plate system. It now adds that elemental reference and a lower-bound caveat. All tools now return structured errors instead of raising.
- 00:40 P3 unprocessable axis: 0 episodes with max EQE ≤ 0, 1 with a tie for best, 38 of 189 with max EQE < 0.01% (20 in the cohort). These form the low-signal stratum and are kept.
- 00:55 R3 load ladder.
  - Step 1: 1 FM cell, 21 s, $0.19. Step 2: 3 arms concurrently, 21-29 s, $0.12-0.25 per cell. Step 3 is the main run at 4 workers, declared here.
  - **Process observation.** In both pilot cells the FM arm made no FM calls and no XRD calls. It reasoned from chemistry knowledge (e.g. "AgSbO3 absorbs visible light") and spent its EQE budget directly. The prompt is not changed.
- 00:58 R4 grant verified from the model side (the init event): each arm's catalog matches its declaration, and 48 of 48 canaries are absent.
- 01:00 R5 gates armed with both controls: G1 EQE budget, G2 no-retry, G3 blind hash.
- 01:02 R8 symmetry table. The only differences are function count and tool descriptions, both ruled part of the intended treatment.
- 01:40 FM precompute finished for all 14 systems.
- I1 floors over 189 included episodes (`instrument/floors.csv`, code hash 4a2211d5):

  | Composition | Mean realized value |
  |---|---|
  | chance | 0.592 |
  | cls_gp (strongest) | 0.719 |
  | cls_xrd | 0.696 |
  | fm_prior | 0.715 |
  | fm_xrd | 0.699 |

- I2 channel count: the FM channels add no mechanical lift. fm_xrd vs cls_xrd is +0.003, and fm_prior vs cls_gp is -0.004.
- I4 construct validity: PASS on proxies. MACE puts 36 of 36 observed top-EQE crystalline phases within 50 meV of the hull. MEGNet gives a gap at or below the photon energy for 30 of 36. The FM prior's location error is 0.249 vs 0.285 for a uniform guess.
- P7: sigma_d = 0.110 at the cluster level, MDE 0.089 (t, df 13), below delta 0.17, so RESOLVABLE. The episode-level MDE is 0.081.
- P4: C1 rules PROCEED, with positive supply (14 clusters) as the binding axis.
- 02:10 Main run: 300/300 cells, 0 failures, $42.4 total (bare $11.0, classical $15.3, fm $16.1).
- 02:12 A2 blind hashes written and pushed before any label was opened (commit f948d13).
- 02:13 A3 scoring. Arm means: bare 0.695, classical 0.733, fm 0.709. Chance 0.587. Strongest floor (cls_gp) 0.740.
  - fm − classical: −0.024 per episode (naive CI [−0.077, +0.029]); +0.029 at cluster level (CI [−0.131, +0.189], p = 0.70). **NO CLAIM.**
  - The FM arm called an FM tool in 19 of 100 episodes. XRD was used in 20–35% of episodes, depending on arm.
  - Observed cluster MDE is 0.225, above delta, driven by La (one plate, +0.92 in a noise-level episode). The cluster test was underpowered post hoc. The prospective MDE of 0.089 underestimated the agent-arm variance.
  - Trace spot-check: no fabrication found. FM-using episodes show explicit cross-modal rejections, e.g. "predicted In11Sb3O24 did not form" and "La3Sb5O12's XRD did not match".
