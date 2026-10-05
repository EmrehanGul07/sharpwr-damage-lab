"""Regression tests for the UI-independent AA engine in the sharpwr package."""
import math
import unittest
from sharpwr import engine_namespace

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
        _,legacy=self.run_build(['Fiendhunter Bolts'],ult=True)
        self.assertEqual(plain,legacy)
        kernel=self.n['combat_hits']('Yunara',15,10000,100,100,['Fiendhunter Bolts'],self.n['F'])
        next(kernel)
        hits=[kernel.send({'time':t,'hp':10000,'event_driven':True,'ultimate_cast_time':0}) for t in (0,1,2,3)]
        self.assertTrue(all('Opening Barrage' in x['notes'] for x in hits[:3]))
        self.assertNotIn('Opening Barrage',hits[3]['notes'])
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
        self.assertEqual(self.n['effective_resistance'](100,.3,1000),0)
        self.assertEqual(self.n['effective_resistance'](-20,.3,10),-20)
    def test_smoke(self):
        for champion in self.n['C']:
            for item in self.n['F']:
                for level in [1,8,15]:
                    row,log=self.n['sim_build'](champion,level,10000,100,100,[item],self.n['F'])
                    self.assertTrue(all(math.isfinite(x[6]) and x[6]>=0 for x in log))

if __name__=='__main__': unittest.main()
