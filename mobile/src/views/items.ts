import { coreChampions, tierOf } from "../builds";
import { type Database, type ItemCategory, itemsOfCategory } from "../data";
import { h, icon } from "../dom";
import { formatGold, itemStatLines } from "../format";
import { href } from "../router";
import { matches } from "../search";
import { type View, currentQuery, emptyState, listFooter, listRow, notFound, searchField, segments, statTable, tierBadge } from "./shared";

const CATEGORIES: ReadonlyArray<[ItemCategory, string]> = [
  ["completed", "Items"],
  ["component", "Components"],
  ["boots", "Boots"],
];

function category(value: string | null | undefined): ItemCategory {
  return CATEGORIES.some(([key]) => key === value) ? (value as ItemCategory) : "completed";
}

export function itemList(db: Database, params: URLSearchParams): View {
  const active = category(params.get("type"));
  const list = h("div", { class: "list" });
  const render = (query: string) => {
    const rows = itemsOfCategory(db, active)
      .filter((item) => matches(query, item.name))
      .map((item) => {
        const stats = itemStatLines(item)
          .slice(0, 2)
          .map((line) => `${line.value} ${line.label}`);
        const badge = active === "completed" ? tierBadge(tierOf(db, item.name)) : null;
        return listRow(href("items", [active, item.name]), item.icon, item.name, [formatGold(item.gold), ...stats].join(" · "), badge);
      });
    list.replaceChildren(...(rows.length ? rows : [emptyState("No item matches this search.")]));
  };
  render(currentQuery(`items-${active}`));
  return {
    title: "Items",
    back: false,
    body: h(
      "section",
      {},
      segments(CATEGORIES.map(([key, label]) => ({ label, target: href("items", [], { type: key }), active: key === active }))),
      searchField(`items-${active}`, "Search items", render),
      list,
      listFooter(),
    ),
  };
}

export function itemDetail(db: Database, categoryName: string, name: string): View {
  const item = itemsOfCategory(db, category(categoryName)).find((record) => record.name === name);
  if (!item) return notFound(name);
  const lines = itemStatLines(item);
  const label = { completed: "Item", component: "Component", boots: "Boots" }[item.category];
  const tier = item.category === "completed" ? tierOf(db, item.name) : null;
  const champions = coreChampions(db, item.name);
  return {
    title: item.name,
    back: true,
    body: h(
      "section",
      { class: "detail" },
      h(
        "div",
        { class: "hero" },
        icon(item.icon, item.name, 72),
        h(
          "div",
          {},
          h("h2", {}, item.name),
          h("p", { class: "muted" }, `${label} · ${formatGold(item.gold)}`),
          tier ? h("p", { class: "tier-line" }, tierBadge(tier), h("a", { href: href("tiers") }, `Tier ${tier} on the tier list`)) : null,
        ),
      ),
      h("h3", {}, "Stats"),
      lines.length ? statTable(lines.map((line) => [line.label, line.value])) : emptyState("No stats."),
      champions.length ? h("h3", {}, "Core item for") : null,
      champions.length
        ? h(
            "div",
            { class: "chips" },
            ...champions.map((champion) => h("a", { class: "chip", href: href("champions", [champion.name]) }, icon(champion.icon, "", 32), champion.name)),
          )
        : null,
    ),
  };
}
