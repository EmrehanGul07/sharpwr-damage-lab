"""Explicit PC timing proxies, applied to WR stats without changing WR damage."""
import json
from functools import lru_cache
from pathlib import Path
@lru_cache(maxsize=1)
def database():return json.loads((Path(__file__).resolve().parent/'data/pc-combat-timing.json').read_text())['champions']
def base_windup(champion):return database()[champion]['aa']['base_windup_seconds']
def attack_windup(champion,bonus_as):
    if champion=='Senna':return .5/(1+.6*bonus_as)
    return base_windup(champion)/(1+.5*max(0.,bonus_as))
def attack_travel(champion,distance,*,melee=False,weapon=None,ultimate=False):
    if melee and champion=='Samira':return 0.
    aa=database()[champion]['aa'];speed=aa['projectile_speed']
    if champion=='Jinx':speed=aa['variants'].get('rockets' if weapon=='rockets' else 'minigun')
    if champion=='Twitch' and ultimate:speed=aa['variants'].get('ultimate',speed)
    return distance/speed if speed else 0.
def skill_travel(champion,slot,distance):
    a=database()[champion]['abilities'][slot]
    if (slot=='E' and champion in ('Samira','Lucian','Zeri')) or (slot=='Q' and champion=='Vayne') or (slot=='W' and champion in ('Tristana','Corki')) or (slot=='R' and champion=="Kai'Sa"):return 0.
    if a.get('fixed_travel_seconds') is not None:return a['fixed_travel_seconds']
    if a.get('projectile_expression','').lower()=='false':return 0.
    if champion=='Ashe' and slot=='R':
        # PC source: 1500 initial, +200 units/s each second, capped 2100.
        if distance<=5400:return (-1500+(1500**2+400*distance)**.5)/200
        return 3+(distance-5400)/2100
    if champion=='Jinx' and slot=='R':return min(distance,1350)/1700+max(0,distance-1350)/2200
    if champion=='Sivir' and slot=='Q':return distance/1450
    if champion=='Yunara' and slot=='W':return distance/2150
    variants=a.get('speed_variants',[])
    speed=a.get('speed_scalar')
    if speed is None and variants and not any(w in variants[0]['label'].lower() for w in ('dash','knockback')):speed=variants[0]['speed']
    return distance/speed if speed else None
def skill_cast_time(champion,slot,bonus_as,level=1):
    a=database()[champion]['abilities'][slot]
    if a.get('cast_time_seconds') is not None:return a['cast_time_seconds']
    if (champion,slot) in [('Tristana','E'),("Kog'Maw",'Q'),('Miss Fortune','Q'),('Smolder','Q')]:return attack_windup(champion,bonus_as)
    if champion=='Xayah' and slot=='Q':return max(.1,.25-.07*bonus_as)
    if champion=='Yunara' and slot=='W':return .45-.225*min(1.,bonus_as)
    if champion=="Kai'Sa" and slot=='E':return max(.6,1.2/(1+bonus_as))
    if champion=='Jinx' and slot=='W':return .6-.2*min(1.,bonus_as/2.5)
    if champion=='Zeri' and slot=='W':return max(.3,.55-.09*bonus_as)
    if champion=='Sivir' and slot=='Q':return max(.1,.25*(1-.5*bonus_as))
    if champion=='Senna' and slot=='Q':return .8*attack_windup(champion,bonus_as)
    if champion=='Jhin' and slot=='R':return 1.
    return None
