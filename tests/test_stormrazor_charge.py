import unittest
from test_combat_engine import engine_namespace
class StormrazorCharge(unittest.TestCase):
 def kernel(self,items=None,energized=False):
  ns=engine_namespace();k=ns['_combat_hits']('Ezreal',15,10000,100,100,items or ['Stormrazor'],ns['F'],energized=energized);next(k);return k
 def hit(self,k,path=0,skill=False):
  return k.send({'hp':10000,'time':0,'event_driven':True,'movement_distance':path,'skill_on_hit':skill,'attack_physical':0})
 def test_walk_and_q_no_charge(self):
  k=self.kernel();h=self.hit(k,700,True);self.assertAlmostEqual(h['stormrazor_charge'],26)
  h=self.hit(k,700,True);self.assertAlmostEqual(h['stormrazor_charge'],26)
  h=self.hit(k,700);self.assertAlmostEqual(h['stormrazor_charge'],35)
 def test_arcane_shift_calibration(self):
  h=self.hit(self.kernel(),700*16/26,True);self.assertAlmostEqual(h['stormrazor_charge'],16)
 def test_aa_threshold_and_reset(self):
  k=self.kernel();hits=[self.hit(k) for _ in range(13)]
  self.assertEqual([i for i,h in enumerate(hits,1) if 'Storm Energized' in h['notes']],[12])
  self.assertEqual(hits[-1]['stormrazor_charge'],9)
 def test_phantom_does_not_grant_nine(self):
  k=self.kernel(['Stormrazor',"Guinsoo's Rageblade"])
  h=[self.hit(k) for _ in range(6)][-1]
  self.assertIn('Phantom Hit',h['notes']);self.assertEqual(h['stormrazor_charge'],54)
 def test_ready_q_consumes_without_grant(self):
  h=self.hit(self.kernel(energized=True),0,True)
  self.assertIn('Storm Energized',h['notes']);self.assertEqual(h['stormrazor_charge'],0)
 def test_movement_saturates_without_banking_extra(self):
  k=self.kernel();h=self.hit(k,7000,True)
  self.assertIn('Storm Energized',h['notes']);self.assertEqual(h['stormrazor_charge'],0)
  self.assertEqual(self.hit(k,7000,True)['stormrazor_charge'],0)
 def test_rfc_shiv_keep_existing_cadence(self):
  k=self.kernel(['Rapid Firecannon','Statikk Shiv'])
  hits=[self.hit(k,7000) for _ in range(7)]
  self.assertIn('Shiv Energized',hits[4]['notes']);self.assertIn('RFC Energized',hits[6]['notes'])
 def test_kiting_path_reaches_kernel_without_radial_change(self):
  from fight_engine import replay_samira
  for champion in ('Smolder','Ashe'):
   seen=[];k=self.kernel()
   def hit(state):
    seen.append(dict(state));return k.send(state)
   replay_samira([],champion=champion,level=15,ad=100,base_ad=100,attack_speed=1,crit_chance=0,crit_damage=2,hp=100000,armor=100,mr=100,q_rank=0,w_rank=0,e_rank=0,r_rank=0,automatic_until=4,movement_speed=350,attack_range=600 if champion=='Ashe' else 550,distance=600 if champion=='Ashe' else 550,timed_combat=True,aa_hit=hit)
   self.assertGreater(seen[-1]['movement_distance'],700)
   self.assertAlmostEqual(seen[0]['distance'],seen[-1]['distance'])
 def test_ezreal_shift_adds_sixteen_without_q_charge(self):
  from fight_engine import replay_samira,FightEvent
  seen=[];k=self.kernel()
  def hit(state):
   h=k.send(state);seen.append(h);return h
  replay_samira([FightEvent(0,'E'),FightEvent(1,'Q')],champion='Ezreal',level=15,ad=100,base_ad=100,attack_speed=1,crit_chance=0,crit_damage=2,hp=100000,armor=100,mr=100,q_rank=1,w_rank=0,e_rank=1,r_rank=0,automatic_until=2,movement_speed=0,attack_range=550,distance=400,timed_combat=True,aa_hit=hit)
  self.assertTrue(seen);self.assertAlmostEqual(seen[0]['stormrazor_charge'],16)
