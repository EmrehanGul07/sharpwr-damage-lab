import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import annotate_failures as af  # noqa: E402

LOG = "/x/game/sim/Match.cs(12,5): error CS0103: The name 'foo' does not exist [/x/SharpWR.Sim.csproj]\n"
TRX = """<TestRun xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010"><Results>
<UnitTestResult testName="A.B" outcome="Failed"><Output><ErrorInfo><Message>Expected 1
But was 2</Message></ErrorInfo></Output></UnitTestResult>
<UnitTestResult testName="A.C" outcome="Passed"/></Results></TestRun>"""


class Annotate(unittest.TestCase):
    def test_compiler_errors_and_failed_tests(self):
        with tempfile.TemporaryDirectory() as d:
            (Path(d) / "b.log").write_text(LOG + LOG)
            (Path(d) / "r.trx").write_text(TRX)
            out = io.StringIO()
            with redirect_stdout(out):
                af.main([str(Path(d) / "b.log"), str(Path(d) / "r.trx")])
        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 2, lines)   # duplicate compiler line collapsed
        self.assertIn("CS0103 Match.cs:12", lines[0])
        self.assertIn("FAILED A.B", lines[1])
        self.assertIn("Expected 1%0ABut was 2", lines[1])


if __name__ == "__main__":
    unittest.main()
