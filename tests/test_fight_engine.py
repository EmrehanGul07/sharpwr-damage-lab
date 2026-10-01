import unittest
from fight_engine import FightEvent, replay_samira, samira_ranks

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
        r=self.run_fight(actions,instant_skills=False)
        self.assertIn('timing unknown',r.rejected[-1]['reason'])
        r=self.run_fight(actions,r_duration=2.23,instant_skills=False,keystone='Conqueror')
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
    def test_haste_and_navori_change_cooldowns(self):
        r=self.run_fight([(0,'Q'),(1,'Q')],ability_haste=100)
        self.assertEqual(len(r.log),2)
        r=self.run_fight([(0,'Q'),(.1,'AA'),(1.8,'Q')],navori=True)
        self.assertEqual(len(r.rejected),0)
        self.assertAlmostEqual(r.log[1]['cooldowns']['Q'],1.9*.85)
    def test_w_e_bonus_ad_and_magic_resistance(self):
        r=self.run_fight([(0,'W'),(.1,'E')],ad=100,base_ad=60,w_rank=1,e_rank=1,mr=100)
        self.assertEqual(r.log[0]['damage'],80)
        self.assertAlmostEqual(r.log[1]['damage'],26.5+(20+.17*100)*(1+80/10000)/2)
        self.assertTrue(r.log[1]['E_buff'])
    def test_magic_penetration(self):
        r=self.run_fight([(0,'E')],e_rank=1,mr=100,pct_mpen=.3,flat_mpen=10)
        self.assertAlmostEqual(r.total_damage,(45+20+.17*100)*100/160)
    def test_instant_r_and_stack_grant_once(self):
        actions=[(0,'AA'),(.1,'Q'),(1,'AA'),(2.1,'Q'),(3,'AA'),(4.1,'Q'),(4.2,'R')]
        r=self.run_fight(actions,keystone='Conqueror')
        shots=[x for x in r.log if x['action']=='R tick']
        self.assertEqual(len(shots),10)
        self.assertEqual({x['time'] for x in shots},{4.2})
        self.assertEqual(r.skill_count,4)
    def test_collector_executes_skill_and_stops(self):
        r=self.run_fight([(0,'Q'),(1,'AA')],hp=180,collector_threshold=.05,q_rank=1)
        self.assertTrue(r.log[0]['executed']);self.assertEqual(r.total_damage,180)
        self.assertEqual(len(r.log),1)
    def test_automatic_rotation_uses_w_e_and_r(self):
        r=self.run_fight([],w_rank=1,e_rank=1,automatic_until=12,hp=100000)
        self.assertFalse(r.rejected)
        self.assertTrue({'AA','Q','W','E','R tick'}.issubset({x['action'] for x in r.log}))
        self.assertTrue(all(x['time']<=12 for x in r.log))
    def test_melee_user_accepted_passive(self):
        r=self.run_fight([(0,'AA')],ad=109,crit_chance=0,melee=True,mr=100)
        self.assertAlmostEqual(r.total_damage,109+(20+.17*109)/2)
    def test_auto_skill_ranks_all_levels(self):
        for level in range(1,16):
            ranks=samira_ranks(level)
            self.assertEqual(sum(ranks.values()),level)
            self.assertTrue(all(0<=ranks[x]<=4 for x in ('Q','W','E')))
            self.assertEqual(ranks['R'],sum(level>=x for x in (5,9,13)))
        self.assertEqual(samira_ranks(1),dict(Q=1,W=0,E=0,R=0))
        self.assertEqual(samira_ranks(15),dict(Q=4,W=4,E=4,R=3))
    def test_until_death_no_duration_cutoff(self):
        r=self.run_fight([],ad=10,q_rank=0,hp=1000,crit_chance=0,until_death=True)
        self.assertEqual(r.hp_remaining,0)
        self.assertEqual(r.killed_at,99)
    def test_dash_switches_to_melee_automatically(self):
        r=self.run_fight([(0,'AA'),(.1,'E'),(1.1,'AA')],e_rank=1,ad=100,crit_chance=0)
        self.assertFalse(r.log[0]['melee'])
        self.assertTrue(r.log[1]['melee'])
        self.assertTrue(r.log[2]['melee'])
        self.assertGreater(r.log[2]['damage'],r.log[0]['damage'])
    def test_r_never_receives_melee_passive(self):
        actions=[(0,'AA'),(.1,'Q'),(1,'AA'),(2.1,'Q'),(3,'AA'),(4.1,'Q'),(4.2,'R')]
        for melee in (False,True):
            r=self.run_fight(actions,melee=melee,crit_chance=.5)
            shots=[x for x in r.log if x['action']=='R tick']
            self.assertEqual(len(shots),10)
            self.assertTrue(all(x['damage']==(20+.5*100)*1.5 for x in shots))
    def test_unknown_rune_rejected(self):
        with self.assertRaises(ValueError):self.run_fight([(0,'AA')],keystone='First Strike')

if __name__=='__main__':unittest.main()
