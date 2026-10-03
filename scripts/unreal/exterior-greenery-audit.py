"""Read-only R7 greenery import, package and optional runtime evidence audit.

Source/import/package success is separate from native visual acceptance and
foreground performance acceptance. Nothing launches Unreal or modifies a
selector, native asset, package, old receipt or source plan. QA defaults to
Cinematic and complete application/window foreground coverage; artifact-only
mode retains screenshots while explicitly invalidating unfocused timing.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-greenery-audit.py'
DESIGN={'variant':'C','heatingLayout':'B','livingLayout':'B'}
ASSETS=ROOT/'output/unreal/exterior-assets-greenery-20260930-r3'
MASTER_SHA='c81bf517e7ba860c592f78c5a62fd40609c9e88f37e0ebf4d3dc01d47864f835'
MATERIAL_SHA='9e5657594af2fc9030141a29c0b4a569954f00acb9c877d2dd2d01e05c1da111'
ASSET_SHA='b3b31006091a580af2d6595c0342463554383aae6d2bf69e215f91820745a8f7'
PLANS={
    'flower':('exterior-garden-flower-masters-20260930-r1c/garden-plan.json','2146de4a95754c5aece0f4018b0e3e92847c74223cf1253fbd7108659234974b'),
    'lawn':('exterior-lawn-natural-20260930-r3d/lawn-natural-plan.json','fa1b794ad5833d4949ae585d5fd1817b97e9f2181863cfe08d1ba95f93b1309a'),
    'canopy':('exterior-canopy-masters-20260930-r1d/canopy-plan.json','1a2c36d4f272302f832b100c052ab1047f651fb10b6a7e301d0ab4fea99d1e51'),
    'ecology':('exterior-canopy-ecology-20260930-r3/canopy-ecology-plan.json','681d311f3c904ff63a73f085daab3caa04b7ab134ffd84e8c8f2c1a54d5270fa')}
LEGACY_COUNTS=dict(zip(('LawnTuft'+str(i)for i in range(4)),(10118,10153,10147,10019)))


def require(ok,message):
    if not ok:raise RuntimeError(message)


def resolve(path):return (ROOT/Path(path)).resolve()


def sha(path):
    h=hashlib.sha256()
    with resolve(path).open('rb')as stream:
        while chunk:=stream.read(1024*1024):h.update(chunk)
    return h.hexdigest()


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(path):return json.loads(resolve(path).read_text())
def receipt(path):return {'path':str(resolve(path)),'sha256':sha(path)}


def pin(path,value):
    path=resolve(path);require(path.is_file()and sha(path)==value,'Audit pin differs: '+str(path));return path


def pins(mapping):
    require(isinstance(mapping,dict)and mapping,'Audit input pin map missing')
    for path,value in mapping.items():pin(path,value)
    return len(mapping)


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


def asset_file(project,asset):
    require(asset.startswith('/Game/')and '.'in asset,'Unexpected native asset reference')
    return project/'Content'/(asset.removeprefix('/Game/').split('.',1)[0]+'.uasset')


def png_size(path):
    header=resolve(path).read_bytes()[:24]
    require(header[:8]==b'\x89PNG\r\n\x1a\n'and header[12:16]==b'IHDR','QA image is not PNG')
    return list(struct.unpack('>II',header[16:24]))


def fixed_plans(report):
    result={}
    for role,(relative,value)in PLANS.items():
        path=pin(ROOT/'output/unreal'/relative,value)
        require(report['inputFiles'].get(str(path))==value,'R7 exact '+role+' plan is not imported/pinned')
        plan=read(path);require(plan['activeDesign']==DESIGN and plan['housePlacement']['streetSetbackMm']==
            plan['housePlacement']['eastSetbackMm']==3000,'R7 plan design/setback differs')
        pins(plan['inputFiles']);result[role]=plan
    require(len(result['flower']['gardenDetailPlacements'])==461,'Final flower plan count differs')
    return result


def texture_identity(role,spec,recipe):
    flip=role=='normal'and recipe['normalConvention']=='OpenGL'
    coverage=float(recipe['opacityMaskClipValue'])if role=='alpha'else 0.
    address=recipe.get('addressMode','wrap');resize=recipe.get('powerOfTwoMode')
    return role+'_'+spec['sha256'][:16]+('_flip'if flip else '')+('_c'+str(round(coverage*1000))if coverage else '')+('_clamp'if address=='clamp'else '')+('_pot'if resize else '')


def audit_materials(source,report):
    project=source/'Project/BreziTwin';material=report['materials'];records=material['materials'];textures=material['textures']
    require(len(records)==39,'R7 native material recipe count differs')
    require(report['materialReadback']=={'status':'verified-saved-exterior-materials','materials':39,'textures':len(textures)},'R7 material readback count differs')
    require(len(textures)==len({r['asset']for r in textures.values()}),'Native deduplicated texture assets repeat')
    pins(material['inputFiles']);pins(material['pipelineFiles']);referenced=set()
    for key,row in records.items():
        require(digest(row['graph'])==row['graphSha256'],'Material graph receipt differs: '+key)
        require(asset_file(project,row['asset']).is_file(),'Saved native material asset missing')
        recipe=row['recipe']
        for src in [recipe]+([recipe['groundCover']]if 'groundCover'in recipe else []):
            for role,spec in src.get('maps',{}).items():
                pin(spec['path'],spec['sha256']);identity=texture_identity(role,spec,recipe)
                require(identity in textures,'Recipe texture absent from native build dedup: '+identity)
        for node in row['graph']['nodes']:
            texture=node.get('values',{}).get('texture')
            if texture:referenced.add(texture)
    require(referenced=={row['asset']for row in textures.values()},'Native texture count differs from actual graph references')
    for key,row in textures.items():
        pin(row['sourcePath'],row['sourceSha256']);require(asset_file(project,row['asset']).is_file(),'Saved native texture asset missing')
        spec={'sha256':row['sourceSha256']};recipe={'normalConvention':row['normalConvention'],
            'addressMode':row['addressMode'],'powerOfTwoMode':row['powerOfTwoMode'],
            'opacityMaskClipValue':row['alphaCoverageThresholds'][0]}
        require(key==texture_identity(row['role'],spec,recipe),'Native texture dedup identity differs')
    return {'materials':39,'textures':len(textures),'textureCountDerivedFromActualNativeDedupAndGraphReferences':True}


def check_saved_groups(report,expected,native,label):
    groups=report['geometry']['groups'];result={}
    for group in expected:
        require(group['id']in groups,label+' saved group absent')
        actual=groups[group['id']];result[group['id']]=actual
        require(actual['instances']==len(group['instances'])and actual['mesh']==native[group['meshId']]['mesh'],label+' saved master/count differs')
        require(actual['qualityDetail']is group.get('qualityDetail',False)and
            (actual['cullStartCm'],actual['cullEndCm'])==(int(group['cullEndCm']*.8),group['cullEndCm']),label+' saved cull/quality differs')
        require(len(actual['transformsSha256'])==64,label+' ordered saved transform witness missing')
    return result


def audit_import(source):
    source=resolve(source);report=read(source/'exterior-import-report.json');project=source/'Project/BreziTwin'
    require(report['owner']=='scripts/unreal/exterior-import.py'and report['status']=='exterior-import-validated','R7 native import incomplete')
    require(resolve(report['project'])==project and resolve(report['output'])==source,'Import output/project identity differs')
    host=read(source/'exterior-import-process.json');process_path=pin(host['processFile'],host['processFileSha256'])
    pin(host['logFile'],host['logSha256']);process=read(process_path)
    require(host['reportSha256']==sha(source/'exterior-import-report.json')and process['code']==0 and process['signal']is None
        and process['pid']==report['nativeProcessId'],'Native import PID/process/report seal differs')
    require(str(project/'BreziTwin.uproject')in process['args']and '-run=pythonscript'in process['args']and
        '-script='+str(ROOT/'scripts/unreal/exterior-import.py')in process['args'],'Native import command differs')
    require(report['activeDesign']==DESIGN and report['setbacksMm']=={'street':3000,'east':3000},'Import design/setback differs')
    for key in ('savedReloaded','protectedContentUnchanged','sourceGeometryCollisionAndTransformsPreserved','originalMaterialAssetsPreserved'):
        require(report[key]is True,'Missing import preservation proof: '+key)
    require(report['protectedActorWitnessSha256']==report['savedProtectedActorWitnessSha256']and
        report['authoredActorWitnessSha256']==report['savedActorWitnessSha256'],'Saved actor witness differs')
    for key in ('inputFiles','pipelineFiles','afterAssetHashes'):pins(report[key])
    before,after=report['beforeAssetHashes'],report['afterAssetHashes'];allowed={str(project/'Content/Brezi/Maps/Brezi.umap'),str(project/'Content/Data/viewpoints.json')}
    require(before.keys()<=after.keys(),'Original Content deleted')
    donor=resolve(report['sourceOutput'])/'Project/BreziTwin/Content'
    for path,value in before.items():pin(donor/resolve(path).relative_to(project/'Content'),value)
    changed={p for p in before if before[p]!=after[p]}
    require(changed<=allowed and changed=={r['path']for r in report['changedAssets']},'Unapproved original Content changes')
    require(set(report['newAssets'])==after.keys()-before.keys(),'New Content inventory differs')
    for path in report['newAssets']:
        p=resolve(path);require(p.is_relative_to(project/'Content/Brezi/Exterior20260926')and p.suffix in ('.uasset','.uexp','.ubulk'),'New asset escaped owned namespace')
    require(not any(r.get('sourceId')=='DOM_00001'for r in report['sourceRenderChanges']+report['materialBindingChanges']),'Original lawn ground changed')
    require(report['viewpoints']['after']['views'][:len(report['viewpoints']['before']['views'])]==report['viewpoints']['before']['views'],'Original cameras changed')
    material_result=audit_materials(source,report)
    require(resolve(report['plantGeometryManifest'])==ASSETS/'geometry-manifest.json','R7 imported master library differs')
    for name,value in [('geometry-manifest.json',MASTER_SHA),('material-manifest.json',MATERIAL_SHA),('asset-manifest.json',ASSET_SHA)]:pin(ASSETS/name,value)
    master=read(ASSETS/'geometry-manifest.json');require(len(master['meshes'])==96 and sum(len(m['lods'])for m in master['meshes'])==288,'R7 master/LOD count differs')
    native={r['id']:r for r in report['savedPlantReadback']};require(len(native)==len(report['savedPlantReadback'])==96 and set(native)=={m['id']for m in master['meshes']},'Saved master inventory differs')
    for mesh in master['meshes']:
        pin(mesh['glbPath'],mesh['glbSha256']);row=native[mesh['id']]
        require(row['lodTriangles']==[lod['triangles']for lod in mesh['lods']],'Saved LOD triangle counts differ')
        screens=mesh.get('lodScreenSizes',[1,.32,.10]if mesh['role']=='tree'else[1,.15,.04])
        require(len(row['lodScreens'])==3 and all(abs(a-b)<1e-6 for a,b in zip(screens,row['lodScreens'])),'Saved LOD screens differ')
        require(sorted(row['materials'])==sorted(report['materials']['materials'][k]['asset']for k in mesh['materialKeys']),'Saved master material bindings differ')
        require(asset_file(project,row['mesh']).is_file(),'Saved master asset absent')
    plans=fixed_plans(report);context_pin=plans['canopy']['sourceContext'];context=read(pin(context_pin['path'],context_pin['sha256']))
    require(plans['ecology']['sourceContext']==context_pin,'Grove context frame differs')
    for plan in plans.values():require(plan['sourceSceneSha256']==context['sourceSceneSha256']and plan['sourceObjSha256']==context['sourceObjSha256'],'R7 source scene/OBJ frame differs')
    lawn_module=module('greenery_lawn','exterior-lawn-native.py');canopy_module=module('greenery_canopy','exterior-canopy-native.py')
    lawn=plans['lawn'];expected_lawn=lawn_module.validated_groups(lawn,read(lawn['geometryManifest']['path']),context['sourceSceneSha256'],context['sourceObjSha256'])
    require((len(expected_lawn),sum(len(g['instances'])for g in expected_lawn))==(40,52013),'R7 lawn scope differs')
    lawn_report=report['naturalLawn'];require(lawn_report['audit']==lawn['audit']and lawn_report['planSha256']==PLANS['lawn'][1]
        and lawn_report['replacementPolicy']==lawn['replacementPolicy'],'Imported lawn audit/preservation policy differs')
    lawn_groups=check_saved_groups(report,expected_lawn,native,'Lawn')
    hidden={r['legacyLawnGroup']:r for r in lawn_report['hiddenOriginalGroups']}
    require(len(hidden)==len(lawn_report['hiddenOriginalGroups'])==4 and set(hidden)==set(LEGACY_COUNTS),'Hidden legacy lawn scope differs')
    require(lawn_report['savedReadback']=={'status':'verified-hidden-original-lawn','actors':4,'instances':40437,
        'originalMeshesMaterialsGroundAndCollisionPreserved':True,'hiddenDetailDensityScalingDisabled':True},'Original lawn saved witness differs')
    for key,row in hidden.items():
        require(row['preserved']['instanceCount']==LEGACY_COUNTS[key]and row['detailDensityScalingAfter']is False and row in report['sourceRenderChanges'],'Legacy lawn hidden witness differs')
        state=row['preserved'];require(state['collisionProfile']=='NoCollision'and not state['navigation']and not state['overlap']
            and state['mesh'].endswith('/'+key+'_LOD0.'+key+'_LOD0')and
            state['material']=='/Game/Brezi/Photoreal/Lawn/Materials/M_blade_a208ebf785c91f00.M_blade_a208ebf785c91f00','Legacy lawn original asset/collision differs')
        for field in ('report','plan'):
            p=row['sourceRuralTrim'][field];pin(p['path'],p['sha256']);require(report['inputFiles'][p['path']]==p['sha256'],'Legacy rural trim not imported/pinned')
        pin(row['sourcePlacement']['path'],row['sourcePlacement']['sha256'])
        trim=row['sourceRuralTrim'];rural=read(trim['report']['path']);entry=rural['managedLawn']['groups'][row['actor']]
        require(trim['group']==entry and entry['kept']==LEGACY_COUNTS[key]and entry['sourceInstanceOrderPreserved']is True
            and len(state['orderedInstanceTransformsSha256'])==64,'Legacy ordered rural subset differs')
    canopy=plans['canopy'];validated=canopy_module.validated_replacements(canopy,read(canopy['geometryManifest']['path']),context,master,context['sourceSceneSha256'],context['sourceObjSha256'])
    imported=module('greenery_importer','exterior-import.py');new_context=dict(context);replacement={r['id']:r for r in validated['placements']}
    new_context['regionalVegetationPlacements']=[replacement.get(r['id'],r)for r in context['regionalVegetationPlacements']]
    regional=imported.regional_groups(master,new_context);canopy_ids={r['meshId']for r in validated['placements']}
    expected_canopy=[g for g in regional if g['meshId']in canopy_ids];check_saved_groups(report,regional,native,'All regional vegetation')
    require(sum(len(g['instances'])for g in expected_canopy)==78,'Native replacement tree count differs')
    canopy_report=report['canopyReplacement'];require(canopy_report['audit']==canopy['audit']and canopy_report['planSha256']==PLANS['canopy'][1]and
        canopy_report['trees']==78 and canopy_report['deletedTrees']==canopy_report['hiddenOriginalActors']==0 and canopy_report['nonGroveRegionalRowsPreserved']is True,'Canopy saved replacement witness differs')
    require(set(canopy_report['groupIds'])=={g['id']for g in expected_canopy},'Canopy saved group membership differs')
    ecology=plans['ecology'];validated_ecology=canopy_module.validated_ecology(ecology,read(ecology['geometryManifest']['path']),context,master,context['sourceSceneSha256'],context['sourceObjSha256'])
    expected_ecology=validated_ecology['groups'];ecology_groups=check_saved_groups(report,expected_ecology,native,'Ecology')
    ecology_report=report['canopyEcology'];require(ecology_report['audit']==ecology['audit']and ecology_report['planSha256']==PLANS['ecology'][1]and
        ecology_report['hiddenOriginalActors']==0 and ecology_report['sourceGroundUnchanged']is True,'Ecology saved preservation witness differs')
    require(set(ecology_report['groupIds'])==set(ecology_groups)and (len(ecology_groups),sum(g['instances']for g in ecology_groups.values()))==(166,24851),'Ecology saved membership differs')
    for key,expected in [('canopyReplacement',expected_canopy),('canopyEcology',expected_ecology)]:
        require(report[key]['savedReadback']=={'status':'verified-saved-grove-groups','groups':len(expected),'instances':sum(len(g['instances'])for g in expected),
            'allNewVisualsNoCollision':True,'orderedNativeTransformsVerifiedAfterReload':True},'Saved grove readback differs')
    require(report['savedGeometryReadback']['allNewVisualsNoCollision']is True,'New geometry collision policy differs')
    managed={**lawn_groups,**{k:v for k,v in ecology_groups.items()if v['qualityDetail']}}
    result={'receipt':receipt(source/'exterior-import-report.json'),'masters':96,'lods':288,**material_result,
        'lawnInstances':52013,'lawnGroups':40,'treesReplaced':78,'ecologyInstances':24851,'ecologyGroups':166,'legacyLawnInstancesPreservedHidden':40437,
        'protectedSavedWitnessSha256':report['savedProtectedActorWitnessSha256'],'nativeVisualAccepted':False,'performanceAccepted':False}
    return report,result,managed,hidden


def audit_package(source,report=None):
    source=resolve(source);report=report or audit_import(source)[0];package=read(source/'model-package.json')
    require(package['status']=='current-model-packaged'and package['gameConfiguration']=='Shipping'and package['activeDesign']==DESIGN,'Shipping package incomplete/design differs')
    require(package['exterior']['reportSha256']==sha(source/'exterior-import-report.json'),'Package does not seal R7 native import')
    for key in ('naturalLawn','canopyReplacement','canopyEcology'):require(package['exterior'][key]==report[key],'Package greenery evidence differs: '+key)
    pins(package['inputs']);require(package['cook']['cookCompleted']is True and not package['cook']['failures'],'Cook validation incomplete')
    require(package['bundle']['status']=='bundle-validated'and package['bundle']['payloadHashScope']=='all-bundle-files','Bundle seal incomplete')
    app=resolve(package['appPath']);payload=package['bundle']['payloadHashes'];require(payload,'Bundle payload seal empty')
    for path,value in payload.items():
        actual=resolve(app/path);require(actual.is_relative_to(app),'Payload escapes app');pin(actual,value)
    launch=package['bundle']['launch'];pin(launch['executable'],launch['executableSha256'])
    return package,{'receipt':receipt(source/'model-package.json'),'bundlePayloadFiles':len(payload),'appPath':str(app),
        'executableSha256':launch['executableSha256'],'nativeVisualAccepted':False,'performanceAccepted':False}


def timing_evidence(runtime,qa,artifact_only=False):
    focus=runtime['focusDuringBenchmark'];frame=runtime['frameInterval'];samples=frame['sampleCount']
    require(isinstance(samples,int)and samples>0 and focus['sampleCount']==samples and focus==qa['foreground'],'Frame/focus receipt samples differ')
    for key in ('applicationForegroundSamples','gameWindowActiveSamples'):
        require(isinstance(focus[key],int)and 0<=focus[key]<=samples,'Invalid focus sample count')
    valid=(focus['applicationForegroundSamples']==samples and focus['gameWindowActiveSamples']==samples and
        focus['applicationForegroundThroughoutBenchmark']is True)
    require(artifact_only or valid,'Timing invalid: every sample must have application foreground and game window active')
    for key in ('meanMs','p50Ms','p95Ms','p99Ms','maxMs'):
        require(math.isfinite(frame[key])and frame[key]>0,'Invalid frame interval receipt')
    return {'timingValid':valid,'timingInvalid':not valid,'timingInvalidReason':None if valid else 'Application foreground or game-window coverage is incomplete; these intervals cannot establish active-play FPS.',
        'frameReceipt':frame,'applicationForegroundSamples':focus['applicationForegroundSamples'],
        'gameWindowActiveSamples':focus['gameWindowActiveSamples'],'sampleCount':samples,'performanceAccepted':False}


def audit_qa(summary_path,source,package_sha,managed,hidden,artifact_only=False):
    source=resolve(source);summary=read(summary_path);require(resolve(summary['source'])==source and summary['packageReportSha256']==package_sha and summary['results'],'QA suite package/source differs')
    package=read(source/'model-package.json');rows=[]
    for entry in summary['results']:
        evidence=resolve(entry['evidence']);qa=read(evidence/'qa.json');require(qa==entry,'QA summary/result differs')
        runtime_path=pin(evidence/'runtime.json',entry['runtimeReportSha256']);runtime=read(runtime_path);image=pin(evidence/'capture.png',entry['screenshotSha256'])
        require(qa['status']=='measured'and qa['outcome']['code']==0 and qa['packageReportSha256']==package_sha and resolve(qa['source'])==source,'QA process/source identity differs')
        require(runtime['status']=='capture-complete'and runtime['processId']==qa['outcome']['pid']and runtime['buildConfiguration']=='Shipping'and runtime['rhi']=='Metal','Runtime native PID/build/RHI differs')
        require(runtime['screenshotSaved']is True and png_size(image)==runtime['screenshotPixels']==qa['pixels'],'Native screenshot dimensions differ')
        require(runtime['walking']['sceneSha256']==package['sourceManifestSha256'],'Runtime architectural frame differs')
        require(qa['shippingLaunch']=={'status':'native-report-pid-and-configuration-verified','loggingAvailable':False},'Shipping native launch evidence differs')
        require(artifact_only or qa['profile']=='cinematic','Default greenery QA requires Cinematic')
        timing=timing_evidence(runtime,qa,artifact_only)
        if qa['profile']=='cinematic':require(runtime['renderSettings']['foliage.DensityScale']==1,'Cinematic full greenery density differs')
        details={r['actor']:r for r in runtime['detailLightingState']};require(len(details)==len(runtime['detailLightingState'])and
            runtime['detailLightingState']==qa['detailLightingState'],'Runtime detail-lighting identity differs')
        require(not(set(details)&{r['actor']for r in hidden.values()}),'Hidden old lawn remains in runtime detail scaling')
        for group in managed.values():
            require(group['actor']in details,'New greenery detail group absent at runtime');actual=details[group['actor']];enabled=qa['profile']=='cinematic'
            require(actual['managedDetail']is True and actual['authoredFlagsCaptured']is True and actual['instanceCount']==group['instances']and
                actual['qualityEnabled']is enabled,'Runtime greenery count/detail quality differs')
            for now,authored in [('castShadow','authoredCastShadow'),('visibleInRayTracing','authoredVisibleInRayTracing'),('affectDistanceFieldLighting','authoredAffectDistanceFieldLighting')]:
                require(actual[now]is(enabled or actual[authored]),'Runtime greenery cinematic flags differ')
        rows.append({'id':qa['id'],'scene':qa['scene'],'profile':qa['profile'],'motion':qa['motion'],
            'qa':receipt(evidence/'qa.json'),'runtime':receipt(runtime_path),'capture':receipt(image),'nativePid':runtime['processId'],'rhi':'Metal',
            'pixels':runtime['screenshotPixels'],'managedGreeneryRuntimeGroups':len(managed),'hiddenLegacyGroupsAbsent':True,**timing,
            'nativeVisualAccepted':False,'artifactOnly':artifact_only,'internalShadingPixelsClaimed':False})
    return {'summary':receipt(summary_path),'results':rows,'nativeVisualAccepted':False,'performanceAccepted':False,
        'artifactOnly':artifact_only,'timingInvalid':any(r['timingInvalid']for r in rows)}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source',required=True);p.add_argument('--receipt',required=True);p.add_argument('--package',action='store_true')
    p.add_argument('--qa-summary',action='append',default=[]);p.add_argument('--artifact-only',action='store_true');a=p.parse_args()
    source,out=resolve(a.source),resolve(a.receipt)
    require(source.is_relative_to(ROOT/'output/unreal')and out.is_relative_to(ROOT/'output/unreal')and not out.exists()and
        not out.is_relative_to(source),'Use fresh external greenery audit receipt')
    require(not a.artifact_only or a.qa_summary,'Artifact-only mode requires a QA summary')
    report,imported,managed,hidden=audit_import(source);package_result=None;suites=[]
    if a.package or a.qa_summary:
        package,package_result=audit_package(source,report)
        suites=[audit_qa(path,source,package_result['receipt']['sha256'],managed,hidden,a.artifact_only)for path in a.qa_summary]
    result={'schemaVersion':1,'owner':OWNER,'sourceSha256':sha(__file__),'source':str(source),
        'status':'PASS_READ_ONLY_R7_GREENERY_RECEIPTS_NATIVE_ACCEPTANCE_PENDING','generatedAtUtc':datetime.now(timezone.utc).isoformat(),
        'activeDesign':DESIGN,'setbacksMm':{'street':3000,'east':3000},'nativeImport':imported,'shippingPackage':package_result,'qa':suites,
        'nativeVisualAccepted':False,'performanceAccepted':False,'timingInvalid':any(s['timingInvalid']for s in suites),
        'limits':['No native process launched; this audit verifies completed receipts and actual bytes.',
            'Native image appearance is decided separately by the parent review; no photorealism acceptance is inferred.',
            'Artifact-only unfocused frame intervals are invalid for active-play FPS; no performance acceptance is inferred.',
            'Capture/output dimensions do not prove internal shading dimensions.']}
    out.parent.mkdir(parents=True,exist_ok=True)
    with out.open('x')as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({'receipt':str(out),'sha256':sha(out),'status':result['status'],'timingInvalid':result['timingInvalid']}))


if __name__=='__main__':main()
