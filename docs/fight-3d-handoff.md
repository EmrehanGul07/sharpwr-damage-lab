# Build Lab 3D replay — 7.1.1

Base: main 8157af9. Branch: codex/fight-3d-replay.

## What changed

The existing recorded-trace player was wired to tier-search results and an Ezreal example, but not the Build Lab Replay fight action. Build Lab now records movement for its winning policy and passes that exact result to replay_payload/replay_html. Candidate searches do not record motion. The engine formulas, selected build, rune settings and search policy are unchanged.

The shared scene now renders a target HP bar. Replay displays item/rune stack snapshots from the last recorded impact, explicitly labeled with their timestamp. It does not invent expiry events between impacts. Seeking backwards clears later state. Custom build replays are labeled Your build rather than Top build.

## Scope

Web Build Lab only. Mobile full fight computation remains BL4. The target still does not attack. Existing renderer motion projection, visual-flight matching and WR timing assumptions remain. This is not a new damage engine or a claim of WR parity. Results are displayed after Replay fight and regenerated when requested, consistent with the existing Build Lab table lifecycle.

## Validation

- Streamlit integration covers all 23 champions at level 15, and all champions at level 1.
- Integration verifies replay motion, champion/source identity, summed impact damage, event count and final target HP against the displayed result.
- ReplayState tests cover same-timestamp event ordering and backward seek for stack snapshots.
- Existing combat replay and rune/UI regressions run unchanged.

Validation result: 303 Python tests passed; all JavaScript test scripts passed; combat audit 3,312 scenarios / 6,912 fights / zero failures. Browser visual inspection was blocked because Chromium was unavailable and its download failed. Review the rendered scene before production merge.

## Next work

Mobile BL4 and the TypeScript fight engine remain open. Skill HUD icons and a richer champion-specific state display can be added independently. Jhin mechanics remain pending the user measurements in ingame-test-todo.md; do not infer those values from animation.
