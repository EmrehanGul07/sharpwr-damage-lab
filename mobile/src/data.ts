/** Types and loader for app-data/database.json (schema 1, see docs/app-data.md). */

export const SUPPORTED_SCHEMA = 1;

export type StatKey =
  | "ad"
  | "as"
  | "crit"
  | "ap"
  | "hp"
  | "mana"
  | "armor"
  | "mr"
  | "ah"
  | "ls"
  | "flatpen"
  | "pctpen"
  | "ms"
  | "flatmpen"
  | "pctmpen";

export interface LevelStats {
  attack_damage: number;
  attack_speed: number;
  hp: number | null;
  mana: number | null;
  hp_regen_per_5s: number | null;
  mana_regen_per_5s: number | null;
  armor: number | null;
  mr: number | null;
  movement_speed: number | null;
  attack_range: number | null;
}

export interface Champion {
  name: string;
  icon: string | null;
  attack_type: string | null;
  resource_type: string | null;
  stats: Record<string, number | null>;
  levels: Record<string, LevelStats>;
  source_status: string;
  wiki_source_url: string | null;
  wiki_last_change_patch: string | null;
}

export type ItemCategory = "completed" | "component" | "boots";

export interface Item {
  name: string;
  icon: string | null;
  category: ItemCategory;
  gold: number;
  stats: Record<StatKey, number>;
  ms_unit?: "fraction" | "flat";
}

export interface Rune {
  name: string;
  icon: string | null;
  tree: string;
  slot: number | null;
  kind: string;
  tooltip: string;
}

export interface RuneTree {
  name: string;
  icon: string | null;
}

/** SharpWR's published item tier list, best tier first. */
export interface TierList {
  title: string;
  patch: string;
  tiers: Array<{ tier: string; items: string[] }>;
}

export type Target = "squishy" | "bruiser" | "tank";

export interface CoreBuild {
  items: string[];
  boots: string;
  /** Seconds to defeat the target; null when it survived. */
  ttk: number | null;
  dps: number;
  gold: number;
  /** Tie explanation, e.g. "Equal TTK · lower-cost option". */
  note: string | null;
}

export interface CoreStage {
  level: number;
  target: Target;
  items_allowed: number;
  builds: CoreBuild[];
}

export interface CoreRanking {
  item: string;
  /** 0-100: Top-3 build presence weighted 1, 1/2, 1/3, averaged over eligible cells. */
  score: number;
  winner_cells: number;
  top3_cells: number;
  appearance_cells: number;
  eligible_cells: number;
}

/** Saved core-item search for one champion (docs/app-data.md). */
export interface ChampionCore {
  core: string[];
  ranking: CoreRanking[];
  stages: CoreStage[];
  notes: string[];
}

export interface CoreItems {
  excluded: string[];
  /** null while the saved result is being recalculated. */
  champions: Record<string, ChampionCore | null>;
}

export interface Database {
  schema: number;
  champions: Champion[];
  items: Item[];
  components: Item[];
  boots: Item[];
  runes: Rune[];
  rune_trees: RuneTree[];
  /** Optional: data exported before app version 0.3.0 has neither. */
  tier_list?: TierList;
  core_items?: CoreItems;
}

/** The Database on screen, and when it was downloaded (null: the copy bundled with the app). */
export interface DataState {
  db: Database;
  downloadedAt: string | null;
}

/** Checks a downloaded or saved Database before the app shows it. */
export function isUsableDatabase(value: unknown): value is Database {
  if (typeof value !== "object" || value === null) return false;
  const data = value as Partial<Record<keyof Database, unknown>>;
  const lists = [data.champions, data.items, data.components, data.boots, data.runes, data.rune_trees];
  const named = (list: unknown) =>
    Array.isArray(list) && list.every((record) => typeof (record as { name?: unknown } | null)?.name === "string");
  return data.schema === SUPPORTED_SCHEMA && lists.every(named) && (data.champions as unknown[]).length > 0;
}

export async function loadDatabase(url = "data/database.json"): Promise<Database> {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Database not found (HTTP ${response.status})`);
  const data = (await response.json()) as Database;
  if (data.schema !== SUPPORTED_SCHEMA) throw new Error(`Unsupported database schema ${data.schema}`);
  return data;
}

export function itemsOfCategory(db: Database, category: ItemCategory): Item[] {
  return { completed: db.items, component: db.components, boots: db.boots }[category];
}
