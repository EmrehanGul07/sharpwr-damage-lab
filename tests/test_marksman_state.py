import unittest
from marksman_state import KitState,zeri_attack_speed_conversion

class KitStateTests(unittest.TestCase):
    def test_kalista_spears_expire_and_rend_consumes(self):
        s=KitState('Kalista')
        s.impact('AA',0);s.impact('Q',1)
        self.assertEqual(s.impact('E',2),[('rend',2)])
        s.impact('AA',3);self.assertEqual(s.impact('E',7),[('rend',0)])
    def test_twitch_stacks_cap_and_expire(self):
        s=KitState('Twitch')
        for i in range(8):s.impact('AA',i)
        self.assertEqual(s.stacks['venom'],5)
        s.advance(12);self.assertNotIn('venom',s.stacks)
    def test_vayne_every_third_eligible_hit(self):
        s=KitState('Vayne')
        self.assertEqual(s.impact('AA',0),[])
        s.impact('Q',.1)
        self.assertEqual(s.impact('AA',1),[('tumble',1)])
        self.assertEqual(s.impact('E',2),[('silver_bolts',1)])
        self.assertEqual(s.stacks['silver_bolts'],0)
    def test_tristana_q_does_not_stack_bomb(self):
        s=KitState('Tristana');s.impact('E',0);s.impact('Q',.1)
        self.assertEqual(s.stacks['bomb'],0)
        for t in (1,2,3):self.assertEqual(s.impact('AA',t),[])
        self.assertEqual(s.impact('W',3.5),[('explosive_charge',4)])
        self.assertEqual(s.ready['W'],3.5)
    def test_ezreal_flux_and_flat_cooldown_refund(self):
        s=KitState('Ezreal');s.ready={a:10 for a in 'QWER'}
        s.impact('W',0)
        self.assertNotIn('rising_spell_force',s.stacks)
        self.assertEqual(s.impact('Q',1),[('essence_flux',1)])
        self.assertEqual(s.ready['R'],8.5)
        self.assertNotIn('flux',s.stacks)
    def test_jhin_empty_magazine_is_not_infinite_attacks(self):
        s=KitState('Jhin')
        for t in range(3):s.impact('AA',t)
        self.assertEqual(s.impact('AA',3),[('fourth_shot',1),('reload_required',1)])
        with self.assertRaises(ValueError):s.impact('AA',4)
    def test_zeri_conversion_units(self):
        self.assertEqual(zeri_attack_speed_conversion(100,60),130)
        self.assertEqual(zeri_attack_speed_conversion(100,0),100)
    def test_ashe_focus_required(self):
        s=KitState('Ashe')
        with self.assertRaises(ValueError):s.impact('Q',0)
        for t in (1,2,3,4):s.impact('AA',t)
        s.impact('Q',4.1);self.assertEqual(s.buffs['focus_as'],.2)
    def test_draven_catch_is_explicit(self):
        s=KitState('Draven');s.impact('Q',0);s.ready['W']=10
        s.impact('AA',1);self.assertEqual(s.ready['W'],10)
        s.axe_catch(2);self.assertEqual(s.ready['W'],2)
    def test_clock_cannot_reverse(self):
        s=KitState('Twitch');s.advance(1)
        with self.assertRaises(ValueError):s.advance(.5)

if __name__=='__main__':unittest.main()
