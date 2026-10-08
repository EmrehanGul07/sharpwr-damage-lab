"""Reference per-hit sequences for the mobile AA kernel, from the Python engine."""
import json
import gzip
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sharpwr.catalog import C,F
from sharpwr.aa_engine import combat_hits, sim_build
cases=[]
sets=[[],['Statikk Shiv',"Guinsoo's Rageblade"],["Guinsoo's Rageblade",'Kraken Slayer','Terminus'],['Blade of the Ruined King',"Guinsoo's Rageblade",'Terminus'],['Muramana','Trinity Force'],['Yun Tal Wildarrows','Infinity Edge','Phantom Dancer'],['Hexoptics C44',"Wit's End"],['Fiendhunter Bolts','Essence Reaver'],['Duskblade of Draktharr','The Collector'],["Nashor's Tooth","Lord Dominik's Regards"]]
for name in C:
 for level in [1,9,15]:
  for items in sets:
   if any(i not in F for i in items):continue
   params=dict(champion=name,level=level,items=items,boots='Immortal Treads',mist=40 if name=='Senna' else 0,yuntalStacks=125)
   target=dict(health=10000,armor=100,magicResist=100,bonusHealth=1000,attackReduction=.1)
   g=combat_hits(name,level,10000,100,100,items,F,mist=params['mist'],bonus_hp=1000,target_aa_reduction=.1,yuntal_start_stacks=125,energized=True,spell=True,boot=params['boots']);next(g)
   hp=10000;t=0;hits=[]
   for index in range(12):
    state={'hp':hp,'time':t}
    hit=g.send(state)
    hits.append({'state':{'health':hp,'time':t},'expected':{k:hit[k] for k in ['damage','as','crit','armor','mr','physical','magic','true','physical_damage','magic_damage','rage','light','dark','phantom_dancer','kraken','yuntal_crit','energized_charge']}})
    hp=max(0,hp-hit['damage']);t+=1/hit['as']
   row,_=sim_build(name,level,10000,100,100,items,F,mist=params['mist'],bonus_hp=1000,target_aa_reduction=.1,yuntal_start_stacks=125,energized=True,boot=params['boots'])
   cases.append({'input':params,'target':target,'options':{'energized':True,'spellblade':True},'hits':hits,'aa':{'ttk':row[2] if row[2]!=float('inf') else None,'attacks':row[3],'dps':row[4]}})
Path('app-data/golden/attacks.json.gz').write_bytes(gzip.compress(json.dumps(cases,separators=(',',':')).encode(),mtime=0))
print(len(cases),'sequences')
