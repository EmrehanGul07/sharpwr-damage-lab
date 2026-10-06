import { existsSync, readFileSync } from "node:fs";
import { join } from "node:path";
import { fileURLToPath } from "node:url";
import { beforeAll, describe, expect, it } from "vitest";
import type { Champion } from "../src/data";
import { SCRIPTS, loadPracticeScripts } from "../src/practice-scripts";
import { href, parseRoute } from "../src/router";

const root = fileURLToPath(new URL("../..", import.meta.url));
const db = JSON.parse(readFileSync(join(root, "app-data/database.json"), "utf8")) as { champions: Champion[] };

interface Slot {
  mode: string;
  damage?: Record<string, number[][]>;
  window?: number;
}
interface Profile {
  id: string;
  hud: { icons: Record<string, string> };
  practice: { slots: Record<string, Slot>; levels: { ad: number[] } };
}
const catalogue = JSON.parse(readFileSync(join(root, "app-data/practice.json"), "utf8")) as {
  champions: Record<string, Profile>;
  practice_targets: Record<string, unknown[]>;
};

type Vec = [number, number, number];
interface PracticeState {
  time: number;
  hero: Vec;
  target: Vec;
  log: Array<{ slot: string; dealt?: number; text?: string }>;
  dummy: { hp: number; max: number };
}
interface PracticeApi {
  create(profile: unknown, options: unknown): PracticeState;
  cast(state: PracticeState, slot: string, point?: Vec): boolean;
  step(state: PracticeState, dt: number): void;
  setDummy(state: PracticeState, values: Record<string, number>): void;
}
const globals = globalThis as unknown as {
  MarksmanPractice: PracticeApi;
  MarksmanFight: { MOVEMENT: unknown };
  MarksmanPracticeTool: { notesMarkdown(notes: unknown, catalogue: unknown, date: Date): string; NOTES_KEY: string };
};

function run(state: PracticeState, seconds: number) {
  const end = state.time + seconds;
  while (state.time < end - 1e-9) globals.MarksmanPractice.step(state, Math.min(1 / 60, end - state.time));
}

describe("Practice tab", () => {
  beforeAll(() => loadPracticeScripts());

  it("has every database champion with practice numbers and bundled icons", () => {
    expect(Object.keys(catalogue.champions).sort()).toEqual(db.champions.map((c) => c.name).sort());
    for (const [name, profile] of Object.entries(catalogue.champions)) {
      expect(profile.practice.levels.ad, name).toHaveLength(15);
      for (const path of Object.values(profile.hud.icons)) expect(existsSync(join(root, path)), path).toBe(true);
      expect(existsSync(join(root, "static/marksman-3d", profile.id, "character.glb")), name).toBe(true);
    }
    expect(Object.keys(catalogue.practice_targets).length).toBeGreaterThan(0);
  });

  it("runs the shared web scripts in order and defines their globals", () => {
    expect(SCRIPTS.map(([name]) => name).indexOf("geometry.js")).toBeLessThan(SCRIPTS.map(([name]) => name).indexOf("practice.js"));
    for (const name of ["MarksmanScene", "MarksmanPractice", "MarksmanGeometry", "MarksmanFight", "MarksmanPracticeTool"])
      expect(typeof (globalThis as Record<string, unknown>)[name], name).toBe("object");
  });

  it("hits the dummy with the engine's numbers after its resistances", () => {
    const P = globals.MarksmanPractice;
    const ezreal = { ...catalogue.champions.Ezreal, name: "Ezreal" };
    const state = P.create(ezreal, { movements: globals.MarksmanFight.MOVEMENT });
    P.setDummy(state, { hp: 5000, armor: 50, mr: 25 });
    expect(P.cast(state, "W")).toBe(true);
    run(state, 1.5);
    expect(P.cast(state, "Q")).toBe(true);
    run(state, 1.5);
    const q = ezreal.practice.slots.Q.damage!.physical[3][14];
    const w = ezreal.practice.slots.W.damage!.magic[3][14];
    const hits = state.log.filter((entry) => entry.dealt);
    expect(hits.map((entry) => entry.slot)).toEqual(["Q", "W detonation"]);
    expect(hits[0].dealt).toBeCloseTo((q * 100) / 150, 6);
    expect(hits[1].dealt).toBeCloseTo((w * 100) / 125, 6);
    expect(state.dummy.hp).toBeCloseTo(5000 - hits[0].dealt! - hits[1].dealt!, 6);
  });

  it("exports notes for the champions that have them", () => {
    const notes = { version: 1, champions: { Jinx: { tested: true, Q: "Rockets feel slower\nthan in game" }, Ezreal: { tested: false } } };
    const text = globals.MarksmanPracticeTool.notesMarkdown(notes, catalogue, new Date("2026-10-06T12:00:00Z"));
    expect(text).toContain("Exported 2026-10-06 · 1/23 champions tested");
    expect(text).toContain("## Jinx (tested)");
    expect(text).toContain("Rockets feel slower / than in game");
    expect(text).not.toContain("## Ezreal");
  });

  it("opens from a link with a champion", () => {
    const route = parseRoute(href("practice", [], { champion: "Kai'Sa" }));
    expect(route.section).toBe("practice");
    expect(route.params.get("champion")).toBe("Kai'Sa");
  });
});
