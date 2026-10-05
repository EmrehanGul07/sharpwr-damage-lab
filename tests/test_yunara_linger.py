import unittest
from sharpwr.fight_engine import FightEvent,replay_samira

class YunaraLinger(unittest.TestCase):
 def fight(self,events,**kw):
  args=dict(champion='Yunara',level=15,ad=150,base_ad=100,ap=100,attack_speed=1,crit_chance=0,crit_damage=2,hp=10000,armor=0,mr=0,q_rank=1,w_rank=1,e_rank=1,r_rank=1,timed_combat=True,movement_speed=0,distance=500,attack_range=575,max_mana=2000,automatic_until=3)
  args.update(kw);return replay_samira(events,**args)
 def test_normal_w_has_four_additional_ticks_on_same_cast(self):
  r=self.fight([FightEvent(0,'W')]);hits=[h for h in r.log if h['action'].startswith('W')]
  self.assertEqual(len(hits),5)
  self.assertAlmostEqual(hits[0]['magic'],60+.85*50+.5*100)
  for j,h in enumerate(hits[1:],1):
   self.assertAlmostEqual(h['time']-hits[0]['time'],j*.25)
   self.assertAlmostEqual(h['magic'],8+.12*50+.075*100)
  self.assertEqual(r.skill_count,1)
  self.assertEqual(len([e for e in r.timeline if e['kind']=='cast']),1)
  self.assertEqual(r.timeline[0]['mana_before']-r.timeline[0]['mana_after'],60)
 def test_empowered_w_is_single_hit(self):
  r=self.fight([FightEvent(0,'R'),FightEvent(.1,'W')]);hits=[h for h in r.log if h['action'].startswith('W')]
  self.assertEqual(len(hits),1);self.assertAlmostEqual(hits[0]['magic'],160+1.2*50+.75*100)
 def test_normal_w_does_not_transform_during_flight_or_ticks(self):
  r=self.fight([FightEvent(0,'W'),FightEvent(.45,'R')]);hits=[h for h in r.log if h['action'].startswith('W')]
  self.assertEqual(len(hits),5);self.assertAlmostEqual(hits[-1]['magic'],21.5)
 def test_muramana_shock_only_once_for_whole_w(self):
  plain=self.fight([FightEvent(0,'W')]);shock=self.fight([FightEvent(0,'W')],muramana=True)
  self.assertAlmostEqual(shock.total_damage-plain.total_damage,.03*2000)
 def test_target_death_stops_remaining_ticks(self):
  r=self.fight([FightEvent(0,'W')],hp=160)
  self.assertEqual(r.hp_remaining,0);self.assertEqual(len(r.log),2)
