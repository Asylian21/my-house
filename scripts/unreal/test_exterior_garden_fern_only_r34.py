"""Bounded CPU source guards for the exact36 fern-only R34 candidate."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
s = importlib.util.spec_from_file_location('r34_exact_source_guard_tests', ROOT/'scripts/unreal/exterior-garden-fern-only-guards-r34.py')
g = importlib.util.module_from_spec(s)
s.loader.exec_module(g)


class FernOnlySource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan, cls.ref = g.load_source()
        cls.raw = g.checked(cls.plan['sourceGlb']).read_bytes()

    def altered(self, change, match):
        plan = copy.deepcopy(self.plan)
        change(plan)
        with self.assertRaisesRegex(RuntimeError, match):
            g.selection(plan, self.ref)

    def test_actual36_and437_scope(self):
        retained = g.selection(self.plan, self.ref)
        self.assertEqual(len(retained), 437)
        self.assertEqual(sum(r['role'] == 'groundcover' for r in retained), 384)
        self.assertEqual(len(self.plan['preservedOrnamentalRootIds']), 12)
        controls = g.retained_controls(self.ref)
        self.assertEqual(sum(len(r['rootIds']) for r in controls.values()), 437)
        for actor, row in self.ref['controls'].items():
            if any(r.startswith('garden_ornamental_') for r in row['rootIds']):
                self.assertEqual(controls[actor], row)

    def test_no_tall_hero_retirement(self):
        self.altered(lambda p: p['wholeOneMemberHeroGroupRetirements'].append({'rootId': 'garden_ornamental_6'}), 'All12')

    def test_no_ornamental_subset_claim(self):
        self.altered(lambda p: p['preservedOrnamentalRootIds'].pop(), 'All12')

    def test_no_extra_low_root_removal(self):
        self.altered(lambda p: p['sourceGroupFilters'][0]['removeSourceOrderedIndices'].append(0), 'Only2')

    def test_no_reposition_or_contact_change(self):
        self.altered(lambda p: p['proposedPlacements'][0]['positionCm'].__setitem__(2, -100), 'exact36')

    def test_no_new_population_or_budget(self):
        self.altered(lambda p: p['expectedCounts'].__setitem__('newOriginalFernRoots', 37), 'Ordered437')

    def test_ordered_retained_source_hash_required(self):
        self.altered(lambda p: p.__setitem__('retainedSourceRowsSha256', '0'*64), 'Ordered437')

    def test_all32124_source_f32_points_in_original_masks(self):
        rows = g.footprints(self.ref)
        self.assertEqual(len(rows), 36)
        self.assertEqual(sum(r['sourceF32VerticesThroughPriorActualNativeMatrix'] for r in rows), 32124)
        self.assertTrue(all(r['allVerticesInsideOriginalBed'] and r['fullCircleExcludesOriginalSteps'] for r in rows))
        self.assertTrue(all(r['nativeR34FrameMeasured'] is False for r in rows))

    def test_outside_full_crown_vertex_rejected(self):
        ref = dict(self.ref)
        ref['models'] = copy.deepcopy(self.ref['models'])
        ref['models']['fern_02_a']['expectedNativeVerticesCm'][0][0] = 100000
        with self.assertRaisesRegex(RuntimeError, 'crown.*(crosses|intersects)'):
            g.footprints(ref)

    def test_exact_original_geometry_bytes(self):
        proof = g.decode_export(self.raw, self.ref['models'])
        self.assertEqual((proof['models'], proof['vertices'], proof['triangles']), (3, 2677, 3848))
        self.assertTrue(proof['originalNormalUvIndexBytesExact'])
        self.assertFalse(proof['nativeR34ReadbackPerformed'])
        self.assertFalse(proof['derivedTangentAttributeInvented'])

    def changed_attribute(self, role):
        raw = bytearray(self.raw)
        size = struct.unpack_from('<I', raw, 12)[0]
        doc = json.loads(raw[20:20+size])
        primitive = doc['meshes'][0]['primitives'][0]
        ai = primitive['indices'] if role == 'indices' else primitive['attributes'][role]
        accessor = doc['accessors'][ai]
        view = doc['bufferViews'][accessor['bufferView']]
        offset = 28+size+view.get('byteOffset', 0)+accessor.get('byteOffset', 0)
        raw[offset] ^= 1
        return bytes(raw)

    def test_uv0_byte_change_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'normal/UV bytes'):
            g.decode_export(self.changed_attribute('TEXCOORD_0'), self.ref['models'])

    def test_normal_byte_change_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'normal/UV bytes'):
            g.decode_export(self.changed_attribute('NORMAL'), self.ref['models'])

    def test_original_winding_connectivity_change_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'order/winding/connectivity'):
            g.decode_export(self.changed_attribute('indices'), self.ref['models'])

    def test_position_shift_change_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'F32 POSITION'):
            g.decode_export(self.changed_attribute('POSITION'), self.ref['models'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
