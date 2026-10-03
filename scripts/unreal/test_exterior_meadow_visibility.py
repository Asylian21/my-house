"""CPU adversarial guards over actual recorded native R16/R17-before data."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('visibility_tests_native', ROOT / 'scripts/unreal/exterior-meadow-visibility-native.py')
n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(n)


class VisibilityGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = n.read(n.BASE / 'exterior-import-report.json')
        cls.scope = n.canonical_scope(cls.report)
        # Actual R17 native before mutation is the independently read clonedR16
        # map; this is recorded data, not a synthesized Unreal fixture.
        cls.before = n.read(ROOT / 'output/unreal/exterior-20261001-r17a/canopy-transmission-witness-before.json')

    def test_exact_scopes_and_original_family_culls(self):
        self.assertEqual(self.scope['audit']['targetGroups'], 601)
        self.assertEqual(self.scope['audit']['targetInstances'], 501890)
        self.assertEqual(len(set(self.scope['scopes'][0]['groupIds']) & set(self.scope['scopes'][1]['groupIds'])), 0)
        self.assertEqual({tuple(t['baseGroup'][k] for k in ('cullStartCm', 'cullEndCm')) for t in self.scope['targets']},
                         {(7200, 9000), (6400, 8000), (8000, 10000), (9600, 12000)})

    def test_counterfactual_only601distance_pairs(self):
        expected, deltas = n.expected_witness(self.before, self.scope['targets'])
        self.assertEqual(len(deltas), 601)
        restored = copy.deepcopy(expected)
        by_path = {c['path']: c for actor in restored.values() for c in actor['components']}
        for row in deltas: by_path[row['component']]['instanceCullCm'] = row['beforeCullCm']
        self.assertEqual(restored, self.before)
        self.assertEqual(sum(d['instances'] for d in deltas), 501890)

    def test_reject_missing_target(self):
        with self.assertRaises(RuntimeError): n.expected_witness(self.before, self.scope['targets'][:-1])

    def test_reject_duplicate_target(self):
        rows = copy.deepcopy(self.scope['targets']); rows[-1] = rows[0]
        with self.assertRaises(RuntimeError): n.expected_witness(self.before, rows)

    def test_reject_oneKilometer_distance(self):
        rows = copy.deepcopy(self.scope['targets']); rows[0]['proposedCullCm'] = [80000, 100000]
        with self.assertRaises(RuntimeError): n.expected_witness(self.before, rows)

    def test_reject_boolean_distance(self):
        rows = copy.deepcopy(self.scope['targets']); rows[0]['proposedCullCm'] = [True, 24000]
        with self.assertRaises(RuntimeError): n.expected_witness(self.before, rows)

    def test_reject_changed_ordered_native_transforms(self):
        before = copy.deepcopy(self.before); row = self.scope['targets'][0]
        before[row['baseGroup']['actor']]['components'][0]['orderedInstanceTransformsSha256'] = '0' * 64
        with self.assertRaises(RuntimeError): n.expected_witness(before, self.scope['targets'])

    def test_reject_changed_density_policy(self):
        before = copy.deepcopy(self.before); row = self.scope['targets'][0]
        before[row['baseGroup']['actor']]['detailDensityScaling'] = False
        with self.assertRaises(RuntimeError): n.expected_witness(before, self.scope['targets'])

    def test_reject_unexpected_original_culls(self):
        before = copy.deepcopy(self.before); row = self.scope['targets'][0]
        before[row['baseGroup']['actor']]['components'][0]['instanceCullCm'] = [0, 9000]
        with self.assertRaises(RuntimeError): n.expected_witness(before, self.scope['targets'])

    def test_geometry_counterfactual_retains_all_original_records(self):
        changed = n.geometry_after(self.report['geometry'], self.scope['targets'])
        restored = copy.deepcopy(changed)
        for t in self.scope['targets']: restored['groups'][t['groupId']] = t['baseGroup']
        self.assertEqual(restored, self.report['geometry'])
        self.assertEqual(len(changed['groups']), 1980)

    def test_reject_asset_added_removed_or_shader_changed(self):
        before = {n.MAP_FILE: {'sha256': 'a', 'bytes': 10}, 'leaf.uasset': {'sha256': 'b', 'bytes': 20}}
        after = copy.deepcopy(before); after[n.MAP_FILE]['sha256'] = 'c'
        self.assertEqual(n.validate_asset_delta(before, after)['changedFiles'], [n.MAP_FILE])
        for mutate in ('add', 'remove', 'shader', 'no-map-change'):
            bad = copy.deepcopy(after)
            if mutate == 'add': bad['new.uasset'] = {'sha256': 'c', 'bytes': 5}
            if mutate == 'remove': del bad['leaf.uasset']
            if mutate == 'shader': bad['leaf.uasset']['sha256'] = 'd'
            if mutate == 'no-map-change': bad = before
            with self.subTest(mutate=mutate), self.assertRaises(RuntimeError): n.validate_asset_delta(before, bad)

    def test_reject_ecology_group_outside_selected_master_whitelist(self):
        report = copy.deepcopy(self.report)
        key = report['canopyEcology']['groupIds'][0]
        report['geometry']['groups'][key]['mesh'] = '/Game/Unrelated.Mesh'
        with self.assertRaises(RuntimeError): n.canonical_scope(report)

    def test_reject_modified_library_population(self):
        report = copy.deepcopy(self.report); report['savedPlantReadback'] = report['savedPlantReadback'][:-1]
        with self.assertRaises(RuntimeError): n.canonical_scope(report)

    def test_reject_missing_original_meadow_group(self):
        report = copy.deepcopy(self.report)
        key = self.scope['scopes'][0]['groupIds'][0]; del report['geometry']['groups'][key]
        with self.assertRaises(RuntimeError): n.canonical_scope(report)


if __name__ == '__main__': unittest.main()
