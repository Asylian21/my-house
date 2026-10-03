"""Independent stdlib native-integration guards; no Unreal or scientific import."""
from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('organic_native', HERE/'exterior-garden-organic-native.py')
native = importlib.util.module_from_spec(spec); spec.loader.exec_module(native)


class OrganicNative(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((native.STUDY/'garden-plan.json').read_text())
        cls.library = json.loads((native.STUDY/'geometry-manifest.json').read_text())
        old = json.loads(Path(cls.library['sourceLibrary']['path']).read_text())
        cls.merged = {'meshes': old['meshes']+cls.library['meshes']}
        cls.raw = (native.STUDY/'garden-organic.glb').read_bytes()

    def validate(self, plan=None, merged=None, scene=None, obj=None):
        return native.validated_garden(plan or self.plan, merged or self.merged,
            scene or self.plan['sourceSceneSha256'], obj or self.plan['sourceObjSha256'])

    def changed_glb(self, change):
        size = struct.unpack_from('<I', self.raw, 12)[0]
        doc = json.loads(self.raw[20:20+size]); binary = bytearray(self.raw[28+size:])
        change(doc, binary)
        encoded = json.dumps(doc, separators=(',', ':')).encode(); encoded += b' '*((-len(encoded)) % 4)
        raw = struct.pack('<4sII', b'glTF', 2, 28+len(encoded)+len(binary))
        raw += struct.pack('<II', len(encoded), 0x4E4F534A)+encoded+struct.pack('<II', len(binary), 0x004E4942)+binary
        with tempfile.TemporaryDirectory(prefix='organic-native-rejection-', dir=native.ROOT/'output/unreal') as folder:
            path = Path(folder)/'mutated.glb'; path.write_bytes(raw)
            return native._decode(path)

    def test_actual_frozen_r1c_all_four_masters_twelve_lods_and473_rows_pass_without_scientific_runtime(self):
        proof = self.validate()
        self.assertEqual(proof['status'], 'verified-source-organic-garden')
        self.assertEqual((proof['masters'], proof['lods'], proof['instances'], proof['allOriginalTransforms'], proof['unchangedOtherGardenRows']), (4, 12, 424, 473, 49))
        self.assertEqual((proof['whiteHeroReplacements'], proof['lowerClumpReplacements']), (4, 420))
        self.assertAlmostEqual(proof['minimumFullCrownToOriginalBedClearanceCm'], 6.6521089228894095, places=12)
        self.assertIs(proof['nativeAppearanceAccepted'], False); self.assertIs(proof['performanceAccepted'], False)
        self.assertIs(proof['originalMaterialRecipesAndPixelsUnchanged'], True)
        self.assertEqual(proof['masterIds'], sorted(native.MAPPING.values()))
        self.assertNotIn('numpy', native.__dict__); self.assertNotIn('shapely', native.__dict__)

    def test_reject_changed_original_roots_yaws_scales_bed_domains_and_unsupported_acceptance_even_when_repin_claimed(self):
        mutations = [lambda p: p.update(owner='scripts/unreal/exterior-garden-organic.py'),
            lambda p: p['ornamentalPlacements'][0]['positionCm'].__setitem__(0, -982.),
            lambda p: p['ornamentalPlacements'][0].update(yawDeg=13),
            lambda p: p['gardenDetailPlacements'][0].update(uniformScale=1.4),
            lambda p: p['sourceMulchTrianglesCm']['DOM_01965'][0][0].__setitem__(0, 100000),
            lambda p: p['organicStudy'].update(nativeVerified=True),
            lambda p: p['organicStudy'].update(nativeVerified=0),
            lambda p: p['housePlacement'].update(streetSetbackMm=2999),
            lambda p: p['ornamentalPlacements'][5].update(meshId='garden_white_organic_a'),
            lambda p: p['organicCrownProof'].update(sha256='0'*64)]
        for mutation in mutations:
            plan = deepcopy(self.plan); mutation(plan)
            with self.subTest(mutation=mutation):
                with self.assertRaisesRegex(RuntimeError, 'immutable'): self.validate(plan=plan)

    def test_reject_scene_or_obj_frame_drift(self):
        with self.assertRaisesRegex(RuntimeError, 'scene/OBJ'): self.validate(scene='0'*64)
        with self.assertRaisesRegex(RuntimeError, 'scene/OBJ'): self.validate(obj='0'*64)

    def test_reject_merged_missing_duplicate_wrong_material_geometry_bounds_lod_counts_or_typed_level(self):
        def change(callback):
            merged = deepcopy(self.merged); callback(merged)
            with self.assertRaisesRegex(RuntimeError, 'merged'): self.validate(merged=merged)
        change(lambda m: m['meshes'].pop())
        change(lambda m: m['meshes'].append(deepcopy(m['meshes'][-1])))
        change(lambda m: m['meshes'][-1]['lods'][0].update(triangles=1))
        change(lambda m: m['meshes'][-1]['lods'][1].update(level=True))
        change(lambda m: m['meshes'][-1]['lods'][0]['expectedBoundsCm']['max'].__setitem__(2, 1000))
        change(lambda m: m['meshes'][-1].update(materialKeys=['ph_shrub_01_ornamental']))
        change(lambda m: m['meshes'][-1].update(placementPolicy='scatter'))

    def test_independent_union_boundary_crown_clearance_ignores_shared_triangle_diagonal_but_protects_hole(self):
        def p(x, y): return [x, y, 0]
        square = [[p(0, 0), p(10, 0), p(10, 10)], [p(0, 0), p(10, 10), p(0, 10)]]
        edges = native._boundary(square); self.assertEqual(len(edges), 4)
        self.assertEqual(min(native._distance([5, 5], a, b) for a, b in edges), 5.)
        self.assertTrue(any(native._triangle_inside([5, 5], [v[:2] for v in tri]) for tri in square))
        self.assertFalse(any(native._triangle_inside([15, 5], [v[:2] for v in tri]) for tri in square))
        ring = []
        corners = [(0, 0), (10, 0), (10, 10), (0, 10)]; inner = [(4, 4), (6, 4), (6, 6), (4, 6)]
        for i in range(4):
            a, b, c, d = corners[i], corners[(i+1)%4], inner[(i+1)%4], inner[i]
            ring.extend([[p(*a), p(*b), p(*c)], [p(*a), p(*c), p(*d)]])
        self.assertEqual(len(native._boundary(ring)), 8)
        self.assertFalse(any(native._triangle_inside([5, 5], [v[:2] for v in tri]) for tri in ring))
        with self.assertRaisesRegex(RuntimeError, 'triangle union'): native._boundary(square+[square[0], square[0]])

    def test_actual_glb_rejects_unmeasured_node_transform_morph_target_material_or_accessor_bounds(self):
        mutations = [lambda d, b: d['nodes'][0].update(translation=[1, 0, 0]),
            lambda d, b: d['meshes'][0]['primitives'][0].update(targets=[{}]),
            lambda d, b: d['materials'][0].update(name='unapproved-new-material'),
            lambda d, b: d['bufferViews'][0].update(byteLength=999999999)]
        for mutate in mutations:
            with self.assertRaises(RuntimeError): self.changed_glb(mutate)

    def test_actual_glb_rejects_nonfinite_positions_invalid_unit_frames_and_opposed_winding(self):
        def write_first(attribute, values):
            def mutate(doc, binary):
                index = doc['meshes'][0]['primitives'][0]['attributes'][attribute]
                view = doc['bufferViews'][doc['accessors'][index]['bufferView']]
                struct.pack_into('<'+'f'*len(values), binary, view['byteOffset'], *values)
            return mutate
        for attribute, values in [('POSITION', [math.nan, 0, 0]), ('NORMAL', [0, 0, 0]), ('TANGENT', [1, 0, 0, 0])]:
            with self.assertRaisesRegex(RuntimeError, 'nonfinite|frame'): self.changed_glb(write_first(attribute, values))
        def flipped(doc, binary):
            index = doc['meshes'][0]['primitives'][0]['indices']; v = doc['bufferViews'][doc['accessors'][index]['bufferView']]
            a, b, c = struct.unpack_from('<III', binary, v['byteOffset']); struct.pack_into('<III', binary, v['byteOffset'], a, c, b)
        with self.assertRaisesRegex(RuntimeError, 'winding'): self.changed_glb(flipped)

    def test_actual_glb_rejects_outside_indices_and_photographic_uv_escape(self):
        def outside(doc, binary):
            index = doc['meshes'][0]['primitives'][0]['indices']; v = doc['bufferViews'][doc['accessors'][index]['bufferView']]
            struct.pack_into('<I', binary, v['byteOffset'], 0xffffffff)
        with self.assertRaisesRegex(RuntimeError, 'indices'): self.changed_glb(outside)
        def uv(doc, binary):
            mat = next(i for i, m in enumerate(doc['materials']) if m['name'] == 'regional_green_leaf')
            primitive = next(p for p in doc['meshes'][0]['primitives'] if p['material'] == mat)
            index = primitive['attributes']['TEXCOORD_0']; v = doc['bufferViews'][doc['accessors'][index]['bufferView']]
            struct.pack_into('<ff', binary, v['byteOffset'], 0., 0.)
        with self.assertRaisesRegex(RuntimeError, 'opaque UV'): self.changed_glb(uv)


if __name__ == '__main__': unittest.main()
