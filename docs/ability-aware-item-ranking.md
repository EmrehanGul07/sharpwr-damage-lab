# Ability-aware item ranking — V5.60

Item Tier List now ranks builds through the same champion fight replay used by Skill Lab, including AA, abilities, expected critical strikes, passive/on-hit effects, timed cooldowns, mana, movement, ammo and channels. The previous AA-only tier calculation is removed. Jhin is included with his provisional four-shot/reload adapter.

The results appear in this order:

1. Full build: three results only, each five completed items plus one Tier 3 boot.
2. One-item Top 10.
3. Two-item Top 10.
4. Three-item Top 10.
5. Four-item Top 10.

Partial stages do not include boots. Full builds compare all seven known Tier 3 boots. The final result is specific to the selected champion, level, target, starting stacks and combat scenario; it is not a universal recommendation across matchups. Gold breaks otherwise equal TTK ties. Survivors rank after defeated targets, using remaining damage. No incoming damage, defensive utility, allied effects or multi-target value is scored.

## Search method

The database currently contains 36 completed items, including its recorded AP items. Every legal single and pair is tested. Three through five item stages expand the best 40 prior-stage candidates. Every screened build uses real AA + ability fights, not an AA-only proxy. Early screening uses the champion's default basic priority with E enabled/disabled; Jinx compares minigun and rockets. Top 20 partial-stage candidates are reranked with six basic priorities. Top 40 five-item candidates are each tested with all Tier 3 boots, then the top 20 item/boot finalists are reranked with all six priorities and E enabled/disabled. The top three are returned.

This search is pruned and cannot prove the global optimum among every possible item/boot/rotation combination. Missing item definitions also cannot enter the search. The UI says “best tested builds” and exposes the tested simulation count. It does not silently promise a universal exact ideal build.

## Champion scaling and caps

AP, AD, crit, haste and penetration are assembled from the selected items and enter the existing champion ability formulas. Dynamic Rageblade, Phantom Dancer, Yun Tal and Fiendhunter AS also feed the attack clock. The normal AS cap is 3.0; Zeri uses her locked 1.5 cap and excess-AS-to-AD conversion, with the existing provisional ultimate exception. An item is not deleted merely because AS overflows: its AD/AP, crit, haste and procs can still contribute. Jhin retains fixed natural AS and reloads; his missing AS/crit-to-AD coefficients remain explicitly unresolved and can change his ranking.

Each final build displays AD, AP, crit, haste, starting AS and starting AS above cap. This number is a starting-state diagnostic, not a measurement of every future buff window. The best-build contribution table removes each item and reruns the fight, including a new rotation search. DPS contribution and TTK increase show the conditional value of the entire item; overlapping contributions are not additive. It also accounts for changes in ability evolution thresholds.

The simulation uses expected damage; thresholds and ability decisions follow expected HP. It does not enumerate random fight outcomes. No keystone or rune damage is included in this item-only benchmark, so results remain comparable across item builds. Existing champion mechanics limitations remain documented in all-marksman-fight-engine.md and in the result's unverified-mechanics expander.

## UI and persistence

Results persist through widget reruns. Changing champion, level, target, scenario or progression hides stale rankings until recalculation. Only three full builds are displayed; there is no expanded full-build Top 10 table. The contribution table is collapsed by default. Galeforce uses an independent fight action when unlocked and repeats 50s after actual use. It does not inject active damage into AA. Galeforce now dashes toward the target by up to 325 units and damages only within 600 units after the dash. First Contact prepares Energized; Spellblade requires an actual skill cast, and ultimates require their real kit resources.

## Validation

Coverage includes all 23 champion evaluators, AP ability scaling, Zeri cap diagnostics, mutually exclusive penetration/mana items, deduplication, cache reuse, stage cardinalities and a real bounded item/boot/rotation search in Streamlit. An Ezreal vs level-15 Ornn full-pool benchmark tested 5,254 fights in approximately 50 seconds using a smaller 20-candidate beam; a Nashor's Tooth build entered its final three. This is test evidence for AP participation, not a universal build recommendation.

Final validation: 127/127 automated tests passed in 88.226 seconds, including all 23 champions, the item optimizer, ability-aware UI and offensive-active cooldown regression.

V5.60.3: highest-percent Spellblade wins; Fiendhunter pre-cast defaults removed; recorded champion mana/growth/regen feeds the kernel. WR7.3 Muramana max-mana Shock remains unchanged in principle; actual skill consumption/refund/regen is tracked and skill-on-hit callbacks do not duplicate AA Shock.
