"""Read-only Database export for the mobile app.

Builds the same records the web app's Database tab shows: champions (with level 1-15
stats), completed items, components, boots and runes. The result is plain JSON data;
scripts/export_app_data.py writes it to app-data/database.json.
"""

import json

from .aa_engine import stats
from .catalog import B, F, K, P, dct
from .champion_database import CHAMPION_DATABASE, level_stats
from .icons import icon_entry
from .rune_database import RUNE_DATABASE, RUNE_SLOTS

SCHEMA = 1
LEVELS = range(1, 16)
# Item tuple fields stored as fractions (0.25 means 25%).
FRACTION_FIELDS = ("as", "crit", "ls", "pctpen", "pctmpen")
# Components whose movement speed is a flat value; every other item's MS is a fraction of base MS.
FLAT_MS_COMPONENTS = {"Boots of Speed"}
DECIMALS = 4


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


def _champion(name, record):
    return {
        "name": name,
        "icon": _icon("champions", name),
        "attack_type": record.get("attack_type"),
        "resource_type": record.get("resource_type"),
        "stats": {key: _number(value) for key, value in record["stats"].items()},
        "levels": {
            str(level): {
                key: _number(value) for key, value in champion_level_stats(name, level).items()
            }
            for level in LEVELS
        },
        "source_status": record["source_status"],
        "wiki_source_url": record.get("wiki_source_url"),
        "wiki_last_change_patch": record.get("wiki_last_change_patch"),
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
    }


def render_database_json():
    """The exact text of app-data/database.json."""
    return json.dumps(build_database(), ensure_ascii=False, allow_nan=False, indent=1) + "\n"
