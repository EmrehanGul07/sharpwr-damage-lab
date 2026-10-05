"""The mobile app's Database export stays current, complete and consistent with the web app."""

import json
import unittest
from pathlib import Path
from unittest.mock import patch

from sharpwr import B, F, P
from sharpwr.app_data import (
    ability_icon_files,
    build_database,
    champion_level_stats,
    render_database_json,
)
from sharpwr.champion_database import CHAMPION_DATABASE
from sharpwr.core_items import BUDGETS, EXCLUDED, core_leaders, core_record
from sharpwr.golden import build_stats_golden, render_golden_json
from sharpwr.rune_database import RUNE_DATABASE

ROOT = Path(__file__).resolve().parents[1]


class AppDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = build_database()

    def test_committed_export_is_current(self):
        committed = (ROOT / "app-data" / "database.json").read_text()
        self.assertTrue(
            committed == render_database_json(), "Run: python scripts/export_app_data.py"
        )

    def test_committed_golden_outputs_are_current(self):
        committed = (ROOT / "app-data" / "golden" / "build-stats.json").read_text()
        self.assertTrue(
            committed == render_golden_json(build_stats_golden()),
            "Run: python scripts/export_app_data.py",
        )

    def test_committed_ability_icons_are_current(self):
        files = ability_icon_files()
        folder = ROOT / "assets" / "riot" / "abilities"
        self.assertEqual(
            sorted(f"assets/riot/abilities/{path.name}" for path in folder.iterdir()),
            sorted(files),
            "Run: python scripts/export_app_data.py",
        )
        for name, data in files.items():
            self.assertTrue((ROOT / name).read_bytes() == data, name)

    def test_every_champion_has_five_described_abilities(self):
        for champion in self.data["champions"]:
            abilities = champion["abilities"]
            self.assertEqual([a["slot"] for a in abilities], ["P", "Q", "W", "E", "R"])
            for ability in abilities:
                where = (champion["name"], ability["slot"])
                self.assertTrue(ability["name"] and ability["description"], where)
                self.assertTrue((ROOT / ability["icon"]).is_file(), where)
                ranks = {"P": None, "R": 3}.get(ability["slot"], 4)
                for values in (ability["cooldown"], ability["mana"]):
                    if ranks is None:
                        self.assertIsNone(values, where)
                    elif values is not None:
                        self.assertEqual(len(values), ranks, where)

    def test_build_inputs_for_the_app(self):
        from sharpwr.catalog import C
        from sharpwr.build_fight_optimizer import EXCLUSIVE

        for champion in self.data["champions"]:
            self.assertEqual(tuple(champion["aa"].values()), C[champion["name"]])
        rules = self.data["build_rules"]
        self.assertEqual(rules["max_items"], 5)
        self.assertEqual(
            [set(group) for group in rules["exclusive_groups"]], [set(g) for g in EXCLUSIVE]
        )

    def test_every_database_record_is_exported_in_display_order(self):
        data = self.data
        self.assertEqual([c["name"] for c in data["champions"]], list(CHAMPION_DATABASE))
        self.assertEqual([i["name"] for i in data["items"]], list(F))
        self.assertEqual([i["name"] for i in data["components"]], list(P))
        self.assertEqual([i["name"] for i in data["boots"]], list(B))
        self.assertEqual([r["name"] for r in data["runes"]], list(RUNE_DATABASE))
        for champion in data["champions"]:
            self.assertEqual(list(champion["levels"]), [str(level) for level in range(1, 16)])

    def test_icon_paths_point_to_bundled_files(self):
        groups = ("champions", "items", "components", "boots", "runes", "rune_trees")
        for group in groups:
            for record in self.data[group]:
                if group == "components":
                    self.assertIsNone(record["icon"], record["name"])
                else:
                    self.assertTrue((ROOT / record["icon"]).is_file(), (group, record["name"]))

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

    def test_tier_list_is_the_published_board(self):
        published = json.loads((ROOT / "data" / "published-tier-list.json").read_text())
        tier_list = self.data["tier_list"]
        self.assertEqual((tier_list["title"], tier_list["patch"]), (published["title"], "7.3a"))
        self.assertEqual([t["tier"] for t in tier_list["tiers"]], ["S", "A", "B", "C", "D", "F"])
        names = [name for tier in tier_list["tiers"] for name in tier["items"]]
        self.assertEqual(len(names), len(set(names)))
        for tier in tier_list["tiers"]:
            self.assertEqual(tier["items"], published["tiers"][tier["tier"]])
        self.assertLessEqual(set(names), set(F))

    def test_core_items_match_the_saved_search(self):
        core_items = self.data["core_items"]
        self.assertEqual(core_items["excluded"], sorted(EXCLUDED))
        self.assertEqual(list(core_items["champions"]), list(CHAMPION_DATABASE))
        for name, exported in core_items["champions"].items():
            record = core_record(name)
            self.assertIsNotNone(exported, name)
            self.assertEqual(exported["core"], core_leaders(record), name)
            self.assertEqual(
                [row["item"] for row in exported["ranking"]],
                [row["Item"] for row in record["ranking"]],
            )
            self.assertTrue(set(exported["core"]) <= {row["item"] for row in exported["ranking"]})
            stages = [
                (stage["level"], stage["target"], stage["items_allowed"])
                for stage in exported["stages"]
            ]
            expected = [
                (level, target, budget)
                for level, budget in BUDGETS.items()
                for target in ("squishy", "bruiser", "tank")
            ]
            self.assertEqual(stages, expected, name)
            for stage in exported["stages"]:
                saved = record["cells"][f'{stage["level"]}:{stage["target"]}']["search"]["full"]
                self.assertEqual(
                    [b["items"] for b in stage["builds"]], [row["Items"] for row in saved]
                )
                for build in stage["builds"]:
                    self.assertEqual(
                        len(build["items"]), stage["items_allowed"], (name, stage["level"])
                    )
                    self.assertTrue(set(build["items"]) <= set(F) - EXCLUDED, build["items"])
                    self.assertIn(build["boots"], B)
            self.assertTrue(all(isinstance(note, str) and note for note in exported["notes"]), name)

    def test_stale_core_results_are_left_out(self):
        with patch("sharpwr.app_data.core_record", return_value=None):
            data = build_database()
        self.assertEqual(set(data["core_items"]["champions"].values()), {None})

    def test_level_stats_match_the_champion_card(self):
        # Live champion card: Kalista level 9 shows 92.0 AD and 1.020 attack speed.
        kalista = champion_level_stats("Kalista", 9)
        self.assertEqual(round(kalista["attack_damage"], 1), 92.0)
        self.assertEqual(round(kalista["attack_speed"], 3), 1.020)
        exported = next(c for c in self.data["champions"] if c["name"] == "Kalista")["levels"]["9"]
        self.assertAlmostEqual(exported["attack_speed"], kalista["attack_speed"], places=4)


if __name__ == "__main__":
    unittest.main()
