"""New R35 source-only repair options on exact saved R32; no Unreal imports.

The original byte arrays are retained. Only two hard-mesh TEXCOORD_1.R arrays
and two explicit near-PBR graph expressions are proposed, with all application
and native freshness controls deferred to a new actual saved candidate.
"""
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode = True
from shapely.geometry import Point, shape
from shapely.ops import unary_union
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-repair-study-r35.py'
OUT = ROOT/'output/unreal/exterior-context-yard-20261002-r35-source-repair-proposal'
INPUTS = {}
BASE_SHA = '99b80074fe1309ee951ea662cf42f75ecd6d0a2bc711f0c76cc5d34e18891a19'
ATTR_SHA = 'f0ac8e38d58faa8409d5460b23888312d6ab20cc5b56d3ca5edcefc9b2e384fe'

def require(ok, message):
    if not ok: raise RuntimeError(message)
def sha(file): return hashlib.sha256(Path(file).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def pin(file, expected=None):
    p=Path(file).resolve();require(p.is_file() and not p.is_symlink(),'Actual original input required')
    h=sha(p);require(expected is None or h==expected,'Pinned input differs: '+str(p));INPUTS[str(p)]=h
    return {'path':str(p),'sha256':h,'bytes':p.stat().st_size}
def read(file): return json.loads(Path(file).read_text())
def checked(row):pin(row['path'],row['sha256']);return read(row['path'])
def f32(value):return struct.unpack('<f',struct.pack('<f',value))[0]
def smooth(value):
    t=max(0.,min(1.,value));return t*t*(3.-2.*t)
def write(file,value):Path(file).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def hard_unions(layout):
    by_yard={}
    for surface in layout['surfaces']:
        if surface['role'] in ('entry_walk','service_court'):
            by_yard.setdefault(surface['buildingSourceId'],[]).append(surface)
    require(len(by_yard)==3 and all(len(rows)==2 for rows in by_yard.values()),'Exactly three original hard unions required')
    return {key:unary_union([shape(row['domainCm'])for row in rows])for key,rows in by_yard.items()}

def proposed_uv_patch(mesh, layout):
    unions=hard_unions(layout);surfaces={row['id']:row for row in layout['surfaces']};coverage={};membership={}
    require(mesh['role'] in ('entry_walk','service_court'),'Hard material channel patch only')
    for row in mesh['sourceSurfaceRanges']:
        source_id=row['sourcePieceId'].replace('yard_ground_r32_','yard_r28_',1)
        surface=surfaces[source_id];union=unions[surface['buildingSourceId']]
        if 'domainCm' in row:require(shape(row['domainCm']).equals(shape(surface['domainCm'])),'Exact original hard footprint must remain unchanged')
        first=row['firstTriangle']*3;last=first+row['triangles']*3
        for index in set(mesh['indices'][first:last]):
            p=Point(mesh['verticesCm'][index][:2]);value=f32(smooth(p.distance(union.boundary)/6.))
            require(index not in coverage or coverage[index]==value,'Shared hard vertex has conflicting yard union')
            coverage[index]=value;membership[index]=surface['buildingSourceId']
    require(set(coverage)==set(range(len(mesh['verticesCm']))),'All original hard vertices must be covered once')
    original=[[f32(x),f32(y)]for x,y in mesh['uv1']];after=[[coverage[i],row[1]]for i,row in enumerate(original)]
    changed=[i for i,(a,b)in enumerate(zip(original,after))if struct.pack('<f',a[0])!=struct.pack('<f',b[0])]
    require(all(a[1]==b[1]for a,b in zip(original,after)),'Earth-fraction G must remain original F32')
    return {'meshId':mesh['id'],'role':mesh['role'],'sourceVertexCount':len(original),'sourceTriangles':len(mesh['indices'])//3,
        'originalUv1F32':original,'proposedUv1F32':after,'changedCoverageVertexIndices':changed,'changedCoverageVertices':len(changed),
        'sourcePieceBuildingByVertex':[membership[i]for i in range(len(original))],
        'allOtherGeometrySourceArraysSha256':{k:digest(mesh[k])for k in ('verticesCm','normals','uv0','indices')},
        'originalUv1F32Sha256':digest(original),'proposedUv1F32Sha256':digest(after),
        'coverageRule':'F32(smoothstep(0,6cm,distance(original per-yard entry_walk union service_court exterior boundary)))',
        'originalSharedRoleHeightOffsetsRetained':True,'sourcePositionFootprintDepthOrderUnchanged':True,'nativeDecoded':False}

def glb_channel_patch(source, patches):
    before=Path(source).read_bytes();after=bytearray(before)
    require(before[:4]==b'glTF' and struct.unpack_from('<I',before,4)[0]==2 and struct.unpack_from('<I',before,8)[0]==len(before),'Original GLB2 required')
    chunks={};at=12
    while at<len(before):
        length,kind=struct.unpack_from('<II',before,at);chunks[kind]=(at+8,length);at+=8+length
    jo,jl=chunks[0x4e4f534a];bo,bl=chunks[0x004e4942];j=json.loads(before[jo:jo+jl]);allow=set();rows=[]
    by_name={node['name']:node for node in j['nodes']};require(len(by_name)==3,'Original three ground nodes required')
    for patch in patches:
        node=by_name[patch['meshId']+'_LOD0'];mesh=j['meshes'][node['mesh']];require(len(mesh['primitives'])==1,'Original one primitive hard mesh required')
        attr=mesh['primitives'][0]['attributes'];a=j['accessors'][attr['TEXCOORD_1']];v=j['bufferViews'][a['bufferView']]
        require(a['componentType']==5126 and a['type']=='VEC2' and a['count']==patch['sourceVertexCount'] and not a.get('normalized',False) and 'sparse' not in a,'Original F32 UV1 required')
        start=bo+v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',8);require(stride>=8,'Original UV stride invalid')
        for i,(original,new)in enumerate(zip(patch['originalUv1F32'],patch['proposedUv1F32'])):
            offset=start+i*stride;require(struct.unpack_from('<ff',before,offset)==tuple(original),'Serialized R32 UV1 differs from pinned source proposal')
            after[offset:offset+4]=struct.pack('<f',new[0]);allow.update(range(offset,offset+4))
        rows.append({'sourceNode':node['name'],'uv1Accessor':attr['TEXCOORD_1'],'vertices':a['count'],'coverageVerticesChanged':patch['changedCoverageVertices']})
    changed=[i for i,(a,b)in enumerate(zip(before,after))if a!=b]
    require(changed and all(i in allow for i in changed),'Only exact two hard UV1.R byte ranges may change')
    return bytes(after),{'originalBytes':len(before),'proposedBytes':len(after),'changedByteCount':len(changed),'changedByteOffsetSha256':digest(changed),
        'allowedUv1CoverageByteRanges':rows,'allBytesOutsideTwoHardUv1RChannelsExact':True,'originalJsonHeaderAndAllGeometryBytesExact':True,
        'originalSubstrateEntireGeometryAndUv1Exact':True,'originalPositionsNormalsIndicesUv0Uv1GExact':True,'nativeInterchangeReimportProofPending':True}

def material_variant(graph):
    require(len(graph['nodes'])==58,'Actual original distant-terrain graph node census differs')
    wanted={'BreziExterior:near-terrain-pbr-color':('return lerp(Terrain,Scan,.30*Near);','return lerp(Terrain,Scan,.65*Near);'),
            'BreziExterior:near-terrain-normal-strength':('return .30*Near;','return .65*Near;')}
    result=copy.deepcopy(graph);seen=set()
    for node in result['nodes']:
        if node['role'] in wanted:
            old,new=wanted[node['role']];require(node['class']=='MaterialExpressionCustom' and node['values']['code']==old,'Actual saved near-PBR graph baseline differs')
            node['values']['code']=new;seen.add(node['role'])
    require(seen==set(wanted),'Exactly two actual near-PBR expressions required')
    restore=copy.deepcopy(result)
    for node in restore['nodes']:
        if node['role'] in wanted:node['values']['code']=wanted[node['role']][0]
    require(restore==graph,'No graph texture/route/world-position/color/camera-distance/flag delta permitted')
    return result,{'originalNodeCount':58,'newNodeCount':58,'changedExpressionRoles':sorted(wanted),
        'sourceRecipeNormalStrengthZeroIsNotTheSavedGraphNormalStrength':True,'actualSavedResponseCoefficient':.30,'proposedResponseCoefficient':.65,
        'albedoNearMixCoefficientChanged':True,'normalNearResponseCoefficientChanged':True,'newTextureObjects':0,'existingTextureMapsAndSettingsUnchanged':True,
        'originalAllOtherGraphNodesInputsRootsFlagsExact':True,'nativeCompileReadbackPending':True,'appearanceGainProven':False}

def main():
    require(not OUT.exists(),'New repair proposal directory only')
    attribution=checked(pin(ROOT/'output/unreal/exterior-context-yard-20261002-r35-source-diagnostic/source-attribution.json',ATTR_SHA))
    report=checked(attribution['actualNativeBase']);require(attribution['actualNativeBase']['sha256']==BASE_SHA and report['savedMapUnloadedReloaded'] is True,'Exact saved R32 only')
    layout=checked(pin(ROOT/'output/unreal/exterior-context-yard-20261002-r28-study/yard-layout.json','3ba5829cef341736b76a5bfce33eb961e919e7d9374ab9aed842bb2e85061ada'))
    study=checked(report['sourceStudy']);geometry=checked(study['proposal']);source_glb=pin(study['sourceGlb']['path'],study['sourceGlb']['sha256'])
    witness=checked(report['savedActorWitness']);controls=checked(report['originalControlsSaved'])
    # Completeness is an independent new source receipt, never inferred from the authored-radius diagnostic.
    complete_file=ROOT/'output/unreal/exterior-context-yard-20261002-r35-source-completeness-r1/source-completeness.json'
    require(complete_file.is_file(),'Actual independent decoded source completeness receipt required before final proposal')
    completeness=checked(pin(complete_file,'44b92bbd1eeecc38b3ebb3d068f419ed886d9ccbec045c44019de1d2a042ed98'))
    require(completeness['census']['completeSourceTriangleSupportCrossings']==34 and completeness['comparison']['newTriangleSupportCrossingsAdded']==[] and completeness['comparison']['priorTriangleSupportCrossingsRemoved']==[], 'Completeness root census must match selected34 or require a new reviewed proposal')
    require([(r['groupId'],r['selectedSourceIndices'])for r in completeness['affectedOriginalGroups']]==[(r['groupId'],r['selectedSourceIndices'])for r in attribution['affectedOriginalGroups']], 'Independent full decoded source retirement indices differ')
    r16=checked(pin(ROOT/'output/unreal/exterior-20261001-r16a/exterior-import-report.json','1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122'))
    original_material=r16['materials']['materials']['context_distant_terrain'];observed=controls['observedOldMaterials']['original56']['clean']['original']['graphs']['context_distant_terrain']
    require(observed['asset']==original_material['asset'] and observed['graphSha256']==original_material['graphSha256']=='81d9b113435b540529622640545fbe6b3745c4b9ec360fc740d0e737c0f88b7a','Current actual R32 material hash must bind historical full graph')
    variants=[]
    for mesh in geometry['meshes']:
        if mesh['role'] in ('entry_walk','service_court'):variants.append(proposed_uv_patch(mesh,layout))
    require(len(variants)==2,'Only two exact hard mesh channel variants permitted');patched,byte_proof=glb_channel_patch(source_glb['path'],variants)
    graph,graph_proof=material_variant(original_material['graph'])
    target=attribution['nearbyOriginalGround']['actualActor'];component=attribution['nearbyOriginalGround']['actualSavedComponent'];require(target.endswith('.StaticMeshActor_197') and component['path'].endswith('.StaticMeshComponent0'),'Only actual backdrop component197 permitted')
    require(component in witness[target]['components'] and component['materials']==[original_material['asset']],'Exact current target binding required')
    same=[{'actor':actor,'component':c['path']}for actor,row in witness.items()for c in row['components']if original_material['asset'] in c.get('materials',[])];require(len(same)==15,'Exact fifteen original material-bound components required')
    for role,row in original_material['recipe']['maps'].items():pin(row['path'],row['sha256'])
    pin(ROOT/'output/unreal/exterior-validation-20260930-r1/r32a-yard-close-r23-paired-review-r1.json','e881d024dada73ada9382bf1ad3f40d24cf114bf8499b4f89f4e601b7fcbd8c4')
    pin(__file__);OUT.mkdir();(OUT/'yard-hard-coverage-r35.glb').write_bytes(patched)
    write(OUT/'hard-uv1-coverage-variants.json',{'schema':'brezi-context-yard-hard-union-uv1-source-variants-r35','variants':variants,'sourceGlb':source_glb,'binaryChannelProof':byte_proof,'nativeApplied':False})
    write(OUT/'backdrop-near-pbr-graph-variant.json',{'schema':'brezi-single-backdrop-near-pbr-source-variant-r35','originalAsset':original_material['asset'],'originalGraphSha256':observed['graphSha256'],'originalFullGraph':original_material['graph'],'proposedGraph':graph,'proof':graph_proof,'originalRecipeSupplemental':original_material['recipe'],'actualCurrentR32Observation':observed,'nativeApplied':False})
    groups=attribution['affectedOriginalGroups'];require(len(groups)==8 and sum(len(g['selectedSourceIndices'])for g in groups)==34,'Exact selected34 retirement required')
    proposal={'schema':'brezi-context-yard-scoped-source-repair-proposal-r35','schemaVersion':1,'owner':OWNER,'status':'source-only-three-scoped-repair-options-on-exact-saved-r32-native-pending','createdAt':datetime.now(timezone.utc).isoformat(),
        'actualNativeBase':attribution['actualNativeBase'],'activeDesign':report['activeDesign'],'setbacksMm':report['setbacksMm'],'sourceAttribution':pin(ROOT/'output/unreal/exterior-context-yard-20261002-r35-source-diagnostic/source-attribution.json',ATTR_SHA),'decodedSourceCompleteness':pin(complete_file),
        'sourceCandidateSelection':'Root-reviewed three repairs remain individually measurable on new exact R32 clones; no saved repaired scene exists.',
        'repairAOriginalEcologyRetirements':{'exactSelectedOriginalRoots':attribution['selectedSourceRootCrossings'],'affectedGroups':groups,'retireRoots':34,'retainedAffectedGroupRoots':1919,'retainedAllOriginalEcologyRoots':24739,'projectedAfterNativeAppliedFullHismInstances':678197,'projectedCountsAreNotActualSavedMeasurement':True,
            'preserveAllRootPositionsAndTransformsElsewhere':True,'nativeFreshnessRequirements':['Actual source/native report/process0 and current Content/protected module closure before execution','Exact eight original actor/component/mesh/count/ordered-frame hashes before mutation','Fresh actual native per-target raw matrix and wrapped recovered transform bound to source XYZ/yaw/positive uniform scale','Full original sourceF32 threeLOD support recheck through actual saved matrices against unchanged hard domains before retiring whole clumps','Remove selected existing indices exactly once, descending RemoveAtSwap then reorder actual wrapped surviving SMData; no matrix/Transform reconstruction or seed setter','All1919 actual affected survivors raw matrices/order/mainseed/customdata exact before save and after reload; all unrelated components whole-witness exact'],
            'unavailableSeedRangesCannotBeInvented':True,'perInstanceShaderRandomPreservationNotProven':True,'alphaVisibleRootIdentityOrVisibleCensusProven':False},
        'repairBHardUnionCoverage':{'variant':pin(OUT/'hard-uv1-coverage-variants.json'),'sourceGlbVariant':pin(OUT/'yard-hard-coverage-r35.glb'),'binaryChannelProof':byte_proof,'unchangedUniqueHardTriangles':4519,'changedCoverageVertices':sum(v['changedCoverageVertices']for v in variants),'actualSourceDiagnosticConservativeInteriorWitnessVertices':555,
            'originalAll3MeshPositionsNormalsIndicesUv0Uv1GByteExact':True,'originalSubstrateByteExact':True,'originalSharedRoleHeightOffsetsRetained':True,'onlyNewNamespaceMeshesFuture':True,'sourcePatchChangesDitherCoverageNotPhysicalHeights':True,'isolatedNativePixelCausalityPending':True},
        'repairCSingleBackdropNearPbr':{'variant':pin(OUT/'backdrop-near-pbr-graph-variant.json'),'actualActor':target,'actualComponent':component['path'],'originalComponentWitness':component,'proposedEffectiveSlot':0,'proposedOwnedMaterialPrefix':'/Game/Brezi/ContextYardRepair20261002R35/Materials/','newGraphs':1,'newTextureObjects':0,'changedCustomExpressions':graph_proof,'unchangedOtherFourteenMaterialComponents':[v for v in same if v['actor']!=target],
            'wholeComponentReboundNotSmallSpatialOverlay':True,'unchangedMapsWorldUvTile200cmOrthophotoRoutesRoughnessAndSourcePixels':True,'noGlobal65GroundMaterialRewrite':True,'sourceElevationUnsureyed':True,'visibleAppearanceGainPending':True},
        'protectedScope':['C/B/B own architecture and both3000mm setbacks','All8949 original managed-lawn members and all78 grove roots','All13 current yard shrubs and current yard planting source domains','All unrelated transforms/rawmatrices/order/seeds/customdata/culls/materials/collision','ExistingR32/R34/R30/R29 history and separate garden provenance'],
        'futureGardenIntegration':{'R34FernOnlyNotAppliedHere':True,'R32ContainsUnacceptedR30TallHeroChange':True,'eventualGardenYardCombinationRequiresNewActualBaseAndIndependentCounterfactual':True},
        'limits':{'sourceSupportDoesNotEstablishAlphaPixelsOrRenderedVisibleIds':True,'newNativePerRootMatricesDecodedHere':False,'exactAllLODsNativeGeometryDecodedHere':False,'nativeFovMeasured':False,'nativeDitherPixelCausalityProven':False,'normalOrNearMixGainProven':False,'materialPackagesIndependentlyUnloaded':False},
        'inputFilesBefore':dict(INPUTS),'inputFilesAfter':dict(INPUTS),'sourceInputsUnchanged':True,'nativeBaseForRepairedScene':None,'nativeExecuted':False,'gpuExecuted':False,'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False}
    require(all(sha(p)==h for p,h in INPUTS.items()),'Source inputs changed before closure');write(OUT/'source-repair-proposal.json',proposal)
    print(json.dumps({'proposal':pin(OUT/'source-repair-proposal.json'),'retireRoots':34,'affectedGroups':8,'changedCoverageVertices':proposal['repairBHardUnionCoverage']['changedCoverageVertices'],'changedGlbBytes':byte_proof['changedByteCount'],'sourceOnly':True}))

if __name__=='__main__':main()
