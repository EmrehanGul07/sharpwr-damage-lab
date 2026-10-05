"""Reproducible engine integrity audit, not build optimization or gameplay proof."""
import json,math,sys,time
from collections import Counter,defaultdict
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from build_fight_optimizer import BuildFightEvaluator,legal
from marksman_kits import PRIORITIES
from champion_database import level_stats
from sharpwr import engine_namespace

PROFILES={
 'no_items':([],None),
 'crit':(['Infinity Edge','Phantom Dancer','Yun Tal Wildarrows','The Collector','Navori Quickblades'],'Armorcrusher Boots'),
 'ap_hybrid':(["Nashor's Tooth",'Statikk Shiv',"Guinsoo's Rageblade",'Galeforce','Muramana'],"Spellslinger's Shoes"),
 'on_hit':(["Guinsoo's Rageblade",'Kraken Slayer','Terminus','Blade of the Ruined King',"Wit's End"],'Gunmetal Greaves'),
 'penetration':(['Duskblade of Draktharr',"Lord Dominik's Regards",'The Collector','Infinity Edge','Muramana'],'Armorcrusher Boots'),
 'cast_proc':(['Trinity Force','Muramana',"Nashor's Tooth",'Galeforce','Fiendhunter Bolts'],'Crimson Lucidity'),
}

def check(result,maxhp,name):
 errors=[]
 def verify(condition,reason):
  if not condition:errors.append(reason)
 verify(math.isclose(result.total_damage,maxhp-result.hp_remaining,rel_tol=1e-9,abs_tol=1e-7),'health ledger')
 verify(math.isclose(result.total_damage,sum(x['damage'] for x in result.log),rel_tol=1e-9,abs_tol=1e-7),'event sum')
 verify([x['time'] for x in result.log]==sorted(x['time'] for x in result.log),'event order')
 verify(not result.rejected,'automatic rejected command')
 for x in result.log:
  verify(math.isfinite(x['damage']) and x['damage']>=0,'invalid damage')
  from damage_classification import TAGS
  for part in x.get('damage_components',[]):
   verify(set(part.get('tags',[]))<=TAGS,'unknown component tag')
   verify(math.isfinite(part['raw_amount']) and part['raw_amount']>=0,'invalid component amount')
   if part.get('component')=='Muramana skill Shock':verify(part['tags']==['Item'],'Shock misclassified as basic damage')
  verify(0<=x['hp_after']<=x['hp_before']+1e-8,'nonmonotonic health')
  if x.get('mana') is not None:verify(0<=x['mana']<=x.get('max_mana',x['mana'])+1e-8,'mana bounds')
 commands=[x for x in result.timeline if x['kind']=='attack'];ids=[x['id'] for x in commands]
 verify(len(ids)==len(set(ids)),'duplicate attack ID')
 attack_map={x['id']:x for x in commands}
 for x in result.timeline:
  verify(x['time']+1e-7>=x.get('lock_before',-1),'command during lock')
  if x['kind']=='attack':
   verify(x['distance']<=x['attack_range']+1e-6,'AA commanded out of range')
   verify(x['impact_time']+1e-8>=x['windup_end']>=x['time'],'impact before launch')
  else:
   allowed=x.get('during_channel_allowed',False) or name=='Samira' and x['action']=='E'
   if not allowed:verify(x['time']+1e-7>=x.get('channel_before',-1),'cast during channel')
   if not(name=='Zeri' and x['action'] in ('W','R')):verify(x['time']+1e-7>=x.get('windup_before',-1),'cast during AA windup')
 for x in result.log:
  if x['action']=='AA' and x.get('attack_id') in attack_map:
   verify(math.isclose(x['time'],attack_map[x['attack_id']]['impact_time'],abs_tol=1e-7),'AA arrival mismatch')
 casts=[x['time'] for x in result.timeline if x['kind']=='cast']
 for labels,cd in [(('Nightstalker',),10.),(('Trinity','ER','Iceborn','Sheen'),1.5),(('Cloudburst active; 50s cooldown','Cloudburst active; dash up to 325; target range 600; 50s cooldown'),50.)]:
  proc_times=[x['time'] for x in result.log if any(e in labels for e in x['effects'])]
  verify(all(b-a>=cd-1e-7 for a,b in zip(proc_times,proc_times[1:])),'item cooldown '+str(labels))
  if cd==1.5:
   previous=-1e10
   for hit_time in proc_times:
    verify(any(previous+1.5-1e-7<=cast<=hit_time+1e-7 for cast in casts),'Spellblade without successful ready cast')
    previous=hit_time
 ultimates=[x['time'] for x in result.timeline if x['kind']=='cast' and x['action']=='R'];barrages=Counter()
 for x in result.log:
  if 'Opening Barrage' not in x['effects']:continue
  prior=[u for u in ultimates if u<x['time']-1e-7]
  verify(bool(prior),'Fiendhunter without R')
  if prior:
   u=prior[-1];barrages[u]+=1;verify(x['time']<=u+8+1e-7,'Fiendhunter expiry')
 verify(all(count<=3 for count in barrages.values()),'Fiendhunter more than three attacks per R')
 return sorted(set(errors))

def run(output=None, trace_output=None):
 ns=engine_namespace();rows=[];warnings=defaultdict(set);started=time.perf_counter();simulations=0;examples={}
 for name in PRIORITIES:
  count=0
  for level in (1,15):
   for target_name in ns['TARGET_PROFILES']:
    target=ns['benchmark_target'](target_name,level)
    e=BuildFightEvaluator(ns,name,level,target['hp'],target['armor'],target['mr'],bonus_hp=target['bonus_hp'],aa_reduction=target.get('aa_reduction',0),retain_traces=True)
    cases=dict(PROFILES)
    if level==15:cases.update({'single:'+item:([item],None) for item in ns['F']})
    for label,(items,boots) in cases.items():
     if not legal(items):raise ValueError(label)
     try:
      row=e.evaluate(items,boots);key=(tuple(sorted(items)),boots,False);r=e.traces[key]
      errors=check(r,target['hp'],name)
      warnings[name].update(r.assumptions)
      rows.append({'champion':name,'level':level,'target':target_name,'profile':label,'items':items,'boots':boots,'TTK':row['TTK'],'DPS':row['DPS'],'damage':r.total_damage,'remaining_hp':r.hp_remaining,'aa_count':r.aa_count,'skill_count':r.skill_count,'proc_counts':dict(Counter(effect for event in r.log for effect in event['effects'])),'cast_counts':dict(Counter(event['action'] for event in r.timeline if event['kind']=='cast')),'command_count':len(r.timeline),'movement':row['Movement'],'rotation':row['Rotation'],'weapon':row['Weapon'],'errors':errors,'status':'integrity_pass' if not errors else 'FAIL'})
      if level==15 and target_name=='Tank • Ornn' and label=='cast_proc' and name in ('Samira','Ezreal','Jhin','Jinx'):examples[name]={'timeline':r.timeline,'log':r.log,'assumptions':r.assumptions}
     except Exception as exc:rows.append({'champion':name,'level':level,'target':target_name,'profile':label,'errors':[repr(exc)],'status':'FAIL'})
     e.traces.clear();count+=1
    simulations+=e.simulations
  print(name,count,'cases',flush=True)
 failures=[r for r in rows if r['status']=='FAIL']
 version=(ROOT/'VERSION').read_text().strip()
 out={'version':version,'purpose':'Integrity audit only; PC timing proxies and provisional WR mechanics do not establish gameplay parity or globally optimal builds. Not a build cache.','champions':len(PRIORITIES),'levels':[1,15],'targets':list(ns['TARGET_PROFILES']),'case_count':len(rows),'fight_simulations':simulations,'elapsed_seconds':time.perf_counter()-started,'failures':failures,'warnings':{k:sorted(v) for k,v in warnings.items()},'rows':rows}
 Path(output or ROOT/'data/combat-audit-current.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
 Path(trace_output or ROOT/'data/combat-audit-traces-current.json').write_text(json.dumps(examples,ensure_ascii=False,separators=(',',':'))+'\n')
 print('RESULT',len(rows),'cases',simulations,'fights',len(failures),'failures',out['elapsed_seconds'],'seconds',flush=True)
 if failures:print(json.dumps(failures[:10],ensure_ascii=False))
 return out
if __name__=='__main__':
 import argparse
 parser=argparse.ArgumentParser();parser.add_argument('--output');parser.add_argument('--trace-output');args=parser.parse_args()
 result=run(args.output,args.trace_output)
 sys.exit(bool(result['failures']))
