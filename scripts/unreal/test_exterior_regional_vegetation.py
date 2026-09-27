"""Geometry and evidence checks on the isolated regional canopy revision."""
from pathlib import Path
import hashlib
import importlib.util
import itertools
import json
import math
import unittest

from PIL import Image
import numpy as np
import shapely
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
PATH = ROOT/'output/unreal/exterior-context-20260927-r8/context-plan.json'
SPEC = importlib.util.spec_from_file_location('regional', ROOT/'scripts/unreal/exterior-regional-vegetation.py')
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)


class RegionalCanopyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(PATH.read_text())
        cls.source = M.read(cls.plan['derivedFrom']['path'])
        cls.policy = cls.plan['regionalVegetationPolicy']
        cls.assets = {m['id']:m for m in M.read(cls.policy['assetManifestPath'])['meshes']}
        cls.rows = cls.plan['regionalVegetationPlacements']
        cls.regions = {r['id']:Polygon(r['polygonCm']) for r in cls.policy['regions']}
        cls.blocked = M.constraints(cls.source, M.read(M.BUILDINGS), M.read(M.SCENE))

    def test_all_frozen_geometry_and_inputs_are_preserved(self):
        self.assertEqual(self.plan['owner'], M.OWNER)
        self.assertEqual(self.plan['generatorSha256'], M.sha(ROOT/self.plan['owner']))
        for key, digest in self.plan['derivedFrom']['preservedFieldHashes'].items():
            self.assertEqual(M.digest(self.plan[key]), digest, key)
            self.assertEqual(self.plan[key], self.source[key], key)
        for path, digest in self.plan['inputFiles'].items():
            self.assertEqual(M.sha(path), digest, path)
        self.assertEqual(self.plan['treePlacements'], [r for r in self.source['treePlacements'] if r['semantic'] != 'garden-margin-tree'])
        self.assertEqual(len(self.plan['derivedFrom']['removedGardenMarginTrees']), 4)
        self.assertEqual(len(self.plan['meadowBladePlacements']), 382678)
        self.assertEqual(self.plan['housePlacement']['streetSetbackMm'], 3000)
        self.assertEqual(self.plan['housePlacement']['eastSetbackMm'], 3000)

    def test_every_transformed_lod_corner_and_crown_clears_protected_geometry(self):
        for row in self.rows:
            with self.subTest(id=row['id']):
                x,y,z = row['positionCm']; scale=row['scale'][0]
                self.assertEqual(row['scale'], [scale]*3)
                radius=row['radiusCm']; point=Point(x,y); region=self.regions.get(row['regionId'])
                clearance=row.get('requiredProtectedCrownClearanceCm',75)
                if region:
                    self.assertTrue(region.contains(point))
                    self.assertGreaterEqual(point.distance(region.boundary)-radius, 10-1e-6)
                for shape in self.blocked.values():
                    self.assertGreaterEqual(point.distance(shape)-radius, clearance-1e-6)
                angle=math.radians(row['yawDeg']);c,s=math.cos(angle),math.sin(angle)
                for lod in self.assets[row['meshId']]['lods']:
                    b=lod['expectedBoundsCm']
                    for p in itertools.product(*[(b['min'][i],b['max'][i]) for i in range(3)]):
                        corner=Point(x+scale*(p[0]*c-p[1]*s),y+scale*(p[0]*s+p[1]*c))
                        self.assertLessEqual(corner.distance(point),radius+1e-6)
                        if region:self.assertTrue(region.contains(corner))
                        self.assertTrue(all(corner.distance(shape)>=clearance-1e-6 for shape in self.blocked.values()))

    def test_imagery_and_height_claims_are_bounded(self):
        manifest=M.read(M.ORTHO);layer=next(v for v in manifest['layers'] if v['id']=='detail2km')
        image=Image.open(layer['rgbaPath'])
        for row in self.rows:
            point=row['positionCm'][:2];pix=M.world_to_pixel(point,layer)
            if 'sourceImageWitness' in row:
                rgba=list(image.getpixel(tuple(math.floor(v) for v in pix)))
                self.assertEqual(rgba,row['sourceImageWitness']['sourcePixelRgba'])
                self.assertEqual(rgba[3],255)
                self.assertGreaterEqual(row['sourceImageWitness']['crownGreenSampleFraction'],.56)
            else:
                self.assertEqual(row['form'],'garden-margin-concept')
                self.assertLessEqual(row['radiusCm'],150)
            self.assertIn('NOT_SURVEYED',row['sourceEvidence'])
            self.assertLessEqual(math.hypot(*point)+row['radiusCm'],110000)
            self.assertLessEqual(row['heightCm'],1000)
            self.assertGreaterEqual(row['heightCm'],125 if row['form'] in ('hedge','garden-margin-concept') else 400)
            actual_low=min(lod['expectedBoundsCm']['min'][2] for lod in self.assets[row['meshId']]['lods'])*row['scale'][0]+row['positionCm'][2]
            self.assertAlmostEqual(actual_low,row['renderedGround']['zCm'],places=6)

    def test_independent_root_spacing_and_cluster_membership(self):
        self.assertGreaterEqual(len(self.rows),400)
        self.assertEqual(len({r['regionId'] for r in self.rows}),16)
        self.assertEqual(len({r['id'] for r in self.rows}),len(self.rows))
        for a,b in itertools.combinations(self.rows,2):
            self.assertGreaterEqual(math.dist(a['positionCm'][:2],b['positionCm'][:2]),max(120,.65*(a['radiusCm']+b['radiusCm']))-1e-6)

    def test_affine_annotations_round_trip_and_known_origin(self):
        layer=next(v for v in M.read(M.ORTHO)['layers'] if v['id']=='detail2km')
        self.assertLess(math.hypot(*M.image_to_world([800,800],layer)),1e-6)
        for px in ([0,0],[1600,0],[1600,1600],[0,1600],[350,780]):
            restored=M.world_to_pixel(M.image_to_world(px,layer),layer)
            for a,b in zip(restored,px):self.assertAlmostEqual(a,b*4096/1600,places=8)

    def test_new_understory_full_crown_surface_and_barycentric_elevation(self):
        rows=self.plan['meadowUnderstoryPlacements']
        self.assertTrue(80000<=len(rows)<=90000)
        protected=unary_union([Polygon(tri) for tri in self.plan['protectedTrianglesCm']])
        xyz=np.asarray([r['positionCm'] for r in rows]);points=shapely.points(xyz[:,:2])
        self.assertGreaterEqual(float(shapely.distance(points,protected).min()),30)
        self.assertLessEqual(float(np.linalg.norm(xyz[:,:2],axis=1).max())+14,7500)
        by_mesh={}
        for i,row in enumerate(rows):by_mesh.setdefault(row['sourceMeshId'],[]).append(i)
        eligible_shapes=[]
        for mesh in self.plan['meshes']:
            if mesh['id'] not in by_mesh:continue
            self.assertIn(mesh['material'],('context_fallow','context_crop','context_arable'))
            coords=np.asarray(mesh['verticesCm'])[np.asarray(mesh['indices']).reshape(-1,3)]
            polygons=[Polygon(tri[:,:2]) for tri in coords]
            shape=unary_union([shapely.set_precision(p,.0001) for p in polygons])
            eligible_shapes.append(shape)
            index=np.asarray(by_mesh[mesh['id']]);p=points[index]
            pairs=STRtree(polygons).query(p,predicate='within')
            ids,first=np.unique(pairs[0],return_index=True)
            self.assertEqual(len(ids),len(index))
            tri=coords[pairs[1,first]]
            ab=tri[:,1]-tri[:,0];ac=tri[:,2]-tri[:,0]
            normal=np.cross(ab,ac)
            expected=tri[:,0,2]-(normal[:,0]*(xyz[index,0]-tri[:,0,0])+normal[:,1]*(xyz[index,1]-tri[:,0,1]))/normal[:,2]
            self.assertLess(float(np.abs(expected-xyz[index,2]).max()),1e-6)
        # Adjacent eligible parcels share one permitted plant domain, as in the
        # original meadow generator. Internal cadastral edges are not obstacles;
        # exact road/house holes and the outer domain must retain full crowns.
        union=unary_union(eligible_shapes)
        self.assertGreaterEqual(float(shapely.distance(points,union.boundary).min()),14-1e-3)
        height=np.asarray([r['heightCm'] for r in rows])
        self.assertGreaterEqual(height.min(),2)
        self.assertLessEqual(height.max(),11)
        self.assertLess(height[np.linalg.norm(xyz[:,:2],axis=1)>7400].max(),2.15)


if __name__=='__main__': unittest.main()
