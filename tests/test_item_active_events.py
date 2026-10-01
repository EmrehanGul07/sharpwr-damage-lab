import unittest
from test_combat_engine import engine_namespace
from fight_engine import replay_samira,FightEvent

class ItemEvents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.ns=engine_namespace()
    def test_duskblade_first_aa_then_ten_second_cooldown(self):
        k=self.ns['_combat_hits']('Ezreal',15,100000,100,100,['Duskblade of Draktharr'],self.ns['F']);next(k)
        hits=[k.send({'time':t,'hp':100000,'event_driven':True}) for t in (0,1,9.99,10,20)]
        self.assertEqual(['Nightstalker' in h['notes'] for h in hits],[True,False,False,True,True])
    def test_skill_on_hit_does_not_consume_duskblade(self):
        k=self.ns['_combat_hits']('Ezreal',15,100000,100,100,['Duskblade of Draktharr'],self.ns['F']);next(k)
        self.assertNotIn('Nightstalker',k.send({'time':0,'hp':100000,'event_driven':True,'skill_on_hit':True})['notes'])
        self.assertIn('Nightstalker',k.send({'time':.1,'hp':100000,'event_driven':True})['notes'])
    def test_galeforce_no_longer_injected_into_aa(self):
        k=self.ns['_combat_hits']('Ezreal',15,100000,100,100,['Galeforce'],self.ns['F'],active_ready=True);next(k)
        self.assertNotIn('Cloudburst',k.send({'time':0,'hp':100000,'event_driven':True})['notes'])
    def test_independent_galeforce_event_and_fifty_second_recast(self):
        for champion in ('Ezreal','Samira','Smolder'):
            with self.subTest(champion=champion):
                r=replay_samira([FightEvent(0,'AA')],champion=champion,level=15,ad=200,base_ad=100,attack_speed=.7,crit_chance=0,crit_damage=2,hp=1000000,armor=100,mr=100,q_rank=0,w_rank=0,e_rank=0,r_rank=0,automatic_until=60,galeforce=True)
                events=[x for x in r.log if x['action']=='Galeforce active']
                self.assertEqual(len(events),2);self.assertAlmostEqual(events[1]['time']-events[0]['time'],50)
                self.assertTrue(all(x['damage']>0 for x in events))
                self.assertAlmostEqual(sum(x['damage'] for x in r.log),r.total_damage)
                self.assertAlmostEqual(1000000-r.hp_remaining,r.total_damage)
                self.assertEqual([x['time'] for x in r.log],sorted(x['time'] for x in r.log))

if __name__=='__main__':unittest.main()
