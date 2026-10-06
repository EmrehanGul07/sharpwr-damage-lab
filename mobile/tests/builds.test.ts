import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { BUILD_LEVELS, KEYSTONE_CHECK_LEVELS, TARGETS, championCore, coreChampions, coreItems, findItem, rankKeystones, stageFor, tierOf } from "../src/builds";
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
          const stage = stageFor(core.stages, level, target.key);
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
    const total = db.champions.reduce((count, champion) => count + coreItems(db, champion).length, 0);
    const linked = db.items.reduce((count, item) => count + coreChampions(db, item.name).length, 0);
    expect(linked).toBe(total);
  });

  it("shows SharpWR's pick as the core item, else the engine's", () => {
    const zeri = db.champions.find((champion) => champion.name === "Zeri")!;
    expect(coreItems(db, zeri)).toEqual([zeri.editor_core!.item]);
    const kalista = db.champions.find((champion) => champion.name === "Kalista")!;
    expect(kalista.editor_core).toBeNull();
    expect(coreItems(db, kalista)).toEqual(championCore(db, "Kalista")!.core);
  });

  it("has every build style and the keystone check for every matchup", () => {
    for (const champion of db.champions) {
      const core = championCore(db, champion.name)!;
      const styles = core.styles ?? [];
      expect(styles.filter((style) => style.editor).length, champion.name).toBe(champion.editor_core ? 1 : 0);
      for (const style of styles) {
        for (const level of BUILD_LEVELS) {
          for (const target of TARGETS) {
            const stage = stageFor(style.stages, level, target.key)!;
            const required = style.items.slice(0, stage.items_allowed).map((name) => (name === "Muramana" && level < 11 ? "Manamune" : name));
            for (const build of stage.builds) for (const name of required) expect(build.items, `${champion.name} ${style.key} ${level}`).toContain(name);
          }
        }
      }
      for (const level of KEYSTONE_CHECK_LEVELS) {
        for (const target of TARGETS) {
          const row = core.keystone_check?.find((check) => check.level === level && check.target === target.key);
          expect(row?.ttk[champion.rune_page!.keystone], `${champion.name} ${level} ${target.key}`).not.toBeUndefined();
        }
      }
    }
  });

  it("ranks keystones fastest first, survivors last", () => {
    expect(rankKeystones({ A: 3, B: null, C: 2 })).toEqual([["C", 2], ["A", 3], ["B", null]]);
  });
});
