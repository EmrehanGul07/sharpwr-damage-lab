# SharpWR Android app

An English Wild Rift marksman Database for Android: champions with stats at every level, items, components, boots and runes, plus SharpWR's published item tier list and each champion's saved core-item results (core item, item ranking, Top 3 builds per level and target). The app shows saved results; it does not calculate. It reads the same data as the web app, works offline, downloads data updates when the phone is online and installs new screens by itself (live updates). Free fan project; the Riot Games notice is on the About screen and under every list.

## Layout

| Path | Content |
|---|---|
| `mobile/src/` | TypeScript UI (no framework): data loader, data updates (`online.ts`), live updates (`live-update.ts`), formatting, search, hash router, views |
| `mobile/tests/` | Vitest unit tests, including checks against the real `app-data/database.json` |
| `mobile/scripts/sync-data.mjs` | Copies `app-data/database.json` and `assets/riot/` into `mobile/public/` before every build |
| `mobile/android/` | Capacitor Android project |
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
