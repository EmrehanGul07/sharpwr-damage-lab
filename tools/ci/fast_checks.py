#!/usr/bin/env python3
"""Fast check tier (~5 s without .NET). Run by the Stop/SubagentStop hooks and CI.

  python -I tools/ci/fast_checks.py            # all checks
  python -I tools/ci/fast_checks.py --hook     # Stop hook mode: skip when no game files changed,
                                               # never loop (respects stop_hook_active)
Exit 2 when any check fails (hook mode: so Claude keeps working on the failure).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = [sys.executable, "-I"]
GAME_ROOTS = ("game/", "tools/", ".claude/", "docs/moba/", "CLAUDE.md")

CHECKS = [
    ("sim determinism lint", PY + ["tools/sim_lint/sim_lint.py"]),
    ("content provenance/IP", PY + ["tools/content/validate_content.py"]),
    ("ownership map", PY + ["tools/ownership/check_ownership.py", "map"]),
    *[(f"unit tests: tools/{d}", PY + ["-m", "unittest", "discover", "-s", f"tools/{d}", "-p", "test_*.py"])
      for d in ("parity", "sim_lint", "content", "ownership", "ci")],
    ("parity fixtures current", PY + ["tools/parity/export_parity_fixtures.py", "--check"]),
    ("fix64 vectors current", PY + ["tools/parity/emit_fix64_vectors.py", "--check"]),
    ("reference content current", PY + ["tools/data_import/import_reference_champion.py", "Samira", "--check"]),
    ("unity embedded content current", PY + ["tools/content/sync_unity_content.py", "--check"]),
]


def game_changes() -> bool:
    out = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"], capture_output=True, text=True).stdout
    return any(line[3:].startswith(GAME_ROOTS) for line in out.splitlines())


def main(argv):
    hook = "--hook" in argv
    if hook:
        try:
            payload = json.load(sys.stdin)
        except (json.JSONDecodeError, ValueError):
            payload = {}
        if payload.get("stop_hook_active") or not game_changes():
            return 0
    checks = list(CHECKS)
    if shutil.which("dotnet"):
        checks.append(("C# sim tests (dotnet)", ["dotnet", "test", "game/sim/tests/SharpWR.Sim.Tests.csproj", "--nologo"]))
    failures = []
    for name, cmd in checks:
        r = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        status = "ok" if r.returncode == 0 else "FAIL"
        print(f"[{status}] {name}")
        if r.returncode:
            failures.append(f"--- {name}\n{(r.stderr or r.stdout)[-3000:]}")
    if not shutil.which("dotnet"):
        print("[skip] C# sim tests: dotnet not installed here (CI runs them: .github/workflows/game-ci.yml)")
    if failures:
        print("fast checks failed:\n" + "\n".join(failures), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
