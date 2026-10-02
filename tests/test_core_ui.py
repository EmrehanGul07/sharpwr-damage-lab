import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
class CoreUI(unittest.TestCase):
 def test_champion_profile_displays_core_name_and_icon(self):
  result={'complete':True,'ranking':[{'Item':'Muramana','Score':90.},{'Item':'Trinity Force','Score':80.}]}
  with patch('core_items.core_record',return_value=result):
   app=AppTest.from_file(str(Path(__file__).resolve().parents[1]/'streamlit_app.py'),default_timeout=60).run()
   app.selectbox(key='tier_champ').set_value('Ezreal').run()
   self.assertFalse(app.exception)
   cards=[x.value for x in app.markdown if 'CORE ITEM</span>' in x.value]
   self.assertTrue(cards);self.assertTrue(any('alt="Muramana"' in x and '<b>Muramana</b>' in x for x in cards))
