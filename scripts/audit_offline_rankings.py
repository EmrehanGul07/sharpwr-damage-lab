"""Bounded sensitivity and optimizer coverage audit; never production build cache."""
import sys,json,time
from pathlib import Path
from itertools import combinations
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.audit_combat_matrix import namespace,PROFILES
from build_fight_optimizer import BuildFightEvaluator,search_builds,legal,score
from marksman_kits import PRIORITIES

def run():
 ns=namespace();profiles=dict(PROFILES);profiles.pop('no_items');profiles['hex_crit']=(['Infinity Edge','Phantom Dancer','Yun Tal Wildarrows','The Collector','Hexoptics C44'],'Armorcrusher Boots')
 rows=[];coverage=[];simulations=0;started=time.perf_counter()
 pool=['Muramana',"Nashor's Tooth",'Infinity Edge','Phantom Dancer',"Guinsoo's Rageblade",'Hexoptics C44']
 for c in PRIORITIES:
  for target in ns['TARGET_PROFILES']:
   t=ns['benchmark_target'](target,15);hp,arm,mr,bhp,aared=t['hp'],t['armor'],t['mr'],t['bonus_hp'],t.get('aa_reduction',0)
   def evaluator(override=None,base_mana=None):return BuildFightEvaluator(ns,c,15,hp,arm,mr,bonus_hp=bhp,aa_reduction=aared,base_mana=base_mana,simulation_overrides=override)
   def rank(ev):
    values=[(label,ev.evaluate(items,boot)) for label,(items,boot) in profiles.items()]
    return sorted(values,key=lambda v:score(v[1]))
   base=evaluator();original=rank(base);simulations+=base.simulations
   variants={'windup_minus20':{'windup_scale':.8},'windup_plus20':{'windup_scale':1.2},'muramana_every_hit':{'muramana_repeat_policy':'every_hit'},'hexoptics_skill_scope_off':{'hexoptics':False}}
   for label,override in variants.items():
    ev=evaluator(override);new=rank(ev);simulations+=ev.simulations
    orig=[x[0] for x in original[:3]];alt=[x[0] for x in new[:3]]
    same={k:v for k,v in new};bestlabel,best=original[0];variantbest=same[bestlabel]
    delta=None if best['TTK'] is None or variantbest['TTK'] is None else variantbest['TTK']-best['TTK']
    rows.append(dict(champion=c,target=target,variant=label,original_top3=orig,variant_top3=alt,top3_changed=orig!=alt,winner_changed=orig[0]!=alt[0],original_winner_ttk_delta=delta,rows=[dict(profile=k,TTK=v['TTK'],damage=v['Damage'],rotation=v['Rotation'],movement=v['Movement']) for k,v in new]))
   if c=='Yunara':
    for mana,ms,radius in [(1000,300,550),(2000,400,650)]:
     ev=evaluator({'movement_speed':ms,'attack_range':radius,'distance':radius},base_mana=mana);new=rank(ev);simulations+=ev.simulations
     orig=[x[0] for x in original[:3]];alt=[x[0] for x in new[:3]]
     rows.append(dict(champion=c,target=target,variant=f'hypothetical_mana{mana}_ms{ms}_range{radius}',original_top3=orig,variant_top3=alt,top3_changed=orig!=alt,winner_changed=orig[0]!=alt[0],note='Illustrative endpoints, not evidence or confidence bounds; core values remain unknown.'))
   # Six-item pool is deliberately small enough to retain EVERY legal subset.
   ev=evaluator();result=search_builds(ev,pool,['Armorcrusher Boots'],beam_width=80,refine_count=3)
   counts={n:sum(legal(x) for x in combinations(pool,n)) for n in range(1,6)}
   exhaustive=[ev.evaluate(x,'Armorcrusher Boots') for x in combinations(pool,5) if legal(x)]
   best=min(exhaustive,key=score);winner=result['full'][0]
   cell=dict(champion=c,target=target,expected_counts=counts,observed_counts=result['tested'],all_stage_candidates_covered=counts==result['tested'],full_candidates=result['full_candidates'],refined=result['refined'],fast_exhaustive_best=best['Items'],fast_best_ttk=best['TTK'],search_best=winner['Items'],search_best_ttk=winner['TTK'],search_not_worse=score(winner)<=score(best),search_status=result['search_status'])
   if c in ('Samira','Ezreal','Jhin','Xayah') and target==list(ns['TARGET_PROFILES'])[0]:
    deep=[ev.evaluate(x,'Armorcrusher Boots',refine=True) for x in combinations(pool,5) if legal(x)];deepbest=min(deep,key=score);cell.update(deep_exhaustive_best=deepbest['Items'],deep_exhaustive_ttk=deepbest['TTK'],deep_search_matches=score(winner)==score(deepbest))
   simulations+=ev.simulations;coverage.append(cell)
  print(c,'completed',flush=True)
 out=dict(version='5.65.0',policy='Six illustrative full-build families; Hexoptics skill-scope stress test keeps kernel basic-AA magnification unchanged; 23 champions x 3 targets at level 15. Sensitivity endpoints are assumptions, not sourced corrections. Six-item optimizer pool checks exact candidate coverage only in that pool; production 36-item search remains bounded. Not a build cache.',sensitivity=rows,optimizer=coverage,simulation_count=simulations,elapsed_seconds=time.perf_counter()-started,failures=[x for x in coverage if not x['all_stage_candidates_covered'] or not x['search_not_worse']])
 (ROOT/'data/offline-rankings-v565.json').write_text(json.dumps(out,ensure_ascii=False,separators=(',',':'))+'\n')
 print('RESULT',len(rows),'sensitivity rows',len(coverage),'optimizer cells',len(out['failures']),'failures',out['elapsed_seconds'],flush=True)
if __name__=='__main__':run()
