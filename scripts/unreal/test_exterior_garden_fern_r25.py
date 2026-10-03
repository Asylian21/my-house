"""CPU source guards only; these are not Unreal/native or appearance evidence."""
import copy
import importlib.util
import json
import struct
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
PATH = Path(__file__).with_name('exterior-garden-fern-study-r25.py')
SPEC = importlib.util.spec_from_file_location('fern_source_r25', PATH)
S = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(S)


class FernSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = json.loads((S.REFERENCE/'fern_02_2k.gltf').read_text())
        cls.binary = (S.REFERENCE/'fern_02.bin').read_bytes()
        cls.rows = S.decode(cls.document, [cls.binary])
        cls.selected = next(r for r in cls.rows if r['node'] == 'fern_02_b')
        cls.garden = json.loads(S.GARDEN.read_text())
        cls.root = next(r for r in cls.garden['ornamentalPlacements'] if r['id'] == S.ROOT_ID)
        cls.guard = S.load_guard()

    def test_actual_original_four_meshes_and_single_uniform_full_crown_fit(self):
        self.assertEqual(sum(r['triangles'] for r in self.rows), 6232)
        self.assertEqual([r['triangles'] for r in self.rows], [2384, 2248, 784, 816])
        proof = S.fit(self.selected, self.root, self.garden, self.guard)
        self.assertEqual(proof['positionCm'], self.root['positionCm'])
        self.assertEqual(proof['yawDeg'], self.root['yawDeg'])
        self.assertEqual(len(set(proof['scale'])), 1)
        self.assertGreater(proof['circleToOriginalBedBoundaryClearanceCm'], 14.5)
        self.assertEqual(proof['allDecodedVerticesChecked'], 1660)
        self.assertLess(proof['abovePivotHeightCm'], 36)

    def test_rejects_rehashed_gltf_with_unreviewed_extension(self):
        doc = copy.deepcopy(self.document)
        doc['extensionsUsed'] = ['KHR_texture_transform']
        with self.assertRaisesRegex(RuntimeError, 'Unreviewed glTF'):
            S.decode(doc, [self.binary])

    def test_rejects_nonfinite_original_vertex(self):
        raw = bytearray(self.binary)
        struct.pack_into('<f', raw, 0, float('nan'))
        with self.assertRaisesRegex(RuntimeError, 'Nonfinite'):
            S.decode(self.document, [raw])

    def test_root_outside_bed_or_nonpositive_fit_is_not_accepted(self):
        root = copy.deepcopy(self.root)
        root['positionCm'][0] += 500
        with self.assertRaisesRegex(RuntimeError, 'containing circle'):
            S.fit(self.selected, root, self.garden, self.guard)
        root = copy.deepcopy(self.root)
        root['radiusCm'] = -1
        with self.assertRaisesRegex(RuntimeError, 'Uniform fit'):
            S.fit(self.selected, root, self.garden, self.guard)

    def test_actual_alpha_is_explicit_normalized_sixteen_bit_mask(self):
        alpha = S.validate_alpha()
        self.assertFalse(alpha['originalGltfMaskAloneProvidesLeafOpacity'])
        self.assertEqual(alpha['alphaSourceBits'], 16)
        self.assertEqual(alpha['cutoff'], .5)
        self.assertAlmostEqual(alpha['atlasCoverageAtCutoff'], .1532752513885498)
        self.assertFalse(alpha['nativeTextureReadbackPerformed'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
