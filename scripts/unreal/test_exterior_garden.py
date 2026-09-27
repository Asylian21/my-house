"""Independent complete-crown checks for the twelve ornamental replacements."""
import hashlib
import json
import math
from pathlib import Path
import unittest

from shapely.geometry import Polygon, Point, MultiPoint
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]


class GardenOrnamental(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((ROOT / 'output/unreal/exterior-garden-20260926-r3/garden-plan.json').read_text())
        cls.beds = {key: unary_union([Polygon([p[:2] for p in tri]) for tri in triangles])
                    for key, triangles in cls.plan['sourceMulchTrianglesCm'].items()}
        cls.stones = unary_union([Polygon([p[:2] for p in tri])
                                 for triangles in cls.plan['sourceStepTrianglesCm'].values() for tri in triangles
                                 if Polygon([p[:2] for p in tri]).area > 1e-7])

    def test_exact_twelve_groups_replace_exact_36_source_cards(self):
        self.assertEqual(len(self.plan['ornamentalPlacements']), 12)
        identities = [key for row in self.plan['ornamentalPlacements'] for key in row['sourceIds']]
        self.assertEqual(identities, [f'DOM_{i:05}' for i in range(1967, 2003)])
        self.assertEqual(identities, self.plan['hideSourceIds'])
        self.assertEqual(len(set(identities)), 36)
        self.assertEqual(sum(row['form'] == 'flowering' for row in self.plan['ornamentalPlacements']), 6)
        self.assertEqual(sum(row['form'] == 'grass' for row in self.plan['ornamentalPlacements']), 6)

    def test_complete_crowns_fit_original_domains_and_clear_all_steps(self):
        outside = []
        for row in self.plan['ornamentalPlacements']:
            point, radius = Point(row['positionCm'][:2]), row['radiusCm']
            self.assertTrue(45 <= radius <= 60)
            if row['sourceBedId']:
                domain = self.beds[row['sourceBedId']]
                self.assertGreaterEqual(point.distance(domain.boundary), radius + 2)
            else:
                outside.append(row['sourceIds'][0])
                domain = MultiPoint([p[:2] for key in row['sourceIds'] for p in self.plan['sourceCardPointsCm'][key]]).convex_hull
                self.assertEqual(row['positionCm'][:2], row['sourcePositionCm'][:2])
                self.assertEqual(row['rootDisplacementCm'], 0)
                self.assertGreaterEqual(point.distance(domain.boundary), radius)
            self.assertTrue(domain.covers(point.buffer(radius, quad_segs=128)))
            self.assertFalse(self.stones.intersects(point.buffer(radius, quad_segs=128)))
            self.assertGreaterEqual(point.distance(self.stones), radius + 4)
        self.assertEqual(outside, ['DOM_01982', 'DOM_01991', 'DOM_01994'])

    def test_source_centers_and_human_scale(self):
        for row in self.plan['ornamentalPlacements']:
            points = self.plan['sourceCardPointsCm'][row['sourceIds'][0]]
            center = [(min(p[k] for p in points) + max(p[k] for p in points)) / 2 for k in (0, 1)]
            self.assertEqual(row['sourcePositionCm'][:2], center)
            self.assertAlmostEqual(math.dist(center, row['positionCm'][:2]), row['rootDisplacementCm'])
            self.assertLessEqual(row['rootDisplacementCm'], 45)
            self.assertTrue((80 <= row['heightCm'] <= 115) if row['form'] == 'flowering' else (90 <= row['heightCm'] <= 125))

    def test_pinned_inputs_and_canonical_architecture(self):
        for path, expected in self.plan['inputFiles'].items():
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(), expected)
        self.assertEqual(self.plan['activeDesign'], {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'})
        self.assertEqual(self.plan['housePlacement']['streetSetbackMm'], 3000)
        self.assertEqual(self.plan['housePlacement']['eastSetbackMm'], 3000)


if __name__ == '__main__':
    unittest.main()
