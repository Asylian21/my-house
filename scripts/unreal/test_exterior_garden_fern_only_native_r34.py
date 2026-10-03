"""CPU counterfactual, package and full-F32 native decoder guards for R34."""
import ast
import copy
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts/unreal'/file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


g = module('r34_native_scope_fixture', 'exterior-garden-fern-only-native-guards-r34.py')
n = module('r34_native_decoder_fixture', 'exterior-garden-fern-only-native-r34.py')


class SourceDescription:
    def __init__(self, row, change=None):
        self.row, self.change = row, change

    def get_triangle_count(self): return self.row['triangles']
    def get_triangle_vertex_instance(self, triangle, corner):
        if self.change == 'reverse' and triangle.id_value == 0:
            corner = (0, 2, 1)[corner]
        return (triangle.id_value, corner)
    def get_vertex_instance_vertex(self, value): return value
    def get_vertex_position(self, value):
        point = list(self.row['expectedNativeVerticesCm'][self.row['indices'][3*value[0]+value[1]]])
        if self.change == 'position' and value == (0, 0): point[0] += .000001
        return SimpleNamespace(**dict(zip('xyz', point)))
    def get_vertex_instance_uv(self, value, channel):
        assert channel == 0
        uv = list(self.row['uv0'][self.row['indices'][3*value[0]+value[1]]])
        if self.change == 'uv' and value == (0, 0): uv[0] += .000001
        return SimpleNamespace(**dict(zip('xy', uv)))


class SourceMesh:
    def __init__(self, row, change=None): self.row, self.change = row, change
    def get_num_lods(self): return 1
    def get_num_triangles(self, lod): return self.row['triangles']
    def get_num_sections(self, lod): return 1
    def get_path_name(self): return g.PREFIX+'/Geometry/StaticMeshes/'+self.row['exportName']+'.'+self.row['exportName']
    def get_editor_property(self, name): return {'static_materials': [object()], 'has_navigation_data': False}[name]
    def get_static_mesh_description(self, lod): return SourceDescription(self.row, self.change)


class NativeScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = g.source_bundle()
        cls.source, cls.base = cls.bundle['source'], cls.bundle['base']
        cls.clone = g.validate_clone(cls.base)
        cls.ref = cls.bundle['reference']
        cls.u = SimpleNamespace(TriangleID=lambda id_value: SimpleNamespace(id_value=id_value))
        settings = {'use_full_precision_u_vs': True, 'generate_lightmap_u_vs': False,
                    'recompute_normals': False, 'recompute_tangents': True, 'remove_degenerates': False}
        cls.subsystem = SimpleNamespace(get_lod_build_settings=lambda mesh, lod: SimpleNamespace(get_editor_property=lambda k: settings[k]))

    def test_actual_base_and_independent_clone(self):
        self.assertEqual(self.base['reportPin']['sha256'], g.source_guard.BASE_SHA)
        self.assertEqual(self.clone['sha256'], '5739620b8bf23812c0bbc03e99e997a72bb177204f95ad9f8bc28a9a373a7729')
        self.assertEqual(len(self.base['witness']), 5351)

    def test_only_two_low_group_fields_change(self):
        before = self.base['witness']
        expected = g.expected_original(before, self.bundle['groups'], self.ref['controls'], self.source['proposal'])
        changed = {k for k in before if expected[k] != before[k]}
        permitted = {self.bundle['groups'][r['groupId']]['actor'] for r in self.source['proposal']['sourceGroupFilters']}
        self.assertEqual(changed, permitted)
        for actor in changed:
            altered = copy.deepcopy(before[actor])
            altered['components'][0]['instanceCount'] = expected[actor]['components'][0]['instanceCount']
            altered['components'][0]['orderedInstanceTransformsSha256'] = expected[actor]['components'][0]['orderedInstanceTransformsSha256']
            self.assertEqual(altered, expected[actor])
        for group in self.bundle['groups'].values():
            if any(r['id'].startswith('garden_ornamental_') for r in group['rows']): self.assertEqual(before[group['actor']], expected[group['actor']])

    def test_retained437_raw_order_seed_custom_and_flower_controls(self):
        expected = g.source_guard.retained_controls(self.ref)
        self.assertEqual(sum(len(v['rootIds']) for v in expected.values()), 437)
        retained_ids = {r for v in expected.values() for r in v['rootIds']}
        self.assertTrue(set(self.source['proposal']['preservedOrnamentalRootIds']).issubset(retained_ids))
        for actor, control in self.ref['controls'].items():
            observed = expected[actor]
            self.assertEqual(observed['mainRandomSeed'], control['mainRandomSeed'])
            self.assertEqual(observed['customData'], control['customData'])
            indices = [i for i, identity in enumerate(control['rootIds']) if identity in retained_ids]
            self.assertEqual(observed['storedMatrices'], [control['storedMatrices'][i] for i in indices])
            self.assertEqual(observed['recoveredValues'], [control['recoveredValues'][i] for i in indices])

    def packages(self):
        return g.package_paths(self.source['models'])+[g.PREFIX+'/Fern/Materials/Original']+[g.PREFIX+'/Fern/Textures/'+r for r in ('Albedo','Normal','ARM','Alpha')]

    def inventory(self):
        result = copy.deepcopy(self.base['content'])
        result['Brezi/Maps/Brezi.umap'] = {'sha256': 'b'*64, 'bytes': 1}
        result.update({p.removeprefix('/Game/')+'.uasset': {'sha256': 'a'*64, 'bytes': 1} for p in self.packages()})
        return result

    def test_exact11_packages_and_map_only(self):
        proof = g.validate_content(self.base['content'], self.inventory(), self.packages())
        self.assertEqual(proof['newPackages'], 11)
        self.assertEqual(proof['savedContentFiles'], 4071)
        self.assertEqual(proof['changedOriginalFiles'], ['Brezi/Maps/Brezi.umap'])

    def test_foreign_package_rejected(self):
        after = self.inventory(); after['Brezi/Other.uasset'] = {'sha256': 'c'*64, 'bytes': 1}
        with self.assertRaisesRegex(RuntimeError, 'Only exact'): g.validate_content(self.base['content'], after, self.packages())

    def test_original_asset_change_rejected(self):
        after = self.inventory(); key = next(k for k in self.base['content'] if k.endswith('.uasset'))
        after[key] = {'sha256': 'c'*64, 'bytes': 1}
        with self.assertRaisesRegex(RuntimeError, 'outside own map'): g.validate_content(self.base['content'], after, self.packages())

    def test_full3848_native_corner_decoder(self):
        proofs = [n.mesh_proof(self.u, SourceMesh(row), row, self.subsystem) for row in self.source['models'].values()]
        self.assertEqual(sum(r['triangles'] for r in proofs), 3848)
        self.assertTrue(all(r['fullOrderedNativeF32PositionUV0WindingVerified'] for r in proofs))
        self.assertTrue(all(r['nativeNormalTangentReadbackAvailable'] is False and r['nativeTangentGenerationNumericallyVerified'] is False for r in proofs))

    def decoder_reject(self, change):
        row = self.source['models']['fern_02_a']
        with self.assertRaisesRegex(RuntimeError, 'Full original native F32'):
            n.mesh_proof(self.u, SourceMesh(row, change), row, self.subsystem)

    def test_native_winding_rejected(self): self.decoder_reject('reverse')
    def test_native_uv_change_rejected(self): self.decoder_reject('uv')
    def test_native_position_change_rejected(self): self.decoder_reject('position')


if __name__ == '__main__':
    unittest.main(verbosity=2)
