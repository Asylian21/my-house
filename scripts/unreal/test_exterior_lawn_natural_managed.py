"""Managed lawn scope and actual all-LOD crown checks against pinned rural keep."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys
import tempfile
import unittest

import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1];sys.path.insert(0,str(HERE))
spec=importlib.util.spec_from_file_location('managed_lawn',HERE/'exterior-lawn-natural-managed.py')
managed=importlib.util.module_from_spec(spec);spec.loader.exec_module(managed)
from test_exterior_lawn_natural import glb
BASE=ROOT/'output/unreal/exterior-lawn-natural-20260930-r1'
OUTPUT=ROOT/'output/unreal/exterior-lawn-natural-20260930-r2b'
RURAL=ROOT/'output/unreal/exterior-20260930-r5/geometry/rural-context-geometry.json'


class ManagedNaturalLawn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=managed.read(OUTPUT/'lawn-natural-plan.json');cls.old=managed.read(BASE/'lawn-natural-plan.json')
        cls.rural=managed.read(RURAL);cls.library=managed.read(OUTPUT/'geometry-manifest.json')
        cls.keep=unary_union([Polygon(p)for p in cls.rural['managedLawnKeepPolygonsCm']])
        cls.source=managed.source_to_native(shapely.from_geojson(cls.old['lawnDomainSourceMm']))
        cls.domain=cls.source.intersection(cls.keep).buffer(0)
        document,decode=glb(BASE/'lawn-natural.glb');cls.radii={}
        for row in cls.library['meshes']:
            points=[]
            for lod in row['lods']:
                node=next(node for node in document['nodes']if node['name']==lod['nodeName'])
                for part in document['meshes'][node['mesh']]['primitives']:
                    points.extend((decode(part['attributes']['POSITION'])[:,[0,2,1]]*100).astype(float).tolist())
            cls.radii[row['id']]=max(math.hypot(*p[:2])for p in points)

    def test_frozen_sources_and_rural_frame_and_output_pins(self):
        p=self.plan;self.assertEqual(p['owner'],'scripts/unreal/exterior-lawn-natural-managed.py')
        self.assertEqual(p['generatorSha256'],managed.sha(HERE/'exterior-lawn-natural-managed.py'))
        self.assertEqual(p['managedLawnPlan'],{'path':str(RURAL),'sha256':managed.sha(RURAL)})
        self.assertEqual(p['managedLawnKeepPolygonsCm'],self.rural['managedLawnKeepPolygonsCm'])
        self.assertEqual(p['activeDesign'],self.rural['metadata']['activeDesign']);self.assertEqual(p['housePlacement'],self.rural['metadata']['housePlacement'])
        self.assertEqual(p['sourceSceneSha256'],managed.sha(RURAL.parent/'scene.json'))
        self.assertEqual(p['sourceObjSha256'],managed.sha(RURAL.parent/'dom-mm.obj'))
        self.assertEqual(p['derivedFrom'],{'path':str(BASE/'lawn-natural-plan.json'),'sha256':managed.sha(BASE/'lawn-natural-plan.json')})
        for path,expected in p['inputFiles'].items():self.assertEqual(managed.sha(path),expected,path)
        manifest=managed.read(OUTPUT/'lawn-natural-manifest.json')
        for key in('plan','geometryManifest','materialManifest','geometryProof','glb'):
            row=manifest[key];self.assertEqual(managed.sha(row['path']),row['sha256'])

    def test_all_actual_decoded_crowns_fit_source_and_external_keep_union(self):
        rows=self.plan['lawnPlacements'];xy=np.asarray([row['positionCm'][:2]for row in rows])
        self.assertTrue(shapely.contains_xy(self.domain,*xy.T).all())
        distances=shapely.distance(shapely.points(xy),self.domain.boundary)
        radii=np.asarray([self.radii[row['meshId']]*row['scale'][0]for row in rows])
        self.assertGreater(float((distances-radii-.1).min()),0)
        self.assertAlmostEqual(float((distances-radii-.1).min())*10,self.plan['audit']['minimumAdditionalCrownClearanceMm'],places=3)
        np.testing.assert_allclose(distances*10,[row['clearanceMm']for row in rows],atol=.00002,rtol=0)
        np.testing.assert_allclose(radii,[row['radiusCm']for row in rows],atol=.000003,rtol=0)
        self.assertTrue(all(row['scale']==[row['scale'][0]]*3 for row in rows))
        self.assertTrue(all(row['positionCm'][2]==-6.5 for row in rows))
        self.assertAlmostEqual(self.domain.area/10000,143.598800884,places=6)
        decoded=managed.source_to_native(shapely.from_geojson(self.plan['lawnDomainSourceMm']))
        self.assertLess(decoded.symmetric_difference(self.domain).area,1e-8)

    def test_derivative_is_exact_subset_and_does_not_cover_unmanaged_native_layer(self):
        rows=self.plan['lawnPlacements'];expected=[]
        for row in self.old['lawnPlacements']:
            point=shapely.Point(row['positionCm'][:2])
            if self.domain.contains(point)and point.distance(self.domain.boundary)>row['radiusCm']+.1:expected.append(row)
        key=lambda row:(row['meshId'],tuple(row['positionCm']),row['yawDeg'],tuple(row['scale']))
        self.assertEqual([key(row)for row in rows],[key(row)for row in expected])
        roots=np.asarray([row['positionCm'][:2]for row in self.old['lawnPlacements']])
        outside=~shapely.contains_xy(self.keep,*roots.T)
        self.assertEqual(int(outside.sum()),15364)
        self.assertEqual(self.plan['audit']['excludedR1RootsOutsideKeep'],15364)
        unmanaged=self.source.difference(self.keep)
        # Every circle lies in keep, so none of the actual geometry envelopes
        # enters the intentionally unmanaged native vegetation domain.
        newxy=np.asarray([row['positionCm'][:2]for row in rows]);self.assertFalse(shapely.contains_xy(unmanaged,*newxy.T).any())
        native=managed.read(ROOT/'output/unreal/exterior-20260930-r5/exterior-placements.json')
        role_counts={}
        for group in native:
            p=np.asarray([row['positionCm'][:2]for row in group['instances']])
            n=int(shapely.contains_xy(unmanaged,*p.T).sum())
            role_counts[group['role']]=role_counts.get(group['role'],0)+n
        self.assertEqual(role_counts['grass'],4198);self.assertEqual(role_counts['groundcover'],491)
        self.assertTrue(self.plan['replacementPolicy']['unmanagedRuralGroundcoverPreserved'])

    def test_geometry_materials_masks_cameras_and_lod_contract_unchanged(self):
        self.assertEqual(self.library['meshes'],managed.read(BASE/'geometry-manifest.json')['meshes'])
        self.assertEqual(managed.read(OUTPUT/'material-manifest.json'),managed.read(BASE/'material-manifest.json'))
        self.assertEqual(self.plan['exclusions'],self.old['exclusions'])
        self.assertEqual(self.plan['sourceLawnDomainSourceMm'],self.old['lawnDomainSourceMm'])
        self.assertEqual(self.plan['lodScreenSizes'],[1,.025,.007])
        flat=[{'meshId':g['meshId'],**row}for g in self.plan['groups']for row in g['instances']]
        self.assertEqual(flat,self.plan['lawnPlacements'])
        self.assertLess(self.plan['audit']['nearTriangleBudget'],10000000)
        views=managed.read(OUTPUT/'lawn-qa-views.json')
        for view in views['views']:
            for key in('eyeCm','targetCm'):self.assertTrue(self.domain.contains(shapely.Point(view[key][:2])))

    def test_changed_rural_frame_empty_keep_and_output_overwrite_rejected(self):
        for mutation,reason in[(lambda r:r['metadata']['activeDesign'].update(variant='A'),'C/B/B'),
                              (lambda r:r['metadata']['housePlacement'].update(eastSetbackMm=2999),'placement'),
                              (lambda r:r.update(managedLawnKeepPolygonsCm=[]),'keep')]:
            with tempfile.TemporaryDirectory(dir=ROOT/'output/unreal',prefix='managed-lawn-rejection-')as temp:
                temp=Path(temp);rural=copy.deepcopy(self.rural);mutation(rural);path=temp/'rural.json'
                path.write_text(json.dumps(rural));(temp/'scene.json').symlink_to(RURAL.parent/'scene.json');(temp/'dom-mm.obj').symlink_to(RURAL.parent/'dom-mm.obj')
                with self.assertRaisesRegex(ValueError,reason):managed.build(BASE,path,temp/'never-created')
        with self.assertRaisesRegex(ValueError,'immutable'):managed.build(BASE,RURAL,OUTPUT)


if __name__=='__main__':unittest.main()
