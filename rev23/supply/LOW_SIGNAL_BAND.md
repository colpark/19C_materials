# Low-signal band: declared before any pooled axis count (PI, 2026-09-19)

For each episode:
- **Noise floor:** the 90th percentile of |merit| over that episode's negative merit points.
- **Low-signal flag:** max merit < 3 × noise floor.
- **No flag** if the episode has fewer than 4 negative points. The noise floor is then undefined, and the episode is recorded as `no_flag_insufficient_negatives`.

Flagged episodes form a stratum. They are never filtered. Base (EQE) and pooled (photocurrent) episodes use the same rule on their own merit units. The rule is scale-free within an episode.

This replaces the run-1 low-signal definition (max EQE < 0.01%) for this pass. The old definition is kept as a secondary column for comparison.
