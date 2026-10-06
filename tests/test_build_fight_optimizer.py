import unittest
from sharpwr import engine_namespace
from sharpwr.build_fight_optimizer import BuildFightEvaluator,search_builds,legal,score,TIER3

class AbilityBuildRanking(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.ns=engine_namespace()
    def evaluator(self,champ='Ezreal',level=15):return BuildFightEvaluator(self.ns,champ,level,10000,100,100)
    def test_every_champion_runs_ability_aware_build(self):
        from sharpwr.marksman_kits import PRIORITIES
        for name in PRIORITIES:
            with self.subTest(champion=name):
                row=self.evaluator(name).evaluate(['Muramana',"Nashor's Tooth"],"Spellslinger's Shoes")
                self.assertGreater(row['Damage'],0)
                self.assertGreaterEqual(row['Other damage'],0)
                if name!='Vayne':self.assertGreater(row['Other damage'],0)
                self.assertAlmostEqual(row['AA damage']+row['Other damage'],row['Damage'])
                self.assertTrue(row['TTK'] is None or row['TTK']>=0)
    def test_ap_changes_ability_damage(self):
        e=self.evaluator();empty=e.evaluate([]);ap=e.evaluate(["Nashor's Tooth"])
        self.assertGreater(ap['AP'],empty['AP'])
        self.assertGreater(ap['Other damage'],empty['Other damage'])
    def test_cap_is_reported_and_zeri_excess_is_not_discarded(self):
        row=self.evaluator('Zeri').evaluate(["Guinsoo's Rageblade",'Phantom Dancer',"Nashor's Tooth","Wit's End",'Rapid Firecannon'],'Gunmetal Greaves')
        self.assertEqual(row['Starting AS'],1.5);self.assertGreater(row['AS over cap'],0)
    def test_legal_exclusive_groups(self):
        self.assertFalse(legal(['Muramana','Manamune']))
        self.assertFalse(legal(['Terminus','Mortal Reminder']))
        self.assertFalse(legal(['Infinity Edge','Infinity Edge']))
    def test_search_deduplicates_and_returns_only_three_full_builds(self):
        pool=['Muramana',"Nashor's Tooth",'Infinity Edge','Phantom Dancer','Statikk Shiv',"Guinsoo's Rageblade"]
        r=search_builds(self.evaluator(),pool,TIER3[:2],beam_width=8,refine_count=4)
        self.assertEqual(len(r['full']),3);self.assertEqual(set(r['stages']),{1,2,3,4})
        self.assertEqual(r['tested'][1],6);self.assertEqual(r['tested'][2],15)
        for stage,rows in r['stages'].items():
            self.assertLessEqual(len(rows),10);self.assertTrue(all(len(x['Items'])==stage for x in rows))
            self.assertEqual(rows,sorted(rows,key=score))
        self.assertTrue(all(len(x['Items'])==5 and x['Boots'] for x in r['full']))
        self.assertEqual(len({(x['Items'],x['Boots']) for x in r['full']}),3)
        self.assertEqual(len(r['marginal']),6)
        self.assertEqual(r['full'],sorted(r['full'],key=score))
    def test_required_items_are_in_every_build(self):
        pool=['Muramana',"Nashor's Tooth",'Infinity Edge','Phantom Dancer','Statikk Shiv']
        r=search_builds(self.evaluator(),pool,TIER3[:2],beam_width=8,refine_count=4,max_items=3,required=['Essence Reaver'])
        self.assertEqual(r['required'],['Essence Reaver']);self.assertEqual(set(r['stages']),{2})
        self.assertEqual(r['tested'][2],5)
        for rows in (r['stages'][2],r['full']):
            self.assertTrue(all('Essence Reaver' in x['Items'] for x in rows))
        self.assertTrue(all(len(x['Items'])==3 for x in r['full']))
        whole=search_builds(self.evaluator(),pool,TIER3[:2],max_items=2,required=['Essence Reaver','Infinity Edge'])
        self.assertTrue(all(x['Items']==('Essence Reaver','Infinity Edge') for x in whole['full']))
        with self.assertRaises(ValueError):search_builds(self.evaluator(),pool,TIER3[:2],max_items=2,required=['Muramana','Manamune'])
    def test_offensive_active_obeys_sixty_second_cooldown(self):
        ns=self.ns;kernel=ns['combat_hits']('Ezreal',15,10000,100,100,['Galeforce'],ns['F'],active_ready=True)
        next(kernel)
        hits=[kernel.send({'hp':10000,'time':t}) for t in (0,1,59,60)]
        self.assertEqual(['Cloudburst' in x['notes'] for x in hits],[True,False,False,True])
    def test_cache_reuses_simulation(self):
        e=self.evaluator();a=e.evaluate(['Muramana']);count=e.simulations;b=e.evaluate(['Muramana'])
        self.assertEqual(a,b);self.assertEqual(e.simulations,count)

if __name__=='__main__':unittest.main()
