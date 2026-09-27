"""R2 roof geometry, inherited official footprints and facade invariants."""
import hashlib
import importlib.util
import json
from pathlib import Path
import unittest

import numpy as np
import shapely
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('roof_refinement', ROOT / 'scripts/unreal/exterior-building-roofs.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class VillageRoofs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = m.base.read(ROOT / 'output/unreal/exterior-buildings-20260926-r1/building-plan.json')
        cls.plan = m.base.read(ROOT / 'output/unreal/exterior-buildings-20260926-r2/building-plan.json')
        cls.old_rows = {row['id']: row for row in cls.old['buildings']}
        cls.rows = cls.plan['buildings']
        cls.shapes = [Polygon(row['polygonsCm'][0][0], row['polygonsCm'][0][1:]) for row in cls.rows]
        cls.index = STRtree(cls.shapes)
        cls.by_building = {row['id']: [] for row in cls.rows}
        for mesh in cls.plan['meshes']:
            if mesh['material'] == 'context_village_wall':
                continue
            vertices = np.array(mesh['verticesCm'])
            triangles = vertices[np.array(mesh['indices']).reshape((-1, 3))]
            centroids = triangles[:, :, :2].mean(axis=1)
            polygons = shapely.polygons(triangles[:, :, :2])
            matches = cls.index.query(shapely.points(centroids), predicate='within')
            by_triangle = {}
            for tri_index, building_index in matches.T:
                by_triangle.setdefault(int(tri_index), []).append(int(building_index))
            for i, triangle in enumerate(triangles):
                candidates = by_triangle.get(i, [])
                if not candidates:
                    # Sub-mm collinear boundary triangles may have a centroid
                    # numerically on an edge; use footprint intersection then.
                    candidates = list(cls.index.query(polygons[i].buffer(.001)))
                candidates = [int(j) for j in candidates if cls.rows[int(j)]['roofMeshId'] == mesh['id']]
                if not candidates:
                    raise AssertionError('Roof triangle has no source footprint')
                selected = max(candidates, key=lambda j: polygons[i].intersection(cls.shapes[j]).area)
                cls.by_building[cls.rows[selected]['id']].append(triangle.tolist())

    def test_all_official_footprints_facades_foundations_and_render_policy_unchanged(self):
        old_mesh = {mesh['id']: mesh for mesh in self.old['meshes']}
        for mesh in self.plan['meshes']:
            if mesh['material'] == 'context_village_wall':
                self.assertEqual(mesh, old_mesh[mesh['id']])
            self.assertEqual(mesh['collision'], 'NoCollision')
            self.assertTrue(mesh['castShadow'])
            self.assertEqual(mesh['maxDrawDistanceCm'], 125000)
            self.assertLess(len(mesh['indices']) // 3, 20000)
        for row in self.rows:
            old = self.old_rows[row['id']]
            for key in ('polygonsCm', 'cell', 'wallMeshId', 'roofMeshId', 'roofMaterial', 'sourceDistanceMetres',
                        'sourceAreaM2', 'sourceHorizontalAccuracyM', 'heightEvidence', 'estimatedWallHeightCm',
                        'eaveElevationCm', 'renderedGroundSamples', 'groundRangeCm'):
                self.assertEqual(row[key], old[key], (row['id'], key))
        self.assertEqual(self.plan['renderPolicy'], self.old['renderPolicy'])
        self.assertEqual(self.plan['terrainPlan'], self.old['terrainPlan'])
        self.assertEqual(self.plan['activeDesign'], self.old['activeDesign'])
        self.assertEqual(self.plan['housePlacement'], self.old['housePlacement'])

    def test_all_complex_roofs_follow_the_estimated_height_field_with_upward_normals(self):
        refined = 0
        for row, shape in zip(self.rows, self.shapes):
            triangles = np.array(self.by_building[row['id']])
            self.assertGreater(len(triangles), 0, row['id'])
            ab, ac = triangles[:, 1] - triangles[:, 0], triangles[:, 2] - triangles[:, 0]
            # Clockwise UE triangles: AC cross AB is the outward normal.
            normals = np.cross(ac, ab)
            self.assertTrue(np.all(normals[:, 2] > 0), row['id'])
            if row['roofStyles'] != [m.STYLE]:
                continue
            refined += 1
            vertices = triangles.reshape((-1, 3))
            distances = shapely.distance(shapely.points(vertices[:, :2]), shape.boundary)
            predicted = row['eaveElevationCm'] + np.minimum(150, .65 * distances)
            self.assertLess(float(np.abs(predicted - vertices[:, 2]).max()), .000001, row['id'])
            self.assertGreater(float((vertices[:, 2] - row['eaveElevationCm']).max()), 1, row['id'])
            self.assertLessEqual(float((vertices[:, 2] - row['eaveElevationCm']).max()), 150.000001)
            self.assertEqual(row['roofRefinement']['evidence'], 'AUTHORED_APPROXIMATION_NOT_ROOF_MEASUREMENT')
        self.assertEqual(refined, 409)

    def test_roof_coverage_preserves_every_complex_polygon_and_courtyard_hole(self):
        for row, shape in zip(self.rows, self.shapes):
            if row['roofStyles'] != [m.STYLE]:
                continue
            triangles = [Polygon([p[:2] for p in tri]) for tri in self.by_building[row['id']]]
            covered = unary_union(triangles)
            self.assertLess(covered.symmetric_difference(shape).area, .1, row['id'])
            self.assertLess(sum(p.area for p in triangles) - covered.area, .1, row['id'])
            self.assertTrue(shape.buffer(.00001).covers(covered), row['id'])

    def test_simple_hip_roof_triangles_remain_exactly_the_same(self):
        old_triangles = set()
        for mesh in self.old['meshes']:
            if mesh['material'] == 'context_village_wall':
                continue
            for i in range(0, len(mesh['indices']), 3):
                old_triangles.add(tuple(tuple(mesh['verticesCm'][j]) for j in mesh['indices'][i:i+3]))
        simple = 0
        for row in self.rows:
            if row['roofStyles'] == [m.STYLE]:
                continue
            simple += 1
            self.assertEqual(row['roofStyles'], self.old_rows[row['id']]['roofStyles'])
            for tri in self.by_building[row['id']]:
                self.assertIn(tuple(tuple(p) for p in tri), old_triangles)
        self.assertEqual(simple, 242)

    def test_inputs_are_pinned_and_revision_is_bounded(self):
        for path, expected in self.plan['inputFiles'].items():
            self.assertEqual(hashlib.sha256(Path(path).read_bytes()).hexdigest(), expected, path)
        self.assertEqual(self.plan['derivedFrom']['sha256'], m.base.sha(self.plan['derivedFrom']['path']))
        self.assertEqual(self.plan['summary']['buildingCount'], 651)
        self.assertEqual(self.plan['summary']['sourceHeightFieldsPopulated'], 0)
        self.assertLess(self.plan['summary']['triangles'], 100000)
        self.assertNotIn(m.FALLBACK, self.plan['summary']['roofStyles'])


if __name__ == '__main__':
    unittest.main()
