"""Final image-selected R38 contract: two slot0 bindings, two graphs, one mask.

Historical source generators/fixtures are not replayed. Frozen source and
dispatch kernels are read from their actual receipts without global mutation.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-soft-coherence-guards-r38-r2.py'
NATIVE_OWNER = 'scripts/unreal/exterior-context-yard-soft-coherence-native-r38-r2.py'
SCHEMA = 'brezi-image-selected-fixed-world-soft-ground-material-overlay-r38'
STUDY = ROOT/'output/unreal/exterior-context-yard-soft-coherence-20261002-r38-native-study-r2'
PLAN = STUDY/'soft-ground-native-plan-r2.json'
CANDIDATE = ROOT/'output/unreal/exterior-20261002-r38b'
BASE = ROOT/'output/unreal/exterior-20261002-r37b'
PROJECT = CANDIDATE/'Project/BreziTwin'
BASE_REPORT = BASE/'garden-yard-integration-native-report-r2.json'
BASE_SHA = 'f589c0d813ccfc35eba928a91a4545e03b159622fffa7ae2ba247545053c4532'
AUDIT_SHA = '5e2b2e057436049d4eabd34f3420d94b351c519094bfaed44cb10ddf24a56bf2'
SELECTION = ROOT/'output/unreal/exterior-garden-yard-20261002-r37-image-base-selection-r1/root-image-base-selection.json'
SELECTION_SHA = '530cac388ce376202dfd086bbcd1c4a02b30e232b772695218b67bfdb24d55a8'
CLONE = CANDIDATE/'soft-ground-project-clone-r38.json'
CLONE_SHA = 'a3710cf4d5b680454b9a8d770354fcea98818de461ee01c8ed1dc6c219a94910'
DRAFT_GUARD_SHA = '8d8f9f267fa944055b5477a30533531e82616a358fa36a90427fd025306b6599'
DRAFT_SCENE_SHA = 'd2b69d136f7c635bad681de8f066099699797ebe837acbb0165e05a8f8fa8aa7'
MODULE_SHA = '2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574'
MAP_RELATIVE = 'Content/Brezi/Maps/Brezi.umap'


def require(ok, message):
    if not ok: raise ValueError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def pin(path):
    p=Path(path).resolve();return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}
def checked(row):
    p=Path(row['path']);require(p.is_absolute()and p.resolve()==p and p.is_file()and not p.is_symlink()
        and pin(p)==row,'Exact regular source pin required: '+str(p));return p
def module(name,row):
    p=checked(row);s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def write(path,value): Path(path).write_text(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n')


_draft_pin=pin(ROOT/'scripts/unreal/exterior-context-yard-soft-coherence-guards-r38-draft.py')
require(_draft_pin['sha256']==DRAFT_GUARD_SHA,'Immutable original source draft changed')
d=module('r38_final_immutable_source_contract',_draft_pin)
for _name in ('SOURCE','SOURCE_SHA','PNG_SHA','PREFIX','TAG','MASK_ASSET','ASSETS','ACTOR197','DONOR668','SAMPLING_POLICY'):
    globals()[_name]=copy.deepcopy(getattr(d,_name))
REPAIR_SCHEMA='brezi-r38-visible-grayscale-texture-reflection-repair-r2'
FAILED=ROOT/'output/unreal/exterior-20261002-r38a'
FAILURE_SHA='f4336357af63d09266ad5ff1e11310f8002a4fe9dca47571c04dfc7c31de4a89'
FAILURE_AUDIT_SHA='93855883a5cfad8c41cc407974444959c6bbf59555b4db4df8128b1b33613a74'
PROBE_SHA='3c0336a80dd788e732511957db1c39351bf6d60b2985a7754bb97ee60708f4cc'
SAMPLING_POLICY.pop('compressionNone')
SAMPLING_POLICY.update(compressionSettings='TC_GRAYSCALE',maskSamplerType='SAMPLERTYPE_LINEAR_GRAYSCALE',
    primaryUncompressedSourcePolicy='source-L8-plus-srgb-false-TC_GRAYSCALE-selects-G8; actual-GPU-format-unverified')


def validate_policy(policy):
    require(policy==SAMPLING_POLICY,'Closed visible24 grayscale/bilinear/noMip/clamp policy required')
    return copy.deepcopy(policy)


def proposed_native_graphs(graphs):
    result=d.proposed_native_graphs(graphs)
    for graph in result.values():
        rows=[v for v in graph['nodes']if v['role']==TAG+'fixed-world-yard-mask']
        require(len(rows)==1 and rows[0]['values']['sampler_type']=='<MaterialSamplerType.SAMPLERTYPE_MASKS: 4>','Exact original owned mask sampler required')
        rows[0]['values']['sampler_type']='<MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE: 7>'
    return result


def validate_native_graphs(source_graphs,native_graphs):
    require(native_graphs==proposed_native_graphs(source_graphs),'Only two new mask values: MipNone and LinearGrayscale allowed')
    return {'newOwnedMaskMipValueMode':'TMVM_NONE','sourceMaskMipValueMode':'TMVM_DERIVATIVE',
        'newOwnedMaskSamplerType':'SAMPLERTYPE_LINEAR_GRAYSCALE','sourceMaskSamplerType':'SAMPLERTYPE_MASKS',
        'changedNewNodeValuesPerGraph':2,'frozenSourceGraphsEdited':False,'old58NodeValuesChanged':0,
        'inheritedUv1RouteChanged':False,'nativeShaderCompileMeasured':False}


def repair_evidence():
    failure=pin(FAILED/'soft-ground-native-report.json');audit=pin(FAILED/'root-native-reflection-failure-byte-audit-r38a-r1.json')
    probe=pin(FAILED/'texture-policy-reflection-probe-report-r1.json')
    require((failure['sha256'],audit['sha256'],probe['sha256'])==(FAILURE_SHA,FAILURE_AUDIT_SHA,PROBE_SHA),'Exact actual failed boundary/probe required')
    r,a,p=read(failure['path']),read(audit['path']),read(probe['path'])
    old=pin(FAILED/'soft-ground-native-r1-process.json');probe_process=pin(FAILED/'texture-policy-reflection-probe-r1-process.json')
    closure={};extra=[]
    for receipt,expected_pid,code,count,report_pin in ((old,66232,255,1012,failure),(probe_process,67918,0,7,probe)):
        wrapper=read(receipt['path']);raw=pin(wrapper['processFile']);log=pin(wrapper['logFile']);process=read(raw['path'])
        require(raw['sha256']==wrapper['processFileSha256']and log['sha256']==wrapper['logSha256']and wrapper['reportSha256']==report_pin['sha256']
            and wrapper['sourcePinsUnchangedAfterNative']is True and len(wrapper['sourcePinsBeforeNative'])==count
            and process['pid']==expected_pid and process['code']==code and process['endedAt'],'Actual closed failure/probe process differs')
        for path,value in wrapper['sourcePinsBeforeNative'].items():require(path not in closure or closure[path]==value,'Conflicting historical pin');closure[path]=value
        for row in (receipt,raw,log,report_pin):extra.append(row);closure[row['path']]=row['sha256']
    require(len(closure)==1024 and all(sha(path)==v for path,v in closure.items()),'Actual1024 failure/probe source closure must remain exact')
    require(r['status']=='failed'and r['nativeProcessId']==66232 and r['nativeApplied']is False and r['savedMapUnloadedReloaded']is False
        and r['error']=="Texture2D: Failed to find property 'compression_none' for attribute 'compression_none' on 'Texture2D'"
        and len(r['inputFiles'])==1003,'Measured R1 texture-reflection failure required')
    require(a['nativeExitCode']==255 and a['nativeProcessId']==66232 and a['ownOriginal4232FilesExact']is True
        and a['selectedR37b4232SourceFilesExact']is True and a['all1012ConsumedSourcePinsExact']is True
        and a['checkpointEmpty']is True and a['newAssetPackages']==0 and a['originalMapChanged']is False
        and not list((FAILED/'soft-ground-checkpoint').iterdir()),'Actual empty before-scene/import failure boundary required')
    require(p['schema']=='brezi-r38-actual-read-only-texture-policy-reflection'and p['nativeProcessId']==67918
        and p['textureClassDefaultProperties']['compression_none']['available']is False
        and all(v['available']is True for k,v in p['textureClassDefaultProperties'].items()if k!='compression_none')
        and all(v['available']is True for v in p['textureSampleClassDefaultProperties'].values())
        and all(p[k]is False for k in ('propertySettersCalled','assetsImported','mapLoadedOrSavedByProbe','nativeApplied','setterAvailabilityVerified','nativeGpuPixelFormatVerified')),
        'Actual read-only24-property/sample4 probe required; setters/GPU unverified')
    require(p['actualReflectedEnums']['TextureCompressionSettings']['TC_GRAYSCALE']=='<TextureCompressionSettings.TC_GRAYSCALE: 3>'
        and p['actualReflectedEnums']['MaterialSamplerType']['SAMPLERTYPE_LINEAR_GRAYSCALE']=='<MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE: 7>',
        'Exact runtime grayscale compression/sampler enums required')
    closure[audit['path']]=audit['sha256']
    return {'repairSchema':REPAIR_SCHEMA,'failedNativeReport':failure,'failedNativeProcess':old,'failureByteAudit':audit,
        'readOnlyReflectionProbe':probe,'reflectionProbeProcess':probe_process,'historicalSourcePins':closure,
        'actualFailureProcessId':66232,'actualReflectionProbeProcessId':67918,'runtimeGetterAvailabilityVerified':True,
        'runtimeSetterAvailabilityVerified':False,'nativeGpuPixelFormatVerified':False,'oldSourcePathsEdited':False}



def binding_for(report,clone,selection,targets):
    return {'schema':SCHEMA,'schemaVersion':2,'nativeOwner':NATIVE_OWNER,'sourceStudy':pin(SOURCE),
        'selectedNativeReport':pin(BASE_REPORT),'selectedRootImageDecision':pin(SELECTION),
        'projectClone':pin(CLONE),'selectedNativeProcessId':54956,'candidateProject':str(PROJECT),
        'targetRefs':targets,'scope':'two-slot-soft-ground-material-pilot-only','activeOutputPromoted':False,'repairEvidence':repair_evidence()}


def require_native_binding(binding):
    require(isinstance(binding,dict)and set(binding)=={'schema','schemaVersion','nativeOwner','sourceStudy','selectedNativeReport',
        'selectedRootImageDecision','projectClone','selectedNativeProcessId','candidateProject','targetRefs','scope','activeOutputPromoted','repairEvidence'}, 'Closed final binding required')
    require(binding['schema']==SCHEMA and binding['schemaVersion']==2 and binding['nativeOwner']==NATIVE_OWNER
        and binding['sourceStudy']==pin(SOURCE) and binding['sourceStudy']['sha256']==SOURCE_SHA
        and binding['selectedNativeReport']==pin(BASE_REPORT) and binding['selectedNativeReport']['sha256']==BASE_SHA
        and binding['selectedRootImageDecision']==pin(SELECTION) and binding['selectedRootImageDecision']['sha256']==SELECTION_SHA
        and binding['projectClone']==pin(CLONE) and binding['projectClone']['sha256']==CLONE_SHA
        and binding['selectedNativeProcessId']==54956 and binding['candidateProject']==str(PROJECT)
        and binding['scope']=='two-slot-soft-ground-material-pilot-only'and binding['activeOutputPromoted']is False,'Actual selected report/image/fresh clone binding differs')
    require(binding['repairEvidence']==repair_evidence(),'Exact measured failure/probe repair evidence required')
    require(set(binding['targetRefs'])=={'backdrop','substrate'}and binding['targetRefs']['backdrop']['actor']==ACTOR197
        and binding['targetRefs']['substrate']['actor']==DONOR668,'Actual R37 mapping is original197 and fresh668')
    saved=read(checked(read(BASE_REPORT)['savedActorWitness']))
    targets={}
    for role,actor in (('backdrop',ACTOR197),('substrate',DONOR668)):
        rows=[c for c in saved[actor]['components']if c['name']=='StaticMeshComponent0']
        require(len(rows)==1,'Exact selected static component required')
        targets[role]={'actor':actor,'component':'StaticMeshComponent0','originalMesh':rows[0]['mesh'],'originalMaterial':rows[0]['materials'][0]}
    require(binding['targetRefs']==targets,'Target mesh/material refs must equal authenticated selected saved witness')


def load_contract():
    bundle=d.load_contract();bundle['samplingPolicy']=copy.deepcopy(SAMPLING_POLICY);bundle['nativeGraphs']=proposed_native_graphs(bundle['graphs'])
    require(sha(BASE_REPORT)==BASE_SHA and sha(SELECTION)==SELECTION_SHA and sha(CLONE)==CLONE_SHA,'Actual selected input differs')
    report,selection,clone=read(BASE_REPORT),read(SELECTION),read(CLONE)
    require(report['schema']=='brezi-r37-clean-selected-garden-plus-saved-yard'and report['schemaVersion']==2
        and report['owner']=='scripts/unreal/exterior-garden-yard-integration-native-r37-r2.py'
        and report['status']=='verified-saved-clean-selected-garden-and-yard-integration'and report['nativeProcessId']==54956
        and report['nativeApplied']is True and report['savedMapUnloadedReloaded']is True and report['sourceInputsUnchanged']is True,'Actual saved R37b required')
    require(all(report[k]is False for k in ('nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified')),'No acceptance promotion allowed')
    require(selection['schema']=='brezi-root-r37-actual-image-base-selection-for-r38-only'and selection['schemaVersion']==1
        and selection['status']=='selected-saved-r37b-only-as-next-scoped-ground-pilot-base'
        and selection['selectedNativeReport']==pin(BASE_REPORT)and selection['selectedNativeProcessId']==54956
        and selection['activeOutputPromoted']is False,'Actual scoped root image decision required')
    require(all(c['rootSessionClosedExitCode']==0 and c['originalWholePngViewedByRoot']is True for c in selection['actualCameraCaptures'])
        and len(selection['actualCameraCaptures'])==3,'Three actually closed root image reviews required')
    audit=read(checked(selection['selectedCurrentByteAudit']));require(selection['selectedCurrentByteAudit']['sha256']==AUDIT_SHA,'Selected current byte audit differs')
    process=read(checked(clone['sourceNativeProcess']));raw_pin=pin(process['processFile'])
    require(raw_pin['sha256']==process['processFileSha256']and process['reportSha256']==BASE_SHA
        and process['sourcePinsUnchangedAfterNative']is True and len(process['sourcePinsBeforeNative'])==854,'Actual854 terminal source pins required')
    raw=read(raw_pin['path']);require(raw['code']==0 and raw['pid']==54956 and raw['endedAt'],'Actual native process0 required')
    before=read(checked(report['savedActorWitness']));composition_before=read(checked(report['beforeActorWitness']))
    require(len(before)==5364 and digest(before)==report['savedActorWitnessSha256']==report['expectedActorWitnessSha256'],'Saved full5364 witness required')
    scene_pin=pin(ROOT/'scripts/unreal/exterior-context-yard-soft-coherence-native-r38-r2-draft.py')
    require(scene_pin['sha256']==DRAFT_SCENE_SHA,'Frozen corrected mapping kernel changed')
    scene=module('r38_final_immutable_mapping_kernel',scene_pin)
    mapping=report['newActorMapping'];require(mapping[DONOR668]==DONOR668,'Actual same-path source mapping required')
    target_witness={'backdrop':before[ACTOR197],'substrate':before[mapping[DONOR668]]}
    targets=scene.resolve_future_targets(before,{'selectedReport':report,'selectedCompositionBeforeWitness':composition_before,'targetWitnesses':target_witness})
    require(targets['backdrop']['originalMaterial']==bundle['originalBackdropAsset']and targets['substrate']['originalMaterial']==bundle['originalSubstrateAsset'],'Actual source materials differ')
    content=read(checked(report['afterContentInventory']));protected=read(checked(report['protectedProjectProof']))
    require(len(content)==4100 and len(protected)==132,'Actual4100 Content132 protected base required')
    binding=binding_for(report,clone,selection,targets);require_native_binding(binding)
    bundle.update(base={'report':report,'reportPin':pin(BASE_REPORT),'project':BASE/'Project/BreziTwin','before':before,
        'content':content,'protected':protected,'process':clone['sourceNativeProcess'],'rawProcess':raw_pin,
        'selection':pin(SELECTION),'audit':selection['selectedCurrentByteAudit'],'clone':pin(CLONE),'cloneReceipt':clone},
        targets=targets,binding=binding,expected=d.counterfactual_two_slots(before,targets),draftScenePin=scene_pin)
    bundle['repairEvidence']=binding['repairEvidence']
    return bundle


def validate_clone(bundle,after=False):
    base=bundle['base'];c=base['cloneReceipt'];project=PROJECT
    require(c['schema']=='brezi-image-selected-saved-r37b-soft-ground-project-clone-r38'and c['schemaVersion']==2
        and c['status']=='verified-byte-identical-independent-apfs-image-selected-r37b-before-scoped-soft-ground-native-repair-r38'
        and c['sourceNativeReport']==base['reportPin']and c['rootImageBaseSelection']==base['selection']and c['sourceStudy']==bundle['source']
        and c['sourceProject']==str(base['project'])and c['project']==str(project)and c['nativeExecuted']is False
        and(c['fileCount'],c['contentFiles'],c['protectedFiles'])==(4232,4100,132),'Exact fresh scoped4232 clone receipt required')
    require(c['repairEvidence']=={'failedNativeReport':bundle['repairEvidence']['failedNativeReport'],
        'rootFailureByteAudit':bundle['repairEvidence']['failureByteAudit'],'failedNativeProcessId':66232,'failedNativeExitCode':255},
        'Fresh repair clone must bind exact R1 failed boundary')
    expected={'Content/'+k:v for k,v in base['content'].items()};expected.update(base['protected']);seen=set()
    for row in c['files']:
        source,destination=Path(row['source']),Path(row['destination']);relative=destination.relative_to(project).as_posix()
        require(relative in expected and relative not in seen and source==base['project']/relative
            and {k:row[k]for k in ('sha256','bytes')}==expected[relative]and row['independentInodes']is True
            and(source.stat().st_dev,source.stat().st_ino)!=(destination.stat().st_dev,destination.stat().st_ino),'Exact independent original clone row required')
        require(source.stat().st_size==row['bytes']and(after and relative==MAP_RELATIVE or destination.stat().st_size==row['bytes']),'Initial clone file size differs')
        seen.add(relative)
    require(seen==set(expected),'All4232 original rows required')


def validate_content_delta(base,current):
    new=set(current)-set(base);removed=set(base)-set(current);changed={k for k in base if k in current and base[k]!=current[k]}
    paths={asset.split('.')[0].replace('/Game/','')+'.uasset'for asset in [*ASSETS.values(),MASK_ASSET]}
    require(not removed and new==paths and changed=={'Brezi/Maps/Brezi.umap'},'Only old map and exact three new packages allowed')
    return {'newRelativeContentFiles':sorted(new),'onlyOriginalMapChanged':True,'newPackages':3}


def input_files(bundle):
    r=bundle['base']['report'];files={**r['inputFiles'],**bundle['repairEvidence']['historicalSourcePins']}
    for row in [bundle['source'],bundle['plan']['materialGraphs'],bundle['plan']['permissionField'],bundle['plan']['permissionFieldProof'],
        bundle['base']['reportPin'],bundle['base']['selection'],bundle['base']['clone'],bundle['base']['audit'],bundle['base']['process'],bundle['base']['rawProcess'],
        r['savedActorWitness'],r['beforeActorWitness'],r['afterContentInventory'],r['protectedProjectProof'],r['protectedControlsSaved'],r['newGroupNativeControlsSaved'],r['retainedEcologySaved'],bundle['draftScenePin'],_draft_pin]:
        checked(row);files[row['path']]=row['sha256']
    for rows in r['materialGraphDiagnosticFiles'].values():
        for row in rows:checked(row);files[row['path']]=row['sha256']
    for p in (ROOT/OWNER,ROOT/NATIVE_OWNER,ROOT/'scripts/unreal/exterior-context-yard-soft-coherence-materials-r38-r2.py'):
        files[str(p)]=sha(p)
    return files
