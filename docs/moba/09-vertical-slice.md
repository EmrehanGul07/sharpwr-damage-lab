# 09 · First vertical slice (M1)

## Scope

| In | Out (later milestones) |
|---|---|
| One controllable champion | Items, runes, levels beyond a fixed test level |
| Isometric camera (fixed angle, follow, desktop edge-pan off by default) | Map, lanes, minions, towers |
| Mobile: virtual joystick + 4 skill buttons with drag-to-aim and cancel zone; desktop: right-click move/attack, QWER with cursor aim, A-move | Fog of war |
| Basic attack (windup, projectile, attack timer, attack-move) | Networking |
| Q/W/E/R through the ability framework (`05-ability-framework.md`) | Audio beyond placeholder |
| Health, damage, death, respawn (fixed 5 s timer) | |
| Practice dummy (configurable HP/armor/MR, regen toggle) | |
| One simple enemy bot (approach, attack, kite, dodge visible skillshots, retreat at low HP) | |
| In-game debug panel: event log, damage per hit, state hash, "unsupported" list | |
| Damage comparison report vs the Python reference | |

## Champion choice — decided

**Samira**, from `game/content/reference-riot/champions/samira.champion.json`, listed in
`game/content/rosters/personal.roster.json` (`distribution: "personal"`). The game is
personal-only (ADR-0004 rev 2): never published or shared. Placeholder art first; the existing
SharpWR Samira fan model may be imported into `Assets/SharpWR/Reference/` later.

## Samira data available

| Element | Status | Slice handling |
|---|---|---|
| Base stats, growth, range 525, MS 340 | wr_wiki / damage_lab_preserved | used |
| AA windup 0.22796 s, projectile 2800 | pc_reference_provisional | used, labelled |
| Q/W/E/R damage, ratios, CD, mana | damage_lab_user_sourced / wr_verified_user (mana) | used |
| Q range 950, width 120; E range 600, dash 650 @1600; W radius 325 | wr_wiki / PC | used, PC labelled |
| R channel 2.277 s, 10 shots, even offsets | PC + assumption | used, labelled "offsets assumed" |
| Style resource (E→S), R gate | PC + user rules; refresh details open | basic version, labelled |
| Passive melee bonus, blade AA ≤200 | provisional interpolation | **unsupported** in slice |
| Q melee cone, E–Q explosives, W projectile destruction, immobilized assist attack | not resolved | **unsupported** in slice |
| Gameplay/collision radius | unknown | slice uses a labelled engine default (not a Samira claim) |

## Work breakdown

| # | Task | Owner | Depends on |
|---|---|---|---|
| S1 | Create Unity 6.3 LTS URP project at `game/unity`, add sim package, commit ProjectVersion | lead (manual: Unity Hub) | — |
| S2 | Entity store (SoA), stable ids, SaveState/LoadState, state hash | combat-engineer | — |
| S3 | 2-D fixed-point movement + collision circles + spatial grid | combat-engineer | S2 |
| S4 | Attack controller (timer, windup, projectile, attack-move) generalizing `BasicAttackDuel` | combat-engineer | S2 |
| S5 | Damage pipeline steps 1–7 (`03` §4), death/respawn | combat-engineer | S4 |
| S6 | Content schema v1 + loader (JSON → definitions → Fix64) | data-verification + champion-implementer | — |
| S7 | Ability framework: targeting, cast/lockouts, delivery (Projectile, Area, Dash, Channel), cooldown/cost, unsupported gating | champion-implementer | S5, S6 |
| S8 | Samira kit in data + hooks | champion-implementer | S7 |
| S9 | Bot v1 (observation delay, decision interval, aim error, dodge) | gameplay-ai | S4, S7 |
| S10 | Offline host loop in Unity (fixed step, catch-up cap, view interpolation) | unity-gameplay | S2 |
| S11 | Camera, touch joystick + skill buttons, desktop input → commands | unity-gameplay | S10 |
| S12 | HUD: HP/mana bars, cooldowns, damage numbers, debug panel | unity-gameplay | S10 |
| S13 | Parity: scenario fixtures (AA loop, Q/W/E/R vs dummy) and comparison report | data-verification + qa | S8 |
| S14 | Acceptance suite + Android/desktop builds | qa | all |

## Acceptance criteria (all automated unless marked)

1. `dotnet test` green on ubuntu x64, ubuntu ARM64, windows, macOS (T2).
2. Fix64 vectors bit-exact; parity fixtures within tolerance; **damage comparison report** lists
   every case with Python value, C# value, |Δ| and status label.
3. Scenario: champion kills a 2,000 HP / 50 armor dummy with an AA-only loop; event times match
   the Python reference for the same inputs within 10 µs; total damage within 1e-3 HP.
4. Scenario: each enabled ability's damage vs fixture; each unsupported ability is uncastable
   and shows its reason.
5. Gates: casting on cooldown / without mana / during lockout produces `Rejected` and no state
   change (tests per gate).
6. Death at HP ≤ 0, respawn after 5 s at spawn with full HP; simultaneous lethal trades both die.
7. Bot duel: 50 seeded bot-vs-bot matches end (death or 180 s) with no exception and identical
   hashes on re-run; difficulty never changes stats.
8. Determinism: a 3-minute recorded input stream replays to the same final hash.
9. Unity PlayMode: scene loads, joystick moves the champion, skill button drag aims and casts,
   desktop QWER casts (input-simulation tests).
10. Builds: Android IL2CPP APK and desktop build produced by CI (or locally with logs attached if
    the Unity license secret is not configured yet).
11. *Manual:* 30 fps p95 on a minimum-tier Android phone for 5 minutes; touch feel review.
