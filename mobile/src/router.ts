/** Hash routes: #/champions, #/champions/Ezreal, #/items?type=boots, #/items/boots/Mercury's Treads, … */

export type Section = "champions" | "items" | "runes" | "about";

export interface Route {
  section: Section;
  /** Path parts after the section, URL-decoded. */
  parts: string[];
  params: URLSearchParams;
}

const SECTIONS: Section[] = ["champions", "items", "runes", "about"];

export function parseRoute(hash: string): Route {
  const [path, query = ""] = hash.replace(/^#\/?/, "").split("?");
  const [first = "", ...rest] = path.split("/").filter(Boolean);
  const section = (SECTIONS as string[]).includes(first) ? (first as Section) : "champions";
  return { section, parts: rest.map(decodeURIComponent), params: new URLSearchParams(query) };
}

export function href(section: Section, parts: string[] = [], params: Record<string, string> = {}): string {
  const path = [section, ...parts.map(encodeURIComponent)].join("/");
  const query = new URLSearchParams(params).toString();
  return `#/${path}${query ? `?${query}` : ""}`;
}
