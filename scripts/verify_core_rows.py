"""Verify every stored finalist under its exact winning policy.

Usage: python scripts/verify_core_rows.py REPO OUTPUT_JSON
Run for baseline and candidate repositories, then compare rows exactly.
This does not rerun the bounded search or establish global optimality.
"""
import sys,json
from pathlib import Path
root=Path(sys.argv[1]);sys.path[:0]=[str(root),str(root/'scripts')]
from sharpwr import engine_namespace,profiles_by_target
from build_fight_optimizer import BuildFightEvaluator
ns=engine_namespace();profiles=profiles_by_target()
def target_at(profile,level):
 if level in profile:return profile[level]
 lo=max(l for l in profile if l<level);hi=min(l for l in profile if l>level);u=(level-lo)/(hi-lo)
 return {**{k:profile[lo][k]+u*(profile[hi][k]-profile[lo][k]) for k in ('hp','armor','mr')},'aa_reduction':profile[hi].get('aa_reduction',0) if level>=5 else 0}
payload=json.loads((root/'data/champion-core-items.json').read_text());output={};warnings={};count=0
for name,record in payload['champions'].items():
 warnings[name]=set()
 for key,cell in record['cells'].items():
  level=cell['level'];target=cell['target'];t=target_at(profiles[target],level);natural=t['hp'] if target=='squishy' else 660+148*ns['gu'](level) if target=='bruiser' else 690+132*ns['gu'](level)
  ev=BuildFightEvaluator(ns,name,level,t['hp'],t['armor'],t['mr'],mist=40 if name=='Senna' else 0,bonus_hp=max(0,t['hp']-natural),aa_reduction=t.get('aa_reduction',0),yuntal_stacks=cell['yuntal_start_stacks'])
  for index,row in enumerate(cell['search']['full']):
   trace=ev.replay_row(row);count+=1;warnings[name].update(trace.assumptions)
   output[f'{name}/{key}/{index}']={'damage':trace.total_damage,'ttk':trace.killed_at,'remaining':trace.hp_remaining,'hits':[(x['time'],x['action'],x['damage']) for x in trace.log]}
 print(name,count,flush=True)
Path(sys.argv[2]).write_text(json.dumps({'count':count,'rows':output,'warnings':{k:sorted(v) for k,v in warnings.items()}},separators=(',',':')))
