# SharpWR — Damage Lab + MOBA game workspace

This repository holds two things:

1. **The Damage Lab** (existing): Python engine `sharpwr/`, data `data/`, Streamlit app,
   Android app `mobile/`, three.js arena `assets/marksman-3d/`. It is the **validation
   reference** for the game. Treat it as read-only. A hook blocks edits; only the user can
   lift it (`SHARPWR_ALLOW_REFERENCE_EDIT=1`) for a deliberate reference change.
2. **The MOBA game** (new): everything under `game/`, `tools/`, `docs/moba/`, `.claude/`.

Start every game task by reading `docs/moba/README.md` (index, current milestone, open
decisions). Architecture: `docs/moba/01-architecture.md`. Roadmap: `docs/moba/08-roadmap.md`.

## Non-negotiable engineering rules

- **Determinism.** Gameplay rules live only in `game/packages/com.sharpwr.sim` (pure C#,
  no `UnityEngine`). Use `Fix64` and `SimTime` (µs); no float/double, wall clock, unseeded
  randomness, threads or hash-ordered iteration in the sim. `tools/sim_lint` enforces this.
- **Fixed-step simulation**, 30 Hz; combat events at exact µs, ordered (time, phase, sequence).
- **Separation:** Unity code turns input into commands and renders snapshots. It never
  computes damage, hits, cooldowns or deaths.
- **Server authority:** clients never decide combat outcomes, offline or online.
- **TDD for combat math.** Write the failing test first. Parity tests compare against
  generated fixtures in `game/parity/fixtures/`, never against hand-typed numbers.
- **Never invent champion statistics.** Every number in `game/content` is a provenance field
  `{value, status, source}`. Unknown ⇒ `status: "unresolved"`, `value: null`, mechanic gated
  off and labelled "unsupported". Do not fill gaps from memory, PC LoL, or guesses.
- **IP boundary.** Riot data only in `game/content/reference-riot/` (not shippable). Shipped
  content and art are original or licensed. Never copy files from `assets/riot/`,
  `static/marksman-3d/` or `assets/marksman-3d/models/` into `game/`. See
  `docs/moba/10-legal-and-ip.md`.
- **Ownership.** Each path has exactly one owner (`.claude/ownership.json`). Parallel agents
  only write inside their own paths; shared contracts change via the protocol in
  `.claude/rules/integration.md`. Check with
  `python -I tools/ownership/check_ownership.py diff --owner <agent>`.
- **Done means proven.** Never report completion unless the milestone's acceptance tests pass.
  Report: work completed, test/build evidence, unverified assumptions, blockers, next milestone.
  List anything that still needs manual verification.
- **Do not mass-implement.** One milestone at a time; each stays independently playable.

## Commands

```sh
python -I tools/ci/fast_checks.py                     # T1: lint, content, ownership, tool tests, fixture freshness, dotnet test
dotnet test game/sim/tests/SharpWR.Sim.Tests.csproj   # C# sim tests (needs .NET 8 SDK)
python -I tools/parity/export_parity_fixtures.py      # regenerate parity fixtures from the Python engine
python -I tools/parity/emit_fix64_vectors.py          # regenerate bit-exact Fix64 vectors
python -I tools/data_import/import_reference_champion.py Samira
python -I tools/content/validate_content.py
python -I tools/sim_lint/sim_lint.py [files]
python -I tools/ownership/check_ownership.py map|owner <path>|diff --owner <name>
# Damage Lab reference suites (unchanged):
python -m unittest discover -s tests && for t in tests/*.cjs; do node "$t" || exit 1; done
```

Run Python tools with `-I`. The Stop hook runs the fast tier automatically when game files changed.

## Agents

`combat-engineer`, `champion-implementer`, `unity-gameplay`, `gameplay-ai`,
`network-engineer`, `data-verification`, `qa` (in `.claude/agents/`). The main session is the
lead: it plans, assigns one owner per task, integrates, and asks `qa` for acceptance.

## Language

Docs and code in English. The Damage Lab's existing Turkish docs stay as they are.
