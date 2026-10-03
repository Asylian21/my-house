"""Single actual-source fractional Pillow raster boundary regression."""
import importlib.util
from pathlib import Path
import sys
import unittest

import numpy as np

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('_r41_fractional_boundary_fixture', Path(__file__).with_name('exterior-lawn-leaf-strip-study-r41-r3.py'))
s = importlib.util.module_from_spec(spec)
spec.loader.exec_module(s)


class FractionalBoundary(unittest.TestCase):
    def test_actual_original_prototype_uses_identical_global_geometry_and_photo_raster(self):
        _, _, _, rows = s.glb(s.PHOTO / 'lawn-photographic-variants.glb')
        row = rows['lawn_photo_0_0_LOD0']
        # Synthetic all-opaque in-memory alpha tests the raster implementation,
        # not provider pixels, native coverage, or the unchanged source images.
        synthetic_alpha = np.full((2048, 2048), 65535, dtype=np.uint16)
        for receipt, geometric, photographic in s.projection_masks(row, synthetic_alpha):
            self.assertFalse(np.any(photographic & ~geometric))
            self.assertGreater(receipt['actualBilinearMip0AlphaCoveredPixels'], 0)


if __name__ == '__main__':
    unittest.main()
