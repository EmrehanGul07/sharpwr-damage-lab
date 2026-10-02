"""Paired Ezreal build diagnostics; preserves live engine coefficients."""
import ast,json,sys,collections
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root),str(root/'tests')]
from test_combat_engine import engine_namespace
from build_fight_optimizer import BuildFightEvaluator
from marksman_kits import records
ns=engine_namespace();profiles={}
for node in ast.parse((root/'streamlit_app.py').read_text()).body:
 if isinstance(node,ast.Assign):
  for target in node.targets:
   if isinstance(target,ast.Name) and target.id in ('SQUISHY_JINX_PROFILE','BRUISER_DARIUS_PROFILE','TANK_ORNN_PROFILE'):profiles[target.id.split('_')[0].lower()]=ast.literal_eval(node.value)[15]
sets={
 'crit':['Duskblade of Draktharr','Infinity Edge',"Lord Dominik's Regards",'The Collector','Yun Tal Wildarrows'],
 'muramana_trinity':['Muramana','Trinity Force',"Lord Dominik's Regards",'Blade of the Ruined King','Navori Quickblades'],
 'muramana_er':['Muramana','Essence Reaver',"Lord Dominik's Regards",'Blade of the Ruined King','Navori Quickblades'],
 'trinity_no_muramana':['Duskblade of Draktharr','Trinity Force',"Lord Dominik's Regards",'Blade of the Ruined King','Navori Quickblades']}
checkpoint=json.loads((root/'data/item-progression-checkpoint.json').read_text());q=records()['Ezreal']['abilities']['Q'];original=list(q['cooldown_by_rank']);out=[]
for target,p in profiles.items():
 sets['current_screen_winner']=checkpoint['results']['Ezreal']['15:'+target]['builds'][0]['Items']
 for rules in ('engine_current','alternate_WR_metadata_CD'):
  q['cooldown_by_rank']=original if rules=='engine_current' else [4.5,4,3.5,3]
  for runes in (False,True):
   overrides={'keystone':'Conqueror','sub_runes':('Brutal','Cut Down','Legend: Bloodline','Bone Plating')} if runes else {'keystone':None,'sub_runes':()}
   natural=p['hp'] if target=='squishy' else 660+148*ns['gu'](15) if target=='bruiser' else 690+132*ns['gu'](15)
   ev=BuildFightEvaluator(ns,'Ezreal',15,p['hp'],p['armor'],p['mr'],bonus_hp=max(0,p['hp']-natural),aa_reduction=p.get('aa_reduction',0),yuntal_stacks=125,retain_traces=True,simulation_overrides=overrides)
   for name,items in sets.items():
    row=ev.evaluate(items,'Armorcrusher Boots',refine=True);trace=ev.traces[(tuple(sorted(items)),'Armorcrusher Boots',True)]
    by=collections.defaultdict(float);counts=collections.Counter()
    for e in trace.log:by[e['action']]+=e['damage'];counts[e['action']]+=1
    procs=collections.Counter(x for e in trace.log for x in e.get('effects',[]) if x in ('ER','Trinity','Nightstalker','Flurry','Phantom Hit'))
    out.append({'target':target,'target_stats':p,'rules':rules,'runes':runes,'build_name':name,'row':row,'damage_by_action':dict(by),'hits_by_action':dict(counts),'proc_counts':dict(procs),'trace':trace.log})
q['cooldown_by_rank']=original
payload={'version':'5.81.0','champion':'Ezreal','level':15,'boot':'Armorcrusher Boots','yuntal_stacks':125,'comparisons':out,'scope':'Fixed build families; same target, boot and starting progression. Full supported priority/movement/weaving search per build. Alternate cooldown is sensitivity only, not verified live data. No live engine coefficients changed.'}
(root/'data/ezreal-core-build-comparison.json').write_text(json.dumps(payload,separators=(',',':')))
lines=['# Ezreal paired build comparison','',payload['scope'],'','| Target | Runes | CD | Build | TTK | AA hits | Q hits | Q dealt |','|---|---|---|---|---:|---:|---:|---:|']
for r in out:lines.append(f"| {r['target']} | {r['runes']} | {r['rules']} | {r['build_name']} | {r['row']['TTK']:.3f} | {r['hits_by_action'].get('AA',0)} | {r['hits_by_action'].get('Q',0)} | {r['damage_by_action'].get('Q',0):.1f} |")
(root/'docs/ezreal-core-build-comparison.md').write_text('\n'.join(lines)+'\n')
for r in out:
 if r['rules']=='engine_current' and not r['runes']:print(r['target'],r['build_name'],round(r['row']['TTK'],3),r['hits_by_action'],r['proc_counts'],flush=True)
