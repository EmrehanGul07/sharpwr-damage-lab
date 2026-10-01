"""Known single-target WR state transitions, not a complete fight scheduler.

Only successful impacts may be applied. Caller must enforce mana, range, cast
locks, cooldown, hit deduplication and pending-effect resolution. Unknown expiry
or consumption rules are deliberately absent rather than guessed.
"""
from dataclasses import dataclass,field
import math

@dataclass
class KitState:
    champion:str
    stacks:dict=field(default_factory=dict)
    expiry:dict=field(default_factory=dict)
    buffs:dict=field(default_factory=dict)
    ready:dict=field(default_factory=lambda:{s:0. for s in 'QWER'})
    last_time:float=0.
    ammo:int|None=None
    last_action:str|None=None

    def __post_init__(self):
        from marksman_ability_database import catalogue
        if self.champion not in catalogue():raise ValueError('Unknown champion')
        if self.champion in ('Jhin','Corki'):self.ammo=4

    def advance(self,time):
        if not math.isfinite(time) or time<self.last_time:raise ValueError('State time must be finite and monotonic')
        for key,end in tuple(self.expiry.items()):
            if time>=end:
                self.stacks.pop(key,None);self.buffs.pop(key,None);del self.expiry[key]
        self.last_time=time

    def add(self,key,count=1,cap=None,duration=None):
        self.stacks[key]=self.stacks.get(key,0)+count
        if cap is not None:self.stacks[key]=min(cap,self.stacks[key])
        if duration is not None:self.expiry[key]=self.last_time+duration

    def buff(self,key,value,duration):
        self.buffs[key]=value;self.expiry[key]=self.last_time+duration

    def reduce(self,slot,seconds=0.,fraction=0.):
        self.ready[slot]=self.last_time+max(0.,self.ready[slot]-self.last_time)*(1-fraction)
        self.ready[slot]=max(self.last_time,self.ready[slot]-seconds)

    def impact(self,action,time,*,ranks=None,cast=True):
        """Apply one champion hit. `cast` marks the first impact of that cast.

        Return requested effects whose damage must be resolved by the scheduler.
        Multi-hit casts should set cast=False after the first successful impact.
        This API does not simulate allied damage or automatic axe catches.
        """
        if action not in ('AA','Q','W','E','R'):raise ValueError('Unknown impact action')
        self.advance(time);ranks=ranks or {s:1 for s in 'QWER'}
        for s,r in ranks.items():
            if s not in 'QWER' or not isinstance(r,int) or not 0<=r<=(3 if s=='R' else 4):raise ValueError('Invalid ranks')
        if action!='AA' and ranks.get(action,0)==0:raise ValueError('Unlearned skill')
        result=[];c=self.champion
        if c=='Twitch':
            if action in ('AA','W'):self.add('venom',cap=5,duration=5)
            if action=='E':result.append(('contaminate',self.stacks.get('venom',0)))
            if action=='Q':self.buff('ambush_as',(.35,.4,.45,.5)[ranks['Q']-1],6)
            if action=='R':self.buff('ultimate_ad',(30,45,60)[ranks['R']-1],6)
        elif c=='Kalista':
            if action in ('AA','Q'):self.add('rend',duration=4)
            if action=='E':result.append(('rend',self.stacks.pop('rend',0)));self.expiry.pop('rend',None)
        elif c=='Vayne':
            if action in ('AA','E'):
                self.add('silver_bolts',cap=3)
                if self.stacks['silver_bolts']==3:result.append(('silver_bolts',1));self.stacks['silver_bolts']=0
            if action=='W':self.buff('silver_as',(.10,.15,.20,.25)[ranks['W']-1],3)
            if action=='Q':self.stacks['tumble_attack']=1
            if action=='AA' and self.stacks.pop('tumble_attack',0):result.append(('tumble',1))
            if action=='R':self.buff('ultimate_ad',(30,40,50)[ranks['R']-1],(8,10,12)[ranks['R']-1])
        elif c=='Tristana':
            # Resolve expired bomb before applying a new event in the scheduler.
            if action=='E':self.stacks['bomb']=0;self.expiry['bomb']=time+4
            elif action in ('AA','W','R') and 'bomb' in self.stacks:
                self.add('bomb',cap=4)
                if self.stacks['bomb']==4:
                    result.append(('explosive_charge',4));self.stacks.pop('bomb');self.expiry.pop('bomb',None);self.ready['W']=time
            if action=='Q':self.buff('rapid_fire_as',(.6,.8,1,1.2)[ranks['Q']-1],7)
        elif c=='Ezreal':
            if action in ('Q','E','R'):self.add('rising_spell_force',cap=4,duration=8)
            if action=='W':self.stacks['flux']=1;self.expiry['flux']=time+4
            elif action in ('AA','Q','E','R') and self.stacks.pop('flux',0):
                self.expiry.pop('flux',None);result.append(('essence_flux',1))
            if action=='Q':
                for s in 'QWER':self.reduce(s,seconds=1.5)
        elif c=='Lucian':
            if action!='AA':self.stacks['lightslinger']=1;self.expiry['lightslinger']=time+3.5
            elif self.stacks.pop('lightslinger',0):
                result.append(('lightslinger',1));self.expiry.pop('lightslinger',None);self.reduce('E',seconds=4)
        elif c=='Varus':
            if action=='AA':self.add('blight',cap=3,duration=6)
            elif action in ('Q','E','R'):
                count=self.stacks.pop('blight',0);self.expiry.pop('blight',None)
                if count:
                    result.append(('blight',count))
                    for s in 'QWE':self.reduce(s,fraction=.13*count)
                if action=='R':result.append(('schedule_blight_application',3))
        elif c=='Ashe':
            if action=='AA':self.add('focus',cap=4,duration=4)
            if action=='Q':
                if self.stacks.get('focus',0)<4:raise ValueError('Ashe Q requires four Focus stacks')
                self.stacks['focus']=0;self.expiry.pop('focus',None);self.buff('focus_as',(.2,.3,.4,.5)[ranks['Q']-1],6)
        elif c=='Draven':
            if action=='Q':self.add('axes',cap=2,duration=6)
            if action=='AA' and self.stacks.get('axes',0):result.append(('spinning_axe',1));result.append(('axe_catch_required',1))
            if action=='W':self.buff('blood_rush_as',(.25,.30,.35,.40)[ranks['W']-1],3)
        elif c=='Xayah':
            if action!='AA' and cast:self.add('feather_attacks',3,cap=5)
            if action=='AA' and self.stacks.get('feather_attacks',0):self.stacks['feather_attacks']-=1;result.append(('place_feather',1))
            if action=='W':self.buff('plumage_as',(.4,.45,.5,.55)[ranks['W']-1],4)
        elif c=='Miss Fortune':
            if action=='AA':
                self.add('love_tap',cap=3)
                if self.stacks['love_tap']==3:result.append(('love_tap',1));self.reduce('W',seconds=2)
            if action=='W':self.buff('strut_as',(.45,.60,.75,.90)[ranks['W']-1],4)
        elif c=="Kai'Sa":
            if action=='AA':self.add('plasma',cap=5)
            if action=='W':result.append(('plasma_application_requires_evolve_state',1))
            if self.stacks.get('plasma',0)==5:result.append(('plasma_detonation',5));self.stacks['plasma']=0
            if action=='AA':self.reduce('E',seconds=.5)
        elif c=='Senna':
            if action=='AA':self.reduce('Q',seconds=1)
            # Mist/soul collection is not inferred from damaging a stationary target.
        elif c=='Zeri':
            if action=='E':self.stacks['spark_attacks']=3;self.expiry['spark_attacks']=time+6
            if action=='AA' and self.stacks.get('spark_attacks',0):self.stacks['spark_attacks']-=1;result.append(('spark_surge',1))
            if action!='E':self.reduce('E',seconds=.5)
        elif c=='Jhin' and action=='AA':
            if self.ammo==0:raise ValueError('Jhin must reload; reload duration unresolved')
            if self.ammo==1:result.append(('fourth_shot',1))
            self.ammo-=1
            if self.ammo==0:result.append(('reload_required',1))
        elif c=='Corki' and action=='R':
            if self.ammo==0:raise ValueError('Corki R has no ammo; recharge must be scheduled')
            self.ammo-=1;self.add('missile_sequence')
            if self.stacks['missile_sequence']%3==0:result.append(('big_one',1))
        elif c=="Kog'Maw" and action=='W':self.buff('barrage_rank',ranks['W'],8)
        elif c=='Sivir' and action=='W':self.buff('ricochet_as',(.25,.30,.35,.40)[ranks['W']-1],4)
        self.last_action=action
        return result

    def axe_catch(self,time):
        if self.champion!='Draven':raise ValueError('Only Draven catches axes')
        self.advance(time);self.expiry['axes']=time+6;self.ready['W']=time


def zeri_attack_speed_conversion(base_ad,excess_as_percent):
    """User locked: bonus AS beyond the 1.5 cap converts at 0.5 AD/point.

    Caller supplies excess bonus AS percentage points after determining the cap;
    this helper does not infer a base-AS ratio or apply ultimate exceptions.
    """
    if not all(math.isfinite(v) for v in (base_ad,excess_as_percent)) or min(base_ad,excess_as_percent)<0:raise ValueError('Invalid conversion stats')
    return base_ad+.5*excess_as_percent
