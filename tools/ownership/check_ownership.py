"""Ownership checks for parallel agents (.claude/ownership.json, .claude/rules/integration.md).

Commands:
  map                       every governed file matches exactly one owner; globs do not overlap
  owner PATH...             print the owner of each path
  diff --owner NAME [--base REF]
                            fail if the working-tree change set touches paths NAME does not own
                            (also fails on protected Damage Lab paths)
Exit 2 on violation.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MAP = ROOT / ".claude" / "ownership.json"


@lru_cache(maxsize=None)
def glob_regex(pattern: str) -> re.Pattern:
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("".join(out) + r"\Z")


def load(path: Path = MAP) -> dict:
    return json.loads(path.read_text())


def matches(path: str, patterns) -> bool:
    return any(glob_regex(p).match(path) for p in patterns)


def owners_of(path: str, data: dict) -> list[str]:
    return [name for name, o in data["owners"].items() if matches(path, o["paths"])]


def governed(path: str, data: dict) -> bool:
    return any(path == r or path.startswith(r) for r in data["governed_roots"])


def is_protected(path: str, data: dict) -> bool:
    return matches(path, data["protected_reference"]["paths"])


def repo_files() -> list[str]:
    out = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--cached", "--others", "--exclude-standard"],
                         capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line]


def check_map(data: dict, files: list[str]) -> list[str]:
    errors = []
    for f in files:
        if not governed(f, data):
            continue
        if is_protected(f, data):
            errors.append(f"{f}: governed path is also protected reference")
        owners = owners_of(f, data)
        if len(owners) != 1:
            errors.append(f"{f}: {len(owners)} owners {owners}")
    # Contracts must be owned by exactly one owner as well.
    for c in data["shared_contracts"]["paths"]:
        probe = c.replace("**", "x/y.cs").replace("*", "x")
        if len(owners_of(probe, data)) != 1:
            errors.append(f"shared contract {c}: not exactly one owner")
    return errors


def changed_files(base: str | None) -> list[str]:
    cmd = ["git", "-C", str(ROOT), "diff", "--name-only"] + ([base] if base else ["HEAD"])
    tracked = subprocess.run(cmd, capture_output=True, text=True, check=True).stdout.split()
    untracked = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--others", "--exclude-standard"],
                               capture_output=True, text=True, check=True).stdout.split()
    return sorted(set(tracked + untracked))


def check_diff(data: dict, owner: str, files: list[str]) -> list[str]:
    if owner not in data["owners"]:
        return [f"unknown owner {owner!r}"]
    errors = []
    for f in files:
        if is_protected(f, data):
            errors.append(f"{f}: protected Damage Lab reference (needs explicit user approval)")
        elif governed(f, data) and owner != "lead" and owners_of(f, data) != [owner]:
            errors.append(f"{f}: owned by {owners_of(f, data) or 'nobody'}, not {owner}")
    return errors


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("map")
    o = sub.add_parser("owner")
    o.add_argument("paths", nargs="+")
    d = sub.add_parser("diff")
    d.add_argument("--owner", required=True)
    d.add_argument("--base")
    args = ap.parse_args(argv)
    data = load()
    if args.cmd == "owner":
        for p in args.paths:
            print(f"{p}: {'PROTECTED' if is_protected(p, data) else ', '.join(owners_of(p, data)) or 'ungoverned'}")
        return 0
    errors = check_map(data, repo_files()) if args.cmd == "map" else check_diff(
        data, args.owner, changed_files(args.base))
    if errors:
        print("ownership check failed:\n  " + "\n  ".join(errors), file=sys.stderr)
        return 2
    print(f"ownership: {args.cmd} ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
