"""Same Tier List search, constrained pool and progressive budgets; resumable."""
import sys,json,argparse
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root),str(root/'tests')]
from sharpwr import engine_namespace,profiles_by_target
from build_fight_optimizer import BuildFightEvaluator,search_builds,TIER3
from core_items import BUDGETS,EXCLUDED,available,rank_core,fingerprint
p=argparse.ArgumentParser();p.add_argument('--champion',action='append');p.add_argument('--output',default=str(root/'data/champion-core-items.json'));args=p.parse_args()
ns=engine_namespace()
profiles=profiles_by_target()
def target_at(profile,level):
 if level in profile:return profile[level]
 lo=max(l for l in profile if l<level);hi=min(l for l in profile if l>level);u=(level-lo)/(hi-lo)
 return {**{k:profile[lo][k]+u*(profile[hi][k]-profile[lo][k]) for k in ('hp','armor','mr')},'aa_reduction':profile[hi].get('aa_reduction',0) if level>=5 else 0}
path=Path(args.output);sig=fingerprint();data=json.loads(path.read_text()) if path.exists() else {}
if data.get('fingerprint')!=sig:data={'version':'5.82.0','fingerprint':sig,'excluded':sorted(EXCLUDED),'budgets':BUDGETS,'method':'Tier List search: beam80/refine40, all Tier3 boots, default engine/runes, Standard Fight; Top3 weighted 1/1/2/1/3 per eligible cell, equal stage/target weighting. Muramana eligibility starts at11. Bounded search, not exhaustive.','champions':{}}
for name in args.champion or ns['C']:
 record=data['champions'].setdefault(name,{'complete':False,'cells':{},'ranking':[]})
 for level,count in BUDGETS.items():
  for target,profile in profiles.items():
   key=f'{level}:{target}'
   if key in record['cells']:continue
   t=target_at(profile,level);natural=t['hp'] if target=='squishy' else 660+148*ns['gu'](level) if target=='bruiser' else 690+132*ns['gu'](level)
   stacks=0 if level<=5 else 125 if level>=9 else round(125*(level-5)/4)
   ev=BuildFightEvaluator(ns,name,level,t['hp'],t['armor'],t['mr'],mist=40 if name=='Senna' else 0,bonus_hp=max(0,t['hp']-natural),aa_reduction=t.get('aa_reduction',0),yuntal_stacks=stacks)
   search=search_builds(ev,[i for i in ns['F'] if available(i,level)],[b for b in TIER3 if b in ns['B']],max_items=count)
   # Keep exact policy/stat details for each selected full finalist.
   search.pop('stages',None);search.pop('marginal',None)
   record['cells'][key]={'level':level,'target':target,'budget':count,'yuntal_start_stacks':stacks,'search':search}
   record['ranking']=rank_core(record['cells'],ns['F']);record['complete']=len(record['cells'])==18
   path.write_text(json.dumps(data,separators=(',',':')))
   print(name,key,search['simulations'],record['ranking'][0]['Item'] if record['ranking'] else '-',flush=True)
 print('COMPLETE',name,record['ranking'][:2],flush=True)
