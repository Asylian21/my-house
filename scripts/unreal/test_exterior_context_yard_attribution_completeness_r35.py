"""Bounded source-only completeness math checks; no native engine fixtures."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
s = importlib.util.spec_from_file_location('r35_complete_source_support', ROOT/'scripts/unreal/exterior-context-yard-attribution-completeness-r35.py')
g = importlib.util.module_from_spec(s)
s.loader.exec_module(g)


class Completeness(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads((g.OUT/'source-completeness.json').read_text())
        cls.ecology = json.loads((ROOT/'output/unreal/exterior-canopy-ecology-20260930-r4/canopy-ecology-plan.json').read_text())
        manifest = g.side(cls.ecology['geometryManifest'])
        cls.models = {m['id']: m for m in manifest['meshes']}
        cls.source = {}
        for m in cls.models.values():
            if m['glbPath'] not in cls.source:
                g.pin(m['glbPath'], m['glbSha256'])
                cls.source[m['glbPath']] = g.glb(m['glbPath'])

    def test_every_actual_aabb_candidate_full_source_vertex_is_enclosed(self):
        excluded = {r['groupId'] for r in self.receipt['groupConservativeSourceBounds'] if r['sourceBoundsExcludedAllRoots']}
        hard = [row['sourceBoundsCm'] for row in self.receipt['sourceHardSurfaces']]
        total = vertices = 0
        for group in self.ecology['groups']:
            if group['id'] in excluded:
                continue
            m = self.receipt['modelFullSourceGeometry'][group['meshId']]['allThreeLodExpectedSourceF32BoundsCm']
            corners = g.np.array([[x,y,z] for x in (m['min'][0],m['max'][0]) for y in (m['min'][1],m['max'][1]) for z in (m['min'][2],m['max'][2])])
            source = self.source[self.models[group['meshId']]['glbPath']]
            for row in group['instances']:
                box = g.transformed_bounds(corners, row)
                if not any(g.overlap(box, b) for b in hard):
                    continue
                total += 1
                rotation, scale, root = g.frame(row)
                for level in range(3):
                    for part in source[group['meshId']+'_LOD'+str(level)]:
                        world = (part['positionsCm']*scale)@rotation+root
                        self.assertTrue(g.np.all(world[:,:2] >= [box[0],box[1]]))
                        self.assertTrue(g.np.all(world[:,:2] <= [box[2],box[3]]))
                        vertices += len(world)
        self.assertEqual(total, 49)
        self.assertGreater(vertices, 10000)

    def test_radius_does_not_limit_transformed_geometry_candidate(self):
        corners = g.np.array([[x,y,z] for x in (8.,12.) for y in (-2.,2.) for z in (0.,3.)])
        row = {'positionCm':[0.,0.,0.], 'yawDeg':0., 'scale':[1.,1.,1.], 'radiusCm':0.}
        box = g.transformed_bounds(corners,row)
        self.assertTrue(g.overlap(box,[9.,-1.,11.,1.]))
        row['radiusCm'] = 100000.
        self.assertEqual(g.transformed_bounds(corners,row),box)

    def test_rotated_anisotropic_bounds_enclose_source_interior_without_epsilon(self):
        points = g.np.array([[x,y,z] for x in (-1.,-.25,2.) for y in (-3.,.75,4.) for z in (-.5,0.,1.5)])
        corners = g.np.array([[x,y,z] for x in (-1.,2.) for y in (-3.,4.) for z in (-.5,1.5)])
        for yaw in (-179.9,-90.,-.001,0.,63.7,90.,179.9):
            row = {'positionCm':[6540.728120406043,28919.610602018693,-24.92], 'yawDeg':yaw, 'scale':[.11,2.39,.62]}
            rotation,scale,root = g.frame(row);world = (points*scale)@rotation+root
            box = g.transformed_bounds(corners,row)
            self.assertTrue(g.np.all(world[:,:2] >= [box[0],box[1]]))
            self.assertTrue(g.np.all(world[:,:2] <= [box[2],box[3]]))

    def test_invalid_authored_frame_rejects_and_census_keeps_native_limits(self):
        row = {'positionCm':[0.,0.,0.], 'yawDeg':0., 'scale':[1.,1.,1.]}
        for k,value in [('scale',[0.,1.,1.]),('scale',[-1.,1.,1.]),('yawDeg',float('nan')),('positionCm',[float('inf'),0.,0.])]:
            invalid = copy.deepcopy(row);invalid[k]=value
            with self.assertRaises(RuntimeError):g.frame(invalid)
        self.assertEqual(self.receipt['census']['completeSourceTriangleSupportCrossings'],34)
        self.assertEqual(self.receipt['comparison']['newTriangleSupportCrossingsAdded'],[])
        self.assertEqual(self.receipt['comparison']['priorTriangleSupportCrossingsRemoved'],[])
        self.assertFalse(self.receipt['sourceBasis']['freshNativePerRootMatricesDecoded'])
        self.assertFalse(self.receipt['nativeExecuted'])


if __name__ == '__main__':
    unittest.main()
