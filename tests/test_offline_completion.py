import json
import math
from pathlib import Path
import subprocess
import tempfile
import shutil
import unittest

from rune_runtime import persistent_stats, own_stats, FirstContact, DamageProcs
from fight_engine import FightEvent, replay_samira
from sharpwr import engine_namespace
from build_fight_optimizer import BuildFightEvaluator, search_builds

ROOT=Path(__file__).resolve().parents[1]

class OfflineCompletion(unittest.TestCase):
    def test_rune_stats_and_full_champion_health(self):
        runes=persistent_stats(15,{'Zombie Ward','Eyeball Collection','Manaflow Band','Overgrowth','Unshakeable','Gathering Storm'},dict(eyeball_stacks=4,overgrowth_stacks=60,nearby_enemies=2,game_minute=15))
        self.assertEqual(runes['ad'],35)
        self.assertEqual(runes['mana'],300)
        own=own_stats(dict(hp=2000,armor=100,mr=50),dict(hp=500,armor=40,mr=20),runes)
        self.assertAlmostEqual(own['hp'],2680*1.03)
        self.assertAlmostEqual(own['armor'],140*1.07)
        self.assertIsNone(own_stats(dict(hp=None,armor=None,mr=None),{},runes)['hp'])
    def test_first_contact_uses_first_damage_time_and_excludes_boundary(self):
        rune=FirstContact(True)
        self.assertEqual(rune.apply(0,0)[0],0)
        self.assertAlmostEqual(rune.apply(2,100)[0],107)
        self.assertAlmostEqual(rune.apply(4.999,100)[0],107)
        self.assertEqual(rune.apply(5,100)[0],100)
        self.assertEqual(FirstContact(True,False).apply(1,100)[0],100)
    def test_first_strike_and_last_stand_all_adapter_paths(self):
        for champion in ('Samira','Smolder','Ezreal'):
            args=dict(champion=champion,level=15,ad=100,base_ad=60,attack_speed=1,crit_chance=0,crit_damage=2,hp=10000,armor=100,mr=100,q_rank=0,w_rank=0,e_rank=0,r_rank=0,automatic_until=5,distance=200)
            events=[FightEvent(1,'AA'),FightEvent(2,'AA'),FightEvent(4,'AA')]
            plain=replay_samira(events,**args)
            strike=replay_samira(events,**args,keystone='First Strike')
            stand=replay_samira(events,**args,sub_runes=['Last Stand'],own_hp_pct=40)
            with self.subTest(champion=champion):
                for a,b in zip(plain.log,strike.log):
                    self.assertAlmostEqual(b['damage'],a['damage']*(1.07 if b['time']<strike.log[0]['time']+3-1e-9 else 1))
                for a,b in zip(plain.log,stand.log):self.assertAlmostEqual(b['damage'],a['damage']*1.11)
                self.assertAlmostEqual(strike.total_damage,10000-strike.hp_remaining)
    def test_damage_procs_threshold_cooldown_and_souls(self):
        procs=DamageProcs(15,'Dark Harvest',['Tyrant','Empowered Attack'],2)
        damage,notes,parts=procs.apply(0,'AA',.5,100,50,100)
        self.assertAlmostEqual(damage,24)
        self.assertEqual(len(parts),1)
        damage,notes,parts=procs.apply(1,'Q',.49,100,50,100)
        self.assertAlmostEqual(damage,(35+22+10+2.5+70+6+1.5)/2)
        self.assertEqual(procs.souls,3)
        self.assertEqual(procs.apply(2,'Q',.49,100,50,100)[0],0)
        self.assertGreater(procs.apply(21,'Q',.49,100,50,100)[0],0)
        self.assertEqual(procs.souls,4)
    def test_first_strike_has_separate_true_damage_component(self):
        for champion in ('Samira','Smolder','Ezreal'):
            result=replay_samira([FightEvent(0,'AA')],champion=champion,level=15,ad=100,attack_speed=1,crit_chance=0,crit_damage=2,hp=10000,armor=100,mr=100,q_rank=0,w_rank=0,e_rank=0,r_rank=0,automatic_until=1,keystone='First Strike')
            parts=[p for p in result.log[0]['damage_components'] if p.get('component')=='First Strike rune bonus']
            self.assertEqual(len(parts),1)
            self.assertEqual(parts[0]['damage_type'],'true')
            self.assertGreater(parts[0]['raw_amount'],0)
    def test_initial_spellblade_ready_survives_event_driven_attack(self):
        ns=engine_namespace()
        def hit(ready):
            kernel=ns['combat_hits']('Ezreal',15,10000,100,100,['Trinity Force'],ns['F'],spell=ready);next(kernel)
            return kernel.send({'hp':10000,'time':0.,'event_driven':True,'spell_cast_times':[]})
        self.assertIn('Trinity',hit(True)['notes'])
        self.assertNotIn('Trinity',hit(False)['notes'])
    def test_deployed_revision_refreshes_cached_core_module(self):
        import core_items
        from engine_runtime import ensure_engine_revision
        old=core_items.SOURCE_FILES
        try:
            core_items.SOURCE_FILES=('stale-module-sentinel',)
            ensure_engine_revision('core-hot-reload-regression')
            self.assertIn('rune_runtime.py',core_items.SOURCE_FILES)
            self.assertIsNotNone(core_items.core_record('Ezreal'))
        finally:
            core_items.SOURCE_FILES=old
            ensure_engine_revision('5.87.1')
    def test_unknown_runes_never_silently_disappear(self):
        with self.assertRaises(ValueError):
            replay_samira([],champion='Ezreal',level=15,ad=100,attack_speed=1,crit_chance=0,crit_damage=2,hp=1000,armor=100,sub_runes=['Scorch'])
    def test_invalid_kernel_inputs_and_live_states(self):
        ns=engine_namespace()
        for field,value in [('hp0',0),('hp0',math.nan),('dist',math.inf),('l',True),('l',1.5),('base_mana',-1),('target_aa_reduction',1.1)]:
            args=dict(n='Ezreal',l=15,hp0=10000,arm=100,mr=100,items=[],db=ns['F'])|{field:value}
            with self.subTest(field=field),self.assertRaises(ValueError):next(ns['combat_hits'](**args))
        kernel=ns['combat_hits']('Ezreal',15,10000,100,100,[],ns['F']);next(kernel)
        kernel.send(dict(hp=10000,time=1))
        with self.assertRaises(ValueError):kernel.send(dict(hp=10000,time=0))
    def test_optimizer_rejects_duplicates_unknowns_and_invalid_budget_controls(self):
        ns=engine_namespace();ev=BuildFightEvaluator(ns,'Ezreal',15,10000,100,100)
        for items,boot in [(['Infinity Edge']*2,None),(['unknown'],None),(['Infinity Edge'],'unknown')]:
            with self.assertRaises(ValueError):ev.evaluate(items,boot)
        for controls in [dict(beam_width=0),dict(refine_count=-1),dict(beam_width=True)]:
            with self.assertRaises(ValueError):search_builds(ev,['Infinity Edge'],['Gunmetal Greaves'],max_items=1,**controls)
    def test_catalogue_rebuild_preserves_every_authoritative_field(self):
        # A real isolated rebuild checks later confirmations, classification,
        # source metadata and unparsed fields, rather than mirroring a merge.
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'scripts').mkdir();(root/'data').mkdir()
            shutil.copy(ROOT/'scripts/build_marksman_catalogue.py',root/'scripts')
            shutil.copy(ROOT/'champion_skill_data.py',root)
            for name in ('marksman-ability-evidence.json','marksman-implementation-queue.json','marksman-ability-catalogue.json'):
                shutil.copy(ROOT/'data'/name,root/'data'/name)
            before=json.loads((root/'data/marksman-ability-catalogue.json').read_text())
            subprocess.run(['python',str(root/'scripts/build_marksman_catalogue.py')],check=True,capture_output=True)
            after=json.loads((root/'data/marksman-ability-catalogue.json').read_text())
            for champion,record in before['champions'].items():
                for slot,ability in record['abilities'].items():
                    for field,value in ability.items():
                        if field not in ('observations','source_keys'):
                            self.assertEqual(after['champions'][champion]['abilities'][slot][field],value,(champion,slot,field))

if __name__=='__main__':unittest.main()
