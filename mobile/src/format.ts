/** Display formatting. Units follow docs/app-data.md. */
import type { Item, LevelStats, StatKey } from "./data";

type ItemUnit = "flat" | "percent" | "ms";

export const ITEM_STATS: ReadonlyArray<[StatKey, string, ItemUnit]> = [
  ["ad", "Attack Damage", "flat"],
  ["as", "Attack Speed", "percent"],
  ["crit", "Critical Strike", "percent"],
  ["ap", "Ability Power", "flat"],
  ["hp", "Health", "flat"],
  ["mana", "Mana", "flat"],
  ["armor", "Armor", "flat"],
  ["mr", "Magic Resist", "flat"],
  ["ah", "Ability Haste", "flat"],
  ["ls", "Life Steal", "percent"],
  ["flatpen", "Armor Penetration", "flat"],
  ["pctpen", "Armor Penetration", "percent"],
  ["ms", "Movement Speed", "ms"],
  ["flatmpen", "Magic Penetration", "flat"],
  ["pctmpen", "Magic Penetration", "percent"],
];

export const LEVEL_STATS: ReadonlyArray<[keyof LevelStats, string, number, string]> = [
  ["attack_damage", "Attack Damage", 1, ""],
  ["attack_speed", "Attack Speed", 3, ""],
  ["hp", "Health", 0, ""],
  ["mana", "Mana", 0, ""],
  ["hp_regen_per_5s", "Health Regen", 1, " / 5s"],
  ["mana_regen_per_5s", "Mana Regen", 1, " / 5s"],
  ["armor", "Armor", 1, ""],
  ["mr", "Magic Resist", 1, ""],
  ["movement_speed", "Movement Speed", 0, ""],
  ["attack_range", "Attack Range", 0, ""],
];

/** Up to `digits` decimals, without trailing zeros. */
export function trimNumber(value: number, digits = 2): string {
  return String(Number(value.toFixed(digits)));
}

/** Values per ability rank as "7.5/6/4.5/3", or one number when every rank is equal; null when absent or all 0. */
export function perRank(values: number[] | null): string | null {
  if (!values || values.every((value) => value === 0)) return null;
  const texts = values.map((value) => trimNumber(value));
  return texts.every((text) => text === texts[0]) ? texts[0] : texts.join("/");
}

/** "attack_damage" -> "Attack damage". */
export function humanize(identifier: string): string {
  const words = identifier.replace(/_/g, " ").trim();
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/** Fixed decimals with thousands separators; unknown values show as a dash. */
export function formatNumber(value: number | null | undefined, digits: number): string {
  if (value === null || value === undefined) return "—";
  return value.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  });
}

export function formatGold(gold: number): string {
  return `${gold.toLocaleString("en-US")} gold`;
}

/** ISO time as a short day, e.g. "5 Oct 2026". */
export function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" });
}

/** Non-zero item stats as label/value pairs, e.g. Attack Speed "+40%". */
export function itemStatLines(item: Item): Array<{ label: string; value: string }> {
  const lines: Array<{ label: string; value: string }> = [];
  for (const [key, label, unit] of ITEM_STATS) {
    const value = item.stats[key];
    if (!value) continue;
    const percent = unit === "percent" || (unit === "ms" && item.ms_unit !== "flat");
    lines.push({ label, value: percent ? `+${trimNumber(value * 100)}%` : `+${trimNumber(value)}` });
  }
  return lines;
}
