"""Explicitly authorized PC timing references; never imports PC damage or WR combat stats."""
import json,re,time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
ROOT=Path(__file__).resolve().parents[1]
BASE='https://wiki.leagueoflegends.com/en-us/'
def fetch(url):
 for attempt in range(3):
  try:
   r=requests.get(url+'?action=raw',timeout=35);r.raise_for_status();return r.text
  except requests.RequestException:
   if attempt==2:raise
 return ''
def params(raw):return dict(re.findall(r'^\|([^=\n]+)=([^\n]*)',raw,re.M))
def scalar(s):
 s=s.strip()
 if re.fullmatch(r'\d+(?:\.\d+)?',s):return float(s)
 m=re.fullmatch(r'\{\{(?:fd|tt)\|(\d+(?:\.\d+)?)(?:\|[^{}]*)?\}\}',s)
 return float(m[1]) if m else None

def main():
 statpath=ROOT/'data/marksman_champion_stats.json';catpath=ROOT/'data/marksman-ability-catalogue.json'
 stats=json.loads(statpath.read_text());cat=json.loads(catpath.read_text());raw=fetch(BASE+'Module:ChampionData/data')
 out={'policy':'PC reference authorized by user; WR damage, ranks, resources, AS stats preserved. Base AA windup follows Samira policy; current windup = base / (1 + 0.5 * WR bonus AS), except preserved WR Senna rule. Compound speeds retained, never guessed.','source':BASE+'Module:ChampionData/data','champions':{}}
 jobs=[]
 for c in stats['champions']:
  n=c['name'];m=re.search(r'\["'+re.escape(n)+r'"\] = \{(.*?)(?=\n  \["|\Z)',raw,re.S)
  if not m:raise ValueError(n)
  p=dict(re.findall(r'\["([^"]+)"\]\s*=\s*([^,\n]+)',m[1]))
  val=lambda k:float(p[k]) if k in p else None
  cast,total,offset=val('attack_cast_time'),val('attack_total_time'),val('attack_delay_offset')
  fraction=cast/total if cast is not None and total else .3+offset if offset is not None else None
  aa={'pc_base_as':val('as_base'),'windup_fraction':fraction,'base_windup_seconds':fraction/val('as_base') if fraction is not None else None,'projectile_speed':val('missile_speed'),'windup_modifier':val('windup_modifier') or 1.,'source':out['source'],'variants':{}}
  for key,field in [('attack_cast_time','attack_cast_time'),('attack_total_time','attack_total_time'),('attack_delay_offset','attack_delay_offset'),('missile_speed','attack_projectile_speed')]:
   if val(key) is not None and c['stats'].get(field) is None:c['stats'][field]=val(key);c['field_sources'][field]={'url':out['source'],'parameter':key,'game':'PC LoL proxy; user authorized'}
  c['stats']['attack_windup']=fraction;c['stats']['base_attack_windup_seconds']=aa['base_windup_seconds'];c['stats']['windup_modifier']=aa['windup_modifier']
  for field in ('attack_windup','base_attack_windup_seconds','windup_modifier'):c['field_sources'][field]={'url':out['source'],'game':'PC LoL proxy; user authorized'}
  c['unavailable_fields']=[k for k in c['unavailable_fields'] if c['stats'].get(k) is None]
  out['champions'][n]={'aa':aa,'abilities':{}}
  for slot in 'PQWER':
   key='skill_i' if slot=='P' else 'skill_'+slot.lower()
   skill=re.search(r'\["'+key+r'"\]\s*=\s*\{[^\n]*?\[1\]\s*=\s*"([^"]+)"',m[1])
   names=[skill[1]] if skill else []
   if names:jobs.append((n,slot,BASE+'Template:Data_'+n.replace(' ','_')+'/'+names[0].replace(' ','_')))
 def get(job):
  n,slot,url=job
  try:
   p={k.strip():v.strip() for k,v in params(fetch(url)).items()}
   return n,slot,{'source':url,'cast_time_expression':p.get('cast time',''),'speed_expression':p.get('speed',''),'projectile_expression':p.get('projectile',''),'range_expression':p.get('range',''),'status':'retrieved','cast_time_seconds':0. if p.get('cast time','').lower()=='none' else scalar(p.get('cast time','')),'speed_scalar':scalar(p.get('speed',''))}
  except Exception as e:return n,slot,{'source':url,'status':'unavailable','error':str(e)}
 with ThreadPoolExecutor(max_workers=8) as pool:
  for n,slot,a in pool.map(get,jobs):
   out['champions'][n]['abilities'][slot]=a
   d=cat['champions'][n]['abilities'][slot];d['pc_timing_reference']=a
   if d['cast_time_seconds'] is None and a.get('cast_time_seconds') is not None:d['cast_time_seconds']=a['cast_time_seconds'];d['cast_time_source']=a['source']
   if d['projectile_speed'] is None and a.get('speed_scalar') is not None and a.get('projectile_expression') not in ('false','none'):
    # Known dash slots must never become missile travel.
    if not (slot=='E' and n in ('Samira','Lucian','Zeri')) and not (slot=='W' and n in ('Tristana','Corki')):
     d['projectile_speed']=a['speed_scalar'];d['projectile_speed_source']=a['source']
   print(n,slot,a.get('speed_expression'),a.get('cast_time_expression'),flush=True)
 for n,c in out['champions'].items():
  for slot,a in c['abilities'].items():
   expr=a.get('speed_expression','');a['speed_variants']=[{'speed':float(v),'label':lab} for v,lab in re.findall(r'\{\{tt\|(\d+(?:\.\d+)?)\|([^{}]+)\}\}',expr)]
   flag=a.get('projectile_expression','').lower()
   a['speed_status']='sourced_scalar' if a.get('speed_scalar') is not None else 'sourced_expression' if expr else 'non_projectile' if flag=='false' else 'not_applicable' if not flag else 'not_in_source'
   if not (n=="Kai'Sa" and slot=='R') and a['speed_variants'] and not any(w in a['speed_variants'][0]['label'].lower() for w in ('dash','knockback')):
    d=cat['champions'][n]['abilities'][slot]
    if d['projectile_speed'] is None:d['projectile_speed']=a['speed_variants'][0]['speed'];d['projectile_speed_source']=a['source']
   cat['champions'][n]['abilities'][slot]['pc_timing_reference']=a
 out['champions']['Twitch']['aa']['variants']['ultimate']=5000
 out['champions']['Jinx']['aa']['status']='missile_speed_not_in_wiki; variants unresolved'
 (ROOT/'data/pc-combat-timing.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
 stats['policy']+=' PC AA timing fields are explicitly authorized proxies; WR combat values remain unchanged.'
 statpath.write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n');catpath.write_text(json.dumps(cat,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
