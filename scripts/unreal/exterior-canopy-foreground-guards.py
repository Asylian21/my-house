"""R21 bounded foreground guards; ordinary Python, no native or scene writes.

Serialized source geometry is authoritative. Derived distances are recomputed
for inequalities, never compared bit-for-bit between CPython and Unreal libm.
Actual native floor positions, both UV channels and winding require F32 proof.
"""
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-canopy-foreground-guards.py'
STUDY = ROOT/'output/unreal/exterior-canopy-foreground-20261001-r21-study'
PLAN_SHA = '71bddb13e370b9523558e2a1d4a90c92c9e49c44476a1b4d40ca8f0ec69e1c4a'
PRODUCER = 'scripts/unreal/exterior-canopy-foreground-study.py'
PRODUCER_SHA = '9f7c82b6e0f2bf62ef76e84a87b1b552400a1e6091c4b3a2f1de4bdc3eb00af1'
DESIGN = {'variant':'C','heatingLayout':'B','livingLayout':'B'}
MODELS = ('canopy_ecology_grass_0','canopy_ecology_grass_1','canopy_ecology_herb_0','canopy_ecology_herb_1')
COUNTS = (213,213,43,43)
MESH_ID = 'canopy_foreground_r21_surface'
MATERIAL_ID = 'canopy_foreground_r21_meadow_feather'
PREFIX = '/Game/Brezi/CanopyForeground20261002R21'
TAG = 'BreziCanopyForeground20261002R21'
NODE_TAG = 'BreziForegroundR21:'
GROUND = 'context_unresolved_flat_backdrop'
BASE_REPORT_SHA = '1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122'
SOURCE_GRAPH_SHA = '4a664b7cbe505d56e9f5e4ebcd11c03cb818fa9b8bd29344fb485bd58c881ef7'
RUNTIME_SOURCE = ROOT/'output/unreal/exterior-20261001-r16a/Project/BreziTwin/Source/BreziTwin/BreziVegetationPatch.cpp'
RUNTIME_SOURCE_SHA = '98a69ae9bacdba83d7d26870a8369b983a93d782e6411e374536cb01e4f66761'
DEPENDENCIES = {
    'exterior-grove-substrate-native.py':'c27e3b935d4486e6150e262a8309223e9f72e0ef6abb9f648af5c897283f692e',
    'exterior-canopy-native.py':'2788c643f4bd924f2fa72714d18ad009a7b4aa599ba86df58baf7582f765a172',
    'exterior-neighbor-finish-native-r3.py':'5a64d2413944cd009d74f5bba7c99b6be4f7f2a04d23f88396366062ebe856ac',
    'exterior-neighbor-finish-guards.py':'d6cbcbc3337d6828f9c3b629860725e7e7c0a3ad6ac622f5b41050494cadd706',
    'exterior-neighbor-finish-materials.py':'d7262e847de18b2a1d47de2991e7df146fe468d6e991fd82b38917efa2e2a5f5',
    'exterior-materials.py':'980284bdf5f5250f3f70f6c74045b77ac9507909cca592236fff2715c4d50707',
    'rural-import.py':'b50b1a36ad673859ee957ccbbca432ede669ddaae24c10a36f1a378b4cc70aa3',
    'performance-optimize.py':'c5a676f45f6333188c1b333564166b0b1e66be4ba242d5a6fcd66c2f0849f2fd',
    'lawn-geometry.py':'bc5bd49c01e880d45022a75ba80a3a3fd971272a86906a7a94d0618df4504d2f',
    'performance_scene_policy.py':'5f9eb8ccc2688b7d17200696cd3498558743c60fc541f8b1fbb0e80a3ba94b9e',
}


def require(value,message):
    if not value: raise ValueError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block:=stream.read(1024*1024): h.update(block)
    return h.hexdigest()


def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def pin(path): return {'path':str(Path(path).resolve()),'sha256':sha(path),'bytes':Path(path).stat().st_size}
def finite(value,n): return isinstance(value,(list,tuple)) and len(value)==n and all(type(v) in (float,int) and math.isfinite(v) for v in value)
def f32(value): return struct.unpack('<f',struct.pack('<f',value))[0]
def cyclic(values): return min(tuple(values[i:]+values[:i]) for i in range(3))


def check_pin(row):
    require(isinstance(row,dict) and set(row) in ({'path','sha256','bytes'},{'path','sha256','bytes','role'}) and
            ('role'not in row or row['role']in {'albedo','normal','roughness'}) and isinstance(row['path'],str) and
            type(row['bytes']) is int and row['bytes']>0 and isinstance(row['sha256'],str) and len(row['sha256'])==64,'Malformed typed source pin')
    path=Path(row['path']).resolve()
    require((path.is_relative_to(ROOT) or path.is_relative_to(Path('/Users/Shared/Epic Games/UE_5.8/Engine'))) and
            path.is_file() and path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],'Source bytes/hash differ: '+str(path))
    return path


def module(filename):
    path=ROOT/'scripts/unreal'/filename
    require(filename in DEPENDENCIES and sha(path)==DEPENDENCIES[filename],'Frozen generic dependency differs: '+filename)
    spec=importlib.util.spec_from_file_location('r21_'+filename.replace('-','_').replace('.','_'),path)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def load_source():
    path=STUDY/'foreground-transition-plan.json'
    require(sha(path)==PLAN_SHA and sha(ROOT/PRODUCER)==PRODUCER_SHA,'Frozen R21 study/producer differs')
    require(sha(RUNTIME_SOURCE)==RUNTIME_SOURCE_SHA,'Frozen original runtime classification source differs')
    plan=read(path)
    inputs={k:read(check_pin(v)) for k,v in plan['inputFiles'].items() if k in {'nativeR16','views','context','terrain','ecology','ecologyGeometry','ecologyPrototypes','substrate','managedLawn'}}
    for row in plan['inputFiles'].values():check_pin(row)
    require(plan['inputFiles']['nativeR16']['sha256']==BASE_REPORT_SHA,'Original R16 receipt differs')
    bundle={'plan':plan,'inputs':inputs,'geometry':read(check_pin(plan['geometry'])),'roots':read(check_pin(plan['roots'])),'material':read(check_pin(plan['materialRecipe']))}
    bundle['audit']=validate_payload(bundle)
    return bundle


def geometry_corners(mesh):
    points=[[f32(f32(v/100)*100) for v in p] for p in mesh['verticesCm']]
    uv0=[[f32(v) for v in p] for p in mesh['uv0']];uv1=[[f32(v) for v in p] for p in mesh['uv1']]
    return [cyclic([tuple(points[i]+uv0[i]+uv1[i]) for i in mesh['indices'][j:j+3]]) for j in range(0,len(mesh['indices']),3)]


def barycentric_check(witness,point,vertices,indices,expected_mesh,expected_material):
    require(witness['meshId']==expected_mesh and witness['material']==expected_material and witness['measuredElevation'] is False,'Ground source class/evidence differs')
    ordinal=witness['triangleOrdinal'];weights=witness['barycentric']
    require(type(ordinal)is int and 0<=ordinal<len(indices)//3 and finite(weights,3) and min(weights)>=-1e-7 and abs(sum(weights)-1)<1e-7,'Ground triangle/barycentric source differs')
    tri=[vertices[i]for i in indices[ordinal*3:ordinal*3+3]]
    reconstructed=[sum(t[k]*w for t,w in zip(tri,weights))for k in range(3)]
    require(max(abs(reconstructed[k]-point[k])for k in (0,1))<1e-6 and abs(reconstructed[2]-witness['zCm'])<1e-7,'Ground contact reconstruction differs')
    return reconstructed[2]


def camera_test(camera,point):
    forward=[b-a for a,b in zip(camera['eyeCm'],camera['targetCm'])];length=math.sqrt(sum(v*v for v in forward));forward=[v/length for v in forward]
    h=math.hypot(*forward[:2]);right=[forward[1]/h,-forward[0]/h,0.]
    up=[right[1]*forward[2],-right[0]*forward[2],right[0]*forward[1]-right[1]*forward[0]]
    delta=[v-a for v,a in zip(point,camera['eyeCm'])];depth=sum(a*b for a,b in zip(delta,forward));th=math.tan(math.radians(camera['horizontalFovDegrees']/2))
    return depth>0 and abs(sum(a*b for a,b in zip(delta,right)))<=depth*th+1e-6 and abs(sum(a*b for a,b in zip(delta,up)))<=depth*th/(16/9)+1e-6


def validate_payload(bundle):
    p,data,geo,roots,material=(bundle[k]for k in ('plan','inputs','geometry','roots','material'))
    require(p.get('schemaVersion')==1 and p.get('owner')==PRODUCER and p.get('status')=='source-only-bounded-artistic-foreground-native-pending' and p['generatorSha256']==PRODUCER_SHA,'R21 typed source identity differs')
    require(p['activeDesign']==data['context']['activeDesign']==DESIGN and p['housePlacement']==data['context']['housePlacement'] and p['housePlacement']['streetSetbackMm']==p['housePlacement']['eastSetbackMm']==3000,'C/B/B3000 changed')
    require(all(p[k] is False for k in ('nativeApplied','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified')),'Source acceptance flags differ')
    require(p['camera']==next(v for v in data['views']['views'] if v['id']=='exterior-canopy-close') if isinstance(data['views'],dict) else p['camera']==next(v for v in data['views']if v['id']=='exterior-canopy-close'),'Original camera changed')
    require(p['cameraAspectRatio']==16/9 and p['sourceClassification']['contextSurfaceIntersections']==[],'Camera/classification scope differs')
    require(data['nativeR16']['status']=='exterior-import-validated'and data['nativeR16']['savedReloaded']is True and len(data['nativeR16']['savedPlantReadback'])==135 and sum(len(v['lodTriangles'])for v in data['nativeR16']['savedPlantReadback'])==405,'Original validated135/405 native plant census differs')
    for key,value in p['preservedSourceArrays'].items(): require(digest(data['context'][key])==value,'Protected context array changed: '+key)
    substrate=module('exterior-grove-substrate-native.py');index=substrate._PolygonIndex
    domain=index(p['domainCm']);old_substrate=index(data['substrate']['domainCm'])
    masks={k:index(v)for k,v in data['ecology']['exclusionDomainsCm'].items()}
    masks['managedLawn']=index({'type':'MultiPolygon','coordinates':[[ring+[ring[0]] if ring[0]!=ring[-1] else ring]for ring in data['managedLawn']['managedLawnKeepPolygonsCm']]})
    mesh=geo['mesh'];vs=mesh['verticesCm'];ids=mesh['indices'];uv=mesh['uv0'];alpha=mesh['uv1']
    require(mesh['id']==MESH_ID and mesh['material']==MATERIAL_ID and mesh['winding']=='clockwise' and len(ids)==1843*3 and len(vs)==len(uv)==len(alpha)==len(geo['sourceGroundVertexWitnesses']),'Surface topology inventory differs')
    require(mesh['collision']=='NoCollision' and mesh['canEverAffectNavigation'] is False and mesh['nanite'] is False and mesh['castShadow'] is False and mesh['maxDrawDistanceCm']==6000 and mesh['nativeApplied'] is False,'Surface policies differ')
    require(all(type(i)is int and 0<=i<len(vs)for i in ids),'Surface index invalid')
    original=next(m for m in data['terrain']['meshes']if m['id']==GROUND)
    for i,(point,tex,coverage)in enumerate(zip(vs,uv,alpha)):
        require(finite(point,3) and finite(tex,2) and finite(coverage,2),'Nonfinite surface attribute')
        require(tex==[point[0]/200,point[1]/200] and 0<=coverage[0]<=1 and coverage[1]==0.,'Metric UV0/feather UV1 differs')
        z=barycentric_check(geo['sourceGroundVertexWitnesses'][str(i)],point,original['verticesCm'],original['indices'],GROUND,'context_distant_terrain')
        require(abs(z+25)<1e-6 and -1e-6<=point[2]-z<=.800001,'Artist microrelief leaves bounded source floor')
        require(all(not m.contains(point[:2]) and m.distance(point[:2],76)>74.999 for m in masks.values()),'Surface crosses authentic exclusion')
        require(not old_substrate.contains(point[:2]) and old_substrate.distance(point[:2],3)>1.999,'Surface expands original leaf substrate')
    for j in range(0,len(ids),3):
        tri=[vs[i][:2]for i in ids[j:j+3]]
        require(substrate._cross(*tri)<-1e-7,'Surface degeneracy/winding differs');domain.triangle_inside(tri)
    require(min(v[0]for v in alpha)<1e-6 and max(v[0]for v in alpha)==1.,'Surface feather is missing')
    require(material['id']==MATERIAL_ID and material['kind']=='fresh-native-meadow-graph-copy-with-masked-UV1-temporal-dither-feather' and material['sourceNativeMaterial']==data['nativeR16']['materials']['materials']['context_meadow']['asset'] and material['sourceGraphSha256']==SOURCE_GRAPH_SHA,'Original104-node PBR graph binding differs')
    require(material['newMaterialCount']==1 and material['newTextureObjects']==0 and material['preserveOriginalGraph'] is True and material['preserveAllExistingPBRRootsExceptNewOpacityMask'] is True and material['sourcePixelsUnchanged'] is True,'New material scope differs')
    graph=data['nativeR16']['materials']['materials']['context_meadow']['graph']
    require(digest(graph)==SOURCE_GRAPH_SHA and len(graph['nodes'])==104,'Original meadow graph receipt differs')
    native={v['id']:v for v in data['nativeR16']['savedPlantReadback']};all_roots=[];budget=[0,0,0]
    require(len(roots['groups'])==4 and set(roots['models'])==set(MODELS) and len(roots['authoringClusters'])==24,'Bounded groups/models/clusters differ')
    for mid,count,g in zip(MODELS,COUNTS,roots['groups']):
        model=roots['models'][mid];actual=native[mid]
        require(g['id']=='EX_canopy_foreground_r21_'+mid and g['meshId']==mid and len(g['instances'])==count and g['nativeMesh']==model['nativeMesh']==actual['mesh'] and g['nativeMaterials']==model['nativeMaterials']==actual['materials'],'Existing native master/group binding differs')
        require(g['renderingPolicy']=={'collision':'NoCollision','navigation':False,'windDisplacementCm':0,'qualityDetail':True,'cullStartCm':4500,'cullEndCm':6000},'New HISM policy differs')
        records=sorted([v for v in data['ecologyPrototypes']if v['nodeName'].startswith(mid+'_LOD')],key=lambda v:v['level']);points=[]
        require([v['level']for v in records]==[0,1,2] and model['lodScreens']==actual['lodScreens'],'Original model LOD source differs')
        for level,row in enumerate(records):
            n=sum(len(part['triangles'])for part in row['parts'].values());points.extend(v for part in row['parts'].values()for v in part['positionsCm'])
            require(model['decodedLods'][level]=={'level':level,'triangles':n,'recordSha256':digest(row)} and n==actual['lodTriangles'][level],'Original decoded LOD pin/census differs')
            budget[level]+=n*count
        radius=max(math.hypot(*v[:2])for v in points);low=min(v[2]for v in points);high=max(v[2]for v in points)
        # These three bounds are libm-derived source annotations, not bit-exact native attributes.
        require(abs(radius-model['radiusCm'])<1e-9 and abs(low-model['minZcm'])<1e-9 and abs(high-model['maxZcm'])<1e-9,'Decoded source model envelope differs')
        for row in g['instances']:
            position,scale=row['positionCm'],row['scale'];require(row['meshId']==mid and finite(position,3) and finite(scale,3) and scale[0]==scale[1]==scale[2] and .5<scale[0]<1.5 and type(row['yawDeg'])in(float,int)and math.isfinite(row['yawDeg']) and -180<=row['yawDeg']<=180,'New serialized transform invalid')
            require(row['landUseEvidence']=='ARTISTIC_UNSURVEYED_CLEARING_TRANSITION_OUTSIDE_AUTHORED_CONTEXT_CLASSES' and 0<=row['clusterIndex']<24,'Land use/cluster evidence differs')
            rad=radius*scale[0]
            require(abs(rad-row['radiusCm'])<1e-9 and abs((high-low)*scale[0]-row['actualHeightCm'])<1e-9,'Source root envelope differs')
            require(domain.contains(position[:2]) and domain.distance(position[:2],rad+1)>rad+.499,'Complete radial root footprint leaves new source domain')
            require(all(not m.contains(position[:2])and m.distance(position[:2],rad+76)>rad+74.999 for m in masks.values()),'Root crosses authentic exclusion')
            require(not old_substrate.contains(position[:2])and old_substrate.distance(position[:2],rad+3)>rad+1.999,'Root expands leaf substrate')
            barycentric_check(row['sourceGround'],position,original['verticesCm'],original['indices'],GROUND,'context_distant_terrain')
            z=barycentric_check(row['newSurfaceContact'],position,vs,ids,MESH_ID,MATERIAL_ID)
            require(abs(position[2]+low*scale[0]-z-.08)<1e-7,'Root contact differs from new surface')
            distance=math.hypot(position[0]-p['camera']['eyeCm'][0],position[1]-p['camera']['eyeCm'][1]);require(200<=distance<=2000,'Root outside bounded foreground range')
            angle=math.radians(row['yawDeg']);c,s=math.cos(angle),math.sin(angle)
            for v in points:
                world=[position[0]+scale[0]*(v[0]*c-v[1]*s),position[1]+scale[0]*(v[0]*s+v[1]*c),position[2]+scale[0]*v[2]]
                require(camera_test(p['camera'],world),'Original all-LOD source vertex leaves actual frustum')
            all_roots.append(row)
    require(sorted(r['id']for r in all_roots)==['foreground_r21_root_'+str(i).zfill(4)for i in range(512)],'Root IDs/order inventory differs')
    require(all(math.hypot(a['positionCm'][0]-b['positionCm'][0],a['positionCm'][1]-b['positionCm'][1])>=20 for i,a in enumerate(all_roots)for b in all_roots[i+1:]),'Root spacing violated')
    require(budget==[221184,147456,107496] and p['audit']['sourceInstanceTriangleBudgetByLOD']==budget,'Bounded source triangle budget differs')
    return {'surfaceTriangles':1843,'newRoots':512,'newGroups':4,'newActors':5,'newMeshAssets':1,'newMaterialAssets':1,'newTextureAssets':0,'importPipelineAssets':3,'sourceInstanceTriangleBudgetByLOD':budget,
            'fullRadialFootprintsAndAllLODSourceFrustumVerified':True,'actualSourceGroundContactsVerified':True,'originalLeafSubstrateNotExpanded':True,'protectedSourceArraysVerified':True,
            'derivedBoundComparison':'Finite geometric inequalities; source envelope annotation tolerance1e-9cm, source contacts1e-7cm; no cross-runtime bit-exact libm annotation claim',
            'groundEvidence':'Artist-authored bounded relief over unresolved flat fallback, not measured elevation or observed land use','nativeGeometryDecoded':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False}


def validate_graph_copy(original,variant):
    require(len(original['nodes'])==104 and digest(original)==SOURCE_GRAPH_SHA,'Protected original meadow graph differs')
    additions=[n for n in variant['nodes']if n['role'].startswith(NODE_TAG)]
    require(len(additions)==3 and len(variant['nodes'])==107 and [n for n in variant['nodes']if not n['role'].startswith(NODE_TAG)]==original['nodes'],'Only three new feather graph nodes allowed')
    by={v['role'][len(NODE_TAG):]:v for v in additions}
    require(set(by)=={'uv1','coverage-r','temporal-dither'} and by['uv1']['class']=='MaterialExpressionTextureCoordinate' and by['uv1']['values']=={'coordinate_index':1,'u_tiling':1.,'v_tiling':1.} and by['coverage-r']['class']=='MaterialExpressionComponentMask' and by['coverage-r']['values']=={'r':True,'g':False,'b':False,'a':False},'New UV1 mask channel differs')
    require(by['coverage-r']['inputs']==[['None',NODE_TAG+'uv1','']] and by['temporal-dither']['class']=='MaterialExpressionMaterialFunctionCall' and by['temporal-dither']['values']['material_function']=='/Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA.DitherTemporalAA','Native DitherTemporalAA source differs')
    alpha=[v for v in by['temporal-dither']['inputs']if 'alpha'in v[0].lower()]
    require(len(alpha)==1 and alpha[0][1:]==[NODE_TAG+'coverage-r',''] and all(v[1]is None for v in by['temporal-dither']['inputs']if v not in alpha),'Temporal dither coverage/random inputs differ')
    require(variant['roots']['OPACITY_MASK']==[NODE_TAG+'temporal-dither','Result'] and all(v==variant['roots'][k]for k,v in original['roots'].items()if k!='OPACITY_MASK'),'Existing PBR roots changed')
    require(variant['flags']['blend_mode']=='<BlendMode.BLEND_MASKED: 1>' and variant['flags']['opacity_mask_clip_value']==.5 and all(v==variant['flags'][k]for k,v in original['flags'].items()if k not in {'blend_mode','opacity_mask_clip_value'}),'Only new blend/opacity flags may differ')


def validate_actor_delta(before,expected,after,added):
    require(len(before)==5306 and len(added)==5 and len(set(added))==5 and not set(added)&set(before),'Closed original/additive actor inventory differs')
    require(set(expected)==set(after)==set(before)|set(added),'Unknown or missing actor in counterfactual')
    require(all(before[k]==expected[k]==after[k]for k in before),'Original actor/component policy or instance changed')
    require(expected==after,'Saved added actor differs from verified pre-save source counterfactual')


def validate_content_delta(before,after,assets):
    require(len(before)==3975 and len(assets)==5 and len(set(assets))==5 and all(v.startswith('Brezi/CanopyForeground20261002R21/')and v.endswith('.uasset')for v in assets),'Closed five-package namespace differs')
    require(set(after)==set(before)|set(assets),'Unknown/missing Content package or data')
    require(all(before[k]==after[k]for k in before if k!='Brezi/Maps/Brezi.umap'),'Original Content bytes changed beyond candidate map')
    require(before['Brezi/Maps/Brezi.umap']!=after['Brezi/Maps/Brezi.umap'],'Candidate map did not change')


def validate_clone(clone,base_rows,protected,base_project,project):
    require(clone['status']=='verified-byte-identical-independent-apfs-r21-project-clone-before-foreground-native'and clone['nativeExecuted']is False and clone['selectedPlan']==pin(STUDY/'foreground-transition-plan.json')and clone['baseNativeReport']==pin(base_project.parents[1]/'exterior-import-report.json'),'Typed fresh R21 independent clone provenance differs')
    require(clone['fileCount']==len(clone['files'])==len(base_rows)+protected['fileCount']==4107,'Clone full original file census differs')
    observed={}
    for row in clone['files']:
        source=Path(row['source']);destination=Path(row['destination'])
        require(source.is_relative_to(base_project)and destination.is_relative_to(project)and source.relative_to(base_project)==destination.relative_to(project)and row['independentInodes']is True,'Clone source/destination/independent ownership differs')
        relative=str(destination.relative_to(project));require(relative not in observed,'Duplicate clone file row');observed[relative]=row
        if relative.startswith('Content/'):
            require({k:row[k]for k in ('sha256','bytes')}==base_rows[relative[len('Content/'):]],'Clone Content original bytes differ')
        else:require(row==protected['files'][relative],'Clone protected original file differs')
    require(set(observed)=={'Content/'+p for p in base_rows}|set(protected['files']),'Clone file membership differs')
