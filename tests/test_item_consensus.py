import unittest
from item_consensus import consensus,adopters
class ItemConsensus(unittest.TestCase):
 def test_equal_targets_and_no_boots(self):
  searches={'tank':{'full':[{'Items':['A'],'Boots':'Boot'}]},'squishy':{'full':[{'Items':['B']},{'Items':['A']},{'Items':['A']}]}}
  rows=consensus(searches)
  self.assertEqual(rows[0]['Item'],'A');self.assertEqual(rows[0]['Target coverage'],2)
  self.assertEqual(rows[0]['Targets tested'],2);self.assertNotIn('Boot',[x['Item'] for x in rows])
 def test_distinct_champions_not_build_count(self):
  runs={'tank':{'full':[{'Items':['A']},{'Items':['A']},{'Items':['A']}]}}
  row=adopters({'Samira':runs,'Ezreal':runs})[0]
  self.assertEqual(row['Champions'],2);self.assertEqual(row['Target appearances'],2)
 def test_empty(self):self.assertEqual(consensus({}),[]);self.assertEqual(adopters({}),[])

class ChampionItemList(unittest.TestCase):
 def test_top_ten_includes_partial_build_candidates(self):
  from item_consensus import champion_items
  search={'full':[{'Items':['A','B','C','D','E']}],'stages':{1:[{'Items':['F']},{'Items':['G']},{'Items':['H']},{'Items':['I']},{'Items':['J']},{'Items':['K']}]}}
  rows=champion_items(search)
  self.assertEqual(len(rows),10);self.assertEqual(rows[0]['Item'],'A');self.assertTrue(all(r['Note'] for r in rows))

 def test_saved_screen_covers_all_items_champions_and_targets(self):
  import json
  from pathlib import Path
  p=json.loads(Path('data/item-adoption-screen.json').read_text())
  self.assertEqual(len(p['results']),23);self.assertEqual(len(p['ranking']),36)
  for profiles in p['results'].values():
   self.assertEqual(set(profiles),{'tank','bruiser','squishy'})
   self.assertTrue(all(len(rows)==36 for rows in profiles.values()))
  self.assertEqual(p['ranking'],sorted(p['ranking'],key=lambda x:(-x['Champions'],-x['Top-5 target appearances'],-x['Mean DPS gain %'],x['Item'])))
