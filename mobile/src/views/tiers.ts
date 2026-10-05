import type { Database } from "../data";
import { h } from "../dom";
import { type View, emptyState, itemTile, listFooter, tierBadge } from "./shared";

export function tierList(db: Database): View {
  const list = db.tier_list;
  if (!list) {
    return {
      title: "Tier List",
      back: false,
      body: h("section", {}, emptyState("The tier list arrives with the next data update. Connect to the internet and reopen the app."), listFooter()),
    };
  }
  return {
    title: "Tier List",
    back: false,
    body: h(
      "section",
      {},
      h("p", { class: "eyebrow" }, `${list.title} · Patch ${list.patch}`),
      ...list.tiers.map(({ tier, items }) =>
        h(
          "div",
          { class: "tier" },
          tierBadge(tier, "tier-label"),
          h("div", { class: "tier-items" }, ...items.map((name) => itemTile(db, name))),
        ),
      ),
      h("p", { class: "note" }, "SharpWR's published ranking of completed items for marksmen. Tap an item for its stats and the champions it is the core item for."),
      listFooter(),
    ),
  };
}
