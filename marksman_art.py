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
    return '\n'.join((ROOT/'assets/marksman-3d'/name).read_text() for name in ('rig.js','effects.js','scene.js'))
def studio_html():
    root=ROOT/'assets/marksman-3d'
    catalogue=json.loads(json.dumps(art_catalogue()))
    abilities=json.loads((ROOT/'data/marksman-ability-catalogue.json').read_text())['champions']
    icons=json.loads((ROOT/'data/marksman-skill-icons.json').read_text())['champions']
    for name,profile in catalogue['champions'].items():
        profile['hud']={'icons':icons[name]['icons'],'icon_source':icons[name]['source'],'abilities':{slot:{'name':entry['name'],'cooldowns':entry.get('cooldown_by_rank')} for slot,entry in abilities[name]['abilities'].items()}}
    html=(root/'studio.html').read_text()
    study=root/'studies/ezreal-v2/ezreal-v2.glb'
    study_data={'ezreal':base64.b64encode(study.read_bytes()).decode('ascii')} if study.is_file() else {}
    replacements={'__BAKED_SCRIPT__':(root/'baked-avatar.js').read_text(),'__STUDY_DATA__':_safe_json(study_data),'__ART_DATA__':_safe_json(catalogue),'__HUD_SCRIPT__':(root/'combat-hud.js').read_text(),'__RIG_SCRIPT__':(root/'rig.js').read_text(),'__FX_SCRIPT__':(root/'effects.js').read_text(),'__SCENE_SCRIPT__':(root/'scene.js').read_text(),'__FIGHT_SCRIPT__':(root/'fight.js').read_text()}
    for key,value in replacements.items():html=html.replace(key,value)
    return html

