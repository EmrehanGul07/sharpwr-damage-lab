# Champion core items — V5.82.1

Core candidates are selected by a separate constrained search, not by filtering an existing unrestricted winner. Lord Dominik's Regards, Serylda's Grudge, Mortal Reminder, Infinity Edge and Terminus are removed from the candidate pool before any build is evaluated. Normal Tier List searches keep their existing item pool.

The scanner calls the same `search_builds` used by Tier List, retaining its defaults: beam width 80, 40 refined finalists, all Tier3 boot choices, rotation/movement/AA-weaving/ultimate timing refinement and the same expected-damage engine. It is a bounded search, not exhaustive optimization.

Stages use item budgets 5→1, 7→1, 9→2, 11→3, 13→4, 15→5, plus boots. Each stage is evaluated against all three target profiles. Starting state matches the UI defaults: Standard Fight, Yun Tal stage progression, zero prior Collector executes, Smolder zero Dragon stacks, Senna 40 Mist; engine default runes. Muramana is unavailable below level 11.

For each eligible stage/target cell, take the final Top3 builds and weight their item presence by 1, 1/2 and 1/3, normalized by the available weights. The item score is the mean across its eligible cells; every stage/target has equal weight. Muramana is scored across nine late-game cells rather than penalized for the nine cells where it is unavailable. Other items have eighteen eligible cells.

Highest score selects the core candidate. Exact score ties display at most two icons. Winner coverage breaks ordering ties. The data retains Top3 commonality, winner coverage and actual build/policy details for review. An item does not need to occur in literally every build to be shown; the label identifies the most consistent constrained-search candidate, not a mandatory purchase.

The shared champion profile displays CORE ITEM, icon and name in Tier List, Build Lab and Item Value. Saved results are checked against a source fingerprint; stale or incomplete results are not displayed as confirmed core items. Champion changes read saved results and do not start a new fight search.

Cache identity covers engine rules, champion/item/ability/timing datasets, target profiles and core-search protocol. Pure UI styling changes do not invalidate numerical results.

Fingerprint schema 5 hashes the full source of every engine module in the `sharpwr/` package plus the selected core-protocol declarations in `sharpwr/core_items.py`. Schema 4 used the earlier root-level module paths; schema 3 hashed selected source segments of `streamlit_app.py`. Hashing source text rather than `ast.dump` keeps the fingerprint independent of the Python version.

## 7.0.5 cache migration

The remaining engine modules moved from the repository root into `sharpwr/` and were Black-formatted; each module's AST is unchanged by formatting. Against baseline commit `c833ad3`, all 1,242 retained finalists replay with identical hit ledgers, damage, health and TTK, and the 3,312-case integrity matrix is identical. The stored fingerprint advanced with this evidence.

## 7.0.4 cache migration

The shared AA engine moved from `streamlit_app.py` into the `sharpwr/` package unchanged apart from public names and docstrings. Against baseline commit `c2762f3`, all 1,242 retained finalists replay with identical hit ledgers, damage, health and TTK, and the 3,312-case integrity matrix is identical. The stored fingerprint was advanced with this evidence (`verification` in `data/champion-core-items.json`).

## V5.87.0 cache migration

The cache now records a verified migration from baseline commit `6f31574`. All 414 cells and 1,242 retained finalists were replayed under their exact selected policy. Baseline and candidate hit timestamps/actions/damage, total damage, health and TTK are identical; every replay also matches its original saved row. Default numerical rules are unchanged by non-default rune/UI wiring and input validation. The source fingerprint was advanced with this evidence, rather than skipping stale-cache checks. This preserves the original bounded search results; it does not claim a fresh search or global optimality. See `verification` in `data/champion-core-items.json` and `scripts/verify_core_rows.py`.
