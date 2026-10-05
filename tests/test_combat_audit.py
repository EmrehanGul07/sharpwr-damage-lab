import unittest
from fight_engine import replay_samira
from marksman_ability_database import mana_cost
from sharpwr import engine_namespace

class CombatAudit(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ns=engine_namespace()
 def fight(self,name,**kw):
  p=dict(champion=name,level=15,ad=100,base_ad=60,ap=0,attack_speed=1,starting_bonus_as=2,crit_chance=0,crit_damage=2,hp=1e6,armor=0,mr=0,q_rank=0,w_rank=0,e_rank=0,r_rank=0,timed_combat=True,distance=2000,attack_range=2000,movement_speed=0,automatic_until=5)
  p.update(kw);return replay_samira([],**p)
 def test_in_flight_attacks_have_unique_ids_and_conqueror_grants(self):
  r=self.fight("Kog'Maw",keystone='Conqueror')
  hits=[x for x in r.log if x['action']=='AA'];commands=[x for x in r.timeline if x['kind']=='attack']
  self.assertGreater(len([x for x in commands if x['time']<hits[0]['time']]),1)
  self.assertEqual(len(set(x['id'] for x in commands)),len(commands))
  self.assertEqual([x['after']['conqueror'] for x in hits[:6]],list(range(1,7)))
 def test_jhin_reserves_four_shots_before_impacts_then_reloads(self):
  r=self.fight('Jhin',distance=4000,attack_range=4000,natural_attack_speed=2)
  commands=[x for x in r.timeline if x['kind']=='attack']
  self.assertTrue(commands[3]['fourth']);self.assertFalse(commands[2]['fourth'])
  self.assertGreaterEqual(commands[4]['time'],commands[3]['windup_end']+2.5-1e-8)
  self.assertTrue(all(x['after']['ammo']>=0 for x in r.log))
 def test_rocket_cost_paid_before_flight_and_weapon_saved_per_attack(self):
  cost=mana_cost('Jinx','Q',1)
  r=self.fight('Jinx',q_rank=1,weapon='rockets',max_mana=cost*1.5,distance=4000,attack_range=4000)
  commands=[x for x in r.timeline if x['kind']=='attack'];hits=[x for x in r.log if x['action']=='AA']
  self.assertEqual(commands[0]['weapon'],'rockets');self.assertEqual(commands[1]['weapon'],'minigun')
  self.assertEqual(commands[0]['mana_after'],cost*.5)
  rocket=next(x for x in hits if x['attack_id']==commands[0]['id']);self.assertAlmostEqual(rocket['physical'],112)
 def test_user_confirmed_energized_hit_cadence(self):
  for item,period,label in [('Rapid Firecannon',13,'RFC Energized'),('Statikk Shiv',9,'Shiv Energized')]:
   k=self.ns['combat_hits']('Ezreal',15,1e6,0,0,[item],self.ns['F'],energized=False);next(k)
   indices=[i for i in range(1,22) if label in k.send({'time':i,'hp':1e6,'event_driven':True})['notes']]
   self.assertEqual(indices,list(range(period,22,period)))
 def test_explicit_energized_readiness_remains_authoritative(self):
  k=self.ns['combat_hits']('Ezreal',15,1e6,0,0,['Statikk Shiv'],self.ns['F']);next(k)
  self.assertIn('Shiv Energized',k.send({'time':0,'hp':1e6,'event_driven':True,'energized_ready':True})['notes'])
  for i in range(1,11):self.assertNotIn('Shiv Energized',k.send({'time':i,'hp':1e6,'event_driven':True,'energized_ready':False})['notes'])
 def test_sivir_return_uses_endpoint_and_return_speed(self):
  from fight_engine import FightEvent
  for distance in (550,1250):
   r=self.fight('Sivir',q_rank=1,distance=distance,attack_range=0,automatic_until=3)
   q=[x for x in r.log if x['action'] in ('Q','Q hit')];cast=next(x for x in r.timeline if x.get('action')=='Q')
   self.assertGreaterEqual(len(q),2)
   self.assertAlmostEqual(q[1]['time']-q[0]['time'],(1250-distance)/1450.+(1250-distance)/1200.)
 def test_muramana_first_cast_shock_gets_same_target_damage_modifier(self):
  from fight_engine import FightEvent
  p=dict(champion='Ezreal',level=15,ad=100,base_ad=60,attack_speed=1,crit_chance=0,crit_damage=2,hp=10000,armor=100,mr=100,q_rank=1,w_rank=0,e_rank=0,r_rank=0,max_mana=2000,muramana=True,automatic_until=2)
  a=replay_samira([FightEvent(0,'Q')],**p);b=replay_samira([FightEvent(0,'Q')],sub_runes=('Cut Down',),**p)
  self.assertAlmostEqual(b.total_damage/a.total_damage,1.065)
if __name__=='__main__':unittest.main()
