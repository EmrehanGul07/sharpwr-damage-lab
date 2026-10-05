/**
 * Port of sharpwr/build_stats.py: a champion's stats with items and boots when a fight starts.
 * Checked against the Python results in app-data/golden/build-stats.json (tests/build.test.ts).
 * Keep the operation order of the Python code: floating-point results then match.
 */
import type { Champion, Database, Item, StatKey } from "../data";

export interface BuildInput {
  champion: string;
  level: number;
  /** Completed items, at most five, in any order. */
  items: string[];
  boots: string | null;
  /** Senna's Mist stacks. */
  mist?: number;
  /** Yun Tal Wildarrows permanent stacks. */
  yuntalStacks?: number;
}

/** Same fields as sharpwr.build_stats.build_stats; fractions stay fractions (0.25 = 25%). */
export interface BuildStats {
  gold: number;
  attack_damage: number;
  ability_power: number;
  attack_speed: number;
  attack_speed_over_cap: number;
  attack_speed_cap: number;
  crit_chance: number;
  crit_damage: number;
  ability_haste: number;
  armor_pen_pct: number;
  armor_pen_flat: number;
  magic_pen_pct: number;
  magic_pen_flat: number;
  lifesteal: number;
  health: number | null;
  mana: number | null;
  armor: number | null;
  magic_resist: number | null;
  movement_speed: number;
}

type Totals = Record<StatKey | "gold", number>;
const KEYS: Array<StatKey | "gold"> = [
  "gold", "ad", "as", "crit", "ap", "hp", "mana", "armor", "mr", "ah", "ls", "flatpen", "pctpen", "ms", "flatmpen", "pctmpen",
];
const MANA_ITEMS = ["Manamune", "Muramana"];

function findCompleted(db: Database, name: string): Item {
  const item = db.items.find((record) => record.name === name);
  if (!item) throw new Error(`Unknown item: ${name}`);
  return item;
}

function findBoots(db: Database, name: string): Item {
  const boots = db.boots.find((record) => record.name === name);
  if (!boots) throw new Error(`Unknown boots: ${name}`);
  return boots;
}

/** Python: sum(q[k] for q in rows), starting from 0, items first, then boots (0 without boots). */
function totals(rows: Item[], boots: Item | null): Totals {
  const out = {} as Totals;
  for (const key of KEYS) {
    let sum = 0;
    for (const row of rows) sum += key === "gold" ? row.gold : row.stats[key];
    sum += boots ? (key === "gold" ? boots.gold : boots.stats[key]) : 0;
    out[key] = sum;
  }
  return out;
}

/** aa_engine.gu: growth factor, 0 at level 1. */
function growth(level: number): number {
  const n = level - 1;
  return n * (0.7025 + 0.0175 * n);
}

function attackStats(champion: Champion, level: number, mist: number) {
  if (!champion.aa) throw new Error("This data has no attack parameters; update the app data.");
  const { base_ad, ad_growth, as_ratio, base_as, base_bonus_as, as_growth } = champion.aa;
  const u = growth(level);
  return {
    ad: base_ad + ad_growth * u + (champion.name === "Senna" ? mist * 1.25 : 0),
    ratio: as_ratio,
    baseas: base_as,
    bba: base_bonus_as,
    lvbas: as_growth * u,
  };
}

/** Python list.sort() order for these names (ASCII). */
function pythonSorted(names: string[]): string[] {
  return [...names].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
}

export function buildStats(db: Database, input: BuildInput): BuildStats {
  const champion = db.champions.find((record) => record.name === input.champion);
  if (!champion) throw new Error(`Unknown champion: ${input.champion}`);
  const n = champion.name;
  const l = input.level;
  const mist = input.mist ?? 0;
  const items = pythonSorted(input.items);
  const core = champion.levels[String(l)];
  const s = attackStats(champion, l, mist);
  const total = totals(items.map((name) => findCompleted(db, name)), input.boots ? findBoots(db, input.boots) : null);
  const maxMana = core.mana === null ? null : core.mana + total.mana;
  const yuntalCrit = items.includes("Yun Tal Wildarrows") ? Math.min(0.25, (input.yuntalStacks ?? 0) * 0.002) : 0;
  const awe = items.some((name) => MANA_ITEMS.includes(name)) ? 0.02 * (maxMana ?? 0) : 0;
  let startingAd = s.ad + total.ad + awe;
  const bonusAs = s.bba + s.lvbas + total.as;
  let startRaw: number;
  if (n === "Jhin") {
    // Whisper converts attack speed and crit into AD; Jhin's attack speed does not grow.
    const crit = Math.min(1, total.crit + yuntalCrit);
    startingAd = startingAd * (1 + 0.3 * bonusAs + 0.4 * crit + 0.03 * l);
    startRaw = s.baseas + s.ratio * (s.bba + s.lvbas);
  } else {
    startRaw = s.baseas + s.ratio * bonusAs;
  }
  const cap = n === "Zeri" ? 1.5 : 3;
  if (n === "Zeri") {
    // Zeri converts bonus attack speed above her 1.5 cap into AD.
    startingAd += 0.5 * Math.max(0, (bonusAs - Math.max(0, (1.5 - s.baseas) / s.ratio)) * 100);
  }
  let critDamage = items.includes("Infinity Edge") ? 2.3 : 2.0;
  if (n === "Senna") critDamage *= 0.9;
  const plus = (key: StatKey, value: number | null) => (value === null ? null : value + total[key]);
  let itemMs = 0;
  for (const name of items) itemMs += findCompleted(db, name).stats.ms;
  return {
    gold: total.gold,
    attack_damage: startingAd,
    ability_power: total.ap,
    attack_speed: Math.min(cap, startRaw),
    attack_speed_over_cap: Math.max(0, startRaw - cap),
    attack_speed_cap: cap,
    crit_chance: Math.min(1, total.crit + (n === "Senna" ? Math.floor(mist / 20) * 0.1 : 0) + yuntalCrit),
    crit_damage: critDamage,
    ability_haste: total.ah,
    armor_pen_pct: total.pctpen,
    armor_pen_flat: total.flatpen,
    magic_pen_pct: total.pctmpen,
    magic_pen_flat: total.flatmpen,
    lifesteal: total.ls,
    health: plus("hp", core.hp),
    mana: maxMana,
    armor: plus("armor", core.armor),
    magic_resist: plus("mr", core.mr),
    movement_speed: (core.movement_speed ?? 0) * (1 + itemMs) + (input.boots ? findBoots(db, input.boots).stats.ms : 0),
  };
}

/** Why a build is not allowed, in the engine's words; empty when it is legal. */
export function buildProblems(db: Database, items: string[], boots: string | null): string[] {
  const rules = db.build_rules;
  const problems: string[] = [];
  if (!rules) return problems;
  if (items.filter((name) => rules.spellblade.includes(name)).length > 1) problems.push("Only one Spellblade item is allowed.");
  if (items.length > rules.max_items) problems.push(`At most ${rules.max_items} items are allowed.`);
  if (new Set(items).size !== items.length) problems.push("Duplicate items are not allowed.");
  if (items.some((name) => !db.items.some((item) => item.name === name))) problems.push("Choose valid items; boots use the separate slot.");
  if (boots !== null && !db.boots.some((item) => item.name === boots)) problems.push("Unknown boots.");
  for (const group of rules.exclusive_groups) {
    // The Spellblade group is reported above.
    if (group.every((name) => rules.spellblade.includes(name))) continue;
    const chosen = items.filter((name) => group.includes(name));
    if (chosen.length > 1) problems.push(`Only one of ${chosen.join(" and ")} is allowed.`);
  }
  return problems;
}
