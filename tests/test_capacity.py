import csv
import hashlib
import io
import json
from pathlib import Path
import unittest

import brca_core as core
from capacity_explorer import budget_options, export_csv, queue_rows, rapid_rows


class EvidenceTests(unittest.TestCase):
    def test_source_files_are_unchanged(self):
        root = Path(__file__).resolve().parents[1] / 'evidence'
        sources = json.loads((root / 'sources.json').read_text())
        for name, details in sources['files'].items():
            with self.subTest(name=name):
                self.assertEqual(hashlib.sha256((root / name).read_bytes()).hexdigest(), details['sha256'])

    def test_measured_tradeoff(self):
        rows = rapid_rows('cv')
        model, combined = rows[0], rows[-1]
        self.assertEqual((model['packages'], model['hits']), (212.6, 26.6))
        self.assertEqual((combined['packages'], combined['hits']), (280, 29.4))
        self.assertAlmostEqual(combined['packages'] - model['packages'], 67.4)
        self.assertAlmostEqual(combined['hits'] - model['hits'], 2.8)
        self.assertAlmostEqual(model['packages_per_hit'], 212.6 / 26.6)

    def test_temporal_tradeoff(self):
        rows = rapid_rows('temporal')
        self.assertEqual((rows[0]['packages'], rows[0]['hits']), (40, 8))
        self.assertEqual((rows[-1]['packages'], rows[-1]['hits']), (49, 8))
        self.assertEqual(rows[1]['hits'], 3)  # 25% threshold loses five detectable positives.

    def test_rapid_hits_are_not_all_carriers(self):
        for period, carriers, detectable in [('cv', 167, 41), ('temporal', 52, 17)]:
            for row in rapid_rows(period):
                self.assertEqual(row['carriers'], carriers)
                self.assertEqual(row['detectable'], detectable)
                self.assertAlmostEqual(row['hits'] + row['unselected_detectable'], detectable)
                self.assertLessEqual(row['hits'], row['packages'])

    def test_budget_boundaries_without_interpolation(self):
        self.assertEqual(budget_options('temporal', 0), [])
        self.assertNotIn('model>=0.2', [r['key'] for r in budget_options('temporal', 39)])
        self.assertIn('model>=0.2', [r['key'] for r in budget_options('temporal', 40)])
        self.assertEqual(len(budget_options('cv', 1295)), 6)
        for invalid in [-1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                budget_options('cv', invalid)

    def test_queue_same_workload_is_distinct_from_fixed_threshold(self):
        a, b, matched = queue_rows(core.M, 'cv')
        self.assertEqual(a['patients'], matched['patients'])
        self.assertAlmostEqual(a['coverage'], 0.778443113772455)
        self.assertAlmostEqual(matched['coverage'], 0.7952095808383233)
        self.assertLess(b['patients'], a['patients'])
        a, b, matched = queue_rows(core.M, 'temporal')
        self.assertEqual((a['patients'], b['patients'], matched['patients']), (180, 176, 180))
        self.assertEqual([r['coverage'] for r in [a, b, matched]], [0.75] * 3)

    def test_summary_uses_selected_rule(self):
        a, b = core.summary('A'), core.summary('B')
        self.assertAlmostEqual(a['covered'], 0.778443113772455)
        self.assertAlmostEqual(b['covered'], 0.7652694610778443)
        self.assertAlmostEqual(b['t_moved'], 176 / 477)
        with self.assertRaises(ValueError):
            core.summary('C')

    def test_export_keeps_exact_counts_and_evaluation(self):
        for period in ('cv', 'temporal'):
            rows = list(csv.DictReader(io.StringIO(export_csv(period).decode('utf-8-sig'))))
            self.assertEqual(len(rows), 6)
            self.assertTrue(all(r['evaluation'] == period for r in rows))
            self.assertEqual(float(rows[0]['hits']), 26.6 if period == 'cv' else 8)

    def test_original_probability_selftest(self):
        self.assertEqual(core.selftest(), (47, 47))
