# Fight Lab handoff — web 7.1.3 / mobile 0.8.2

Base main: 8157af9. Branch: codex/fight-3d-replay. PR: #20.

## Completed work

1. Web Build Lab records the winning fight policy and opens that exact trace in the shared 3D replay. Candidate searches do not retain motion. Target HP, event inspection and last-impact item/rune stack snapshots are shown. ReplayState loads before the first animation frame.
2. Mobile native TypeScript AA kernel and AA-only cycle TTK/DPS benchmark match Python: 690 champion/level/item sequences, 8,280 per-hit comparisons, plus 690 full AA benchmark summaries. Decimal rounding follows CPython's exact binary-float ties-to-even behavior.
3. Full mobile fights run the same Python engine offline in a bundled Pyodide 0.28.3 worker, including all 23 champions, skills, mana, cooldowns, champion passives, rune loadouts, movement and TTK. This deliberately revises the earlier full TypeScript port plan; a native TypeScript fight scheduler has NOT been implemented. No server or runtime CDN is involved. The worker stays warm for repeated calculations, then releases after 30 seconds idle or immediately on cancellation/navigation/error/timeout.
4. Mobile replays the calculated trace using the shared web renderer, bundled Three.js and all 23 GLBs (full and CPU preview). WebGL attributes allocate through Three.js to avoid cross-window typed-array failures. HTML is copied as a static template to preserve its styles through Vite. Source JSON substitutions use callbacks so replacement metacharacters cannot corrupt scripts.
5. Mobile version 0.8.0, Android workflow, APK contents checks and documentation updated. Browser smoke tests run before Android packaging. APK build results are recorded on the PR/Actions run.

## Validation

- 303 Python tests passed, including Streamlit Build Lab integration for all 23 champions at levels 1 and 15.
- Shared JavaScript test scripts passed: motion/dash, skill geometry, animations, practice, replay ordering and stack seeking.
- Mobile CPython/WASM parity: 69 complete fights (23 champions at levels 1, 9 and 15), rune on/off, surviving targets; TTK, damage/DPS, selected rotation, every event's time/action/damage/mana and motion sample count match.
- Offline Chromium smoke tests at 390px and 1280px: Ezreal, Samira and Kai'Sa; actual worker computation, bundled GLB + WebGL, playback, reset/stack rewind, cancellation and navigation; zero page errors and no engine/model/CDN requests.
- Browser screenshots were visually inspected. npm build/type-check passes. Prior full combat audit: 3,312 scenarios / 6,912 fights / zero failures.

## Run/check

```sh
python scripts/export_attack_golden.py
python scripts/export_mobile_fights.py
cd mobile
npm ci
npm test
npm run build
npx playwright install chromium
npm run test:browser
npx cap sync android
cd android && ./gradlew assembleDebug
```

The golden files are deterministic gzip; regenerate intentionally after engine changes. sync-engine.mjs copies Python source files and the seven required engine data files. Add dependencies there if future Python imports read additional files. Android CI verifies the WASM runtime, Python source bundle and 23 full GLBs in the APK.

## Remaining constraints

The target is stationary and does not attack; results inherit the audited engine's WR evidence gaps. Jhin's pending in-game measurements remain in ingame-test-todo.md. AA-only is explicitly a legacy item-kernel baseline, excluding champion abilities/passives and runes; cycle duration includes the final attack interval. Full-fight TTK is the actual defeat event. Rendering uses representative lateral movement, never changes damage timing and is not validated WR footage.

The web bundle is about 65 MB uncompressed, including roughly 13 MB WASM/Python runtime and 44 MB full/preview GLBs. First fight startup and memory/performance on physical phones still need measurement; browser parity does not substitute for Android device validation. Smaller GLBs/native TypeScript scheduler can be considered later without changing the reference engine. A data-only online update cannot update the embedded Python motor; engine source changes travel with a live screen update/APK.

## Follow-up completed (0.8.1)

Persistent manual fight controls, warm worker, lighter rendering option, selected-profile-only replay data and skill icons/cooldown sweeps are implemented. The native shell is unchanged; publishing main produces the automatic live update. The separate Practice 1v1 base-kit sandbox is now implemented (see docs/duel-bot.md); Build Lab remains the audited stationary-target calculation. Explicit overrides are labeled at the mobile adapter boundary; the reference optimizer source and its cached-ranking fingerprint are unchanged.
