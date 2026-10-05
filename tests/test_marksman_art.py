import json,sys,tempfile,unittest,zipfile
from unittest.mock import patch
from pathlib import Path
from html.parser import HTMLParser
from marksman_art import art_catalogue,studio_html
from sharpwr.marksman_kits import PRIORITIES
ROOT=Path(__file__).resolve().parents[1]
class MarksmanArt(unittest.TestCase):
 def test_complete_roster_and_exports(self):
  profiles=art_catalogue()['champions'];manifest=json.loads((ROOT/'data/marksman-3d-assets.json').read_text())
  self.assertEqual(set(profiles),set(PRIORITIES));self.assertEqual(set(manifest['champions']),set(PRIORITIES))
  for name,p in profiles.items():
   self.assertEqual(set(p['skills']),set('QWER'))
   asset=manifest['champions'][name];self.assertEqual((ROOT/'assets/marksman-3d/models'/asset['file']).stat().st_size,asset['bytes'])
   self.assertEqual([x['name'] for x in asset['clips']],['Idle','Walk','AA','P','Q','W','E','R'])
 def test_download_bundle_matches_current_assets(self):
  sys.path.insert(0,str(ROOT/'scripts'));from package_marksman_art import package
  with tempfile.TemporaryDirectory() as folder,zipfile.ZipFile(package(Path(folder)/'bundle.zip')) as archive:
   for model in (ROOT/'assets/marksman-3d/models').glob('*.glb'):
    self.assertEqual(archive.read('models/'+model.name),model.read_bytes())
   for name in ['rig.js','effects.js','scene.js']:
    self.assertEqual(archive.read('runtime/'+name),(ROOT/'assets/marksman-3d'/name).read_bytes())
 def test_studio_is_complete_and_separate(self):
  html=studio_html();self.assertNotIn('__ART_DATA__',html);self.assertNotIn('__RIG_SCRIPT__',html)
  self.assertIn('Animation studies use authored demonstration durations',html)
  self.assertNotIn('BuildFightEvaluator',html)
  for name in PRIORITIES:self.assertIn(name,html)
  self.assertTrue('"modelBase": "app/static/marksman-3d/"' in html,'studio loads models from the app static path')
  self.assertLess(len(html),1_500_000,'models load from static/, never embedded in the page')
 def test_studio_render_is_cached_until_an_input_changes(self):
  import marksman_art
  self.assertIs(studio_html(),studio_html())
  with tempfile.TemporaryDirectory() as folder:
   probe=Path(folder)/'probe.js';probe.write_text('a')
   with patch.object(marksman_art,'_studio_inputs',return_value=[probe,Path(folder)/'missing.js']):
    before=marksman_art._input_stamp();probe.write_text('changed')
    self.assertNotEqual(before,marksman_art._input_stamp())
 def test_channel_windows_come_from_captured_trace(self):
  from sharpwr import engine_namespace
  from sharpwr.build_fight_optimizer import BuildFightEvaluator
  from combat_replay import replay_payload
  for name in ['Samira','Lucian','Jhin']:
   ev=BuildFightEvaluator(engine_namespace(),name,15,10000,100,100);row=ev.evaluate([]);r=ev.replay_row(row)
   payload=replay_payload(r,champion=name,level=15,target='Dummy',hp=10000,build=row)
   channels=[w for w in payload['animation_windows'] if w['channel_end']>w['time']]
   self.assertTrue(channels,name)
   for w in channels:self.assertIn(w['channel_end'],[m.get('channel_until') for m in r.motion])
   self.assertEqual(payload['damage'],row['Damage']);self.assertEqual(payload['ttk'],row['TTK'])
