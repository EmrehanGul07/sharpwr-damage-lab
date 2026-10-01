# Damage classification and ranking display · V5.62.0

Every one of the 115 ability records, 73 item records, 51 rune records and 27 champion-stat fields has a classification record. Classification coverage is not a claim of complete Wild Rift parity.

Damage resistance types (physical/magic/true) are independent of source tags. BasicAttack identifies basic damage; ActiveSpell identifies spell damage; AOE and Periodic describe supported area and repeated classifications. Proc, OnHit and Item remain separate attributes. Untagged/default damage is distinguished from unknown classification. Critical eligibility, lifesteal and on-hit triggering are separate nullable properties.

Source: https://wiki.leagueoflegends.com/en-us/Damage. The article itself warns that portions are outdated/confusing. Its taxonomy is used as vocabulary. WR ability templates provide the per-ability evidence; PC examples and coefficients are not copied into the WR model. No damage coefficients or user-confirmed item approximations were replaced.

## Runtime changes

- Hexoptics applies only to explicitly basic components. Ezreal Q and Miss Fortune Q positive damage are basic; their zero spell-effect instances are separately described. Senna Q remains area spell damage despite applying on-hit effects.
- Smolder initial Q is a spell/basic-effects hybrid according to WR notes. Its default true burn is not magnified. Confirmed on-hit eligibility now triggers the shared item kernel on Q; stack eligibility/phantom interactions remain provisional.
- Corki true attack conversion is basic in the WR template and is magnified. Samira melee magic bonus is default damage and is not magnified; R does not gain melee passive.
- Additional physical components for Vayne Q, Xayah W, Miss Fortune passive, Senna passive and Jhin fourth-shot missing-health proc no longer inherit the attack-base tag automatically.
- Ashe Q first-arrow/basic vs subsequent-default/proc is recorded separately. Five-arrow equal splitting is a provisional engine assumption for Magnification; it remains an in-game TODO.
- Items retain their independently sourced Item/OnHit origins. Their unknown BasicAttack memberships are excluded from Magnification pending WR verification. In particular, PC Kraken classification is not imported into WR.
- Fight logs expose classification and component metadata. These are audit records, not new mandatory user controls. Zero spell effects do not become extra damage or stack grants.

## Display

Full build Top 3 remains first. Each 1–4 item Top 10 stage now has responsive cards with icons, item names, TTK, DPS, cost and main stats. Detailed tables remain in expandable panels. Equal-TTK cheaper options receive `Equal TTK · lower-cost option`; the label does not assert equal uncapped damage.

The Kalista level-15 squishy comparison gives identical modeled TTK (0.5833244367s): Mortal Reminder build 17,700g vs LDR build 18,000g. This is the current model with unknown Kalista attack/projectile timing, not an in-game measurement.

## Remaining source gaps

77 ability records have a direct translated WR classification; 25 have no direct damage; Ashe Q has explicit mixed components; 12 remain unresolved. Unknown values are retained rather than filled from PC.

| Champion | Slot | Source label |
|---|---|---|
| Tristana | R | special |
| Ashe | P | no WR classification |
| Xayah | P | special |
| Yunara | P | no WR classification |
| Yunara | Q | no WR classification |
| Yunara | W | no WR classification |
| Yunara | E | no WR classification |
| Yunara | R | no WR classification |
| Jinx | Q | special |
| Jhin | W | special |
| Jhin | R | special |
| Senna | P | no WR classification |

All item BasicAttack/Proc memberships and damaging-rune source tags still need WR-specific evidence. The WR item module provides descriptions for 53 of 73 stored items; 20 are absent there. Item origin/on-hit applicability is recorded where explicit. Pure stats, resources, timing, geometry and modifiers are marked as such rather than arbitrarily given damage tags.

Unknown ApplyCritical/ApplyAttackRatio behavior is not inferred from tag names. Target invulnerability, shields, spell shields and incoming damage are not silently introduced into the stationary-target ranking. Existing WR mitigation/expected-crit formulas continue to use supplied build values.

## Validation

- Existing full regression: 149 tests passed.
- Classification tests: 7 passed, covering hybrid zero events, default burn, Samira E magic classification, selective Magnification and first-event Galeforce.
- Subsequent fight/optimizer/UI checks: 62 tests passed after on-hit routing update.
- Partial-card rendering checked with cached fight rows: 1–4 stage cards, 10 named icons, tie explanation, no Streamlit exception.

The source snapshots retain classification fields and short evidence excerpts, not full wiki articles. `scripts/build_damage_classification.py` rebuilds metadata without importing numerical ratios.
