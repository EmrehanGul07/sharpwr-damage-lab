---
name: migrate-champion-data
description: Migrate a champion's numbers from the Python Damage Lab into game content with per-field provenance, generate its parity fixtures, and list unsupported mechanics. Use when a reference champion is needed for engine validation (data-verification agent).
---
# Migrate champion data (reference only)

Reference (Riot) champions are for private engine validation, never shippable content.

1. Inventory sources for the champion (read-only):
   - `data/marksman_champion_stats.json` (`stats`, `field_sources`, `missing_fields`)
   - ability table: `sharpwr/champion_skill_data.py` (Samira/Smolder) or
     `data/marksman-ability-catalogue.json` + `sharpwr/marksman_kits.py` (others)
   - geometry `data/marksman-skill-geometry.json`; timing `data/pc-combat-timing.json`
     (PC → `pc_reference_provisional`); open questions `docs/ingame-test-todo.md`,
     `docs/marksman-task-queue.md`, `data/marksman-runtime-assumptions.json`.
2. Extend `tools/data_import/import_reference_champion.py` (add the champion to `SUPPORTED`
   with a reader for its ability source). Every value → provenance field; unknown → `unresolved`/null.
3. Run it, then `python -I tools/content/validate_content.py`.
4. Extend `tools/parity/export_parity_fixtures.py` with the champion's cases by **calling the
   Python engine** (new fixture file `<champion>-reference-v1.json`).
5. Write the champion's `unsupported_mechanics` list from the open-questions sources; do not
   resolve any of them by assumption.
6. Run `python -I tools/ci/fast_checks.py`; report counts per status and the unsupported list.
