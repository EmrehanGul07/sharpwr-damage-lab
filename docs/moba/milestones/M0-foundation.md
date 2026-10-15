# M0 · Foundation — Partially accepted

Date 2026-10-15 · branch `moba/foundation` from `4361afd` · Damage Lab VERSION 7.1.23 ·
Python 3.13 · Node 22.22 · .NET SDK: **not available** · Unity: **not available** ·
Environment: cloud sandbox, package registries blocked.

## Work completed

- Read-only audit of the Damage Lab (`00-audit.md`), including baseline test run.
- Architecture and plans `01`–`10`, ADR-0001…0004.
- Simulation core skeleton `game/packages/com.sharpwr.sim` (Fix64 Q32.32, SimTime µs, fixed
  30 Hz clock, PCG32, CombatMath, event model, scheduler, hashed EventLog, `BasicAttackDuel`
  spike) + `game/sim` dotnet projects with NUnit tests (vectors, parity, determinism).
- Parity harness: `tools/parity` (fixture exporter calling the Python engine, bit-exact
  fixed-point model, C#-algorithm transcription fuzz, Fix64 vector emitter).
- Data migration: `tools/data_import/import_reference_champion.py` → Samira reference content
  with per-field provenance (91 provenance fields: 21 wr_wiki, 4 wr_verified_user,
  7 damage_lab_preserved, 42 damage_lab_user_sourced, 6 pc_reference_provisional,
  10 unresolved, passive unsupported).
- Content validator (provenance + IP boundary), sim determinism lint, ownership map + checker.
- Claude Code config: `CLAUDE.md`, 5 rules, 7 agents, 4 skills, hooks (PreToolUse guard,
  PostToolUse checks, Stop/SubagentStop fast tier), `game-ci.yml`.

## Evidence

| Check | Command | Platform | Result |
|---|---|---|---|
| Fast tier | `python -I tools/ci/fast_checks.py` | linux x64 sandbox | 11 checks ok, C# step skipped (no .NET) |
| Fixed-point parity vs Python | `python -I -m unittest discover -s tools/parity -p "test_*.py"` | same | 7/7 pass; 15 level, 60 resistance, 270 ability, 12 AA-impact cases; max |Δ| stat 1.31e-8, multiplier 1.27e-10, damage 2.66e-7 HP, time 1.11e-6 s |
| C# algorithm transcription | `test_csharp_algorithm_port.py` | same | 40k fuzz pairs + exact ties equal the model; 2 deliberate rounding mutants detected |
| Sim lint | `tools/sim_lint` (+3 tests) | same | 8 C# files clean; found 2 real uses (diagnostic accessors), now annotated |
| Content validator | `tools/content` (+7 tests) | same | Samira reference valid; IP leak/rostering cases rejected |
| Ownership | `tools/ownership` (+5 tests) | same | every governed file has exactly one owner; Damage Lab protected |
| Hooks | `tools/ci/test_hooks.py` (6 tests) | same | Damage Lab edits blocked, override works, Riot art blocked; caught and fixed a relative-path bug |
| Damage Lab untouched | `git status` on protected paths | same | 0 changes |
| Damage Lab suites | `python -m unittest discover -s tests` | same | 296 run, 289 pass, 7 errors = all `No module named streamlit` (identical to baseline) |
| C# compile + NUnit | `dotnet test game/sim/tests/SharpWR.Sim.Tests.csproj` | — | **Not run**: no .NET SDK, NuGet blocked |
| Unity project | — | — | **Not created**: needs Unity Hub (manual step S1) |

## Acceptance criteria (M0)

| # | Criterion | Automated | Status |
|---|---|---|---|
| 1 | Numeric design reproduces Python within tolerance | yes | **Pass** (Python bit-exact model) |
| 2 | C# compiles; `dotnet test` green on x64 + ARM64 | yes (CI) | **Not run** |
| 3 | Unity project opens with the sim package, no compile errors | manual | **Not done** |
| 4 | Ownership, hooks, lint, validator tests green | yes | **Pass** |
| 5 | Damage Lab unchanged and its suites still pass | yes | **Pass** for runnable suites; 14 env-blocked suites unchanged from baseline |

## Unverified assumptions

- C# source has not been compiled. Its arithmetic algorithm is checked by transcription, not by
  the compiler/runtime; NuGet package versions in the test project are unrestored pins.
- Samira timing values are PC proxies (windup, projectile speeds, cast times) — labelled.
- Growth curve is the Damage Lab's app curve; WR level audit open.
- Claude Code rule/agent/skill/hook file formats follow current documentation as I know it;
  the docs pages could not be fetched in this session. Verify with `/agents`, `/hooks`,
  `/memory` in Claude Code (manual step below).

## Manual verification still required

1. On a machine with .NET 8: `dotnet test game/sim/tests/SharpWR.Sim.Tests.csproj` → all pass.
2. Push the branch; confirm `Game CI` passes on all four OS runners.
3. Unity Hub step S1 (`game/unity/README.md`); confirm `SharpWR.Sim` compiles in the editor.
4. In Claude Code at the repo root: `/agents` lists 7 agents; `/hooks` shows 4 hook events;
   try editing `sharpwr/aa_engine.py` → blocked with the Damage Lab message.
5. Re-run the 14 environment-blocked Damage Lab suites (streamlit UI tests, three.js tests).

## Remaining blockers

- Resolved 2026-10-15: personal-only game, Samira first (ADR-0004 rev 2).
- Unity license for CI builds.

## Next recommended milestone

Close M0 items 2–3 (≈ half a day with .NET + Unity), then **M1 vertical slice** starting with
S2–S5 (combat-engineer) and S10–S11 (unity-gameplay) in parallel.
