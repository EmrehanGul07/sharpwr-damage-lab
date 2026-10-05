import type { Database, Rune } from "../data";
import { h, icon } from "../dom";
import { humanize } from "../format";
import { href } from "../router";
import { matches } from "../search";
import { type View, currentQuery, emptyState, listFooter, listRow, notFound, searchField, segments } from "./shared";

const TREES = ["Key Rune", "Precision", "Domination", "Resolve", "Sorcery"];

function placement(rune: Rune): string {
  return rune.slot ? `${rune.tree} · Row ${rune.slot}` : rune.tree;
}

function treeIcon(db: Database, tree: string): string | null {
  return db.rune_trees.find((record) => record.name === tree)?.icon ?? null;
}

export function runeList(db: Database, params: URLSearchParams): View {
  const requested = params.get("tree");
  const active = requested && TREES.includes(requested) ? requested : "All";
  const list = h("div", { class: "list" });
  const render = (query: string) => {
    const groups = (active === "All" ? TREES : [active]).flatMap((tree) => {
      const rows = db.runes
        .filter((rune) => rune.tree === tree && matches(query, rune.name, rune.tooltip))
        .map((rune) => listRow(href("runes", [rune.name]), rune.icon, rune.name, rune.slot ? `Row ${rune.slot} · ${humanize(rune.kind)}` : humanize(rune.kind)));
      if (!rows.length) return [];
      return [h("h3", { class: "group" }, icon(treeIcon(db, tree), "", 22), tree), ...rows];
    });
    list.replaceChildren(...(groups.length ? groups : [emptyState("No rune matches this search.")]));
  };
  render(currentQuery("runes"));
  const options = ["All", ...TREES].map((tree) => ({
    label: tree,
    target: tree === "All" ? href("runes") : href("runes", [], { tree }),
    active: tree === active,
  }));
  return {
    title: "Runes",
    back: false,
    body: h("section", {}, segments(options), searchField("runes", "Search runes or effects", render), list, listFooter()),
  };
}

export function runeDetail(db: Database, name: string): View {
  const rune = db.runes.find((record) => record.name === name);
  if (!rune) return notFound(name);
  return {
    title: rune.name,
    back: true,
    body: h(
      "section",
      { class: "detail" },
      h("div", { class: "hero" }, icon(rune.icon, rune.name, 72), h("div", {}, h("h2", {}, rune.name), h("p", { class: "muted" }, placement(rune)), h("span", { class: "badge" }, humanize(rune.kind)))),
      h("h3", {}, "Effect"),
      h("p", { class: "tooltip" }, rune.tooltip),
    ),
  };
}
