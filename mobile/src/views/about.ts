import { version } from "../../package.json";
import type { DataState } from "../data";
import { h } from "../dom";
import { formatDate } from "../format";
import { installedApkVersion } from "../live-update";
import { RIOT_NOTICE, type View, statTable } from "./shared";

export function about({ db, downloadedAt }: DataState): View {
  return {
    title: "About",
    back: false,
    body: h(
      "section",
      { class: "detail" },
      h("h2", {}, "SharpWR"),
      h("p", {}, "A database of the Wild Rift marksmen: champion stats at every level, items, boots and runes, SharpWR's item tier list and each champion's best tested builds. It works offline and downloads data updates when your phone is online. A free fan project for players."),
      statTable([
        ["App version", version],
        ["Installed APK", installedApkVersion() ?? "—"],
        ["Data", downloadedAt ? `Downloaded ${formatDate(downloadedAt)}` : "Built into the app"],
        ["Data format", `Schema ${db.schema}`],
        ["Tier list", db.tier_list ? `Patch ${db.tier_list.patch}` : "—"],
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
