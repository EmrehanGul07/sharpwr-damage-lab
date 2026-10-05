import math
import unittest
from sharpwr import engine_namespace

class UserItemCadence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ns=engine_namespace()
 def hits(self,item,physical,count):
  k=self.ns['combat_hits']('Smolder',15,10000,100,100,(item if isinstance(item,list) else [item]),self.ns['F']);next(k);hp=10000;out=[]
  for i in range(count):
   hit=k.send({'hp':hp,'time':i,'event_driven':True,'on_hit_health_multiplier':1.065,'attack_physical':physical,'critical_attack_physical':physical*2})
   hit['rune_damage']=hit['damage']*1.065;hp-=hit['rune_damage'];out.append(hit)
  return out
 def test_rageblade_phantom_on_six_and_nine_from_zero(self):
  hits=self.hits("Guinsoo's Rageblade",138,10)
  self.assertEqual([i for i,h in enumerate(hits,1) if 'Phantom Hit' in h['notes']],[6,9])
  self.assertEqual([math.ceil(h['magic']*.5*1.065) for h in hits],[16,16,16,16,16,32,16,16,32,16])
  self.assertEqual([h['rage'] for h in hits],[1,2,3,4,4,4,4,4,4,4])
 def test_kraken_three_six_nine_and_damage_matches_user(self):
  hits=self.hits('Kraken Slayer',148,9)
  self.assertEqual([i for i,h in enumerate(hits,1) if 'Kraken' in h['notes']],[3,6,9])
  self.assertEqual([math.ceil(h['rune_damage']) for h in hits],[79,79,170,79,79,172,79,79,174])

 def test_terminus_order(self):
  hits=self.hits('Terminus',138,10)
  self.assertEqual([math.ceil(h['physical_damage']*1.065) for h in hits],[74,78,78,82,82,87,87,87,87,87])
  self.assertEqual([math.ceil(h['magic_damage']*1.065) for h in hits],[16,16,17,17,18,18,19,19,19,19])
 def test_phantom_advances_kraken(self):
  hits=self.hits(["Guinsoo's Rageblade",'Kraken Slayer'],183,12)
  self.assertEqual([i for i,h in enumerate(hits,1) if any('Kraken' in x for x in h['notes'])],[3,6,8,10,12])
  self.assertIn('Kraken (Phantom)',hits[11]['notes'])
 def test_phantom_advances_terminus_between_magic_hits(self):
  hits=self.hits(["Guinsoo's Rageblade",'Terminus'],173,12)
  self.assertEqual([math.ceil(h['physical_damage']*1.065) for h in hits],[93,97,97,103,103,109,109,109,109,109,109,109])
  self.assertEqual([math.ceil(h['magic_damage']*1.065) for h in hits],[32,32,34,34,36,74,38,38,76,38,38,76])
  self.assertEqual(hits[5]['dark'],3)
  self.assertEqual([math.ceil(e['magic_damage']*1.065) for e in hits[5]['on_hit_events']],[36,38])
 def test_triple_item_proc_order(self):
  hits=self.hits(["Guinsoo's Rageblade",'Terminus','Kraken Slayer'],218,12)
  self.assertEqual([i for i,h in enumerate(hits,1) if any('Kraken' in x for x in h['notes'])],[3,6,8,10,12])
  self.assertEqual(hits[5]['dark'],3)
  self.assertEqual([math.ceil(e['magic_damage']*1.065) for e in hits[5]['on_hit_events']],[36,38])
  self.assertEqual([math.ceil(h['magic_damage']*1.065) for h in hits],[32,32,34,34,36,74,38,38,76,38,38,76])

 def test_botrk_ranged_six_percent_and_phantom_remaining_hp(self):
  hits=self.hits(["Guinsoo's Rageblade",'Blade of the Ruined King'],178,6)
  for hit,observed in zip(hits[:5],[414,401,387,374,362]):
   self.assertAlmostEqual(hit['physical_damage']*1.065,observed,delta=1.)
  h=hits[5];events=h['on_hit_events']
  primary=(178+events[0]['physical_proc_raw'])*.5*1.065
  phantom=events[1]['physical_proc_raw']*.5*1.065
  self.assertAlmostEqual(primary,350,delta=1.)
  self.assertAlmostEqual(phantom,243,delta=1.)
  self.assertLess(events[1]['physical_proc_raw'],events[0]['physical_proc_raw'])
 def test_samira_close_range_retains_ranged_item_class(self):
  k=self.ns['combat_hits']('Samira',15,10000,100,100,['Blade of the Ruined King'],self.ns['F']);next(k)
  h=k.send({'hp':10000,'time':0,'melee':True,'attack_physical':0})
  self.assertEqual(h['physical'],600.)

 def test_ezreal_q_advances_kraken_in_both_mixed_orders(self):
  for actions in [('AA','AA','Q'),('Q','AA','AA')]:
   kernel=self.ns['combat_hits']('Ezreal',15,10000,100,100,['Kraken Slayer'],self.ns['F']);next(kernel)
   out=[]
   for i,action in enumerate(actions):
    out.append(kernel.send({'hp':10000,'time':i,'event_driven':True,'skill_on_hit':action=='Q','attack_physical':0}))
   self.assertEqual([i for i,h in enumerate(out,1) if 'Kraken' in h['notes']],[3])
 def test_ezreal_six_qs_trigger_phantom(self):
  kernel=self.ns['combat_hits']('Ezreal',15,10000,100,100,["Guinsoo's Rageblade"],self.ns['F']);next(kernel)
  out=[kernel.send({'hp':10000,'time':i,'event_driven':True,'skill_on_hit':True,'attack_physical':0}) for i in range(6)]
  self.assertEqual([i for i,h in enumerate(out,1) if 'Phantom Hit' in h['notes']],[6])
  self.assertEqual([h['magic'] for h in out],[30,30,30,30,30,60])
 def test_ezreal_q_terminus_stack_progression(self):
  kernel=self.ns['combat_hits']('Ezreal',15,10000,100,100,['Terminus'],self.ns['F']);next(kernel)
  out=[kernel.send({'hp':10000,'time':i,'event_driven':True,'skill_on_hit':True,'attack_physical':0}) for i in range(8)]
  self.assertEqual([(h['light'],h['dark']) for h in out],[(1,0),(1,1),(2,1),(2,2),(3,2),(3,3),(3,3),(3,3)])

 def test_muramana_does_not_repeat_shock_on_phantom(self):
  kernel=self.ns['combat_hits']('Ezreal',15,10000,100,100,['Muramana',"Guinsoo's Rageblade"],self.ns['F']);next(kernel)
  out=[kernel.send({'hp':10000,'time':i,'event_driven':True,'max_mana':1000,'attack_physical':0}) for i in range(6)]
  self.assertEqual([h['physical'] for h in out],[15.]*6)
  self.assertEqual(out[5]['on_hit_events'][1]['physical_proc_raw'],0.)
 def test_skill_phantom_botrk_includes_primary_skill_damage(self):
  def run(extra):
   kernel=self.ns['combat_hits']('Ezreal',15,10000,100,100,['Blade of the Ruined King',"Guinsoo's Rageblade"],self.ns['F']);next(kernel)
   for i in range(6):h=kernel.send({'hp':10000,'time':i,'event_driven':True,'skill_on_hit':True,'attack_physical':0,'primary_external_damage':extra})
   return h['on_hit_events'][1]['physical_proc_raw']
  self.assertAlmostEqual(run(0)-run(200),12.)
