"""Presentation and navigation checks; no patient analyses."""
import json
import unittest
from pathlib import Path
from streamlit.testing.v1 import AppTest
from scripts.build_model_guides import build

ROOT=Path(__file__).resolve().parents[1]

class ModelGuideTests(unittest.TestCase):
    def test_web_content_matches_existing_guide_source(self):
        for lang in ['tr','en']:
            blocks=json.loads((ROOT/f'assets/model_details/model_guide_{lang}.json').read_text())
            self.assertEqual(blocks,json.loads(json.dumps(build(lang,web=True))))
            self.assertEqual([b['number'] for b in blocks if b['type']=='chapter'],list(range(16)))
            self.assertEqual(sum(b['type']=='math' for b in blocks),25)
            self.assertEqual(sum(b['type']=='link' for b in blocks),9)

    def test_fourth_view_deep_links_and_language_switch(self):
        for lang in ['tr','en']:
            at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
            at.session_state['auth']=True
            at.query_params.update({'sayfa':'rehber','dil':lang})
            at.run()
            self.assertFalse(at.exception,[e.message for e in at.exception])
            self.assertEqual(at.session_state['app_view'],'guide')
            self.assertEqual(at.title[0].value,'Model rehberi' if lang=='tr' else 'Model guide')
            self.assertEqual(len(at.latex),25)
            selector=next(n for n in at if getattr(n,'key',None)=='app_view')
            self.assertEqual(len(selector.options),4)
            other='en' if lang=='tr' else 'tr'
            next(n for n in at if getattr(n,'key',None)=='lang_sel').set_value(other).run()
            self.assertFalse(at.exception)
            self.assertEqual(at.query_params['dil'],[other])

if __name__=='__main__':unittest.main()
