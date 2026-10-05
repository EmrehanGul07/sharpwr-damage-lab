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

export interface Database {
  schema: number;
  champions: Champion[];
  items: Item[];
  components: Item[];
  boots: Item[];
  runes: Rune[];
  rune_trees: RuneTree[];
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
