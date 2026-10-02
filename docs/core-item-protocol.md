# Champion core items — V5.82.1

Core candidates are selected by a separate constrained search, not by filtering an existing unrestricted winner. Lord Dominik's Regards, Serylda's Grudge, Mortal Reminder, Infinity Edge and Terminus are removed from the candidate pool before any build is evaluated. Normal Tier List searches keep their existing item pool.

The scanner calls the same `search_builds` used by Tier List, retaining its defaults: beam width 80, 40 refined finalists, all Tier3 boot choices, rotation/movement/AA-weaving/ultimate timing refinement and the same expected-damage engine. It is a bounded search, not exhaustive optimization.

Stages use item budgets 5→1, 7→1, 9→2, 11→3, 13→4, 15→5, plus boots. Each stage is evaluated against all three target profiles. Starting state matches the UI defaults: Standard Fight, Yun Tal stage progression, zero prior Collector executes, Smolder zero Dragon stacks, Senna 40 Mist; engine default runes. Muramana is unavailable below level 11.

For each eligible stage/target cell, take the final Top3 builds and weight their item presence by 1, 1/2 and 1/3, normalized by the available weights. The item score is the mean across its eligible cells; every stage/target has equal weight. Muramana is scored across nine late-game cells rather than penalized for the nine cells where it is unavailable. Other items have eighteen eligible cells.

Highest score selects the core candidate. Exact score ties display at most two icons. Winner coverage breaks ordering ties. The data retains Top3 commonality, winner coverage and actual build/policy details for review. An item does not need to occur in literally every build to be shown; the label identifies the most consistent constrained-search candidate, not a mandatory purchase.

The shared champion profile displays CORE ITEM, icon and name in Tier List, Build Lab and Item Value. Saved results are checked against a source fingerprint; stale or incomplete results are not displayed as confirmed core items. Champion changes read saved results and do not start a new fight search.

Cache identity covers engine rules, champion/item/ability/timing datasets, target profiles and core-search protocol. Pure UI styling changes do not invalidate numerical results.

Fingerprint schema 3 hashes the exact source segments of selected model declarations rather than `ast.dump`. This avoids Python-version-specific AST serialization invalidating unchanged saved results on Streamlit Cloud. Numerical engine/search rules and all 414 results are unchanged.
