"""Cushion membership, construction, tilt, topology and actual GLB unit checks."""
import copy
import importlib.util
import math
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('upholstery', Path(__file__).with_name('realism-upholstery-geometry.py'))
U = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(U)


def fixture():
    scene = {'activeDesign': {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'},
             'house': {'placement': {'streetSetbackMm': 3000, 'eastSetbackMm': 3000}}, 'objects': []}
    sources = {}
    for index, number in enumerate(U.NUMBERS):
        id_ = f'DOM_{number:05}'; name, mat = U.expected(number); kind = U.recipe(number)['kind']
        sizes = {'sofa-seat': (795, 965, 190), 'sofa-back': (795, 490, 215),
                 'accent-cushion': (400, 400, 180), 'chair-seat': (460, 470, 82), 'chair-back': (350, 245, 44)}[kind]
        angle = .15 if number == 1452 else .085 if number in U.SOFA_BACKS else 0
        if number in U.SOFA_BACKS or number == 1452:
            axes = ((-1., 0., 0.), (0., -math.sin(angle), math.cos(angle)), (0., math.cos(angle), math.sin(angle)))
        elif number in U.CHAIR_BACKS:
            sign = 1 if number < 1493 else -1
            axes = ((0., sign, 0.), (0., 0., 1.), (sign, 0., 0.))
        else: axes = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.))
        frame = {'centerMm': (index*2000., 1800., 740.), 'axes': axes}
        points = [U.transformed((sx*sizes[0]/2, sy*sizes[1]/2, sz*sizes[2]/2), frame)
                  for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)]
        sources[id_] = {'vertices': points, 'faces': []}
        scene['objects'].append({'id': id_, 'name': name, 'materialNames': [mat], 'materialSlots': ['MAT_test'],
                                 'enabled': True, 'instances': 1, 'metadata': {'babylonCheckCollisions': False}, 'boundsMm': U.bounds(points)})
    return scene, sources


class UpholsteryGeometryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene, cls.sources = fixture()
        cls.meshes, cls.rows = U.build_geometry(cls.scene, cls.sources)

    def test_exact_visual_only_cohort_and_inputs_immutable(self):
        scene, sources = fixture(); original = copy.deepcopy((scene, sources))
        _, rows = U.build_geometry(scene, sources)
        self.assertEqual((scene, sources), original)
        self.assertEqual(len(rows), 20); self.assertLessEqual(sum(row['triangles'] for row in rows), 100000)
        for row in rows:
            id_ = row['sourceIds'][0]
            self.assertEqual(row['hiddenSourceIds'], [])
            self.assertEqual(row['hiddenVisualSourceIds'], ['PH_'+id_])
            self.assertEqual(row['materialBindings'], [{'sourceId': id_, 'sourceSlot': 0, 'visualSourceId': 'PH_'+id_}])

    def test_closed_oriented_body_and_welt_inside_original_envelope(self):
        for row in self.rows:
            self.assertEqual(row['nonManifoldEdges'], 0)
            self.assertLess(row['outwardEnvelopeMm'], 1e-6)
            self.assertGreater(row['minimumTriangleAreaMm2'], 1e-7)
            self.assertEqual([p['kind'] for p in row['parts']], ['closed-cushion', 'restrained-shoulder-welt'])
            self.assertTrue(all(p['signedVolumeMm3'] > 0 for p in row['parts']))
            self.assertLess(row['recipe']['seamRadiusMm'], 1)

    def test_crown_changes_shoulder_without_inflating_center_or_sphere(self):
        half = (397.5, 482.5, 95); spec = U.recipe(1443)
        self.assertEqual(U.deform((0, 0, 95), half, spec), (0, 0, 95))
        shoulder = U.deform((half[0]-34, 0, 95), half, spec)
        self.assertGreater(95-shoulder[2], 10); self.assertLess(95-shoulder[2], 15)
        self.assertEqual(U.deform((0, 0, -95), half, spec), (0, 0, -95))
        self.assertEqual(U.deform((half[0], 0, 0), half, spec), (half[0], 0, 0))

    def test_source_tilt_recovered_and_not_replaced_with_world_aabb(self):
        for row in self.rows:
            number = int(row['sourceIds'][0][4:]); expected = .15 if number == 1452 else .085 if number in U.SOFA_BACKS else 0
            self.assertAlmostEqual(abs(row['frame']['sourceTiltRadians']), expected, places=7)
            if number in U.SOFA_BACKS: self.assertAlmostEqual(row['frame']['halfMm'][2], 107.5, places=6)

    def test_translation_equivariance_preserves_existing_pose(self):
        scene, sources = fixture(); delta = (187.25, -360.5, 33.)
        for row in scene['objects']:
            for key in ('min', 'max'): row['boundsMm'][key] = list(U.add(row['boundsMm'][key], delta))
        for row in sources.values(): row['vertices'] = [U.add(p, delta) for p in row['vertices']]
        after, rows = U.build_geometry(scene, sources)
        for a, b in zip(self.meshes, after):
            for p, q in zip(a.vertices, b.vertices):
                for axis in range(3): self.assertAlmostEqual(q[axis]-p[axis], delta[axis], places=7)

    def test_unreviewed_identity_collision_pose_and_bounds_fail_closed(self):
        for change in ('missing', 'duplicate', 'name', 'material', 'collision', 'motion', 'design', 'setback', 'bounds', 'tilt'):
            scene, sources = fixture()
            if change == 'missing': scene['objects'].pop()
            if change == 'duplicate': scene['objects'].append(copy.deepcopy(scene['objects'][0]))
            if change == 'name': scene['objects'][0]['name'] = 'Different sofa'
            if change == 'material': scene['objects'][0]['materialNames'] = ['stone']
            if change == 'collision': scene['objects'][0]['metadata']['babylonCheckCollisions'] = True
            if change == 'motion': scene['objects'][0]['metadata']['doorMotion'] = 'HINGED'
            if change == 'design': scene['activeDesign']['variant'] = 'A'
            if change == 'setback': scene['house']['placement']['eastSetbackMm'] = 2500
            if change == 'bounds': scene['objects'][0]['boundsMm']['min'][0] -= 1
            if change == 'tilt':
                points = sources['DOM_01444']['vertices']; center = [sum(p[i] for p in points)/len(points) for i in range(3)]
                sources['DOM_01444']['vertices'] = [tuple(center[i]+(p[i]-center[i])*(2 if i == 1 else 1) for i in range(3)) for p in points]
                next(r for r in scene['objects'] if r['id'] == 'DOM_01444')['boundsMm'] = U.bounds(sources['DOM_01444']['vertices'])
            with self.subTest(change=change), self.assertRaises(RuntimeError): U.build_geometry(scene, sources)

    def test_actual_glb_roundtrip_material_slots_and_normals(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'cushions.glb'; U.write_glb(path, self.meshes)
            report = U.inspect_glb(path, self.rows)
            self.assertEqual(report['glbObjectCount'], 20)
            self.assertLess(report['roundtripErrorMm'], .01)
            self.assertTrue(report['glbNormalUnitVerified'])

    def test_deterministic_mesh_topology_and_dimensions(self):
        meshes, rows = U.build_geometry(*fixture())
        self.assertEqual(rows, self.rows)
        self.assertEqual([(m.vertices, m.faces, m.uvs) for m in meshes], [(m.vertices, m.faces, m.uvs) for m in self.meshes])


if __name__ == '__main__': unittest.main()
