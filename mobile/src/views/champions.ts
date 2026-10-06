import { buildParams } from "../build-state";
import { BUILD_LEVELS, KEYSTONE_CHECK_LEVELS, TARGETS, championCore, coreItems, findItem, rankKeystones, stageFor } from "../builds";
import type { Ability, AbilitySlot, BuildStyle, Champion, ChampionCore, CoreBuild, CoreStage, Database, Target } from "../data";
import { h, icon } from "../dom";
import { LEVEL_STATS, formatGold, formatNumber, perRank, trimNumber } from "../format";
import { href } from "../router";
import { matches } from "../search";
import { modelTab } from "./model3d";
import {
  type View,
  choiceChips,
  currentQuery,
  emptyState,
  itemIcon,
  itemTile,
  listFooter,
  listRow,
  notFound,
  searchField,
  segments,
  statTable,
} from "./shared";

// Kept while the user moves between champions.
let selectedLevel = 1;
let buildLevel = 15;
let buildTarget: Target = "squishy";
// Selected build style per champion.
const selectedStyle = new Map<string, string>();

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

/** Core item icons at the end of a champion row; plain images, since the row is already a link. */
function coreIcons(db: Database, champion: Champion): HTMLElement | null {
  const core = coreItems(db, champion);
  if (!core.length) return null;
  return h("span", { class: "row-core", title: `Core item: ${core.join(", ")}` }, ...core.map((name) => icon(findItem(db, name)?.icon ?? null, name, 30)));
}

function subtitle(champion: Champion): string {
  const range = champion.levels["1"]?.attack_range;
  return [champion.attack_type, range ? `Range ${range}` : null].filter(Boolean).join(" · ");
}

export function championList(db: Database): View {
  const list = h("div", { class: "list" });
  const render = (query: string) => {
    const rows = db.champions
      .filter((champion) => matches(query, champion.name))
      .map((champion) => listRow(href("champions", [champion.name]), champion.icon, champion.name, subtitle(champion), coreIcons(db, champion)));
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

function coreCard(db: Database, champion: Champion, core: ChampionCore): HTMLElement {
  const pick = champion.editor_core;
  const engine = h("div", { class: "core-items" }, ...core.core.map((name) => itemTile(db, name, pick ? 44 : 56)));
  const engineText = `The item that appears most consistently in ${champion.name}'s top builds from level 5 to 15, against all three targets.`;
  if (!pick) {
    return h("div", { class: "core-card" }, h("p", { class: "eyebrow" }, core.core.length > 1 ? "Core items" : "Core item"), engine, h("p", { class: "muted small" }, engineText));
  }
  const agrees = core.core.includes(pick.item);
  return h(
    "div",
    { class: "core-card" },
    h("p", { class: "eyebrow" }, "Core item · SharpWR pick"),
    h("div", { class: "core-items" }, itemTile(db, pick.item, 56)),
    pick.reason ? h("p", { class: "small" }, pick.reason) : null,
    h("p", { class: "eyebrow" }, agrees ? "The damage engine agrees" : "Damage engine's core"),
    agrees ? null : engine,
    h("p", { class: "muted small" }, engineText, agrees ? "" : ` Compare both in "Build styles" below.`),
  );
}

function runeIcon(db: Database, name: string, size: number): HTMLElement {
  const rune = db.runes.find((record) => record.name === name);
  const image = icon(rune?.icon ?? null, name, size);
  return rune ? h("a", { class: "icon-link", href: href("runes", [rune.name]), title: name }, image) : image;
}

function keystoneLevel(): number {
  return KEYSTONE_CHECK_LEVELS.includes(buildLevel) ? buildLevel : KEYSTONE_CHECK_LEVELS[KEYSTONE_CHECK_LEVELS.length - 1];
}

function keystoneCheck(core: ChampionCore, keystone: string): HTMLElement | null {
  const level = keystoneLevel();
  const row = core.keystone_check?.find((check) => check.level === level && check.target === buildTarget);
  if (!row) return null;
  const own = row.ttk[keystone] ?? null;
  const target = TARGETS.find((option) => option.key === buildTarget);
  return h(
    "div",
    {},
    h("p", { class: "muted small" }, `Keystone check · level ${level} vs ${target?.label.toLowerCase()}: this matchup's #1 build with each keystone and the rest of the page.`),
    statTable(
      rankKeystones(row.ttk).map(([name, ttk]): [string, string] => {
        const label = name === keystone ? `${name} (page)` : name;
        if (ttk === null) return [label, "Target survived"];
        const change = own !== null && name !== keystone ? ` (${ttk <= own ? "−" : "+"}${trimNumber((Math.abs(ttk - own) / own) * 100, 1)}%)` : "";
        return [label, `TTK ${trimNumber(ttk)} s${change}`];
      }),
    ),
  );
}

function runeCard(db: Database, champion: Champion, core: ChampionCore): HTMLElement | null {
  const page = champion.rune_page;
  if (!page) return null;
  const names = [page.keystone, ...page.primary, page.secondary];
  return h(
    "div",
    { class: "rune-card" },
    h("p", { class: "eyebrow" }, "Rune page"),
    h("div", { class: "rune-icons" }, runeIcon(db, page.keystone, 48), ...[...page.primary, page.secondary].map((name) => runeIcon(db, name, 34))),
    h("p", { class: "build-names" }, names.join(" · ")),
    h("p", { class: "muted small" }, "SharpWR's default page. Every build below is calculated with it; stacking runes fill with level."),
    keystoneCheck(core, page.keystone),
  );
}

function buildCard(db: Database, champion: Champion, stage: CoreStage, build: CoreBuild, rank: number): HTMLElement {
  const names = [...build.items, build.boots];
  const ttk = build.ttk === null ? "Target survived" : `TTK ${trimNumber(build.ttk)} s`;
  return h(
    "div",
    { class: rank === 1 ? "build best" : "build" },
    h("div", { class: "build-head" }, h("strong", {}, `#${rank}`), h("span", {}, `${ttk} · ${Math.round(build.dps)} DPS · ${formatGold(build.gold)}`)),
    h("div", { class: "build-icons" }, ...names.map((name) => itemIcon(db, name, 44))),
    h("p", { class: "build-names" }, names.join(" · ")),
    build.note ? h("p", { class: "build-note" }, build.note) : null,
    h("a", { class: "try", href: href("build", [], buildParams(champion.name, stage.level, build.items, build.boots)) }, "Try in Build Lab ›"),
  );
}

function stageView(db: Database, champion: Champion, stages: CoreStage[]): HTMLElement {
  const stage = stageFor(stages, buildLevel, buildTarget);
  if (!stage) return emptyState("No saved builds for this level and target.");
  const target = TARGETS.find((option) => option.key === buildTarget);
  const items = stage.items_allowed === 1 ? "1 item" : `${stage.items_allowed} items`;
  return h(
    "div",
    {},
    h("p", { class: "muted small" }, `Level ${stage.level} · ${items} + boots · vs ${target?.label.toLowerCase()} (${target?.example})`),
    ...stage.builds.map((build, index) => buildCard(db, champion, stage, build, index + 1)),
  );
}

function styleLabel(style: BuildStyle): string {
  return style.editor ? `${style.items[0]} (SharpWR pick)` : style.name;
}

function styleView(db: Database, champion: Champion, style: BuildStyle): HTMLElement {
  const facts = [
    style.items.length ? `Holds ${style.items.join(", then ")}` : null,
    style.keystone ? `Keystone: ${style.keystone}` : null,
  ].filter(Boolean);
  return h(
    "div",
    {},
    style.note ? h("p", { class: "small" }, style.note) : null,
    facts.length ? h("p", { class: "muted small" }, facts.join(" · ")) : null,
    stageView(db, champion, style.stages),
  );
}

function rankingList(db: Database, core: ChampionCore): HTMLElement {
  return h(
    "div",
    { class: "list" },
    ...core.ranking.map((row, index) => {
      const item = findItem(db, row.item);
      const subtitle = `Score ${trimNumber(row.score, 1)} · #1 build in ${row.winner_cells} of ${row.eligible_cells} matchups`;
      const target = item ? href("items", [item.category, item.name]) : href("items");
      return listRow(target, item?.icon ?? null, `${index + 1}. ${row.item}`, subtitle);
    }),
  );
}

function method(db: Database, core: ChampionCore): HTMLElement {
  const excluded = db.core_items?.excluded ?? [];
  return h(
    "div",
    {},
    h("h3", {}, "How these are calculated"),
    h(
      "p",
      { class: "note" },
      "SharpWR's damage model fights a training target that does not hit back, using the champion's rune page. A matchup is one level and target type; the target is a champion of that type at the same level. TTK is the time to defeat the target. The item ranking weights each matchup's top 3 builds 1, 1/2 and 1/3. These are bounded searches, not match statistics.",
    ),
    excluded.length
      ? h("p", { class: "note" }, `The core item search and item ranking leave out ${excluded.join(", ")}, which are strong but never a first item. Top builds and build styles use every item.`)
      : null,
    core.notes.length
      ? h("details", { class: "notes" }, h("summary", {}, `Unverified mechanics (${core.notes.length})`), h("ul", {}, ...core.notes.map((note) => h("li", {}, note))))
      : null,
  );
}

function buildsTab(db: Database, champion: Champion): Array<HTMLElement | null> {
  const core = championCore(db, champion.name);
  if (!core) {
    const text = db.core_items
      ? `Build results for ${champion.name} are being recalculated.`
      : "Build results arrive with the next data update. Connect to the internet and reopen the app.";
    return [emptyState(text)];
  }
  const styles = core.styles ?? [];
  const styleKey = () => {
    const key = selectedStyle.get(champion.name);
    return styles.some((style) => style.key === key) ? key : (styles.find((style) => style.editor) ?? styles[0])?.key;
  };
  const stage = h("div", {}, stageView(db, champion, core.stages));
  const styleStage = h("div", {});
  const runes = h("div", {});
  const redraw = () => {
    stage.replaceChildren(stageView(db, champion, core.stages));
    const style = styles.find((option) => option.key === styleKey());
    styleStage.replaceChildren(...(style ? [styleView(db, champion, style)] : []));
    runes.replaceChildren(...[runeCard(db, champion, core)].filter((node): node is HTMLElement => node !== null));
  };
  redraw();
  return [
    coreCard(db, champion, core),
    runes,
    choiceChips(
      "Level",
      BUILD_LEVELS.map((level) => ({ value: level, label: String(level) })),
      buildLevel,
      (level) => {
        buildLevel = level;
        redraw();
      },
    ),
    choiceChips(
      "Target",
      TARGETS.map((target) => ({ value: target.key, label: target.label })),
      buildTarget,
      (target) => {
        buildTarget = target;
        redraw();
      },
    ),
    h("h3", {}, "Top builds"),
    stage,
    ...(styles.length
      ? [
          h("h3", {}, "Build styles"),
          choiceChips(
            "Style",
            styles.map((style) => ({ value: style.key, label: styleLabel(style) })),
            styleKey() ?? "",
            (key) => {
              selectedStyle.set(champion.name, key);
              redraw();
            },
          ),
          styleStage,
        ]
      : []),
    h("h3", {}, "Item ranking"),
    rankingList(db, core),
    method(db, core),
  ];
}

const SLOT_LABELS: Record<AbilitySlot, string> = { P: "Passive", Q: "Q", W: "W", E: "E", R: "Ultimate" };

function abilityCard(ability: Ability): HTMLElement {
  const cooldown = perRank(ability.cooldown);
  const mana = perRank(ability.mana);
  const facts = [
    cooldown ? `Cooldown ${cooldown} s` : null,
    mana ? `Mana ${mana}` : null,
    ability.range ? `Range ${trimNumber(ability.range, 0)}` : null,
  ].filter(Boolean);
  return h(
    "div",
    { class: "ability" },
    icon(ability.icon, ability.name, 48),
    h(
      "div",
      { class: "ability-text" },
      h("p", { class: "ability-head" }, h("span", { class: "ability-slot" }, SLOT_LABELS[ability.slot]), h("strong", {}, ability.name)),
      facts.length ? h("p", { class: "ability-facts" }, facts.join(" · ")) : null,
      h("p", { class: "ability-description" }, ability.description),
    ),
  );
}

function abilitiesTab(champion: Champion): HTMLElement[] {
  if (!champion.abilities?.length) {
    return [emptyState("Abilities arrive with the next data update. Connect to the internet and reopen the app.")];
  }
  return [
    ...champion.abilities.map(abilityCard),
    h("p", { class: "note" }, "Numbers per rank, recorded from the game. Summaries by SharpWR; AD and AP ratios in brackets."),
  ];
}

function statsTab(champion: Champion): HTMLElement[] {
  const levelLabel = h("output", { class: "level-value" }, `Level ${selectedLevel}`);
  const slider = h("input", { type: "range", min: 1, max: 15, step: 1, class: "level", "aria-label": "Champion level" });
  slider.value = String(selectedLevel);
  const table = h("div", {}, levelTable(champion, selectedLevel));
  slider.addEventListener("input", () => {
    selectedLevel = Number(slider.value);
    levelLabel.textContent = `Level ${selectedLevel}`;
    table.replaceChildren(levelTable(champion, selectedLevel));
  });
  return [
    h("h3", {}, "Stats by level"),
    h("p", { class: "muted small" }, "Before items and runes."),
    h("div", { class: "level-row" }, slider, levelLabel),
    table,
    h("h3", {}, "Base values"),
    baseTable(champion),
    source(champion),
  ];
}

export function championDetail(db: Database, name: string, params: URLSearchParams): View {
  const champion = db.champions.find((record) => record.name === name);
  if (!champion) return notFound(name);
  const tab = params.get("tab");
  const meta = [champion.attack_type, champion.resource_type].filter(Boolean).join(" · ");
  const tabs = segments(
    [
      { label: "Builds", target: href("champions", [champion.name]), active: tab !== "stats" && tab !== "abilities" && tab !== "3d" },
      { label: "Abilities", target: href("champions", [champion.name], { tab: "abilities" }), active: tab === "abilities" },
      { label: "Stats", target: href("champions", [champion.name], { tab: "stats" }), active: tab === "stats" },
      { label: "3D", target: href("champions", [champion.name], { tab: "3d" }), active: tab === "3d" },
    ],
    true,
  );
  const content =
    tab === "stats" ? statsTab(champion) : tab === "abilities" ? abilitiesTab(champion) : tab === "3d" ? modelTab(champion) : buildsTab(db, champion);
  return {
    title: champion.name,
    back: true,
    body: h(
      "section",
      { class: "detail" },
      h("div", { class: "hero" }, icon(champion.icon, champion.name, 88, "portrait"), h("div", {}, h("h2", {}, champion.name), meta ? h("p", { class: "muted" }, meta) : null)),
      tabs,
      ...content,
    ),
  };
}
