"""Original 23-champion art studio; independent of combat and Build Lab controls."""
import json
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
ART_DIRECTION=ROOT/'data/marksman-art-direction.json'
ABILITY_CATALOGUE=ROOT/'data/marksman-ability-catalogue.json'
SKILL_GEOMETRY=ROOT/'data/marksman-skill-geometry.json'
SKILL_ICONS=ROOT/'data/riot/marksman-skill-icons.json'
ABILITY_TEXTS=ROOT/'data/ability-descriptions.json'
# Skinned GLBs live in static/ and are served by Streamlit (server.enableStaticServing).
MODEL_BASE='app/static/marksman-3d/'
# Editable Blender sources and download packages are published by CI as release assets, not tracked in git.
RELEASE_URL='https://github.com/EmrehanGul07/sharpwr-damage-lab/releases/download/art-sources/'
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
    return [STUDIO_ROOT/'studio.html',*scripts,ART_DIRECTION,ABILITY_CATALOGUE,SKILL_GEOMETRY,SKILL_ICONS]

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

def studio_catalogue():
    """Art direction profiles with their HUD data (skill geometry, icons, ability names and cooldowns)."""
    catalogue=json.loads(ART_DIRECTION.read_text())
    abilities=json.loads(ABILITY_CATALOGUE.read_text())['champions']
    geometry=json.loads(SKILL_GEOMETRY.read_text())['champions']
    icons=json.loads(SKILL_ICONS.read_text())['champions']
    for name,profile in catalogue['champions'].items():
        profile['hud']=_hud_profile(name,geometry,icons,abilities)
    return catalogue

def practice_catalogue(icon_files=False):
    """Studio profiles plus the engine's Practice Tool numbers (sharpwr/practice_data.py).

    icon_files: ability icons as bundled file paths (the phone app) instead of data URLs (the web page).
    """
    from sharpwr.practice_data import practice_data
    from sharpwr.app_data import ability_icon_path
    data=practice_data()
    catalogue=studio_catalogue()
    texts=json.loads(ABILITY_TEXTS.read_text())['champions']
    for name,profile in catalogue['champions'].items():
        hud=profile['hud']
        for slot,ability in hud['abilities'].items():
            ability['name']=texts[name][slot]['name']  # the app's ability names, without damage-type markers
        for slot in hud['geometry']['slots'].values():
            slot.pop('raw',None);slot.pop('source',None)
        if icon_files:
            hud['icons']={slot:ability_icon_path(name,slot) for slot in hud['icons']}
        profile['practice']=data['champions'][name]
    catalogue['practice_targets']=data['targets']
    return catalogue

def release_asset_url(name):
    return RELEASE_URL+name

@lru_cache(maxsize=1)
def _render_studio(stamp):
    catalogue=studio_catalogue()
    html=(STUDIO_ROOT/'studio.html').read_text()
    html=html.replace('__STUDY_DATA__',_safe_json({'modelBase':MODEL_BASE}))
    html=html.replace('__ART_DATA__',_safe_json(catalogue))
    for placeholder,name in STUDIO_SCRIPTS:html=html.replace(placeholder,(STUDIO_ROOT/name).read_text())
    return html

def studio_html():
    """Self-contained Animation Studio page, cached until a studio input file changes."""
    return _render_studio(_input_stamp())

# practice-tool.html placeholder -> inlined script file (geometry loads before practice).
PRACTICE_SCRIPTS=(
    ('__BAKED_SCRIPT__','baked-avatar.js'),
    ('__RIG_SCRIPT__','rig.js'),
    ('__FX_SCRIPT__','effects.js'),
    ('__ARENA_SCRIPT__','rift-arena.js'),
    ('__SCENE_SCRIPT__','scene.js'),
    ('__FIGHT_SCRIPT__','fight.js'),
    ('__GEOMETRY_SCRIPT__','geometry.js'),
    ('__PRACTICE_SCRIPT__','practice.js'),
    ('__TOOL_SCRIPT__','practice-tool.js'),
    ('__BOT_SCRIPT__','duel-bot.js'),
    ('__MECHANICS_SCRIPT__','duel-mechanics.js'),
    ('__DUEL_SCRIPT__','duel.js'),
)

def _practice_stamp():
    # The practice numbers come from the engine, so engine and data changes rebuild the page too.
    paths=[*_studio_inputs(),STUDIO_ROOT/'practice-tool.html',STUDIO_ROOT/'practice-tool.css',STUDIO_ROOT/'practice-tool.js',STUDIO_ROOT/'duel-bot.js',STUDIO_ROOT/'duel.js',STUDIO_ROOT/'duel-mechanics.js',
           *sorted((ROOT/'sharpwr').glob('*.py')),*sorted((ROOT/'data').glob('*.json'))]
    return tuple((str(p),p.stat().st_mtime_ns,p.stat().st_size) if p.is_file() else (str(p),None,None) for p in paths)

@lru_cache(maxsize=1)
def _render_practice(stamp):
    html=(STUDIO_ROOT/'practice-tool.html').read_text()
    html=html.replace('__PRACTICE_CSS__',(STUDIO_ROOT/'practice-tool.css').read_text())
    html=html.replace('__STUDY_DATA__',_safe_json({'modelBase':MODEL_BASE}))
    html=html.replace('__PRACTICE_DATA__',_safe_json(practice_catalogue()))
    for placeholder,name in PRACTICE_SCRIPTS:html=html.replace(placeholder,(STUDIO_ROOT/name).read_text())
    return html

def practice_tool_html():
    """Self-contained Practice Tool page, cached until one of its inputs changes."""
    return _render_practice(_practice_stamp())
