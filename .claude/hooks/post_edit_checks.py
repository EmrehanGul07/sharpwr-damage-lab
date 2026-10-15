#!/usr/bin/env python3
"""PostToolUse checks after Edit/Write/MultiEdit. Fast (<1 s), scoped to the edited file.

- simulation C#  -> tools/sim_lint (determinism rules)
- game/content   -> tools/content/validate_content.py (provenance / IP boundary)
Exit 2 feeds the findings back to Claude so it fixes them before moving on.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))


def run(args):
    r = subprocess.run([sys.executable, "-I", *args], cwd=ROOT, capture_output=True, text=True)
    return r.returncode, (r.stderr or r.stdout).strip()


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    target = (payload.get("tool_input") or {}).get("file_path")
    if not target:
        return 0
    try:
        rel = Path(target).resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return 0
    if rel.startswith("game/packages/com.sharpwr.sim/Runtime/") and rel.endswith(".cs"):
        code, out = run(["tools/sim_lint/sim_lint.py", rel])
    elif rel.startswith("game/content/") and rel.endswith(".json"):
        code, out = run(["tools/content/validate_content.py"])
    else:
        return 0
    if code != 0:
        print(out, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
