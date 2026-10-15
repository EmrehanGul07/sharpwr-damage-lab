"""Fail unless a dotnet TRX results file shows >= N executed tests and zero failures.

`dotnet test` exits 0 when no tests are discovered; this makes "nothing ran" a failure and
prints the counts so CI evidence is visible in the job summary.
Usage: python -I tools/ci/check_trx.py RESULTS.trx --min 26
"""
import argparse
import os
import sys
import xml.etree.ElementTree as ET


def counts(path):
    root = ET.parse(path).getroot()
    node = next(el for el in root.iter() if el.tag.endswith("Counters"))
    return {k: int(v) for k, v in node.attrib.items() if v.isdigit()}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("trx")
    ap.add_argument("--min", type=int, required=True)
    a = ap.parse_args(argv)
    c = counts(a.trx)
    line = f"tests executed={c.get('executed', 0)} passed={c.get('passed', 0)} failed={c.get('failed', 0)} (min {a.min})"
    print(line)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write(f"- {line}\n")
    ok = c.get("failed", 0) == 0 and c.get("executed", 0) >= a.min
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
