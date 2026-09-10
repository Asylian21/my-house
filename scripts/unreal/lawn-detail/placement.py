"""Deterministic additive grass on the actual source lawn; ordinary Python only.

`prepare` rebuilds the explicit placement artifact and its source receipt.
Native import calls verify_inputs; it never silently regenerates planting.
"""
import bisect
import hashlib
import importlib.util
import itertools
import json
import math
from pathlib import Path
import random
import sys

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'lib/twin-site.ts').is_file())
HERE = Path(__file__).resolve().parent
GEOMETRY = ROOT/'output/unreal/geometry'
PROTOTYPES = ROOT/'output/unreal/vegetation-prototypes'
SCENE_SHA = '61ba228f4b72a5ee5fc754e60e112ff70d03605f8cf56fec97bccc3519b8863b'
OBJ_SHA = 'a42e9eb169d929bc67056ad21bf3885e3f1a32838f15c328cb98bacd008fa455'
PARCEL = 'DOM_00001'
EXTRA = {**{f'DOM_{1813+i:05}':f'gravel-strip-{i}' for i in range(1,4)},
         **{f'DOM_{1816+i:05}':f'garden-step-{i}' for i in range(1,5)},
         **{f'DOM_{1820+i:05}':f'mulch-bed-{i}' for i in range(1,3)}}
MODEL = 'grass_bermuda_01'
# The design reference shows mown lawn. Use only the 32–55 mm source forms;
# taller seed-bearing library forms remain available for a different planting.
IDS = tuple(f'{MODEL}_small_{letter}' for letter in 'abcd')


def require(ok, message):
    if not ok: raise ValueError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def read(path): return json.loads(Path(path).read_text())


def vegetation():
    spec=importlib.util.spec_from_file_location('lawn_source_vegetation',ROOT/'scripts/unreal/vegetation.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


def signed_area(a,b,c): return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])


def footprint_polygons(faces):
    """All nondegenerate XY projections, including nonrectangular mulch beds.

    A closed box has duplicate top/bottom footprints; deduplicate them, while
    retaining every distinct projected triangle rather than filling an AABB.
    """
    unique={}
    for face in faces:
        polygon=[tuple(p[:2]) for p in face]
        if abs(signed_area(*polygon))>1e-6:
            unique[tuple(sorted(polygon))]=polygon
    require(unique,'Ground object has no projected footprint')
    return list(unique.values())


def source_context(scene, geometry):
    v=vegetation(); rows={o['id']:o for o in scene['objects']}
    require(sha(geometry/'scene.json')==SCENE_SHA and sha(geometry/'dom-mm.obj')==OBJ_SHA,'Canonical lawn geometry changed')
    require(digest(scene)==digest(read(geometry/'scene.json')),'Supplied scene differs')
    patches=v.register_patches(scene); lawn=next(p for p in patches if p['kind']=='lawn')
    require(lawn['sourceObjectIds']==[PARCEL] and rows[PARCEL]['materialSlots']==['MAT_0001'],'Wrong parcel source')
    for id_,walk_id in EXTRA.items():
        row=rows[id_]
        require(row['enabled'] and row['instances']==1 and row['metadata']['walkSurfaceId']==walk_id,
                'Extra grass exclusion source changed: '+id_)
    source=v.read_source_triangles(geometry/'dom-mm.obj',scene,{PARCEL,*EXTRA})
    exclusions=v.exclusion_polygons(scene)
    for id_ in EXTRA:
        for n,p in enumerate(footprint_polygons(source[id_])):
            exclusions.append({'id':f'{id_}/{n}','polygonSourceMm':p})
    return v,lawn,source[PARCEL],exclusions


def checked_prototypes():
    v=vegetation(); report=read(PROTOTYPES/'prototypes.json')
    require(report['status']=='prototype-conversion-validated' and report['converterSha256']==sha(ROOT/'scripts/unreal/vegetation-convert.py')
            and report['auditorSha256']==sha(ROOT/'scripts/unreal/vegetation.py'),'Converted plant recipe changed')
    audit=v.audit_assets(ROOT/'scripts/archviz/assets.lock.json',ROOT/'output/archviz/assets')
    require(audit==report['assetAudit'],'Original model lock or bytes changed')
    selected={p['id']:p for p in report['prototypes'] if p['assetId']==MODEL and p['id'] in IDS}
    require(set(selected)==set(IDS),'Expected exact four short Bermuda prototypes')
    pins={'output/unreal/vegetation-prototypes/prototypes.json':sha(PROTOTYPES/'prototypes.json'),
          'scripts/unreal/vegetation.py':sha(ROOT/'scripts/unreal/vegetation.py'),
          'scripts/unreal/vegetation-convert.py':sha(ROOT/'scripts/unreal/vegetation-convert.py'),
          'scripts/archviz/assets.lock.json':sha(ROOT/'scripts/archviz/assets.lock.json')}
    for p in selected.values():
        require(p['file']==p['id']+'.glb' and p['alphaMode']=='MASK' and p['alphaCutoff']==.45
                and p['doubleSided'] and p['khronosValidation']['numErrors']==0,'Unexpected grass prototype policy')
        require(sha(PROTOTYPES/p['file'])==p['sha256'],'Grass GLB changed')
        require(8<=p['triangles']<=30 and len(p['verticesSourceZUpMetres'])>0,'Grass topology changed')
        require(all(math.isfinite(x) for point in p['verticesSourceZUpMetres'] for x in point),'Nonfinite grass vertex')
        pins[str((PROTOTYPES/p['file']).relative_to(ROOT))]=p['sha256']
    for item in report['models'][MODEL]['textures'].values():
        require(sha(PROTOTYPES/item['path'])==item['sha256'],'Converted grass texture changed')
        pins[str((PROTOTYPES/item['path']).relative_to(ROOT))]=item['sha256']
    for model in audit['models']:
        for entry in model['verifiedFiles']:
            p=ROOT/'output/archviz/assets'/entry['path'];pins[str(p.relative_to(ROOT))]=sha(p)
    return report,selected,pins


def transform_vertices(prototype, position, yaw, scale):
    angle=math.radians(yaw);c,s=math.cos(angle),math.sin(angle)
    return [[position[0]+1000*scale*(c*x-s*y),position[1]+1000*scale*(s*x+c*y),position[2]+1000*scale*z]
            for x,y,z in prototype['verticesSourceZUpMetres']]


def mesh_aabb_vertices(prototype):
    bounds=prototype['boundsSourceZUpMetres']
    return list(itertools.product(*[(bounds['min'][i],bounds['max'][i]) for i in range(3)]))


def unreal_bounds(points):
    native=[[p[0]/10,-p[1]/10,p[2]/10] for p in points]
    return {'min':[min(p[i] for p in native) for i in range(3)],'max':[max(p[i] for p in native) for i in range(3)]}


def boundary_and_areas(faces):
    edges={};cumulative=[];area=0
    for a,b,c in faces:
        require(max(a[2],b[2],c[2])-min(a[2],b[2],c[2])<=.05,'Unsupported lawn slope')
        triangle_area=abs(signed_area(a,b,c))/2;require(triangle_area>0,'Degenerate lawn source')
        area+=triangle_area;cumulative.append(area)
        for u,w in [(a,b),(b,c),(c,a)]:
            key=tuple(sorted((tuple(u),tuple(w))));edges[key]=edges.get(key,0)+1
    require(all(n<=2 for n in edges.values()),'Nonmanifold lawn source')
    boundary=[e for e,n in edges.items() if n==1];require(boundary,'Missing lawn boundary')
    return boundary,cumulative,area


def build_plan(scene, geometry, seed=601226, density=100.0):
    require(math.isfinite(density) and 0<density<=100,'Density outside reviewed budget')
    v,lawn,faces,exclusions=source_context(scene,geometry)
    _,prototypes,_=checked_prototypes()
    boundary,cumulative,area=boundary_and_areas(faces)
    samples=math.floor(area/1e6*density);require(samples<=100000,'Grass sample budget exceeded')
    polygons=[]
    for e in exclusions:
        p=e['polygonSourceMm'];polygons.append((e['id'],p,[min(q[0] for q in p),min(q[1] for q in p),max(q[0] for q in p),max(q[1] for q in p)]))
    rng=random.Random(int(hashlib.sha256(f'{seed}/{lawn["sourceIdentity"]}/grass-detail-1'.encode()).hexdigest(),16))
    groups={i:{'id':'LAWN_'+i,'prototypeId':i,'instances':[],'vertices':[],'boxVertices':[]} for i in IDS}
    rejected={'edgeOrHole':0,'hardscape':0};reject_sources={};min_margin=float('inf');vertices_checked=0
    for index in range(samples):
        a,b,c=faces[bisect.bisect_right(cumulative,rng.random()*area)]
        root,t=math.sqrt(rng.random()),rng.random();w=[1-root,root*(1-t),root*t]
        point=[round(sum(w[j]*p[i] for j,p in enumerate([a,b,c])),3) for i in range(3)]
        prototype=prototypes[IDS[rng.randrange(len(IDS))]];yaw=round(rng.uniform(-180,180),5);scale=round(rng.uniform(.8,1.15),6)
        verts=transform_vertices(prototype,point,yaw,scale)
        # A disk enclosing EVERY transformed source vertex also encloses all
        # their triangles. Proving this disk misses every boundary/hole segment
        # and exclusion polygon is stronger than testing only roots or AABBs.
        radius=max(math.hypot(p[0]-point[0],p[1]-point[1]) for p in verts)+1.0
        edge_distance=min(math.sqrt(v.segment_distance_squared(point,a,b)) for a,b in boundary)
        if edge_distance<=radius:rejected['edgeOrHole']+=1;continue
        hit=None
        for id_,polygon,box in polygons:
            if point[0]+radius<box[0] or point[0]-radius>box[2] or point[1]+radius<box[1] or point[1]-radius>box[3]:continue
            if v.intersects_buffered_polygon(point,polygon,radius):hit=id_;break
        if hit is not None:
            rejected['hardscape']+=1;reject_sources[hit]=reject_sources.get(hit,0)+1;continue
        min_margin=min(min_margin,edge_distance-radius);vertices_checked+=len(verts)
        group=groups[prototype['id']]
        group['instances'].append({'id':index,'positionUnrealCm':[point[0]/10,-point[1]/10,point[2]/10],
                                   'yawDegreesUnreal':-yaw,'uniformScale':scale})
        group['vertices'].extend(verts)
        group['boxVertices'].extend(transform_vertices({'verticesSourceZUpMetres':mesh_aabb_vertices(prototype)},point,yaw,scale))
    for group in groups.values():
        require(group['instances'],'Empty grass prototype group')
        group['geometryBoundsUnrealCm']=unreal_bounds(group.pop('vertices'))
        group['componentBoundsUnrealCm']=unreal_bounds(group.pop('boxVertices'))
    count=sum(len(g['instances']) for g in groups.values())
    return {'schemaVersion':1,'status':'lawn-detail-placement-validated','sourceObjectId':PARCEL,
            'sourceManifestSha256':SCENE_SHA,'sourceObjSha256':OBJ_SHA,'plannerSha256':sha(__file__),
            'seed':seed,'densityTuftsPerM2':density,'cullStartCm':600,'cullEndCm':1200,
            'sourceAreaM2':area/1e6,'sourceTriangleCount':len(faces),'boundarySegmentCount':len(boundary),
            'sampleCount':samples,'instanceCount':count,'groups':list(groups.values()),'rejected':rejected,
            'rejectedByExclusion':reject_sources,'exclusions':exclusions,'extraExclusionObjectIds':list(EXTRA),
            'placementProof':{'method':'complete transformed vertex enclosing disk inside triangulated source domain and outside every source exclusion',
                              'transformedVerticesChecked':vertices_checked,'extraClearanceMm':1,'minimumOuterBoundaryMarginMm':min_margin,
                              'sourceTriangleInteriorsPreserved':True},
            'sourceMutation':{'hidden':[],'deleted':[],'modifiedMeshes':[],'collisionChanges':[]},
            'limits':['Designed illustrative Bermuda lawn detail, not measured site vegetation or selected grass species.',
                      'Density, culling and optical transmission require packaged native4K visual/performance QA.',
                      'All base parcel geometry and walking collision remain authoritative; no tree or roadside card replacement.']}


def prepare():
    scene=read(GEOMETRY/'scene.json');_,_,pins=checked_prototypes();plan=build_plan(scene,GEOMETRY)
    path=GEOMETRY.parent/'lawn-detail/placement.json';path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(plan,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n')
    pins.update({str((GEOMETRY/'scene.json').relative_to(ROOT)):SCENE_SHA,str((GEOMETRY/'dom-mm.obj').relative_to(ROOT)):OBJ_SHA,
                 str(path.relative_to(ROOT)):sha(path)})
    reference={'sourceManifestSha256':SCENE_SHA,'sourceObjSha256':OBJ_SHA,'placementPath':str(path.relative_to(ROOT)),
               'inputFiles':pins,'sourceObjectId':PARCEL,'extraExclusionObjectIds':list(EXTRA),'prototypeIds':list(IDS)}
    (HERE/'reference.json').write_text(json.dumps(reference,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({'path':str(path),'sha256':sha(path),'instances':plan['instanceCount'],'groups':len(plan['groups']),
                      'rejected':plan['rejected'],'proof':plan['placementProof']},indent=2))


def verify_inputs(scene, geometry):
    geometry=Path(geometry);ref=read(HERE/'reference.json')
    require(ref['sourceManifestSha256']==SCENE_SHA and ref['sourceObjSha256']==OBJ_SHA
            and ref['sourceObjectId']==PARCEL and ref['prototypeIds']==list(IDS)
            and ref['extraExclusionObjectIds']==list(EXTRA),'Foreign lawn reference scope')
    require(sha(geometry/'scene.json')==SCENE_SHA and sha(geometry/'dom-mm.obj')==OBJ_SHA
            and digest(scene)==digest(read(geometry/'scene.json')),'Canonical lawn source changed')
    for name,expected in ref['inputFiles'].items():
        p=ROOT/name;require(p.resolve().is_relative_to(ROOT) and not p.is_symlink() and sha(p)==expected,'Lawn input changed: '+name)
    plan=read(ROOT/ref['placementPath'])
    require(plan['status']=='lawn-detail-placement-validated' and plan['plannerSha256']==sha(__file__)
            and plan['sourceManifestSha256']==SCENE_SHA and plan['sourceObjSha256']==OBJ_SHA,'Regenerate lawn placements with current source/planner')
    require(plan['sourceObjectId']==PARCEL and plan['instanceCount']==sum(len(g['instances']) for g in plan['groups'])
            and {g['prototypeId'] for g in plan['groups']}==set(IDS) and len(plan['groups'])==len(IDS),'Lawn placement scope differs')
    files={**ref['inputFiles'],str(Path(__file__).relative_to(ROOT)):sha(__file__),str((HERE/'reference.json').relative_to(ROOT)):sha(HERE/'reference.json')}
    return {'plan':plan,'pipelineFiles':files,'prototypeReport':read(PROTOTYPES/'prototypes.json'),'scene':scene}


if __name__=='__main__':
    require(sys.argv[1:]==['prepare'],'Usage: placement.py prepare');prepare()
