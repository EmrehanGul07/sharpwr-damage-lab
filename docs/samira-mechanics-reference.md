# Samira: Wild Rift values and PC timing reference

User supplied on 2026-10-01. PC excerpt contents were provided directly; no inference that the numbers are Wild Rift values. Structured record: samira-mechanics-reference.json.

## Confirmed Wild Rift mana

Q 30, W 60, E 40 at every rank. R mana remains unknown; the PC listing of 6 Style does not prove zero mana in Wild Rift. The library and displayed cost table are updated. Mana consumption is not enabled until the resource model is completed.

## Recorded timing and action rules (PC reference only)

| Ability | Cast / travel | Action restrictions and interactions |
|---|---|---|
| P | Dash speed 2050; ranged AA projectile 2800; empowered AA six bolts over 0.5s | Blade AA within 200 edge range is non-projectile. Empowered AA resets attack timer, uncancellable windup, one on-hit application. Style lasts 6s and refreshes on repeated as well as unique hits. |
| Q | Cast 0.25s; projectile speed 2600 | Ranged shot hits first enemy; melee cone. During E creates explosives detonating at dash end. PC lifesteal effectiveness 100%. |
| W | Cast 0.1s; two hits at start/end of 0.75s effect | AA/Q blocked. R ends W early. Destroys non-turret hostile projectiles. |
| E | No cast time; dash speed 1600 | Q/R usable during dash; W buffers to dash end. PC takedown reset window 3s. Preserve WR AS duration 3s; reject PC 5s duration. |
| R | No cast time; channel 2.277s, shot window 2.013s, approximate 0.2s spacing | AA/Q/W blocked; movement allowed. Cast requires visible enemy; shots do not. Style consumed at effect end. Cast-inhibiting CC/disarm interrupts; disarmed cast prohibited. PC lifesteal effectiveness 100%. |

All range, width, queue, target immunity and targeting values from the excerpt are retained in JSON with ambiguous mappings explicitly unresolved. Q/W/E/R queue threshold in the excerpt is 0.5s. P target immunity 10 has no supplied unit.

## Source boundaries

Do not change existing WR base damage, AD/AS ratios, cooldown tables, crit scaling or level progression from these PC formulas. R PC static cooldown 5s is recorded only; WR 6s stays intact and its haste applicability needs confirmation. P's PC passive list includes blade AA/W/E/Q slash/E-Q explosives, but not R; WR R exclusion is confirmed by the user’s 2026-09-30 practice test, reported 2026-10-01. The engine now excludes melee passive from every R shot.

Current instant expected-damage fight behavior remains unchanged. This record prepares future timing/lockout integration; it does not silently switch simulation modes.
