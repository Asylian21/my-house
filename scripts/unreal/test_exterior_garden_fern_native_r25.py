"""R25 CPU source/receipt fixtures, never native saved or appearance evidence."""
import copy
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts/unreal'/filename)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


guard = load('r25_native_test_guard', 'exterior-garden-fern-guards-r25.py')
native = load('r25_native_test_entry', 'exterior-garden-fern-native-r25.py')
maps = load('r25_native_test_maps', 'exterior-garden-fern-materials-r25.py')


def graph_fixture(textures):
    tag = maps.TAG+maps.KEY+':'
    roots = {'BASE_COLOR': [tag+'albedo', 'RGB'], 'NORMAL': [tag+'normalGL', 'RGB'],
        'ROUGHNESS': [tag+'ARM', 'G'], 'METALLIC': [tag+'metallic-factor', ''],
        'SPECULAR': [tag+'dielectric-specular', ''], 'OPACITY_MASK': [tag+'alpha', 'R'],
        'SUBSURFACE_COLOR': [tag+'transmission', ''], 'AMBIENT_OCCLUSION': None,
        'WORLD_POSITION_OFFSET': None}
    nodes = [{'role': tag+'uv', 'class': 'MaterialExpressionTextureCoordinate',
        'values': {'coordinate_index': 0, 'u_tiling': 1., 'v_tiling': 1.}, 'inputs': []}]
    for role, path in textures.items():
        sampler = 'NORMAL' if role == 'normalGL' else 'MASKS' if role in ('ARM', 'alpha') else 'COLOR'
        nodes.append({'role': tag+role, 'class': 'MaterialExpressionTextureSample',
            'values': {'texture': path, 'sampler_type': '<MaterialSamplerType.SAMPLERTYPE_'+sampler+': 0>'},
            'inputs': [['UVs', tag+'uv', ''], ['Tex', None, None], ['Apply View MipBias', None, None]]})
    for role, value in (('metallic-zero', 0.), ('dielectric-specular', .5), ('strength', .08)):
        nodes.append({'role': tag+role, 'class': 'MaterialExpressionConstant',
            'values': {'r': maps.f32(value)}, 'inputs': []})
    for role, a, output, b in (('metallic-factor', 'ARM', 'B', 'metallic-zero'),
                              ('transmission', 'albedo', 'RGB', 'strength')):
        nodes.append({'role': tag+role, 'class': 'MaterialExpressionMultiply', 'values': {},
            'inputs': [['A', tag+a, output], ['B', tag+b, '']]})
    return {'roots': roots, 'nodes': nodes}


class FernNativeCpuGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = guard.source()
        cls.base = guard.saved_native_base()
        cls.before = cls.base['witness']
        cls.actor, cls.component = cls.base['targetActor'], cls.base['targetComponent']
        cls.mesh = guard.PREFIX+'/Geometry/StaticMeshes/'+guard.MODEL+'_LOD0.'+guard.MODEL+'_LOD0'
        cls.material = guard.PREFIX+'/Materials/M_fixture.M_fixture'
        # Constructed serialized Transform: this fixture grants no native transform proof.
        cls.value = [cls.bundle['root']['positionCm'], [0., 0., 0., 1.],
                     cls.bundle['plan']['placementProposal']['scale']]
        cls.textures = {role: guard.PREFIX+'/Textures/T_fixture_'+role+'.T_fixture_'+role
                        for role in ('albedo', 'normalGL', 'ARM', 'alpha')}

    def expected(self):
        return guard.expected_witness(self.before, self.actor, self.component, self.base['oldMesh'],
                                      self.mesh, self.material, self.value)

    def test_actual_source_and_saved_base_closure(self):
        self.assertEqual(self.base['report']['nativeProcessId'], 50344)
        self.assertEqual((len(self.before), len(self.base['content']), len(self.base['protected'])),
                         (5346, 4049, 132))
        self.assertEqual(self.bundle['row']['triangles'], 2384)
        self.assertLess(self.bundle['plan']['placementProposal']['abovePivotHeightCm'], 36)
        self.assertFalse(self.bundle['plan']['audit']['nativeApplied'])
        maps.validate_recipe(self.bundle['plan'])
        native.primary_api()
        self.assertEqual(guard.validate_clone(self.base)['path'],
                         str(guard.NATIVE_OUTPUT/'garden-fern-project-clone.json'))

    def test_original_attribute_bytes_and_glb_tamper(self):
        with tempfile.TemporaryDirectory(prefix='brezi-r25-cpu-fixture-') as directory:
            path = Path(directory)/'fern.glb'
            proof = guard.write_glb(path, self.bundle)
            self.assertTrue(proof['originalPositionNormalUvIndexBytesPreserved'])
            raw = bytearray(path.read_bytes())
            size, _ = struct.unpack_from('<II', raw, 12)
            raw[20+size+8] ^= 1
            path.write_bytes(raw)
            with self.assertRaisesRegex(RuntimeError, 'attribute/index bytes changed'):
                guard.decode_glb(path, self.bundle)

    def test_single_root_counterfactual_preserves_every_other_field(self):
        expected = self.expected()
        self.assertEqual(guard.verify_counterfactual(self.before, expected, self.actor, self.component,
            self.base['oldMesh'], self.mesh, self.material, self.value), expected)
        original = guard.component(self.before, self.actor, self.component)
        changed = guard.component(expected, self.actor, self.component)
        fields = {key for key in original if original[key] != changed[key]}
        self.assertEqual(fields, {'mesh', 'materials', 'orderedInstanceTransformsSha256'})
        self.assertEqual(original['instanceCullCm'], [14400, 18000])

    def test_foreign_actor_or_cull_change_rejected(self):
        for mode in ('foreign', 'cull'):
            saved = self.expected()
            if mode == 'foreign':
                actor = next(k for k in saved if k != self.actor)
                saved[actor]['hidden'] = not saved[actor]['hidden']
            else:
                guard.component(saved, self.actor, self.component)['instanceCullCm'][1] += 1
            with self.assertRaisesRegex(RuntimeError, 'counterfactual'):
                guard.verify_counterfactual(self.before, saved, self.actor, self.component,
                    self.base['oldMesh'], self.mesh, self.material, self.value)

    def test_wrong_base_or_unverified_status_rejected(self):
        for field, value in (('owner', 'scripts/unreal/exterior-realism-integration-native-r22.py'),
                             ('savedMapUnloadedReloaded', False), ('scopedMaterialGraphs', 55)):
            report = copy.deepcopy(self.base['report'])
            report[field] = value
            with self.assertRaises(RuntimeError):
                guard.validate_base_header(report)

    def test_material_exact_masked_graph_fixture(self):
        graph = graph_fixture(self.textures)
        proof = maps.check_graph(graph, self.textures)
        self.assertTrue(proof['normalizedOriginalAlphaRToOpacityMask'])
        for mode in ('alpha-a', 'ao', 'uv1', 'extra-node'):
            changed = copy.deepcopy(graph)
            if mode == 'alpha-a':
                changed['roots']['OPACITY_MASK'][1] = 'A'
            elif mode == 'ao':
                changed['roots']['AMBIENT_OCCLUSION'] = [maps.TAG+maps.KEY+':ARM', 'R']
            elif mode == 'uv1':
                changed['nodes'][0]['values']['coordinate_index'] = 1
            else:
                changed['nodes'].append(copy.deepcopy(changed['nodes'][0]))
            with self.assertRaises(RuntimeError):
                maps.check_graph(changed, self.textures)

    def test_source_precision_or_rehashed_recipe_tamper_rejected(self):
        for field, value in (('alphaSourceBits', 8), ('cutoff', .25)):
            changed = copy.deepcopy(self.bundle['plan'])
            changed['materialProposal']['explicitAlpha'][field] = value
            with self.assertRaisesRegex(RuntimeError, 'Exact typed'):
                maps.validate_recipe(changed)

    def test_enum_prefix_resolution_is_narrow(self):
        class Group:
            MSM_TWO_SIDED_FOLIAGE = 'known'
            FOREIGN_TWO_SIDED_FOLIAGE = 'foreign'
        class UnrealFixture:
            MaterialShadingModel = Group
        self.assertEqual(maps.enum(UnrealFixture, 'MaterialShadingModel', 'TWOSIDEDFOLIAGE'), 'known')
        Group.TWO_SIDED_FOLIAGE = 'ambiguous'
        with self.assertRaisesRegex(RuntimeError, 'ambiguous'):
            maps.enum(UnrealFixture, 'MaterialShadingModel', 'TWOSIDEDFOLIAGE')

    def test_serialization_equality_rejects_signed_zero_and_one_ulp(self):
        native.numeric_exact([[1., 0.]], [[1., 0.]], 'fixture')
        for value in (-0.,):
            with self.assertRaisesRegex(RuntimeError, 'fixture'):
                native.numeric_exact([[1., value]], [[1., 0.]], 'fixture')
        with self.assertRaisesRegex(RuntimeError, 'fixture'):
            native.numeric_exact([1.0000000000000002], [1.], 'fixture')

    def test_exact_package_scope_rejects_source_views_or_extra_asset(self):
        before = self.base['content']
        packages = [guard.PREFIX+'/'+str(i) for i in range(9)]
        after = copy.deepcopy(before)
        after['Brezi/Maps/Brezi.umap'] = {'sha256': 'fixture-changed-map', 'bytes': 1}
        after.update({p.removeprefix('/Game/')+'.uasset': {'sha256': 'fixture', 'bytes': 1}
                      for p in packages})
        self.assertEqual(guard.validate_content(before, after, packages)['newUassetPackages'], 9)
        for mode in ('views', 'extra'):
            changed = copy.deepcopy(after)
            if mode == 'views':
                changed['Brezi/Data/viewpoints.json'] = {'sha256': 'foreign', 'bytes': 1}
            else:
                changed['Brezi/foreign.uasset'] = {'sha256': 'foreign', 'bytes': 1}
            with self.assertRaises(RuntimeError):
                guard.validate_content(before, changed, packages)


if __name__ == '__main__':
    print('R25 CPU fixtures/source receipts only; no native saved/appearance/performance evidence.', flush=True)
    unittest.main(verbosity=2)
