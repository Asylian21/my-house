"""Read-only exact R9a upright lawn, unflared grove and substrate evidence audit.

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
OWNER='scripts/unreal/exterior-greenery-upright-audit.py'
DESIGN={'variant':'C','heatingLayout':'B','livingLayout':'B'}
SOURCE=ROOT/'output/unreal/exterior-20260930-r9a'
ASSETS=ROOT/'output/unreal/exterior-assets-greenery-20260930-r5'
MASTER_SHA='0849b3bf615bac261630cc2e97257c47e0e7641695a3859494690a5c7279c2b8'
MATERIAL_SHA='42dbaddc637c479d30482b1524217d8e9c288ff89de8f64d9f38396a1e63fbbb'
ASSET_SHA='dea3ce4b7528b78bf04fe4d192be7b79cf9ed9620547d239a42db428b67ca79c'
PLANS={
    'flower':('exterior-garden-flower-masters-20260930-r1c/garden-plan.json','2146de4a95754c5aece0f4018b0e3e92847c74223cf1253fbd7108659234974b'),
    'lawn':('exterior-lawn-upright-20260930-r4-study/lawn-natural-plan.json','60a5faa40bbd9033099b69177e90c9916ceeeff466a8ea8b359186a568078df8'),
    'canopy':('exterior-canopy-growth-20260930-r1c-study/canopy-plan.json','65e29a7bbced73ce3af4756a9d8a8efe58aba810a024bb73d8a853145412f6d8'),
    'ecology':('exterior-canopy-ecology-20260930-r4/canopy-ecology-plan.json','27d66e0032c3b8648e5c74f80dc675efb3bee0a4efde00a1549a4502cc86b576'),
    'substrate':('exterior-grove-substrate-20260930-r3/grove-substrate-plan.json','cb8ecc37bae3dc77e34bf5da4b7ea0d1c7be91599f941473254eebee328d9e10')}
LAWN_COVERAGE=('exterior-lawn-upright-20260930-r4-study/lawn-coverage-receipt.json','825f6e51a6e0642905a557d3cbaf5163d3911a35b988443e3dc2a55d2f17828d')
LAWN_BOUNDARY=('exterior-lawn-upright-20260930-r4-study/lawn-boundary-receipt.json','8f375cfa03269d711b40cddf6896b7fab1017b74c75f5a9dc03b6f564ab38dbc')
LAWN_COUNTS=(40,102011)
LAWN_TRIANGLES=[18571200,18571200,18571200]
QA_SCENES=('exterior-garden-day','exterior-lawn-detail-day','exterior-lawn-edge-day',
    'exterior-canopy-floor-day','exterior-canopy-close-day','exterior-canopy-lod-day')
LEGACY_COUNTS=dict(zip(('LawnTuft'+str(i)for i in range(4)),(10118,10153,10147,10019)))
FLOOR_ALBEDO_SHA='9ecd60bb97fa26139de6729b4baa817672acdee34f1853618c8930dde7833da7'
ENCODING_PROOF=('exterior-texture-encoding-probe-analysis-20260930-r2/diagnostic.json','c1ab90a731e9baafed80f6326cc05278e0db0b21f7e8160f7672b13cd3cf1f70')
LEGACY_INSPECTION=('lawn-native-inspection-20260930-r1.json','f293a08ee4a063bc2d9525c55aff5c3b94386a4ac48c5fda3abab73c9206841c')
PIPELINE_NAMES=('exterior-import.py','exterior-context.py','exterior-materials.py','rural-import.py','lawn-geometry.py',
    'realism-import.py','realism-room-details-import.py','realism-fixtures-import.py','performance-optimize.py',
    'performance_scene_policy.py','exterior-lawn-native.py','exterior-canopy-native.py','exterior-grove-substrate-native.py')


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


def required_pipeline(report):
    for name in PIPELINE_NAMES:
        path=ROOT/'scripts/unreal'/name
        require(report['pipelineFiles'].get(str(path))==sha(path),'Canonical native pipeline dependency missing or changed: '+name)


def legacy_inspection_state(report,hidden):
    path=pin(ROOT/'output/unreal'/LEGACY_INSPECTION[0],LEGACY_INSPECTION[1])
    require(report['inputFiles'].get(str(path))==LEGACY_INSPECTION[1],'Original native lawn inspection is not imported/pinned')
    actors={r['actor']:r for r in read(path)['taggedLawnActors']}
    require(len(actors)==4 and {r['actor']for r in hidden.values()}==set(actors),'Original native lawn actor identity differs')
    for row in hidden.values():
        old=actors[row['actor']];state=row['preserved']
        expected={k:old[k]for k in ('mesh','orderedInstanceTransformsSha256','actorTransform','componentWorldTransform','collision','collisionProfile','cullDistancesCm','navigation','overlap')}
        expected.update(material=old['materials'][0],instanceCount=old['instances'])
        require(all(state.get(k)==v for k,v in expected.items()),'Original native lawn saved state differs from immutable inspection')
        require(digest(old['orderedInstanceTransforms'])==old['orderedInstanceTransformsSha256'],
                'Original native lawn inspection ordered data differs')
    return {'inspection':receipt(path),'orderedSavedNativeTransformsCompared':40437}


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


def candidate(source):
    source=resolve(source)
    require(source==SOURCE,'This auditor accepts only the exact R9a candidate; older imports/packages/suites are excluded')
    return source


def fixed_plans(report):
    result={}
    for role,(relative,value)in PLANS.items():
        path=pin(ROOT/'output/unreal'/relative,value)
        require(report['inputFiles'].get(str(path))==value,'R9 exact '+role+' plan is not imported/pinned')
        plan=read(path);require(plan['activeDesign']==DESIGN and plan['housePlacement']['streetSetbackMm']==
            plan['housePlacement']['eastSetbackMm']==3000,'R9 plan design/setback differs')
        pins(plan['inputFiles']);result[role]=plan
    require(len(result['flower']['gardenDetailPlacements'])==461,'Final flower plan count differs')
    return result


def upright_lawn_receipts(report,plan):
    require(plan['owner']=='scripts/unreal/exterior-lawn-upright.py'and plan['audit']['status']==
        'MEASURED_UPRIGHT_MANAGED_LAWN_STUDY_NOT_NATIVE_ACCEPTED'and plan['audit']['nativeVerified']is False,
        'R9 exact upright lawn source policy differs')
    require((plan['audit']['groups'],plan['audit']['instances'])==LAWN_COUNTS and
        len(plan['lawnPlacements'])==LAWN_COUNTS[1]and
        plan['audit']['allInstancesTriangleBudgetByLod']==LAWN_TRIANGLES and
        plan['audit']['nearTriangleBudget']==LAWN_TRIANGLES[0]<=20000000,'R9 exact upright lawn population/budget differs')
    require(report['naturalLawn']['audit']==plan['audit'],'Imported upright lawn source audit differs')
    for field,(relative,value)in [('coverageReceipt',LAWN_COVERAGE),('boundaryCoverageReceipt',LAWN_BOUNDARY)]:
        path=pin(ROOT/'output/unreal'/relative,value);expected={'path':str(path),'sha256':value}
        require(plan[field]==report['naturalLawn'].get(field)==expected and
            report['inputFiles'].get(str(path))==value,'R9 upright lawn '+field+' is not the exact independently pinned receipt')
        actual=read(path)
        require(actual==plan['audit']['physicalCoverage'if field=='coverageReceipt'else'boundaryCoverage'],
            'Upright lawn coverage claims differ from external measured receipt')
    return {'physicalCoverage':plan['coverageReceipt'],'boundaryCoverage':plan['boundaryCoverageReceipt'],
        'allInstancesTriangleBudgetByLod':LAWN_TRIANGLES,'nearTriangleBudgetMeasuredFromDecodedGlbByNativeHelper':True}


def unflared_scope(report,plan,validation):
    require(plan['owner']=='scripts/unreal/exterior-canopy-ecology-unflared.py'and
        (plan['audit']['groups'],plan['audit']['instances'])==(130,24773)and
        plan['audit']['perFamily']=={'litter':19866,'twig':919,'herb':1417,'grass':2571}and
        all(r['ecologyFamily']!='flare'for r in plan['ecologyPlacements']), 'R9 unflared ecology source/count differs')
    removal=plan['audit']['collarRemoval']
    require(removal['removedInstances']==78 and removal['removedGroups']==36 and
        removal['originalTreeTransformsChanged']is False and removal['inheritedNativeActorsHidden']==0,
        'R9 unflared ecology removal/preservation differs')
    require(report['canopyEcology']['validation']==validation and
        validation['status']=='verified-source-grove-ecology'and validation['basalGroups']==0 and
        validation['instances']==24773 and validation['groups']==validation['qualityDetailGroups']==130,
        'R9 unflared native source validation differs')


def substrate_validation_comparison(native,recomputed):
    # UE's embedded Python and offline Python3.12 sum the same signed polygon
    # area with a 4.55e-13m² difference. This one explicitly named leaf permits
    # 1e-9m² (0.001mm²); every other value, type and key remains byte canonical.
    field='sourceDomainAreaM2';tolerance=1e-9
    require(set(native)==set(recomputed)and field in native,'Substrate validation keys differ')
    a,b=native[field],recomputed[field]
    require(type(a)is float and type(b)is float and math.isfinite(a)and math.isfinite(b)and
        abs(a-b)<=tolerance,'Substrate source-domain numeric area exceeds explicit recomputation tolerance')
    require(digest({k:v for k,v in native.items()if k!=field})==
        digest({k:v for k,v in recomputed.items()if k!=field}),
        'Substrate actual source validation differs outside the one bounded floating area')
    return {'countsHashesFlagsAndAllOtherFieldsExactlyCanonical':True,
        'boundedNumericalLeaves':[{'path':'validation.'+field,'nativeValue':a,'recomputedValue':b,
            'absoluteDifference':abs(a-b),'absoluteTolerance':tolerance,'unit':'m2'}]}


def substrate_readback(report,plan,validation):
    floor=report.get('groveSubstrate');require(isinstance(floor,dict),'R9 substrate native receipt is missing')
    meshes=plan['meshes'];ids=[m['id']for m in meshes]
    require(len(ids)==len(set(ids))==53 and sum(len(m['verticesCm'])for m in meshes)==216024 and
        sum(len(m['indices'])//3 for m in meshes)==406669,'R9 exact substrate decoded population differs')
    path=ROOT/'output/unreal'/PLANS['substrate'][0]
    require(floor['plan']==str(path)and floor['planSha256']==PLANS['substrate'][1]and
        report['inputFiles'].get(str(path))==PLANS['substrate'][1]and floor['regionId']=='village_nearest_grove',
        'R9 substrate plan/region is not the exact imported pin')
    require(floor['audit']==plan['audit']and
        validation['status']=='verified-source-grove-substrate','Substrate actual source geometry validation differs')
    comparison=substrate_validation_comparison(floor['validation'],validation)
    require(floor['sourceGroundUnchanged']is True and floor['hiddenOriginalActors']==0 and
        floor['meshIds']==ids,'Substrate native source ground/inventory differs')
    require(floor['savedReadback']=={'status':'verified-saved-grove-substrate','meshes':53,
        'allNewVisualsNoCollision':True,'nativeMeshBindingsVerifiedAfterReload':True},'Substrate saved native binding/collision proof differs')
    actors=[];assets=[]
    for mesh in meshes:
        mid=mesh['id'];actor=report['geometry']['actors'].get(mid);asset=report['geometry']['meshes'].get(mid)
        require(mid.startswith('context_grove_substrate_')and isinstance(actor,str)and
            actor.startswith('/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.')and isinstance(asset,str)and
            asset.startswith('/Game/Brezi/Exterior20260926/Geometry/'),'Substrate actual native actor/mesh binding absent')
        require(mesh['material']=='canopy_floor_litter'and mesh['collision']=='NoCollision'and
            mesh['castShadow']is False and mesh['nanite']is False and mesh['maxDrawDistanceCm']==18000,
            'Substrate render/collision source policy differs')
        actors.append(actor);assets.append(asset)
    require(len(set(actors))==len(set(assets))==53,'Substrate saved native actor/mesh bindings repeat')
    return {'meshes':53,'vertices':216024,'triangles':406669,'sourceGroundUnchanged':True,
        'hiddenOriginalActors':0,'savedNativeMeshBindingsVerifiedAfterReload':True,'numericRecomputationComparison':comparison}


def texture_identity(role,spec,recipe):
    flip=role=='normal'and recipe['normalConvention']=='OpenGL'
    coverage=float(recipe['opacityMaskClipValue'])if role=='alpha'else 0.
    address=recipe.get('addressMode','wrap');resize=recipe.get('powerOfTwoMode')
    encoded=role=='albedo'and recipe.get('sourceEncodingOverride')=='sRGB'
    require(not encoded or spec['sha256']==FLOOR_ALBEDO_SHA,'Unproven texture source encoding identity')
    return role+'_'+spec['sha256'][:16]+('_flip'if flip else '')+('_c'+str(round(coverage*1000))if coverage else '')+('_clamp'if address=='clamp'else '')+('_pot'if resize else '')+('_srcsrgb'if encoded else '')


def floor_encoding(records,textures,inputs):
    path=pin(ROOT/'output/unreal'/ENCODING_PROOF[0],ENCODING_PROOF[1])
    expected={'path':str(path),'sha256':ENCODING_PROOF[1]}
    floor=records['canopy_floor_litter']['recipe']
    require(floor.get('sourceEncodingOverride')=='sRGB'and floor.get('sourceEncodingProof')==expected
            and inputs.get(str(path))==expected['sha256'],'Floor source encoding proof is not sealed')
    matches=[row for row in textures.values()if row['role']=='albedo'and row['sourceSha256']==FLOOR_ALBEDO_SHA]
    require(len(matches)==1,'Floor source encoding texture identity differs')
    for row in textures.values():
        corrected=row is matches[0]
        require(row.get('sourceEncodingOverride')==('sRGB'if corrected else 'None')and
                row.get('sourceEncodingReadback')==('TSE_S_RGB'if corrected else 'TSE_NONE'),
                'Floor source encoding saved readback differs')
    return {'proof':expected,'correctedFloorAlbedos':1,'otherTextureSourceInterpretationsUnchanged':True}


def audit_materials(source,report):
    project=source/'Project/BreziTwin';material=report['materials'];records=material['materials'];textures=material['textures']
    require(len(records)==40 and len(textures)==73,'R9 native material recipe/texture count differs')
    require(report['materialReadback']=={'status':'verified-saved-exterior-materials','materials':40,'textures':73},'R9 material readback count differs')
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
            'opacityMaskClipValue':row['alphaCoverageThresholds'][0],'sourceEncodingOverride':row['sourceEncodingOverride']}
        require(key==texture_identity(row['role'],spec,recipe),'Native texture dedup identity differs')
    supplied=read(pin(ASSETS/'material-manifest.json',MATERIAL_SHA))
    expected=module('fine_greenery_materials','exterior-materials.py').prepare_manifest(supplied)['materials']
    for key in supplied:
        require(records[key]['recipe']==expected[key],'Native supplied recipe response differs: '+key)
    encoding_result=floor_encoding(records,textures,report['inputFiles'])
    floor=records['canopy_floor_litter']['recipe']
    require(floor['sourceUrl']=='https://polyhaven.com/a/forest_leaves_04'and floor['tileCm']==150 and
        floor['featherUV']is True and floor['stochasticGround']is False and floor['distanceFadeCm']==[12000.,18000.],
        'Native continuous photographic substrate mapping differs')
    return {'materials':40,'textures':73,'textureCountDerivedFromActualNativeDedupAndGraphReferences':True,
            'floorSourceEncoding':encoding_result}


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
    source=candidate(source);report=read(source/'exterior-import-report.json');project=source/'Project/BreziTwin'
    require(report['owner']=='scripts/unreal/exterior-import.py'and report['status']=='exterior-import-validated','R9 native import incomplete')
    required_pipeline(report)
    require(resolve(report['project'])==project and resolve(report['output'])==source,'Import output/project identity differs')
    host=read(source/'exterior-import-process.json');process_path=pin(host['processFile'],host['processFileSha256'])
    pin(host['logFile'],host['logSha256']);process=read(process_path)
    require(host['reportSha256']==sha(source/'exterior-import-report.json')and process['code']==0 and process['signal']is None
        and type(process['pid'])is int and process['pid']>0 and process['pid']==report['nativeProcessId'],
        'Native import PID/process/report seal differs')
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
    require(resolve(report['plantGeometryManifest'])==ASSETS/'geometry-manifest.json','R9 imported master library differs')
    for name,value in [('geometry-manifest.json',MASTER_SHA),('material-manifest.json',MATERIAL_SHA),('asset-manifest.json',ASSET_SHA)]:
        path=pin(ASSETS/name,value)
        require(report['inputFiles'].get(str(path))==value,'R9 merged library is not an exact imported input pin')
    master=read(ASSETS/'geometry-manifest.json');require(len(master['meshes'])==96 and sum(len(m['lods'])for m in master['meshes'])==288,'R9 master/LOD count differs')
    native={r['id']:r for r in report['savedPlantReadback']};require(len(native)==len(report['savedPlantReadback'])==96 and set(native)=={m['id']for m in master['meshes']},'Saved master inventory differs')
    for mesh in master['meshes']:
        pin(mesh['glbPath'],mesh['glbSha256']);row=native[mesh['id']]
        require(row['lodTriangles']==[lod['triangles']for lod in mesh['lods']],'Saved LOD triangle counts differ')
        screens=mesh.get('lodScreenSizes',[1,.32,.10]if mesh['role']=='tree'else[1,.15,.04])
        require(len(row['lodScreens'])==3 and all(abs(a-b)<1e-6 for a,b in zip(screens,row['lodScreens'])),'Saved LOD screens differ')
        require(sorted(row['materials'])==sorted(report['materials']['materials'][k]['asset']for k in mesh['materialKeys']),'Saved master material bindings differ')
        require(asset_file(project,row['mesh']).is_file(),'Saved master asset absent')
    plans=fixed_plans(report);context_pin=plans['canopy']['sourceContext'];context=read(pin(context_pin['path'],context_pin['sha256']))
    require(plans['ecology']['sourceContext']==plans['substrate']['sourceContext']==context_pin,'Grove context frame differs')
    for plan in plans.values():require(plan['sourceSceneSha256']==context['sourceSceneSha256']and plan['sourceObjSha256']==context['sourceObjSha256'],'R9 source scene/OBJ frame differs')
    lawn_module=module('greenery_lawn','exterior-lawn-native.py');canopy_module=module('greenery_canopy','exterior-canopy-native.py')
    lawn=plans['lawn'];expected_lawn=lawn_module.validated_groups(lawn,read(lawn['geometryManifest']['path']),context['sourceSceneSha256'],context['sourceObjSha256'])
    require((len(expected_lawn),sum(len(g['instances'])for g in expected_lawn))==LAWN_COUNTS,'R9 decoded upright lawn scope differs')
    lawn_coverage=upright_lawn_receipts(report,lawn)
    lawn_report=report['naturalLawn'];require(lawn_report['audit']==lawn['audit']and lawn_report['planSha256']==PLANS['lawn'][1]
        and lawn_report['replacementPolicy']==lawn['replacementPolicy'],'Imported lawn audit/preservation policy differs')
    lawn_groups=check_saved_groups(report,expected_lawn,native,'Lawn')
    hidden={r['legacyLawnGroup']:r for r in lawn_report['hiddenOriginalGroups']}
    require(len(hidden)==len(lawn_report['hiddenOriginalGroups'])==4 and set(hidden)==set(LEGACY_COUNTS),'Hidden legacy lawn scope differs')
    legacy_state=legacy_inspection_state(report,hidden)
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
    require(canopy_report['validation']==validated['audit'],'Canopy decoded source validation differs')
    ecology=plans['ecology'];validated_ecology=canopy_module.validated_ecology(ecology,read(ecology['geometryManifest']['path']),context,master,context['sourceSceneSha256'],context['sourceObjSha256'])
    expected_ecology=validated_ecology['groups'];ecology_groups=check_saved_groups(report,expected_ecology,native,'Ecology')
    ecology_report=report['canopyEcology'];require(ecology_report['audit']==ecology['audit']and ecology_report['planSha256']==PLANS['ecology'][1]and
        ecology_report['hiddenOriginalActors']==0 and ecology_report['sourceGroundUnchanged']is True,'Ecology saved preservation witness differs')
    require(set(ecology_report['groupIds'])==set(ecology_groups)and (len(ecology_groups),sum(g['instances']for g in ecology_groups.values()))==(130,24773),'Unflared ecology saved membership differs')
    unflared_scope(report,ecology,validated_ecology['audit'])
    for key,expected in [('canopyReplacement',expected_canopy),('canopyEcology',expected_ecology)]:
        require(report[key]['savedReadback']=={'status':'verified-saved-grove-groups','groups':len(expected),'instances':sum(len(g['instances'])for g in expected),
            'allNewVisualsNoCollision':True,'orderedNativeTransformsVerifiedAfterReload':True},'Saved grove readback differs')
    require(report['savedGeometryReadback']['allNewVisualsNoCollision']is True,'New geometry collision policy differs')
    actual_geometry=report['geometry']
    require(report['savedGeometryReadback']=={'meshCount':len(actual_geometry['meshes']),
        'groupCount':len(actual_geometry['groups']),'instanceCount':sum(g['instances']for g in actual_geometry['groups'].values()),
        'allNewVisualsNoCollision':True},'Whole native saved geometry inventory/readback differs')
    substrate=plans['substrate'];substrate_module=module('fine_greenery_substrate','exterior-grove-substrate-native.py')
    substrate_validation=substrate_module.validated_substrate(substrate,context,context['sourceSceneSha256'],context['sourceObjSha256'])
    require(substrate_validation['meshes']==substrate['meshes'],'Substrate validated native import geometry differs')
    substrate_result=substrate_readback(report,substrate,substrate_validation['audit'])
    for mid in report['groveSubstrate']['meshIds']:
        require(asset_file(project,report['geometry']['meshes'][mid]).is_file(),'Saved photographic substrate asset absent')
    managed={**lawn_groups,**{k:v for k,v in ecology_groups.items()if v['qualityDetail']}}
    result={'receipt':receipt(source/'exterior-import-report.json'),'masters':96,'lods':288,**material_result,
        'lawnInstances':102011,'lawnGroups':40,'uprightLawnMeasuredCoverage':lawn_coverage,'treesReplaced':78,
        'ecologyInstances':24773,'ecologyGroups':130,'authoredConicalCollars':0,'groveSubstrate':substrate_result,'legacyLawnInstancesPreservedHidden':40437,
        'protectedSavedWitnessSha256':report['savedProtectedActorWitnessSha256'],'legacyNativeInspection':legacy_state,
        'newGroupOrderedTransformsEvidence':'Exact before/after native hashes enforced by the mandatory pinned importer; raw native quaternion hashes are not independently reconstructed offline.',
        'nativeVisualAccepted':False,'performanceAccepted':False}
    return report,result,managed,hidden


def audit_package(source,report=None):
    source=candidate(source);report=report or audit_import(source)[0];package=read(source/'model-package.json')
    require(digest(report)==digest(read(source/'exterior-import-report.json')),'Package caller import evidence differs from actual saved receipt')
    require(package['status']=='current-model-packaged'and package['gameConfiguration']=='Shipping'and package['activeDesign']==DESIGN,'Shipping package incomplete/design differs')
    require(package['exterior']['reportSha256']==sha(source/'exterior-import-report.json'),'Package does not seal R9 native import')
    for key in ('naturalLawn','canopyReplacement','canopyEcology','groveSubstrate'):require(package['exterior'][key]==report[key],'Package greenery evidence differs: '+key)
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
    for key in ('applicationForegroundSamples','gameWindowActiveSamples','sceneViewportKeyboardFocusSamples'):
        require(type(focus[key])is int and 0<=focus[key]<=samples,'Invalid focus sample count')
    valid=(focus['applicationForegroundSamples']==samples and focus['gameWindowActiveSamples']==samples and
        focus['applicationForegroundThroughoutBenchmark']is True)
    require(artifact_only or valid,'Timing invalid: every sample must have application foreground and game window active')
    for key in ('meanMs','p50Ms','p95Ms','p99Ms','maxMs'):
        require(math.isfinite(frame[key])and frame[key]>0,'Invalid frame interval receipt')
    return {'timingValid':valid,'timingInvalid':not valid,'timingInvalidReason':None if valid else 'Application foreground or game-window coverage is incomplete; these intervals cannot establish active-play FPS.',
        'frameReceipt':frame,'applicationForegroundSamples':focus['applicationForegroundSamples'],
        'gameWindowActiveSamples':focus['gameWindowActiveSamples'],
        'sceneViewportKeyboardFocusSamples':focus['sceneViewportKeyboardFocusSamples'],
        'sampleCount':samples,'performanceAccepted':False}


def qa_identity(summary,source,package_sha):
    source=candidate(source)
    require(resolve(summary['source'])==source and summary['packageReportSha256']==package_sha,
        'R9 QA suite package/source differs; older suites cannot be reused')
    rows=summary.get('results',[])
    require(len(rows)==6 and {r['scene']for r in rows}==set(QA_SCENES)and
        len({r['id']for r in rows})==len({r['evidence']for r in rows})==6,'R9 exact six-view native suite differs')
    return source


def audit_qa(summary_path,source,package_sha,managed,hidden,artifact_only=False):
    source=candidate(source);summary=read(summary_path);qa_identity(summary,source,package_sha)
    pin(source/'model-package.json',package_sha)
    package=read(source/'model-package.json');rows=[]
    for entry in summary['results']:
        evidence=resolve(entry['evidence']);qa=read(evidence/'qa.json');require(qa==entry,'QA summary/result differs')
        runtime_path=pin(evidence/'runtime.json',entry['runtimeReportSha256']);runtime=read(runtime_path);image=pin(evidence/'capture.png',entry['screenshotSha256'])
        require(qa['status']=='measured'and qa['outcome']['code']==0 and qa['outcome']['signal']is None and
            qa['packageReportSha256']==package_sha and resolve(qa['source'])==source,'QA process/source identity differs')
        require(runtime['status']=='capture-complete'and type(runtime['processId'])is int and runtime['processId']>0 and
            runtime['processId']==qa['outcome']['pid']and runtime['buildConfiguration']=='Shipping'and runtime['rhi']=='Metal',
            'Runtime native PID/build/RHI differs')
        require(qa['mode']=='retina'and qa['motion']=='static'and qa['software']is False and qa['statOverlays']is False and
            runtime['screenshotSaved']is True and png_size(image)==runtime['screenshotPixels']==qa['pixels']==[1920,1080]and
            runtime['screenshotKind']=='current-scene-render-target-preserving-view-history','Native screenshot dimensions/mode differs')
        require(runtime['warmupFrames']==2400 and runtime['requestedBenchmarkFrames']==runtime['frameInterval']['sampleCount']==300 and
            qa['frame']==runtime['frameInterval'],'R9 exact warmup/frame measurement differs')
        require(runtime['walking']['sceneSha256']==package['sourceManifestSha256'],'Runtime architectural frame differs')
        require(qa['shippingLaunch']=={'status':'native-report-pid-and-configuration-verified','loggingAvailable':False},'Shipping native launch evidence differs')
        require(artifact_only or qa['profile']=='cinematic','Default R9 greenery QA requires Cinematic')
        require(runtime['activeView']==qa['scene'].removesuffix('-day'),'Native greenery view identity differs')
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
        'status':'PASS_READ_ONLY_R9A_UPRIGHT_GREENERY_RECEIPTS_NATIVE_ACCEPTANCE_PENDING','generatedAtUtc':datetime.now(timezone.utc).isoformat(),
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
