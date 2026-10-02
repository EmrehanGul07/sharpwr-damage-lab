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
  k=self.kernel();hits=[self.hit(k) for _ in range(14)]
  self.assertEqual([i for i,h in enumerate(hits,1) if 'Storm Energized' in h['notes']],[13])
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
 def test_rfc_shiv_share_new_charge(self):
  k=self.kernel(['Rapid Firecannon','Statikk Shiv'])
  hits=[self.hit(k,0) for _ in range(9)]
  self.assertFalse(any('Shiv Energized' in h['notes'] for h in hits[:8]))
  self.assertIn('Shiv Energized',hits[8]['notes']);self.assertIn('RFC Energized',hits[8]['notes'])
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

 def test_consumption_at_launch_damage_at_hit_no_recharge(self):
  k=self.kernel(energized=True)
  launch=k.send({'event_phase':'attack_launch','attack_id':1,'movement_distance':0})
  self.assertEqual(launch['energized_charge'],0);self.assertTrue(launch['energized_reserved'])
  self.assertNotIn('damage',launch)
  hit=k.send({'hp':10000,'time':1,'event_driven':True,'attack_id':1,'movement_distance':0,'attack_physical':0})
  self.assertIn('Storm Energized',hit['notes']);self.assertEqual(hit['energized_charge'],0)
  after=k.send({'hp':10000,'time':2,'event_driven':True,'attack_id':2,'movement_distance':0,'attack_physical':0})
  self.assertEqual(after['energized_charge'],9)
 def test_charge_filled_during_flight_waits_for_next_launch(self):
  k=self.kernel();k.send({'event_phase':'attack_launch','attack_id':1,'movement_distance':0})
  h=k.send({'hp':10000,'time':1,'event_driven':True,'attack_id':1,'movement_distance':3000,'attack_physical':0})
  self.assertEqual(h['energized_charge'],100);self.assertNotIn('Storm Energized',h['notes'])
 def test_ezreal_q_pd_yes_yuntal_no(self):
  k=self.kernel(['Phantom Dancer','Yun Tal Wildarrows'])
  h=self.hit(k,skill=True)
  self.assertEqual(h['phantom_dancer'],1);self.assertEqual(h['yuntal_crit'],0)
  self.assertEqual(h['yuntal_until'],-1);self.assertNotIn('Flurry',h['notes'])
 def test_shared_items_one_charge_pool(self):
  h=self.hit(self.kernel(['Stormrazor','Rapid Firecannon','Statikk Shiv'],True))
  self.assertEqual(h['magic'],260);self.assertEqual(h['energized_charge'],0)
 def test_replay_launch_precedes_impact_both_adapters(self):
  from fight_engine import replay_samira
  for champion in ('Smolder','Ezreal'):
   seen=[];k=self.kernel(energized=True)
   def hit(state):
    value=k.send(state);seen.append((dict(state),dict(value)));return value
   r=replay_samira([],champion=champion,level=15,ad=100,base_ad=100,attack_speed=1,crit_chance=0,crit_damage=2,hp=100000,armor=100,mr=100,q_rank=0,w_rank=0,e_rank=0,r_rank=0,automatic_until=2,movement_speed=0,attack_range=550,distance=550,timed_combat=True,energized_items=True,aa_hit=hit)
   launch=next((s,h) for s,h in seen if s.get('event_phase')=='attack_launch')
   impact=next((s,h) for s,h in seen if s.get('event_phase') is None)
   self.assertLess(launch[0]['time'],impact[0]['time'])
   self.assertEqual(launch[1]['energized_charge'],0)
   self.assertIn('Storm Energized',impact[1]['notes'])
   self.assertEqual(impact[1]['energized_charge'],0)
   from combat_replay import replay_payload
   payload=replay_payload(r,champion=champion,level=15,target='dummy',hp=100000,build={'Items':['Stormrazor'],'Boots':'None','Rotation':'QWE','Movement':'kite','Ultimate timing':'default','Attack weaving':'default','Weapon':'default','E enabled':False})
   self.assertTrue(any(e['phase']=='launch' for e in payload['events']))
   self.assertEqual(len({e['order'] for e in payload['events']}),len(payload['events']))
