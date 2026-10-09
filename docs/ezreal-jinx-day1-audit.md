# Ezreal–Jinx: Day 1 audit

This audit verifies the implemented simulator, not numerical parity with a live Wild Rift client. Build Lab is unchanged.

## Evidence and rules

`data/ability-descriptions.json` supplies local WR descriptions. `app-data/practice.json` exports costs, cooldowns, cast/travel tables and damage from `sharpwr/practice_data.py`, the ability catalogue and champion kits. Some timing values are authorized PC proxies. No unsupported values were replaced with guesses during this audit.

| Kit | Implemented behavior checked | Remaining limits |
| --- | --- | --- |
| Ezreal AA | Windup, cooldown, queued movement after release, frozen cast target; moving victim receives damage and impact at its actual position | Flight duration is scheduled from initial distance; visible flight is not a physically simulated homing path |
| Ezreal P | Damaging ability stacks, maximum four, 13% AS per stack, eight-second expiry | Full item/on-hit interactions are outside this base-kit duel |
| Ezreal Q | First eligible collision, minion blocking, damage, 1.5-second cooldown refund, hit/miss passive | Full item proc integration remains outside this duel |
| Ezreal W | Four-second mark; minions do not block; champion/tower eligibility; single detonation; ability mana refund; safe HUD countdown | No epic-monster units; AA refund behavior follows existing reference configuration |
| Ezreal E | Blink endpoint, landing-origin bolt; acquire nearest living enemy with active W priority; freeze acquired identity; root prevents cast | Bolt radius/timing retain existing proxies; no epic-monster scene |
| Ezreal R | Fixed direction, each lane victim hit once, 50% minion damage | Global visuals terminate at scene range; no monsters |
| Jinx AA/Q | Free toggle; rank-dependent range and AS; stacks/decay; 112% rocket damage; per-shot mana; cancelled windup refund; low-mana fallback | Provisional splash radius 1.2 m; affordability observations no longer mutate weapons |
| Jinx W | Cast direction, AS-dependent cast table, blockers, rank slow and expiry | Reveal/vision has no fog-of-war system to affect |
| Jinx E | Champion-only trigger independent of selected unit, arm delay, lifetime, one root, dash interruption, root expiry | Circular envelope rather than three individual traps; one-second arm delay is provisional |
| Jinx R | First champion collision; missing HP read at impact; 80% secondary splash | Existing minimum-flight damage is retained; exact flight amplification curve unresolved |
| Jinx P | Direct/splash champion kill grants MS/AS and missing-mana refund | Three-second assist window, structure/monster takedowns and exact movement-decay curve are not fully modeled |

## Fixes delivered

1. Traps inspect the opposing champion rather than the currently selected minion/tower.
2. Arcane Shift independently acquires an eligible enemy; selection changes and victim death cannot redirect its bolt.
3. `canCast` observation is side-effect free. Low-mana weapon fallback happens only during a gameplay cast request.
4. AA/bolt impact positions use the actual victim position without changing the frozen skillshot heading.
5. Finish/death clears held AA, pending/buffered casts, queued movement, aiming, target lock and pending hits, then ends cast animation locks. Finished/dead actors reject new movement, attacks and casts.

## Control and animation checks

- Only joystick/arrow keys request human walking; AA, target selection, Farm and skill aiming never approach targets.
- Queued walking preserves attack windup, then replaces follow-through with a single Walk state.
- Cast facing follows requested world direction; gait and blend continuity tests cover idle/resume, speed changes and isolated projectile-launch sampling.
- Browser scenarios cover real touch ownership, foreign pointer rejection, simultaneous AA/joystick, aiming while walking, skill cancellation that preserves the joystick, blur cleanup and late pointer releases.
- Numerical regression cases cover every Q/W/E/R rank for both champions, cooldown rejection, resource regeneration, collision, mark/refund, root/slow expiry, execute-time HP and death cleanup.

Unresolved rows above are explicit follow-up work, not a claim that both complete WR kits are reproduced. Day 1's audit and verified bug-fix scope is complete once the recorded test suite and mobile viewport checks pass.
