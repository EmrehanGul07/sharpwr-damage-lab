# Samira timed combat — V5.54

User-authorized PC Wiki timing/range reference is now used provisionally with preserved user-confirmed WR damage, mana, cooldown and E attack-speed duration. The target is stationary and never attacks.

Implemented: Q 0.25-second cast, ranged projectile speed 2600, close slash, E-Q detonation at dash end; W 0.1-second cast, two independent hits separated by 0.75 seconds, AA/Q lock, cancellation of pending W when R casts; E fixed 650-unit dash at speed 1600, 600 target range, Q/R usable during dash, W buffered to dash end; R 2.277-second channel, ten hits across 2.013 seconds, AA/Q/W lock and E permitted, Style consumed at channel end. Range gates: AA champion database range, Q950, W325, E600, R600. Melee AA200, Q slash340. Dash position updates at each event; overshooting can leave the target outside melee range. R never gains melee passive. Mana/cooldowns are charged once at cast, stacks at actual impacts. W hits can gain separate Style if another ability hit occurs between them. Auto events interleave with pending impacts instead of waiting for all projectiles to finish.

AA ranged travel speed2800. AA windup remains unavailable and defaults to zero: this is an explicit gap, not a verified game value. Exact R sporadic shot offsets are unavailable: ten offsets are evenly spaced through the 2.013-second reference window. Target/champion collision radii are unknown; distance uses a one-dimensional point-target approximation rather than exact center/edge hitbox geometry.

Remaining before claiming parity: verified WR timing/ranges and R haste rule, AA windup and timer adjustment under mid-cycle AS buffs, exact R offsets, full skill-specific item/on-hit interactions, positional movement/aim/visibility/CC state, immobilized-target passive assist attacks. Projectile defense has no incoming-projectile events in this target-only scope. Healing/own-survival are intentionally outside scope because the target never attacks. No PC damage ratios or five-rank tables were imported.

## V5.55 movement correction

The champion now walks continuously toward the stationary target between events, except during Q/W cast locks, a supplied AA windup, and dash travel. W active time and R channel allow walking. Movement uses the champion database MS plus selected build MS, Style's 3% per stack and R's 30% penalty from the user-authorized PC reference. A 0.05-second movement wake-up allows the auto scheduler to notice entry into attack/skill range; position is integrated across exact dash/cast/channel boundaries, not teleported at each wake-up. Dash overshoot is followed by walking back toward the target. Unknown AA windup remains zero by default. Distance is now shown per impact in the UI. Exact WR MS soft caps, collision radius and unit-overlap stopping distance remain unverified.

## V5.56 provisional AA windup

User authorized only PC Samira's base windup as a fallback. PC Template:Data_Samira reports windup0.149999994 and baseAS0.658; their quotient is 0.2279635167 seconds. PC base AS is used only to derive this constant and does not replace WR/app AD or AS. The base is shared provisionally for melee/ranged attacks; separate WR measurements remain unavailable.

Runtime calculation uses the WR Patch2.2 formula: baseWindup/(1+bonusAS*0.5). Bonus AS includes the selected level, items/boots, Alacrity, live E/Lethal Tempo and tracked Rageblade/Phantom Dancer/Yun Tal buffs at attack start. Movement and new skills wait until windup finishes; issuing commands does not cancel the AA, per user WR confirmation. Projectile travel remains separate. Exact WR base and unchanged applicability of this historic WR formula remain unverified. This supersedes the earlier zero-windup default for the UI.
