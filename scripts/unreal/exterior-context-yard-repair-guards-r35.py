"""Stdlib source and full-scene counterfactual for three bounded R35 repairs.

Fresh native controls are supplied by the owned native writer. This module
never constructs survivor transforms, seeds, or unavailable random ranges.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-repair-guards-r35.py'
NATIVE_OWNER = 'scripts/unreal/exterior-context-yard-repair-native-r35.py'
SCHEMA = 'brezi-context-yard-scoped-repair-native-r35'
STATUS = 'verified-saved-scoped-hardcourt-ecology-coverage-near-pbr-repair'
PREFIX = '/Game/Brezi/ContextYardRepair20261002R35'
TAG = 'BreziContextYardRepairR35'
MATERIAL = PREFIX+'/Materials/M_backdrop_near_pbr_r35.M_backdrop_near_pbr_r35'
BASE = ROOT/'output/unreal/exterior-20261002-r32a'
CANDIDATE = ROOT/'output/unreal/exterior-20261002-r35a'
PROPOSAL = ROOT/'output/unreal/exterior-context-yard-20261002-r35-source-repair-proposal/source-repair-proposal.json'
PROPOSAL_SHA = '1abfb6c418efa64de951b1e1da2862aaab0b2145342a21052a51c4627abd41e4'
BASE_SHA = '99b80074fe1309ee951ea662cf42f75ecd6d0a2bc711f0c76cc5d34e18891a19'
COMPLETE_SHA = '44b92bbd1eeecc38b3ebb3d068f419ed886d9ccbec045c44019de1d2a042ed98'
COUNTS = {'originalActors':5360,'savedActors':5360,'fullHismComponents':2321,'fullHismInstances':678197,
          'originalEcologyRootsRetired':34,'affectedOriginalEcologyGroups':8,'retainedAffectedOriginalEcologyRoots':1919,
          'originalEcologyRootsRetained':24739,'reboundHardGroundComponents':2,'reboundBackdropMaterialComponents':1,'newMeshAssets':2,
          'newMaterialGraphs':1,'newTextureObjects':0,'newPipelineAssets':3,'newPackages':6,
          'uniqueHardMeshTriangles':4519,'scopedMaterialGraphs':64,'scopedTextureObjects':95,'contentFiles':4092,'protectedFiles':132}


def require(value, reason):
    if not value: raise RuntimeError(reason)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def pin(path):
    path=Path(path).resolve();require(path.is_file() and not path.is_symlink(),'Actual owned source file required')
    return {'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size}
def check_pin(row):
    path=Path(row['path']);actual=pin(path)
    require(path.is_absolute() and set(row) in ({'path','sha256'},{'path','sha256','bytes'})
            and all(actual[k]==v for k,v in row.items()),'Pinned source file differs');return path
def checked(row): return read(check_pin(row))
def f32(value): return struct.unpack('<f',struct.pack('<f',value))[0]
def write(path,value):
    with Path(path).open('x') as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')
def module(name,path):
    path=Path(path);path=path if path.is_absolute() else ROOT/'scripts/unreal'/path
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def binary64(values):
    if isinstance(values,(list,tuple)):return b''.join(binary64(v)for v in values)
    require(type(values) in (float,int) and math.isfinite(values),'Finite numeric measured frame required')
    return struct.pack('<d',values)
def exact(actual,expected,message='Binary64 measured frames differ'):require(binary64(actual)==binary64(expected),message)


def swap_remove_order(count,remove):
    require(type(count) is int and count>0 and isinstance(remove,list) and remove==sorted(set(remove))
            and all(type(i) is int and 0<=i<count for i in remove),'Unique sorted original indices required')
    order=list(range(count))
    for i in reversed(remove):order[i]=order[-1];order.pop()
    return order


def expected_control(control,remove):
    n=control['instanceCount'];swap_remove_order(n,remove)
    require(control['numCustomDataFloats']==0 and control['customData']==[],'Reviewed zero custom-data semantics required')
    require(control['additionalRandomSeedsReadbackAvailable'] is False and control['seedRangesReconstructed'] is False,
            'Unavailable additional random ranges must not be inferred')
    require(all(len(control[k])==n for k in ('rootIds','sourceRootIndices','recoveredValues','storedMatrices')),'Full raw control arrays required')
    keep=[i for i in range(n) if i not in remove];result=copy.deepcopy(control)
    for key in ('rootIds','sourceRootIndices','recoveredValues','storedMatrices'):result[key]=[control[key][i]for i in keep]
    result['instanceCount']=len(keep)
    return result


def component(witness,name):
    rows=[c for c in witness['components'] if c['name']==name or c.get('path')==name]
    require(len(rows)==1,'Exactly one named original component required');return rows[0]
def cyclic(face):return min(tuple(face[i:]+face[:i])for i in range(3))


def validate_coverage_bytes(coverage,source_glb,variant_glb):
    before=Path(source_glb).read_bytes();proposed=Path(variant_glb).read_bytes();expected=bytearray(before)
    require(before[:4]==b'glTF' and struct.unpack_from('<II',before,4)==(2,len(before)) and len(proposed)==len(before),'Original equal-size GLB2 required')
    chunks={};at=12
    while at<len(before):
        n,k=struct.unpack_from('<II',before,at);require(k not in chunks and at+8+n<=len(before),'Original GLB extent differs')
        chunks[k]=(at+8,n);at+=8+n
    require(at==len(before),'Original GLB length differs')
    jo,jl=chunks[0x4e4f534a];bo,bl=chunks[0x004e4942];doc=json.loads(before[jo:jo+jl]);nodes={n['name']:n for n in doc['nodes']}
    require(len(nodes)==3 and len(coverage['variants'])==2,'Exactly original three nodes and two hard variants required')
    rows=[];allowed=set();changed_vertices=0
    for patch in coverage['variants']:
        node=nodes[patch['meshId']+'_LOD0'];parts=doc['meshes'][node['mesh']]['primitives'];require(len(parts)==1,'Original single hard section required')
        index=parts[0]['attributes']['TEXCOORD_1'];a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']]
        require(a['componentType']==5126 and a['type']=='VEC2' and a['count']==patch['sourceVertexCount'] and v['buffer']==0
                and 'sparse' not in a and not a.get('normalized',False),'Original dense source F32 UV1 required')
        start=bo+v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',8)
        require(stride>=8 and start+(a['count']-1)*stride+8<=bo+bl and len(patch['originalUv1F32'])==len(patch['proposedUv1F32'])==a['count'],'UV1 accessor/serialized variant extent differs')
        changed=[]
        for i,(old,new)in enumerate(zip(patch['originalUv1F32'],patch['proposedUv1F32'])):
            offset=start+i*stride;require(len(old)==len(new)==2 and struct.pack('<ff',*old)==before[offset:offset+8]
                and struct.pack('<f',old[1])==struct.pack('<f',new[1]) and all(math.isfinite(x)for x in old+new)
                and 0<=new[0]<=1,'Only serialized hard source coverage R may change; original G is exact')
            raw=struct.pack('<f',new[0]);expected[offset:offset+4]=raw;allowed.update(range(offset,offset+4))
            if raw!=before[offset:offset+4]:changed.append(i)
        require(changed==patch['changedCoverageVertexIndices'] and len(changed)==patch['changedCoverageVertices'],'Serialized changed coverage vertex census differs')
        changed_vertices+=len(changed)
        rows.append({'sourceNode':node['name'],'uv1Accessor':index,'vertices':a['count'],'coverageVerticesChanged':len(changed)})
    differences=[i for i,(a,b)in enumerate(zip(before,expected))if a!=b];proof=coverage['binaryChannelProof']
    require(bytes(expected)==proposed and all(i in allowed for i in differences),'Any byte changed outside exact two hard UV1.R channels')
    require(proof['originalBytes']==proof['proposedBytes']==len(before) and proof['changedByteCount']==len(differences)
        and proof['changedByteOffsetSha256']==digest(differences) and proof['allowedUv1CoverageByteRanges']==rows
        and proof['allBytesOutsideTwoHardUv1RChannelsExact'] is True and changed_vertices==628,'Exact frozen byte-only coverage proof differs')
    return True


def validate_graph_variant(variant):
    original=variant['originalFullGraph'];proposed=variant['proposedGraph'];restore=copy.deepcopy(proposed)
    require(len(original['nodes'])==len(proposed['nodes'])==58,'Exact full58-node source graph required')
    wanted={'BreziExterior:near-terrain-pbr-color':('return lerp(Terrain,Scan,.30*Near);','return lerp(Terrain,Scan,.65*Near);'),
            'BreziExterior:near-terrain-normal-strength':('return .30*Near;','return .65*Near;')};seen=set()
    for old,new,back in zip(original['nodes'],proposed['nodes'],restore['nodes']):
        if old['role'] in wanted:
            a,b=wanted[old['role']];require(old['class']==new['class']=='MaterialExpressionCustom' and old['values']['code']==a and new['values']['code']==b,'Exact two proposed source response codes required')
            back['values']['code']=a;seen.add(old['role'])
    require(seen==set(wanted) and restore==original and variant['proof']['changedExpressionRoles']==sorted(wanted)
            and variant['proof']['actualSavedResponseCoefficient']==.30 and variant['proof']['proposedResponseCoefficient']==.65,'No graph route/texture/flag/node change outside exact two Custom codes permitted')
    return True


def decode_ecology(path,wanted):
    data=Path(path).read_bytes();require(data[:4]==b'glTF' and struct.unpack_from('<II',data,4)==(2,len(data)),'Original GLB2 required')
    chunks={};at=12
    while at<len(data):
        n,k=struct.unpack_from('<II',data,at);require(k not in chunks and at+8+n<=len(data),'Invalid GLB chunk')
        chunks[k]=data[at+8:at+8+n];at+=8+n
    require(at==len(data),'GLB extent differs');j=json.loads(chunks[0x4e4f534a]);b=chunks[0x004e4942]
    require(len(j['buffers'])==1 and 'uri' not in j['buffers'][0] and all(not n.get('children') for n in j['nodes']),'Flat original embedded source required')
    def array(i):
        a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        fmt={5126:'f',5125:'I',5123:'H',5121:'B'}[a['componentType']];width=struct.calcsize('<'+fmt)*size
        require('sparse' not in a and not a.get('normalized',False) and v['buffer']==0 and a['count']>0,'Dense original attributes required')
        stride=v.get('byteStride',width);start=v.get('byteOffset',0)+a.get('byteOffset',0)
        require(stride>=width and start+(a['count']-1)*stride+width<=len(b),'Accessor range differs')
        return [list(struct.unpack_from('<'+fmt*size,b,start+i*stride))for i in range(a['count'])]
    result={key:{'id':key,'lods':[]}for key in wanted}
    nodes={n['name']:n for n in j['nodes'] if 'mesh' in n};require(len(nodes)==len([n for n in j['nodes']if 'mesh'in n]),'Duplicate source node name')
    for key in wanted:
        for level in range(3):
            node=nodes[key+'_LOD'+str(level)];require(not any(k in node for k in ('matrix','translation','rotation','scale')),'Node basis must remain original')
            parts=[]
            for p in j['meshes'][node['mesh']]['primitives']:
                require(p.get('mode',4)==4,'Original indexed triangles required')
                a=p['attributes'];positions=array(a['POSITION']);uv0=array(a['TEXCOORD_0']);uv1=array(a['TEXCOORD_1']);ids=[v[0]for v in array(p['indices'])]
                require(len(positions)==len(uv0)==len(uv1) and len(ids)%3==0 and all(type(i)is int and 0<=i<len(positions)for i in ids),'Full original attributes/index topology required')
                points=[[f32(100*v[0]),f32(100*v[2]),f32(100*v[1])]for v in positions]
                require(all(math.isfinite(x)for v in points+uv0+uv1 for x in v),'Finite source F32 required')
                parts.append({'positionsCm':points,'uv0':uv0,'uv1':uv1,'indices':ids,'triangles':len(ids)//3,
                              'materialIndex':p['material'],'materialName':j['materials'][p['material']]['name']})
            result[key]['lods'].append({'level':level,'parts':parts,'triangles':sum(p['triangles']for p in parts),'vertices':sum(len(p['positionsCm'])for p in parts)})
    return result


def validate_source():
    require(sha(PROPOSAL)==PROPOSAL_SHA,'Frozen three-scope source proposal differs');proposal=read(PROPOSAL)
    require(proposal['schema']=='brezi-context-yard-scoped-source-repair-proposal-r35' and proposal['schemaVersion']==1
            and proposal['nativeBaseForRepairedScene'] is None and all(proposal[k] is False for k in
            ('nativeApplied','nativeExecuted','gpuExecuted','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified')),
            'Only frozen source-only repair proposal accepted')
    complete=checked(proposal['decodedSourceCompleteness'])
    require(proposal['decodedSourceCompleteness']['sha256']==COMPLETE_SHA and complete['census']['completeSourceTriangleSupportCrossings']==34
            and complete['census']['fullModelAabbRootCandidates']==49 and complete['comparison']['newTriangleSupportCrossingsAdded']==[]
            and complete['comparison']['priorTriangleSupportCrossingsRemoved']==[],'Full geometry candidate completeness differs')
    require(proposal['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'} and proposal['setbacksMm']=={'street':3000,'east':3000},'Protected active design differs')
    for path,h in proposal['inputFilesBefore'].items():require(sha(path)==h,'Frozen source proposal input differs')
    require(proposal['inputFilesBefore']==proposal['inputFilesAfter'] and proposal['sourceInputsUnchanged'] is True,'Frozen source closure differs')
    report=checked(proposal['actualNativeBase']);require(proposal['actualNativeBase']['sha256']==BASE_SHA
            and report['nativeProcessId']==5443 and report['owner']=='scripts/unreal/exterior-context-yard-ground-native-r32.py'
            and report['status']=='verified-saved-resolved-context-yard-ground-and-low-detail'
            and report['nativeApplied'] is report['savedMapUnloadedReloaded'] is report['sourceInputsUnchanged'] is True,'Actual successful saved R32 required')
    terminal_path=BASE/'context-yard-ground-native-process.json';terminal=read(terminal_path);process=checked({'path':terminal['processFile'],'sha256':terminal['processFileSha256'],'bytes':Path(terminal['processFile']).stat().st_size})
    require(terminal['reportSha256']==BASE_SHA and process['pid']==5443 and process['code']==0 and process['signal'] is None
            and terminal['sourcePinsUnchangedAfterNative'] is True and len(terminal['sourcePinsBeforeNative'])==531,'Actual successful closed R32 process required')
    audit_path=BASE/'root-native-byte-audit-r32a.json';require(sha(audit_path)=='5be46410d8abed8630ab5a706fd447dc69b2f4568de6d270b18520fde8978906','Actual R32 byte audit differs')
    native=module('r35_frozen_saved_r32_native','exterior-context-yard-ground-native-r32.py')
    source_plan,source_bundle=native.guard.validate_plan();pf=checked(report['sourcePreflight'])
    checker_path=ROOT/'scripts/unreal/exterior-context-yard-ground-editor-check-r22.py'
    require(sha(checker_path)=='731b30a47943ec31d882d72ba07c29bf6580c2414f11b63b03a31869ce912277','Frozen actual R32 checker differs')
    checker=module('r35_frozen_saved_r32_checker',checker_path)
    # The Editor checker consumes the independently decoded source-study bundle,
    # while native helpers require the separately validated native-plan bundle.
    checker_bundle=checker.g.load_source()
    base_proof=checker.validate_saved(report,source_plan,checker_bundle,pf)
    witness=checked(report['savedActorWitness']);content=checked(report['afterContentInventory']);protected=checked(report['protectedProjectProof'])
    require(len(witness)==5360 and len(content)==4086 and len(protected)==132,'Actual R32 full source/witness census differs')
    base={'report':report,'witness':witness,'content':content,'protected':protected,'project':BASE/'Project/BreziTwin',
          'reportPin':proposal['actualNativeBase'],'process':{'pid':5443,'receipt':pin(terminal_path),'raw':pin(terminal['processFile']),'log':pin(terminal['logFile'])},
          'audit':pin(audit_path),'native':native,'sourceBundle':source_bundle,'sourcePlan':source_plan,'sourcePreflight':pf,'independentSavedProof':base_proof}
    ecology_path=ROOT/'output/unreal/exterior-canopy-ecology-20260930-r4/canopy-ecology-plan.json'
    require(sha(ecology_path)=='27d66e0032c3b8648e5c74f80dc675efb3bee0a4efde00a1549a4502cc86b576','Frozen ecology source differs')
    ecology=read(ecology_path);all_groups={g['id']:g for g in ecology['groups']};groups={}
    r16_path=ROOT/'output/unreal/exterior-20261001-r16a/exterior-import-report.json'
    require(sha(r16_path)=='1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122','Original saved native ecology source differs')
    r16=read(r16_path)
    selected=proposal['repairAOriginalEcologyRetirements']['affectedGroups']
    require([(g['groupId'],g['selectedSourceIndices'])for g in selected]==[(g['groupId'],g['selectedSourceIndices'])for g in complete['affectedOriginalGroups']], 'Exact complete source retirement indices differ')
    for row in selected:
        source=all_groups[row['groupId']];old=witness[row['actor']];c=component(old,row['component']);indices=row['selectedSourceIndices']
        swap_remove_order(len(source['instances']),indices)
        require(c['mesh']==r16['geometry']['groups'][row['groupId']]['mesh'] and c['instanceCount']==row['originalInstances']==len(source['instances']),'Current original ecology source mesh/count differs')
        require(c['orderedInstanceTransformsSha256']==row['originalSavedOrderedTransformsSha256'],'Exact original ecology native order differs')
        groups[row['groupId']]={**row,'sourceRows':source['instances'],'originalWitness':old,'mesh':c['mesh'],'componentName':c['name']}
    require(len(groups)==8 and sum(len(g['selectedSourceIndices'])for g in groups.values())==34
            and sum(g['originalInstances'] for g in groups.values())-34==1919,'Only exact eight component/34 member filters allowed')
    manifest=checked(ecology['geometryManifest']);models={m['id']:m for m in manifest['meshes']};wanted={g['modelId']for g in groups.values()}
    paths={}
    for key in wanted:paths.setdefault(str(check_pin({'path':models[key]['glbPath'],'sha256':models[key]['glbSha256'],'bytes':Path(models[key]['glbPath']).stat().st_size})),set()).add(key)
    decoded={}
    for path,keys in paths.items():decoded.update(decode_ecology(path,keys))
    coverage=checked(proposal['repairBHardUnionCoverage']['variant']);glb=check_pin(proposal['repairBHardUnionCoverage']['sourceGlbVariant'])
    require(coverage['binaryChannelProof']==proposal['repairBHardUnionCoverage']['binaryChannelProof']
            and coverage['binaryChannelProof']['allBytesOutsideTwoHardUv1RChannelsExact'] is True,'Only hard UV1.R source patch allowed')
    # Union-distance math was executed by frozen source CPU tooling. Native
    # validation consumes those serialized F32 values and independently proves
    # the exact channel-only bytes; it does not import or recompute Shapely.
    layout_path=ROOT/'output/unreal/exterior-context-yard-20261002-r28-study/yard-layout.json';layout=read(layout_path)
    original=checked(source_bundle['source']['plan']['proposal'])
    floors={m['id']:m for m in original['meshes']if m['role'] in ('entry_walk','service_court')}
    source_study=checked(report['sourceStudy']);source_glb=check_pin(source_study['sourceGlb'])
    validate_coverage_bytes(coverage,source_glb,glb)
    require({v['meshId']for v in coverage['variants']}==set(floors),'Only two original hard mesh variants required')
    for v in coverage['variants']:
        require(v['allOtherGeometrySourceArraysSha256']=={k:digest(floors[v['meshId']][k])for k in ('verticesCm','normals','uv0','indices')},'Original complete hard source geometry arrays differ')
    floor_records={v['meshId']:{**floors[v['meshId']],'uv1':v['proposedUv1F32']}for v in coverage['variants']};targets={}
    for key,row in floor_records.items():
        target=report['targets'][row['role']];c=component(witness[target['actor']],target['component'])
        require(c['mesh']==report['newMeshes'][key] and len(c['materials'])==1,'Actual hard floor source/mesh slot differs')
        targets[key]={**target,'componentName':c['name'],'currentMesh':c['mesh'],'currentMaterials':c['materials'],'currentOverrides':c['overrideMaterials'],'witness':witness[target['actor']]}
    variant=checked(proposal['repairCSingleBackdropNearPbr']['variant']);validate_graph_variant(variant)
    old_materials=checked(report['originalControlsSaved'])['observedOldMaterials']['original56']['clean']['original']
    require(old_materials['graphs']['context_distant_terrain']['graphSha256']==variant['originalGraphSha256'],'Actual full original terrain graph binding differs')
    textures={v['asset']:v for v in old_materials['textures'].values()}
    references={n['values']['texture']for n in variant['originalFullGraph']['nodes']if n['values'].get('texture')}
    require(references<=set(textures),'All original shared graph texture objects must remain observed')
    return {'proposal':proposal,'base':base,'ecologyGroups':groups,'ecologySourceModels':decoded,'floorRecords':floor_records,
            'floorTargets':targets,'materialVariant':variant,'materialSharedTextures':{a:textures[a]for a in references},
            'backdropTarget':proposal['repairCSingleBackdropNearPbr'],
            'hardFootprints':{s['id']:s['domainCm']for s in layout['surfaces']if s['role']in ('entry_walk','service_court')},
            'completeness':complete,'sourceGeometryVariant':proposal['repairBHardUnionCoverage']['sourceGlbVariant']}


def validate_native_controls(control,group,bundle):
    require(control['groupId']==group['groupId'] and control['actor']==group['actor'] and control['component']==group['component']
            and control['mesh']==group['mesh'] and control['instanceCount']==group['originalInstances'],'Fresh original native control identity differs')
    n=control['instanceCount'];require(control['sourceRootIndices']==list(range(n))
            and control['rootIds']==[group['groupId']+':'+str(i) for i in range(n)]
            and len(control['recoveredValues'])==len(control['storedMatrices'])==len(control['rootIds'])==n,'Full original source order/raw arrays required')
    require(digest(control['recoveredValues'])==group['originalSavedOrderedTransformsSha256'],'Fresh native recovered order no longer equals actual saved group')
    expected_control(control,group['selectedSourceIndices'])
    for source,recovered,matrix in zip(group['sourceRows'],control['recoveredValues'],control['storedMatrices']):
        require(len(recovered)==3 and list(map(len,recovered))==[3,4,3] and len(matrix)==4 and all(len(p)==4 for p in matrix),'Measured native frame layout differs')
        binary64(recovered);binary64(matrix);exact(recovered[0],source['positionCm'],'Actual source root XYZ differs');exact(matrix[3][:3],source['positionCm'],'Actual raw source translation differs')
        require(min(recovered[2])>0,'Positive original native scale required')
    return True


def _cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def _on_segment(p,a,b):return _cross(a,b,p)==0 and min(a[0],b[0])<=p[0]<=max(a[0],b[0]) and min(a[1],b[1])<=p[1]<=max(a[1],b[1])
def _segments(a,b,c,d):
    aa,bb,cc,dd=_cross(a,b,c),_cross(a,b,d),_cross(c,d,a),_cross(c,d,b)
    return ((aa>0)!=(bb>0) and (cc>0)!=(dd>0)) or _on_segment(c,a,b) or _on_segment(d,a,b) or _on_segment(a,c,d) or _on_segment(b,c,d)
def _ring_point(p,ring):
    inside=False
    for a,b in zip(ring,ring[1:]):
        if _on_segment(p,a,b):return 0
        if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return 1 if inside else -1
def _polygon_point(p,rings):
    outer=_ring_point(p,rings[0])
    if outer<=0:return outer==0
    for ring in rings[1:]:
        hole=_ring_point(p,ring)
        if hole==0:return True
        if hole==1:return False
    return True
def _triangle_point(p,tri):
    if _cross(*tri)==0:return False
    values=[_cross(tri[i],tri[(i+1)%3],p)for i in range(3)]
    return all(v>=0 for v in values) or all(v<=0 for v in values)
def source_support_intersects(triangle,domain):
    require(len(triangle)==3 and all(len(p)>=2 and all(math.isfinite(v)for v in p)for p in triangle),'Finite source triangle required')
    require(domain['type'] in ('Polygon','MultiPolygon'),'Exact polygon hard domain required')
    polygons=[domain['coordinates']] if domain['type']=='Polygon' else domain['coordinates']
    tri=[p[:2]for p in triangle]
    for rings in polygons:
        require(rings and all(len(r)>3 and r[0]==r[-1]for r in rings),'Closed hard source rings required')
        if any(_polygon_point(p,rings)for p in tri):return True
        if any(_triangle_point(p,tri)for ring in rings for p in ring[:-1]):return True
        if any(_segments(tri[i],tri[(i+1)%3],a,b)for i in range(3)for ring in rings for a,b in zip(ring,ring[1:])):return True
    return False


def native_support_checks(control,group,bundle):
    """Full source FLOAT support through freshly read actual stored matrices.

    This is not native alpha visibility or fresh normals/tangent evidence. All
    three actual source LODs participate even if only one has a hard crossing.
    """
    validate_native_controls(control,group,bundle);model=bundle['ecologySourceModels'][group['modelId']];result=[]
    for index in group['selectedSourceIndices']:
        matrix=control['storedMatrices'][index];levels=[];hits=set()
        for lod in model['lods']:
            counts={};vertices=triangles=0
            for part in lod['parts']:
                world=[[sum(p[j]*matrix[j][axis]for j in range(3))+matrix[3][axis]for axis in range(3)]for p in part['positionsCm']]
                vertices+=len(world)
                for at in range(0,len(part['indices']),3):
                    triangle=[world[i]for i in part['indices'][at:at+3]];triangles+=1
                    for identity,domain in bundle['hardFootprints'].items():
                        if source_support_intersects(triangle,domain):counts[identity]=counts.get(identity,0)+1;hits.add(identity)
            levels.append({'level':lod['level'],'sourceVertices':vertices,'sourceTriangles':triangles,'intersectingTriangleSupportsByHardSurface':counts})
        require(hits,'Selected authored crossing no longer intersects any hard domain through actual native matrix')
        result.append({'groupId':group['groupId'],'sourceGroupInstanceIndex':index,'rootId':control['rootIds'][index],
                       'actualStoredMatrix':matrix,'sourceModelId':group['modelId'],'allThreeSourceLodsChecked':True,
                       'intersectingHardSurfaceIds':sorted(hits),'lods':levels,'alphaVisiblePixelIdentityClaimed':False,
                       'nativeNormalTangentReadbackAvailable':False})
    return result


native_support_proof=native_support_checks


def expected_counterfactual(before,bundle,new_mesh_paths,new_material_path):
    require(before==bundle['base']['witness'],'Whole actual saved R32 scene required')
    require(set(new_mesh_paths)==set(bundle['floorRecords']) and all(p.startswith(PREFIX+'/')for p in new_mesh_paths.values())
            and new_material_path==MATERIAL,'Exactly two new hard meshes and one owned backdrop graph required')
    controls=bundle['nativeEcologyControls'];require(set(controls)==set(bundle['ecologyGroups']),'All exact eight fresh native controls required')
    result=copy.deepcopy(before)
    for key,group in bundle['ecologyGroups'].items():
        validate_native_controls(controls[key],group,bundle);keep=expected_control(controls[key],group['selectedSourceIndices'])
        c=component(result[group['actor']],group['component']);c['instanceCount']=keep['instanceCount'];c['orderedInstanceTransformsSha256']=digest(keep['recoveredValues'])
    for key,target in bundle['floorTargets'].items():component(result[target['actor']],target['component'])['mesh']=new_mesh_paths[key]
    target=bundle['proposal']['repairCSingleBackdropNearPbr'];c=component(result[target['actualActor']],target['actualComponent'])
    require(c==target['originalComponentWitness'] and len(c['materials'])==1 and not c['overrideMaterials'],'Only single original backdrop slot without prior override accepted')
    c['materials']=[new_material_path];c['overrideMaterials']=[new_material_path]
    hisms=[c for a in result.values()for c in a['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
    require(len(result)==5360 and len(hisms)==2321 and sum(c['instanceCount']for c in hisms)==678197,'Full actor/HISM after exact34 retirements differs')
    return result


def validate_content(before,after,packages,map_changed=True):
    require(len(before)==4086 and len(packages)==len(set(packages))==6 and all(p.startswith(PREFIX+'/')for p in packages),'Exactly six owned packages required')
    relative={p.split('.')[0].removeprefix('/Game/')+'.uasset'for p in packages}
    require(not set(before)&relative and set(after)==set(before)|relative,'Only six declared new packages permitted')
    changed=[k for k in before if before[k]!=after[k]]
    require(changed==(['Brezi/Maps/Brezi.umap']if map_changed else[]),'Original Content changed outside own map')
    return {'changedOriginalFiles':changed,'newOwnedPackages':sorted(relative),'originalContentFiles':4086,'savedContentFiles':4092,'newPackages':6}
