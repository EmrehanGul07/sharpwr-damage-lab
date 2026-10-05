import { describe, expect, it } from "vitest";
import type { Item } from "../src/data";
import { formatDate, formatGold, formatNumber, humanize, itemStatLines, trimNumber } from "../src/format";

function item(stats: Partial<Item["stats"]>, extra: Partial<Item> = {}): Item {
  const zero = { ad: 0, as: 0, crit: 0, ap: 0, hp: 0, mana: 0, armor: 0, mr: 0, ah: 0, ls: 0, flatpen: 0, pctpen: 0, ms: 0, flatmpen: 0, pctmpen: 0 };
  return { name: "Test", icon: null, category: "completed", gold: 2650, stats: { ...zero, ...stats }, ...extra };
}

describe("format", () => {
  it("shows a download time as a short day", () => {
    expect(formatDate("2026-10-05T11:48:51.000Z")).toBe("5 Oct 2026");
  });

  it("trims numbers to at most two decimals", () => {
    expect(trimNumber(0.4 * 100)).toBe("40");
    expect(trimNumber(4.5)).toBe("4.5");
    expect(trimNumber(0.022 * 100)).toBe("2.2");
    expect(trimNumber(0.644, 3)).toBe("0.644");
  });

  it("turns identifiers into readable labels", () => {
    expect(humanize("attack_damage")).toBe("Attack damage");
    expect(humanize("damage")).toBe("Damage");
  });

  it("shows unknown values as a dash and keeps fixed decimals", () => {
    expect(formatNumber(null, 1)).toBe("—");
    expect(formatNumber(2191.8, 0)).toBe("2,192");
    expect(formatNumber(1.02, 3)).toBe("1.020");
    expect(formatGold(3400)).toBe("3,400 gold");
  });

  it("lists only non-zero item stats with their units", () => {
    // Phantom Dancer: 40% AS, 25% crit, 7% movement speed.
    const lines = itemStatLines(item({ as: 0.4, crit: 0.25, ms: 0.07 }, { ms_unit: "fraction" }));
    expect(lines).toEqual([
      { label: "Attack Speed", value: "+40%" },
      { label: "Critical Strike", value: "+25%" },
      { label: "Movement Speed", value: "+7%" },
    ]);
  });

  it("shows flat movement speed for boots", () => {
    expect(itemStatLines(item({ ms: 45 }, { category: "boots", ms_unit: "flat" }))).toEqual([{ label: "Movement Speed", value: "+45" }]);
  });
});
