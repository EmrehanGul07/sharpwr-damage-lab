import re
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest

ROOT=Path(__file__).resolve().parents[1]

class LegalNoticeTests(unittest.TestCase):
    def test_riot_notice_is_shown_and_matches_readme(self):
        notice=re.search(r'^RIOT_NOTICE="(.+)"$',(ROOT/'streamlit_app.py').read_text(),re.M).group(1)
        readme=(ROOT/'README.md').read_text()
        self.assertEqual(readme.split('## Legal\n',1)[1].strip(),notice)
        app=AppTest.from_file(str(ROOT/'streamlit_app.py'),default_timeout=60).run()
        self.assertFalse(app.exception)
        self.assertIn(notice,[caption.value for caption in app.caption])

if __name__=='__main__':
    unittest.main()
