import sys,unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from marksman_kits import PRIORITIES

class AllMarksmanUI(unittest.TestCase):
    def test_all_twenty_three_champions_can_replay_from_build_lab(self):
        a=AppTest.from_file(str(ROOT/'streamlit_app.py'),default_timeout=60).run()
        self.assertFalse(a.exception)
        a.slider(key='build_level').set_value(15).run()
        a.radio(key='build_target_profile').set_value('Tank • Ornn').run()
        a.button(key='build_keystone__7__Conqueror').click().run()
        for name in PRIORITIES:
            with self.subTest(champion=name):
                a.selectbox(key='build_champ').set_value(name).run()
                self.assertFalse(a.exception,[x.message for x in a.exception])
                self.assertFalse(a.button(key='fight_calculate').disabled)
                a.button(key='fight_calculate').click().run()
                self.assertFalse(a.exception,[x.message for x in a.exception])
                self.assertFalse(a.error,[x.value for x in a.error])
                table=next(x.value for x in a.dataframe if 'Stacks after' in x.value.columns)
                self.assertGreater(len(table),0)
                self.assertTrue((table['Damage']>=0).all())
                self.assertEqual(table['Target HP'].iloc[-1],0)
                self.assertFalse(any('not available yet' in x.value for x in a.info))
    def test_unlearned_skills_at_level_one_do_not_crash(self):
        a=AppTest.from_file(str(ROOT/'streamlit_app.py'),default_timeout=60).run()
        a.slider(key='build_level').set_value(1).run()
        a.button(key='build_keystone__7__Conqueror').click().run()
        for name in PRIORITIES:
            with self.subTest(champion=name):
                a.selectbox(key='build_champ').set_value(name).run()
                a.button(key='fight_calculate').click().run()
                self.assertFalse(a.exception,[x.message for x in a.exception])
                self.assertFalse(a.error,[x.value for x in a.error])

if __name__=='__main__':unittest.main()
