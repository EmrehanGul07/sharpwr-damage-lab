import type { Champion, Database } from "../data";
import { h, icon } from "../dom";
import { LEVEL_STATS, formatNumber, trimNumber } from "../format";
import { href } from "../router";
import { matches } from "../search";
import { type View, currentQuery, emptyState, listFooter, listRow, notFound, searchField, statTable } from "./shared";

let selectedLevel = 1;

// [label, base field, growth field, growth shown as a percentage, base decimals]
const BASE_STATS: ReadonlyArray<[string, string, string | null, boolean, number]> = [
  ["Attack Damage", "base_ad", "ad_growth", false, 2],
  ["Attack Speed", "base_as", "as_growth", true, 3],
  ["Health", "base_hp", "hp_growth", false, 2],
  ["Mana", "base_mana", "mana_growth", false, 2],
  ["Health Regen / 5s", "base_hp_regen_per_5s", "hp_regen_growth_per_5s", false, 2],
  ["Mana Regen / 5s", "base_mana_regen_per_5s", "mana_regen_growth_per_5s", false, 2],
  ["Armor", "base_armor", "armor_growth", false, 2],
  ["Magic Resist", "base_mr", "mr_growth", false, 2],
  ["Movement Speed", "movement_speed", null, false, 0],
  ["Attack Range", "attack_range", null, false, 0],
];

function subtitle(champion: Champion): string {
  const range = champion.levels["1"]?.attack_range;
  return [champion.attack_type, range ? `Range ${range}` : null].filter(Boolean).join(" · ");
}

export function championList(db: Database): View {
  const list = h("div", { class: "list" });
  const render = (query: string) => {
    const rows = db.champions
      .filter((champion) => matches(query, champion.name))
      .map((champion) => listRow(href("champions", [champion.name]), champion.icon, champion.name, subtitle(champion)));
    list.replaceChildren(...(rows.length ? rows : [emptyState("No champion matches this search.")]));
  };
  render(currentQuery("champions"));
  return {
    title: "Champions",
    back: false,
    body: h("section", {}, searchField("champions", "Search champions", render), list, listFooter()),
  };
}

function levelTable(champion: Champion, level: number): HTMLElement {
  const stats = champion.levels[String(level)];
  return statTable(
    LEVEL_STATS.map(([key, label, digits, suffix]) => {
      const value = stats[key];
      return [label, value === null ? "—" : formatNumber(value, digits) + suffix];
    }),
  );
}

function baseTable(champion: Champion): HTMLElement {
  const rows = BASE_STATS.map(([label, baseKey, growthKey, percent, digits]): [string, string] => {
    const base = champion.stats[baseKey];
    const growth = growthKey ? champion.stats[growthKey] : null;
    const baseText = base === null || base === undefined ? "—" : trimNumber(base, digits);
    if (growth === null || growth === undefined) return [label, baseText];
    return [label, `${baseText}  (+${percent ? `${trimNumber(growth * 100)}%` : trimNumber(growth)} growth)`];
  });
  return statTable(rows);
}

function source(champion: Champion): HTMLElement {
  if (champion.source_status === "manual_observed_levels_partial") {
    return h("p", { class: "note" }, "Values recorded manually in game at every level; some fields are still unknown.");
  }
  return h(
    "p",
    { class: "note" },
    "Source: ",
    champion.wiki_source_url
      ? h("a", { href: champion.wiki_source_url, target: "_blank", rel: "noopener" }, "Wild Rift wiki")
      : "Wild Rift wiki",
    champion.wiki_last_change_patch ? ` · last change ${champion.wiki_last_change_patch}` : "",
  );
}

export function championDetail(db: Database, name: string): View {
  const champion = db.champions.find((record) => record.name === name);
  if (!champion) return notFound(name);
  const levelLabel = h("output", { class: "level-value" }, `Level ${selectedLevel}`);
  const slider = h("input", { type: "range", min: 1, max: 15, step: 1, class: "level", "aria-label": "Champion level" });
  slider.value = String(selectedLevel);
  const table = h("div", {}, levelTable(champion, selectedLevel));
  slider.addEventListener("input", () => {
    selectedLevel = Number(slider.value);
    levelLabel.textContent = `Level ${selectedLevel}`;
    table.replaceChildren(levelTable(champion, selectedLevel));
  });
  const meta = [champion.attack_type, champion.resource_type].filter(Boolean).join(" · ");
  return {
    title: champion.name,
    back: true,
    body: h(
      "section",
      { class: "detail" },
      h("div", { class: "hero" }, icon(champion.icon, champion.name, 88, "portrait"), h("div", {}, h("h2", {}, champion.name), meta ? h("p", { class: "muted" }, meta) : null)),
      h("h3", {}, "Stats by level"),
      h("p", { class: "muted small" }, "Before items and runes."),
      h("div", { class: "level-row" }, slider, levelLabel),
      table,
      h("h3", {}, "Base values"),
      baseTable(champion),
      source(champion),
    ),
  };
}
