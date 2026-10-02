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
 def test_ezreal_w_visual_arrival_is_mark_application_not_detonation(self):
  ev=BuildFightEvaluator(self.ns,'Ezreal',15,6000,100,100)
  row=ev.evaluate(['Muramana','Trinity Force'],'Armorcrusher Boots',refine=True)
  trace=ev.replay_row(row)
  payload=replay_payload(trace,champion='Ezreal',level=15,target='Training target',hp=6000,build=row)
  casts=[c for c in trace.timeline if c['kind']=='cast' and c['action']=='W']
  flights=[f for f in payload['visual_flights'] if f['action']=='W']
  self.assertTrue(casts);self.assertEqual(len(casts),len(flights))
  for c,f in zip(casts,flights):
   self.assertEqual(f['launch'],c['cast_end']);self.assertEqual(f['impact'],c['impact_time'])
  detonations=[e['time'] for e in trace.log if e['action']=='W detonation']
  self.assertTrue(detonations);self.assertLess(flights[0]['impact'],detonations[0])
  self.assertEqual(payload['damage'],row['Damage']);self.assertEqual(payload['ttk'],row['TTK'])
 def test_runtime_recovers_stale_dependency_graph(self):
  import build_fight_optimizer as optimizer
  import marksman_damage_components as components
  import engine_runtime
  from unittest.mock import patch
  del components.jhin_attack_damage
  optimizer.BuildFightEvaluator=type('StaleEvaluator',(),{})
  engine_runtime.ensure_engine_revision('stale-dependency-test')
  self.assertTrue(callable(components.jhin_attack_damage))
  self.assertTrue(callable(optimizer.BuildFightEvaluator.replay_row))
  ev=optimizer.BuildFightEvaluator(self.ns,'Jhin',15,2000,100,100)
  row=ev.evaluate([]);self.assertEqual(ev.replay_row(row).total_damage,row['Damage'])
  with patch('engine_runtime.importlib.reload') as reload:
   engine_runtime.ensure_engine_revision('stale-dependency-test')
   reload.assert_not_called()
 def test_displayed_starting_crit_includes_yuntal_and_caps(self):
  for stacks,items,expected in ((0,['Yun Tal Wildarrows'],0),(50,['Yun Tal Wildarrows'],10),(125,['Yun Tal Wildarrows'],25),(125,['Yun Tal Wildarrows','Infinity Edge'],50),(125,['Infinity Edge'],25),(125,['Yun Tal Wildarrows','Infinity Edge','The Collector','Phantom Dancer','Navori Quickblades'],100)):
   ev=BuildFightEvaluator(self.ns,'Samira',15,2000,100,100,yuntal_stacks=stacks)
   row=ev.evaluate(items);self.assertAlmostEqual(row['Crit %'],expected)
   trace=ev.replay_row(row);self.assertGreaterEqual(trace.log[0]['crit_chance']*100,row['Crit %'])
 def test_html_escapes_data_and_keeps_real_damage(self):
  ev=BuildFightEvaluator(self.ns,'Samira',15,2000,100,100);row=ev.evaluate([]);r=ev.replay_row(row)
  p=replay_payload(r,champion='Samira',level=15,target='</script><script>alert(1)</script>',hp=2000,build=row)
  h=replay_html(p);self.assertNotIn('__REPLAY_DATA__',h);self.assertNotIn(p['target'],h);self.assertIn('\\u003c/script',h)
  self.assertEqual(p['damage'],row['Damage'])
if __name__=='__main__':unittest.main()
