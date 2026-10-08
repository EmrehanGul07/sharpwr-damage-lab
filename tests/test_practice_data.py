"""Practice Tool numbers (sharpwr/practice_data.py) are the engine's, and the committed export is current."""

import ast
import json
import unittest
from pathlib import Path

from marksman_art import practice_catalogue
from sharpwr.app_data import champion_level_stats
from sharpwr.champion_database import CHAMPION_DATABASE
from sharpwr.marksman_damage_components import damage_component
from sharpwr.marksman_kits import Kit, default_ranks
from sharpwr.practice_data import (
    HIT_OPTIONS,
    MARKS,
    ON_ATTACK,
    SKIPPED,
    engine_buff_calls,
    practice_data,
    render_practice_json,
)

ROOT = Path(__file__).resolve().parents[1]


class PracticeDataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = practice_data()["champions"]

    def test_committed_export_is_current(self):
        committed = (ROOT / "app-data" / "practice.json").read_text()
        self.assertTrue(
            committed == render_practice_json(practice_catalogue(icon_files=True)),
            "Run: python scripts/export_app_data.py",
        )

    def test_every_champion_has_level_stats_from_the_engine(self):
        self.assertEqual(sorted(self.data), sorted(CHAMPION_DATABASE))
        for name, record in self.data.items():
            for level in (1, 9, 15):
                stats = champion_level_stats(name, level)
                self.assertAlmostEqual(record["levels"]["ad"][level - 1], stats["attack_damage"], delta=6e-4)
                self.assertAlmostEqual(record["levels"]["as"][level - 1], stats["attack_speed"], delta=6e-4)
                self.assertEqual(record["levels"]["ms"][level - 1], stats["movement_speed"])
                for field in ("hp", "armor", "mr"):
                    self.assertAlmostEqual(record["levels"][field][level - 1], stats[field], delta=6e-4)
                self.assertEqual(record["ranks"][level - 1], default_ranks(name, level))

    def test_hit_damage_is_damage_component(self):
        for name, record in self.data.items():
            for slot, entry in record["slots"].items():
                if entry["mode"] not in ("hit", "mark", "attack"):
                    continue
                for rank, level in ((1, 1), (2, 9), (3, 15)):
                    ad = champion_level_stats(name, level)["attack_damage"]
                    raw = damage_component(
                        name, slot, rank, ad=ad, base_ad=ad, level=level, **HIT_OPTIONS.get((name, slot), {})
                    )
                    for kind, rows in entry["damage"].items():
                        self.assertAlmostEqual(rows[rank - 1][level - 1], getattr(raw, kind), delta=6e-4, msg=f"{name} {slot}")

    def test_rules_name_real_abilities(self):
        for name, slot in [*HIT_OPTIONS, *ON_ATTACK, *MARKS, *SKIPPED]:
            self.assertIn(name, CHAMPION_DATABASE)
            self.assertIn(slot, "QWER")
        for (name, slot), _ in SKIPPED.items():
            self.assertEqual(self.data[name]["slots"][slot]["mode"], "skip")

    def test_buffs_are_the_fight_engine_buffs(self):
        tristana = self.data["Tristana"]["slots"]["Q"]["buff"]
        self.assertEqual(tristana["as"], [0.6, 0.8, 1, 1.2])
        self.assertEqual(tristana["duration"], [7, 7, 7, 7])
        vayne = self.data["Vayne"]["slots"]["R"]["buff"]
        self.assertEqual((vayne["ad"], vayne["duration"]), ([30, 40, 50], [8, 10, 12]))
        twitch = self.data["Twitch"]["slots"]["R"]["buff"]
        self.assertEqual((twitch["ad"], twitch["range"]), ([30, 45, 60], [225, 225, 225]))
        self.assertEqual(self.data["Kog'Maw"]["slots"]["W"]["buff"]["range"], [90, 120, 150, 180])
        self.assertEqual(self.data["Yunara"]["slots"]["R"]["buff"]["by"], "Q")
        self.assertEqual(self.data["Kog'Maw"]["rank_as"], {"R": [0.1, 0.2, 0.3]})

    def test_every_stat_buff_in_the_fight_engine_is_found(self):
        """Each buff() whose key the kit reads as attack speed or AD belongs to one champion and slot."""
        source = (ROOT / "sharpwr" / "marksman_fight_engine.py").read_text()
        keys = set()
        for node in ast.walk(ast.parse(source)):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "buff":
                for sub in ast.walk(node.args[0]):
                    if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
                        keys.add(sub.value)
            if isinstance(node, ast.keyword) and node.arg == "key" and isinstance(node.value, ast.Constant):
                keys.add(node.value.value)
        stat_keys = {k for k in keys if k.endswith(("_as", "_ad"))}
        found = set()
        for name, slots, key, *_ in engine_buff_calls():
            self.assertTrue(slots, f"{name} buff without a slot")
            for slot in slots:
                found.add(eval(compile(ast.Expression(key), "", "eval"), {"__builtins__": {}}, {"slot": slot}))
        self.assertTrue(stat_keys <= found, stat_keys - found)

    def test_cooldowns_and_cast_times_come_from_the_kit(self):
        for name, record in self.data.items():
            for slot, entry in record["slots"].items():
                ranks = {"Q": 4, "W": 4, "E": 4, "R": 3}
                kit = Kit(name, ranks, 1, CHAMPION_DATABASE[name]["stats"]["attack_range"])
                self.assertAlmostEqual(entry["cast"], kit.cast_time(slot, 0.0, 0.0), delta=6e-4)
                cd = kit.cd(slot)
                self.assertEqual(entry["cooldown"][-1], None if cd is None else round(cd, 3))

    def test_web_and_phone_share_the_catalogue(self):
        web, phone = practice_catalogue(), json.loads((ROOT / "app-data" / "practice.json").read_text())
        for name in CHAMPION_DATABASE:
            self.assertEqual(web["champions"][name]["practice"], phone["champions"][name]["practice"])
            self.assertTrue(all(v.startswith("data:image/") for v in web["champions"][name]["hud"]["icons"].values()))
            self.assertTrue(all((ROOT / v).is_file() for v in phone["champions"][name]["hud"]["icons"].values()))


if __name__ == "__main__":
    unittest.main()
