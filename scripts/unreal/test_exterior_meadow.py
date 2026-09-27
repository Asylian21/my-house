"""Independent spatial density and frozen-source checks for R5 meadow base."""
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import unittest

from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely.prepared import prep
from shapely import set_precision

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('exterior_context', HERE / 'exterior-context.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class MeadowDensity(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = m.ROOT / 'output/unreal/exterior-context-20260926-r5'
        cls.path = cls.directory / 'context-plan.json'
        cls.plan = json.loads(cls.path.read_text())
        cls.previous = json.loads((m.ROOT / 'output/unreal/exterior-context-20260926-r4/context-plan.json').read_text())
        cls.selected = {r['meshId']: r for r in cls.plan['surfaces'] if r['material'] == 'context_meadow'}
        # Floating triangulation edges can survive a global GEOS union as
        # zero-area internal seams. A 1-micrometre analysis grid removes only
        # those seams; source meshes and all original float positions stay exact.
        triangles = [Polygon([mesh['verticesCm'][j][:2] for j in mesh['indices'][i:i + 3]])
                     for mesh in cls.plan['meshes'] if mesh['id'] in cls.selected
                     for i in range(0, len(mesh['indices']), 3)]
        cls.raw_union = unary_union(triangles)
        cls.union = unary_union([set_precision(triangle, .0001) for triangle in triangles])
        cls.protected = unary_union([Polygon(tri) for tri in cls.plan['protectedTrianglesCm']])
        cls.points = cls.plan['meadowBasePlacements']

    def test_all_existing_fields_and_immutable_inputs_preserved(self):
        for key, value in self.previous.items():
            if key == 'generatorSha256':
                continue
            self.assertEqual(self.plan[key], value, key)
            expected = hashlib.sha256(m.json_bytes(value)).hexdigest()
            self.assertEqual(self.plan['derivedFrom']['preservedFieldHashes'][key], expected)
        self.assertEqual(self.plan['generatorSha256'], m.sha(HERE / 'exterior-context.py'))
        self.assertEqual(self.plan['derivedFrom']['sha256'], m.sha(self.plan['derivedFrom']['path']))
        receipt = json.loads((self.directory / 'build-environment.json').read_text())
        for path, expected in receipt['inputFiles'].items():
            self.assertEqual(m.sha(path), expected, path)

    def test_every_whole_crown_is_on_meadow_and_clear_of_original_road(self):
        self.assertLess(self.raw_union.symmetric_difference(self.union).area, 100)
        prepared = prep(self.union)
        for row in self.points:
            p = Point(row['positionCm'][:2])
            self.assertTrue(prepared.covers(p))
            # Exact line-boundary distance implies the complete 22cm circle fits,
            # including between discrete circle vertices and at concave edges.
            self.assertGreaterEqual(p.distance(self.union.boundary), 22)
            self.assertGreaterEqual(p.distance(self.protected), 25)
            self.assertLessEqual(math.hypot(*row['positionCm'][:2]) + row['radiusCm'], 9000)
            self.assertIn(row['sourceMeshId'], self.selected)

    def test_budget_height_cull_and_road_shoulders(self):
        self.assertTrue(20000 <= len(self.points) <= 35000)
        self.assertGreater(sum(p['sourceFinish'] == 'shoulder' for p in self.points), 1000)
        for row in self.points:
            self.assertEqual(row['role'], 'grass')
            self.assertEqual(row['radiusCm'], 22)
            self.assertTrue(18 <= row['heightCm'] <= 25)
            self.assertEqual(row['cullEndCm'], 9000)
        self.assertLessEqual(self.plan['meadowBasePolicy']['cullEndCm'], 9000)

    def test_continuous_coverage_at_five_metre_scale(self):
        eligible = self.union.buffer(-22).intersection(Point(0, 0).buffer(8978, quad_segs=256))
        counts = Counter((math.floor(p['positionCm'][0] / 500), math.floor(p['positionCm'][1] / 500)) for p in self.points)
        audited = 0
        for x in range(-18, 18):
            for y in range(-18, 18):
                shape = eligible.intersection(box(x * 500, y * 500, (x + 1) * 500, (y + 1) * 500))
                area = shape.area / 10000
                if area < 10:
                    continue
                audited += 1
                self.assertGreater(counts[(x, y)], 0, (x, y, area))
                self.assertGreater(counts[(x, y)] / area, .8, (x, y, area))
        self.assertGreater(audited, 350)


if __name__ == '__main__':
    unittest.main()
