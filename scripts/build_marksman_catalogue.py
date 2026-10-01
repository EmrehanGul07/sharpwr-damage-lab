"""Rebuild the catalogue from preserved observations without inferring mechanics."""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from champion_abilities import SAMIRA_ABILITIES,SMOLDER_ABILITIES
source=json.loads((ROOT/'data/marksman-ability-evidence.json').read_text())
queue=json.loads((ROOT/'data/marksman-implementation-queue.json').read_text())
known={'Samira':SAMIRA_ABILITIES,'Smolder':SMOLDER_ABILITIES}
# Later user confirmations have precedence over earlier screenshot summaries.
confirmed={'Yunara':{'Q':[30]*4,'W':[60]*4,'E':[40]*4,'R':[100]*3}}
existing_path=ROOT/'data/marksman-ability-catalogue.json'
existing=json.loads(existing_path.read_text()).get('champions',{}) if existing_path.exists() else {}
records={}
for record in source['champions']:
    name=record['champion'];slots={}
    for slot in ('P','Q','W','E','R'):
        observations=record.get('ability_observations',{}).get(slot,[])
        text=' '.join(observations)
        match=re.search(r'\*\*'+slot+r'\s*[—–-]\s*(.*?):\*\*',text)
        ability_name=match.group(1).strip() if match else None
        if name=='Smolder' and slot=='P':ability_name='Dragon Practice'
        n=3 if slot=='R' else 4
        costs=record.get('mana_by_rank',{}).get(slot)
        provenance=record.get('mana_evidence',{}).get(slot)
        if name in confirmed and slot in confirmed[name]:
            costs=confirmed[name][slot];provenance={'kind':'user_confirmation','source':'visible conversation: every rank constant'}
        cd=None
        # Extract only explicitly labelled CD arrays. Charge/refresh is not cast CD.
        m=re.search(r'(?<!\w)CD\s+(\d+(?:\.\d+)?(?:/\d+(?:\.\d+)?)*)',text)
        if m:
            values=[float(x) for x in m.group(1).split('/')]
            if len(values)==n:cd=values
            elif len(values)==1:cd=values*n
        if name in known and slot!='P':
            d=known[name][slot];ability_name=d['name'];v=d['mana']
            costs=list(v) if isinstance(v,tuple) else [v]*n
            cd=list(d['cooldown']);provenance={'kind':'implemented_user_WR_reference','source':d.get('mana_source','user practice confirmation')}
        if costs is not None and len(costs)==1:costs=costs*n
        slots[slot]={'name':ability_name,'observations':observations,'source_keys':record.get('source_keys',[]),'mana_by_rank':costs,'mana_evidence':provenance,'cooldown_by_rank':cd,'cast_time_seconds':None,'projectile_speed':None,'range':None,'timing_source':None}
        prior=existing.get(name,{}).get('abilities',{}).get(slot,{})
        for field in ('wr_wiki_metadata','cast_time_seconds','projectile_speed','range','timing_source','target_range_by_rank','effect_radius_by_rank','duration_by_rank','cooldown_source'):
            if field in prior:slots[slot][field]=prior[field]
        if costs is None and (prior.get('mana_evidence') or {}).get('kind')=='WR_wiki_parameter':
            slots[slot]['mana_by_rank']=prior['mana_by_rank'];slots[slot]['mana_evidence']=prior['mana_evidence']
        if cd is None and prior.get('cooldown_source'):
            slots[slot]['cooldown_by_rank']=prior['cooldown_by_rank']
    records[name]={'abilities':slots,'fight_engine_supported':True,'remaining':record.get('unresolved_note'),'source_type':record.get('source_type')}
out={'schema_version':1,'unknown_policy':'null means unresolved, never assumed zero','champions':records}
(ROOT/'data/marksman-ability-catalogue.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
for task in queue['champions']:
    record=records[task['champion']]
    task['catalogue_complete']=True
    task['engine_connected']=record['fight_engine_supported']
    task['missing_mana']=[s for s in ('Q','W','E','R') if record['abilities'][s]['mana_by_rank'] is None]
    task['missing_cooldown']=[s for s in ('Q','W','E','R') if record['abilities'][s]['cooldown_by_rank'] is None]
    task['state']='integrated_provisional' if record['fight_engine_supported'] else 'catalogued_engine_pending'
(ROOT/'data/marksman-implementation-queue.json').write_text(json.dumps(queue,ensure_ascii=False,indent=2)+'\n')
print(f'Catalogue: {len(records)} champions, {sum(len(x["abilities"]) for x in records.values())} ability records')
