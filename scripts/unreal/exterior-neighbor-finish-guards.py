"""Dependency-free R18 source/receipt guards. No Unreal import or source writes."""
from collections import Counter
import copy
import hashlib
import json
import math
from pathlib import Path
import random
import struct

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighbor-finish-guards.py'
STUDY = ROOT/'output/unreal/exterior-neighbor-finish-20261001-r18-study'
PLAN_SHA = '6e73abcdfc5a0d7a712625f0468cf0a58c9e174e329947b4a04f1cfc846d9351'
PRODUCER_SHA = 'd139a74d8427459efa60e8ff0ca1fa05c63f07b295e4798bf90b67f66b37b338'
DESIGN = {'variant':'C','heatingLayout':'B','livingLayout':'B'}
PREFIX = '/Game/Brezi/NeighborFinish20261001R18'
TARGETS = {'BU.572063':(28,6,8),'BU.3800911':(44,106,14),'BU.3852341':(50,125,13)}
PARTITIONS = {'village_0_2_wall':(204,122,82),'village_0_2_roof':(234,112,122),
              'village_0_2_darkroof':(125,125,0),'neighborhood_0_2_wire':(1698,340,1358),
              'neighborhood_0_2_village_wall':(250,140,110),'neighborhood_0_2_boundary_post':(128,80,48)}
ROLES = {'roof':237,'roof_ridge':420,'roof_eave':900,'wall':458,'window_reveal':280,
         'window_frame':2100,'window_sill':420,'window_glass':70,'window_backing':70,'window_curtain':140}
FLAGS = ('nativeApplied','nativeGeometryDecoded','nativeAppearanceAccepted','performanceAccepted','fullPhotorealismAccepted')


def require(ok,message):
    if not ok: raise ValueError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def f32(v): return struct.unpack('<f',struct.pack('<f',v))[0]
def finite(v,n): return isinstance(v,list) and len(v)==n and all(type(x) in (int,float) and math.isfinite(x) for x in v)
def cross(a,b): return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def dot(a,b): return sum(x*y for x,y in zip(a,b))
def area(points): return abs(sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:]+points[:1])))/2
def cyclic(face): return min(tuple(face[i:]+face[:i]) for i in range(3))


def triangles(mesh):
    return [[mesh['verticesCm'][i] for i in mesh['indices'][j:j+3]] for j in range(0,len(mesh['indices']),3)]


def native_corner_sequence(mesh):
    """Exact two-rounding GLB-metres→native-cm representation, with winding."""
    positions=[[f32(f32(v/100)*100) for v in p] for p in mesh['verticesCm']]
    uv=[[f32(v) for v in t] for t in mesh['uvs']]
    return [cyclic([tuple(positions[i]+uv[i]) for i in mesh['indices'][j:j+3]]) for j in range(0,len(mesh['indices']),3)]


def distance_segment(p,a,b):
    ab=[b[k]-a[k] for k in (0,1)];n=dot(ab,ab)
    t=max(0.,min(1.,dot([p[k]-a[k] for k in (0,1)],ab)/n)) if n else 0.
    return math.hypot(*(p[k]-a[k]-t*ab[k] for k in (0,1)))


def ring_inside(p,ring):
    inside=False
    for a,b in zip(ring,ring[1:]+ring[:1]):
        if distance_segment(p,a,b)<1e-6:return True
        if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:inside=not inside
    return inside


def footprint_distance(p,polygons):
    if any(ring_inside(p,poly[0]) and not any(ring_inside(p,hole) for hole in poly[1:]) for poly in polygons):return 0.
    return min(distance_segment(p,a,b) for poly in polygons for ring in poly for a,b in zip(ring,ring[1:]+ring[:1]))


def canonical(ring):
    points=list(ring[:-1] if ring[0]==ring[-1] else ring)
    signed=sum(a[0]*b[1]-a[1]*b[0] for a,b in zip(points,points[1:]+points[:1]))
    return list(reversed(points)) if signed<0 else points


def source_equal(a,b):
    if type(a) in (int,float) and type(b) in (int,float):return math.isfinite(a) and math.isfinite(b) and abs(a-b)<=1e-7
    if isinstance(a,list) and isinstance(b,list):return len(a)==len(b) and all(source_equal(x,y) for x,y in zip(a,b))
    return type(a) is type(b) and a==b


def expected_windows(village):
    result=[]
    for b in village['buildings']:
        if b['id'] not in TARGETS:continue
        rng=random.Random(int(hashlib.sha256(b['id'].encode()).hexdigest()[:14],16))
        floor=b['eaveElevationCm']-b['estimatedWallHeightCm'];eaves=b['eaveElevationCm']
        for poly in b['polygonsCm']:
            ring=canonical(poly[0])
            for a,end in zip(ring,ring[1:]+ring[:1]):
                length=math.dist(a,end)
                if length<240:continue
                tangent=[(end[k]-a[k])/length for k in (0,1)];out=[tangent[1],-tangent[0]]
                quantity=max(1,math.floor((length-70)/260));spacing=(length-120)/quantity
                for i in range(quantity):
                    center=60+spacing*(i+.5);width=min(rng.uniform(102,133),spacing-55)
                    frame='context_boundary_post' if rng.random()<.23 else 'context_wire'
                    result.append({'buildingSourceId':b['id'],'originCm':a,'tangent':tangent,'outward':out,
                                   'leftCm':center-width/2,'rightCm':center+width/2,'bottomCm':floor+90,
                                   'topCm':min(floor+225,eaves-42),'sourceWindowIndex':len(result),'originalFrameMaterial':frame})
    require(len(result)==35,'Original source window reconstruction differs')
    return result


def old_window_triangles(windows):
    """Reconstruct only the original relief planes, never gutters or plinths.

    The frozen producer emits two clockwise triangles for each non-solid box.
    Rounded micrometre-scale corners absorb only the documented double add /
    subtract reconstruction; source mesh hashes and ordinal partitions are exact.
    """
    result={name:Counter() for name in PARTITIONS if name.startswith('neighborhood_')}
    def key(points):return cyclic([tuple(round(v,6) for v in p) for p in points])
    for w in windows:
        a,t,o=w['originCm'],w['tangent'],w['outward'];l,r,z1,z2=w['leftCm'],w['rightCm'],w['bottomCm'],w['topCm'];c=(l+r)/2
        boxes=[('context_village_wall',l-9,r+9,z1-10,z2+10,3.5),('context_wire',l,r,z1,z2,5)]
        boxes.extend((w['originalFrameMaterial'],x1,x2,bottom,top,7) for x1,x2,bottom,top in
                     [(l,l+5,z1,z2),(r-5,r,z1,z2),(l,r,z1,z1+5),(l,r,z2-5,z2),(c-2.5,c+2.5,z1,z2)])
        boxes.append(('context_village_wall',l-10,r+10,z1-14,z1-8,13))
        for material,left,right,bottom,top,depth in boxes:
            points=[[a[0]+t[0]*x+o[0]*depth,a[1]+t[1]*x+o[1]*depth,z] for x,z in
                    [(left,bottom),(right,bottom),(right,top),(left,top)]]
            identity='neighborhood_0_2_'+material.removeprefix('context_')
            for face in [(points[0],points[1],points[2]),(points[0],points[2],points[3])]:
                face=list(face);normal=cross([face[2][k]-face[0][k] for k in range(3)],[face[1][k]-face[0][k] for k in range(3)])
                if dot(normal,o+[0])<0:face[1],face[2]=face[2],face[1]
                result[identity][key(face)]+=1
    return result


def rectangle_intersection_area(points,left,right,bottom,top):
    """Convex triangle clip, sufficient to reject walls covering openings."""
    polygon=points
    for axis,edge,side in [(0,left,1),(0,right,-1),(1,bottom,1),(1,top,-1)]:
        output=[]
        if not polygon:return 0.
        for a,b in zip(polygon,polygon[1:]+polygon[:1]):
            av=(a[axis]-edge)*side;bv=(b[axis]-edge)*side
            if av>=0:output.append(a)
            if (av>=0)!=(bv>=0):
                t=av/(av-bv);output.append([a[k]+t*(b[k]-a[k]) for k in (0,1)])
        polygon=output
    return area(polygon) if len(polygon)>=3 else 0.


def validate_candidate_data(plan,data,recipes,village,neighborhood,context):
    require(plan.get('owner')=='scripts/unreal/exterior-neighbor-finish-study.py' and plan.get('status')=='source-only-neighbor-finish-proposal-native-pending','Typed plan ownership/status differs')
    require(plan.get('schemaVersion')==1 and type(plan['schemaVersion']) is int and plan['activeDesign']==DESIGN and plan['setbacksMm']=={'street':3000,'east':3000},'Plan design/schema differs')
    require(all(plan.get(k) is False for k in FLAGS),'Source plan falsely claims native acceptance')
    require(data.get('owner')==plan['owner'] and data.get('status')=='source-only-neighbor-finish-geometry-native-pending','Geometry ownership/status differs')
    require(plan['candidateTriangles']==5095 and type(plan['candidateTriangles']) is int and plan['windowCount']==35,'Typed plan counts differ')
    require(plan['sourceSceneSha256']==village['sourceSceneSha256']==neighborhood['sourceSceneSha256']==context['sourceSceneSha256'] and plan['sourceObjSha256']==village['sourceObjSha256']==neighborhood['sourceObjSha256']==context['sourceObjSha256'],'Architecture frame differs')
    for source in [village,neighborhood,context]:
        require(source['activeDesign']==DESIGN and source['housePlacement']['streetSetbackMm']==source['housePlacement']['eastSetbackMm']==3000,'Protected C/B/B placement differs')
    original={m['id']:m for family in [village,neighborhood] for m in family['meshes']}
    buildings={b['id']:b for b in village['buildings'] if b['id'] in TARGETS}
    require(len(plan['targetBuildings'])==3 and {b['sourceId'] for b in plan['targetBuildings']}==set(TARGETS),'Target building scope differs')
    for row in plan['targetBuildings']:
        b=buildings[row['sourceId']];require(digest(b)==row['sourceRecordSha256'] and row['footprintUnchanged'] is True and row['sourceBaseVolumeUnchanged'] is True,'Original building record differs')
    partitions=data['sourceTrianglePartitions'];remainders={m['id']:m for m in data['unchangedRemainderMeshes']}
    require(len(partitions)==6 and {p['sourceMeshId'] for p in partitions}==set(PARTITIONS) and set(remainders)==set(PARTITIONS),'Six exact partition/remainder identities required')
    reconstructed=expected_windows(village);old_windows=old_window_triangles(reconstructed)
    for p in partitions:
        identity=p['sourceMeshId'];src=original[identity];ret=remainders[identity];total,removed,kept=PARTITIONS[identity]
        require(p['sourceTriangles']==total and len(p['removedTriangleOrdinals'])==removed and p['retainedTriangles']==kept,'919 old source triangle membership differs')
        remove=p['removedTriangleOrdinals'];retain=p['retainedTriangleOrdinals']
        require(all(type(x) is int for x in remove+retain) and remove==sorted(set(remove)) and retain==sorted(set(retain)) and not set(remove)&set(retain) and sorted(remove+retain)==list(range(total)),'Triangle partition/order differs')
        require(digest(src)==p['sourceGeometrySha256'] and p['sourceMaterial']==src['material'],'Old source geometry/material differs')
        require(all(ret[k]==v for k,v in src.items() if k!='indices') and ret['indices']==[i for ordinal in retain for i in src['indices'][ordinal*3:ordinal*3+3]],'Unselected source arrays/ordered triangles changed')
        require(digest(ret)==p['replacementRemainderSha256'] and p['omitOldActorOnlyIfRemainderEmpty'] is (not bool(kept)),'Remainder receipt/empty actor policy differs')
        if identity in old_windows:
            actual=Counter(cyclic([tuple(round(v,6) for v in point) for point in triangles(src)[ordinal]]) for ordinal in remove)
            require(actual==old_windows[identity],'Removed original detail triangles are not exactly the35 old windows; gutters/plinths must remain')
        else:
            role='wall' if identity.endswith('_wall') else 'roof'
            expected=sorted(i for row in plan['targetBuildings'] if buildings[row['sourceId']][role+'MeshId']==identity for i in row['selectedBaseTriangleOrdinals'][role])
            require(remove==expected,'Removed original base triangles escape selected3 buildings')
    windows=data['windows']
    require(len(windows)==35,'Exact 35 windows required')
    for w,expected in zip(windows,reconstructed):
        require(all(source_equal(w[k],v) for k,v in expected.items()) and type(w['sourceWindowIndex']) is int,'Source window bay/position/frame changed')
        require(w.get('nativeApplied') is False and w['wallOpeningActuallyCutInSource'] is True and w['newRecessCm']==20 and w['revealDepthCm']==18 and w['backingDepthCm']==45 and w['curtainDepthCm']==38 and w['newGlassMaterial']=='neighbor_window_dielectric','Window source/native semantics differ')
    meshes=data['candidateMeshes'];ids=[m['id'] for m in meshes]
    require(len(ids)==len(set(ids))==32,'Exactly 32 unique candidate meshes required')
    counts=Counter();wall_area=0.;minimum_uv=float('inf');normal_error=0.;maximum_reach=0.
    for m in meshes:
        require(m['buildingSourceId'] in TARGETS and m['role'] in ROLES and m['material'] in set(recipes)|{'context_boundary_post'},'Candidate role/building/material escapes pilot')
        require(m.get('nativeApplied') is False and m['collision']=='NoCollision' and m['canEverAffectNavigation'] is False and m['winding']=='clockwise' and m['maxDrawDistanceCm']==65000 and m['nanite'] is False,'Candidate native policy differs')
        vertices=m['verticesCm'];require(vertices and len(m['indices'])%3==0 and m['indices'] and all(type(i) is int and 0<=i<len(vertices) for i in m['indices']),'Candidate indices invalid')
        require(all(len(m[k])==len(vertices) for k in ['uvs','normals','tangents','tangentHandedness']),'Candidate attributes differ')
        b=buildings[m['buildingSourceId']]
        for i,p in enumerate(vertices):
            require(finite(p,3) and finite(m['uvs'][i],2) and finite(m['normals'][i],3) and finite(m['tangents'][i],3),'Nonfinite or boolean candidate coordinates')
            reach=footprint_distance(p[:2],b['polygonsCm']);maximum_reach=max(maximum_reach,reach)
            require(reach<=13.01,'Candidate exceeds source footprint visual reach13cm')
            n,t=m['normals'][i],m['tangents'][i]
            error=max(abs(dot(n,n)-1),abs(dot(t,t)-1),abs(dot(n,t)));normal_error=max(normal_error,error)
            require(error<1e-7 and type(m['tangentHandedness'][i]) in (int,float) and m['tangentHandedness'][i] in [-1,1],'Candidate normal/tangent basis differs')
        for ordinal in range(len(m['indices'])//3):
            idx=m['indices'][ordinal*3:ordinal*3+3];points=[vertices[i] for i in idx]
            ab=[points[1][k]-points[0][k] for k in range(3)];ac=[points[2][k]-points[0][k] for k in range(3)];out=cross(ac,ab);size=math.sqrt(dot(out,out));require(size>1e-8,'Degenerate candidate triangle')
            require(all(dot([x/size for x in out],m['normals'][i])>1-1e-7 for i in idx),'Candidate winding/normal differs')
            uv=[m['uvs'][i] for i in idx];uv_area=area(uv);minimum_uv=min(minimum_uv,uv_area);require(uv_area>1e-11,'Collapsed facade/roof UV')
            if m['role']=='wall':
                wall_area+=size/2
                for w in windows:
                    if w['buildingSourceId']!=b['id']:continue
                    a=w['originCm'];t=w['tangent'];o=w['outward']
                    if max(abs(dot([p[k]-a[k] for k in (0,1)],o)) for p in points)>.002:continue
                    projected=[[dot([p[k]-a[k] for k in (0,1)],t),p[2]] for p in points]
                    require(rectangle_intersection_area(projected,w['leftCm'],w['rightCm'],w['bottomCm'],w['topCm'])<1e-5,'Solid candidate wall covers actual window opening')
        counts[m['role']]+=len(m['indices'])//3
    require(dict(counts)==ROLES and sum(counts.values())==5095,'Exact role/triangle budget differs')
    original_wall_area=0.
    for row in plan['targetBuildings']:
        b=buildings[row['sourceId']];source=original[b['wallMeshId']]
        for ordinal in row['selectedBaseTriangleOrdinals']['wall']:
            a,end,c=triangles(source)[ordinal];v=cross([end[k]-a[k] for k in range(3)],[c[k]-a[k] for k in range(3)])
            original_wall_area+=math.sqrt(dot(v,v))/2
        roof=next(m for m in meshes if m['buildingSourceId']==b['id'] and m['role']=='roof')
        old=triangles(original[b['roofMeshId']]);require(triangles(roof)==[old[i] for i in row['selectedBaseTriangleOrdinals']['roof']],'Underlying original roof positions/order changed')
    openings=sum((w['rightCm']-w['leftCm'])*(w['topCm']-w['bottomCm']) for w in windows)
    require(abs(original_wall_area-openings-wall_area)<.01,'Decoded cut walls fail exact area partition')
    require(len(recipes)==9 and set(recipes)==set(plan['materialRecipeIds']),'Nine exact typed recipes required')
    for name,r in recipes.items():
        require(r.get('nativeApplied') is False and r.get('metallic')==0,'Recipe claims native or metallic glazing')
        if r['kind']=='neighbor-plaster-scan':
            require(set(r['maps'])=={'albedo','normal','roughness'} and r['periodCm']==100 and r['normalConvention']=='OPENGL_GREEN_POSITIVE_V' and r['mapping']=='AUTHORED_METRIC_FACADE_U_ALONG_EDGE_V_HEIGHT','Plaster physical map policy differs')
        elif r['kind']=='neighbor-procedural-roof-tile':require(not r['maps'] and r['evidence']=='PROJECT_AUTHORED_NOT_SCANNED_CERAMIC_ATLAS','False photographic roof claim')
    glass=recipes['neighbor_window_dielectric'];require(glass['kind']=='neighbor-window-dielectric' and glass['roughness']==.12 and glass['blendProposal']=='TRANSLUCENT' and glass['nativeShaderCompileVerified'] is False,'Glazing roughness/blend/source semantics differ')
    return {'sourceGeometryDecoded':True,'nativeGeometryDecoded':False,'candidateMeshes':32,'candidateTriangles':5095,
            'remainderMeshes':5,'retiredOldTriangles':919,'windowCount':35,'windowOpeningAreaM2':openings/10000,
            'retainedWallAreaM2':wall_area/10000,'wallAreaErrorCm2':abs(original_wall_area-openings-wall_area),
            'maximumVisualReachCm':maximum_reach,'minimumUVTriangleArea':minimum_uv,'maximumNormalTangentError':normal_error,
            'nativeApplied':False,'nativeAppearanceAccepted':False,'performanceAccepted':False,'fullPhotorealismAccepted':False}


def validated_candidate():
    path=STUDY/'neighbor-finish-plan.json';require(sha(path)==PLAN_SHA,'Frozen R18 source plan drift')
    plan=read(path);require(plan['generatorSha256']==PRODUCER_SHA and sha(ROOT/plan['owner'])==PRODUCER_SHA,'Frozen R18 producer drift')
    for p,h in {**plan['inputFiles'],**plan['payloadFiles']}.items():
        require(Path(p).is_relative_to(ROOT) and sha(p)==h,'Frozen R18 sidecar/input drift: '+p)
    data=read(STUDY/'neighbor-finish-geometry.json');recipes=read(STUDY/'neighbor-finish-recipes.json')
    village=read(ROOT/'output/unreal/exterior-buildings-20260926-r2/building-plan.json')
    neighborhood=read(ROOT/'output/unreal/exterior-context-20260930-r3/neighborhood-details.json')
    context=read(ROOT/'output/unreal/exterior-context-20260927-r8/context-plan.json')
    audit=validate_candidate_data(plan,data,recipes,village,neighborhood,context)
    original={m['id']:m for family in [village,neighborhood] for m in family['meshes']}
    return {'plan':plan,'geometry':data,'recipes':recipes,'audit':audit,
            'originalChunks':{identity:original[identity] for identity in PARTITIONS},
            'inputPins':{str(path):PLAN_SHA,**plan['inputFiles'],**plan['payloadFiles']}}


def expected_original_witness(before,changes):
    require(len(changes)==6 and {c['sourceMeshId'] for c in changes}==set(PARTITIONS),'Exactly six original component changes required')
    expected=copy.deepcopy(before)
    for change in changes:
        actor=expected[change['actor']];components=[c for c in actor['components'] if c['name']==change['componentName']]
        require(len(components)==1,'Affected original component ambiguous');component=components[0]
        require(component['mesh']==change['beforeMesh'],'Affected source mesh differs')
        if change['sourceMeshId']=='village_0_2_darkroof':
            require(change['operation']=='hide-empty-source-chunk' and change['afterMesh']==change['beforeMesh'] and change['changedFields']==['visible','hiddenInGame','cast_shadow','cast_hidden_shadow'],'Empty source actor hide/field scope differs')
            component['visible']=False;component['hiddenInGame']=True
            component['neighborRenderPolicy']['cast_shadow']=False;component['neighborRenderPolicy']['cast_hidden_shadow']=False
        else:
            require(change['operation']=='replace-with-retained-source-chunk' and change['afterMesh'].startswith(PREFIX+'/') and change['changedFields']==['mesh'],'Unreviewed source binding/field scope')
            component['mesh']=change['afterMesh']
    return expected


def verify_original_witness(before,after,changes,added):
    expected=expected_original_witness(before,changes)
    require(len(added)==len(set(added))==32 and not set(added)&set(expected),'Exactly 32 fresh owned actor identities required')
    require(set(after)==set(expected)|set(added),'Unreported actor addition/removal')
    for path,row in expected.items():require(after[path]==row,'Protected original actor/component policy changed: '+path)
    return {'originalActors':len(before),'addedActors':32,'affectedComponents':6,'allWitnessedOriginalPoliciesPreserved':True}


def validate_content_delta(before,after,supplement=None,allowed_packages=None):
    require(set(before)<=set(after),'Original Content file removed')
    for p,h in before.items():
        if p=='Brezi/Maps/Brezi.umap':continue
        if p=='Data/viewpoints.json' and supplement is not None:
            require(h==supplement['originalViewpoints']['sha256'] and after[p]==supplement['appendedViewpoints']['sha256'],'Typed diagnostic viewpoint byte delta differs')
        else:require(after[p]==h,'Original asset/data bytes changed: '+p)
    for p in set(after)-set(before):
        require(p.startswith('Brezi/NeighborFinish20261001R18/') and Path(p).suffix in {'.uasset','.uexp','.ubulk'},'New native asset escapes R18 namespace: '+p)
        if allowed_packages is not None:require(str(Path(p).with_suffix('')) in allowed_packages,'Unexpected new R18 native package: '+p)
    if allowed_packages is not None:require({str(Path(p).with_suffix('')) for p in set(after)-set(before) if p.endswith('.uasset')}==set(allowed_packages),'Exact new R18 package closure differs')
    return {'originalAssetBytesPreserved':True,'viewpointsBytesPreserved':supplement is None,'originalViewpointRowsPreserved':True,
            'typedDiagnosticViewsAppended':1 if supplement else 0,'newFileCount':len(set(after)-set(before))}
