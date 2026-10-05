import { findItem } from "../builds";
import type { Database } from "../data";
import { h, icon } from "../dom";
import { href } from "../router";

export interface View {
  title: string;
  /** Detail pages show a back button. */
  back: boolean;
  body: HTMLElement;
}

export const RIOT_NOTICE =
  "SharpWR isn't endorsed by Riot Games and doesn't reflect the views or opinions of Riot Games or anyone officially involved in producing or managing Riot Games properties. Riot Games, and all associated properties are trademarks or registered trademarks of Riot Games, Inc.";

/** Search text per list, kept while the user opens and closes detail pages. */
const queries: Record<string, string> = {};

export function searchField(key: string, placeholder: string, onChange: (query: string) => void): HTMLElement {
  const input = h("input", {
    class: "search",
    type: "search",
    placeholder,
    "aria-label": placeholder,
    autocomplete: "off",
    enterkeyhint: "search",
  });
  input.value = queries[key] ?? "";
  input.addEventListener("input", () => {
    queries[key] = input.value;
    onChange(input.value);
  });
  return input;
}

export function currentQuery(key: string): string {
  return queries[key] ?? "";
}

export function listRow(
  target: string,
  iconSrc: string | null,
  title: string,
  subtitle: string,
  badge: HTMLElement | null = null,
): HTMLElement {
  return h(
    "a",
    { class: "row", href: target },
    icon(iconSrc, "", 44),
    h("span", { class: "row-text" }, h("strong", {}, title), h("span", {}, subtitle)),
    badge,
    h("span", { class: "chevron", "aria-hidden": "true" }, "›"),
  );
}

/**
 * Links between views of one screen. With `replace`, switching does not add a history entry,
 * so Back leaves the screen instead of stepping through its views.
 */
export function segments(options: Array<{ label: string; target: string; active: boolean }>, replace = false): HTMLElement {
  return h(
    "nav",
    { class: "segments" },
    ...options.map((option) =>
      h(
        "a",
        {
          href: option.target,
          class: option.active ? "active" : "",
          "aria-current": option.active ? "page" : undefined,
          onclick: replace
            ? (event: Event) => {
                event.preventDefault();
                location.replace(option.target);
              }
            : undefined,
        },
        option.label,
      ),
    ),
  );
}

/** Buttons that pick one option in place, without leaving the screen. */
export function choiceChips<T>(
  label: string,
  options: ReadonlyArray<{ value: T; label: string }>,
  selected: T,
  onSelect: (value: T) => void,
): HTMLElement {
  const group = h("div", { class: "segments choices", role: "group", "aria-label": label });
  const draw = (current: T) =>
    group.replaceChildren(
      h("span", { class: "chips-label", "aria-hidden": "true" }, label),
      ...options.map((option) =>
        h(
          "button",
          {
            type: "button",
            class: option.value === current ? "active" : "",
            "aria-pressed": String(option.value === current),
            onclick: () => {
              draw(option.value);
              onSelect(option.value);
            },
          },
          option.label,
        ),
      ),
    );
  draw(selected);
  return group;
}

/** Same colours as the web app's tier board (assets/live_tier_list.html). */
const TIER_COLORS: Record<string, string> = {
  S: "#f48c89",
  A: "#f7b083",
  B: "#f3d184",
  C: "#91cdab",
  D: "#86b9df",
  F: "#ad9ed7",
};

export function tierBadge(tier: string | null, extraClass = ""): HTMLElement | null {
  if (!tier) return null;
  const style = `background:${TIER_COLORS[tier] ?? "var(--muted)"}`;
  return h("span", { class: `tier-badge ${extraClass}`.trim(), style, title: `Tier ${tier}` }, tier);
}

function itemHref(db: Database, name: string): string | null {
  const item = findItem(db, name);
  return item ? href("items", [item.category, item.name]) : null;
}

/** Item icon and name, linking to the item's page when the item is in the database. */
export function itemTile(db: Database, name: string, size = 52): HTMLElement {
  const target = itemHref(db, name);
  const content = [icon(findItem(db, name)?.icon ?? null, "", size), h("span", {}, name)];
  return target ? h("a", { class: "tile", href: target }, ...content) : h("span", { class: "tile" }, ...content);
}

/** Item icon alone, linking to the item's page. */
export function itemIcon(db: Database, name: string, size = 44): HTMLElement {
  const target = itemHref(db, name);
  const image = icon(findItem(db, name)?.icon ?? null, name, size);
  return target ? h("a", { class: "icon-link", href: target, title: name }, image) : image;
}

export function statTable(rows: Array<[string, string]>): HTMLElement {
  return h(
    "dl",
    { class: "stats" },
    ...rows.flatMap(([label, value]) => [h("dt", {}, label), h("dd", {}, value)]),
  );
}

export function emptyState(text: string): HTMLElement {
  return h("p", { class: "status" }, text);
}

/** Short Riot notice under every list; the full text is on the About page. */
export function listFooter(): HTMLElement {
  return h(
    "p",
    { class: "footnote" },
    "Free fan project, not endorsed by Riot Games. ",
    h("a", { href: href("about") }, "About"),
  );
}

export function notFound(what: string): View {
  return { title: "Not found", back: true, body: emptyState(`${what} is not in the database.`) };
}
