"""Validate game content: provenance on every number, no invented values, IP boundary.

Rules (docs/moba/02-data-migration.md, docs/moba/10-legal-and-ip.md):
  R1  every content file declares a known "schema"
  R2  every provenance field {value, status, source} uses a known status; value is decimal text
      or null; null <=> status "unresolved"; source is non-empty
  R3  champion files carry id, display_name, ip, shippable, stats, abilities
  R4  files under reference-riot/ are ip "riot-reference" and shippable false;
      files elsewhere are ip "original" and may only use original/design statuses
  R5  rosters declare "distribution": "personal" (owner-only build, may list reference
      champions) or "public" (only shippable champions); every listed champion exists

Usage: python -I tools/content/validate_content.py [content_root]   (exit 2 on violations)
"""

from __future__ import annotations

import json
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONTENT = ROOT / "game" / "content"

SCHEMAS = {"sharpwr.champion/1", "sharpwr.roster/1", "sharpwr.ai-profiles/1"}
REFERENCE_STATUSES = {
    "wr_verified_user",        # explicit user Wild Rift confirmation
    "wr_wiki",                 # Wild Rift wiki data template
    "damage_lab_preserved",    # existing Damage Lab value, provenance recorded there
    "damage_lab_user_sourced", # Damage Lab value from user-supplied WR evidence keys
    "pc_reference_provisional",# PC LoL value used as a labelled stand-in
    "unresolved",              # unknown: value must be null and the mechanic gated off
}
ORIGINAL_STATUSES = {
    "original_design",         # a design decision for SharpWR's own content
    "original_placeholder",    # temporary design value, must be tuned before release
    "unresolved",
}
ALL_STATUSES = REFERENCE_STATUSES | ORIGINAL_STATUSES


def is_decimal_text(value) -> bool:
    if not isinstance(value, str):
        return False
    try:
        Decimal(value)
    except InvalidOperation:
        return False
    return True


def walk_fields(node, path=""):
    if isinstance(node, dict):
        if "status" in node and "value" in node:
            yield path, node
            return
        for key, child in node.items():
            yield from walk_fields(child, f"{path}.{key}" if path else key)
    elif isinstance(node, list):
        for i, child in enumerate(node):
            yield from walk_fields(child, f"{path}[{i}]")


def check_field(path, f, allowed):
    errors = []
    status, value, source = f.get("status"), f.get("value"), f.get("source")
    if status not in ALL_STATUSES:
        errors.append(f"{path}: unknown status {status!r}")
    elif status not in allowed:
        errors.append(f"{path}: status {status!r} not allowed in this content area")
    if status == "unresolved":
        if value is not None:
            errors.append(f"{path}: unresolved field must have value null (got {value!r})")
    elif value is None:
        errors.append(f"{path}: null value requires status 'unresolved'")
    elif not is_decimal_text(value) and not (isinstance(value, str) and path.endswith("curve")):
        errors.append(f"{path}: value must be decimal text for Fix64.Parse (got {value!r})")
    if not source or not str(source).strip():
        errors.append(f"{path}: missing source")
    return errors


def validate(content_root: Path = CONTENT) -> list[str]:
    errors: list[str] = []
    champions: dict[str, dict] = {}
    rosters: list[tuple[Path, dict]] = []
    for file in sorted(content_root.rglob("*.json")):
        rel = file.relative_to(content_root)
        try:
            data = json.loads(file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{rel}: invalid JSON ({exc})")
            continue
        schema = data.get("schema")
        if schema not in SCHEMAS:
            errors.append(f"{rel}: R1 unknown schema {schema!r}")
            continue
        reference_area = rel.parts[0] == "reference-riot"
        if schema == "sharpwr.roster/1":
            if reference_area:
                errors.append(f"{rel}: R5 rosters may not live in reference-riot/")
            rosters.append((rel, data))
            continue
        if schema == "sharpwr.ai-profiles/1":
            if reference_area or data.get("ip") != "original":
                errors.append(f"{rel}: R4 AI profiles are original content outside reference-riot/")
            for path, f in walk_fields(data):
                errors += [f"{rel}: R2 {e}" for e in check_field(path, f, ORIGINAL_STATUSES)]
            continue
        for key in ("id", "display_name", "ip", "shippable", "stats", "abilities"):
            if key not in data:
                errors.append(f"{rel}: R3 missing {key!r}")
        if reference_area:
            if data.get("ip") != "riot-reference" or data.get("shippable") is not False:
                errors.append(f"{rel}: R4 reference-riot content must be ip 'riot-reference', shippable false")
            allowed = REFERENCE_STATUSES
        else:
            if data.get("ip") != "original":
                errors.append(f"{rel}: R4 content outside reference-riot/ must be ip 'original'")
            allowed = ORIGINAL_STATUSES
        for path, f in walk_fields(data):
            errors += [f"{rel}: R2 {e}" for e in check_field(path, f, allowed)]
        if data.get("id") in champions:
            errors.append(f"{rel}: duplicate champion id {data['id']!r}")
        champions[data.get("id")] = data
    for rel, roster in rosters:
        distribution = roster.get("distribution")
        if distribution not in ("personal", "public"):
            errors.append(f"{rel}: R5 distribution must be 'personal' or 'public'")
        for cid in roster.get("champions", []):
            champ = champions.get(cid)
            if champ is None:
                errors.append(f"{rel}: R5 unknown champion {cid!r}")
            elif distribution == "public" and champ.get("shippable") is not True:
                errors.append(f"{rel}: R5 champion {cid!r} is not shippable (public roster)")
    return errors


def main(argv):
    root = Path(argv[0]) if argv else CONTENT
    errors = validate(root)
    if errors:
        print("content validation failed:\n  " + "\n  ".join(errors), file=sys.stderr)
        return 2
    count = len(list(root.rglob("*.json")))
    print(f"content: {count} file(s) valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
