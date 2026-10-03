"""Independent decoded anatomy, source-frame and garden crown tests; no Unreal."""
import importlib.util
import json
import math
from pathlib import Path
import struct
import unittest

import numpy as np
from PIL import Image
import shapely
from shapely.geometry import Polygon

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('organic_study',HERE/'exterior-garden-organic.py')
study=importlib.util.module_from_spec(spec);spec.loader.exec_module(study)
OUT=study.OUTPUT


def decode(path):
    raw=Path(path).read_bytes();magic,version,length=struct.unpack_from('<4sII',raw)
    if (magic,version,length)!=(b'glTF',2,len(raw)):raise AssertionError('Bad GLB header')
    count,kind=struct.unpack_from('<II',raw,12)
    if kind!=0x4e4f534a:raise AssertionError('Missing JSON chunk')
    doc=json.loads(raw[20:20+count]);size,kind=struct.unpack_from('<II',raw,20+count)
    if kind!=0x004e4942 or 28+count+size!=len(raw):raise AssertionError('Missing binary chunk')
    binary=raw[28+count:]
    def values(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dtype={5126:'<f4',5125:'<u4'}[a['componentType']]
        return np.frombuffer(binary,dtype=dtype,count=a['count']*width,offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,width).astype(float)
    result={}
    for node in doc['nodes']:
        if any(key in node for key in ('matrix','translation','rotation','scale')):raise AssertionError('Unexpected unbaked node transform')
        parts={}
        for p in doc['meshes'][node['mesh']]['primitives']:
            a=p['attributes'];t=values(a['TANGENT']);key=doc['materials'][p['material']]['name']
            parts[key]={'positions':values(a['POSITION'])[:,[0,2,1]]*100,'normals':values(a['NORMAL'])[:,[0,2,1]],
                'tangents':np.column_stack([t[:,:3][:,[0,2,1]],-t[:,3]]),'uv':values(a['TEXCOORD_0']),
                'colors':values(a['COLOR_0']),'triangles':values(p['indices']).astype(int).reshape(-1,3)[:,[0,2,1]]}
        result[node['name']]=parts
    return doc,result


class OrganicGarden(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=study.read(OUT/'garden-plan.json');cls.bundle=study.read(OUT/'garden-organic-manifest.json')
        cls.old=study.read(study.GARDEN);cls.library=study.read(OUT/'geometry-manifest.json')
        cls.original_library=study.read(study.LIBRARY);cls.recipes=study.read(OUT/'material-manifest.json')
        cls.morphology=study.read(OUT/'morphology-audit.json');cls.crown=study.read(OUT/'crown-validation.json')
        cls.doc,cls.actual=decode(OUT/'garden-organic.glb')

    def test_r10_source_closure_exact_existing_recipes_maps_and_cbb_are_preserved(self):
        for path,digest in self.bundle['inputFiles'].items():self.assertEqual(study.sha(path),digest,path)
        self.assertEqual(self.bundle['generatorSha256'],study.sha(HERE/'exterior-garden-organic.py'))
        for field in ('sourceNativeImport','sourceGarden','sourceLibrary','geometryManifest','materialManifest','plan','morphology','glb','preview','assetManifest','crownValidation'):
            entry=self.bundle[field];self.assertEqual(study.sha(entry['path']),entry['sha256'])
        self.assertEqual(len(self.original_library['meshes']),96)
        report=study.read(study.REPORT)
        self.assertEqual(report['gardenPlanting']['instances'],461);self.assertEqual(report['gardenPlanting']['ornamentalReplacements'],12)
        originals=study.read(study.MATERIALS)
        self.assertEqual(set(self.recipes),set(study.ALLOWED))
        for key,recipe in self.recipes.items():
            self.assertEqual(recipe,originals[key])
            for entry in recipe.get('maps',{}).values():self.assertEqual(study.sha(entry['path']),entry['sha256'])
        self.assertEqual(self.plan['activeDesign'],{'variant':'C','heatingLayout':'B','livingLayout':'B'})
        self.assertEqual(self.plan['housePlacement'],self.old['housePlacement'])
        self.assertEqual(self.plan['housePlacement']['streetSetbackMm'],3000)
        self.assertEqual(self.plan['housePlacement']['eastSetbackMm'],3000)
        for field in ('sourceMulchTrianglesCm','sourceStepTrianglesCm','sourceCardPointsCm','sourceSceneSha256','sourceObjSha256','hideSourceIds'):
            self.assertEqual(self.plan[field],self.old[field])
        self.assertEqual(self.doc['asset']['generator'],study.OWNER)
        self.assertEqual({m['name']for m in self.doc['materials']},set(study.ALLOWED))

    def test_actual_twelve_lod_meshes_bounds_and_rebuilt_uv_normal_tangent_winding(self):
        self.assertEqual(len(self.actual),12);self.assertEqual(len(self.library['meshes']),4)
        self.assertEqual({m['id']for m in self.library['meshes']},set(study.MAPPING.values()))
        for master in self.library['meshes']:
            self.assertEqual([row['level']for row in master['lods']],[0,1,2])
            for lod in master['lods']:
                parts=self.actual[lod['nodeName']];p=np.concatenate([part['positions']for part in parts.values()])
                self.assertEqual(len(p),lod['vertices']);self.assertEqual(sum(len(part['triangles'])for part in parts.values()),lod['triangles'])
                self.assertLessEqual(lod['triangles'],20000)
                np.testing.assert_allclose(p.min(axis=0),lod['expectedBoundsCm']['min'],atol=.000005)
                np.testing.assert_allclose(p.max(axis=0),lod['expectedBoundsCm']['max'],atol=.000005)
                self.assertAlmostEqual(np.linalg.norm(p[:,:2],axis=1).max(),lod['radialEnvelopeCm'],places=7)
                self.assertGreaterEqual(p[:,2].min(),-.000005)
                self.assertLessEqual(p[:,2].max(),77.800005 if 'white' in master['id']else 9.300005)
                for part in parts.values():
                    p,n,t,uv,faces=(part[k]for k in ('positions','normals','tangents','uv','triangles'))
                    self.assertTrue(all(np.isfinite(v).all()for v in part.values()))
                    np.testing.assert_allclose(np.linalg.norm(n,axis=1),1.,atol=1e-6)
                    np.testing.assert_allclose(np.linalg.norm(t[:,:3],axis=1),1.,atol=1e-6)
                    np.testing.assert_allclose((n*t[:,:3]).sum(axis=1),0.,atol=1e-6)
                    q=p[faces];e1,e2=q[:,1]-q[:,0],q[:,2]-q[:,0];cross=np.cross(e1,e2)
                    self.assertTrue((np.linalg.norm(cross,axis=1)>1e-9).all())
                    self.assertTrue((np.einsum('ij,ij->i',cross,n[faces].mean(axis=1))>0).all())
                    d1,d2=uv[faces[:,1]]-uv[faces[:,0]],uv[faces[:,2]]-uv[faces[:,0]];det=d1[:,0]*d2[:,1]-d1[:,1]*d2[:,0]
                    self.assertTrue((abs(det)>1e-10).all())
                    expected_n=np.zeros_like(p);expected_t=np.zeros_like(p);expected_b=np.zeros_like(p)
                    vt=(e1*d2[:,1,None]-e2*d1[:,1,None])/det[:,None]
                    vb=(e2*d1[:,0,None]-e1*d2[:,0,None])/det[:,None]
                    for column in range(3):
                        np.add.at(expected_n,faces[:,column],cross);np.add.at(expected_t,faces[:,column],vt);np.add.at(expected_b,faces[:,column],vb)
                    expected_n/=np.linalg.norm(expected_n,axis=1)[:,None]
                    expected_t-=expected_n*(expected_t*expected_n).sum(axis=1)[:,None]
                    expected_t/=np.linalg.norm(expected_t,axis=1)[:,None]
                    np.testing.assert_allclose(n,expected_n,atol=.00007)
                    np.testing.assert_allclose(t[:,:3],expected_t,atol=.00007)
                    np.testing.assert_array_equal(t[:,3],np.where((np.cross(expected_n,expected_t)*expected_b).sum(axis=1)<0,-1.,1.))

    def test_decoded_branch_rings_parent_connections_and_each_leaf_attached_to_its_petiole(self):
        for master in self.library['meshes']:
            for lod in master['lods']:
                level=lod['level'];proof=self.morphology[master['id']][level];parts=self.actual[lod['nodeName']]
                green=parts['garden_blade_green'];offset=0;centers={}
                self.assertEqual(sum(row['parent']is None for row in proof['branches']),1)
                for branch in proof['branches']:
                    kind=branch['kind'];sides={'rooted-main':(6,5,4)[level],'flowering-shoot':(5,4,4)[level],
                        'axillary-shoot':(4,4,3)[level],'creeping-root':(4,4,3)[level],'broadleaf-shoot':3,
                        'leaf-petiole':3,'floret-pedicel':3,'flower-receptacle':5}[kind]
                    count=len(branch['pathCm'])*(sides+1);p=green['positions'][offset:offset+count].reshape(-1,sides+1,3)
                    actual_centers=p[:,:sides].mean(axis=1);centers[branch['id']]=actual_centers
                    np.testing.assert_allclose(actual_centers,branch['pathCm'],atol=.000008)
                    radii=np.linalg.norm(p[:,:sides]-actual_centers[:,None],axis=2)
                    target=np.array([branch['radiusCm']*(1-.45*j/(len(p)-1))for j in range(len(p))])
                    np.testing.assert_allclose(radii,np.repeat(target[:,None],sides,axis=1),atol=.000008)
                    if branch['parent']is not None:
                        self.assertLess(branch['parent'],branch['id'])
                        parent=proof['branches'][branch['parent']]
                        np.testing.assert_allclose(actual_centers[0],study.curve(parent['pathCm'],branch['parentT']),atol=.000008)
                    offset+=count
                self.assertEqual(offset,len(green['positions']))
                photo=parts['regional_green_leaf'];expected_count=176 if master['id']=='garden_white_organic_a'else 204 if master['id']=='garden_white_organic_b'else 16 if master['id']=='garden_broadleaf_organic_a'else 23
                self.assertEqual(proof['leafCount'],expected_count);self.assertEqual(len(proof['leaves']),expected_count)
                self.assertEqual(sum(row['vertexCount']for row in proof['leaves']),len(photo['positions']))
                self.assertEqual(sum(row['triangleCount']for row in proof['leaves']),len(photo['triangles']))
                for leaf in proof['leaves']:
                    p=photo['positions'][leaf['vertexOffset']:leaf['vertexOffset']+leaf['vertexCount']]
                    np.testing.assert_allclose(p[0],centers[leaf['parentPetiole']][-1],atol=.000008)
                    np.testing.assert_allclose(p[0],leaf['anchorCm'],atol=.000008)
                    np.testing.assert_allclose(p[-1],leaf['centerlineCm'][-1],atol=.000008)
                    self.assertIs(leaf['pointedTip'],True)
                    self.assertGreater(np.linalg.norm(np.cross(p[2]-p[0],p[-1]-p[0])),.001)
                    if len(p)>11:self.assertGreater(np.linalg.norm(p[2]-(p[1]+p[3])*.5),.005)
                self.assertGreaterEqual(len({r['age']for r in proof['leaves']}),2)
        for master in self.library['meshes']:
            counts=[self.morphology[master['id']][i]['leafCount']for i in range(3)]
            self.assertEqual(counts,[counts[0]]*3)

    def test_real_cupped_florets_and_opaque_photographic_tissue_uv_without_whole_plant_cards(self):
        recipe=self.recipes['regional_green_leaf'];path=recipe['maps']['alpha']['path']
        with Image.open(path)as image:alpha=np.array(image.convert('L'))
        u0,v0,u1,v1=study.LEAF_UV
        patch=alpha[int(v0*(alpha.shape[0]-1)):math.ceil(v1*(alpha.shape[0]-1))+1,
                    int(u0*(alpha.shape[1]-1)):math.ceil(u1*(alpha.shape[1]-1))+1]
        self.assertGreaterEqual(int(patch.min()),254)
        for master in self.library['meshes']:
            for lod in master['lods']:
                parts=self.actual[lod['nodeName']];proof=self.morphology[master['id']][lod['level']]
                uv=parts['regional_green_leaf']['uv']
                self.assertTrue((uv[:,0]>=u0-1e-7).all()and(uv[:,0]<=u1+1e-7).all())
                self.assertTrue((uv[:,1]>=v0-1e-7).all()and(uv[:,1]<=v1+1e-7).all())
                self.assertTrue(np.all(parts['regional_green_leaf']['colors']==1.))
                if 'white' in master['id']:
                    expected=184 if master['id'].endswith('_a')else 211
                    self.assertEqual(proof['flowers'],expected);self.assertEqual(len(proof['inflorescences']),expected)
                    p=parts['garden_plume_silk']['positions']
                    self.assertEqual(len(p),expected*36)
                    self.assertEqual(sum(b['kind']=='flower-receptacle'for b in proof['branches']),expected)
                    for flower in proof['inflorescences']:
                        self.assertEqual(flower['petalCount'],4);self.assertIs(flower['actualCuppedPetals'],True)
                        np.testing.assert_allclose(flower['centerCm'],proof['branches'][flower['parentPedicel']]['pathCm'][-1],atol=1e-9)
                        q=p[flower['vertexOffset']:flower['vertexOffset']+9]
                        normal=np.cross(q[1]-q[0],q[3]-q[0]);normal/=np.linalg.norm(normal)
                        self.assertGreater(abs((q[8]-q[0])@normal),.003)
                else:self.assertEqual(proof['flowers'],0)

    def test_every_transformed_crown_inside_unchanged_beds_and_exact473_rows_except_selected_ids(self):
        beds={key:shapely.union_all([Polygon([p[:2]for p in t])for t in triangles])for key,triangles in self.old['sourceMulchTrianglesCm'].items()}
        masters={m['id']:m for m in self.library['meshes']};audit={r['id']:r for r in self.crown['measuredReplacements']};changed=0;other=0
        self.assertEqual(len(audit),424);self.assertEqual(self.crown['instances'],424)
        for collection in ('ornamentalPlacements','gardenDetailPlacements'):
            rows=self.plan[collection];before=self.old[collection]
            self.assertEqual(len(rows),len(before));self.assertEqual(self.plan['original'+collection[0].upper()+collection[1:]],before)
            for row,old in zip(rows,before):
                if old['meshId']not in study.MAPPING:self.assertEqual(row,old);other+=1;continue
                expected={**old,'meshId':study.MAPPING[old['meshId']],'sourceMeshId':old['meshId']};self.assertEqual(row,expected);changed+=1
                points=np.concatenate([part['positions']for lod in masters[row['meshId']]['lods']for part in self.actual[lod['nodeName']].values()])
                radius=np.linalg.norm(points[:,:2],axis=1).max()*row['uniformScale'];height=points[:,2].max()*row['uniformScale']
                self.assertLessEqual(radius,old['radiusCm']+1e-5);self.assertLessEqual(height,old['actualHeightCm']+1e-5)
                root=shapely.Point(row['positionCm'][:2]);bed=beds[row['sourceBedId']];clearance=root.distance(bed.boundary)-radius
                self.assertTrue(bed.contains(root));self.assertGreater(clearance,0.)
                self.assertAlmostEqual(radius,audit[row['id']]['actualRadiusCm'],places=7)
                self.assertAlmostEqual(height,audit[row['id']]['actualHeightCm'],places=7)
                self.assertAlmostEqual(clearance,audit[row['id']]['fullCrownToOriginalBedClearanceCm'],places=7)
                angle=math.radians(row['yawDeg']);c,s=math.cos(angle),math.sin(angle);world=points[:,:2]*row['uniformScale']
                world=world@np.array([[c,s],[-s,c]])+row['positionCm'][:2]
                self.assertTrue(shapely.contains_xy(bed,world[:,0],world[:,1]).all())
        self.assertEqual((changed,other),(424,49))
        self.assertEqual(self.crown['measuredReplacements'],self.plan['organicStudy']['measuredReplacements'])
        self.assertGreater(self.crown['minimumFullCrownToBedEdgeCm'],0.)

    def test_actual_cpu_comparison_and_source_limits_do_not_grant_native_acceptance(self):
        self.assertEqual(self.bundle['audit']['whiteHeroReplacements'],4);self.assertEqual(self.bundle['audit']['lowerClumpReplacements'],420)
        for key in ('nativeVerified','nativeAppearanceAccepted','performanceAccepted','integrationAuthorized'):
            self.assertIs(self.plan['organicStudy'][key],False)
        self.assertIs(self.plan['organicStudy']['artistInterpretation'],True);self.assertIs(self.plan['organicStudy']['surveyedBotany'],False)
        self.assertIn('not a claim about native texture encoding',self.bundle['previewPolicy'])
        with Image.open(OUT/'organic-side-by-side.png')as image:
            self.assertEqual(image.size,(2400,1360));pixels=np.array(image)
        self.assertGreater(np.mean(abs(pixels[70:690,:600].astype(float)-pixels[70:690,600:1200])),1.)
        self.assertGreater(np.mean(abs(pixels[70:690,1200:1800].astype(float)-pixels[70:690,1800:2400])),1.)
        with self.assertRaisesRegex(ValueError,'immutable'):study.build(OUT)


if __name__=='__main__':unittest.main()
