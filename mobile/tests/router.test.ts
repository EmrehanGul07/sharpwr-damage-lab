import { describe, expect, it } from "vitest";
import { href, parseRoute } from "../src/router";

describe("router", () => {
  it("round-trips names with spaces and apostrophes", () => {
    const target = href("items", ["boots", "Mercury's Treads"]);
    const route = parseRoute(target);
    expect(route.section).toBe("items");
    expect(route.parts).toEqual(["boots", "Mercury's Treads"]);
  });

  it("reads query parameters and falls back to champions", () => {
    expect(parseRoute(href("runes", [], { tree: "Key Rune" })).params.get("tree")).toBe("Key Rune");
    expect(parseRoute("").section).toBe("champions");
    expect(parseRoute("#/unknown").section).toBe("champions");
  });

  it("opens the tier list and champion tabs", () => {
    expect(parseRoute(href("tiers")).section).toBe("tiers");
    const route = parseRoute(href("champions", ["Kai'Sa"], { tab: "stats" }));
    expect(route.parts).toEqual(["Kai'Sa"]);
    expect(route.params.get("tab")).toBe("stats");
  });
});
