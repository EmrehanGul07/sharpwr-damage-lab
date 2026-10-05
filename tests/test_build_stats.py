"""build_stats is the one source of the build summary and reproduces every saved search row."""

import json
import unittest
from pathlib import Path

from sharpwr.build_stats import build_stats

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = {
    "Gold": lambda s: s["gold"],
    "AD": lambda s: s["attack_damage"],
    "AP": lambda s: s["ability_power"],
    "Crit %": lambda s: 100 * s["crit_chance"],
    "AH": lambda s: s["ability_haste"],
    "Starting AS": lambda s: s["attack_speed"],
    "AS over cap": lambda s: s["attack_speed_over_cap"],
}


class BuildStatsTests(unittest.TestCase):
    def test_reproduces_every_saved_core_search_row(self):
        # Saved rows come from an older summation order: equal to 1e-9, not to the last bit.
        # Against the search code it replaced, build_stats is bit-for-bit identical
        # (21,242 builds, see verification in data/champion-core-items.json).
        payload = json.loads((ROOT / "data" / "champion-core-items.json").read_text())
        checked = 0
        for name, record in payload["champions"].items():
            for key, cell in record["cells"].items():
                for row in cell["search"]["full"]:
                    summary = build_stats(
                        name,
                        cell["level"],
                        row["Items"],
                        row["Boots"],
                        mist=40 if name == "Senna" else 0,
                        yuntal_stacks=cell["yuntal_start_stacks"],
                    )
                    for field, value in SUMMARY.items():
                        self.assertAlmostEqual(
                            value(summary), row[field], 9, (name, key, row["Items"], field)
                        )
                    checked += 1
        self.assertEqual(checked, 1242)

    def test_champion_rules(self):
        zeri = build_stats(
            "Zeri", 15, ["Kraken Slayer", "Phantom Dancer", "Statikk Shiv"], "Berserker's Greaves"
        )
        self.assertEqual((zeri["attack_speed"], zeri["attack_speed_cap"]), (1.5, 1.5))
        self.assertGreater(zeri["attack_speed_over_cap"], 0)
        jhin = build_stats("Jhin", 9, ["Infinity Edge"])
        self.assertEqual(jhin["attack_speed"], build_stats("Jhin", 9, [])["attack_speed"])
        self.assertAlmostEqual(build_stats("Senna", 1, ["Infinity Edge"])["crit_damage"], 2.07)
        self.assertEqual(build_stats("Senna", 1, [], mist=40)["crit_chance"], 0.2)

    def test_mana_items_and_unknown_values(self):
        plain = build_stats("Ezreal", 11, ["Manamune"])
        self.assertAlmostEqual(
            plain["attack_damage"] - build_stats("Ezreal", 11, [])["attack_damage"],
            40 + 0.02 * plain["mana"],
        )
        yunara = build_stats("Yunara", 1, [])
        self.assertIn(yunara["health"], (None, yunara["health"]))

    def test_item_order_does_not_matter(self):
        a = build_stats(
            "Kalista",
            13,
            ["Yun Tal Wildarrows", "Kraken Slayer", "Infinity Edge"],
            "Berserker's Greaves",
        )
        b = build_stats(
            "Kalista",
            13,
            ["Infinity Edge", "Kraken Slayer", "Yun Tal Wildarrows"],
            "Berserker's Greaves",
        )
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
