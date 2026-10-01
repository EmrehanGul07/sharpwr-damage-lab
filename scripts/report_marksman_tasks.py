"""Refresh honest completion states and per-champion offline/in-game blockers."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from marksman_damage_components import LINEAR
q=json.loads((ROOT/'data/marksman-implementation-queue.json').read_text())
c=json.loads((ROOT/'data/marksman-ability-catalogue.json').read_text())['champions']
rows=['# Marksman implementation queue — 2026-10-01','',
'All 23 champions are connected to Skill Lab. All adapters are provisional: integration completion does not imply verified Wild Rift parity.', '',
'Each champion has an executable event timeline, automatic ranks, item callbacks, resource handling and movement. Unknown timings and source conflicts remain explicit in runtime assumptions and the in-game TODO.','',
'| Order | Champion | Catalogue | Fight engine | Missing mana slots |',
'|---|---|---|---|---|']
for task in q['champions']:
    name=task['champion'];record=c[name]
    missing=[s for s in 'QWER' if record['abilities'][s]['mana_by_rank'] is None]
    task['missing_mana']=missing
    task['missing_cooldown']=[s for s in 'QWER' if record['abilities'][s]['cooldown_by_rank'] is None]
    task['damage_components_prepared']=name in LINEAR or name in ('Samira','Smolder')
    task['state']='integrated_provisional' if record['fight_engine_supported'] else 'catalogued_engine_pending'
    task['subtasks']={'catalogue':'completed','metadata_research':'completed_available_sources','damage_components':'implemented_known_values','kit_timeline_adapter':'provisional' if record['fight_engine_supported'] else 'pending','movement_optimizer':'provisional' if record['fight_engine_supported'] else 'pending','end_to_end_validation':'automated_level_1_and_15_build_matrix'}
    rows.append(f"| {task['order']} | {name} | 5 slots | {'Provisional' if record['fight_engine_supported'] else 'Pending'} | {', '.join(missing) or '—'} |")
rows+=['','## Remaining work by champion','']
for task in q['champions']:
    name=task['champion'];record=c[name]
    rows += [f"### {task['order']}. {name}",'',f"- [x] P/Q/W/E/R observations and provenance catalogued.",f"- [x] Available WR template metadata researched; user damage/CD values preserved.",f"- [{'x' if record['fight_engine_supported'] else ' '}] Timeline adapter, item/rune interaction, kit movement and rotation search.",f"- [ ] WR parity checks for unresolved details."]
    note=task['remaining']
    if name=='Samira':note='See docs/ingame-test-todo.md T01–T16. Mana and S Style are user-confirmed; they are not missing.'
    if name=='Smolder':note='See docs/ingame-test-todo.md T17–T23. Mana is user-confirmed; it is not missing.'
    if name=='Yunara':note='User mana Q30/W60/E40/R100 and empowered W160/320/480 are recorded. Base HP/mana/MS/core stats remain manual pending. Burn/linger/crit interaction timing needs WR validation.'
    rows += [f"Remaining mechanics: {note}",f"Unresolved mana: {', '.join(task['missing_mana']) or 'none'}.",'']
rows += ['## Important source limits','',
'Blank cost fields were not interpreted as zero. Explicit `none` was interpreted as zero with its source retained.',
'Kog’Maw R template has five ranks and a 40–400 conditional cost; the user WR record has three ranks and a different mana ramp. This conflict is retained and not applied.',
'PC base windup is authorized for Samira only. No PC timing fallback was added for other champions.',
'See docs/all-marksman-fight-engine.md for executable mechanics, conservative exclusions and outstanding parity checks.','']
(ROOT/'docs/marksman-task-queue.md').write_text('\n'.join(rows))
(ROOT/'data/marksman-implementation-queue.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n')
print('Task report refreshed: 23 champions; 23 provisional fight adapters; 0 pending integration')
