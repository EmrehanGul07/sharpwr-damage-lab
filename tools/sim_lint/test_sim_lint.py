import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sim_lint import lint_text  # noqa: E402


class SimLint(unittest.TestCase):
    def rules(self, code):
        return [p.split("[")[1].split("]")[0] for p in lint_text(code)]

    def test_flags_float_and_unity(self):
        self.assertEqual(self.rules("float speed = 1.5f;"), ["floating-point"])
        self.assertIn("unity-engine", self.rules("using UnityEngine;"))
        self.assertIn("nondeterministic-source", self.rules("var r = new Random(1);"))
        self.assertIn("unordered-collection", self.rules("var d = new Dictionary<int, int>();"))
        self.assertIn("concurrency", self.rules("async Task Run() {}"))

    def test_comments_strings_and_allow_markers(self):
        self.assertEqual(self.rules("// a float in a comment"), [])
        self.assertEqual(self.rules('var s = "double";'), [])
        self.assertEqual(self.rules("/* float\n double */ int x;"), [])
        self.assertEqual(self.rules("double d = 1; // sim-lint: allow(floating-point) debug"), [])
        # A marker without a reason does not count.
        self.assertEqual(self.rules("double d = 1; // sim-lint: allow(floating-point)"), ["floating-point"])
        # A marker only allows the rule it names.
        self.assertEqual(self.rules("double d; // sim-lint: allow(concurrency) x"), ["floating-point"])

    def test_fix64_is_clean(self):
        self.assertEqual(self.rules("Fix64 a = Fix64.Parse(\"1.5\") * b;"), [])


if __name__ == "__main__":
    unittest.main()
