"""Bounded draft-contract adversaries; no frozen source producer or Unreal calls."""
import copy
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(name, file):
    spec = importlib.util.spec_from_file_location(name, HERE/file)
    result = importlib.util.module_from_spec(spec);spec.loader.exec_module(result)
    return result


g = load('r38_draft_fixture_guard', 'exterior-context-yard-soft-coherence-guards-r38-draft.py')
m = load('r38_draft_fixture_materials', 'exterior-context-yard-soft-coherence-materials-r38-draft.py')
n = load('r38_draft_fixture_native', 'exterior-context-yard-soft-coherence-native-r38-draft.py')


class NoUnrealAccess:
    def __getattr__(self, name):
        raise AssertionError('Unbound draft touched Unreal: '+name)


class DraftContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = g.load_contract()

    def test_pending_binding_cannot_be_promoted_by_an_acceptance_flag(self):
        bundle = self.bundle;row = n.describe_draft(bundle)
        for key in g.DRAFT_BINDING:
            self.assertIsNone(row[key])
        for value in (None, {}, {'selectedNativeBase': 'invented', 'imageAccepted': True}):
            with self.assertRaisesRegex(RuntimeError, 'NEW finalized immutable'):
                n.apply_overlay(NoUnrealAccess(), {}, bundle, value)
            with self.assertRaises(RuntimeError):
                m.build_materials(NoUnrealAccess(), bundle, value, None, None)
            with self.assertRaises(RuntimeError):
                m.verify_materials(NoUnrealAccess(), bundle, value, {}, None, None)

    def test_default_anisotropic_shared_wrap_and_mips_rejected(self):
        for key, value in [('filter', 'TF_DEFAULT'), ('filter', 'TF_TRILINEAR'),
            ('samplerSource', 'SSM_WRAP_WORLD_GROUP_SETTINGS'), ('addressX', 'TA_WRAP'),
            ('mipGenSettings', 'TMGS_FROM_TEXTURE_GROUP'), ('compressionNone', False),
            ('downscaleDefault', 0.0), ('nativeGpuPixelFormatVerified', True)]:
            policy = copy.deepcopy(g.SAMPLING_POLICY);policy[key] = value
            with self.assertRaises(ValueError):g.validate_policy(policy)

    def test_original_metric_phase_and_normal_graph_unchanged(self):
        for field in ('values', 'inputs'):
            graphs = copy.deepcopy(self.bundle['graphs'])
            row = next(x for x in graphs['backdrop']['nodes'] if x['role'].startswith('BreziExterior:') and x[field])
            if field == 'inputs': row[field][0][1] = 'foreign-camera-phase'
            else: row[field][next(iter(row[field]))] = 'changed'
            with self.assertRaises(ValueError):g.validate_graphs(self.bundle['originalGraph'], graphs, self.bundle['ditherNodes'])

    def test_endpoints_must_share_the_same_world_phase(self):
        graphs = copy.deepcopy(self.bundle['graphs'])
        row = next(x for x in graphs['substrate']['nodes'] if x['role'] == g.TAG+'common-color')
        row['inputs'][1][1] = 'foreign-unregistered-scan'
        with self.assertRaises(ValueError):g.validate_graphs(self.bundle['originalGraph'], graphs, self.bundle['ditherNodes'])

    def test_inherited_uv1_dither_route_cannot_be_removed_or_rerouted(self):
        for mutation in ('remove', 'uv', 'channel'):
            graphs = copy.deepcopy(self.bundle['graphs']);rows = graphs['substrate']['nodes']
            node = next(x for x in rows if x['role'].endswith(':coverage-r'))
            if mutation == 'remove': rows.remove(node)
            elif mutation == 'uv': node['inputs'][0][1] = 'BreziExterior:world-position'
            else: node['values']['r'] = False;node['values']['g'] = True
            with self.assertRaises(ValueError):g.validate_graphs(self.bundle['originalGraph'], graphs, self.bundle['ditherNodes'])

    def test_only_two_slot0_material_and_override_fields_change(self):
        # Historic witnesses exercise the pure patch kernel; they are not an
        # accepted current base or fresh native readback.
        targets = self.bundle['plan']['targets']
        before = {g.ACTOR197: copy.deepcopy(targets['backdropOriginalActor197']['historicalWitness']),
            'mapped-substrate-only-fixture': copy.deepcopy(targets['substrateDonorActor668']['historicalWitness']),
            'protected-lawn-control': {'components': [], 'seed': 129, 'transform': [[0, 0, 0]], 'rootCount': 8949}}
        refs = {}
        for key, actor in [('backdrop', g.ACTOR197), ('substrate', 'mapped-substrate-only-fixture')]:
            c = before[actor]['components'][0]
            refs[key] = {'actor': actor, 'component': c['name'], 'originalMesh': c['mesh'], 'originalMaterial': c['materials'][0]}
        expected = g.counterfactual_two_slots(before, refs)
        restored = copy.deepcopy(expected)
        for key, target in refs.items():
            restored[target['actor']]['components'][0]['materials'] = before[target['actor']]['components'][0]['materials']
            restored[target['actor']]['components'][0]['overrideMaterials'] = before[target['actor']]['components'][0]['overrideMaterials']
        self.assertEqual(restored, before)
        self.assertEqual(expected['protected-lawn-control'], before['protected-lawn-control'])
        self.assertEqual(expected['mapped-substrate-only-fixture']['components'][0]['overrideMaterials'], [g.ASSETS['substrate']])
        bad = copy.deepcopy(refs);bad['substrate']['originalMesh'] = 'guessed-mesh'
        with self.assertRaises(ValueError):g.counterfactual_two_slots(before, bad)

    def test_native_policy_readback_rejects_group_resizing_and_filter_alias(self):
        enums = {k: 'enum-'+k for k in ('compression', 'mips', 'filter', 'address', 'powerOfTwo', 'encoding')}
        row = {'asset': g.MASK_ASSET, 'values': m.expected_texture_values(enums), 'size': [2048, 2048],
            'sourceEncoding': 'enum-encoding', 'downscale': {'default': 1., 'perPlatform': {}}, 'alphaCoverageThresholds': [0., 0., 0., 0.]}
        m.validate_mask_snapshot(row, enums)
        for field, value in [('size', [1024, 1024]), ('downscale', {'default': 1., 'perPlatform': {'Mac': 2.}})]:
            bad = copy.deepcopy(row);bad[field] = value
            with self.assertRaises(ValueError):m.validate_mask_snapshot(bad, enums)
        bad = copy.deepcopy(row);bad['values']['filter'] = 'enum-group-default'
        with self.assertRaises(ValueError):m.validate_mask_snapshot(bad, enums)

    def test_exact_enum_names_allow_underscore_reflection_only(self):
        class Good:
            TF_BILINEAR = 4
        class Wrong:
            TF_TRILINEAR = 4
        self.assertEqual(m.exact_enum(Good, 'TF_Bilinear'), 4)
        with self.assertRaises(ValueError):m.exact_enum(Wrong, 'TF_BILINEAR')

    def test_native_adaptation_only_changes_new_mask_mip_mode(self):
        native = copy.deepcopy(self.bundle['nativeGraphs'])
        g.validate_native_graphs(self.bundle['graphs'], native)
        for key, graph in native.items():
            mask = next(x for x in graph['nodes'] if x['role'] == g.TAG+'fixed-world-yard-mask')
            self.assertEqual(mask['values']['mip_value_mode'], '<TextureMipValueMode.TMVM_NONE: 0>')
            mask['values']['mip_value_mode'] = '<TextureMipValueMode.TMVM_DERIVATIVE: 3>'
            self.assertEqual(graph, self.bundle['graphs'][key])
        with self.assertRaises(ValueError):g.validate_native_graphs(self.bundle['graphs'], native)


if __name__ == '__main__':
    unittest.main()
