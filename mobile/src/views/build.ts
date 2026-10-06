import { type BuildState, ITEM_SLOTS, buildInput, defaultYuntalStacks, emptyBuild } from "../build-state";
import { findItem, tierOf } from "../builds";
import type { Database, Item } from "../data";
import { h, icon } from "../dom";
import { type BuildStats, buildProblems, buildStats } from "../engine/build";
import { formatGold, itemStatLines, trimNumber } from "../format";
import { href } from "../router";
import { matches } from "../search";
import { type View, choiceChips, currentQuery, emptyState, notFound, searchField, statTable, tierBadge } from "./shared";

/** The build behind the Build screen (main.ts): set() redraws the screen, replace() does not. */
export interface BuildStore {
  get(): BuildState;
  set(state: BuildState): void;
  replace(state: BuildState): void;
}

const percent = (value: number) => `${trimNumber(value * 100, 1)}%`;
const known = (value: number | null, digits: number) => (value === null ? "—" : trimNumber(value, digits));

function statRows(stats: BuildStats): Array<[string, string]> {
  const speed = trimNumber(stats.attack_speed, 3);
  const overCap = stats.attack_speed_over_cap > 0 ? ` (cap ${stats.attack_speed_cap}, +${trimNumber(stats.attack_speed_over_cap, 3)} over)` : "";
  return [
    ["Attack Damage", trimNumber(stats.attack_damage, 1)],
    ["Attack Speed", speed + overCap],
    ["Critical Strike Chance", percent(stats.crit_chance)],
    ["Critical Strike Damage", percent(stats.crit_damage)],
    ["Ability Power", trimNumber(stats.ability_power, 1)],
    ["Ability Haste", trimNumber(stats.ability_haste, 1)],
    ["Armor Penetration", percent(stats.armor_pen_pct)],
    ["Lethality", trimNumber(stats.armor_pen_flat, 1)],
    ["Magic Penetration", percent(stats.magic_pen_pct)],
    ["Flat Magic Penetration", trimNumber(stats.magic_pen_flat, 1)],
    ["Life Steal", percent(stats.lifesteal)],
    ["Health", known(stats.health, 0)],
    ["Mana", known(stats.mana, 0)],
    ["Armor", known(stats.armor, 1)],
    ["Magic Resist", known(stats.magic_resist, 1)],
    ["Movement Speed", trimNumber(stats.movement_speed, 0)],
    ["Gold", formatGold(stats.gold)],
  ];
}

function stepper(label: string, value: number, max: number, step: number, onChange: (value: number) => void): HTMLElement {
  const output = h("output", { class: "level-value" }, String(value));
  const change = (delta: number) => () => {
    const next = Math.max(0, Math.min(max, value + delta));
    if (next !== value) onChange(next);
  };
  return h(
    "div",
    { class: "stepper" },
    h("span", { class: "muted" }, label),
    h("button", { class: "button", type: "button", "aria-label": `Fewer ${label}`, onclick: change(-step) }, "−"),
    output,
    h("button", { class: "button", type: "button", "aria-label": `More ${label}`, onclick: change(step) }, "+"),
  );
}

function slot(db: Database, name: string | null, target: string, label: string): HTMLElement {
  const item = name ? findItem(db, name) : undefined;
  return h(
    "a",
    { class: name ? "slot filled" : "slot", href: target, "aria-label": name ? `${label}: ${name}` : `Add ${label.toLowerCase()}` },
    item ? icon(item.icon, "", 56) : h("span", { class: "slot-plus", "aria-hidden": "true" }, "+"),
    h("span", {}, name ?? label),
  );
}

export function buildView(db: Database, store: BuildStore): View {
  const state = store.get();
  const update = (change: Partial<BuildState>) => store.set({ ...state, ...change });
  const champion = db.champions.find((record) => record.name === state.champion);
  if (!champion?.aa) return { title: "Build Lab", back: false, body: emptyState("The build calculator arrives with the next data update. Connect to the internet and reopen the app.") };

  const select = h("select", { class: "select", "aria-label": "Champion" });
  for (const record of db.champions) select.append(h("option", { value: record.name }, record.name));
  select.value = state.champion;
  select.addEventListener("change", () => store.set({ ...emptyBuild(select.value, state.level), items: state.items, boots: state.boots }));

  const level = h("input", { type: "range", min: 1, max: 15, step: 1, class: "level", "aria-label": "Champion level" });
  level.value = String(state.level);
  level.addEventListener("change", () => update({ level: Number(level.value), yuntalStacks: defaultYuntalStacks(Number(level.value)) }));
  const levelLabel = h("output", { class: "level-value" }, `Level ${state.level}`);
  level.addEventListener("input", () => (levelLabel.textContent = `Level ${level.value}`));

  const page = champion.rune_page;
  const input = { ...buildInput(state), runes: state.runes && Boolean(champion.rune_stats) };
  const problems = buildProblems(db, input.items, input.boots);
  const hasYuntal = input.items.includes("Yun Tal Wildarrows");
  const filled = input.items.length + (input.boots ? 1 : 0);
  return {
    title: "Build Lab",
    back: false,
    body: h(
      "section",
      { class: "detail" },
      h("div", { class: "hero" }, icon(champion.icon, champion.name, 56, "portrait"), select),
      h("div", { class: "level-row" }, level, levelLabel),
      state.champion === "Senna" ? stepper("Mist stacks", state.mist, 1000, 10, (mist) => update({ mist })) : null,
      h("h3", {}, "Items"),
      h("div", { class: "slots" }, ...state.items.map((name, index) => slot(db, name, href("build", ["pick", String(index)]), "Item"))),
      h("h3", {}, "Boots"),
      h("div", { class: "slots" }, slot(db, state.boots, href("build", ["pick", "boots"]), "Boots")),
      hasYuntal ? stepper("Yun Tal stacks", state.yuntalStacks, 125, 5, (yuntalStacks) => update({ yuntalStacks })) : null,
      page && champion.rune_stats
        ? h(
            "div",
            {},
            h("h3", {}, "Runes"),
            choiceChips(
              "Runes",
              [
                { value: true, label: "SharpWR page" },
                { value: false, label: "Off" },
              ],
              state.runes,
              (runes) => update({ runes }),
            ),
            h("p", { class: "muted small" }, `${[page.keystone, ...page.primary, page.secondary].join(" · ")}. Adds the page's attack speed, AD, ability haste and mana; stacking runes fill with level.`),
          )
        : null,
      filled ? h("button", { class: "button clear", type: "button", onclick: () => update({ items: Array(ITEM_SLOTS).fill(null), boots: null }) }, "Clear build") : null,
      h("h3", {}, "Stats at the start of a fight"),
      problems.length ? h("p", { class: "notice" }, problems.join(" ")) : statTable(statRows(buildStats(db, input))),
      h(
        "p",
        { class: "note" },
        "Champion stats plus items, boots and runes, before stacks, procs and ability effects, from the same formulas as SharpWR's damage engine. Fight damage comes in the next Build Lab step.",
      ),
    ),
  };
}

function pickRow(item: Item, subtitle: string, problem: string | null, badge: HTMLElement | null, onPick: () => void): HTMLElement {
  return h(
    "button",
    { class: problem ? "row pick disabled" : "row pick", type: "button", disabled: Boolean(problem), onclick: onPick },
    icon(item.icon, "", 44),
    h("span", { class: "row-text" }, h("strong", {}, item.name), h("span", {}, problem ?? subtitle)),
    badge,
  );
}

/** Item or boots picker for one slot; picking returns to the Build screen. */
export function pickView(db: Database, store: BuildStore, slotName: string, done: () => void): View {
  const state = store.get();
  const bootsSlot = slotName === "boots";
  const index = Number(slotName);
  if (!bootsSlot && !(Number.isInteger(index) && index >= 0 && index < ITEM_SLOTS)) return notFound("This slot");
  const current = bootsSlot ? state.boots : state.items[index];
  const others = state.items.filter((name, i): name is string => name !== null && (bootsSlot || i !== index));
  const choose = (name: string | null) => {
    if (bootsSlot) store.set({ ...state, boots: name });
    else store.set({ ...state, items: state.items.map((value, i) => (i === index ? name : value)) });
    done();
  };
  const list = h("div", { class: "list" });
  const key = bootsSlot ? "pick-boots" : "pick-items";
  const render = (query: string) => {
    const candidates = (bootsSlot ? db.boots : db.items).filter((item) => matches(query, item.name));
    const rows = candidates.map((item) => {
      const problems = bootsSlot ? [] : buildProblems(db, [...others, item.name], null);
      const stats = itemStatLines(item).slice(0, 2).map((line) => `${line.value} ${line.label}`);
      const badge = bootsSlot ? null : tierBadge(tierOf(db, item.name));
      return pickRow(item, [formatGold(item.gold), ...stats].join(" · "), problems[0] ?? null, badge, () => choose(item.name));
    });
    list.replaceChildren(...(rows.length ? rows : [emptyState("Nothing matches this search.")]));
  };
  render(currentQuery(key));
  return {
    title: bootsSlot ? "Choose boots" : "Choose an item",
    back: true,
    body: h(
      "section",
      {},
      current ? h("button", { class: "button clear", type: "button", onclick: () => choose(null) }, `Remove ${current}`) : null,
      searchField(key, bootsSlot ? "Search boots" : "Search items", render),
      list,
    ),
  };
}
