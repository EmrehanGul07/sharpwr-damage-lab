import unittest
from champion_skill_data import samira_skill

class SamiraTests(unittest.TestCase):
    def test_q_practice_coefficients(self):
        normal=samira_skill('Q',1,109,.5,2.,100,outcome='Normal')
        critical=samira_skill('Q',1,109,.5,2.,100,outcome='Critical')
        self.assertAlmostEqual(normal.total,75.625)
        self.assertAlmostEqual(critical.total/normal.total,1.5)
        normal=samira_skill('Q',1,184,.85,2.3,100,outcome='Normal')
        critical=samira_skill('Q',1,184,.85,2.3,100,outcome='Critical')
        self.assertAlmostEqual(critical.total/normal.total,1.65)
    def test_r_tooltip_and_crit_ratio(self):
        normal=samira_skill('R',1,184,.85,2.3,100,outcome='Normal',hits=1)
        self.assertEqual(normal.physical,112)
        self.assertEqual(normal.total,56)
        critical=samira_skill('R',1,184,.85,2.3,100,outcome='Critical',hits=1)
        self.assertAlmostEqual(critical.total/normal.total,2.3)
    def test_expected_is_probability_weighted(self):
        for slot in ['Q','R']:
            for chance in [0.,.25,.5,.85,1.]:
                base=samira_skill(slot,1,184,chance,2.3,100,outcome='Normal')
                expected=samira_skill(slot,1,184,chance,2.3,100)
                multiplier=1+chance*(2.3-1)*(.5 if slot=='Q' else 1)
                self.assertAlmostEqual(expected.total,base.total*multiplier)
    def test_all_ranks_and_unlearned(self):
        for slot,maxrank in [('Q',4),('R',3)]:
            previous=-1
            for rank in range(maxrank+1):
                hit=samira_skill(slot,rank,100,0,2,0)
                self.assertGreater(hit.total,previous);previous=hit.total
            self.assertEqual(samira_skill(slot,0,100,0,2,0).total,0)
    def test_r_hit_count(self):
        for count in range(1,11):
            hit=samira_skill('R',1,100,0,2,100,hits=count)
            self.assertEqual(hit.total,35*count)
    def test_penetration_not_aa_reduction(self):
        hit=samira_skill('Q',1,100,0,2,100,pct_pen=.3,flat_pen=10)
        self.assertAlmostEqual(hit.total,140*100/160)
        self.assertEqual(hit.magic,0);self.assertEqual(hit.true,0)
    def test_invalid_inputs(self):
        for kwargs in [{'rank':5},{'crit_chance':1.1},{'crit_chance':0,'outcome':'Critical'},{'hits':2},{'ad':float('nan')}]:
            args=dict(slot='Q',rank=1,ad=100,crit_chance=.5,crit_damage=2,armor=100);args.update(kwargs)
            with self.assertRaises(ValueError):samira_skill(**args)
        with self.assertRaises(ValueError):samira_skill('Z',1,100,.5,2,100)

if __name__=='__main__':unittest.main()
