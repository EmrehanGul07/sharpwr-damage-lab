import unittest
from sharpwr.combat_timing import database,attack_windup,attack_travel,skill_travel,skill_cast_time
class TimingTests(unittest.TestCase):
 def test_all_23_have_sourced_base_windup(self):
  self.assertEqual(len(database()),23)
  for n,c in database().items():
   with self.subTest(champion=n):
    self.assertGreater(c['aa']['base_windup_seconds'],0)
    self.assertAlmostEqual(attack_windup(n,1),(.5/1.6 if n=='Senna' else c['aa']['base_windup_seconds']/1.5))
    self.assertEqual(set(c['abilities']),set('PQWER'))
 def test_non_projectile_and_samira_melee(self):
  self.assertEqual(attack_travel('Zeri',500),0)
  self.assertEqual(attack_travel('Senna',500),0)
  self.assertEqual(attack_travel('Samira',100,melee=True),0)
  self.assertAlmostEqual(attack_travel('Samira',500),500/2800)
 def test_twitch_ultimate_speed(self):
  self.assertAlmostEqual(attack_travel('Twitch',500,ultimate=True),.1)
  self.assertAlmostEqual(attack_travel('Twitch',500),.2)
 def test_dash_is_not_missile(self):
  self.assertEqual(skill_travel('Vayne','Q',500),0)
  self.assertEqual(skill_travel("Kai'Sa",'R',500),0)
  self.assertEqual(skill_travel('Lucian','Q',500),0)
  self.assertAlmostEqual(skill_travel('Caitlyn','E',500),500/1600)
 def test_dynamic_casts_use_wr_bonus_as(self):
  self.assertAlmostEqual(skill_cast_time('Sivir','Q',1),.125)
  self.assertEqual(skill_cast_time("Kai'Sa",'E',3),.6)
  self.assertAlmostEqual(skill_cast_time('Smolder','Q',1),attack_windup('Smolder',1))
 def test_game_file_supplements(self):
  self.assertAlmostEqual(attack_travel('Jinx',550,weapon='minigun'),550/2750)
  self.assertAlmostEqual(attack_travel('Jinx',550,weapon='rockets'),550/2000)
  self.assertEqual(skill_travel('Varus','E',100),.5)
  self.assertEqual(skill_travel('Varus','E',1000),.5)
  self.assertAlmostEqual(skill_travel("Kai'Sa",'Q',500),.4)
 def test_jinx_rocket_speed_stages(self):
  self.assertAlmostEqual(skill_travel('Jinx','R',2450),1350/1700+.5)
if __name__=='__main__':unittest.main()
