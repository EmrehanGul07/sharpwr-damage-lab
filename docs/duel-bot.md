# Playable 1v1 bot (mobile 0.8.2 / web 7.1.3)

Open Practice, select **1v1 bot**, pick the opponent and difficulty, then Start 1v1. All 23 marksmen are available. The player uses the normal joystick/ground movement, attack button and aimed skills. Pause freezes both sides; Restart starts a clean round. A death ends the round, with victory/defeat/draw; three minutes without a death ends in a time limit. A pause or hidden page does not accumulate combat time.

## Difficulty changes decisions only

| Mode | Observation delay | Decision interval | Aim error (game units) | Movement prediction | Dodge chance | Preferred AA range |
|---|---:|---:|---:|---:|---:|---:|
| Easy | 650 ms | 240 ms | up to 110 | none | 8% | 58% |
| Medium | 300 ms | 140 ms | up to 55 | partial | 40% | 76% |
| Hard | 140 ms | 75 ms | up to 18 | strong | 80% | 90% |
| Impossible | 50 ms | 35 ms | zero added error | full linear prediction | 100% | 96% |

These are authored policy settings, not Wild Rift balance values. Impossible is the strongest policy, not a guarantee of victory or perfect dodging: cast locks, reaction delay, stale observations and changes in the player's direction still apply.

HP, AD, armor, MR, move speed, attack speed, range, ability damage, ranks, cooldowns and cast durations are the same for a given champion/level in every mode. HP/armor/MR come from `champion_level_stats`, exported beside the existing Practice numbers. Difficulty never edits those profiles. Both actors use the same simulation and collision rules.

`duel-bot.js` is a deterministic decision controller with a seeded PRNG, not a trained model or remote LLM. It receives delayed public position, observed velocity, health and visible cast telegraphs; its own cooldowns are available normally. It cannot read pending enemy hits, enemy input/destination, future positions or the opponent's private cooldowns. It leads shots, spaces and kites between legal attacks, dodges visible threats, saves movement spells to escape and chooses buff/combo/finishing casts. Ezreal W→Q, Tristana E→Q and Varus W→Q have explicit priority policies. Lower modes sometimes skip a decision. It never casts an unsupported damage model to fake a result.

## Combat boundary

`duel.js` advances the two Practice actors on a shared 120 Hz fixed clock. Line skillshots retain their direction and test swept projectile segments against the moving enemy. Targeted basic attacks stay homing. Area/cone/movement skills test their geometry on arrival. Damage is bidirectional; dummy healing and respawning are disabled. A completed round freezes before more inputs can deal damage. Rendering includes both GLBs, original animations/effects, health bars and damage numbers.

This is the **base-kit Practice sandbox**, not the full Build Lab combat engine. Items, runes, shields and unresolved passive/stack/channel/execute mechanics are not simulated. Mana and CC support for the Ezreal–Jinx pilot is described below. The existing per-champion “What this practice simulates” panel lists unresolved abilities. Those abilities remain excluded from the bot's damage rotation. The audited Build Lab formulas, cached rankings and full-fight scheduler are unchanged. Porting the remaining stateful mechanics and item/rune builds into real-time duels is separate work.

## Verification

`node tests/test_duel_bot.cjs` covers all 92 champion/difficulty combinations, stat equality, delayed visibility, deterministic/frame-rate-independent runs, skillshot avoidance/intersection, homing AA, death freeze and dodge decisions. `tests/test_practice_data.py` checks the defensive stats against the Python database. Mobile `test:browser` plays all four modes at 390 px and 1280 px with external requests blocked, checks pause/controls/model loading and returns to Practice/navigation. The Android workflow runs the bot checks before packing the live update.

## Ezreal–Jinx pilot (0.8.3)

Only 1v1 enables the new resource and state hooks in `duel-mechanics.js`; training dummy behavior and the full Build Lab engine remain separate. Level mana/HP regeneration, costs and passive attack speed are exported from the database/Kit in `practice.duel`.

- Ezreal: damaging ability hits build four eight-second Spell Force stacks; Q hit refunds 1.5 s of Q/W/E/R cooldown. W marks and detonates, with the reference engine's ability-only mana refund. E blinks then acquires the lone enemy inside its bolt radius.
- Jinx: free Q weapon toggle, minigun stacks/decay, extra rocket range, per-shot mana, boosted rocket damage and distinct rocket visuals. W slows; E persists and roots once; R calculates the reference minimum-flight missing-health damage at impact. Get Excited triggers on kill, then the finished round freezes.
- Root blocks walking and new mobility casts; it interrupts active non-blink dashes. Slow expires independently. The HUD displays mana, weapon, stacks and crowd control.
- Bots check their own mana and switch Jinx weapons by range. Hard/Impossible pressure after observing Ezreal E. Enemy cooldown estimates are derived from delayed visible casts and Q hits; no private cooldown deadlines are read.

Known limits: no items/runes yet; Jinx E uses one circular collision envelope and the reference's provisional one-second arm delay. R's distance scaling remains unresolved and explicitly uses the minimum-flight model. Get Excited movement-speed fade is a linear presentation approximation. Other champions retain base-kit sandbox limitations; this does not establish Wild Rift parity.
