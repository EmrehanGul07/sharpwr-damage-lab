import unittest
from marksman_ability_database import catalogue,mana_cost,cooldown
from marksman_damage_components import damage_component,yunara_arc_of_ruin,varus_blight

class CatalogueTests(unittest.TestCase):
    def test_all_champions_preserve_slots_and_unknowns(self):
        records=catalogue()
        self.assertEqual(len(records),23)
        for name,r in records.items():
            self.assertEqual(set(r['abilities']),set('PQWER'))
            for slot,a in r['abilities'].items():
                costs=a['mana_by_rank']
                if costs is not None:self.assertEqual(len(costs),3 if slot=='R' else 4)
                elif slot!='P':
                    with self.assertRaises(LookupError):mana_cost(name,slot,1)
    def test_user_confirmations_override_wiki(self):
        for rank in range(1,5):
            self.assertEqual(mana_cost('Yunara','Q',rank),30)
            self.assertEqual(mana_cost('Samira','Q',rank),30)
        self.assertEqual(mana_cost('Samira','R',3),0)
        self.assertEqual(cooldown('Ezreal','E',4,100),6.75)
    def test_mana_unlearned_does_not_spend(self):
        self.assertEqual(mana_cost('Ashe','Q',0),0)
    def test_isolated_kaisa_missiles(self):
        stats=dict(ad=100,base_ad=60,ap=0)
        one=damage_component("Kai'Sa",'Q',1,**stats).physical
        self.assertEqual(damage_component("Kai'Sa",'Q',1,hits=6,**stats).physical,one*2.25)
        self.assertEqual(damage_component("Kai'Sa",'Q',1,hits=12,**stats).physical,one*3.75)
    def test_tristana_full_charge_expected_crit(self):
        base=80+1.2*40
        actual=damage_component('Tristana','E',1,ad=100,base_ad=60,crit_chance=.5,stacks=4).physical
        self.assertEqual(actual,base*1.25*2)
    def test_twitch_rank_and_level_are_separate(self):
        for level,base in [(1,1),(4,2),(7,3),(10,4),(13,5),(15,5)]:
            self.assertEqual(damage_component('Twitch','P',1,ad=100,base_ad=60,level=level,stacks=5).true,base*5)
    def test_varus_blight_maximum_health(self):
        self.assertAlmostEqual(varus_blight(4,3,target_max_hp=10000,ap=100).magic,1710)
    def test_varus_rank_ratios_keep_user_bonus_ad_basis(self):
        self.assertAlmostEqual(damage_component('Varus','Q',2,ad=100,base_ad=60).physical,188)
        self.assertAlmostEqual(damage_component('Varus','Q',4,ad=100,base_ad=60,empowered=True).physical,474)
    def test_xayah_falloff_preserves_user_damage_coefficients(self):
        self.assertAlmostEqual(damage_component('Xayah','E',4,ad=100,base_ad=60,hits=5).physical,120*4)
    def test_yunara_ultimate_rank_damage(self):
        self.assertEqual(yunara_arc_of_ruin(3,bonus_ad=100,ap=100).magic,675)
    def test_negative_and_nonfinite_inputs_rejected(self):
        for ad in (-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError):damage_component('Ezreal','Q',1,ad=ad,base_ad=60)
    def test_rank_four_ezreal_and_bonus_ad(self):
        result=damage_component('Ezreal','E',4,ad=160,base_ad=100,ap=100)
        self.assertEqual(result.magic,380)
        self.assertEqual(result.physical,0)
    def test_vayne_true_damage_minimum_and_wall(self):
        self.assertEqual(damage_component('Vayne','W',1,ad=100,base_ad=60,target_max_hp=100).true,50)
        self.assertEqual(damage_component('Vayne','W',4,ad=100,base_ad=60,target_max_hp=10000).true,900)
        self.assertEqual(damage_component('Vayne','E',1,ad=100,base_ad=60,wall=True).physical,207)
    def test_all_twenty_one_pending_champions_have_known_damage_component(self):
        cases={'Twitch':'E','Yunara':'Q','Lucian':'Q','Varus':'E','Ezreal':'Q','Vayne':'E','Tristana':'W','Ashe':'W','Kalista':'Q','Draven':'E','Caitlyn':'Q','Jinx':'W',"Kai'Sa":'W',"Kog'Maw":'Q','Miss Fortune':'Q','Xayah':'Q','Sivir':'Q','Corki':'Q','Senna':'Q','Zeri':'Q','Jhin':'Q'}
        for name,slot in cases.items():
            with self.subTest(champion=name):
                result=damage_component(name,slot,1,ad=100,base_ad=60,stacks=3)
                self.assertGreater(result.physical+result.magic+result.true,0)

if __name__=='__main__':unittest.main()
