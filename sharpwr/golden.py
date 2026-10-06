"""Golden outputs for the mobile app's port of the engine.

The app re-implements engine functions in TypeScript (mobile/src/engine/) and checks them
against these Python results (mobile/tests/). scripts/export_app_data.py writes them to
app-data/golden/; tests/test_app_data.py fails while the committed files are out of date.
"""

import json
from pathlib import Path

from .build_stats import build_stats
from .champion_database import CHAMPION_DATABASE
from .rune_pages import default_loadout

CORE_ITEMS = Path(__file__).resolve().parents[1] / "data" / "champion-core-items.json"
# Builds that exercise a special rule: crit damage, mana items, caps, champion conversions.
EDGE_CASES = (
    ("Senna", 9, ["Infinity Edge", "Yun Tal Wildarrows"], None, 0, 125),
    ("Senna", 15, ["Infinity Edge"], "Berserker's Greaves", 100, 0),
    ("Senna", 15, [], None, 500, 0),
    ("Ezreal", 11, ["Manamune", "Trinity Force"], "Ionian Boots of Lucidity", 0, 0),
    ("Ezreal", 15, ["Muramana", "Infinity Edge", "Nashor's Tooth"], None, 0, 0),
    ("Zeri", 15, ["Kraken Slayer", "Phantom Dancer", "Statikk Shiv"], "Berserker's Greaves", 0, 0),
    (
        "Jhin",
        13,
        ["Infinity Edge", "Yun Tal Wildarrows", "The Collector"],
        "Gunmetal Greaves",
        0,
        125,
    ),
    ("Kalista", 15, ["Yun Tal Wildarrows"], None, 0, 300),
    (
        "Twitch",
        15,
        [
            "Guinsoo's Rageblade",
            "Kraken Slayer",
            "Blade of the Ruined King",
            "Phantom Dancer",
            "Navori Quickblades",
        ],
        "Berserker's Greaves",
        0,
        0,
    ),
    ("Yunara", 7, ["Iceborn Gauntlet", "Edge of Night"], "Immortal Treads", 0, 0),
)


def _cases():
    seen = set()
    cases = []

    def add(champion, level, items, boots=None, mist=0, yuntal_stacks=0, runes=False):
        key = (champion, level, tuple(sorted(items)), boots, mist, yuntal_stacks, runes)
        if key not in seen:
            seen.add(key)
            cases.append(key)

    for name in CHAMPION_DATABASE:
        for level in (1, 5, 6, 9, 15):
            add(name, level, [])
            add(name, level, [], runes=True)
    for case in EDGE_CASES:
        add(*case)
        add(*case, runes=True)
    # Real builds: every saved finalist with the search's starting state and the default runes.
    for name, record in json.loads(CORE_ITEMS.read_text())["champions"].items():
        cells = [
            *record["cells"].values(),
            *record.get("top", {}).values(),
            *(
                cell
                for style in record.get("styles", [])
                if not style["keystone"]
                for cell in style["cells"].values()
            ),
        ]
        for cell in cells:
            for row in cell["search"]["full"]:
                mist = 40 if name == "Senna" else 0
                add(
                    name,
                    cell["level"],
                    row["Items"],
                    row["Boots"],
                    mist,
                    cell["yuntal_start_stacks"],
                    "top" in record,
                )
    return cases


def build_stats_golden():
    """Each case's runes flag means the champion's default rune page (app data rune_stats)."""
    return [
        {
            "champion": champion,
            "level": level,
            "items": list(items),
            "boots": boots,
            "mist": mist,
            "yuntal_stacks": stacks,
            "runes": runes,
            "expected": build_stats(
                champion,
                level,
                items,
                boots,
                mist=mist,
                yuntal_stacks=stacks,
                runes=default_loadout(champion, level) if runes else None,
            ),
        }
        for champion, level, items, boots, mist, stacks, runes in _cases()
    ]


def render_golden_json(cases):
    """One case per line, so reviews show which builds changed."""
    lines = (json.dumps(case, ensure_ascii=False, allow_nan=False) for case in cases)
    return "[\n" + ",\n".join(lines) + "\n]\n"
