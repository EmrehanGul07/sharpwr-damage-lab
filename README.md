# SharpWR Damage Lab — V7.0.7

Free, fan-made Wild Rift damage research app: 23 marksman adapters, level 1–15 stats, expected crit, item callbacks, mana/cooldowns, movement and deterministic fight replays, plus an original 3D Animation Studio. Entry point: `streamlit_app.py`; the UI-independent damage engine lives in `sharpwr/`. Target architecture and roadmap (including the planned Android app): [docs/architecture.md](docs/architecture.md).

The model covers a stationary target that does not attack back. Authorized PC timing proxies and unresolved WR rules remain explicit assumptions. Automated tests check the implemented model; they do not establish real Wild Rift parity.

## Current controls

- Published 7.3a tier board is read-only. Public build searches remain disabled, including synthetic clicks.
- Build Lab supports 5 distinct completed items and one boots slot. Replay uses champion skills and persistent rune stats; the separate “Calculate build” action is the legacy AA-only calculation.
- Replay supports Conqueror, Lethal Tempo, initial-engagement First Strike, Dark Harvest and the supported damage/stat runes. Unsupported offensive loadouts block replay instead of silently dropping their effects.
- First Strike models only the explicitly ready initial three-second engagement; rearming and gold are excluded. Adaptive damage procs retain the existing ADC physical assumption.
- Yun Tal starting crit/Flurry, Energized launch consumption, Spellblade readiness, manual base mana and persistent rune settings reach replay.
- Recorded core items use a bounded search, not exhaustive/global optimization. Source fingerprints guard saved results.
- Animation Studio is presentation only: original stylized skinned models for all 23 marksmen, practice mode and range-aware skill indicators. It does not calculate damage.

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
- [Offline completion report](docs/offline-completion-20261003.md)
- [Active WR evidence TODO](docs/ingame-test-todo.md)
- [Per-champion queue](docs/marksman-task-queue.md)
- [Current adapters and runtime assumptions](docs/all-marksman-fight-engine.md)
- [Core-item protocol](docs/core-item-protocol.md)
- [Skinned roster V7](docs/roster-v7.md)

## Deploy

Streamlit Community Cloud uses this repository's `main` branch and `streamlit_app.py`. The published tier board and its saved data are separate from the research calculator.

## Legal

SharpWR isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.
