import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";
import { type Database, SUPPORTED_SCHEMA } from "../src/data";

// The app ships app-data/database.json and assets/riot/ from the repository root.
const repo = fileURLToPath(new URL("../..", import.meta.url));
const db = JSON.parse(readFileSync(join(repo, "app-data", "database.json"), "utf8")) as Database;

describe("bundled database", () => {
  it("uses the schema this app reads", () => {
    expect(db.schema).toBe(SUPPORTED_SCHEMA);
  });

  it("has every section the app shows", () => {
    expect(db.champions).toHaveLength(23);
    expect(db.runes).toHaveLength(51);
    expect(db.items.length + db.components.length + db.boots.length).toBeGreaterThan(0);
    for (const champion of db.champions) expect(Object.keys(champion.levels)).toHaveLength(15);
  });

  it("points every icon at a bundled file", () => {
    const records = [...db.champions, ...db.items, ...db.components, ...db.boots, ...db.runes, ...db.rune_trees];
    for (const record of records) {
      if (record.icon) expect(existsSync(join(repo, record.icon)), record.icon).toBe(true);
    }
  });
});
