"""Six focused R43 source contracts, no Unreal or historical producer replay."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('r43_source', Path(__file__).with_name('exterior-context-parcel-boundary-study-r43.py'))
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)


class BoundarySourceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = g.load_inputs()
        cls.materials = g.material_proposals(cls.data)
        cls.geometry = g.build_geometry(cls.data)

    def test_mapped_holes_strip_and_illustrative_division(self):
        self.assertEqual(set(self.data['parcels']), {'4184/2', '4184/3', '4215/5'})
        self.assertEqual(len(self.data['parcelRows']), 3)
        cottage = self.data['feet']['BU.572063']
        self.assertEqual(cottage.intersection(self.data['parcels']['4184/2']).area, 0)
        big_house = self.data['feet']['BU.3852341']
        self.assertEqual(big_house.intersection(self.data['parcels']['4184/3']).area, 0)
        wrong = copy.deepcopy(self.data['selection']); wrong['fullPhotorealismAccepted'] = True
        with self.assertRaises(ValueError): g.validate_selection(wrong)

    def test_full_ground_face_support_is_not_a_flat_height_assumption(self):
        meshes = [{'id': 'slope', 'material': 'context_distant_terrain',
                   'verticesCm': [[0, 0, 0], [10, 0, 10], [0, 10, 0]], 'indices': [0, 1, 2]},
                  {'id': 'flat', 'material': 'context_distant_terrain',
                   'verticesCm': [[0, 0, 2], [10, 0, 2], [0, 10, 2]], 'indices': [0, 1, 2]}]
        ground = g.Ground(meshes, g.box(0, 0, 10, 10))
        self.assertEqual(ground.at([1, 1])['zCm'], 2)
        self.assertEqual(ground.at([6, 1])['zCm'], 6)
        result = ground.footprint(g.box(1, 1, 3, 3))
        self.assertEqual(result['maximumExistingGroundZCm'], 3)
        self.assertEqual(len(result['intersectedSourceFaces']), 2)
        with self.assertRaises(ValueError): ground.footprint(g.box(9, 9, 11, 11))

    def test_actual_open_gates_and_pedestrian_footprint_reject_intrusion(self):
        geom = self.geometry
        self.assertEqual([r['openAngleDegrees'] for r in geom['openGates']], [135, 90])
        self.assertEqual(geom['connector']['widthCm'], 120)
        self.assertTrue(self.data['parcels']['4184/2'].covers(g.shape(geom['connector']['sourceDomainCm'])))
        row = g.box_mesh([6420, 28250], [6500, 28250], -25, 90, 8, 'wood', 'intruding-post', '4184/2')
        with self.assertRaises(ValueError):
            g.validate_solids([row], self.data, g.shape(geom['connector']['sourceDomainCm']))

    def test_real_bevels_metric_grain_normals_and_winding(self):
        row = g.box_mesh([0, 0], [240, 0], 0, 7, 4, 'wood', 'test-rail', '4184/2')
        self.assertEqual(row['edgeBevelCm'], .2)
        self.assertEqual(len(row['indices'])//3, 44)
        self.assertGreater(g.signed_volume(row), 0)
        self.assertEqual(len(row['uv0']), len(row['verticesCm']))
        self.assertEqual(len(row['normals']), len(row['verticesCm']))
        reversed_row = copy.deepcopy(row)
        reversed_row['indices'] = [i for face in g.np.asarray(row['indices']).reshape(-1, 3)[:, ::-1] for i in face.tolist()]
        self.assertLess(g.signed_volume(reversed_row), 0)
        self.assertTrue(all(r['conservativeFrontElevationOpenFraction'] >= .70 for r in self.geometry['openness']))

    def test_camera_front_frustum_and_behind_rejection(self):
        camera = {'eyeCm': [0, 0, 10], 'targetCm': [0, 100, 10], 'horizontalFovDegrees': 72}
        front = g.box_mesh([-20, 100], [20, 100], 0, 20, 4, 'wood', 'front', '4184/2')
        behind = g.box_mesh([-20, -100], [20, -100], 0, 20, 4, 'wood', 'back', '4184/2')
        self.assertGreater(g.screen_support([front], camera).area, 0)
        self.assertTrue(g.screen_support([behind], camera).is_empty)
        self.assertEqual({r['id'] for r in self.data['cameras']}, {'exterior-context-yard-572063-close-r18', 'exterior-neighborhood-ground-r38'})

    def test_original_photo_channels_and_source_scope(self):
        self.assertEqual(self.materials['wood']['metricTileCm'], 150)
        self.assertEqual(self.materials['gravel']['metricTileCm'], 200)
        self.assertEqual(set(self.materials['wood']['maps']), {'diffuse', 'normal', 'roughness'})
        self.assertTrue(all(not rec['pixelEdits'] for key in ('wood', 'gravel') for rec in self.materials[key]['maps'].values()))
        self.assertEqual(len(self.geometry['segments']), 6)
        self.assertTrue(all(not r['collision'] for r in self.geometry['objects']))
        self.assertTrue(all(not r['mappedLegalFence'] for r in self.geometry['segments']))


if __name__ == '__main__':
    unittest.main(verbosity=2)
