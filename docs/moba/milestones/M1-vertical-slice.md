# M1 · Vertical slice — Not accepted yet (simulation side complete; Unity items pending)

Date 2026-10-17 · branch `moba/foundation` · Damage Lab 7.1.23 · .NET 8 (CI) · Unity: not run.

## Work completed

- **Simulation** (`com.sharpwr.sim`): match loop with commands, movement, dashes, basic attacks
  (windup with bonus-AS scaling, homing projectiles, melee blade attacks, buffered commands),
  swept line skillshots visible from cast start, mana/regen, cooldowns, cast locks, damage with
  armor/MR, death after same-µs damage, 5 s respawn, state hash, full Clone.
- **Ability framework**: data abilities + stateless kits (`IChampionKit`), generic gates
  (lock → kit → rank → cooldown → mana), `CheckCast` shared with bots.
- **Samira** (reference content, personal build): Style, provisional melee passive, Q
  projectile/slash, W two hits (R cancels the second), E dash + AS buff, R S-Style gate with 10
  shots, Style consumed at channel end. Gaps are rejected and listed, not guessed.
- **Bot** (`AI/`): delayed observations, decision interval, aim error + lead, telegraph dodge,
  kite to preferred range, retreat; four difficulties from `content/ai` (never change stats).
- **Client core** (`com.sharpwr.client`, no Unity): fixed-step host, input → commands, view
  interpolation, HUD model, camera math, practice arena (player + dummy + bot).
- **Unity layer** (`com.sharpwr.unity`): code-built arena, isometric camera, touch joystick and
  drag-aim buttons, desktop controls, HUD, debug panel. Content embedded as generated C#.
- **CI**: annotations for failures/reports, test-count gate, Unity stub compile check.

## Evidence (CI, identical on ubuntu x64, ubuntu ARM64, windows, macOS)

| Check | Result |
|---|---|
| `dotnet test` (sim + client) | 50 executed, 50 passed |
| Damage comparison | `M1-parity.md`, `M1-parity-cases.csv`: 390 formula cases pass; 3 AA loops and a 17-hit Q/W/E/R rotation match the Python engine (max 3.3 µs / 2.3e-7 HP for the acceptance dummy) |
| Cross-platform determinism | 3-minute recorded match: hash `5CA32C74A80474C7` on all four platforms |
| Bot | 50 seeded bot duels terminate and replay identically; Q hits taken: easy 19/20, impossible 0/20 |
| Unity package | compiles against API stubs for Input System and legacy input (not the real editor) |
| Fast tier | lint, content provenance/IP, ownership, tool tests, fixture/embedding freshness |

## Acceptance criteria (`09-vertical-slice.md`)

| # | Criterion | Status |
|---|---|---|
| 1 | `dotnet test` green on 4 platforms | **Pass** |
| 2 | Bit-exact vectors, parity within tolerance, per-case damage report | **Pass** |
| 3 | AA kill of 2000 HP / 50 armor dummy within 10 µs, damage 1e-3 HP | **Pass** (3.25 µs, 2.3e-7 HP) |
| 4 | Enabled abilities vs fixture; unsupported uncastable with reason | **Pass** in sim (rotation parity, `UnsupportedMechanic` test); on-screen reason not verified in Unity |
| 5 | Gate rejections without state change | **Pass** (cooldown, lock, mana, requirement, invalid target) |
| 6 | Death, respawn 5 s, simultaneous lethal trade | **Pass** |
| 7 | 50 seeded bot duels, identical re-runs, stats unchanged by difficulty | **Pass** |
| 8 | 3-minute input replay → same hash | **Pass** (and same on all 4 platforms) |
| 9 | Unity PlayMode: scene loads, joystick, drag-aim, desktop QWER | **Not run** — Unity project not created yet |
| 10 | Android IL2CPP + desktop builds | **Not run** — needs Unity (and secrets for CI) |
| 11 | Manual: 30 fps p95 on a minimum-tier phone, touch feel | **Not run** |

## Unverified assumptions

- Samira AA windup, cast times, projectile speeds, W/R timings: `pc_reference_provisional`.
- Passive melee bonus: Damage Lab's provisional interpolation (labelled in content).
- R shot offsets: evenly spaced (exact WR offsets unknown).
- Gameplay radius unresolved → units are points for range checks.
- Walking positions update at tick end (mid-tick events see tick-start positions; dashes exact).
- Bot `CheckCast` can reveal true range when a cast is refused (documented leak, small).
- Unity layer: real Unity API compatibility unverified (stub check only).

## Manual verification required

Follow `game/UNITY_SETUP.md`: create the project, confirm no compile errors, play on desktop
(move, attack, Q/W/E/R, death/respawn, bot difficulties), build to an Android phone and judge
touch controls and frame rate.

## Remaining blockers

- Unity project creation (Unity Hub, ~10 min) — only the owner can do it.
- Optional: Unity licence secrets for CI builds/PlayMode tests.

## Next recommended step

Owner runs `game/UNITY_SETUP.md` and reports Console errors or play feedback. Then close M1
(criteria 9–11) and start **M2 combat depth** (CC, shields, healing, on-hit flags).
