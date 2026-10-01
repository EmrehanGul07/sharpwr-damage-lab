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
