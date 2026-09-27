"""Exercise the one-node fire calibration and its protected native witnesses."""
import copy
import importlib.util
import json
from pathlib import Path
import types
import unittest
from unittest.mock import patch


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).with_name(file))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


M = load('stove_calibration_test_target', 'realism-stove-calibration-material.py')
F = load('stove_graph_cpu_fakes', 'test_realism_stove_materials.py')


class CalibrationTests(unittest.TestCase):
    def fixture(self):
        u = F.fake_unreal()
        u.MaterialProperty.MP_REFRACTION = 'REFRACTION'
        assets = u.EditorAssetLibrary
        actors = F.source_actors(u)
        original_bindings = M.prior.native_sources(u, actors)
        textures = {name: F.Material(M.prior.TEXTURE_PREFIX+'/'+name) for name in M.prior.TEXTURES}
        writer = M.prior.Writer(u, textures)
        materials = {role: writer.create(role) for role in ('chamber', 'logs', 'flames', 'embers')}
        fire = materials['flames']
        del assets.values[fire.path]
        fire.path = M.SOURCE
        assets.values[fire.path] = fire
        for material in assets.values.values():
            material.props.update(translucency_pass='AFTER_DOF', refraction_method='NONE',
                                  translucency_lighting_mode='SURFACE_PER_PIXEL_LIGHTING', disable_depth_test=False)
        for actor in actors:
            for component in actor.get_components_by_class(object):
                old = component.get_editor_property
                component.get_editor_property = lambda key, old=old: (0 if key == 'translucency_sort_priority' else
                    0. if key == 'translucency_sort_distance_offset' else old(key))
        target = {'actor': '/Level/RFIRE', 'component': '/Level/RFIRE.Mesh', 'mesh': '/Game/RFIRE_FLAMES',
                  'materials': [M.SOURCE], 'materialRole': 'flames', 'sourceIds': ['DOM_00564', 'DOM_00565', 'DOM_00566']}
        bound = [fire]
        props = {'static_mesh': F.Material(target['mesh']), 'translucency_sort_priority': 0, 'translucency_sort_distance_offset': 0.}
        component = types.SimpleNamespace(get_path_name=lambda: target['component'], get_num_materials=lambda: 1,
            get_material=lambda slot: bound[slot], set_material=lambda slot, material: bound.__setitem__(slot, material),
            get_editor_property=lambda key: props[key])
        actors.append(types.SimpleNamespace(get_path_name=lambda: target['actor'], get_components_by_class=lambda cls: [component]))
        def duplicate(source, destination):
            material = copy.deepcopy(assets.values[source])
            material.path = destination+'.'+destination.rsplit('/', 1)[1]
            assets.values[material.path] = material
            return material
        assets.duplicate_asset = duplicate
        originals = {r['material']: M.snapshot(u, assets.load_asset(r['material'])) for r in original_bindings.values()}
        graphs = {m.path: M.snapshot(u, m) for m in materials.values()}
        material_readback = {'status': 'saved-reloaded-validated', 'originalGraphs': originals, 'graphs': graphs,
                            'sourceBindings': original_bindings, 'materials': {role: mat.path for role, mat in materials.items()}}
        stove = {'status': 'realism-stove-validated', 'savedReloaded': True, 'protectedContentUnchanged': True,
                 'originalMaterialAssetsPreserved': True, 'savedMaterialReadback': material_readback,
                 'objects': {'RFIRE_FLAMES': target}}
        return u, actors, stove, target, graphs[M.SOURCE], component, props

    def apply(self, fixture):
        u, actors, stove, target, graph, component, props = fixture
        with patch.object(M, 'preflight', return_value=(stove, target, graph, {})):
            return M.apply(u, actors, M.ROOT/'output/unreal/cpu-only-calibration-test')

    def test_only_the_exact_terminal_multiplier_is_replaced(self):
        code = M.prior.emission_hlsl()
        calibrated = M.calibrated_code(code)
        self.assertEqual(calibrated.replace('*512.0;', '*3.0;'), code)
        self.assertEqual(calibrated.count('*512.0;'), 1)
        for altered in (code.replace('0.12', '0.13'), code.replace('*3.0;', '*4.0;'), calibrated, code+'\n'):
            with self.assertRaisesRegex(RuntimeError, 'exact reviewed'):
                M.calibrated_code(altered)

    def test_expected_graph_keeps_all_other_nodes_edges_and_flags(self):
        _, _, _, _, original, _, _ = self.fixture()
        saved = copy.deepcopy(original)
        expected = M.expected_graph(original)
        self.assertEqual(original, saved)
        changed = [(a, b) for a, b in zip(original['nodes'], expected['nodes']) if a != b]
        self.assertEqual(len(changed), 1)
        self.assertEqual(changed[0][0]['role'], M.ROLE)
        self.assertEqual(original['flags'], expected['flags'])
        self.assertEqual(original['roots'], expected['roots'])
        ambiguous = copy.deepcopy(original)
        ambiguous['nodes'].append(copy.deepcopy(changed[0][0]))
        with self.assertRaisesRegex(RuntimeError, 'ambiguous'):
            M.expected_graph(ambiguous)

    def test_apply_creates_one_clone_rebinds_one_slot_and_preserves_sources(self):
        fixture = self.fixture()
        u, actors, stove, target, graph, component, props = fixture
        original_asset = u.EditorAssetLibrary.load_asset(M.SOURCE)
        report = self.apply(fixture)
        self.assertEqual(len(report['ownedAssets']), 1)
        self.assertEqual(len(report['bindingChanges']), 1)
        self.assertEqual(report['bindingChanges'][0]['before'], M.SOURCE)
        self.assertEqual(report['bindingChanges'][0]['component'], target['component'])
        self.assertEqual(M.snapshot(u, original_asset), graph)
        self.assertEqual(report['diagnosticsBefore'], report['diagnosticsAfter'])
        self.assertFalse(report['glassModified'])
        self.assertFalse(report['emberModified'])
        self.assertTrue(M.verify(u, actors, report)['savedReloaded'])

    def test_shared_original_binding_fails_before_any_duplicate(self):
        fixture = self.fixture()
        u, actors, stove, target, graph, component, props = fixture
        other = copy.copy(component)
        other.get_path_name = lambda: '/Level/Unexpected.Mesh'
        actors.append(types.SimpleNamespace(get_path_name=lambda: '/Level/Unexpected', get_components_by_class=lambda cls: [other]))
        with patch.object(u.EditorAssetLibrary, 'duplicate_asset', side_effect=AssertionError('must not clone')):
            with self.assertRaisesRegex(RuntimeError, 'shared beyond'):
                self.apply(fixture)

    def test_saved_graph_rejects_changed_texture_uv_tint_or_blend(self):
        for target in ('texture', 'uv', 'tint', 'blend'):
            fixture = self.fixture()
            u, actors, _, _, _, component, _ = fixture
            report = self.apply(fixture)
            material = component.get_material(0)
            by_role = {n.props['desc']: n for n in material.nodes}
            if target == 'texture':
                by_role[M.prior.TAG+'atlas-sample-0'].props['texture'] = F.Material('/WrongTexture')
            elif target == 'uv':
                by_role[M.prior.TAG+'flame-card-uv'].props['v_tiling'] = -1
            elif target == 'tint':
                by_role[M.ROLE].props['code'] = by_role[M.ROLE].props['code'].replace('0.12', '0.13')
            else:
                material.props['blend_mode'] = 'OPAQUE'
            with self.assertRaisesRegex(RuntimeError, 'beyond the single'):
                M.verify(u, actors, report)

    def test_saved_probe_rejects_changed_sort_refraction_or_translucency_pass(self):
        for target in ('sort', 'pass', 'refraction'):
            fixture = self.fixture()
            u, actors, _, _, _, component, props = fixture
            report = self.apply(fixture)
            if target == 'sort':
                props['translucency_sort_priority'] = 1
            elif target == 'pass':
                component.get_material(0).props['translucency_pass'] = 'BEFORE_DOF'
            else:
                component.get_material(0).props['refraction_method'] = 'INDEX_OF_REFRACTION'
            with self.assertRaisesRegex(RuntimeError, 'diagnostics changed'):
                M.verify(u, actors, report)

    def test_saved_original_glass_or_emission_change_is_rejected(self):
        for source in ('glass', 'flames'):
            fixture = self.fixture()
            u, actors, _, _, _, _, _ = fixture
            report = self.apply(fixture)
            path = report['glassTarget']['material'] if source == 'glass' else M.SOURCE
            u.EditorAssetLibrary.load_asset(path).props['two_sided'] = not u.EditorAssetLibrary.load_asset(path).props['two_sided']
            with self.assertRaisesRegex(RuntimeError, 'original stove graph'):
                M.verify(u, actors, report)

    def test_inherited_native_package_and_copied_asset_pins_fail_closed(self):
        _, _, stove, _, _, _, _ = self.fixture()
        output = M.ROOT/'output/unreal/cpu-calibration-receiver'
        donor = M.ROOT/'output/unreal/cpu-calibration-donor'
        original = donor/'Project/BreziTwin/Content/Brezi/Realism/Stove/Materials/M_Stove_Flames.uasset'
        copied = output/'Project/BreziTwin/Content/Brezi/Realism/Stove/Materials/M_Stove_Flames.uasset'
        package = {'project': str(donor/'Project/BreziTwin'), 'stove': {'reportSha256': 'r'},
                   'inputs': {str(donor/'realism-stove-report.json'): 'r', str(original): 'a'}}
        inheritance = {'status': 'verified-scene-inherited', 'donor': str(donor),
                       'receiptPins': {str(donor/'model-package.json'): 'p'}}
        documents = {output/'performance-source.json': inheritance, donor/'model-package.json': package,
                     donor/'realism-stove-report.json': stove}
        hashes = {output/'performance-source.json': 'i', donor/'model-package.json': 'p', donor/'realism-stove-report.json': 'r',
                  original: 'a', copied: 'a'}
        with patch.object(M, 'read', side_effect=lambda p: copy.deepcopy(documents[Path(p)])), patch.object(M, 'sha', side_effect=lambda p: hashes[Path(p)]):
            self.assertEqual(M.preflight(output)[1], stove['objects']['RFIRE_FLAMES'])
            hashes[copied] = 'altered'
            with self.assertRaisesRegex(RuntimeError, 'asset bytes differ'):
                M.preflight(output)
            hashes[copied] = 'a'
            package['stove']['reportSha256'] = 'wrong'
            with self.assertRaisesRegex(RuntimeError, 'not pinned'):
                M.preflight(output)


if __name__ == '__main__':
    unittest.main()
