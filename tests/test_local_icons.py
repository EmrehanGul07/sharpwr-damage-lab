import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

def _app_dict(name):
    for node in ast.parse((ROOT/'streamlit_app.py').read_text()).body:
        if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):
            return ast.literal_eval(node.value)
    raise KeyError(name)

class LocalIconTests(unittest.TestCase):
    def test_every_local_icon_file_exists(self):
        # A missing file silently renders an empty icon, so check every mapped path.
        paths=list(_app_dict('LOCAL_ITEM_ICON').values())+['assets/riot/items/'+name for name in _app_dict('BOOT_ICON_FILE').values()]
        self.assertTrue(paths)
        for path in paths:
            self.assertTrue(path.startswith('assets/riot/'),path)
            self.assertTrue((ROOT/path).is_file(),path)

if __name__=='__main__':
    unittest.main()
