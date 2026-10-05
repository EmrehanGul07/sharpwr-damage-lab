"""Original 23-champion art studio; independent of combat and Build Lab controls."""
import json
import base64
from pathlib import Path
from functools import lru_cache
ROOT=Path(__file__).resolve().parent
@lru_cache(maxsize=1)
def art_catalogue():
    return json.loads((ROOT/'data/marksman-art-direction.json').read_text())
def _safe_json(value):
    return json.dumps(value,ensure_ascii=False,allow_nan=False).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026')
def art_scripts():
    return '\n'.join((ROOT/'assets/marksman-3d'/name).read_text() for name in ('baked-avatar.js','geometry.js','rig.js','effects.js','rift-arena.js','scene.js'))
# Studio inputs. The rendered page is rebuilt only when one of these files changes.
STUDIO_ROOT=ROOT/'assets/marksman-3d'
STUDY_ROOT=STUDIO_ROOT/'studies/ezreal-v2'
ART_DIRECTION=ROOT/'data/marksman-art-direction.json'
ABILITY_CATALOGUE=ROOT/'data/marksman-ability-catalogue.json'
SKILL_GEOMETRY=ROOT/'data/marksman-skill-geometry.json'
SKILL_ICONS=ROOT/'data/marksman-skill-icons.json'
PRODUCTION_URL='https://raw.githubusercontent.com/EmrehanGul07/sharpwr-damage-lab/main/assets/marksman-3d/production/'
# studio.html placeholder -> inlined script file.
STUDIO_SCRIPTS=(
    ('__GEOMETRY_SCRIPT__','geometry.js'),
    ('__BAKED_SCRIPT__','baked-avatar.js'),
    ('__HUD_SCRIPT__','combat-hud.js'),
    ('__ARENA_SCRIPT__','rift-arena.js'),
    ('__PRACTICE_SCRIPT__','practice.js'),
    ('__RIG_SCRIPT__','rig.js'),
    ('__FX_SCRIPT__','effects.js'),
    ('__SCENE_SCRIPT__','scene.js'),
    ('__FIGHT_SCRIPT__','fight.js'),
)

def _studio_inputs():
    scripts=[STUDIO_ROOT/name for _,name in STUDIO_SCRIPTS]
    studies=[STUDY_ROOT/'ezreal-v2.glb',STUDY_ROOT/'ezreal-v2-preview.glb']
    return [STUDIO_ROOT/'studio.html',*scripts,ART_DIRECTION,ABILITY_CATALOGUE,SKILL_GEOMETRY,SKILL_ICONS,*studies]

def _input_stamp():
    stamp=[]
    for path in _studio_inputs():
        if path.is_file():
            info=path.stat()
            stamp.append((str(path),info.st_mtime_ns,info.st_size))
        else:
            stamp.append((str(path),None,None))
    return tuple(stamp)

def _hud_profile(name,geometry,icons,abilities):
    return {
        'geometry':geometry[name],
        'icons':icons[name]['icons'],
        'icon_source':icons[name]['source'],
        'abilities':{slot:{'name':entry['name'],'cooldowns':entry.get('cooldown_by_rank')} for slot,entry in abilities[name]['abilities'].items()},
    }

def _study_data(catalogue):
    data={}
    study=STUDY_ROOT/'ezreal-v2.glb'
    if study.is_file():data['ezreal']=base64.b64encode(study.read_bytes()).decode('ascii')
    preview=STUDY_ROOT/'ezreal-v2-preview.glb'
    if preview.is_file():data['ezreal_preview']=base64.b64encode(preview.read_bytes()).decode('ascii')
    data['production']={
        profile['id']:{'full':PRODUCTION_URL+profile['id']+'/character.glb','preview':PRODUCTION_URL+profile['id']+'/preview.glb'}
        for profile in catalogue['champions'].values()
    }
    return data

@lru_cache(maxsize=1)
def _render_studio(stamp):
    catalogue=json.loads(ART_DIRECTION.read_text())
    abilities=json.loads(ABILITY_CATALOGUE.read_text())['champions']
    geometry=json.loads(SKILL_GEOMETRY.read_text())['champions']
    icons=json.loads(SKILL_ICONS.read_text())['champions']
    for name,profile in catalogue['champions'].items():
        profile['hud']=_hud_profile(name,geometry,icons,abilities)
    html=(STUDIO_ROOT/'studio.html').read_text()
    html=html.replace('__STUDY_DATA__',_safe_json(_study_data(catalogue)))
    html=html.replace('__ART_DATA__',_safe_json(catalogue))
    for placeholder,name in STUDIO_SCRIPTS:html=html.replace(placeholder,(STUDIO_ROOT/name).read_text())
    return html

def studio_html():
    """Self-contained Animation Studio page, cached until a studio input file changes."""
    return _render_studio(_input_stamp())
