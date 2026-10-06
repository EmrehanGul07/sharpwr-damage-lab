# Practice Tool

A training lane on the web (the "🎯 Practice Tool" tab) and in the Android app (the Practice tab): pick any of the 23 marksmen, walk around, cast every skill at a training dummy and note what differs from Wild Rift. Both use the same code.

## Files

| Path | Role |
|---|---|
| `sharpwr/practice_data.py` | The engine's numbers for one champion with no items or runes (below) |
| `marksman_art.py` (`practice_catalogue`, `practice_tool_html`) | Studio profiles plus those numbers; the self-contained web page |
| `app-data/practice.json` | The same catalogue for the app (icons as bundled files), written by `scripts/export_app_data.py` |
| `assets/marksman-3d/practice.js` | Simulation: movement, casts, buffs, hits on the dummy (tool mode when a profile carries `practice`) |
| `assets/marksman-3d/practice-tool.js`, `.css`, `.html` | Interface: arena, joystick and skill buttons, settings, damage log, notes |
| `assets/marksman-3d/scene.js` | Shared 3D stage; draws the dummy's health bar and the damage numbers. Pages that bundle Three.js (the app) pass it in with their own model loader |
| `mobile/src/views/practice.ts`, `mobile/src/practice-scripts.ts` | The app tab: runs the shared scripts with the bundled Three.js and the 3D tab's offline model cache |
| `tests/test_practice_data.py`, `tests/test_practice_tool.cjs`, `mobile/tests/practice.test.ts` | Checks below |

## What it simulates

Everything numeric comes from the engine; `tests/test_practice_data.py` compares it with the engine functions and fails while `app-data/practice.json` is stale.

- **Level stats:** AD and attack speed (AA engine), movement speed (champion database), attack range (kit; Tristana grows with level). Skill ranks start at the engine's default ranks for the level and can be changed.
- **Basic attack:** an attack every 1 / attack speed; windup from `combat_timing.attack_windup` (shorter with bonus attack speed), projectile speed from the PC timing table. It deals the champion's AD as physical damage; on-hit passives are not simulated (the tool says so). Moving during the windup cancels the attack; afterwards it only cuts the animation.
- **Skills:** cooldowns, cast times, damaging reach and projectile travel from the kit. The hero cannot move during a cast (or a dash); a skill pressed during another cast waits up to 0.6 s for it; a skill pressed during an attack windup cancels the attack. The animation's windup is fitted to the cast time and its follow-through plays at the authored speed.
- **Damage:** `damage_component` raw damage at the rank and level, after the dummy's armor or magic resistance (`100 / (100 + x)`). A skill only damages the dummy when its shape reaches it (line, cone, area, target range, dash path, blink bolt radius). Some abilities hit without a number because their damage needs state the dummy does not track (stacks, missing health, channel ticks); `SKIPPED` lists them with the reason the tool shows. Special cases: Ezreal W marks the dummy and the next other hit within 4 s detonates it; Draven Q adds its damage to attacks during the buff and Vayne Q to the next attack; Kai'Sa Q lands six missiles on the lone dummy, Xayah Q two daggers, Varus Q is fully charged.
- **Buffs:** attack speed, AD and range from the fight engine's own `buff()` calls, read from its source and applied to a kit (Tristana Q, Vayne W/R, Twitch Q/R, Kog'Maw W range, …); Kog'Maw R's passive attack speed. Instant self buffs apply on the press.
- **Dummy:** a squishy, bruiser or tank benchmark at the selected level (`sharpwr/targets.py`) or custom health, armor and magic resistance. It heals 5 s after the last hit, stands up 1.5 s after being defeated, and blocks movement. The arena shows the current combo (damage, hits, time, DPS) and the damage log shows raw → mitigated damage per hit.

Not simulated: items, runes, mana, crits, passives and the abilities listed as skipped.

## Notes

The notes panel keeps notes per champion (general, basic attack, P, Q, W, E, R) and a "tested" mark in the browser's or the phone's local storage (`sharpwr.practiceNotes`). "Copy all notes" (and "Download .md" on the web) gives them as Markdown, one section per champion, ready to paste.

## Controls

Web: click or tap the ground or use the arrow keys to move; Q, W, E and R cast toward the mouse (or at the dummy); Space attacks, held to keep attacking. Touch screens: joystick, tap a skill to cast at the dummy, drag from a skill to aim (the drag direction becomes the aim direction), hold Attack. "Move dummy" places the dummy with the next tap; "No cooldowns" and "Reset cooldowns" help with testing.
