# SharpWR Android app

An English Wild Rift marksman Database for Android: champions with stats at every level, items, components, boots and runes, plus SharpWR's published item tier list and each champion's saved core-item results (core item, item ranking, Top 3 builds per level and target). The app shows saved results; it does not calculate. It reads the same data as the web app, works offline and downloads data updates when the phone is online. Free fan project; the Riot Games notice is on the About screen and under every list.

## Layout

| Path | Content |
|---|---|
| `mobile/src/` | TypeScript UI (no framework): data loader, online updates (`online.ts`), formatting, search, hash router, views |
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

## Online updates

All addresses are in `mobile/src/online.ts`; [third-party-assets.md](third-party-assets.md) lists them too.

- **Data:** at every launch the app downloads `app-data/database.json` from the `main` branch (`raw.githubusercontent.com`). A copy that passes the check in `isUsableDatabase` (same `schema`, every section present) is saved on the phone and shown from the next screen on. Offline, the app shows the last saved copy, or the copy bundled with it. A newly installed build ignores copies saved by the previous build until it is online again. So data changes on `main` reach installed apps without a new APK; a change old apps cannot read must raise `schema` ([app-data.md](app-data.md)), and old apps then keep their data until they are updated.
- **Icons:** an icon that a data update adds but the APK does not bundle loads from the same branch; offline it shows an empty placeholder.
- **New app version (preview builds only):** builds made with `VITE_PREVIEW_BUILD=1` (the workflow sets it) compare their version with `mobile/package.json` on `main` and offer the APK download when it is higher. Raise `version` for every change users should install; until the workflow finishes publishing that build (a few minutes), the link still serves the previous APK. Google Play builds must not set this flag: Play updates the app, and its policy forbids apps that update themselves from elsewhere.

## Preview builds

Every push that touches `mobile/`, `app-data/` or `assets/riot/` runs the workflow. Each run keeps the APK as a workflow artifact; runs on `main` also publish it to the [`mobile-preview` release](https://github.com/EmrehanGul07/sharpwr-damage-lab/releases/tag/mobile-preview) as `sharpwr-database-preview.apk`, at a stable download link.

- **Version:** `mobile/package.json` `version` is the version name; the workflow run number is the version code, so each build installs over the previous one.
- **Signing:** preview APKs are signed with `mobile/android/app/preview.keystore`, which is committed on purpose so updates install in place. It is not a release key. A Play Store build must be signed with a private key kept outside the repository (roadmap T4).
- **App ID:** `io.github.emrehangul07.sharpwr`. It becomes permanent once the app is on Google Play; change it before then if needed (`mobile/capacitor.config.json` and `mobile/android/app/build.gradle`).
