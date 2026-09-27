"""Independent numerical checks for the isolated growing-season prototype."""
import importlib.util
from pathlib import Path
import unittest

import numpy as np

SPEC = importlib.util.spec_from_file_location('seasonal', Path(__file__).with_name('exterior-seasonal-fields.py'))
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)


class SeasonalFieldsTests(unittest.TestCase):
    def test_zero_mask_and_green_source_are_exactly_preserved(self):
        rng = np.random.default_rng(6012)
        source = rng.uniform(0, 1, (2000, 3))
        result, weight = M.seasonal_color(source, np.zeros(2000))
        np.testing.assert_array_equal(result, source)
        np.testing.assert_array_equal(weight, 0)
        green = np.array([[.06, .12, .025], [.01, .03, .015], [.20, .25, .15]])
        result, weight = M.seasonal_color(green, np.ones(3))
        np.testing.assert_array_equal(result, green)
        np.testing.assert_array_equal(weight, 0)

    def test_synthetic_road_roof_rock_and_water_remain_outside_mask(self):
        source = np.array([[[175, 160, 135, 255], [170, 135, 100, 255],
                            [190, 184, 171, 255], [75, 94, 106, 255], [159, 133, 87, 255]]], dtype=np.uint8)
        result, _ = M.apply_preview(source, [[0, 0, 0, 0, 1]])
        np.testing.assert_array_equal(result[:, :4], source[:, :4])
        self.assertGreater(result[0, 4, 1], result[0, 4, 0])

    def test_source_alpha_nodata_and_zero_weight_rgb_are_byte_exact(self):
        source = np.array([[[150, 128, 86, 0], [150, 128, 86, 252], [150, 128, 86, 255]]], dtype=np.uint8)
        result, _ = M.apply_preview(source, [[1, 1, 1]])
        np.testing.assert_array_equal(result[0, :2], source[0, :2])
        np.testing.assert_array_equal(result[..., 3], source[..., 3])

    def test_field_luminance_order_and_texture_variation_survive(self):
        scale = np.linspace(.2, 2., 500)
        source = scale[:, None]*[.20, .15, .075]
        result, _ = M.seasonal_color(source, np.ones(500))
        old_y = source @ M.LUMA; new_y = result @ M.LUMA
        self.assertTrue(np.all(np.diff(new_y) > 0))
        self.assertGreater(new_y.std()/new_y.mean(), .40)
        self.assertGreater(np.corrcoef(old_y, new_y)[0, 1], .995)
        self.assertTrue(np.all(result[:, 1] > result[:, 0]))
        self.assertTrue(np.all((result >= 0) & (result <= .32)))

    def test_inner_feather_never_extends_beyond_field_or_nodata_hole(self):
        binary = np.zeros((101, 101), dtype=bool); binary[10:91, 10:91] = True; binary[45:56, 45:56] = False
        result = M.interior_mask(binary, 1., 500., 1000.)
        self.assertEqual(float(result[~binary].max()), 0)
        self.assertEqual(float(result[10:16].max()), 0)
        self.assertEqual(float(result[45:56, 45:56].max()), 0)
        self.assertEqual(float(result[30, 30]), 1)
        self.assertTrue(np.all(np.diff(result[10:30, 30]) >= 0))

    def test_scalar_reference_matches_vector_shader_oracle(self):
        def step(lo, hi, x):
            v = max(0., min(1., (x-lo)/(hi-lo))); return v*v*(3-2*v)
        rng = np.random.default_rng(601227)
        for rgb, mask in zip(rng.uniform(0, 1, (500, 3)), rng.uniform(-.2, 1.2, 500)):
            y = sum(a*b for a, b in zip(rgb, [.2126, .7152, .0722]))
            w = max(0., min(1., mask))*step(-.02, .10, (rgb[0]-rgb[1])/max(rgb[0]+rgb[1], .00001))
            w *= (1-step(.82, 1.10, rgb[2]/max(rgb[1], .00001)))*step(.008, .035, y)*(1-step(.45, .70, y))*.88
            target = [c*(max(y, .004)/.18)**.82 for c in [.065, .115, .030]]
            target_y = sum(a*b for a, b in zip(target, [.2126, .7152, .0722]))
            target = [max(0., min(.32, t+max(-.8, min(.8, c/max(y, .004)-1))*target_y*.07)) for t, c in zip(target, rgb)]
            expected = [c+(t-c)*w for c, t in zip(rgb, target)]
            result, weight = M.seasonal_color(rgb, mask)
            np.testing.assert_allclose(result, expected, atol=1e-15)
            self.assertAlmostEqual(float(weight), w, places=14)

    def test_world_affine_is_used_without_centimetre_rescaling_or_v_flip(self):
        layer = {'width': 100, 'height': 100, 'worldCmToUvRows': [[.0001, 0, .5], [0, -.0001, .5]]}
        np.testing.assert_array_equal(M.world_to_pixel([[0, 0], [100, 200]], layer), [[50, 50], [51, 48]])

    def test_geographic_raster_excludes_buffered_road_and_provider_nodata(self):
        layer = {'width': 200, 'height': 200, 'worldCmToUvRows': [[1/20000, 0, 0], [0, 1/20000, 0]], 'pixelSizeMetres': [1, 1]}
        plan = {'regions': [{'id': 'synthetic', 'kind': 'field-season-illustration',
                             'polygonCm': [[1000, 1000], [19000, 1000], [19000, 19000], [1000, 19000]]}],
                'exclusions': [{'polygonCm': [[9600, 0], [10400, 0], [10400, 20000], [9600, 20000]], 'bufferCm': 500}]}
        coverage = np.ones((200, 200)); coverage[30:50, 140:160] = 0
        mask = M.build_mask(plan, layer, coverage)
        self.assertEqual(float(mask[:, 89:111].max()), 0)
        self.assertEqual(float(mask[coverage == 0].max()), 0)
        self.assertEqual(float(mask[:20].max()), 0)
        self.assertEqual(float(mask[100, 55]), 1)
        self.assertEqual(float(mask[100, 145]), 1)


if __name__ == '__main__':
    unittest.main()
