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
    if isinstance(level,bool) or not isinstance(level, int) or not 1 <= level <= 15:
        raise ValueError('Invalid champion level.')
    u = (level-1)*(.7025+.0175*(level-1)) if growth_units is None else growth_units
    from combat_validation import finite
    finite(u,'growth units',0)
    raw = champion_record(name)['stats']
    pairs = {'hp':('base_hp','hp_growth'), 'mana':('base_mana','mana_growth'),
             'hp_regen_per_5s':('base_hp_regen_per_5s','hp_regen_growth_per_5s'),
             'mana_regen_per_5s':('base_mana_regen_per_5s','mana_regen_growth_per_5s'),
             'armor':('base_armor','armor_growth'), 'mr':('base_mr','mr_growth')}
    out = {key: None if raw.get(b) is None or raw.get(g) is None else raw[b]+raw[g]*u
           for key,(b,g) in pairs.items()}
    observations = champion_record(name).get('observed_level_stats', {})
    for key in ('hp', 'mana', 'armor', 'mr', 'mana_regen_per_5s'):
        points = sorted((int(l), values[key]) for l, values in observations.items() if key in values)
        exact = dict(points).get(level)
        if exact is not None:
            out[key] = exact
        elif points and points[0][0] < level < points[-1][0]:
            lo = max(p for p in points if p[0] < level)
            hi = min(p for p in points if p[0] > level)
            out[key] = lo[1] + (hi[1]-lo[1])*(level-lo[0])/(hi[0]-lo[0])
    out.update({key:raw.get(key) for key in ('movement_speed','attack_range')})
    return out
