import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import type { Database } from "../src/data";
import { type BuildStats, buildProblems, buildStats } from "../src/engine/build";

const read = (path: string) => JSON.parse(readFileSync(new URL(`../../app-data/${path}`, import.meta.url), "utf8"));
const db = read("database.json") as Database;
const golden = read("golden/build-stats.json") as Array<{
  champion: string;
  level: number;
  items: string[];
  boots: string | null;
  mist: number;
  yuntal_stacks: number;
  expected: BuildStats;
}>;

// Champion level stats are exported rounded to 4 decimals, so health, mana and armor (and AD
// with Manamune/Muramana, 2% of mana) can differ from Python by a few millionths.
const TOLERANCE = 1e-6;

describe("build stats port", () => {
  it("matches the Python engine on every golden build", () => {
    expect(golden.length).toBeGreaterThan(1000);
    for (const c of golden) {
      const actual = buildStats(db, { champion: c.champion, level: c.level, items: c.items, boots: c.boots, mist: c.mist, yuntalStacks: c.yuntal_stacks });
      for (const [field, expected] of Object.entries(c.expected) as Array<[keyof BuildStats, number | null]>) {
        const label = `${c.champion} L${c.level} ${c.items.join("+")} ${c.boots ?? ""} ${field}`;
        if (expected === null) expect(actual[field], label).toBeNull();
        else expect(Math.abs((actual[field] as number) - expected), label).toBeLessThanOrEqual(TOLERANCE * Math.max(1, Math.abs(expected)));
      }
    }
  });

  it("is exact wherever no rounded level stat is involved", () => {
    let exact = 0;
    for (const c of golden) {
      const actual = buildStats(db, { champion: c.champion, level: c.level, items: c.items, boots: c.boots, mist: c.mist, yuntalStacks: c.yuntal_stacks });
      const fields: Array<keyof BuildStats> = ["gold", "ability_power", "attack_speed", "attack_speed_over_cap", "crit_chance", "crit_damage", "ability_haste", "movement_speed"];
      if (!c.items.some((name) => name === "Manamune" || name === "Muramana")) fields.push("attack_damage");
      for (const field of fields) expect(actual[field], `${c.champion} ${c.items.join("+")} ${field}`).toBe(c.expected[field]);
      exact += fields.length;
    }
    expect(exact).toBeGreaterThan(9000);
  });
});

describe("build rules", () => {
  it("accepts a legal build", () => {
    expect(buildProblems(db, ["Infinity Edge", "Yun Tal Wildarrows", "Lord Dominik's Regards"], "Berserker's Greaves")).toEqual([]);
  });

  it("explains illegal builds", () => {
    expect(buildProblems(db, ["Trinity Force", "Essence Reaver"], null)).toEqual(["Only one Spellblade item is allowed."]);
    expect(buildProblems(db, ["Infinity Edge", "Infinity Edge"], null)).toEqual(["Duplicate items are not allowed."]);
    expect(buildProblems(db, ["Lord Dominik's Regards", "Mortal Reminder"], null)).toEqual(["Only one of Lord Dominik's Regards and Mortal Reminder is allowed."]);
    expect(buildProblems(db, ["Manamune", "Muramana"], null)).toEqual(["Only one of Manamune and Muramana is allowed."]);
    expect(buildProblems(db, ["Berserker's Greaves"], null)).toEqual(["Choose valid items; boots use the separate slot."]);
    const six = db.items.slice(0, 6).map((item) => item.name);
    expect(buildProblems(db, six, null)).toContain("At most 5 items are allowed.");
  });
});
