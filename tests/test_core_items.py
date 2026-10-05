import unittest
from sharpwr.core_items import EXCLUDED,available,rank_core
from sharpwr.build_fight_optimizer import BuildFightEvaluator,search_builds,legal
from sharpwr import engine_namespace
class CoreItems(unittest.TestCase):
 def test_five_exclusions_and_muramana_unlock(self):
  self.assertEqual(EXCLUDED,{'Infinity Edge',"Lord Dominik's Regards","Serylda's Grudge",'Mortal Reminder','Terminus'})
  self.assertFalse(available('Muramana',9));self.assertTrue(available('Muramana',11))
  self.assertFalse(available('Terminus',15))
 def test_late_item_is_scored_only_when_eligible(self):
  cells={str(l):{'level':l,'search':{'full':[{'Items':['Muramana' if l>=11 else 'Essence Reaver']}]}} for l in (5,7,9,11,13,15)}
  r=rank_core(cells,['Muramana','Essence Reaver','Terminus'])
  self.assertEqual(r[0]['Item'],'Muramana');self.assertEqual(r[0]['Score'],100);self.assertEqual(r[0]['Eligible cells'],3)
  self.assertEqual(r[1]['Score'],50);self.assertFalse(any(x['Item']=='Terminus' for x in r))
 def test_top_three_have_equal_cell_weights_not_raw_simulation_weights(self):
  cells={'a':{'level':15,'search':{'full':[{'Items':['Muramana']},{'Items':['Essence Reaver']},{'Items':['Essence Reaver']}]}},'b':{'level':15,'search':{'full':[{'Items':['Muramana']}]}}}
  r=rank_core(cells,['Muramana','Essence Reaver'])
  self.assertEqual(r[0]['Item'],'Muramana');self.assertAlmostEqual(r[0]['Score'],100*(1+1/(1+.5+1/3))/2,places=5)
 def test_real_search_honors_one_item_budget_and_compares_boots(self):
  ns=engine_namespace();ev=BuildFightEvaluator(ns,'Ezreal',5,1500,40,30)
  result=search_builds(ev,['Trinity Force','Essence Reaver','Kraken Slayer'],['Armorcrusher Boots','Gunmetal Greaves'],beam_width=8,refine_count=3,max_items=1)
  self.assertEqual(result['max_items'],1);self.assertEqual(result['stages'],{})
  self.assertTrue(all(len(r['Items'])==1 and legal(r['Items']) for r in result['full']))
  self.assertEqual(result['boot_count'],2)
 def test_fingerprint_selection_ignores_ui_and_tracks_model(self):
  from sharpwr.core_items import _selected_digest
  base='F={"test":1}\ndef stats():return 1\ndef ui():return "old"\n'
  names={'F','stats'}
  self.assertEqual(_selected_digest(base,names),_selected_digest(base.replace('"old"','"new"'),names))
  self.assertNotEqual(_selected_digest(base,names),_selected_digest(base.replace('return 1','return 2'),names))

 def test_fingerprint_is_independent_of_ast_dump_schema(self):
  from unittest.mock import patch
  from sharpwr.core_items import _selected_digest
  source='F={"test":1}\ndef stats():return 1\n'
  expected=_selected_digest(source,{'F','stats'})
  with patch('ast.dump',side_effect=AssertionError('Runtime-specific AST serialization must not be hashed')):
   self.assertEqual(_selected_digest(source,{'F','stats'}),expected)
 def test_saved_results_match_current_fingerprint(self):
  from sharpwr.core_items import core_record
  ns=engine_namespace()
  for name in ns['C']:
   with self.subTest(champion=name):
    record=core_record(name)
    self.assertIsNotNone(record)
    self.assertTrue(record['complete'])
    self.assertEqual(len(record['cells']),18)
