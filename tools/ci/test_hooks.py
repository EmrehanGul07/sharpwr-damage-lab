"""Black-box tests of the Claude Code hook scripts (stdin JSON in, exit code out)."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HOOKS = ROOT / ".claude" / "hooks"


def run(hook, file_path, env=None):
    payload = {"hook_event_name": "PreToolUse", "tool_name": "Write",
               "tool_input": {"file_path": str(ROOT / file_path), "content": "x"}}
    r = subprocess.run([sys.executable, str(HOOKS / hook)], input=json.dumps(payload),
                       capture_output=True, text=True,
                       env={"CLAUDE_PROJECT_DIR": str(ROOT), "PATH": "/usr/bin:/bin", **(env or {})})
    return r.returncode, r.stderr


class GuardPaths(unittest.TestCase):
    def test_blocks_damage_lab(self):
        for path in ("sharpwr/fight_engine.py", "data/marksman_champion_stats.json", "mobile/src/main.ts"):
            code, err = run("guard_paths.py", path)
            self.assertEqual(code, 2, path)
            self.assertIn("Damage Lab", err)

    def test_explicit_override(self):
        code, _ = run("guard_paths.py", "sharpwr/fight_engine.py", {"SHARPWR_ALLOW_REFERENCE_EDIT": "1"})
        self.assertEqual(code, 0)

    def test_allows_game_code(self):
        code, _ = run("guard_paths.py", "game/packages/com.sharpwr.sim/Runtime/AI/Bot.cs")
        self.assertEqual(code, 0)

    def test_blocks_riot_art_in_game(self):
        self.assertEqual(run("guard_paths.py", "game/unity/Assets/Art/samira.glb")[0], 2)
        self.assertEqual(run("guard_paths.py", "game/unity/Assets/Art/riot/icon.png")[0], 2)
        self.assertEqual(run("guard_paths.py", "game/unity/Assets/Art/original-hero.glb")[0], 0)


class PostEditChecks(unittest.TestCase):
    def test_clean_sim_file_passes(self):
        code, _ = run("post_edit_checks.py", "game/packages/com.sharpwr.sim/Runtime/Numerics/Fix64.cs")
        self.assertEqual(code, 0)

    def test_unrelated_file_is_ignored(self):
        self.assertEqual(run("post_edit_checks.py", "docs/moba/README.md")[0], 0)


if __name__ == "__main__":
    unittest.main()
