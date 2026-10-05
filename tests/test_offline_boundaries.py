import unittest,math
from sharpwr.fight_engine import FightEvent,replay_samira
from sharpwr.marksman_kits import Kit,PRIORITIES
from sharpwr.damage_classification import registry
class OfflineBoundaries(unittest.TestCase):
 def args(self,c):return dict(champion=c,level=15,ad=100,base_ad=60,attack_speed=1,crit_chance=.5,crit_damage=2,hp=10000,armor=100,mr=100,q_rank=1,w_rank=0,e_rank=0,r_rank=0,max_mana=1000,timed_combat=True,distance=200,attack_range=550,movement_speed=0,automatic_until=3)
 def test_nonfinite_spatial_and_fractional_ranks_rejected(self):
  for c in ('Samira','Smolder','Ezreal'):
   for key,val in [('distance',math.nan),('movement_speed',math.inf),('mana_regen_per_5s',math.nan),('q_rank',1.5),('windup_scale',0)]:
    with self.subTest(c=c,key=key),self.assertRaises(ValueError):replay_samira([],**(self.args(c)|{key:val}))
 def test_insufficient_mana_never_casts_and_aa_remains_available(self):
  for c in ('Samira','Smolder','Ezreal'):
   r=replay_samira([],**(self.args(c)|{'max_mana':0}))
   self.assertFalse(any(x['kind']=='cast' for x in r.timeline));self.assertGreater(r.aa_count,0)
 def test_death_stops_pending_projectiles_and_health_ledger(self):
  for c in ('Samira','Smolder','Ezreal','Jhin'):
   r=replay_samira([],**(self.args(c)|{'hp':1,'q_rank':0}))
   self.assertEqual(r.hp_remaining,0);self.assertAlmostEqual(r.total_damage,1)
   self.assertTrue(all(x['time']<=r.killed_at for x in r.log))
 def test_skill_ranges_use_wr_reach_not_aa_range(self):
  for c,s,value in [('Lucian','W',800),('Caitlyn','Q',1150),('Jinx','W',1500),("Kog'Maw",'E',1360),('Xayah','Q',1000)]:
   k=Kit(c,dict(Q=1,W=1,E=1,R=1),15,550);self.assertEqual(k.range(s,0),value)
  k=Kit('Zeri',dict(Q=1,W=1,E=1,R=1),15,550);self.assertNotEqual(k.range('E',0),300)
 def test_every_hit_is_explicit_sensitivity_only_and_shock_is_item_tagged(self):
  for c in ('Samira','Lucian'):
   a=self.args(c)|dict(q_rank=0,r_rank=1,muramana=True)
   if c=='Samira':
    events=[FightEvent(i*.3,x) for i,x in enumerate(('AA','Q','AA','W','AA','E'))]+[FightEvent(2,'R')];a['q_rank']=1;a['w_rank']=1;a['e_rank']=1;a['timed_combat']=False;a['automatic_until']=5
   else:events=[FightEvent(0,'R')]
   first=replay_samira(events,**a);every=replay_samira(events,**a,muramana_repeat_policy='every_hit')
   self.assertGreater(every.total_damage,first.total_damage)
   parts=[p for x in first.log for p in x['damage_components'] if p.get('component')=='Muramana skill Shock']
   self.assertTrue(parts);self.assertTrue(all(p['tags']==['Item'] for p in parts))
 def test_registry_covers_all_kit_slots_items_and_properties(self):
  r=registry();self.assertEqual(set(r['abilities']),set(PRIORITIES))
  self.assertTrue(all(set(v)==set('PQWER') for v in r['abilities'].values()))
  self.assertTrue(all(x.get('status') for v in r['abilities'].values() for x in v.values()))
if __name__=='__main__':unittest.main()
