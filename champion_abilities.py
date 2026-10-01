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
    'Q': {'name':'Flair','base':(15.,20.,25.,30.),'total_ad':1.25,'cooldown':(6.5,5.,3.5,2.),'hits':1,'crit_effectiveness':.5,'mana':None,'source':'D001–D002; user practice Q 76/114 and 123/203'},
    'R': {'name':'Inferno Trigger','base':(20.,40.,60.),'total_ad':.5,'cooldown':(6.,6.,6.),'hits':10,'crit_effectiveness':1.,'mana':None,'source':'D007–D008; user tooltip and R 69/158 crit ratio'},
}

def resistance_multiplier(value):
    return 100/(100+value) if value>=0 else 2-100/(100-value)

def effective_resistance(value,pct=0.,flat=0.):
    # Penetration never creates negative resistance; negative resistance can come from reductions.
    return value if value<0 else max(0.,value*(1-min(1.,max(0.,pct)))-max(0.,flat))

def samira_skill(slot,rank,ad,crit_chance,crit_damage,armor,*,pct_pen=0.,flat_pen=0.,outcome='Expected',hits=None):
    if slot not in SAMIRA_ABILITIES: raise ValueError('Only Samira Q and R have executable formulas.')
    data=SAMIRA_ABILITIES[slot]
    if not isinstance(rank,int) or not 0<=rank<=len(data['base']): raise ValueError('Invalid ability rank.')
    if not all(math.isfinite(x) for x in (ad,crit_chance,crit_damage,armor,pct_pen,flat_pen)): raise ValueError('Stats must be finite.')
    if ad<0 or not 0<=crit_chance<=1 or crit_damage<1: raise ValueError('Invalid combat stats.')
    if outcome not in ('Normal','Critical','Expected'): raise ValueError('Invalid outcome.')
    if outcome=='Critical' and crit_chance==0: raise ValueError('A critical outcome requires nonzero critical chance.')
    count=data['hits'] if hits is None else hits
    if not isinstance(count,int) or not 1<=count<=data['hits']: raise ValueError('Invalid hit count.')
    normal=(data['base'][rank-1]+data['total_ad']*ad) if rank else 0.
    crit_bonus=data['crit_effectiveness']*(crit_damage-1.)
    probability={'Normal':0.,'Critical':1.,'Expected':crit_chance}[outcome]
    raw=normal*(1+probability*crit_bonus)
    physical=raw*count
    dealt=physical*resistance_multiplier(effective_resistance(armor,pct_pen,flat_pen))
    return SkillDamage(slot,rank,outcome,count,raw,physical,0.,0.,dealt,0.,0.)
