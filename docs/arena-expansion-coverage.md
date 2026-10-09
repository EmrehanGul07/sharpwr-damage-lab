# Arena expansion — 7.1.22 / mobile 0.8.21

## Five workstreams

1. **Homing:** AA and Ezreal E keep their acquired target identity and advance their projectile head towards its live position. Death removes the target; selection changes never redirect an existing projectile. Muzzle sampling stays frozen, flight stays flat, skillshots keep their firing direction.
2. **Jinx:** three separate champion-only trap points, ultimate base/bonus-AD damage growing during the first flight second, and champion/tower takedowns following personal damage within three seconds. Direct kills grant the mana reward once.
3. **Saved loadout:** mobile reads the matching saved champion build for each new round. Items/boots/default rune stats affect AD, AP, AS, health, mana, resistances, movement, haste and penetration. Resolved skill tables export AD/AP coefficients from the Python damage model. The existing AttackKernel supplies item procs on AA and Ezreal Q; each round gets a fresh scheduler. Crit is the engine's deterministic expected damage, not a random crit roll. Physical AA damage grants lifesteal capped by victim health before impact.
4. **Drills:** four selectable 60-second scenarios. Kite uses a following attacker; Dodge repeatedly attempts W respecting the champion's normal resource/cooldown rules; Last hit leaves the enemy bot inactive while waves fight; Tower trades leaves towers/minions active without a bot disrupting the exercise. Reports show the relevant damage, avoided casts, CS or tower hits. Preview/start/input gating and joystick ownership remain unchanged.
5. **Roster foundation:** all 23 marksmen receive sourced costs, mana/HP regeneration, legal rank/cooldown rules, homing AA, flat skillshots, shared crowd-control reception and mobile loadout integration. Added victim-specific state: Caitlyn Headshot/net, Lucian double shot/E refunds, Kai’Sa Plasma/E refunds, Vayne Silver Bolts, Ashe slow, Corki passive true damage.

## Evidence and exact scope

Repository sources: `data/ability-descriptions.json`, `sharpwr/marksman_fight_engine.py`, `sharpwr/marksman_damage_components.py`, `sharpwr/marksman_kits.py`, `sharpwr/rune_runtime.py`. No new Riot asset or unverified live-patch number is presented as exact.

| Area | Remaining limitations |
| --- | --- |
| Jinx traps | 1s arming, 50u spacing and 20u radius remain provisional. Three independent one-use trap points match the visual positions. |
| Jinx R | Confirmed minimum/maximum damage endpoints; interpolation between them is provisionally linear over one second. Splash radius remains the earlier prototype assumption. |
| Takedowns | Champion and tower contributions work; there are no epic monsters in this arena. |
| Build bridge | Uses the locally bundled catalogue; opponent keeps its base kit. Active items, buying from earned gold, item shields/slows, cleave/chain targets and general ability-triggered item effects remain outside this adapter. |
| Runes | Live adapters cover Lethal Tempo/Conqueror stacks and expiry, Empowerment, Dark Harvest, Tyrant, Empowered Attack, Brutal, initial First Strike and Phase Rush cooldown reduction. Fleet heal/energy, Phase Rush speed/haste, defensive/ally conditions, Sudden Impact and fully dynamic persistent-stat conditions need separate adapters. Rune damage follows the existing provisional ADC model. |
| Caitlyn | Six-hit Headshot uses the engine's confirmed 60% baseline; level/crit progression and brush counting remain unresolved. W has rank-based charges, sequential recharge, 30s lifetime, oldest-trap eviction, root and delayed Headshot bonus; net/trap rights are reserved on AA and restored on cancellation. R has 1.5s lineup, champion-only targeting and homing damage. The 1v1 arena contains no second opposing champion for R interception. Arming (1s), collision radius (20u) and Headshot entitlement window (4s) remain provisional. The R lineup follows the tooltip summary; the older Kit cast-time value is 0.375s. |
| Lucian | Two AA impacts and on-hit scheduling; secondary shot uses the existing confirmed 40% baseline (100% against minions), with each impact reducing E. Level progression, Vigilance and full channel behavior remain unresolved. |
| Kai’Sa | Plasma stacks live on each victim and expire in 4s; detonation follows the engine coefficient. AA magic uses the engine's known level-one baseline. R requires a live Plasma-marked champion and grants the rank/AD/AP-scaled 2s shield, absorbing champion, minion and tower damage after mitigation. Landing uses the existing 400u target-centered region. Target acquisition range and dash speed remain unresolved; evolutions and missile splitting still need adapters. |
| Other kits | Existing `skip` entries remain explicit: channels, poison/bombs/feathers, transformations, reloads and target-dependent procs are not converted into fake damage. Resources/common standards are complete across the roster; complete custom kits are not. |

## Validation

`tests/test_arena_expansion.cjs` exercises moving projectile heads, locked identities, three trap positions, flight endpoints, recent contribution windows, every marksman's resources/manual movement, added passives and drill duration. `mobile/tests/arena-build.test.ts` checks saved loadout isolation, fresh item stacks and rune proc timing. Python practice-data checks validate all roster resource/cost exports. Browser checks exercise saved equipment, every scenario, reports and input gating alongside the prior three-viewport controls suite.

The full local Python discovery initially passed executable tests but could not import seven Streamlit UI modules because this runtime lacks Streamlit. CI installs `requirements.txt` before running the complete suite.
