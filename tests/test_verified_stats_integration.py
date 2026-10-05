"""Database-to-fight regressions: resource, reach and real event timing."""
import math
import unittest
from sharpwr.champion_database import level_stats, CHAMPION_DATABASE
from sharpwr.build_fight_optimizer import BuildFightEvaluator
from sharpwr import engine_namespace

class VerifiedStatsIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.ns=engine_namespace()

    def test_yunara_observations_and_interpolation(self):
        observed=dict(enumerate([345,370,396,423,451,481,512,544,578,613,649,687,726,766,807],1))
        for level,mana in observed.items():
            self.assertEqual(level_stats('Yunara',level)['mana'],mana)
        self.assertEqual(level_stats('Yunara',14)['mana'],766)
        self.assertEqual(level_stats('Yunara',15)['mana_regen_per_5s'],19)
        self.assertEqual(set(CHAMPION_DATABASE['Yunara']['observed_level_stats']),set(map(str,range(1,16))))
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

    def test_yunara_regenerates_mana_between_actions(self):
        from sharpwr.fight_engine import FightEvent,replay_samira
        core=level_stats('Yunara',15)
        r=replay_samira([FightEvent(0,'W'),FightEvent(5,'AA')],champion='Yunara',level=15,ad=100,base_ad=100,ap=0,attack_speed=1,crit_chance=0,crit_damage=2,hp=10000,armor=100,mr=100,q_rank=0,w_rank=1,e_rank=1,r_rank=0,max_mana=core['mana'],mana_regen_per_5s=core['mana_regen_per_5s'],timed_combat=False,movement_speed=0,distance=500,attack_range=575,automatic_until=6)
        w=next(x for x in r.timeline if x['kind']=='cast' and x['action']=='W')
        self.assertEqual(w['mana_after'],747)
        attack=next(x for x in r.timeline if x['kind']=='attack')
        self.assertEqual(attack['time'],5)
        self.assertAlmostEqual(attack['mana_before'],766)
        self.assertAlmostEqual(r.log[-1]['mana'],747+r.log[-1]['time']*3.8)
