import unittest
from sharpwr.fight_engine import FightEvent, replay_samira, samira_ranks

class ReplayTests(unittest.TestCase):
    def run_fight(self,actions,**kw):
        args=dict(aa_windup=0.,level=15,ad=100,attack_speed=1,crit_chance=.5,crit_damage=2,hp=10000,armor=0,q_rank=4);args.update(kw)
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
    def test_mana_costs_and_regeneration(self):
        r=self.run_fight([(0,'Q'),(.1,'W'),(5,'Q')],w_rank=1,max_mana=30,mana_regen_per_5s=30)
        self.assertEqual([x['mana'] for x in r.log],[0,0])
        self.assertEqual(r.rejected[0]['reason'],'Insufficient mana')
    def test_automatic_zero_mana_continues_attacking(self):
        r=self.run_fight([],max_mana=0,until_death=True,hp=300,crit_chance=0)
        self.assertEqual(r.skill_count,0)
        self.assertEqual(r.hp_remaining,0)
    def test_r_free_and_style_expires(self):
        a=[(0,'AA'),(.1,'Q'),(1,'AA'),(2.1,'Q'),(3,'AA'),(4.1,'Q'),(4.2,'R')]
        r=self.run_fight(a,max_mana=90)
        self.assertEqual(len([x for x in r.log if x['action']=='R tick']),10)
        self.assertEqual(r.log[-1]['mana'],0)
        r=self.run_fight(a[:-1]+[(11,'R')],max_mana=90)
        self.assertEqual(r.rejected[-1]['reason'],'S style required')
    def test_timed_w_blocks_aa_q_and_has_two_hits(self):
        r=self.run_fight([(0,'W'),(.2,'AA'),(.3,'Q'),(.9,'AA')],w_rank=1,timed_combat=True,distance=100)
        self.assertEqual([round(x['time'],2) for x in r.log if x['action']=='W'],[.1,.85])
        self.assertEqual([x['reason'] for x in r.rejected],['W active','W active'])
        self.assertEqual(r.skill_count,1)
    def test_timed_r_cancels_pending_w_hit(self):
        a=[(0,'AA'),(.1,'Q'),(1,'AA'),(2.1,'Q'),(3,'AA'),(4.1,'W'),(4.3,'R'),(4.4,'AA'),(4.5,'Q'),(4.6,'W')]
        r=self.run_fight(a,w_rank=1,timed_combat=True,distance=100)
        self.assertEqual(len([x for x in r.log if x['action']=='W']),1)
        shots=[x for x in r.log if x['action']=='R tick']
        self.assertEqual(len(shots),10)
        self.assertAlmostEqual(shots[-1]['time']-shots[0]['time'],2.013)
        self.assertTrue(all(x['reason']=='R channel active' for x in r.rejected))
    def test_timed_q_projectile_and_e_q_buffered_w(self):
        r=self.run_fight([(0,'Q')],timed_combat=True,distance=500)
        self.assertAlmostEqual(r.log[0]['time'],.25+500/2600)
        r=self.run_fight([(0,'E'),(.1,'Q'),(.2,'W')],e_rank=1,w_rank=1,timed_combat=True,distance=525)
        self.assertEqual([x['action'] for x in r.log],['E','Q','W','W'])
        self.assertAlmostEqual(r.log[1]['time'],650/1600)
        self.assertAlmostEqual(r.log[2]['time'],650/1600+.1)
    def test_timed_range_and_automatic_interleaving(self):
        r=self.run_fight([(0,'AA'),(0,'W')],w_rank=1,timed_combat=True,distance=700)
        self.assertEqual(len(r.log),0)
        self.assertEqual(len(r.rejected),2)
        r=self.run_fight([],w_rank=1,e_rank=1,r_rank=3,timed_combat=True,distance=525,automatic_until=10)
        self.assertFalse(r.rejected)
        self.assertTrue(any(x['action']=='R tick' for x in r.log))
        self.assertTrue(all(x['time']<=10 for x in r.log))
    def test_walk_back_after_dash_keeps_auto_attacking(self):
        r=self.run_fight([],e_rank=1,w_rank=1,r_rank=3,timed_combat=True,movement_speed=340,distance=525,automatic_until=20,hp=100000)
        aas=[x for x in r.log if x['action']=='AA' and 9<=x['time']<=15]
        self.assertGreaterEqual(len(aas),3)
        self.assertFalse(r.rejected)
        self.assertTrue(all(x['distance']<=525 for x in aas))
    def test_walk_closes_initial_range_and_respects_cast_stop(self):
        r=self.run_fight([],q_rank=0,timed_combat=True,movement_speed=340,distance=700,automatic_until=2)
        self.assertGreater(r.aa_count,0)
        self.assertLess(r.log[0]['distance'],525)
        r=self.run_fight([(0,'Q')],timed_combat=True,movement_speed=340,distance=500)
        self.assertAlmostEqual(r.log[0]['distance'],500-340*(500/2600))
    def test_r_allows_walking_with_movement_penalty(self):
        a=[(0,'AA'),(.1,'Q'),(1,'AA'),(2.1,'Q'),(3,'AA'),(4.1,'Q'),(4.7,'R')]
        r=self.run_fight(a,timed_combat=True,movement_speed=10,distance=525)
        shots=[x for x in r.log if x['action']=='R tick']
        self.assertEqual(len(shots),10)
        self.assertLess(shots[-1]['distance'],shots[3]['distance'])
    def test_pc_base_windup_with_wr_scaling(self):
        base=.149999994/.658
        r=self.run_fight([(0,'AA')],timed_combat=True,distance=100,base_windup=base,starting_bonus_as=1)
        self.assertAlmostEqual(r.log[0]['time'],base/1.5)
        self.assertAlmostEqual(r.log[0]['windup'],base/1.5)
        r=self.run_fight([(0,'AA')],timed_combat=True,distance=500,base_windup=base,aa_stats=lambda state:{'bonus_as_total':2})
        self.assertAlmostEqual(r.log[0]['time'],base/2+500/2800)
    def test_windup_prevents_movement_and_does_not_cancel_aa(self):
        base=.149999994/.658
        r=self.run_fight([(0,'AA'),(.1,'Q')],timed_combat=True,distance=100,movement_speed=340,base_windup=base)
        self.assertEqual(r.aa_count,1)
        self.assertEqual(r.log[0]['distance'],100)
        self.assertEqual(r.rejected[0]['reason'],'AA windup active')
    def test_mid_cycle_attack_speed_change_updates_clock(self):
        r=self.run_fight([(0,'AA'),(.2,'E'),(.85,'AA')],e_rank=1,timed_combat=True,distance=525)
        self.assertEqual(r.aa_count,2)
        self.assertFalse(r.rejected)
    def test_attack_speed_expiry_updates_clock(self):
        r=self.run_fight([],q_rank=0,timed_combat=True,distance=0,automatic_until=2,aa_stats=lambda state:{'bonus_as_total':1 if state['time']<.25 else 0,'as':2 if state['time']<.25 else 1,'buff_expiry':.25})
        self.assertAlmostEqual(r.log[1]['time'],.75)
    def test_mana_refund_and_muramana_skill_proc(self):
        r=self.run_fight([(0,'Q')],max_mana=1000,mana_refund=.15,muramana=True,crit_chance=0,q_rank=1)
        self.assertAlmostEqual(r.log[0]['mana'],974.5)
        self.assertAlmostEqual(r.log[0]['damage'],170)
        r=self.run_fight([(0,'W')],w_rank=1,max_mana=1000,muramana=True,timed_combat=True,distance=100,crit_chance=0)
        self.assertEqual(sum('Muramana' in note for hit in r.log for note in hit['effects']),1)
    def test_damage_ledger_caps_overkill(self):
        r=self.run_fight([(0,'AA')],hp=10)
        self.assertEqual(r.total_damage,10)
        self.assertEqual(r.log[0]['damage'],10)
        self.assertEqual(r.log[0]['raw_damage'],150)
    def test_style_expiry_checked_before_r_cast(self):
        a=[(0,'AA'),(.1,'Q'),(1,'AA'),(2.1,'Q'),(3,'AA'),(4.1,'Q'),(12,'R')]
        r=self.run_fight(a,timed_combat=True,distance=0)
        self.assertEqual(r.rejected[-1]['reason'],'S style required')
    def test_unknown_rune_rejected(self):
        with self.assertRaises(ValueError):self.run_fight([(0,'AA')],keystone='unrecognized')

if __name__=='__main__':unittest.main()
