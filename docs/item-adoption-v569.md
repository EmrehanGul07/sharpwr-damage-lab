# Stage-budget item adoption — v5.69.0

All 23 ADCs are tested on three existing target profiles at levels 5, 7, 9, 11, 13 and 15. Exact item budgets are 1, 1, 2, 3, 4 and 5. Level 7's unspecified quantity is interpreted as one item. Muramana is banned from every candidate below level 11, including later-stage seeds. Boots and runes are excluded.

All singles are evaluated at levels 5 and 7. Subsequent stages grow the previous stage's diverse 12-build shortlist, enumerate legal additions and compare 12 finalists over skill orders. This is a bounded small-screen search, not exhaustive optimization. Champion ranks, level stats, target stats and cooldowns follow each level. Yun Tal starts at 0 stacks at level 5, 62 at level 7, and 125 at level 9 onward; this is a progression assumption. Yunara unknown core-stat fallbacks remain provisional.

The overall item score is reciprocal-rank appearance share in retained Top-10 builds, divided by build item count, with equal weight per level and per target and per champion. Each cell distributes the same total score despite different item budgets. Distinct champion count remains visible, but is not used as the sole sort key: appearing once at level 15 must not overpower consistency across stages. The screen offers an All stages view and individual level views, plus per-champion/level/target build tables.

Regenerate using scripts/build_item_adoption.py. Its checkpoint resumes completed cells with the same item fingerprint; delete the checkpoint before changing engine policy or stage budget. The exported JSON stores compact result rows. This screen evaluates offense, not real-match pick rates, gold budgets, incoming damage or defensive utility. Items are complete at every stage except the explicit Muramana restriction; level 5 can therefore include other late-game items under this simplified user-specified item-count model.

Validation: all 414 cells complete; 272,772 recorded simulation evaluations. Seven ranking/dataset tests and four replay tests passed. Budget checks and early Muramana exclusion cover every retained build.
UI smoke checks passed: startup, overall ranking, level selection, single-item level-5 table and zero early Muramana score.
