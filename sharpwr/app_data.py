"""Read-only Database export for the mobile app.

Builds the same records the web app's Database tab shows: champions (with level 1-15
stats and abilities), completed items, components, boots and runes, plus SharpWR's published
item tier list and the saved core-item search results. The result is plain JSON data;
scripts/export_app_data.py writes it to app-data/database.json, and the ability icons to
assets/riot/abilities/.
"""

import base64
import json
from pathlib import Path

from .aa_engine import stats
from .build_fight_optimizer import EXCLUSIVE, SPELLBLADE
from .catalog import B, C, F, K, P, dct
from .champion_database import CHAMPION_DATABASE, level_stats
from .core_items import (
    BUDGETS,
    EDITOR_PATH,
    EXCLUDED,
    TARGETS,
    build_styles,
    core_leaders,
    core_record,
)
from .icons import icon_entry
from .marksman_ability_database import catalogue
from .rune_database import RUNE_DATABASE, RUNE_SLOTS
from .rune_pages import DEFAULT_PAGES, default_loadout

SCHEMA = 1
LEVELS = range(1, 16)
# Item tuple fields stored as fractions (0.25 means 25%).
FRACTION_FIELDS = ("as", "crit", "ls", "pctpen", "pctmpen")
# Components whose movement speed is a flat value; every other item's MS is a fraction of base MS.
FLAT_MS_COMPONENTS = {"Boots of Speed"}
DECIMALS = 4
ROOT = Path(__file__).resolve().parents[1]
TIER_LIST = ROOT / "data" / "published-tier-list.json"
ABILITY_TEXTS = ROOT / "data" / "ability-descriptions.json"
# Ability icons cropped from Wild Rift screenshots (or Data Dragon), stored as data URLs.
SKILL_ICONS = ROOT / "data" / "riot" / "marksman-skill-icons.json"
ABILITY_ICON_DIR = "assets/riot/abilities"
ABILITY_SLOTS = ("P", "Q", "W", "E", "R")
# Attack parameters per champion, in sharpwr/catalog.py C tuple order.
AA_FIELDS = ("base_ad", "ad_growth", "as_ratio", "base_as", "base_bonus_as", "as_growth")


def _icon(kind, name):
    """Repository-relative path of the bundled icon, or None."""
    entry = icon_entry(kind, name) if kind else None
    return entry["path"] if entry else None


def _number(value):
    return round(value, DECIMALS) if isinstance(value, float) else value


def champion_level_stats(name, level, mist=0):
    """Champion stats at a level before items and runes, as the champion card shows them.

    Attack damage and attack speed come from the AA engine; the remaining stats from the
    champion database. Senna's AD includes 1.25 per Mist stack.
    """
    profile = stats(name, level, mist)
    attack_speed = profile["baseas"] + profile["ratio"] * (profile["bba"] + profile["lvbas"])
    return {
        "attack_damage": profile["ad"],
        "attack_speed": attack_speed,
        **level_stats(name, level),
    }


def _ability_icon(champion, slot, data_url):
    """Repository-relative file for an ability icon, named after the champion icon file."""
    stem = Path(_icon("champions", champion)).stem
    extension = {"data:image/webp": "webp", "data:image/png": "png"}[data_url.split(";", 1)[0]]
    return f"{ABILITY_ICON_DIR}/{stem}-{slot}.{extension}"


def ability_icon_files():
    """Every ability icon as {repository-relative path: image bytes}."""
    icons = json.loads(SKILL_ICONS.read_text())["champions"]
    return {
        _ability_icon(name, slot, url): base64.b64decode(url.split(",", 1)[1])
        for name in CHAMPION_DATABASE
        for slot, url in icons[name]["icons"].items()
    }


def _per_rank(values):
    return None if values is None else [_number(float(value)) for value in values]


def _abilities(name):
    """Passive, Q, W, E and R: editor summary, icon, and cooldown and mana per rank."""
    texts = json.loads(ABILITY_TEXTS.read_text())["champions"][name]
    icons = json.loads(SKILL_ICONS.read_text())["champions"][name]["icons"]
    records = catalogue()[name]["abilities"]
    return [
        {
            "slot": slot,
            "name": texts[slot]["name"],
            "icon": _ability_icon(name, slot, icons[slot]),
            "description": texts[slot]["text"],
            "cooldown": _per_rank(records[slot]["cooldown_by_rank"]),
            "mana": _per_rank(records[slot]["mana_by_rank"]),
            "range": records[slot]["range"],
        }
        for slot in ABILITY_SLOTS
    ]


def rune_stats(name, level):
    """What the default rune page adds to build_stats at a level, unrounded: AD, mana, ability
    haste and bonus attack speed."""
    loadout = default_loadout(name, level)
    return {
        "ad": loadout.persistent["ad"],
        "mana": loadout.persistent["mana"],
        "ah": loadout.persistent["ah"],
        "bonus_as": loadout.bonus_as,
    }


def _champion(name, record):
    return {
        "name": name,
        "icon": _icon("champions", name),
        "attack_type": record.get("attack_type"),
        "resource_type": record.get("resource_type"),
        "stats": {key: _number(value) for key, value in record["stats"].items()},
        "aa": dict(zip(AA_FIELDS, C[name])),
        "levels": {
            str(level): {
                key: _number(value) for key, value in champion_level_stats(name, level).items()
            }
            for level in LEVELS
        },
        "source_status": record["source_status"],
        "wiki_source_url": record.get("wiki_source_url"),
        "wiki_last_change_patch": record.get("wiki_last_change_patch"),
        "abilities": _abilities(name),
        "rune_page": DEFAULT_PAGES[name],
        "rune_stats": {str(level): rune_stats(name, level) for level in LEVELS},
        "editor_core": json.loads(EDITOR_PATH.read_text())["picks"].get(name),
    }


def _item(name, values, category):
    record = dct(values)
    entry = {
        "name": name,
        "icon": _icon({"completed": "items", "boots": "boots"}.get(category), name),
        "category": category,
        "gold": record["gold"],
        "stats": {key: _number(record[key]) for key in K if key != "gold"},
    }
    if record["ms"]:
        flat = category == "boots" or name in FLAT_MS_COMPONENTS
        entry["ms_unit"] = "flat" if flat else "fraction"
    return entry


def _rune_slot(name):
    for tree_slots in RUNE_SLOTS.values():
        for slot, names in tree_slots.items():
            if name in names:
                return slot
    return None


def _rune(name, record):
    return {
        "name": name,
        "icon": _icon("runes", name),
        "tree": record["tree"],
        "slot": _rune_slot(name),
        "kind": record["kind"],
        "tooltip": record["tooltip"],
        "data": record["data"],
    }


def _tier_list():
    """Published tier list, best tier first, without the unranked pool."""
    published = json.loads(TIER_LIST.read_text())
    return {
        "title": published["title"],
        "patch": published["patch"],
        "tiers": [
            {"tier": tier, "items": names}
            for tier, names in published["tiers"].items()
            if tier != "pool"
        ],
    }


def _build(row):
    return {
        "items": row["Items"],
        "boots": row["Boots"],
        "ttk": None if row["TTK"] is None else round(row["TTK"], 3),
        "dps": round(row["DPS"], 1),
        "gold": row["Gold"],
        "note": row.get("Rank explanation"),
    }


def _stages(cells):
    """Saved finalists per matchup, in level and target order."""
    return [
        {
            "level": level,
            "target": target,
            "items_allowed": budget,
            "builds": [_build(row) for row in cells[f"{level}:{target}"]["search"]["full"]],
        }
        for level, budget in BUDGETS.items()
        for target in TARGETS
    ]


def _core_builds(name):
    """Saved build results for one champion; None while they are stale or incomplete."""
    record = core_record(name)
    core = core_leaders(record)
    if not core:
        return None
    defined = {style["key"]: style for style in build_styles(name)}
    styles = [style for style in record.get("styles", []) if style["key"] in defined]
    every_cell = [
        *record["cells"].values(),
        *record.get("top", {}).values(),
        *(cell for style in styles for cell in style["cells"].values()),
    ]
    return {
        "core": core,
        "ranking": [
            {
                "item": row["Item"],
                "score": round(row["Score"], 1),
                "winner_cells": row["Winner cells"],
                "top3_cells": row["Common Top-3 cells"],
                "appearance_cells": row["Appearance cells"],
                "eligible_cells": row["Eligible cells"],
            }
            for row in record["ranking"]
        ],
        # Top builds: every item allowed (saved before 7.1.0: the core-item search).
        "stages": _stages(record.get("top") or record["cells"]),
        "styles": [
            {
                "key": style["key"],
                "name": defined[style["key"]]["name"],
                "items": style["items"],
                "keystone": style["keystone"],
                "editor": bool(defined[style["key"]].get("editor")),
                "note": defined[style["key"]].get("note"),
                "stages": _stages(style["cells"]),
            }
            for style in styles
        ],
        "keystone_check": [
            {
                "level": row["level"],
                "target": row["target"],
                "items": row["items"],
                "boots": row["boots"],
                "ttk": {
                    keystone: None if ttk is None else round(ttk, 3)
                    for keystone, ttk in row["ttk"].items()
                },
            }
            for row in record.get("keystone_check", [])
        ],
        "notes": sorted(
            {
                note
                for cell in every_cell
                for row in cell["search"]["full"]
                for note in row["Assumptions"]
            }
        ),
    }


def _core_items():
    return {
        "excluded": sorted(EXCLUDED),
        "champions": {name: _core_builds(name) for name in CHAMPION_DATABASE},
    }


def build_database():
    """Every Database record as JSON-ready data, in the web app's display order."""
    return {
        "schema": SCHEMA,
        "units": {
            "fractions": list(FRACTION_FIELDS),
            "ms": "Per item: ms_unit 'fraction' (share of base MS) or 'flat'.",
            "levels": "Champion stats per level 1-15 before items and runes.",
            "icon": "Repository-relative path under assets/riot/; null when there is no icon.",
        },
        "champions": [_champion(name, record) for name, record in CHAMPION_DATABASE.items()],
        "items": [_item(name, values, "completed") for name, values in F.items()],
        "components": [_item(name, values, "component") for name, values in P.items()],
        "boots": [_item(name, values, "boots") for name, values in B.items()],
        "runes": [_rune(name, record) for name, record in RUNE_DATABASE.items()],
        "rune_trees": [{"name": tree, "icon": _icon("rune_trees", tree)} for tree in RUNE_SLOTS],
        "build_rules": {
            "max_items": 5,
            "exclusive_groups": [sorted(group) for group in EXCLUSIVE],
            "spellblade": sorted(SPELLBLADE),
        },
        "tier_list": _tier_list(),
        "core_items": _core_items(),
    }


def render_database_json():
    """The exact text of app-data/database.json."""
    return json.dumps(build_database(), ensure_ascii=False, allow_nan=False, indent=1) + "\n"
