"""Protection-only aerial RGB permission: pinned artifact and independent geometry.

Runs in the existing exterior Python environment. No Unreal, input rewriting,
network request or historical output mutation is performed by these tests.
"""
import copy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np
from PIL import Image
import shapely

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('projection_mask',HERE/'exterior-ortho-projection-mask.py')
mask_module=importlib.util.module_from_spec(spec);spec.loader.exec_module(mask_module)
ROOT=mask_module.ROOT
MANIFEST=ROOT/'output/unreal/exterior-ortho-projection-20260930-r2/ortho-projection-manifest.json'


def material_module():
    spec=importlib.util.spec_from_file_location('projection_material_policy',HERE/'exterior-materials.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


class PinnedProjection(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        if not MANIFEST.exists():raise unittest.SkipTest('Generate the isolated projection mask first')
        cls.manifest=mask_module.read(MANIFEST)
        cls.mask=np.asarray(Image.open(cls.manifest['texture']['path']))
        cls.context=mask_module.read(next(p for p in cls.manifest['inputFiles']if p.endswith('/context-plan.json')))
        cls.scene=mask_module.read(next(p for p in cls.manifest['inputFiles']if p.endswith('/scene.json')))
        cls.ortho=mask_module.read(cls.manifest['orthoManifest']['path'])

    def test_pinned_sources_exact_active_frame_and_unedited_provider_pixels(self):
        m=self.manifest
        for path,expected in m['inputFiles'].items():self.assertEqual(mask_module.sha(path),expected,path)
        self.assertEqual(mask_module.sha(m['texture']['path']),m['texture']['sha256'])
        self.assertEqual(m['generatorSha256'],mask_module.sha(ROOT/m['owner']))
        self.assertEqual(m['sourceSceneSha256'],self.context['sourceSceneSha256'])
        self.assertEqual(m['sourceObjSha256'],self.context['sourceObjSha256'])
        self.assertEqual(m['activeDesign'],{'variant':'C','livingLayout':'B','heatingLayout':'B'})
        self.assertEqual(m['housePlacement'],self.scene['housePlacement'])
        self.assertEqual(m['housePlacement']['streetSetbackMm'],3000)
        self.assertEqual(m['housePlacement']['eastSetbackMm'],3000)
        self.assertEqual(m['orthoManifest']['sha256'],mask_module.sha(m['orthoManifest']['path']))
        self.assertFalse(self.ortho['sourcePixelEdits'])
        for layer in self.ortho['layers']:self.assertEqual(mask_module.sha(layer['rgbaPath']),layer['rgbaSha256'])

    def test_lossless_linear_permission_channels_and_whole_ground_extent(self):
        self.assertEqual(self.mask.shape,(1024,1024,4))
        self.assertEqual(self.mask.dtype,np.uint8)
        self.assertFalse(self.manifest['texture']['sRGB'])
        self.assertTrue(self.manifest['texture']['lossless'])
        self.assertTrue((self.mask[:,:,1]==255).all())
        self.assertTrue((self.mask[:,:,2]==0).all())
        self.assertTrue((self.mask[:,:,3]==255).all())
        self.assertEqual(int(self.mask[:,:,0].min()),0)
        self.assertEqual(int(self.mask[:,:,0].max()),255)
        self.assertGreater(int(((self.mask[:,:,0]>0)&(self.mask[:,:,0]<255)).sum()),1000)
        xmin,ymin,xmax,ymax=self.manifest['worldBoundsCm']
        self.assertEqual(self.manifest['worldCmToUvRows'],[[1/(xmax-xmin),0.,-xmin/(xmax-xmin)],
                                                         [0.,-1/(ymax-ymin),ymax/(ymax-ymin)]])
        for mesh in self.context['meshes']:
            if mesh['material']not in self.manifest['allowedMaterialKeys']:continue
            xyz=np.asarray(mesh['verticesCm'])
            self.assertGreaterEqual(xyz[:,0].min(),xmin)
            self.assertLessEqual(xyz[:,0].max(),xmax)
            self.assertGreaterEqual(xyz[:,1].min(),ymin)
            self.assertLessEqual(xyz[:,1].max(),ymax)

    def test_bilinear_permission_zero_on_every_actual_private_source_vertex(self):
        # Independent OBJ face inspection, rather than only manifest statistics
        # or a few polygon representatives. Includes all authored house/garden,
        # fencing, pool, terraces and private entrance geometry.
        groups={'Walls','Windows','Roof','Pool','Fence','Decking','Floors','Foundations','Interior','Landscape'}
        public={'DOM_%05d'%i for i in [0,*range(2,54),*range(2022,2028),2039]}
        selected={row['id']for row in self.scene['objects']if row['id']not in public and
                  (row['group']in groups or row['id']in {'DOM_%05d'%i for i in range(54,60)})}
        obj_path=next(p for p in self.manifest['inputFiles']if p.endswith('/dom-mm.obj'))
        vertices=[];used=set();current=None
        with Path(obj_path).open()as stream:
            for line in stream:
                parts=line.split()
                if not parts:continue
                if parts[0]=='v':vertices.append([float(parts[1])/10,-float(parts[2])/10])
                elif parts[0]=='o':current=parts[1]
                elif parts[0]=='f'and current in selected:used.update(int(p.split('/')[0])-1 for p in parts[1:])
        points=np.asarray([vertices[i]for i in sorted(used)])
        sampled,inside=mask_module.sample(self.mask[:,:,0]/255.,points,self.manifest['worldCmToUvRows'])
        self.assertEqual(len(points),271788)
        self.assertTrue(inside.all())
        self.assertEqual(float(sampled.max()),0.)
        self.assertEqual(int((sampled>1e-9).sum()),0)

    def test_ordinary_ground_continuity_including_dark_image_and_road_positions(self):
        m=self.manifest
        converter=mask_module.source_module('exterior-context.py','test_projection_subject_frame')
        subject=mask_module.unary_union([mask_module.Polygon([converter.to_unreal(p,self.scene)for p in rings[0]],
                     [[converter.to_unreal(p,self.scene)for p in hole]for hole in rings[1:]])
                     for row in self.context['parcels']if row['parcelNumber']=='6012/26'for rings in row['polygonsSjtskMm']])
        private,_=mask_module.full_authored_site(subject,self.scene,Path(next(p for p in m['inputFiles']if p.endswith('/dom-mm.obj'))))
        buildings=mask_module.read(next(p for p in m['inputFiles']if p.endswith('/building-plan.json')))
        building_shape=mask_module.unary_union([mask_module.Polygon(rings[0],rings[1:])
                          for row in buildings['buildings']for rings in row['polygonsCm']])
        blocked=mask_module.unary_union([private,building_shape.buffer(150.)])
        safety=m['policy']['rasterBilinearGuardCm']+m['policy']['geometricFeatherCm']+np.sqrt(2)*100000/1024
        tested=0;road_tested=0
        for mesh in self.context['meshes']:
            if mesh['material']not in m['allowedMaterialKeys']:continue
            tri=np.asarray(mesh['verticesCm'])[np.asarray(mesh['indices']).reshape(-1,3)]
            centres=tri[:,:,:2].mean(axis=1)
            outside=shapely.distance(blocked,shapely.points(centres))>safety
            permission,inside=mask_module.sample(self.mask[:,:,0]/255.,centres,m['worldCmToUvRows'])
            self.assertTrue(inside.all())
            self.assertTrue((permission[outside]>=1-1e-9).all(),mesh['id'])
            tested+=int(outside.sum())
            if mesh['material']=='context_track':road_tested+=int(outside.sum())
        self.assertEqual(tested,65833)
        self.assertGreater(road_tested,500)
        witnesses=np.asarray([row['worldCm']for row in m['darkSourceWitnesses']])
        permission,inside=mask_module.sample(self.mask[:,:,0]/255.,witnesses,m['worldCmToUvRows'])
        self.assertTrue(inside.all())
        self.assertTrue((permission>=1-1e-9).all())
        self.assertGreater(m['summary']['darkOrdinaryContextPixelsPermitted'],6000)
        self.assertTrue(all(row['sourceLinearLuminance']<.045 for row in m['darkSourceWitnesses']))

    def test_mask_intent_has_no_field_or_darkness_gate_and_optional_extent_is_guarded(self):
        for name in ('protectionOnly','noDarkPixelExclusion','noFieldBoundaryExclusion','noCanopyExclusion','noRoadExclusion','providerCoverageSeparate'):
            self.assertTrue(self.manifest['policy'][name])
        self.assertEqual(set(self.manifest['allowedMaterialKeys']),set(mask_module.KEYS))
        value,inside=mask_module.sample(self.mask[:,:,0]/255.,[[60000,0]],self.manifest['worldCmToUvRows'])
        self.assertFalse(bool(inside[0]))
        # Clamp sampling alone is insufficient: the explicit bounds guard is
        # required even when a clamped permission sample happens to be white.
        self.assertEqual(float(value[0]*inside[0]),0.)

    def test_material_validator_rejects_frame_mismatch_and_unsafe_optional_mask(self):
        materials=material_module()
        self.assertTrue(hasattr(materials,'prepare_projection'),'Projection validator must be available')
        ortho=materials.prepare_orthophoto(self.manifest['orthoManifest']['path'])
        valid=materials.prepare_projection(MANIFEST,ortho)
        self.assertEqual(valid['manifestSha256'],mask_module.sha(MANIFEST))
        for defect in ('sourceFrame','wrongBounds','darknessGate','unsafeGreen','unsafeRed'):
            with self.subTest(defect=defect),tempfile.TemporaryDirectory(dir=ROOT/'output/unreal')as temp:
                candidate=copy.deepcopy(self.manifest)
                if defect=='sourceFrame':candidate['sourceSceneSha256']='0'*64
                elif defect=='wrongBounds':candidate['worldBoundsCm'][0]-=100
                elif defect=='darknessGate':candidate['policy']['noDarkPixelExclusion']=False
                else:
                    rgba=self.mask.copy()
                    if defect=='unsafeGreen':rgba[:,:,1]=0
                    else:rgba[:,:,0]=255
                    image_path=Path(temp)/'unsafe.png';Image.fromarray(rgba).save(image_path)
                    candidate['texture']['path']=str(image_path);candidate['texture']['sha256']=mask_module.sha(image_path)
                path=Path(temp)/'candidate.json';path.write_text(json.dumps(candidate))
                expected={'sourceFrame':'architectural frame','wrongBounds':'affine frame',
                          'darknessGate':'protection-only policy','unsafeGreen':'(channel|coverage|pixel)',
                          'unsafeRed':'(channel|protection|pixel)'}[defect]
                with self.assertRaisesRegex(RuntimeError,expected):materials.prepare_projection(path,ortho)


if __name__=='__main__':unittest.main()
