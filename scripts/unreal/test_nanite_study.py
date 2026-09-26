"""Portable study boundaries and source witness tests; no Unreal process."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as N
import unittest
from unittest.mock import patch

from nanite_study_policy import asset_file, asset_path, eligible_record, ranked_records, validate_changes, validate_derived_bounds

SPEC = importlib.util.spec_from_file_location('nanite_study', Path(__file__).with_name('nanite-study.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


def record(identity='DOM_00001'):
    return {'id': identity, 'name': 'decor', 'group': 'Interior', 'enabled': True, 'triangles': 12, 'instances': 1,
            'metadata': {}, 'materialSlots': ['opaque'], 'boundsMm': {'min': [0, 0, 0], 'max': [2, 2, 2]}}


class Description:
    def __init__(self):
        self.position = 1.25
        self.uv = .625
        self.group = 7
        self.valid = True

    def get_triangle_count(self): return 1
    def is_triangle_valid(self, tri): return self.valid and tri.id_value == 0
    def get_triangle_vertex_instance(self, tri, corner): return N(id_value=corner)
    def is_vertex_instance_valid(self, instance): return True
    def get_vertex_instance_vertex(self, instance): return instance
    def is_vertex_valid(self, vertex): return True
    def get_vertex_position(self, vertex): return N(x=self.position + vertex.id_value, y=2., z=3.)
    def get_vertex_instance_uv(self, instance, channel): return N(x=self.uv + channel, y=instance.id_value)
    def get_triangle_polygon_group(self, tri): return N(id_value=self.group)
    def get_vertex_instance_count(self): return 3
    def get_vertex_count(self): return 3


class NaniteStudyTests(unittest.TestCase):
    def test_transient_preflight_restores_rejected_settings_without_saving_assets(self):
        class Settings:
            def __init__(self, values): self.values = dict(values)
            def get_editor_property(self, key): return self.values[key]
            def set_editor_property(self, key, value): self.values[key] = value
            def export_text(self): return repr(sorted(self.values.items()))
        class Mesh:
            def __init__(self, bad):
                self.bad = bad
                self.values = {'enabled': False, 'keep_percent_triangles': 1., 'trim_relative_error': 0.,
                               'fallback_target': 'auto', 'fallback_percent_triangles': .5, 'fallback_relative_error': 1.}
            def get_editor_property(self, key):
                assert key == 'nanite_settings'; return Settings(self.values)
            def set_editor_property(self, key, value):
                assert key == 'nanite_settings'; self.values = dict(value.values)
        meshes = {'good': Mesh(False), 'bad': Mesh(True)}
        before = [[1., 2., 3.], [1., 1., 1.]]
        rows = [{'sourceId': name, 'asset': name, 'witness': {'source': 'exact'}, 'derivedBoundsBeforeCm': before}
                for name in meshes]
        u = N(load_asset=meshes.get, NaniteFallbackTarget=N(PERCENT_TRIANGLES='percent'))
        def bounds(mesh):
            return [[1.01, 2., 3.], [1., 1., 1.]] if mesh.bad and mesh.values['enabled'] else before
        excluded = {}
        with patch.object(M, 'finish'), patch.object(M, 'mesh_witness', return_value={'source': 'exact'}), \
                patch.object(M, 'derived_bounds', side_effect=bounds):
            accepted = M.preflight(u, None, None, rows, excluded)
        self.assertEqual([row['sourceId'] for row in accepted], ['good'])
        self.assertTrue(meshes['good'].values['enabled'])
        self.assertFalse(meshes['bad'].values['enabled'])
        self.assertEqual(meshes['bad'].values['fallback_target'], 'auto')
        self.assertEqual(meshes['bad'].values['fallback_percent_triangles'], .5)
        self.assertFalse(excluded['bad']['assetSaved'])

    def test_derived_bounds_allow_only_float32_roundoff_and_absolute_micrometre_cap(self):
        before = [[1209.1000366210938, 0., 86.45000076293945], [1., 1., 1.]]
        after = [[1209.10009765625, 0., 86.44999694824219], [1., 1., 1.]]
        self.assertEqual(validate_derived_bounds(before, after), .00006103515625)
        self.assertEqual(validate_derived_bounds([[1., 0., 0.], [1., 1., 1.]],
                                               [[1. + 2**-23, 0., 0.], [1., 1., 1.]]), 2**-23)
        for old, new in [(1., 1. + 2**-22), (100000., 100000. + 2**-7), (0., .000001)]:
            with self.subTest(old=old, new=new), self.assertRaises(RuntimeError):
                validate_derived_bounds([[old, 0., 0.], [1., 1., 1.]], [[new, 0., 0.], [1., 1., 1.]])

    def test_only_small_opaque_interior_static_source_candidates(self):
        materials = {'opaque': {'alpha': 1.}, 'glass': {'alpha': .5}}
        self.assertTrue(eligible_record(record(), materials, set()))
        for field, value in [('group', 'Vegetation'), ('enabled', False), ('triangles', 0), ('triangles', 512),
                             ('triangles', True), ('instances', 2), ('materialSlots', []), ('materialSlots', ['glass'])]:
            r = record(); r[field] = value
            with self.subTest(field=field, value=value):
                self.assertFalse(eligible_record(r, materials, set()))
        self.assertFalse(eligible_record(record(), materials, {'DOM_00001'}))

    def test_all_gameplay_and_door_metadata_are_excluded(self):
        for flag in ('doorMotion', 'dynamicCameraOccluder', 'walkSurface', 'cameraOccluder', 'babylonCheckCollisions'):
            r = record(); r['metadata'][flag] = True
            with self.subTest(flag=flag):
                self.assertFalse(eligible_record(r, {'opaque': {'alpha': 1}}, set()))

    def test_fixed_door_parts_and_stove_effects_are_excluded_without_motion_metadata(self):
        for name in ['Dvere obytný priestor · pravá zárubňa', 'Dveře · klika', 'EAST-04 · D1.1.002 · parapet',
                     'Bočná výplň · kľučka', 'DOOR-HANDLE', 'FIREPLACE-STOVE · LOG-1', 'FLAME-3']:
            r = record(); r['name'] = name
            with self.subTest(name=name): self.assertFalse(eligible_record(r, {'opaque': {'alpha': 1}}, set()))

    def test_rank_is_nearest_living_room_then_stable_identity_and_excludes_door_members(self):
        far, near, door = record('DOM_00001'), record('DOM_00002'), record('DOM_00003')
        far['boundsMm'] = {'min': [100, 0, 0], 'max': [102, 2, 2]}
        scene = {'objects': [far, door, near], 'materials': {'opaque': {'alpha': 1}},
                 'interior': {'rooms': [{'id': 'ROOM-1-03', 'standingPointMm': {'x': 1, 'y': 1}}]}}
        doors = {'sourceManifestSha256': 'a' * 64, 'doors': [{'members': [{'sourceObjectId': door['id']}]}]}
        self.assertEqual([r['id'] for r in ranked_records(scene, doors)], [near['id'], far['id']])

    def test_only_every_selected_asset_can_change(self):
        mesh = asset_file('DOM_00001')
        before = {mesh: 'old', 'Brezi/Maps/Brezi.umap': 'map', 'Materials/opaque.uasset': 'material'}
        after = {**before, mesh: 'new'}
        self.assertEqual(validate_changes(before, after, ['DOM_00001']), [mesh])
        for changed in [before, {**after, 'Brezi/Maps/Brezi.umap': 'changed'}, {**after, 'extra': 'asset'},
                        {**after, 'Materials/opaque.uasset': 'changed'}]:
            with self.subTest(changed=changed), self.assertRaises(RuntimeError):
                validate_changes(before, changed, ['DOM_00001'])

    def test_invalid_duplicate_or_oversized_cohort_fails_closed(self):
        for ids in [[], ['DOM_00001', 'DOM_00001'], ['DOM_%05d' % i for i in range(129)], ['../../map']]:
            with self.subTest(ids=ids), self.assertRaises(RuntimeError):
                validate_changes({}, {}, ids)
        self.assertEqual(asset_path('DOM_00001'), '/Game/Brezi/Geometry/brezi-twin/StaticMeshes/DOM_00001.DOM_00001')

    def test_source_witness_detects_positions_all_uv_channels_and_polygon_group_changes(self):
        desc = Description()
        mesh = N(get_num_lods=lambda: 1, get_static_mesh_description=lambda lod: desc)
        subsystem = N(get_lod_count=lambda mesh: 1, get_num_uv_channels=lambda mesh, lod: 2)
        u = N(TriangleID=lambda id_value: N(id_value=id_value))
        before = M.source_geometry(u, mesh, subsystem)
        self.assertEqual(before['rows'][0]['corners'][0]['uvs'], [[.625, 0.], [1.625, 0.]])
        for field in ('position', 'uv', 'group'):
            original = getattr(desc, field); setattr(desc, field, original + 1)
            with self.subTest(field=field): self.assertNotEqual(M.source_geometry(u, mesh, subsystem), before)
            setattr(desc, field, original)
        desc.valid = False
        with self.assertRaisesRegex(RuntimeError, 'Sparse source triangle'):
            M.source_geometry(u, mesh, subsystem)


if __name__ == '__main__':
    unittest.main()
