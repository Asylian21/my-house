"""Geometry/evidence checks for the contextual cadastral layer, no native UE."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('exterior_context', HERE / 'exterior-context.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class ContextGeometry(unittest.TestCase):
    def test_active_c3_rounding_precedes_client_translation(self):
        scene = {'cadastralDatumSjtskMm': {'x': 10, 'y': 20},
                 'siteAxis': {'ux': 1, 'uy': 0, 'vx': 0, 'vy': 1},
                 'housePlacement': {'translationMm': {'x': .25, 'y': 0}},
                 'sceneCenterMm': {'x': 0, 'y': 0}}
        self.assertEqual(m.to_unreal([10.5, 20.5], scene), (.075, -.1))
        self.assertEqual(m.js_round(-.5), 0)

    def test_polygon_difference_preserves_area_without_overlap(self):
        square = [(0, 0), (10, 0), (10, 10), (0, 10)]
        cutter = [(3, 3), (7, 3), (7, 7), (3, 7)]
        pieces = m.subtract_convex(square, cutter)
        self.assertAlmostEqual(sum(abs(m.area(p)) for p in pieces), 84)
        for piece in pieces:
            clipped = m.intersect_convex(piece, cutter)
            self.assertLess(abs(m.area(clipped)) if clipped else 0, 1e-7)
        for i, a in enumerate(pieces):
            for b in pieces[i + 1:]:
                overlap = m.intersect_convex(a, m.ccw(b))
                self.assertLess(abs(m.area(overlap)) if overlap else 0, 1e-7)

    def test_disjoint_exclusion_does_not_remove_polygon(self):
        square = [(0, 0), (10, 0), (10, 10), (0, 10)]
        pieces = m.subtract_convex(square, [(20, 20), (30, 20), (30, 30), (20, 30)])
        self.assertAlmostEqual(sum(abs(m.area(p)) for p in pieces), 100)

    def test_road_holes_are_retained_by_triangulation(self):
        outer = [[0, 0], [10, 0], [10, 10], [0, 10], [0, 0]]
        hole = [[3, 3], [3, 7], [7, 7], [7, 3], [3, 3]]
        data = m.earcut_many([[outer, hole]])[0]
        triangles = [[data['points'][j] for j in data['indices'][i:i + 3]] for i in range(0, len(data['indices']), 3)]
        self.assertAlmostEqual(sum(abs(m.area(t)) for t in triangles), 84)
        self.assertTrue(all(not m.within((5, 5), t) for t in triangles))

    def test_snapshot_writer_refuses_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'snapshot'
            m.immutable_write(path, b'original')
            m.immutable_write(path, b'original')
            with self.assertRaises(ValueError):
                m.immutable_write(path, b'changed')
            self.assertEqual(path.read_bytes(), b'original')

    def test_source_exclusion_and_context_clipping(self):
        triangle = [(-20, -20), (20, -20), (0, 20)]
        boundary = [(-10, -10), (10, -10), (10, 10), (-10, 10)]
        cutter = [(-2, -2), (2, -2), (0, 2)]
        pieces = m.safe_fragments(triangle, [(cutter, m.bounds(cutter))], boundary)
        self.assertTrue(pieces)
        for piece in pieces:
            self.assertTrue(all(-10 - 1e-8 <= v <= 10 + 1e-8 for p in piece for v in p))
            overlap = m.intersect_convex(piece, cutter)
            self.assertLess(abs(m.area(overlap)) if overlap else 0, 1e-7)

    def test_upward_unreal_clockwise_winding(self):
        mesh = m.Mesh('check', 'context_meadow')
        mesh.surface([(0, 0), (100, 0), (100, 100), (0, 100)])
        data = mesh.data()
        for i in range(0, len(data['indices']), 3):
            points = [data['verticesCm'][j] for j in data['indices'][i:i + 3]]
            self.assertLess(m.cross(*points), 0)

    def test_wire_prototype_clockwise_normals_face_outward(self):
        wire = m.vineyard_prototypes()[1]
        for i in range(0, 36, 3):
            a, b, c = [wire['verticesCm'][j] for j in wire['indices'][i:i + 3]]
            ab, ac = [[p[k] - a[k] for k in range(3)] for p in (b, c)]
            normal = [ac[1] * ab[2] - ac[2] * ab[1], ac[2] * ab[0] - ac[0] * ab[2], ac[0] * ab[1] - ac[1] * ab[0]]
            center = [(a[k] + b[k] + c[k]) / 3 for k in range(3)]
            self.assertGreater(normal[1] * center[1] + normal[2] * center[2], 0)


class CurrentPlanEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = m.ROOT / 'output/unreal/exterior-context-20260926-r4'
        path = directory / 'context-plan.json'
        if not path.exists():
            raise unittest.SkipTest('Generate the new context plan to run receipt/geometry verification')
        cls.plan = json.loads(path.read_text())
        cls.directory = directory

    def test_official_snapshot_has_all_embedded_parcels_and_road_holes(self):
        plan = self.plan
        self.assertEqual(m.sha(self.directory / 'inputs/cuzk-parcels.gml'), plan['sourceEvidence']['sha256'])
        self.assertEqual(len(plan['existingParcelComparison']['matched']), 13)
        parcels = {p['parcelNumber']: p for p in plan['parcels']}
        self.assertEqual(len(parcels['6012/1']['polygonsSjtskMm'][0]), 4)
        self.assertEqual(plan['housePlacement']['streetSetbackMm'], 3000)
        self.assertEqual(plan['housePlacement']['eastSetbackMm'], 3000)

    def test_added_surfaces_never_cover_protected_subject_or_road(self):
        exclusions = [(p, m.bounds(p)) for p in self.plan['protectedTrianglesCm']]
        prototypes = {group['meshId'] for group in self.plan['groups']}
        for mesh in self.plan['meshes']:
            if mesh['id'] in prototypes:
                continue
            for i in range(0, len(mesh['indices']), 3):
                tri = m.ccw([p[:2] for p in [mesh['verticesCm'][j] for j in mesh['indices'][i:i + 3]]])
                box = m.bounds(tri)
                for excluded, exclusion_box in exclusions:
                    if m.overlap(box, exclusion_box):
                        overlap = m.intersect_convex(tri, excluded)
                        self.assertLess(abs(m.area(overlap)) if overlap else 0, 1e-3, mesh['id'])

    def test_placements_are_low_and_outside_protected_geometry(self):
        self.assertTrue(self.plan['treePlacements'])
        self.assertLessEqual(len(self.plan['boundaryPosts']), 12)
        for plant in self.plan['treePlacements']:
            if plant['semantic'] == 'vineyard-row':
                self.assertIn(plant['parcelNumber'], ('6015', '6034'))
                self.assertTrue(125 <= plant['heightCm'] <= 175)
            else:
                self.assertEqual(plant['semantic'], 'garden-margin-tree')
                self.assertEqual(plant['parcelNumber'], '6014')
                self.assertEqual(plant['crownDiameterCm'], 300)
            point = plant['positionCm'][:2]
            self.assertFalse(any(m.within(point, p) for p in self.plan['protectedTrianglesCm']))

    def test_canopies_and_ground_cover_have_whole_footprint_clearance(self):
        garden_trees = [p for p in self.plan['treePlacements'] if p['semantic'] == 'garden-margin-tree']
        self.assertEqual(len(garden_trees), 4)
        self.assertTrue(self.plan['groundCoverPlacements'])
        for plant in [*garden_trees, *self.plan['groundCoverPlacements'], *self.plan['boundaryPosts']]:
            point = plant['positionCm'][:2]
            radius = plant.get('crownDiameterCm', 0) / 2 or plant.get('radiusCm', 3)
            for polygon in self.plan['protectedTrianglesCm']:
                self.assertFalse(m.within(point, polygon))
                self.assertGreaterEqual(min(m.segment_distance(point, a, b) for a, b in zip(polygon, polygon[1:] + polygon[:1])), radius)

    def test_stakes_are_instanced_and_not_duplicated_as_world_meshes(self):
        self.assertEqual(len(self.plan['groups']), 3)
        group = next(g for g in self.plan['groups'] if g['id'] == 'context_boundary_stakes')
        self.assertEqual(group['meshId'], 'context_boundary_stake')
        self.assertEqual(len(group['instances']), 12)
        prototype = next(mesh for mesh in self.plan['meshes'] if mesh['id'] == group['meshId'])
        self.assertEqual(max(p[2] for p in prototype['verticesCm']), 32)
        self.assertEqual(min(p[2] for p in prototype['verticesCm']), 0)
        self.assertEqual(len(prototype['indices']) // 3, 12)

    def test_physical_roads_partition_exact_legal_corridors(self):
        from shapely.geometry import Polygon
        from shapely.ops import unary_union
        scene = json.loads((m.ROOT / 'output/unreal/realism-20260926-r5/geometry/scene.json').read_text())
        parcels = {p['parcelNumber']: p for p in self.plan['parcels']}
        for number in ('6012/1', '6035/1', '6013', '6019'):
            legal = unary_union([Polygon([m.to_unreal(p, scene) for p in rings[0]],
                                         [[m.to_unreal(p, scene) for p in ring] for ring in rings[1:]])
                                 for rings in parcels[number]['polygonsSjtskMm']])
            finishes = [part for part in self.plan['roadFinishPolicy']['parts'] if part['parcelNumber'] == number]
            shapes = {part['finish']: unary_union([Polygon(rings[0], rings[1:]) for rings in part['polygonsCm']])
                      for part in finishes}
            self.assertLess(legal.symmetric_difference(shapes['core'].union(shapes['shoulder'])).area, .1)
            self.assertLess(shapes['core'].intersection(shapes['shoulder']).area, .1)
            self.assertLess(shapes['core'].area, legal.area * .8)
            self.assertGreater(shapes['shoulder'].area, 10000)
            for part in finishes:
                self.assertEqual(part['material'], 'context_track' if part['finish'] == 'core' else 'context_meadow')

    def test_vineyards_are_dense_and_trellis_segments_are_crown_safe(self):
        from shapely.geometry import Polygon, LineString
        from shapely.ops import unary_union
        scene = json.loads((m.ROOT / 'output/unreal/realism-20260926-r5/geometry/scene.json').read_text())
        parcels = {p['parcelNumber']: p for p in self.plan['parcels']}
        legal = unary_union([Polygon([m.to_unreal(p, scene) for p in rings[0]],
                                     [[m.to_unreal(p, scene) for p in ring] for ring in rings[1:]])
                             for number in ('6015', '6034') for rings in parcels[number]['polygonsSjtskMm']])
        blockers = unary_union([Polygon(poly) for poly in self.plan['protectedTrianglesCm']])
        vines = [p for p in self.plan['treePlacements'] if p['semantic'] == 'vineyard-row']
        self.assertGreater(len(vines), 2500)
        self.assertEqual(self.plan['vineyardPolicy']['stationSpacingCm'], 110)
        self.assertEqual(self.plan['vineyardPolicy']['rowSpacingCm'], 240)
        import math
        for vine in vines:
            from shapely.geometry import Point
            canopy = Point(vine['positionCm'][:2]).buffer(vine['crownDiameterCm'] / 2)
            self.assertTrue(legal.covers(canopy))
            self.assertFalse(blockers.intersects(canopy))
        group = next(g for g in self.plan['groups'] if g['id'] == 'context_vine_wires')
        self.assertGreater(len(group['instances']), 500)
        for instance in group['instances']:
            a = instance['positionCm'][:2]
            yaw, length = math.radians(instance['yawDeg']), 600 * instance['scale'][0]
            self.assertLessEqual(length, 600.001)
            b = [a[0] + length * math.cos(yaw), a[1] + length * math.sin(yaw)]
            line = LineString([a, b]).buffer(.25)
            self.assertTrue(legal.covers(line))
            self.assertFalse(blockers.intersects(line))


if __name__ == '__main__':
    unittest.main()
