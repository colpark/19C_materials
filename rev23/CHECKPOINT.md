# Rev 2.3 autonomous pass: checkpoint

- **Restart point:** O1 on the pooled P7 provisional pass (`rev21/pool/power_provisional_fm_xrd.json`, RESOLVABLE, MDE 0.163).
- **Done:**
  - Skill vendored; audit shows 48 cases.
  - Router settled by replaying decisions 001–003 through rev 2.3: `rev23/router/decision_R00*.json`. Envelope reconciled to measured spend; C1 depth 2 of 3.
  - D5 standing rulings recorded: `rev23/D5_amendments.json`.
- **Next:** main run in progress (rev23_main, 468 cells), then A2 blind hash, A3 score, A4 report. Restart: re-run run_batch with the same tag; existing cells are skipped.
