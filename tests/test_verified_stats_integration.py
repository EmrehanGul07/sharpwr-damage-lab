"""Database-to-fight regressions: resource, reach and real event timing."""
import math
import unittest
from champion_database import level_stats, CHAMPION_DATABASE
from build_fight_optimizer import BuildFightEvaluator
from test_combat_engine import engine_namespace

class VerifiedStatsIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.ns=engine_namespace()

    def test_yunara_observations_and_interpolation(self):
        observed={1:345,3:396,5:451,8:544,10:613,13:726,15:807}
        for level,mana in observed.items():
            self.assertEqual(level_stats('Yunara',level)['mana'],mana)
        self.assertEqual(level_stats('Yunara',14)['mana'],766.5)
        self.assertIsNone(level_stats('Yunara',15)['mana_regen_per_5s'])
        self.assertIsNone(CHAMPION_DATABASE['Yunara']['stats']['mana_growth'])

    def test_yunara_muramana_reaches_fight_and_item_kernel(self):
        ev=BuildFightEvaluator(self.ns,'Yunara',15,10000,100,100,retain_traces=True)
        row=ev.evaluate(['Muramana']);trace=next(iter(ev.traces.values()))
        item=self.ns['dct'](self.ns['F']['Muramana'])
        maximum=807+item['mana']
        self.assertEqual(trace.timeline[0]['mana_before'],maximum)
        self.assertAlmostEqual(row['AD'],self.ns['stats']('Yunara',15,0)['ad']+item['ad']+.02*maximum)
        attacks=[x for x in trace.timeline if x['kind']=='attack']
        self.assertEqual(attacks[0]['attack_range'],575)
        self.assertEqual(attacks[0]['distance'],575)
        self.assertAlmostEqual(attacks[0]['impact_time']-attacks[0]['windup_end'],575/2500)
        self.assertTrue(any(x['mana_after']<x['mana_before'] for x in trace.timeline if x['kind']=='cast'))
        self.assertFalse(any('Maximum mana unknown' in a for a in trace.assumptions))

    def test_all_champions_receive_core_stats_and_resource_bounds(self):
        for name in CHAMPION_DATABASE:
            for level in (1,15):
                with self.subTest(champion=name,level=level):
                    ev=BuildFightEvaluator(self.ns,name,level,10000,100,100,retain_traces=True)
                    row=ev.evaluate([]);trace=next(iter(ev.traces.values()));core=level_stats(name,level)
                    self.assertGreater(core['mana'],0)
                    self.assertGreater(core['movement_speed'],0)
                    self.assertGreater(core['attack_range'],0)
                    self.assertGreater(trace.aa_count,0)
                    for hit in trace.log:
                        self.assertTrue(math.isfinite(hit['damage']))
                        self.assertLessEqual(hit['hp_after'],hit['hp_before'])
                        self.assertGreaterEqual(hit['mana'],0)
                        self.assertLessEqual(hit['mana'],core['mana']+1e-8)
                    for event in trace.timeline:
                        if event['kind']=='attack':
                            self.assertGreaterEqual(event['windup_end'],event['time'])
                            self.assertGreaterEqual(event['impact_time'],event['windup_end'])
                            self.assertLessEqual(event['distance'],event['attack_range']+1e-6)
                    self.assertAlmostEqual(sum(x['damage'] for x in trace.log),row['Damage'])
