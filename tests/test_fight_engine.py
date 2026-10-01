import unittest
from fight_engine import FightEvent, replay_samira

class ReplayTests(unittest.TestCase):
    def run_fight(self,actions,**kw):
        args=dict(level=15,ad=100,attack_speed=1,crit_chance=.5,crit_damage=2,hp=10000,armor=0,q_rank=4);args.update(kw)
        return replay_samira([FightEvent(t,a) for t,a in actions],**args)
    def test_50_percent_expected(self):
        r=self.run_fight([(0,'Q')],q_rank=1)
        self.assertEqual(r.log[0]['damage'],(15+125)*1.25)
        r=self.run_fight([(0,'AA')])
        self.assertEqual(r.log[0]['damage'],150)
    def test_conqueror_post_hit_changes_next_ad(self):
        r=self.run_fight([(0,'AA'),(1,'Q'),(2,'AA')],keystone='Conqueror')
        self.assertEqual([x['AD'] for x in r.log],[100,105,110])
        self.assertEqual([x['after']['conqueror'] for x in r.log],[1,2,3])
        self.assertEqual(r.aa_count,2);self.assertEqual(r.skill_count,1)
    def test_expiry(self):
        r=self.run_fight([(0,'AA'),(7,'Q')],keystone='Conqueror')
        self.assertEqual(r.log[1]['AD'],100)
    def test_style_different_hits_only(self):
        r=self.run_fight([(0,'AA'),(1,'AA'),(1.5,'Q'),(2.5,'AA')])
        self.assertEqual([x['after']['style'] for x in r.log],[1,1,2,3])
    def test_lethal_tempo_attacks_only(self):
        r=self.run_fight([(0,'AA'),(.5,'Q'),(1.5,'AA')],keystone='Lethal Tempo')
        self.assertEqual([x['after']['lethal_tempo'] for x in r.log],[1,1,2])
    def test_rejected_actions_have_no_stacks(self):
        r=self.run_fight([(0,'AA'),(.1,'AA'),(.2,'Q'),(.3,'Q')],keystone='Conqueror')
        self.assertEqual(len(r.rejected),2);self.assertEqual(r.log[-1]['after']['conqueror'],2)
    def test_r_requires_style_and_measured_duration(self):
        r=self.run_fight([(0,'R')]);self.assertEqual(len(r.log),0)
        actions=[(0,'AA'),(1,'Q'),(2,'AA'),(3,'Q'),(4,'AA'),(5,'Q'),(6,'R')]
        r=self.run_fight(actions)
        self.assertIn('timing unknown',r.rejected[-1]['reason'])
        r=self.run_fight(actions,r_duration=2.23,keystone='Conqueror')
        self.assertEqual(len([x for x in r.log if x['action']=='R tick']),10)
        self.assertEqual(r.skill_count,4)
        self.assertEqual(r.log[-1]['after']['style'],0)
    def test_seeded_crit_reproducible(self):
        a=[(i,'AA') for i in range(10)]
        r=self.run_fight(a,mode='Seeded critical rolls',seed=42)
        r2=self.run_fight(a,mode='Seeded critical rolls',seed=42)
        self.assertEqual(r.log,r2.log)
        self.assertEqual({x['damage'] for x in r.log},{100,200})
    def test_yuntal_growth_attacks_only(self):
        r=self.run_fight([(0,'AA'),(.5,'Q'),(1.5,'AA')],yuntal=True,crit_chance=0)
        self.assertEqual([x['crit_chance'] for x in r.log],[0,.002,.002])
    def test_dead_target_stops_replay(self):
        r=self.run_fight([(0,'AA'),(1,'Q')],hp=10)
        self.assertEqual(len(r.log),1);self.assertEqual(r.hp_remaining,0)
    def test_unknown_rune_rejected(self):
        with self.assertRaises(ValueError):self.run_fight([(0,'AA')],keystone='First Strike')

if __name__=='__main__':unittest.main()
