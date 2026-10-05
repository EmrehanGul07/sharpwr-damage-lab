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

export function listRow(target: string, iconSrc: string | null, title: string, subtitle: string): HTMLElement {
  return h(
    "a",
    { class: "row", href: target },
    icon(iconSrc, "", 44),
    h("span", { class: "row-text" }, h("strong", {}, title), h("span", {}, subtitle)),
    h("span", { class: "chevron", "aria-hidden": "true" }, "›"),
  );
}

export function segments(options: Array<{ label: string; target: string; active: boolean }>): HTMLElement {
  return h(
    "nav",
    { class: "segments" },
    ...options.map((option) =>
      h("a", { href: option.target, class: option.active ? "active" : "", "aria-current": option.active ? "page" : undefined }, option.label),
    ),
  );
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
