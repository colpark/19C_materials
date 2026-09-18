# R0 replay regression report

Verdicts written from skill text only, hashed before scoring (`verdict_hashes.txt`), not edited after scoring.
`RULINGS_SEALED.csv` opened only after both scores were saved.

## Polarity scores (replay.py score)

| Set | must_fire | must_not_fire | validator-only |
|---|---|---|---|
| development (26) | 17 of 17 | 9 of 9 | 0 |
| sealed (12) | 8 of 8 | 4 of 4 | 0 |

## Caveat: the polarity score is not blind

`replay.py emit` prints `polarity=must_fire|must_not_fire` next to every case, so the verdict under test (`fired`) was visible while writing it. A 38 of 38 polarity result therefore shows internal consistency, not discrimination. `score` also never compares the ruling text. The ruling comparison below is the part that actually tests something. Recommendation: remove polarity from `emit` output.

## Unearned passes

The scorer reports none, because every verdict was marked `via: stage`. One is doubtful:
- **K24 (D5)**: the D5 brief has no refusal of its own for a slot sourced as "standard". The catch comes from D4's refusal, global refusal 15 and manifest validation. D5 only implies it ("ratification is accepting a derivation already on the page"). A strict reading makes this validator-level, so it is unearned for D5. Suggested fix: give D5 an explicit refusal to ratify a slot whose provenance does not resolve.

## Ruling divergences vs sealed rulings (polarity correct in all of them)

| Case | My ruling | Sealed ruling | Why I misruled |
|---|---|---|---|
| K06 (P2) | CLOSE, or escalate with the headroom stated | Do not close. Move the headline off this metric, split the floor into classical-only and instrument-mechanical, rebuild any leaked input | I read about 89 to 92 percent as "the floor takes the ceiling" under P2's close rule. The brief gives no threshold, and the record treated 92 percent as a reframe. **Substantive: wrong disposition.** |
| K02 (P3) | Refuse the raw counts. Motif-family count UNDEMONSTRATED | 2 validated motif families | The case text gives no family count that I could see, so I did not produce the number. Same refusal, but the required answer is missing. |
| K03 (P3) | Effective 8 constructs, 0 negatives, "likely binds" | Close on supply and on label independence | Too hedged. I did not close outright and did not name co-deposition as occupancy rather than preference. |
| K04 (P3) | Split integrity FAIL. Re-split or audit | FAIL. Report the straddle count and escalate above the benchmark question | Left out the escalation. |
| K09 (I4) | Fails construct validity. Leave unmounted | Also rename it to what it measures, bar it from scoring, and close the dependent workflow with the null preregistered | Left out the downstream closure. |
| K11 (R5) | Refuse the invented threshold. Run UNDEMONSTRATED | Disposition "unreadable". Replace the safety gate with a validity gate on measurement representativeness | Left out the replacement validity gate. |
| N03 (R7) | Cosmetic. Keep and score the cells | Cosmetic. Normalise with must-fire controls, recover the cells from disk, and disclose the recovery as post-hoc | Left out the normalisation controls and the post-hoc disclosure (A4 rule). |

Minor omissions, core agreeing: K13 (disclose narrowly when arms were filtered at the model boundary), N01 (record the duty cycle for pricing), N04 (pin the revision on the card).
