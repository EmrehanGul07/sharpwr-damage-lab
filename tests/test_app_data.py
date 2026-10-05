"""The mobile app's Database export stays current, complete and consistent with the web app."""

import unittest
from pathlib import Path

from sharpwr import B, F, P
from sharpwr.app_data import build_database, champion_level_stats, render_database_json
from sharpwr.champion_database import CHAMPION_DATABASE
from sharpwr.rune_database import RUNE_DATABASE

ROOT = Path(__file__).resolve().parents[1]


class AppDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build_database()

    def test_committed_export_is_current(self):
        committed = (ROOT / "app-data" / "database.json").read_text()
        self.assertTrue(committed == render_database_json(), "Run: python scripts/export_app_data.py")

    def test_every_database_record_is_exported_in_display_order(self):
        data = self.data
        self.assertEqual([c["name"] for c in data["champions"]], list(CHAMPION_DATABASE))
        self.assertEqual([i["name"] for i in data["items"]], list(F))
        self.assertEqual([i["name"] for i in data["components"]], list(P))
        self.assertEqual([i["name"] for i in data["boots"]], list(B))
        self.assertEqual([r["name"] for r in data["runes"]], list(RUNE_DATABASE))
        for champion in data["champions"]:
            self.assertEqual(list(champion["levels"]), [str(level) for level in range(1, 16)])

    def test_movement_speed_unit_is_explicit(self):
        for group in ("items", "components", "boots"):
            for record in self.data[group]:
                ms = record["stats"]["ms"]
                if not ms:
                    self.assertNotIn("ms_unit", record)
                elif record["ms_unit"] == "flat":
                    self.assertGreaterEqual(ms, 1, record["name"])
                else:
                    self.assertEqual(record["ms_unit"], "fraction")
                    self.assertLess(ms, 1, record["name"])

    def test_level_stats_match_the_champion_card(self):
        # Live champion card: Kalista level 9 shows 92.0 AD and 1.020 attack speed.
        kalista = champion_level_stats("Kalista", 9)
        self.assertEqual(round(kalista["attack_damage"], 1), 92.0)
        self.assertEqual(round(kalista["attack_speed"], 3), 1.020)
        exported = next(c for c in self.data["champions"] if c["name"] == "Kalista")["levels"]["9"]
        self.assertAlmostEqual(exported["attack_speed"], kalista["attack_speed"], places=4)


if __name__ == "__main__":
    unittest.main()
