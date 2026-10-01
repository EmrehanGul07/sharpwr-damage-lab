"""Isolated, source-backed skill estimates; no ability timeline or proc simulation."""
from dataclasses import dataclass
import math

@dataclass(frozen=True)
class SkillDamage:
    slot: str
    rank: int
    outcome: str
    hits: int
    physical_per_hit: float
    physical: float
    magic: float
    true: float
    dealt_physical: float
    dealt_magic: float
    dealt_true: float

    @property
    def total(self): return self.dealt_physical+self.dealt_magic+self.dealt_true

SAMIRA_ABILITIES={
    'Q': {'name':'Flair','base':(15.,20.,25.,30.),'total_ad':1.25,'cooldown':(6.5,5.,3.5,2.),'hits':1,'crit_effectiveness':.5,'mana':30,'mana_source':'User Wild Rift confirmation, 2026-10-01; constant across ranks','source':'D001–D002; user practice Q 76/114 and 123/203'},
    'W': {'name':'Blade Whirl','base':(20.,40.,60.,80.),'bonus_ad':.5,'cooldown':(22.,20.,18.,16.),'hits':2,'crit_effectiveness':0.,'mana':60,'mana_source':'User Wild Rift confirmation, 2026-10-01; constant across ranks','source':'D003–D004'},
    'E': {'name':'Wild Rush','base':(45.,60.,75.,90.),'bonus_ad':.2,'cooldown':(20.,17.,14.,11.),'hits':1,'crit_effectiveness':0.,'mana':40,'mana_source':'User Wild Rift confirmation, 2026-10-01; constant across ranks','source':'D005–D006'},
    'R': {'name':'Inferno Trigger','base':(20.,40.,60.),'total_ad':.5,'cooldown':(6.,6.,6.),'hits':10,'crit_effectiveness':1.,'mana':0,'required_resource':{'type':'Style','grade':'S','stacks':6},'mana_source':'User Wild Rift confirmation, 2026-10-01: no mana; S Style required','source':'D007–D008; user tooltip and R 69/158 crit ratio'},
}

def resistance_multiplier(value):
    return 100/(100+value) if value>=0 else 2-100/(100-value)

def effective_resistance(value,pct=0.,flat=0.):
    # Penetration never creates negative resistance; negative resistance can come from reductions.
    return value if value<0 else max(0.,value*(1-min(1.,max(0.,pct)))-max(0.,flat))

def samira_skill(slot,rank,ad,crit_chance,crit_damage,armor,*,pct_pen=0.,flat_pen=0.,outcome='Expected',hits=None,base_ad=None,mr=0.,pct_mpen=0.,flat_mpen=0.):
    if slot not in SAMIRA_ABILITIES: raise ValueError('Unknown Samira ability.')
    data=SAMIRA_ABILITIES[slot]
    if not isinstance(rank,int) or not 0<=rank<=len(data['base']): raise ValueError('Invalid ability rank.')
    if not all(math.isfinite(x) for x in (ad,crit_chance,crit_damage,armor,pct_pen,flat_pen,mr,pct_mpen,flat_mpen)): raise ValueError('Stats must be finite.')
    if ad<0 or not 0<=crit_chance<=1 or crit_damage<1: raise ValueError('Invalid combat stats.')
    if outcome not in ('Normal','Critical','Expected'): raise ValueError('Invalid outcome.')
    if outcome=='Critical' and crit_chance==0: raise ValueError('A critical outcome requires nonzero critical chance.')
    count=data['hits'] if hits is None else hits
    if not isinstance(count,int) or not 1<=count<=data['hits']: raise ValueError('Invalid hit count.')
    normal=(data['base'][rank-1]+data.get('total_ad',0.)*ad+data.get('bonus_ad',0.)*max(0.,ad-(ad if base_ad is None else base_ad))) if rank else 0.
    crit_bonus=data['crit_effectiveness']*(crit_damage-1.)
    probability={'Normal':0.,'Critical':1.,'Expected':crit_chance}[outcome]
    raw=normal*(1+probability*crit_bonus)
    physical=raw*count if slot!='E' else 0.
    magic=raw*count if slot=='E' else 0.
    dealt=physical*resistance_multiplier(effective_resistance(armor,pct_pen,flat_pen))
    dealt_magic=magic*resistance_multiplier(effective_resistance(mr,pct_mpen,flat_mpen))
    return SkillDamage(slot,rank,outcome,count,raw if slot!='E' else 0.,physical,magic,0.,dealt,dealt_magic,0.)

SMOLDER_ABILITIES={
 'Q':{'name':'Super Scorcher Breath','cooldown':(5.5,5.,4.5,4.),'mana':30},
 'W':{'name':'Achooo!','cooldown':(12.,11.,10.,9.),'mana':(50,55,60,65)},
 'E':{'name':'Flap Flap Flap','cooldown':(18.,16.,14.,12.),'mana':65},
 'R':{'name':'MOOOMMM!','cooldown':(80.,70.,60.),'mana':100},
}

def smolder_skill(slot,rank,ad,base_ad,ap,stacks,crit_chance,crit_damage):
    """User WR data. Count/timing candidates explicitly remain provisional."""
    bonus=max(0.,ad-base_ad)
    if slot=='Q':
        # User tests support this candidate; official 7.1e wording is additive.
        amp=1+.45*(crit_chance+max(0.,crit_damage-2.))
        return ((45,80,115,150)[rank-1]+1.1*bonus)*amp,.3*stacks*amp
    if slot=='W':return (65,85,105,125)[rank-1]+.6*bonus+(10,35,60,85)[rank-1]+.55*bonus+.8*ap,.55*stacks
    if slot=='E':return (15,20,25,30)[rank-1]+.3*ad,.12*stacks
    if slot=='R':return (300,450,600)[rank-1]+1.65*bonus+1.5*ap,0.
    raise ValueError('Unknown Smolder skill.')
