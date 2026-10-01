# V5.58 — Smolder full-kit adapter and movement policies

## Scope

Executable fight replay now supports Samira and Smolder. Other21marksman ability adapters are still pending. The shared policy is kit-dependent: Samira approaches for melee-passive value; Smolder maintains max AA range and moves along an alternating arc during movement-permitted intervals. Radial distance is independent from lateral arc travel; being stationary radially does not imply no movement. Windup/cast/dash/channel restrictions remain enforced. AA/Hexoptics uses live radial distance. Orbit angle oscillates ±30degrees; target collision/hitbox geometry remains approximate.

## Smolder

P/Q/W/E/R use preserved user WR tables. R center hit is chosen for the fixed target to maximize damage; outer+center are not added. Q crit amplification uses official7.1e additive formula1+0.45*(critChance+max(0,critDamage-2)). AA does not grant Dragon Practice. First successful skill hit grants one per cast/target, pending E multi-hit stack verification. Skill damage evaluates existing stacks before that grant. Q25/100/175 thresholds follow current stack state; AoE/projectiles do not automatically hit the original single target extra times. Q kill gives an extra stack and15mana once. W applies sneeze+first explosion, excluding nonexistent additional champions. E count uses nearest(5+0.0154S) candidate supported by recorded100stack7/10stack5 observations. E bolts span1.25seconds; AA waits for flight end.

At175stacks Q starts seven burn ticks, first atQ impact then0.5s apart; damage(.00025*bonusAD+.00005*stacks)*targetMaxHP/7. Refresh replaces pending prior burn, provisionally. Enemy below6.5%maxHP while burning is executed after damage. Rune/rounding/refresh rules remain TODO.

Champion level determines ranks by Q>W>E order withR at5/9/13. Mana Q30/W50..65/E65/R100, regen, haste and selected build stats are active. Conqueror/Lethal Tempo and supported damage runes retain common flow. Selected items use shared AA kernel and first-hit Muramana skill policy. Mana refund rules remain shared.

## Rotation search

UI creates twelve independent replays for each supported champion (Samira and Smolder): six Q/W/E priority permutations × E enabled/disabled. Each gets a fresh item kernel, fresh stacks/mana/timers. Select shortest target-kill time; if none kills before safety limit, select least HP remaining. This optimizes among tested fixed-priority policies, not all possible delayed/held combos. It does not assume E must always increase DPS: flight's AA lock can make E worse. Initial range is the champion database's max AA range (currently575for Smolder). If Q is ready and affordable, the controller steps into provisionalQ550range, casts, then returns toward max AA range. It does not park outside Q range and silently skip Q.

## Provisional limitations

Smolder Q/W/R cast/projectile timing is not sourced and currently instant. E shot timing/count, skill stack grants, W processing order, burn schedule/refresh are candidate rules identified explicitly in the in-game TODO. Smolder AA windup remains unknown; PC Samira windup was not transferred. Skill range gatesQ550/W1000/E700/R2000are provisional pending reference. No global maximum-DPS or exact WR parity claim is made. Unknown Energized travel coefficients do not generate extra procs. Heal is excluded from target-only damage as the enemy never attacks.

## Sources

User current ability text and1October practice evidence: data/smolder-research-reference.json.
Official Qcrit/threshold changes: https://wildrift.leagueoflegends.com/en-gb/news/game-updates/wild-rift-patch-notes-7-1e/

## Validation

Full suite75tests passed including live-UI AppTest Smolder175stack replay vs TankOrnn, initial-stack persistence, target death and range checks. A separate regression was added for575AA range/550Q step-in/return and all9Smolder tests passed afterward.
