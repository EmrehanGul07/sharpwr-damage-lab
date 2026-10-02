import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
import build_fight_optimizer as optimizer

class TierFightUI(unittest.TestCase):
    def test_real_fight_search_renders_three_full_builds_then_four_top_tens(self):
        from engine_runtime import ensure_engine_revision
        ensure_engine_revision("5.85.0")
        original=optimizer.search_builds
        def bounded(evaluator,pool,boots,**kwargs):
            return original(evaluator,['Muramana',"Nashor's Tooth",'Infinity Edge','Phantom Dancer','Statikk Shiv',"Guinsoo's Rageblade"],boots[:2],beam_width=8,refine_count=4,progress=kwargs.get('progress'))
        with patch.object(optimizer,'search_builds',side_effect=bounded):
            app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'streamlit_app.py'),default_timeout=60).run()
            app.selectbox(key='tier_champ').set_value('Ezreal').run()
            app.slider(key='tier_level').set_value(15).run()
            app.button(key='tiercalc').click().run()
            self.assertFalse(app.exception,[x.message for x in app.exception]);self.assertFalse(app.error)
            tables=[x.value for x in app.dataframe if 'Abilities / passives' in x.value.columns]
            self.assertEqual(len(tables),5);self.assertEqual(len(tables[0]),3)
            self.assertTrue(all(len(t)<=10 for t in tables[1:]))
            self.assertTrue((tables[0]['Abilities / passives']>0).all())
            self.assertIn('FINAL IDEAL BUILD',' '.join(x.value for x in app.markdown))
            before=app.session_state['tier_fight_results']['results']['simulations']
            app.run();self.assertFalse(app.exception)
            self.assertEqual(before,app.session_state['tier_fight_results']['results']['simulations'])
            app.slider(key='tier_level').set_value(14).run()
            self.assertFalse(any('Abilities / passives' in x.value.columns for x in app.dataframe))

if __name__=='__main__':unittest.main()
