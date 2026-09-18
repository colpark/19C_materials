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
