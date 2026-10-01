import unittest
from damage_classification import ability_profile,ability_magnification,event_profile,magnification,registry
from marksman_damage_components import damage_component
from fight_engine import replay_samira,FightEvent
from test_combat_engine import engine_namespace

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
        ns=engine_namespace();k=ns['_combat_hits']('Kalista',15,10000,0,0,['Hexoptics C44',"Wit's End"],ns['F']);next(k)
        hit=k.send({'hp':10000,'time':0,'distance':550,'attack_physical':200,'nonbasic_attack_physical':50})
        self.assertAlmostEqual(hit['physical'],215)
        self.assertAlmostEqual(hit['magic'],40)
        self.assertTrue(all('BasicAttack' not in x['tags'] for x in hit['damage_components']))
    def test_ezreal_q_applies_basic_multiplier_without_item_callback(self):
        kw=dict(champion='Ezreal',level=15,ad=100,base_ad=60,attack_speed=1,crit_chance=0,crit_damage=2,hp=10000,armor=0,mr=0,q_rank=1,w_rank=0,e_rank=0,r_rank=0,distance=550)
        a=replay_samira([FightEvent(0,'Q')],**kw);b=replay_samira([FightEvent(0,'Q')],hexoptics=True,**kw)
        self.assertAlmostEqual(b.total_damage,a.total_damage*1.1)
    def test_galeforce_classification_exists_before_other_hits(self):
        r=replay_samira([],level=15,ad=100,attack_speed=1,crit_chance=0,crit_damage=2,hp=10000,armor=0,mr=0,galeforce=True,automatic_until=.1)
        hit=next(x for x in r.log if x['action']=='Galeforce active')
        self.assertEqual(hit['damage_classification']['tags'],['Item','ActiveSpell'])

if __name__=='__main__':unittest.main()
