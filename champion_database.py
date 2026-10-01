"""Source-attributed marksman stats; null is unknown, never zero-filled."""
import json
from pathlib import Path

DATABASE=json.loads((Path(__file__).resolve().parent/'data/marksman_champion_stats.json').read_text())
CHAMPION_DATABASE={record['name']:record for record in DATABASE['champions']}

def champion_record(name):
    return CHAMPION_DATABASE[name]

def champion_stat(name,field):
    return champion_record(name)['stats'].get(field)
