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
});
