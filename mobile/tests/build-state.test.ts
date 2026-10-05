import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { buildFromParams, buildInput, buildParams, cleanBuild, defaultYuntalStacks, emptyBuild, loadBuild, saveBuild } from "../src/build-state";
import type { Database } from "../src/data";
import type { KeyValueStore } from "../src/online";

const db = JSON.parse(readFileSync(new URL("../../app-data/database.json", import.meta.url), "utf8")) as Database;

function memoryStore(): KeyValueStore {
  const values = new Map<string, string>();
  return { getItem: (key) => values.get(key) ?? null, setItem: (key, value) => void values.set(key, value) };
}

describe("build state", () => {
  it("follows the web Tier List's Yun Tal stack defaults", () => {
    expect([1, 5, 6, 7, 8, 9, 15].map(defaultYuntalStacks)).toEqual([0, 0, 31, 63, 94, 125, 125]);
  });

  it("starts empty and saves between launches", () => {
    const store = memoryStore();
    expect(loadBuild(store, db)).toEqual(emptyBuild(db.champions[0].name));
    const state = { ...emptyBuild("Senna", 9), items: ["Infinity Edge", null, null, null, null], boots: "Berserker's Greaves" };
    saveBuild(store, state);
    expect(loadBuild(store, db)).toEqual(state);
    expect(state.mist).toBe(40);
  });

  it("drops what this data does not know", () => {
    const cleaned = cleanBuild(db, { champion: "Ezreal", level: 99, items: ["Infinity Edge", "Old Item"], boots: "Old Boots" });
    expect(cleaned?.level).toBe(15);
    expect(cleaned?.items).toEqual(["Infinity Edge", null, null, null, null]);
    expect(cleaned?.boots).toBeNull();
    expect(cleanBuild(db, { champion: "Teemo" })).toBeNull();
  });

  it("opens a linked build", () => {
    const params = new URLSearchParams(buildParams("Ezreal", 9, ["Muramana", "Nashor's Tooth"], "Spellslinger's Shoes"));
    const state = buildFromParams(db, params)!;
    expect(buildInput(state)).toEqual({
      champion: "Ezreal",
      level: 9,
      items: ["Muramana", "Nashor's Tooth"],
      boots: "Spellslinger's Shoes",
      mist: 0,
      yuntalStacks: 125,
    });
  });
});
