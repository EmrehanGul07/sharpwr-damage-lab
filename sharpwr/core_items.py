"""Saved build results: core items from constrained searches, Top builds and build styles from
full-pool searches, all with each champion's default rune page (scripts/build_core_items.py)."""

from pathlib import Path
from functools import lru_cache
import hashlib, json

from .rune_pages import DEFAULT_PAGES, rune_loadout

EXCLUDED = frozenset(
    {"Lord Dominik's Regards", "Serylda's Grudge", "Mortal Reminder", "Infinity Edge", "Terminus"}
)
BUDGETS = {5: 1, 7: 1, 9: 2, 11: 3, 13: 4, 15: 5}
TARGETS = ("squishy", "bruiser", "tank")
# Levels whose Top builds are replayed with every keystone (keystone check).
KEYSTONE_CHECK_LEVELS = (13, 15)
ROOT = Path(__file__).resolve().parents[1]
STYLES_PATH = ROOT / "data" / "build-styles.json"
EDITOR_PATH = ROOT / "data" / "editor-core-items.json"
SOURCE_FILES = (
    "sharpwr/build_fight_optimizer.py",
    "sharpwr/build_stats.py",
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
    "sharpwr/rune_pages.py",
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
    h = hashlib.sha256(b"core-protocol-v5-runes-top-styles")
    for name in SOURCE_FILES:
        h.update(name.encode())
        h.update((ROOT / name).read_bytes())
    h.update(
        _selected_digest(
            (ROOT / "sharpwr/core_items.py").read_text(),
            {
                "EXCLUDED",
                "BUDGETS",
                "KEYSTONE_CHECK_LEVELS",
                "available",
                "rank_core",
                "matchup",
                "rune_page",
                "cell_evaluator",
                "style_items",
            },
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


def matchup(ns, profiles, level, target):
    """The benchmark target at a level, interpolated between profile levels, and the Yun Tal
    stacks a champion has gathered by then."""
    profile = profiles[target]
    if level in profile:
        stats = profile[level]
    else:
        lo = max(l for l in profile if l < level)
        hi = min(l for l in profile if l > level)
        u = (level - lo) / (hi - lo)
        stats = {
            **{
                k: profile[lo][k] + u * (profile[hi][k] - profile[lo][k])
                for k in ("hp", "armor", "mr")
            },
            "aa_reduction": profile[hi].get("aa_reduction", 0) if level >= 5 else 0,
        }
    natural = (
        stats["hp"]
        if target == "squishy"
        else 660 + 148 * ns["gu"](level) if target == "bruiser" else 690 + 132 * ns["gu"](level)
    )
    return {
        "hp": stats["hp"],
        "armor": stats["armor"],
        "mr": stats["mr"],
        "aa_reduction": stats.get("aa_reduction", 0),
        "bonus_hp": max(0, stats["hp"] - natural),
        "yuntal_stacks": 0 if level <= 5 else 125 if level >= 9 else round(125 * (level - 5) / 4),
    }


def rune_page(champion, keystone=None):
    """The champion's default rune page, with another keystone when one is given."""
    page = dict(DEFAULT_PAGES[champion])
    if keystone:
        page["keystone"] = keystone
    return page


def cell_evaluator(ns, profiles, champion, level, target, keystone=None, **options):
    """Build evaluator for one matchup with the champion's rune page."""
    from .build_fight_optimizer import BuildFightEvaluator

    m = matchup(ns, profiles, level, target)
    return BuildFightEvaluator(
        ns,
        champion,
        level,
        m["hp"],
        m["armor"],
        m["mr"],
        mist=40 if champion == "Senna" else 0,
        bonus_hp=m["bonus_hp"],
        aa_reduction=m["aa_reduction"],
        yuntal_stacks=m["yuntal_stacks"],
        runes=rune_loadout(rune_page(champion, keystone), level),
        **options,
    )


def build_styles(champion):
    """Styles to compute: the editor's core item first, then data/build-styles.json, each once."""
    pick = json.loads(EDITOR_PATH.read_text())["picks"].get(champion)
    listed = json.loads(STYLES_PATH.read_text())["styles"].get(champion, [])
    styles = [{"name": "Editor's core", "items": [pick["item"]], "editor": True}] if pick else []
    styles += [dict(style) for style in listed]
    unique = {}
    for style in styles:
        style.setdefault("keystone", None)
        unique.setdefault(style_key(style), style)
    return [{**style, "key": key} for key, style in unique.items()]


def style_key(style):
    return "+".join(style["items"]) + (f"@{style['keystone']}" if style.get("keystone") else "")


def style_items(style, level, budget):
    """A style's required items in a build of `budget` items: the first ones on its path."""
    return [("Manamune" if x == "Muramana" and level < 11 else x) for x in style["items"][:budget]]


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


def editor_pick(champion):
    """SharpWR's own core item pick ({"item", "reason"}), or None."""
    return json.loads(EDITOR_PATH.read_text())["picks"].get(champion)


def shown_core(champion):
    """Core item(s) the apps show: SharpWR's pick, else the engine's leaders (empty while pending)."""
    pick = editor_pick(champion)
    return [pick["item"]] if pick else core_leaders(core_record(champion))


def core_record(champion):
    """Saved results for a champion; None while they are stale (engine or rune page changed)."""
    path = ROOT / "data/champion-core-items.json"
    if not path.exists():
        return None
    payload = _read(str(path), path.stat().st_mtime_ns)
    if payload.get("fingerprint") != fingerprint():
        return None
    record = payload.get("champions", {}).get(champion)
    if record is None or record.get("rune_page") != DEFAULT_PAGES.get(champion):
        return None
    return record
