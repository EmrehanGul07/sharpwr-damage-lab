# 02 · Data migration strategy

Goal: move numbers from the Damage Lab into the game **without losing provenance and without
inventing anything**, and keep the two in agreement as either side changes.

## Principles

1. **One direction.** Python Damage Lab → exporters in `tools/` → `game/content` and
   `game/parity`. The game never writes back. The Damage Lab is protected by a PreToolUse hook.
2. **Generated, not hand-typed.** Reference content and fixtures are produced by scripts with
   `--check` modes; CI fails when a committed file is stale relative to the Python source.
3. **Every number is a provenance field**:
   `{"value": "60", "status": "wr_wiki", "source": "https://…#hp_base"}`.
   Values are **decimal text** so `Fix64.Parse` is exact and platform independent.
4. **Unknown stays unknown.** `status: "unresolved"` ⇒ `value: null`. The sim refuses to
   run a mechanic whose required fields are unresolved and the UI labels it
   "Unsupported: <reason>".
5. **IP boundary.** Riot reference data lives only in `game/content/reference-riot/`
   (`ip: "riot-reference"`, `shippable: false`). Shippable content is `ip: "original"` and may
   only use `original_design` / `original_placeholder` / `unresolved` statuses, so Riot
   numbers cannot leak into a shipped champion by copy-paste (validator rule R4).

## Status vocabulary

| Status | Meaning | Allowed in |
|---|---|---|
| `wr_verified_user` | Explicit user Wild Rift confirmation recorded in the Damage Lab | reference |
| `wr_wiki` | Wild Rift wiki data template (URL + parameter + retrieval time) | reference |
| `damage_lab_preserved` | Existing Damage Lab value (`existing_user_preserved`) | reference |
| `damage_lab_user_sourced` | Damage Lab value from user evidence keys (D0xx), not re-verified | reference |
| `pc_reference_provisional` | PC LoL value used as a labelled stand-in | reference |
| `original_design` | SharpWR design value for original content | original |
| `original_placeholder` | Temporary design value; release checklist blocks it | original |
| `unresolved` | Unknown; value null; mechanic gated off | both |

## Mapping (Damage Lab → game content)

| Damage Lab source | Game target | Tool | Status |
|---|---|---|---|
| `data/marksman_champion_stats.json` (+ `field_sources`) | `champion.stats.*` | `tools/data_import/import_reference_champion.py` | Samira done |
| `sharpwr/champion_skill_data.py SAMIRA_ABILITIES` | `champion.abilities.{Q,W,E,R}` base/ratios/CD/mana/crit | same | Samira done |
| `data/marksman-skill-geometry.json` | `ability.geometry` (shape, range, width, radius) | same | Samira done |
| `docs/samira-mechanics-reference.json` (PC) | cast times, projectile speeds (provisional) | same | Samira done |
| Passive interpolation inside `replay_samira` | `champion.passive` | — | **unsupported** (provisional formula; not exported) |
| `data/damage-classification.json` | `damage.flags` (BasicAttack/ActiveSpell/Proc, on-hit) | M2 | planned |
| `sharpwr/catalog.py` items, `app-data/database.json` items/boots | reference items | M3 | planned |
| `sharpwr/rune_runtime.py`, `rune_database.py` | reference runes | M3 | planned |
| Other 22 marksmen | per champion, data-verification agent | M3+ | planned |

Known source duplications resolved during migration: `champion_abilities.py` is a byte copy of
`champion_skill_data.py` (importer reads the latter); Samira base stats exist in both
`catalog.C` and the stats JSON (importer reads the JSON and its `field_sources`).

## Parity fixtures

`tools/parity/export_parity_fixtures.py` calls the Python engine directly and writes
`game/parity/fixtures/samira-reference-v1.json`: 15 level-stat cases, 60 resistance cases,
270 ability-damage cases, 3 AA timeline scenarios, with a fingerprint (Damage Lab version,
git head, SHA-256 of the 7 source files) and tolerances. Bumping the fixture version is required
when the expected values change on purpose; the PR must explain why.

## Original content workflow (shippable)

1. Design writes `game/content/champions/<id>.champion.json` with `ip: "original"`.
2. Every number is `original_design` or `original_placeholder` with a `source` pointing at the
   design doc/ticket.
3. The same validator, sim and tests apply; balance targets (TTK bands) come from design,
   optionally informed by Damage Lab *aggregates* (e.g. "marksman level-9 DPS band"), never
   by copying a Riot champion's table.
