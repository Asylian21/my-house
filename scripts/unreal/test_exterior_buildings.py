"""Official footprint invariants, safe world massing and rendered terrain Z."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import unittest

from shapely.geometry import Polygon, Point, MultiPoint
from shapely.ops import unary_union
from shapely.prepared import prep

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('exterior_buildings', ROOT / 'scripts/unreal/exterior-buildings.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class TerrainSampling(unittest.TestCase):
    def test_barycentric_height_on_known_inclined_plane(self):
        mesh = {'id': 'slope', 'verticesCm': [[0, 0, 5], [10, 0, 25], [0, 10, 35]], 'indices': [0, 2, 1]}
        sampler = m.GroundSampler({'meshes': [mesh]})
        self.assertEqual(sampler.sample([2, 3]), (18, 'slope'))
        self.assertEqual(sampler.sample([0, 0]), (5, 'slope'))
        with self.assertRaises(ValueError):
            sampler.sample([10, 10])


class VillageGeometry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = m.read(ROOT / 'output/unreal/exterior-buildings-20260926-r1/building-plan.json')
        cls.source = m.read(ROOT / 'output/unreal/exterior-building-audit-20260926-r1/building-footprints.json')
        cls.context = m.read(ROOT / 'output/unreal/exterior-context-20260926-r5/context-plan.json')
        cls.terrain = m.read(ROOT / 'output/unreal/exterior-terrain-20260926-r4/terrain-plan.json')
        cls.shapes = {b['id']: unary_union([Polygon(rings[0], rings[1:]) for rings in b['polygonsCm']]) for b in cls.plan['buildings']}
        cls.union = unary_union(list(cls.shapes.values()))
        cls.boundaries = unary_union([shape.boundary for shape in cls.shapes.values()])

    def test_source_footprints_are_identical_and_no_point_features_extruded(self):
        expected = {r['id']: r for r in self.source['features'] if r['sourceDistanceMetres'] <= 1000}
        self.assertEqual(len(self.plan['buildings']), 651)
        self.assertEqual(set(self.shapes), set(expected))
        for row in self.plan['buildings']:
            self.assertEqual(row['polygonsCm'], expected[row['id']]['polygonsCm'])
            self.assertEqual(row['sourceHorizontalAccuracyM'], 1.5)
            self.assertEqual(row['heightEvidence'], 'AUTHORED_APPROXIMATION_NO_POPULATED_WFS_HEIGHT_OR_FLOOR_COUNT')
        for path, expected_hash in self.plan['inputFiles'].items():
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(), expected_hash, path)

    def test_no_architectural_or_empty_development_plot_overlap(self):
        protected = unary_union([Polygon(tri) for tri in self.context['protectedTrianglesCm']])
        self.assertLess(self.union.intersection(protected).area, .01)
        self.assertEqual(self.plan['summary']['sourceFootprintsRejected'], [])
        self.assertEqual(self.source['sourceEvidence']['knownDevelopmentParcelIntersections'], [])
        self.assertEqual(self.plan['activeDesign'], {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'})
        self.assertEqual(self.plan['housePlacement']['streetSetbackMm'], 3000)
        self.assertEqual(self.plan['housePlacement']['eastSetbackMm'], 3000)

    def test_geometry_remains_on_footprints_and_roof_normals_face_up(self):
        # Roof eaves may omit only near-collinear vertices at sub-mm precision;
        # source footprint and every facade foundation vertex remain unchanged.
        roof_domain = prep(self.union.buffer(.15))
        for mesh in self.plan['meshes']:
            self.assertLess(len(mesh['indices']) // 3, 20000)
            self.assertTrue(mesh['castShadow'])
            self.assertEqual(mesh['collision'], 'NoCollision')
            self.assertEqual(mesh['maxDrawDistanceCm'], 125000)
            if mesh['material'] == 'context_village_wall':
                self.assertTrue(all(Point(p[:2]).distance(self.boundaries) < .00001 for p in mesh['verticesCm']))
            else:
                for i in range(0, len(mesh['indices']), 3):
                    tri = [mesh['verticesCm'][j] for j in mesh['indices'][i:i+3]]
                    self.assertLess(m.cross(*tri), 0)
                    self.assertTrue(roof_domain.covers(Polygon([p[:2] for p in tri])))

    def test_every_ground_sample_matches_rendered_terrain_and_conservative_heights(self):
        sampler = m.GroundSampler(self.terrain)
        max_error = 0
        for row in self.plan['buildings']:
            self.assertTrue(280 <= row['estimatedWallHeightCm'] <= 330)
            self.assertTrue(140 <= row['estimatedRoofRiseCm'] <= 175)
            for sample in row['renderedGroundSamples']:
                z, identity = sampler.sample(sample['xyCm'])
                self.assertEqual(identity, sample['terrainMeshId'])
                max_error = max(max_error, abs(z - sample['renderedGroundZCm']))
                self.assertLess(Point(sample['xyCm']).distance(self.shapes[row['id']].boundary), .00001)
            self.assertAlmostEqual(row['eaveElevationCm'], row['groundRangeCm'][1] + row['estimatedWallHeightCm'])
        self.assertLess(max_error, .000001)


if __name__ == '__main__':
    unittest.main()
