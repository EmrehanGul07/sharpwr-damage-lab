import unittest
from test_combat_engine import engine_namespace
from fight_engine import replay_samira,FightEvent

class SpellbladeCasts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.ns=engine_namespace()
    def kernel(self,item,spell=False):
        k=self.ns['_combat_hits']('Ezreal',15,10000,100,100,[item],self.ns['F'],spell=spell)
        next(k);return k
    def test_precaster_does_not_rearm_from_cooldown(self):
        for item,label in [('Trinity Force','Trinity'),('Essence Reaver','ER'),('Iceborn Gauntlet','Iceborn')]:
            with self.subTest(item=item):
                k=self.kernel(item,True)
                self.assertEqual([label in k.send({'hp':10000,'time':t})['notes'] for t in (0,2,4)],[True,False,False])
    def test_only_actual_casts_rearm_and_icd_cast_is_not_queued(self):
        k=self.kernel('Trinity Force')
        events=[(0,[0]),(1,[1]),(2,[]),(3,[3]),(5,[])]
        self.assertEqual(['Trinity' in k.send({'hp':10000,'time':t,'event_driven':True,'spell_cast_times':casts})['notes'] for t,casts in events],[True,False,False,True,False])
    def test_delayed_aa_checks_cast_timestamp(self):
        k=self.kernel('Essence Reaver')
        self.assertIn('ER',k.send({'hp':10000,'time':0,'event_driven':True,'spell_cast_times':[0]})['notes'])
        self.assertNotIn('ER',k.send({'hp':10000,'time':2,'event_driven':True,'spell_cast_times':[1]})['notes'])
    def test_multiple_spellblade_items_are_rejected(self):
        with self.assertRaises(ValueError):
            k=self.ns['_combat_hits']('Ezreal',15,10000,100,100,['Trinity Force','Essence Reaver'],self.ns['F']);next(k)
    def test_successful_replay_casts_reach_item_kernel(self):
        k=self.kernel('Trinity Force');seen=[]
        def hit(state):
            seen.extend(state.get('spell_cast_times',[]));return k.send(state)
        replay_samira([FightEvent(0,'Q'),FightEvent(.5,'AA'),FightEvent(2,'AA'),FightEvent(3,'E'),FightEvent(3.5,'AA')],champion='Ezreal',level=15,ad=200,base_ad=100,attack_speed=.7,crit_chance=0,crit_damage=2,hp=10000,armor=100,mr=100,q_rank=1,w_rank=1,e_rank=1,r_rank=1,max_mana=1000,aa_hit=hit,automatic_until=5,attack_range=550,distance=550)
        self.assertEqual(seen,[0,3])

if __name__=='__main__':unittest.main()
