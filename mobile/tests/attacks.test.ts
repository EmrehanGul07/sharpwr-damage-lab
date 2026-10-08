import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { describe, it, expect } from "vitest";
import type { Database } from "../src/data";
import {
  AttackKernel,
  type AttackState,
  type Target,
  type AttackOptions,
} from "../src/engine/attacks";
import type { BuildInput } from "../src/engine/build";
import { simulateAa } from "../src/engine/aa";
const db = JSON.parse(
  readFileSync(
    new URL("../../app-data/database.json", import.meta.url),
    "utf8",
  ),
) as Database;
const golden = JSON.parse(
  gunzipSync(
    readFileSync(
      new URL("../../app-data/golden/attacks.json.gz", import.meta.url),
    ),
  ).toString(),
) as Array<{
  input: BuildInput;
  target: Target;
  options: AttackOptions;
  hits: Array<{ state: AttackState; expected: Record<string, number> }>;
  aa: { ttk: number | null; attacks: number; dps: number };
}>;
describe("Python AA parity", () => {
  it("matches all champion / item / stack sequences", () => {
    const names: Record<string, string> = {
      as: "attackSpeed",
      mr: "magicResist",
      true: "trueDamage",
      physical_damage: "physicalDamage",
      magic_damage: "magicDamage",
    };
    for (const c of golden) {
      const kernel = new AttackKernel(db, c.input, c.target, c.options);
      for (const h of c.hits) {
        const actual = kernel.hit(h.state);
        for (const [key, value] of Object.entries(h.expected)) {
          const got =
            key in actual
              ? (actual as unknown as Record<string, number>)[key]
              : names[key]
                ? (actual as unknown as Record<string, number>)[names[key]]
                : actual.stacks[key];
          expect(
            got,
            `${c.input.champion} L${c.input.level} ${c.input.items} t${h.state.time} ${key}`,
          ).toBeCloseTo(value, 5);
        }
      }
    }
  });
});
it("matches Python sim_build cycle TTK, attack count and DPS", () => {
  for (const c of golden) {
    const actual = simulateAa(db, c.input, c.target),
      context = `${c.input.champion} L${c.input.level} ${c.input.items}`;
    expect(actual.ttk, context).toEqual(c.aa.ttk);
    expect(actual.attacks, context).toEqual(c.aa.attacks);
    expect(actual.dps, context).toBeCloseTo(c.aa.dps, 1);
  }
});
