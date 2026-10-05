import sys
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))

class InterfaceTests(unittest.TestCase):
    def setUp(self):self.app=AppTest.from_file(str(ROOT/'streamlit_app.py'),default_timeout=60).run();self.assertFalse(self.app.exception)
    def test_tab_state_survives_item_and_rune_rerun(self):
        a=self.app
        for key,value in [('tier_champ','Samira'),('build_champ','Smolder'),('iv_champ','Twitch')]:a.selectbox(key=key).set_value(value).run()
        for key,value in [('tier_level',1),('build_level',15),('iv_level',8)]:a.slider(key=key).set_value(value).run()
        a.radio(key='tier_target').set_value('Tank • Ornn').run()
        a.radio(key='build_target_profile').set_value('Bruiser • Darius').run()
        a.button(key='remove_item_0').click().run()
        self.assertEqual(len(a.session_state['build_items_v2']),4)
        a.button(key='native_item_0').click().run()
        a.button(key='build_keystone__7__Conqueror').click().run()
        self.assertFalse(a.exception)
        self.assertEqual([a.selectbox(key=k).value for k in ['tier_champ','build_champ','iv_champ']],['Samira','Smolder','Twitch'])
        self.assertEqual([a.slider(key=k).value for k in ['tier_level','build_level','iv_level']],[1,15,8])
        self.assertTrue(all(b.disabled for b in a.button if b.key and b.key.startswith('native_item_')))
        next(b for b in a.button if b.label=='Calculate build').click().run()
        self.assertFalse(a.exception)
        self.assertTrue(a.button(key='tiercalc').disabled)
    def test_samira_skill_panel(self):
        a=self.app
        a.selectbox(key='build_champ').set_value('Samira').run()
        self.assertFalse(a.exception)
        self.assertFalse(any(x.key and x.key.startswith('ability_samira_') for x in a.selectbox))
        self.assertFalse(any(x.key in ('fight_auto','fight_melee') for x in a.checkbox))
        a.slider(key='build_level').set_value(1).run()
        self.assertFalse(any('Outcome' in x.value.columns for x in a.dataframe))
        self.assertFalse(any(x.key in ('fight_override_crit','fight_seed','fight_base_crit') for x in list(a.checkbox)+list(a.number_input)))
        self.assertFalse(any(x.key=='fight_crit_mode' for x in a.selectbox))
        a.selectbox(key='build_champ').set_value('Smolder').run()
        self.assertFalse(any('Outcome' in x.value.columns for x in a.dataframe))

    def test_fight_timeline_replay(self):
        a=self.app
        a.selectbox(key='build_champ').set_value('Samira').run()
        a.button(key='build_keystone__7__Conqueror').click().run()
        a.button(key='fight_calculate').click().run()
        self.assertFalse(a.exception)
        table=next(x.value for x in a.dataframe if 'Stacks after' in x.value.columns)
        self.assertGreater(len(table),3)
        self.assertGreater(table['AD'].iloc[2],table['AD'].iloc[0])
        self.assertTrue(all(0<=x<=100 for x in table['Crit %']))
        self.assertNotIn('Critical roll',table.columns)
        self.assertEqual(table['Target HP'].iloc[-1],0)
        self.assertTrue(any('Target defeated' in x.value for x in a.success))
        self.assertIn('Melee',set(table['Range']))
        self.assertTrue(set(table['Range']).issubset({'Melee','Ranged'}))

    def test_smolder_fight_panel_and_optimized_kite(self):
        a=self.app
        a.selectbox(key='build_champ').set_value('Smolder').run()
        a.radio(key='build_target_profile').set_value('Tank • Ornn').run()
        a.number_input(key='smolder_fight_stacks').set_value(175).run()
        a.button(key='build_keystone__7__Conqueror').click().run()
        a.button(key='fight_calculate').click().run()
        self.assertFalse(a.exception)
        self.assertFalse(a.error)
        table=next(x.value for x in a.dataframe if 'Dragon stacks' in x.value.columns)
        self.assertEqual(table['Target HP'].iloc[-1],0)
        self.assertGreater(table['Dragon stacks'].iloc[-1],175)
        from sharpwr.champion_database import level_stats
        max_range=level_stats('Smolder',15)['attack_range']
        self.assertTrue(all(550<=x<=max_range for x in table['Distance']))
        self.assertIn('Q',set(table['Event']))

    def test_champion_database_fields(self):
        a=self.app
        a.radio(key='db_category').set_value('Champions').run()
        a.text_input(key='db_champion_search').set_value('Samira').run()
        self.assertFalse(a.exception)
        table=next(x.value for x in a.dataframe if 'base_mana' in x.value.columns)
        self.assertEqual(len(table),1)
        self.assertEqual(table['base_ad'].iloc[0],60)
        self.assertEqual(table['base_mana'].iloc[0],345)
        a.text_input(key='db_champion_search').set_value('Yunara').run()
        self.assertFalse(a.exception)
        self.assertTrue(any('manual core data at all 15 levels' in x.value for x in a.info))
        observed=next(x.value for x in a.dataframe if 'mana_regen_per_5s' in x.value.columns)
        self.assertEqual(len(observed),15)
        self.assertEqual(observed.loc[observed['Level']=='15','mana'].iloc[0],807)

    def test_keystone_calculations(self):
        a=self.app
        for i,name in enumerate(['First Strike','Ice Overlord','Phase Rush','Arcane Comet','Aery','Guardian','Grasp of the Undying','Conqueror','Fleet Footwork','Lethal Tempo','Empowerment','Dark Harvest']):
            with self.subTest(keystone=name):
                a.button(key=f'build_keystone__{i}__{name}').click().run()
                next(b for b in a.button if b.label=='Calculate build').click().run()
                self.assertFalse(a.exception,[e.message for e in a.exception])
                a.button(key='remove_build_keystone').click().run()

if __name__=='__main__':unittest.main()
