"""Fetch WR template evidence; fill missing simple geometry, never overwrite combat values."""
import sys,json,re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.import_wr_ability_metadata import numbers

def run():
 p=ROOT/'data/marksman-ability-catalogue.json';cat=json.loads(p.read_text());jobs=[]
 for c,row in cat['champions'].items():
  for s,a in row['abilities'].items():
   url=a.get('wr_wiki_metadata',{}).get('url')
   if s!='P' and url:jobs.append((c,s,url))
 def fetch(job):
  c,s,url=job
  try:
   r=requests.get(url+'?action=raw',timeout=20);r.raise_for_status()
   params={k.strip():v.strip() for k,v in re.findall(r'^\|([^=\n]+)=([^\n]*)',r.text,re.M)}
   return dict(champion=c,slot=s,url=url,retrieved_at='2026-10-01',status='retrieved',parameters={k:params.get(k,'') for k in ('range','target range','effect radius','cast time','speed','duration','projectile','damagetype','cost','costtype','spelleffects','onhiteffects')})
  except Exception as e:return dict(champion=c,slot=s,url=url,status='unavailable',error=str(e))
 with ThreadPoolExecutor(max_workers=8) as pool:records=list(pool.map(fetch,jobs))
 updates=[];conflicts=[]
 for row in records:
  if row['status']!='retrieved':continue
  c,s=row['champion'],row['slot'];a=cat['champions'][c]['abilities'][s];n=3 if s=='R' else 4;pms=row['parameters'];a['offline_source_evidence']=row
  a.get('damage_classification',{}).setdefault('field_roles',{})['offline_source_evidence']='evidence'
  candidate=numbers(pms.get('cost',''),n)
  if candidate and a.get('mana_by_rank') and candidate!=a['mana_by_rank']:conflicts.append(dict(champion=c,slot=s,field='mana_by_rank',preserved=a['mana_by_rank'],source_candidate=candidate,url=row['url']))
  for field,key in [('range','range'),('target_range_by_rank','target range'),('effect_radius_by_rank','effect radius'),('duration_by_rank','duration')]:
   vals=numbers(pms.get(key,''),1 if field=='range' else n)
   if a.get(field) is None and vals is not None:
    a[field]=vals[0] if field=='range' else vals;a[field+'_source']=row['url'];updates.append(dict(champion=c,slot=s,field=field,value=a[field]))
 (ROOT/'data/offline-source-research-v565.json').write_text(json.dumps({'policy':'Raw WR template evidence; only missing simple geometry/duration fields filled. Damage, rank, mana, cooldown and user references preserved. Conflicts remain evidence.','records':records,'updates':updates,'conflicts_preserved':conflicts},ensure_ascii=False,indent=2)+'\n')
 p.write_text(json.dumps(cat,ensure_ascii=False,indent=2)+'\n')
 regpath=ROOT/'data/damage-classification.json';reg=json.loads(regpath.read_text())
 for row in records:
  if row['status']=='retrieved':reg['abilities'][row['champion']][row['slot']]['field_roles']['offline_source_evidence']='evidence'
 regpath.write_text(json.dumps(reg,ensure_ascii=False,indent=2)+'\n')
 print('retrieved',sum(r['status']=='retrieved' for r in records),'/',len(records),'updates',len(updates),flush=True)
if __name__=='__main__':run()
