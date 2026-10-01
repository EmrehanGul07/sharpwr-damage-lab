"""Impact-event replay: deterministic expected hits or reproducible critical rolls.

Times are supplied impact times, not invented cast/projectile timings. Unsupported
mechanics are surfaced by the caller; this is not a complete Wild Rift engine.
"""
from dataclasses import dataclass, asdict
import math
import random
from champion_abilities import samira_skill, resistance_multiplier, effective_resistance

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


def replay_samira(events,*,level,ad,attack_speed,crit_chance,crit_damage,hp,armor,q_rank=1,r_rank=1,ability_haste=0.,pct_pen=0.,flat_pen=0.,mode='Expected',seed=1,keystone=None,sub_runes=(),r_duration=None,aa_hit=None,yuntal_initial=0.,yuntal=False,base_ad=None,terminus=False):
    """Replay AA/Q impacts and an explicitly timed R channel against one champion.

    Conqueror: one grant per separate attack/cast (not each R tick).
    Lethal Tempo: attacks only. Style: different consecutive attack/skill types.
    Cast lockout/projectile travel and mana are not inferred from these timestamps.
    """
    values=(ad,attack_speed,crit_chance,crit_damage,hp,armor,ability_haste,pct_pen,flat_pen)
    if not all(math.isfinite(x) for x in values) or hp<=0 or ad<0 or attack_speed<=0 or ability_haste<0 or not 0<=pct_pen<=1 or flat_pen<0:raise ValueError('Invalid combat stats.')
    if not 1<=level<=15 or not 0<=crit_chance<=1 or crit_damage<1:raise ValueError('Invalid champion stats.')
    if mode not in ('Expected','Seeded critical rolls'):raise ValueError('Unknown critical mode.')
    if keystone not in (None,'Conqueror','Lethal Tempo'):raise ValueError('This replay supports Conqueror or Lethal Tempo only.')
    if any(x not in ('Brutal','Cut Down','Coup de Grace','Battle Zeal','Legend: Alacrity') for x in sub_runes):raise ValueError('Unsupported offensive rune in replay.')
    if not 0<=q_rank<=4 or not 0<=r_rank<=3:raise ValueError('Invalid skill rank.')
    if r_duration is not None and (not math.isfinite(r_duration) or r_duration<=0):raise ValueError('Invalid R duration.')
    if any(not math.isfinite(e.time) or e.time<0 or e.action not in ('AA','Q','R') for e in events):raise ValueError('Invalid impact timeline.')
    rng=random.Random(seed); queue=[(e.time,i,e.action,None) for i,e in enumerate(events)];queue.sort(key=lambda x:(x[0],x[1]))
    base_ad=ad if base_ad is None else base_ad
    dark=0; ultimate_cast_time=None
    conq=lt=style=aa=casts=0; last_style=None; conq_expiry=lt_expiry=-1.; next_aa=next_q=next_r=0.; channel_until=-1.; combat_start=None; spell_pending=False
    health=float(hp); log=[]; rejected=[]; total=0.; killed=None; r_cast_id=0
    def reject(t,action,reason):rejected.append({'time':t,'action':action,'reason':reason})
    while queue and health>0:
        t,order,action,cast_id=queue.pop(0)
        if t>=conq_expiry:conq=0
        if t>=lt_expiry:lt=0
        if action!='R tick' and t<channel_until:reject(t,action,'R channel active');continue
        if action=='AA' and t+1e-9<next_aa:reject(t,action,'Attack interval has not elapsed');continue
        if action=='Q' and (q_rank==0 or t+1e-9<next_q):reject(t,action,'Q unlearned or on cooldown');continue
        if action=='R':
            if r_rank==0 or t+1e-9<next_r:reject(t,action,'R unlearned or on cooldown');continue
            if style<6:reject(t,action,'S style required');continue
            if r_duration is None:reject(t,action,'R channel timing unknown: supply measured duration');continue
            r_cast_id+=1;style=0;last_style=None;channel_until=t+r_duration;next_r=t+6/(1+ability_haste/100);casts+=1;spell_pending=True;ultimate_cast_time=t
            # First and last impact bounds are explicit model assumptions, not cast-time inference.
            for shot in range(10):queue.append((t+r_duration*shot/9,order+shot/100,'R tick',(r_cast_id,shot)))
            queue.sort(key=lambda x:(x[0],x[1]));continue
        before_hp=health;before={'style':style,'conqueror':conq,'lethal_tempo':lt,'AA':aa,'skills':casts}
        bonus_ad=conq*(3+(level-1)*2/14) if keystone=='Conqueror' else 0.
        current_ad=ad+bonus_ad
        current_crit=min(1.,crit_chance+(min(.25,yuntal_initial+.002*aa) if yuntal else 0.))
        rolled=(rng.random()<current_crit) if mode=='Seeded critical rolls' else None
        probability=current_crit if rolled is None else float(rolled)
        live_pen=min(.40,pct_pen+.10*dark) if terminus else pct_pen
        ea=effective_resistance(armor,live_pen,flat_pen)
        if action=='AA':
            bonus_as=.048*lt if keystone=='Lethal Tempo' else 0.
            if aa_hit:
                hit=aa_hit({'hp':health,'time':t,'bonus_ad':bonus_ad,'bonus_as':bonus_as,'crit':probability,'event_driven':True,'spell_cast':spell_pending,'ultimate_cast_time':ultimate_cast_time})
                damage=hit['damage'];speed=hit['as'];ea=hit['armor'];dark=hit.get('dark',dark)
                lt_bonus_as=hit.get('bonus_as_total',bonus_as)
            else:
                damage=current_ad*(1+probability*(crit_damage-1))*resistance_multiplier(ea)
                speed=attack_speed*(1+bonus_as);lt_bonus_as=bonus_as
            if keystone=='Lethal Tempo' and lt>=6:
                damage+=(6+(level-1))* (1+.0033*lt_bonus_as*100)*resistance_multiplier(ea)
            if 'Brutal' in sub_runes:damage+=(6+.08*max(0,current_ad-base_ad))*resistance_multiplier(ea)
            next_aa=t+1/speed;aa+=1;spell_pending=False
        else:
            slot='Q' if action=='Q' else 'R'
            rank=q_rank if slot=='Q' else r_rank
            hit=samira_skill(slot,rank,current_ad,probability,crit_damage,armor,pct_pen=live_pen,flat_pen=flat_pen,outcome='Expected',hits=1)
            damage=hit.total
            if action=='Q':next_q=t+[6.5,5,3.5,2][q_rank-1]/(1+ability_haste/100);casts+=1;spell_pending=True
            if action=='Q' and 'Battle Zeal' in sub_runes and combat_start is not None:damage*=1+.014*min(3,int(t-combat_start))
        if 'Cut Down' in sub_runes and before_hp/hp>.60:damage*=1.065
        if 'Coup de Grace' in sub_runes and before_hp/hp<.40:damage*=1.08
        health=max(0.,health-damage);total+=damage
        if combat_start is None:combat_start=t
        # Stack grants are after the hit and change the NEXT event's stats.
        separate=(action!='R tick' or cast_id[1]==0)
        if keystone=='Conqueror' and separate:conq=min(6,conq+1);conq_expiry=t+6
        if keystone=='Lethal Tempo' and action=='AA':lt=min(6,lt+1);lt_expiry=t+6
        if action in ('AA','Q') and action!=last_style:style=min(6,style+1);last_style=action
        after={'style':style,'conqueror':conq,'lethal_tempo':lt,'AA':aa,'skills':casts}
        log.append({'time':t,'action':action,'AD':current_ad,'crit_chance':current_crit,'critical':rolled,'damage':damage,'hp_before':before_hp,'hp_after':health,'before':before,'after':after})
        if health<=0:killed=t
    return FightResult(log,rejected,health,aa,casts,total,killed)
