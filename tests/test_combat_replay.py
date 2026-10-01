import unittest,json
from test_combat_engine import engine_namespace
from build_fight_optimizer import BuildFightEvaluator
from combat_replay import replay_payload,replay_html
class CombatReplay(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ns=engine_namespace()
 def test_selected_winner_matches_damage_ttk_and_records_movement(self):
  for c in ('Samira','Smolder','Jinx','Ezreal','Xayah'):
   with self.subTest(c=c):
    ev=BuildFightEvaluator(self.ns,c,15,2000,100,100);row=ev.evaluate(['Muramana','Phantom Dancer']);r=ev.replay_row(row)
    self.assertEqual(r.killed_at,row['TTK']);self.assertEqual(r.total_damage,row['Damage']);self.assertTrue(r.motion)
    p=replay_payload(r,champion=c,level=15,target='Test',hp=2000,build=row)
    self.assertEqual(p['events'],sorted(p['events'],key=lambda v:(v['time'],v['order'])))
    self.assertEqual(len({e['order'] for e in p['events']}),len(p['events']))
    self.assertEqual([e['event_id'] for e in p['events']],list(range(1,len(p['events'])+1)))
    self.assertFalse(ev.retain_traces)
 def test_entrypoint_recovers_stale_optimizer_class(self):
  import ast,types
  from pathlib import Path
  import build_fight_optimizer as module
  source=Path('streamlit_app.py').read_text();tree=ast.parse(source)
  guard=next(n for n in tree.body if isinstance(n,ast.If) and '_build_optimizer' in ast.unparse(n.test))
  original=module.BuildFightEvaluator
  module.BuildFightEvaluator=type('StaleEvaluator',(),{})
  try:
   scope={'_build_optimizer':module}
   exec(compile(ast.Module(body=[guard],type_ignores=[]),'<reload guard>','exec'),scope)
   self.assertTrue(callable(module.BuildFightEvaluator.replay_row))
   ev=module.BuildFightEvaluator(self.ns,'Samira',15,2000,100,100)
   row=ev.evaluate([]);self.assertEqual(ev.replay_row(row).total_damage,row['Damage'])
  finally:module.BuildFightEvaluator=original
 def test_html_escapes_data_and_keeps_real_damage(self):
  ev=BuildFightEvaluator(self.ns,'Samira',15,2000,100,100);row=ev.evaluate([]);r=ev.replay_row(row)
  p=replay_payload(r,champion='Samira',level=15,target='</script><script>alert(1)</script>',hp=2000,build=row)
  h=replay_html(p);self.assertNotIn('__REPLAY_DATA__',h);self.assertNotIn(p['target'],h);self.assertIn('\\u003c/script',h)
  self.assertEqual(p['damage'],row['Damage'])
if __name__=='__main__':unittest.main()
