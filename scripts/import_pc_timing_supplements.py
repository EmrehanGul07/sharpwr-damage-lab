"""Supplement missing wiki timing with exact Riot game missile movement records.
Pinned PC 16.19; CommunityDragon decodes Riot assets. Generic missileSpeed values
are not trusted: actual movement components take precedence. No damage import.
"""
import json
from pathlib import Path
import requests
ROOT=Path(__file__).resolve().parents[1]
BASE='https://raw.communitydragon.org/16.19/game/data/characters/'
TARGETS={
 'Jinx':{'aa_minigun':'Characters/Jinx/Spells/JinxBasicAttack','aa_rockets':'Characters/Jinx/Spells/JinxQAbility/JinxQAttack'},
 'Varus':{'E':'Characters/Varus/Spells/VarusEMissile'},
 'Xayah':{'R':'Characters/Xayah/Spells/XayahRAbility/XayahRMissile','Q_raw_only':'Characters/Xayah/Spells/XayahQAbility/XayahQMissile1'},
 'Samira':{'R':'Characters/Samira/Spells/SamiraRAbility/SamiraRMissile'},
 "Kai'Sa":{'Q':'Characters/Kaisa/Spells/KaisaQAbility/KaisaQLeftMissile1'},
 'Jhin':{'E':'Characters/Jhin/Spells/JhinEAbility/JhinETrap'},
}
def main():
 timing=json.loads((ROOT/'data/pc-combat-timing.json').read_text());cat=json.loads((ROOT/'data/marksman-ability-catalogue.json').read_text());stats=json.loads((ROOT/'data/marksman_champion_stats.json').read_text())
 supplements={}
 for name,targets in TARGETS.items():
  slug='kaisa' if name=="Kai'Sa" else name.lower();url=BASE+slug+'/'+slug+'.bin.json'
  response=requests.get(url,timeout=40);response.raise_for_status();raw=response.json()
  for slot,path in targets.items():
   movement=raw[path]['mSpell']['mMissileSpec']['movementComponent']
   evidence={'source':url,'record':path,'movement_type':movement['__type'],**{k:movement[k] for k in ('mSpeed','mTravelTime') if k in movement}}
   supplements[name+' '+slot]=evidence
   c=timing['champions'][name]
   if slot.startswith('aa_'):
    c['aa']['variants'][slot[3:]]=movement['mSpeed'];c['aa']['game_file_source']=url;c['aa']['status']='sourced_riot_game_files'
    if slot=='aa_minigun':
     c['aa']['projectile_speed']=movement['mSpeed']
     r=next(x for x in stats['champions'] if x['name']==name);r['stats']['attack_projectile_speed']=movement['mSpeed'];r['field_sources']['attack_projectile_speed']=evidence;r['unavailable_fields']=[k for k in r['unavailable_fields'] if k!='attack_projectile_speed']
   elif slot.endswith('_raw_only'):
    # Xayah scripts may override 400; retain evidence without claiming effective speed.
    c['abilities'][slot[0]]['raw_game_movement']=evidence;c['abilities'][slot[0]]['speed_status']='raw_asset_only_runtime_override_unresolved'
   else:
    a=c['abilities'][slot];a['game_movement']=evidence;a['speed_status']='sourced_fixed_time' if 'mTravelTime' in movement else 'sourced_game_movement'
    if 'mSpeed' in movement:a['speed_scalar']=movement['mSpeed'];cat['champions'][name]['abilities'][slot]['projectile_speed']=movement['mSpeed'];cat['champions'][name]['abilities'][slot]['projectile_speed_source']=url
    if 'mTravelTime' in movement:a['fixed_travel_seconds']=movement['mTravelTime']
    cat['champions'][name]['abilities'][slot]['pc_timing_reference']=a
 (ROOT/'data/pc-timing-game-supplements.json').write_text(json.dumps(supplements,ensure_ascii=False,indent=2)+'\n')
 for path,data in [('pc-combat-timing.json',timing),('marksman-ability-catalogue.json',cat),('marksman_champion_stats.json',stats)]:
  (ROOT/'data'/path).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
