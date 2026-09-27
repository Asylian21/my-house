"""Pinned DEM parsing and protected near-site terrain geometry; no Unreal."""
import importlib.util
import json
import math
from pathlib import Path
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('exterior_terrain', HERE / 'exterior-terrain.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TerrainPolicy(unittest.TestCase):
    def test_near_join_and_full_scale_relief(self):
        self.assertEqual(m.height_cm([30000, 0], 200, 184), -25)
        self.assertEqual(m.height_cm([90000, 0], 200, 184), 1575)
        self.assertEqual(m.height_cm([60000, 0], 200, 184), 775)
        self.assertEqual(m.height_cm([90000, 0], 200, 184, 0), -25)

    def test_pixel_center_georeference(self):
        grid = {'extent': {'xmin': 10, 'ymax': 50}, 'pixelScale': [2, 2, 0]}
        self.assertEqual(m.national_point(0, 0, grid), [11, 49])
        self.assertEqual(m.national_point(2, 3, grid), [15, 43])

    def test_c3_transform_rounds_before_fractional_client_offset(self):
        scene = {'cadastralDatumSjtskMm': {'x': 10000, 'y': 20000},
                 'siteAxis': {'ux': 1, 'uy': 0, 'vx': 0, 'vy': 1},
                 'housePlacement': {'translationMm': {'x': .25, 'y': 0}},
                 'sceneCenterMm': {'x': 0, 'y': 0}}
        self.assertEqual(m.local_xy_cm([10.0005, 20.0005], scene), [.075, -.1])


class PinnedTerrain(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = m.ROOT / 'output/unreal/exterior-terrain-20260926-r4'
        path = cls.directory / 'terrain-plan.json'
        if not path.exists():
            raise unittest.SkipTest('Generate the isolated terrain plan first')
        cls.plan = json.loads(path.read_text())

    def test_raw_and_mask_receipts_match_no_data_exactly(self):
        inputs = self.directory / 'inputs'
        grid = m.masked_grid((inputs / 'dmr5g-16km-f32.tif').read_bytes(),
                             (inputs / 'dmr5g-16km-mask.png').read_bytes(), self.plan['grid']['extent'])
        self.assertEqual(grid['values'], self.plan['grid']['valuesBpvMetres'])
        self.assertEqual(grid['validSamples'], 50140)
        self.assertEqual(grid['missingSamples'], 15909)
        self.assertLess(max(z for z in grid['values'] if z is not None), 550)
        self.assertGreater(min(z for z in grid['values'] if z is not None), 165)
        for path, expected in self.plan['inputFiles'].items():
            self.assertEqual(m.sha(path), expected, path)

    def test_all_triangle_winding_and_inner_exclusion(self):
        for mesh in self.plan['meshes']:
            for i in range(0, len(mesh['indices']), 3):
                tri = [mesh['verticesCm'][j] for j in mesh['indices'][i:i + 3]]
                self.assertLess(m.cross(*tri), 0, mesh['id'])
                self.assertTrue(all(math.isfinite(v) for p in tri for v in p))
                if mesh['id'] == 'context_unresolved_flat_backdrop':
                    self.assertTrue(all(p[2] == -25 for p in tri))
                    # Preserve the existing DOM_00000 baseline rectangle.
                    clipped = tri
                    square = [[-12000, -10000], [12000, -10000], [12000, 10000], [-12000, 10000]]
                    for a, b in zip(square, square[1:] + square[:1]):
                        clipped = m.clip_halfplane(clipped, a, b, True)
                        if not clipped:
                            break
                    self.assertLess(abs(m.area(clipped)) if clipped else 0, .1)
                else:
                    # Check complete edge distances, not only vertices.
                    for a, b in zip(tri, tri[1:] + tri[:1]):
                        dx, dy = b[0] - a[0], b[1] - a[1]
                        length = dx * dx + dy * dy
                        t = max(0, min(1, -(a[0] * dx + a[1] * dy) / length)) if length else 0
                        self.assertGreaterEqual(math.hypot(a[0] + t * dx, a[1] + t * dy), 30000 - .01)

    def test_evidence_preserves_canonical_design_and_no_measured_fallback_claim(self):
        self.assertEqual(self.plan['activeDesign'], {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'})
        self.assertEqual(self.plan['housePlacement']['streetSetbackMm'], 3000)
        self.assertEqual(self.plan['housePlacement']['eastSetbackMm'], 3000)
        self.assertEqual(self.plan['heightPolicy']['verticalExaggeration'], 1)
        self.assertFalse(self.plan['noDataFallback']['measured'])
        self.assertEqual(self.plan['noDataFallback']['replaceOriginalFlatVisualSourceIds'], ['DOM_02039'])
        peak = self.plan['peakSample']
        self.assertGreater(peak['distanceFromSceneMetres'], 9000)
        self.assertGreater(peak['positionCm'][2], 35000)


if __name__ == '__main__':
    unittest.main()
