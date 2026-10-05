import unittest
from champion_database import CHAMPION_DATABASE, champion_stat
from sharpwr import C

class ChampionDatabaseTests(unittest.TestCase):
    def test_existing_stats_preserved_exactly(self):
        old=C
        fields=('base_ad','ad_growth','as_ratio','base_as','base_bonus_as','as_growth')
        self.assertEqual(set(old),set(CHAMPION_DATABASE))
        for name,values in old.items():
            self.assertEqual(tuple(champion_stat(name,f) for f in fields),values)
    def test_sourced_core_stats_and_no_pc_fallback(self):
        core=('base_hp','hp_growth','base_hp_regen_per_5s','hp_regen_growth_per_5s','base_mana','mana_growth','base_mana_regen_per_5s','mana_regen_growth_per_5s','base_armor','armor_growth','base_mr','mr_growth','movement_speed','attack_range')
        for name,record in CHAMPION_DATABASE.items():
            if name=='Yunara':continue
            self.assertEqual(record['source_status'],'wr_wiki_parameter_table')
            self.assertIn('WR_Data_',record['wiki_source_url'])
            for field in core:
                value=record['stats'][field]
                self.assertIsInstance(value,(int,float),(name,field))
                self.assertGreaterEqual(value,0)
                self.assertEqual(record['field_sources'][field]['url'],record['wiki_source_url'])
    def test_unknown_is_null_and_yunara_manual(self):
        record=CHAMPION_DATABASE['Yunara']
        self.assertEqual(record['source_status'],'manual_observed_levels_partial')
        self.assertEqual(champion_stat('Yunara','base_mana'),345)
        for record in CHAMPION_DATABASE.values():
            self.assertEqual(set(record['unavailable_fields']),{field for field,value in record['stats'].items() if value is None})

if __name__=='__main__':unittest.main()

class LevelStatTests(unittest.TestCase):
    def test_samira_level_and_item_independent_stats(self):
        from champion_database import level_stats
        self.assertEqual(level_stats('Samira',1)['mana'],345)
        self.assertAlmostEqual(level_stats('Samira',15)['mana'],345+49*13.265)
        self.assertEqual(level_stats('Yunara',15)['mana'],807)
