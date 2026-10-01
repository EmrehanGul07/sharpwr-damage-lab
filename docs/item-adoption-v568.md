# Item tier cards and adoption screen — v5.68.0

The selected champion's Top 10 item cards appear directly below the full-build Top 3, with icons and situational notes. Scores sum full-build reciprocal rank with weight 5 and the one-to-four-item reciprocal ranks with weight 1/stage. These recommendations reflect the selected target and completed bounded search; notes are not unconditional must-buy claims.

Item Value now leads with a persisted, reproducible level-15 adoption screen across all 23 champions and three existing target profiles. It tests all 36 single items and legal item additions to each champion/target's three best single-item anchors. No boots or runes; expected crit; fully stacked Yun Tal. Total: 19,522 fight simulations.

Each candidate is scored by mean relative DPS gain over its empty and eligible one-item anchor builds. An item counts once per champion if it is Top 5 on any target. Ranking prioritizes distinct champion coverage, then Top-5 target appearances, then mean gain. Every item remains visible in the table. The JSON includes per-champion/target results and an item-stat fingerprint; regenerate using scripts/build_item_adoption.py after item/engine updates.

This is a small offensive single/pair screen, not full-build optimization, real-match popularity, defensive value or gold efficiency. The existing single-item gold/value controls remain below it. Yunara's unknown mana/movement/range fallback remains provisional. The screen's fully stacked Yun Tal assumption must be considered when discussing early purchases.
