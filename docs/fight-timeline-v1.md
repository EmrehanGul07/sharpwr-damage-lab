# Samira fight engine V5.48

User-selected instant resolution: every skill applies damage at its button timestamp. No cast, projectile, dash or channel delay. W resolves two hits together, R ten individual crit rolls together; a skill grants one Conqueror/Style event. Attack intervals and cooldowns remain enforced. The legacy optional timed R API is retained for research tests, not offered in the UI.

Selected build supplies AD/AP, attack speed, crit chance/damage, ability haste, both penetration types and Manamune/Muramana Awe. Samira Q/R scale with total AD; W/E scale with bonus AD; E uses MR/magic penetration. W/E do not crit. Item AP has no invented Samira coefficient.

All four rank selectors are enabled. E gives rank-based AS for three seconds. Navori AA reduces remaining Q/W/E cooldowns by 15%; Collector tests its configured threshold after AA/skill damage. LDR and Immortal damage amplifiers apply to skills. Legend Haste and Transcendence AH/cooldown effects are connected. Melee passive is opt-in using the previously accepted level/linear missing-health model. AA procs reuse the shared kernel and item stack state is reported. Yun Tal starts at zero in each replay and gains only from AA. Unsupported offensive runes block replay.

Automatic rotation runs R at S, then E/W/Q, and attacks when ready. This declared priority is not an optimal-combo claim. Manual timestamps remain available. Crit defaults to selected items; 50% override is optional. Expected mode uses probability-weighted hits; nonlinear HP/execute paths are approximate. Seeded rolls are reproducible.

Known gaps: mana costs (no mana gating), Style/item buff expiry, precise skill-specific on-hit effects and movement/attack-driven Energized recharge. Defensive stats, healing and incoming damage have no model here. Mana costs must be sourced, never guessed. Item AA mechanics preserve the audited implementation; exact remaining attack-clock changes after temporary buff expiry need follow-up. W's separate hit/stack interaction is compressed under the user's instant-resolution model.

Evidence: curated D000–D008 screenshots and user practice measurements. 37 unit/UI regression tests passed, including full-build UI replay, automatic rotation, W/E scaling, MR penetration, instant R, haste/Navori cooldowns, Collector and melee passive.
