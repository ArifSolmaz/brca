import os
from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

APP = Path(__file__).resolve().parents[1] / 'app.py'


def html(at):
    return '\n'.join(n.value for n in at if n.type == 'html')


def result(at):
    return next(n.value for n in at if n.type == 'html' and "id='sonuc'" in n.value)


class AppTests(unittest.TestCase):
    def start(self, lang='en', rule='A', mode='order'):
        at = AppTest.from_file(str(APP), default_timeout=30)
        at.session_state['auth'] = True
        at.session_state['lang_sel'] = lang
        at.session_state['mode'] = mode
        at.query_params['rule'] = rule
        at.run()
        self.assertFalse(at.exception, [e.message for e in at.exception])
        return at

    def test_bilingual_start_and_period_controls(self):
        for lang in ['tr', 'en']:
            with self.subTest(lang=lang):
                at = self.start(lang)
                self.assertEqual(len(at.dataframe), 2)
                self.assertNotIn("data-testid='pcal'", html(at))
                at.radio(key='capacity_period').set_value('temporal').run()
                self.assertFalse(at.exception)
                self.assertEqual(at.metric[0].value, '40.0')
                self.assertEqual(at.metric[1].value, '8.0')
                at.slider(key='capacity_budget_temporal').set_value(0).run()
                self.assertFalse(at.exception)
                at.radio(key='capacity_period').set_value('cv').run()
                self.assertFalse(at.exception)
                self.assertEqual(at.metric[0].value, '212.6')

    def test_b_preview_has_its_own_evidence(self):
        at = self.start(rule='B')
        # Hero rounds coverage to 77% and moved share to 44%.
        self.assertIn("<div class='v'>77%</div>", html(at))
        self.assertIn('by moving 44% of patients', html(at))
        self.assertNotIn("<div class='v'>78%</div>", html(at))

    def test_family_hides_personal_probability_everywhere(self):
        for lang in ['tr', 'en']:
            with self.subTest(lang=lang):
                at = self.start(lang)
                at.number_input(key='age').set_value(62).run()
                self.assertIn("data-testid='pcal'", result(at))
                at.toggle(key='urg_fam').set_value(True).run()
                self.assertFalse(at.exception)
                self.assertNotIn("data-testid='pcal'", result(at))
                self.assertNotIn('≈', result(at))
                self.assertNotIn("class='scale'", result(at))
                self.assertEqual(len(at.warning), 1)
                self.assertIn('P/LP', result(at))
                self.assertIn('targeted' if lang == 'en' else 'hedefli', result(at))
                mobile = next(n.value for n in at if n.type == 'html' and "class='sticky'" in n.value)
                self.assertNotIn('%', mobile)

    def test_reduction_keeps_full_test_and_fractional_misses(self):
        at = self.start(mode='reduce')
        at.number_input(key='age').set_value(62).run()
        self.assertFalse(at.exception)
        rendered = result(at)
        self.assertIn('MEETS THE HYPOTHETICAL RULE', rendered)
        self.assertIn('Full test in the usual order', rendered)
        self.assertIn('0.2', rendered)
        self.assertIn('1 in 431', rendered)
        self.assertIn('4.2%', rendered)
        self.assertNotIn('TEST CAN BE SKIPPED', html(at))
        at.toggle(key='urg_dec').set_value(True).run()
        self.assertIn('DOES NOT MEET THE HYPOTHETICAL RULE', result(at))
        self.assertIn('Request the full test now', result(at))

    def test_capacity_controls_never_change_patient_result(self):
        at = self.start()
        at.button(key='btn_example').click().run()
        before = result(at)
        for i in range(6):
            at.selectbox(key='capacity_strategy').set_value(i).run()
            self.assertFalse(at.exception)
            self.assertEqual(result(at), before)
        at.radio(key='capacity_period').set_value('temporal').run()
        at.slider(key='capacity_budget_temporal').set_value(0).run()
        self.assertEqual(result(at), before)

    def test_password_gate_still_blocks_explorer(self):
        with patch.dict(os.environ, {'BRCA_NO_PASSWORD': '', 'BRCA_APP_PASSWORD': 'synthetic-test-password'}):
            at = AppTest.from_file(str(APP), default_timeout=30).run()
        self.assertFalse(at.exception)
        self.assertEqual(len(at.dataframe), 0)
        self.assertEqual(len(at.metric), 0)
