"""Static determinism lint for the simulation core (ADR-0002, .claude/rules/simulation-core.md).

Scans C# under game/packages/com.sharpwr.sim/Runtime and fails on constructs that break
cross-platform determinism or the simulation/rendering split. A line can opt out with an
inline marker naming the rule and a reason:

    return Raw / 4294967296.0; // sim-lint: allow(floating-point) diagnostics only

Usage:
    python -I tools/sim_lint/sim_lint.py                 # whole sim package
    python -I tools/sim_lint/sim_lint.py path/a.cs ...   # specific files (hooks)
Exit code 2 on violations (Claude Code hooks treat 2 as "blocking, show stderr").
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIM_ROOT = ROOT / "game" / "packages" / "com.sharpwr.sim" / "Runtime"

RULES = [
    ("floating-point", re.compile(r"\b(float|double|Single|Double)\b|\b\d+\.\d+f\b"),
     "float/double in simulation code; use Fix64 (raw floats differ across ARM/x64/IL2CPP)"),
    ("unity-engine", re.compile(r"\bUnityEngine\b|\bMathf\b|\bVector[234]\b|\bQuaternion\b"),
     "UnityEngine types in simulation; the sim must compile without Unity"),
    ("nondeterministic-source", re.compile(
        r"\bSystem\.Random\b|\bnew\s+Random\s*\(|\bDateTime\b|\bStopwatch\b|\bEnvironment\.TickCount|"
        r"\bGuid\.NewGuid\b|\bTime\.(time|deltaTime)"),
     "wall clock / unseeded randomness; use SimTime and DeterministicRandom"),
    ("concurrency", re.compile(r"\basync\b|\bawait\b|\bTask\b|\bThread\b|\bParallel\.|\bThreadPool\b"),
     "concurrency inside a tick; simulation steps are single-threaded"),
    ("unordered-collection", re.compile(r"\b(Dictionary|HashSet|ConcurrentDictionary)\s*<"),
     "hash collections enumerate in implementation-defined order; use sorted lists or "
     "allow(unordered-collection) for lookup-only use"),
    ("hash-code-ordering", re.compile(r"\.GetHashCode\(\)\s*[<>]|OrderBy\([^)]*GetHashCode"),
     "ordering by GetHashCode is not stable across runtimes"),
    ("system-math-float", re.compile(r"\bSystem\.Math\.(Sin|Cos|Tan|Atan2?|Sqrt|Pow|Exp|Log)\b"),
     "transcendental floating-point functions; use Fix64 lookup/series implementations"),
]

ALLOW = re.compile(r"//\s*sim-lint:\s*allow\(([a-z\-, ]+)\)\s+\S+")


def strip_comment_and_strings(line: str) -> str:
    out, i, in_str = [], 0, False
    while i < len(line):
        ch = line[i]
        if not in_str and line.startswith("//", i):
            break
        if ch == '"' and (i == 0 or line[i - 1] != "\\"):
            in_str = not in_str
            out.append('"')
        elif not in_str:
            out.append(ch)
        i += 1
    return "".join(out)


def lint_text(text: str, name: str = "<text>") -> list[str]:
    problems = []
    in_block = False
    for number, raw in enumerate(text.splitlines(), 1):
        line = raw
        if in_block:
            if "*/" not in line:
                continue
            line, in_block = line.split("*/", 1)[1], False
        if "/*" in line and "*/" not in line.split("/*", 1)[1]:
            line, in_block = line.split("/*", 1)[0], True
        allowed = set()
        marker = ALLOW.search(raw)
        if marker:
            allowed = {r.strip() for r in marker.group(1).split(",")}
        code = strip_comment_and_strings(line)
        for rule, pattern, why in RULES:
            if rule not in allowed and pattern.search(code):
                problems.append(f"{name}:{number}: [{rule}] {why}\n    {raw.strip()}")
    return problems


def default_files() -> list[Path]:
    return sorted(SIM_ROOT.rglob("*.cs"))


def main(argv: list[str]) -> int:
    files = [(ROOT / a).resolve() if not Path(a).is_absolute() else Path(a) for a in argv] if argv else default_files()
    files = [f for f in files if f.suffix == ".cs" and SIM_ROOT in f.resolve().parents]
    problems = []
    for f in files:
        problems += lint_text(f.read_text(encoding="utf-8"), str(f.relative_to(ROOT)))
    if problems:
        print("sim-lint: determinism violations\n" + "\n".join(problems), file=sys.stderr)
        return 2
    print(f"sim-lint: {len(files)} file(s) clean")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
