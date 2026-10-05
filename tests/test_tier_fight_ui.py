import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from sharpwr import build_fight_optimizer as optimizer

class TierFightUI(unittest.TestCase):
    def test_public_search_is_disabled_and_cannot_be_triggered(self):
        with patch.object(optimizer,'search_builds',side_effect=AssertionError('Published tier board must not start a search')):
            app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'streamlit_app.py'),default_timeout=60).run()
            for key in ('tiercalc','compare_all_profiles'):
                self.assertTrue(app.button(key=key).disabled)
                # AppTest can synthesize clicks even on disabled controls.
                app.button(key=key).click().run()
                self.assertFalse(app.exception,[x.message for x in app.exception])
                self.assertFalse(app.error)
            self.assertNotIn('tier_fight_results',app.session_state)
            self.assertNotIn('tier_comparison',app.session_state)

if __name__=='__main__':unittest.main()
