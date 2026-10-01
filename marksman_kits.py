"""Wild Rift marksman adapters and explicit uncertainty metadata.

User damage/cooldowns take precedence. Missing WR timing uses the engine's
instant-impact mode for that action and is recorded, never a hidden PC fallback.
"""
from functools import lru_cache
import math
from marksman_ability_database import catalogue

PRIORITIES={
'Twitch':'EQW','Yunara':'QWE','Lucian':'QEW','Varus':'QWE','Ezreal':'QEW','Vayne':'QWE','Tristana':'EQW','Ashe':'QWE','Kalista':'EQW','Draven':'QWE','Caitlyn':'QWE','Jinx':'QWE',"Kai'Sa":'QEW',"Kog'Maw":'WQE','Miss Fortune':'QWE','Xayah':'EWQ','Sivir':'QWE','Corki':'QEW','Senna':'QWE','Zeri':'QEW','Jhin':'QWE','Samira':'QEW','Smolder':'QWE'}
# These actions offer no offensive value against the configured lone target,
# which never attacks; vision/ally-control/shield are not damage skills.
SOLO_DISABLED={'Kalista':{'W','R'},'Ashe':{'E'},'Sivir':{'E'},'Senna':{'E'},"Kai'Sa":{'R'}}
CHANNELS={'Miss Fortune':('R',3.,False),'Lucian':('R',3.,True)}

@lru_cache(maxsize=1)
def records():return catalogue()

def default_ranks(champion,level):
    if champion not in PRIORITIES or not isinstance(level,int) or not 1<=level<=15:raise ValueError('Invalid champion/level')
    if champion in ('Samira','Smolder'):
        order=('QEWQRQQEREEWRWW' if champion=='Samira' else 'QWEQRQQWRWWEREE')
        return {s:order[:level].count(s) for s in 'QWER'}
    primary,secondary,third=PRIORITIES[champion]
    start=('Q','E','W') if champion=='Xayah' else (primary,secondary,third)
    order=list(start)+[primary,'R',primary,primary,secondary,'R',secondary,secondary,third,'R',third,third]
    return {s:order[:level].count(s) for s in 'QWER'}

class Kit:
    def __init__(self,champion,ranks,level,attack_range,*,mist=0,weapon='minigun'):
        if champion not in records():raise ValueError('Unknown champion')
        self.name=champion;self.data=records()[champion]['abilities'];self.ranks=ranks;self.level=level
        self.base_range=attack_range;self.mist=mist;self.weapon=weapon;self.unresolved=set()
        self.disabled=set(SOLO_DISABLED.get(champion,()))
        self.state={};self.buff_end={};self.buff_values={};self.cast_id=0
        self.feathers=[];self.ammo=4 if champion in ('Jhin','Corki') else None;self.recharge_at=None
        self.reloading_until=-1.;self.last_style=None
        if champion=='Yunara':self.unresolved.add('Yunara core mana/MS/range await manual WR data; resource and spatial timing remain unresolved')
        self.unresolved.add('Unknown WR AA windup/projectile values use instant AA impacts; no PC fallback')
    def rank(self,slot):return self.ranks.get(slot,0)
    def cost(self,slot,t):
        if self.name=='Yunara' and t<self.buff_end.get('transcend',-1) and slot in ('Q','W','E'):return 0.
        if self.name=='Varus' and slot=='W':
            self.unresolved.add('Varus W cost absent in WR wiki: provisional free activation; verify in-game')
            return 0.
        if self.name=="Kog'Maw" and slot=='R':
            self.unresolved.add('Kog’Maw R initial mana/ramp source conflict: provisional 40 + 50 per cast, capped at user 500')
            return min(500.,40.+50*self.state.get('artillery_cost',0))
        v=self.data[slot]['mana_by_rank']
        if v is None:
            self.unresolved.add(f'{self.name} {slot} mana unresolved: action excluded from automatic rotation')
            return None
        return v[self.rank(slot)-1]
    def cd(self,slot):
        if self.name=='Ashe' and slot=='Q':return 0.
        if self.name=='Yunara':return {'Q':0.,'W':10.,'E':9.,'R':(70.,60.,50.)[self.rank('R')-1] if self.rank('R') else 0.}[slot]
        v=self.data[slot]['cooldown_by_rank']
        if v is None:self.unresolved.add(f'{self.name} {slot} cooldown unresolved');return None
        return v[self.rank(slot)-1]
    def cast_time(self,slot,t,bonus_as=0.):
        v=self.data[slot]['cast_time_seconds']
        if self.name=='Senna' and slot=='Q':
            self.unresolved.add('Senna Q level modifier unresolved: 80% of sourced WR base AA windup')
            return .4/(1+.6*bonus_as)
        if v is None:
            self.unresolved.add(f'{self.name} {slot} cast time unresolved: instant cast mode')
            return 0.
        return v
    def range(self,slot,t):
        # Dash target range is not damage reach; use the damage radius/AA envelope
        # where the source only describes how far a movement command can travel.
        if self.name=='Ezreal' and slot=='E':return 750.
        if self.name=='Lucian' and slot=='E':return math.inf
        if self.name=='Yunara':return self.attack_range(t)
        if self.name=='Corki' and slot=='E':return 600.
        if slot in ('R',) and self.name in ('Senna','Ezreal','Jinx','Draven'):return math.inf
        values=self.data[slot].get('target_range_by_rank')
        if values is not None:return values[self.rank(slot)-1]
        if self.name=='Ashe' and slot=='W':return 1200.
        if self.name=='Miss Fortune' and slot=='R':return 1450.
        if self.name=='Zeri' and slot=='R':return 640.
        self.unresolved.add(f'{self.name} {slot} range unresolved: conservative AA-range targeting')
        return self.attack_range(t)
    def travel(self,slot,gap):
        v=self.data[slot]['projectile_speed']
        # E dash values are movement speed, not attack missiles.
        if slot=='E' and self.name in ('Lucian','Zeri'):return 0.
        if v and v>0:return gap/v
        self.unresolved.add(f'{self.name} {slot} projectile timing unresolved: instant impact after cast')
        return 0.
    def expire(self,t):
        expired=[]
        for k,v in list(self.buff_end.items()):
            if t>=v:
                expired.append(k);del self.buff_end[k];self.buff_values.pop(k,None)
        for key,duration in [('venom',5),('rend',4),('blight',6),('focus',4),('plasma',4),('flux',4),('lightslinger',3.5),('rising_spell_force',8),('love_tap',5),('feather_attacks',7.5),('artillery_cost',8)]:
            if (t>self.state.get(key+'_until',math.inf) if key=='venom' else t>=self.state.get(key+'_until',math.inf)):self.state[key]=0;self.state.pop(key+'_until',None)
        while self.state.get('minigun',0) and t>=self.state.get('minigun_until',math.inf):
            self.state['minigun']-=1;self.state['minigun_until']+=2
        # Do not expire Tristana bomb before its damage event resolves.
        self.feathers=[x for x in self.feathers if x>t]
        return expired
    def buff(self,key,end,value):self.buff_end[key]=end;self.buff_values[key]=value
    def active(self,key,t):return t<self.buff_end.get(key,-1)
    def attack_range(self,t):
        value=self.base_range+(10*(self.level-1) if self.name=='Tristana' else 0)+(15*(self.mist//20) if self.name=='Senna' else 0)
        if self.name=='Twitch' and self.active('ultimate_ad',t):value+=225
        if self.name=="Kog'Maw" and self.active('barrage',t):value+=(90,120,150,180)[self.rank('W')-1]
        if self.name=='Jinx' and self.weapon=='rockets' and self.rank('Q'):value+=(80,95,110,125)[self.rank('Q')-1]
        return value
    def bonus_as(self,t):
        value=sum(v for k,v in self.buff_values.items() if k.endswith('_as') and self.active(k,t))
        if self.name=='Ezreal':value+=.13*self.state.get('rising_spell_force',0)
        if self.name=='Jinx' and self.weapon=='minigun' and self.rank('Q'):
            stacks=self.state.get('minigun',0);value+=(.175,.30,.425,.55)[self.rank('Q')-1]*(1+.5*(stacks-1)) if stacks else 0
        if self.name=="Kog'Maw" and self.rank('R'):value+=(.1,.2,.3)[self.rank('R')-1]
        return value
    def bonus_ad(self,t):return sum(v for k,v in self.buff_values.items() if k.endswith('_ad') and self.active(k,t))
    def enabled(self,slot,t):
        if not self.rank(slot) or slot in self.disabled or self.cost(slot,t) is None or self.cd(slot) is None:return False
        c=self.name;s=self.state
        if c=='Ashe' and slot=='Q':return s.get('focus',0)>=4 and not self.active('focus_as',t)
        if c=='Twitch' and slot=='E':return s.get('venom',0)>=5
        if c=='Kalista' and slot=='E':return s.get('rend',0)>0
        if c=='Draven' and slot=='Q':return s.get('axes',0)<2
        if c=='Vayne' and slot=='Q':return not s.get('tumble_attack',0)
        if c=='Tristana' and slot=='E':return not s.get('bomb_active',0)
        if c=='Ezreal' and slot=='W':return not s.get('flux',0)
        if c=='Xayah' and slot=='E':return len(self.feathers)>=1
        if c=='Jinx' and slot=='Q':return False # weapon is a candidate policy, not a toggle spam
        if c=='Corki' and slot=='R':return self.ammo>0
        if c=='Jhin' and slot=='R':return self.ammo==0
        if c=='Yunara' and slot=='Q':return s.get('unleash',0)>=6 and not self.active('unbound_as',t) and not self.active('transcend',t)
        if c=='Yunara' and slot=='E':return False # MS-only costs mana with no solo-DPS benefit
        return True
    def snapshot(self,t):
        return {'stacks':dict(self.state),'buffs':{k:v for k,v in self.buff_values.items() if self.active(k,t)},'ammo':self.ammo,'feathers':len(self.feathers),'weapon':self.weapon}
