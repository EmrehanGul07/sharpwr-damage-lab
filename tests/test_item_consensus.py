import unittest
from sharpwr.item_consensus import consensus,adopters
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
  from sharpwr.item_consensus import champion_items
  search={'full':[{'Items':['A','B','C','D','E']}],'stages':{1:[{'Items':['F']},{'Items':['G']},{'Items':['H']},{'Items':['I']},{'Items':['J']},{'Items':['K']}]}}
  rows=champion_items(search)
  self.assertEqual(len(rows),10);self.assertEqual(rows[0]['Item'],'A');self.assertTrue(all(r['Note'] for r in rows))

 def test_saved_screen_covers_progression_and_excludes_early_muramana(self):
  import json
  from pathlib import Path
  p=json.loads(Path('data/item-adoption-screen.json').read_text())
  self.assertEqual(len(p['results']),23);self.assertEqual(len(p['ranking']),36)
  budgets={5:1,7:1,9:2,11:3,13:4,15:5}
  for cells in p['results'].values():
   self.assertEqual(len(cells),18)
   for cell in cells.values():
    self.assertEqual(cell['item_count'],budgets[cell['level']])
    for row in cell['builds']:
     self.assertEqual(len(row['Items']),cell['item_count'])
     if cell['level']<11:self.assertNotIn('Muramana',row['Items'])
  self.assertEqual(p['ranking'],sorted(p['ranking'],key=lambda x:(-x['Stage-balanced score'],-x['Champions'],x['Item'])))

class ProgressionWeights(unittest.TestCase):
 def test_five_item_stage_cannot_outweigh_one_item_stage(self):
  from sharpwr.item_consensus import progression_ranking
  data={'Samira':{'5:tank':{'item_count':1,'builds':[{'Items':['A']}]},'15:tank':{'item_count':5,'builds':[{'Items':['A','B','C','D','E']}]}}}
  rows=progression_ranking(data,['A','B','C','D','E'])
  self.assertEqual(rows[0]['Stage-balanced score'],60)
  self.assertEqual(sum(r['Stage-balanced score'] for r in rows),100)
 def test_champion_is_counted_once(self):
  from sharpwr.item_consensus import progression_ranking
  cells={str(i):{'item_count':1,'builds':[{'Items':['A']}]} for i in range(18)}
  row=progression_ranking({'Samira':cells},['A'])[0]
  self.assertEqual(row['Champions'],1);self.assertEqual(row['Level-target appearances'],18)
