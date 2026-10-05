"""The damage engine stays independent of the Streamlit UI (required for the mobile app)."""
import ast
import unittest
from pathlib import Path

import sharpwr

ROOT = Path(__file__).resolve().parents[1]


def _imported_modules(path):
    names = set()
    for node in ast.walk(ast.parse(path.read_text())):
        if isinstance(node, ast.Import):
            names.update(alias.name.split('.')[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            names.add(node.module.split('.')[0])
    return names


class EnginePackageTests(unittest.TestCase):
    def test_engine_does_not_import_the_ui(self):
        for path in (ROOT / 'sharpwr').glob('*.py'):
            self.assertNotIn('streamlit', _imported_modules(path), path.name)

    def test_app_does_not_redefine_engine_names(self):
        app = ast.parse((ROOT / 'streamlit_app.py').read_text())
        defined = {node.name for node in app.body if isinstance(node, ast.FunctionDef)}
        defined |= {t.id for node in app.body if isinstance(node, ast.Assign) for t in node.targets if isinstance(t, ast.Name)}
        self.assertFalse(defined & set(sharpwr.ENGINE_NAMES))

    def test_namespace_is_complete_and_fresh(self):
        first, second = sharpwr.engine_namespace(), sharpwr.engine_namespace()
        self.assertEqual(set(first), set(sharpwr.ENGINE_NAMES))
        self.assertIsNot(first, second)
        self.assertIs(first['combat_hits'], sharpwr.combat_hits)


if __name__ == '__main__':
    unittest.main()
