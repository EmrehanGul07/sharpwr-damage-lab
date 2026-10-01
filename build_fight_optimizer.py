"""Ability-aware build search. Candidate pruning is explicit, never global optimality."""
from itertools import combinations,permutations
from champion_database import level_stats
from fight_engine import replay_samira,champion_ranks
from marksman_kits import PRIORITIES

EXCLUSIVE=({'Mortal Reminder',"Lord Dominik's Regards","Serylda's Grudge",'Terminus'},{'Manamune','Muramana'})
TIER3=('Immortal Treads','Crimson Lucidity','Gunmetal Greaves','Chainlaced Crushers','Armored Advance',"Spellslinger's Shoes",'Armorcrusher Boots')
def legal(items):return len(items)==len(set(items)) and all(len(set(items)&group)<=1 for group in EXCLUSIVE)
def score(row):return (row['TTK'] is None,row['TTK'] if row['TTK'] is not None else -row['Damage'],row['Gold'],row['Items'],row['Boots'] or '')

class BuildFightEvaluator:
    def __init__(self,namespace,champion,level,hp,armor,mr,*,mist=0,bonus_hp=0,aa_reduction=0,base_mana=None,energized=False,yuntal_stacks=0,execs=0,dragon_stacks=0):
        self.ns=namespace;self.champion=champion;self.level=level;self.hp=hp;self.armor=armor;self.mr=mr;self.mist=mist;self.bonus_hp=bonus_hp;self.aa_reduction=aa_reduction;self.base_mana=base_mana;self.energized=energized;self.yuntal_stacks=yuntal_stacks;self.execs=execs;self.dragon_stacks=dragon_stacks;self.cache={};self.simulations=0
    def evaluate(self,items,boot=None,refine=False):
        items=tuple(sorted(items));key=(items,boot,refine)
        if key in self.cache:return self.cache[key]
        if not legal(items):raise ValueError('Illegal build')
        ns=self.ns;n=self.champion;l=self.level;core=level_stats(n,l);s=ns['stats'](n,l,self.mist)
        stats=[ns['dct'](ns['F'][x]) for x in items]+[ns['dct'](ns['B'][boot]) if boot else ns['dct'](())]
        total={k:sum(q[k] for q in stats) for k in ns['K']}
        base_mana=core['mana'] if core['mana'] is not None else self.base_mana
        maxmana=None if base_mana is None else base_mana+total['mana'];awe=.02*(maxmana or 0) if any(x in items for x in ('Manamune','Muramana')) else 0
        radius=core['attack_range'] or 550;ms=(core['movement_speed'] or 0)*(1+sum(ns['dct'](ns['F'][x])['ms'] for x in items))+(ns['dct'](ns['B'][boot])['ms'] if boot else 0)
        default=tuple(PRIORITIES[n]);priorities=list(permutations('QWE')) if refine else [default]
        results=[]
        for priority in priorities:
            for use_e in (False,True):
                for weapon in (('minigun','rockets') if n=='Jinx' else ('minigun',)):
                    kernel=ns['_combat_hits'](n,l,self.hp,self.armor,self.mr,items,ns['F'],self.mist,self.bonus_hp,radius,self.aa_reduction,self.yuntal_stacks,base_mana or 0,False,self.energized,False,self.execs,True,boot)
                    next(kernel);last={}
                    def aa_stats(state):
                        dyn=(.08*state['items'].get('rage',0) if "Guinsoo's Rageblade" in items else 0)+(.06*state['items'].get('phantom_dancer',0) if 'Phantom Dancer' in items else 0)
                        if state['time']<last.get('yuntal_until',-1):dyn+=.35
                        ult=state.get('ultimate_cast_time');fiend=.5 if 'Fiendhunter Bolts' in items and ult is not None and state['time']<=ult+8 and (last.get('fiend_remaining',3)>0 or last.get('ult_seen')!=ult) else 0
                        bonus=s['bba']+s['lvbas']+total['as']+dyn+state['bonus_as']+fiend
                        expiry=[v for v in (last.get('yuntal_until',-1),ult+8 if fiend else -1) if v>state['time']]
                        return {'bonus_as_total':bonus,'as':min(3.,s['baseas']+s['ratio']*bonus),'buff_expiry':min(expiry) if expiry else -1}
                    def aa(state):
                        hit=kernel.send(state);last.update(hit);last['ult_seen']=state.get('ultimate_cast_time');return hit
                    r=replay_samira([],champion=n,level=l,ad=s['ad']+total['ad']+awe,base_ad=s['ad'],ap=total['ap'],attack_speed=s['baseas'],as_ratio=s['ratio'],natural_attack_speed=s['baseas']+s['ratio']*(s['bba']+s['lvbas']),crit_chance=min(1,total['crit']+(self.mist//20*.1 if n=='Senna' else 0)),crit_damage=2.3 if 'Infinity Edge' in items else 2,hp=self.hp,armor=self.armor,mr=self.mr,**{k.lower()+'_rank':v for k,v in champion_ranks(n,l).items()},ability_haste=total['ah'],pct_pen=total['pctpen'],flat_pen=total['flatpen'],pct_mpen=total['pctmpen'],flat_mpen=total['flatmpen'],skill_priority=priority,use_e=use_e,weapon=weapon,movement_speed=ms,attack_range=radius,distance=radius,timed_combat=True,instant_skills=False,base_windup=.149999994/.658 if n=='Samira' else None,aa_hit=aa,aa_stats=aa_stats,max_mana=maxmana,mana_regen_per_5s=core['mana_regen_per_5s'] or 0,until_death=True,automatic_until=60,mist=self.mist,initial_stacks=self.dragon_stacks,completed_items=len(items),item_as=total['as'],item_ad=total['ad'],navori='Navori Quickblades' in items,muramana='Muramana' in items,mana_refund=.15 if any(x in items for x in ('Manamune','Muramana')) else 0,terminus='Terminus' in items,yuntal='Yun Tal Wildarrows' in items,yuntal_initial=min(.25,self.yuntal_stacks*.002),collector_threshold=min(1,.05+.001*self.execs) if 'The Collector' in items else 0,skill_amp=(1.05 if boot=='Immortal Treads' else 1)*(1+min(.12,self.bonus_hp/125*.01) if "Lord Dominik's Regards" in items else 1))
                    self.simulations+=1
                    duration=max(.05,r.killed_at if r.killed_at is not None else 60)
                    # Separate command-based AA damage from ability/passive/DoT events.
                    aa_damage=sum(x['damage'] for x in r.log if x['action'].startswith('AA'))
                    start_raw=s['baseas']+s['ratio']*(s['bba']+s['lvbas']+total['as'])
                    cap=1.5 if n=='Zeri' else 3
                    results.append({'Items':items,'Boots':boot,'TTK':r.killed_at,'DPS':r.total_damage/duration,'Damage':r.total_damage,'AA damage':aa_damage,'Other damage':max(0.,r.total_damage-aa_damage),'Gold':total['gold'],'AD':s['ad']+total['ad']+awe+(.5*max(0.,(s['bba']+s['lvbas']+total['as']-max(0.,(1.5-s['baseas'])/s['ratio']))*100) if n=='Zeri' else 0.),'AP':total['ap'],'Crit %':min(100,total['crit']*100),'AH':total['ah'],'Starting AS':min(cap,start_raw),'AS over cap':max(0,start_raw-cap),'Rotation':' → '.join(priority),'E enabled':use_e,'Weapon':weapon,'Assumptions':r.assumptions})
        row=min(results,key=score);self.cache[key]=row;return row

def search_builds(evaluator,pool,boots,*,beam_width=40,refine_count=20,progress=None):
    """All singles/pairs; beam expansion for 3–5, then all Tier3 boots + rotations."""
    pool=tuple(sorted(pool));stages={};beam=[()];tested={}
    for stage in range(1,6):
        candidates={tuple(sorted((*seed,item))) for seed in beam for item in pool if item not in seed and legal((*seed,item))}
        rows=[evaluator.evaluate(x) for x in sorted(candidates)]
        rows.sort(key=score);tested[stage]=len(rows);stages[stage]=rows[:10];beam=[x['Items'] for x in rows[:beam_width]]
        if stage<5:
            shortlist=[evaluator.evaluate(x['Items'],refine=True) for x in rows[:refine_count]]
            shortlist.sort(key=score);stages[stage]=shortlist[:10]
        if progress:progress(stage/7,f'{stage}-item candidates: {len(rows)}')
    full=[evaluator.evaluate(items,boot) for items in beam for boot in boots]
    full.sort(key=score)
    # Rerank finalists with every supported basic priority rather than AA-only screening.
    refined=[evaluator.evaluate(x['Items'],x['Boots'],refine=True) for x in full[:refine_count]]
    refined.sort(key=score)
    if progress:progress(1.,'Complete')
    marginal=[]
    if refined:
        best=refined[0]
        for removed in (*best['Items'],best['Boots']):
            without=evaluator.evaluate(tuple(x for x in best['Items'] if x!=removed),None if removed==best['Boots'] else best['Boots'],refine=True)
            marginal.append({'Item':removed,'DPS contribution':best['DPS']-without['DPS'],'TTK increase without item':None if best['TTK'] is None or without['TTK'] is None else without['TTK']-best['TTK'],'Target survives without item':without['TTK'] is None})
    return {'marginal':marginal,'stages':{k:v for k,v in stages.items() if k<5},'full':refined[:3],'tested':tested,'full_candidates':len(full),'refined':len(refined),'simulations':evaluator.simulations,'beam_width':beam_width,'pool_size':len(pool),'boot_count':len(boots)}
