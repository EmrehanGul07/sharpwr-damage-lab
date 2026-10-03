"""Read-only presentation of a ranked engine trace; never calculates damage."""
import json
from bisect import bisect_right
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
    # Animation windows are presentation metadata from the captured trace.
    # Some adapters record lock ends only in motion, not in cast commands.
    samples=list(unique.values()); sample_times=[x['time'] for x in samples]
    animation_windows=[]
    for command in result.timeline:
        if command['kind'] not in ('attack','cast'):continue
        index=bisect_right(sample_times,command['time']+1e-8)-1
        sample=samples[index] if index>=0 else {}
        end=command.get('windup_end',command.get('cast_end',max(command['time'],sample.get('cast_until',command['time']))))
        channel_end=sample.get('channel_until',command['time'])
        if channel_end<=command.get('channel_before',command['time'])+1e-8:channel_end=command['time']
        animation_windows.append(dict(time=command['time'],order=command.get('order',0),end=end,channel_end=max(command['time'],channel_end)))
    visual_flights=[]
    for command in result.timeline:
        action=command['action']
        if command['kind']=='attack':
            visual_flights.append(dict(action='AA',time=command['time'],order=command.get('order',0),launch=command['windup_end'],impact=command['impact_time']))
        elif command['kind']=='cast' and action in ('Q','W','E','R'):
            launch=command.get('cast_end',command['time'])
            hits=[e for e in result.log if e['action'].startswith(action) and e.get('order',0)>command.get('order',-1) and e['time']>=command['time']]
            impact=command.get('impact_time',hits[0]['time'] if hits else launch)
            if impact>launch+1e-7:
                visual_flights.append(dict(action=action,time=command['time'],order=command.get('order',0),launch=launch,impact=impact))
    return dict(animation_windows=animation_windows,visual_flights=visual_flights,skill_flights=flights,schema=2,champion=champion,level=level,target=target,max_hp=hp,duration=duration,build=list(build['Items'])+[build['Boots']],policy={k:build[k] for k in ('Rotation','Movement','Ultimate timing','Attack weaving','Weapon','E enabled')},events=events,attacks=result.timeline,motion=list(unique.values()),assumptions=result.assumptions,damage=result.total_damage,ttk=result.killed_at,notice='Recorded engine events. Lateral position is a representative projection of recorded distance/kite arc; effects and unit sizes are illustrative. This is not validated Wild Rift footage.')

def replay_html(payload):
    from marksman_art import art_catalogue, art_scripts, _safe_json
    root=Path(__file__).resolve().parent
    profiles=art_catalogue()['champions']
    art='window.MarksmanArtProfiles='+_safe_json({payload['champion']:profiles[payload['champion']]} if payload['champion'] in profiles else {})+';\n'+art_scripts()+'\n'+(root/'assets/marksman-3d/replay.js').read_text()
    data=json.dumps(payload,ensure_ascii=False,allow_nan=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
    return (Path(__file__).resolve().parent/'assets/combat_replay.html').read_text().replace('__REPLAY_DATA__',data).replace('__REPLAY_STATE_SCRIPT__',(Path(__file__).resolve().parent/'assets/replay_state.js').read_text()).replace('__EZREAL_3D_SCRIPT__',art)
