import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_ownership as co  # noqa: E402


class Ownership(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = co.load()

    def test_repository_map_is_exclusive(self):
        self.assertEqual(co.check_map(self.data, co.repo_files()), [])

    def test_glob(self):
        self.assertTrue(co.glob_regex("game/unity/Assets/**").match("game/unity/Assets/A/b.cs"))
        self.assertTrue(co.glob_regex("docs/moba/*.md").match("docs/moba/01-architecture.md"))
        self.assertFalse(co.glob_regex("docs/moba/*.md").match("docs/moba/adr/0001.md"))
        self.assertTrue(co.glob_regex(".github/workflows/game-*.yml").match(".github/workflows/game-ci.yml"))

    def test_expected_owners(self):
        cases = {
            "game/packages/com.sharpwr.sim/Runtime/Numerics/Fix64.cs": ["combat-engineer"],
            "game/packages/com.sharpwr.sim/Runtime/Abilities/AbilityDefinition.cs": ["champion-implementer"],
            "game/packages/com.sharpwr.sim/Runtime/AI/BotBrain.cs": ["gameplay-ai"],
            "game/packages/com.sharpwr.sim/Runtime/Net/Snapshot.cs": ["network-engineer"],
            "game/unity/Assets/SharpWR/Input/TouchJoystick.cs": ["unity-gameplay"],
            "game/parity/fixtures/samira-reference-v1.json": ["data-verification"],
            "game/sim/tests/Parity/SamiraReferenceParityTests.cs": ["qa"],
            "CLAUDE.md": ["lead"],
        }
        for path, owners in cases.items():
            self.assertEqual(co.owners_of(path, self.data), owners, path)

    def test_damage_lab_is_protected_and_unowned(self):
        for path in ("sharpwr/fight_engine.py", "data/marksman_champion_stats.json", "streamlit_app.py",
                     "mobile/src/main.ts", "docs/architecture.md"):
            self.assertTrue(co.is_protected(path, self.data), path)
            self.assertEqual(co.owners_of(path, self.data), [], path)
        self.assertFalse(co.is_protected("docs/moba/01-architecture.md", self.data))

    def test_diff_rejects_foreign_paths(self):
        errors = co.check_diff(self.data, "gameplay-ai", [
            "game/packages/com.sharpwr.sim/Runtime/AI/x.cs",
            "game/packages/com.sharpwr.sim/Runtime/Combat/y.cs",
            "sharpwr/aa_engine.py"])
        self.assertEqual(len(errors), 2, errors)


if __name__ == "__main__":
    unittest.main()
