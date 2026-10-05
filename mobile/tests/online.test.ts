import { readFileSync } from "node:fs";
import { afterEach, describe, expect, it, vi } from "vitest";
import { type Database, type DataState, isUsableDatabase } from "../src/data";
import {
  DATA_URL,
  type KeyValueStore,
  downloadDatabase,
  isNewerVersion,
  latestAppVersion,
  readSaved,
  remoteAsset,
  save,
} from "../src/online";

const db = JSON.parse(readFileSync(new URL("../../app-data/database.json", import.meta.url), "utf8")) as Database;

function memoryStore(): KeyValueStore & { values: Map<string, string> } {
  const values = new Map<string, string>();
  return { values, getItem: (key) => values.get(key) ?? null, setItem: (key, value) => void values.set(key, value) };
}

function serve(body: unknown, status = 200): void {
  vi.stubGlobal("fetch", vi.fn(async () => new Response(JSON.stringify(body), { status })));
}

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("database check", () => {
  it("accepts the repository's database", () => {
    expect(isUsableDatabase(db)).toBe(true);
  });

  it("rejects a newer schema, missing sections and broken records", () => {
    expect(isUsableDatabase({ ...db, schema: 2 })).toBe(false);
    expect(isUsableDatabase({ ...db, runes: undefined })).toBe(false);
    expect(isUsableDatabase({ ...db, champions: [] })).toBe(false);
    expect(isUsableDatabase({ ...db, items: [null] })).toBe(false);
    expect(isUsableDatabase(null)).toBe(false);
    expect(isUsableDatabase("database")).toBe(false);
  });
});

describe("download", () => {
  it("reads the database from the main branch", async () => {
    serve(db);
    await expect(downloadDatabase()).resolves.toEqual(db);
    expect(fetch).toHaveBeenCalledWith(DATA_URL, expect.objectContaining({ cache: "no-cache" }));
  });

  it("returns null for a format this app cannot read, an HTTP error or no network", async () => {
    serve({ ...db, schema: 2 });
    await expect(downloadDatabase()).resolves.toBeNull();
    serve(db, 404);
    await expect(downloadDatabase()).resolves.toBeNull();
    vi.stubGlobal("fetch", vi.fn(async () => Promise.reject(new TypeError("Failed to fetch"))));
    await expect(downloadDatabase()).resolves.toBeNull();
  });

  it("reads the published app version", async () => {
    serve({ name: "sharpwr-mobile", version: "0.3.1" });
    await expect(latestAppVersion()).resolves.toBe("0.3.1");
    serve({ name: "sharpwr-mobile" });
    await expect(latestAppVersion()).resolves.toBeNull();
  });

  it("points icons the app does not bundle at the repository", () => {
    expect(remoteAsset("assets/riot/items/new.png")).toBe(
      "https://raw.githubusercontent.com/EmrehanGul07/sharpwr-damage-lab/main/assets/riot/items/new.png",
    );
  });
});

describe("versions", () => {
  it("compares x.y.z numbers, not text", () => {
    expect(isNewerVersion("0.2.0", "0.1.0")).toBe(true);
    expect(isNewerVersion("0.10.0", "0.9.0")).toBe(true);
    expect(isNewerVersion("1.0", "0.9.9")).toBe(true);
    expect(isNewerVersion("0.2.0", "0.2.0")).toBe(false);
    expect(isNewerVersion("0.1.9", "0.2.0")).toBe(false);
  });
});

describe("saved data", () => {
  const state: DataState = { db, downloadedAt: "2026-10-05T11:48:51.000Z" };

  it("comes back for the build that saved it", () => {
    const store = memoryStore();
    save(store, "build-1", state);
    expect(readSaved(store, "build-1")).toEqual(state);
  });

  it("is ignored by another build, when corrupt, or when missing", () => {
    const store = memoryStore();
    expect(readSaved(store, "build-1")).toBeNull();
    save(store, "build-1", state);
    expect(readSaved(store, "build-2")).toBeNull();
    store.values.set("sharpwr.database", "{not json");
    expect(readSaved(store, "build-1")).toBeNull();
  });

  it("does not fail when storage is full", () => {
    const full: KeyValueStore = {
      getItem: () => null,
      setItem: () => {
        throw new DOMException("Quota exceeded", "QuotaExceededError");
      },
    };
    expect(() => save(full, "build-1", state)).not.toThrow();
  });
});
