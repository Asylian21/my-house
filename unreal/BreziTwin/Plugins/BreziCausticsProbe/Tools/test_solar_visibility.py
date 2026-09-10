"""Synthetic CPU tests only. They do not claim an executed GPU or camera capture."""
import json
import hashlib
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import uuid

import solar_visibility_cases as generator
import validate_solar_visibility as validator


class SolarTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='brezi-solar-synthetic-')
        self.root=Path(self.temp.name)
        self.fixture=validator.checked_fixture(validator.BASE.parent/'Resources/solar-visibility-cases.json')

    def tearDown(self):self.temp.cleanup()

    def save_json(self,path,value):path.write_text(json.dumps(value,indent=2)+'\n')

    def capture(self,name='a',camera=(0,0,100)):
        directory=self.root/name;directory.mkdir()
        cases=self.fixture
        (directory/'solar-visibility-cases.json').write_bytes((validator.BASE.parent/'Resources/solar-visibility-cases.json').read_bytes())
        meta={'status':'GPU-readback-awaiting-opaque-source-validation','syntheticCPUFixture':True,
              'captureId':str(uuid.uuid4()),'casesSha256':validator.CASES_SHA256,'shaderSha256':validator.SHADER_SHA256,
              'sceneSha256':cases['sceneSha256'],'sourceObjSha256':cases['sourceObjSha256'],
              'caseCount':6,'resultStrideBytes':48,'productionLightingBound':False,'sunVisibilityImplemented':False,
              'opaqueForced':True,'proceduralGeometrySkipped':True,'instanceMask':4,'nativeIdsAreCanonicalSourceIds':False,
              'pairedViewUniformBindingValid':True,'pairedViewUniformSource':'current-PostTLAS-FSceneView.ViewUniformBuffer','pairedViewUniformBindingMode':'explicit-shader-binding','pairedViewUniformFrameNumber':60,'gameSnapshotSceneIdentityMatched':True,'gameSnapshotFrameCounter':100,'viewFamilyFrameCounter':100,'gameSnapshotFrameNumber':60,'cvarSnapshotThread':'game-thread-matched-frame-and-family','nativeSunAffectsWorldVisible':True,'eligiblePostTLASCallbacks':60,'runtimeRayTracingEnabled':True,'sameFramePostTLAS':True,'mainViewOnly':True,'runtimeHWRTSupported':True,'runtimeInlineSupported':True,
              'rhi':'Synthetic CPU Metal fixture','cameraOriginCm':list(camera),'preViewTranslationCm':[-v for v in camera],
              'solarTravelDirection':cases['solarTravelDirection'],'nativeDirectionalLux':80000,'frameNumber':60,
              'rendererPid':12345,'capturedCvars':{
                  'r.RayTracing.Culling':3,'r.RayTracing.Culling.PerInstance':1,'r.RayTracing.Culling.Radius':30000,
                  'r.RayTracing.Culling.Angle':1,'r.RayTracing.Nanite.Mode':0,
                  'r.RayTracing.Geometry.NaniteProxies':1,'r.Lumen.HardwareRayTracing':1}}
        self.save_json(directory/'capture.json',meta)
        records=[]
        for i,c in enumerate(cases['cases']):
            hit=c['expected']=='blocked';distance=c['expectedHitDistanceCm'] if hit else -1
            point=[a+b*distance for a,b in zip(c['originCm'],c['directionTowardSun'])] if hit else c['originCm']
            native=[20+i,30+i,40+i,0] if hit else [0xffffffff]*4
            records.append([*point,distance,*native,int(hit),i,4,1])
        (directory/'solar-results-le.bin').write_bytes(b''.join(struct.pack('<4f8I',*row) for row in records))
        log=directory/'engine.log';log.write_text('SYNTHETIC CPU TEST\nBREZI_SOLAR_VISIBILITY_CAPTURE '+str(directory/meta['captureId'])+'\nLogExit: Exiting.\n')
        process={'syntheticCPUFixture':True,'rendererPid':12345,'rendererProcessExitObserved':True,'returnCode':0,
                 'signal':None,'timedOut':False,'renderersRemainingAtVerification':[],
                 'inputsChangedDuringRun':[],'inputSha256':validator.source_pins()}
        self.save_json(directory/'process.json',process)
        return directory

    def validate(self,directory):
        return validator.validate(directory,directory/'engine.log',directory/'process.json',allow_synthetic=True)

    def mutate_json(self,directory,name,mutate):
        p=directory/name;value=json.loads(p.read_text());mutate(value);self.save_json(p,value)

    def mutate_row(self,directory,index,mutate):
        p=directory/'solar-results-le.bin';rows=[list(r) for r in struct.iter_unpack('<4f8I',p.read_bytes())]
        mutate(rows[index]);p.write_bytes(b''.join(struct.pack('<4f8I',*r) for r in rows))

    def rejected(self,directory):
        with self.assertRaises((ValueError,KeyError)):self.validate(directory)
        self.assertEqual(json.loads((directory/'solar-validation.json').read_text())['status'],'validation-failed')

    def test_positive_is_explicitly_synthetic(self):
        result=self.validate(self.capture());self.assertEqual(result['status'],'synthetic-solar-fixture-passed')
        self.assertFalse(result['sunVisibilityImplemented']);self.assertEqual(len(result['cases']),6)

    def test_synthetic_cannot_enter_native_path(self):
        d=self.capture()
        with self.assertRaisesRegex(ValueError,'Synthetic'):validator.validate(d,d/'engine.log',d/'process.json')

    def test_source_cases_exact_pin(self):
        d=self.capture();self.mutate_json(d,'solar-visibility-cases.json',lambda x:x.update(nativeHitDistanceToleranceCm=100));self.rejected(d)

    def test_core_transport_body_unchanged(self):
        p=validator.BASE.parent/'Source/BreziCausticsProbe/Private/BreziCausticsProbe.cpp'
        text=p.read_text().removeprefix('#include "BreziSolarVisibilityProbe.h"\n')
        self.assertEqual(hashlib.sha256(text.split('class FBreziCausticsProbeModule')[0].encode()).hexdigest(),
                         '1282ea848ee21e1f8f0dff2c674af2215d0a4f365127d00b89270a41b2ba02f5')

    def test_inactive_or_hidden_sun_rejected(self):
        for key,value in [('nativeSunAffectsWorldVisible',False),('nativeDirectionalLux',0),('runtimeRayTracingEnabled',False),('eligiblePostTLASCallbacks',59)]:
            with self.subTest(key=key):
                d=self.capture(key);self.mutate_json(d,'capture.json',lambda x:x.update({key:value}));self.rejected(d)

    def test_software_lumen_not_silently_accepted(self):
        d=self.capture();self.mutate_json(d,'capture.json',lambda x:x['capturedCvars'].update({'r.Lumen.HardwareRayTracing':0}));self.rejected(d)

    def test_production_claim_rejected(self):
        d=self.capture();self.mutate_json(d,'capture.json',lambda x:x.update(sunVisibilityImplemented=True));self.rejected(d)

    def test_foreign_shader_pin(self):
        d=self.capture();self.mutate_json(d,'capture.json',lambda x:x.update(shaderSha256='0'*64));self.rejected(d)

    def test_stale_game_snapshot_rejected(self):
        d=self.capture();self.mutate_json(d,'capture.json',lambda x:x.update(gameSnapshotFrameCounter=99));self.rejected(d)

    def test_foreign_game_scene_snapshot_rejected(self):
        d=self.capture();self.mutate_json(d,'capture.json',lambda x:x.update(gameSnapshotSceneIdentityMatched=False));self.rejected(d)

    def test_missing_native_view_uniform_rejected(self):
        d=self.capture();self.mutate_json(d,'capture.json',lambda x:x.pop('pairedViewUniformBindingValid'));self.rejected(d)

    def test_foreign_or_nonshader_view_uniform_rejected(self):
        for field,value in [('pairedViewUniformBindingValid',False),('pairedViewUniformSource','other-view'),('pairedViewUniformBindingMode','static-only'),('pairedViewUniformFrameNumber',59)]:
            with self.subTest(field=field):
                d=self.capture(field);self.mutate_json(d,'capture.json',lambda x:x.update({field:value}));self.rejected(d)

    def test_wrong_scene(self):
        d=self.capture();self.mutate_json(d,'capture.json',lambda x:x.update(sceneSha256='0'*64));self.rejected(d)

    def test_wrong_case_order(self):
        d=self.capture();self.mutate_row(d,0,lambda x:x.__setitem__(9,3));self.rejected(d)

    def test_opaque_becomes_clear(self):
        d=self.capture();self.mutate_row(d,0,lambda x:x.__setitem__(8,0));self.rejected(d)

    def test_clear_becomes_opaque(self):
        d=self.capture();self.mutate_row(d,3,lambda x:x.__setitem__(8,1));self.rejected(d)

    def test_wrong_shadow_mask(self):
        d=self.capture();self.mutate_row(d,0,lambda x:x.__setitem__(10,8));self.rejected(d)

    def test_incomplete_traversal(self):
        d=self.capture();self.mutate_row(d,0,lambda x:x.__setitem__(11,0));self.rejected(d)

    def test_outside_distance_tolerance(self):
        d=self.capture();self.mutate_row(d,0,lambda x:x.__setitem__(3,x[3]+.051));self.rejected(d)

    def test_outside_hit_position_tolerance(self):
        d=self.capture();self.mutate_row(d,0,lambda x:x.__setitem__(0,x[0]+.051));self.rejected(d)

    def test_nan(self):
        d=self.capture();self.mutate_row(d,0,lambda x:x.__setitem__(0,float('nan')));self.rejected(d)

    def test_truncated_buffer(self):
        d=self.capture();p=d/'solar-results-le.bin';p.write_bytes(p.read_bytes()[:-1]);self.rejected(d)

    def test_launcher_pid_is_not_renderer_exit_proof(self):
        d=self.capture();self.mutate_json(d,'process.json',lambda x:x.update(rendererPid=999));self.rejected(d)

    def test_process_failure(self):
        for field,value in [('rendererProcessExitObserved',False),('returnCode',1),('signal','SIGSEGV'),('timedOut',True),('renderersRemainingAtVerification',[12345])]:
            with self.subTest(field=field):
                d=self.capture(field);self.mutate_json(d,'process.json',lambda x:x.update({field:value}));self.rejected(d)

    def test_shader_and_ensure_errors(self):
        for i,entry in enumerate(['LogShaderCompilers: Error: failed','Ensure condition failed: Foo','Fatal: bad','BREZI_SOLAR_VISIBILITY_INCOMPLETE']):
            with self.subTest(entry=entry):
                d=self.capture(str(i));p=d/'engine.log';p.write_text(p.read_text()+entry+'\n');self.rejected(d)

    def test_missing_completion_marker(self):
        d=self.capture();(d/'engine.log').write_text('LogExit: Exiting.\n');self.rejected(d)

    def test_source_changed_during_run(self):
        d=self.capture();self.mutate_json(d,'process.json',lambda x:x.update(inputsChangedDuringRun=['source.cpp']));self.rejected(d)

    def test_process_source_pin_missing(self):
        d=self.capture();self.mutate_json(d,'process.json',lambda x:x['inputSha256'].pop('Source/BreziCausticsProbe/Private/BreziSolarVisibilityProbe.cpp'));self.rejected(d)

    def test_stale_success_invalidated(self):
        d=self.capture();self.validate(d);self.mutate_row(d,0,lambda x:x.__setitem__(8,0));self.rejected(d)

    def test_generator_failure_invalidates_old_cases(self):
        p=self.root/'cases.json';p.write_text('{"status":"old-success"}')
        with patch.object(generator,'derive',side_effect=ValueError('source changed')):
            with self.assertRaises(ValueError):generator.generate(self.root,p)
        self.assertEqual(json.loads(p.read_text())['status'],'solar-source-derivation-failed')

    def pair(self):
        a=self.capture('a');b=self.capture('b',(1000,500,100));self.validate(a);self.validate(b);return a,b

    def test_two_camera_synthetic_positive(self):
        result=validator.compare(*self.pair(),self.root/'compare.json',allow_synthetic=True)
        self.assertEqual(result['status'],'synthetic-camera-invariance-fixture-passed');self.assertFalse(result['sunVisibilityImplemented'])

    def test_same_camera_fails(self):
        a=self.capture('a');b=self.capture('b');self.validate(a);self.validate(b)
        with self.assertRaisesRegex(ValueError,'sufficiently distinct'):validator.compare(a,b,self.root/'compare.json',allow_synthetic=True)

    def test_changed_settings_fails(self):
        a=self.capture('a');b=self.capture('b',(1000,0,0));self.mutate_json(b,'capture.json',lambda x:x['capturedCvars'].update({'r.RayTracing.Culling':0}));self.validate(a);self.validate(b)
        with self.assertRaisesRegex(ValueError,'settings changed'):validator.compare(a,b,self.root/'compare.json',allow_synthetic=True)

    def test_changed_capture_after_receipt_fails(self):
        a,b=self.pair();self.mutate_row(b,0,lambda x:x.__setitem__(3,x[3]+.001))
        with self.assertRaisesRegex(ValueError,'bytes changed'):validator.compare(a,b,self.root/'compare.json',allow_synthetic=True)

    def test_camera_invariance_is_stricter_than_individual_source_tolerance(self):
        a=self.capture('a');b=self.capture('b',(1000,0,0));self.mutate_row(b,0,lambda x:x.__setitem__(3,x[3]+.03));self.validate(a);self.validate(b)
        with self.assertRaisesRegex(ValueError,'changes with camera'):validator.compare(a,b,self.root/'compare.json',allow_synthetic=True)


if __name__=='__main__':unittest.main()
