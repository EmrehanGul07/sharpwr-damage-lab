# Offline engine validation — V5.71.0 / 2026-10-02

## Sonuç

190/190 automated tests passed in 88.398 seconds, including Streamlit UI, replay, 23 marksman adapters, item integration and damage classification. A focused 95-test engine run also passed in 2.603 seconds. Passing these checks establishes consistency with the implemented rules, not complete Wild Rift parity.

## Database → fight doğrulaması

Added database-to-engine regressions at levels 1 and 15 for all 23 champions: positive mana/MS/range, bounded resources and health, finite damage, attacks within range, launch/impact order and exact damage ledgers. Existing suites cover mana depletion, cooldown/haste, channel and AA restrictions, projectile scheduling, stacks and deterministic replays.

Yunara observed levels 1/3/5/8/10/13/15 use exact displayed HP/mana/armor/MR values; other levels interpolate. Base MS 335 and attack range 575 are user-verified. Level 15 base mana 807 plus Muramana mana 1200 yields 2007 maximum mana. Item Awe and Shock receive this total; ability spending is logged. Verified AA travel at range 575 is 0.23 seconds after windup with the authorized PC projectile proxy 2500. Existing AD/AS formulas remain untouched.

Removed stale runtime claim that Yunara mana/MS/range are entirely unknown. Database Explorer now identifies manual verification and PC timing proxies correctly, and displays the observation table. Unknown regeneration remains null in the database and is conservatively zero in the engine; regeneration units and growth remain TODO.

## Item Value refresh

Recomputed all 18 affected Yunara cells (six levels × three targets). Preserved the 396 unaffected cells for the other 22 champions; their inputs and combat rules did not change. Aggregate scores were rebuilt from all 414 cells. Retained dataset evaluation count: 272764 (this is not exhaustive enumeration). Existing single-item enumeration and diverse 12-build progressive beam with skill-order refinement remain unchanged. Muramana remains excluded below level 11. Budgets: 5→1, 7→1, 9→2, 11→3, 13→4, 15→5.

Overall Top 10 ordering did not change: Yun Tal Wildarrows, Infinity Edge, Lord Dominik’s Regards, Guinsoo’s Rageblade, Kraken Slayer, Blade of the Ruined King, The Collector, Galeforce, Essence Reaver, Duskblade of Draktharr. Adoption counts denote appearance in retained Top 10 builds, not necessarily rank-one winners.

The screen generator accepts --champion NAME --refresh to redo affected champion cells without discarding other results. Corrected relative AppTest paths for current Streamlit and initialize the runtime before patching search in the bounded UI test.

## Remaining verification

See [ingame-test-todo.md](ingame-test-todo.md). PC timing remains a proxy. Yunara intermediate stats, regeneration and W linger contact/tick are unresolved. Other item/kit eligibility and movement assumptions are not closed merely by these automated tests. No new WR damage coefficients or timing constants were invented.
