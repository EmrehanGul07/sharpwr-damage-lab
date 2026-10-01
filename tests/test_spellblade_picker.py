import unittest
from streamlit.testing.v1 import AppTest
from build_fight_optimizer import legal

class SpellbladePicker(unittest.TestCase):
    def test_exclusive_search_group(self):
        for pair in [('Trinity Force','Essence Reaver'),('Essence Reaver','Iceborn Gauntlet'),('Trinity Force','Iceborn Gauntlet')]:self.assertFalse(legal(pair))
    def test_equipping_locks_others_removing_unlocks(self):
        app=AppTest.from_file('streamlit_app.py',default_timeout=60)
        app.session_state['build_items_v2']=['Essence Reaver'];app.run()
        self.assertFalse(app.exception)
        locked=[x for x in app.button if x.label=='Spellblade locked']
        self.assertEqual(len(locked),2);self.assertTrue(all(x.disabled for x in locked))
        keys=[x.key for x in locked]
        app.button(key='remove_item_0').click().run()
        self.assertFalse(app.exception)
        self.assertTrue(all(not app.button(key=k).disabled for k in keys))
    def test_old_illegal_state_retains_only_first_spellblade(self):
        app=AppTest.from_file('streamlit_app.py',default_timeout=60)
        app.session_state['build_items_v2']=['Essence Reaver','Trinity Force','Iceborn Gauntlet'];app.run()
        self.assertFalse(app.exception)
        self.assertEqual(app.session_state['build_items_v2'],['Essence Reaver'])

if __name__=='__main__':unittest.main()
