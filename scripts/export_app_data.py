"""Write app-data/database.json, the read-only Database the mobile app ships with.

Run after changing champion, item, boots or rune data; tests/test_app_data.py fails while
the committed file is out of date.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from sharpwr.app_data import render_database_json

OUTPUT = ROOT / "app-data" / "database.json"

if __name__ == "__main__":
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(render_database_json())
    print(OUTPUT.relative_to(ROOT))
