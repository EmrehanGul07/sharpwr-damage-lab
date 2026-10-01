# Shared AA engine regression fixes — 1 October 2026

Item Tier List, Item Value, Build Lab's rune combat loop and its item-only max-hit estimate now consume `_combat_hits`. Rune events are applied on top of the item result and feed their live target HP back into the next attack.

Fixed Fiendhunter ultimate first-three-hit behavior, Nashor scaling from total item AP, magic penetration from boots and Terminus, and differing C44 / Lord Dominik / Iceborn / Energized / Spellblade calculations between tabs. Energized recharge remains an assumed benchmark cadence; Spellblade-ready permits recurring casts every 1.5 seconds. These scenario assumptions are visible in Build Lab; actual skill damage remains TODO.

The engine rejects more than five items, duplicates, unknown items and boots in item slots. Unknown boots are rejected. No unverified mutually exclusive item purchase rules were invented. Spellblade stacking and purchase restrictions still need source verification.

The attack limit produces a NOT KILLED label and infinite TTK in benchmark rows; Build Lab displays an explicit warning and unavailable TTK. Negative resistance is supported without allowing penetration to make positive resistance negative.

Cross-tab widget state is retained through item/rune early reruns. Item removal no longer resets Item Value's champion selection.

Validation: Python compile; 10 regression tests (8 engine + 2 interface) including single/multi parity for all 36 items with effects on/off, 2,484 champion/item/level smoke combinations, invalid-build rejection and 500-attack timeout. Streamlit AppTest covers independent champion/level/target state, remove/equip, Build Lab calculation, tier calculation and Database search and all 12 keystone calculation paths. Existing game-measurement TODOs remain unresolved. Live in-game verification was not performed.

Run: `python -m unittest discover -s tests -v`.
