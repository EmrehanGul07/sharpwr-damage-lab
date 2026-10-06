# Champion build results — V7.1.0

`scripts/build_core_items.py` saves four results per champion in `data/champion-core-items.json`, all with the champion's default rune page (`data/default-rune-pages.json`; stacking runes fill with level, `sharpwr/rune_pages.py`):

1. **Core-item search (`cells`).** A separate constrained search, not a filter of an unrestricted winner: Lord Dominik's Regards, Serylda's Grudge, Mortal Reminder, Infinity Edge and Terminus are removed from the candidate pool before any build is evaluated. Its Top 3 builds rank the core items.
2. **Top builds (`top`).** The same search with every item. These are the builds the apps show.
3. **Build styles (`styles`).** The full-pool search with a style's items required (`search_builds(required=...)`): SharpWR's core item pick (`data/editor-core-items.json`) and the editor's styles (`data/build-styles.json`). A style's items are a build path: a build with N items holds the first N; Muramana stands for Manamune below level 11. A style may set another keystone.
4. **Keystone check (`keystone_check`).** At levels 13 and 15 against each target, the #1 Top build replayed with every keystone the fight engines model, the rest of the page unchanged. It reports alternatives; it does not change the page.

Every search calls the same `search_builds` as the Tier List with its defaults: beam width 80, 40 refined finalists, all Tier 3 boots, rotation/movement/AA-weaving/ultimate timing refinement and the same expected-damage engine. It is a bounded search, not exhaustive optimization.

Stages use item budgets 5→1, 7→1, 9→2, 11→3, 13→4, 15→5, plus boots, each against all three target profiles (`core_items.matchup`). Starting state: Standard Fight, Yun Tal stage progression, zero prior Collector executes, Smolder zero Dragon stacks, Senna 40 Mist, the champion's rune page. Muramana is unavailable below level 11.

For each eligible core-search cell, take the final Top 3 builds and weight their item presence by 1, 1/2 and 1/3, normalized by the available weights. The item score is the mean across its eligible cells; every stage/target has equal weight. Muramana is scored across nine late-game cells rather than penalized for the nine cells where it is unavailable. Other items have eighteen eligible cells.

Highest score selects the engine's core item. Exact score ties display at most two icons. Winner coverage breaks ordering ties. An item does not need to occur in literally every build to be shown; the label identifies the most consistent constrained-search candidate, not a mandatory purchase. Where SharpWR has its own pick, the apps show that pick with its reason first and the engine's core beside it (`core_items.shown_core`); the pick's style shows how its builds compare with the Top builds.

The web champion profile shows CORE ITEM, icon and name in Tier List, Build Lab and Item Value. The mobile app shows the core item, the rune page with the keystone check, every cell's Top 3 builds, the build styles and the item ranking from `app-data/database.json` ([app-data.md](app-data.md)). Saved results are checked against a source fingerprint and the champion's current rune page; stale or incomplete results are not displayed. Champion changes read saved results and do not start a new fight search.

Cache identity covers engine rules, champion/item/ability/timing datasets, target profiles, the rune page code and the protocol (`EXCLUDED`, `BUDGETS`, `KEYSTONE_CHECK_LEVELS`, `available`, `rank_core`, `matchup`, `rune_page`, `cell_evaluator`, `style_items`). A champion's rune page is checked per champion, so editing one page invalidates only that champion. Styles are matched by their definition (`key`: items and keystone); a changed or new style shows as pending until computed. Pure UI styling changes do not invalidate numerical results.

The fingerprint (seed `core-protocol-v5-runes-top-styles`) hashes the full source of every engine module in the `sharpwr/` package plus the selected protocol declarations in `sharpwr/core_items.py`. Earlier seeds covered the core search only (`v4`), the root-level module paths, or selected source segments of `streamlit_app.py`. Hashing source text rather than `ast.dump` keeps the fingerprint independent of the Python version.

The work is split into one shard per champion (`--work DIR`, resumable; several processes can share the champions), then `--merge` writes the data file. `scripts/verify_core_rows.py` replays every saved finalist of all three sections under its exact policy.

## 7.1.0 recompute

Everything was recalculated, not migrated: default rune pages now enter every fight, Top builds use every item, build styles and the keystone check are new, and Galeforce's Cloudburst follows the Wild Rift tooltip (40–125 by level plus 35% bonus AD physical damage, 60 s cooldown; previously 40–120 plus 45%, 50 s).

The run covered all 23 champions: 1,530 bounded searches (core, Top builds and 40 build styles over 18 matchups each) and 13.1 million fight simulations. All 4,590 saved finalists replay under their recorded policies with `scripts/verify_core_rows.py`.

Results worth knowing:

- Engine core items: Yun Tal Wildarrows leads for 11 champions, Muramana for 6 (Ezreal, Corki, Kog'Maw, Samira, Smolder, Jhin), The Collector for Lucian and Miss Fortune, Guinsoo's Rageblade for Kai'Sa and Yunara, Nashor's Tooth for Varus and Kraken Slayer for Senna.
- Keystone check at level 15: Empowerment beats the default page's keystone against bruisers or tanks for 13 champions, most clearly Senna against tanks (10.98 s against 12.40 s with Fleet Footwork). Tristana's Empowerment build style is as fast as or faster than her Lethal Tempo Top build in all 18 matchups.
- Build styles that keep up with the Top builds from level 11: The Collector for Jhin, Draven, Samira and Miss Fortune; Yun Tal Wildarrows for Ashe, Jinx, Sivir and Yunara.

## 7.0.9 cache migration

The search's build summary (AD, AP, Crit %, AH, Starting AS, AS over cap, gold, mana, movement speed) moved into `sharpwr/build_stats.py`, which the mobile app's build calculator also ports, and that module joined the fingerprint. It is bit-for-bit identical to the replaced code on 21,242 builds. Against baseline commit `ded24d0`, all 1,242 retained finalists replay with identical hit ledgers, damage, health and TTK, and the 3,312-case integrity matrix is identical apart from its run time. Saved rows' Starting AS can differ from `build_stats` in the last bit, from an older summation order; tests compare them to 1e-9.

## 7.0.5 cache migration

The remaining engine modules moved from the repository root into `sharpwr/` and were Black-formatted; each module's AST is unchanged by formatting. Against baseline commit `c833ad3`, all 1,242 retained finalists replay with identical hit ledgers, damage, health and TTK, and the 3,312-case integrity matrix is identical. The stored fingerprint advanced with this evidence.

## 7.0.4 cache migration

The shared AA engine moved from `streamlit_app.py` into the `sharpwr/` package unchanged apart from public names and docstrings. Against baseline commit `c2762f3`, all 1,242 retained finalists replay with identical hit ledgers, damage, health and TTK, and the 3,312-case integrity matrix is identical. The stored fingerprint was advanced with this evidence (`verification` in `data/champion-core-items.json`).

## V5.87.0 cache migration

The cache now records a verified migration from baseline commit `6f31574`. All 414 cells and 1,242 retained finalists were replayed under their exact selected policy. Baseline and candidate hit timestamps/actions/damage, total damage, health and TTK are identical; every replay also matches its original saved row. Default numerical rules are unchanged by non-default rune/UI wiring and input validation. The source fingerprint was advanced with this evidence, rather than skipping stale-cache checks. This preserves the original bounded search results; it does not claim a fresh search or global optimality. See `verification` in `data/champion-core-items.json` and `scripts/verify_core_rows.py`.
