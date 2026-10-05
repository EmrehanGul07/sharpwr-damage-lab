"""Default rune pages, the page-to-fight loadout and the runes added for them."""

import unittest

from sharpwr.champion_database import CHAMPION_DATABASE
from sharpwr.rune_pages import DEFAULT_PAGES, default_loadout, page_problems, rune_loadout, stack_progress
from sharpwr.rune_runtime import DamageProcs, FleetFootwork, PhaseRush

# Pages the editor has not finished yet; they still load, with the missing choice left out.
INCOMPLETE = {"Caitlyn", "Corki"}


class RunePageTests(unittest.TestCase):
    def test_every_champion_has_a_legal_default_page(self):
        self.assertEqual(set(DEFAULT_PAGES), set(CHAMPION_DATABASE))
        broken = {name for name, page in DEFAULT_PAGES.items() if page_problems(page)}
        self.assertLessEqual(broken, INCOMPLETE, {n: page_problems(DEFAULT_PAGES[n]) for n in broken})

    def test_every_default_rune_has_a_fight_effect_or_none_by_design(self):
        for name in CHAMPION_DATABASE:
            for level in (1, 9, 15):
                self.assertEqual(default_loadout(name, level).unmodeled, (), name)

    def test_stacks_fill_with_level(self):
        self.assertEqual([stack_progress(l) for l in (1, 5, 6, 7, 8, 9, 15)], [0, 0, 0.25, 0.5, 0.75, 1, 1])
        page = {"keystone": "Dark Harvest", "primary_tree": "Precision", "primary": ["Brutal", "Cut Down", "Legend: Alacrity"],
                "secondary_tree": "Resolve", "secondary": "Bone Plating"}
        self.assertAlmostEqual(rune_loadout(page, 5).bonus_as, 0.03)
        self.assertAlmostEqual(rune_loadout(page, 7).bonus_as, 0.12)
        self.assertAlmostEqual(rune_loadout(page, 9).bonus_as, 0.21)
        self.assertEqual(rune_loadout(page, 11).dark_harvest_souls, 11)
        self.assertEqual(rune_loadout(page, 11).runes, ("Brutal", "Cut Down", "Legend: Alacrity"))

    def test_runes_without_a_model_are_reported(self):
        page = {"keystone": "Arcane Comet", "primary": ["Brutal", None, None], "secondary": "Scorch"}
        self.assertEqual(rune_loadout(page, 9).unmodeled, ("Arcane Comet", "Scorch"))

    def test_page_rules(self):
        page = dict(DEFAULT_PAGES["Ezreal"])
        self.assertEqual(page_problems(page), [])
        self.assertIn("The secondary rune must come from another tree", page_problems({**page, "secondary_tree": page["primary_tree"]}))
        self.assertIn("Cut Down is not in Precision row 1", page_problems({**page, "primary": ["Cut Down", "Cut Down", "Legend: Alacrity"]}))


class NewRuneTests(unittest.TestCase):
    def test_empowerment_fires_on_the_third_hit_then_amplifies(self):
        procs = DamageProcs(15, "Empowerment", ())
        self.assertEqual(procs.apply(0.0, "AA", 1.0, 0, 0, 0)[0], 0.0)
        self.assertEqual(procs.apply(0.5, "Q", 1.0, 0, 0, 0)[0], 0.0)
        self.assertEqual(procs.amplification(), 1.0)
        damage, notes, parts = procs.apply(1.0, "AA", 1.0, 0, 0, 0)
        self.assertAlmostEqual(damage, 165.0)
        self.assertEqual(procs.amplification(), 1.08)

    def test_empowerment_hits_reset_after_a_pause(self):
        procs = DamageProcs(1, "Empowerment", ())
        procs.apply(0.0, "AA", 1.0, 0, 0, 0)
        procs.apply(1.0, "AA", 1.0, 0, 0, 0)
        self.assertEqual(procs.apply(6.0, "AA", 1.0, 0, 0, 0)[0], 0.0)

    def test_sudden_impact_needs_a_dash_and_is_true_damage(self):
        procs = DamageProcs(15, "Conqueror", ("Sudden Impact",))
        self.assertEqual(procs.apply(0.0, "AA", 1.0, 0, 0, 200)[0], 0.0)
        procs.dashed(1.0)
        damage, _, parts = procs.apply(2.0, "AA", 1.0, 0, 0, 200)
        self.assertAlmostEqual(damage, 65.0)
        self.assertEqual(parts[0]["damage_type"], "true")
        procs.dashed(3.0)
        self.assertEqual(procs.apply(4.0, "AA", 1.0, 0, 0, 200)[0], 0.0)  # cooldown 15s

    def test_phase_rush(self):
        rush = PhaseRush(True, 15)
        self.assertEqual(rush.cooldown, 7)
        self.assertFalse(rush.hit(0.0) or rush.hit(1.0))
        self.assertTrue(rush.hit(2.0))
        self.assertEqual((rush.haste(4.9), rush.haste(5.1)), (10.0, 0.0))
        self.assertFalse(rush.hit(3.0) or rush.hit(3.5) or rush.hit(4.0))
        self.assertFalse(PhaseRush(False, 15).hit(0.0))

    def test_fleet_footwork_energy(self):
        fleet = FleetFootwork(True)
        for _ in range(11):
            fleet.start_attack(0.0)
            self.assertEqual(fleet.bonus_as(), 0.0)
        fleet.start_attack(700.0)
        self.assertEqual(fleet.bonus_as(), 0.40)
        fleet.start_attack(700.0)
        self.assertEqual(fleet.bonus_as(), 0.0)
        self.assertEqual(FleetFootwork(True, ready=True).energy, 100.0)


class EvaluatorRuneTests(unittest.TestCase):
    def test_runes_reach_the_build_search(self):
        from sharpwr import engine_namespace, profiles_by_target
        from sharpwr.build_fight_optimizer import BuildFightEvaluator

        ns = engine_namespace()
        t = profiles_by_target()["squishy"][9]
        items, boots = ["Yun Tal Wildarrows", "Runaan's Hurricane"], "Berserker's Greaves"
        plain = BuildFightEvaluator(ns, "Jinx", 9, t["hp"], t["armor"], t["mr"], yuntal_stacks=125)
        runed = BuildFightEvaluator(ns, "Jinx", 9, t["hp"], t["armor"], t["mr"], yuntal_stacks=125, runes=default_loadout("Jinx", 9))
        self.assertLess(runed.evaluate(items, boots)["TTK"], plain.evaluate(items, boots)["TTK"])
        self.assertGreater(runed.evaluate(items, boots)["Starting AS"], plain.evaluate(items, boots)["Starting AS"])
        with self.assertRaises(ValueError):
            BuildFightEvaluator(ns, "Jinx", 9, t["hp"], t["armor"], t["mr"], runes=rune_loadout({"keystone": "Arcane Comet"}, 9))


if __name__ == "__main__":
    unittest.main()
