"""Independent actual photographic substrate geometry and source provenance."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import tempfile
import unittest

import numpy as np
from PIL import Image
import shapely

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('grove_substrate',HERE/'exterior-grove-substrate.py')
substrate=importlib.util.module_from_spec(spec);spec.loader.exec_module(substrate)
OUTPUT=Path(os.environ.get('BREZI_GROVE_SUBSTRATE',ROOT/'output/unreal/exterior-grove-substrate-20260930-r3'))


def glb(path):
    raw=Path(path).read_bytes();magic,version,length=struct.unpack_from('<4sII',raw)
    if magic!=b'glTF'or version!=2 or length!=len(raw):raise AssertionError('Actual GLB header differs')
    size,kind=struct.unpack_from('<II',raw,12)
    if kind!=0x4e4f534a:raise AssertionError('Missing GLB JSON')
    doc=json.loads(raw[20:20+size]);offset=20+size;binsize,binkind=struct.unpack_from('<II',raw,offset)
    if binkind!=0x004e4942:raise AssertionError('Missing GLB binary')
    binary=raw[offset+8:offset+8+binsize]
    def decode(index):
        row=doc['accessors'][index];view=doc['bufferViews'][row['bufferView']]
        width={'SCALAR':1,'VEC2':2,'VEC3':3}[row['type']];dtype={5126:'<f4',5125:'<u4'}[row['componentType']]
        return np.frombuffer(binary,dtype=dtype,count=row['count']*width,
            offset=view.get('byteOffset',0)+row.get('byteOffset',0)).reshape(-1,width)
    return doc,decode


class PhotographicGroveSubstrate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=substrate.read(OUTPUT/'grove-substrate-plan.json');cls.manifest=substrate.read(OUTPUT/'grove-substrate-manifest.json')
        cls.context,cls.ecology,cls.trees,cls.region,cls.domain,cls.sampler=substrate.source(
            *[cls.plan[k]['path']for k in('sourceContext','sourceEcology','sourceTerrain','sourceBuildings','sourceScene')])
        cls.receipt=substrate.verified_acquisition(Path(cls.plan['acquisitionManifest']['path']).parent)
        cls.recipe=substrate.read(cls.plan['materialManifest']['path'])['canopy_floor_litter']
        cls.height=substrate.height_image(cls.receipt['maps']['displacement']['path'])
        cls.vertices=np.asarray([p for mesh in cls.plan['meshes']for p in mesh['verticesCm']])

    def test_all_pins_and_exact_old_domain_tree_metadata_and_protected_frame(self):
        p=self.plan
        self.assertEqual(p['owner'],'scripts/unreal/exterior-grove-substrate.py');self.assertEqual(p['kind'],'grove-continuous-photographic-substrate')
        self.assertEqual(p['generatorSha256'],substrate.sha(HERE/'exterior-grove-substrate.py'))
        self.assertEqual(p['activeDesign'],{'variant':'C','heatingLayout':'B','livingLayout':'B'})
        self.assertEqual(p['housePlacement'],self.context['housePlacement'])
        self.assertEqual(p['housePlacement']['streetSetbackMm'],3000);self.assertEqual(p['housePlacement']['eastSetbackMm'],3000)
        for path,value in p['inputFiles'].items():self.assertEqual(substrate.sha(path),value,path)
        for key in('plan','geometryManifest','materialManifest','previewGeometry'):
            item=self.manifest[key];self.assertEqual(substrate.sha(item['path']),item['sha256'])
        self.assertEqual(p['trees'],self.ecology['existingTrees']);self.assertEqual(p['trees'],self.trees);self.assertEqual(len(self.trees),78)
        self.assertEqual(p['sourceRegion'],self.region);self.assertEqual(p['domainCm'],self.ecology['ecologyDomainCm'])
        self.assertTrue(shapely.equals_exact(shapely.from_geojson(p['domainCm']),self.domain,1e-7))
        self.assertEqual(substrate.read(self.manifest['geometryManifest']['path'])['meshes'],[])
        for key in('sourceGroundUnchanged','originalTreesUnchanged','protectedArchitectureUnchanged','sourcePixelsUnmodified','exactOriginalEcologyDomain'):
            self.assertIs(p['policy'][key],True)
        self.assertIs(p['audit']['nativeVerified'],False)

    def test_provider_api_original_bytes_and_native_three_map_physical_recipe(self):
        files=substrate.read(self.receipt['filesApi']['path'])
        self.assertEqual(self.receipt['license'],'CC0-1.0');self.assertEqual(self.receipt['physicalTileCm'],150)
        for role,key in substrate.ROLES.items():
            item=self.receipt['maps'][role];provider=files[key]['2k']['png'];payload=Path(item['path']).read_bytes()
            self.assertEqual(item['md5'],hashlib.md5(payload).hexdigest());self.assertEqual(item['md5'],provider['md5'])
            self.assertEqual(len(payload),provider['size']);self.assertEqual(item['url'],provider['url'])
            self.assertEqual(substrate.sha(item['path']),item['sha256'])
            with Image.open(item['path'])as image:self.assertEqual(image.size,(2048,2048));self.assertEqual(image.format,'PNG')
        r=self.recipe;self.assertEqual(set(r['maps']),{'albedo','normal','roughness'});self.assertEqual(r['kind'],'ground')
        self.assertEqual(r['tileCm'],150);self.assertEqual(r['yawDegrees'],0);self.assertEqual(r['normalConvention'],'OpenGL')
        self.assertIs(r['featherUV'],True);self.assertIs(r['stochasticGround'],False);self.assertEqual(r['distanceFadeCm'],[12000.,18000.])
        self.assertEqual(r['sourceUrl'],'https://polyhaven.com/a/forest_leaves_04')
        for role,item in r['maps'].items():self.assertEqual(item,{k:self.receipt['maps'][role][k]for k in('path','sha256')})

    def test_every_actual_triangle_complete_inside_holes_preserved_area_and_no_overlap(self):
        total=0;count=0
        safe=self.domain.buffer(2e-8)
        for mesh in self.plan['meshes']:
            p=np.asarray(mesh['verticesCm']);idx=np.asarray(mesh['indices']).reshape(-1,3);faces=p[idx]
            triangles=shapely.polygons(faces[:,:,:2]);outside=shapely.area(shapely.difference(triangles,safe))
            self.assertLess(float(outside.max()),1e-6,mesh['id'])
            self.assertTrue(shapely.covers(safe,triangles).all(),mesh['id'])
            winding=np.cross(faces[:,2]-faces[:,0],faces[:,1]-faces[:,0])
            self.assertGreater(float(winding[:,2].min()),1e-7)
            self.assertLessEqual(float(np.linalg.norm(faces[:,:2,:2]-faces[:,1:3,:2],axis=2).max()),12.5*np.sqrt(2)+1e-6)
            area=shapely.area(triangles);total+=float(area.sum());count+=len(idx)
            self.assertAlmostEqual(float(shapely.union_all(triangles).area),float(area.sum()),places=5)
            np.testing.assert_allclose(p.min(axis=0),mesh['bounds']['min'],atol=1e-8,rtol=0)
            np.testing.assert_allclose(p.max(axis=0),mesh['bounds']['max'],atol=1e-8,rtol=0)
            self.assertEqual(mesh['collision'],'NoCollision');self.assertIs(mesh['castShadow'],False)
            self.assertEqual(mesh['maxDrawDistanceCm'],18000);self.assertIs(mesh['nanite'],False)
        self.assertAlmostEqual(total,self.domain.area,places=3);self.assertEqual(count,self.plan['audit']['triangles'])
        self.assertAlmostEqual(total/10000,self.plan['audit']['actualTriangleAreaM2'],places=8)

    def test_decoded_glb_actual_axes_normals_coverage_indices_and_chunk_scope(self):
        doc,decode=glb(OUTPUT/'grove-substrate-preview.glb');lookup={node['name']:doc['meshes'][node['mesh']]for node in doc['nodes']}
        self.assertEqual(len(lookup),len(self.plan['meshes']));self.assertEqual(doc['asset']['version'],'2.0')
        for mesh in self.plan['meshes']:
            node=lookup[mesh['id']+'_LOD0'];self.assertEqual(len(node['primitives']),1);primitive=node['primitives'][0];attrs=primitive['attributes']
            points=decode(attrs['POSITION'])[:,[0,2,1]].astype(float)*100
            # Exact IEEE754 float32 cm->metre/axis witness; at worldY256m,
            # the maximum expected conversion quantisation is0.00153cm.
            encoded=(np.asarray(mesh['verticesCm'])[:,[0,2,1]]/100).astype(np.float32)
            np.testing.assert_array_equal(decode(attrs['POSITION']),encoded)
            np.testing.assert_allclose(points,mesh['verticesCm'],atol=.002,rtol=0)
            np.testing.assert_array_equal(decode(primitive['indices']).ravel(),mesh['indices'])
            np.testing.assert_allclose(decode(attrs['TEXCOORD_0']),mesh['uvs'],atol=3e-8,rtol=0)
            normals=decode(attrs['NORMAL'])[:,[0,2,1]].astype(float)
            np.testing.assert_allclose(normals,mesh['normals'],atol=3e-8,rtol=0)
            np.testing.assert_allclose(np.linalg.norm(normals,axis=1),1,atol=5e-8,rtol=0)
            self.assertGreater(float(normals[:,2].min()),.99)

    def test_actual_source_registered_microrelief_and_edge_alpha_full_opaque_core(self):
        core=0;boundary=0;seams={};duplicates=0
        for mesh in self.plan['meshes']:
            p=np.asarray(mesh['verticesCm']);xy=p[:,:2];alpha=np.asarray(mesh['uvs'])[:,0]
            distances=shapely.distance(shapely.points(xy),self.domain.boundary)
            widths=180+22*np.sin(xy[:,0]/127+xy[:,1]/211)+13*np.sin(xy[:,0]/43-xy[:,1]/73+1.7)
            t=np.clip(distances/widths,0,1);expected=t*t*(3-2*t)
            np.testing.assert_allclose(alpha,expected,atol=1e-12,rtol=0)
            np.testing.assert_array_equal(np.asarray(mesh['uvs'])[:,1],np.zeros(len(p)))
            np.testing.assert_allclose(p[:,2]+25,.12+.68*substrate.sample_height(xy,self.height)*alpha,atol=1e-11,rtol=0)
            self.assertGreaterEqual(float((p[:,2]+25).min()),.12-1e-10);self.assertLessEqual(float((p[:,2]+25).max()),.8+1e-10)
            self.assertTrue((alpha[distances>=215]==1).all());self.assertTrue((alpha[distances<1e-7]<1e-12).all())
            self.assertEqual(mesh['sourceGround'],{'id':'context_unresolved_flat_backdrop','zCm':-25.,'measuredElevation':False})
            core+=int((alpha==1).sum());boundary+=int((distances<1e-7).sum())
            for row,a in zip(p,alpha):
                key=tuple(row[:2]);value=(row[2],a)
                if key in seams:np.testing.assert_allclose(value,seams[key],atol=1e-12,rtol=0);duplicates+=1
                else:seams[key]=value
        self.assertGreater(core,50000);self.assertGreater(boundary,5000);self.assertGreater(duplicates,1000)
        # Metric source phase repeats exactly at the provider's declared scale,
        # including negative world coordinates; camera movement is irrelevant.
        xy=np.array([[-14.3,231.2],[4395.17,20473.13],[7732.1,23121.25]])
        np.testing.assert_allclose(substrate.sample_height(xy,self.height),substrate.sample_height(xy+150,self.height),atol=1e-12,rtol=0)

    def test_immutable_output_and_unsafe_provider_receipt_source_frame_rejected(self):
        args=[self.plan[k]['path']for k in('sourceContext','sourceEcology','sourceTerrain','sourceBuildings','sourceScene')]
        with self.assertRaisesRegex(ValueError,'fresh immutable'):
            substrate.build(*args,Path(self.plan['acquisitionManifest']['path']).parent,OUTPUT)
        with tempfile.TemporaryDirectory(dir=ROOT/'output/unreal')as temporary:
            temp=Path(temporary);bad=copy.deepcopy(self.receipt);bad['physicalTileCm']=1
            (temp/'acquisition-receipt.json').write_text(json.dumps(bad))
            with self.assertRaisesRegex(ValueError,'Unreviewed'):
                substrate.verified_acquisition(temp)
            wrong=copy.deepcopy(self.ecology);wrong['sourceSceneSha256']='0'*64
            path=temp/'ecology.json';path.write_text(json.dumps(wrong))
            with self.assertRaisesRegex(ValueError,'scene/OBJ'):
                substrate.source(args[0],path,*args[2:])


if __name__=='__main__':unittest.main()
