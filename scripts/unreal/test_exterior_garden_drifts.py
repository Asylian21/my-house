"""Independent source/GLB checks for the layered C/B/B garden detail."""
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import struct
import unittest

from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path(os.environ.get('BREZI_GARDEN_DRIFTS', str(ROOT/'output/unreal/exterior-garden-drifts-20260930-r1')))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def obj_triangles(path, wanted):
    vertices, current, triangles = [], None, {key:[] for key in wanted}
    for line in Path(path).read_text().splitlines():
        row = line.split()
        if not row:
            continue
        if row[0] == 'v':
            vertices.append([float(row[1])/10, -float(row[2])/10, float(row[3])/10])
        elif row[0] == 'o':
            current = row[1]
        elif row[0] == 'f' and current in wanted:
            face = [vertices[int(p.split('/')[0])-1] for p in row[1:]]
            triangles[current].extend([face[0],face[i],face[i+1]] for i in range(1,len(face)-1))
    return triangles


def position_data(path, node_name):
    data = Path(path).read_bytes()
    length = struct.unpack_from('<I',data,12)[0]
    doc, raw = json.loads(data[20:20+length]), data[28+length:]
    node = next(n for n in doc['nodes'] if n['name']==node_name)
    assert not any(k in node for k in ('matrix','translation','rotation','scale'))
    points = []
    for primitive in doc['meshes'][node['mesh']]['primitives']:
        accessor = doc['accessors'][primitive['attributes']['POSITION']]
        view = doc['bufferViews'][accessor['bufferView']]
        assert accessor['componentType']==5126 and accessor['type']=='VEC3'
        offset = view.get('byteOffset',0)+accessor.get('byteOffset',0)
        stride = view.get('byteStride',12)
        for index in range(accessor['count']):
            x,y,z = struct.unpack_from('<3f',raw,offset+index*stride)
            points.append([100*x,100*z,100*y])
    return points


class GardenDrifts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((OUTPUT/'garden-plan.json').read_text())
        cls.old = json.loads((ROOT/'output/unreal/exterior-garden-morphology-20260927-r6b/garden-plan.json').read_text())
        cls.library = json.loads((ROOT/'output/unreal/exterior-assets-20260927-r6/geometry-manifest.json').read_text())
        cls.meshes = {r['id']:r for r in cls.library['meshes']}
        cls.scene_path = next(Path(p) for p in cls.plan['inputFiles'] if p.endswith('/performance-shipping-20260927-r1/geometry/scene.json'))
        cls.scene = json.loads(cls.scene_path.read_text())
        cls.obj_path = cls.scene_path.with_name('dom-mm.obj')
        cls.bed_ids = {'DOM_01965','DOM_01966'}
        cls.step_ids = {f'DOM_{i:05}' for i in range(1961,1965)}
        protected_ids = {r['id'] for r in cls.scene['objects'] if r['enabled'] and r.get('metadata',{}).get('walkSurface')
                         and r['id'] not in ('DOM_00000','DOM_00001','DOM_00002','DOM_00003','DOM_00004','DOM_00007','DOM_00008',
                                             'DOM_01965','DOM_01966')}
        source = obj_triangles(cls.obj_path, cls.bed_ids|cls.step_ids|protected_ids)
        def shape(ids):
            return unary_union([Polygon([p[:2] for p in triangle]) for key in ids for triangle in source[key]
                                if Polygon([p[:2] for p in triangle]).area>1e-7])
        cls.beds = {key:shape([key]) for key in cls.bed_ids}
        cls.steps, cls.protected = shape(cls.step_ids), shape(protected_ids)
        cls.detail = cls.plan['gardenDetailPlacements']

    def test_unchanged_primary_planting_geometry_and_cadastral_frame(self):
        for key in ('ornamentalPlacements','hideSourceIds','sourceMulchTrianglesCm','sourceStepTrianglesCm',
                    'sourceCardPointsCm','housePlacement','activeDesign','sourceSceneSha256','sourceObjSha256'):
            self.assertEqual(self.plan[key],self.old[key],key)
        self.assertEqual(len(self.plan['ornamentalPlacements']),12)
        self.assertEqual(self.plan['activeDesign'],{'variant':'C','heatingLayout':'B','livingLayout':'B'})
        self.assertEqual(self.plan['housePlacement']['streetSetbackMm'],3000)
        self.assertEqual(self.plan['housePlacement']['eastSetbackMm'],3000)
        self.assertEqual(digest(self.scene_path),self.plan['sourceSceneSha256'])
        self.assertEqual(digest(self.obj_path),self.plan['sourceObjSha256'])

    def test_detail_complete_crowns_clear_source_beds_steps_and_walk_surfaces(self):
        for row in self.detail:
            p, radius = Point(row['positionCm'][:2]), row['radiusCm']
            bed = self.beds[row['sourceBedId']]
            self.assertTrue(bed.covers(p))
            self.assertGreaterEqual(p.distance(bed.boundary)-radius,4)
            self.assertGreaterEqual(p.distance(self.steps)-radius,12)
            self.assertGreaterEqual(p.distance(self.protected)-radius,12)
            self.assertEqual(row['collision'],'NoCollision')
            self.assertGreaterEqual(row['groundSurfaceZCm'], -2.901)
            self.assertLessEqual(row['groundSurfaceZCm'], -2.899)
            self.assertAlmostEqual(row['positionCm'][2]+row['sourceMinimumZCm']*row['uniformScale'],
                                   row['groundSurfaceZCm']+.08, places=7)

    def test_root_spacing_and_nonoverlapping_middle_crowns(self):
        for a,b in itertools.combinations(self.detail,2):
            distance = math.dist(a['positionCm'][:2],b['positionCm'][:2])
            self.assertGreaterEqual(distance,13.5)
            if a['layer']==b['layer']=='middle':
                self.assertGreaterEqual(distance-a['radiusCm']-b['radiusCm'],2)
        for row in (r for r in self.detail if r['layer']=='middle'):
            for original in self.plan['ornamentalPlacements']:
                if original['sourceBedId']==row['sourceBedId']:
                    self.assertGreaterEqual(math.dist(row['positionCm'][:2],original['positionCm'][:2])
                                            -row['radiusCm']-original['radiusCm'],2)

    def test_actual_all_lod_glb_vertices_fit_uniform_scaled_crowns(self):
        for mesh_id in {row['meshId'] for row in self.detail}:
            mesh = self.meshes[mesh_id]
            all_points = [p for lod in mesh['lods'] for p in position_data(mesh['glbPath'],lod['nodeName'])]
            radius = max(math.hypot(p[0],p[1]) for p in all_points)
            lo, hi = min(p[2] for p in all_points), max(p[2] for p in all_points)
            for row in (r for r in self.detail if r['meshId']==mesh_id):
                self.assertEqual(len(set(row['scale'])),1)
                self.assertEqual(row['scale'][0],row['uniformScale'])
                self.assertLessEqual(radius*row['uniformScale'],row['radiusCm']+.001)
                self.assertAlmostEqual(lo,row['sourceMinimumZCm'],places=3)
                self.assertLessEqual((hi-lo)*row['uniformScale'],row['actualHeightCm']+.001)

    def test_input_chain_no_texture_or_asset_rewrite_and_bounded_budget(self):
        for path,pin in self.plan['inputFiles'].items():
            self.assertEqual(digest(path),pin,path)
        for mesh_id in {r['meshId'] for r in self.detail}:
            row = self.meshes[mesh_id]
            self.assertEqual(digest(row['glbPath']),row['glbSha256'])
        self.assertFalse(self.plan['gardenDetailAudit']['sourceTexturePixelsChanged'])
        self.assertEqual(self.plan['gardenDetailAudit']['status'],'PASS_OFFLINE_NOT_NATIVE')
        self.assertGreaterEqual(len(self.detail),200)
        self.assertLessEqual(len(self.detail),550)
        self.assertLessEqual(self.plan['gardenDetailAudit']['detailLodTriangleTotalsBeforeCulling'][0],1800000)
        self.assertEqual({r['sourceBedId'] for r in self.detail},self.bed_ids)
        self.assertTrue(self.plan['gardenDetailPolicy']['replaceGenericGardenUnderstory'])


if __name__ == '__main__':
    unittest.main()
