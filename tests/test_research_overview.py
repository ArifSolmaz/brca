import hashlib
import json
import os
from pathlib import Path
import re
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from research_overview import EVIDENCE, build_overview_html, overview_article, snapshot

APP = Path(__file__).resolve().parents[1] / 'app.py'


def rendered(at):
    return '\n'.join(n.value for n in at if n.type == 'html')


def control(at, key):
    return next(n for n in at if getattr(n, 'key', None) == key)


class ResearchEvidenceTests(unittest.TestCase):
    def test_frozen_source_integrity_and_aggregate_only(self):
        manifest = json.loads((EVIDENCE / 'sources.json').read_text())
        for name, source in manifest['files'].items():
            with self.subTest(name=name):
                data = (EVIDENCE / name).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), source['sha256'])
                self.assertNotRegex(data.decode(), r'BR\d{3,}|/Users/|download_url|protocol_ids')
        d = snapshot()
        self.assertEqual(d['primary']['n'], 87)
        self.assertGreater(d['primary']['hi'], 1)
        self.assertGreater(d['primary']['q_cumulative'], .05)
        self.assertEqual(d['result']['cumulative_attempts'], 26035)

    def test_offline_presentation_keeps_uncertainty_and_data_request(self):
        for lang, upper, unvalidated, independent in [
            ('tr', '1,0007', 'henüz doğrulanmış değil', 'Bağımsız hastalar ve aileler'),
            ('en', '1.0007', 'remains unvalidated', 'Independent patients and families'),
        ]:
            with self.subTest(lang=lang):
                text = build_overview_html(lang)
                self.assertIn(overview_article(lang), text)
                self.assertIn(upper, text)  # Rounding must not turn the CI into a claim of significance.
                self.assertIn(unvalidated, text)
                self.assertIn(independent, text)
                self.assertIn('703', text)
                self.assertNotIn('<script', text)
                self.assertNotRegex(text, r'(?:src|href)=[\'"]https?://')
                self.assertNotIn('/Users/', text)


class ResearchAppTests(unittest.TestCase):
    def start(self, research=False, lang='tr'):
        at = AppTest.from_file(str(APP), default_timeout=30)
        at.session_state['auth'] = True
        at.session_state['lang_sel'] = lang
        if research:
            at.query_params['sayfa'] = 'arastirma'
        at.run()
        self.assertFalse(at.exception, [e.message for e in at.exception])
        return at

    def test_direct_route_and_bilingual_overview(self):
        for lang, title, size in [('tr', 'Elimizde ne var', '0,4206–1,0007'),
                                  ('en', 'What do we have', '0.4206–1.0007')]:
            with self.subTest(lang=lang):
                at = self.start(True, lang)
                self.assertIn(title, rendered(at))
                self.assertIn(size, rendered(at))
                self.assertEqual(control(at, 'app_view').value, 'research')
                self.assertEqual(len(at.number_input), 0)
                self.assertIn('research_overview_download', [getattr(n, 'key', None) for n in at])

    def test_view_round_trip_preserves_patient_and_capacity_state(self):
        at = self.start()
        at.button(key='btn_example').click().run()
        at.radio(key='capacity_period').set_value('temporal').run()
        at.slider(key='capacity_budget_temporal').set_value(10).run()
        before = next(n.value for n in at if n.type == 'html' and "id='sonuc'" in n.value)
        control(at, 'app_view').set_value('research').run()
        self.assertFalse(at.exception)
        # Another rerun allows hidden-widget cleanup and a language change to occur.
        control(at, 'lang_sel').set_value('en').run()
        control(at, 'lang_sel').set_value('tr').run()
        control(at, 'app_view').set_value('calculator').run()
        self.assertFalse(at.exception, [e.message for e in at.exception])
        after = next(n.value for n in at if n.type == 'html' and "id='sonuc'" in n.value)
        self.assertEqual(before, after)
        self.assertEqual(at.radio(key='capacity_period').value, 'temporal')
        self.assertEqual(at.slider(key='capacity_budget_temporal').value, 10)
        self.assertNotIn('sayfa', at.query_params)

    def test_password_gate_protects_overview_and_download(self):
        with patch.dict(os.environ, {'BRCA_NO_PASSWORD': '', 'BRCA_APP_PASSWORD': 'synthetic-test-password'}):
            at = AppTest.from_file(str(APP), default_timeout=30)
            at.query_params['sayfa'] = 'arastirma'
            at.run()
        self.assertFalse(at.exception)
        self.assertNotIn("id='arastirma'", rendered(at))
        self.assertNotIn('research_overview_download', [getattr(n, 'key', None) for n in at])
