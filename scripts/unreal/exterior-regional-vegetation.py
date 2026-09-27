"""Ortho-derived canopy groups in an isolated revision of the frozen context.

Canopy regions are image interpretations; individual roots, sizes and species
are not surveyed. House/roads/buildings and exact source ground are protected.
This generator never executes Unreal or changes a historical output.
"""
import argparse
from collections import Counter
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import shutil
import sys

import numpy as np
from PIL import Image
import shapely
from shapely.geometry import Point, Polygon
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-regional-vegetation.py'
SOURCE = ROOT/'output/unreal/exterior-context-20260926-r7/context-plan.json'
TERRAIN = ROOT/'output/unreal/exterior-terrain-20260926-r4/terrain-plan.json'
BUILDINGS = ROOT/'output/unreal/exterior-buildings-20260926-r2/building-plan.json'
ORTHO = ROOT/'output/unreal/exterior-ortho-20260926-r1/orthophoto-manifest.json'
SCENE = ROOT/'output/unreal/realism-20260926-r5/geometry/scene.json'
REGIONS = ROOT/'scripts/unreal/regional-canopy/regions.json'
GROUND = {'context_fallow', 'context_meadow', 'context_crop', 'context_arable', 'context_track'}
ASSETS = ('regional_broadleaf_a', 'regional_upright_b', 'regional_orchard_c', 'regional_hedge_a')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def image_to_world(point, layer, annotation_size=(1600, 1600)):
    """Solve the frozen affine; imagery coordinates use pixel edges, V down."""
    u, v = [point[i]/annotation_size[i] for i in range(2)]
    a, b, c = layer['worldCmToUvRows'][0]
    d, e, f = layer['worldCmToUvRows'][1]
    determinant = a*e-b*d
    return [(e*(u-c)-b*(v-f))/determinant, (-d*(u-c)+a*(v-f))/determinant]


def world_to_pixel(point, layer):
    uv = [row[0]*point[0]+row[1]*point[1]+row[2] for row in layer['worldCmToUvRows']]
    return [uv[0]*layer['width'], uv[1]*layer['height']]


def asset_envelope(mesh):
    """Conservative full all-LOD boxes: one radial envelope for every yaw."""
    boxes = [lod['expectedBoundsCm'] for lod in mesh['lods']]
    low = [min(box['min'][i] for box in boxes) for i in range(3)]
    high = [max(box['max'][i] for box in boxes) for i in range(3)]
    radius = max(math.hypot(x, y) for x in (low[0], high[0]) for y in (low[1], high[1]))
    require(0 < radius < 1500 and 0 < high[2]-low[2] < 2000, 'Unexpected asset size')
    return {'min': low, 'max': high, 'radiusCm': radius, 'heightCm': high[2]-low[2]}


def crown_witness(point, radius, image, layer):
    """Source-colour evidence within curated canopy regions, not tree detection.

    Roads/roofs are separately excluded. This rejects bare holes or bright lawns
    inside the conservative manually digitised group polygons.
    """
    samples = [[0, 0]]
    for fraction, count in ((.4, 8), (.8, 16)):
        samples.extend([[radius*fraction*math.cos(i*math.tau/count), radius*fraction*math.sin(i*math.tau/count)] for i in range(count)])
    colors = []
    for delta in samples:
        px = world_to_pixel([point[i]+delta[i] for i in range(2)], layer)
        x, y = map(math.floor, px)
        if not (0 <= x < image.shape[1] and 0 <= y < image.shape[0]):
            return None
        colors.append([int(v) for v in image[y, x]])
    green = [a == 255 and g >= 25 and g > r*1.025 and g > b*1.08 and (.2126*r+.7152*g+.0722*b) < 132
             for r, g, b, a in colors]
    fraction = sum(green)/len(green)
    if not green[0] or fraction < .56 or any(color[3] != 255 for color in colors):
        return None
    return {'sourcePixelRgba': colors[0], 'sourcePixelXy': world_to_pixel(point, layer),
            'crownGreenSampleFraction': fraction, 'sampleCount': len(samples)}


def constraints(context, buildings, scene):
    convert = load_module(ROOT/'scripts/unreal/exterior-context.py', 'regional_c3')
    protected = unary_union([Polygon(tri) for tri in context['protectedTrianglesCm']])
    roads = []
    subject = []
    for parcel in context['parcels']:
        if parcel['parcelNumber'] not in ('6012/26', '6012/1', '6035/1', '6013', '6019'):
            continue
        for rings in parcel['polygonsSjtskMm']:
            polygon = Polygon([convert.to_unreal(p, scene) for p in rings[0]],
                              [[convert.to_unreal(p, scene) for p in hole] for hole in rings[1:]])
            (subject if parcel['parcelNumber'] == '6012/26' else roads).append(polygon)
    buildings = unary_union([Polygon(rings[0], rings[1:]) for building in buildings['buildings'] for rings in building['polygonsCm']])
    return {'protected': protected, 'subject': unary_union(subject), 'roads': unary_union(roads), 'buildings': buildings}


class GroundSampler:
    """Highest actual context/DMR triangle under each new root; no DEM guesses."""
    def __init__(self, context, terrain):
        self.triangles, self.ids, shapes = [], [], []
        for mesh in [m for m in context['meshes'] if m['material'] in GROUND]+terrain['meshes']:
            vertices = mesh['verticesCm']
            for i in range(0, len(mesh['indices']), 3):
                tri = [vertices[j] for j in mesh['indices'][i:i+3]]
                polygon = Polygon([p[:2] for p in tri])
                if polygon.area < 1e-6:
                    continue
                self.triangles.append(tri); self.ids.append(mesh['id']); shapes.append(polygon)
        self.index = STRtree(shapes)

    def sample(self, point):
        p = Point(point); candidates = []
        for index in self.index.query(p):
            tri = self.triangles[int(index)]
            a, b, c = tri
            denominator = (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
            u = ((b[0]-point[0])*(c[1]-point[1])-(b[1]-point[1])*(c[0]-point[0]))/denominator
            v = ((c[0]-point[0])*(a[1]-point[1])-(c[1]-point[1])*(a[0]-point[0]))/denominator
            w = 1-u-v
            if min(u, v, w) >= -1e-8:
                candidates.append((a[2]*u+b[2]*v+c[2]*w, self.ids[int(index)]))
        require(candidates, 'No rendered ground under canopy root: '+str(point))
        return max(candidates)


def understory(source):
    """Short irregular plants on exact nearby fallow/crop surfaces only."""
    records = {r['meshId']: r for r in source['surfaces'] if r['material'] in ('context_fallow', 'context_crop', 'context_arable')}
    shapes, triangles, coordinates, identities, per_surface = [], [], [], [], {}
    extent = Point(0, 0).buffer(7500, quad_segs=256)
    for mesh in source['meshes']:
        if mesh['id'] not in records:
            continue
        pieces = []
        for i in range(0, len(mesh['indices']), 3):
            tri = [mesh['verticesCm'][j] for j in mesh['indices'][i:i+3]]
            shape = Polygon([p[:2] for p in tri])
            if shape.area < .00001:
                continue
            pieces.append(shapely.set_precision(shape, .0001))
            triangles.append(shape); coordinates.append(tri); identities.append(mesh['id'])
        shape = unary_union(pieces).intersection(extent)
        if shape.area > 1:
            per_surface[mesh['id']] = shape; shapes.append(shape)
    domain = unary_union(shapes)
    protected = unary_union([Polygon(tri) for tri in source['protectedTrianglesCm']])
    safe = domain.buffer(-14.02).difference(protected.buffer(30.02))
    rng = np.random.default_rng(6012262026092708)
    grid = np.arange(-10800., 10801., 24.)
    xx, yy = np.meshgrid(grid, grid, indexing='ij')
    a = xx.ravel()+rng.uniform(-6, 6, xx.size)+3*np.sin(yy.ravel()/690)
    b = yy.ravel()+rng.uniform(-6, 6, xx.size)+3*np.sin(xx.ravel()/1100)
    angle = math.radians(17.3)
    x,y = math.cos(angle)*a-math.sin(angle)*b,math.sin(angle)*a+math.cos(angle)*b
    keep = np.hypot(x,y) <= 7486
    x,y = x[keep],y[keep]
    shapely.prepare(safe); keep = shapely.contains_xy(safe,x,y)
    x,y = x[keep],y[keep]
    broad = np.clip(.5+.28*np.sin(x/510+.4*np.sin(y/810))+.22*np.cos(y/730-x/1400),0,1)
    keep = rng.random(len(x)) < .90+.08*broad
    x,y,broad = x[keep],y[keep],broad[keep]
    points = shapely.points(x,y)
    edge = shapely.distance(points,domain.boundary)
    clearance = shapely.distance(points,protected)
    def smooth(value):
        t=np.clip(value,0,1);return t*t*(3-2*t)
    height = 2+(5+4*broad)*smooth((edge-14)/200)*(1-smooth((np.hypot(x,y)-6000)/1500))
    helper = load_module(ROOT/'scripts/unreal/exterior-meadow-blades.py','regional_understory_ground')
    z,ids = helper.sample_ground(x,y,triangles,np.asarray(coordinates),identities)
    yaw = rng.uniform(-180,180,len(x))
    placements = [{'role':'grass','positionCm':[float(a),float(b),float(c)],'heightCm':float(h),'radiusCm':14.,
                   'yawDeg':float(yaw_value),'sourceMeshId':identity,'sourceFinish':records[identity]['finish']}
                  for a,b,c,h,yaw_value,identity in zip(x,y,z,height,yaw,ids)]
    require(80000 <= len(placements) <= 90000,'Understory outside approved 80–90k budget')
    require(float(edge.min()) >= 14 and float(clearance.min()) >= 30,'Understory full crown escaped source geometry')
    counts=Counter(ids)
    policy={'evidence':'ILLUSTRATIVE_SEASONAL_SHORT_UNDERSTORY_NOT_MEASURED_VEGETATION',
            'instances':len(placements),'sourceMaterials':['context_fallow','context_crop','context_arable'],
            'gridSpacingCm':24,'jitterCm':6,'gridRotationDegrees':17.3,'radiusCm':14,
            'heightRangeCm':[float(height.min()),float(height.max())],'heightFeatherRadialCm':[6000,7500],
            'heightFeatherAtDomainEdgesCm':200,'minimumEdgeHeightCm':2,
            'maximumCrownRadiusFromOriginCm':float(np.hypot(x,y).max()+14),'cullStartCm':7500,'cullEndCm':9000,
            'minimumSourceEdgeClearanceCm':float(edge.min()),'minimumProtectedCenterClearanceCm':float(clearance.min()),
            'eligibleSurfaceAreaM2':domain.area/10000,'safeCenterAreaM2':safe.area/10000,
            'nativeRole':'Original nativeLawnTuft0–3 with existing blade material, full all-LOD footprint scaled to <=14cm',
            'groundMethod':'Exact barycentric Z on the unchanged crop/fallow source triangles',
            'perSurface':[{'meshId':key,'parcelNumber':records[key]['parcelNumber'],'instances':counts[key],'areaM2':shape.area/10000} for key,shape in per_surface.items()]}
    return placements,policy


def build(assets_path):
    source, terrain, buildings, ortho, scene, annotations, assets = map(read, (SOURCE, TERRAIN, BUILDINGS, ORTHO, SCENE, REGIONS, assets_path))
    require(sha(SOURCE) == 'ac86af5212ae0fdde515baad434407de50b2ded1263432239566d9ca1e9edbf6', 'Frozen R7 changed')
    require(source['sourceSceneSha256'] == terrain['sourceSceneSha256'] == sha(SCENE), 'Source scene differs')
    require(source['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'C/B/B required')
    require(source['housePlacement']['streetSetbackMm'] == source['housePlacement']['eastSetbackMm'] == 3000, 'Setbacks changed')
    mesh_map = {row['id']: row for row in assets['meshes'] if row['id'] in ASSETS}
    require(set(mesh_map) == set(ASSETS), 'Regional canopy asset set incomplete')
    envelopes = {key: asset_envelope(mesh) for key, mesh in mesh_map.items()}
    layer = next(v for v in ortho['layers'] if v['id'] == 'detail2km')
    require(sha(layer['rgbaPath']) == layer['rgbaSha256'] and layer['sourceCurrencyYear'] == 2024, 'Ortho pixels/currency differ')
    image = np.array(Image.open(layer['rgbaPath']))
    blocked = constraints(source, buildings, scene)
    all_blocked = unary_union(list(blocked.values()))
    sampler = GroundSampler(source, terrain)
    placements, region_records, rejected = [], [], Counter()
    # Spatial hash permits overlap of foliage but not coincident root clusters.
    root_cells = {}
    for region in annotations['regions']:
        polygon = Polygon([image_to_world(p, layer, annotations['annotationImageSize']) for p in region['polygon']])
        require(polygon.is_valid and polygon.area > 0, 'Invalid annotated region: '+region['id'])
        bounds = polygon.bounds
        rng = random.Random(int(hashlib.sha256(region['id'].encode()).hexdigest()[:16], 16))
        count = 0
        for attempt in range(region['budget']*120):
            if count >= region['budget']:
                break
            p = [rng.uniform(bounds[0], bounds[2]), rng.uniform(bounds[1], bounds[3])]
            point = Point(p)
            if region['form'] == 'hedge':
                mesh_id = ASSETS[3]; desired_height = rng.uniform(125, 205)
            elif region['form'] == 'orchard':
                mesh_id = ASSETS[2]; desired_height = rng.uniform(400, 570)
            else:
                mesh_id = rng.choices(ASSETS[:3], [65, 25, 10])[0]
                desired_height = rng.uniform(540, 940) if mesh_id != ASSETS[2] else rng.uniform(420, 570)
            envelope = envelopes[mesh_id]
            scale = desired_height/envelope['heightCm']
            radius = envelope['radiusCm']*scale
            if not polygon.contains(point) or point.distance(polygon.boundary) < radius+10:
                rejected['canopyRegionBoundary'] += 1; continue
            if math.hypot(*p)+radius > 110000:
                rejected['distanceBudget'] += 1; continue
            if point.distance(all_blocked) < radius+75:
                rejected['protectedRoadHouseBuilding'] += 1; continue
            witness = crown_witness(p, radius, image, layer)
            if not witness:
                rejected['sourceImageColourOrCoverage'] += 1; continue
            cell = (math.floor(p[0]/1000), math.floor(p[1]/1000))
            nearby = [row for x in range(cell[0]-2, cell[0]+3) for y in range(cell[1]-2, cell[1]+3) for row in root_cells.get((x, y), [])]
            if any(math.dist(p, row['positionCm'][:2]) < max(120, .65*(radius+row['radiusCm'])) for row in nearby):
                rejected['rootSpacing'] += 1; continue
            z, ground_id = sampler.sample(p)
            root_offset = envelope['min'][2]*scale
            row = {'id': region['id']+'_'+str(count), 'regionId': region['id'], 'form': region['form'], 'meshId': mesh_id,
                   'positionCm': [p[0], p[1], z-root_offset], 'yawDeg': rng.uniform(-180, 180), 'scale': [scale]*3,
                   'heightCm': desired_height, 'radiusCm': radius, 'cullEndCm': 125000 if region['form'] != 'hedge' else 90000,
                   'sourceEvidence': '2024_ORTHOPHOTO_CANOPY_GROUP_INFERRED_ROOT_SIZE_AND_SPECIES_NOT_SURVEYED',
                   'renderedGround': {'zCm': z, 'meshId': ground_id, 'assetMinimumZOffsetCm': root_offset,
                                      'measuredElevation': ground_id.startswith('context_distant_terrain_')},
                   'sourceImageWitness': witness,
                   'clearanceCm': {key: point.distance(shape)-radius for key, shape in blocked.items()},
                   'canopyRegionEdgeClearanceCm': point.distance(polygon.boundary)-radius}
            placements.append(row); root_cells.setdefault(cell, []).append(row); count += 1
        region_records.append({**region, 'polygonCm': [list(p) for p in polygon.exterior.coords[:-1]],
                               'areaM2': polygon.area/10000, 'placedCount': count})
    require(len(placements) >= 400, 'Too little confirmed canopy coverage; review regions/assets')
    # Retain the already authored four garden-margin roots, clearly separate
    # from observed canopy groups. A naturally slender prototype stays uniform.
    old_trees = [row for row in source['treePlacements'] if row['semantic'] == 'garden-margin-tree']
    mesh_id = 'regional_upright_b'; envelope=envelopes[mesh_id]
    for index,old in enumerate(old_trees):
        point=Point(old['positionCm'][:2]);distance=point.distance(all_blocked)
        radius=min(150.,distance-20.)
        require(radius >= 80,'Retained garden tree root has insufficient crown space')
        scale=radius/envelope['radiusCm']; z,ground_id=sampler.sample(old['positionCm'][:2])
        offset=envelope['min'][2]*scale
        placements.append({'id':'retained_garden_margin_'+str(index),'regionId':'retained_garden_margin_concept',
            'form':'garden-margin-concept','meshId':mesh_id,'positionCm':[*old['positionCm'][:2],z-offset],
            'yawDeg':old['yawDeg'],'scale':[scale]*3,'heightCm':envelope['heightCm']*scale,'radiusCm':radius,
            'cullEndCm':90000,'sourceEvidence':'RETAINED_ILLUSTRATIVE_GARDEN_PLANTING_CONCEPT_NOT_SURVEYED',
            'originalPlacementId':old['id'],'requiredProtectedCrownClearanceCm':20,
            'renderedGround':{'zCm':z,'meshId':ground_id,'assetMinimumZOffsetCm':offset,'measuredElevation':False},
            'clearanceCm':{key:point.distance(shape)-radius for key,shape in blocked.items()}})
    result = copy.deepcopy(source)
    changed = {'owner', 'generatorSha256', 'derivedFrom', 'treePlacements'}
    result.update(owner=OWNER, generatorSha256=sha(__file__), regionalVegetationPlacements=placements)
    result['meadowUnderstoryPlacements'],result['meadowUnderstoryPolicy']=understory(source)
    removed = [row for row in source['treePlacements'] if row['semantic'] == 'garden-margin-tree']
    require(len(removed) == 4, 'Unexpected old tree replacement scope')
    result['treePlacements'] = [row for row in source['treePlacements'] if row['semantic'] != 'garden-margin-tree']
    result['derivedFrom'] = {'path': str(SOURCE), 'sha256': sha(SOURCE),
                             'preservedFieldHashes': {key: digest(value) for key, value in source.items() if key not in changed},
                             'changeScope': 'Replace four old tree assets at retained illustrative roots, add ortho-derived regional canopy groups and short understory on exact fallow/crop surfaces; all ground meshes, parcels, vineyard rows/trellises and original meadow blades unchanged',
                             'removedGardenMarginTrees': removed}
    paths = [SOURCE, TERRAIN, BUILDINGS, ORTHO, SCENE, REGIONS, Path(assets_path), Path(__file__), ROOT/'scripts/unreal/exterior-context.py', ROOT/'scripts/unreal/exterior-meadow-blades.py']
    inputs = {str(p.resolve()): sha(p) for p in paths}
    for mesh in mesh_map.values():
        require(sha(mesh['glbPath']) == mesh['glbSha256'], 'Regional GLB changed')
        inputs[mesh['glbPath']] = mesh['glbSha256']
    inputs.update(ortho['inputFiles'])
    result['inputFiles'] = inputs
    result['regionalVegetationPolicy'] = {'assetManifestPath': str(Path(assets_path).resolve()), 'assetManifestSha256': sha(assets_path),
        'sourceOrthoManifest': str(ORTHO), 'sourceOrthoManifestSha256': sha(ORTHO), 'sourceCurrencyYear': 2024,
        'attribution': ortho['license']['displayCredit'], 'evidence': annotations['evidence'], 'precision': annotations['precision'],
        'regions': region_records, 'assetEnvelopesCm': envelopes, 'exclusionClearanceCm': 75,
        'canopyBoundaryClearanceCm': 10, 'maximumDistanceCm': 110000,
        'retainedGardenConcept': {'count':4,'meshId':mesh_id,'maximumRadiusCm':150,'minimumProtectedCrownClearanceCm':20,
                                 'meaning':'Existing authored garden-margin roots retained; small young slender-tree size is constrained by full uniform all-LOD crown, not claimed from orthophoto'},
        'sourceColourWitness': '25 samples within each conservative full all-LOD crown circle, centre green and >=56% green samples, all provider alpha255; this filters holes within curated canopy regions, not botanical detection',
        'rootSpacing': '>= max(120cm,0.65*(sum of neighbouring all-LOD radial envelopes)); crown overlap allowed for continuous groups',
        'ground': 'Highest barycentric Z on exact retained context ground or frozen rendered terrain; asset lowest all-LOD bound touches this height',
        'noSpeciesOrIndividualTreeSurveyClaim': True, 'collision': 'NoCollision', 'rejectedCandidates': dict(rejected)}
    counts = Counter(row['meshId'] for row in placements)
    summary = {'status': 'native-compatible-not-native-verified', 'placements': len(placements), 'byMesh': dict(counts),
               'regionCount': len(region_records), 'nonemptyRegions': sum(row['placedCount'] > 0 for row in region_records),
               'heightRangeCm': [min(row['heightCm'] for row in placements), max(row['heightCm'] for row in placements)],
               'radiusRangeCm': [min(row['radiusCm'] for row in placements), max(row['radiusCm'] for row in placements)],
               'minimumProtectedCrownClearanceCm': min(min(row['clearanceCm'].values()) for row in placements),
               'minimumRegionEdgeClearanceCm': min(row['canopyRegionEdgeClearanceCm'] for row in placements if 'canopyRegionEdgeClearanceCm' in row),
               'sourceContextSha256': sha(SOURCE), 'preservedMeadowBlades': len(result['meadowBladePlacements']),
               'preservedVineyardEntries': len(result['treePlacements']), 'removedIllustrativeTrees': len(removed),
               'understoryInstances':len(result['meadowUnderstoryPlacements']),
               'understoryHeightRangeCm':result['meadowUnderstoryPolicy']['heightRangeCm'],
               'nativeExecution': False}
    return result, summary


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--assets', required=True); parser.add_argument('--output', required=True)
    args = parser.parse_args(); output = Path(args.output).resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Use a fresh isolated output directory')
    plan, summary = build(Path(args.assets).resolve())
    output.mkdir(parents=True); (output/'inputs').mkdir()
    for name in ('cuzk-parcels.gml', 'source-receipt.json'):
        shutil.copyfile(SOURCE.parent/'inputs'/name, output/'inputs'/name)
    with (output/'context-plan.json').open('xb') as stream:
        stream.write((json.dumps(plan,separators=(',',':'),ensure_ascii=False,allow_nan=False)+'\n').encode())
    with (output/'summary.json').open('xb') as stream:stream.write(encode(summary))
    import shapely
    receipt = {'pythonExecutable': sys.executable, 'pythonVersion': sys.version, 'numpyVersion': np.__version__,
               'shapelyVersion': shapely.__version__, 'geosVersion': shapely.geos_version_string,
               'files': {str(Path(module.__file__).resolve()): sha(module.__file__) for module in (np, shapely)},
               'generatorSha256': sha(__file__), 'contextPlanSha256': sha(output/'context-plan.json')}
    with (output/'build-environment.json').open('xb') as stream: stream.write(encode(receipt))
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
