"""Write app-data/database.json, the read-only Database the mobile app ships with, its ability
icons under assets/riot/abilities/, app-data/practice.json, the Practice tab's champions and engine
numbers, and app-data/golden/, the Python results the app's TypeScript engine port is tested against.

Run after changing champion, item, boots or rune data, the published tier list or the saved
core-item results, and after engine changes (stale core results are exported as null);
tests/test_app_data.py fails while the committed file is out of date.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from marksman_art import practice_catalogue
from sharpwr.app_data import ability_icon_files, render_database_json
from sharpwr.golden import build_stats_golden, render_golden_json
from sharpwr.practice_data import render_practice_json

OUTPUTS = {
    ROOT / "app-data" / "database.json": render_database_json,
    ROOT
    / "app-data"
    / "golden"
    / "build-stats.json": lambda: render_golden_json(build_stats_golden()),
    ROOT / "app-data" / "practice.json": lambda: render_practice_json(practice_catalogue(icon_files=True)),
}

if __name__ == "__main__":
    for path, render in OUTPUTS.items():
        path.parent.mkdir(exist_ok=True)
        path.write_text(render())
        print(path.relative_to(ROOT))
    icons = ability_icon_files()
    for name, data in icons.items():
        (ROOT / name).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / name).write_bytes(data)
    print(f"{len(icons)} ability icons")
