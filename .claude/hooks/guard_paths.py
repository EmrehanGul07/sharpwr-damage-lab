#!/usr/bin/env python3
"""PreToolUse guard for Edit/Write/MultiEdit/NotebookEdit.

Blocks (exit 2, reason on stderr):
  1. writes to the protected Python Damage Lab (the validation reference), unless the user
     started the session with SHARPWR_ALLOW_REFERENCE_EDIT=1 for a deliberate change;
  2. Riot-derived art (copies of assets/riot or static/marksman-3d files, or any path segment
     named "riot") anywhere in game/ EXCEPT the personal-build folder
     game/unity/Assets/SharpWR/Reference/, which a public build excludes (ADR-0004 rev 2).
Everything else passes. Ownership between agents is enforced by tools/ownership (diff check),
because a hook cannot reliably tell which subagent is writing.
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR", Path(__file__).resolve().parents[2]))
sys.path.insert(0, str(ROOT / "tools" / "ownership"))
import check_ownership as co  # noqa: E402

REFERENCE_ART_DIR = "game/unity/assets/sharpwr/reference/"
ART = (".png", ".webp", ".jpg", ".jpeg", ".glb", ".gltf", ".fbx", ".blend", ".wav", ".ogg", ".mp3")


def riot_art_names():
    names = set()
    for folder in ("assets/riot", "static/marksman-3d", "assets/marksman-3d/models"):
        base = ROOT / folder
        if base.exists():
            names |= {p.name.lower() for p in base.rglob("*") if p.is_file()}
    return names


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0
    tool_input = payload.get("tool_input") or {}
    target = tool_input.get("file_path") or tool_input.get("notebook_path")
    if not target:
        return 0
    try:
        rel = Path(target).resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return 0  # outside the project
    data = co.load(ROOT / ".claude" / "ownership.json")
    if co.is_protected(rel, data) and os.environ.get("SHARPWR_ALLOW_REFERENCE_EDIT") != "1":
        print(f"BLOCKED: {rel} is part of the Python Damage Lab, the validation reference. "
              "Do not modify it; read it, or export data/fixtures via tools/parity or "
              "tools/data_import. If the user explicitly wants a reference change, they must "
              "restart with SHARPWR_ALLOW_REFERENCE_EDIT=1.", file=sys.stderr)
        return 2
    lower = rel.lower()
    if lower.startswith("game/") and lower.endswith(ART) and not lower.startswith(REFERENCE_ART_DIR):
        if "/riot/" in f"/{lower}" or Path(lower).name in riot_art_names():
            print(f"BLOCKED: {rel} looks like Riot-derived art. Put it under "
                  "game/unity/Assets/SharpWR/Reference/ (personal build only, excluded from any "
                  "public build; docs/moba/10-legal-and-ip.md).", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
