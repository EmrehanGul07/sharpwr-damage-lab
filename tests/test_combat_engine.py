"""Regression tests load pure engine definitions without executing Streamlit UI."""
import ast
import math
from pathlib import Path
import unittest

APP=Path(__file__).resolve().parents[1]/'streamlit_app.py'
FUNCTIONS={'stats','gu','dct','rm','lvl_scale','_combat_hits','_validate_build','_effective_resistance','sim','sim_build'}
DATA={'C','F','B','P','K'}
def engine_namespace():
    ns={}
    for node in ast.parse(APP.read_text()).body:
        if isinstance(node,ast.FunctionDef) and node.name in FUNCTIONS or isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id in DATA for t in node.targets):
            exec(compile(ast.Module(body=[node],type_ignores=[]),str(APP),'exec'),ns)
    return ns

class CombatTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.n=engine_namespace()
    def run_build(self,items,**kw):
        return self.n['sim_build']('Yunara',15,10000,100,100,items,self.n['F'],**kw)
    def test_single_multi_parity(self):
        for name in self.n['F']:
            for proc in [False,True]:
                with self.subTest(item=name,proc=proc):
                    a,al=self.n['sim']('Yunara',15,10000,100,100,name,self.n['F'],0,0,550,0,True,True,True,0,proc)
                    b,bl=self.run_build([name],spell=True,energized=True,ult=True,item_proc=proc)
                    self.assertEqual(a,b);self.assertEqual(al,[x[:9] for x in bl])
    def test_nashor_full_ap(self):
        args=('Yunara',1,10000,0,0)
        _,a=self.n['sim_build'](*args,["Nashor's Tooth"],self.n['F'])
        _,b=self.n['sim_build'](*args,["Nashor's Tooth",'Statikk Shiv'],self.n['F'])
        self.assertAlmostEqual(b[0][6]-a[0][6],48,places=1)
    def test_magic_pen_boot(self):
        _,a=self.run_build(["Wit's End"])
        _,b=self.run_build(["Wit's End"],boot="Spellslinger's Shoes")
        self.assertGreater(b[0][6],a[0][6])
    def test_fiendhunter_trigger_and_expiry(self):
        _,plain=self.run_build(['Fiendhunter Bolts'])
        _,ult=self.run_build(['Fiendhunter Bolts'],ult=True)
        self.assertGreater(ult[0][6],plain[0][6])
        self.assertTrue(all('Opening Barrage' in x[8] for x in ult[:3]))
        self.assertNotIn('Opening Barrage',ult[3][8])
    def test_validation(self):
        for items in [list(self.n['F'])[:6],['Infinity Edge']*2,['missing'],['Boots of Speed']]:
            with self.subTest(items=items),self.assertRaises(ValueError):self.run_build(items)
        with self.assertRaises(ValueError):self.run_build([],boot='missing')
    def test_timeout(self):
        row,log=self.n['sim_build']('Yunara',1,1e9,100,100,[],{})
        self.assertTrue(math.isinf(row[2]));self.assertIn('NOT KILLED',row[0]);self.assertGreater(log[-1][7],0)
    def test_resistance(self):
        self.assertEqual(self.n['rm'](100),.5)
        self.assertGreater(self.n['rm'](-100),1)
        self.assertEqual(self.n['_effective_resistance'](100,.3,1000),0)
        self.assertEqual(self.n['_effective_resistance'](-20,.3,10),-20)
    def test_smoke(self):
        for champion in self.n['C']:
            for item in self.n['F']:
                for level in [1,8,15]:
                    row,log=self.n['sim_build'](champion,level,10000,100,100,[item],self.n['F'])
                    self.assertTrue(all(math.isfinite(x[6]) and x[6]>=0 for x in log))

if __name__=='__main__': unittest.main()
