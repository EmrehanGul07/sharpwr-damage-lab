"""Source-preserving ability catalogue. Unknown fields are None, never zero.

This catalogue is separate from fight support: registering an ability does not
make its champion executable by the timeline engine.
"""
import json
from pathlib import Path
import math

ROOT=Path(__file__).resolve().parents[1]

def catalogue():
    return json.loads((ROOT/'data/marksman-ability-catalogue.json').read_text())['champions']

def ability(champion,slot):
    if slot not in ('P','Q','W','E','R'):raise ValueError('Unknown ability slot')
    if champion not in catalogue():raise ValueError('Unknown champion')
    return catalogue()[champion]['abilities'][slot]

def mana_cost(champion,slot,rank):
    data=ability(champion,slot)
    limit=3 if slot=='R' else 4
    if slot=='P' or not isinstance(rank,int) or isinstance(rank,bool) or not 0<=rank<=limit:
        raise ValueError('Invalid active ability rank')
    if rank==0:return 0.
    costs=data['mana_by_rank']
    if costs is None:raise LookupError(f'{champion} {slot}: mana is unresolved')
    return float(costs[rank-1])

def cooldown(champion,slot,rank,haste=0.):
    data=ability(champion,slot)
    limit=3 if slot=='R' else 4
    if slot=='P' or not isinstance(rank,int) or isinstance(rank,bool) or not 1<=rank<=limit:raise ValueError('Invalid active ability rank')
    if not math.isfinite(haste) or haste<0:raise ValueError('Invalid haste')
    values=data['cooldown_by_rank']
    if values is None:raise LookupError(f'{champion} {slot}: cooldown is unresolved')
    return values[rank-1]/(1+haste/100)
