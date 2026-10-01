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

AP, AD, crit, haste and penetration are assembled from the selected items and enter the existing champion ability formulas. Dynamic Rageblade, Phantom Dancer, Yun Tal and Fiendhunter AS also feed the attack clock. The normal AS cap is 3.0; Zeri uses her locked 1.5 cap and excess-AS-to-AD conversion, with the existing provisional ultimate exception. An item is not deleted merely because AS overflows: its AD/AP, crit, haste and procs can still contribute. Jhin retains fixed natural AS and reloads; WR 7.3 Whisper AD conversion is now applied once to permanent and transient AS/crit/AD, without speeding up his fixed attack clock.

Each final build displays AD, AP, crit, haste, starting AS and starting AS above cap. This number is a starting-state diagnostic, not a measurement of every future buff window. The best-build contribution table removes each item and reruns the fight, including a new rotation search. DPS contribution and TTK increase show the conditional value of the entire item; overlapping contributions are not additive. It also accounts for changes in ability evolution thresholds.

The simulation uses expected damage; thresholds and ability decisions follow expected HP. It does not enumerate random fight outcomes. No keystone or rune damage is included in this item-only benchmark, so results remain comparable across item builds. Existing champion mechanics limitations remain documented in all-marksman-fight-engine.md and in the result's unverified-mechanics expander.

## UI and persistence

Results persist through widget reruns. Changing champion, level, target, scenario or progression hides stale rankings until recalculation. Only three full builds are displayed; there is no expanded full-build Top 10 table. The contribution table is collapsed by default. Galeforce uses an independent fight action when unlocked and repeats 50s after actual use. It does not inject active damage into AA. Galeforce now dashes toward the target by up to 325 units and damages only within 600 units after the dash. First Contact prepares Energized; Spellblade requires an actual skill cast, and ultimates require their real kit resources.

## Validation

Coverage includes all 23 champion evaluators, AP ability scaling, Zeri cap diagnostics, mutually exclusive penetration/mana items, deduplication, cache reuse, stage cardinalities and a real bounded item/boot/rotation search in Streamlit. An Ezreal vs level-15 Ornn full-pool benchmark tested 5,254 fights in approximately 50 seconds using a smaller 20-candidate beam; a Nashor's Tooth build entered its final three. This is test evidence for AP participation, not a universal build recommendation.

Final validation: 127/127 automated tests passed in 88.226 seconds, including all 23 champions, the item optimizer, ability-aware UI and offensive-active cooldown regression.

V5.60.3: highest-percent Spellblade wins; Fiendhunter pre-cast defaults removed; recorded champion mana/growth/regen feeds the kernel. WR7.3 Muramana max-mana Shock remains unchanged in principle; actual skill consumption/refund/regen is tracked and skill-on-hit callbacks do not duplicate AA Shock.

V5.60.4: only one Spellblade item is legal (ER/Trinity/Iceborn/Sheen). Full and partial build search exclude multiple Spellblade items.

## V5.61.0 — wider search and final validation

All legal singles and pairs are screened; promising partial builds receive six-priority rotation replays before advancing the beam. Stages 3–5 retain up to 80 candidates instead of 40. Half the slots retain performance leaders; remaining slots round-robin the strongest AP, crit, on-hit, penetration, exact archetype and pairwise hybrid candidates, then backfill. Terminus is classified as penetration despite its penetration being earned in combat. No AP/crit/on-hit/penetration class is discarded by a static champion stereotype. Exclusive purchase rules still apply.

Up to 40 full-build finalists instead of 20 receive deeper replay. Replay compares six basic-skill priorities, E enabled/skipped, two R timings and skill-first/AA-weaving orders. At the default movement policy, all six priorities are tested; the champion's default priority is also compared at three movement envelopes (ready-skill envelope, AA envelope, close envelope). Samira retains her melee approach; Jinx also compares both weapons. This is 64 policy combinations per general champion build, 48 for Samira, 192 for Xayah (recall at 1/3/5 feathers), and 128 for Jinx. Top3 is reranked from these refined results, never merely copied from preliminary screening. The winning policy is displayed next to each result.

Results remain best **tested** builds: beam pruning and the bounded policy grid are not an exhaustive proof of global optimum. Rankings can still change when unresolved collision/windup/kit assumptions are measured. Target never attacks and approved RFC/Stormrazor/Statikk/YunTal approximations are unchanged.

Jhin Whisper now uses `AD_before_passive × (1 + 0.30 bonus_AS + 0.40 crit + 0.03 level)`, sourced from Riot WR 7.3 and checked against 7.3a. Dynamic item AS and crit change AD; they do not increase the attack clock. Displayed starting AD follows the same formula. Xayah E now sums every recalled feather at 100%, 90%, 80%, …, with a 10% floor, using the WR template's raw formula. User-tested E base/AD/crit coefficients are preserved. Xayah uses aligned radial movement for the stationary target benchmark; lateral path collision geometry remains a TODO, not a claim that arbitrary feathers always hit.

Source records: `data/verified-ranking-formulas.json`. Regression checks cover class preservation, stronger refinement, conversion units/one-time application, feather floor and motion affecting the trace.

Xayah Q now plants and damages with both daggers, stored passive attacks expire at 7.5s, and manual E accepts one feather. Automatic finalists compare recall thresholds of 1/3/5 feathers. Jhin fourth-AA missing-health damage follows the WR template level sequence 11% through 25%; the user-confirmed 11% level-one value is preserved.

Varus Q rank 2–4 raw damage components now match the existing fight adapter using sourced 110/120/130/140% minimum and 165/180/195/210% maximum scaling. The user bonus-AD basis is preserved despite wiki total-AD wording; the scope conflict remains an explicit in-game TODO.
