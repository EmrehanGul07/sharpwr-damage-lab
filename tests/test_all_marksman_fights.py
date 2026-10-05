import math
import unittest
from sharpwr.fight_engine import FightEvent,replay_samira,champion_ranks
from sharpwr.marksman_kits import PRIORITIES

PENDING=[n for n in PRIORITIES if n not in ('Samira','Smolder')]

def fight(name,**extra):
    ranks=champion_ranks(name,15)
    args=dict(champion=name,level=15,ad=200,base_ad=100,ap=50,attack_speed=.7,starting_bonus_as=1,crit_chance=.5,crit_damage=2,hp=10000,armor=100,mr=100,q_rank=ranks['Q'],w_rank=ranks['W'],e_rank=ranks['E'],r_rank=ranks['R'],automatic_until=30,timed_combat=True,movement_speed=350,attack_range=550,distance=550,max_mana=2000,mana_regen_per_5s=20)
    args.update(extra);return replay_samira(args.pop('events',[]),**args)

class AllMarksmanFights(unittest.TestCase):
    def test_every_adapter_has_valid_ledger_mana_time_and_movement(self):
        for name in PENDING:
            with self.subTest(champion=name):
                r=fight(name)
                self.assertTrue(r.log);self.assertGreater(r.aa_count,0);self.assertGreater(r.skill_count,0)
                self.assertFalse(r.rejected)
                self.assertAlmostEqual(r.total_damage,10000-r.hp_remaining)
                self.assertAlmostEqual(sum(x['damage'] for x in r.log),r.total_damage)
                self.assertEqual([x['time'] for x in r.log],sorted(x['time'] for x in r.log))
                for x in r.log:
                    self.assertGreaterEqual(x['hp_after'],0);self.assertLessEqual(x['hp_after'],x['hp_before'])
                    self.assertTrue(math.isfinite(x['damage']));self.assertGreaterEqual(x['damage'],0)
                    self.assertTrue(0<=x['mana']<=2000);self.assertGreaterEqual(x['distance'],0)
                if name=='Xayah':
                    self.assertEqual(max(x['kite_arc'] for x in r.log),0)
                    self.assertTrue(any('aligned radial movement' in a for a in r.assumptions))
                else:self.assertGreater(max(x['kite_arc'] for x in r.log),0)
    def test_skill_orders_obey_rank_caps_and_ultimate_unlocks(self):
        for name in PRIORITIES:
            for level in range(1,16):
                with self.subTest(champion=name,level=level):
                    ranks=champion_ranks(name,level)
                    self.assertEqual(sum(ranks.values()),level)
                    self.assertEqual(ranks['R'],sum(level>=x for x in (5,9,13)))
                    self.assertTrue(all(0<=r<=4 for s,r in ranks.items() if s!='R'))
    def test_low_mana_still_auto_attacks(self):
        for name in PENDING:
            with self.subTest(champion=name):
                r=fight(name,max_mana=0,mana_regen_per_5s=0,automatic_until=10)
                self.assertGreater(r.aa_count,0)
                self.assertTrue(all(x['mana']==0 for x in r.log))
    def test_expected_crit_50_percent_is_midpoint_for_basic_attack(self):
        for n in ('Ezreal','Kalista','Twitch'):
            vals=[]
            for crit in (0,.5,1):
                r=fight(n,crit_chance=crit,events=[FightEvent(0,'AA')],automatic_until=1)
                vals.append(next(x['damage'] for x in r.log if x['action']=='AA'))
            self.assertAlmostEqual(vals[1],(vals[0]+vals[2])/2)
    def test_twitch_first_tick_plus_five_later_ticks(self):
        r=fight('Twitch',events=[FightEvent(0,'AA')],automatic_until=6,ap=0,crit_chance=0)
        ticks=[x for x in r.log if x['action']=='Venom tick']
        first=next(x['time'] for x in r.log if x['action']=='AA')
        for i,x in enumerate(ticks):self.assertAlmostEqual(x['time'],first+i)
        self.assertEqual(len(ticks),6)
        self.assertEqual([x['damage'] for x in ticks],[5]*6)
    def test_tristana_bomb_expiry_is_scheduled_damage(self):
        r=fight('Tristana',events=[FightEvent(0,'E')],automatic_until=5)
        det=next(x for x in r.log if x['action']=='E detonation')
        from sharpwr.combat_timing import attack_windup
        self.assertAlmostEqual(det['time'],4+attack_windup('Tristana',1)+550/2400);self.assertGreater(det['damage'],0)
    def test_vayne_three_eligible_hits_trigger_true_damage(self):
        r=fight('Vayne',events=[FightEvent(0,'AA'),FightEvent(1,'AA'),FightEvent(2,'AA')],automatic_until=3,crit_chance=0)
        aa=[x for x in r.log if x['action']=='AA']
        self.assertEqual([x['true'] for x in aa],[0,0,900])
    def test_lucian_secondary_shot_is_not_a_second_aa_command(self):
        r=fight('Lucian',events=[FightEvent(0,'E'),FightEvent(.4,'AA')],automatic_until=1)
        self.assertEqual(r.aa_count,1)
        self.assertEqual([x['action'] for x in r.log],['AA','AA second'])
    def test_miss_fortune_channel_blocks_basic_attacks(self):
        r=fight('Miss Fortune',events=[FightEvent(0,'R'),FightEvent(1,'AA'),FightEvent(3.1,'AA')],automatic_until=4)
        self.assertEqual(r.aa_count,1);self.assertEqual(len([x for x in r.log if x['action'].startswith('R')]),16)
        self.assertTrue(any(x['action']=='AA' and x['time']==1 for x in r.rejected))
    def test_jhin_reload_requires_elapsed_time(self):
        r=fight('Jhin',events=[FightEvent(t,'AA') for t in (0,2,4,6,7,9)],automatic_until=10,natural_attack_speed=.7)
        self.assertEqual(r.aa_count,5)
        times=[x['time'] for x in r.log if x['action']=='AA']
        self.assertTrue(all(a>b for a,b in zip(times,(0,2,4,6,9))))
    def test_yunara_ultimate_free_skills_and_automatic_q(self):
        r=fight('Yunara',events=[FightEvent(0,'R'),FightEvent(1,'W'),FightEvent(2,'AA')],automatic_until=3,max_mana=100,mana_regen_per_5s=0)
        self.assertTrue(all(x['mana']==0 for x in r.log));self.assertGreater(next(x['magic'] for x in r.log if x['action']=='W'),0)
        self.assertGreater(next(x['magic'] for x in r.log if x['action']=='AA'),0)
    def test_zeri_cap_and_conversion_change_damage(self):
        base=fight('Zeri',starting_bonus_as=0,automatic_until=10,r_rank=0)
        high=fight('Zeri',starting_bonus_as=4,automatic_until=10,r_rank=0)
        self.assertLessEqual(high.aa_count,16)
        self.assertGreater(next(x['AD'] for x in high.log if x['action']=='AA'),next(x['AD'] for x in base.log if x['action']=='AA'))
    def test_kaisa_isolated_missiles_evolve_from_completed_items(self):
        non=fight("Kai'Sa",events=[FightEvent(0,'Q')],automatic_until=1,completed_items=0)
        evolved=fight("Kai'Sa",events=[FightEvent(0,'Q')],automatic_until=1,completed_items=3)
        self.assertAlmostEqual(evolved.log[0]['physical']/non.log[0]['physical'],3.75/2.25)
    def test_ezreal_flux_is_consumed_once(self):
        r=fight('Ezreal',events=[FightEvent(0,'W'),FightEvent(1,'Q'),FightEvent(2,'AA')],automatic_until=3)
        self.assertEqual(len([x for x in r.log if x['action']=='W detonation']),1)
    def test_repeat_fights_are_deterministic(self):
        for n in PENDING:
            self.assertEqual(fight(n).log,fight(n).log)

if __name__=='__main__':unittest.main()
