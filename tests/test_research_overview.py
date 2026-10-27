import hashlib
import io
import json
import os
from pathlib import Path
import re
import unittest
import zipfile
from unittest.mock import patch

from streamlit.testing.v1 import AppTest
from research_overview import EVIDENCE, build_overview_html, build_evidence_bundle, overview_article, snapshot
from research_report import report_data, report_html, PDF as REPORT_PDF

APP = Path(__file__).resolve().parents[1] / 'app.py'


def rendered(at):
    return '\n'.join(n.value for n in at if n.type == 'html')


def control(at, key):
    return next(n for n in at if getattr(n, 'key', None) == key)


class ResearchEvidenceTests(unittest.TestCase):
    def test_download_bundle_is_aggregate_only_and_matches_display_sources(self):
        with zipfile.ZipFile(io.BytesIO(build_evidence_bundle())) as archive:
            hashes = json.loads(archive.read('paket_manifestosu.json'))
            self.assertEqual(set(archive.namelist()), set(hashes) | {'paket_manifestosu.json'})
            self.assertIn('KANIT_REHBERI_TR.md', hashes)
            self.assertIn('calculator_prediction_date_audit.json', hashes)
            self.assertIn('research/size_results.json', hashes)
            for name, expected in hashes.items():
                data = archive.read(name)
                self.assertEqual(hashlib.sha256(data).hexdigest(), expected)
                if name.endswith('.pdf'):
                    self.assertTrue(data.startswith(b'%PDF-'))
                    self.assertEqual(data, REPORT_PDF.read_bytes())
                else:
                    self.assertNotRegex(data.decode(), r'BR\d{3,}|/Users/|download_url|patient_action_list|protocol_ids')
            self.assertEqual(json.loads(archive.read('model_full_embedded.json'))['n'], 1295)
            self.assertEqual(json.loads(archive.read('research/size_results.json')), snapshot()['result'])

    def test_report_versions_match_frozen_sources_and_pdf(self):
        manifest = json.loads((EVIDENCE.parent / 'research_report_manifest.json').read_text())
        for name, expected in manifest['files'].items():
            self.assertEqual(hashlib.sha256((APP.parent / name).read_bytes()).hexdigest(), expected)
        d = report_data()
        self.assertEqual(len(d['pages']), 7)
        self.assertEqual(d['prepared'], '25 Ekim 2026')
        self.assertEqual(d['pages'][0]['title'], 'Önce kısa özet')
        self.assertIn('Bu çalışma neyi gösteriyor, neyi henüz göstermiyor?', report_html())
        self.assertIn('p ve q', report_html())
        self.assertIn('İkisi de bulgunun doğru olma olasılığı değildir.', report_html())
        self.assertEqual(d['evidence_date'], '24 Ekim 2026')
        text = report_html()
        self.assertIn('20 stop-gain, 67 frameshift', text)
        self.assertIn('0,4206 - 1,0007', text)
        self.assertIn('0,5273', text)
        self.assertIn('0 doğrulamaya uygun hasta', text)
        self.assertIn('[P1]', text)
        self.assertIn('[P4]', text)
        self.assertNotIn('[1]', text)
        refs = [b for p in d['pages'] for b in p['blocks'] if b['type'] == 'reference']
        self.assertEqual({b['id'] for b in refs}, {'M1', 'M2'})
        urls = {b['url'] for b in refs}
        self.assertEqual(urls, {'https://doi.org/10.1016/j.jmoldx.2014.11.004',
                                'https://doi.org/10.1111/j.2517-6161.1995.tb02031.x'})
        for url in urls:
            self.assertIn(f"href='{url}'", text)
        self.assertNotRegex(text, r'BR\d{3,}|/Users/|Hülya hoca|kohort')

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

        audit = json.loads((EVIDENCE.parent / 'calculator_prediction_date_audit.json').read_text())
        summary, validation = audit['summary'], audit['validation']
        self.assertEqual((summary['patients'], summary['recorded_family_groups']), (51, 51))
        self.assertEqual((summary['positive'], summary['negative']), (14, 37))
        self.assertEqual(summary['original_diagnosis_year_available'] + summary['missing_diagnosis_year_after'], 51)
        self.assertEqual(summary['missing_diagnosis_year_after'], 10)
        self.assertEqual(summary['validation_eligible'], 0)
        self.assertEqual(validation['prediction_calls'] + validation['fit_calls'] + validation['new_hypotheses'], 0)
        self.assertIsNone(validation['auc'])  # Not estimable must never be displayed as zero performance.
        for filename, key in [('model_full_embedded.json', 'model_sha256'), ('brca_core.py', 'calculation_core_sha256')]:
            self.assertEqual(hashlib.sha256((APP.parent / filename).read_bytes()).hexdigest(), validation[key])
        self.assertNotRegex(json.dumps(audit), r'BR\d{3,}|/Users/|download_url|protocol_ids|patient_action_list')

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
                external_links = re.findall(r"""(?:src|href)=['"](https?://[^'"]+)""", text)
                self.assertEqual(external_links, ['https://doi.org/10.1016/j.jmoldx.2014.11.004'])
                self.assertNotIn('Drive’daki 2015', text)
                self.assertNotIn('paper stored in Drive', text)
                self.assertNotIn('/Users/', text)
                self.assertNotIn('Hülya hoca', text)
                if lang == 'tr':
                    self.assertNotIn('kohort', text.lower())
                    self.assertIn('Bu rakamlar nereden geliyor?', text)
                self.assertIn("id='hesaplayici-dogrulama'", text)
                self.assertEqual(text.count("id='provenance-title'"), 1)
                self.assertIn('0’ı tarihli veri kontrolünü geçti' if lang == 'tr' else '0 of 51 candidates passed', text)
                self.assertIn('sekiz aile öyküsü' if lang == 'tr' else 'eight family-history', text)
                self.assertIn('ilk BRCA sonucunun' if lang == 'tr' else 'first BRCA result/disclosure', text)
                self.assertIn('Tanı yılı hesaplayıcının bir girdisi değil' if lang == 'tr' else 'Diagnosis year is not a calculator input', text)


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
                self.assertIn('research_evidence_download', [getattr(n, 'key', None) for n in at])
                self.assertIn('research_report_pdf_download', [getattr(n, 'key', None) for n in at])
                self.assertIn("id='arastirma-rapor-metni'", rendered(at))

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
        self.assertNotIn('research_evidence_download', [getattr(n, 'key', None) for n in at])
        self.assertNotIn('research_report_pdf_download', [getattr(n, 'key', None) for n in at])
