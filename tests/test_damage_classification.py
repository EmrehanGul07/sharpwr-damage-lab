import unittest
from damage_classification import ability_profile,ability_magnification,event_profile,magnification,registry
from marksman_damage_components import damage_component
from fight_engine import replay_samira,FightEvent
from sharpwr import engine_namespace

class DamageClassificationTests(unittest.TestCase):
    def test_inventory_and_unknown_are_explicit(self):
        d=registry();self.assertEqual(sum(len(x) for x in d['abilities'].values()),115)
        self.assertEqual(len(d['runes']),51);self.assertEqual(len(d['items']),73)
        self.assertEqual(ability_profile('Yunara','W')['status'],'unknown_WR')
        self.assertEqual(ability_profile('Samira','P')['classification'],'default_damage')
        self.assertNotEqual(ability_profile('Yunara','W')['status'],ability_profile('Samira','P')['status'])
    def test_basic_skill_does_not_tag_zero_spell_event_basic(self):
        q=ability_profile('Ezreal','Q');self.assertEqual(q['tags'],['BasicAttack'])
        self.assertEqual(q['variants']['spell_effect_event']['raw_damage'],0)
        self.assertEqual(q['variants']['spell_effect_event']['tags'],['ActiveSpell'])
        self.assertAlmostEqual(ability_magnification('Ezreal','Q',550),1.1)
        self.assertEqual(ability_magnification('Senna','Q',550),1)
        self.assertEqual(ability_magnification('Samira','Q',550),1)
    def test_default_burn_is_distinct_from_initial_smolder_q(self):
        self.assertEqual(event_profile('Smolder','Burn tick')['tags'],[])
        self.assertAlmostEqual(ability_magnification('Smolder','Q',550),1.1)
        self.assertEqual(ability_magnification('Smolder','Burn tick',550),1)
    def test_magic_spell_is_not_magic_melee_passive(self):
        raw=damage_component('Samira','E',1,ad=100,base_ad=60)
        self.assertEqual(raw.instances('Samira','E')[0]['tags'],['ActiveSpell','AOE'])
    def test_hexoptics_excludes_champion_extra_and_item_onhit(self):
        ns=engine_namespace();k=ns['combat_hits']('Kalista',15,10000,0,0,['Hexoptics C44',"Wit's End"],ns['F']);next(k)
        hit=k.send({'hp':10000,'time':0,'distance':550,'attack_physical':200,'nonbasic_attack_physical':50})
        self.assertAlmostEqual(hit['physical'],215)
        self.assertAlmostEqual(hit['magic'],40)
        self.assertTrue(all('BasicAttack' not in x['tags'] for x in hit['damage_components']))
    def test_ezreal_q_applies_basic_multiplier_without_item_callback(self):
        kw=dict(champion='Ezreal',level=15,ad=100,base_ad=60,attack_speed=1,crit_chance=0,crit_damage=2,hp=10000,armor=0,mr=0,q_rank=1,w_rank=0,e_rank=0,r_rank=0,distance=550)
        a=replay_samira([FightEvent(0,'Q')],**kw);b=replay_samira([FightEvent(0,'Q')],hexoptics=True,**kw)
        self.assertAlmostEqual(b.total_damage,a.total_damage*1.1)
    def test_user_verified_ezreal_q_does_not_magnify_carried_wits_end(self):
        ns=engine_namespace()
        def run(distance,items):
            kernel=ns['combat_hits']('Ezreal',15,10000,100,100,items,ns['F']);next(kernel)
            def onhit(state):return kernel.send(state)
            r=replay_samira([FightEvent(0,'Q')],champion='Ezreal',level=15,ad=178,base_ad=123,ap=0,attack_speed=.99,crit_chance=.25,crit_damage=2,hp=10000,armor=100,mr=100,q_rank=1,w_rank=0,e_rank=0,r_rank=0,distance=distance,attack_range=550,movement_speed=0,max_mana=2000,aa_hit=onhit,hexoptics=True,sub_runes=('Cut Down',),automatic_until=2)
            return r.total_damage
        near=run(0,['Hexoptics C44']);far=run(550,['Hexoptics C44'])
        self.assertGreater(far,near)
        near_onhit=run(0,['Hexoptics C44',"Wit's End"])-near
        far_onhit=run(550,['Hexoptics C44',"Wit's End"])-far
        self.assertAlmostEqual(near_onhit,far_onhit)
        self.assertAlmostEqual(near_onhit,20*1.065)
        profile=ability_profile('Ezreal','Q')
        self.assertEqual(profile['user_validation']['date'],'2026-10-02')

    def test_galeforce_classification_exists_before_other_hits(self):
        r=replay_samira([],level=15,ad=100,attack_speed=1,crit_chance=0,crit_damage=2,hp=10000,armor=0,mr=0,galeforce=True,automatic_until=.1)
        hit=next(x for x in r.log if x['action']=='Galeforce active')
        self.assertEqual(hit['damage_classification']['tags'],['Item','ActiveSpell'])

if __name__=='__main__':unittest.main()
