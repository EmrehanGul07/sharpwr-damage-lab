"""Compact CPython references for offline mobile/WASM parity, regenerated intentionally."""
import json
import gzip
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'mobile'))
from engine_bridge import mobile_fight
from sharpwr.catalog import C
cases = []
for champion in C:
    for level, runes, items, health in [(1, False, [], 100000),
                                      (9, True, ['Statikk Shiv', "Guinsoo's Rageblade"], 3000),
                                      (15, True, ['Muramana', 'Trinity Force', 'Infinity Edge'], 6000)]:
        request = {'build': {'champion': champion, 'level': level, 'items': items, 'boots': 'Immortal Treads',
                             'mist': 40 if champion == 'Senna' else 0, 'yuntalStacks': 125, 'runes': runes},
                   'target': {'health': health, 'armor': 100, 'magicResist': 80, 'bonusHealth': 1000,
                              'attackReduction': .1}}
        result = json.loads(mobile_fight(request))
        replay = result['replay']
        cases.append({'request': request, 'summary': result['summary'],
                      'events': [{'time': e['time'], 'action': e['action'], 'phase': e['phase'],
                                  **{key: e[key] for key in ['damage', 'hp_after', 'mana_after', 'cost'] if key in e}}
                                 for e in replay['events']],
                      'motionCount': len(replay['motion'])})
(ROOT / 'app-data/golden/fights.json.gz').write_bytes(gzip.compress(json.dumps(cases, separators=(',', ':')).encode(), mtime=0))
print(f'Exported {len(cases)} mobile fights')
# Explicit controls must survive the winning-policy replay rerun.
for champion in ['Ezreal', 'Samira', 'Jinx', "Kai'Sa"]:
    for movement in ['skill_envelope', 'aa_envelope', 'close_envelope']:
        request = {'build': {'champion': champion, 'level': 15, 'items': ['Statikk Shiv', "Guinsoo's Rageblade"], 'boots': 'Immortal Treads', 'runes': True},
                   'target': {'health': 5000, 'armor': 100, 'magicResist': 80},
                   'settings': {'rotation': 'EWQ', 'movement': movement, 'ultimate': 'after_basics', 'distance': 850}}
        result = json.loads(mobile_fight(request)); replay = result['replay']
        assert result['summary']['Rotation'] == 'E → W → Q'
        assert result['summary']['Movement'] == movement
        assert result['summary']['Ultimate timing'] == 'after_basics'
        assert replay['motion'][0]['distance'] == 850
        cases.append({'request': request, 'summary': result['summary'],
                      'events': [{'time': e['time'], 'action': e['action'], 'phase': e['phase'],
                                  **{key: e[key] for key in ['damage', 'hp_after', 'mana_after', 'cost'] if key in e}}
                                 for e in replay['events']], 'motionCount': len(replay['motion'])})
(ROOT / 'app-data/golden/fights.json.gz').write_bytes(gzip.compress(json.dumps(cases, separators=(',', ':')).encode(), mtime=0))
print(f'Exported {len(cases)} fights including manual controls')
