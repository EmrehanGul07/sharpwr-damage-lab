import math
import unittest
from test_combat_engine import engine_namespace

class UserItemCadence(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.ns=engine_namespace()
 def hits(self,item,physical,count):
  k=self.ns['_combat_hits']('Smolder',15,10000,100,100,[item],self.ns['F']);next(k);hp=10000;out=[]
  for i in range(count):
   hit=k.send({'hp':hp,'time':i,'event_driven':True,'attack_physical':physical,'critical_attack_physical':physical*2})
   hit['rune_damage']=hit['damage']*1.065;hp-=hit['rune_damage'];out.append(hit)
  return out
 def test_rageblade_phantom_on_six_and_nine_from_zero(self):
  hits=self.hits("Guinsoo's Rageblade",138,10)
  self.assertEqual([i for i,h in enumerate(hits,1) if 'Phantom Hit' in h['notes']],[6,9])
  self.assertEqual([math.ceil(h['magic']*.5*1.065) for h in hits],[16,16,16,16,16,32,16,16,32,16])
  self.assertEqual([h['rage'] for h in hits],[1,2,3,4,4,4,4,4,4,4])
 def test_kraken_three_six_nine_and_damage_matches_user(self):
  hits=self.hits('Kraken Slayer',148,9)
  self.assertEqual([i for i,h in enumerate(hits,1) if 'Kraken' in h['notes']],[3,6,9])
  self.assertEqual([math.ceil(h['rune_damage']) for h in hits],[79,79,170,79,79,172,79,79,174])
