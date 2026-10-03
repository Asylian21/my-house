"""Independent small-geometry, source-ground and grove-exclusion evidence."""
import copy
from collections import Counter
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import shapely

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('grove_ecology',HERE/'exterior-canopy-ecology.py')
ecology=importlib.util.module_from_spec(spec);spec.loader.exec_module(ecology)
from test_exterior_lawn_natural import glb
OUTPUT=Path(os.environ.get('BREZI_CANOPY_ECOLOGY',ROOT/'output/unreal/exterior-canopy-ecology-20260930-r3'))
CONTEXT=ROOT/'output/unreal/exterior-context-20260927-r8/context-plan.json'
TERRAIN=ROOT/'output/unreal/exterior-terrain-20260926-r4/terrain-plan.json'
BUILDINGS=ROOT/'output/unreal/exterior-buildings-20260926-r2/building-plan.json'
SCENE=ROOT/'output/unreal/realism-20260926-r5/geometry/scene.json'
ASSETS=ROOT/'output/unreal/exterior-assets-20260927-r7'


class GroveEcology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=ecology.read(OUTPUT/'canopy-ecology-plan.json');cls.manifest=ecology.read(OUTPUT/'canopy-ecology-manifest.json')
        cls.library=ecology.read(OUTPUT/'geometry-manifest.json');cls.records=ecology.read(OUTPUT/'canopy-ecology-prototypes.json')
        cls.context=ecology.read(CONTEXT);cls.terrain=ecology.read(TERRAIN);cls.buildings=ecology.read(BUILDINGS);cls.scene=ecology.read(SCENE)
        cls.trees,cls.region,cls.grove,cls.crowns,cls.blocked,cls.domain,cls.sampler=ecology.domains(cls.context,cls.terrain,cls.buildings,cls.scene)
        cls.lookup={row['id']:row for row in cls.library['meshes']}

    def test_source_geometry_frame_and_all_lawful_photo_pins(self):
        self.assertEqual(self.plan['owner'],'scripts/unreal/exterior-canopy-ecology.py')
        self.assertEqual(self.plan['generatorSha256'],ecology.sha(HERE/'exterior-canopy-ecology.py'))
        self.assertEqual(self.plan['activeDesign'],self.scene['activeDesign']);self.assertEqual(self.plan['housePlacement'],self.scene['house']['placement'])
        self.assertEqual(self.plan['housePlacement']['streetSetbackMm'],3000);self.assertEqual(self.plan['housePlacement']['eastSetbackMm'],3000)
        self.assertEqual(self.plan['sourceSceneSha256'],ecology.sha(SCENE));self.assertEqual(self.plan['sourceObjSha256'],ecology.sha(SCENE.parent/'dom-mm.obj'))
        for path,expected in self.plan['inputFiles'].items():self.assertEqual(ecology.sha(path),expected,path)
        for key in('plan','geometryManifest','materialManifest','geometryProof','glb'):
            row=self.manifest[key];self.assertEqual(ecology.sha(row['path']),row['sha256'])
        recipes=ecology.read(OUTPUT/'material-manifest.json');base=ecology.read(ASSETS/'material-manifest.json')
        for key in('ph_tree_small_02_branches','regional_green_leaf'):self.assertEqual(recipes[key],base[key])
        for key,source in(('canopy_litter_oak','regional_oak_leaf'),('canopy_litter_green','regional_green_leaf')):
            self.assertEqual(recipes[key]['maps'],base[source]['maps']);self.assertEqual(recipes[key]['license'],'CC0-1.0')
            self.assertEqual(recipes[key]['sourceUrl'],base[source]['sourceUrl']);self.assertLessEqual(recipes[key]['subsurfaceScale'],.03)
        self.assertFalse(self.plan['audit']['providerPixelsChanged'])

    def test_actual_glb_axes_topology_bounds_and_small_explicit_master_scope(self):
        doc,decode=glb(OUTPUT/'canopy-ecology.glb');nodes={node['name']:doc['meshes'][node['mesh']]for node in doc['nodes']}
        self.assertEqual(len(nodes),51);self.assertEqual(len(self.library['meshes']),17)
        for record in self.records:
            decoded=[]
            for primitive in nodes[record['nodeName']]['primitives']:
                key=doc['materials'][primitive['material']]['name'];part=record['parts'][key];attrs=primitive['attributes']
                points=decode(attrs['POSITION'])[:,[0,2,1]]*100;decoded.extend(points.astype(float).tolist())
                np.testing.assert_allclose(points,part['positionsCm'],atol=.000004,rtol=0)
                idx=decode(primitive['indices']).reshape(-1,3)[:,[0,2,1]];np.testing.assert_array_equal(idx,part['triangles'])
                np.testing.assert_array_equal(decode(attrs['TEXCOORD_0']),np.asarray(part['uv0'],dtype=np.float32))
                n=decode(attrs['NORMAL']);t=decode(attrs['TANGENT'])[:,:3]
                np.testing.assert_allclose(np.linalg.norm(n,axis=1),1,atol=1e-6);np.testing.assert_allclose((n*t).sum(axis=1),0,atol=1e-6)
                faces=points[idx];areas=np.linalg.norm(np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]),axis=1)
                self.assertGreater(float(areas.min()),1e-9)
            decoded=np.asarray(decoded)
            self.assertAlmostEqual(float(np.linalg.norm(decoded[:,:2],axis=1).max()),record['radialEnvelopeCm'],places=4)
            for key,fn in(('min',np.min),('max',np.max)):np.testing.assert_allclose(fn(decoded,axis=0),record['expectedBoundsCm'][key],atol=.000004)
        for row in self.library['meshes']:
            self.assertEqual(row['placementPolicy'],'explicit-only');self.assertIn(row['role'],('grass','groundcover'))
            self.assertLess(max(lod['radialEnvelopeCm']for lod in row['lods']),45)
            self.assertTrue(all(lod['triangles']<800 for lod in row['lods']))
            self.assertEqual(len(row['lods']),3)

    def test_curled_leaves_grass_and_connected_twig_forks_survive_all_lods(self):
        for record in self.records:
            lod=record['level'];kind=next(row['ecologyFamily']for row in self.library['meshes']if record['nodeName'].startswith(row['id']+'_LOD'))
            if kind=='litter':
                self.assertEqual(len(record['features']),6)
                for feature in record['features']:
                    self.assertEqual(feature['kind'],'fallen-leaf');self.assertGreaterEqual(feature['sections'],2)
                    points=np.asarray(feature['centerlineCm']);t=np.linspace(0,1,len(points))[:,None]
                    deviation=np.linalg.norm(points-(points[0]+t*(points[-1]-points[0])),axis=1)
                    self.assertGreater(float(deviation.max()),.2)
                self.assertGreaterEqual(min(p[2]for part in record['parts'].values()for p in part['positionsCm']),.119999999)
            if kind=='grass':
                self.assertEqual(len(record['features']),18)
                self.assertTrue(all(f['sections']>=[6,4,3][lod]for f in record['features']))
            if kind=='twig':
                axis=np.asarray(record['features'][0]['pathCm'])
                for fork in record['features'][1:]:
                    p=np.asarray(fork['pathCm'][0]);a,b=axis[:-1],axis[1:];v=b-a
                    t=np.clip(((p-a)*v).sum(axis=1)/(v*v).sum(axis=1),0,1)
                    self.assertLess(float(np.linalg.norm(a+t[:,None]*v-p,axis=1).min()),1e-10)

    def test_every_complete_crown_fits_original_grove_crowns_and_real_exclusions(self):
        rows=self.plan['ecologyPlacements'];xy=np.asarray([row['positionCm'][:2]for row in rows]);points=shapely.points(xy)
        self.assertTrue(shapely.contains_xy(self.domain,*xy.T).all())
        radii=np.asarray([max(l['radialEnvelopeCm']for l in self.lookup[row['meshId']]['lods'])*row['scale'][0]for row in rows])
        domain_clearance=shapely.distance(points,self.domain.boundary)-radii
        self.assertGreater(float(domain_clearance.min()),.1)
        self.assertAlmostEqual(float(domain_clearance.min()),self.plan['audit']['minimumAdditionalWholeFootprintClearanceCm'],places=7)
        self.assertTrue((shapely.distance(points,self.grove.boundary)-radii>=10).all())
        for key,shape in self.blocked.items():
            if not shape.is_empty:self.assertTrue((shapely.distance(points,shape)-radii>=75).all(),key)
        self.assertTrue((shapely.distance(points,self.crowns.boundary)-radii>=0).all())
        self.assertTrue(shapely.equals_exact(shapely.from_geojson(self.plan['ecologyDomainCm']),self.domain,1e-7))
        self.assertLess(self.plan['audit']['allInstancesTriangleBudgetByLod'][0],5000000)
        self.assertEqual(len(rows),24851)
        flat=[{'meshId':group['meshId'],**row}for group in self.plan['groups']for row in group['instances']]
        # Native HISM grouping deliberately changes cross-group order; exact
        # row membership and multiplicity remain the integration contract.
        digest=lambda row:hashlib.sha256(json.dumps(row,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        self.assertEqual(Counter(map(digest,flat)),Counter(map(digest,rows)))

    def test_all_78_existing_root_yaw_scales_and_rendered_ground_remain_exact(self):
        self.assertEqual(self.plan['existingTrees'],self.trees);self.assertEqual(len(self.trees),78)
        indexed={tree['id']:tree for tree in self.trees};flares=[row for row in self.plan['ecologyPlacements']if row['ecologyFamily']=='flare']
        self.assertEqual({row['existingTreeId']for row in flares},set(indexed))
        for row in flares:
            original=indexed[row['existingTreeId']]
            self.assertEqual(row['positionCm'],original['positionCm']);self.assertEqual(row['yawDeg'],original['yawDeg']);self.assertEqual(row['scale'],original['scale'])
            self.assertEqual(self.lookup[row['meshId']]['existingTreeFamily'],original['meshId'])
            self.assertLess(row['radiusCm'],original['radiusCm'])
        # All input roots resolve onto the actual highest retained fallback at
        # -25cm. There are no new terrain height/collision measurements implied.
        for row in self.plan['ecologyPlacements']:
            self.assertEqual(row['renderedGround']['meshId'],'context_unresolved_flat_backdrop')
            self.assertAlmostEqual(row['renderedGround']['zCm'],-25.,places=8)
            self.assertFalse(row['renderedGround']['measuredElevation'])
            if row['ecologyFamily']!='flare':self.assertAlmostEqual(row['positionCm'][2],-24.92,places=8)
        for group in self.plan['groups']:
            family=self.lookup[group['meshId']]['ecologyFamily'];self.assertEqual(group['qualityDetail'],family!='flare')
        self.assertFalse(self.plan['audit']['sourceGroundChanged']);self.assertEqual(self.plan['policy']['collision'],'none')
        self.assertFalse(self.plan['policy']['navigation']);self.assertEqual(self.plan['policy']['windDisplacementCm'],0)

    def test_source_frame_tree_scope_and_immutable_output_rejections(self):
        mutations=[('context',lambda x:x['activeDesign'].update(variant='A'),'C/B/B'),
            ('context',lambda x:x['housePlacement'].update(eastSetbackMm=2999),'placement|setbacks'),
            ('context',lambda x:x.update(sourceObjSha256='0'*64),'OBJ'),
            ('context',lambda x:x['regionalVegetationPlacements'].pop(0),'census'),
            ('buildings',lambda x:x.update(sourceSceneSha256='0'*64),'scene')]
        for key,mutation,message in mutations:
            with tempfile.TemporaryDirectory(dir=ROOT/'output/unreal',prefix='ecology-source-rejection-')as directory:
                directory=Path(directory);source=copy.deepcopy(self.context if key=='context'else self.buildings);mutation(source)
                path=directory/'invalid.json';path.write_text(json.dumps(source))
                with self.assertRaisesRegex(ValueError,message):
                    ecology.build(path if key=='context'else CONTEXT,TERRAIN,path if key=='buildings'else BUILDINGS,SCENE,ASSETS,directory/'never-created')
        with self.assertRaisesRegex(ValueError,'immutable'):ecology.build(CONTEXT,TERRAIN,BUILDINGS,SCENE,ASSETS,OUTPUT)


if __name__=='__main__':unittest.main()
