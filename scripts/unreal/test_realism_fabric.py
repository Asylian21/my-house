import copy
import importlib.util
import json
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('realism_fabric', Path(__file__).with_name('realism-fabric.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class FabricCorrectionTests(unittest.TestCase):
    def source(self, name='real-fabric'):
        return {'name': name, 'color': M.hex_channels(M.SOURCES[name]), 'texture': None,
                'alpha': 1, 'metallic': 0, 'emission': [0, 0, 0]}

    def accepted(self, name='real-fabric'):
        return {'sourceName': name, 'recipe': {'kind': 'woven-linen', 'sourceTexturePatternRemoved': True,
                'solidColorLinear': self.source(name)['color'], 'clothMask': .38, 'normalStrength': .48}}

    def rows(self):
        return [{'pin': pin, 'node': 'old_'+pin, 'role': 'original:'+pin, 'channel': ''}
                for pin in ('Base Color', 'Subsurface Color', 'Clear Coat', 'Normal', 'Roughness', 'Ambient Occlusion')]

    def graph(self):
        attrs = M.validate_attribute_inputs(self.rows())
        return {'nodes': [{'role': 'original:cloth-attributes', 'class': 'MaterialExpressionMakeMaterialAttributes',
                          'values': {}, 'inputs': [[r['pin'], r['role'], ''] for r in self.rows()]},
                         {'role': 'original:cloth-mask', 'class': 'MaterialExpressionConstant', 'values': {'r': .38}, 'inputs': []}],
                'roots': {'BASE_COLOR': ['old-base', ''], 'SUBSURFACE_COLOR': ['old-fuzz', ''], 'ROUGHNESS': ['old-rough', '']},
                'useMaterialAttributes': True, 'attributeRoot': 'MakeMaterialAttributes_0', 'attributes': attrs}

    def test_two_exact_swatches_decode_once_without_changing_weave_recipe(self):
        for name in M.SOURCES:
            source, accepted = self.source(name), self.accepted(name)
            prior = copy.deepcopy((source, accepted))
            recipe = M.recipe(source, accepted)
            self.assertEqual(recipe['preservedClothRecipe'], accepted['recipe'])
            self.assertEqual((source, accepted), prior)
            for raw, ratio, linear in zip(source['color'], recipe['correctionRatio'], recipe['decodedLinear']):
                self.assertAlmostEqual(raw*ratio, linear, places=12)
                self.assertLess(linear, raw)
        self.assertAlmostEqual(M.recipe(self.source('real-upholstery-dark'), self.accepted('real-upholstery-dark'))['decodedLinear'][0], .01599629336550963, places=12)

    def test_changed_and_already_linear_swatches_fail_closed(self):
        source = self.source()
        for altered in ({**source, 'color': [M.decode_srgb(v) for v in source['color']]},
                        {**source, 'texture': '/assets/fabric.jpg'}, {**source, 'alpha': .5},
                        {**source, 'emission': [.1, 0, 0]}, {**source, 'metallic': .1}):
            with self.assertRaises(RuntimeError):
                M.recipe(altered, self.accepted())
        accepted = self.accepted()
        accepted['recipe']['solidColorLinear'] = [M.decode_srgb(v) for v in source['color']]
        with self.assertRaisesRegex(RuntimeError, 'already corrected'):
            M.recipe(source, accepted)

    def test_unrelated_cloth_is_never_selected_by_color(self):
        source = {**self.source(), 'name': 'Living warm sofa | real-interior-upholstery'}
        with self.assertRaisesRegex(RuntimeError, 'Unreviewed cloth'):
            M.recipe(source, self.accepted())

    def test_active_attribute_selection_keeps_cloth_custom_data_pin(self):
        pins = M.validate_attribute_inputs(self.rows())
        self.assertEqual(pins['clearcoat']['node'], 'old_Clear Coat')
        self.assertEqual(M.COLOR_PINS, {'basecolor', 'subsurfacecolor'})
        for missing in ('Clear Coat', 'Base Color', 'Normal'):
            with self.assertRaises(RuntimeError):
                M.validate_attribute_inputs([r for r in self.rows() if r['pin'] != missing])
        with self.assertRaises(RuntimeError):
            M.validate_attribute_inputs(self.rows()+[{'pin': 'BaseColor', 'node': 'duplicate'}])

    def test_disconnected_mask_or_weave_is_rejected(self):
        for pin in ('Clear Coat', 'Roughness', 'Ambient Occlusion', 'Subsurface Color'):
            rows = self.rows()
            next(r for r in rows if r['pin'] == pin)['node'] = None
            with self.assertRaisesRegex(RuntimeError, 'disconnected'):
                M.validate_attribute_inputs(rows)

    def test_protected_graph_allows_only_two_color_edges_and_new_owned_nodes(self):
        before = self.graph()
        after = copy.deepcopy(before)
        for key in M.COLOR_PINS:
            after['attributes'][key]['node'] = 'corrected_'+key
        for row in after['nodes'][0]['inputs']:
            if M.normalize(row[0]) in M.COLOR_PINS:
                row[1] = M.TAG+'corrected-'+M.normalize(row[0])
        after['nodes'].append({'role': M.TAG+'ratio', 'class': 'MaterialExpressionConstant3Vector', 'values': {}, 'inputs': []})
        after['roots']['BASE_COLOR'] = ['new-base', '']
        after['roots']['SUBSURFACE_COLOR'] = ['new-fuzz', '']
        self.assertEqual(M.protected_graph(before), M.protected_graph(after))
        for mutation in ('cloth-mask', 'roughness', 'attributes-flag'):
            bad = copy.deepcopy(after)
            if mutation == 'cloth-mask':
                bad['nodes'][1]['values']['r'] = .1
            elif mutation == 'roughness':
                next(r for r in bad['nodes'][0]['inputs'] if M.normalize(r[0]) == 'roughness')[1] = 'different'
            else:
                bad['useMaterialAttributes'] = False
            self.assertNotEqual(M.protected_graph(before), M.protected_graph(bad))

    def test_accepted_r2_receipts_and_package_hashes_resolve_both_missing_targets(self):
        output = M.ROOT/'output/unreal/realism-20260926-r2'
        if not (output/'model-package.json').is_file():
            self.skipTest('Optional accepted native r2 evidence is unavailable')
        targets, pins = M.load_inputs(output)
        self.assertEqual({r['sourceName'] for r in targets.values()}, set(M.SOURCES))
        self.assertEqual(len(targets), 2)
        self.assertTrue(all(t['originalPackageSha256'] for t in targets.values()))
        self.assertTrue(any(p.endswith('photoreal-import-report.json') for p in pins))

    def test_receipt_target_resolution_rejects_missing_duplicate_and_renamed_slots(self):
        root = M.ROOT/'output/unreal/realism-20260926-r2'
        if not (root/'photoreal-import-report.json').exists():
            self.skipTest('Optional accepted native receipt is unavailable')
        scene, report = M.read(root/'geometry/scene.json'), M.read(root/'photoreal-import-report.json')
        target_slot = next(k for k, v in report['interior']['materials'].items() if v['sourceName'] == 'real-fabric')
        bad = copy.deepcopy(report)
        del bad['interior']['materials'][target_slot]
        with self.assertRaisesRegex(RuntimeError, 'targets missing'):
            M.select_targets(scene, bad)
        bad = copy.deepcopy(report)
        bad['interior']['materials']['unknown-slot'] = bad['interior']['materials'][target_slot]
        with self.assertRaisesRegex(RuntimeError, 'Ambiguous'):
            M.select_targets(scene, bad)


if __name__ == '__main__':
    unittest.main()
