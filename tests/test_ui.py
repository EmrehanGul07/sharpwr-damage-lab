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
        a.button(key='tiercalc').click().run();self.assertFalse(a.exception)
    def test_samira_skill_panel(self):
        a=self.app
        a.selectbox(key='build_champ').set_value('Samira').run()
        self.assertFalse(a.exception)
        self.assertFalse(any(x.key and x.key.startswith('ability_samira_') for x in a.selectbox))
        self.assertFalse(any(x.key in ('fight_auto','fight_melee') for x in a.checkbox))
        a.slider(key='build_level').set_value(1).run()
        table=next(x.value for x in a.dataframe if 'Outcome' in x.value.columns)
        self.assertTrue(all(x.startswith('Q') for x in table['Ability']))
        a.slider(key='build_level').set_value(15).run()
        table=next(x.value for x in a.dataframe if 'Outcome' in x.value.columns)
        self.assertEqual({x[0] for x in table['Ability']},{'Q','W','E','R'})
        a.selectbox(key='build_champ').set_value('Smolder').run()
        self.assertFalse(any('Outcome' in x.value.columns for x in a.dataframe))

    def test_fight_timeline_replay(self):
        a=self.app
        a.selectbox(key='build_champ').set_value('Samira').run()
        a.checkbox(key='fight_override_crit').set_value(True).run()
        a.number_input(key='fight_base_crit').set_value(50).run()
        a.button(key='build_keystone__7__Conqueror').click().run()
        a.button(key='fight_calculate').click().run()
        self.assertFalse(a.exception)
        table=next(x.value for x in a.dataframe if 'Stacks after' in x.value.columns)
        self.assertGreater(len(table),3)
        self.assertGreater(table['AD'].iloc[2],table['AD'].iloc[0])
        self.assertTrue(all(x==50 for x in table['Crit %']))
        self.assertEqual(table['Target HP'].iloc[-1],0)
        self.assertTrue(any('Target defeated' in x.value for x in a.success))
        self.assertTrue(all(x=='Melee' for x in table['Range']))

    def test_keystone_calculations(self):
        a=self.app
        for i,name in enumerate(['First Strike','Ice Overlord','Phase Rush','Arcane Comet','Aery','Guardian','Grasp of the Undying','Conqueror','Fleet Footwork','Lethal Tempo','Empowerment','Dark Harvest']):
            with self.subTest(keystone=name):
                a.button(key=f'build_keystone__{i}__{name}').click().run()
                next(b for b in a.button if b.label=='Calculate build').click().run()
                self.assertFalse(a.exception,[e.message for e in a.exception])
                a.button(key='remove_build_keystone').click().run()

if __name__=='__main__':unittest.main()
