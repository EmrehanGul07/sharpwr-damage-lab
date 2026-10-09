# SharpWR Damage Lab — V7.1.5

Free, fan-made Wild Rift damage research app: 23 marksman adapters, level 1–15 stats, expected crit, item callbacks, mana/cooldowns, movement and deterministic fight replays, plus an original 3D Animation Studio. Entry point: `streamlit_app.py`; the UI-independent damage engine lives in `sharpwr/`. Target architecture and roadmap (including the planned Android app): [docs/architecture.md](docs/architecture.md).

The model covers a stationary target that does not attack back. Authorized PC timing proxies and unresolved WR rules remain explicit assumptions. Automated tests check the implemented model; they do not establish real Wild Rift parity.

## Current controls

- Published 7.3a tier board is read-only. Public build searches remain disabled, including synthetic clicks.
- Build Lab supports 5 distinct completed items and one boots slot. Replay uses champion skills and persistent rune stats; the separate “Calculate build” action is the legacy AA-only calculation.
- Android Build Lab 0.8.4 calculates AA DPS and full skill fights offline for all 23 champions, then plays the recorded fight with bundled 3D models.
- Build Lab’s “Replay fight” also plays the selected build’s recorded fight in 3D, with movement, timed casts, damage, target HP and event inspection.
- Replay supports Conqueror, Lethal Tempo, initial-engagement First Strike, Dark Harvest, Empowerment, Phase Rush, Fleet Footwork and the supported damage/stat runes (Sudden Impact included). Defensive and utility runes (Bone Plating, Second Wind, …) have no effect on the stationary benchmark. Unsupported offensive loadouts block replay instead of silently dropping their effects.
- Each champion has a default rune page chosen by the SharpWR editor (`data/default-rune-pages.json`, `sharpwr/rune_pages.py`): stacking runes fill with level (empty to 5, full from 9) and Dark Harvest has one soul per level. Every saved build result uses it (`BuildFightEvaluator(runes=...)`).
- First Strike models only the explicitly ready initial three-second engagement; rearming and gold are excluded. Adaptive damage procs retain the existing ADC physical assumption.
- Yun Tal starting crit/Flurry, Energized launch consumption, Spellblade readiness, manual base mana and persistent rune settings reach replay.
- Saved build results (`scripts/build_core_items.py`, [docs/core-item-protocol.md](docs/core-item-protocol.md)): a core-item search that leaves out Infinity Edge, Lord Dominik's Regards, Mortal Reminder, Serylda's Grudge and Terminus; Top builds and the editor's build styles from every item; a keystone check. SharpWR's own core pick (`data/editor-core-items.json`) is shown first with the engine's core beside it. Bounded searches, not exhaustive/global optimization. Source fingerprints and each champion's rune page guard saved results.
- Galeforce's Cloudburst follows the Wild Rift tooltip: 40–125 by level plus 35% bonus AD physical damage, 60 s cooldown.
- Animation Studio is presentation only: original stylized skinned models for all 23 marksmen, practice mode and range-aware skill indicators. It does not calculate damage.
- Practice Tool (web tab and Android Practice tab, [docs/practice-tool.md](docs/practice-tool.md)): walk around with any champion, cast every skill at a training dummy with the engine's numbers (no items or runes) and keep notes on what differs from Wild Rift.

## Run and validate

```sh
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
python -m unittest discover -s tests
npm ci --ignore-scripts
for test in tests/*.cjs; do node "$test" || exit 1; done
python scripts/audit_combat_matrix.py
black --check .   # engine package formatting; pip install black
python scripts/export_app_data.py   # refresh app-data/database.json after data changes
```

The integrity audit writes `data/combat-audit-current.json` and `data/combat-audit-traces-current.json`; historical audits remain unchanged. It exits with failure when any scenario fails.

## 3D assets

- Runtime models live in `static/marksman-3d/<champion>/`: `character.glb` for WebGL and `preview.glb` for the software renderer. Streamlit serves them at `app/static/` (`server.enableStaticServing` in `.streamlit/config.toml`); the studio falls back to the GitHub copy if that path is unreachable.
- Editable Blender sources and download packages are not tracked. The art workflow (`.github/workflows/marksman-art-package.yml`) rebuilds them with Blender when a build script or the art direction changes (`scripts/check_art_sources.py`) and publishes them to the [`art-sources` release](https://github.com/EmrehanGul07/sharpwr-damage-lab/releases/tag/art-sources). Local builds write to `build/`, which git ignores.

## Versioning

`VERSION` is the single version source. The app footer, the integrity audit and this title read or match it, and a test enforces that. Bump it with every release that changes Python code: the live server reloads the engine modules only when the version changes.

## Current work and evidence

- [Architecture and roadmap](docs/architecture.md)
- [Third-party assets and external hosts](docs/third-party-assets.md)
- [Mobile app data (`app-data/database.json`)](docs/app-data.md)
- [Android app (`mobile/`)](docs/mobile.md)
- [Offline completion report](docs/offline-completion-20261003.md)
- [Active WR evidence TODO](docs/ingame-test-todo.md)
- [Per-champion queue](docs/marksman-task-queue.md)
- [Current adapters and runtime assumptions](docs/all-marksman-fight-engine.md)
- [Core-item protocol](docs/core-item-protocol.md)
- [Skinned roster V8](docs/roster-v8.md)
- [Practice Tool](docs/practice-tool.md)

## Deploy

Streamlit Community Cloud uses this repository's `main` branch and `streamlit_app.py`. The published tier board and its saved data are separate from the research calculator.

## Legal

SharpWR isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
