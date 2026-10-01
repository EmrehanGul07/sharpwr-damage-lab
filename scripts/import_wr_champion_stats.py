"""Import only absent stats from the explicitly requested Wild Rift wiki.

Run from repo root. Existing six combat stats remain authoritative. No PC fallback.
Dependencies for this one-time importer: requests, lxml (not app dependencies).
"""
import ast
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import requests
import lxml.html

ROOT=Path(__file__).resolve().parents[1]
AUDIT=Path(os.environ.get('SHARPWR_WIKI_AUDIT_DIR','/tmp/sharpwr-wiki-stat-audit'))
FIELD_MAP={
    'hp_base':'base_hp','hp_lvl':'hp_growth',
    'hp5_base':'base_hp_regen_per_5s','hp5_lvl':'hp_regen_growth_per_5s',
    'mp_base':'base_mana','mp_lvl':'mana_growth',
    'mp5_base':'base_mana_regen_per_5s','mp5_lvl':'mana_regen_growth_per_5s',
    'arm_base':'base_armor','arm_lvl':'armor_growth',
    'mr_base':'base_mr','mr_lvl':'mr_growth',
    'ms':'movement_speed','range':'attack_range',
    'attack_cast_time':'attack_cast_time','attack_total_time':'attack_total_time',
    'attack_delay_offset':'attack_delay_offset','windup':'attack_windup',
    'windup_modifier':'windup_modifier','missile_speed':'attack_projectile_speed',
    'gameplay_radius':'gameplay_radius',
}
LEGACY_FIELDS=('base_ad','ad_growth','as_ratio','base_as','base_bonus_as','as_growth')
LEGACY={}
for node in ast.parse((ROOT/'streamlit_app.py').read_text()).body:
    if isinstance(node,ast.Assign) and any(isinstance(x,ast.Name) and x.id=='C' for x in node.targets):
        LEGACY=ast.literal_eval(node.value)

def number(value):
    cleaned=value.strip().replace(',','').replace('−','-')
    if re.fullmatch(r'-?\d+(?:\.\d+)?',cleaned):
        v=float(cleaned)
        return int(v) if v.is_integer() else v
    return None

def fetch(name):
    slug=name.replace(' ','_')
    url='https://wiki.leagueoflegends.com/en-us/Template:WR_Data_'+slug
    record={'name':name,'stats':dict(zip(LEGACY_FIELDS,LEGACY[name])),
            'field_sources':{f:'existing_user_preserved' for f in LEGACY_FIELDS},
            'wiki_source_url':url,'wiki_last_change_patch':None,'source_status':None,
            'wiki_combat_values_not_applied':{},'unavailable_fields':[],
            'retrieved_at':datetime.now(timezone.utc).isoformat()}
    for field in FIELD_MAP.values():record['stats'][field]=None
    if name=='Yunara':
        record['source_status']='manual_pending_user_instruction'
        record['unavailable_fields']=list(FIELD_MAP.values())
        return record
    try:
        response=requests.get(url,timeout=40,headers={'User-Agent':'SharpWR-stat-research/1.0'})
        record['http_status']=response.status_code
        if response.status_code!=200:raise ValueError('HTTP '+str(response.status_code))
        doc=lxml.html.fromstring(response.content)
        params={}
        for table in doc.xpath('//table'):
            rows=[]
            for tr in table.xpath('.//tr'):
                cells=[' '.join(' '.join(x.itertext()).split()) for x in tr.xpath('./th|./td')]
                if len(cells)>=2:rows.append(cells)
            if any(row[0]=='hp_base' for row in rows):
                params={row[0]:row[1] for row in rows}
                break
        if not params:raise ValueError('WR parameter table not found')
        # Only explicitly numeric parameter values become executable stats.
        for key,field in FIELD_MAP.items():
            v=number(params.get(key,''))
            record['stats'][field]=v
            if v is not None:record['field_sources'][field]={'url':url,'parameter':key,'retrieved_at':record['retrieved_at']}
        record['resource_type']=params.get('resource')
        record['attack_type']=params.get('rangetype')
        record['wiki_last_change_patch']=params.get('changes')
        for key in ('dam_base','dam_lvl','as_base','as_ratio','as_lvl','crit_base','crit_mod'):
            record['wiki_combat_values_not_applied'][key]=params.get(key,'')
        record['source_status']='wr_wiki_parameter_table'
        # Small auditable numerical transcription, not an article copy.
        audit={'source_url':url,'retrieved_at':record['retrieved_at'],'parameters':{k:params.get(k,'') for k in FIELD_MAP},'last_change_patch':record['wiki_last_change_patch']}
        AUDIT.mkdir(parents=True,exist_ok=True)
        (AUDIT/(slug+'.json')).write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n')
    except Exception as exc:
        record['source_status']='source_unavailable'
        record['source_error']=str(exc)
    record['unavailable_fields']=[f for f in FIELD_MAP.values() if record['stats'][f] is None]
    return record

def main():
    with ThreadPoolExecutor(max_workers=4) as pool:
        records=list(pool.map(fetch,LEGACY))
    out={'schema_version':1,'retrieval_date':datetime.now(timezone.utc).date().isoformat(),
         'policy':'Fill only missing fields. Preserve existing AD/AS values. No PC stat fallback. Wiki values are source references, not independently verified patch-7.3a measurements.',
         'units':{'regen':'per 5 seconds','movement_speed':'game units per second','attack_range':'game units','timing':'as specified by source parameter; blank remains null'},
         'growth_model':'coefficients stored as supplied; no inferred level-growth formula introduced',
         'champions':records}
    (ROOT/'data').mkdir(exist_ok=True)
    (ROOT/'data/marksman_champion_stats.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    for record in records:
        print(record['name'],record['source_status'],len(record['unavailable_fields']),'missing')
if __name__=='__main__':main()
