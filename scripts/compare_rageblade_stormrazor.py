"""Paired diagnostics only: no edits to locked item coefficients or rankings."""
import json,sys,collections
from pathlib import Path
root=Path(__file__).resolve().parents[1];sys.path[:0]=[str(root),str(root/'tests')]
from sharpwr import engine_namespace,profiles_by_target
from sharpwr.build_fight_optimizer import BuildFightEvaluator,legal
from sharpwr.champion_database import level_stats
ns=engine_namespace();screen=json.loads((root/'data/item-adoption-screen.json').read_text());screen['results']=json.loads((root/'data/item-progression-checkpoint.json').read_text())['results']
profiles=profiles_by_target()
G="Guinsoo's Rageblade";S='Stormrazor';results=[]
def measure(champ,level,target,common,policy,charged):
 t=profiles[target][level];natural=t['hp'] if target=='squishy' else (660+148*ns['gu'](level) if target=='bruiser' else 690+132*ns['gu'](level))
 overrides=dict(keystone='Conqueror',sub_runes=('Brutal','Cut Down'),skill_priority=tuple(policy['Rotation'].split(' → ')),movement_policy=policy['Movement'],ultimate_policy=policy['Ultimate timing'],action_policy=policy['Attack weaving'],use_e=policy['E enabled'],weapon=policy['Weapon'])
 if policy.get('Recall minimum') is not None:overrides['recall_min_feathers']=policy['Recall minimum']
 boot='Boots of Dynamism' if level==5 else 'Armorcrusher Boots'
 ev=BuildFightEvaluator(ns,champ,level,t['hp'],t['armor'],t['mr'],bonus_hp=max(0,t['hp']-natural),aa_reduction=t.get('aa_reduction',0),energized=charged,yuntal_stacks=0 if level==5 else 125,retain_traces=True,simulation_overrides=overrides)
 out={}
 for item in (G,S):
  build=common+[item];r=ev.evaluate(build,boot);trace=ev.traces[(tuple(sorted(build)),boot,False)]
  proc=collections.Counter(effect for row in trace.log for effect in row.get('effects',[]) if effect in ('Phantom Hit','Storm Energized','Kraken','Kraken (Phantom)'))
  rawcrit=sum(ns['dct'](ns['F'][x])['crit'] for x in build)+(.25 if 'Yun Tal Wildarrows' in build and level==15 else 0)
  early={str(sec):sum(row['damage'] for row in trace.log if row['time']<=sec) for sec in (1,2,3)}
  out[item]={'ttk':r['TTK'],'damage':r['Damage'],'damage_at_seconds':early,'dead_by_seconds':{str(sec):r['TTK'] is not None and r['TTK']<=sec for sec in (1,2,3)},'aa_count':trace.aa_count,'skill_count':trace.skill_count,'ad':r['AD'],'ap':r['AP'],'crit_percent':r['Crit %'],'raw_crit_percent':100*rawcrit,'starting_as':r['Starting AS'],'procs':dict(proc),'assumptions':r['Assumptions']}
 a,b=out[G]['ttk'],out[S]['ttk'];winner='tie' if a==b else G if b is None or a is not None and a<b else S
 return {'champion':champ,'level':level,'target':target,'common_items':common,'boots':boot,'energized_at_start':charged,'policy':overrides,'items':out,'ttk_winner':winner}
for champ,cells in screen['results'].items():
 for level in (5,15):
  for target in profiles:
   cells_rows=cells[f'{level}:{target}']['builds'];base=next((r for r in cells_rows if G in r['Items'] and S not in r['Items']),cells_rows[0]);common=[i for i in base['Items'] if i!=G] if level==15 else []
   if level==15 and len(common)!=4:common=['Infinity Edge',"Lord Dominik's Regards",'The Collector','Yun Tal Wildarrows']
   variants=[('screen_background',common)]
   if level==15:
    raw=sum(ns['dct'](ns['F'][i])['crit'] for i in common)+(.25 if 'Yun Tal Wildarrows' in common else 0)
    if raw>=1:
     remove=next((i for i in ('The Collector','Hexoptics C44','Stormrazor','Infinity Edge',"Lord Dominik's Regards") if i in common),None)
     replacement=next((i for i in ('Kraken Slayer','Blade of the Ruined King',"Wit's End") if i not in common and legal([x for x in common if x!=remove]+[i,G]) and legal([x for x in common if x!=remove]+[i,S])),None)
     if remove and replacement:variants.append(('avoid_crit_overcap',[x for x in common if x!=remove]+[replacement]))
   for variant,items in variants:
    for charged in (False,True):
     row=measure(champ,level,target,items,base,charged);row['background']=variant;results.append(row)
 print('DONE',champ,len(results),flush=True)
summary={}
for level in (5,15):
 for background in ('screen_background','avoid_crit_overcap'):
  for charged in (False,True):
   subset=[r for r in results if r['level']==level and r['background']==background and r['energized_at_start']==charged]
   if subset:summary[f'{level}:{background}:charged={charged}']={'pairs':len(subset),'wins':dict(collections.Counter(r['ttk_winner'] for r in subset)),'early_1s_wins':dict(collections.Counter('tie' if r['items'][G]['damage_at_seconds']['1']==r['items'][S]['damage_at_seconds']['1'] else G if r['items'][G]['damage_at_seconds']['1']>r['items'][S]['damage_at_seconds']['1'] else S for r in subset))}
payload={'engine_version':screen['version'],'method':'Paired swaps, same other items/boots/Conqueror+Brutal+Cut Down/target/policy. Level5 one item and level15 five items. Energized uncharged versus charged at start; locked120 magic/7 eligible-hit cadence unchanged. Additional level15 background removes redundant crit when baseline already100%. Backgrounds were selected from retained Rageblade candidates and are not unbiased global optimal builds. No slow/utility value scored. Burst windows after target death are capped at HP and marked.','results':results,'summary':summary}
(root/'data/rageblade-stormrazor-paired-comparison.json').write_text(json.dumps(payload,indent=2));print(json.dumps(summary,indent=2),flush=True)
