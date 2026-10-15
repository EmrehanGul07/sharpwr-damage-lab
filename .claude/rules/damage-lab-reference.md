---
paths:
  - "sharpwr/**"
  - "data/**"
  - "app-data/**"
  - "scripts/**"
  - "tests/**"
  - "mobile/**"
  - "assets/**"
  - "static/**"
  - "streamlit_app.py"
---
# Damage Lab (reference) rules

- This is the validation oracle for the game. Do not modify, reformat, move or delete it.
  Edits are blocked by `.claude/hooks/guard_paths.py`.
- To use its knowledge in the game, write or extend an exporter under `tools/parity` or
  `tools/data_import` that *calls* the Python engine or *reads* its data.
- Its own conventions still apply if the user explicitly asks for a reference change (bump
  `VERSION`, run its integrity audit, Turkish docs in `docs/`).
- Known duplicates: `sharpwr/champion_abilities.py` == `sharpwr/champion_skill_data.py`; read
  the latter. Samira stats exist in `sharpwr/catalog.py` and `data/marksman_champion_stats.json`;
  read the JSON and its `field_sources`.
