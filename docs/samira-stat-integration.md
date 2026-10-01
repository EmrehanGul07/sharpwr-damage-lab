# Samira stat integration — V5.53

Champion core stats resolve from the source-attributed database at the selected level using the existing app growth curve, n*(0.7025+0.0175*n). This curve is retained for consistency and still needs a Wild Rift level-stat audit; no new exactness claim is made.

Fight starting mana includes champion mana and selected item/boot mana. The same champion mana is supplied to the shared AA kernel and Manamune/Muramana AD calculation, replacing the manual mana override for Skill Lab. Mana regeneration is continuous between instant impact events, capped at maximum mana. Q/W/E consume 30/60/40 mana only after validity and cooldown checks. Insufficient mana rejects manual events without changing stacks/cooldowns; automatic rotation continues attacking and schedules skills when affordable. R costs zero mana and requires S Style. Style expires after six seconds without an AA/basic skill hit.

Own HP, armor, MR, movement speed and range are resolved and displayed with item bonuses. These do not imply incoming enemy attacks, survival, healing, range gating, or travel timing simulation. HP regen is available through level_stats but own survival remains outside the current one-target damage replay. Existing AD/AS, crit, haste, item procs and penetration behavior is preserved.
