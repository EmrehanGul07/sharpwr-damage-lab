# 00 · Audit of the SharpWR Damage Lab

Audited: 15 Oct 2026, commit `4361afd` (Damage Lab `VERSION` 7.1.23, mobile 0.8.22). Read-only:
nothing in the existing project was modified. Baseline tests were run in a sandbox without
package-registry access (see "Test baseline").

## What the repository is

A deterministic **damage research tool** for 23 Wild Rift marksmen, plus a surprisingly deep
**real-time practice sandbox**:

| Layer | Where | Size | Notes |
|---|---|---|---|
| Python engine | `sharpwr/` (27 modules) | ~9.2k lines | UI-free (enforced by test). AA kernel, item callbacks, runes, champion adapters, build optimizer. |
| Champion fight adapters | `sharpwr/fight_engine.py` (Samira, Smolder), `sharpwr/marksman_fight_engine.py` (other 21) | 1.5k + 2.0k lines | Each is **one closure-heavy function** (`replay_samira` ≈1,480 lines to end of file, `replay_marksman` ≈1,960). Continuous float time, event-driven. |
| Data | `data/*.json`, `data/marksman_champion_stats.{csv,json}` | 18 MB | **Field-level provenance** (URL + parameter + retrieval time, or `existing_user_preserved`), explicit `missing_fields`, evidence keys (D0xx), PC-vs-WR separation. |
| Exported app data | `app-data/database.json` | 23 champions, 36 items, 23 components, 14 boots, 51 runes, 4 trees | Schema 1; feeds the Android app. |
| Golden fixtures | `app-data/golden/` | AA, build stats, 81 fight scenarios | Python → TypeScript parity precedent already exists. |
| Integrity audit | `scripts/audit_combat_matrix.py` | 3,312 scenarios / 6,912 fights | Before/after equality for refactors. |
| Web UI | `streamlit_app.py` | 1.8k lines | Thin shell. |
| Mobile app | `mobile/` (Capacitor + TS + Vite) | ~5.3k TS lines, 17 test files | TS AA/build port with golden tests; full fights via bundled **Pyodide/WASM** worker. |
| Real-time arena | `assets/marksman-3d/*.js` (three.js 0.169) | ~300 KB, dense one-line style | 120 Hz fixed clock, 1v1 bot with 4 difficulties, lane minions/towers, swept skillshots, mana/CC for some kits, Build Lab loadouts at impact. |
| 3D art | `static/marksman-3d/`, `assets/marksman-3d/models/` | 23 skinned GLBs (+ previews) | Original meshes, but **depict Riot characters**. |
| Riot images | `assets/riot/`, `data/riot/` | ~130 icons/portraits | Inventoried in `docs/third-party-assets.md`. |

## Reusable for the game (high value)

1. **Verified numbers with provenance** — champion stats, ability tables, mana, cooldowns,
   geometry, PC timing proxies, each labelled. This is the input to the data migration
   (`02-data-migration.md`) and the reason "never invent a stat" is enforceable.
2. **Combat formulas** — resistance/penetration (`aa_engine.rm`, `effective_resistance`),
   level growth (`gu`), crit scaling, ability scaling, item on-hit ordering, rune procs
   (`rune_runtime.py`: Conqueror, Lethal Tempo, First Strike, Dark Harvest, Phase Rush,
   Fleet Footwork…). Ported 1:1 to the C# core and checked by parity fixtures.
3. **Timed-combat rules already researched** for Samira (cast locks, W two-hit timing, E dash
   at 1600, R 10-shot channel, AA windup formula `base/(1+bonusAS*0.5)`), with every
   assumption written down (`docs/samira-timed-combat.md`).
4. **Damage classification** (`data/damage-classification.json`): BasicAttack / ActiveSpell /
   Proc tags and on-hit eligibility — maps directly onto the game's damage pipeline flags.
5. **Event logs** — `FightResult.log/timeline` already records order, time, action, damage,
   components, stacks before/after. This becomes the golden reference for scenario parity.
6. **Bot design** — `duel-bot.js`: observation delay, decision interval, aim error, prediction,
   dodge chance; difficulty never changes stats. A sound, fair AI contract to port.
7. **Test culture** — 296 Python tests, Node arena tests, mobile golden tests, integrity matrix.
   Parity-against-reference is already the house style.

## Current architectural limitations (for a real game)

| Limitation | Evidence | Consequence for the game |
|---|---|---|
| Expected-value crits | `mode="Expected"` default; outcomes Normal/Critical/Expected | Game needs rolled crits from a seeded RNG; parity uses Normal/Critical only. |
| Float, continuous time | `time` floats, event heap in Python | Not bit-reproducible across devices; game needs fixed point + fixed tick. |
| 1-D positions | `distance` scalar, "one-dimensional point-target approximation" | 2-D movement, collision radii, skillshot geometry must be new. |
| One attacker vs one stationary target | "target never attacks" | Multi-unit combat, incoming damage, healing, shields, CC on the player are new. |
| Monolithic champion functions | `replay_samira`, `replay_marksman` | Not portable as-is; re-expressed as data + small scripted hooks (`05-ability-framework.md`). |
| Duplicated sources | `sharpwr/champion_abilities.py` ≡ `champion_skill_data.py` (byte-identical); Samira stats in both `catalog.C` and the stats JSON | Migration reads one source per field and records which. |
| Arena JS is dense and untyped | one-line functions up to 1,144 chars | Keep as behaviour reference; do not port line-by-line. |
| Unresolved mechanics | `docs/ingame-test-todo.md` (Samira: R haste/start, W1–E–W2 order, refresh, CC assist attack, R offsets); passive melee bonus is a provisional interpolation | Shipped as **unsupported/labelled**, never guessed. |
| Committed signing key | `mobile/android/app/preview.keystore` | Fine for preview builds; never reuse for a store release. |

## Intellectual property — blocking finding

Riot's fan-content policy prohibits using its IP **in games and apps**, explicitly listing
character appearance, abilities, maps, icons and items
([Riot legal](https://www.riotgames.com/en/legal)). A playable MOBA with Samira's kit,
Riot champion likenesses (the 23 GLBs), Wild Rift items/runes or the Rift layout is outside
what the policy allows without a written license. The architecture therefore separates
**reference data** (private validation of the engine against the Damage Lab) from
**shippable content** (original champions, items, map, art). See `10-legal-and-ip.md`.
This also bears on the existing Android Practice/1v1 features; that is outside this audit's
scope to change, but the owner should be aware of it. This is not legal advice.

## Test baseline (sandbox, 15 Oct 2026)

| Suite | Result | Note |
|---|---|---|
| `python -m unittest discover -s tests` | 296 run: **289 pass**, 7 errors | All 7 are `ModuleNotFoundError: streamlit` (UI tests); registry blocked in sandbox, not a code failure. |
| `node tests/*.cjs` | **10 pass**, 7 fail to start | All 7 are `Cannot find module 'three'` (npm blocked in sandbox). |
| `mobile` (vitest) | not run | npm blocked. |
| `.NET` | not available | No SDK in sandbox; the new C# tests are therefore **not yet compiled** (CI does it). |

Unverified here and to be re-run on a normal machine: the 14 environment-blocked suites.
