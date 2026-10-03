"""Only the changed R41 baseline-alpha and raster comparison contracts."""
import importlib.util
from pathlib import Path
import sys
import unittest

import numpy as np

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('_r41_changed_alpha_fixture', Path(__file__).with_name('exterior-lawn-leaf-strip-study-r41-r2.py'))
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class ChangedAlphaContracts(unittest.TestCase):
    def test_failed_original_lower_bound_is_recorded_without_an_opaque_claim(self):
        alpha = np.full((2048, 2048), 65535, dtype=np.uint16)
        uv = np.asarray([[100.6 / 2048, 100.6 / 2048], [100.7 / 2048, 100.6 / 2048], [100.6 / 2048, 100.7 / 2048]], dtype='<f4')
        alpha[101, 101] = 0
        receipt = s.triangle_alpha_certificate(uv, np.asarray([[0, 1, 2]]), alpha, require_opaque=False)
        self.assertFalse(receipt['conservativeContinuousMip0AlphaLowerBoundPassedClip'])
        self.assertFalse(receipt['failedLowerBoundProvesActualTransparency'])
        with self.assertRaisesRegex(RuntimeError, 'remove coverage'):
            s.triangle_alpha_certificate(uv, np.asarray([[0, 1, 2]]), alpha)

    def test_projection_compares_actual_alpha_and_does_not_hide_coverage_loss(self):
        alpha = np.full((2048, 2048), 65535, dtype=np.uint16)
        row = {'POSITION': np.asarray([[0, 0, 0], [1, 1, 1], [0, 1, 2]], dtype='<f4'),
               'TEXCOORD_0': np.asarray([[.25, .25], [.30, .25], [.25, .30]], dtype='<f4'),
               'indices': np.asarray([[0, 1, 2]])}
        original = s.projection_masks(row, alpha)
        alpha[510:616, 510:616] = 0
        corrupt = s.projection_masks(row, alpha)
        for (_, old_geometry, old_photo), (_, bad_geometry, bad_photo) in zip(original, corrupt):
            self.assertTrue(np.array_equal(old_geometry, bad_geometry))
            self.assertGreater(int((old_photo & ~bad_photo).sum()), 0)


if __name__ == '__main__':
    unittest.main()
