"""R23 closed CPU guards; source evidence is not a native or appearance result."""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
OWNER='scripts/unreal/exterior-roof-pbr-guards.py'
STUDY=ROOT/'output/unreal/exterior-roof-pbr-20261002-r3-study'
PLAN=STUDY/'roof-pbr-source-plan.json'
PLAN_SHA='0370301cb33688419b1940dd7c812f5fbedf8c7590a5df09b3e5e6e1de26000b'
BASE=ROOT/'output/unreal/exterior-20261001-r18b'
BASE_SHA='40ccc7cc686e2beafc05e5248eb8abe371f23bc8ad470c05284d4c442ed950da'
PREFIX='/Game/Brezi/RoofPbr20261002R23'
MATERIAL=PREFIX+'/Materials/M_roof_tiles_original.M_roof_tiles_original'
GENERIC=ROOT/'scripts/unreal/exterior-canopy-transmission-native.py'
GENERIC_SHA='10cc942f098e130f8f22f0acb9948f4381bdc0226d5db2af17a4665fd701bc6b'
TARGET_IDS=tuple('neighbor_r18_BU_'+building+'_'+role+'_neighbor_roof_red' for building in ('572063','3800911') for role in ('roof','roof_ridge'))
FLAGS=('nativeExecuted','nativeApplied','nativeAppearanceAccepted','performanceAccepted','fullPhotorealismAccepted','shippingVerified','packageVerified')
def require(ok,message):
    if not ok:raise RuntimeError(message)
def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1048576),b''):h.update(block)
    return h.hexdigest()
def read(path):return json.loads(Path(path).read_text())
def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def pin(path):
    path=Path(path).resolve();require(path.is_file()and not path.is_symlink(),'Regular source file required')
    return dict(path=str(path),sha256=sha(path),bytes=path.stat().st_size)
def check_pin(row):
    require(set(row)=={'path','sha256','bytes'},'Unexpected pin schema');p=Path(row['path'])
    require(p.is_absolute()and p.resolve()==p and not p.is_symlink()and p.is_file()and p.stat().st_size==row['bytes']and sha(p)==row['sha256'],'Pinned bytes changed: '+str(p));return p
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def generic():
    require(sha(GENERIC)==GENERIC_SHA,'Immutable generic helper changed');return module('r23_immutable_generic',GENERIC)
def pins_in(value,inputs):
    if not isinstance(value,(dict,list)):return
    if isinstance(value,dict)and {'path','sha256','bytes'}<=set(value):
        row={k:value[k]for k in ('path','sha256','bytes')};check_pin(row);inputs[row['path']]=row['sha256'];return
    for v in (value.values()if isinstance(value,dict)else value):pins_in(v,inputs)
def validate_recipe(recipe):
    proposal=STUDY/'roof-material-proposal.json';require(sha(proposal)=='36db8b60ad3d6c01f97c5e4ef0f49b02455bfc6446dea675cb98b45f39bd13e7'and recipe==read(proposal),'Only the exact pinned original-map physical recipe is supported')
    require(recipe['id']=='roof_tiles_original_terracotta_r1'and recipe['kind']=='original-provider-roof-pbr-material-only-proposal'and set(recipe['maps'])=={'albedo','normal','roughness'},'Unapproved roof material roles')
    require(recipe['sourcePage']=='https://polyhaven.com/a/roof_tiles'and recipe['license']=='CC0-1.0'and recipe['author']=='Stephan Seeliger','Provider identity differs')
    require(recipe['physicalPeriodMm']==[2000,2000]and recipe['inputUVChannel']==0 and recipe['existingUV0PhysicalPeriodCm']==100 and recipe['proposedUVMultiplier']==[.5,.5]and recipe['metallic']==0. and recipe['blendMode']=='Opaque','Physical map routes/period differ')
    for key in ('displacementApplied','worldPositionOffsetApplied','sourcePixelsEdited','nativeApplied','nativeAppearanceAccepted'):require(recipe[key]is False,'Source recipe claims mutation/acceptance')
    require([recipe[k]for k in ('newNativeMaterialGraphsProposed','newNativeTextureObjectsProposed','newNativeMeshObjectsProposed','newImportPipelineAssetsProposed')]==[1,3,0,0],'Asset scope changed')
    for role,row in recipe['maps'].items():
        require(row['publishedIdentityVerified']is True and row['sourcePixelsEdited']is False and row['publishedMD5']==row['actualMD5']and row['publishedBytes']==row['bytes'],'Provider map identity differs')
        p=check_pin({k:row[k]for k in ('path','sha256','bytes')})
        require(hashlib.md5(p.read_bytes()).hexdigest()==row['publishedMD5'],'Original published MD5 differs')
    return recipe

def expected_witness(before,targets,material=MATERIAL):
    require(len(before)==5338 and len(targets)==4 and {r['sourceMeshId']for r in targets}==set(TARGET_IDS),'Exact R18b scene and four redroof targets required')
    result=copy.deepcopy(before);changes=[]
    require(len({r['actor']for r in targets})==4,'Duplicate target actor')
    for target in targets:
        require(target['slot']==0 and target['componentClass']=='/Script/Engine.StaticMeshComponent','Only static component slot0 may change')
        actor=result[target['actor']];require(before[target['actor']]==target['originalSavedActorWitness'],'Target original saved witness differs')
        parts=[c for c in actor['components']if c['name']==target['componentName']and c['class']==target['componentClass']]
        require(len(parts)==1,'Target component missing/ambiguous');c=parts[0]
        require(c['mesh']==target['mesh']and c['materials']==[target['oldMaterial']]and c['overrideMaterials']==[],'Target mesh/material/override differs')
        c['materials']=[material];c['overrideMaterials']=[material]
        changes.append(dict(sourceMeshId=target['sourceMeshId'],actor=target['actor'],componentName=target['componentName'],slot=0,mesh=target['mesh'],beforeMaterial=target['oldMaterial'],afterMaterial=material,changedFields=['materials','overrideMaterials']))
    return result,changes

def validate_content_delta(before,after,texture_assets):
    require(len(before)==4027 and set(before)<=set(after),'Original R18b Content membership differs/removed')
    changed=sorted(k for k in before if before[k]!=after[k]);require(changed==['Brezi/Maps/Brezi.umap'],'Only original scene map may change')
    packages={a.split('.')[0].removeprefix('/Game/')for a in [MATERIAL,*texture_assets]}
    require(len(packages)==4 and all(p.startswith(PREFIX.removeprefix('/Game/')+'/')for p in packages),'Exactly1graph3texture packages required')
    added=sorted(set(after)-set(before))
    require(all(Path(k).suffix in ('.uasset','.uexp','.ubulk')and str(Path(k).with_suffix(''))in packages for k in added),'Unexpected added asset/pipeline/geometry')
    require({k for k in added if k.endswith('.uasset')}=={k+'.uasset'for k in packages},'Four complete packages required')
    return dict(changedFiles=changed,newFiles=added,newUassetPackages=4,protectedOriginalFilesByteIdentical=4026)

def load_source():
    require(sha(PLAN)==PLAN_SHA,'Only accepted frozen roof R3 source option is supported');plan=read(PLAN)
    require(plan['schemaVersion']==1 and plan['schema']=='brezi-original-roof-pbr-source-option-r1'and plan['owner']=='scripts/unreal/exterior-roof-pbr-study-r3.py'and plan['status']=='source-only-original-roof-pbr-material-option-native-pending','Unapproved source owner/type/status')
    require(all(plan[k]is False for k in FLAGS),'Source option claims native acceptance')
    inputs={};pins_in(plan,inputs)
    require(plan['baseNativeReport']==pin(BASE/'neighbor-finish-overlay-report-r3.json')and plan['baseNativeReport']['sha256']==BASE_SHA,'Exact R18b native base required')
    base=read(check_pin(plan['baseNativeReport']));require(base['schemaVersion']==3 and base['owner']=='scripts/unreal/exterior-neighbor-finish-native-r3.py'and base['status']=='neighbor-finish-native-overlay-validated'and base['savedReloaded']is True,'R18b native base not saved')
    require(base['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}and base['setbacksMm']=={'street':3000,'east':3000},'Binding design/setbacks changed')
    require(base['project']==str(BASE/'Project/BreziTwin')and base['output']==str(BASE),'Foreign base project')
    process=read(check_pin(plan['baseNativeProcessReceipt']));run=read(process['processFile'])
    require(run['code']==0 and run['signal']is None and run['pid']==base['nativeProcessId']==32105 and process['reportSha256']==BASE_SHA and sha(process['processFile'])==process['processFileSha256']and sha(process['logFile'])==process['logSha256']and process['sourcePinsUnchangedAfterNative']is True,'Actual base process closure changed')
    inputs.update({process['processFile']:process['processFileSha256'],process['logFile']:process['logSha256']})
    for file,h in process['sourcePinsBeforeNative'].items():require(sha(file)==h,'Base consumed pin changed');inputs[file]=h
    recipe=validate_recipe(read(check_pin(plan['materialProposal'])))
    geometry=read(check_pin(plan['sourceGeometry']));rows={r['id']:r for r in geometry['candidateMeshes']if r['id']in TARGET_IDS}
    require(set(rows)==set(TARGET_IDS)and sum(len(r['indices'])//3 for r in rows.values())==332,'Exact existing332 roof/ridge source triangles required')
    saved=read(check_pin(plan['baseSavedActorWitness']));require(plan['baseSavedActorWitness']==base['savedActorWitness']and len(saved)==5338,'Original complete actor witness differs')
    targets=plan['targets'];require({r['sourceMeshId']for r in targets}==set(TARGET_IDS),'Source target population changed')
    for target in targets:
        identity=target['sourceMeshId'];row=rows[identity]
        require(target['actor']==base['addedActors'][identity]and target['mesh']==base['meshes'][identity]and target['oldMaterial']==base['materials']['materials']['neighbor_roof_red']['asset']and target['buildingSourceId']==row['buildingSourceId']and target['role']==row['role'],'Source target semantic identity differs')
    expected_witness(saved,targets)
    measurement=read(check_pin(plan['sourceMeasurement']))
    require(measurement['sourceTriangles']==332 and measurement['redRoofTargetComponents']==4 and measurement['geometryModified']is False and measurement['maximumRelativeMetricEdgeError']<1e-4 and measurement['maximumRelativeMetricEdgeError']>1e-5 and measurement['existingUV0MetricWithinMeasuredSourcePrecision']is True,'Measured UV limitation lost')
    # Numeric measurements are retained as pinned source records. Runtime math
    # may differ by ULP; no derived exact-dictionary equality is required here.
    review=pin(STUDY/'source-visual-review.json');require(review['sha256']=='343daa8b1949cb42ffb058b6fb6a1592a2cd02639b7c96eabccc3daf2d09d308','Selected source review changed');inputs[review['path']]=review['sha256']
    content=read(check_pin(base['afterContentInventory']));proof=read(check_pin(base['protectedProjectProof']))
    require(len(content)==4027 and proof['fileCount']==len(proof['files'])==132,'Base Content/protected membership differs')
    project={k:dict(sha256=v['sha256'],bytes=v['bytes'])for k,v in proof['files'].items()}
    require(len(base['materials']['materials'])==9 and len(base['materials']['textures'])==3,'Existing R18 material/texture scope differs')
    pins_in({k:base[k]for k in ('afterContentInventory','protectedProjectProof','savedActorWitness','originalMaterialTextureWitness','savedOriginalMaterialTextureWitness','sourceStudy','diagnosticSupplement')},inputs)
    for file,h in base['pipelineFiles'].items():require(sha(file)==h,'Frozen successful R18 pipeline changed');inputs[file]=h
    inputs[str(GENERIC)]=GENERIC_SHA;generic()
    audit=dict(baseActors=5338,targetComponents=4,sourceRoofTriangles=332,newMaterialGraphs=1,newTextures=3,newGeometryAssets=0,newImportPipelines=0,existingMaterialGraphs=51,existingTextureObjects=77,measuredSourceMaximumRelativeUVMetricError=measurement['maximumRelativeMetricEdgeError'],sourceOnly=True,nativeGeometryReadbackAvailable=False,nativeAppearanceAccepted=False,fullPhotorealismAccepted=False,performanceAccepted=False)
    return dict(plan=plan,base=base,recipe=recipe,sourceRows=rows,targets=targets,baseSaved=saved,content=content,projectProof=project,sourceMeasurement=measurement,sourceVisualReview=review,inputPins=inputs,audit=audit)
