import hashlib
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from streamlit.testing.v1 import AppTest
from model_teaching import trace, paired_tex, contribution_html, PDF, ASSETS
ROOT=Path(__file__).resolve().parents[1]

def control(at,key):return next(n for n in at if getattr(n,'key',None)==key)
def result(at):return next(n.value for n in at if n.type=='html' and "id='sonuc'" in n.value)

class ModelTeachingTests(unittest.TestCase):
    def start(self,lang='en',teaching=True):
        at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30)
        at.session_state['auth']=True
        if teaching:at.query_params.update({'sayfa':'model','dil':lang})
        else:at.session_state['lang_sel']=lang
        at.run();self.assertFalse(at.exception,[e.message for e in at.exception]);return at

    def test_frozen_core_and_all_synthetic_traces(self):
        for filename,sha in {'brca_core.py':'97406bcaae6528db1fbd64b867ba6492f7f2f92fc8d594f1306b75774eaa9356','model_full_embedded.json':'79374a66c7530d58a547a0a4a8ba252fb151489b376463a3ff5bd9cb201914aa'}.items():
            self.assertEqual(hashlib.sha256((ROOT/filename).read_bytes()).hexdigest(),sha)
        for c in json.loads((ASSETS/'synthetic_examples.json').read_text()):
            r=trace(c['inputs'])
            for k in ['z','p_cal','p_raw','eta']:self.assertAlmostEqual(r[k],c[k],places=12)
            for rule in ['A','B']:
                for k in ['total','lane','rapid']:self.assertEqual(r[rule][k],c[rule][k])

    def test_bilingual_routes_downloads_and_language_switch(self):
        for lang,title,percent in [('tr','Model ayrıntıları ve elle hesap','25,8%'),('en','Model details and manual calculations','25.8%')]:
            at=self.start(lang);self.assertEqual(at.title[0].value,title);self.assertEqual(at.metric[0].value,percent)
            self.assertEqual(at.metric[1].value,'6');self.assertTrue(PDF[lang].read_bytes().startswith(b'%PDF-'))
            self.assertEqual(len(at.get('download_button')),2)
        control(at,'lang_sel').set_value('tr').run();self.assertFalse(at.exception);self.assertEqual(at.query_params['dil'],['tr'])
        self.assertEqual(at.metric[0].value,'25,8%')
        self.assertEqual(at.selectbox(key='teaching_preset_tr').value,1)
        self.assertEqual(at.selectbox(key='teaching_dx_tr').value,'breast')

    def test_teaching_and_research_round_trip_preserves_calculator(self):
        at=self.start(teaching=False);at.button(key='btn_example').click().run();before=result(at)
        control(at,'app_view').set_value('model').run();self.assertFalse(at.exception)
        at.selectbox(key='teaching_preset_en').set_value(2).run();self.assertFalse(at.exception);self.assertEqual(at.metric[0].value,'8.6%')
        control(at,'app_view').set_value('research').run();self.assertFalse(at.exception)
        control(at,'app_view').set_value('calculator').run();self.assertFalse(at.exception)
        self.assertEqual(result(at),before)

    def test_live_result_tracks_edits_and_reset_without_changing_calculator(self):
        at=self.start();at.number_input(key='teaching_age').set_value(48).run()
        self.assertFalse(at.exception)
        html=' '.join(n.value for n in at if n.type=='html')
        self.assertNotIn('id="teaching-live"',html)
        self.assertIn('max-width:none',html)
        self.assertIn('teaching-arithmetic',html)
        self.assertIn('class="edited"',html)
        self.assertIn('Age at diagnosis: 38 → 48',html)
        self.assertIn('percentage points',html)
        self.assertIn('Δz -0.297415',html)
        formulas=' '.join(n.proto.body for n in at if n.type=='latex')
        self.assertIn('0.51964871',formulas)
        self.assertIn('-1.33602736',formulas)
        self.assertIn('0.208164117',formulas)
        self.assertIn('leftarrow 6',formulas)
        self.assertIn('Last-edit contributions', ' '.join(n.label for n in at.expander))
        at.checkbox(key='teaching_urg_dec').set_value(True).run()
        self.assertFalse(at.exception)
        self.assertEqual(at.session_state['_teaching_change']['delta_pp'],0)
        self.assertEqual(at.session_state['_teaching_change']['contributions'],[])
        at.checkbox(key='teaching_urg_fam').set_value(True).run()
        self.assertFalse(at.exception)
        self.assertEqual(at.metric[0].value,'Family-specific assessment')
        at.button(key='teaching_reset').click().run()
        self.assertFalse(at.exception);self.assertEqual(at.metric[0].value,'25.8%')
        self.assertNotIn('_teaching_change',at.session_state)
        at.selectbox(key='teaching_preset_en').set_value(2).run()
        control(at,'lang_sel').set_value('tr').run()
        self.assertFalse(at.exception)
        self.assertEqual(at.metric[0].value,'8,6%')
        self.assertEqual(at.selectbox(key='teaching_preset_tr').value,2)
        self.assertEqual(at.selectbox(key='teaching_grade_tr').value,'g3')

    def test_previous_values_follow_only_the_last_edit_in_both_languages(self):
        for lang in ['en','tr']:
            at=self.start(lang)
            initial=trace(at.session_state['_teaching_previous']['v'])
            at.number_input(key='teaching_age').set_value(48).run()
            self.assertFalse(at.exception)
            current=at.session_state['_teaching_previous']
            formulas=' '.join(n.proto.body for n in at if n.type=='latex')
            for key,digits in [('z',8),('p_raw',8),('eta',8),('p_cal',9)]:
                self.assertIn(paired_tex(current[key],initial[key],lang,digits),formulas)
            self.assertIn(paired_tex(20.8,25.8,lang,1,rounded=True),formulas)
            self.assertIn(paired_tex(0,1,lang,0),formulas)  # Lost age card point remains visible.
            html=contribution_html(current,at.session_state['_teaching_change'],lang)
            self.assertGreaterEqual(html.count('formula-previous'),7)  # Input, contribution and all later cumulative sums.
            self.assertNotIn('boxed{-1.82409575',formulas)  # Calibration coefficient is fixed.
            at.checkbox(key='teaching_urg_dec').set_value(True).run()
            self.assertFalse(at.exception)
            compact=[n.proto.body for n in at if n.type=='latex'][:9]
            self.assertNotIn('boxed',' '.join(compact[:6]))  # No false propagation through probability math.
            self.assertIn(paired_tex(2,0,lang,0),' '.join(compact))
            saved=at.session_state['_teaching_change']['previous']
            at.run();self.assertFalse(at.exception)
            self.assertEqual(at.session_state['_teaching_change']['previous'],saved)
            at.button(key='teaching_reset').click().run()
            self.assertNotIn('_teaching_change',at.session_state)

    def test_teaching_route_keeps_password_gate(self):
        with patch.dict('os.environ',{'BRCA_APP_PASSWORD':'test-password','BRCA_NO_PASSWORD':'0'}):
            at=AppTest.from_file(str(ROOT/'app.py'),default_timeout=30);at.query_params.update({'sayfa':'model','dil':'en'});at.run()
            self.assertFalse(at.exception);self.assertEqual(len(at.get('download_button')),0);self.assertEqual(len(at.metric),0)

if __name__=='__main__':unittest.main()
