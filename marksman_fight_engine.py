"""Event-driven single-target adapters for the remaining WR marksmen.

Known damage/state rules are executable. Unresolved WR parameters are exposed in
FightResult.assumptions and the persistent TODO, not presented as verified parity.
The target never attacks. Timing follows sourced casts/channels when available.
"""
import heapq
import itertools
import math
from damage_classification import event_profile,ability_magnification,component_profile,magnification
from champion_skill_data import resistance_multiplier,effective_resistance
from marksman_kits import Kit,default_ranks
from marksman_damage_components import damage_component,yunara_arc_of_ruin,varus_blight,jhin_attack_damage,RawDamage


def replay_marksman(events,**p):
    from fight_engine import FightResult
    name=p['champion'];level=p['level'];ad=p['ad'];base_ad=p.get('base_ad') if p.get('base_ad') is not None else ad
    ap=p.get('ap',0.);maxhp=p['hp'];health=float(maxhp);armor=p['armor'];mr=p.get('mr',0.)
    crit=p['crit_chance'];critd=p['crit_damage'];base_as=p['attack_speed'];haste=p.get('ability_haste',0.)
    if p.get('mode','Expected')!='Expected':raise ValueError('Marksman adapters use expected damage')
    for value in (level,ad,base_ad,ap,maxhp,armor,mr,crit,critd,base_as,haste):
        if not math.isfinite(value):raise ValueError('Nonfinite combat stat')
    if not isinstance(level,int) or not 1<=level<=15 or min(ad,base_ad,ap,haste)<0 or maxhp<=0 or base_as<=0 or not 0<=crit<=1 or critd<1:raise ValueError('Invalid combat stats')
    ranks={s:p.get({'Q':'q_rank','W':'w_rank','E':'e_rank','R':'r_rank'}[s],default_ranks(name,level)[s]) for s in 'QWER'}
    for s,r in ranks.items():
        if not isinstance(r,int) or isinstance(r,bool) or not 0<=r<=(3 if s=='R' else 4):raise ValueError('Invalid skill rank')
    maxmana=p.get('max_mana');mana=maxmana;regen=p.get('mana_regen_per_5s',0.)/5
    ms=p.get('movement_speed',0.);gap=float(p.get('distance',p.get('attack_range',550.)))
    if gap<0 or ms<0 or regen<0 or maxmana is not None and (maxmana<0 or not math.isfinite(maxmana)):raise ValueError('Invalid spatial/resource stats')
    movement_policy=p.get('movement_policy','skill_envelope');ultimate_policy=p.get('ultimate_policy','immediate')
    if movement_policy not in ('skill_envelope','aa_envelope','close_envelope'):raise ValueError('Invalid movement policy')
    if ultimate_policy not in ('immediate','after_basics'):raise ValueError('Invalid ultimate policy')
    attack_range=p.get('attack_range',550.)
    if attack_range is None:attack_range=0.
    kit=Kit(name,ranks,level,attack_range,mist=p.get('mist',0),weapon=p.get('weapon','minigun'))
    if maxmana is None:kit.unresolved.add('Maximum mana unknown: resource affordability is unresolved; mana costs still logged')
    if name=='Yunara':kit.state['unleash']=0
    ready={s:0. for s in 'QWER'};kit.state['born']=0.
    aa_clock=0.;t=0.;last_t=0.;last_speed=base_as;lock=0.;channel=0.;root_until=0.;aa_lock=0.;dash_until=0.
    cast_id=0;aa_count=skill_count=0;log=[];rejected=[];total=0.;killed=None
    conq=lt=0;conq_until=lt_until=-1.;combat_start=None;ultimate=None;spell_pending=False;spell_cast_times=[]
    items={'yuntal_crit':min(.25,p.get('yuntal_initial',0.))};kite_arc=0.;dark=0;transcend_ready=0.;amp=p.get('skill_amp',1.)
    runes=set(p.get('sub_runes',()));keystone=p.get('keystone');aa_hit=p.get('aa_hit');aa_stats=p.get('aa_stats')
    if keystone not in (None,'Conqueror','Lethal Tempo'):raise ValueError('Unsupported offensive keystone')
    if not 0<=p.get('mana_refund',0.)<=1 or not 0<=p.get('collector_threshold',0.)<=1 or amp<=0:raise ValueError('Invalid modifiers')
    for key in ('pct_pen','pct_mpen'):
        if not 0<=p.get(key,0.)<=1:raise ValueError('Invalid percentage penetration')
    for key in ('flat_pen','flat_mpen'):
        if not math.isfinite(p.get(key,0.)) or p.get(key,0.)<0:raise ValueError('Invalid flat penetration')
    sequence=itertools.count();heap=[];hit_casts=set();shock_casts=set();manual=bool(events)
    end=p.get('automatic_until') or (120. if p.get('until_death') else (max((e.time for e in events),default=0)+15.))
    if not 0<end<=120:raise ValueError('Fight duration must be in (0,120]')
    for e in events:
        if e.action not in ('AA','Q','W','E','R') or e.time<0 or not math.isfinite(e.time):raise ValueError('Invalid command')
        heapq.heappush(heap,(e.time,next(sequence),'command',{'action':e.action}))
    def queue(time,kind,**payload):heapq.heappush(heap,(time,next(sequence),kind,payload))
    def reduce(slot,seconds=0.,fraction=0.):ready[slot]=t+max(0.,ready[slot]-t)*(1-fraction);ready[slot]=max(t,ready[slot]-seconds)
    def buff(key,duration,value):kit.buff(key,t+duration,value)
    def add(key,count=1,cap=None,duration=None):
        kit.state[key]=kit.state.get(key,0)+count
        if cap is not None:kit.state[key]=min(cap,kit.state[key])
        if duration is not None:kit.state[key+'_until']=t+duration
    def total_as():
        bonus=kit.bonus_as(t)+(.048*lt if keystone=='Lethal Tempo' and t<lt_until else 0.)
        if aa_stats:
            value=aa_stats({'time':t,'bonus_as':bonus,'items':items,'ultimate_cast_time':ultimate,'distance':gap})
            raw=value['as'];bonus_total=value.get('bonus_as_total',0.)
        else:
            bonus_total=p.get('starting_bonus_as',0.)+bonus;raw=base_as*(1+bonus_total);value={'bonus_as_total':bonus_total}
        if name=='Jhin':
            # WR reload/fixed-AS progression is sourced in kit overrides.
            raw=p.get('natural_attack_speed',base_as)
        if name=='Zeri':
            cap=3. if kit.active('zeri_ultimate_as',t) else 1.5
            raw=min(cap,raw)
        return max(.01,min(3.,raw)),value
    def current_ad():
        value=ad+kit.bonus_ad(t)+(conq*(3+(level-1)*2/14) if keystone=='Conqueror' else 0.)
        if name=='Jhin':
            _,info=total_as();value=jhin_attack_damage(value,level,info.get('bonus_as_total',0.),probability())
        if name=='Sivir' and kit.active('morale',t):value+=kit.state.get('morale',0)*(2,2.5,3)[ranks['R']-1]
        if name=='Zeri':
            _,info=total_as();bonus=info.get('bonus_as_total',0.)
            # The cap threshold is converted back to bonus-AS percentage points.
            ratio=p.get('as_ratio',base_as);threshold=max(0.,(1.5-base_as)/ratio)
            if not kit.active('zeri_ultimate_as',t):value+=.5*max(0.,(bonus-threshold)*100)
        return value
    def probability():return min(1.,crit+(items.get('yuntal_crit',0.) if p.get('yuntal') else 0.))
    def effective():
        pen=p.get('pct_pen',0.)+(.1*dark if p.get('terminus') else 0.)
        mp=p.get('pct_mpen',0.)+(.1*dark if p.get('terminus') else 0.)
        if p.get('terminus'):pen=min(.4,pen);mp=min(.4,mp)
        arm=armor;mres=mr
        if kit.active('spittle',t):arm*=1-kit.buff_values['spittle'];mres*=1-kit.buff_values['spittle']
        if kit.active('gatling',t):
            fraction=min(1.,max(0.,t-kit.state.get('gatling_start',t))/2)
            shred=(12,14,16,18)[ranks['E']-1]*fraction;arm-=shred;mres-=shred
        return effective_resistance(arm,pen,p.get('flat_pen',0.)),effective_resistance(mres,mp,p.get('flat_mpen',0.))
    def raw(slot,*,hits=1,stacks=0,empowered=False):
        return damage_component(name,slot,ranks[slot],ad=current_ad(),base_ad=base_ad,ap=ap,crit_chance=probability(),crit_damage=critd,stacks=stacks,hits=hits,target_max_hp=maxhp,target_missing_hp=maxhp-health,level=level,empowered=empowered)
    def multiplier(action):
        v=amp
        if name=='Miss Fortune' and kit.state.get('love_tap',0)>=3:v*=1.06
        if 'Cut Down' in runes and health/maxhp>.6:v*=1.065
        if 'Coup de Grace' in runes and health/maxhp<.4:v*=1.08
        if action!='AA' and action.startswith(('Q','W','E')) and 'Battle Zeal' in runes and combat_start is not None:v*=1+.014*min(3,int(t-combat_start))
        return v
    def record(action,value,*,cid=None,eligible=False,effects=(),raw_override=None,before=None,used_ad=None,used_crit=None,components=None):
        nonlocal health,total,killed,conq,conq_until,lt,lt_until,combat_start
        if health<=0:return
        applied_ad=current_ad() if used_ad is None else used_ad;applied_crit=probability() if used_crit is None else used_crit
        prior=health;ea,em=effective()
        classification=event_profile(name,action)
        if any((value.physical,value.magic,value.true)) and classification['status']=='unknown_WR':kit.unresolved.add(f'{name} {action}: WR damage tags unresolved')
        class_amp=ability_magnification(name,action,gap,p.get('hexoptics',False)) if not action.startswith('AA') else 1.
        damage=(value.physical*resistance_multiplier(ea)+value.magic*resistance_multiplier(em)+value.true)*multiplier(action)*class_amp if raw_override is None else raw_override
        if p.get('muramana') and eligible and not action.startswith('AA') and cid not in shock_casts:
            damage+=.03*(maxmana or 0.)*resistance_multiplier(ea)*amp;shock_casts.add(cid)
        if not math.isfinite(damage) or damage<0:raise ValueError('Invalid event damage')
        health=max(0.,health-damage);executed=False
        threshold=p.get('collector_threshold',0.)
        if threshold and 0<health<=maxhp*threshold:health=0.;executed=True
        dealt=prior-health;total+=dealt
        if eligible and cid not in hit_casts:
            hit_casts.add(cid)
            if keystone=='Conqueror':conq=min(6,conq+1);conq_until=t+6
        if action=='AA' and keystone=='Lethal Tempo':lt=min(6,lt+1);lt_until=t+6
        if combat_start is None and damage:combat_start=t
        log.append({'time':t,'action':action,'damage_classification':classification,'damage_components':components if components is not None else value.instances(name,action[0]) if action and action[0] in 'QWER' else [{'damage_type':k,'raw_amount':v,'tags':classification['tags'],'status':classification['status']} for k,v in (('physical',value.physical),('magic',value.magic),('true',value.true)) if v],'AD':applied_ad,'crit_chance':applied_crit,'critical':None,'damage':dealt,'raw_damage':damage,'physical':value.physical,'magic':value.magic,'true':value.true,'hp_before':prior,'hp_after':health,'mana':mana,'max_mana':maxmana,'distance':gap,'windup':kit.state.get('aa_windup',0.) if action.startswith('AA') else None,'melee':gap<=200,'executed':executed,'effects':list(effects),'before':before or {},'after':kit.snapshot(t)|{'conqueror':conq,'lethal_tempo':lt,'items':dict(items)},'cooldowns':{s:max(0.,v-t) for s,v in ready.items()},'ability_haste':haste,'dragon_stacks':0,'kite_arc':kite_arc,'kite_angle':math.asin(math.sin(kite_arc/max(1.,kit.attack_range(t))*3))/3,'movement_policy':movement_policy})
        if health<=0:killed=t
    def tick(action,value,**kw):record(action,value,**kw)
    def damage_impact(slot,cid,index=0):
        nonlocal mana,spell_pending,dark,items
        before=kit.snapshot(t);s=kit.state;c=name;r=ranks[slot];value=RawDamage();effects=[]
        try:
            if c=='Twitch':
                if slot=='W':
                    add('venom',cap=5,duration=5)
                    if not s.get('poison_ticking',False):s['poison_ticking']=True;queue(t,'poison')
                    for j in range(1,4):queue(t+j,'venom_pool',cid=cid)
                    return
                if slot=='E':value=raw('E',stacks=s.get('venom',0))
            elif c=='Tristana' and slot=='E':
                s['bomb']=0;s['bomb_active']=cid;queue(t+4,'bomb_expire',cid=cid);return
            elif c=='Ezreal':
                if slot=='W':s['flux']=1;s['flux_until']=t+4;return
                if s.get('flux',0):
                    flux=raw('W');tick('W detonation',flux,cid=cid,eligible=True);s['flux']=0;s.pop('flux_until',None)
                    if mana is not None:mana=min(maxmana,mana+(60,70,80,90)[ranks['W']-1]);effects.append('Essence Flux mana refund')
                value=raw(slot);add('rising_spell_force',cap=4,duration=8)
                if slot=='Q':
                    for basic in 'QWER':reduce(basic,seconds=1.5)
            elif c=='Varus':
                if slot=='Q':
                    value=RawDamage(physical=(120,210,300,390)[r-1]+(1.65,1.8,1.95,2.1)[r-1]*max(0.,current_ad()-base_ad))
                    kit.unresolved.add('Varus Q rank 2–4 ratios sourced from WR wiki, retaining user bonus-AD basis; wiki total-AD wording conflicts')
                else:value=raw(slot)
                blight=s.get('blight',0)
                if blight:
                    det=varus_blight(ranks['W'],blight,target_max_hp=maxhp,ap=ap) if ranks['W'] else RawDamage()
                    value=RawDamage(value.physical,value.magic+det.magic*(1.5 if slot=='Q' else 1),value.true);s['blight']=0
                    for basic in 'QWE':reduce(basic,seconds=(kit.cd(basic) or 0.)/(1+haste/100)*.13*blight)
                if slot=='Q' and kit.active('varus_empower',t):
                    value=RawDamage(value.physical,value.magic+(maxhp-health)*(.09,.12,.15,.18)[ranks['W']-1],value.true);kit.buff_end.pop('varus_empower',None)
                if slot=='R':
                    for j in range(1,4):queue(t+.5*j,'blight')
            elif c=='Kalista' and slot=='E':value=raw('E',stacks=s.get('rend',0));s['rend']=0
            elif c=='Xayah':
                if slot=='Q':value=raw('Q',hits=2);kit.feathers.extend([t+6]*2)
                elif slot=='E':
                    count=s.pop('recall_count',0)
                    value=raw('E',hits=count) if count else RawDamage();effects.append(f'{count} aligned feathers recalled; 10 percentage-point falloff, floor 10%')
                elif slot=='R':value=raw('R');kit.feathers.extend([t+6]*5)
            elif c=="Kai'Sa":
                if slot=='Q':value=raw('Q',hits=12 if s.get('q_evolved') else 6)
                elif slot=='W':
                    value=raw('W');add('plasma',3 if s.get('w_evolved') else 2,cap=5,duration=4)
                    if s.get('w_evolved'):reduce('W',fraction=.7)
            elif c=='Corki':
                if slot=='R':value=raw('R',empowered=index%3==0)
                else:value=raw(slot)
                if slot in ('W','E'):value=RawDamage(value.physical*.25,value.magic*.25)
            elif c=='Lucian' and slot=='R':value=raw('R')
            elif c=='Miss Fortune':
                if slot=='R':value=raw('R')
                else:value=raw(slot)
            elif c=='Jhin':
                if slot=='R':
                    normal=raw('R');value=RawDamage(physical=normal.physical*(2 if index==3 else 1))
                    if index==3:value=RawDamage(physical=normal.physical*critd)
                else:value=raw(slot)
            elif c=='Caitlyn' and slot=='R':
                kit.unresolved.add('Caitlyn R crit modifier unresolved: confirmed non-crit component only')
                value=RawDamage(physical=(250,450,650)[r-1]+max(0.,current_ad()-base_ad)+.2*(maxhp-health))
            elif c=='Jinx' and slot=='R':
                kit.unresolved.add('Jinx R distance/flight curve unresolved: minimum flight-damage component')
                value=RawDamage(physical=(25,35,45)[r-1]+.12*max(0.,current_ad()-base_ad)+(.25,.30,.35)[r-1]*(maxhp-health))
            elif c=="Kog'Maw" and slot=='R':
                normal=(80,120,160)[r-1]+.75*max(0.,current_ad()-base_ad)+.25*ap
                if health/maxhp<.4:value=RawDamage(magic=normal*2)
                else:
                    kit.unresolved.add('Kog’Maw R missing-health interpolation unresolved: non-amplified component above 40%')
                    value=RawDamage(magic=normal)
            elif c=='Yunara':
                if slot=='W' and kit.active('transcend',t):value=yunara_arc_of_ruin(ranks['R'],bonus_ad=max(0.,current_ad()-base_ad),ap=ap)
                elif slot=='W':
                    value=raw('W')
                    kit.unresolved.add('Yunara W linger contact/total ticks unresolved: initial hit only')
                else:return
            else:value=raw(slot)
        except LookupError as exc:
            kit.unresolved.add(str(exc));return
        item_damage=0.
        if aa_hit and event_profile(name,slot).get('properties',{}).get('TriggerOnHitEvents') is True:
            ea,em=effective()
            item=aa_hit({'hp':health,'time':t,'mana':mana,'max_mana':maxmana,'bonus_ad':current_ad()-ad,'bonus_as':kit.bonus_as(t)+(.048*lt if keystone=='Lethal Tempo' else 0.),'crit':0.,'melee':gap<=200,'event_driven':True,'spell_cast':spell_pending,'spell_cast_times':list(spell_cast_times),'ultimate_cast_time':ultimate,'distance':gap,'attack_physical':0.,'critical_attack_physical':0.,'armor_override':ea,'mr_override':em,'skill_on_hit':True})
            item_damage=item['damage'];spell_pending=False;spell_cast_times.clear();dark=item.get('dark',dark)
            items.update({k:item.get(k,0) for k in ('rage','dark','light','phantom_dancer','kraken','yuntal_crit')})
            effects.extend(item.get('notes',[]));kit.unresolved.add('Skill on-hit item stack eligibility/Phantom Hit interactions remain provisional')
        if item_damage:
            ea,em=effective();dealt=(value.physical*resistance_multiplier(ea)+value.magic*resistance_multiplier(em)+value.true)*multiplier(slot)*ability_magnification(name,slot,gap,p.get('hexoptics',False))+item_damage*multiplier(slot)/amp
            record(slot if index==0 else slot+' hit',value,cid=cid,eligible=True,effects=effects,before=before,raw_override=dealt)
        else:
            record(slot if index==0 else slot+' hit',value,cid=cid,eligible=True,effects=effects,before=before)

        if name=="Kog'Maw" and slot=='Q':buff('spittle',4,(.2,.24,.28,.32)[r-1])
        if name=='Miss Fortune' and t>=kit.state.get('love_ability_ready',-1):
            add('love_tap',cap=3,duration=5);kit.state['love_ability_ready']=t+1
        if name=='Kalista' and slot=='Q':add('rend',duration=4)
        if name=='Lucian' and slot!='R':s['lightslinger']=1;s['lightslinger_until']=t+3.5
        if name=='Tristana' and slot in ('W','R'):bomb_stack()
        if name=="Kai'Sa":plasma()
        if name=='Sivir' and kit.active('morale',t):add('morale');kit.unresolved.add('Sivir Morale cap/expiry unresolved')
        if name=='Zeri' and slot!='E':
            reduce('E',seconds=.5)
            if kit.active('zeri_ultimate_as',t):kit.buff_end['zeri_ultimate_as']=min(t+5,kit.buff_end['zeri_ultimate_as']+1.5)
    def bomb_stack():
        s=kit.state
        if not s.get('bomb_active'):return
        s['bomb']=min(4,s.get('bomb',0)+1)
        if s['bomb']==4:
            record('E detonation',raw('E',stacks=4),cid=s['bomb_active'],eligible=True);s['bomb_active']=0;ready['W']=t
    def plasma():
        if kit.state.get('plasma',0)<5:return
        record('Plasma detonation',RawDamage(magic=(.15+.00025*ap)*(maxhp-health)),effects=('WR wiki: AP missing-health coefficient; user base preserved',));kit.state['plasma']=0
    def basic_attack(cid,secondary=False):
        nonlocal aa_count,dark,spell_pending,items,mana,aa_clock
        s=kit.state;before=kit.snapshot(t);cad=current_ad();prob=probability();ea,em=effective();critical=cad*critd;physical=cad*(1+prob*(critd-1));magic=true=0.;effects=[];phantom=False;nonbasic_physical=0.
        if name=='Ashe':
            if s.get('frost_until',-1)>t:physical=cad*(1+prob*(critd-1))
            else:physical=cad
            critical=physical
            if kit.active('focus_as',t):
                physical*=(1.15,1.2,1.25,1.3)[ranks['Q']-1];critical*=(1.15,1.2,1.25,1.3)[ranks['Q']-1]
                nonbasic_physical=physical*.8
                kit.unresolved.add('Ashe Q subsequent arrows: WR says default/proc; Hexoptics only first arrow, exact component split pending WR test')
            s['frost_until']=t+2;add('focus',cap=4,duration=4)
            kit.unresolved.add('Ashe first-hit/Frost base modifier and Q flurry item-on-hit count need WR validation')
        if name=='Draven' and s.get('axes',0):
            axe=raw('Q').physical;physical+=axe;critical+=axe
            kit.unresolved.add('Draven axe crit scope/catch timing provisional; explicit catch event after 1s')
            queue(t+1,'axe_catch')
        if name=='Vayne':
            if s.pop('tumble_attack',0):physical+=raw('Q').physical;critical+=raw('Q').physical;nonbasic_physical+=raw('Q').physical
            if ranks['W']:add('silver_bolts',cap=3)
            if ranks['W'] and s['silver_bolts']==3:
                true+=raw('W').true;s['silver_bolts']=0
        if name=='Twitch':
            add('venom',cap=5,duration=5)
            if not s.get('poison_ticking',False):s['poison_ticking']=True;queue(t,'poison')
        if name=='Kalista':add('rend',duration=4);kit.unresolved.add('Kalista boot hop speed/distance unresolved: max-range walking kite')
        if name=='Varus' and ranks['W']:magic+=raw('W').magic;add('blight',cap=3,duration=6)
        if name=='Yunara' and ranks['Q']:
            active=kit.active('unbound_as',t) or kit.active('transcend',t)
            magic+=raw('Q',empowered=active).magic
            magic+=cad*critd*prob*(.08+.0008*ap)
            if not active:add('unleash',2,cap=6,duration=6)
        if name=="Kog'Maw" and kit.active('barrage',t):magic+=raw('W').magic
        if name=='Xayah':
            if kit.active('plumage_as',t):nonbasic_physical+=physical*.25;physical*=1.25;critical*=1.25
            if s.get('feather_attacks',0):s['feather_attacks']-=1;kit.feathers.append(t+6)
        if name=='Miss Fortune':
            add('love_tap',cap=3,duration=5)
            if s['love_tap']==3:
                kit.unresolved.add('Miss Fortune Love Tap crit/level modifier unresolved: confirmed 60% base component only')
                extra=(15+.4*max(0.,cad-base_ad))*.6;physical+=extra;nonbasic_physical+=extra;reduce('W',seconds=2)
        if name=='Lucian' and secondary:
            factor=.4
            kit.unresolved.add('Lucian second-shot level progression unresolved: confirmed 40% baseline')
            physical*=factor;critical*=factor;reduce('E',seconds=2)
        elif name=='Lucian' and s.pop('lightslinger',0):
            queue(t,'aa_hit',cid=cid,secondary=True);reduce('E',seconds=2)
        if name=='Caitlyn':
            add('headshot',cap=6)
            if s.get('headshot_ready') or s['headshot']>=6:
                extra=.6*cad
                physical+=extra;critical+=extra;s['headshot']=0;s['headshot_ready']=False
                kit.unresolved.add('Caitlyn headshot level/crit progression unresolved: confirmed 60% baseline')
            if s.pop('trap_bonus',False):physical+=raw('W').physical;critical+=raw('W').physical
        if name=='Jinx':
            if kit.weapon=='minigun':add('minigun',cap=3,duration=2.5)
            else:
                cost=kit.cost('Q',t)
                if mana is not None and mana<cost:kit.weapon='minigun'
                else:
                    if mana is not None:mana-=cost
                    physical*=1.12;critical*=1.12
        if name=="Kai'Sa":
            add('plasma',cap=5,duration=4);reduce('E',seconds=.5)
            kit.unresolved.add('Kai’Sa passive level progression unresolved: level-one known base only')
            magic+=5+.12*ap+max(0,s['plasma']-1)*(2+.02*ap)
        if name=='Corki':
            true+=.16*cad*(1+prob*(critd-1));kit.unresolved.add('Corki passive Spellblade/crit interaction order needs validation')
            if kit.recharge_at is not None:
                kit.recharge_at=max(t,kit.recharge_at-(2+3*prob));add('recharge_seq');queue(kit.recharge_at,'corki_recharge',seq=s['recharge_seq'])
        if name=='Senna':
            physical=cad*(1+prob*(.9*critd-1))
            critical=cad*.9*critd;reduce('Q',seconds=1)
            kit.unresolved.add('Senna passive bonus AA and two-hit level progression unresolved: confirmed base extra 10 physical')
            physical+=10;critical+=10;nonbasic_physical+=10
            if t>=s.get('senna_lock',-1):
                if s.get('senna_mark_until',-1)>t:
                    physical+=.01*health;nonbasic_physical+=.01*health;s['senna_lock']=t+6;s['senna_mark_until']=-1
                    kit.unresolved.add('Senna mist generation from champion siphon unresolved: initial supplied mist retained')
                else:s['senna_mark_until']=t+4
        if name=='Zeri':
            physical=(20+1.02*cad)*(1+prob*(critd-1));critical=(20+1.02*cad)*critd
            kit.unresolved.add('Zeri Burst Fire flat level progression unresolved: confirmed 20 baseline')
            if s.get('spark_attacks',0):magic+=raw('E').magic;s['spark_attacks']-=1
            reduce('E',seconds=.5+prob)
            if kit.active('zeri_ultimate_as',t):kit.buff_end['zeri_ultimate_as']=min(t+5,kit.buff_end['zeri_ultimate_as']+1.5)
        if name=='Jhin':
            physical=cad*(1+prob*(.8*critd-1));critical=cad*.8*critd
            if kit.ammo==1:
                nonbasic_physical+=(.11+.01*(level-1))*(maxhp-health);physical=critical+nonbasic_physical
            kit.ammo-=1
            if kit.ammo==0:
                kit.reloading_until=t+2.5;queue(t+2.5,'reload');effects.append('Reload started (2.5s WR source)')
        bonus=cad-ad
        components=[{'damage_type':'physical','raw_amount':physical-nonbasic_physical,'tags':['BasicAttack'],'status':'fundamental_basic_attack'}]
        if nonbasic_physical:components.append({'damage_type':'physical','raw_amount':nonbasic_physical,'tags':[],'status':'nonbasic_or_unresolved_WR','component':'champion additional physical damage'})
        if magic:components.append({'damage_type':'magic','raw_amount':magic,'tags':[],'status':'nonbasic_or_unresolved_WR','component':'champion on-hit/passive addition'})
        if true:components.append({'damage_type':'true','raw_amount':true,'tags':component_profile(name,'P')['tags'] if name=='Corki' else component_profile(name,'W')['tags'],'status':'WR_wiki_classification'})
        if aa_hit:
            hit=aa_hit({'hp':health,'time':t,'mana':mana,'max_mana':maxmana,'bonus_ad':bonus,'bonus_as':kit.bonus_as(t)+(.048*lt if keystone=='Lethal Tempo' else 0.),'crit':prob,'melee':gap<=200,'event_driven':True,'spell_cast':spell_pending,'spell_cast_times':list(spell_cast_times),'ultimate_cast_time':ultimate,'distance':gap,'attack_physical':physical,'nonbasic_attack_physical':nonbasic_physical,'critical_attack_physical':critical,'armor_override':ea,'mr_override':em})
            components.extend(hit.get('damage_components',[]));actual=hit['damage'];phantom='Phantom Hit' in hit.get('notes',[]);dark=hit.get('dark',dark);items={k:hit.get(k,0) for k in ('rage','dark','light','phantom_dancer','kraken','yuntal_crit')}
            actual+=magic*resistance_multiplier(em)*amp+true*amp*(magnification(gap,component_profile(name,'P')['tags']) if p.get('hexoptics') and name=='Corki' else 1.);effects+=hit.get('notes',[])
        else:actual=((physical-nonbasic_physical)*magnification(gap,['BasicAttack'])*resistance_multiplier(ea)+nonbasic_physical*resistance_multiplier(ea)+magic*resistance_multiplier(em)+true*(magnification(gap,component_profile(name,'P')['tags']) if name=='Corki' else 1.))*amp if p.get('hexoptics') else (physical*resistance_multiplier(ea)+magic*resistance_multiplier(em)+true)*amp
        if 'Brutal' in runes:actual+=(6+.08*max(0.,cad-base_ad))*resistance_multiplier(ea)*amp
        if keystone=='Lethal Tempo' and lt>=6:actual+=(6+level-1)*(1+.33*total_as()[1].get('bonus_as_total',0.))*resistance_multiplier(ea)*amp
        if name=='Miss Fortune' and kit.state.get('love_tap',0)>=3:actual*=1.06
        if 'Cut Down' in runes and health/maxhp>.6:actual*=1.065
        if 'Coup de Grace' in runes and health/maxhp<.4:actual*=1.08
        record('AA second' if secondary else 'AA',RawDamage(physical,magic,true),raw_override=actual,cid=cid,eligible=True,effects=effects,before=before,used_ad=cad,used_crit=prob,components=components)
        if not secondary:aa_count+=1
        spell_pending=False;spell_cast_times.clear()
        if p.get('navori'):
            for basic in 'QWE':reduce(basic,fraction=.15)
        if phantom:
            extra=RawDamage()
            if name=='Vayne' and ranks['W']:
                add('silver_bolts',cap=3)
                if kit.state['silver_bolts']==3:extra=raw('W');kit.state['silver_bolts']=0
            elif name=='Varus' and ranks['W']:extra=raw('W');add('blight',cap=3,duration=6)
            elif name=='Twitch':add('venom',cap=5,duration=5)
            elif name=='Kalista':add('rend',duration=4)
            elif name=='Yunara' and ranks['Q']:extra=raw('Q',empowered=kit.active('unbound_as',t) or kit.active('transcend',t))
            elif name=="Kog'Maw" and kit.active('barrage',t):extra=raw('W')
            elif name=="Kai'Sa":
                add('plasma',cap=5,duration=4);extra=RawDamage(magic=5+.12*ap+max(0,kit.state['plasma']-1)*(2+.02*ap))
            if extra.physical or extra.magic or extra.true:record('Phantom on-hit',extra,effects=('Champion on-hit repeated',))
        if name=='Tristana':bomb_stack()
        if name=="Kai'Sa":plasma()
        if name=='Ezreal' and s.get('flux',0):tick('W detonation',raw('W'),eligible=True,cid=cid);s['flux']=0
        if name=='Sivir' and kit.active('morale',t):add('morale')
    def cast(slot,manual_command=False):
        nonlocal mana,skill_count,cast_id,spell_pending,ultimate,lock,channel,root_until,aa_clock,dash_until,aa_lock,transcend_ready
        if not kit.enabled(slot,t):
            if manual_command:rejected.append({'time':t,'action':slot,'reason':'Unlearned, resource unresolved, or kit prerequisite not met'})
            return False
        if t+1e-9<max(lock,0. if name=='Zeri' and slot in ('W','R') and t<dash_until else aa_lock,ready[slot]) or t<channel and not(name=='Lucian' and slot=='E'):return False
        if gap>kit.range(slot,t)+1e-7:return False
        cost=kit.cost(slot,t)
        if mana is not None and mana+1e-9<cost:return False
        if mana is not None:mana=max(0.,mana-cost+cost*p.get('mana_refund',0.))
        cd=kit.cd(slot);cooldown_value=cd/(1+haste/100)
        if name=='Sivir' and slot in 'QWE' and kit.active('morale',t):cooldown_value*=1-(.2,.25,.3)[ranks['R']-1]
        ready[slot]=t+cooldown_value
        if name=='Caitlyn' and slot=='W':
            ready[slot]=t+(25,20,15,10)[ranks['W']-1]/(1+haste/100)
            kit.unresolved.add('Caitlyn trap ammo/recharge pool provisional: one charge per recharge')
        if name=='Jhin' and slot=='E':ready[slot]=t+(20,18,16,14)[ranks['E']-1]/(1+haste/100)
        skill_count+=1;cast_id+=1;cid=cast_id;spell_pending=True;spell_cast_times.append(t)
        if slot=='R':ultimate=t
        duration=kit.cast_time(slot,t,total_as()[1].get('bonus_as_total',0.));lock=t+duration
        arrival=lock+kit.travel(slot,gap)
        if name=='Varus' and slot=='Q':
            lock=t+1.5;channel=lock;arrival=lock+kit.travel(slot,gap);ready['Q']=lock+kit.cd('Q')/(1+haste/100);kit.state['mobile_cast_until']=lock;buff('charge_ms',1.5,.8)
        s=kit.state;r=ranks[slot];c=name
        if p.get('transcendence') and level>=9 and t>=transcend_ready:
            for basic in 'QWE':reduce(basic,fraction=.08)
            transcend_ready=t+8
        if c=='Varus' and slot=='W':buff('varus_empower',5.5,1);return True
        if c=='Twitch' and slot in ('Q','R'):
            buff('ambush_as' if slot=='Q' else 'ultimate_ad',6,(.35,.4,.45,.5)[r-1] if slot=='Q' else (30,45,60)[r-1]);return True
        if c=='Tristana' and slot=='Q':buff('rapid_fire_as',7,(.6,.8,1,1.2)[r-1]);return True
        if c=='Vayne':
            if slot=='Q':s['tumble_attack']=1;aa_clock=0.;kit.unresolved.add('Vayne Q dash speed/end-point unresolved: instant lateral tumble');return True
            if slot=='W':buff('silver_as',3,(.1,.15,.2,.25)[r-1]);return True
            if slot=='R':buff('ultimate_ad',(8,10,12)[r-1],(30,40,50)[r-1]);return True
        if c=='Ashe' and slot=='Q':s['focus']=0;buff('focus_as',6,(.2,.3,.4,.5)[r-1]);return True
        if c=='Draven':
            if slot=='Q':add('axes',cap=2);buff('axes',6,s['axes']);return True
            if slot=='W':buff('blood_rush_as',3,(.25,.3,.35,.4)[r-1]);return True
        if c=='Xayah':
            add('feather_attacks',3,cap=5,duration=7.5)
            if slot=='W':buff('plumage_as',4,(.4,.45,.5,.55)[r-1]);return True
            if slot=='E':s['recall_count']=len(kit.feathers);kit.feathers=[]
            if slot=='R':lock=max(lock,t+1.5);aa_lock=lock;kit.unresolved.add('Xayah R 1.5s untargetable lock provisional WR timing')
        if c=="Kog'Maw" and slot=='W':buff('barrage',8,r);return True
        if c=='Miss Fortune':
            if slot=='W':buff('strut_as',4,(.45,.6,.75,.9)[r-1]);return True
            if slot=='E':
                for j in range(8):queue(lock+.25*j,'skill_hit',slot=slot,cid=cid,index=j)
                return True
            if slot=='R':
                channel=t+3;root_until=channel
                count=(12,14,16)[r-1]
                for j in range(count):queue(t+3*j/count,'skill_hit',slot='R',cid=cid,index=j)
                return True
        if c=='Lucian':
            s['lightslinger']=1;s['lightslinger_until']=t+3.5
            if slot=='E':aa_clock=0.;dash_until=t+425/1350;aa_lock=dash_until;return True
            if slot=='R':
                channel=t+3
                count=max(1,int(20+20*probability()*(critd-1)))
                kit.unresolved.add('Lucian R bullet rounding/cap uses floor of tooltip candidate')
                for j in range(count):queue(t+3*j/count,'skill_hit',slot='R',cid=cid,index=j)
                return True
        if c=="Kai'Sa" and slot=='E':
            kit.unresolved.add('Kai’Sa E AS-dependent charge duration unresolved: provisional 1s charge')
            lock=t+1;aa_lock=lock;kit.state['mobile_cast_until']=lock;queue(lock,'buff',key='supercharge_as',duration=4,value=(.4,.5,.6,.7)[r-1]);return True
        if c=='Yunara':
            if slot=='Q':s['unleash']=0;buff('unbound_as',5,(.25,.35,.45,.55)[r-1]);return True
            if slot=='R':
                buff('transcend',15,1);buff('unbound_as',15,(.25,.35,.45,.55)[ranks['Q']-1] if ranks['Q'] else 0)
                reduce('W',fraction=.8);ready['E']=t;queue(t+15,'transcend_end');return True
        if c=="Kog'Maw" and slot=='R':
            add('artillery_cost');kit.state['artillery_cost_until']=t+8
        if c=='Corki':
            if slot=='E':
                buff('gatling',4,1);s['gatling_start']=t
                for j in range(16):queue(t+.25*j,'skill_hit',slot='E',cid=cid,index=j)
                kit.unresolved.add('Corki E/W tick cadence uses provisional 0.25s integration');return True
            if slot=='W':
                for j in range(10):queue(t+.25*j,'skill_hit',slot='W',cid=cid,index=j)
                return True
            if slot=='R':
                kit.ammo-=1;add('missile_sequence')
                if kit.recharge_at is None:
                    kit.recharge_at=t+16/(1+haste/100);add('recharge_seq');queue(kit.recharge_at,'corki_recharge',seq=s['recharge_seq'])
                queue(arrival,'skill_hit',slot='R',cid=cid,index=s['missile_sequence']);kit.unresolved.add('Corki recharge retains user 16s baseline; wiki 20s conflicts; AA refund candidate 2 + 3×crit');return True
        if c=='Caitlyn' and slot=='W':queue(t+1,'trap',cid=cid);kit.unresolved.add('Caitlyn trap arming provisional 1s');return True
        if c=='Caitlyn' and slot=='R':lock=t+1.5;arrival=lock+kit.travel('R',gap)
        if c=='Caitlyn' and slot=='E':s['headshot_ready']=True
        if c=='Jinx' and slot=='E':arrival=t+1;kit.unresolved.add('Jinx trap arming provisional 1s')
        if c=='Zeri':
            if slot=='E':
                s['spark_attacks']=3;buff('spark_attacks',6,3);aa_clock=0.;dash_until=t+300/(600+ms);aa_lock=dash_until;return True
            if slot=='R':buff('zeri_ultimate_as',5,.3)
        if c=='Sivir':
            if slot=='W':buff('ricochet_as',4,(.25,.3,.35,.4)[r-1]);return True
            if slot=='R':buff('morale',(8,10,12)[r-1],1);s['morale']=0;return True
            if slot=='Q':queue(arrival+.25,'skill_hit',slot='Q',cid=cid,index=1);kit.unresolved.add('Sivir Q return travel unresolved: provisional 0.25s return delay')
        if c=='Jhin' and slot=='R':
            lock=t+1;channel=t+2;root_until=channel;ready['R']=channel+kit.cd('R')/(1+haste/100)
            for j in range(4):queue(t+1+.25*(j+1),'skill_hit',slot='R',cid=cid,index=j)
            return True
        if c=='Draven' and slot=='R':queue(arrival+kit.travel('R',gap),'skill_hit',slot='R',cid=cid,index=1)
        queue(arrival,'skill_hit',slot=slot,cid=cid,index=0)
        return True
    def start_attack():
        nonlocal aa_clock,aa_lock
        bonus=total_as()[1].get('bonus_as_total',0.)
        windup=p.get('aa_windup') or 0.
        if name=='Senna':
            windup=.5/(1+.6*bonus)
            kit.unresolved.add('Senna WR base windup 0.5s with 60% AS scaling; level-dependent modifier unresolved')
        kit.state['aa_windup']=windup;aa_clock=1.;aa_lock=t+windup
        queue(t+windup,'aa_hit',cid=('AA',aa_count+1))
    priority=p.get('skill_priority',('Q','W','E'));use_e=p.get('use_e',True)
    action_policy=p.get('action_policy','skill_first')
    if action_policy not in ('skill_first','aa_weave'):raise ValueError('Invalid action policy')
    if p.get('galeforce'):queue(.001,'galeforce')
    # Evolution is based on purchased bonus stats, never on temporary fight buffs.
    if name=="Kai'Sa":
        evolved=set(p.get('evolved_slots',('Q','W','E') if p.get('completed_items',0)>=3 else tuple(s for s in priority[:p.get('completed_items',0)])))
        kit.state['q_evolved']='Q' in evolved;kit.state['w_evolved']='W' in evolved;kit.state['e_evolved']='E' in evolved
    while t<=end and health>0:
        dt=t-last_t
        if dt>0:
            aa_clock=max(0.,aa_clock-dt*last_speed)
            if mana is not None:mana=min(maxmana,mana+dt*regen)
            movement_block=max(root_until,dash_until,0. if last_t<kit.state.get('mobile_cast_until',-1) else max(lock,aa_lock))
            if last_t>=movement_block and ms:
                desired=kit.attack_range(t)
                # Enter a shorter damaging ability envelope only when it is ready.
                for s in priority:
                    if s=='E' and not use_e:continue
                    if kit.enabled(s,t) and t>=ready[s] and (mana is None or mana>=kit.cost(s,t)):
                        if movement_policy!='aa_envelope':desired=min(desired,kit.range(s,t))
                if movement_policy=='close_envelope':desired=min(desired,200.)
                move_factor=kit.buff_values.get('charge_ms',1.) if kit.active('charge_ms',t) else 1.
                if name=="Kai'Sa" and last_t<kit.state.get('mobile_cast_until',-1):move_factor=1+( .5,.55,.6,.65)[ranks['E']-1]
                step=ms*move_factor*dt
                if abs(gap-desired)<1e-7:
                    if name!='Xayah':kite_arc+=step
                    else:kit.unresolved.add('Xayah benchmark uses aligned radial movement against a stationary target; lateral feather collision geometry unverified')
                else:gap+=math.copysign(min(abs(gap-desired),step),desired-gap)
        kit.expire(t)
        if name=='Draven' and not kit.active('axes',t):kit.state['axes']=0
        if t>=conq_until:conq=0
        if t>=lt_until:lt=0
        while heap and heap[0][0]<=t+1e-9 and health>0:
            _,_,kind,payload=heapq.heappop(heap)
            if kind=='command':
                a=payload['action']
                if a=='AA':
                    if t>=max(lock,channel,aa_lock,kit.reloading_until) and aa_clock<=1e-9 and gap<=kit.attack_range(t)+1e-7:start_attack()
                    else:rejected.append({'time':t,'action':a,'reason':'Attack locked, reloading, on interval, or out of range'})
                elif not cast(a,True):rejected.append({'time':t,'action':a,'reason':'Cast locked, out of range, on cooldown, or insufficient mana'})
            elif kind=='galeforce':
                blocked=max(lock,channel,aa_lock,dash_until)
                if t<blocked:queue(blocked+1e-6,'galeforce')
                else:
                    if gap>925:
                        queue(t+.05,'galeforce');continue
                    gap=max(0.,gap-min(325.,max(0.,gap-(min(600.,kit.attack_range(t)) if name!='Samira' else 0.))))
                    if gap>600:
                        queue(t+.05,'galeforce');continue
                    record('Galeforce active',RawDamage(physical=40+(level-1)/14*80+.45*max(0.,current_ad()-base_ad)),effects=('Cloudburst active; 50s cooldown',))
                    queue(t+50,'galeforce')
            elif kind=='aa_hit':basic_attack(payload['cid'],payload.get('secondary',False))
            elif kind=='skill_hit':damage_impact(payload['slot'],payload['cid'],payload.get('index',0))
            elif kind=='buff':buff(payload['key'],payload['duration'],payload['value'])
            elif kind=='reload':kit.ammo=4
            elif kind=='corki_recharge':
                if payload.get('seq')==kit.state.get('recharge_seq'):
                    kit.ammo=min(4,kit.ammo+1)
                    if kit.ammo<4:
                        kit.recharge_at=t+16/(1+haste/100);add('recharge_seq');queue(kit.recharge_at,'corki_recharge',seq=kit.state['recharge_seq'])
                    else:kit.recharge_at=None
            elif kind=='axe_catch':
                kit.buff_end['axes']=t+6;ready['W']=t
            elif kind=='blight':add('blight',cap=3,duration=6)
            elif kind=='venom_pool':
                add('venom',cap=5,duration=5)
                if not kit.state.get('poison_ticking',False):kit.state['poison_ticking']=True;queue(t,'poison')
            elif kind=='poison':
                stacks=kit.state.get('venom',0)
                if stacks:
                    value=damage_component('Twitch','P',1,ad=current_ad(),base_ad=base_ad,ap=ap,stacks=stacks,level=level)
                    record('Venom tick',value);queue(t+1,'poison')
                else:kit.state['poison_ticking']=False
            elif kind=='bomb_expire':
                if kit.state.get('bomb_active')==payload['cid']:
                    record('E detonation',raw('E',stacks=kit.state.get('bomb',0)),eligible=True,cid=payload['cid']);kit.state['bomb_active']=0
            elif kind=='trap':kit.state['headshot_ready']=True;kit.state['trap_bonus']=True
            elif kind=='transcend_end':reduce('W',fraction=.8);ready['E']=t
        if health<=0:break
        if not manual:
            # Compare AA weaving against skill-first priorities without bypassing locks.
            if action_policy=='aa_weave' and t>=max(lock,channel,aa_lock,dash_until,kit.reloading_until) and aa_clock<=1e-9 and gap<=kit.attack_range(t)+1e-7:start_attack()
            if t>=max(lock,aa_lock) and (t>=channel or name=='Lucian'):
                if ultimate_policy=='immediate' and t>=channel and kit.rank('R') and t>=ready['R']:cast('R')
                for s in priority:
                    if s=='E' and not use_e:continue
                    if t<channel and not(name=='Lucian' and s=='E'):continue
                    if name=='Xayah' and s=='E' and len(kit.feathers)<p.get('recall_min_feathers',3):continue
                    if cast(s):
                        if t<lock or t<channel:break
                if ultimate_policy=='after_basics' and t>=max(lock,channel,aa_lock) and kit.rank('R') and t>=ready['R']:cast('R')
                if t>=max(lock,channel,aa_lock,dash_until,kit.reloading_until) and aa_clock<=1e-9 and gap<=kit.attack_range(t)+1e-7:
                    start_attack()
        last_t=t
        speed,info=total_as();last_speed=speed
        future=[end+1e-8]
        if heap:future.append(heap[0][0])
        for v in (lock,channel,aa_lock,dash_until,kit.reloading_until,*ready.values(),*kit.buff_end.values(),*[v for k,v in kit.state.items() if k.endswith('_until') and isinstance(v,(int,float))],conq_until,lt_until,info.get('buff_expiry',-1.)):
            if v>t+1e-8:future.append(v)
        if aa_clock>1e-9:future.append(t+aa_clock/speed)
        # Range entry and lateral walk are integrated at 20 Hz. Impacts, AA
        # intervals and all lock/expiry boundaries retain their exact timestamps.
        future.append(t+.05)
        next_t=min(future)
        if heap and abs(next_t-heap[0][0])<1e-8:next_t=heap[0][0]
        if next_t<=t+1e-9:
            if heap and heap[0][0]<=t+1e-9:continue
            next_t=t+.00001
        t=next_t
    return FightResult(log,rejected,health,aa_count,skill_count,total,killed,assumptions=sorted(kit.unresolved))
