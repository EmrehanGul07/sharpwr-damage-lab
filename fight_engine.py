"""Impact-event replay: deterministic expected hits or reproducible critical rolls.

Times are supplied impact times, not invented cast/projectile timings. Unsupported
mechanics are surfaced by the caller; this is not a complete Wild Rift engine.
"""
from dataclasses import dataclass
import math
import random
from champion_abilities import samira_skill, resistance_multiplier, effective_resistance, SAMIRA_ABILITIES

@dataclass(frozen=True)
class FightEvent:
    time: float
    action: str

@dataclass
class FightResult:
    log: list
    rejected: list
    hp_remaining: float
    aa_count: int
    skill_count: int
    total_damage: float
    killed_at: float | None


SAMIRA_SKILL_ORDER=('Q','E','W','Q','R','Q','Q','E','R','E','E','W','R','W','W')

def samira_ranks(level):
    if not isinstance(level,int) or not 1<=level<=15:raise ValueError('Invalid champion level.')
    return {slot:SAMIRA_SKILL_ORDER[:level].count(slot) for slot in ('Q','W','E','R')}

def replay_samira(events,*,level,ad,attack_speed,crit_chance,crit_damage,hp,armor,q_rank=1,r_rank=1,ability_haste=0.,pct_pen=0.,flat_pen=0.,mode='Expected',seed=1,keystone=None,sub_runes=(),r_duration=None,aa_hit=None,yuntal_initial=0.,yuntal=False,base_ad=None,terminus=False,w_rank=0,e_rank=0,mr=0.,pct_mpen=0.,flat_mpen=0.,instant_skills=True,navori=False,collector_threshold=0.,skill_amp=1.,melee=False,transcendence=False,automatic_until=None,until_death=False,max_mana=None,mana_regen_per_5s=0.,timed_combat=False,distance=525.,attack_range=525.,aa_windup=None,movement_speed=0.,base_windup=None,starting_bonus_as=0.,aa_stats=None):
    """Replay AA/Q impacts and an explicitly timed R channel against one champion.

    Conqueror: one grant per separate attack/cast (not each R tick).
    Lethal Tempo: attacks only. Style: different consecutive attack/skill types.
    Cast lockout/projectile travel are not inferred. Optional mana regenerates between events.
    """
    values=(ad,attack_speed,crit_chance,crit_damage,hp,armor,ability_haste,pct_pen,flat_pen,mr,pct_mpen,flat_mpen,skill_amp,collector_threshold)
    if not all(math.isfinite(x) for x in values) or hp<=0 or ad<0 or attack_speed<=0 or ability_haste<0 or not 0<=pct_pen<=1 or flat_pen<0 or not 0<=pct_mpen<=1 or flat_mpen<0 or skill_amp<=0 or not 0<=collector_threshold<=1:raise ValueError('Invalid combat stats.')
    if not 1<=level<=15 or not 0<=crit_chance<=1 or crit_damage<1:raise ValueError('Invalid champion stats.')
    if mode not in ('Expected','Seeded critical rolls'):raise ValueError('Unknown critical mode.')
    if keystone not in (None,'Conqueror','Lethal Tempo'):raise ValueError('This replay supports Conqueror or Lethal Tempo only.')
    if any(x not in ('Brutal','Cut Down','Coup de Grace','Battle Zeal','Legend: Alacrity','Legend: Haste','Transcendence') for x in sub_runes):raise ValueError('Unsupported offensive rune in replay.')
    if not 0<=q_rank<=4 or not 0<=w_rank<=4 or not 0<=e_rank<=4 or not 0<=r_rank<=3:raise ValueError('Invalid skill rank.')
    if r_duration is not None and (not math.isfinite(r_duration) or r_duration<=0):raise ValueError('Invalid R duration.')
    if any(not math.isfinite(e.time) or e.time<0 or e.action not in ('AA','Q','W','E','R') for e in events):raise ValueError('Invalid impact timeline.')
    if automatic_until is not None and (not math.isfinite(automatic_until) or not 0<automatic_until<=120):raise ValueError('Automatic duration must be in (0,120].')
    if max_mana is not None and (not math.isfinite(max_mana) or max_mana<0 or not math.isfinite(mana_regen_per_5s) or mana_regen_per_5s<0):raise ValueError('Invalid mana stats.')
    if timed_combat and (not math.isfinite(movement_speed) or movement_speed<0 or not math.isfinite(distance) or distance<0 or attack_range<=0 or (aa_windup is not None and aa_windup<0)):raise ValueError('Invalid spatial/timing stats.')
    movement_time=0.;attack_windup_until=-1.
    if base_windup is not None and (not math.isfinite(base_windup) or base_windup<0):raise ValueError('Invalid base windup.')
    position=0.;target_position=distance;dash_start=dash_end=-1.;dash_origin=dash_destination=0.
    cast_until=w_until=-1.;w_id=0;cast_seq=0;timed_casts=set();next_auto_time=0.
    mana=max_mana;mana_time=0.;style_expiry=-1.
    rng=random.Random(seed); queue=[(e.time,i,e.action,None) for i,e in enumerate(events)];queue.sort(key=lambda x:(x[0],x[1]))
    base_ad=ad if base_ad is None else base_ad
    dark=0; ultimate_cast_time=None;item_stacks={}
    ranks={'Q':q_rank,'W':w_rank,'E':e_rank,'R':r_rank}; ready={k:0. for k in ranks}; e_until=-1.; transcend_ready=0.
    conq=lt=style=aa=casts=0; last_style=None; conq_expiry=lt_expiry=-1.; next_aa=next_q=next_r=0.; channel_until=-1.; combat_start=None; spell_pending=False
    health=float(hp); log=[]; rejected=[]; total=0.; killed=None; r_cast_id=0
    def reject(t,action,reason):rejected.append({'time':t,'action':action,'reason':reason})
    def advance_position(t):
        nonlocal position,movement_time
        if not timed_combat:return
        boundaries=sorted({movement_time,t,*[x for x in (dash_start,dash_end,cast_until,attack_windup_until,channel_until,style_expiry) if movement_time<x<t]})
        for start,end in zip(boundaries,boundaries[1:]):
            if dash_start<=start<dash_end:
                position=dash_origin+(dash_destination-dash_origin)*min(1.,(end-dash_start)/(dash_end-dash_start))
            elif start>=cast_until and start>=attack_windup_until and movement_speed:
                stacks=style if start<style_expiry or start<channel_until else 0
                speed=movement_speed*(1+.03*stacks)*(.7 if start<channel_until else 1.)
                gap=target_position-position
                position+=math.copysign(min(abs(gap),speed*(end-start)),gap) if gap else 0.
        movement_time=t
    auto_time=0.;auto_order=0
    while (queue or automatic_until is not None or until_death) and health>0:
        if not queue or timed_combat and (automatic_until is not None or until_death):
            choices=[]
            for i,k in enumerate(('E','W','Q')):
                if not ranks[k]:continue
                nt=max(auto_time,ready[k]);cost=SAMIRA_ABILITIES[k]['mana']
                if mana is not None:
                    if cost>max_mana:continue
                    available=min(max_mana,mana+max(0.,nt-mana_time)*mana_regen_per_5s/5)
                    if available<cost:
                        if mana_regen_per_5s==0:continue
                        nt+=(cost-available)/(mana_regen_per_5s/5)
                if timed_combat:
                    nt=max(nt,cast_until,attack_windup_until)
                    if k in ('W','Q'):nt=max(nt,channel_until)
                    if k=='Q':nt=max(nt,w_until)
                    if k=='W':nt=max(nt,dash_end)
                    gap=abs(target_position-position)
                    if k=='E' and gap>600:continue
                    if k=='W' and gap>325:continue
                    if k=='Q' and gap>950:continue
                choices.append((nt,i,k))
            if not timed_combat or abs(target_position-position)<=attack_range:
                choices.append((max(auto_time,next_aa,cast_until,w_until,channel_until,dash_end,attack_windup_until) if timed_combat else max(auto_time,next_aa),4,'AA'))
            if r_rank and style>=6 and (not timed_combat or abs(target_position-position)<=600):choices.append((max(auto_time,next_r,cast_until,attack_windup_until) if timed_combat else max(auto_time,next_r),-1,'R'))
            if timed_combat and movement_speed and abs(target_position-position)>1e-8:
                choices.append((auto_time+.05,9,'Move'))
            if not choices:
                if queue:pass
                else:break
            else:
                nt,_,na=min(choices)
                if not ((automatic_until is not None and nt>automatic_until) or auto_order>=(20000 if timed_combat else 1000)):
                    if not queue or nt<queue[0][0]-1e-9:
                        auto_order+=1;queue.append((nt,100000+auto_order,na,None));queue.sort(key=lambda x:(x[0],x[1]))
                elif not queue:break
        t,order,action,cast_id=queue.pop(0)
        if timed_combat and automatic_until is not None and t>automatic_until:break
        advance_position(t)
        auto_time=t
        if action=='Move':continue
        if mana is not None:mana=min(max_mana,mana+max(0.,t-mana_time)*mana_regen_per_5s/5);mana_time=t
        if timed_combat:
            if action=='R end':
                style=0;last_style=None;channel_until=t;continue
            impact=action.endswith(' hit') or action=='R tick'
            if action=='W hit' and cast_id[0]!=w_id:continue
            if action.endswith(' hit'):
                action=action[:-4]
            gap=abs(target_position-position)
            if not impact:
                if t<attack_windup_until:reject(t,action,'AA windup active');continue
                if t<cast_until:reject(t,action,'Cast active');continue
                if action in ('AA','Q','W') and t<channel_until:reject(t,action,'R channel active');continue
                if action in ('AA','Q') and t<w_until:reject(t,action,'W active');continue
                if action=='AA' and t<dash_end:reject(t,action,'Dash active');continue
                if action=='W' and t<dash_end:
                    queue.append((dash_end,order,action,None));queue.sort(key=lambda x:(x[0],x[1]));continue
                limit={'AA':attack_range,'Q':950,'W':325,'E':600,'R':600}[action]
                if gap>limit:reject(t,action,'Target out of range');continue
                if action=='AA' and t+1e-9<next_aa:reject(t,action,'Attack interval has not elapsed');continue
                if action in ('Q','W','E') and (not ranks[action] or t+1e-9<ready[action]):reject(t,action,action+' unlearned or on cooldown');continue
                if action in ('Q','W','E'):
                    cost=SAMIRA_ABILITIES[action]['mana']
                    if mana is not None and mana+1e-9<cost:reject(t,action,'Insufficient mana');continue
                    if mana is not None:mana=max(0.,mana-cost)
                    ready[action]=t+SAMIRA_ABILITIES[action]['cooldown'][ranks[action]-1]/(1+ability_haste/100)
                    casts+=1;spell_pending=True;cast_seq+=1
                    if transcendence and level>=9 and t>=transcend_ready:
                        for basic in ('Q','W','E'):ready[basic]=t+max(0.,ready[basic]-t)*.92
                        transcend_ready=t+8.
                    if action=='E':
                        dash_start=t;dash_end=t+650/1600;dash_origin=position
                        dash_destination=position+(650 if target_position>=position else -650)
                        arrival=t+gap/1600;e_until=t+3.
                        queue.append((arrival,order,'E hit',(cast_seq,0)))
                    elif action=='W':
                        w_id+=1;cast_until=t+.1;w_until=t+.1+.75
                        queue.extend([(t+.1,order,'W hit',(w_id,0)),(w_until,order+.01,'W hit',(w_id,1))])
                    else:
                        slash=gap<=340;cast_until=t+.25 if t>=dash_end else t
                        arrival=dash_end if t<dash_end else t+.25+(0 if slash else gap/2600)
                        queue.append((arrival,order,'Q hit',(cast_seq,0,slash or t<dash_end)))
                    queue.sort(key=lambda x:(x[0],x[1]));continue
                if action=='AA':
                    bonus_as=(.048*lt if keystone=='Lethal Tempo' and t<lt_expiry else 0.)+([.25,.30,.35,.40][e_rank-1] if e_rank and t<e_until else 0.)
                    total_bonus_as=starting_bonus_as+bonus_as
                    if aa_stats:total_bonus_as=aa_stats({'time':t,'bonus_as':bonus_as,'items':dict(item_stacks)})['bonus_as_total']
                    windup=(base_windup/(1+.5*total_bonus_as)) if base_windup is not None else (aa_windup or 0)
                    attack_windup_until=t+windup
                    arrival=t+windup+(gap/2800 if gap>200 else 0)
                    next_aa=max(next_aa,arrival)
                    queue.append((arrival,order,'AA hit',(cast_seq,0,t,gap<=200,windup)));queue.sort(key=lambda x:(x[0],x[1]));continue
            else:
                limit={'AA':float('inf'),'Q':float('inf'),'W':325,'E':250,'R tick':600}[action]
                if gap>limit:continue
            melee=cast_id[3] if impact and action=='AA' else gap<=200
        if mana is not None:mana=min(max_mana,mana+max(0.,t-mana_time)*mana_regen_per_5s/5);mana_time=t
        if t>=style_expiry and (not timed_combat or t>=channel_until):style=0;last_style=None
        if t>=conq_expiry:conq=0
        if t>=lt_expiry:lt=0
        if not timed_combat and action!='R tick' and t<channel_until:reject(t,action,'R channel active');continue
        if not timed_combat and action=='AA' and t+1e-9<next_aa:reject(t,action,'Attack interval has not elapsed');continue
        if not timed_combat and action in ('Q','W','E') and (ranks[action]==0 or t+1e-9<ready[action]):reject(t,action,action+' unlearned or on cooldown');continue
        if not timed_combat and action in ('Q','W','E') and mana is not None:
            cost=SAMIRA_ABILITIES[action]['mana']
            if mana+1e-9<cost:reject(t,action,'Insufficient mana');continue
            mana=max(0.,mana-cost)
        if action=='R':
            if r_rank==0 or t+1e-9<next_r:reject(t,action,'R unlearned or on cooldown');continue
            if style<6:reject(t,action,'S style required');continue
            if not timed_combat and not instant_skills and r_duration is None:reject(t,action,'R channel timing unknown: supply measured duration');continue
            r_cast_id+=1;style=style if timed_combat else 0;last_style=last_style if timed_combat else None;channel_until=t+(2.277 if timed_combat else (0. if instant_skills else r_duration));next_r=t+6/(1+ability_haste/100);casts+=1;ready['R']=next_r;spell_pending=True;ultimate_cast_time=t
            if timed_combat:
                w_id+=1;w_until=t
                queue.append((channel_until,order+1,'R end',None))
            # First and last impact bounds are explicit model assumptions, not cast-time inference.
            for shot in range(10):queue.append((t+(2.013*shot/9 if timed_combat else (0. if instant_skills else r_duration*shot/9)),order+shot/100,'R tick',(r_cast_id,shot)))
            queue.sort(key=lambda x:(x[0],x[1]));continue
        effects=[]
        before_hp=health;before={'items':dict(item_stacks),'style':style,'conqueror':conq,'lethal_tempo':lt,'AA':aa,'skills':casts}
        bonus_ad=conq*(3+(level-1)*2/14) if keystone=='Conqueror' else 0.
        current_ad=ad+bonus_ad
        current_crit=min(1.,crit_chance+(min(.25,yuntal_initial+.002*aa) if yuntal else 0.))
        rolled=(rng.random()<current_crit) if mode=='Seeded critical rolls' and action in ('AA','Q','R tick') else (False if mode=='Seeded critical rolls' else None)
        probability=current_crit if rolled is None else float(rolled)
        live_pen=min(.40,pct_pen+.10*dark) if terminus else pct_pen
        ea=effective_resistance(armor,live_pen,flat_pen)
        hit_magic_pen=min(.40,pct_mpen+.10*dark) if terminus else pct_mpen
        if action=='AA':
            bonus_as=(.048*lt if keystone=='Lethal Tempo' else 0.)+([.25,.30,.35,.40][e_rank-1] if e_rank and t<e_until else 0.)
            if aa_hit:
                hit=aa_hit({'hp':health,'time':t,'bonus_ad':bonus_ad,'bonus_as':bonus_as,'crit':probability,'melee':melee,'event_driven':True,'spell_cast':spell_pending,'ultimate_cast_time':ultimate_cast_time})
                damage=hit['damage'];speed=hit['as'];ea=hit['armor'];dark=hit.get('dark',dark)
                lt_bonus_as=hit.get('bonus_as_total',bonus_as)
                effects.extend(hit.get('notes',[]))
                item_stacks={k:hit.get(k,0) for k in ('rage','light','dark','phantom_dancer','kraken')}
                item_stacks['yuntal_crit']=round(hit.get('yuntal_crit',0),4)
            else:
                damage=current_ad*(1+probability*(crit_damage-1))*resistance_multiplier(ea)
                speed=attack_speed*(1+bonus_as);lt_bonus_as=bonus_as
            if keystone=='Lethal Tempo' and lt>=6:
                damage+=(6+(level-1))* (1+.0033*lt_bonus_as*100)*resistance_multiplier(ea)*skill_amp
            if 'Brutal' in sub_runes:damage+=(6+.08*max(0,current_ad-base_ad))*resistance_multiplier(ea)*skill_amp
            next_aa=(cast_id[2] if timed_combat else t)+1/speed;aa+=1;spell_pending=False
            if navori:
                effects.append('Navori: remaining basic cooldown ×0.85')
                for slot in ('Q','W','E'):ready[slot]=t+max(0.,ready[slot]-t)*.85
        else:
            slot='R' if action=='R tick' else action
            rank=ranks[slot]
            magic_pen=min(.40,pct_mpen+.10*dark) if terminus else pct_mpen
            hit=samira_skill(slot,rank,current_ad,probability,crit_damage,armor,pct_pen=live_pen,flat_pen=flat_pen,outcome='Expected',hits=1 if timed_combat or slot!='W' else 2,base_ad=base_ad,mr=mr,pct_mpen=magic_pen,flat_mpen=flat_mpen)
            damage=hit.total*skill_amp
            if not timed_combat and action in ('Q','W','E'):
                ready[action]=t+SAMIRA_ABILITIES[action]['cooldown'][rank-1]/(1+ability_haste/100);casts+=1;spell_pending=True
                if action=='E':
                    e_until=t+3.;melee=True;effects.extend(['E attack speed buff (3s)','Dash reached target: melee range'])
                if transcendence and level>=9 and t>=transcend_ready:
                    for basic in ('Q','W','E'):ready[basic]=t+max(0.,ready[basic]-t)*.92
                    transcend_ready=t+8.;effects.append('Transcendence: remaining basic cooldown ×0.92')
            if action in ('Q','W','E') and 'Battle Zeal' in sub_runes and combat_start is not None:damage*=1+.014*min(3,int(t-combat_start))
        passive_eligible=(action in ('W','E') or (action=='AA' and melee) or (action=='Q' and cast_id[2])) if timed_combat else melee and action!='R tick'
        if passive_eligible:
            # User-accepted level and linear missing-health model; one passive per landed hit.
            magic_pen=min(.40,pct_mpen+.10*dark) if terminus else pct_mpen
            passive=(level+5+(.05+.008*level)*current_ad)*(1+(hp-before_hp)/hp)
            damage+=passive*resistance_multiplier(effective_resistance(mr,hit_magic_pen,flat_mpen))*(2 if action=='W' and not timed_combat else 1)*skill_amp
        if 'Cut Down' in sub_runes and before_hp/hp>.60:damage*=1.065
        if 'Coup de Grace' in sub_runes and before_hp/hp<.40:damage*=1.08
        health=max(0.,health-damage);executed=False
        if collector_threshold and 0<health<=hp*collector_threshold:
            damage+=health;health=0.;executed=True;effects.append('Collector execute')
        total+=damage
        if combat_start is None:combat_start=t
        # Stack grants are after the hit and change the NEXT event's stats.
        separate=(action!='R tick' or cast_id[1]==0) and (not timed_combat or action!='W' or cast_id[1]==0)
        if keystone=='Conqueror' and separate:conq=min(6,conq+1);conq_expiry=t+6
        if keystone=='Lethal Tempo' and action=='AA':lt=min(6,lt+1);lt_expiry=t+6
        if action in ('AA','Q','W','E') and action!=last_style:style=min(6,style+1);last_style=action
        if action in ('AA','Q','W','E'):style_expiry=t+6.
        after={'items':dict(item_stacks),'style':style,'conqueror':conq,'lethal_tempo':lt,'AA':aa,'skills':casts}
        log.append({'time':t,'action':action,'mana':mana,'max_mana':max_mana,'AD':current_ad,'crit_chance':current_crit,'critical':rolled,'executed':executed,'effects':effects,'melee':melee,'windup':cast_id[4] if timed_combat and action=='AA' else None,'distance':abs(target_position-position) if timed_combat else None,'ability_haste':ability_haste,'cooldowns':{k:max(0.,v-t) for k,v in ready.items()},'E_buff':t<e_until,'damage':damage,'hp_before':before_hp,'hp_after':health,'before':before,'after':after})
        if health<=0:killed=t
    return FightResult(log,rejected,health,aa,casts,total,killed)
