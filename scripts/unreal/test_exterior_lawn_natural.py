"""Independent source-domain, curved geometry and immutable lawn GLB checks."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
import tempfile
import unittest

import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('natural_lawn',HERE/'exterior-lawn-natural.py')
natural=importlib.util.module_from_spec(spec);spec.loader.exec_module(natural)
OUTPUT=ROOT/'output/unreal/exterior-lawn-natural-20260930-r1'
GEOMETRY=ROOT/'output/unreal/realism-20260926-r5/geometry'


def read(path):return json.loads(Path(path).read_text())


def glb(path):
    raw=Path(path).read_bytes();magic,version,length=struct.unpack_from('<4sII',raw)
    if magic!=b'glTF' or version!=2 or length!=len(raw):raise AssertionError('Invalid GLB header')
    size,kind=struct.unpack_from('<II',raw,12)
    if kind!=0x4e4f534a:raise AssertionError('Missing GLB JSON')
    doc=json.loads(raw[20:20+size]);offset=20+size
    binsize,binkind=struct.unpack_from('<II',raw,offset)
    if binkind!=0x004e4942:raise AssertionError('Missing GLB binary')
    binary=raw[offset+8:offset+8+binsize]
    def decode(index):
        row=doc['accessors'][index];view=doc['bufferViews'][row['bufferView']]
        width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[row['type']]
        dtype={5126:'<f4',5125:'<u4'}[row['componentType']]
        return np.frombuffer(binary,dtype=dtype,count=row['count']*width,
                             offset=view.get('byteOffset',0)+row.get('byteOffset',0)).reshape(-1,width)
    return doc,decode


class NaturalLawn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(OUTPUT/'lawn-natural-plan.json');cls.manifest=read(OUTPUT/'lawn-natural-manifest.json')
        cls.library=read(OUTPUT/'geometry-manifest.json');cls.records=read(OUTPUT/'lawn-natural-prototypes.json')
        cls.lookup={row['id']:row for row in cls.library['meshes']}
        cls.scene,cls.faces,cls.grass,cls.forbidden,cls.domain,cls.exclusions,cls.extra=natural.source_domain(GEOMETRY)

    def test_source_and_output_pins_preserve_canonical_masks(self):
        for path,expected in self.plan['inputFiles'].items():self.assertEqual(natural.sha(path),expected,path)
        self.assertEqual(self.plan['owner'],'scripts/unreal/exterior-lawn-natural.py')
        self.assertEqual(self.plan['activeDesign'],natural.ACTIVE)
        self.assertEqual(self.plan['housePlacement'],self.scene['house']['placement'])
        self.assertEqual(self.plan['sourceSceneSha256'],natural.sha(GEOMETRY/'scene.json'))
        self.assertEqual(self.plan['sourceObjSha256'],natural.sha(GEOMETRY/'dom-mm.obj'))
        self.assertEqual(self.plan['housePlacement']['streetSetbackMm'],3000)
        self.assertEqual(self.plan['housePlacement']['eastSetbackMm'],3000)
        self.assertEqual(self.plan['exclusions'],json.loads(json.dumps(self.exclusions)))
        self.assertEqual(self.plan['sourceLawnId'],'DOM_00001')
        self.assertEqual(self.plan['sourceTriangleCount'],27)
        self.assertTrue(shapely.equals_exact(shapely.from_geojson(self.plan['lawnDomainSourceMm']),self.domain,1e-8))
        for key in ('plan','glb','geometryManifest','materialManifest','geometryProof'):
            row=self.manifest[key];self.assertEqual(natural.sha(row['path']),row['sha256'],key)
        self.assertEqual(self.plan['replacementPolicy']['inheritedLawnGroups'],['LawnTuft0','LawnTuft1','LawnTuft2','LawnTuft3'])
        self.assertTrue(self.plan['replacementPolicy']['sourceGroundAndCollisionUnchanged'])

    def test_actual_glb_geometry_axes_bounds_vertex_colours_and_all_lods(self):
        doc,decode=glb(OUTPUT/'lawn-natural.glb')
        nodes={node['name']:doc['meshes'][node['mesh']]for node in doc['nodes']}
        self.assertEqual(len(nodes),60)
        for record in self.records:
            primitive=nodes[record['nodeName']]['primitives'][0];attrs=primitive['attributes']
            native=decode(attrs['POSITION'])[:,[0,2,1]]*100
            np.testing.assert_allclose(native,record['positionsCm'],atol=.000003,rtol=0)
            for key,op in [('min',np.min),('max',np.max)]:
                np.testing.assert_allclose(op(native,axis=0),record['expectedBoundsCm'][key],atol=.000003,rtol=0)
            indices=decode(primitive['indices']).reshape(-1,3)[:,[0,2,1]]
            np.testing.assert_array_equal(indices,record['triangles'])
            colors=decode(attrs['COLOR_0'])
            np.testing.assert_allclose(colors,record['colors'],atol=3e-8,rtol=0)
            self.assertTrue(np.isfinite(colors).all());self.assertTrue(((colors>=0)&(colors<=1)).all())
            np.testing.assert_allclose(colors[:,3],1)
            normals=decode(attrs['NORMAL']);tangents=decode(attrs['TANGENT'])
            np.testing.assert_allclose(np.linalg.norm(normals,axis=1),1,atol=1e-6)
            np.testing.assert_allclose(np.linalg.norm(tangents[:,:3],axis=1),1,atol=1e-6)
            np.testing.assert_allclose((normals*tangents[:,:3]).sum(axis=1),0,atol=1e-6)
            triangles=native[indices]
            areas=np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1)
            self.assertGreater(float(areas.min()),1e-8)
        for mesh in self.library['meshes']:
            self.assertEqual(mesh['placementPolicy'],'explicit-only');self.assertEqual(mesh['role'],'grass')
            self.assertEqual(mesh['materialKeys'],['lawn_natural_blade']);self.assertEqual(mesh['lodScreenSizes'],[1,.025,.007])
            self.assertGreater(mesh['lods'][0]['triangles'],mesh['lods'][1]['triangles'])
            self.assertGreater(mesh['lods'][1]['triangles'],mesh['lods'][2]['triangles'])

    def test_blades_are_curved_folded_and_mixed_through_far_lod(self):
        for record in self.records:
            lod=record['level'];minimum=[4,3,2][lod]
            ranges=record['bladeRanges'];self.assertEqual(len(ranges),48 if lod<2 else 24)
            self.assertTrue(any(row['low']for row in ranges));self.assertTrue(any(not row['low']for row in ranges))
            self.assertTrue(any(row['clipped']for row in ranges));self.assertTrue(any(not row['clipped']for row in ranges))
            for blade in ranges:
                self.assertGreaterEqual(blade['segments'],minimum)
                centers=np.asarray(blade['centerlineCm']);levels=np.linspace(0,1,len(centers))[:,None]
                chord=centers[0]+levels*(centers[-1]-centers[0])
                self.assertGreater(float(np.linalg.norm(centers-chord,axis=1).max()),.03)
                start,count=blade['vertexOffset'],blade['vertexCount'];p=np.asarray(record['positionsCm'][start:start+count])
                colors=np.asarray(record['colors'][start:start+count])
                self.assertGreater(float(np.linalg.norm(colors[-1,:3]-colors[0,:3])),.1)
                if lod<2:
                    for i in range(0,count,3):self.assertGreater(p[i+1,2]-(p[i,2]+p[i+2,2])/2,.001)
            roots=np.asarray([row['rootCm']for row in ranges]);radius=np.linalg.norm(roots,axis=1)
            self.assertGreater(float(radius.std()),.1 if record['edgeMaster']else 1.)

    def test_every_saved_instance_has_actual_complete_crown_clearance(self):
        rows=self.plan['lawnPlacements'];self.assertEqual(len(rows),24918)
        self.assertEqual(sum(len(g['instances'])for g in self.plan['groups']),len(rows))
        flat=[{'meshId':g['meshId'],**row}for g in self.plan['groups']for row in g['instances']]
        self.assertEqual(rows,flat)
        p=np.asarray([row['positionCm']for row in rows]);xy=np.column_stack([p[:,0]*10,-p[:,1]*10])
        self.assertTrue(shapely.contains_xy(self.domain,*xy.T).all());np.testing.assert_allclose(p[:,2],-6.5,atol=0)
        distance=shapely.distance(shapely.points(xy),self.domain.boundary)
        radii=[]
        for row in rows:
            mesh=self.lookup[row['meshId']];scale=row['scale']
            self.assertEqual(scale,[scale[0]]*3);self.assertTrue(.6<=scale[0]<=1.25)
            actual=max(math.hypot(*v[:2])for r in self.records if r['nodeName'].startswith(row['meshId']+'_LOD')for v in r['positionsCm'])
            radii.append(actual*scale[0]*10+1)
            self.assertAlmostEqual(row['radiusCm'],actual*scale[0],places=7)
            self.assertAlmostEqual(row['actualHeightCm'],mesh['heightCm']*scale[0],places=7)
        margin=distance-np.asarray(radii)
        self.assertGreater(float(margin.min()),0)
        self.assertAlmostEqual(float(margin.min()),self.plan['audit']['minimumAdditionalCrownClearanceMm'],places=3)
        for group in self.plan['groups']:
            self.assertTrue(group['qualityDetail']);self.assertEqual(group['cullEndCm'],4000)
        policy=self.plan['renderingPolicy'];self.assertEqual(policy['collision'],'none')
        self.assertFalse(policy['navigation']);self.assertEqual(policy['windDisplacementCm'],0)
        self.assertLessEqual(self.plan['audit']['nearTriangleBudget'],26000000)

    def test_placement_breaks_old_lattice_and_has_coherent_multiscale_variation(self):
        rows=[row for row in self.plan['lawnPlacements']if not row['edge']]
        roots=np.asarray([[row['positionCm'][0]*10,-row['positionCm'][1]*10]for row in rows])
        phase=np.abs(np.exp(2j*np.pi*roots/60).mean(axis=0));self.assertLess(float(phase.max()),.04)
        scales=np.asarray([row['scale'][0]for row in rows]);self.assertGreater(float(scales.std()),.04)
        x,y=np.meshgrid(np.arange(-6000,6000,47.),np.arange(-6000,6000,53.));a=natural.growth_fields(x,y)
        near=natural.growth_fields(x+30,y-20);far=natural.growth_fields(x+2000,y-1500)
        self.assertLess(float(np.abs(a[1]-near[1]).mean()),float(np.abs(a[1]-far[1]).mean())*.15)
        self.assertGreater(float(a[0].std()),.04)
        self.assertGreater(self.plan['audit']['nearestPatchCentreDistanceMm']['standardDeviation'],15)
        material=read(OUTPUT/'material-manifest.json')['lawn_natural_blade']
        self.assertEqual(material['kind'],'authored-foliage');self.assertEqual(material['maps'],{})
        self.assertEqual(material['linearColor'],[.06,.10,.024]);self.assertEqual(material['subsurfaceScale'],.16)

    def test_rejects_changed_design_setbacks_lawn_and_output_overwrite(self):
        original=read(GEOMETRY/'scene.json')
        for mutate in [lambda scene:scene['activeDesign'].update(variant='A'),
                       lambda scene:scene['house']['placement'].update(streetSetbackMm=2999),
                       lambda scene:scene['house']['placement'].update(eastSetbackMm=2999),
                       lambda scene:next(row for row in scene['objects']if row['id']=='DOM_00001').update(materialNames=['road'])]:
            with tempfile.TemporaryDirectory(dir=ROOT/'output/unreal',prefix='lawn-source-rejection-')as directory:
                path=Path(directory);scene=copy.deepcopy(original);mutate(scene)
                (path/'scene.json').write_text(json.dumps(scene));(path/'dom-mm.obj').symlink_to(GEOMETRY/'dom-mm.obj')
                with self.assertRaisesRegex(RuntimeError,'C/B/B|Setbacks|Wrong source lawn'):natural.source_domain(path)
        with self.assertRaisesRegex(ValueError,'immutable'):natural.build(GEOMETRY,OUTPUT)


if __name__=='__main__':unittest.main()
