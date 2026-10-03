"""Independent exported-geometry and whole-crown audit for grove successors."""
import argparse
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import sys
import unittest

import numpy as np
from shapely.geometry import Point, Polygon, shape

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(os.environ.get('BREZI_CANOPY_MASTERS',str(ROOT/'output/unreal/exterior-canopy-masters-20260930-r1d')))
HELPER=ROOT/'scripts/unreal/test_exterior_garden_masters.py'
spec=importlib.util.spec_from_file_location('frozen_canopy_decoder',HELPER)
decoder=importlib.util.module_from_spec(spec);spec.loader.exec_module(decoder)
accessor=decoder.accessor


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def quadratic(points,t):
    p=np.asarray(points);return p[0]*(1-t)**2+p[1]*2*t*(1-t)+p[2]*t*t
def evaluate(branch,t):
    if branch['kind']!='trunk':return quadratic(branch['points'],t)
    z=branch['height']*t
    if z>50:return quadratic(branch['upperPoints'],(z-50)/(branch['height']-50))
    old=branch['oldBasalAxis'];source=old['branches'][0];factor=old['sharedUniformScale']
    p=quadratic(source['points'],z/(source['points'][-1][2]*100*factor))*100*factor
    return np.array([p[0],-p[1],z])


class Canopy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geometry=json.loads((OUT/'geometry-manifest.json').read_text())
        cls.plan=json.loads((OUT/'canopy-plan.json').read_text());cls.materials=json.loads((OUT/'material-manifest.json').read_text())
        cls.skeleton=json.loads((OUT/'growth-skeletons.json').read_text());cls.audit=json.loads((OUT/'morphology-audit.json').read_text())
        cls.source=json.loads(Path(cls.plan['sourceContext']['path']).read_text())
        old_library=next(Path(p).parent for p in cls.geometry['inputFiles']if p.endswith('/geometry-manifest.json'))
        cls.old_materials=json.loads((old_library/'material-manifest.json').read_text())
        cls.old_meshes={r['id']:r for r in json.loads((old_library/'geometry-manifest.json').read_text())['meshes']}
        cls.meshes={r['id']:r for r in cls.geometry['meshes']};cls.export={};cls.decoded={}
        for row in cls.geometry['meshes']:
            raw=Path(row['glbPath']).read_bytes();length=struct.unpack_from('<I',raw,12)[0]
            doc=json.loads(raw[20:20+length]);binary=raw[28+length:];cls.export[row['id']]=(doc,binary)
            for lod in row['lods']:
                node=next(n for n in doc['nodes']if n['name']==lod['nodeName'])
                parts={}
                for p in doc['meshes'][node['mesh']]['primitives']:
                    attrs=p['attributes'];key=doc['materials'][p['material']]['name']
                    parts[key]={'p':accessor(doc,binary,attrs['POSITION']),
                                'n':accessor(doc,binary,attrs['NORMAL']),'t':accessor(doc,binary,attrs['TANGENT']),
                                'uv':accessor(doc,binary,attrs['TEXCOORD_0']),
                                'color':accessor(doc,binary,attrs['COLOR_0']),
                                'indices':accessor(doc,binary,p['indices']).reshape(-1,3).astype(int)}
                cls.decoded[lod['nodeName']]=parts
        cls.ecology=json.loads((ROOT/'output/unreal/exterior-canopy-ecology-20260930-r3/canopy-ecology-plan.json').read_text())

    def test_source_pins_exact_recipes_and_no_new_materials_or_source_photos(self):
        for manifest in (self.geometry,self.plan):
            for path,pin in manifest['inputFiles'].items():self.assertEqual(sha(path),pin,path)
        self.assertEqual(set(self.materials),{'ph_tree_small_02_branches','regional_oak_leaf','regional_green_leaf'})
        for key,recipe in self.materials.items():
            self.assertEqual(recipe,self.old_materials[key])
            for channel in recipe['maps'].values():self.assertEqual(sha(channel['path']),channel['sha256'])
        self.assertEqual(self.plan['sourceContext']['sha256'],sha(self.plan['sourceContext']['path']))
        self.assertFalse(self.plan['policy']['nativeAppearanceAccepted'])

    def test_nine_distinct_real_canopies_twenty_seven_lods_and_measured_bounds(self):
        self.assertEqual(len(self.meshes),9)
        for row in self.meshes.values():
            self.assertEqual(row['placementPolicy'],'explicit-only');doc,binary=self.export[row['id']]
            self.assertEqual(len(doc['nodes']),3);self.assertEqual(sha(row['glbPath']),row['glbSha256'])
            self.assertEqual([l['level']for l in row['lods']],[0,1,2])
            self.assertGreater(row['lods'][0]['triangles'],row['lods'][1]['triangles'])
            self.assertGreater(row['lods'][1]['triangles'],row['lods'][2]['triangles'])
            points=[]
            for lod in row['lods']:
                node=next(n for n in doc['nodes']if n['name']==lod['nodeName'])
                self.assertFalse(any(k in node for k in ('scale','matrix','translation','rotation')))
                parts=self.decoded[lod['nodeName']];xyz=np.concatenate([p['p'][:,[0,2,1]]*100 for p in parts.values()])
                triangles=sum(len(p['indices'])for p in parts.values());self.assertEqual(triangles,lod['triangles'])
                self.assertLess(triangles,165000);self.assertEqual(len(xyz),lod['vertices'])
                if lod['level']==0:self.assertLessEqual(triangles,self.old_meshes[row['sourceFamily']]['lods'][0]['triangles'])
                np.testing.assert_allclose(xyz.min(0),lod['expectedBoundsCm']['min'],atol=.0002)
                np.testing.assert_allclose(xyz.max(0),lod['expectedBoundsCm']['max'],atol=.0002)
                self.assertAlmostEqual(float(np.linalg.norm(xyz[:,:2],axis=1).max()),lod['radialEnvelopeCm'],delta=.0002)
                self.assertGreater(float(np.ptp(xyz[:,0])),260);self.assertGreater(float(np.ptp(xyz[:,1])),200)
                self.assertGreater(float(xyz[:,2].max()),row['heightCm']*.94);points.extend(xyz)
            xyz=np.array(points);self.assertAlmostEqual(float(xyz[:,2].max()),row['heightCm'],delta=.0002)
            self.assertGreaterEqual(float(xyz[:,2].min()),-.0002)
            self.assertLessEqual(float(np.linalg.norm(xyz[:,:2],axis=1).max()),self.old_meshes[row['sourceFamily']]['radialEnvelopeCm']+.0002)
        for family in ('broadleaf','upright','orchard'):
            meshes=[r for r in self.meshes.values()if r['id'].startswith('canopy_'+family+'_')]
            self.assertEqual(len({r['glbSha256']for r in meshes}),3)
            self.assertEqual(len({r['branches']for r in meshes}),3)

    def test_every_exported_face_normal_tangent_uv_and_neutral_vertex_colour(self):
        total=0;largest=0.
        for node,parts in self.decoded.items():
            for key,part in parts.items():
                p,n,t,uv,indices=(part[k]for k in ('p','n','t','uv','indices'))
                for values in (p,n,t,uv):self.assertTrue(np.isfinite(values).all(),node)
                self.assertLess(float(np.max(np.abs(np.linalg.norm(n,axis=1)-1))),1e-5)
                self.assertLess(float(np.max(np.abs(np.linalg.norm(t[:,:3],axis=1)-1))),1e-5)
                ndot=np.abs(np.sum(n*t[:,:3],axis=1));largest=max(largest,float(ndot.max()))
                self.assertLess(float(ndot.max()),1e-5);self.assertTrue(set(t[:,3])<={-1,1})
                np.testing.assert_array_equal(part['color'],np.ones_like(part['color']))
                face=np.cross(p[indices[:,1]]-p[indices[:,0]],p[indices[:,2]]-p[indices[:,0]])
                self.assertTrue((np.linalg.norm(face,axis=1)>1e-13).all(),node)
                self.assertTrue((np.sum(face*n[indices].mean(1),axis=1)>0).all(),node)
                if key.startswith('regional_'):
                    self.assertGreaterEqual(float(uv.min()),0);self.assertLessEqual(float(uv.max()),1)
                total+=len(indices)
        print('DECODED_CANOPY_TRIANGLES',total,'MAX_NORMAL_TANGENT_DOT',largest)
        type(self).decodedMetrics={'triangles':total,'opposedFaces':0,'degenerateFaces':0,'maximumAbsNormalDotTangent':largest}

    def test_branch_continuity_cluster_centres_nested_lods_and_nonplanar_leaf_tissue(self):
        for mid,morph in self.skeleton.items():
            for b in morph['branches'][1:]:
                np.testing.assert_allclose(b['points'][0],evaluate(morph['branches'][b['parent']],b['parentT']),atol=1e-9)
                self.assertGreater(b['radius'],b['tipRadius']);self.assertGreater(b['tipRadius'],0)
            for leaf in morph['leaves']:
                np.testing.assert_allclose(leaf['base'],evaluate(morph['branches'][leaf['branch']],leaf['t']),atol=1e-9)
            selection=self.audit['meshes'][mid]['lodLeafIds']
            self.assertTrue(set(selection['2']).issubset(selection['1']))
            self.assertTrue(set(selection['1']).issubset(selection['0']))
            for level in ('0','1','2'):
                represented={morph['leaves'][i]['cluster']for i in selection[level]}
                self.assertEqual(represented,set(range(len(morph['clusters']))))
            self.assertGreaterEqual(len(morph['clusters']),27)
            reaches=[np.linalg.norm(np.asarray(b['points'][-1])[:2]-np.asarray(b['points'][0])[:2])for b in morph['branches']if b['order']==1]
            self.assertGreater(float(np.std(reaches)/np.mean(reaches)),.20)
            self.assertGreater(float(np.std([l['roll']for l in morph['leaves']])),.40)
            for lod in range(3):
                part=self.decoded[mid+'_LOD'+str(lod)][morph['leafMaterial']]
                width=(15,9,6)[lod];xyz=part['p'].reshape(-1,width,3)
                # Real exported individual leaves have curved/folded geometry;
                # this rejects a flat whole-leaf quad with mere metadata claims.
                values=np.linalg.svd(xyz-xyz.mean(1)[:,None,:],compute_uv=False)
                self.assertGreater(float(np.quantile(values[:,2],.05)),.0001)

    def test_exact_78_roots_yaws_uniform_scales_global_heights_and_all_crown_exclusions(self):
        old=[r for r in self.source['regionalVegetationPlacements']if r['regionId']=='village_nearest_grove']
        self.assertEqual(len(old),78);self.assertEqual(self.plan['originalCanopyPlacements'],old)
        self.assertEqual(self.plan['activeDesign'],{'variant':'C','heatingLayout':'B','livingLayout':'B'})
        self.assertEqual(self.plan['housePlacement'],self.source['housePlacement'])
        region=Polygon(self.ecology['sourceRegion']['polygonCm'])
        exclusions={k:shape(json.loads(v))for k,v in self.ecology['exclusionDomainsCm'].items()}
        for row,source in zip(self.plan['canopyPlacements'],old):
            self.assertEqual({k:v for k,v in row.items()if k not in ('meshId','sourceMeshId')},
                             {k:v for k,v in source.items()if k!='meshId'})
            self.assertEqual(row['sourceMeshId'],source['meshId']);self.assertEqual(len(set(row['scale'])),1)
            record=self.meshes[row['meshId']]
            xyz=np.concatenate([p['p'][:,[0,2,1]]*100 for l in record['lods']for p in self.decoded[l['nodeName']].values()])
            xyz*=row['scale'][0];radius=float(np.linalg.norm(xyz[:,:2],axis=1).max())
            self.assertLessEqual(radius,row['radiusCm']+.001)
            self.assertLessEqual(float(np.ptp(xyz[:,2])),row['heightCm']+.001)
            point=Point(row['positionCm'][:2]);self.assertTrue(region.contains(point))
            self.assertGreaterEqual(point.distance(region.boundary),radius+10)
            for key,polygon in exclusions.items():
                self.assertFalse(polygon.contains(point),key)
                self.assertGreater(point.distance(polygon),radius,key)
        self.assertEqual({r['regionId']for r in self.plan['canopyPlacements']},{'village_nearest_grove'})

    def test_exported_basal_axis_and_radius_compatibility_with_original_root_flares(self):
        for row in self.meshes.values():
            proof=self.audit['meshes'][row['id']]
            for lod in row['lods']:
                bark=self.decoded[lod['nodeName']]['ph_tree_small_02_branches']['p'][:,[0,2,1]]*100
                for expected,radius in zip(proof['basalAxisSamplesCm'],proof['basalRadiiCm']):
                    ring=bark[np.isclose(bark[:,2],expected[2],atol=.0001)]
                    self.assertGreaterEqual(len(ring),9)
                    # Discard the duplicated UV seam vertex before centroiding.
                    ring=ring[:-1];np.testing.assert_allclose(ring[:,:2].mean(0),expected[:2],atol=.0002)
                    np.testing.assert_allclose(np.linalg.norm(ring[:,:2]-expected[:2],axis=1),radius,atol=.0002)


if __name__=='__main__':
    parser=argparse.ArgumentParser(add_help=False);parser.add_argument('--receipt')
    args,remaining=parser.parse_known_args();program=unittest.main(argv=[sys.argv[0],*remaining],exit=False)
    if program.result.wasSuccessful()and args.receipt:
        receipt={'status':'PASS_OFFLINE_NATIVE_PENDING','tests':program.result.testsRun,'metrics':Canopy.decodedMetrics,
                 'geometryManifestSha256':sha(OUT/'geometry-manifest.json'),'canopyPlanSha256':sha(OUT/'canopy-plan.json'),
                 'generatorSha256':sha(ROOT/'scripts/unreal/exterior-canopy-masters.py'),'testSourceSha256':sha(__file__),
                 'rootCount':78,'masters':9,'lods':27,'allRootYawUniformScaleAndInheritedHeightRadialEnvelopesPreserved':True,
                 'allWholeCrownsClearProtectedSubjectRoadsBuildingsCultivatedGroundAndRegionEdge':True,
                 'sourcePhotographicMaterialsUnchanged':True,'allLodBasalFlareCompatibility':True,
                 'nativeAppearanceAccepted':False}
        with Path(args.receipt).open('x')as stream:json.dump(receipt,stream,indent=2);stream.write('\n')
    sys.exit(0 if program.result.wasSuccessful()else 1)
