"""Translate cached WR spell-effect labels; never import PC or WR damage numbers."""
import json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from sharpwr.damage_classification import TAGS,PROPERTIES

def build():
    sources=json.loads((ROOT/'data/wr-damage-classification-sources.json').read_text())
    lookup={(r['champion'],r['slot']):r for r in sources['records']}
    cat=json.loads((ROOT/'data/marksman-ability-catalogue.json').read_text())
    result={'schema_version':1,'taxonomy_source':'https://wiki.leagueoflegends.com/en-us/Damage','taxonomy_warning':'PC article explicitly warns of confusing/outdated material. WR template labels translated into taxonomy; no PC coefficients or implicit properties imported.','retrieved_at':'2026-10-01','tags':sorted(TAGS),'properties':sorted(PROPERTIES),'policy':'Every field has a semantic role. Unknown is distinct from untagged/default damage. Each physical/magic/true component is a separate damage instance; shared cast id prevents duplicate cast triggers.','abilities':{},'items':{},'runes':{},'stat_fields':{}}
    mapping={'basic':['BasicAttack'],'attack':['BasicAttack'],'spell':['ActiveSpell'],'single':['ActiveSpell'],'single target':['ActiveSpell'],'aoe':['ActiveSpell','AOE'],'area':['ActiveSpell','AOE'],'area of effect':['ActiveSpell','AOE'],'spellaoe':['ActiveSpell','AOE'],'aoedot':['ActiveSpell','AOE','Periodic'],'periodic':['ActiveSpell','Periodic'],'proc':['Proc'],'default':[]}
    for c,row in cat['champions'].items():
        result['abilities'][c]={}
        for s,a in row['abilities'].items():
            src=lookup.get((c,s));p=src.get('parameters',{}) if src else {};label=p.get('spelleffects','').lower().strip();tags=mapping.get(label,[])
            status='WR_wiki_classification' if label in mapping else 'unknown_WR'
            props={key:None for key in sorted(PROPERTIES)}
            if p.get('onhiteffects','').lower()=='true':props['TriggerOnHitEvents']=True
            if p.get('callforhelp','').lower()=='true':props['EnableCallForHelp']=True
            has_damage=bool(p.get('damagetype','').strip() and p.get('damagetype','').lower()!='none') or (c,s) in [('Senna','P'),('Yunara','P'),('Yunara','Q')]
            if label in ('none','') and p.get('damagetype','').lower() in ('none','') and not has_damage:status='no_direct_damage' if src else 'unknown_WR'
            v={'tags':list(tags),'status':status,'resistance_type_text':p.get('damagetype'),'properties':props,'source':src['url'] if src else None,'source_label':label or None,'variants':{},'field_roles':{k:('resource' if k.startswith('mana') else 'timing' if any(t in k for t in ('cooldown','cast_time','speed','duration')) else 'geometry' if 'range' in k or 'radius' in k else 'evidence' if k in ('observations','source_keys','wr_wiki_metadata','timing_source') else 'metadata') for k in a if k!='damage_classification'}}
            def variant(key,t,st='WR_wiki_classification',**kw):
                v['variants'][key]={'tags':t,'status':st,'source':v['source'],'properties':{},**kw}
            if (c,s) in [('Ezreal','Q'),('Miss Fortune','Q')]:
                v.update(tags=['BasicAttack'],status='WR_wiki_classification');v['properties']['TriggerOnHitEvents']=True
                variant('spell_effect_event',['ActiveSpell'],raw_damage=0,reason='WR notes explicitly separate zero spell damage from positive basic damage')
            if (c,s)==('Smolder','Q'):
                v.update(tags=['ActiveSpell','BasicAttack'],status='WR_wiki_classification');v['properties']['TriggerOnHitEvents']=True
                variant('explosion',['ActiveSpell','AOE']);variant('burn',[],damage_type='true',classification='default_damage');variant('execute',[],classification='default_damage',ignores_shields=True)
            if (c,s)==('Samira','Q'):
                v.update(tags=['ActiveSpell'],status='WR_wiki_classification');variant('shot',['ActiveSpell']);variant('slash',['ActiveSpell','AOE']);variant('dash_explosives',['ActiveSpell','AOE'])
            if (c,s)==('Samira','P'):
                v.update(tags=[],status='WR_wiki_classification');v['classification']='default_damage';variant('melee_bonus',[],classification='default_damage');variant('flurry_first',['BasicAttack']);variant('flurry_remaining',[],classification='default_damage')
            if (c,s)==("Kai'Sa",'Q'):
                v.update(tags=['ActiveSpell','AOE'],status='WR_wiki_classification');variant('first',['ActiveSpell','AOE']);variant('subsequent',['ActiveSpell','AOE','Periodic'])
            if (c,s)==('Ashe','Q'):
                v.update(tags=[],status='mixed_WR_components');variant('first',['BasicAttack']);variant('subsequent',[],'unknown_WR',reason='WR notes ambiguous between default and proc; never assign BasicAttack to whole flurry')
            if (c,s)==('Zeri','W'):
                v.update(tags=['ActiveSpell'],status='WR_wiki_classification');variant('pulse',['ActiveSpell']);variant('wall_laser',['ActiveSpell','AOE'])
            if (c,s)==('Zeri','R'):
                v.update(tags=['ActiveSpell','AOE'],status='WR_wiki_classification');variant('nova',['ActiveSpell','AOE']);variant('bounce',['Proc'])
            if (c,s)==('Ezreal','W'):variant('mark_application',['Proc'],raw_damage=0)
            if c=='Yunara':v['status']='unknown_WR';v['source']=None
            if label=='default':v['classification']='default_damage'
            result['abilities'][c][s]=v;a['damage_classification']=v
    audit=json.loads((ROOT/'data/item-trigger-audit.json').read_text())
    item_sources={x['item']:x for x in json.loads((ROOT/'data/wr-item-classification-sources.json').read_text())['records']}
    for r in audit['records']:
        category=r.get('trigger_category');item=r['item']
        result['items'][item]={'origin_tags':['Item'],'damage_tags':[],'status':'unknown_WR','trigger_category':category,'user_locked':r.get('status') in ('user_locked_in_game_measurement','user_confirmed_scope'),'reason':'Item origin is known; basic/proc source classification requires WR evidence, not inference from on-hit activation.'}
        source=item_sources.get(item,{});text=' '.join(source.get('descriptions',[]))
        result['items'][item].update(source=source.get('source'),source_status=source.get('status'),field_roles={'stats':'stat','trigger_category':'trigger','finding':'evidence'})
        if source.get('on_hit_explicit'):result['items'][item]['damage_tags']=['Item','OnHit']
        if category=='active':result['items'][item]['damage_tags']=['Item','ActiveSpell']
        r['damage_classification']=result['items'][item]
    from sharpwr.rune_database import RUNE_DATABASE
    for name,rune in RUNE_DATABASE.items():
        data=rune.get('data',{});kind=rune.get('kind','')
        direct=any('damage' in k and not ('amp' in k or 'reduction' in k) for k in data) or name in ('Brutal','Lethal Tempo')
        result['runes'][name]={'role':'additional_damage' if direct else 'damage_modifier' if any(x in kind for x in ('amp','damage_reduction')) else 'stat_or_state_modifier','tags':[],'status':'unknown_WR' if direct else 'not_a_damage_instance','field_roles':{k:('damage_formula' if 'damage' in k else 'timing' if 'cooldown' in k or 'duration' in k else 'parameter') for k in data}}
    stats=json.loads((ROOT/'data/marksman_champion_stats.json').read_text())
    for f in stats['champions'][0]['stats']:
        result['stat_fields'][f]={'role':'resource' if 'mana' in f else 'geometry' if 'range' in f or 'radius' in f else 'timing' if any(x in f for x in ('windup','cast_time','total_time','delay','projectile')) else 'defense' if any(x in f for x in ('armor','mr','hp')) else 'stat','tags':[],'status':'not_a_damage_instance'}
    for row in stats['champions']:row['stat_classification']={f:result['stat_fields'][f] for f in row['stats']}
    for path,d in [('data/damage-classification.json',result),('data/marksman-ability-catalogue.json',cat),('data/item-trigger-audit.json',audit),('data/marksman_champion_stats.json',stats)]:
        (ROOT/path).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
    print('Abilities:',sum(map(len,result['abilities'].values())),'items:',len(result['items']),'stats:',len(result['stat_fields']))
if __name__=='__main__':build()
