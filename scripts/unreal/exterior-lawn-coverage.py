"""Continuous mown cover successor on the exact pinned managed source lawn.

The R6a study was visually rejected: sparse patch centers and destructive far
LOD blade thinning exposed the bright source floor. This fresh revision keeps
real bent/folded leaves but allocates geometry to overlapping low foliage, a
uniform continuous stochastic root population and coverage-preserving LODs.
No source ground, collision, architecture, unmanaged vegetation or old output
is changed. Photographic/native acceptance remains an explicit separate step.
"""
import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import importlib.util
import json
import math
from pathlib import Path
import random
import sys

import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OWNER = 'scripts/unreal/exterior-lawn-coverage.py'
SEED = 601226300013
MATERIAL = 'lawn_natural_blade'
SCREENS = [1., .025, .007]
BUDGET = 20000000


def load_module(name, path):
    if str(HERE) not in sys.path: sys.path.insert(0, str(HERE))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


natural = load_module('lawn_coverage_source', HERE/'exterior-lawn-natural.py')
require, sha, write = natural.require, natural.sha, natural.write


def read(path): return json.loads(Path(path).read_text())


def native_shape(source):
    return shapely.transform(source, lambda p: np.column_stack([p[:, 0]/10, -p[:, 1]/10]))


def source_shape(native):
    return shapely.transform(native, lambda p: np.column_stack([p[:, 0]*10, -p[:, 1]*10]))


def managed_source(geometry, rural_path, original_path):
    scene, faces, grass, forbidden, source, exclusions, extra = natural.source_domain(geometry)
    rural, original = read(rural_path), read(original_path)
    require(rural['metadata']['activeDesign'] == original['activeDesign'] == scene['activeDesign'], 'Managed C/B/B differs')
    require(rural['metadata']['housePlacement'] == original['housePlacement'] == scene['house']['placement'], 'Managed placement differs')
    require(rural['metadata']['sourceObjSha256'] == sha(geometry/'dom-mm.obj') == original['sourceObjSha256'], 'Managed OBJ frame differs')
    require(sha(rural_path.parent/'scene.json') == sha(geometry/'scene.json') == original['sourceSceneSha256'], 'Managed scene frame differs')
    require(sha(rural_path.parent/'dom-mm.obj') == sha(geometry/'dom-mm.obj'), 'Managed OBJ mirror differs')
    require(original['owner'] == 'scripts/unreal/exterior-lawn-natural.py' and
            shapely.equals_exact(source, shapely.from_geojson(original['lawnDomainSourceMm']), 1e-8), 'Original source lawn domain differs')
    polygons = rural['managedLawnKeepPolygonsCm']
    require(len(polygons) == 2, 'Managed keep polygon inventory differs')
    keep = unary_union([Polygon(p) for p in polygons])
    # Intersect the real lawn/exclusion union with the inherited rural keep;
    # remove zero-area line members at coincident edges, not polygon area.
    domain = native_shape(source).intersection(keep).buffer(0)
    require(domain.is_valid and 143 < domain.area/10000 < 144, 'Managed source area differs')
    return scene, faces, grass, forbidden, source, domain, exclusions, extra, polygons


def blade_parameters(variant, growth, compact=False):
    rng = random.Random(SEED + variant*1777 + int(compact)*8111)
    blades = []
    # 36 low and canopy leaves overlap between all stochastic patch centers.
    # Roots themselves are independently dispersed; there is no radial fan.
    for i in range(36):
        angle, radius = rng.uniform(0, math.tau), math.sqrt(rng.random())*(1.9 if compact else 5.4)
        low = i % 3 != 0
        clipped = rng.random() < .90
        height = rng.uniform(1.3, 2.3) if low else rng.uniform(2.9, 4.35)
        # Broad, leaning basal blades provide actual canopy area rather than
        # disguising a bare floor with a flat card or a different ground colour.
        width = rng.uniform(.36, .49) if low else rng.uniform(.23, .35)
        reach = rng.uniform(4.1, 5.8) if low else rng.uniform(2.0, 3.6)
        if compact:
            height *= .82; reach *= .28; width *= .88
        blades.append({'rootCm': [math.cos(angle)*radius, math.sin(angle)*radius],
            'angleRad': rng.uniform(-math.pi, math.pi), 'heightCm': height, 'widthCm': width,
            'reachCm': reach, 'curlCm': rng.uniform(-.35, .35)*( .32 if compact else 1),
            'twistRad': rng.uniform(-.20, .20), 'droop': rng.uniform(.09, .15),
            'clipped': clipped, 'low': low, 'dry': growth == 1 and rng.random() < .08,
            'tone': rng.uniform(.94, 1.), 'bladeSeed': rng.random()})
    return blades


def mesh(variant, growth, lod, compact=False):
    points, uv, uv1, colors, triangles, ranges = [], [], [], [], [], []
    for index, blade in enumerate(blade_parameters(variant, growth, compact)):
        segments = 3 if lod == 0 and not blade['low'] else 2
        columns = 3 if lod < 2 else 2
        start = len(points); centers = []
        for level in range(segments+1):
            t = level/segments
            angle = blade['angleRad'] + blade['twistRad']*t
            forward = np.array([math.cos(angle), math.sin(angle)])
            across = np.array([-forward[1], forward[0]])
            center = np.array(blade['rootCm']) + forward*blade['reachCm']*(.20*t+.80*t*t)
            center += across*blade['curlCm']*math.sin(math.pi*t)
            z = blade['heightCm']*(t + blade['droop']*math.sin(math.pi*t))
            centers.append([*center, z])
            # Finite clipped tips, tapering base and a broad central grass leaf.
            tip = .68 if blade['clipped'] else .045
            width = blade['widthCm']*(.54*(1-t) + tip*t + .48*math.sin(math.pi*t))
            rgb = np.array([.77+.20*t, .87+.13*t, .57+.16*t])
            if blade['dry']:
                rgb = rgb*(1-.45*t) + np.array([.99, .86, .60])*(.45*t)
            rgb *= blade['tone']
            if growth: rgb *= np.array([.995, .988, .975])
            for col in range(columns):
                u = col/(columns-1)
                p = center + across*width*(u-.5)
                fold = width*.10*math.sin(math.pi*u) if columns == 3 else 0
                points.append([float(p[0]), float(p[1]), z+fold])
                uv.append([u,t]); uv1.append([blade['bladeSeed'],float(growth)])
                colors.append([*np.clip(rgb,0,1).tolist(),1.])
            
        for level in range(segments):
            for col in range(columns-1):
                a = start+level*columns+col; b = a+columns
                triangles.extend([[a,a+1,b],[a+1,b+1,b]])
        ranges.append({'bladeIndex':index,'vertexOffset':start,'vertexCount':len(points)-start,
            'columns':columns,'segments':segments,'centerlineCm':centers,'clipped':blade['clipped'],
            'low':blade['low'],'dry':blade['dry'],'rootCm':blade['rootCm'],'widthCm':blade['widthCm']})
    record = {'nodeName':f'lawn_natural_{"edge_" if compact else ""}{growth}_{variant}_LOD{lod}',
        'variant':variant,'growthClass':growth,'edgeMaster':compact,'level':lod,
        'positionsCm':points,'uv0':uv,'uv1':uv1,'colors':colors,'triangles':triangles,'bladeRanges':ranges}
    record['expectedBoundsCm'] = {name:[op(p[k] for p in points) for k in range(3)] for name,op in [('min',min),('max',max)]}
    record['radialEnvelopeCm'] = max(math.hypot(*p[:2]) for p in points)
    return record


def placements(domain, prototypes):
    rng = np.random.default_rng(SEED); xmin,ymin,xmax,ymax = domain.bounds
    # A single continuous homogeneous point population covers both interior
    # and margins. No density islands and no independently stamped edge rows.
    count = int((xmax-xmin)*(ymax-ymin)/10000*565)
    x,y = rng.uniform(xmin,xmax,count),rng.uniform(ymin,ymax,count)
    inside = shapely.contains_xy(domain,x,y); x,y = x[inside],y[inside]
    distances = shapely.distance(shapely.points(x,y),domain.boundary)
    broad = natural.value_noise(x*10,-y*10,2150.,30179)
    medium = natural.value_noise(x*10,-y*10,690.,72917)
    height = .94 + .06*broad + .025*(medium-.5)
    dryness = natural.value_noise(x*10,-y*10,1850.,83407)
    lookup = {p['id']:p for p in prototypes}
    envelopes = {p['id']:max(l['radialEnvelopeCm'] for l in p['lods']) for p in prototypes}
    groups, occupied, rejected = {},defaultdict(list),Counter()
    radius_max = max(envelopes[k] for k in envelopes if not lookup[k]['edgeMaster'])
    margin, near = math.inf,0
    for a,b,d,h,dry in zip(x,y,distances,height,dryness):
        growth = int(dry>.74); scale = round(float(h*rng.uniform(.974,1.026)),6)
        compact = bool(d < radius_max*scale + .1)
        variant = int(rng.integers(2 if compact else 8))
        mid = f'lawn_natural_{"edge_" if compact else ""}{growth}_{variant}'
        radius = envelopes[mid]*scale
        if d <= radius+.1: rejected['whole-crown-managed-clearance'] += 1; continue
        cell = math.floor(a/2.4),math.floor(b/2.4)
        # 24mm prevents coincident centers but leaves irregular continuously
        # distributed roots. It does not impose a 60mm mesh or repeated grid.
        if any((a-q[0])**2+(b-q[1])**2 < 2.4**2 for dx in (-1,0,1) for dy in (-1,0,1)
               for q in occupied.get((cell[0]+dx,cell[1]+dy),[])):
            rejected['root-minimum-spacing'] += 1; continue
        occupied[cell].append((a,b)); row = lookup[mid]
        near += row['lods'][0]['triangles']; require(near <= BUDGET,'Lawn coverage near triangle budget exceeded')
        native = [round(float(a),5),round(float(b),5),-6.5]
        gid = f'EX_lawn_natural_{math.floor(a/2000)}_{math.floor(b/2000)}_{"edge_" if compact else ""}{growth}_{variant}'
        group = groups.setdefault(gid,{'id':gid,'meshId':mid,'role':'grass','cullEndCm':4000,
            'qualityDetail':True,'instances':[]})
        group['instances'].append({'positionCm':native,'yawDeg':round(float(rng.uniform(-180,180)),5),
            'scale':[scale]*3,'edge':compact,'clearanceMm':float(d)*10,
            'enclosingRadiusMm':radius*10+1,'radiusCm':radius,'actualHeightCm':row['heightCm']*scale,'growthClass':growth})
        margin = min(margin,(d-radius)*10-1)
    flat = [{'meshId':g['meshId'],**r} for g in groups.values() for r in g['instances']]
    require(38000 < len(flat) < 58000,'Unexpected continuous managed coverage population')
    budgets = [sum(len(g['instances'])*lookup[g['meshId']]['lods'][lod]['triangles'] for g in groups.values()) for lod in range(3)]
    centers = np.array([r['positionCm'][:2] for r in flat])*10
    phase = [float(abs(np.exp(2j*np.pi*centers[:,k]/60).mean())) for k in range(2)]
    require(max(phase)<.025,'Continuous cover unexpectedly repeats the old 60mm lattice')
    # Low-frequency variation changes growth slightly, never removes geometry.
    scales = np.array([r['scale'][0] for r in flat])
    return list(groups.values()),flat,{'instances':len(flat),'groups':len(groups),
        'edgeInstances':sum(r['edge'] for r in flat),'nearTriangleBudget':budgets[0],
        'allInstancesTriangleBudgetByLod':budgets,'minimumAdditionalCrownClearanceMm':margin,
        'exactAllowedDomainM2':domain.area/10000,'rootElevationCm':-6.5,
        'perMesh':dict(Counter(r['meshId'] for r in flat)), 'sixtyMmLatticePhaseAmplitudeXY':phase,
        'heightScaleRange':[float(scales.min()),float(scales.max())],'heightScaleStandardDeviation':float(scales.std()),
        'placementMethod':'One homogeneous continuous random dart population, 24mm minimum spacing; no density thinning or edge line population.',
        'fieldScalesMm':[690,1850,2150],'rejected':dict(rejected)}


def raster_coverage(records, rows, center, size_cm=100., resolution=4000):
    """Physical top-view triangle area from saved geometry, not root counts.

    Submillimetre raster samples cover a fixed 1m² interior lawn window.
    It captures individual leaves and uncovered floor in every explicit LOD.
    Geometry is transformed with the saved native uniform scale and yaw.
    """
    lookup = {r['nodeName']:r for r in records}
    center = np.asarray(center); lo = center-size_cm/2
    nearby = [r for r in rows if abs(r['positionCm'][0]-center[0])<size_cm/2+r['radiusCm'] and
              abs(r['positionCm'][1]-center[1])<size_cm/2+r['radiusCm']]
    masks = []
    for lod in range(3):
        image = Image.new('L',(resolution,resolution),0); draw = ImageDraw.Draw(image)
        for row in nearby:
            record = lookup[row['meshId']+'_LOD'+str(lod)]
            p = np.asarray(record['positionsCm'])[:,:2]*row['scale'][0]
            angle = math.radians(row['yawDeg']); c,s = math.cos(angle),math.sin(angle)
            rotation = np.array([[c,-s],[s,c]])
            p = ((p@rotation.T+row['positionCm'][:2]-lo)/size_cm*resolution).tolist()
            for face in record['triangles']: draw.polygon([tuple(p[i]) for i in face], fill=255)
        masks.append(np.asarray(image,dtype=np.uint8))
    # Record occupied fraction of every 10cm spatial bin to expose wide holes.
    result = []
    for lod, mask in enumerate(masks):
        fractions = (mask>0).reshape(10,resolution//10,10,resolution//10).mean(axis=(1,3))
        result.append({'lod':lod,'projectedCoverage':float((mask>0).mean()),
            'tenCmBinCoverageMinimum':float(fractions.min()),
            'tenCmBinCoverageP10':float(np.quantile(fractions,.1)),
            'bareTenCmBins':int((fractions<.20).sum())})
    return {'centerCm':center.tolist(),'sizeCm':size_cm,'resolution':resolution,
        'method':f'Saved individual triangle raster at{size_cm*10/resolution:g}mm, native positions/yaws/scales, full population, no floor mesh.',
        'instancesIntersectingWindow':len(nearby),'lods':result},masks


def coverage_receipt(records, rows, domain, prior_output, output):
    centers = [[-630.,-650.],[-950.,-860.],[-1180.,-950.],[-630.,-450.]]
    prior = read(prior_output/'lawn-natural-plan.json')
    prior_records = read(ROOT/'output/unreal/exterior-lawn-natural-20260930-r1/lawn-natural-prototypes.json')
    windows = []; atlas = Image.new('RGB',(900,4*230),(237,237,231)); draw=ImageDraw.Draw(atlas)
    for i,center in enumerate(centers):
        require(domain.contains(shapely.box(center[0]-50,center[1]-50,center[0]+50,center[1]+50)), 'Coverage window outside actual managed lawn')
        result,masks = raster_coverage(records,rows,center)
        before,_ = raster_coverage(prior_records,prior['lawnPlacements'],center)
        result['rejectedR6aStudy'] = before['lods']; windows.append(result)
        for lod,mask in enumerate(masks):
            require(result['lods'][lod]['projectedCoverage']>.70,'Insufficient continuous physical lawn coverage')
            require(result['lods'][lod]['tenCmBinCoverageP10']>.55,'Continuous lawn retains broad bare islands')
            rgb = np.zeros((*mask.shape,3),dtype=np.uint8); rgb[:] = [208,216,186];rgb[mask>0]=[63,97,45]
            tile = Image.fromarray(rgb).resize((215,215),Image.Resampling.BOX)
            atlas.paste(tile,(lod*300,i*230+15))
            draw.text((lod*300,i*230),f'ROI {i+1} LOD{lod}: {result["lods"][lod]["projectedCoverage"]:.1%}',fill=(25,35,20))
    atlas.save(output/'lawn-coverage-topview.png')
    return {'status':'PASS_STATIC_PHYSICAL_COVERAGE_NOT_NATIVE_ACCEPTED','windows':windows,
        'criteria':{'minimumTopViewCoverage':.70,'minimumTenCmBinP10':.55,'maximumPermittedBladeLossAcrossLods':0},
        'nativeAcceptanceRequired':'Same garden/detail/edge views, Cinematic density1; inspect floor gaps, rim continuity, mown silhouette and actual shading.'}


def build(geometry, rural_path, original_path, prior_output, output):
    geometry,rural_path,original_path,prior_output,output = map(lambda p:Path(p).resolve(),(geometry,rural_path,original_path,prior_output,output))
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Use fresh immutable lawn coverage output')
    scene,faces,grass,forbidden,source,domain,exclusions,extra,keep = managed_source(geometry,rural_path,original_path)
    records,prototypes = [],[]
    for compact in (False,True):
      for growth in range(2):
        for variant in range(2 if compact else 8):
            lods=[]
            for lod in range(3):
                r = mesh(variant,growth,lod,compact);records.append(r)
                lods.append({'level':lod,'nodeName':r['nodeName'],'vertices':len(r['positionsCm']),
                    'triangles':len(r['triangles']),'expectedBoundsCm':r['expectedBoundsCm'],
                    'radialEnvelopeCm':r['radialEnvelopeCm'],'blades':len(r['bladeRanges']), 'minimumCurveSegments':2})
            prototypes.append({'id':f'lawn_natural_{"edge_" if compact else ""}{growth}_{variant}',
                'role':'grass','placementPolicy':'explicit-only','heightCm':max(r['expectedBoundsCm']['max'][2] for r in lods),
                'materialKeys':[MATERIAL],'lodScreenSizes':SCREENS,'lods':lods,'growthClass':growth,'edgeMaster':compact,
                'composition':'36 overlapping individually bent mown grass leaves,24 low leaning/12 canopy; all36 retained everyLOD.'})
    groups,rows,audit = placements(domain,prototypes)
    inputs = {str(p):sha(p) for p in [Path(__file__),HERE/'exterior-lawn-natural.py',HERE/'lawn-geometry.py',
        HERE/'vegetation.py',HERE/'performance_scene_policy.py',geometry/'scene.json',geometry/'dom-mm.obj',
        rural_path,rural_path.parent/'scene.json',rural_path.parent/'dom-mm.obj',original_path,
        prior_output/'lawn-natural-plan.json',prior_output/'geometry-manifest.json',
        ROOT/'output/unreal/exterior-lawn-natural-20260930-r1/lawn-natural-prototypes.json']}
    common = {'schemaVersion':1,'owner':OWNER,'generatorSha256':sha(__file__), 'inputFiles':inputs,
        'activeDesign':scene['activeDesign'],'housePlacement':scene['house']['placement'],
        'sourceSceneSha256':sha(geometry/'scene.json'),'sourceObjSha256':sha(geometry/'dom-mm.obj'),
        'managedLawnPlan':{'path':str(rural_path),'sha256':sha(rural_path)},'managedLawnKeepPolygonsCm':keep,
        'derivedFrom':{'path':str(original_path),'sha256':sha(original_path)}}
    output.mkdir(parents=True)
    glb=output/'lawn-natural.glb'
    # Reuse only the immutable low-level tangent/GLB encoder, not old geometry
    # or patch generation. The in-memory generator label is this new creator.
    natural.OWNER=OWNER;natural.write_glb(glb,records)
    for row in prototypes:row.update(glbPath=str(glb),glbSha256=sha(glb))
    coverage = coverage_receipt(records,rows,domain,prior_output,output)
    write(output/'lawn-coverage-receipt.json',coverage)
    common['coverageReceipt']={'path':str(output/'lawn-coverage-receipt.json'),'sha256':sha(output/'lawn-coverage-receipt.json')}
    audit.update(status='PASS_STATIC_CONTINUOUS_MANAGED_GEOMETRY_NOT_NATIVE_ACCEPTED',nativeVerified=False,
        sourceAreaM2=grass.area/1e6,fullSourceLawnM2=source.area/1e6,
        unmanagedSourceLawnExcludedM2=source.area/1e6-domain.area/10000,sourceTriangles=len(faces),
        exclusionUnionM2=forbidden.area/1e6,sourceMasksUnchanged=True,managedLawnKeepPolygonsPreserved=True,
        allLodGeometryVertices=sum(len(r['positionsCm']) for r in records),
        allLodGeometryTriangles=sum(len(r['triangles']) for r in records),extraExclusionSourceIds=extra,
        crownProof='Every complete actual allLOD radial envelope inside exact DOM1/exclusions intersect pinned native rural keep union, plus1mm; WPO forbidden.',
        boundaryPlacement='Same homogeneous continuous dart population; compact variant adaptation, no independent border row.',
        leavesPerPatchEveryLod=36,lowLeaningLeavesPerPatch=24,physicalCoverage=coverage,
        densityPatchesPerM2=len(rows)/(domain.area/10000),bladesPerM2EveryLod=len(rows)*36/(domain.area/10000))
    geometry_manifest = {'schema':1,**common,'units':'metres','axes':'glTF Y-up; Unreal native = [100*x,100*z,100*y]',
        'status':'OFFLINE_NOT_NATIVE_ACCEPTED','meshes':prototypes,'revision':'Continuous curved mown cover R3'}
    recipe = deepcopy(read(prior_output/'material-manifest.json')[MATERIAL])
    recipe['source'] = 'Original project authored continuous mown grass leaves; new geometry and bounded vertex palette, no photographic pixel edits'
    recipe['artDirection'] = 'Physical basal cover and canopy preserved everyLOD; mild root-tip colouring without dark root multiplier islands.'
    plan = {'kind':'authored-natural-lawn-replacement',**common,'seed':SEED,'sourceLawnId':'DOM_00001',
        'sourceLawnMaterial':'MAT_0001','sourceElevationMm':-65,'sourceTriangleCount':len(faces),'exclusions':exclusions,
        'sourceLawnDomainSourceMm':shapely.to_geojson(source),'lawnDomainSourceMm':shapely.to_geojson(source_shape(domain)),
        'groups':groups,'lawnPlacements':rows,'lodScreenSizes':SCREENS,
        'renderingPolicy':deepcopy(read(prior_output/'lawn-natural-plan.json')['renderingPolicy']),
        'replacementPolicy':deepcopy(read(prior_output/'lawn-natural-plan.json')['replacementPolicy']),'audit':audit}
    write(output/'geometry-manifest.json',geometry_manifest)
    plan['geometryManifest']={'path':str(output/'geometry-manifest.json'),'sha256':sha(output/'geometry-manifest.json')}
    write(output/'material-manifest.json',{MATERIAL:recipe})
    write(output/'asset-manifest.json',{'schema':1,**common,
        'sources':[{'kind':'original-authored-geometry','generator':OWNER,'license':'Original project asset'}],
        'scope':'Exact inherited managed lawn only; no new botanical census or surveyed geometry claim.'})
    write(output/'lawn-natural-plan.json',plan,compact=True);write(output/'lawn-natural-prototypes.json',records,compact=True)
    write(output/'lawn-natural-audit.json',audit)
    manifest = {**common,'status':'PASS_STATIC_COVERAGE_NOT_NATIVE_ACCEPTED','geometryManifest':plan['geometryManifest'],
        'materialManifest':{'path':str(output/'material-manifest.json'),'sha256':sha(output/'material-manifest.json')},
        'plan':{'path':str(output/'lawn-natural-plan.json'),'sha256':sha(output/'lawn-natural-plan.json')},
        'geometryProof':{'path':str(output/'lawn-natural-prototypes.json'),'sha256':sha(output/'lawn-natural-prototypes.json')},
        'coverageReceipt':{'path':str(output/'lawn-coverage-receipt.json'),'sha256':sha(output/'lawn-coverage-receipt.json')},
        'glb':{'path':str(glb),'sha256':sha(glb)},'audit':audit,
        'integrationContract':'Same strict20 lawn_natural IDs/materialkey/LOD screens; fresh explicit-only GLB and managed groups. Hide exact4 inherited40437 lawninstances after identity checks; preserve native unmanaged vegetation and DOM1 ground/collision. Native garden/detail/edge acceptance still required.'}
    write(output/'lawn-natural-manifest.json',manifest)
    views=deepcopy(read(prior_output/'lawn-qa-views.json'))
    views.update(owner=OWNER,generatorSha256=sha(__file__),managedLawnPlan=common['managedLawnPlan'],
        plan=manifest['plan'],status='PASS_PRIVATE_MANAGED_LAWN_XY_ONLY_NOT_NATIVE_ACCEPTED')
    for view in views['views']:
        for key in ('eyeCm','targetCm'):require(domain.contains(shapely.Point(view[key][:2])),'Lawn camera escaped managed domain')
    write(output/'lawn-qa-views.json',views)
    return {k:v for k,v in audit.items() if k!='physicalCoverage'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--geometry',required=True);p.add_argument('--rural',required=True);p.add_argument('--original',required=True)
    p.add_argument('--prior',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();print(json.dumps(build(a.geometry,a.rural,a.original,a.prior,a.output)))
