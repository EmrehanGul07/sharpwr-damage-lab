# SharpWR Android app

An English Wild Rift marksman Database for Android: champions with stats at every level and their abilities (icon, cooldown and mana per rank, SharpWR's English summary), items, components, boots and runes, plus SharpWR's published item tier list, each champion's saved build results (SharpWR's core item pick beside the engine's, the rune page with a keystone check, Top 3 builds per level and target from every item, build styles and the item ranking) Build Lab, which calculates a build's stats on the phone, a 3D tab on every champion page with the champion's skinned model and its eight studio animations, and the Practice tab, where any champion walks around, casts its skills at a training dummy and the user keeps notes. It reads the same data as the web app, works offline, downloads data updates when the phone is online and installs new screens by itself (live updates). Free fan project; the Riot Games notice is on the About screen and under every list.

## Layout

| Path | Content |
|---|---|
| `mobile/src/` | TypeScript UI (no framework): data loader, data updates (`online.ts`), live updates (`live-update.ts`), formatting, search, hash router, views |
| `mobile/src/engine/` | TypeScript port of engine functions, checked against Python golden outputs (`app-data/golden/`) |
| `mobile/tests/` | Vitest unit tests, including checks against the real `app-data/database.json` and the golden outputs |
| `mobile/scripts/sync-data.mjs` | Copies `app-data/database.json`, `app-data/practice.json` and `assets/riot/` into `mobile/public/` before every build |
| `mobile/android/` | Capacitor Android project |
| `scripts/make_app_icons.py` | Draws the app icon (gold arrow through a crosshair ring on navy) and the splash screens into `mobile/android/.../res/`, plus `mobile/resources/icon-512.png` for store listings. Android 12+ shows the launcher icon on `values/colors.xml` `splash_background` |
| `mobile/native.json` | Oldest APK that can run the current screens, and the fingerprint of the Android shell |
| `.github/workflows/mobile-android.yml` | Tests, builds and packs the preview APK and the live update |

## Develop

```sh
cd mobile
npm ci
npm run dev        # browser preview with live reload
npm test           # unit tests
npm run build      # sync data, type-check, bundle into dist/
npx cap sync android
cd android && ./gradlew assembleDebug   # needs JDK 21 and the Android SDK
```

When champion, item or rune data changes, run `python scripts/export_app_data.py` at the repository root first; the next build picks the new file up.

## 3D tab

`src/views/model3d.ts` shows the champion's model from the web Animation Studio (`static/marksman-3d/<id>/character.glb`, see [roster-v8.md](roster-v8.md)) with buttons for Idle, Run, Attack, P, Q, W, E and R; the caption names the ability. Drag turns the model. The model downloads from this repository's `main` branch the first time the tab opens (network first, so updated models arrive) and is kept in Cache Storage for offline use. Three.js (a dev dependency, so the Android shell fingerprint is unchanged) loads as a separate chunk only when the tab opens. One viewer runs at a time and releases its GPU resources when the tab is left.

## Practice tab

`src/views/practice.ts` runs the web Practice Tool ([practice-tool.md](practice-tool.md)) on the phone: the shared scripts in `assets/marksman-3d/` run as classic scripts (`src/practice-scripts.ts`), the scene uses bundled Three.js and bundled GLBs, with the 3D tab's model cache as a fallback, and the data is `app-data/practice.json`. Everything loads only when the tab opens. "Full screen" covers the app window; the Android back button leaves it. The 3D tab links to it ("Practice with …"). Notes stay on the phone; "Copy all notes" copies them as Markdown.

## Build Lab

The Build tab picks a champion, level, five items and boots (plus Senna's Mist and Yun Tal stacks) and shows the stats at the start of a fight. `src/engine/build.ts` ports `sharpwr/build_stats.py` operation by operation; `tests/build.test.ts` compares it with `app-data/golden/build-stats.json`: exact where no level stat is involved, within 1e-6 where the exported 4-decimal level stats are (health, mana, armor, MR, and AD with Manamune/Muramana). Pickers disable items that make a build illegal and say why (`build_rules`). The build is saved on the phone; champion pages open their builds in Build Lab with "Try in Build Lab". A switch counts the champion's SharpWR rune page (`rune_stats`: attack speed, AD, ability haste, mana at the level), as the saved build results do; golden cases cover builds with and without it. Version 0.8.0 adds custom target HP, armor, MR, bonus HP and AA reduction, a native TypeScript AA-only benchmark, and full skill fights calculated offline in a dedicated Python/WASM worker. The rune switch applies the same full rune loadout as the Python engine. The AA-only baseline deliberately excludes champion abilities/passives and runes, and retains Python sim_build's final-cycle duration convention; full-fight TTK is the actual recorded defeat event.

`engine_bridge.py` calls BuildFightEvaluator and records only the winning policy. `scripts/sync-engine.mjs` bundles Pyodide 0.28.3 and the exact Python sources/data beside the app (about 13 MB); no runtime/CDN/server connection is required. Every operation gets an isolated worker, terminated on completion, cancellation, navigation or a 180s timeout. Startup repeats per fight to release WASM memory; device timings are not yet measured.

The recorded replay uses the web HTML/state/scene adapter with bundled Three.js and GLBs for all 23 champions. Play/pause, speed, event stepping, seeking, cameras, range, motion trail, HP, mana, cooldowns and last-impact stack snapshots use the captured engine trace. Models in `public/assets/models` work without a first download. Existing WR timing uncertainties and the stationary target assumption remain.

Parity fixtures are generated by `scripts/export_attack_golden.py` (690 AA sequences / 8,280 hits plus AA fight summaries) and `scripts/export_mobile_fights.py` (69 full fights: 23 champions at levels 1, 9 and 15, rune on/off and surviving targets). Compressed golden files are deterministic gzip. `npm test` regenerates the bundled source files before testing WASM against those CPython traces. These tests verify implementation parity, not new in-game WR evidence.

## Online updates

All addresses are in `mobile/src/online.ts` and `mobile/src/live-update.ts`; [third-party-assets.md](third-party-assets.md) lists them too.

- **Data:** at every launch the app downloads `app-data/database.json` from the `main` branch (`raw.githubusercontent.com`). A copy that passes the check in `isUsableDatabase` (same `schema`, every section present) is saved on the phone and shown from the next screen on. Offline, the app shows the last saved copy, or the copy bundled with it. A newly installed build ignores copies saved by the previous build until it is online again. So data changes on `main` reach installed apps without a new APK; a change old apps cannot read must raise `schema` ([app-data.md](app-data.md)), and old apps then keep their data until they are updated.
- **Icons:** an icon that a data update adds but the APK does not bundle loads from the same branch; offline it shows an empty placeholder.
- **New screens (live updates, preview builds only):** the app is a web page inside an Android shell, so most changes only replace the web part. The workflow zips `dist/` as `sharpwr-web-<version>.zip` and writes `sharpwr-web.json` (`version`, `minApkVersion`, `url`, `checksum`) to the `mobile-preview` release. At launch the app reads that manifest; when its `version` is higher than the running screens and the installed APK is at least `minApkVersion`, it downloads the zip in the background with [`@capgo/capacitor-updater`](https://github.com/Cap-go/capacitor-updater) (MPL-2.0), which verifies the SHA-256, and switches to it on the next start or when the user taps "Restart now". So: raise `version` in `mobile/package.json` for every change users should get.
  - **Safety:** the app calls `notifyAppReady` first thing on every launch; screens that do not get that far within 10 seconds are rolled back, and the app remembers that version as failed and does not download it again. Installing a new APK discards downloaded screens.
  - **Privacy:** the plugin runs in manual mode with its update, statistics and channel addresses set to `""` (`capacitor.config.json`), so it contacts nothing but the URLs above.
  - **New APK:** when the Android shell changes (Capacitor or plugin versions, anything under `android/`, `capacitor.config.json`), `tests/native.test.ts` fails until `mobile/native.json` gets the new fingerprint and `minApkVersion` is raised to the current `version`. Older APKs then skip the screens and offer the APK download instead.
  - **Google Play:** Play allows live updates of web code, but this channel is for preview builds: they are built with `VITE_PREVIEW_BUILD=1`, which also turns on the APK download notice that Play forbids. A Play build gets its own release channel (roadmap T4).

## Preview builds

Every push that touches `mobile/`, `app-data/` or `assets/riot/` runs the workflow. Each run keeps the APK as a workflow artifact; runs on `main` also publish it to the [`mobile-preview` release](https://github.com/EmrehanGul07/sharpwr-damage-lab/releases/tag/mobile-preview) as `sharpwr-database-preview.apk`, at a stable download link.

- **Version:** `mobile/package.json` `version` is the version name; the workflow run number is the version code, so each build installs over the previous one.
- **Signing:** preview APKs are signed with `mobile/android/app/preview.keystore`, which is committed on purpose so updates install in place. It is not a release key. A Play Store build must be signed with a private key kept outside the repository (roadmap T4).
- **App ID:** `io.github.emrehangul07.sharpwr`. It becomes permanent once the app is on Google Play; change it before then if needed (`mobile/capacitor.config.json` and `mobile/android/app/build.gradle`).
