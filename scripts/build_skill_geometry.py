"""Presentation geometry from existing WR evidence. Does not fill combat-engine fields."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
MOVES={'Caitlyn':{'E':'recoil'},'Corki':{'W':'dash'},'Ezreal':{'E':'blink'},"Kai'Sa":{'R':'target-dash'},'Lucian':{'E':'dash'},'Samira':{'E':'target-dash'},'Tristana':{'W':'jump'},'Vayne':{'Q':'roll'},'Zeri':{'E':'slide'}}
SELF={'buff','guard','rally','passive','fade','ascend','orbit','sprint','switch','brandish'}
GROUND={'place','bomb','artillery','point','throw'}
CONE={('Ashe','W'),('Corki','E'),('Miss Fortune','R'),('Jhin','R'),('Smolder','W')}
def values(text):
 text=str(text or '').replace('−','-');text=re.sub(r'(?<=\d)\.\s+(?=\d)','.',text)
 if not re.fullmatch(r'\s*\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)*\s*',text):return None
 return[float(x.strip())for x in text.split('/')]
def main():
 profiles=json.loads((ROOT/'data/marksman-art-direction.json').read_text())['champions'];abilities=json.loads((ROOT/'data/marksman-ability-catalogue.json').read_text())['champions'];stats={p['name']:p['stats']for p in json.loads((ROOT/'data/marksman_champion_stats.json').read_text())['champions']};champions={}
 for name,p in profiles.items():
  slots={'AA':{'shape':'target','range':[stats[name].get('attack_range')],'source':'data/marksman_champion_stats.json','status':'database','label':'Basic attack'}}
  for slot,a in abilities[name]['abilities'].items():
   raw=a.get('wr_wiki_metadata',{}).get('parameters',{});pose=p['passive']['pose']if slot=='P'else p['skills'][slot]['pose'];effect=p['passive']['effect']if slot=='P'else p['skills'][slot]['effect'];motion=MOVES.get(name,{}).get(slot)
   cast=values(raw.get('target range'))or a.get('target_range_by_rank');travel=values(raw.get('range'))or([a['range']]if a.get('range')is not None else None);radius=values(raw.get('effect radius'))or a.get('effect_radius_by_rank');global_range=any('global'in str(raw.get(k,'')).lower()for k in['range','target range']);r=cast or travel
   shape='self'if slot=='P'or pose in SELF else'area'if pose in GROUND and radius else'line';shape='cone'if(name,slot)in CONE else shape
   if shape=='cone':r=r or radius
   if motion:shape=motion
   if shape=='self':r=radius
   if(name,slot)in[('Tristana','E'),('Tristana','R')]:r=[545];shape='target'
   if name=='Samira'and slot=='Q':r=[950]if raw.get('range')=='950 / 400'else r;shape='line'
   movement_range=cast if motion in['blink','dash','jump']else travel if motion=='slide'else None
   # A target radius (Kai'Sa R) is never treated as a dash length. Net range isn't recoil distance.
   if motion=='target-dash':movement_range=None
   if name=='Samira'and slot=='E':movement_range=[650]
   if name=='Zeri'and slot=='W'and raw.get('range')=='1200 \\ 1500':r=[1200]
   if name=='Smolder'and slot=='R'and raw.get('range')=='3300 / -500':r=[3300]
   if name=="Kai'Sa"and slot=='Q':shape='self';r=cast
   if name=='Smolder'and slot=='Q':shape='target'
   if name=='Caitlyn'and slot=='W':shape='area'
   if name=='Caitlyn'and slot=='R':shape='target'
   slots[slot]={'shape':shape,'range':r,'travel_range':travel,'movement_range':movement_range,'radius':radius,'width':values(raw.get('width')),'global':global_range,'source':a.get('timing_source')or a.get('wr_wiki_metadata',{}).get('url'),'status':'database'if r or global_range else'unresolved','label':a['name'],'raw':{k:raw.get(k,'')for k in['range','target range','effect radius','width']}}
   if name=='Tristana'and slot in['E','R']:slots[slot]['level_range']={'base':545,'per_level':10,'max_level':15};slots[slot]['status']='database_level_scaled'
  champions[name]={'slots':slots,'attack_level_range':{'base':545,'per_level':10,'max_level':15}if name=='Tristana'else None}
 out={'schema':1,'units_per_world_unit':100,'policy':'Existing WR database geometry only. Rank 1 / level 1 defaults; global ranges remain unbounded. Unknown values are labeled, never replaced by PC ranges. Authoring fallback movement distances are explicitly previews.','champions':champions}
 (ROOT/'data/marksman-skill-geometry.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)+'\n')
 print('Skill geometry:',len(champions),'champions;',sum(s['status']=='unresolved'for c in champions.values()for s in c['slots'].values()),'unresolved slots (including self skills without numerical radius)')
if __name__=='__main__':main()
