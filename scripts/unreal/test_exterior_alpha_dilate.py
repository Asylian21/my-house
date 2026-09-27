import importlib.util
from pathlib import Path
import unittest
import numpy as np

SPEC=importlib.util.spec_from_file_location('dilation',Path(__file__).with_name('exterior-alpha-dilate.py'))
D=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(D)


class DilationTests(unittest.TestCase):
    def test_white_fringe_removed_but_opaque_photo_and_alpha_stay_byte_exact(self):
        rgb=np.full((32,32,3),255,dtype=np.uint8); alpha=np.full((32,32),.15,dtype=np.float32)
        rgb[13:19,13:19]=[45,100,18];alpha[13:19,13:19]=1
        before=alpha.copy();actual=D.nearest_opaque_rgb(rgb,alpha)
        self.assertTrue(np.all(actual==[45,100,18]))
        np.testing.assert_array_equal(alpha,before)
        self.assertTrue(np.all(actual[alpha>=.99]==rgb[alpha>=.99]))
        old=D.mip_audit(rgb,alpha.copy());new=D.mip_audit(actual,alpha.copy())
        self.assertGreater(old[-1]['visibleMeanLinearRGB'][2],new[-1]['visibleMeanLinearRGB'][2]*10)

    def test_nearest_donor_preserves_distinct_leaf_and_flower_colours(self):
        rgb=np.full((4,6,3),255,dtype=np.uint8);alpha=np.zeros((4,6),np.float32)
        rgb[1,1]=[30,80,10];rgb[1,4]=[240,20,100];alpha[1,1]=alpha[1,4]=1
        actual=D.nearest_opaque_rgb(rgb,alpha)
        np.testing.assert_array_equal(actual[1,2],[30,80,10])
        np.testing.assert_array_equal(actual[1,3],[240,20,100])

    def test_absent_opaque_donors_and_size_mismatch_fail(self):
        rgb=np.zeros((4,4,3),np.uint8)
        with self.assertRaisesRegex(RuntimeError,'no opaque'):D.nearest_opaque_rgb(rgb,np.zeros((4,4)))
        with self.assertRaisesRegex(RuntimeError,'dimensions'):D.nearest_opaque_rgb(rgb,np.ones((3,4)))


if __name__=='__main__':unittest.main()
