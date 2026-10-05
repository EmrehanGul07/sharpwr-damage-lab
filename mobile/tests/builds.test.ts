import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { BUILD_LEVELS, TARGETS, championCore, coreChampions, findItem, stageFor, tierOf } from "../src/builds";
import type { Database } from "../src/data";

const db = JSON.parse(readFileSync(new URL("../../app-data/database.json", import.meta.url), "utf8")) as Database;

describe("tier list", () => {
  it("lists every completed item it ranks, once", () => {
    const names = db.tier_list!.tiers.flatMap((tier) => tier.items);
    expect(new Set(names).size).toBe(names.length);
    for (const name of names) expect(db.items.map((item) => item.name), name).toContain(name);
  });

  it("finds an item's tier", () => {
    expect(tierOf(db, "Yun Tal Wildarrows")).toBe("S");
    expect(tierOf(db, "Iceborn Gauntlet")).toBe("F");
    expect(tierOf(db, "Not an item")).toBeNull();
    expect(tierOf({ ...db, tier_list: undefined }, "Yun Tal Wildarrows")).toBeNull();
  });
});

describe("core builds", () => {
  it("has results for every champion", () => {
    for (const champion of db.champions) expect(championCore(db, champion.name), champion.name).not.toBeNull();
    expect(championCore({ ...db, core_items: undefined }, "Ezreal")).toBeNull();
  });

  it("has a Top 3 for every level and target, made of known items and boots", () => {
    for (const champion of db.champions) {
      const core = championCore(db, champion.name)!;
      for (const level of BUILD_LEVELS) {
        for (const target of TARGETS) {
          const stage = stageFor(core, level, target.key);
          expect(stage?.builds, `${champion.name} ${level} ${target.key}`).toHaveLength(3);
          for (const build of stage!.builds) {
            expect(build.items).toHaveLength(stage!.items_allowed);
            for (const name of build.items) expect(findItem(db, name)?.category, name).toBe("completed");
            expect(findItem(db, build.boots)?.category, build.boots).toBe("boots");
          }
        }
      }
      for (const row of core.ranking) expect(findItem(db, row.item), row.item).toBeDefined();
    }
  });

  it("links an item to the champions it is the core item for", () => {
    const names = (item: string) => coreChampions(db, item).map((champion) => champion.name);
    expect(names("Muramana")).toContain("Ezreal");
    expect(names("Infinity Edge")).toEqual([]);
    const total = db.champions.reduce((count, champion) => count + championCore(db, champion.name)!.core.length, 0);
    const linked = db.items.reduce((count, item) => count + coreChampions(db, item.name).length, 0);
    expect(linked).toBe(total);
  });
});
