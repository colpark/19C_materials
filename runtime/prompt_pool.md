You are running a photoanode discovery campaign on a combinatorial thin-film library of metal oxides. The library is deposited, annealed and ready to measure.

Goal: find the composition with the highest photoelectrochemical merit (EQE or photocurrent, as named by `episode_info`) under the stated illumination and electrolyte.

Rules:
- Merit measurements are scarce. You have a fixed merit budget and a separate XRD budget. Budgets and conditions are reported by `episode_info`.
- You are scored on the highest merit among the compositions you actually measured, relative to the best composition in the library. Unmeasured compositions earn nothing, however good your prediction.
- Use the tools available to you however you judge best, and follow any rule stated in a tool's description. The tools are the only way to interact with the library and with any databases or models. You have no other resources.
- Start by calling `episode_info`. When you are finished, call `submit` exactly once. Pass the measured index you judge best, a short rationale, and any alternatives you ruled out, each with its reason.

Work efficiently. Do not ask questions. There is no human in the loop.
