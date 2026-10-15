"""Validates ADR-0002 (Q32.32 fixed point + microsecond time) against the Python reference.

Run: python -I -m unittest discover -s tools/parity -p "test_*.py"
"""

import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

from fixed_point_model import (  # noqa: E402
    MICROS,
    Fix,
    aa_impacts_stationary,
    crit_scaled,
    effective_resistance,
    resistance_multiplier,
    scaled_ability,
    stat_at_level,
)

FIXTURE = ROOT / "game" / "parity" / "fixtures" / "samira-reference-v1.json"
# Samira reference inputs as they would arrive from game/content (decimal text, not floats).
SAMIRA = {
    "base_ad": "60",
    "ad_growth": "3.5",
    "base_hp": "630",
    "hp_growth": "128",
    "base_armor": "35",
    "armor_growth": "5",
    "base_mr": "30",
    "mr_growth": "1.4",
}
SKILLS = {
    "Q": {"base": ("15", "20", "25", "30"), "total_ad": "1.25", "bonus_ad": "0", "crit": "0.5"},
    "W": {"base": ("20", "40", "60", "80"), "total_ad": "0", "bonus_ad": "0.5", "crit": "0"},
    "E": {"base": ("45", "60", "75", "90"), "total_ad": "0", "bonus_ad": "0.2", "crit": "0"},
    "R": {"base": ("20", "40", "60"), "total_ad": "0.5", "bonus_ad": "0", "crit": "1"},
}


def fix(value):
    # Fixture numbers are Python floats; repr() gives the shortest round-tripping decimal,
    # which is what the content importer writes.
    return Fix.parse(repr(float(value)))


class FixedPointParity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(FIXTURE.read_text())
        cls.tol = cls.data["tolerance"]
        cls.max_error = {}

    def note(self, key, error):
        self.max_error[key] = max(self.max_error.get(key, 0.0), error)

    def test_level_stats(self):
        p = {k: Fix.parse(v) for k, v in SAMIRA.items()}
        for case in self.data["level_stats"]["cases"]:
            lvl = case["level"]
            for stat, base, growth in (
                ("ad", "base_ad", "ad_growth"),
                ("hp", "base_hp", "hp_growth"),
                ("armor", "base_armor", "armor_growth"),
                ("mr", "base_mr", "mr_growth"),
            ):
                got = stat_at_level(p[base], p[growth], lvl).to_float()
                error = abs(got - case[stat])
                self.note("stat", error)
                self.assertLessEqual(error, self.tol["stat"], (lvl, stat, got, case[stat]))

    def test_resistance(self):
        for case in self.data["resistance"]["cases"]:
            eff = effective_resistance(
                fix(case["resistance"]), fix(case["pct_pen"]), fix(case["flat_pen"])
            )
            mult = resistance_multiplier(eff)
            self.note("multiplier", abs(mult.to_float() - case["multiplier"]))
            self.assertLessEqual(abs(eff.to_float() - case["effective"]), self.tol["stat"], case)
            self.assertLessEqual(
                abs(mult.to_float() - case["multiplier"]), self.tol["multiplier"], case
            )

    def test_skills(self):
        zero = Fix(0)
        for case in self.data["skills"]["cases"]:
            s = SKILLS[case["slot"]]
            raw = scaled_ability(
                Fix.parse(s["base"][case["rank"] - 1]),
                Fix.parse(s["total_ad"]),
                Fix.parse(s["bonus_ad"]),
                fix(case["ad"]),
                fix(case["base_ad"]),
            )
            hit = crit_scaled(
                raw, Fix.parse(s["crit"]), fix(case["crit_damage"]), case["outcome"] == "Critical"
            )
            magic = case["slot"] == "E"
            resist = fix(case["mr"] if magic else case["armor"])
            dealt = zero
            for _ in range(case["hits"]):
                dealt = dealt + hit * resistance_multiplier(effective_resistance(resist, zero, zero))
            error = abs(dealt.to_float() - case["dealt_total"])
            self.note("damage", error)
            self.assertLessEqual(error, self.tol["damage"], (case, dealt.to_float()))

    def test_timeline(self):
        for scenario in self.data["timeline"]["scenarios"]:
            i = scenario["inputs"]
            impacts = aa_impacts_stationary(
                fix(i["aa_windup_seconds"]),
                fix(i["attack_speed"]),
                fix(i["distance"]),
                fix(i["projectile_speed"]),
                int(i["until_seconds"] * MICROS),
            )
            expected = [e["time"] for e in scenario["impacts"] if e["action"] == "AA"]
            self.assertEqual(len(impacts), len(expected), scenario["name"])
            for got, want in zip(impacts, expected):
                error = abs(got / MICROS - want)
                self.note("time_seconds", error)
                self.assertLessEqual(error, self.tol["time_seconds"], (scenario["name"], got, want))

    def test_champion_loop_from_content(self):
        """Same algorithm as Match: stats from content, us-grid periods, homing projectile."""
        from fixed_point_model import ONE_FIX, ZERO, growth_units, seconds_to_micros

        content = json.loads((ROOT / "game/content/reference-riot/champions/samira.champion.json").read_text())
        p = lambda k: Fix.parse(content["stats"][k]["value"])  # noqa: E731
        for sc in self.data["champion_loop"]["scenarios"]:
            i = sc["inputs"]
            bonus = p("bonus_attack_speed_level1") + p("bonus_attack_speed_per_level") * growth_units(i["level"])
            speed = p("base_attack_speed") + p("attack_speed_ratio") * bonus
            windup = p("attack_windup_seconds") / (ONE_FIX + p("attack_windup_bonus_as_factor") * bonus)
            ad = stat_at_level(p("base_ad"), p("ad_per_level"), i["level"])
            period = seconds_to_micros(ONE_FIX / speed)
            lead = seconds_to_micros(windup) + seconds_to_micros(fix(i["distance"]) / p("attack_projectile_speed"))
            hit = ad * resistance_multiplier(effective_resistance(fix(i["dummy_armor"]), ZERO, ZERO))
            hp, start = fix(i["dummy_hp"]), 0
            for imp in sc["impacts"]:
                removed = hit if hit < hp else hp
                hp = hp - removed
                error = abs((start + lead) / MICROS - imp["time"])
                self.note("loop_time_seconds", error)
                self.assertLessEqual(error, self.tol["loop_time_seconds"], sc["name"])
                self.assertLessEqual(abs(removed.to_float() - imp["damage"]), self.tol["damage"], sc["name"])
                start += period
            self.assertEqual(hp.raw, 0, sc["name"])

    def test_arithmetic_is_exact_and_symmetric(self):
        a, b = Fix.parse("-3.75"), Fix.parse("1.5")
        self.assertEqual((a * b).raw, Fix.parse("-5.625").raw)
        self.assertEqual((a / b).raw, Fix.parse("-2.5").raw)
        self.assertEqual((-a / b).raw, -(a / b).raw)  # rounding is sign-symmetric
        with self.assertRaises(OverflowError):
            Fix.of_int(1 << 31) * Fix.of_int(1 << 31)

    @classmethod
    def tearDownClass(cls):
        print("\nmax |fixed - reference| by kind:", {k: f"{v:.3g}" for k, v in cls.max_error.items()})


if __name__ == "__main__":
    unittest.main()
