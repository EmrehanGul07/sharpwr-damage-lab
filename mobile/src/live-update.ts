/**
 * Live updates (preview builds). The Android workflow publishes the web screens as a zip next to
 * the APK on the mobile-preview release. The app downloads a newer version in the background and
 * switches to it the next time it starts. Only a change to the Android shell itself
 * (mobile/native.json) still needs a new APK; then the app offers the APK download instead.
 */
import { Capacitor, CapacitorHttp } from "@capacitor/core";
import { CapacitorUpdater } from "@capgo/capacitor-updater";
import { type KeyValueStore, isNewerVersion } from "./online";

const RELEASE = "https://github.com/EmrehanGul07/sharpwr-damage-lab/releases/download/mobile-preview";
export const WEB_UPDATE_URL = `${RELEASE}/sharpwr-web.json`;
export const APK_URL = `${RELEASE}/sharpwr-database-preview.apk`;
const PENDING_KEY = "sharpwr.update.pending";
const FAILED_KEY = "sharpwr.update.failed";
const TIMEOUT_MS = 10_000;

/** sharpwr-web.json, written by .github/workflows/mobile-android.yml. */
export interface WebUpdate {
  version: string;
  /** Oldest installed APK that can run these screens. */
  minApkVersion: string;
  url: string;
  /** SHA-256 of the zip; the updater refuses a download that does not match. */
  checksum: string;
}

export function isWebUpdate(value: unknown): value is WebUpdate {
  const update = value as Partial<Record<keyof WebUpdate, unknown>> | null;
  return (
    typeof update?.version === "string" &&
    typeof update.minApkVersion === "string" &&
    typeof update.url === "string" &&
    update.url.startsWith(`${RELEASE}/`) &&
    typeof update.checksum === "string" &&
    /^[0-9a-f]{64}$/.test(update.checksum)
  );
}

export type UpdatePlan = { action: "none" } | { action: "download"; update: WebUpdate } | { action: "apk"; version: string };

/** What to do about a published update, given the running screens, the installed APK and a failed version. */
export function planUpdate(update: WebUpdate, running: string, apk: string, failed: string | null): UpdatePlan {
  if (!isNewerVersion(update.version, running) || update.version === failed) return { action: "none" };
  if (isNewerVersion(update.minApkVersion, apk)) return { action: "apk", version: update.version };
  return { action: "download", update };
}

/**
 * Call once per launch. A version set for this launch that is still not running did not start
 * (the updater rolled it back), so it is remembered as failed and not downloaded again.
 * Returns the failed version, if any.
 */
export function recordLaunch(store: KeyValueStore, running: string): string | null {
  const pending = store.getItem(PENDING_KEY);
  if (pending && isNewerVersion(pending, running)) store.setItem(FAILED_KEY, pending);
  store.setItem(PENDING_KEY, "");
  return store.getItem(FAILED_KEY) || null;
}

const native = Capacitor.isNativePlatform();
let apkVersion: string | null = null;

/** First thing on every launch: tells the updater these screens started, so it keeps them. */
export function confirmStarted(): void {
  if (native) void CapacitorUpdater.notifyAppReady();
}

/** Version of the installed APK; null outside the Android app or before it is known. */
export function installedApkVersion(): string | null {
  return apkVersion;
}

export async function readApkVersion(): Promise<string | null> {
  if (!native) return null;
  try {
    apkVersion = (await CapacitorUpdater.getBuiltinVersion()).version;
  } catch {
    apkVersion = null;
  }
  return apkVersion;
}

/** Latest published update, or null when offline or when there is none. */
export async function latestWebUpdate(): Promise<WebUpdate | null> {
  try {
    // A native request: GitHub release downloads do not allow browser (CORS) requests.
    const response = await CapacitorHttp.get({
      url: WEB_UPDATE_URL,
      responseType: "json",
      connectTimeout: TIMEOUT_MS,
      readTimeout: TIMEOUT_MS,
    });
    const data: unknown = typeof response.data === "string" ? JSON.parse(response.data) : response.data;
    return response.status === 200 && isWebUpdate(data) ? data : null;
  } catch {
    return null;
  }
}

/** Downloads the update and sets it for the next launch. False when the download or its check failed. */
export async function downloadForNextLaunch(store: KeyValueStore, update: WebUpdate): Promise<boolean> {
  try {
    const bundle = await CapacitorUpdater.download({ url: update.url, version: update.version, checksum: update.checksum });
    await CapacitorUpdater.next({ id: bundle.id });
    store.setItem(PENDING_KEY, update.version);
    return true;
  } catch {
    return false;
  }
}

/** Restarts the app on the downloaded screens. */
export function restartNow(): void {
  void CapacitorUpdater.reload();
}
