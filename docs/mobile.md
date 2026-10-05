# SharpWR Android app

An offline, English Wild Rift marksman Database for Android: champions with stats at every level, items, components, boots and runes. It reads the same data as the web app's Database tab and needs no network. Free fan project; the Riot Games notice is on the About screen and under every list.

## Layout

| Path | Content |
|---|---|
| `mobile/src/` | TypeScript UI (no framework): data loader, formatting, search, hash router, views |
| `mobile/tests/` | Vitest unit tests, including checks against the real `app-data/database.json` |
| `mobile/scripts/sync-data.mjs` | Copies `app-data/database.json` and `assets/riot/` into `mobile/public/` before every build |
| `mobile/android/` | Capacitor Android project |
| `.github/workflows/mobile-android.yml` | Tests, builds and packs the preview APK |

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

## Preview builds

Every push that touches `mobile/`, `app-data/` or `assets/riot/` runs the workflow. Each run keeps the APK as a workflow artifact; runs on `main` also publish it to the [`mobile-preview` release](https://github.com/EmrehanGul07/sharpwr-damage-lab/releases/tag/mobile-preview) as `sharpwr-database-preview.apk`, at a stable download link.

- **Version:** `mobile/package.json` `version` is the version name; the workflow run number is the version code, so each build installs over the previous one.
- **Signing:** preview APKs are signed with `mobile/android/app/preview.keystore`, which is committed on purpose so updates install in place. It is not a release key. A Play Store build must be signed with a private key kept outside the repository (roadmap T4).
- **App ID:** `io.github.emrehangul07.sharpwr`. It becomes permanent once the app is on Google Play; change it before then if needed (`mobile/capacitor.config.json` and `mobile/android/app/build.gradle`).
