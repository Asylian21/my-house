"""Actual GLB coverage, all-LOD area and independent managed crown checks."""
from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest

import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('continuous_lawn',HERE/'exterior-lawn-coverage.py')
cover=importlib.util.module_from_spec(spec);spec.loader.exec_module(cover)
OUTPUT=ROOT/'output/unreal/exterior-lawn-natural-20260930-r3d'
GEOMETRY=ROOT/'output/unreal/realism-20260926-r5/geometry'
RURAL=ROOT/'output/unreal/exterior-20260930-r5/geometry/rural-context-geometry.json'
ORIGINAL=ROOT/'output/unreal/exterior-lawn-natural-20260930-r1/lawn-natural-plan.json'
PRIOR=ROOT/'output/unreal/exterior-lawn-natural-20260930-r2b'


def read(path):return json.loads(Path(path).read_text())


def decode_glb(path):
    raw=Path(path).read_bytes();magic,version,length=struct.unpack_from('<4sII',raw)
    if (magic,version,length)!=(b'glTF',2,len(raw)):raise AssertionError('GLB header differs')
    size,kind=struct.unpack_from('<II',raw,12)
    if kind!=0x4e4f534a:raise AssertionError('GLB JSON absent')
    doc=json.loads(raw[20:20+size]);offset=20+size
    binsize,kind=struct.unpack_from('<II',raw,offset)
    if kind!=0x004e4942 or offset+8+binsize!=len(raw):raise AssertionError('GLB binary differs')
    binary=raw[offset+8:]
    def decode(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        return np.frombuffer(binary,dtype={5126:'<f4',5125:'<u4'}[a['componentType']],count=a['count']*width,
            offset=v.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,width)
    return doc,decode


class ContinuousManagedLawn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(OUTPUT/'lawn-natural-plan.json');cls.manifest=read(OUTPUT/'lawn-natural-manifest.json')
        cls.library=read(OUTPUT/'geometry-manifest.json');cls.records=read(OUTPUT/'lawn-natural-prototypes.json')
        cls.lookup={m['id']:m for m in cls.library['meshes']}
        cls.doc,cls.decode=decode_glb(OUTPUT/'lawn-natural.glb')
        cls.actual=[];cls.envelopes={}
        for node in cls.doc['nodes']:
            p=cls.doc['meshes'][node['mesh']]['primitives'][0];attrs=p['attributes']
            native=cls.decode(attrs['POSITION'])[:,[0,2,1]]*100
            tris=cls.decode(p['indices']).reshape(-1,3)[:,[0,2,1]]
            cls.actual.append({'nodeName':node['name'],'positionsCm':native.tolist(),'triangles':tris.tolist()})
            mid=node['name'].rsplit('_LOD',1)[0]
            cls.envelopes[mid]=max(cls.envelopes.get(mid,0),float(np.linalg.norm(native[:,:2],axis=1).max()))
        cls.scene,cls.faces,cls.grass,cls.forbidden,cls.source,cls.domain,cls.exclusions,cls.extra,cls.keep=cover.managed_source(GEOMETRY,RURAL,ORIGINAL)

    def test_pins_exact_source_managed_geometry_and_no_unmanaged_mutation(self):
        p=self.plan
        self.assertEqual(p['owner'],'scripts/unreal/exterior-lawn-coverage.py')
        for path,digest in p['inputFiles'].items():self.assertEqual(cover.sha(path),digest,path)
        for key in ('plan','glb','geometryManifest','materialManifest','geometryProof','coverageReceipt'):
            row=self.manifest[key];self.assertEqual(cover.sha(row['path']),row['sha256'],key)
        self.assertEqual(p['coverageReceipt'],self.library['coverageReceipt'])
        self.assertEqual(p['coverageReceipt'],self.manifest['coverageReceipt'])
        self.assertEqual(p['sourceSceneSha256'],cover.sha(GEOMETRY/'scene.json'))
        self.assertEqual(p['sourceObjSha256'],cover.sha(GEOMETRY/'dom-mm.obj'))
        self.assertEqual(p['activeDesign'],{'variant':'C','heatingLayout':'B','livingLayout':'B'})
        self.assertEqual(p['housePlacement'],self.scene['house']['placement'])
        self.assertEqual(p['housePlacement']['streetSetbackMm'],3000);self.assertEqual(p['housePlacement']['eastSetbackMm'],3000)
        self.assertEqual(p['exclusions'],json.loads(json.dumps(self.exclusions)))
        self.assertEqual(p['managedLawnKeepPolygonsCm'],read(RURAL)['managedLawnKeepPolygonsCm'])
        self.assertEqual(p['sourceLawnDomainSourceMm'],read(ORIGINAL)['lawnDomainSourceMm'])
        self.assertTrue(shapely.equals_exact(cover.native_shape(shapely.from_geojson(p['lawnDomainSourceMm'])),self.domain,1e-7))
        self.assertAlmostEqual(self.domain.area/10000,143.598800884,places=7)
        self.assertEqual(p['replacementPolicy'],read(PRIOR/'lawn-natural-plan.json')['replacementPolicy'])
        self.assertTrue(p['replacementPolicy']['unmanagedRuralGroundcoverPreserved'])

    def test_actual_glb_has_individual_curved_mown_leaves_and_same_population_all_lods(self):
        by_name={r['nodeName']:r for r in self.actual}
        self.assertEqual(len(by_name),60);self.assertEqual(len(self.library['meshes']),20)
        for record in self.records:
            actual=by_name[record['nodeName']];p=np.asarray(actual['positionsCm'])
            np.testing.assert_allclose(p,record['positionsCm'],atol=.000003,rtol=0)
            np.testing.assert_array_equal(actual['triangles'],record['triangles'])
            self.assertLess(float(p[:,2].max()),4.6);self.assertGreater(float(p[:,2].max()),2.9)
            self.assertEqual(len(record['bladeRanges']),36)
            self.assertEqual(sum(b['low'] for b in record['bladeRanges']),24)
            for b in record['bladeRanges']:
                self.assertGreaterEqual(b['segments'],2)
                center=np.asarray(b['centerlineCm']);t=np.linspace(0,1,len(center))[:,None]
                self.assertGreater(float(np.linalg.norm(center-(center[0]+t*(center[-1]-center[0])),axis=1).max()),.06)
                self.assertGreaterEqual(b['widthCm'],.20);self.assertLessEqual(b['widthCm'],.49)
            faces=p[np.asarray(actual['triangles'])]
            self.assertGreater(float(np.linalg.norm(np.cross(faces[:,1]-faces[:,0],faces[:,2]-faces[:,0]),axis=1).min()),1e-8)
        for mesh in self.library['meshes']:
            self.assertEqual(mesh['placementPolicy'],'explicit-only');self.assertEqual(mesh['materialKeys'],['lawn_natural_blade'])
            self.assertEqual(mesh['lodScreenSizes'],[1,.025,.007])
            self.assertEqual([l['triangles']for l in mesh['lods']],[336,288,144])
            variants=[next(r for r in self.records if r['nodeName']==mesh['id']+'_LOD'+str(lod)) for lod in range(3)]
            root_sets=[[b['rootCm'] for b in r['bladeRanges']] for r in variants]
            self.assertEqual(root_sets[0],root_sets[1]);self.assertEqual(root_sets[1],root_sets[2])

    def test_every_actual_all_lod_crown_fits_source_and_actual_rural_keep_plus_one_mm(self):
        rows=self.plan['lawnPlacements'];self.assertTrue(38000<len(rows)<58000)
        self.assertEqual(rows,[{'meshId':g['meshId'],**r}for g in self.plan['groups']for r in g['instances']])
        xy=np.array([r['positionCm'][:2] for r in rows]);points=shapely.points(xy)
        self.assertTrue(shapely.contains_xy(self.domain,*xy.T).all())
        distance=shapely.distance(points,self.domain.boundary)
        radius=np.array([self.envelopes[r['meshId']]*r['scale'][0] for r in rows])
        margin=(distance-radius)*10-1
        self.assertGreater(float(margin.min()),0)
        self.assertAlmostEqual(float(margin.min()),self.plan['audit']['minimumAdditionalCrownClearanceMm'],places=4)
        for i,row in enumerate(rows):
            self.assertEqual(row['positionCm'][2],-6.5);self.assertEqual(row['scale'],[row['scale'][0]]*3)
            self.assertTrue(.89<row['scale'][0]<1.06)
            self.assertAlmostEqual(row['radiusCm'],radius[i],places=5)
        budget=sum(len(g['instances'])*self.lookup[g['meshId']]['lods'][0]['triangles'] for g in self.plan['groups'])
        self.assertEqual(budget,self.plan['audit']['nearTriangleBudget']);self.assertLessEqual(budget,20000000)
        self.assertAlmostEqual(len(rows)/(self.domain.area/10000),self.plan['audit']['densityPatchesPerM2'])
        self.assertAlmostEqual(len(rows)*36/(self.domain.area/10000),self.plan['audit']['bladesPerM2EveryLod'])
        self.assertEqual(self.plan['renderingPolicy'],read(PRIOR/'lawn-natural-plan.json')['renderingPolicy'])

    def test_decoded_glb_projected_cover_and_local_no_bare_island_receipt(self):
        receipt=read(OUTPUT/'lawn-coverage-receipt.json')
        for window in receipt['windows']:
            actual,_=cover.raster_coverage(self.actual,self.plan['lawnPlacements'],window['centerCm'])
            for got,expected,before in zip(actual['lods'],window['lods'],window['rejectedR6aStudy']):
                self.assertAlmostEqual(got['projectedCoverage'],expected['projectedCoverage'],delta=.0001)
                self.assertGreater(got['projectedCoverage'],.70)
                self.assertGreater(got['tenCmBinCoverageP10'],.55)
                self.assertEqual(got['bareTenCmBins'],0)
                self.assertGreater(got['projectedCoverage'],before['projectedCoverage']*1.65)
            self.assertGreater(actual['lods'][2]['projectedCoverage'],actual['lods'][0]['projectedCoverage']*.94)

    def test_stochastic_population_does_not_recreate_grid_or_stamped_edge_line(self):
        rows=self.plan['lawnPlacements'];xy=np.array([r['positionCm'][:2]for r in rows])*10
        phase=np.abs(np.exp(2j*np.pi*xy/60).mean(axis=0));self.assertLess(float(phase.max()),.025)
        interior=[r for r in rows if not r['edge']];self.assertGreater(len(interior),len(rows)*.85)
        scales=np.array([r['scale'][0]for r in rows]);self.assertLess(float(scales.std()),.025)
        self.assertGreater(float(scales.std()),.01)
        edge=[r['clearanceMm']for r in rows if r['edge']]
        self.assertGreater(float(np.std(edge)),20)
        self.assertIn('no density thinning',self.plan['audit']['placementMethod'])
        self.assertIn('no independent border row',self.plan['audit']['boundaryPlacement'])

    def test_rejects_unsafe_source_frame_changed_keep_and_immutable_overwrite(self):
        with self.assertRaisesRegex(ValueError,'immutable'):cover.build(GEOMETRY,RURAL,ORIGINAL,PRIOR,OUTPUT)
        rural=read(RURAL)
        for mutate in [lambda p:p['metadata']['activeDesign'].update(variant='A'),
                       lambda p:p['metadata']['housePlacement'].update(eastSetbackMm=2999),
                       lambda p:p['metadata'].update(sourceObjSha256='0'*64),
                       lambda p:p.update(managedLawnKeepPolygonsCm=[[[0,0],[1,0],[1,1],[0,1]]])]:
            with tempfile.TemporaryDirectory(dir=ROOT/'output/unreal',prefix='continuous-lawn-rejection-')as temporary:
                folder=Path(temporary);p=deepcopy(rural);mutate(p);path=folder/'rural-context-geometry.json'
                path.write_text(json.dumps(p));(folder/'scene.json').symlink_to(RURAL.parent/'scene.json')
                (folder/'dom-mm.obj').symlink_to(RURAL.parent/'dom-mm.obj')
                with self.assertRaisesRegex(ValueError,'differs'):cover.managed_source(GEOMETRY,path,ORIGINAL)


if __name__=='__main__':unittest.main()
