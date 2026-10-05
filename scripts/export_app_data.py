"""Write app-data/database.json, the read-only Database the mobile app ships with, and
app-data/golden/, the Python results the app's TypeScript engine port is tested against.

Run after changing champion, item, boots or rune data, the published tier list or the saved
core-item results, and after engine changes (stale core results are exported as null);
tests/test_app_data.py fails while the committed file is out of date.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sharpwr.app_data import render_database_json
from sharpwr.golden import build_stats_golden, render_golden_json

OUTPUTS = {
    ROOT / "app-data" / "database.json": render_database_json,
    ROOT
    / "app-data"
    / "golden"
    / "build-stats.json": lambda: render_golden_json(build_stats_golden()),
}

if __name__ == "__main__":
    for path, render in OUTPUTS.items():
        path.parent.mkdir(exist_ok=True)
        path.write_text(render())
        print(path.relative_to(ROOT))
