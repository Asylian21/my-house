"""One isolated R18 source-only three-building finish candidate.

No Unreal, package, browser or original artifact writes. The buildings retain
their frozen, approximate volumes. Only selected facade/window/roof visual
parts change; cadastral XY is not an observation of fences or building finishes.
"""
import ast
from collections import Counter, defaultdict
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import sys

sys.dont_write_bytecode = True
from PIL import Image, ImageDraw, ImageFont
from shapely.geometry import LineString, Point, Polygon, box as rectangle
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighbor-finish-study.py'
DESTINATION = ROOT / 'output/unreal/exterior-neighbor-finish-20261001-r18-study'
TARGETS = {'BU.572063': (28, 6, 8), 'BU.3800911': (44, 106, 14), 'BU.3852341': (50, 125, 13)}
SOURCES = {
    'context': ('output/unreal/exterior-context-20260927-r8/context-plan.json', '4b0b72a5f39d5bec3915846abb159147a4cf73b65cbf920884ffe7dd762a4176'),
    'village': ('output/unreal/exterior-buildings-20260926-r2/building-plan.json', 'fd8b61e6fa5c462a851fab26a2ec5d5edcbec9d07bb80e1d6e7163b6568fb318'),
    'neighborhood': ('output/unreal/exterior-context-20260930-r3/neighborhood-details.json', '54a34a1cdbe372ad213a61a086abfb1267b7290b80e6a5029d24b0e58ee4b4cb'),
    'materialInputs': ('scripts/unreal/archviz-material-inputs.json', '7cdbf81496bfcb32e590eb3230c5ea911da99e8a2281bdcc11357039825cd075'),
    'buildingsProducer': ('scripts/unreal/exterior-buildings.py', '57c41a781f301dc07f946b12f95053f29d746c09d940983a9dc7db7a37b7375c'),
    'scene': ('output/unreal/realism-20260926-r5/geometry/scene.json', '0e2925319fa0effc3727b121ee24f75a3b8e8bd53b3a31d230e29e29a56ed387'),
    'architecturalObj': ('output/unreal/realism-20260926-r5/geometry/dom-mm.obj', 'a86c83e68e14898fdeb3fd071c24a6bb82d3a6d0e61f52d8e9a757bce4a2634d'),
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, separators=(',', ':'), allow_nan=False) + '\n')


def load_module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def normalized(v):
    length = math.sqrt(sum(x*x for x in v))
    require(length > 1e-9, 'Degenerate source frame')
    return [x / length for x in v]


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def triangle_points(mesh, ordinal):
    return [mesh['verticesCm'][i] for i in mesh['indices'][ordinal*3:ordinal*3+3]]


def triangle_normal(points):
    a, b, c = points
    return normalized(cross([c[i]-a[i] for i in range(3)], [b[i]-a[i] for i in range(3)]))


class Mesh:
    def __init__(self, identity, material, source_id, role):
        self.record = {'id': identity, 'material': material, 'buildingSourceId': source_id,
                       'role': role, 'verticesCm': [], 'indices': [], 'uvs': [], 'normals': [],
                       'tangents': [], 'tangentHandedness': [], 'winding': 'clockwise',
                       'nanite': False, 'collision': 'NoCollision', 'canEverAffectNavigation': False,
                       'castShadow': True, 'maxDrawDistanceCm': 65000, 'nativeApplied': False}

    def triangle(self, points, outward, uvs=None):
        a, b, c = [list(p) for p in points]
        n = triangle_normal([a, b, c])
        if dot(n, outward) < 0:
            b, c = c, b
            if uvs:
                uvs = [uvs[0], uvs[2], uvs[1]]
            n = triangle_normal([a, b, c])
        if uvs is None:
            u = normalized([b[i]-a[i] for i in range(3)])
            v = normalized(cross(n, u))
            uvs = [[dot(p, u)/100, dot(p, v)/100] for p in [a, b, c]]
        ab, ac = [[p[i]-a[i] for i in range(3)] for p in [b, c]]
        du1, dv1 = [uvs[1][i]-uvs[0][i] for i in range(2)]
        du2, dv2 = [uvs[2][i]-uvs[0][i] for i in range(2)]
        denominator = du1*dv2-du2*dv1
        require(abs(denominator) > 1e-10, 'Collapsed candidate metric UV')
        tangent = normalized([(ab[i]*dv2-ac[i]*dv1)/denominator for i in range(3)])
        bitangent = normalized([(ac[i]*du1-ab[i]*du2)/denominator for i in range(3)])
        handedness = 1 if dot(cross(n, tangent), bitangent) >= 0 else -1
        offset = len(self.record['verticesCm'])
        self.record['verticesCm'].extend([a, b, c]); self.record['indices'].extend(range(offset, offset+3))
        self.record['uvs'].extend(uvs); self.record['normals'].extend([n]*3)
        self.record['tangents'].extend([tangent]*3); self.record['tangentHandedness'].extend([handedness]*3)

    def face(self, points, outward):
        for i in range(1, len(points)-1):
            self.triangle([points[0], points[i], points[i+1]], outward)


def facade_box(mesh, origin, tangent, outward, left, right, bottom, top, back, front):
    def p(s, d, z):
        return [origin[k] + tangent[k]*s + outward[k]*d for k in (0, 1)] + [z]
    mesh.face([p(left,front,bottom),p(right,front,bottom),p(right,front,top),p(left,front,top)], [*outward,0])
    mesh.face([p(left,back,top),p(right,back,top),p(right,back,bottom),p(left,back,bottom)], [-outward[0],-outward[1],0])
    mesh.face([p(left,back,bottom),p(right,back,bottom),p(right,front,bottom),p(left,front,bottom)], [0,0,-1])
    mesh.face([p(left,front,top),p(right,front,top),p(right,back,top),p(left,back,top)], [0,0,1])
    mesh.face([p(left,back,bottom),p(left,front,bottom),p(left,front,top),p(left,back,top)], [-tangent[0],-tangent[1],0])
    mesh.face([p(right,front,bottom),p(right,back,bottom),p(right,back,top),p(right,front,top)], [*tangent,0])


def replay_windows(village, neighborhood, module):
    """Execute only the frozen producer's facade loop, tracking exact box ranges.

    Geometry equality against every replayed frozen detail mesh is mandatory.
    This isolates per-building window ordinals without guessed spatial tags.
    """
    producer = ROOT / 'scripts/unreal/exterior-neighborhood.py'
    require(sha(producer) == neighborhood['generatorSha256'], 'Frozen neighborhood producer drift')
    syntax = ast.parse(producer.read_text())
    function = next(n for n in syntax.body if isinstance(n, ast.FunctionDef) and n.name == 'build')
    loop = next(n for n in function.body if isinstance(n, ast.For) and isinstance(n.target, ast.Name) and n.target.id == 'building')
    loop = copy.deepcopy(loop)
    loop.body.insert(0, ast.parse("current['building'] = building").body[0])
    loop.body.insert(1, ast.parse("current['active'] = False").body[0])
    tree = ast.fix_missing_locations(ast.Module(body=[loop], type_ignores=[]))
    chunks, current, windows, removed = {}, {}, [], defaultdict(set)
    def chunk(cell, material):
        key = (tuple(cell), material)
        if key not in chunks:
            name = '_'.join(('m'+str(-v)) if v < 0 else str(v) for v in cell)
            chunks[key] = module.base.Mesh('neighborhood_'+name+'_'+material.removeprefix('context_'), material)
            chunks[key].record['maxDrawDistanceCm'] = 65000 if material != 'context_track' else 18000
        return chunks[key]
    def box(mesh, origin, tangent, outward, start, finish, bottom, top, depth=4, solid=False):
        target = current['building']['id'] in TARGETS
        if target and not solid and depth == 3.5:
            current['active'] = True
            current['window'] = {'buildingSourceId': current['building']['id'], 'originCm': origin,
                                 'tangent': tangent, 'outward': outward, 'leftCm': start+9,
                                 'rightCm': finish-9, 'bottomCm': bottom+10, 'topCm': top-10,
                                 'sourceWindowIndex': len(windows), 'originalFrameMaterial': None}
            windows.append(current['window'])
        first = len(mesh.record['indices'])//3
        module.box(mesh, origin, tangent, outward, start, finish, bottom, top, depth, solid)
        if target and current['active']:
            removed[mesh.record['id']].update(range(first, len(mesh.record['indices'])//3))
            if depth == 7:
                current['window']['originalFrameMaterial'] = mesh.record['material']
            if depth == 13:
                current['active'] = False
    env = {'selected': [b for b in village['buildings'] if b['sourceDistanceMetres'] <= 600],
           'current': current, 'chunk': chunk, 'box': box, 'tube': module.tube,
           'Counter': Counter, 'counts': Counter(), 'building_audit': [], 'random': random,
           'hashlib': hashlib, 'math': math, 'base': module.base, 'Polygon': Polygon,
           'unary_union': unary_union,
           'roof_sampler': module.base.GroundSampler({'meshes': [m for m in village['meshes'] if m['material'] in ('context_village_roof','context_village_darkroof')]})}
    exec(compile(tree, str(producer), 'exec'), env)
    original = {m['id']: m for m in neighborhood['meshes']}
    replayed = []
    for mesh in chunks.values():
        row = mesh.record; source = original[row['id']]
        require(all(row[k] == source[k] for k in ('verticesCm','indices','uvs','material')), 'Producer replay differs: '+row['id'])
        replayed.append({'sourceMeshId': row['id'], 'sourceGeometrySha256': digest(source),
                         'triangles': len(source['indices'])//3, 'exactReplay': True})
    require(len(windows) == 35 and sum(len(x) for x in removed.values()) == 560, 'Original 35-window membership differs')
    for identity, (_, _, count) in TARGETS.items():
        require(sum(w['buildingSourceId'] == identity for w in windows) == count, 'Window count differs: '+identity)
    return windows, removed, replayed


def select_base(village, targets, shapes):
    source = {m['id']: m for m in village['meshes']}
    selected = defaultdict(lambda: defaultdict(list))
    membership = defaultdict(set)
    for building in targets:
        shape = shapes[building['id']]
        for role, key in [('wall','wallMeshId'),('roof','roofMeshId')]:
            mesh = source[building[key]]
            for ordinal in range(len(mesh['indices'])//3):
                points = triangle_points(mesh, ordinal)
                center = Point(sum(p[0] for p in points)/3, sum(p[1] for p in points)/3)
                belongs = shape.boundary.distance(center) < .002 if role == 'wall' else shape.buffer(.002).covers(center)
                if belongs:
                    require(ordinal not in membership[mesh['id']], 'Duplicate selected base triangle')
                    selected[building['id']][role].append(ordinal); membership[mesh['id']].add(ordinal)
            expected = TARGETS[building['id']][0 if role == 'wall' else 1]
            require(len(selected[building['id']][role]) == expected, 'Source subset differs: '+building['id']+'/'+role)
    require(sum(len(v) for v in membership.values()) == 359, 'Selected 359 base triangles differ')
    return selected, membership


def source_remainder(mesh, removed):
    row = copy.deepcopy(mesh)
    row['indices'] = [i for ordinal in range(len(mesh['indices'])//3) if ordinal not in removed
                      for i in mesh['indices'][ordinal*3:ordinal*3+3]]
    require(row['verticesCm'] == mesh['verticesCm'] and row['uvs'] == mesh['uvs'], 'Original remainder arrays changed')
    return row


def candidate_geometry(village, targets, shapes, windows, selected, module):
    source = {m['id']: m for m in village['meshes']}
    meshes, wall_jobs, wall_audit, roof_audit = {}, [], [], []
    def chunk(identity, role, material):
        key = (identity,role,material)
        if key not in meshes:
            meshes[key] = Mesh('neighbor_r18_'+identity.replace('.','_')+'_'+role+'_'+material, material, identity, role)
        return meshes[key]
    for building in targets:
        identity = building['id']; mesh = source[building['wallMeshId']]
        rings = [module.base.canonical(poly[0]) for poly in building['polygonsCm']]
        edges = [(a,b) for ring in rings for a,b in zip(ring,ring[1:]+ring[:1])]
        for ordinal in selected[identity]['wall']:
            points = triangle_points(mesh,ordinal)
            edge = min(edges, key=lambda e: max(LineString(e).distance(Point(p[:2])) for p in points))
            require(max(LineString(edge).distance(Point(p[:2])) for p in points) < .002, 'Wall edge membership uncertain')
            a,b = edge; length=math.dist(a,b); tangent=[(b[k]-a[k])/length for k in (0,1)]
            outward=[tangent[1],-tangent[0]]
            projected = [[dot([p[k]-a[k] for k in (0,1)],tangent),p[2]] for p in points]
            polygon = Polygon(projected)
            openings = [rectangle(w['leftCm'],w['bottomCm'],w['rightCm'],w['topCm']) for w in windows
                        if w['buildingSourceId']==identity and math.dist(w['originCm'],a)<.002]
            cut = polygon.difference(unary_union(openings))
            pieces = [] if cut.is_empty else [cut] if cut.geom_type=='Polygon' else list(cut.geoms)
            require(all(p.geom_type=='Polygon' for p in pieces), 'Unexpected facade cut geometry')
            for piece in pieces:
                rings2 = [list(piece.exterior.coords)[:-1]] + [list(r.coords)[:-1] for r in piece.interiors]
                wall_jobs.append((identity,a,tangent,outward,rings2))
            wall_audit.append({'buildingSourceId':identity,'sourceMeshId':mesh['id'],'sourceTriangleOrdinal':ordinal,
                               'sourceProjectedAreaCm2':polygon.area,'retainedProjectedAreaCm2':cut.area,
                               'openingProjectedAreaCm2':polygon.area-cut.area})
        roof = source[building['roofMeshId']]; roof_out = chunk(identity,'roof','neighbor_roof_charcoal' if building['roofMaterial'].endswith('darkroof') else 'neighbor_roof_red')
        crease_edges = defaultdict(list)
        for ordinal in selected[identity]['roof']:
            points = triangle_points(roof,ordinal); normal=triangle_normal(points)
            if math.hypot(normal[0],normal[1])>.01:
                u=normalized([-normal[1],normal[0],0]);v=normalized(cross(normal,u))
            else:
                u=[1,0,0];v=[0,1,0]
            roof_out.triangle(points,normal,[[dot(p,u)/100,dot(p,v)/100] for p in points])
            for a,b in zip(points,points[1:]+points[:1]):
                key=tuple(sorted(tuple(round(x,5) for x in p) for p in (a,b)))
                crease_edges[key].append(normal)
        ridge_count, ridge_length, eave_count, eave_length = 0,0.,0,0.
        ridge=chunk(identity,'roof_ridge','neighbor_roof_charcoal' if building['roofMaterial'].endswith('darkroof') else 'neighbor_roof_red')
        fascia=chunk(identity,'roof_eave','neighbor_frame_paint')
        for endpoints,normals in crease_edges.items():
            a,b=[list(p) for p in endpoints];length=math.dist(a,b)
            if len(normals)==2 and dot(*normals)<.99 and min(a[2],b[2])>=building['eaveElevationCm']+building['estimatedRoofRiseCm']-2 and length>=80:
                module.tube(ridge,[a[0],a[1],a[2]+2],[b[0],b[1],b[2]+2],3.5,6)
                ridge_count+=1;ridge_length+=length
            if len(normals)==1 and abs(a[2]-building['eaveElevationCm'])<.01 and abs(b[2]-building['eaveElevationCm'])<.01:
                tangent=normalized([b[0]-a[0],b[1]-a[1]])
                outward=[tangent[1],-tangent[0]]
                mid=[(a[k]+b[k])/2 for k in (0,1)]
                if shapes[identity].covers(Point([mid[k]+outward[k]*2 for k in (0,1)])):
                    outward=[-x for x in outward]
                facade_box(fascia,a[:2],tangent,outward,0,length,a[2]-7,a[2],-2,1)
                eave_count+=1;eave_length+=length
        roof_audit.append({'buildingSourceId':identity,'baseRoofTriangles':len(selected[identity]['roof']),
                           'originalBasePositionsPreserved':True,'sourceHipBaseMassPreserved':True,
                           'newRidgeRuns':ridge_count,'newRidgeLengthCm':ridge_length,
                           'newEaveRuns':eave_count,'newEaveLengthCm':eave_length,
                           'roofSurfaceEvidence':'AUTHORED_PROCEDURAL_TILE_NOT_PHOTOGRAPHIC_ATLAS'})
    data=module.base.triangulate([job[-1] for job in wall_jobs])
    for job,triangulation in zip(wall_jobs,data):
        identity,a,tangent,outward,_=job
        wall=chunk(identity,'wall','neighbor_plaster_'+identity.replace('.','_'))
        for j in range(0,len(triangulation['indices']),3):
            uv=[triangulation['points'][i] for i in triangulation['indices'][j:j+3]]
            points=[[a[k]+tangent[k]*p[0] for k in (0,1)]+[p[1]] for p in uv]
            wall.triangle(points,[*outward,0],[[p[0]/100,p[1]/100] for p in uv])
    for w in windows:
        identity=w['buildingSourceId'];a=w['originCm'];t=w['tangent'];o=w['outward']
        left,right,bottom,top=[w[k] for k in ['leftCm','rightCm','bottomCm','topCm']];center=(left+right)/2
        def p(s,d,z): return [a[k]+t[k]*s+o[k]*d for k in (0,1)]+[z]
        reveal=chunk(identity,'window_reveal','neighbor_plaster_'+identity.replace('.','_'))
        for points,normal in [([p(left,0,bottom),p(left,-18,bottom),p(left,-18,top),p(left,0,top)],[*t,0]),
                              ([p(right,-18,bottom),p(right,0,bottom),p(right,0,top),p(right,-18,top)],[-t[0],-t[1],0]),
                              ([p(left,0,bottom),p(right,0,bottom),p(right,-18,bottom),p(left,-18,bottom)],[0,0,1]),
                              ([p(left,-18,top),p(right,-18,top),p(right,0,top),p(left,0,top)],[0,0,-1])]:
            reveal.face(points,normal)
        frame_material='context_boundary_post' if w['originalFrameMaterial']=='context_boundary_post' else 'neighbor_frame_paint'
        frame=chunk(identity,'window_frame',frame_material)
        for l,r,b,z in [(left,left+5,bottom,top),(right-5,right,bottom,top),(left,right,bottom,bottom+5),
                        (left,right,top-5,top),(center-2.5,center+2.5,bottom,top)]:
            facade_box(frame,a,t,o,l,r,b,z,-21,-15)
        sill=chunk(identity,'window_sill','neighbor_plaster_'+identity.replace('.','_'))
        facade_box(sill,a,t,o,left-10,right+10,bottom-14,bottom-8,-18,13)
        glass=chunk(identity,'window_glass','neighbor_window_dielectric')
        glass.face([p(left,-20,bottom),p(right,-20,bottom),p(right,-20,top),p(left,-20,top)],[*o,0])
        interior=chunk(identity,'window_backing','neighbor_interior_shadow')
        interior.face([p(left,-45,bottom),p(right,-45,bottom),p(right,-45,top),p(left,-45,top)],[*o,0])
        curtain=chunk(identity,'window_curtain','neighbor_curtain')
        fraction=.18 + .045*(w['sourceWindowIndex']%4)
        for l,r in [(left,left+(right-left)*fraction),(right-(right-left)*fraction,right)]:
            curtain.face([p(l,-38,bottom+5),p(r,-38,bottom+5),p(r,-38,top-5),p(l,-38,top-5)],[*o,0])
        w.update({'newRecessCm':20,'revealDepthCm':18,'backingDepthCm':45,'curtainDepthCm':38,
                  'wallOpeningActuallyCutInSource':True,'newGlassMaterial':'neighbor_window_dielectric',
                  'sourcePositionsAndBayCountRetained':True,'nativeApplied':False})
    records=[m.record for m in meshes.values() if m.record['indices']]
    require(sum(len(m['indices'])//3 for m in records)<10000, 'Candidate exceeds 10k total-triangle pilot budget')
    return records,wall_audit,roof_audit


def recipes(material_inputs, targets):
    plaster=copy.deepcopy(material_inputs['assets']['white_plaster_02'])
    palettes={'BU.572063':[.46,.43,.37],'BU.3800911':[.40,.405,.385],'BU.3852341':[.50,.465,.40]}
    result={}
    for b in targets:
        result['neighbor_plaster_'+b['id'].replace('.','_')]={
            'kind':'neighbor-plaster-scan','maps':plaster['maps'],'asset':'white_plaster_02',
            'license':'CC0-1.0','mapping':'AUTHORED_METRIC_FACADE_U_ALONG_EDGE_V_HEIGHT',
            'periodCm':100,'linearPalette':palettes[b['id']], 'albedoContrast':.075,
            'normalStrength':.2,'normalConvention':'OPENGL_GREEN_POSITIVE_V',
            'roughnessBase':.88,'roughnessMapAmplitude':.09,'metallic':0,'specular':.3,
            'aging':{'kind':'SOURCE_GROUND_ANCHORED_PLINTH_AND_RAINWATER_CONTACT','heightCm':55,
                     'maximumAlbedoDarkening':.075,'sourceGroundSamples':b['renderedGroundSamples'],
                     'notObservedWeathering':True},'nativeApplied':False}
    for name,palette in [('neighbor_roof_red',[.14,.052,.027]),('neighbor_roof_charcoal',[.03,.035,.037])]:
        result[name]={'kind':'neighbor-procedural-roof-tile','maps':{},'mapping':'METRIC_ROOF_FACET_U_EAVE_V_SLOPE',
                      'linearPalette':palette,'tileWidthCm':30,'tileCourseCm':40,'reliefHeightCm':.65,
                      'roughnessBase':.82,'roughnessVariation':.08,'albedoVariation':.06,'metallic':0,
                      'evidence':'PROJECT_AUTHORED_NOT_SCANNED_CERAMIC_ATLAS','nativeApplied':False}
    result['neighbor_window_dielectric']={'kind':'neighbor-window-dielectric','metallic':0,'roughness':.12,
                                          'indexOfRefraction':1.5,'linearTint':[.87,.9,.92],
                                          'blendProposal':'TRANSLUCENT','nativeShaderCompileVerified':False,'nativeApplied':False}
    result['neighbor_frame_paint']={'kind':'neighbor-coated-frame','linearPalette':[.045,.049,.045],
                                    'roughness':.48,'metallic':0,'specular':.35,'nativeApplied':False}
    result['neighbor_interior_shadow']={'kind':'neighbor-interior-backing','linearPalette':[.035,.029,.023],
                                       'roughness':.95,'metallic':0,'nativeApplied':False}
    result['neighbor_curtain']={'kind':'neighbor-curtain','linearPalette':[.34,.32,.28],
                               'roughness':.93,'metallic':0,'nativeApplied':False}
    return result


def decode_and_validate(records, targets, shapes, context, wall_audit, windows):
    protected=unary_union([Polygon(row) for row in context['protectedTrianglesCm']])
    road_triangles=[Polygon([p[:2] for p in triangle_points(m,i)]) for m in context['meshes']
                    if m['material']=='context_track' for i in range(len(m['indices'])//3)]
    roads=unary_union(road_triangles)
    max_reach,decoded,normal_error,uv_min=0.,0,0.,float('inf')
    candidate_wall_area=0.;minimum_road_distance=float('inf')
    for m in records:
        n=len(m['verticesCm']);require(n==len(m['uvs'])==len(m['normals'])==len(m['tangents'])==len(m['tangentHandedness']), 'Candidate attribute count differs')
        require(m['collision']=='NoCollision' and m['canEverAffectNavigation'] is False, 'Visual collision policy differs')
        shape=shapes[m['buildingSourceId']]
        for p in m['verticesCm']:
            require(all(math.isfinite(x) for x in p), 'Non-finite candidate point')
            reach=shape.distance(Point(p[:2]));max_reach=max(max_reach,reach)
            require(reach<=13.01 and protected.distance(Point(p[:2]))>20, 'Candidate leaves source building visual envelope/protected architecture')
            road_distance=roads.distance(Point(p[:2]));minimum_road_distance=min(minimum_road_distance,road_distance)
            require(road_distance>13, 'Candidate intrudes existing source road visual surface')
        for ordinal in range(len(m['indices'])//3):
            index=m['indices'][ordinal*3:ordinal*3+3];require(len(set(index))==3 and all(0<=i<n for i in index), 'Candidate indices differ')
            p=[m['verticesCm'][i] for i in index];normal=triangle_normal(p)
            if m['role']=='wall':
                a,b,c=p;area_vector=cross([b[k]-a[k] for k in range(3)],[c[k]-a[k] for k in range(3)])
                candidate_wall_area+=math.sqrt(dot(area_vector,area_vector))/2
            uv=[m['uvs'][i] for i in index]
            uv_area=abs((uv[1][0]-uv[0][0])*(uv[2][1]-uv[0][1])-(uv[2][0]-uv[0][0])*(uv[1][1]-uv[0][1]))/2
            uv_min=min(uv_min,uv_area);require(uv_area>1e-11, 'Collapsed candidate UV triangle')
            for i in index:
                error=max(abs(dot(m['normals'][i],m['normals'][i])-1),abs(dot(m['tangents'][i],m['tangents'][i])-1),abs(dot(m['normals'][i],m['tangents'][i])),abs(1-dot(normal,m['normals'][i])))
                normal_error=max(normal_error,error);require(error<1e-7 and m['tangentHandedness'][i] in [-1,1], 'Candidate tangent frame differs')
            decoded+=1
    expected=sum((w['rightCm']-w['leftCm'])*(w['topCm']-w['bottomCm']) for w in windows)
    actual=sum(x['openingProjectedAreaCm2'] for x in wall_audit)
    require(abs(expected-actual)<.01, '35 openings do not exactly partition the old facade area')
    retained=sum(x['retainedProjectedAreaCm2'] for x in wall_audit)
    require(abs(candidate_wall_area-retained)<.01, 'Decoded candidate wall triangles do not cover the exact retained source area')
    return {'sourceCandidateGeometryDecoded':True,'candidateTriangles':decoded,'maximumTangentFrameError':normal_error,
            'minimumUVTriangleArea':uv_min,'maximumOutwardVisualReachCm':max_reach,
            'windowOpeningProjectedAreaM2':actual/10000,'windowOpeningAreaPartitionErrorCm2':abs(actual-expected),
            'decodedCandidateWallAreaM2':candidate_wall_area/10000,
            'decodedCandidateWallAreaPartitionErrorCm2':abs(candidate_wall_area-retained),
            'minimumExistingSourceRoadDistanceCm':minimum_road_distance,
            'protectedMainArchitectureExcluded':True,'candidateWithinExistingBuildingVisualEnvelope':True,
            'nativeGeometryDecoded':False,'nativeSavedVerified':False,'nativeApplied':False,
            'nativeAppearanceAccepted':False,'performanceAccepted':False,'fullPhotorealismAccepted':False}


def plots(targets, shapes, windows, records, destination, module):
    font=ImageFont.load_default(size=20);small=ImageFont.load_default(size=15)
    image=Image.new('RGB',(1500,1100),'#efefe9');draw=ImageDraw.Draw(image)
    draw.text((28,20),'R18 THREE BUILDINGS / SOURCE PLAN ONLY / NATIVE PENDING',fill='#172622',font=font)
    draw.text((28,54),'Frozen approximate footprints/volumes; new finish proposal is not a survey or a rendered appearance.',fill='#42534c',font=small)
    bounds=unary_union(list(shapes.values())).bounds
    scale=min(1360/(bounds[2]-bounds[0]),900/(bounds[3]-bounds[1]))
    def p(xy):return (80+(xy[0]-bounds[0])*scale,1020-(xy[1]-bounds[1])*scale)
    colors=['#cbb78c','#b3beb4','#c8c3b9']
    for building,color in zip(targets,colors):
        shape=shapes[building['id']];draw.polygon([p(xy) for xy in shape.exterior.coords],fill=color,outline='#394541',width=3)
        center=p([shape.centroid.x,shape.centroid.y]);draw.text((center[0]-55,center[1]),building['id'],fill='#1e2924',font=small)
        for w in windows:
            if w['buildingSourceId']==building['id']:
                a=w['originCm'];t=w['tangent'];draw.line([p([a[k]+t[k]*s for k in (0,1)]) for s in [w['leftCm'],w['rightCm']]],fill='#076989',width=5)
    draw.text((28,1060),'Blue = 35 unchanged source-authored window bay positions. No fence, driveway or ownership geometry is invented.',fill='#253b34',font=small)
    image.save(destination/'source-plan.png')
    for b in targets:
        identity=b['id'];ws=[w for w in windows if w['buildingSourceId']==identity]
        longest=max(ws,key=lambda w:sum(x['originCm']==w['originCm'] for x in ws))
        edge_windows=[w for w in ws if w['originCm']==longest['originCm']]
        ring=module.base.canonical(b['polygonsCm'][0][0]);a=longest['originCm'];end=ring[(ring.index(a)+1)%len(ring)]
        length=math.dist(a,end);floor=b['eaveElevationCm']-b['estimatedWallHeightCm']
        canvas=Image.new('RGB',(1500,780),'#efefe9');d=ImageDraw.Draw(canvas)
        d.text((26,20),identity+' / SAME SOURCE FACADE / CUT + RECESSED WINDOW GEOMETRY',fill='#172622',font=font)
        d.text((26,52),'Orthographic source diagrams, not shader previews or native renders. Heights and positions remain authored estimates.',fill='#42534c',font=small)
        sc=min(1370/length,250/b['estimatedWallHeightCm'])
        for label,y,after in [('Frozen source: opaque metal cards on solid walls',370,False),('Candidate: openings + 20cm recess + reveals / curtain backing',710,True)]:
            d.text((35,y-290),label,fill='#243e34',font=small)
            def q(s,z):return (65+s*sc,y-(z-floor)*sc)
            d.rectangle([q(0,b['eaveElevationCm']),q(length,floor)],fill='#d1cab8',outline='#566058',width=2)
            for w in edge_windows:
                l,r,bt,tp=[w[k] for k in ['leftCm','rightCm','bottomCm','topCm']]
                d.rectangle([q(l,tp),q(r,bt)],fill='#3c443f' if after else '#747a75',outline='#eee9db',width=3)
                if after:
                    d.line([q(l,tp),q(l+7,tp-7),q(r-7,tp-7)],fill='#1b2520',width=3)
                    fraction=.18+.045*(w['sourceWindowIndex']%4)
                    for x1,x2 in [(l,l+(r-l)*fraction),(r-(r-l)*fraction,r)]:
                        d.rectangle([q(x1,tp-5),q(x2,bt+5)],fill='#a9a295')
                    d.line([q((l+r)/2,tp),q((l+r)/2,bt)],fill='#2c322e',width=4)
        canvas.save(destination/('facade-source-'+identity.replace('.','_')+'.png'))


def build():
    require(not DESTINATION.exists(), 'Destination already exists; frozen study must not be overwritten')
    pins={str(ROOT/path):expected for path,expected in SOURCES.values()}
    for path,expected in pins.items():require(sha(path)==expected,'Source pin differs: '+path)
    context,village,neighborhood,inputs,scene=[read(ROOT/SOURCES[k][0]) for k in ['context','village','neighborhood','materialInputs','scene']]
    active={'variant':'C','heatingLayout':'B','livingLayout':'B'}
    require(context['activeDesign']==village['activeDesign']==neighborhood['activeDesign']==scene['activeDesign']==active,'C/B/B differs')
    require(context['housePlacement']['streetSetbackMm']==context['housePlacement']['eastSetbackMm']==3000,'Setbacks differ')
    require(village['sourceSceneSha256']==neighborhood['sourceSceneSha256']==context['sourceSceneSha256']==SOURCES['scene'][1], 'Source frame differs')
    require(village['sourceObjSha256']==neighborhood['sourceObjSha256']==context['sourceObjSha256'],'Source architecture differs')
    require(context['sourceObjSha256']==SOURCES['architecturalObj'][1],'Pinned original architectural OBJ differs')
    pins[str(ROOT/'scripts/unreal/exterior-neighborhood.py')]=neighborhood['generatorSha256']
    module=load_module('neighbor_original_neighborhood','scripts/unreal/exterior-neighborhood.py')
    targets=[next(b for b in village['buildings'] if b['id']==identity) for identity in TARGETS]
    shapes={b['id']:unary_union([Polygon(poly[0],poly[1:]) for poly in b['polygonsCm']]) for b in targets}
    windows,removed_windows,replayed=replay_windows(village,neighborhood,module)
    selected,removed_base=select_base(village,targets,shapes)
    records,wall_audit,roof_audit=candidate_geometry(village,targets,shapes,windows,selected,module)
    material_recipes=recipes(inputs,targets)
    for recipe in material_recipes.values():
        for map_input in recipe.get('maps',{}).values():
            p=str(ROOT/map_input['path']);require(sha(p)==map_input['sha256'],'Local map drift: '+p);pins[p]=map_input['sha256']
    decoder=decode_and_validate(records,targets,shapes,context,wall_audit,windows)
    remainders=[];partitions=[]
    for family,data,removed in [('village',village,removed_base),('neighborhood',neighborhood,removed_windows)]:
        for m in data['meshes']:
            if m['id'] not in removed:continue
            remaining=source_remainder(m,removed[m['id']]);remainders.append(remaining)
            partitions.append({'family':family,'sourceMeshId':m['id'],'sourceMaterial':m['material'],
                               'sourceGeometrySha256':digest(m),'sourceTriangles':len(m['indices'])//3,
                               'removedTriangleOrdinals':sorted(removed[m['id']]),
                               'retainedTriangleOrdinals':[i for i in range(len(m['indices'])//3) if i not in removed[m['id']]],
                               'retainedTriangles':len(remaining['indices'])//3,'replacementRemainderSha256':digest(remaining),
                               'originalVerticesUVsIndicesOrderAndMaterialRetained':True,
                               'omitOldActorOnlyIfRemainderEmpty':not bool(remaining['indices'])})
    require(sum(len(p['removedTriangleOrdinals']) for p in partitions)==919, 'Exact 359-base/560-window partition differs')
    triangle_counts=Counter()
    for m in records:triangle_counts[m['role']]+=len(m['indices'])//3
    selected_audit=[]
    for b in targets:
        original=next(x for x in neighborhood['buildings'] if x['sourceId']==b['id'])
        selected_audit.append({'sourceId':b['id'],'sourceRecordSha256':digest(b),'sourceAreaM2':b['sourceAreaM2'],
                               'cell':b['cell'],'sourceHeightEvidence':b['heightEvidence'],'estimatedWallHeightCm':b['estimatedWallHeightCm'],
                               'estimatedRoofRiseCm':b['estimatedRoofRiseCm'],'eaveElevationCm':b['eaveElevationCm'],
                               'originalDetails':original['details'],'selectedBaseTriangleOrdinals':dict(selected[b['id']]),
                               'footprintUnchanged':True,'sourceBaseVolumeUnchanged':True})
    payload={'schemaVersion':1,'owner':OWNER,'status':'source-only-neighbor-finish-geometry-native-pending',
             'units':'UE_CENTIMETRES','candidateMeshes':records,'unchangedRemainderMeshes':remainders,
             'sourceTrianglePartitions':partitions,'windows':windows,'wallAreaAudit':wall_audit,'roofEdgeAudit':roof_audit}
    DESTINATION.mkdir(parents=True)
    write(DESTINATION/'neighbor-finish-geometry.json',payload);write(DESTINATION/'neighbor-finish-recipes.json',material_recipes)
    decoded_payload=read(DESTINATION/'neighbor-finish-geometry.json')
    require(digest(decoded_payload)==digest(payload),'Saved source geometry JSON differs')
    decoder=decode_and_validate(decoded_payload['candidateMeshes'],targets,shapes,context,decoded_payload['wallAreaAudit'],decoded_payload['windows'])
    plots(targets,shapes,windows,records,DESTINATION,module)
    validation={**decoder,'schemaVersion':1,'owner':OWNER,'status':'source-only-neighbor-finish-preflight-passed-native-pending',
                'exactOriginalDetailProducerReplay':replayed,'sourcePinsUnchanged':True,
                'baseTrianglePartition':{'selected':359,'wall':122,'redRoof':112,'charcoalRoof':125},
                'oldWindowTrianglesRetiredInProposal':560,'totalOldVisualTrianglesRetiredInProposal':919,
                'candidateTrianglesByRole':dict(triangle_counts),'nativeBudgetProof':False,
                'unchangedSourceArraysRetained':{'contextGroups':digest(context['groups']),
                    'boundaryPosts':digest(context['boundaryPosts']),'parcelBoundaries':digest(context['parcelBoundaries']),
                    'villageBuildings':digest(village['buildings']),'neighborhoodBuildings':digest(neighborhood['buildings'])}}
    write(DESTINATION/'source-validation.json',validation)
    payload_pins={str(p):sha(p) for p in sorted(DESTINATION.iterdir()) if p.is_file()}
    plan={'schemaVersion':1,'owner':OWNER,'status':'source-only-neighbor-finish-proposal-native-pending',
          'generatedAt':datetime.now(timezone.utc).isoformat(),'generatorSha256':sha(ROOT/OWNER),
          'activeDesign':active,'setbacksMm':{'street':3000,'east':3000},'sourceSceneSha256':context['sourceSceneSha256'],
          'sourceObjSha256':context['sourceObjSha256'],'inputFiles':pins,'payloadFiles':payload_pins,
          'targetBuildings':selected_audit,'sourceTrianglePartitions':partitions,'windowCount':35,
          'candidateTriangles':decoder['candidateTriangles'],'candidateTrianglesByRole':dict(triangle_counts),
          'netVisualTriangleChangeProposal':decoder['candidateTriangles']-919,'totalCandidateTriangleBudget':10000,
          'materialRecipeIds':list(material_recipes),'existingMaterialReferences':['context_boundary_post'],
          'futureNativeAssetPrefix':'/Game/Brezi/NeighborFinish20261001R18',
          'futureIntegration':{'operation':'REPLACE_SELECTED_359_BASE_AND_560_WINDOW_TRIANGLES_WITH_SPLIT_REMAINDERS_AND_CANDIDATE',
             'removeOldActorOnlyForEmptyRemainder':True,'keepUnselectedChunksAndArrays':True,
             'keepOriginalSelectedGuttersDownpipesEntrancesChimney':True,
             'newShaderAndSavedMeshValidationRequired':True,'actualNearCameraAppearanceReviewRequired':True,
             'newFencesOrDriveways':0,'newTracks':0,'terrainOrMainHouseChanges':0},
          'sourceSafeguards':decoder,'sourceTopologyValidation':validation['baseTrianglePartition'],
          'nativeApplied':False,'nativeGeometryDecoded':False,'nativeAppearanceAccepted':False,
          'performanceAccepted':False,'fullPhotorealismAccepted':False,
          'limits':['Selected buildings are approximate source massing from official two-dimensional footprints, not measured elevations or roof forms.',
                    'Windows, curtain positions, finish colors and weathering are authored visual estimates; physical trim extends up to 13cm from frozen footprint edges.',
                    'The source shows sampled terrain, including unresolved flat backdrop under BU.572063; terrain was not upgraded by this finish pilot.',
                    'Plaster maps are existing local pinned CC0 files; roof tile relief is procedural and no scanned ceramic atlas is claimed.',
                    'Material recipes are proposed types; no native graph compilation, transparency appearance, performance or saved geometry has been validated.',
                    'Plans/elevation plots are source diagrams, not rendered previews.',
                    'No fences, gardens, driveway ownership or infrastructure are inferred from illustrative legal boundary markings.']}
    for path,expected in pins.items():require(sha(path)==expected,'Source changed during study: '+path)
    write(DESTINATION/'neighbor-finish-plan.json',plan)
    print(json.dumps({'status':plan['status'],'destination':str(DESTINATION),'candidateTriangles':decoder['candidateTriangles'],
                      'removedSourceTriangles':919,'windows':35,'newMaterialRecipes':len(material_recipes),
                      'payloadFiles':len(payload_pins),'nativeApplied':False},indent=2))


if __name__=='__main__':
    build()
