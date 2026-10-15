# 08 · Incremental development roadmap

Each milestone ends **independently playable** (or, for M0, independently runnable), with an
acceptance report in `docs/moba/milestones/` listing work, test/build evidence, unverified
assumptions, blockers and the next milestone. Nothing is reported complete unless its
acceptance tests pass in CI.

| # | Milestone | Playable outcome | Acceptance (summary) | Main owners |
|---|---|---|---|---|
| **M0** | Foundation | Runnable sim core + parity harness; Claude Code config | Fixed-point model passes parity vs Python; C# compiles and `dotnet test` green on ARM64 + x64; Unity project opens with sim package; ownership/hook tests green | lead, combat, data, qa |
| **M1** | Vertical slice (`09-vertical-slice.md`) | One champion vs dummy and a simple bot, isometric camera, touch + desktop | Slice acceptance list; Android APK + desktop build launch; damage parity report | all |
| **M2** | Combat depth | Buffs/debuffs, CC (stun, slow, root, knock-up), shields, healing, on-hit, damage flags | Status/pipeline unit tests; CC scenario tests; Samira (ref) Style + R channel parity scenario | combat, champion |
| **M3** | Items, runes, progression | Gold, XP, levels 1–15, shop, 10 original items, 6 runes | Item/rune parity for reference items; progression tests; shop UI test | combat, champion, data, unity |
| **M4** | Lane | One lane: minion waves, towers, last hitting, bot laner | Wave/tower rules tests; bot completes a 10-min lane session without stuck states | ai, combat, unity |
| **M5** | Full map offline | Three lanes, jungle camps, objectives, fog, Nexus, 5v5 bots | 20-minute bot match ends with Nexus kill; fog tests; perf on minimum device | all |
| **M6** | Online 1v1 | Server-authoritative 1v1 over the internet | Prediction/reconciliation tests; desync suite; 150 ms/3% loss playtest | network, qa |
| **M7** | Online 5v5 | Matchmaking-lite, 10 players, reconnect | Load test 20 matches/instance; reconnect tests | network |
| **M8** | Roster and polish | 6+ original champions, audio, onboarding | Balance TTK bands; device matrix | champion, unity |

Ordering rationale: depth of one champion before breadth; offline full match before netcode,
but every milestone keeps the sim snapshot-able so M6 is not a rewrite.

## Parallelization (after M0)

| Stream | Can start | Blocked by |
|---|---|---|
| Unity presentation shell (camera, input, HUD mock) | M1 day 1 | Unity project creation (M0) |
| Entity store + movement + attack controller | M1 day 1 | — |
| Ability framework data model + loader | M1 day 1 | content schema (data-verification) |
| Bot (attack/kite/dodge) | after attack controller | entity/observation API |
| Netcode spike (transport choice) | M4 | sim save/load state |

Shared contracts (`Runtime/Contracts`, `Numerics`, `Core`, `CombatEvent.cs`) change only via the
contract-change protocol in `.claude/rules/integration.md`.
