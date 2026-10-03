"""Bounded source R35 attribution on actual saved R32, with no scene mutation.

Find original canopy-ecology source triangles crossing the existing hard yards,
then bind source group order to unchanged saved native component identities.
Source support intersections are not alpha-pixel visibility or new native poses.
"""
import collections
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode = True
import numpy as np
from shapely.geometry import Point, Polygon, LineString, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-attribution-r35.py'
OUTPUT = ROOT/'output/unreal/exterior-context-yard-20261002-r35-source-diagnostic'
INPUTS = {}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(file):
    return hashlib.sha256(Path(file).read_bytes()).hexdigest()


def pin(file, expected=None):
    file = Path(file).resolve()
    require(file.is_file() and file.is_relative_to(ROOT) and not file.is_symlink(), 'Actual owned input required')
    h = sha(file)
    require(expected is None or h == expected, 'Pinned input differs: '+str(file))
    INPUTS[str(file)] = h
    return {'path': str(file), 'sha256': h, 'bytes': file.stat().st_size}


def read_pin(row):
    pin(row['path'], row['sha256'])
    return json.loads(Path(row['path']).read_text())


def glb(path):
    data = Path(path).read_bytes()
    require(data[:4] == b'glTF' and struct.unpack_from('<I', data, 4)[0] == 2
        and struct.unpack_from('<I', data, 8)[0] == len(data), 'Original GLB2 required')
    chunks = {}; at = 12
    while at < len(data):
        length, kind = struct.unpack_from('<II', data, at)
        chunks[kind] = data[at+8:at+8+length]; at += 8+length
    j = json.loads(chunks[0x4e4f534a]); binary = chunks[0x004e4942]
    require(len(j['buffers']) == 1 and 'uri' not in j['buffers'][0], 'Embedded original binary required')
    def accessor(index):
        a = j['accessors'][index]; v = j['bufferViews'][a['bufferView']]
        require('sparse' not in a and not a.get('normalized', False), 'Unmodified dense source attributes required')
        sizes = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}
        dtype = {5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
        width = sizes[a['type']]; stride = v.get('byteStride', np.dtype(dtype).itemsize*width)
        start = v.get('byteOffset',0)+a.get('byteOffset',0)
        return np.ndarray((a['count'],width), dtype=dtype, buffer=binary, offset=start,
            strides=(stride,np.dtype(dtype).itemsize)).copy()
    result = {}
    for node in j['nodes']:
        if 'mesh' not in node:
            continue
        require(not any(k in node for k in ('matrix','translation','rotation','scale')), 'Authored GLB node transform cannot be ignored')
        parts=[]
        for primitive in j['meshes'][node['mesh']]['primitives']:
            require(primitive.get('mode',4)==4,'Original triangle primitive required')
            p = accessor(primitive['attributes']['POSITION']).astype(np.float64)[:,[0,2,1]]*100.
            ids=accessor(primitive['indices']).reshape(-1).astype(np.int64)
            require(len(ids)%3==0 and int(ids.max()) < len(p),'Actual original triangle indices differ')
            parts.append({'positionsCm':p,'indices':ids.reshape(-1,3)})
        result[node['name']]=parts
    return result


def projected_support(points):
    unique=list(dict.fromkeys(tuple(float(v)for v in p[:2])for p in points))
    if len(unique)==1:
        return Point(unique[0])
    polygon=Polygon(unique) if len(unique)>=3 else None
    return polygon if polygon is not None and polygon.area>0 else LineString(unique)


def source_intersections(group, index, row, decoded, surfaces):
    yaw=math.radians(row['yawDeg']);c,s=math.cos(yaw),math.sin(yaw)
    rotation=np.array([[c,s,0],[-s,c,0],[0,0,1]],dtype=np.float64)
    scale=np.array(row['scale'],dtype=np.float64);root=np.array(row['positionCm'],dtype=np.float64)
    lods=[];hit_ids=set();world_min=[math.inf]*3;world_max=[-math.inf]*3
    for level in range(3):
        node=group['meshId']+'_LOD'+str(level);require(node in decoded,'Actual complete three-LOD source node missing')
        triangles=points=hit_count=0;hits=collections.Counter();maximum_height=-math.inf
        for part in decoded[node]:
            world=(part['positionsCm']*scale)@rotation+root
            world_min=np.minimum(world_min,world.min(axis=0)).tolist();world_max=np.maximum(world_max,world.max(axis=0)).tolist()
            points+=len(world);maximum_height=max(maximum_height,float(world[:,2].max()))
            for face in part['indices']:
                tri=world[face];support=projected_support(tri);tri_hits=[]
                for surface,domain in surfaces:
                    if support.intersects(domain):
                        tri_hits.append(surface['id']);hits[surface['id']]+=1;hit_ids.add(surface['id'])
                hit_count+=bool(tri_hits);triangles+=1
        lods.append({'level':level,'decodedSourceVertices':points,'decodedSourceTriangles':triangles,
            'projectedTriangleSupportsIntersectingHardFootprints':hit_count,'hitsBySurface':dict(hits),
            'sourceMaximumWorldZCm':maximum_height})
    if not hit_ids:return None
    return {'groupId':group['id'],'sourceGroupInstanceIndex':index,'modelId':group['meshId'],
        'sourceFamily':row['ecologyFamily'],'sourceRoot':row,'sourceAllLodWorldBoundsCm':{'min':world_min,'max':world_max},
        'intersectingHardSurfaceIds':sorted(hit_ids),'sourceRootInsideHardFootprint':any(d.covers(Point(root[:2]))for _,d in surfaces),
        'allThreeSourceLodsDecoded':True,'lodIntersections':lods,
        'sourceLeafAlphaPixelsDecodedForIntersection':False,'exactRenderedVisibleRootIdentityClaimed':False,
        'freshNativePerInstanceRawMatrixDecodedHere':False}


def seam_witness(proposal):
    hard=[m for m in proposal['meshes']if m['role']in('entry_walk','service_court')]
    domains=[(m,r,shape(r['domainCm']))for m in hard for r in m['sourceSurfaceRanges']]
    union=unary_union([d for _,_,d in domains]);rows=[]
    for m,r,domain in domains:
        first=r['firstTriangle']*3;last=(r['firstTriangle']+r['triangles'])*3
        indices=m['indices'][first:last];used=sorted(set(indices));internal=[]
        for i in used:
            p=Point(m['verticesCm'][i][:2]);own=p.distance(domain.boundary);whole=p.distance(union.boundary)
            if union.covers(p) and whole>6.0 and m['uv1'][i][0]<.99:
                internal.append({'sourceVertexIndex':i,'xyCm':m['verticesCm'][i][:2],
                    'storedUV1CoverageR':m['uv1'][i][0],'ownDomainBoundaryDistanceCm':own,
                    'wholeHardUnionBoundaryDistanceCm':whole})
        rows.append({'meshId':m['id'],'sourcePieceId':r['sourcePieceId'],'hardFeatherCm':6,
            'internalToWholeHardUnionButFeatheredVertices':len(internal),'examples':internal[:12],
            'allInternalWitnessRowsSha256':hashlib.sha256(json.dumps(internal,sort_keys=True,separators=(',',':')).encode()).hexdigest()})
    return {'sourcePolicy':'Frozen R32 mesh() computes UV1.R from each separate role/piece domain boundary, not from the combined hard union.',
        'sourceInternalContourFeatherWitness':rows,'internalWitnessVertices':sum(r['internalToWholeHardUnionButFeatheredVertices']for r in rows),
        'proposedNextSourceChange':'On NEW source geometry, derive hard UV1.R from the union of entry_walk/service_court for each yard, preserving original footprint and all current F32 position/index topology. Keep feather only at external hard/soft boundary; preserve UV1.G earth-fraction routes.',
        'nativeDitherPixelsCausallyProvenHere':False,'appearanceRegressionAttribution':'Source coverage exposes underlying green within the combined hard domain; this explains a credible source cause of the observed inset outline. No isolated native counterfactual capture has yet proven pixel causality.'}


def main():
    require(not OUTPUT.exists(),'Fresh source diagnostic only')
    report=read_pin(pin(ROOT/'output/unreal/exterior-20261002-r32a/context-yard-ground-native-report.json',
        '99b80074fe1309ee951ea662cf42f75ecd6d0a2bc711f0c76cc5d34e18891a19'))
    witness=read_pin(report['savedActorWitness']);r16=read_pin(pin(ROOT/'output/unreal/exterior-20261001-r16a/exterior-import-report.json',
        '1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122'))
    ecology=read_pin(pin(ROOT/'output/unreal/exterior-canopy-ecology-20260930-r4/canopy-ecology-plan.json',
        '27d66e0032c3b8648e5c74f80dc675efb3bee0a4efde00a1549a4502cc86b576'))
    manifest=read_pin(ecology['geometryManifest']);layout=read_pin(pin(ROOT/'output/unreal/exterior-context-yard-20261002-r28-study/yard-layout.json',
        '3ba5829cef341736b76a5bfce33eb961e919e7d9374ab9aed842bb2e85061ada'))
    study=read_pin(report['sourceStudy']);proposal=read_pin(study['proposal']);pin(study['sourceGlb']['path'],study['sourceGlb']['sha256'])
    pin(ROOT/'output/unreal/exterior-validation-20260930-r1/r32a-yard-close-r23-paired-review-r1.json',
        'e881d024dada73ada9382bf1ad3f40d24cf114bf8499b4f89f4e601b7fcbd8c4')
    pin(__file__);hard=[(row,shape(row['domainCm']))for row in layout['surfaces']if row['role']in('entry_walk','service_court')]
    require(len(hard)==6 and len(ecology['groups'])==130 and sum(len(g['instances'])for g in ecology['groups'])==24773,'Original source scope differs')
    models={m['id']:m for m in manifest['meshes']};decoded={};candidates=selected_count=0;groups=[];selected=[];families=collections.Counter()
    for group in ecology['groups']:
        original=r16['geometry']['groups'][group['id']];actor=witness[original['actor']]
        components=[c for c in actor['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
        require(len(components)==1,'Unique actual ecology HISM required');component=components[0]
        require(component['mesh']==original['mesh'] and component['instanceCount']==original['instances']==len(group['instances'])
            and component['orderedInstanceTransformsSha256']==original['transformsSha256'],'Actual saved native ecology identity/order differs')
        selected_indices=[]
        for index,row in enumerate(group['instances']):
            root=Point(row['positionCm'][:2]);near=[(s,d)for s,d in hard if root.distance(d)<=row['radiusCm']]
            if not near:continue
            candidates+=1;model=models[group['meshId']];file=model['glbPath'];pin(file,model['glbSha256'])
            if file not in decoded:decoded[file]=glb(file)
            found=source_intersections(group,index,row,decoded[file],near)
            if found:
                found['actualNativeActor']=original['actor'];found['actualNativeComponent']=component['path']
                found['wholeSavedGroupOrderedTransformSha256']=component['orderedInstanceTransformsSha256']
                selected.append(found);selected_indices.append(index);selected_count+=1;families[row['ecologyFamily']]+=1
        if selected_indices:
            groups.append({'groupId':group['id'],'actor':original['actor'],'component':component['path'],'modelId':group['meshId'],
                'originalInstances':len(group['instances']),'selectedSourceIndices':selected_indices,
                'expectedRetainedSourceIndices':[i for i in range(len(group['instances']))if i not in set(selected_indices)],
                'originalSavedOrderedTransformsSha256':component['orderedInstanceTransformsSha256'],
                'currentVisible':component['visible'],'currentHiddenInGame':component['hiddenInGame'],
                'currentCullCm':component['instanceCullCm'],'actualNativeMaterials':component['materials'],
                'futureNativeRawMatrixSurvivalAndOrderProofRequired':True,'additionalRandomSeedRangesObserved':False})
    require(selected_count==len(selected)and selected_count>0,'Source crossing census empty or duplicated')
    backdrop_path=r16['geometry']['actors']['context_unresolved_flat_backdrop'];backdrop=witness[backdrop_path]
    backdrop_component=[c for c in backdrop['components']if c.get('mesh')==r16['geometry']['meshes']['context_unresolved_flat_backdrop']]
    require(len(backdrop_component)==1 and backdrop_component[0]['materials']==[r16['materials']['materials']['context_distant_terrain']['asset']],
        'Actual nearby source floor/material differs')
    existing_r21=ROOT/'output/unreal/exterior-canopy-foreground-20261001-r21-study/foreground-root-groups.json';r21=read_pin(pin(existing_r21))
    r21roots=[i['positionCm']for g in r21['groups'] for i in g['instances']]
    require(len(r21roots)==512,'Original R21 source census differs')
    r21bounds={'min':[min(p[k]for p in r21roots)for k in range(3)],'max':[max(p[k]for p in r21roots)for k in range(3)]}
    result={'schema':'brezi-context-yard-source-attribution-r35','owner':OWNER,
        'status':'source-diagnosed-hardcourt-ecology-support-and-internal-uv-feather-native-pending',
        'createdAt':datetime.now(timezone.utc).isoformat(),'actualNativeBase':pin(ROOT/'output/unreal/exterior-20261002-r32a/context-yard-ground-native-report.json'),
        'activeDesign':report['activeDesign'],'setbacksMm':report['setbacksMm'],
        'nearbyOriginalGround':{'sourceMeshId':'context_unresolved_flat_backdrop','actualActor':backdrop_path,
            'actualSavedComponent':backdrop_component[0],'sourceElevationCm':-25,'measuredElevation':False,
            'isContinuous65UnbuiltGroundMaterial':False},
        'originalEcologySourceCensus':{'groups':130,'roots':24773,'circleCandidatesNearSixHardSurfaces':candidates,
            'sourceFullThreeLodTriangleSupportCrossings':selected_count,'affectedGroups':len(groups),'perFamily':dict(families),
            'allOriginalEcologyGroupCountsMeshesAndOrderedNativeHashesUnchangedFromR16':True},
        'selectedSourceRootCrossings':selected,'affectedOriginalGroups':groups,'sourceHardSurfaceIds':[s['id']for s,_ in hard],
        'r21NewForegroundRootSourceBoundsCm':r21bounds,'r21SourceRootsInFirstHardYard':sum(any(d.covers(Point(p[:2]))for _,d in hard)for p in r21roots),
        'sourceFirstYardClumpsMustNotBeCalledR21New512WithoutEvidence':True,
        'hardSurfaceInternalFeatherDiagnosis':seam_witness(proposal),
        'narrowFutureNativeScope':['Retire only selected original canopy-ecology source member indices crossing unchanged six hard footprints; preserve all other root XYZ/rotations/scales and raw survivor matrices/order with actual native proof.',
            'No RemoveAtSwap survivor reconstruction; filter/reorder wrapped actual surviving SMData, retain main seed/custom data, report unavailable AdditionalRandomSeeds truthfully.',
            'Replace only hard-floor UV1.R on NEW namespace meshes using per-yard combined hard union; retain current F32 positions/indices/UV0/UV1.G/source footprint and native full-corner/depth proof.',
            'Scope any later nearby ground material pilot to actual context_unresolved_flat_backdrop component/material after root review; no global65-binding rewrite.'],
        'protectedScope':['Own C/B/B architecture and both3000mm setbacks','8949 original managed-lawn members','78 grove tree roots','All unrelated plant/root matrices/materials/culls/collision and current thirteen yard shrubs'],
        'limitations':{'supportIntersectionsAreSourceGeometryNotAlphaVisibleCoverage':True,
            'projectedTriangleSupportsDoNotEstablishRenderedPixelIdentityOrVisibility':True,
            'existingNativeWholeGroupHashesBindOriginalOrderButNotFreshPerRootRawMatrices':True,
            'futureNativeSurvivorMatrixMainSeedCustomDataProofRequired':True,
            'additionalRandomSeedRangesObserved':False,'perInstanceShaderRandomValuePreservationProven':False,
            'currentCameraVisibleBadPlantCountEstablished':False,'nativeDitherPixelCausalityEstablished':False},
        'inputFilesBefore':dict(INPUTS),'inputFilesAfter':dict(INPUTS),'sourceInputsUnchanged':True,
        'nativeApplied':False,'nativeExecuted':False,'gpuExecuted':False,'nativeAppearanceAccepted':False,
        'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False}
    require(all(sha(p)==h for p,h in INPUTS.items()),'Bounded source input changed')
    OUTPUT.mkdir();Path(OUTPUT/'source-attribution.json').write_text(json.dumps(result,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'receipt':pin(OUTPUT/'source-attribution.json'),'selectedSourceCrossings':selected_count,
        'groups':len(groups),'perFamily':dict(families),'internalCoverageVertices':result['hardSurfaceInternalFeatherDiagnosis']['internalWitnessVertices']}))


if __name__=='__main__':main()
