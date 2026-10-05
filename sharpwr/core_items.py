"""Core items come from separate, protocol-matched constrained searches."""

from pathlib import Path
from functools import lru_cache
import hashlib, json

EXCLUDED = frozenset(
    {"Lord Dominik's Regards", "Serylda's Grudge", "Mortal Reminder", "Infinity Edge", "Terminus"}
)
BUDGETS = {5: 1, 7: 1, 9: 2, 11: 3, 13: 4, 15: 5}
ROOT = Path(__file__).resolve().parents[1]
SOURCE_FILES = (
    "sharpwr/build_fight_optimizer.py",
    "sharpwr/fight_engine.py",
    "sharpwr/marksman_fight_engine.py",
    "sharpwr/marksman_damage_components.py",
    "sharpwr/marksman_kits.py",
    "sharpwr/champion_database.py",
    "sharpwr/combat_timing.py",
    "sharpwr/damage_classification.py",
    "sharpwr/champion_abilities.py",
    "sharpwr/champion_skill_data.py",
    "sharpwr/marksman_state.py",
    "sharpwr/marksman_ability_database.py",
    "sharpwr/rune_database.py",
    "sharpwr/rune_runtime.py",
    "sharpwr/combat_validation.py",
    "scripts/build_core_items.py",
    "sharpwr/__init__.py",
    "sharpwr/catalog.py",
    "sharpwr/aa_engine.py",
    "sharpwr/targets.py",
    "data/marksman-ability-catalogue.json",
    "data/pc-combat-timing.json",
    "data/marksman_champion_stats.json",
    "data/damage-classification.json",
)


def _selected_digest(source, names):
    import ast

    selected = []
    for node in ast.parse(source).body:
        if (
            isinstance(node, ast.FunctionDef)
            and node.name in names
            or isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id in names for t in node.targets)
        ):
            selected.append(ast.get_source_segment(source, node))
    return "\n".join(selected)


@lru_cache(maxsize=2)
def _fingerprint(stamps):
    h = hashlib.sha256(b"core-protocol-v4-sharpwr-package")
    for name in SOURCE_FILES:
        h.update(name.encode())
        h.update((ROOT / name).read_bytes())
    h.update(
        _selected_digest(
            (ROOT / "sharpwr/core_items.py").read_text(),
            {"EXCLUDED", "BUDGETS", "available", "rank_core"},
        ).encode()
    )
    return h.hexdigest()


def fingerprint():
    return _fingerprint(
        tuple(
            (name, (ROOT / name).stat().st_mtime_ns)
            for name in (*SOURCE_FILES, "sharpwr/core_items.py")
        )
    )


def available(item, level):
    return item not in EXCLUDED and (item != "Muramana" or level >= 11)


def rank_core(cells, pool):
    rows = []
    for item in pool:
        if item in EXCLUDED:
            continue
        eligible = [c for c in cells.values() if available(item, c["level"])]
        if not eligible:
            continue
        score = 0.0
        winner = common = appearances = 0
        for cell in eligible:
            builds = cell["search"]["full"][:3]
            weights = [1 / (r + 1) for r in range(len(builds))]
            denom = sum(weights)
            presence = [item in b["Items"] for b in builds]
            score += sum(w for w, yes in zip(weights, presence) if yes) / denom if denom else 0
            winner += bool(presence and presence[0])
            common += bool(presence and all(presence))
            appearances += any(presence)
        if score:
            rows.append(
                {
                    "Item": item,
                    "Score": round(100 * score / len(eligible), 6),
                    "Winner cells": winner,
                    "Common Top-3 cells": common,
                    "Appearance cells": appearances,
                    "Eligible cells": len(eligible),
                }
            )
    return sorted(
        rows, key=lambda r: (-r["Score"], -r["Winner cells"] / r["Eligible cells"], r["Item"])
    )


@lru_cache(maxsize=4)
def _read(path, mtime):
    return json.loads(Path(path).read_text())


def core_leaders(record):
    """Core item names to show: the top score, at most two on an exact tie.

    Empty when the saved record is missing (stale fingerprint), incomplete or unranked.
    """
    if not record or not record.get("complete") or not record.get("ranking"):
        return []
    best = record["ranking"][0]["Score"]
    return [row["Item"] for row in record["ranking"] if abs(row["Score"] - best) < 1e-6][:2]


def core_record(champion):
    path = ROOT / "data/champion-core-items.json"
    if not path.exists():
        return None
    payload = _read(str(path), path.stat().st_mtime_ns)
    if payload.get("fingerprint") != fingerprint():
        return None
    return payload.get("champions", {}).get(champion)
