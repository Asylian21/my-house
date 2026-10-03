"""Ten bounded source-mask/response cases; no historical source checker replay."""
import copy
import importlib.util
from pathlib import Path
import struct
import sys
import unittest
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('r38_source', Path(__file__).with_name('exterior-context-yard-soft-coherence-study-r38.py'))
s = importlib.util.module_from_spec(spec); spec.loader.exec_module(s)


class SourceContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b = s.build_source()
        cls.pixels, png, cls.field = s.rasterize_mask(cls.b['mask'])
        s.require(not s.FIXTURE.exists(), 'Fresh source raster fixture output only')
        s.FIXTURE.mkdir()
        path = s.FIXTURE/'permission-field.png'; path.write_bytes(png)
        cls.field.update(png=s.pin(path), producer=s.pin(s.ROOT/s.OWNER), fixtures=s.pin(Path(__file__)))
        import json
        (s.FIXTURE/'permission-field-proof.json').write_text(json.dumps(cls.field, separators=(',', ':'), allow_nan=False)+'\n')

    def test_actual_mask_is_inside_all_original_permissions(self):
        from shapely.geometry import Polygon
        self.assertEqual(self.b['mask']['targetBuildingSourceIds'], list(s.TARGETS))
        for p in self.b['mask']['polygons']:
            q = Polygon(p['ringsCm'][0], p['ringsCm'][1:])
            self.assertTrue(self.b['allowed'].covers(q))
            self.assertTrue(q.disjoint(self.b['exclusions']))
        self.assertTrue(self.field['exhaustiveNonzeroCenterDistanceGuardChecked'])
        self.assertGreater(self.field['minimumNonzeroCenterBoundaryDistanceCm'], self.field['layout']['minimumCenterToMaskBoundaryCm'])

    def test_actual_polygons_finite_f32_and_nonzero_edges(self):
        for p in self.b['mask']['polygons']:
            for r in p['ringsCm']:
                for a, b in zip(r, r[1:]+r[:1]):
                    self.assertNotEqual(a, b)
                    self.assertTrue(all(s.f32(x) == x for x in a))
        self.assertLessEqual(self.b['mask']['segments'], 512)
        self.assertFalse(self.pixels[0].any()); self.assertFalse(self.pixels[-1].any())
        self.assertFalse(self.pixels[:, 0].any()); self.assertFalse(self.pixels[:, -1].any())
        self.assertEqual(self.field['layout']['plannedNativePolicy']['mipGenSettings'], 'NO_MIPMAPS')

    def test_falloff_boundary_midpoint_and_core(self):
        mask = {'polygons': [{'ringsCm': [[[0., 0.], [1000., 0.], [1000., 1000.], [0., 1000.]]], 'boundsCm': [0., 0., 1000., 1000.]}], 'interiorFalloffCm': 150.}
        self.assertEqual(s.mask_weight([0., 500.], mask), 0.)
        self.assertEqual(s.mask_weight([75., 500.], mask), .5)
        self.assertEqual(s.mask_weight([500., 500.], mask), 1.)
        self.assertEqual(s.mask_weight([-1., 500.], mask), 0.)

    def test_holes_and_nonfinite_inputs(self):
        mask = {'polygons': [{'ringsCm': [[[0., 0.], [1000., 0.], [1000., 1000.], [0., 1000.]], [[400., 400.], [600., 400.], [600., 600.], [400., 600.]]], 'boundsCm': [0., 0., 1000., 1000.]}], 'interiorFalloffCm': 150.}
        self.assertEqual(s.mask_weight([500., 500.], mask), 0.)
        self.assertEqual(s.mask_weight([400., 500.], mask), 0.)
        with self.assertRaises(ValueError): s.mask_weight([float('nan'), 0.], mask)

    def test_outside_values_preserve_binary64_and_signed_zero(self):
        for old in (-0., 0., .3330000042915344, 1e-250, -7.25):
            actual = s.outside_preserving_mix(old, 200., 0.)
            self.assertEqual(struct.pack('<d', old), struct.pack('<d', actual))
        self.assertEqual(s.outside_preserving_mix([1., -0., -2.], [999., 4., 3.], 0.), [1., -0., -2.])

    def test_fixed_world_field_has_no_camera_dependency(self):
        from shapely.geometry import Polygon
        p = self.b['mask']['polygons'][0]
        xy = list(Polygon(p['ringsCm'][0], p['ringsCm'][1:]).representative_point().coords)[0]
        a = s.mask_weight(xy, self.b['mask'])
        # Camera is deliberately absent from the evaluator and Custom inputs.
        self.assertEqual(a, s.mask_weight(xy, self.b['mask']))
        self.assertNotIn('Camera', s.hlsl_mask(self.b['mask']))
        nodes = {n['role']: n for n in self.b['graphs']['backdrop']['nodes']}
        self.assertEqual(nodes[s.TAG+'fixed-world-mask-uv']['inputs'], [['Position', 'BreziExterior:world-position', 'XYZ']])
        self.assertNotIn('Camera', nodes[s.TAG+'fixed-world-mask-uv']['values']['code'])
        self.assertEqual(next(e for e in nodes[s.TAG+'common-normal']['inputs'] if e[0] == 'VertexNormal')[1:], [s.TAG+'common-artist-flat-up', ''])
        self.assertNotIn('Position.z', nodes[s.TAG+'common-flat-landcover']['values']['code'])

    def test_all_original_58_nodes_exact_and_same_endpoints(self):
        self.assertEqual(s.validate_graphs(self.b['originalGraph'], self.b['substrateGraph'], self.b['graphs'])['sameTwelveNewResponseNodesOnBothSurfaces'], True)
        self.assertEqual(len(self.b['graphs']['backdrop']['nodes']), 70)
        self.assertEqual(len(self.b['graphs']['substrate']['nodes']), 73)

    def test_old_world_uv_or_radial_mutation_rejected(self):
        changed = copy.deepcopy(self.b['graphs'])
        node = next(n for n in changed['backdrop']['nodes'] if n['role'] == 'BreziExterior:ortho-radial-distance')
        node['values']['code'] = 'return 1.0;'
        with self.assertRaises(ValueError): s.validate_graphs(self.b['originalGraph'], self.b['substrateGraph'], changed)

    def test_substrate_alpha_policy_mutation_rejected(self):
        changed = copy.deepcopy(self.b['graphs']); changed['substrate']['flags']['blend_mode'] = '<BlendMode.BLEND_OPAQUE: 0>'
        with self.assertRaises(ValueError): s.validate_graphs(self.b['originalGraph'], self.b['substrateGraph'], changed)
        node = next(n for n in self.b['graphs']['substrate']['nodes'] if n['role'].endswith(':coverage-r'))
        self.assertEqual(node['values'], {'r': True, 'g': False, 'b': False, 'a': False})

    def test_original_photo_bytes_and_unchanged_target_geometry(self):
        self.assertEqual(len(self.b['photoNativeObjects']), 3)
        for k in ('albedo', 'normal', 'roughness'):
            s.checked(self.b['inputs']['originalPhoto_'+k])
        self.assertEqual(len(self.b['targetWitness']), 2)
        for row in self.b['targetWitness'].values():
            self.assertEqual(len(row['components']), 1)
            self.assertTrue(row['components'][0]['mesh'])


if __name__ == '__main__':
    unittest.main()
