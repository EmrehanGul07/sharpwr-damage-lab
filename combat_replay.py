"""Read-only presentation of a ranked engine trace; never calculates damage."""
import json
from pathlib import Path

def replay_payload(result,*,champion,level,target,hp,build):
    events=[dict(x,phase='launch' if x.get('kind')=='attack_launch' else 'command') for x in result.timeline]+[dict(x,phase='impact') for x in result.log]
    events.sort(key=lambda x:(x['time'],x.get('order',0)))
    for i,x in enumerate(events):x['event_id']=i+1
    duration=result.killed_at if result.killed_at is not None else 60.
    frames=sorted(result.motion,key=lambda x:x['time'])
    # Later samples at an identical timestamp include the newer lock state.
    unique={x['time']:x for x in frames}
    flights=[]
    for command in result.timeline:
        if command['kind']!='cast' or command['action']!='Q':continue
        hits=[e for e in result.log if e['action'].startswith('Q') and e.get('order',0)>command.get('order',-1) and e['time']>=command['time']]
        if hits and hits[0]['time']>command.get('cast_end',command['time'])+1e-7:flights.append(dict(time=command['time'],launch=command.get('cast_end',command['time']),impact=hits[0]['time'],distance=command['distance']))
    return dict(skill_flights=flights,schema=1,champion=champion,level=level,target=target,max_hp=hp,duration=duration,build=list(build['Items'])+[build['Boots']],policy={k:build[k] for k in ('Rotation','Movement','Ultimate timing','Attack weaving','Weapon','E enabled')},events=events,attacks=result.timeline,motion=list(unique.values()),assumptions=result.assumptions,damage=result.total_damage,ttk=result.killed_at,notice='Recorded engine events. Lateral position is a representative projection of recorded distance/kite arc; effects and unit sizes are illustrative. This is not validated Wild Rift footage.')

def replay_html(payload):
    data=json.dumps(payload,ensure_ascii=False,allow_nan=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    return (Path(__file__).resolve().parent/'assets/combat_replay.html').read_text().replace('__REPLAY_DATA__',data)
