"""Independent decoded GLB and complete-world-crown audit for 3D garden masters."""
import hashlib
import json
import math
import os
from pathlib import Path
import struct
import unittest

import numpy as np
from PIL import Image
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(os.environ.get('BREZI_GARDEN_MASTERS',str(ROOT/'output/unreal/exterior-garden-masters-20260930-r3')))


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def accessor(doc,raw,index):
    a=doc['accessors'][index];view=doc['bufferViews'][a['bufferView']]
    dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];kind={5126:'f',5125:'I',5123:'H'}[a['componentType']]
    fmt='<'+kind*dim;start=view.get('byteOffset',0)+a.get('byteOffset',0);stride=view.get('byteStride',struct.calcsize(fmt))
    return np.array([struct.unpack_from(fmt,raw,start+i*stride)for i in range(a['count'])])


class Masters(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((OUT/'geometry-manifest.json').read_text());cls.garden=json.loads((OUT/'garden-plan.json').read_text())
        cls.old=json.loads((ROOT/'output/unreal/exterior-garden-drifts-20260930-r1/garden-plan.json').read_text())
        cls.meshes={r['id']:r for r in cls.manifest['meshes']}
        cls.materials=json.loads((OUT/'material-manifest.json').read_text())
        data=Path(cls.manifest['meshes'][0]['glbPath']).read_bytes();length=struct.unpack_from('<I',data,12)[0]
        cls.doc=json.loads(data[20:20+length]);cls.raw=data[28+length:]
        cls.decoded={}
        for mesh in cls.manifest['meshes']:
            points=[]
            for lod in mesh['lods']:
                node=next(n for n in cls.doc['nodes']if n['name']==lod['nodeName'])
                for primitive in cls.doc['meshes'][node['mesh']]['primitives']:
                    xyz=accessor(cls.doc,cls.raw,primitive['attributes']['POSITION'])
                    points.extend(xyz[:,[0,2,1]]*100)
            cls.decoded[mesh['id']]=np.array(points)
        cls.beds={k:unary_union([Polygon([p[:2]for p in t])for t in triangles if Polygon([p[:2]for p in t]).area>1e-7])
                  for k,triangles in cls.garden['sourceMulchTrianglesCm'].items()}
        cls.steps=unary_union([Polygon([p[:2]for p in t])for triangles in cls.garden['sourceStepTrianglesCm'].values()
                              for t in triangles if Polygon([p[:2]for p in t]).area>1e-7])

    def test_all_frozen_input_pins_and_material_source_pixels_unchanged(self):
        for report in (self.manifest,self.garden):
            for path,pin in report['inputFiles'].items():self.assertEqual(sha(path),pin,path)
        for recipe in self.materials.values():
            for spec in recipe['maps'].values():self.assertEqual(sha(spec['path']),spec['sha256'])
        source=json.loads((ROOT/'output/unreal/exterior-assets-20260927-r6/material-manifest.json').read_text())
        self.assertEqual(self.materials['regional_green_leaf'],source['regional_green_leaf'])
        self.assertEqual(self.materials['garden_blade_photo']['maps'],{k:v for k,v in source['ph_grass_medium_01']['maps'].items()if k!='alpha'})

    def test_twenty_one_real_three_dimensional_lods_with_bounded_triangle_budget(self):
        self.assertEqual(len(self.manifest['meshes']),7)
        self.assertEqual(len(self.doc['nodes']),21)
        for row in self.manifest['meshes']:
            self.assertEqual(row['placementPolicy'],'explicit-only')
            self.assertEqual([l['level']for l in row['lods']],[0,1,2])
            self.assertGreater(row['lods'][0]['triangles'],row['lods'][1]['triangles'])
            self.assertGreater(row['lods'][1]['triangles'],row['lods'][2]['triangles'])
            for lod in row['lods']:
                self.assertLessEqual(lod['triangles'],20000)
                node=next(n for n in self.doc['nodes']if n['name']==lod['nodeName'])
                self.assertFalse(any(key in node for key in ('matrix','translation','scale','rotation')))
                actual=sum(len(accessor(self.doc,self.raw,p['indices']))//3 for p in self.doc['meshes'][node['mesh']]['primitives'])
                self.assertEqual(actual,lod['triangles'])
            xyz=self.decoded[row['id']]
            self.assertTrue(np.isfinite(xyz).all())
            self.assertGreater(np.ptp(xyz[:,0]),5)
            self.assertGreater(np.ptp(xyz[:,1]),5)
            self.assertGreater(np.ptp(xyz[:,2]),5)

    def test_decoded_normals_tangents_vertex_colors_and_winding(self):
        for mesh in self.doc['meshes']:
            for primitive in mesh['primitives']:
                attrs=primitive['attributes'];p=accessor(self.doc,self.raw,attrs['POSITION']);n=accessor(self.doc,self.raw,attrs['NORMAL'])
                t=accessor(self.doc,self.raw,attrs['TANGENT']);c=accessor(self.doc,self.raw,attrs['COLOR_0'])
                self.assertLess(float(np.max(np.abs(np.linalg.norm(n,axis=1)-1))),1e-5)
                self.assertLess(float(np.max(np.abs(np.linalg.norm(t[:,:3],axis=1)-1))),1e-5)
                self.assertLess(float(np.max(np.abs(np.sum(n*t[:,:3],axis=1)))),1e-5)
                self.assertTrue(set(t[:,3])<={-1,1});self.assertGreaterEqual(float(c.min()),.0);self.assertLessEqual(float(c.max()),1.)
                indices=accessor(self.doc,self.raw,primitive['indices']).reshape(-1,3).astype(int)
                face=np.cross(p[indices[:,1]]-p[indices[:,0]],p[indices[:,2]]-p[indices[:,0]])
                self.assertTrue((np.linalg.norm(face,axis=1)>1e-13).all())
                self.assertTrue((np.sum(face*n[indices].mean(axis=1),axis=1)>0).all())

    def test_twelve_primary_roots_and_safe_radial_envelopes_including_all_lod_vertices(self):
        for row,original in zip(self.garden['ornamentalPlacements'],self.old['ornamentalPlacements']):
            for key in ('positionCm','yawDeg','sourceIds','sourceBedId','collision'):
                self.assertEqual(row[key],original[key])
            self.assertLessEqual(row['radiusCm'],original['radiusCm']+1e-7)
            self.assertLessEqual(row['heightCm'],(120 if row['form']=='grass'else original['heightCm'])+1e-7)
            if row['form']=='grass':
                self.assertTrue(row['meshId'].startswith('garden_feather_'))
                self.assertGreaterEqual(row['heightCm'],85)
                self.assertEqual(len(set(row['scale'])),1)
                xyz=self.decoded[row['meshId']]*row['uniformScale']
                self.assertLessEqual(float(np.linalg.norm(xyz[:,:2],axis=1).max()),original['radiusCm']+.001)
        self.assertEqual(self.garden['activeDesign'],{'variant':'C','heatingLayout':'B','livingLayout':'B'})
        self.assertEqual(self.garden['housePlacement'],self.old['housePlacement'])

    def test_no_yellow_groundcovers_and_original_detail_world_clearances(self):
        for row,old in zip(self.garden['gardenDetailPlacements'],self.old['gardenDetailPlacements']):
            self.assertEqual(row['positionCm'][:2],old['positionCm'][:2]);self.assertEqual(row['yawDeg'],old['yawDeg'])
            self.assertNotIn('celandine',row['meshId']);self.assertNotIn('grass_medium',row['meshId'])
            self.assertEqual(len(set(row['scale'])),1)
            xyz=self.decoded[row['meshId']]*row['uniformScale']
            self.assertLessEqual(float(np.linalg.norm(xyz[:,:2],axis=1).max()),old['radiusCm']+.001)
            self.assertLessEqual(float(xyz[:,2].max()-xyz[:,2].min()),old['heightCm']+.001)
            point=Point(row['positionCm'][:2]);radius=row['radiusCm']
            self.assertGreaterEqual(point.distance(self.beds[row['sourceBedId']].boundary)-radius,4)
            self.assertGreaterEqual(point.distance(self.steps)-radius,12)
        self.assertEqual(sum(r['meshId'].startswith('garden_violet')for r in self.garden['gardenDetailPlacements']),41)

    def test_blade_uv_uses_opaque_green_photographic_tissue_only(self):
        source=json.loads((ROOT/'output/unreal/exterior-assets-20260927-r6/material-manifest.json').read_text())['ph_grass_medium_01']
        alpha=np.array(Image.open(source['maps']['alpha']['path']).convert('L'))
        rgb=np.array(Image.open(source['maps']['albedo']['path']).convert('RGB'))/255
        self.assertGreaterEqual(int(alpha[720:848,1872:1880].min()),250)
        sample=rgb[720:848,1872:1880].mean((0,1));self.assertGreater(sample[1],sample[0]);self.assertGreater(sample[1],sample[2])
        for mesh in self.doc['meshes']:
            for primitive in mesh['primitives']:
                if self.doc['materials'][primitive['material']]['name']!='garden_blade_photo':continue
                uv=accessor(self.doc,self.raw,primitive['attributes']['TEXCOORD_0'])
                self.assertGreaterEqual(float(uv[:,0].min()),.9140625-1e-7);self.assertLessEqual(float(uv[:,0].max()),.91796875+1e-7)
                self.assertGreaterEqual(float(uv[:,1].min()),.3515625-1e-7);self.assertLessEqual(float(uv[:,1].max()),.4140625+1e-7)


if __name__=='__main__':unittest.main()
