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

class NewUserRules(unittest.TestCase):
    def test_galeforce_cannot_hit_beyond_dash_plus_six_hundred(self):
        r=replay_samira([FightEvent(0,'AA')],champion='Ezreal',level=15,ad=200,base_ad=100,attack_speed=.7,crit_chance=0,crit_damage=2,hp=100000,armor=100,mr=100,q_rank=0,w_rank=0,e_rank=0,r_rank=0,automatic_until=1,distance=1000,attack_range=550,movement_speed=0,galeforce=True)
        self.assertFalse(any(x['action']=='Galeforce active' for x in r.log))
    def test_galeforce_dash_is_bounded_and_hits_inside_six_hundred(self):
        r=replay_samira([FightEvent(0,'AA')],champion='Ezreal',level=15,ad=200,base_ad=100,attack_speed=.7,crit_chance=0,crit_damage=2,hp=100000,armor=100,mr=100,q_rank=0,w_rank=0,e_rank=0,r_rank=0,automatic_until=1,distance=900,attack_range=550,movement_speed=0,galeforce=True)
        hit=next(x for x in r.log if x['action']=='Galeforce active')
        self.assertEqual(hit['distance'],575)
    def test_skill_cost_awe_refund_and_current_mana_reach_kernel(self):
        ns=engine_namespace();k=ns['_combat_hits']('Ezreal',15,100000,100,100,['Muramana'],ns['F']);next(k);seen=[]
        def hit(state):seen.append((state['mana'],state['max_mana']));return k.send(state)
        r=replay_samira([FightEvent(0,'Q'),FightEvent(1,'AA')],champion='Ezreal',level=15,ad=200,base_ad=100,attack_speed=.7,crit_chance=0,crit_damage=2,hp=100000,armor=100,mr=100,q_rank=1,w_rank=0,e_rank=0,r_rank=0,automatic_until=2,max_mana=1000,mana_regen_per_5s=0,mana_refund=.15,muramana=True,aa_hit=hit)
        self.assertTrue(seen);self.assertTrue(all(maxmana==1000 for mana,maxmana in seen))
        self.assertLess(seen[0][0],1000)
        self.assertEqual(seen[0][0],r.log[0]['mana'])
        self.assertTrue(all(mana==seen[0][0] for mana,maxmana in seen))

class OnHitAuditRegression(unittest.TestCase):
    def test_onhit_skill_does_not_consume_attack_only_buffs(self):
        ns=engine_namespace();k=ns['_combat_hits']('Ezreal',15,10000,100,100,['Phantom Dancer','Yun Tal Wildarrows','Fiendhunter Bolts','Duskblade of Draktharr'],ns['F']);next(k)
        q=k.send({'hp':10000,'time':0,'event_driven':True,'skill_on_hit':True,'attack_physical':0,'ultimate_cast_time':0})
        self.assertEqual(q['phantom_dancer'],1);self.assertEqual(q['yuntal_crit'],0);self.assertEqual(q['fiend_remaining'],3)
        self.assertNotIn('Nightstalker',q['notes']);self.assertNotIn('Opening Barrage',q['notes'])
        aa=k.send({'hp':10000,'time':1,'event_driven':True,'ultimate_cast_time':0})
        self.assertEqual(aa['phantom_dancer'],2);self.assertAlmostEqual(aa['yuntal_crit'],.002);self.assertEqual(aa['fiend_remaining'],2)
        self.assertIn('Nightstalker',aa['notes']);self.assertIn('Opening Barrage',aa['notes'])
    def test_muramana_skill_shock_once_with_phantom(self):
        ns=engine_namespace();k=ns['_combat_hits']('Ezreal',15,10000,100,100,['Muramana',"Guinsoo's Rageblade"],ns['F']);next(k)
        r=replay_samira([FightEvent(i*7,'Q') for i in range(6)],champion='Ezreal',level=15,ad=100,base_ad=60,ap=0,attack_speed=1,crit_chance=0,crit_damage=2,hp=10000,armor=100,mr=100,q_rank=1,w_rank=0,e_rank=0,r_rank=0,max_mana=1000,mana_regen_per_5s=10,automatic_until=40,muramana=True,aa_hit=lambda state:k.send(state))
        self.assertEqual(len(r.log),6)
        for row in r.log:
            shocks=[c for c in row['damage_components'] if c.get('component')=='Muramana skill Shock']
            self.assertEqual(len(shocks),1);self.assertEqual(shocks[0]['raw_amount'],30)
        self.assertIn('Phantom Hit',r.log[-1]['effects'])
    def test_smolder_q_uses_new_terminus_physical_penetration(self):
        ns=engine_namespace();k=ns['_combat_hits']('Smolder',15,10000,100,100,['Terminus'],ns['F']);next(k)
        r=replay_samira([FightEvent(0,'Q'),FightEvent(7,'Q')],champion='Smolder',level=15,ad=100,base_ad=60,ap=0,attack_speed=1,crit_chance=0,crit_damage=2,hp=10000,armor=100,mr=100,q_rank=1,w_rank=0,e_rank=0,r_rank=0,automatic_until=10,terminus=True,aa_hit=lambda state:k.send(state))
        row=r.log[1];skill=[c for c in row['damage_components'] if c.get('tags')==['ActiveSpell','BasicAttack']]
        physical=sum(c['raw_amount'] for c in skill if c['damage_type']=='physical');magic=sum(c['raw_amount'] for c in skill if c['damage_type']=='magic')
        self.assertGreater(physical,0)
        self.assertAlmostEqual(row['damage'],(physical+magic)/1.9+15.)

class EssenceReaverCarrierCrit(unittest.TestCase):
    def test_zero_carrier_crit_retains_build_crit_for_er(self):
        ns=engine_namespace()
        for name in ('Ezreal','Smolder'):
            with self.subTest(champion=name):
                k=ns['_combat_hits'](name,15,10000,100,100,['Essence Reaver'],ns['F']);next(k)
                h=k.send({'hp':10000,'time':0,'event_driven':True,'skill_on_hit':True,'spell_cast':True,'crit':0.,'attack_physical':0.})
                self.assertAlmostEqual(h['physical'],1.35*ns['stats'](name,15)['basead']+20.)
                self.assertEqual(h['crit'],0.)
    def test_carrier_explicit_crit_uses_current_yuntal_progression(self):
        ns=engine_namespace();k=ns['_combat_hits']('Ezreal',15,10000,100,100,['Essence Reaver'],ns['F']);next(k)
        h=k.send({'hp':10000,'time':0,'event_driven':True,'skill_on_hit':True,'spell_cast':True,'crit':0.,'spellblade_crit':.5,'attack_physical':0.})
        self.assertAlmostEqual(h['physical'],1.35*ns['stats']('Ezreal',15)['basead']+40.)
    def test_q_adapter_forwards_spellblade_crit_independently(self):
        ns=engine_namespace()
        for name in ('Ezreal','Smolder'):
            with self.subTest(champion=name):
                seen=[];k=ns['_combat_hits'](name,15,10000,100,100,['Essence Reaver'],ns['F']);next(k)
                def hit(state):seen.append(state);return k.send(state)
                r=replay_samira([FightEvent(0,'Q')],champion=name,level=15,ad=100,base_ad=60,attack_speed=1,crit_chance=.75,crit_damage=2,hp=10000,armor=100,mr=100,q_rank=1,w_rank=0,e_rank=0,r_rank=0,automatic_until=3,aa_hit=hit)
                carriers=[s for s in seen if s.get('skill_on_hit')]
                self.assertEqual(len(carriers),1);self.assertEqual(carriers[0]['crit'],0.);self.assertEqual(carriers[0]['spellblade_crit'],.75)
                self.assertIn('ER',r.log[0]['effects'])
