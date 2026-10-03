"""Independent source, actual triangle, framing and camera exclusion checks."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import unittest

import numpy as np
import shapely
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
spec = importlib.util.spec_from_file_location('grove_floor_views', HERE/'exterior-canopy-growth-views.py')
views = importlib.util.module_from_spec(spec); spec.loader.exec_module(views)
OUTPUT = Path(os.environ.get('BREZI_CANOPY_GROWTH_VIEWS', ROOT/'output/unreal/exterior-canopy-growth-views-20260930-r1'))


def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def independent_blockers(triangles, eye, target):
    """Plane crossing then barycentric inclusion, independent of Moller test."""
    eye, target = np.asarray(eye), np.asarray(target)
    a, b, c = triangles[:, 0], triangles[:, 1], triangles[:, 2]
    ab, ac = b-a, c-a; normal = np.cross(ab, ac)
    start = ((eye-a)*normal).sum(axis=1); end = ((target-a)*normal).sum(axis=1)
    crossing = np.flatnonzero((start*end < 0) & (abs(start-end) > 1e-8))
    if not len(crossing): return []
    fraction = start[crossing]/(start[crossing]-end[crossing])
    point = eye+fraction[:, None]*(target-eye)
    # Oriented edge half-planes avoid cancellation in narrow roof triangles.
    face = triangles[crossing]; n = normal[crossing]; area2 = (n*n).sum(axis=1)
    inside = np.ones(len(crossing), dtype=bool)
    for index in range(3):
        start_vertex, end_vertex = face[:, index], face[:, (index+1)%3]
        side = (np.cross(end_vertex-start_vertex, point-start_vertex)*n).sum(axis=1)
        inside &= side >= -1e-8*area2
    good = (fraction > 1e-5) & (fraction < 1-1e-5) & (area2 > 1e-18) & inside
    return crossing[good].tolist()


class GroveFloorView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest = read(OUTPUT/'viewpoints.json'); cls.view = cls.manifest['views'][0]
        cls.paths = {key: Path(cls.manifest['source'+key]['path']) for key in
                     ('Context', 'Terrain', 'Buildings', 'Scene', 'Ecology', 'Canopy')}
        cls.paths['Diagnostic'] = Path(cls.manifest['priorDiagnosticViews']['path'])
        cls.data = {key: read(path) for key, path in cls.paths.items()}
        cls.original = [row for row in cls.data['Context']['regionalVegetationPlacements'] if row['regionId'] == views.REGION]
        cls.tri = views.SolidTriangles(cls.data['Context'], cls.data['Terrain'], cls.data['Buildings'], views.helper())

    def test_every_frozen_source_and_camera_generator_hash(self):
        manifest = self.manifest
        self.assertEqual(manifest['owner'], views.OWNER); self.assertEqual(manifest['generatorSha256'], sha(HERE/'exterior-canopy-growth-views.py'))
        self.assertEqual(manifest['sourceSceneSha256'], sha(self.paths['Scene']))
        self.assertEqual(manifest['sourceObjSha256'], sha(self.paths['Scene'].parent/'dom-mm.obj'))
        for path, expected in manifest['inputFiles'].items(): self.assertEqual(sha(path), expected, path)
        for key in ('Context', 'Terrain', 'Buildings', 'Scene', 'Ecology', 'Canopy'):
            self.assertEqual(manifest['source'+key]['sha256'], sha(self.paths[key]))
        self.assertFalse(manifest['policy']['nativeExecution']); self.assertFalse(manifest['policy']['nativeAppearanceAccepted'])
        self.assertFalse(manifest['policy']['newGeometry']); self.assertFalse(manifest['policy']['newCollision'])

    def test_original_diagnostic_views_and_all_78_grove_rows_are_unchanged(self):
        self.assertEqual(self.manifest['priorDiagnosticViews']['sha256'], sha(self.paths['Diagnostic']))
        prior = self.data['Diagnostic']['views']
        self.assertEqual([row['id'] for row in prior], ['exterior-canopy-close', 'exterior-canopy-lod', 'exterior-canopy-grove'])
        self.assertEqual([row['id'] for row in self.manifest['views']], ['exterior-canopy-floor'])
        self.assertEqual(self.data['Ecology']['existingTrees'], self.original)
        self.assertEqual(self.data['Canopy']['originalCanopyPlacements'], self.original)
        self.assertEqual(len(self.original), 78)
        self.assertEqual(self.manifest['activeDesign'], {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'})
        self.assertEqual(self.manifest['housePlacement'], self.data['Scene']['house']['placement'])
        self.assertEqual(self.manifest['housePlacement']['eastSetbackMm'], 3000)
        self.assertEqual(self.manifest['housePlacement']['streetSetbackMm'], 3000)

    def test_actual_rendered_ground_clearance_and_unmeasured_evidence(self):
        # Reconstruct the highest triangle Z without calling GroundSampler.sample.
        helper = views.helper(); meshes = self.data['Terrain']['meshes']+[
            m for m in self.data['Context']['meshes'] if m['material'] in helper.GROUND]
        tri = np.concatenate([np.asarray(m['verticesCm'])[np.asarray(m['indices']).reshape(-1, 3)] for m in meshes])
        a, ab, ac = tri[:, 0], tri[:, 1]-tri[:, 0], tri[:, 2]-tri[:, 0]
        determinant = ab[:, 0]*ac[:, 1]-ab[:, 1]*ac[:, 0]
        valid = abs(determinant) > 1e-6
        eye, target = np.asarray(self.view['eyeCm']), np.asarray(self.view['targetCm'])
        clearances = []
        for fraction in np.linspace(0, 1, 113):
            p = eye+(target-eye)*fraction; rel = p[:2]-a[:, :2]
            u = np.divide(rel[:, 0]*ac[:, 1]-rel[:, 1]*ac[:, 0], determinant, out=np.zeros(len(tri)), where=valid)
            v = np.divide(ab[:, 0]*rel[:, 1]-ab[:, 1]*rel[:, 0], determinant, out=np.zeros(len(tri)), where=valid)
            mask = valid & (u >= -1e-8) & (v >= -1e-8) & (u+v <= 1+1e-8)
            self.assertTrue(mask.any())
            z = (a[:, 2]+u*ab[:, 2]+v*ac[:, 2])[mask].max()
            clearances.append(float(p[2]-z)); self.assertAlmostEqual(float(z), -25., places=8)
        self.assertAlmostEqual(clearances[0], 80., places=8); self.assertAlmostEqual(clearances[-1], 12., places=8)
        self.assertGreaterEqual(min(clearances), 12.-1e-8)
        audit = self.manifest['cameraAudits'][0]
        self.assertFalse(audit['eyeGroundMeasured']); self.assertFalse(audit['targetGroundMeasured'])
        self.assertTrue(all(not row['measuredElevation'] for row in audit['centreRayGroundSamples']))
        self.assertEqual(audit['eyeGroundMeshId'], 'context_unresolved_flat_backdrop')

    def test_centre_sightline_has_no_source_solid_or_exclusion_crossing(self):
        eye, target = self.view['eyeCm'], self.view['targetCm']
        self.assertEqual(independent_blockers(self.tri.triangles, eye, target), [])
        corridor = LineString([eye[:2], target[:2]])
        domain = shapely.from_geojson(self.data['Ecology']['ecologyDomainCm'])
        self.assertTrue(domain.contains(corridor.buffer(20)))
        for key, encoded in self.data['Ecology']['exclusionDomainsCm'].items():
            shape = shapely.from_geojson(encoded)
            if not shape.is_empty: self.assertGreater(corridor.distance(shape), 100, key)
        root = next(row for row in self.original if row['id'] == 'village_nearest_grove_3')
        self.assertAlmostEqual(math.dist(eye[:2], root['positionCm'][:2]), 280.)
        self.assertAlmostEqual(math.dist(target[:2], root['positionCm'][:2]), 60.)
        self.assertGreater(corridor.distance(domain.boundary), 200)
        self.assertEqual(self.manifest['cameraAudits'][0]['rayTestTriangleCount'], len(self.tri.triangles))

    def test_real_feature_vertices_in_frame_and_cull_range(self):
        # Require actual LOD0 vertices from every family, not merely bound counts.
        ecology = self.data['Ecology']; records = read(Path(ecology['sourceEcology']['path']).parent/'canopy-ecology-prototypes.json')
        master = {row['nodeName'].removesuffix('_LOD0'): row for row in records if row['level'] == 0}
        eye = np.asarray(self.view['eyeCm']); forward = np.asarray(self.view['targetCm'])-eye; forward /= np.linalg.norm(forward)
        right = np.cross(forward, [0, 0, 1]); right /= np.linalg.norm(right); up = np.cross(right, forward)
        tan_h = math.tan(math.radians(55/2)); tan_v = tan_h/(16/9); visible = set()
        for row in ecology['ecologyPlacements']:
            if math.dist(eye, row['positionCm']) > 800: continue
            record = master[row['meshId']]
            p = np.asarray([p for part in record['parts'].values() for p in part['positionsCm']])
            angle = math.radians(row['yawDeg']); c, s = math.cos(angle), math.sin(angle)
            p = p@np.array([[c, s, 0], [-s, c, 0], [0, 0, 1]])*row['scale'][0]+row['positionCm']-eye
            z, x, y = p@forward, p@right, p@up
            if ((z > 0) & (abs(x) <= z*tan_h) & (abs(y) <= z*tan_v)).any(): visible.add(row['ecologyFamily'])
        self.assertEqual(visible, {'litter', 'twig', 'herb', 'grass'})
        self.assertTrue(all(group['cullEndCm'] >= 8000 for group in ecology['groups']))

    def test_bad_ground_camera_and_output_overwrite_are_rejected(self):
        bad = deepcopy(self.view); bad['eyeCm'][2] = -25.
        with self.assertRaises(ValueError): views.camera_audit(bad, self.data, self.original)
        bad = deepcopy(self.view); bad['targetCm'] = [0., 0., 12.]
        with self.assertRaises(ValueError): views.camera_audit(bad, self.data, self.original)
        with self.assertRaisesRegex(ValueError, 'fresh'):
            views.build(*([None]*7), OUTPUT)
        synthetic = np.array([[[0., -1., -1.], [0., 1., -1.], [0., 0., 1.]]])
        self.assertEqual(independent_blockers(synthetic, [-1., 0., 0.], [1., 0., 0.]), [0])


if __name__ == '__main__': unittest.main()
