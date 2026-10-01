"""Fill absent mana and WR timing metadata; preserve all user combat values."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import json,re
from pathlib import Path
from urllib.parse import quote
import requests
import lxml.html
ROOT=Path(__file__).resolve().parents[1]

def numbers(value,n):
    value=re.sub(r'(?<=\d)\.\s+(?=\d)', '.', value.strip().replace('−','-'))
    if not re.fullmatch(r'\d+(?:\.\d+)?(?:\s*/\s*\d+(?:\.\d+)?)*',value):return None
    v=[float(x) for x in value.split('/')]
    return v*n if len(v)==1 else v if len(v)==n else None

def fetch(task):
    champion,slot,name=task
    overrides={('Jinx','P'):'Get Excited!',('Zeri','Q'):'Electrocute!',('Jinx','Q'):'Switcheroo!',('Jinx','W'):'Zap!',('Jinx','E'):'Flame Chompers!',('Jinx','R'):'Super Mega Death Rocket!',('Smolder','E'):'Flap, Flap, Flap',('Smolder','R'):'MMOOOMMMM!'}
    name=overrides.get((champion,slot),name)
    name=re.sub(r'\s+(?:ek\s+)?[FMT](?:/\w+)?$','',name).replace('’',"'")
    if champion=='Varus' and slot=='W':name='Blighted Quiver'
    if champion=="Kai'Sa" and slot=='R':name='Killer Instinct'
    url='https://wiki.leagueoflegends.com/en-us/Template:WR_Data_'+quote(champion.replace(' ','_'))+'/'+quote(name.replace(' ','_'))
    result={'champion':champion,'slot':slot,'url':url,'retrieved_at':datetime.now(timezone.utc).isoformat()}
    try:
        response=requests.get(url,timeout=30,headers={'User-Agent':'SharpWR-ability-research/1.0'})
        response.raise_for_status();doc=lxml.html.fromstring(response.content)
        params={}
        for table in doc.xpath('//table'):
            rows=[]
            for tr in table.xpath('.//tr'):
                cells=[' '.join(' '.join(c.itertext()).split()) for c in tr.xpath('./th|./td')]
                if len(cells)>1:rows.append(cells)
            if any(r[0] in ('cost','cast time','cooldown') for r in rows):
                params={r[0]:r[1] for r in rows};break
        if not params:raise ValueError('No ability parameter table')
        keys=('cost','costtype','cooldown','cast time','range','target range','effect radius','speed','width','duration','queue threshold')
        result['parameters']={k:v for k,v in params.items() if k in keys}
        result['status']='retrieved'
    except Exception as exc:result.update(status='unavailable',error=str(exc))
    return result

def main():
    p=ROOT/'data/marksman-ability-catalogue.json';catalogue=json.loads(p.read_text())
    tasks=[(c,s,a['name']) for c,r in catalogue['champions'].items() if c!='Yunara' for s,a in r['abilities'].items() if a['name']]
    cached_path=ROOT/'data/marksman-wr-ability-metadata.json'
    cached={(r['champion'],r['slot']):r for r in json.loads(cached_path.read_text())['records']} if cached_path.exists() else {}
    missing=[t for t in tasks if cached.get(t[:2],{}).get('status')!='retrieved']
    with ThreadPoolExecutor(max_workers=6) as pool:new=list(pool.map(fetch,missing))
    cached.update({(r['champion'],r['slot']):r for r in new})
    records=[cached[t[:2]] for t in tasks]
    for record in records:
        if record['status']!='retrieved':continue
        a=catalogue['champions'][record['champion']]['abilities'][record['slot']];params=record['parameters'];n=3 if record['slot']=='R' else 4
        a['wr_wiki_metadata']=record
        costs=numbers(params.get('cost',''),n)
        if params.get('cost','').lower()=='none':costs=[0.]*n
        if record['slot']!='P' and a['mana_by_rank'] is None and costs is not None and ('mana' in params.get('costtype','').lower() or params.get('cost','').lower()=='none'):
            a['mana_by_rank']=costs;a['mana_evidence']={'kind':'WR_wiki_parameter','url':record['url'],'retrieved_at':record['retrieved_at']}
        # Store conditional or formula timing text separately. Never flatten it.
        for field,key in [('cast_time_seconds','cast time'),('projectile_speed','speed'),('range','range')]:
            v=numbers(params.get(key,''),1)
            if v is not None:a[field]=v[0]
            elif key=='cast time' and params.get(key,'').lower()=='none':a[field]=0.
        for field,key in [('target_range_by_rank','target range'),('effect_radius_by_rank','effect radius'),('duration_by_rank','duration')]:
            a[field]=numbers(params.get(key,''),n)
        if record['slot']!='P' and a['cooldown_by_rank'] is None:
            cd=numbers(params.get('cooldown',''),n)
            if cd is not None:a['cooldown_by_rank']=cd;a['cooldown_source']=record['url']
        a['timing_source']=record['url']
    p.write_text(json.dumps(catalogue,ensure_ascii=False,indent=2)+'\n')
    (ROOT/'data/marksman-wr-ability-metadata.json').write_text(json.dumps({'policy':'WR metadata only; user values retained; unparsed conditional fields stay text','records':records},ensure_ascii=False,indent=2)+'\n')
    print('WR templates retrieved:',sum(r['status']=='retrieved' for r in records),'/',len(records))
if __name__=='__main__':main()
