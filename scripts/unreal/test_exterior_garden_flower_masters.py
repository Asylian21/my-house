"""Independent source, decoded geometry and world containment audit for pink flowers."""
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import unittest

import numpy as np
from PIL import Image
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(os.environ.get('BREZI_GARDEN_FLOWERS',str(ROOT/'output/unreal/exterior-garden-flower-masters-20260930-r1c')))
spec=importlib.util.spec_from_file_location('garden_glb_decode',ROOT/'scripts/unreal/test_exterior_garden_masters.py')
decode=importlib.util.module_from_spec(spec);spec.loader.exec_module(decode)


class Flowers(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((OUT/'geometry-manifest.json').read_text())
        cls.garden=json.loads((OUT/'garden-plan.json').read_text())
        cls.original=json.loads((ROOT/'output/unreal/exterior-garden-masters-20260930-r3/garden-plan.json').read_text())
        cls.materials=json.loads((OUT/'material-manifest.json').read_text())
        cls.morphology=json.loads((OUT/'morphology-audit.json').read_text())
        data=Path(cls.manifest['meshes'][0]['glbPath']).read_bytes();length=struct.unpack_from('<I',data,12)[0]
        cls.doc=json.loads(data[20:20+length]);cls.raw=data[28+length:]
        cls.meshes={r['id']:r for r in cls.manifest['meshes']}
        cls.nodes={n['name']:n for n in cls.doc['nodes']}
        cls.decoded={}
        for mesh in cls.manifest['meshes']:
            cls.decoded[mesh['id']]=np.concatenate([decode.accessor(cls.doc,cls.raw,p['attributes']['POSITION'])[:,[0,2,1]]*100
                for lod in mesh['lods']for p in cls.doc['meshes'][cls.nodes[lod['nodeName']]['mesh']]['primitives']])

    def test_frozen_sources_and_reused_maps_are_exact(self):
        for report in (self.manifest,self.garden):
            for path,pin in report['inputFiles'].items():self.assertEqual(decode.sha(path),pin,path)
        original=json.loads((ROOT/'output/unreal/exterior-assets-20260930-r3/material-manifest.json').read_text())
        for key in ('regional_green_leaf','garden_blade_green','garden_plume_silk'):
            self.assertEqual(self.materials[key],original[key])
        self.assertEqual(self.materials['garden_petal_rose']['linearColor'],[.34,.115,.205])
        self.assertEqual(self.materials['garden_petal_rose']['maps'],{})
        self.assertTrue(self.materials['garden_petal_rose']['twoSided'])

    def test_all_six_decoded_lods_have_bounded_real_geometry(self):
        self.assertEqual(len(self.manifest['meshes']),2);self.assertEqual(len(self.doc['nodes']),6)
        for mesh in self.manifest['meshes']:
            self.assertEqual(mesh['placementPolicy'],'explicit-only')
            counts=[r['triangles']for r in mesh['lods']]
            self.assertGreater(counts[0],counts[1]);self.assertGreater(counts[1],counts[2])
            for lod in mesh['lods']:
                node=self.nodes[lod['nodeName']]
                actual=sum(len(decode.accessor(self.doc,self.raw,p['indices']))//3
                           for p in self.doc['meshes'][node['mesh']]['primitives'])
                self.assertEqual(actual,lod['triangles']);self.assertLessEqual(actual,20000)
            xyz=self.decoded[mesh['id']]
            self.assertTrue(np.isfinite(xyz).all())
            self.assertGreater(np.ptp(xyz[:,0]),25);self.assertGreater(np.ptp(xyz[:,1]),25)
            self.assertAlmostEqual(float(xyz[:,2].max()-xyz[:,2].min()),45,places=4)
        self.assertFalse(np.array_equal(self.decoded[self.manifest['meshes'][0]['id']],self.decoded[self.manifest['meshes'][1]['id']]))

    def test_normals_tangents_winding_and_colours(self):
        for mesh in self.doc['meshes']:
            for primitive in mesh['primitives']:
                a=primitive['attributes'];p=decode.accessor(self.doc,self.raw,a['POSITION']);n=decode.accessor(self.doc,self.raw,a['NORMAL'])
                t=decode.accessor(self.doc,self.raw,a['TANGENT']);c=decode.accessor(self.doc,self.raw,a['COLOR_0'])
                self.assertLess(float(np.max(np.abs(np.linalg.norm(n,axis=1)-1))),1e-5)
                self.assertLess(float(np.max(np.abs(np.linalg.norm(t[:,:3],axis=1)-1))),1e-5)
                self.assertLess(float(np.max(np.abs(np.sum(n*t[:,:3],axis=1)))),1e-5)
                self.assertTrue(set(t[:,3])<={-1,1});self.assertGreaterEqual(c.min(),0);self.assertLessEqual(c.max(),1)
                i=decode.accessor(self.doc,self.raw,primitive['indices']).astype(int).reshape(-1,3)
                face=np.cross(p[i[:,1]]-p[i[:,0]],p[i[:,2]]-p[i[:,0]])
                self.assertTrue((np.linalg.norm(face,axis=1)>1e-13).all())
                self.assertTrue((np.sum(face*n[i].mean(axis=1),axis=1)>0).all())

    def test_leaves_sample_only_opaque_healthy_photo_tissue(self):
        recipe=self.materials['regional_green_leaf'];alpha=np.array(Image.open(recipe['maps']['alpha']['path']).convert('L'))
        rgb=np.array(Image.open(recipe['maps']['albedo']['path']).convert('RGB'))
        rect=alpha[round(.30*alpha.shape[0]):round(.74*alpha.shape[0])+1,
                   round(.28*alpha.shape[1]):round(.73*alpha.shape[1])+1]
        self.assertGreaterEqual(int(rect.min()),250)  # Includes interpolated UV tissue.
        for mesh in self.doc['meshes']:
            leaf=next(p for p in mesh['primitives']if self.doc['materials'][p['material']]['name']=='regional_green_leaf')
            uv=decode.accessor(self.doc,self.raw,leaf['attributes']['TEXCOORD_0'])
            self.assertTrue((uv[:,0]>=.28-1e-7).all()and(uv[:,0]<=.73+1e-7).all())
            self.assertTrue((uv[:,1]>=.30-1e-7).all()and(uv[:,1]<=.74+1e-7).all())
            x=np.clip(np.rint(uv[:,0]*(alpha.shape[1]-1)).astype(int),0,alpha.shape[1]-1)
            y=np.clip(np.rint(uv[:,1]*(alpha.shape[0]-1)).astype(int),0,alpha.shape[0]-1)
            self.assertGreaterEqual(int(alpha[y,x].min()),250)
            mean=rgb[y,x].mean(0);self.assertGreater(mean[1],mean[0]);self.assertGreater(mean[1],mean[2])
            # Muted lamina contains substantial blue, unlike the yellow original
            # periwinkle atlas. This catches accidentally restoring that atlas.
            self.assertGreater(mean[2]/mean[1],.4)

    def test_leaf_and_corolla_surfaces_are_curved_and_jointed(self):
        for mesh in self.doc['meshes']:
            for key in ('regional_green_leaf','garden_petal_rose'):
                primitive=next(p for p in mesh['primitives']if self.doc['materials'][p['material']]['name']==key)
                p=decode.accessor(self.doc,self.raw,primitive['attributes']['POSITION'])
                indices=decode.accessor(self.doc,self.raw,primitive['indices']).astype(int).reshape(-1,3)
                # First connected surface component is an individual leaf/petal,
                # measured directly from exported triangle connectivity.
                connected={0};changed=True
                while changed:
                    changed=False
                    for triangle in indices:
                        if any(int(v)in connected for v in triangle):
                            previous=len(connected);connected.update(int(v)for v in triangle)
                            changed|=len(connected)>previous
                component=p[sorted(connected)]
                _,singular,_=np.linalg.svd(component-component.mean(0),full_matrices=False)
                self.assertGreater(float(singular[2]/singular[0]),.012,key+' must not be a flat image card')
        for proof in self.morphology['nodes'].values():
            self.assertEqual(proof['stemCount'],13)
            self.assertGreaterEqual(len(proof['flowers']),30)
            self.assertTrue(all(f['petals']==5 for f in proof['flowers']))
            for pair in proof['pairedNodes']:
                a,b=np.array(pair['directions']);self.assertLess(float(np.dot(a[:2],b[:2])),-.98)
        for row in self.manifest['meshes']:
            proofs=[self.morphology['nodes'][lod['nodeName']]for lod in row['lods']]
            self.assertEqual(proofs[0]['flowers'],proofs[1]['flowers'])
            self.assertEqual(proofs[0]['flowers'],proofs[2]['flowers'])
            # Common physical flower attachment positions survive all LODs;
            # lowering leaf topology must not advance the random generator.
            for proof in proofs[1:]:self.assertEqual(proof['normalization'],proofs[0]['normalization'])

    def test_exact_primary_roots_and_detail_planting_with_safe_full_lod_crowns(self):
        self.assertEqual(self.garden['activeDesign'],self.original['activeDesign'])
        self.assertEqual(self.garden['housePlacement'],self.original['housePlacement'])
        self.assertEqual(self.garden['gardenDetailPlacements'],self.original['gardenDetailPlacements'])
        replaced=[]
        for row,old in zip(self.garden['ornamentalPlacements'],self.original['ornamentalPlacements']):
            for key in ('positionCm','yawDeg','sourceIds','sourceBedId','collision'):
                self.assertEqual(row[key],old[key])
            if row['meshId']==old['meshId']:self.assertEqual(row,old);continue
            replaced.append(row)
            self.assertTrue(old['meshId'].startswith('garden_pink_r6_'))
            self.assertEqual(len(set(row['scale'])),1)
            self.assertLessEqual(row['radiusCm'],old['radiusCm']);self.assertLessEqual(row['heightCm'],old['heightCm'])
            xyz=self.decoded[row['meshId']]*row['uniformScale']
            self.assertLessEqual(float(np.linalg.norm(xyz[:,:2],axis=1).max()),old['radiusCm']+.001)
            self.assertLessEqual(float(np.ptp(xyz[:,2])),min(45,old['heightCm'])+.001)
            # Some original hero rows have no bed association. Their inherited
            # safe circle remains the contract; do not invent bed membership.
            if row['sourceBedId']:
                bed=unary_union([Polygon([p[:2]for p in t])for t in self.garden['sourceMulchTrianglesCm'][row['sourceBedId']]])
                self.assertTrue(bed.buffer(.001).covers(Point(row['positionCm'][:2]).buffer(row['radiusCm'])))
        self.assertEqual(len(replaced),2)


if __name__=='__main__':unittest.main()
