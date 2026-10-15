# 06 · Automated testing strategy

"Done" means the acceptance tests for that milestone pass in CI and the runnable build was
produced. Anything not covered by automation is listed as **manual verification** in the
milestone report.

## Tiers

| Tier | What | Runs where | Time budget |
|---|---|---|---|
| T0 hooks | determinism lint on edited sim file; content validation on edited content | Claude Code PostToolUse | < 1 s |
| T1 fast | `tools/ci/fast_checks.py`: lint, content, ownership map, tool unit tests, fixture freshness, `dotnet test` | Stop/SubagentStop hooks, every push | < 60 s |
| T2 sim | NUnit: Fix64 vectors (bit-exact), parity vs Python, determinism (same seed → same hash), property tests (damage monotonic in AD, never negative after mitigation), scenario tests | CI matrix: ubuntu x64, ubuntu ARM64, windows, macOS | < 5 min |
| T3 Unity EditMode | presentation logic: input mapping, camera math, view interpolation | Unity test runner (GameCI) | < 5 min |
| T4 Unity PlayMode / acceptance | scripted matches in a scene: champion kills dummy, bot duel completes, respawn | `com.sharpwr.acceptance` | < 15 min |
| T5 build | Android IL2CPP APK + desktop build produced and smoke-launched (headless where possible) | CI on main and release branches | < 30 min |
| T6 device | frame time / memory on real phones | manual or device farm, per milestone | report |
| Reference | Damage Lab's own suites (unchanged) + `--check` of every exporter | CI | existing |

## Test-driven rules for combat code

* Write the failing test first for every formula and gate; commit tests with the change.
* Parity tests compare to generated fixtures only — never to numbers typed into the test.
* Every bug fix adds a regression test reproducing it via commands + seed.
* Determinism: any test that runs a match also asserts the final `EventLog.Hash` equals a second
  run's hash.
* Cross-platform: T2 runs on ARM64 and x64; Fix64 vectors guarantee bit-equality.

## Parity harness

```
sharpwr (Python) ──export_parity_fixtures.py──► game/parity/fixtures/*.json ◄── NUnit parity tests (C#)
                 └─fixed_point_model.py (bit-exact model) ──emit_fix64_vectors.py──► fix64-vectors-v1.json
```

Tolerances live in the fixture (`stat 1e-6`, `multiplier 1e-9`, `damage 1e-3 HP`,
`time 1e-5 s`). Measured in M0 with the bit-exact model: stat 1.3e-8, multiplier 1.3e-10,
damage 2.7e-7, time 1.1e-6.

## Hooks configured (`.claude/settings.json`)

| Hook | Script | Effect |
|---|---|---|
| PreToolUse Edit/Write | `.claude/hooks/guard_paths.py` | blocks edits to the Damage Lab (unless `SHARPWR_ALLOW_REFERENCE_EDIT=1`) and Riot-derived art in `game/` |
| PostToolUse Edit/Write | `.claude/hooks/post_edit_checks.py` | sim lint / content validation on the edited file; exit 2 returns findings to Claude |
| Stop, SubagentStop | `tools/ci/fast_checks.py --hook` | T1 when game files changed; failures keep the agent working; loop-safe |

## Unity CI (M1)

GameCI (`game-ci/unity-test-runner`, `game-ci/unity-builder`) needs a Unity license secret
(`UNITY_LICENSE` or serial + email/password). Setting secrets is a manual step for the
repository owner; until then T3–T5 run locally and the milestone report says so.
