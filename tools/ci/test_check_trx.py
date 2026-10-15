import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import check_trx  # noqa: E402

TRX = """<?xml version="1.0"?><TestRun xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010">
<ResultSummary outcome="Completed"><Counters total="{t}" executed="{t}" passed="{p}" failed="{f}"/></ResultSummary></TestRun>"""


class CheckTrx(unittest.TestCase):
    def run_with(self, t, p, f, minimum):
        with tempfile.NamedTemporaryFile("w", suffix=".trx", delete=False) as fh:
            fh.write(TRX.format(t=t, p=p, f=f))
        return check_trx.main([fh.name, "--min", str(minimum)])

    def test_pass_fail_and_too_few(self):
        self.assertEqual(self.run_with(26, 26, 0, 26), 0)
        self.assertEqual(self.run_with(26, 25, 1, 26), 1)
        self.assertEqual(self.run_with(0, 0, 0, 26), 1)


if __name__ == "__main__":
    unittest.main()
