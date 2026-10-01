"""Replay actual item kernels through every new champion adapter."""
import math,unittest
from test_combat_engine import engine_namespace
from test_all_marksman_fights import PENDING
from champion_database import level_stats
from fight_engine import replay_samira,champion_ranks,FightEvent

class MarksmanItems(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.ns=engine_namespace()
    def run_fight(self,name,build,events=None):
        ns=self.ns;s=ns['stats'](name,15);core=level_stats(name,15)
        total={k:sum(ns['dct'](ns['F'][item])[k] for item in build) for k in ns['K']}
        mana=(core.get('mana') or 1000)+total['mana'];last={}
        kernel=ns['_combat_hits'](name,15,10000,100,100,build,ns['F'],base_mana=mana-total['mana'],dist=550)
        next(kernel)
        def hit(state):
            out=kernel.send(state);last.update(out);return out
        def stats(state):
            dynamic=(.08*state['items'].get('rage',0) if "Guinsoo's Rageblade" in build else 0)+(.06*state['items'].get('phantom_dancer',0) if 'Phantom Dancer' in build else 0)
            bonus=s['bba']+s['lvbas']+total['as']+dynamic+state['bonus_as']
            return {'bonus_as_total':bonus,'as':s['baseas']+s['ratio']*bonus}
        return replay_samira(events or [],champion=name,level=15,ad=s['ad']+total['ad'],base_ad=s['ad'],ap=total['ap'],attack_speed=s['baseas'],as_ratio=s['ratio'],natural_attack_speed=s['baseas']+s['ratio']*(s['bba']+s['lvbas']),crit_chance=min(1,total['crit']),crit_damage=2.3 if 'Infinity Edge' in build else 2,hp=10000,armor=100,mr=100,**{k.lower()+'_rank':v for k,v in champion_ranks(name,15).items()},ability_haste=total['ah'],pct_pen=total['pctpen'],flat_pen=total['flatpen'],pct_mpen=total['pctmpen'],flat_mpen=total['flatmpen'],movement_speed=core.get('movement_speed') or 350,attack_range=core.get('attack_range') or 550,distance=550,max_mana=mana,mana_regen_per_5s=core.get('mana_regen_per_5s') or 0,automatic_until=20,aa_hit=hit,aa_stats=stats,muramana='Muramana' in build,navori='Navori Quickblades' in build,terminus='Terminus' in build,yuntal='Yun Tal Wildarrows' in build,completed_items=len(build))
    def test_three_build_families_on_every_new_adapter(self):
        for name in PENDING:
            for build in (['Infinity Edge','Phantom Dancer'],['Muramana',"Nashor's Tooth"],["Guinsoo's Rageblade",'Terminus']):
                with self.subTest(champion=name,build=build):
                    r=self.run_fight(name,build)
                    self.assertGreater(r.aa_count,0)
                    self.assertAlmostEqual(r.total_damage,10000-r.hp_remaining)
                    self.assertAlmostEqual(sum(x['damage'] for x in r.log),r.total_damage)
                    self.assertTrue(all(math.isfinite(x['damage']) and x['damage']>=0 and x['mana']>=0 for x in r.log))
    def test_skill_on_hit_items_increase_eligible_skill_damage(self):
        for name in ('Ezreal','Senna','Miss Fortune'):
            with self.subTest(champion=name):
                event=[FightEvent(0,'Q')]
                plain=self.run_fight(name,[],event)
                item=self.run_fight(name,["Nashor's Tooth"],event)
                self.assertGreater(item.total_damage,plain.total_damage)

if __name__=='__main__':unittest.main()
