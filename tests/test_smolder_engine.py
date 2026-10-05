import unittest
from sharpwr.champion_skill_data import smolder_skill
from sharpwr.fight_engine import replay_samira,champion_ranks,FightEvent

class SmolderTests(unittest.TestCase):
    def fight(self,events=(),**kw):
        a=dict(champion='Smolder',level=15,ad=178,base_ad=103,ap=0,attack_speed=1.5,crit_chance=0,crit_damage=2,hp=10000,armor=100,mr=100,q_rank=4,w_rank=4,e_rank=4,r_rank=3,max_mana=1000,mana_regen_per_5s=20,timed_combat=True,movement_speed=340,distance=550,attack_range=550)
        a.update(kw);return replay_samira([FightEvent(t,x) for t,x in events],**a)
    def test_user_q_crit_and_stack_damage(self):
        p,m=smolder_skill('Q',1,129,54,0,0,0,2)
        self.assertAlmostEqual(p,127.5)
        p1,m=smolder_skill('Q',1,129,54,0,0,1,2)
        p2,m=smolder_skill('Q',1,129,54,0,0,1,2.3)
        self.assertAlmostEqual(p1/p,1.45)
        self.assertAlmostEqual(p2/p,1.585)
        _,m=smolder_skill('Q',1,178,103,0,20,1,2)
        self.assertAlmostEqual(m,8.7)
    def test_auto_ranks_and_mana(self):
        for lv in range(1,16):self.assertEqual(sum(champion_ranks('Smolder',lv).values()),lv)
        r=self.fight([(0,'W'),(1,'Q'),(2,'R')],w_rank=1)
        for x,cost,start in zip(r.log,(50,30,100),(0,1,2)):
            expected=(1000-50 if start==0 else 1000-80 if start==1 else 1000-180)+4*x['time']
            self.assertAlmostEqual(x['mana'],expected)
        self.assertEqual([x['dragon_stacks'] for x in r.log],[1,2,3])
    def test_burn_ticks_and_execute(self):
        r=self.fight([(0,'Q')],initial_stacks=175)
        ticks=[x for x in r.log if x['action']=='Burn tick']
        self.assertEqual(len(ticks),7)
        first=next(x['time'] for x in r.log if x['action']=='Q')
        for i,x in enumerate(ticks):self.assertAlmostEqual(x['time'],first+i*.5)
        self.assertAlmostEqual(sum(x['damage'] for x in ticks),(.00025*75+.00005*175)*10000)
        r=self.fight([(0,'Q')],initial_stacks=175,hp=100)
        self.assertEqual(r.hp_remaining,0)
    def test_aa_never_grants_dragon_practice(self):
        r=self.fight([(0,'AA'),(1,'Q'),(2,'AA')])
        self.assertEqual([x['dragon_stacks'] for x in r.log],[0,1,1])
    def test_candidate_e_bolts_at_100_stacks(self):
        r=self.fight([(0,'E')],initial_stacks=100)
        self.assertEqual(len(r.log),7)
        self.assertEqual(r.skill_count,1)
        self.assertEqual(r.log[-1]['dragon_stacks'],101)
    def test_kite_preserves_max_range_and_arc(self):
        r=self.fight(automatic_until=10)
        self.assertFalse(r.rejected)
        self.assertTrue(all(x['distance']==550 for x in r.log))
        self.assertGreater(r.log[-1]['kite_arc'],1000)
        self.assertTrue(all(x['movement_policy']=='max_range_kite' for x in r.log))
    def test_shorter_q_range_steps_in_then_returns(self):
        r=self.fight(automatic_until=8,attack_range=575,distance=575,use_e=False)
        self.assertFalse(r.rejected)
        q=[x for x in r.log if x['action']=='Q']
        self.assertTrue(q)
        self.assertTrue(all(x['cast_distance']<=550+1e-8 for x in q))
        self.assertTrue(any(x['action']=='AA' and x['distance']>550 for x in r.log))
    def test_no_mana_auto_keeps_attacking(self):
        r=self.fight(automatic_until=5,max_mana=0,mana_regen_per_5s=0)
        self.assertGreater(r.aa_count,0);self.assertEqual(r.skill_count,0)
    def test_threshold_activates_on_next_q(self):
        r=self.fight([(0,'Q'),(4,'Q')],initial_stacks=174)
        self.assertEqual(len([x for x in r.log if x['action']=='Burn tick']),7)
        self.assertEqual(r.log[0]['dragon_stacks'],175)
