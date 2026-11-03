"""Presentation and navigation checks; no patient analyses."""
import json
import unittest
from unittest.mock import patch
from model_guide import guide_latex, guide_mobile_steps, NAV_SCRIPT
from pathlib import Path
from streamlit.testing.v1 import AppTest
from scripts.build_model_guides import build
from model_guide_additions import guide_additions
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]

class ModelGuideTests(unittest.TestCase):
    def test_prediction_scope_and_clinical_utility_limits_are_in_both_pdfs(self):
        for lang in ['tr','en']:
            additions=guide_additions(lang)
            self.assertEqual([b['number'] for b in additions if b['type']=='chapter'],[16,17,18,19])
            reader=PdfReader(ROOT/f'assets/model_details/BRCA_Model_Guide_{lang.upper()}.pdf')
            self.assertEqual(len(reader.pages),20)
            text=' '.join(' '.join(page.extract_text() for page in reader.pages).replace('-\n','').split())
            self.assertIn('BRCA_status_v3_strict',text)
            self.assertIn('1.128' if lang=='tr' else '1,128',text)
            self.assertIn('bekleme süresinin kısaldığı' if lang=='tr' else 'shorter waiting times',text)
            self.assertIn('hasta sonuçlarının iyileştiği ölçülmedi' if lang=='tr' else 'improved patient outcomes',text)
            self.assertIn('bağımsız doğrulama' if lang=='tr' else 'independent validation',text)

    def test_web_content_matches_existing_guide_source(self):
        for lang in ['tr','en']:
            blocks=json.loads((ROOT/f'assets/model_details/model_guide_{lang}.json').read_text())
            self.assertEqual(blocks,json.loads(json.dumps(build(lang,web=True))))
            self.assertEqual([b['number'] for b in blocks if b['type']=='chapter'],list(range(16)))
            self.assertEqual(sum(b['type']=='math' for b in blocks),25)
            self.assertEqual(sum(b['type']=='link' for b in blocks),9)

    def test_desktop_equation_is_unchanged_and_mobile_has_final_result(self):
        blocks=build('en',web=True)
        formulas=[b['text'] for b in blocks if b['type']=='math']
        for i,formula in enumerate(formulas):
            with patch('model_guide.st.container'),patch('model_guide.st.latex') as latex:
                guide_latex(formula,i)
                self.assertEqual(latex.call_args_list[0].args,(formula,))
        position=next(f for f in formulas if f.startswith(r'\mathrm{Position}'))
        steps=guide_mobile_steps(position)
        self.assertEqual(steps[-1],r'\mathrm{Position}=89')
        self.assertIn('guide-toc a',NAV_SCRIPT)
        self.assertIn('preventDefault()',NAV_SCRIPT)
        self.assertIn('scrollIntoView',NAV_SCRIPT)

    def test_downloadable_pdfs_include_shared_additions_and_their_sources(self):
        for lang in ['tr','en']:
            asset=ROOT/f'assets/model_details/BRCA_Model_Guide_{lang.upper()}.pdf'
            self.assertEqual(asset.read_bytes(),(ROOT/f'output/pdf/{asset.name}').read_bytes())
            reader=PdfReader(asset)
            text=' '.join(page.extract_text() for page in reader.pages)
            # Arial's PDF mapping may extract a semicolon as the identical Greek glyph.
            normalized=''.join(text.split()).replace('\u037e',';')
            for block in guide_additions(lang):
                if block['type']=='chapter':
                    self.assertIn(''.join(block['text'].split()),normalized)
            links={str(a.get_object().get('/A',{}).get('/URI','')) for page in reader.pages for a in page.get('/Annots',[])}
            for block in guide_additions(lang):
                if block['type']=='link': self.assertIn(block['url'],links)
            for value in ['1.609','0.223','4.605','92.88' if lang=='en' else '92,88']:
                self.assertIn(value,text)

    def test_fourth_view_deep_links_and_language_switch(self):
        for lang in ['tr','en']:
            at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
            at.session_state['auth']=True
            at.query_params.update({'sayfa':'rehber','dil':lang})
            at.run()
            self.assertFalse(at.exception,[e.message for e in at.exception])
            self.assertEqual(at.session_state['app_view'],'guide')
            self.assertEqual(at.title[0].value,'Model rehberi' if lang=='tr' else 'Model guide')
            self.assertGreater(len(at.latex),50)
            selector=next(n for n in at if getattr(n,'key',None)=='app_view')
            self.assertEqual(len(selector.options),4)
            other='en' if lang=='tr' else 'tr'
            next(n for n in at if getattr(n,'key',None)=='lang_sel').set_value(other).run()
            self.assertFalse(at.exception)
            self.assertEqual(at.query_params['dil'],[other])

if __name__=='__main__':unittest.main()
