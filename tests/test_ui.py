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
    def test_keystone_calculations(self):
        a=self.app
        for i,name in enumerate(['First Strike','Ice Overlord','Phase Rush','Arcane Comet','Aery','Guardian','Grasp of the Undying','Conqueror','Fleet Footwork','Lethal Tempo','Empowerment','Dark Harvest']):
            with self.subTest(keystone=name):
                a.button(key=f'build_keystone__{i}__{name}').click().run()
                next(b for b in a.button if b.label=='Calculate build').click().run()
                self.assertFalse(a.exception,[e.message for e in a.exception])
                a.button(key='remove_build_keystone').click().run()

if __name__=='__main__':unittest.main()
