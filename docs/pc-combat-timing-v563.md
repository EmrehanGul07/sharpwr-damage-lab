# Marksman timing references — V5.63.0

All 23 champions researched from PC LoL wiki under explicit user authorization. WR AD, AS, damage ratios, costs and ranks remain authoritative. This is a PC timing proxy, not verified WR parity.

AA windup: 23/23 sourced. AA projectile: 23/23 sourced (Senna/Zeri explicitly non-projectile); Jinx minigun 2750 / rockets 2000 from Riot PC 16.19 game movement components. PC windup fraction = cast/total time or 0.3 + attack delay offset. Base seconds = fraction / PC base AS. Existing authorized WR scaling applied: base / (1 + 0.5 × WR bonus AS). Existing Senna WR 0.5/(1+0.6×bonus AS) preserved. PC windup modifier is recorded, not substituted into WR scaling.

|Champion|Base AA windup (s)|AA projectile speed|
|---|---:|---:|
|Kalista|0.518732|2600.0|
|Tristana|0.225620|2250.0|
|Twitch|0.297373|2500.0|
|Draven|0.229962|1600.0|
|Kog'Maw|0.249960|1800.0|
|Vayne|0.266624|2000.0|
|Ashe|0.333280|2500.0|
|Varus|0.266624|2000.0|
|Xayah|0.268807|2500.0|
|Samira|0.227964|2800.0|
|Miss Fortune|0.225620|2000.0|
|Yunara|0.250075|2500.0|
|Kai'Sa|0.250128|2000.0|
|Corki|0.419255|2000.0|
|Lucian|0.235110|2800.0|
|Smolder|0.260538|1800.0|
|Caitlyn|0.260034|2500.0|
|Jinx|0.270000|2750 / 2000|
|Ezreal|0.301418|2000.0|
|Zeri|0.237462|non-projectile|
|Jhin|0.250000|2600.0|
|Sivir|0.192000|1750.0|
|Senna|0.500000|non-projectile|

## Coverage and remaining data

All 115 P/Q/W/E/R timing templates were retrieved. Missing speed is not zero: buffs/non-projectile effects have no missile speed; expressions and variants are preserved separately. Dash and knockback speeds never become primary missile travel. Source URLs and numerical expressions are in data/pc-combat-timing.json.

Riot game-file supplements (decoded via CommunityDragon, pinned PC 16.19) resolve: Jinx AA 2750/2000, Varus E fixed 0.5s travel, Kai’Sa Q fixed ~0.4s spline travel, Xayah R 4000, Samira R 2800 and Jhin E 1600. Actual movement component fields take precedence over generic spell missileSpeed. Sources and exact records are in data/pc-timing-game-supplements.json.

Remaining effective projectile values:
- Xayah Q: raw asset movement says 400; script runtime override/effective speed unresolved. Stored as raw evidence, not executable guessed speed.
- Jhin W: no missile movement component in PC game file; beam timing/classification needs validation. Generic missileSpeed 10000 is not treated as physical travel.
- Jinx E: multiple mine/delivery spell records; effective damaging trajectory unresolved. Generic missileSpeed is not trusted.
- Compound/variant timings are stored; Smolder W exact deceleration, Yunara W lingering travel, alternate missiles and special missile geometry require dedicated trajectory logic. Primary missile speeds are wired where numeric.
- Lucian Q level-dependent PC cast expression lacks explicit mapped WR breakpoints; existing WR scalar cast remains authoritative.
- Samira R retains existing channel/shot timing and no melee passive; shots now have sourced 2800 projectile flight.
- Other mechanics (reload start, range geometry, dash trajectories, attack resets) still require kit-specific validation; this import does not claim complete engine parity.

## Runtime

Run scripts/import_pc_combat_timing.py, then scripts/import_pc_timing_supplements.py to reproduce the source import.

AA launch locks walking/casts through windup, then projectile flight permits movement and independent actions. Existing attack interval remains based on WR AS. Smolder Q/W/R now use sourced cast + flight; Q checks range at launch and can land after the caster kites away. Skill buff/non-projectile effects retain their own behavior. Database cache signature bumped; no build result database added.
