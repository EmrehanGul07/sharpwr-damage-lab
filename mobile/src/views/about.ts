import { version } from "../../package.json";
import type { Database } from "../data";
import { h } from "../dom";
import { RIOT_NOTICE, type View, statTable } from "./shared";

export function about(db: Database): View {
  return {
    title: "About",
    back: false,
    body: h(
      "section",
      { class: "detail" },
      h("h2", {}, "SharpWR"),
      h("p", {}, "An offline database of the Wild Rift marksmen: champion stats at every level, items, boots and runes. A free fan project for players."),
      statTable([
        ["App version", version],
        ["Data format", `Schema ${db.schema}`],
        ["Champions", String(db.champions.length)],
        ["Items", String(db.items.length)],
        ["Components", String(db.components.length)],
        ["Boots", String(db.boots.length)],
        ["Runes", String(db.runes.length)],
      ]),
      h("h3", {}, "Legal"),
      h("p", { class: "notice" }, RIOT_NOTICE),
      h("p", { class: "note" }, "Champion portraits and item and rune icons are Riot Games artwork."),
    ),
  };
}
