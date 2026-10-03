"""Isolated natural lawn replacement on the unchanged authored C/B/B lawn.

The source lawn, collision, architectural objects and all exclusion masks remain
unchanged. New individual folded blades retain real curvature through every LOD.
Continuous stochastic patch centres and coherent growth fields replace the old
60 mm lawn grid. The generated library is explicit-only, with a separate native
instance plan; it never enters random meadow or ornamental asset selection.
"""
import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import struct

import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-lawn-natural.py'
MATERIAL = 'lawn_natural_blade'
SEED = 601226300010
ACTIVE = {'variant': 'C', 'livingLayout': 'B', 'heatingLayout': 'B'}
SCREENS = [1., .025, .007]
NEAR_TRIANGLE_BUDGET = 26000000


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value, compact=False):
    with Path(path).open('x') as stream:
        json.dump(value, stream, ensure_ascii=False, allow_nan=False,
                  indent=None if compact else 2, separators=(',', ':') if compact else None)
        stream.write('\n')


def source_module():
    path = ROOT / 'scripts/unreal/lawn-geometry.py'
    spec = importlib.util.spec_from_file_location('natural_lawn_source', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def source_domain(geometry):
    source = source_module()
    scene, faces, boundary, exclusions, extra = source.source_context(geometry)
    grass = unary_union([Polygon([p[:2] for p in triangle]) for triangle in faces])
    forbidden = unary_union([Polygon(row['polygonSourceMm']) for row in exclusions])
    domain = grass.difference(forbidden)
    require(domain.is_valid and 300e6 < domain.area < 400e6, 'Unexpected exact lawn domain')
    return scene, faces, grass, forbidden, domain, exclusions, extra


def value_noise(x, y, scale, seed):
    """Deterministic smooth nonperiodic value noise, source coordinates in mm."""
    x, y = np.asarray(x, dtype=float) / scale, np.asarray(y, dtype=float) / scale
    ix, iy = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    def corner(a, b):
        # Integer hashing is platform-independent; all arithmetic stays int64.
        h = np.bitwise_xor(a * 73856093, b * 19349663) ^ seed
        h = ((h ^ (h >> 13)) & 0xffffffff) * 1274126177
        return (h & 0xffffff).astype(float) / 0xffffff
    a, b, c, d = corner(ix, iy), corner(ix + 1, iy), corner(ix, iy + 1), corner(ix + 1, iy + 1)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def growth_fields(x, y):
    broad = value_noise(x, y, 1850., 21773)
    middle = value_noise(x, y, 470., 67337)
    fine = value_noise(x, y, 130., 92261)
    density = np.clip(.48 + .38 * broad + .20 * middle + .09 * (fine - .5), .48, .94)
    height = .75 + .26 * broad + .12 * middle + .05 * (fine - .5)
    dryness = value_noise(x, y, 1350., 81011)
    return density, height, dryness


def blade_parameters(variant, growth, edge=False):
    rng = random.Random(SEED + variant * 1777)
    result = []
    # Random dispersed roots have no golden-angle radial signature or lattice.
    for i in range(48):
        angle = rng.uniform(0, math.tau)
        radius = math.sqrt(rng.random()) * (1.0 if edge else 8.2)  # cm
        low = i % 3 == 0
        uncut = not low and rng.random() < .21
        height = rng.uniform(1.55, 2.85) if low else rng.uniform(5.3, 7.1) if uncut else rng.uniform(3.0, 5.35)
        width = rng.uniform(.30, .47) if low else rng.uniform(.17, .33)
        dry = growth == 1 and rng.random() < .24
        result.append({'rootCm': [math.cos(angle) * radius, math.sin(angle) * radius],
                       'angleRad': rng.uniform(-math.pi, math.pi), 'heightCm': height,
                       'widthCm': width, 'reachCm': rng.uniform(3.3, 6.6) if low else rng.uniform(1.5, 4.1),
                       'curlCm': rng.uniform(-.7, .7), 'twistRad': rng.uniform(-.45, .45),
                       'droop': rng.uniform(.14, .32), 'clipped': not uncut and rng.random() < .77,
                       'low': low, 'dry': dry, 'tone': rng.uniform(.77, 1.),
                       'segmentsNear': 4 if low else rng.choice([4, 5, 6]),
                       'bladeSeed': rng.random()})
        if edge:
            result[-1]['heightCm'] *= .68
            result[-1]['reachCm'] *= .23
            result[-1]['curlCm'] *= .18
    return result


def mesh(variant, growth, lod, edge=False):
    params = blade_parameters(variant, growth, edge)
    points, uv, uv1, colors, triangles, ranges = [], [], [], [], [], []
    for i, blade in enumerate(params):
        if lod == 2 and i % 2:
            continue
        segments = blade['segmentsNear'] if lod == 0 else 3 if lod == 1 else 2
        columns = 3 if lod < 2 else 2
        start = len(points)
        centers = []
        for level in range(segments + 1):
            t = level / segments
            angle = blade['angleRad'] + blade['twistRad'] * t
            forward = np.array([math.cos(angle), math.sin(angle)])
            across = np.array([-forward[1], forward[0]])
            center = np.array(blade['rootCm']) + forward * blade['reachCm'] * (.14 * t + .86 * t * t)
            center += across * blade['curlCm'] * math.sin(math.pi * t)
            z = blade['heightCm'] * (t + blade['droop'] * math.sin(math.pi * t))
            centers.append([*center, z])
            # Natural narrow base, broad midrib, physical clipped/pointed tip.
            tip = .54 if blade['clipped'] else .055
            width = blade['widthCm'] * (.36 * (1-t) + tip * t + .67 * math.sin(math.pi * t)**.8)
            healthy = np.array([.49 + .40*t, .61 + .35*t, .34 + .24*t])
            if blade['dry']:
                dry = np.array([.54 + .46*t, .49 + .34*t, .31 + .17*t])
                healthy = healthy * (1 - t*.87) + dry * (t*.87)
            if growth:
                healthy *= np.array([.96, .94, .90])
            rgb = np.clip(healthy * blade['tone'], 0, 1).tolist()
            for col in range(columns):
                u = col / (columns - 1)
                position = center + across * width * (u - .5)
                # A small longitudinal fold provides a real normal transition.
                fold = width * .19 * math.sin(math.pi * u) if columns == 3 else 0
                points.append([float(position[0]), float(position[1]), z + fold])
                uv.append([u, t]); uv1.append([blade['bladeSeed'], float(growth)])
                colors.append([*rgb, 1.])
        for level in range(segments):
            for col in range(columns - 1):
                a = start + level * columns + col
                b = a + columns
                triangles.extend([[a, a+1, b], [a+1, b+1, b]])
        ranges.append({'bladeIndex': i, 'vertexOffset': start, 'vertexCount': len(points)-start,
                       'columns': columns, 'segments': segments, 'centerlineCm': centers,
                       'clipped': blade['clipped'], 'low': blade['low'], 'dry': blade['dry'],
                       'rootCm': blade['rootCm'], 'widthCm': blade['widthCm']})
    record = {'nodeName': f'lawn_natural_{"edge_" if edge else ""}{growth}_{variant}_LOD{lod}', 'variant': variant, 'growthClass': growth,
              'edgeMaster': edge,
              'level': lod, 'positionsCm': points, 'uv0': uv, 'uv1': uv1, 'colors': colors,
              'triangles': triangles, 'bladeRanges': ranges}
    record['expectedBoundsCm'] = {name: [op(p[k] for p in points) for k in range(3)]
                                  for name, op in [('min', min), ('max', max)]}
    record['radialEnvelopeCm'] = max(math.hypot(*p[:2]) for p in points)
    return record


def basis(record):
    p, uv, triangles = map(np.asarray, (record['positionsCm'], record['uv0'], record['triangles']))
    normals, tangents, bitangents = np.zeros_like(p), np.zeros_like(p), np.zeros_like(p)
    for indices in triangles:
        a,b,c = indices
        e1,e2 = p[b]-p[a], p[c]-p[a]
        n = np.cross(e1,e2)
        d1,d2 = uv[b]-uv[a], uv[c]-uv[a]
        det = d1[0]*d2[1]-d1[1]*d2[0]
        require(np.dot(n,n)>1e-14 and abs(det)>1e-12, 'Degenerate natural blade face/UV')
        t,bt = (e1*d2[1]-e2*d1[1])/det, (e2*d1[0]-e1*d2[0])/det
        normals[indices] += n; tangents[indices] += t; bitangents[indices] += bt
    normals /= np.linalg.norm(normals,axis=1)[:,None]
    tangents -= normals * (normals*tangents).sum(axis=1)[:,None]
    tangents /= np.linalg.norm(tangents,axis=1)[:,None]
    signs = np.where((np.cross(normals,tangents)*bitangents).sum(axis=1)<0,-1.,1.)
    require(np.isfinite(normals).all() and np.isfinite(tangents).all(), 'Nonfinite tangent basis')
    return normals.tolist(), np.column_stack([tangents,signs]).tolist()


def write_glb(path, records):
    binary = bytearray()
    doc = {'asset': {'version': '2.0', 'generator': OWNER}, 'scene': 0,
           'scenes': [{'nodes': list(range(len(records)))}], 'nodes': [], 'meshes': [],
           'accessors': [], 'bufferViews': [], 'buffers': [], 'materials': [
               {'name': MATERIAL, 'doubleSided': True, 'pbrMetallicRoughness':
                {'baseColorFactor': [.06,.10,.024,1], 'metallicFactor': 0, 'roughnessFactor': .84}}]}
    def accessor(rows,kind,component=5126,target=34962):
        rows = np.asarray(rows, dtype='<f4' if component==5126 else '<u4')
        binary.extend(b'\0' * (-len(binary) % 4)); start=len(binary); binary.extend(rows.tobytes())
        view=len(doc['bufferViews'])
        doc['bufferViews'].append({'buffer':0,'byteOffset':start,'byteLength':len(binary)-start,'target':target})
        row={'bufferView':view,'componentType':component,'count':len(rows),'type':kind}
        if kind=='VEC3': row.update(min=rows.min(axis=0).tolist(),max=rows.max(axis=0).tolist())
        doc['accessors'].append(row); return len(doc['accessors'])-1
    def rotate(rows): return [[p[0],p[2],p[1]] for p in rows]
    for record in records:
        normals,tangents=basis(record)
        attrs={'POSITION':accessor(np.asarray(rotate(record['positionsCm']))*.01,'VEC3'),
               'NORMAL':accessor(rotate(normals),'VEC3'),
               'TANGENT':accessor([[*rotate([p[:3]])[0],-p[3]]for p in tangents],'VEC4'),
               'TEXCOORD_0':accessor(record['uv0'],'VEC2'), 'TEXCOORD_1':accessor(record['uv1'],'VEC2'),
               'COLOR_0':accessor(record['colors'],'VEC4')}
        idx=accessor([i for a,b,c in record['triangles'] for i in (a,c,b)],'SCALAR',5125,34963)
        doc['nodes'].append({'name':record['nodeName'],'mesh':len(doc['meshes'])})
        doc['meshes'].append({'name':record['nodeName'],'primitives':[{'attributes':attrs,'indices':idx,'material':0,'mode':4}]})
    binary.extend(b'\0' * (-len(binary)%4));doc['buffers']=[{'byteLength':len(binary)}]
    raw=json.dumps(doc,separators=(',',':'),allow_nan=False).encode();raw+=b' ' * (-len(raw)%4)
    with Path(path).open('xb') as stream:
        stream.write(struct.pack('<4sII',b'glTF',2,28+len(raw)+len(binary)) + struct.pack('<II',len(raw),0x4e4f534a)+raw
                     +struct.pack('<II',len(binary),0x004e4942)+binary)


def placements(domain, prototypes):
    rng=np.random.default_rng(SEED); xmin,ymin,xmax,ymax=domain.bounds
    # Pure continuous dart proposals, not a jittered lattice. Seeded thinning
    # and a local minimum spacing reject coincident patches without regular rows.
    candidates=int((xmax-xmin)*(ymax-ymin)/1e6*108)
    x=rng.uniform(xmin,xmax,candidates);y=rng.uniform(ymin,ymax,candidates)
    inside=shapely.contains_xy(domain,x,y);x,y=x[inside],y[inside]
    density,height,dryness=growth_fields(x,y)
    keep=rng.random(len(x))<density
    x,y,height,dryness=x[keep],y[keep],height[keep],dryness[keep]
    distances=shapely.distance(shapely.points(x,y),domain.boundary)
    envelopes={row['id']:max(l['radialEnvelopeCm']for l in row['lods'])for row in prototypes}
    lookup={row['id']:row for row in prototypes}; groups={}; occupied=defaultdict(list); rejected=Counter()
    min_margin=math.inf; near_budget=0; roots=[]; field_samples=[]
    def attempt(a,b,d,h,dry,edge=False):
        nonlocal min_margin,near_budget
        growth=int(dry>.74);variant=int(rng.integers(2 if edge else 8));mid=f'lawn_natural_{"edge_" if edge else ""}{growth}_{variant}'
        scale=float(h*rng.uniform(.91,1.08))
        if edge:
            scale=float(h*rng.uniform(.83,1.01))
        scale=round(scale,6)
        radius=envelopes[mid]*scale*10 + 1.  # enclosing every LOD vertex + 1 mm
        if d<=radius: rejected['entire-crown-clearance']+=1;return
        key=math.floor(a/55),math.floor(b/55)
        spacing=20. if edge else 51.
        if any((a-q[0])**2+(b-q[1])**2<spacing**2 for dx in (-1,0,1)for dy in (-1,0,1)
               for q in occupied.get((key[0]+dx,key[1]+dy),[])):
            rejected['patch-minimum-spacing']+=1;return
        row=lookup[mid];cost=row['lods'][0]['triangles']
        require(near_budget+cost<=NEAR_TRIANGLE_BUDGET,'Natural lawn near geometry budget exceeded')
        occupied[key].append((a,b));near_budget+=cost
        native=[round(a/10,5),round(-b/10,5),-6.5]
        yaw=float(rng.uniform(-180,180));cell=f'{math.floor(native[0]/2000)}_{math.floor(native[1]/2000)}'
        gid=f'EX_lawn_natural_{cell}_{"edge_" if edge else ""}{growth}_{variant}'
        group=groups.setdefault(gid,{'id':gid,'meshId':mid,'role':'grass','cullEndCm':4000,
                                    'qualityDetail':True,'instances':[]})
        group['instances'].append({'positionCm':native,'yawDeg':round(yaw,5),'scale':[scale]*3,
                                   'edge':edge,'clearanceMm':float(d),'enclosingRadiusMm':radius,
                                   'radiusCm':envelopes[mid]*scale,'actualHeightCm':row['heightCm']*scale,
                                   'growthClass':growth})
        min_margin=min(min_margin,d-radius);roots.append([a,b]);field_samples.append([scale,scale,growth,edge])
    for args in zip(x,y,distances,height,dryness):attempt(*map(float,args))
    # The exact polygon boundary supplies both sides; only the grass side and
    # complete crown pass. Irregular interval/offset avoids a dotted border.
    rings=[]
    for polygon in shapely.get_parts(domain):
        rings.extend([polygon.exterior,*polygon.interiors])
    for ring in rings:
        coordinates=list(ring.coords)
        for (ax,ay),(bx,by) in zip(coordinates,coordinates[1:]):
            length=math.hypot(bx-ax,by-ay)
            if length<8:continue
            along=float(rng.uniform(0,27))
            while along<length:
                offset=float(rng.uniform(30,68));t=along/length
                for sign in (-1,1):
                    a=ax+(bx-ax)*t-sign*(by-ay)/length*offset
                    b=ay+(by-ay)*t+sign*(bx-ax)/length*offset
                    if not shapely.contains_xy(domain,a,b):continue
                    d=domain.boundary.distance(shapely.Point(a,b));_,h,dry=growth_fields(a,b)
                    attempt(a,b,float(d),float(h),float(dry),True)
                along+=float(rng.uniform(27,56))
    roots=np.asarray(roots);fields=np.asarray(field_samples)
    require(16000<len(roots)<35000,'Natural lawn instance budget is unexpected')
    budgets=[sum(len(g['instances'])*lookup[g['meshId']]['lods'][lod]['triangles']for g in groups.values())for lod in range(3)]
    # Independent nearest-centre distribution and old-grid phase measure.
    bins=defaultdict(list)
    for index,(a,b)in enumerate(roots):bins[(math.floor(a/100),math.floor(b/100))].append(index)
    nearest=[]
    for index,(a,b)in enumerate(roots):
        bx,by=math.floor(a/100),math.floor(b/100);best=math.inf
        for reach in range(1,30):
            candidates=[q for dx in range(-reach,reach+1)for dy in range(-reach,reach+1)
                        for q in bins.get((bx+dx,by+dy),[])if q!=index]
            if candidates:best=float(np.linalg.norm(roots[candidates]-[a,b],axis=1).min())
            outside=min(a-(bx-reach)*100,(bx+reach+1)*100-a,b-(by-reach)*100,(by+reach+1)*100-b)
            if best<outside:break
        require(math.isfinite(best)and best<outside,'Nearest-root spatial proof did not converge')
        nearest.append(best)
    nearest=np.asarray(nearest)
    phase=[float(abs(np.exp(2j*np.pi*roots[:,axis]/60.).mean()))for axis in range(2)]
    require(max(phase)<.04,'A residual 60 mm lawn lattice was introduced')
    require(float(np.std(fields[fields[:,3]==0,1]))>.04,'Growth height field collapsed')
    return list(groups.values()),{'instances':len(roots),'groups':len(groups),'edgeInstances':int(fields[:,3].sum()),
           'perMesh':dict(Counter(g['meshId']for g in groups.values()for _ in g['instances'])),
           'nearTriangleBudget':budgets[0],'allInstancesTriangleBudgetByLod':budgets,
           'minimumAdditionalCrownClearanceMm':min_margin,'rootElevationCm':-6.5,
           'nearestPatchCentreDistanceMm':{'minimum':float(nearest.min()),'median':float(np.median(nearest)),
                'p95':float(np.quantile(nearest,.95)),'standardDeviation':float(nearest.std())},
           'sixtyMmLatticePhaseAmplitudeXY':phase,
           'interiorHeightScaleRange':[float(fields[fields[:,3]==0,1].min()),float(fields[fields[:,3]==0,1].max())],
           'interiorHeightScaleStandardDeviation':float(fields[fields[:,3]==0,1].std()),
           'coherentDryGrowthInstances':int(fields[:,2].sum()),'rejected':dict(rejected)}


def build(geometry,output):
    geometry,output=Path(geometry).resolve(),Path(output).resolve()
    require(output.is_relative_to(ROOT/'output/unreal')and not output.exists(),'Use a new isolated immutable output')
    scene,faces,grass,forbidden,domain,exclusions,extra=source_domain(geometry)
    records=[]; prototypes=[]
    for edge in (False,True):
      for growth in range(2):
        for variant in range(2 if edge else 8):
            lods=[]
            for lod in range(3):
                record=mesh(variant,growth,lod,edge); records.append(record)
                lods.append({'level':lod,'nodeName':record['nodeName'],'vertices':len(record['positionsCm']),
                             'triangles':len(record['triangles']),'expectedBoundsCm':record['expectedBoundsCm'],
                             'radialEnvelopeCm':record['radialEnvelopeCm'],
                             'blades':len(record['bladeRanges']),'minimumCurveSegments':min(b['segments']for b in record['bladeRanges'])})
            prototypes.append({'id':f'lawn_natural_{"edge_" if edge else ""}{growth}_{variant}','role':'grass','placementPolicy':'explicit-only',
                               'heightCm':max(row['expectedBoundsCm']['max'][2]for row in lods),'materialKeys':[MATERIAL],
                               'lodScreenSizes':SCREENS,'lods':lods,'growthClass':growth,'edgeMaster':edge,
                               'composition':'Actual dispersed individual folded grass blades; clipped and pointed mixed tips and lower leaning leaves.'})
    groups,audit=placements(domain,prototypes)
    inputs={str(p):sha(p)for p in [Path(__file__),ROOT/'scripts/unreal/lawn-geometry.py',
            ROOT/'scripts/unreal/vegetation.py',ROOT/'scripts/unreal/performance_scene_policy.py',
            geometry/'scene.json',geometry/'dom-mm.obj']}
    common={'schemaVersion':1,'owner':OWNER,'generatorSha256':sha(__file__),'activeDesign':scene['activeDesign'],
            'housePlacement':scene['house']['placement'],'sourceSceneSha256':sha(geometry/'scene.json'),
            'sourceObjSha256':sha(geometry/'dom-mm.obj'),'inputFiles':inputs}
    output.mkdir(parents=True);glb=output/'lawn-natural.glb';write_glb(glb,records)
    for row in prototypes:row.update(glbPath=str(glb),glbSha256=sha(glb))
    recipe={'kind':'authored-foliage','maps':{},'linearColor':[.06,.10,.024],
            'roughness':.84,'specular':.22,'subsurfaceScale':.16,'twoSided':True,
            'source':'Original project authored curved lawn blades with per-vertex root, midrib, tip and dry-leaf colours',
            'artDirection':'Bounded diffuse grass palette with coherent growth classes; no emission or wind displacement.'}
    geometry_manifest={**common,'schema':1,'units':'metres','axes':'glTF Y-up; Unreal native = [100*x,100*z,100*y]',
                       'status':'OFFLINE_NOT_NATIVE_ACCEPTED','meshes':prototypes,'revision':'Natural curved lawn R1'}
    plan={**common,'kind':'authored-natural-lawn-replacement','geometryManifest':{'path':str(output/'geometry-manifest.json')},
          'seed':SEED,'sourceLawnId':'DOM_00001','sourceLawnMaterial':'MAT_0001','sourceElevationMm':-65,
          'sourceTriangleCount':len(faces),'exclusions':exclusions,
          'lawnDomainSourceMm':shapely.to_geojson(domain),'groups':groups,'lodScreenSizes':SCREENS,
          'lawnPlacements':[{'meshId':group['meshId'],**row}for group in groups for row in group['instances']],
          'renderingPolicy':{'collision':'none','navigation':False,'windDisplacementCm':0,
              'qualityDetail':True,'densityScaling':True,'cullStartCm':3200,'cullEndCm':4000,
              'savedCastShadow':False,'savedVisibleInRayTracing':False},
          'replacementPolicy':{'hideOnlyVerifiedInheritedLawnActors':True,'inheritedLawnTag':'BreziPhotorealLawn',
              'inheritedLawnGroups':['LawnTuft0','LawnTuft1','LawnTuft2','LawnTuft3'],
              'sourceGroundAndCollisionUnchanged':True,'architectureUnchanged':True,
              'sharedOldBladeAssetsUnchanged':True,'meadowYardAndGardenUntouched':True},
          'audit':audit}
    audit.update(status='PASS_STATIC_GEOMETRY_AND_CLEARANCE',nativeVerified=False,
                 sourceAreaM2=grass.area/1e6,exactAllowedDomainM2=domain.area/1e6,
                 exclusionUnionM2=forbidden.area/1e6,sourceTriangles=len(faces),
                 sourceMasksUnchanged=True,extraExclusionSourceIds=extra,
                 allLodGeometryVertices=sum(len(row['positionsCm'])for row in records),
                 allLodGeometryTriangles=sum(len(row['triangles'])for row in records),
                 crownProof='Every instance enclosing circle covers every LOD vertex, with exact union/exclusion clearance plus 1 mm; WPO forbidden.',
                 boundaryPlacement='Irregular edge intervals and offsets, only inside the exact allowed domain',
                 fieldScalesMm=[130,470,1850],placementMethod='Continuous random dart proposals; smooth seeded density/height/growth fields; local 51 mm hard core. No lattice.')
    write(output/'geometry-manifest.json',geometry_manifest);plan['geometryManifest']['sha256']=sha(output/'geometry-manifest.json')
    write(output/'material-manifest.json',{MATERIAL:recipe})
    write(output/'asset-manifest.json',{'schema':1,**common,'sources':[{'kind':'original-authored-geometry',
          'generator':OWNER,'license':'Original project asset'}],'scope':'Only the exact existing maintained lawn domain; botanical illustration, not a vegetation survey.'})
    write(output/'lawn-natural-plan.json',plan,compact=True);write(output/'lawn-natural-prototypes.json',records,compact=True)
    write(output/'lawn-natural-audit.json',audit)
    manifest={**common,'status':'PASS_STATIC_NOT_NATIVE_ACCEPTED','geometryManifest':plan['geometryManifest'],
              'materialManifest':{'path':str(output/'material-manifest.json'),'sha256':sha(output/'material-manifest.json')},
              'plan':{'path':str(output/'lawn-natural-plan.json'),'sha256':sha(output/'lawn-natural-plan.json')},
              'geometryProof':{'path':str(output/'lawn-natural-prototypes.json'),'sha256':sha(output/'lawn-natural-prototypes.json')},
              'glb':{'path':str(glb),'sha256':sha(glb)},'audit':audit,
              'integrationContract':'Merge this explicit-only library into the frozen exterior plant manifest. Pin and append only this plan groups. Hide the four verified inherited BreziPhotorealLawn HISM actors by report identity; preserve original lawn ground/collision and all shared meadow assets. Respect per-mesh lodScreenSizes in import and readback.'}
    write(output/'lawn-natural-manifest.json',manifest)
    return audit


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--geometry',required=True);parser.add_argument('--output',required=True)
    args=parser.parse_args();print(json.dumps(build(args.geometry,args.output)))
