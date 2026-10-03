"""CPU adversarial scope guards, not simulated native/visual acceptance."""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('exterior-canopy-transmission-native.py')
spec = importlib.util.spec_from_file_location('canopy_transmission_guards', SCRIPT)
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
BASE_REPORT = native.ROOT / 'output/unreal/exterior-20261001-r16a/exterior-import-report.json'


class ScopeGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = native.read(BASE_REPORT)
        cls.scope = native.canonical_scope(cls.report)

    def test_actual_native_scope_excludes_other_green_leaf_users(self):
        self.assertEqual((len(self.scope['targets']), sum(r['baseGroup']['instances'] for r in self.scope['targets'])), (23, 78))
        targets = {r['baseGroup']['mesh'] for r in self.scope['targets']}
        green = self.report['materials']['materials']['regional_green_leaf']['asset']
        other = [r for r in self.report['savedPlantReadback'] if green in r['materials'] and r['mesh'] not in targets]
        self.assertGreater(len(other), 0, 'The fixture must expose the broad-alias hazard')
        self.assertTrue(all(r['slot'] == 1 and r['unchangedBarkSlot'] == 0 for r in self.scope['targets']))

    def test_scalar_delta_has_one_native_float_change_and_no_graph_mutation(self):
        for key in native.LEAF_IDS:
            old = self.report['materials']['materials'][key]['graph']
            old_copy = copy.deepcopy(old)
            proposed = native.scalar_variant(old)
            self.assertEqual(old, old_copy)
            changed = [(a['role'], a['values'], b['values']) for a, b in zip(old['nodes'], proposed['nodes']) if a != b]
            self.assertEqual(changed, [(native.ROLE, {'r': native.EXPECTED_BASE}, {'r': native.EXPECTED_NEW})])
            self.assertEqual(proposed['roots'], old['roots'])
            self.assertEqual(proposed['flags'], old['flags'])

    def test_duplicate_role_is_rejected(self):
        g = copy.deepcopy(self.report['materials']['materials']['regional_oak_leaf']['graph'])
        g['nodes'].append(copy.deepcopy(next(n for n in g['nodes'] if n['role'] == native.ROLE)))
        with self.assertRaisesRegex(RuntimeError, 'ambiguous'):
            native.scalar_variant(g)

    def test_missing_transmission_root_or_changed_expression_is_rejected(self):
        for mutation in ('root', 'code'):
            g = copy.deepcopy(self.report['materials']['materials']['regional_green_leaf']['graph'])
            if mutation == 'root':
                g['roots']['SUBSURFACE_COLOR'] = None
            else:
                next(n for n in g['nodes'] if n['role'] == 'BreziExterior:leaf-transmission')['values']['code'] += ' '
            with self.assertRaises(RuntimeError):
                native.scalar_variant(g)

    def test_baseline_library_or_population_tampering_is_rejected(self):
        for kind in ('library', 'population', 'slot', 'graph', 'design'):
            r = copy.deepcopy(self.report)
            if kind == 'library': r['savedPlantReadback'].pop()
            elif kind == 'population': r['geometry']['groups'][self.scope['targets'][0]['groupId']]['instances'] += 1
            elif kind == 'slot': r['savedPlantReadback'][-1]['materials'].reverse()
            elif kind == 'graph': r['materials']['materials']['regional_green_leaf']['graph']['flags']['two_sided'] = False
            else: r['activeDesign']['variant'] = 'A'
            with self.assertRaises(RuntimeError, msg=kind):
                native.canonical_scope(r)

    def test_same_master_outside_grove_cannot_substitute_for_selected_group(self):
        r = copy.deepcopy(self.report)
        identity = self.scope['targets'][0]['groupId']
        row = r['geometry']['groups'].pop(identity)
        r['geometry']['groups']['unrelated-same-master'] = row
        with self.assertRaisesRegex(RuntimeError, 'saved grove canopy receipt'):
            native.canonical_scope(r)

    @staticmethod
    def inventory_pair():
        before = {native.MAP_FILE: {'sha256': 'old', 'bytes': 1}, 'other.uasset': {'sha256': 'protected', 'bytes': 5}}
        after = copy.deepcopy(before)
        after[native.MAP_FILE] = {'sha256': 'new', 'bytes': 2}
        for asset in native.NEW_ASSETS.values():
            after[asset.split('.')[0].removeprefix('/Game/') + '.uasset'] = {'sha256': 'variant', 'bytes': 10}
        return before, after

    def test_only_one_map_and_two_new_material_packages_allowed(self):
        before, after = self.inventory_pair()
        delta = native.validate_asset_delta(before, after)
        self.assertEqual(delta['changedFiles'], [native.MAP_FILE])
        self.assertEqual(len(delta['newFiles']), 2)
        self.assertEqual(delta['protectedFilesByteIdentical'], 1)

    def test_protected_original_material_edit_is_rejected(self):
        before, after = self.inventory_pair()
        after['other.uasset']['sha256'] = 'overwritten'
        with self.assertRaisesRegex(RuntimeError, 'one saved map'):
            native.validate_asset_delta(before, after)

    def test_extra_texture_or_missing_variant_or_removed_original_is_rejected(self):
        for attack in ('texture', 'missing', 'removed', 'unchanged-map'):
            before, after = self.inventory_pair()
            if attack == 'texture': after['Brezi/CanopyTransmissionR1/Materials/T_extra.uasset'] = {'sha256': 'new', 'bytes': 10}
            elif attack == 'missing': del after[next(k for k in after if 'M_canopy_transmission' in k)]
            elif attack == 'removed': del after['other.uasset']
            else: after[native.MAP_FILE] = before[native.MAP_FILE]
            with self.assertRaises(RuntimeError, msg=attack):
                native.validate_asset_delta(before, after)

    def witness(self):
        rows = {'unrelated': {'components': [{'path': 'garden', 'mesh': 'garden-mesh',
                'materials': [self.scope['variants']['regional_green_leaf']['originalAsset']], 'overrideMaterials': [],
                'cast_shadow': False, 'instanceCullCm': [7200, 9000]}]}}
        for t in self.scope['targets']:
            rows[t['baseGroup']['actor']] = {'components': [{'path': t['groupId'] + '.HISM',
                'mesh': t['baseGroup']['mesh'], 'instanceCount': t['baseGroup']['instances'],
                'materials': [native.BARK, t['originalLeafAsset']], 'overrideMaterials': [],
                'orderedInstanceTransformsSha256': t['baseGroup']['transformsSha256'],
                'renderFlags': {'cast_shadow': True}, 'instanceCullCm': [100000, 125000],
                'collision': 'NO_COLLISION', 'navigation': False}], 'detailDensityScaling': False}
        return rows

    def test_effective_override_delta_preserves_bark_unrelated_garden_and_culls(self):
        before = self.witness()
        expected, deltas = native.expected_witness(before, self.scope['targets'])
        self.assertEqual(expected['unrelated'], before['unrelated'])
        self.assertEqual(len(deltas), 23)
        for t in self.scope['targets']:
            old = before[t['baseGroup']['actor']]['components'][0]
            new = expected[t['baseGroup']['actor']]['components'][0]
            self.assertEqual(new['materials'], [native.BARK, t['newLeafAsset']])
            self.assertEqual(new['overrideMaterials'], [None, t['newLeafAsset']])
            self.assertEqual({k: v for k, v in new.items() if k not in ('materials', 'overrideMaterials')},
                             {k: v for k, v in old.items() if k not in ('materials', 'overrideMaterials')})

    def test_foreign_component_override_is_rejected(self):
        before = self.witness()
        before[self.scope['targets'][0]['baseGroup']['actor']]['components'][0]['overrideMaterials'] = ['foreign']
        with self.assertRaisesRegex(RuntimeError, 'foreign'):
            native.expected_witness(before, self.scope['targets'])

    def test_transform_drift_is_rejected(self):
        before = self.witness()
        before[self.scope['targets'][0]['baseGroup']['actor']]['components'][0]['orderedInstanceTransformsSha256'] = 'drift'
        with self.assertRaisesRegex(RuntimeError, 'transforms'):
            native.expected_witness(before, self.scope['targets'])

    def test_live_pin_cannot_accept_byte_tampering(self):
        with tempfile.TemporaryDirectory(prefix='canopy-transmission-pin-') as directory:
            p = Path(directory) / 'source.py'; p.write_text('original')
            witness = native.pin(p)
            self.assertEqual(native.check_pin(witness), p.resolve())
            p.write_text('modified')
            with self.assertRaisesRegex(RuntimeError, 'Pinned bytes changed'):
                native.check_pin(witness)


if __name__ == '__main__':
    unittest.main()
