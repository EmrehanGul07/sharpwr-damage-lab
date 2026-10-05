"""Integration regressions against the actual shared item kernel and fight replay."""
import math
import unittest
from sharpwr import engine_namespace
from fight_engine import replay_samira,samira_ranks
from champion_database import level_stats

class SamiraBuildMatrix(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.ns=engine_namespace()

    def simulate(self,items,level=15,boot=None,keystone=None,distance=550):
        ns=self.ns;core=level_stats('Samira',level);s=ns['stats']('Samira',level)
        qs=[ns['dct'](ns['F'][name]) for name in items]+[ns['dct'](ns['B'][boot]) if boot else ns['dct'](())]
        total={k:sum(q[k] for q in qs) for k in ns['K']}
        mana=core['mana']+total['mana'];awe=.02*mana if any(x in items for x in ('Muramana','Manamune')) else 0
        kernel=ns['combat_hits']('Samira',level,10000,249,182,items,ns['F'],base_mana=core['mana'],boot=boot,dist=distance)
        next(kernel);last={}
        def stats(state):
            dyn=(.08*state['items'].get('rage',0) if "Guinsoo's Rageblade" in items else 0)+(.06*state['items'].get('phantom_dancer',0) if 'Phantom Dancer' in items else 0)
            if state['time']<last.get('yuntal_until',-1):dyn+=.35
            bonus=s['bba']+s['lvbas']+total['as']+dyn+state['bonus_as']
            return {'bonus_as_total':bonus,'as':min(3,s['baseas']+s['ratio']*bonus),'buff_expiry':last.get('yuntal_until',-1)}
        def hit(state):
            result=kernel.send(state);last.update(result);return result
        r=replay_samira([],level=level,ad=s['ad']+total['ad']+awe,base_ad=s['ad'],attack_speed=s['baseas'],crit_chance=min(1,total['crit']),crit_damage=2.3 if 'Infinity Edge' in items else 2,hp=10000,armor=249,mr=182,**{k.lower()+'_rank':v for k,v in samira_ranks(level).items()},ability_haste=total['ah'],pct_pen=total['pctpen'],flat_pen=total['flatpen'],pct_mpen=total['pctmpen'],flat_mpen=total['flatmpen'],timed_combat=True,movement_speed=core['movement_speed']*(1+total['ms']),distance=distance,attack_range=core['attack_range'],base_windup=.149999994/.658,aa_hit=hit,aa_stats=stats,max_mana=mana,mana_regen_per_5s=core['mana_regen_per_5s'],automatic_until=30,keystone=keystone,muramana='Muramana' in items,mana_refund=.15 if any(x in items for x in ('Muramana','Manamune')) else 0,navori='Navori Quickblades' in items,terminus='Terminus' in items,yuntal='Yun Tal Wildarrows' in items,collector_threshold=.05 if 'The Collector' in items else 0)
        return r,mana

    def assert_ledger(self,result,mana):
        self.assertFalse(result.rejected)
        previous=10000
        for hit in result.log:
            self.assertTrue(all(math.isfinite(hit[k]) for k in ('time','damage','hp_before','hp_after','mana','distance')))
            self.assertAlmostEqual(hit['hp_before'],previous)
            self.assertAlmostEqual(hit['hp_before']-hit['hp_after'],hit['damage'])
            self.assertTrue(0<=hit['mana']<=mana+1e-8)
            previous=hit['hp_after']
        self.assertAlmostEqual(sum(x['damage'] for x in result.log),result.total_damage)
        self.assertAlmostEqual(10000-result.hp_remaining,result.total_damage)

    def test_each_item_and_boot_against_tank(self):
        for name in self.ns['F']:
            with self.subTest(item=name):self.assert_ledger(*self.simulate([name]))
        for boot in self.ns['B']:
            with self.subTest(boot=boot):self.assert_ledger(*self.simulate([],boot=boot))

    def test_levels_runes_and_builds(self):
        builds=[[],['Infinity Edge','The Collector','Navori Quickblades','Bloodthirster','Mortal Reminder'],['Muramana',"Guinsoo's Rageblade",'Phantom Dancer','Terminus',"Nashor's Tooth"]]
        for level in (1,5,9,15):
            for rune in (None,'Conqueror','Lethal Tempo'):
                for build in builds:
                    with self.subTest(level=level,rune=rune,build=build):self.assert_ledger(*self.simulate(build,level=level,keystone=rune))

    def test_expected_replay_is_deterministic(self):
        items=['Infinity Edge','Navori Quickblades','The Collector']
        a,_=self.simulate(items);b,_=self.simulate(items)
        self.assertEqual(a.log,b.log)
