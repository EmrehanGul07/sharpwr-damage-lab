/** Lookups for the tier list and the saved core-item results. */
import type { Champion, ChampionCore, CoreStage, Database, Item, Target } from "./data";

export const BUILD_LEVELS = [5, 7, 9, 11, 13, 15];

/** Benchmark targets: each fight is against this champion type at the same level. */
export const TARGETS: ReadonlyArray<{ key: Target; label: string; example: string }> = [
  { key: "squishy", label: "Squishy", example: "Jinx" },
  { key: "bruiser", label: "Bruiser", example: "Darius" },
  { key: "tank", label: "Tank", example: "Ornn" },
];

/** Completed item or boots by name; builds and the tier list use both. */
export function findItem(db: Database, name: string): Item | undefined {
  return db.items.find((item) => item.name === name) ?? db.boots.find((item) => item.name === name);
}

export function tierOf(db: Database, itemName: string): string | null {
  return db.tier_list?.tiers.find((tier) => tier.items.includes(itemName))?.tier ?? null;
}

export function championCore(db: Database, championName: string): ChampionCore | null {
  return db.core_items?.champions[championName] ?? null;
}

/** Champions whose core item this is. */
export function coreChampions(db: Database, itemName: string): Champion[] {
  return db.champions.filter((champion) => championCore(db, champion.name)?.core.includes(itemName));
}

export function stageFor(core: ChampionCore, level: number, target: Target): CoreStage | undefined {
  return core.stages.find((stage) => stage.level === level && stage.target === target);
}
