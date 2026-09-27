"""Independent R6 geometry, source preservation and exact garden-domain checks."""
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import struct
import unittest

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(os.environ.get('BREZI_GARDEN_MORPHOLOGY',ROOT/'output/unreal/exterior-garden-morphology-20260927-r6b'))


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def positions(doc,raw,index):
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
    start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',12)
    return [struct.unpack_from('<3f',raw,start+i*stride) for i in range(a['count'])]


class GardenMorphology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geometry=json.loads((OUT/'geometry-manifest.json').read_text())
        cls.plan=json.loads((OUT/'garden-plan.json').read_text())
        cls.old=json.loads((ROOT/'output/unreal/exterior-garden-20260926-r4/garden-plan.json').read_text())
        cls.morph=json.loads((OUT/'morphology-audit.json').read_text())
        cls.validation=json.loads((OUT/'geometry-validation.json').read_text())
        cls.material=json.loads((ROOT/'output/unreal/exterior-assets-20260926-r5/material-manifest.json').read_text())['ph_periwinkle_plant']
        data=(OUT/'glb/garden_pink_r6.glb').read_bytes();length=struct.unpack_from('<I',data,12)[0]
        cls.doc=json.loads(data[20:20+length]);cls.raw=data[28+length:]

    def test_complete_frozen_input_chain(self):
        for manifest in [self.geometry,self.plan]:
            for path,pin in manifest['inputFiles'].items():self.assertEqual(digest(path),pin,path)
        for row in self.geometry['meshes']:self.assertEqual(digest(row['glbPath']),row['glbSha256'])
        for spec in self.material['maps'].values():self.assertEqual(digest(spec['path']),spec['sha256'])

    def test_two_explicit_only_variants_and_existing_material(self):
        self.assertEqual([r['id']for r in self.geometry['meshes']],['garden_pink_r6_a','garden_pink_r6_b'])
        for row in self.geometry['meshes']:
            self.assertEqual((row['role'],row['form'],row['flowerColor']),('ornamental','flowering','pink'))
            self.assertEqual(row['placementPolicy'],'explicit-only')
            self.assertEqual(row['materialKeys'],['ph_periwinkle_plant'])
            self.assertEqual([l['level']for l in row['lods']],[0,1,2])
            self.assertGreater(row['lods'][0]['triangles'],row['lods'][1]['triangles'])
            self.assertGreater(row['lods'][1]['triangles'],row['lods'][2]['triangles'])
        self.assertEqual(self.material['leafCalibration']['brightness'],.78)
        self.assertEqual(self.morph['newMaterialKeys'],[])
        self.assertFalse(self.morph['texturePixelsChanged'])

    def test_all_roots_yaws_and_ten_other_placements_unchanged(self):
        changed=[]
        for row,old in zip(self.plan['ornamentalPlacements'],self.old['ornamentalPlacements']):
            for key in ['positionCm','yawDeg','sourceIds','sourceBedId','sourcePositionCm','rootDisplacementCm','collision']:
                self.assertEqual(row[key],old[key],(row['id'],key))
            if row!=old:changed.append(row['id'])
        self.assertEqual(changed,['garden_ornamental_1','garden_ornamental_5'])
        self.assertEqual(self.plan['hideSourceIds'],[f'DOM_{i:05}'for i in range(1967,2003)])
        self.assertEqual(self.plan['activeDesign'],{'variant':'C','heatingLayout':'B','livingLayout':'B'})
        self.assertEqual(self.plan['housePlacement'],self.old['housePlacement'])
        self.assertEqual(self.plan['housePlacement']['streetSetbackMm'],3000)
        self.assertEqual(self.plan['housePlacement']['eastSetbackMm'],3000)

    def test_actual_glb_vertices_fit_preserved_crown_envelopes(self):
        for mesh in self.geometry['meshes']:
            row=next(r for r in self.plan['ornamentalPlacements']if r['meshId']==mesh['id'])
            old=next(r for r in self.old['ornamentalPlacements']if r['id']==row['id'])
            self.assertEqual(len(set(row['scale'])),1)
            self.assertLessEqual(row['radiusCm'],old['radiusCm']+1e-7)
            self.assertLessEqual(row['actualHeightCm'],old['actualHeightCm']+1e-7)
            for lod in mesh['lods']:
                node=next(n for n in self.doc['nodes']if n['name']==lod['nodeName'])
                for primitive in self.doc['meshes'][node['mesh']]['primitives']:
                    points=positions(self.doc,self.raw,primitive['attributes']['POSITION'])
                    for x,y,z in points:
                        # glTF Y-up -> native XY = glTF XZ, units m -> cm.
                        self.assertLessEqual(math.hypot(x,z)*100*row['uniformScale'],row['radiusCm']+1e-4)
                        self.assertGreaterEqual(y*100,-1e-4)
                        self.assertLessEqual(y*100*row['uniformScale'],old['actualHeightCm']+1e-4)

    def test_clearance_to_original_beds_steps_hardscape_and_other_crowns(self):
        steps=unary_union([Polygon([p[:2]for p in tri]) for triangles in self.plan['sourceStepTrianglesCm'].values()
                           for tri in triangles if Polygon([p[:2]for p in tri]).area>1e-7])
        scene=json.loads((ROOT/'output/unreal/realism-20260926-r5/geometry/scene.json').read_text())
        hardscape=unary_union([box((r['x0']-15200)/10,-(r['y1']-10800)/10,(r['x1']-15200)/10,-(r['y0']-10800)/10)
                              for item in [*scene['terraces'],scene['poolDeck']]for r in item['rectsMm']]+[
                             Polygon([((p['x']-15200)/10,-(p['y']-10800)/10)for p in scene['pool']['copingFootprintMm']])])
        for row in self.plan['ornamentalPlacements']:
            original=next(r for r in self.old['audit']['individual']if r['id']==row['id'])
            domain=Polygon(original['sourceDomainRingCm']);p=Point(row['positionCm'][:2]);radius=row['radiusCm']
            self.assertTrue(domain.covers(p))
            self.assertGreaterEqual(p.distance(domain.boundary)-radius,(14 if row['sourceBedId']else 0)-1e-6)
            self.assertGreaterEqual(p.distance(steps)-radius,14-1e-6)
            self.assertGreaterEqual(p.distance(hardscape)-radius,14-1e-6)
        for a,b in itertools.combinations(self.plan['ornamentalPlacements'],2):
            distance=math.dist(a['positionCm'][:2],b['positionCm'][:2])
            self.assertGreaterEqual(distance,60)
            self.assertGreaterEqual(distance-a['radiusCm']-b['radiusCm'],2-1e-6)

    def test_original_shoot_topology_uv_and_export_basis_audited(self):
        self.assertEqual(len(self.morph['sourceParts']),138)
        self.assertTrue(all(p['uvUnchanged']and p['sourceTriangles']==p['derivedTriangles']for p in self.morph['sourceParts']))
        self.assertEqual(len(self.validation['nodes']),6)
        for node in self.validation['nodes']:
            self.assertTrue(node['uvSourceRangeExact'])
            self.assertLess(node['maxAbsNormalTangentDot'],.001)
            self.assertLess(node['boundErrorCm'],.001)
            self.assertLess(node['opposedFaces']/node['faces'],.001)


if __name__=='__main__':unittest.main()
