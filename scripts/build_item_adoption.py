"""Small level-15 AA+ability screen: singles and additions to top-three singles."""
import sys,json,ast,hashlib
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'tests')]
from test_combat_engine import engine_namespace
from build_fight_optimizer import BuildFightEvaluator,legal
from collections import defaultdict
root=Path(__file__).resolve().parents[1];ns=engine_namespace();targets={}
for node in ast.parse((root/'streamlit_app.py').read_text()).body:
 if isinstance(node,ast.Assign):
  for x in node.targets:
   if isinstance(x,ast.Name) and x.id in ('SQUISHY_JINX_PROFILE','BRUISER_DARIUS_PROFILE','TANK_ORNN_PROFILE'):targets[x.id.split('_')[0].lower()]=ast.literal_eval(node.value)[15]
results={};simulations=0
for champion in ns['C']:
 results[champion]={}
 for target,t in targets.items():
  natural=t['hp'] if target=='squishy' else (660+148*ns['gu'](15) if target=='bruiser' else 690+132*ns['gu'](15))
  ev=BuildFightEvaluator(ns,champion,15,t['hp'],t['armor'],t['mr'],bonus_hp=max(0,t['hp']-natural),aa_reduction=t.get('aa_reduction',0),yuntal_stacks=125)
  baseline=ev.evaluate([])['DPS'];singles={i:ev.evaluate([i])['DPS'] for i in ns['F']};anchors=sorted(singles,key=singles.get,reverse=True)[:3];rows=[]
  for item in ns['F']:
   gains=[(singles[item]-baseline)/max(1,baseline)]
   for anchor in anchors:
    if item!=anchor and legal([item,anchor]):gains.append((ev.evaluate([item,anchor])['DPS']-singles[anchor])/max(1,singles[anchor]))
   rows.append({'item':item,'score':sum(gains)/len(gains),'single_dps':singles[item]})
  rows.sort(key=lambda x:(-x['score'],x['item']))
  results[champion][target]=rows;simulations+=ev.simulations
 print(champion,simulations,flush=True)
ranking=[]
for item in ns['F']:
 champions=[];appearances=0;scores=[]
 for champion,profiles in results.items():
  hit=False
  for rows in profiles.values():
   index=next(i for i,r in enumerate(rows) if r['item']==item);scores.append(rows[index]['score'])
   if index<5:appearances+=1;hit=True
  if hit:champions.append(champion)
 ranking.append({'Item':item,'Champions':len(champions),'Champion names':', '.join(champions),'Top-5 target appearances':appearances,'Mean DPS gain %':round(100*sum(scores)/len(scores),2)})
ranking.sort(key=lambda x:(-x['Champions'],-x['Top-5 target appearances'],-x['Mean DPS gain %'],x['Item']))
payload={'version':'5.68.0','level':15,'champions':len(results),'targets':3,'simulations':simulations,'method':'Single items plus legal additions to each champion/target top-three single-item anchors; mean relative DPS gain. Adoption = top five on at least one target. No boots, no runes, expected crit, Yun Tal starts at 125 stacks. Not full-build optimization. Yunara mana/MS/range fallback remains unverified.','fingerprint':hashlib.sha256(repr(ns['F']).encode()).hexdigest(),'ranking':ranking,'results':results}
(root/'data/item-adoption-screen.json').write_text(json.dumps(payload,indent=2))
print('DONE',simulations)
