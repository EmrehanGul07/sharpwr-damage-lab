"""Turn build/test failures into GitHub annotations (readable through the checks API).

Usage: python -I tools/ci/annotate_failures.py BUILD_LOG [TRX]
Prints at most 10 `::error` lines: compiler errors first, then failed tests with messages.
Always exits 0; the calling step decides failure.
"""
import re
import sys
import xml.etree.ElementTree as ET


def esc(text):
    return text.replace("%", "%25").replace("\r", "").replace("\n", "%0A")


def compiler_errors(path):
    try:
        lines = open(path, encoding="utf-8", errors="replace").read().splitlines()
    except OSError:
        return []
    seen, out = set(), []
    for line in lines:
        m = re.search(r"([^\s:]+\.cs)\((\d+),\d+\): error (CS\d+): (.*?)(\s\[.*\])?$", line)
        if m and m.group(0) not in seen:
            seen.add(m.group(0))
            out.append((f"{m.group(3)} {m.group(1).split('/')[-1]}:{m.group(2)}", m.group(4)))
    return out


def failed_tests(path):
    try:
        root = ET.parse(path).getroot()
    except (OSError, ET.ParseError):
        return []
    out = []
    for r in root.iter():
        if r.tag.endswith("UnitTestResult") and r.get("outcome") == "Failed":
            msg = "".join(t.text or "" for t in r.iter() if t.tag.endswith("Message"))
            out.append((f"FAILED {r.get('testName')}", msg[:3000]))
    return out


def main(argv):
    items = compiler_errors(argv[0]) + (failed_tests(argv[1]) if len(argv) > 1 else [])
    for title, message in items[:9]:
        print(f"::error title={esc(title)}::{esc(message)}")
    if len(items) > 9:
        print(f"::error title=more failures::{len(items) - 9} more not shown")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
