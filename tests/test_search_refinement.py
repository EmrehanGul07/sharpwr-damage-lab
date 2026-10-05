import unittest
from fight_engine import FightEvent,replay_samira
from build_fight_optimizer import BuildFightEvaluator,diverse_shortlist,build_profiles
from marksman_damage_components import jhin_attack_damage,xayah_feather_multiplier,damage_component
from sharpwr import engine_namespace

class SearchRefinement(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.ns=engine_namespace()
    def test_diversity_keeps_weaker_ap_path_and_mixed_path(self):
        evaluator=BuildFightEvaluator(self.ns,'Ezreal',15,10000,100,100)
        items=[('Infinity Edge',),('Bloodthirster',),('Phantom Dancer',),("Nashor's Tooth",),("Nashor's Tooth",'Infinity Edge'),('Terminus',)]
        rows=[{'Items':x,'Boots':None,'TTK':None,'Damage':100-i*10,'Gold':100} for i,x in enumerate(items)]
        kept=diverse_shortlist(evaluator,rows,5)
        self.assertIn(("Nashor's Tooth",'Infinity Edge'),[x['Items'] for x in kept])
        self.assertTrue(any('AP' in build_profiles(evaluator,x['Items']) for x in kept))
        self.assertTrue(any('penetration' in build_profiles(evaluator,x['Items']) for x in kept))
    def test_refinement_enumerates_more_policies_and_is_not_worse(self):
        e=BuildFightEvaluator(self.ns,'Ezreal',15,2000,100,100)
        baseline=e.evaluate(['Muramana']);refined=e.evaluate(['Muramana'],refine=True)
        self.assertLessEqual(refined['TTK'],baseline['TTK'])
        self.assertEqual(e.simulations,2+144)
        self.assertIn(refined['Movement'],('skill_envelope','aa_envelope','close_envelope'))
    def test_jhin_conversion_units_and_no_recursive_conversion(self):
        self.assertAlmostEqual(jhin_attack_damage(100,15,.5,.5),180)
        self.assertAlmostEqual(jhin_attack_damage(100,1,0,0),103)
        args=dict(champion='Jhin',level=15,ad=100,base_ad=60,ap=0,attack_speed=.625,starting_bonus_as=.5,crit_chance=.5,crit_damage=2,hp=10000,armor=0,mr=0,q_rank=0,w_rank=0,e_rank=0,r_rank=0,automatic_until=3)
        r=replay_samira([FightEvent(0,'AA'),FightEvent(2,'AA')],**args)
        self.assertTrue(all(abs(x['AD']-180)<1e-8 for x in r.log if x['action'].startswith('AA')))
        self.assertFalse(any('conversion coefficients missing' in x for x in r.assumptions))
    def test_xayah_falloff_has_floor_and_does_not_double_multiply(self):
        self.assertAlmostEqual(xayah_feather_multiplier(3),2.7)
        self.assertAlmostEqual(xayah_feather_multiplier(10),5.5)
        self.assertAlmostEqual(xayah_feather_multiplier(12),5.7)
        one=damage_component('Xayah','E',4,ad=100,base_ad=60,crit_chance=.5,crit_damage=2.3)
        multi=damage_component('Xayah','E',4,ad=100,base_ad=60,crit_chance=.5,crit_damage=2.3,hits=3)
        self.assertAlmostEqual(multi.physical,one.physical*2.7)
    def test_movement_choice_changes_trace_and_range(self):
        args=dict(champion='Ezreal',level=15,ad=100,ap=0,attack_speed=1,crit_chance=0,crit_damage=2,hp=10000,armor=0,mr=0,q_rank=0,w_rank=0,e_rank=0,r_rank=0,automatic_until=2,movement_speed=350,distance=550,attack_range=550)
        far=replay_samira([],movement_policy='aa_envelope',**args)
        close=replay_samira([],movement_policy='close_envelope',**args)
        self.assertEqual(far.log[-1]['distance'],550)
        self.assertLess(close.log[-1]['distance'],550)
        self.assertGreaterEqual(close.log[-1]['distance'],200)
        self.assertNotEqual(far.log[-1]['movement_policy'],close.log[-1]['movement_policy'])

class FeatherTimeline(unittest.TestCase):
    def test_q_plants_two_and_manual_e_recalls_both(self):
        r=replay_samira([FightEvent(0,'Q'),FightEvent(2,'E')],champion='Xayah',level=15,ad=100,base_ad=60,ap=0,attack_speed=1,crit_chance=0,crit_damage=2,hp=10000,armor=0,mr=0,q_rank=1,w_rank=0,e_rank=1,r_rank=0,distance=200,attack_range=550,movement_speed=0,automatic_until=3,max_mana=1000)
        self.assertFalse(r.rejected)
        q=next(x for x in r.log if x['action'].startswith('Q'))
        e=next(x for x in r.log if x['action'].startswith('E'))
        self.assertAlmostEqual(q['raw_damage'],140)
        self.assertAlmostEqual(e['raw_damage'],90*1.9)
        self.assertEqual(q['after']['feathers'],2)
    def test_stored_passive_attacks_expire(self):
        from marksman_kits import Kit
        k=Kit('Xayah',{'Q':1,'W':0,'E':1,'R':0},15,550)
        k.state.update(feather_attacks=3,feather_attacks_until=7.5)
        k.expire(7.5);self.assertEqual(k.state['feather_attacks'],0)

if __name__=='__main__':unittest.main()
