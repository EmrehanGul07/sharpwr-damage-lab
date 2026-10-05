"""Riot artwork bundled for offline use, indexed by data/riot/icons.json.

Each entry maps a record name to a file under assets/riot/ and, when known, the URL it
was fetched from. scripts/fetch_riot_icons.py downloads entries whose file is missing.
"""

import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "data" / "riot" / "icons.json"
KINDS = ("items", "boots", "runes", "rune_trees", "champions")


@lru_cache(maxsize=1)
def manifest():
    return json.loads(MANIFEST.read_text())


def icon_entry(kind, name):
    """{'path': repository-relative file, 'source': URL or None}, or None when unmapped."""
    return manifest()[kind].get(name)


def icon_file(kind, name):
    """The bundled file for a record, or None when it is unmapped or not downloaded yet."""
    entry = icon_entry(kind, name)
    if entry is None:
        return None
    path = ROOT / entry["path"]
    return path if path.is_file() else None


def icon_source(kind, name):
    entry = icon_entry(kind, name)
    return entry["source"] if entry else None
