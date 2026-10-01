"""Source-attributed marksman stats; null is unknown, never zero-filled."""
import json
from pathlib import Path

DATABASE=json.loads((Path(__file__).resolve().parent/'data/marksman_champion_stats.json').read_text())
CHAMPION_DATABASE={record['name']:record for record in DATABASE['champions']}

def champion_record(name):
    return CHAMPION_DATABASE[name]

def champion_stat(name,field):
    return champion_record(name)['stats'].get(field)


def level_stats(name, level, growth_units=None):
    """Resolve core stats using the app's existing growth curve (not a new WR claim)."""
    if not isinstance(level, int) or not 1 <= level <= 15:
        raise ValueError('Invalid champion level.')
    u = (level-1)*(.7025+.0175*(level-1)) if growth_units is None else growth_units
    raw = champion_record(name)['stats']
    pairs = {'hp':('base_hp','hp_growth'), 'mana':('base_mana','mana_growth'),
             'hp_regen_per_5s':('base_hp_regen_per_5s','hp_regen_growth_per_5s'),
             'mana_regen_per_5s':('base_mana_regen_per_5s','mana_regen_growth_per_5s'),
             'armor':('base_armor','armor_growth'), 'mr':('base_mr','mr_growth')}
    out = {key: None if raw.get(b) is None or raw.get(g) is None else raw[b]+raw[g]*u
           for key,(b,g) in pairs.items()}
    out.update({key:raw.get(key) for key in ('movement_speed','attack_range')})
    return out
