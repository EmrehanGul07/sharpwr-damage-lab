import re
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class VersionTests(unittest.TestCase):
    def test_version_has_a_single_source(self):
        version=(ROOT/'VERSION').read_text().strip()
        self.assertRegex(version,r'^\d+\.\d+\.\d+$')
        self.assertEqual((ROOT/'README.md').read_text().splitlines()[0],f'# SharpWR Damage Lab — V{version}')
        app=(ROOT/'streamlit_app.py').read_text()
        self.assertIn('ensure_engine_revision(APP_VERSION)',app)
        self.assertIn('st.caption(f"Web V{APP_VERSION} | ',app)
        self.assertIsNone(re.search(r'ensure_engine_revision\("',app))

if __name__=='__main__':
    unittest.main()
