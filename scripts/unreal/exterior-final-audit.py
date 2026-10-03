"""Independent read-only R6a import/package/runtime receipt audit.

Requires completed QA summaries. Writes only a new external JSON receipt, never
updates a selector, source receipt, asset, map, package or native process.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]
DESIGN={'variant':'C','heatingLayout':'B','livingLayout':'B'}
GROUPS=tuple('LawnTuft'+str(i)for i in range(4))
COUNTS=(10118,10153,10147,10019)
_HASHES={}


def require(ok,message):
    if not ok:raise RuntimeError(message)


def resolve(path):return (ROOT/Path(path)).resolve()


def sha(path):
    path=resolve(path)
    if path not in _HASHES:
        h=hashlib.sha256()
        with path.open('rb')as stream:
            while chunk:=stream.read(1024*1024):h.update(chunk)
        _HASHES[path]=h.hexdigest()
    return _HASHES[path]


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def read(path):return json.loads(resolve(path).read_text())


def pin(path,value):
    path=resolve(path)
    require(path.is_file() and sha(path)==value,'Audit input hash differs: '+str(path))
    return path


def pins(mapping):
    require(isinstance(mapping,dict) and mapping,'Audit input map missing')
    for path,value in mapping.items():pin(path,value)
    return len(mapping)


def receipt(path):return {'path':str(resolve(path)),'sha256':sha(path)}


def asset_file(project,asset):
    require(asset.startswith('/Game/') and '.' in asset,'Unexpected native asset path')
    return project/'Content'/(asset.removeprefix('/Game/').split('.',1)[0]+'.uasset')


def png_size(path):
    header=resolve(path).read_bytes()[:24]
    require(header[:8]==b'\x89PNG\r\n\x1a\n' and header[12:16]==b'IHDR','QA image is not a PNG')
    return list(struct.unpack('>II',header[16:24]))


def audit_import(source):
    file=source/'exterior-import-report.json';report=read(file);project=source/'Project/BreziTwin'
    require(report['status']=='exterior-import-validated' and report['owner']=='scripts/unreal/exterior-import.py',
            'Exterior native import is incomplete')
    require(report['activeDesign']==DESIGN and report['setbacksMm']=={'street':3000,'east':3000},'Native design/setback drift')
    for key in ('savedReloaded','protectedContentUnchanged','sourceGeometryCollisionAndTransformsPreserved','originalMaterialAssetsPreserved'):
        require(report[key] is True,'Missing native preservation proof: '+key)
    require(report['protectedActorWitnessSha256']==report['savedProtectedActorWitnessSha256']
            and report['authoredActorWitnessSha256']==report['savedActorWitnessSha256'],'Native saved witness differs')
    counted={key:pins(report[key])for key in ('inputFiles','pipelineFiles')}
    before,after=report['beforeAssetHashes'],report['afterAssetHashes']
    require(before.keys()<=after.keys(),'Original Content file removed')
    allowed={str(project/'Content/Brezi/Maps/Brezi.umap'),str(project/'Content/Data/viewpoints.json')}
    require(all(path in allowed or after[path]==value for path,value in before.items()),'Protected original Content hash changed')
    require({r['path'] for r in report['changedAssets']}<=allowed,'Unapproved original Content mutation')
    counted['afterAssetHashes']=pins(after)
    for path in after.keys()-before.keys():
        p=resolve(path)
        require(p.is_relative_to(project/'Content/Brezi/Exterior20260926') and p.suffix in ('.uasset','.uexp','.ubulk'),
                'New native asset escapes owned namespace')
    require(not any(r.get('sourceId')=='DOM_00001' for r in report['sourceRenderChanges']+report['materialBindingChanges']),
            'Original lawn ground was rebound or hidden')
    material=report['materials'];require(len(material['materials'])==36 and len(material['textures'])==70,'Native material/texture inventory differs')
    require(report['materialReadback']=={'status':'verified-saved-exterior-materials','materials':36,'textures':70},'Saved native material readback differs')
    counted.update({f'material.{key}':pins(material[key])for key in ('inputFiles','pipelineFiles')})
    for row in material['materials'].values():
        require(digest(row['graph'])==row['graphSha256'],'Saved material graph receipt hash differs')
        require(asset_file(project,row['asset']).is_file(),'Saved material asset absent')
    master_path=pin(report['plantGeometryManifest'],report['inputFiles'][report['plantGeometryManifest']]);master=read(master_path)
    require(len(master['meshes'])==70 and sum(len(m['lods'])for m in master['meshes'])==210,'Master/LOD inventory differs')
    native={row['id']:row for row in report['savedPlantReadback']}
    require(len(native)==70 and set(native)=={m['id']for m in master['meshes']},'Saved native master inventory differs')
    for mesh in master['meshes']:
        pin(mesh['glbPath'],mesh['glbSha256']);row=native[mesh['id']]
        require(row['lodTriangles']==[lod['triangles']for lod in mesh['lods']],'Native LOD triangle inventory differs')
        screens=mesh.get('lodScreenSizes',[1,.32,.10]if mesh['role']=='tree'else[1,.15,.04])
        require(len(row['lodScreens'])==3 and all(abs(a-b)<1e-6 for a,b in zip(screens,row['lodScreens'])),'Saved native LOD screens differ')
        require(asset_file(project,row['mesh']).is_file(),'Saved master asset absent')
    lawn=report['naturalLawn'];plan=read(pin(lawn['plan'],lawn['planSha256']))
    require(report['inputFiles'][lawn['plan']]==lawn['planSha256'] and lawn['audit']==plan['audit'],'Natural lawn plan/audit differs')
    require(plan['owner']=='scripts/unreal/exterior-lawn-natural-managed.py'
            and plan['audit']['status']=='PASS_STATIC_MANAGED_GEOMETRY_AND_CLEARANCE'
            and (plan['audit']['instances'],plan['audit']['groups'])==(9234,38),'Natural managed lawn scope differs')
    hidden={row['legacyLawnGroup']:row for row in lawn['hiddenOriginalGroups']}
    require(set(hidden)==set(GROUPS) and len(lawn['hiddenOriginalGroups'])==4,'Legacy hidden lawn inventory differs')
    expected={'status':'verified-hidden-original-lawn','actors':4,'instances':40437,
              'originalMeshesMaterialsGroundAndCollisionPreserved':True,'hiddenDetailDensityScalingDisabled':True}
    require(lawn['savedReadback']==expected,'Saved hidden lawn readback differs')
    for key,count in zip(GROUPS,COUNTS):
        row=hidden[key];state=row['preserved'];trim=row['sourceRuralTrim']
        require(state['instanceCount']==count and row['detailDensityScalingAfter'] is False,'Hidden legacy native lawn count/density differs')
        require(state['collisionProfile']=='NoCollision' and not state['navigation'] and not state['overlap'],'Legacy lawn collision changed')
        require(state['mesh'].endswith('/'+key+'_LOD0.'+key+'_LOD0'),'Hidden legacy mesh family differs')
        require(state['material']=='/Game/Brezi/Photoreal/Lawn/Materials/M_blade_a208ebf785c91f00.M_blade_a208ebf785c91f00','Original lawn material differs')
        require(row in report['sourceRenderChanges'],'Legacy visibility change absent from protected witness delta')
        for field in ('report','plan'):
            pin(trim[field]['path'],trim[field]['sha256'])
            require(report['inputFiles'][trim[field]['path']]==trim[field]['sha256'],'Trim provenance not independently imported/pinned')
        pin(row['sourcePlacement']['path'],row['sourcePlacement']['sha256'])
        rural=read(trim['report']['path']);entry=rural['managedLawn']['groups'][row['actor']]
        require(trim['group']==entry and entry['kept']==count and entry['sourceInstanceOrderPreserved'] is True,'Original ordered rural trim proof differs')
    groups=report['geometry']['groups'];new={g['id']:groups[g['id']]for g in plan['groups']}
    require(len(new)==38 and sum(r['instances']for r in new.values())==9234,'Native natural groups missing')
    for group in plan['groups']:
        actual=new[group['id']]
        require(actual['instances']==len(group['instances']) and actual['qualityDetail'] is True
                and (actual['cullStartCm'],actual['cullEndCm'])==(3200,4000),'Native natural detail policy differs')
        require(actual['mesh']==native[group['meshId']]['mesh'],'Native natural master binding differs')
    return report,{'receipt':receipt(file),'verifiedHashMaps':counted,'originalContentFiles':len(before),
                  'newContentFiles':len(after)-len(before),'masters':70,'lods':210,'materials':36,'textures':70,
                  'managedLawnInstances':9234,'managedLawnGroups':38,'hiddenOriginalLawnInstances':40437,
                  'protectedSavedWitnessSha256':report['savedProtectedActorWitnessSha256'],
                  'originalGroundAndPrivatePreservationEvidence':'Saved native actor witness plus unchanged protected Content hashes; no new native inspection performed by this audit.'},new,hidden


def audit_package(source,report):
    file=source/'model-package.json';package=read(file)
    require(package['status']=='current-model-packaged' and package['gameConfiguration']=='Shipping' and package['activeDesign']==DESIGN,
            'Shipping package incomplete or design differs')
    require(package['exterior']['reportSha256']==sha(source/'exterior-import-report.json')
            and package['exterior']['naturalLawn']==report['naturalLawn'],'Package does not seal this native import')
    count=pins(package['inputs']);require(package['cook']['cookCompleted'] is True and not package['cook']['failures'],'Cook validation missing')
    require(package['bundle']['status']=='bundle-validated' and package['bundle']['payloadHashScope']=='all-bundle-files','Bundle seal incomplete')
    app=resolve(package['appPath']);payload=package['bundle']['payloadHashes']
    for path,value in payload.items():pin(app/path,value)
    require(sha(package['bundle']['launch']['executable'])==package['bundle']['launch']['executableSha256'],'Packaged executable differs')
    return package,{'receipt':receipt(file),'verifiedPackageInputPins':count,'verifiedBundlePayloadFiles':len(payload),
                    'appPath':str(app),'executableSha256':package['bundle']['launch']['executableSha256']}


def audit_qa(summary_path,source,package_sha,new,hidden):
    summary=read(summary_path);require(resolve(summary['source'])==source and summary['packageReportSha256']==package_sha,'QA suite uses another package')
    require(summary['results'],'QA suite empty');rows=[]
    for entry in summary['results']:
        evidence=resolve(entry['evidence']);qa=read(evidence/'qa.json');runtime_path=pin(evidence/'runtime.json',entry['runtimeReportSha256'])
        image=pin(evidence/'capture.png',entry['screenshotSha256']);runtime=read(runtime_path)
        require(qa==entry and qa['status']=='measured' and qa['outcome']['code']==0,'QA summary/result receipt differs')
        require(qa['packageReportSha256']==package_sha and resolve(qa['source'])==source,'QA result package/source drift')
        require(runtime['status']=='capture-complete' and runtime['processId']==qa['outcome']['pid']
                and runtime['buildConfiguration']=='Shipping' and runtime['rhi']=='Metal','Runtime native PID/build/RHI differs')
        require(runtime['screenshotSaved'] is True and png_size(image)==runtime['screenshotPixels']==qa['pixels'],'Captured image dimensions differ')
        require(qa['shippingLaunch']=={'status':'native-report-pid-and-configuration-verified','loggingAvailable':False},
                'Shipping launch native identity proof differs')
        focus=runtime['focusDuringBenchmark'];samples=runtime['frameInterval']['sampleCount']
        require(samples>0 and focus['sampleCount']==samples and focus['applicationForegroundSamples']==samples
                and focus['gameWindowActiveSamples']==samples and focus['applicationForegroundThroughoutBenchmark'] is True
                and focus==qa['foreground'],'Native benchmark foreground/focus sample coverage differs')
        require(runtime['walking']['sceneSha256']==read(source/'model-package.json')['sourceManifestSha256'],'Runtime architectural frame differs')
        details={row['actor']:row for row in runtime['detailLightingState']}
        require(len(details)==len(runtime['detailLightingState']) and not (set(details)&{row['actor']for row in hidden.values()}),
                'Hidden original lawn still participates in runtime detail lighting')
        require(runtime['detailLightingState']==qa['detailLightingState'],'QA/native detail-lighting copy differs')
        for group in new.values():
            require(group['actor']in details,'New natural lawn group absent from native detail-lighting state')
            actual=details[group['actor']];enabled=qa['profile']=='cinematic'
            require(actual['managedDetail'] is True and actual['authoredFlagsCaptured'] is True
                    and actual['instanceCount']==group['instances'] and actual['qualityEnabled'] is enabled,
                    'Runtime natural lawn membership/count/quality differs')
            for current,authored in [('castShadow','authoredCastShadow'),('visibleInRayTracing','authoredVisibleInRayTracing'),
                                     ('affectDistanceFieldLighting','authoredAffectDistanceFieldLighting')]:
                require(actual[current] is (enabled or actual[authored]),'Natural lawn cinematic lighting/restoration differs')
        rows.append({'id':qa['id'],'profile':qa['profile'],'scene':qa['scene'],'motion':qa['motion'],
                     'qa':receipt(evidence/'qa.json'),'runtime':receipt(runtime_path),'capture':receipt(image),
                     'pixels':runtime['screenshotPixels'],'nativePid':runtime['processId'],'rhi':'Metal','focusSamples':samples,
                     'sceneKeyboardFocusSamples':focus['sceneViewportKeyboardFocusSamples'],'frame':runtime['frameInterval'],
                     'naturalRuntimeGroups':38,'hiddenLegacyGroupsAbsent':True,
                     'screenPercentageMaxResolutionConfigured':runtime['renderSettings'].get('r.ScreenPercentage.MaxResolution'),
                     'internalShadingPixelsMeasured':False,'entryLogDetector':qa['entry']['status']})
    return {'summary':receipt(summary_path),'results':rows}


def audit_source_validation(path):
    data=read(path);require(data['status']=='PASS_SOURCE_TESTS_NATIVE_VISUAL_SEPARATE','Source test seal incomplete')
    require(data['testCount']==sum(row['testCount']for row in data['results']),'Source test counts differ')
    pins(data['sourcePins'])
    for row in data['results']:
        require(row['exitCode']==0,'A source test run failed')
        files=[p for p in row['command']if p.endswith(('.py','.mjs','.js'))]
        require(len(files)==1 and sha(files[0])==row['testSourceSha256'],'Recorded test source drift')
        for name in ('validationReceipt','log'):
            if name in row:pin(row[name],row[name+'Sha256'])
    return {'receipt':receipt(path),'testCount':data['testCount'],
            'freshlyValidatedTests':data.get('freshlyValidatedTests'),'retainedUnchangedSourceTests':data.get('retainedUnchangedSourceTests'),
            'evidence':'Recorded source test receipts; this audit does not rerun tests.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',required=True);parser.add_argument('--qa-summary',action='append',required=True)
    parser.add_argument('--source-validation');parser.add_argument('--output',required=True);args=parser.parse_args()
    source=resolve(args.source);output=resolve(args.output)
    require(source.is_relative_to(ROOT/'output/unreal') and output.is_relative_to(ROOT/'output/unreal')
            and not output.exists() and not output.is_relative_to(source/'Project'),'Audit receipt must be new and external to native project')
    report,import_result,new,hidden=audit_import(source);package,package_result=audit_package(source,report)
    suites=[audit_qa(p,source,package_result['receipt']['sha256'],new,hidden)for p in args.qa_summary]
    require(any(r['profile']=='cinematic'for s in suites for r in s['results']),'Cinematic runtime natural-lawn acceptance missing')
    result={'schemaVersion':1,'owner':'scripts/unreal/exterior-final-audit.py','sourceSha256':sha(__file__),
            'status':'PASS_READ_ONLY_IMPORT_PACKAGE_AND_RUNTIME_RECEIPTS','generatedAtUtc':datetime.now(timezone.utc).isoformat(),
            'source':str(source),'activeDesign':DESIGN,'setbacksMm':{'street':3000,'east':3000},
            'nativeImport':import_result,'shippingPackage':package_result,'qa':suites,
            'sourceValidation':audit_source_validation(args.source_validation)if args.source_validation else None,
            'limits':['Receipts and actual source/package/capture byte hashes verified; no editor or app launched by this audit.',
                      'Shipping logging is unavailable; the app-entry log detector is not claimed to pass.',
                      'Output target/capture dimensions and configured resolution cap do not establish internal shading dimensions.',
                      'This receipt does not assert indistinguishability from reality or replace human visual review.']}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x')as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({'receipt':str(output),'sha256':sha(output),'status':result['status'],
                      'qaResults':sum(len(s['results'])for s in suites)}))


if __name__=='__main__':main()
