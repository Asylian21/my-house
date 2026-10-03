"""New R41 alpha/whole-blade/byte-scope guards only; no old producer replay."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import unittest

import numpy as np

sys.dont_write_bytecode = True
PATH = Path(__file__).with_name('exterior-lawn-leaf-strip-study-r41.py')
spec = importlib.util.spec_from_file_location('_r41_source_guard_fixture', PATH)
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class R41SourceGuards(unittest.TestCase):
    def test_only_uv0_and_tangent_bytes_may_change(self):
        source = bytes(range(80))
        changed = bytearray(source)
        changed[22] = 231
        ranges = [{'attribute': 'TEXCOORD_0', 'start': 20, 'stop': 30}]
        s.validate_replacement_bytes(source, changed, ranges)
        changed[40] = 232
        with self.assertRaisesRegex(RuntimeError, 'outside UV0/tangent'):
            s.validate_replacement_bytes(source, changed, ranges)

    def test_geometry_ranges_and_shared_ranges_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Only bounded'):
            s.validate_replacement_bytes(bytes(40), bytes(40), [{'attribute': 'POSITION', 'start': 0, 'stop': 10}])
        with self.assertRaisesRegex(RuntimeError, 'overlap'):
            s.validate_replacement_bytes(bytes(40), bytes(40), [
                {'attribute': 'TEXCOORD_0', 'start': 0, 'stop': 10}, {'attribute': 'TANGENT', 'start': 8, 'stop': 20}])

    def test_complete_whole_blade_crops_keep_root_mid_tip(self):
        body = {'axis': 1, 'mappedUvBounds': [[.625, .125], [.6875, .75]]}
        normalized = np.asarray([[0, 0], [1, 0], [0, .45], [1, .45], [.5, 1]], dtype='<f4')
        got = s.mapped_uv(normalized, body)
        self.assertTrue(np.array_equal(got[[0, 1, 4]], [[.625, .75], [.6875, .75], [.65625, .125]]))
        broken = normalized.copy()
        broken[4, 0] = 0
        with self.assertRaisesRegex(RuntimeError, 'root/mid/tip'):
            s.mapped_uv(broken, body)

    def test_mixture_is_per_whole_blade_and_identical_across_source_lods(self):
        for size in (48, 64):
            first = s.assign_bodies('lawn_photo_0_0', size)
            self.assertEqual(first, s.assign_bodies('lawn_photo_0_0', size))
            self.assertEqual(len(first), size)
            self.assertEqual(set(first), {b['id'] for b in s.BODIES})
            self.assertLessEqual(first.count('dry_body') / size, .11)

    def test_bilinear_support_guard_checks_neighbor_texel_not_only_triangle_centres(self):
        alpha = np.full((2048, 2048), 65535, dtype=np.uint16)
        uv = np.asarray([[100.6 / 2048, 100.6 / 2048], [100.7 / 2048, 100.6 / 2048],
                         [100.6 / 2048, 100.7 / 2048]], dtype='<f4')
        faces = np.asarray([[0, 1, 2]], dtype=np.uint32)
        self.assertEqual(s.triangle_alpha_certificate(uv, faces, alpha)['minimumBilinearSupportAlpha16'], 65535)
        alpha[101, 101] = 0
        with self.assertRaisesRegex(RuntimeError, 'remove coverage'):
            s.triangle_alpha_certificate(uv, faces, alpha)

    def test_derived_tangent_rejects_degenerate_uv_and_is_orthogonal(self):
        row = {'POSITION': np.asarray([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype='<f4'),
               'NORMAL': np.asarray([[0, 0, 1]] * 3, dtype='<f4'), 'indices': np.asarray([[0, 1, 2]])}
        uv = np.asarray([[0, 0], [1, 0], [0, 1]], dtype='<f4')
        tangent, proof = s.tangent_frame(row, uv)
        self.assertTrue(np.array_equal(tangent, [[1, 0, 0, 1]] * 3))
        self.assertEqual(proof['maximumFloat32TangentNormalDot'], 0)
        with self.assertRaisesRegex(RuntimeError, 'degenerate'):
            s.tangent_frame(row, np.zeros((3, 2), dtype='<f4'))


if __name__ == '__main__':
    unittest.main()
