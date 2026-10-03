# SharpWR Damage Lab — V5.87.0

Wild Rift damage research app: 23 marksman adapters, level 1–15 stats, expected crit, item callbacks, mana/cooldowns, movement and deterministic fight replays. Entry point: `streamlit_app.py`.

The model covers a stationary target that does not attack back. Authorized PC timing proxies and unresolved WR rules remain explicit assumptions. Automated tests check the implemented model; they do not establish real Wild Rift parity.

## Current controls

- Published 7.3a tier board is read-only. Public build searches remain disabled, including synthetic clicks.
- Build Lab supports 5 distinct completed items and one boots slot. Replay uses champion skills and persistent rune stats; the separate “Calculate build” action is the legacy AA-only calculation.
- Replay supports Conqueror, Lethal Tempo, initial-engagement First Strike, Dark Harvest and the supported damage/stat runes. Unsupported offensive loadouts block replay instead of silently dropping their effects.
- First Strike models only the explicitly ready initial three-second engagement; rearming and gold are excluded. Adaptive damage procs retain the existing ADC physical assumption.
- Yun Tal starting crit/Flurry, Energized launch consumption, Spellblade readiness, manual base mana and persistent rune settings reach replay.
- Recorded core items use a bounded search, not exhaustive/global optimization. Source fingerprints guard saved results.

## Run and validate

```sh
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
python -m unittest discover -s tests
node tests/test_replay_state.cjs
python scripts/audit_combat_matrix.py
```

The integrity audit writes `data/combat-audit-current.json` and `data/combat-audit-traces-current.json`; historical audits remain unchanged. It exits with failure when any scenario fails.

## Current work and evidence

- [Offline completion report](docs/offline-completion-20261003.md)
- [Active WR evidence TODO](docs/ingame-test-todo.md)
- [Per-champion queue](docs/marksman-task-queue.md)
- [Current adapters and runtime assumptions](docs/all-marksman-fight-engine.md)
- [Core-item protocol](docs/core-item-protocol.md)

## Deploy

Streamlit Community Cloud uses this repository's `main` branch and `streamlit_app.py`. The published tier board and its saved data are separate from the research calculator.
