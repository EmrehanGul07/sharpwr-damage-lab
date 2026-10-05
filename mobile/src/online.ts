/**
 * Online data updates. The app ships with its own copy of the Database and works offline. When the
 * phone is online it downloads the latest copy from this repository's main branch and saves it for
 * offline launches. New app screens arrive separately (src/live-update.ts).
 */
import { type Database, type DataState, isUsableDatabase } from "./data";

const REPO_RAW = "https://raw.githubusercontent.com/EmrehanGul07/sharpwr-damage-lab/main";
export const DATA_URL = `${REPO_RAW}/app-data/database.json`;

const TIMEOUT_MS = 10_000;
const SAVED_KEY = "sharpwr.database";

/** Online copy of a repository file the app does not bundle, e.g. the icon of a newly added item. */
export function remoteAsset(path: string): string {
  return `${REPO_RAW}/${path}`;
}

async function fetchJson(url: string): Promise<unknown> {
  // no-cache: ask GitHub whether the file changed instead of reusing a stale WebView copy.
  const response = await fetch(url, { cache: "no-cache", signal: AbortSignal.timeout(TIMEOUT_MS) });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

/** Latest Database from GitHub, or null when offline or when it is in a format this app cannot read. */
export async function downloadDatabase(url = DATA_URL): Promise<Database | null> {
  try {
    const data = await fetchJson(url);
    return isUsableDatabase(data) ? data : null;
  } catch {
    return null;
  }
}

/** True when `candidate` is a higher x.y.z version than `current`. */
export function isNewerVersion(candidate: string, current: string): boolean {
  const parse = (version: string) => version.split(".").map((part) => Number.parseInt(part, 10) || 0);
  const [next, now] = [parse(candidate), parse(current)];
  for (let index = 0; index < Math.max(next.length, now.length); index += 1) {
    const difference = (next[index] ?? 0) - (now[index] ?? 0);
    if (difference !== 0) return difference > 0;
  }
  return false;
}

/** The parts of localStorage the app uses, so tests can pass an in-memory store. */
export type KeyValueStore = Pick<Storage, "getItem" | "setItem">;

/**
 * Database saved by an earlier download. Only the app build that saved it reuses it: a newly
 * installed build starts from its own bundled copy until the phone is online again.
 */
export function readSaved(store: KeyValueStore, build: string): DataState | null {
  try {
    const raw = store.getItem(SAVED_KEY);
    if (!raw) return null;
    const saved = JSON.parse(raw) as { build?: unknown; downloadedAt?: unknown; db?: unknown };
    if (saved.build !== build || typeof saved.downloadedAt !== "string" || !isUsableDatabase(saved.db)) return null;
    return { db: saved.db, downloadedAt: saved.downloadedAt };
  } catch {
    return null;
  }
}

export function save(store: KeyValueStore, build: string, state: DataState): void {
  try {
    store.setItem(SAVED_KEY, JSON.stringify({ build, downloadedAt: state.downloadedAt, db: state.db }));
  } catch {
    // Storage full or unavailable: the downloaded data still shows until the app closes.
  }
}
