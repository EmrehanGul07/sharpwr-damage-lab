/** The build on the Build screen, kept on the phone between launches. */
import type { Database } from "./data";
import type { BuildInput } from "./engine/build";
import type { KeyValueStore } from "./online";

export const ITEM_SLOTS = 5;
const KEY = "sharpwr.build";

export interface BuildState {
  champion: string;
  level: number;
  /** Five slots; null is empty. */
  items: Array<string | null>;
  boots: string | null;
  mist: number;
  yuntalStacks: number;
  /** Count the champion's default rune page. */
  runes: boolean;
}

/** Yun Tal permanent stacks the web Tier List assumes at a level: 0 to level 5, 125 from level 9. */
export function defaultYuntalStacks(level: number): number {
  return level <= 5 ? 0 : level >= 9 ? 125 : Math.round((125 * (level - 5)) / 4);
}

export function emptyBuild(champion: string, level = 15): BuildState {
  return {
    champion,
    level,
    items: Array<string | null>(ITEM_SLOTS).fill(null),
    boots: null,
    mist: champion === "Senna" ? 40 : 0,
    yuntalStacks: defaultYuntalStacks(level),
    runes: true,
  };
}

export function buildInput(state: BuildState): BuildInput {
  return {
    champion: state.champion,
    level: state.level,
    items: state.items.filter((name): name is string => name !== null),
    boots: state.boots,
    mist: state.mist,
    yuntalStacks: state.yuntalStacks,
    runes: state.runes,
  };
}

/** A build checked against this data: unknown items or boots are dropped; null without a known champion. */
export function cleanBuild(db: Database, saved: Partial<BuildState>): BuildState | null {
  const champion = db.champions.find((record) => record.name === saved.champion)?.name;
  if (!champion) return null;
  const level = Number.isInteger(saved.level) && saved.level! >= 1 && saved.level! <= 15 ? saved.level! : 15;
  const known = (name: unknown) => (typeof name === "string" && db.items.some((item) => item.name === name) ? name : null);
  const count = (value: unknown, fallback: number) => (Number.isInteger(value) && (value as number) >= 0 ? (value as number) : fallback);
  return {
    champion,
    level,
    items: Array.from({ length: ITEM_SLOTS }, (_, index) => known(saved.items?.[index])),
    boots: typeof saved.boots === "string" && db.boots.some((item) => item.name === saved.boots) ? saved.boots : null,
    mist: count(saved.mist, champion === "Senna" ? 40 : 0),
    yuntalStacks: count(saved.yuntalStacks, defaultYuntalStacks(level)),
    // Builds saved before runes existed start with the default page.
    runes: saved.runes !== false,
  };
}

/** The saved build, or an empty one for the first champion. */
export function loadBuild(store: KeyValueStore | null, db: Database): BuildState {
  try {
    const raw = store?.getItem(KEY);
    if (raw) return cleanBuild(db, JSON.parse(raw) as Partial<BuildState>) ?? emptyBuild(db.champions[0].name);
  } catch {
    // Unreadable storage: start empty.
  }
  return emptyBuild(db.champions[0].name);
}

/** Link parameters that open a build in Build Lab (#/build?champion=…&level=…&items=A|B&boots=…). */
export function buildParams(champion: string, level: number, items: string[], boots: string | null): Record<string, string> {
  return { champion, level: String(level), items: items.join("|"), ...(boots ? { boots } : {}) };
}

export function buildFromParams(db: Database, params: URLSearchParams): BuildState | null {
  const level = Number(params.get("level"));
  const items = (params.get("items") ?? "").split("|").filter(Boolean);
  const champion = params.get("champion") ?? "";
  return cleanBuild(db, {
    champion,
    level,
    items,
    boots: params.get("boots"),
    mist: champion === "Senna" ? 40 : 0,
    yuntalStacks: defaultYuntalStacks(level),
  });
}

export function saveBuild(store: KeyValueStore | null, state: BuildState): void {
  try {
    store?.setItem(KEY, JSON.stringify(state));
  } catch {
    // Storage full or unavailable: the build stays until the app closes.
  }
}
