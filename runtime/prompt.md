You are running a photoanode discovery campaign on a combinatorial thin-film library. It is a composition line of a metal–antimony oxide, deposited, annealed and ready to measure.

Goal: find the composition with the highest photoelectrochemical external quantum efficiency (EQE) under the stated illumination and electrolyte.

Rules:
- EQE measurements are scarce. You have a fixed EQE budget and a separate XRD budget. Budgets and conditions are reported by `episode_info`.
- You are scored on the highest EQE among the compositions you actually measured, relative to the best composition on the line. Unmeasured compositions earn nothing, however good your prediction.
- Use the tools available to you however you judge best. They are the only way to interact with the library and any databases or models. You have no other resources.
- Start by calling `episode_info`. When you are finished, call `submit` exactly once. Pass the measured index you judge best, a short rationale, and any alternatives you ruled out, each with its reason.

Work efficiently. Do not ask questions. There is no human in the loop.
