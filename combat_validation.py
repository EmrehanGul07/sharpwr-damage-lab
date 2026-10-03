"""Reject invalid inputs before a combat loop or optimizer can mutate state."""
import math

def finite(value, label, minimum=None, maximum=None):
    if isinstance(value,bool) or not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError(f'{label} must be finite')
    if minimum is not None and value<minimum or maximum is not None and value>maximum:
        raise ValueError(f'Invalid {label}')
    return value

def integer(value, label, minimum, maximum=None):
    finite(value,label,minimum,maximum)
    if not isinstance(value,int):raise ValueError(f'{label} must be an integer')
    return value

def benchmark(champion, level, hp, armor, mr, *, mist=0, bonus_hp=0,
              distance=0, reduction=0, mana=0, stacks=0, executes=0):
    from champion_database import CHAMPION_DATABASE
    if champion not in CHAMPION_DATABASE:raise ValueError('Unknown champion')
    integer(level,'level',1,15);finite(hp,'target HP',0)
    if hp==0:raise ValueError('Target HP must be positive')
    for label,value in (('armor',armor),('MR',mr)):finite(value,label)
    for label,value in (('bonus HP',bonus_hp),('distance',distance),('mana',mana)):finite(value,label,0)
    finite(reduction,'AA reduction',0,1)
    for label,value in (('mist',mist),('stacks',stacks),('executes',executes)):integer(value,label,0)
