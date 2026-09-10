"""Independent CPU validation of bounded opaque TLAS controls and two-camera invariance.

validate <capture-dir> --runtime-log <log> --process-receipt <json>
compare <capture-dir-a> <capture-dir-b> --output <new-report.json>
No engine calls. Native acceptance requires the actual renderer PID and clean exit evidence.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import struct

BASE=Path(__file__).resolve().parent
CASES_SHA256='8ac28c7cf18d0b24ea634798e5f82151fef2ac54eb4c8a5f3fab34265a3b2e59'
SHADER_SHA256='d7647fe7779609b31f5908e774adf7485a0e9cc45272267bcad54a788e5674a6'


def require(value,message):
    if not value:raise ValueError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+'.tmp');temp.write_text(json.dumps(value,indent=2)+'\n');temp.replace(path)


def source_pins():
    plugin=BASE.parent
    files=['Source/BreziCausticsProbe/BreziCausticsProbe.Build.cs',
           'Source/BreziCausticsProbe/Private/BreziCausticsProbe.cpp',
           'Source/BreziCausticsProbe/Private/BreziSolarVisibilityProbe.h',
           'Resources/solar-visibility-cases.json','Shaders/Private/BreziSolarVisibility.usf',
           'Source/BreziCausticsProbe/Private/BreziSolarVisibilityProbe.cpp',
           'Source/BreziCausticsProbe/Private/BreziSolarVisibilityContract.h']
    return {name:sha(plugin/name) for name in files}


def checked_fixture(path):
    require(sha(path)==CASES_SHA256,'Unreviewed solar fixture bytes')
    c=json.loads(Path(path).read_text())
    require(c['coordinateSystem']=='unreal-axes-centimetres','Solar source axes changed')
    require(c['productionLightingBound'] is False and c['sunVisibilityImplemented'] is False,'Unsupported optical visibility claim')
    require(len(c['cases'])==6 and len({x['id'] for x in c['cases']})==6,'Case count or uniqueness changed')
    require(sum(x['expected']=='blocked' for x in c['cases'])==3,'Expected three positive source controls')
    require(sum(x['expected']=='unblocked' for x in c['cases'])==3,'Expected three source aperture controls')
    return c


def _validate(directory,runtime_log,process_receipt,allow_synthetic=False):
    directory,runtime_log,process_receipt=Path(directory),Path(runtime_log),Path(process_receipt)
    cases=checked_fixture(directory/'solar-visibility-cases.json')
    meta=json.loads((directory/'capture.json').read_text());process=json.loads(process_receipt.read_text())
    require(meta.get('syntheticCPUFixture') is not True or allow_synthetic,'Synthetic fixture is not native GPU evidence')
    require(meta['status']=='GPU-readback-awaiting-opaque-source-validation','Solar GPU capture is incomplete')
    require(meta['casesSha256']==CASES_SHA256 and meta['shaderSha256']==SHADER_SHA256,'Compiled shader/fixture pin changed')
    require(meta['sceneSha256']==cases['sceneSha256'] and meta['sourceObjSha256']==cases['sourceObjSha256'],'Foreign runtime scene provenance')
    require(meta['caseCount']==6 and meta['resultStrideBytes']==48,'Native output layout changed')
    require(meta['productionLightingBound'] is False and meta['sunVisibilityImplemented'] is False,'Unexpected production visibility claim')
    require(meta['opaqueForced'] is True and meta['proceduralGeometrySkipped'] is True and meta['instanceMask']==4,'Ray optical scope changed')
    require(meta['nativeIdsAreCanonicalSourceIds'] is False,'Native TLAS indices are not canonical object IDs')
    require(meta['pairedViewUniformBindingValid'] is True and meta['pairedViewUniformSource']=='current-PostTLAS-FSceneView.ViewUniformBuffer'
            and meta['pairedViewUniformBindingMode']=='explicit-shader-binding' and meta['pairedViewUniformFrameNumber']==meta['frameNumber'],
            'Missing or foreign paired View uniform shader binding')
    require(meta['gameSnapshotSceneIdentityMatched'] is True,'Game snapshot scene identity differs from TLAS scene')
    require(meta['gameSnapshotFrameCounter']==meta['viewFamilyFrameCounter'] and meta['gameSnapshotFrameNumber']==meta['frameNumber']
            and meta['cvarSnapshotThread']=='game-thread-matched-frame-and-family','Sun/settings snapshot differs from the actual TLAS frame')
    require(meta['sameFramePostTLAS'] is True and meta['mainViewOnly'] is True,'TLAS frame/view binding unproven')
    require(meta['runtimeRayTracingEnabled'] is True and type(meta['eligiblePostTLASCallbacks']) is int and meta['eligiblePostTLASCallbacks']>=60,'No active warmed-up main-view TLAS proof')
    require(meta['runtimeHWRTSupported'] is True and meta['runtimeInlineSupported'] is True and 'metal' in meta['rhi'].lower(),'Actual Metal inline capability is absent')
    for key in ['cameraOriginCm','preViewTranslationCm','solarTravelDirection']:
        require(len(meta[key])==3 and all(math.isfinite(v) for v in meta[key]),'Nonfinite view/sun data')
    require(math.dist(meta['solarTravelDirection'],cases['solarTravelDirection'])<1e-5,'Runtime sun changed from source fixtures')
    require(meta['nativeSunAffectsWorldVisible'] is True,'Native sun is hidden or does not affect the world')
    require(math.isfinite(meta['nativeDirectionalLux']) and meta['nativeDirectionalLux']>0,'Sun is disabled')
    require(type(meta['frameNumber']) is int and meta['frameNumber']>=0,'Invalid native frame')
    for name in ['r.RayTracing.Culling','r.RayTracing.Culling.PerInstance','r.RayTracing.Culling.Radius',
                 'r.RayTracing.Culling.Angle','r.RayTracing.Nanite.Mode','r.RayTracing.Geometry.NaniteProxies','r.Lumen.HardwareRayTracing']:
        require(name in meta['capturedCvars'] and isinstance(meta['capturedCvars'][name],(int,float)) and math.isfinite(meta['capturedCvars'][name]),'Missing native culling/Nanite settings')
    require(meta['capturedCvars']['r.Lumen.HardwareRayTracing']>0,'Current HWRT Lumen main-view mode was not enabled')
    require(type(meta['rendererPid']) is int and meta['rendererPid']>0 and process['rendererPid']==meta['rendererPid'],
            'Process receipt must track the actual renderer PID, not just its launcher')
    require(process.get('rendererProcessExitObserved') is True and process['returnCode']==0 and process['signal'] is None
            and process['timedOut'] is False and process['renderersRemainingAtVerification']==[], 'Renderer exit is not clean or unverified')
    require(process['inputsChangedDuringRun']==[],'Sources changed during native execution')
    pins=source_pins()
    require(pins['Resources/solar-visibility-cases.json']==CASES_SHA256 and pins['Shaders/Private/BreziSolarVisibility.usf']==SHADER_SHA256,'Current reviewed plugin source pins changed')
    for relative,expected in pins.items():
        matching=[h for path,h in process['inputSha256'].items() if path.endswith('/'+relative) or path==relative]
        require(matching==[expected],'Native process source hashes do not pin '+relative)
    text=runtime_log.read_text(errors='replace')
    failures=[line for line in text.splitlines() if re.search(r'\b(?:Error:|Fatal:)|ensure condition failed|failed to compile|shader compilation failures|BREZI_SOLAR_VISIBILITY_INCOMPLETE',line,re.I)]
    require(not failures,'Native log contains ensure/shader/fatal/incomplete failures')
    require(re.fullmatch(r'[a-fA-F0-9-]{36}',meta['captureId']) is not None,'Invalid native capture identity')
    require(any('BREZI_SOLAR_VISIBILITY_CAPTURE' in line and meta['captureId'] in line for line in text.splitlines()),'Native log has no matching completed capture')
    require('LogExit: Exiting.' in text,'Normal engine exit marker missing')
    raw=(directory/'solar-results-le.bin').read_bytes();require(len(raw)==6*48,'Solar readback buffer length changed')
    rows=[]
    for index,(case,record) in enumerate(zip(cases['cases'],struct.iter_unpack('<4f8I',raw))):
        point=record[:3];distance=record[3];native=record[4:8];status,case_index,mask,complete=record[8:12]
        require(all(math.isfinite(v) for v in record[:4]),'Nonfinite solar hit data')
        require(case_index==index and mask==4 and complete==1 and status in [0,1],'Foreign case identity or incomplete ray traversal')
        require((status==1)==(case['expected']=='blocked'),'Native opaque classification differs from source case '+case['id'])
        error=0
        if status==1:
            require(all(v!=0xffffffff for v in native),'Blocked ray has no native TLAS identity')
            require(case['tMinCm']<=distance<=case['tMaxCm'],'Blocked ray distance outside source bounds')
            error=abs(distance-case['expectedHitDistanceCm'])
            require(error<=cases['nativeHitDistanceToleranceCm'],'Native first-hit distance differs from the exact source face')
            expected=[a+b*case['expectedHitDistanceCm'] for a,b in zip(case['originCm'],case['directionTowardSun'])]
            require(math.dist(point,expected)<=cases['nativeHitDistanceToleranceCm'],'Native hit position differs from exact source ray/face')
        else:
            require(distance==-1 and all(v==0xffffffff for v in native),'Unblocked ray must have miss sentinels')
            require(math.dist(point,case['originCm'])<=cases['nativeHitDistanceToleranceCm'],'Miss record no longer retains source origin')
        rows.append({'caseId':case['id'],'role':case['role'],'blocked':bool(status),'distanceCm':distance,'hitPositionCm':point,
                     'sourceObjectId':case['expectedSourceObjectId'],'sourceFaceIndex':case['expectedSourceFaceIndex'],
                     'nativeInstanceId':native[0],'nativeInstanceIndex':native[1],'nativePrimitiveIndex':native[2],'nativeGeometryIndex':native[3],
                     'sourceDistanceErrorCm':error,'nativeCanonicalIdentityProven':False})
    return {'status':'synthetic-solar-fixture-passed' if meta.get('syntheticCPUFixture') else 'bounded-opaque-source-distance-controls-validated',
            'cameraInvariance':'pending-second-distinct-camera-capture','nativeGPUExecutedByValidator':False,
            'captureMeta':meta,'sourcePins':pins,'cases':rows,'maxHitDistanceErrorCm':max(r['sourceDistanceErrorCm'] for r in rows),
            'hashes':{p.name:sha(p) for p in [directory/'capture.json',directory/'solar-visibility-cases.json',directory/'solar-results-le.bin']},
            'runtimeLog':str(runtime_log.resolve()),'runtimeLogSha256':sha(runtime_log),
            'processReceipt':str(process_receipt.resolve()),'processReceiptSha256':sha(process_receipt),
            'productionLightingBound':False,'sunVisibilityImplemented':False,
            'limitations':cases['limitations']+['Native TLAS IDs are recorded separately; agreement proves finite hit positions/distances, not canonical runtime object identity.']}


def validate(directory,runtime_log,process_receipt,allow_synthetic=False):
    report=Path(directory)/'solar-validation.json';write(report,{'status':'validation-pending','sunVisibilityImplemented':False})
    try:result=_validate(directory,runtime_log,process_receipt,allow_synthetic)
    except Exception as error:
        write(report,{'status':'validation-failed','sunVisibilityImplemented':False,'error':str(error)});raise
    write(report,result);return result


def compare(a,b,output,allow_synthetic=False):
    output=Path(output);write(output,{'status':'camera-invariance-pending','sunVisibilityImplemented':False})
    try:
        results=[]
        for directory in [Path(a),Path(b)]:
            saved=json.loads((directory/'solar-validation.json').read_text())
            require(saved['status'] in ['bounded-opaque-source-distance-controls-validated','synthetic-solar-fixture-passed'],'Individual capture validation did not pass')
            require(sha(saved['runtimeLog'])==saved['runtimeLogSha256'] and sha(saved['processReceipt'])==saved['processReceiptSha256'],'Native runtime evidence changed after validation')
            for name,expected in saved['hashes'].items():require(sha(directory/name)==expected,'Capture bytes changed after validation')
            results.append(_validate(directory,saved['runtimeLog'],saved['processReceipt'],allow_synthetic))
        ra,rb=results;ma,mb=ra['captureMeta'],rb['captureMeta']
        require(ma['captureId']!=mb['captureId'],'Camera comparison requires distinct actual captures')
        source=checked_fixture(Path(a)/'solar-visibility-cases.json')
        camera_distance=math.dist(ma['cameraOriginCm'],mb['cameraOriginCm'])
        require(camera_distance>=source['minimumDistinctCameraDistanceCm'],'Camera positions are not sufficiently distinct')
        require(ma['capturedCvars']==mb['capturedCvars'],'Culling/Nanite/settings changed between cameras')
        require(math.dist(ma['solarTravelDirection'],mb['solarTravelDirection'])<1e-7 and abs(ma['nativeDirectionalLux']-mb['nativeDirectionalLux'])<.01,'Sun changed between cameras')
        deltas=[]
        for x,y in zip(ra['cases'],rb['cases']):
            require(x['caseId']==y['caseId'] and x['blocked']==y['blocked'],'Camera-dependent case identity/classification')
            delta=abs(x['distanceCm']-y['distanceCm'])
            require(delta<=source['cameraInvarianceDistanceToleranceCm'],'Opaque hit distance changes with camera')
            require(math.dist(x['hitPositionCm'],y['hitPositionCm'])<=source['cameraInvarianceDistanceToleranceCm'],'Opaque hit position changes with camera')
            deltas.append(delta)
        synthetic=ma.get('syntheticCPUFixture') or mb.get('syntheticCPUFixture')
        result={'status':'synthetic-camera-invariance-fixture-passed' if synthetic else 'bounded-opaque-controls-camera-invariance-validated',
                'captureDirectories':[str(Path(a).resolve()),str(Path(b).resolve())],
                'captureIds':[ma['captureId'],mb['captureId']],'casesSha256':CASES_SHA256,'caseCount':6,
                'cameraDistanceCm':camera_distance,'maxNativeHitDistanceDifferenceCm':max(deltas),
                'perCaptureInputHashes':[ra['hashes'],rb['hashes']],'perCaptureNativeSourcePins':[ra['sourcePins'],rb['sourcePins']],
                'productionLightingBound':False,'sunVisibilityImplemented':False,'nativeGPUExecutedByComparator':False,
                'limitations':source['limitations']+['Only these six controls and two recorded views; no global camera invariance claim.']}
    except Exception as error:
        write(output,{'status':'camera-invariance-failed','sunVisibilityImplemented':False,'error':str(error)});raise
    write(output,result);return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    v=sub.add_parser('validate');v.add_argument('directory',type=Path);v.add_argument('--runtime-log',required=True,type=Path);v.add_argument('--process-receipt',required=True,type=Path)
    c=sub.add_parser('compare');c.add_argument('a',type=Path);c.add_argument('b',type=Path);c.add_argument('--output',required=True,type=Path)
    args=parser.parse_args()
    result=validate(args.directory,args.runtime_log,args.process_receipt) if args.action=='validate' else compare(args.a,args.b,args.output)
    print(json.dumps(result,indent=2))
