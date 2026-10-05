import { describe, expect, it } from "vitest";
import { type WebUpdate, WEB_UPDATE_URL, isWebUpdate, planUpdate, recordLaunch } from "../src/live-update";
import type { KeyValueStore } from "../src/online";

const RELEASE = WEB_UPDATE_URL.slice(0, WEB_UPDATE_URL.lastIndexOf("/"));
const update: WebUpdate = {
  version: "0.4.1",
  minApkVersion: "0.4.0",
  url: `${RELEASE}/sharpwr-web-0.4.1.zip`,
  checksum: "a".repeat(64),
};

function memoryStore(): KeyValueStore {
  const values = new Map<string, string>();
  return { getItem: (key) => values.get(key) ?? null, setItem: (key, value) => void values.set(key, value) };
}

describe("published update", () => {
  it("accepts only a zip from this project's release with a SHA-256", () => {
    expect(isWebUpdate(update)).toBe(true);
    expect(isWebUpdate({ ...update, url: "https://example.com/sharpwr-web-0.4.1.zip" })).toBe(false);
    expect(isWebUpdate({ ...update, checksum: "1234abcd" })).toBe(false);
    expect(isWebUpdate({ ...update, minApkVersion: undefined })).toBe(false);
    expect(isWebUpdate(null)).toBe(false);
  });
});

describe("update plan", () => {
  it("downloads newer screens the installed APK can run", () => {
    expect(planUpdate(update, "0.4.0", "0.4.0", null)).toEqual({ action: "download", update });
  });

  it("does nothing when the screens are current or that version failed before", () => {
    expect(planUpdate(update, "0.4.1", "0.4.0", null)).toEqual({ action: "none" });
    expect(planUpdate(update, "0.5.0", "0.4.0", null)).toEqual({ action: "none" });
    expect(planUpdate(update, "0.4.0", "0.4.0", "0.4.1")).toEqual({ action: "none" });
  });

  it("offers the APK when the installed one is too old", () => {
    expect(planUpdate({ ...update, version: "0.5.0", minApkVersion: "0.5.0" }, "0.4.1", "0.4.0", null)).toEqual({
      action: "apk",
      version: "0.5.0",
    });
  });
});

describe("launch record", () => {
  it("keeps a version that started", () => {
    const store = memoryStore();
    store.setItem("sharpwr.update.pending", "0.4.1");
    expect(recordLaunch(store, "0.4.1")).toBeNull();
  });

  it("remembers a version that was set for this launch but did not start", () => {
    const store = memoryStore();
    store.setItem("sharpwr.update.pending", "0.4.1");
    expect(recordLaunch(store, "0.4.0")).toBe("0.4.1");
    // Later launches still skip it, until a newer version is published.
    expect(recordLaunch(store, "0.4.0")).toBe("0.4.1");
    expect(planUpdate({ ...update, version: "0.4.2" }, "0.4.0", "0.4.0", "0.4.1").action).toBe("download");
  });
});
