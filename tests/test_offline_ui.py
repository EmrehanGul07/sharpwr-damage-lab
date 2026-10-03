import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from engine_runtime import ensure_engine_revision

ROOT=Path(__file__).resolve().parents[1]

class OfflineInterface(unittest.TestCase):
    def test_skill_replay_uses_rune_stats_mana_override_and_yuntal_start(self):
        ensure_engine_revision('5.87.1')
        import fight_engine
        original=fight_engine.replay_samira;calls=[]
        def capture(events,**kwargs):
            result=original(events,**kwargs);calls.append((kwargs,result));return result
        with patch.object(fight_engine,'replay_samira',side_effect=capture):
            app=AppTest.from_file(str(ROOT/'streamlit_app.py'),default_timeout=60).run()
            app.session_state['build_items_v2']=['Muramana','Yun Tal Wildarrows','Infinity Edge','Phantom Dancer','Statikk Shiv']
            app.session_state['build_primary_tree']='Sorcery'
            app.session_state['build_primary_slot1']='Manaflow Band'
            app.session_state['build_primary_slot2']='Absolute Focus'
            app.session_state['build_primary_slot3']='Gathering Storm'
            app.session_state['build_secondary_tree']='Domination'
            app.session_state['build_secondary_rune']='Zombie Ward'
            app.run()
            app.slider(key='build_level').set_value(15).run()
            app.number_input(key='build_mana').set_value(2000).run()
            app.selectbox(key='build_yt_crit').set_value(25).run()
            app.checkbox(key='build_yt_flurry').set_value(True).run()
            app.button(key='fight_calculate').click().run()
            self.assertFalse(app.exception,[e.message for e in app.exception])
            self.assertFalse(app.error,[x.value for x in app.error])
            self.assertTrue(calls)
            from test_combat_engine import engine_namespace
            ns=engine_namespace();s=ns['stats'](calls[0][0]['champion'],15)
            item_ad=sum(ns['dct'](ns['F'][i])['ad'] for i in app.session_state['build_items_v2'])+ns['dct'](ns['B'][app.session_state['build_boot_v2']])['ad']
            item_mana=sum(ns['dct'](ns['F'][i])['mana'] for i in app.session_state['build_items_v2'])+ns['dct'](ns['B'][app.session_state['build_boot_v2']])['mana']
            for args,result in calls:
                self.assertEqual(args['max_mana'],2000+item_mana+300)
                self.assertAlmostEqual(args['ad'],s['ad']+item_ad+.02*args['max_mana']+20+14+15)
                self.assertEqual(args['yuntal_initial'],.25)
                self.assertTrue(args['energized_items'])
                self.assertTrue(any(x['kind']=='attack_launch' for x in result.timeline))
                self.assertEqual(result.log[0]['crit_chance'],.75)
            # Early item reruns must preserve the rune controls and start state.
            app.slider(key='gathering_storm_minute').set_value(12).run()
            app.checkbox(key='absolute_focus_active').set_value(False).run()
            app.button(key='remove_item_0').click().run()
            self.assertEqual(app.slider(key='gathering_storm_minute').value,12)
            self.assertFalse(app.checkbox(key='absolute_focus_active').value)
            self.assertTrue(app.checkbox(key='build_yt_flurry').value)

if __name__=='__main__':unittest.main()
