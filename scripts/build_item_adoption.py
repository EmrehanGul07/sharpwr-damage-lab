"""Progressive item-budget screen across six equally weighted game stages."""
import sys,json,ast,hashlib,argparse
from pathlib import Path
sys.path[:0]=[str(Path(__file__).resolve().parents[1]),str(Path(__file__).resolve().parents[1]/'tests')]
from test_combat_engine import engine_namespace
from build_fight_optimizer import BuildFightEvaluator,legal,score,diverse_shortlist
from item_consensus import progression_ranking
parser=argparse.ArgumentParser()
parser.add_argument('--champion', action='append', help='Recompute only selected champion(s), preserving other checkpoint cells')
parser.add_argument('--checkpoint', help='Separate checkpoint path for an isolated worker')
parser.add_argument('--output', help='Separate output path for an isolated worker')
parser.add_argument('--refresh', action='store_true', help='Discard selected completed cells before recomputing')
args=parser.parse_args()
root=Path(__file__).resolve().parents[1];ns=engine_namespace();targets={}
for node in ast.parse((root/'streamlit_app.py').read_text()).body:
 if isinstance(node,ast.Assign):
  for x in node.targets:
   if isinstance(x,ast.Name) and x.id in ('SQUISHY_JINX_PROFILE','BRUISER_DARIUS_PROFILE','TANK_ORNN_PROFILE'):targets[x.id.split('_')[0].lower()]=ast.literal_eval(node.value)
def target_at(profile,level):
 if level in profile:return profile[level]
 lo=max(l for l in profile if l<level);hi=min(l for l in profile if l>level);u=(level-lo)/(hi-lo)
 t={k:profile[lo][k]+u*(profile[hi][k]-profile[lo][k]) for k in ('hp','armor','mr')};t['aa_reduction']=profile[hi].get('aa_reduction',0) if level>=5 else 0
 return t
budgets={5:1,7:1,9:2,11:3,13:4,15:5};fingerprint=hashlib.sha256(repr(ns['F']).encode()).hexdigest();checkpoint=Path(args.checkpoint) if args.checkpoint else root/'data/item-progression-checkpoint.json'
state=json.loads(checkpoint.read_text()) if checkpoint.exists() else {'fingerprint':fingerprint,'results':{},'simulations':0}
if state['fingerprint']!=fingerprint:raise ValueError('Checkpoint uses different item stats')
selected=args.champion or list(ns['C'])
if any(n not in ns['C'] for n in selected):raise ValueError('Unknown champion')
if args.refresh:
 for name in selected:
  removed=state['results'].pop(name,{})
  state['simulations']-=sum(cell['simulations'] for cell in removed.values())
 checkpoint.write_text(json.dumps(state,separators=(',',':')))
for champion in selected:
 cells=state['results'].setdefault(champion,{})
 for target,profile in targets.items():
  beam=[()]
  for level,count in budgets.items():
   key=f'{level}:{target}'
   if key in cells:
    beam=[tuple(r['Items']) for r in cells[key]['beam']];continue
   t=target_at(profile,level);natural=t['hp'] if target=='squishy' else (660+148*ns['gu'](level) if target=='bruiser' else 690+132*ns['gu'](level))
   stacks=0 if level<=5 else (125 if level>=9 else round(125*(level-5)/4))
   ev=BuildFightEvaluator(ns,champion,level,t['hp'],t['armor'],t['mr'],bonus_hp=max(0,t['hp']-natural),aa_reduction=t.get('aa_reduction',0),yuntal_stacks=stacks)
   pool=[i for i in ns['F'] if i!='Muramana' or level>=11]
   if count==1:candidates=[(i,) for i in pool]
   else:candidates=sorted({tuple(sorted((*seed,i))) for seed in beam for i in pool if i not in seed and legal((*seed,i))})
   rows=[ev.evaluate(items) for items in candidates];rows.sort(key=score)
   selected=diverse_shortlist(ev,rows,12)
   refined=[ev.evaluate(r['Items'],refine='rotations') for r in selected];refined.sort(key=score)
   # Re-rank the twelve candidates at this stage; retain variety for the next budget.
   beam=[r['Items'] for r in diverse_shortlist(ev,refined,12)]
   cells[key]={'level':level,'target':target,'item_count':count,'yuntal_start_stacks':stacks,'builds':refined[:10],'beam':refined,'candidates':len(candidates),'simulations':ev.simulations}
   state['simulations']+=ev.simulations;checkpoint.write_text(json.dumps(state,separators=(',',':')))
   print(champion,key,ev.simulations,'total',state['simulations'],flush=True)
payload={'version':'5.80.0','levels':list(budgets),'item_budgets':budgets,'champions':len(state['results']),'targets':3,'simulations':state['simulations'],'method':'Equal level/target weighting. Exact single-item enumeration; later budgets grow a diverse 12-build beam, followed by rotation checks. Top-10 build reciprocal-rank item share is normalized by item count. Adoption = present in at least one retained build, once per champion. Muramana excluded below level 11. No boots/runes; expected crit; Yun Tal uses level-dependent starting progression (0 at 5, 62 at 7, 125 at 9+). Not exhaustive full-build optimization. Yunara uses user-verified level snapshots for HP/mana/armor/MR, MS 335 and range 575; all 15 levels are observed; mana regeneration uses user-confirmed per-5-second values. Normal Yunara W includes four linger ticks over one second.','fingerprint':fingerprint,'ranking':progression_ranking(state['results'],ns['F']),'results':state['results']}
for cells in payload['results'].values():
 for cell in cells.values():
  cell.pop('beam',None)
  cell['builds']=[{k:r[k] for k in ('Items','DPS','TTK','Damage','Crit %','Rotation')} for r in cell['builds']]
(Path(args.output) if args.output else root/'data/item-adoption-screen.json').write_text(json.dumps(payload,separators=(',',':')))
print('DONE',state['simulations'],flush=True)
