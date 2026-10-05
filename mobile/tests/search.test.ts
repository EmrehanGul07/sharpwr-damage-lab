import { describe, expect, it } from "vitest";
import { matches, normalize } from "../src/search";

describe("search", () => {
  it("ignores case, spaces and punctuation", () => {
    expect(normalize("Kai'Sa")).toBe("kaisa");
    expect(matches("kaisa", "Kai'Sa")).toBe(true);
    expect(matches("kog maw", "Kog'Maw")).toBe(true);
    expect(matches("miss f", "Miss Fortune")).toBe(true);
  });

  it("matches any field and treats an empty query as a match", () => {
    expect(matches("", "Anything")).toBe(true);
    expect(matches("true damage", "First Strike", "deal 7% bonus true damage")).toBe(true);
    expect(matches("zzz", "Ezreal")).toBe(false);
  });
});
