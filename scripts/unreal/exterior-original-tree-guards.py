"""R24 DRAFT guards: original tree source + actually saved R22 only.

No future native receipt is fabricated. Source inputs are frozen R1/R2. A
runnable preflight may be written only after the closed R22 saved process0.
"""
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-original-tree-guards.py'
PREFIX = '/Game/Brezi/OriginalTree20261002R24'
TAG = 'BreziOriginalTree20261002R24'
R1 = ROOT/'output/unreal/exterior-original-tree-20261002-r24-study'
R2 = ROOT/'output/unreal/exterior-original-tree-20261002-r24-tangent-r2-study'
R1_SHA = 'c45ff265adc98c394a58b69167066f3445f53800d4c6d9aa7fdb7d0cc1eb1ba6'
R2_SHA = '0e24b32ffc0f65d5888bb33c1410b0f42769e831e53523559bb884f1aeec0025'
BASE = ROOT/'output/unreal/exterior-20261002-r22c'
BASE_REPORT = BASE/'realism-integration-native-report-r3.json'
BASE_REPORT_SHA = '999fc17ea7600136a2097aecefed3d846ff0d7e9baeb7f005480b113b60b1f40'
BASE_NATIVE_OWNER = 'scripts/unreal/exterior-realism-integration-native-r22-r3.py'
BASE_NATIVE_SHA = 'f93ea98e9599ac85abd2842dc8c08d50f7977366fa1bb3ae35b5923bfd12cbae'
SAMPLE_COUNTS = (256, 3712, 128)
SOURCE_FILES = {
    'exterior-original-tree-study.py':'0240c7ff60b8ae9a009a642510bd68327aa0d3ea07a06f7b07ef954b1f54fa6e',
    'exterior-original-tree-tangent-study.py':'7d3ba062d0622cfe54dca3a4ccd22667b84df96778f5c683a9a2c8e378e357da'}


def require(value,message):
    if not value: raise RuntimeError(message)


def read(path): return json.loads(Path(path).read_text())
def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while data := stream.read(1024*1024): h.update(data)
    return h.hexdigest()
def pin(path): return {'path':str(Path(path).resolve()),'sha256':sha(path),'bytes':Path(path).stat().st_size}
def check_pin(row):
    p = Path(row['path']); require(p.is_file() and sha(p)==row['sha256'] and p.stat().st_size==row['bytes'],'Input pin changed: '+str(p)); return p
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def write(path,value):
    with Path(path).open('x') as stream: json.dump(value,stream,indent=2,allow_nan=False); stream.write('\n')
def f32(value): return struct.unpack('<f',struct.pack('<f',value))[0]
def module(name,file):
    spec = importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


def load_source():
    for name,value in SOURCE_FILES.items(): require(sha(ROOT/'scripts/unreal'/name)==value,'Frozen tree source producer changed')
    require(sha(R1/'original-tree-source-plan.json')==R1_SHA and sha(R2/'original-tree-tangent-supplement-r2.json')==R2_SHA,'Frozen R24 R1/R2 plan changed')
    r1 = read(R1/'original-tree-source-plan.json'); r2 = read(R2/'original-tree-tangent-supplement-r2.json')
    require(r1['owner']=='scripts/unreal/exterior-original-tree-study.py' and r2['owner']=='scripts/unreal/exterior-original-tree-tangent-study.py'
        and r1['schemaVersion']==1 and r2['schemaVersion']==2 and r2['r1SourceStudy']==pin(R1/'original-tree-source-plan.json'),'Known typed original source/tangent study required')
    require(r2['status']=='source-only-original-tree-derived-tangent-supplement-native-R22-base-pending','Unknown source tangent state')
    for plan in (r1,r2):
        for row in plan['inputFiles'].values(): check_pin(row)
        require(all(plan[k] is False for k in ('nativeApplied','nativeAppearanceAccepted','fullPhotorealismAccepted','ecologicalFitVerified','performanceAccepted','shippingVerified','packageVerified')),'Source study grants unsupported acceptance')
        require(plan['pendingNativeBase']['selectedNativeReport'] is None and plan['pendingNativeBase']['selectionComplete'] is False,'Source study fabricated future native base')
    descriptor = read(check_pin(r2['candidateDescriptor'])); original = read(check_pin(r1['inputFiles']['provider:tree_small_02_2k.gltf']))
    extension = module('r24_frozen_tangent_guard','exterior-original-tree-tangent-study.py')
    extension.validate_descriptor(descriptor,read(check_pin(r1['candidateGLTF'])),R2,[62772,1698569,15937],28436448)
    proof = read(check_pin(r2['tangentProof'])); require(proof['sourceVertices']==1777278 and proof['sourceTriangles']==2062487
        and proof['sharedIndexCornerFrameConflicts']==proof['originalVertexSplits']==proof['originalIndexChanges']==0
        and proof['providerTangentsPresent'] is False and proof['nativeNormalTangentReadbackAvailable'] is False,
        'Exact original indexed source and derived-basis proof required')
    recipes = read(check_pin(r2['materialProposal'])); source_recipes = read(check_pin(r1['materialProposal']))
    require(recipes==extension.material_proposal(source_recipes,proof['parts']),'Derived original UV/material interpretation changed')
    for row in proof['parts']:
        report = read(check_pin(row['perCornerMikkReport'])); extension.validate_mikk_report(report,row['vertices'],row['triangles']*3)
        check_pin(row['derivedTangents']); require(row['tangentValidation']['orderedFloat32Vec4Sha256']==row['derivedTangents']['sha256'],'Ordered derived tangent bytes differ')
    masks = read(check_pin(r1['maskReview'])); selection = read(check_pin(r1['selection']))
    require(selection['id']=='village_nearest_grove_3' and selection['retiredOriginalIndex']==0 and selection['originalNativeMembers']==4 and selection['remainingNativeMembers']==3
        and selection['retainedSourceRootIds']==['village_nearest_grove_11','village_nearest_grove_27','village_nearest_grove_30'],'Only selected index0 of exact original4-tree group may retire')
    require(masks['decodedTransformedVertices']==1777278 and masks['triangles']==2062487 and masks['originalNormalsPreserved'] is True
        and set(masks['exclusions'])=={'protected','subject','roads','buildings','cultivatedGround','managedLawn'}
        and all(r['completeTriangleClearanceLowerBoundCm']>75 for r in masks['exclusions'].values())
        and masks['wholeTreeGroveBoundaryClearanceLowerBoundCm']>0,'Full transformed original source mask proof required')
    require(r1['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}
        and r1['housePlacement']['streetSetbackMm']==r1['housePlacement']['eastSetbackMm']==3000,'C/B/B3000 changed')
    return {'r1':r1,'r2':r2,'descriptor':descriptor,'original':original,'proof':proof,'recipes':recipes,
        'selection':selection,'maskProof':masks,'binaryPath':check_pin(r1['inputFiles']['provider:tree_small_02.bin']),
        'tangentPath':check_pin(r2['derivedTangentBuffer'])}


def load_saved_base(path=BASE_REPORT):
    """Closed actual successful R22; file absence/running/failed cannot load."""
    path = Path(path).resolve(); require(path==BASE_REPORT and path.is_file()and sha(path)==BASE_REPORT_SHA,'Exact successful saved R22c R3 required; no other base can create an R24 preflight')
    r = read(path)
    require(r['schema']=='brezi-exterior-realism-saved-donor-integration-r22'
        and r['owner']==BASE_NATIVE_OWNER and r['output']==str(BASE)
        and r['status']=='verified-saved-six-donor-exterior-realism-integration' and r['savedMapUnloadedReloaded'] is True,
        'Running/failed/unregistered R22 base cannot load')
    require(r['actualAudit']['savedActors']==5346 and r['originalR16Unchanged'] is True and r['sourceInputsUnchanged'] is True
        and r['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'} and r['setbacksMm']=={'street':3000,'east':3000},'Exact saved R22 architecture/source scope required')
    require(r['nativeAppearanceAccepted'] is False and r['fullPhotorealismAccepted'] is False and r['performanceAccepted'] is False,'Saved composition is a review candidate')
    g = module('r24_successful_r22_provenance','exterior-realism-integration-guards-r22.py')
    process = g.actual_terminal(path,BASE/'realism-integration-native-r3-process.json',r['owner'],'realism-integration-native-r3')
    repair = module('r24_successful_r22_r3_provenance','exterior-realism-integration-repair-r22-r3.py')
    repair.validate_supplement(check_pin(r['repairSupplement']))
    require(r['repairSchema']==repair.SCHEMA and r['ownedSources']['native']['live']==pin(ROOT/BASE_NATIVE_OWNER)
        and r['ownedSources']['native']['live']['sha256']==BASE_NATIVE_SHA,'Actual saved R3 executable/repair provenance changed')
    require(r['beforeActorWitnessSha256']!=r['savedActorWitnessSha256'] and r['expectedActorWitnessSha256']==r['savedActorWitnessSha256'],'Saved R22 full counterfactual is incomplete')
    witness = read(check_pin(r['savedActorWitness'])); require(len(witness)==5346 and digest(witness)==r['savedActorWitnessSha256'],'Actual saved base witness pin differs')
    for key in ('selectedPlan','afterContentInventory','protectedProjectProof','materialsSaved'): check_pin(r[key])
    plan,_ = g.validate_plan(check_pin(r['selectedPlan']))
    require(r['selectedPlan']==pin(g.PLAN) and r['actualAudit']==g.EXPECTED,'Base actual typed composition plan differs')
    for file,value in r['inputFiles'].items(): require(sha(file)==value,'Saved base consumed source changed')
    for row in r['ownedSources'].values(): check_pin(row['live']); check_pin(row['snapshot'])
    return {'report':r,'pin':pin(path),'process':process,'witness':witness,'content':read(check_pin(r['afterContentInventory'])),
        'protected':read(check_pin(r['protectedProjectProof'])),'plan':plan,'guard':g,
        'nativeHelper':check_pin(r['ownedSources']['native']['live']),'nativeHelperPin':r['ownedSources']['native']['live']}


def validate_clone(path,project,base):
    receipt=read(path);project=Path(project).resolve();source=BASE/'Project/BreziTwin'
    require(receipt['schemaVersion']==1 and receipt['status']=='verified-byte-identical-independent-apfs-r24-project-clone-before-native'
        and receipt['sourceProject']==str(source)and receipt['project']==str(project)
        and receipt['baseNativeReport']==base['pin']and receipt['sourceStudy']==pin(R1/'original-tree-source-plan.json')
        and receipt['tangentSupplement']==pin(R2/'original-tree-tangent-supplement-r2.json')
        and receipt['fileCount']==4181 and receipt['contentFiles']==4049 and receipt['protectedFiles']==132,
        'Typed actual saved R22c independent R24 clone required')
    require(len(receipt['files'])==4181,'Complete actual cloned project membership required')
    observed=set();content=0
    for row in receipt['files']:
        src,dst=Path(row['source']).resolve(),Path(row['destination']).resolve()
        require(src.is_relative_to(source)and dst.is_relative_to(project)
            and src.relative_to(source)==dst.relative_to(project),'Clone row escaped exact project scope')
        relative=str(dst.relative_to(project));require(relative not in observed,'Clone row duplicated');observed.add(relative)
        content+=relative.split('/')[0]=='Content'
        require(row['independentInodes']is True and src.is_file()and dst.is_file()
            and src.stat().st_ino!=dst.stat().st_ino and src.stat().st_size==dst.stat().st_size==row['bytes']
            and sha(src)==sha(dst)==row['sha256'],'Actual cloned bytes/inodes differ: '+relative)
    expected={'Content/'+p for p in base['content']}|set(base['protected'])
    require(observed==expected and content==4049,'Clone must cover only4049 Content plus132 protected project files')
    return pin(path)


def import_descriptor(bundle,output):
    """NEW staging descriptor changes only node fit, explicitly applied natively.

    Source primitive binary32 attributes remain untouched. Importing the raw
    source shape avoids unmeasured affine-bake rounding; one new component then
    carries the frozen common node scale/translation below the copied root/yaw.
    """
    doc = deepcopy(bundle['descriptor'])
    for row in doc['buffers']+doc['images']: row['uri'] = os.path.relpath((R2/row['uri']).resolve(),output)
    doc['nodes'][0]['translation']=[0.,0.,0.]; doc['nodes'][0]['scale']=[1.,1.,1.]
    return doc


def placement_contract(bundle):
    row = bundle['selection']['newActorProposal']; node = bundle['descriptor']['nodes'][0]
    require(node['scale']==[row['sourceNodeUniformScale']]*3 and node['translation']==row['sourceNodeTranslationM'],'Frozen common fit changed')
    return {'actorAndComponentFrame':'One owned single-instance HISM in exact identity frame; no legacy ownership tag or quality-detail classification.',
        'instanceRootAndRotation':'Copy selected actual native HISM index0 translation/quaternion; add declared common source node bottom shift to the instance origin. Original geometry bottom/root is preserved.',
        'instanceOriginOffsetCm':[node['translation'][0]*100,node['translation'][2]*100,node['translation'][1]*100],
        'instanceUniformScale':node['scale'],
        'sourceCommonNodeFitPreserved':True,'sourceAttributeBakeDisabled':True,
        'nativeComputedMathAnnotationExactGate':False,'sourceRootPlacementSurveyed':False,
        'nativeMatrixProjectionIsGpuReadback':False}


def accessor_layout(document,index):
    a = document['accessors'][index]; v = document['bufferViews'][a['bufferView']]
    widths = {5126:4,5123:2,5125:4}; n = {'VEC2':2,'VEC3':3,'VEC4':4,'SCALAR':1}[a['type']]
    require(v['buffer']==0 and not a.get('sparse'),'Original provider buffer accessor required')
    return a,v.get('byteOffset',0)+a.get('byteOffset',0),v.get('byteStride',widths[a['componentType']]*n)


def cyclic(face): return min(tuple(face[i:]+face[:i]) for i in range(3))


def source_corners(document,binary,primitive):
    pa,po,ps = accessor_layout(document,primitive['attributes']['POSITION'])
    _,uo,us = accessor_layout(document,primitive['attributes']['TEXCOORD_0'])
    _,vo,vs = accessor_layout(document,primitive['attributes']['TEXCOORD_1'])
    ia,io,is_ = accessor_layout(document,primitive['indices']); fmt = '<H' if ia['componentType']==5123 else '<I'
    def vertex(i):
        require(0<=i<pa['count'],'Source index outside original vertex population')
        x,y,z = struct.unpack_from('<fff',binary,po+i*ps)
        uv0 = struct.unpack_from('<ff',binary,uo+i*us); uv1 = struct.unpack_from('<ff',binary,vo+i*vs)
        return (f32(x*100),f32(z*100),f32(y*100),*uv0,*uv1)
    for j in range(0,ia['count'],3):
        indices = [struct.unpack_from(fmt,binary,io+(j+k)*is_)[0] for k in (0,2,1)]
        yield cyclic([vertex(i) for i in indices])


def sample_triangle_indices(triangles,count):
    require(isinstance(triangles,int)and isinstance(count,int)and 2<=count<=triangles,'Bounded deterministic triangle sample required')
    result=[j*(triangles-1)//(count-1)for j in range(count)]
    require(len(set(result))==count and result[0]==0 and result[-1]==triangles-1,'Sample order/extent differs')
    return result


def source_face(document,binary,primitive,triangle):
    pa,po,ps=accessor_layout(document,primitive['attributes']['POSITION'])
    _,uo,us=accessor_layout(document,primitive['attributes']['TEXCOORD_0'])
    _,vo,vs=accessor_layout(document,primitive['attributes']['TEXCOORD_1'])
    ia,io,stride=accessor_layout(document,primitive['indices']);fmt='<H'if ia['componentType']==5123 else'<I'
    require(isinstance(triangle,int)and 0<=triangle<ia['count']//3,'Source sampled triangle out of range')
    face=[]
    for corner in (0,2,1):
        index=struct.unpack_from(fmt,binary,io+(triangle*3+corner)*stride)[0]
        require(0<=index<pa['count'],'Source sampled index out of range')
        x,y,z=struct.unpack_from('<fff',binary,po+index*ps)
        face.append((f32(x*100),f32(z*100),f32(y*100),*struct.unpack_from('<ff',binary,uo+index*us),
            *struct.unpack_from('<ff',binary,vo+index*vs)))
    return cyclic(face)


def sampled_corner_hash(indexed_faces):
    h=hashlib.sha256();count=0;prior=-1
    for index,face in indexed_faces:
        require(isinstance(index,int)and index>prior and len(face)==3,'Strict ordered sample IDs/corners required')
        h.update(struct.pack('<I',index))
        for row in cyclic(list(face)):h.update(struct.pack('<7f',*row))
        count+=1;prior=index
    return {'sampleTriangles':count,'sampledFloat32PositionUV0UV1OrderedCornerSha256':h.hexdigest()}


def source_bounds(document,binary):
    minimum=[math.inf]*3;maximum=[-math.inf]*3;count=0
    for primitive in document['meshes'][0]['primitives']:
        accessor,offset,stride=accessor_layout(document,primitive['attributes']['POSITION'])
        for index in range(accessor['count']):
            x,y,z=struct.unpack_from('<fff',binary,offset+index*stride)
            point=(f32(x*100),f32(z*100),f32(y*100))
            for axis in range(3):minimum[axis]=min(minimum[axis],point[axis]);maximum[axis]=max(maximum[axis],point[axis])
            count+=1
    require(count==1777278 and all(math.isfinite(x)for x in minimum+maximum),'Full original source bounds differ')
    return {'minimumCm':minimum,'maximumCm':maximum,'sourceVertices':count,'nativeReadbackPerformed':False}


def corner_hash(faces):
    h = hashlib.sha256(); count = 0
    for face in faces:
        require(len(face)==3 and all(len(row)==7 and all(math.isfinite(x) for x in row) for row in face),'Native/source corner values malformed')
        for row in face: h.update(struct.pack('<7f',*row))
        count+=1
    return {'triangles':count,'orderedFloat32PositionUV0UV1CornersSha256':h.hexdigest()}


def expected_original(before,selection,remaining_values):
    require(len(before)==5346 and len(remaining_values)==3,'Exact saved R22 and remaining3 roots required')
    path = selection['originalNativeActor']; require(path in before,'Original selected tree actor missing')
    result = deepcopy(before); components = result[path]['components']
    require(len(components)==1 and components[0]['instanceCount']==4,'Original selected4-tree component changed')
    components[0]['instanceCount']=3; components[0]['orderedInstanceTransformsSha256']=digest(remaining_values)
    return result


def validate_actor_delta(before,expected,after,new_path):
    require(len(before)==len(expected)==5346 and len(after)==5347 and set(after)-set(before)=={new_path},'Only one owned new tree actor may be added')
    require(all(after[k]==v for k,v in expected.items()),'Any original actor/policy differs from exact single-member retirement')


def validate_content(before,after,new_packages):
    require(len(before)==4049 and set(before)<=set(after),'All saved R22 Content members must remain')
    require(sorted(p for p in before if before[p]!=after[p])==['Brezi/Maps/Brezi.umap'],'Only original scene map may change')
    require(len(new_packages)==len(set(new_packages))==17 and set(after)-set(before)==set(new_packages),'Exactly1mesh3materials10textures3pipelines required')
    require(all(p.startswith('Brezi/OriginalTree20261002R24/') and p.endswith('.uasset') for p in new_packages),'Owned exact tree namespace required')
    return {'changedOriginalFiles':['Brezi/Maps/Brezi.umap'],'newPackageFiles':sorted(new_packages),
        'originalContentFiles':4049,'savedContentFiles':4066,'unchangedOriginalContentFiles':4048,'newPackages':17}
