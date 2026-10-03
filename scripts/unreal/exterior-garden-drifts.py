"""Add bounded, layered perennial drifts to the unchanged C/B/B mulch beds.

Keeps every primary garden root and transform byte-for-byte equivalent.  The
detail replaces the old uniformly random understory, using existing textured
3D assets, common isotropic all-LOD scaling and exact source surface heights.
Planting is an artistic garden proposal; it is not a measured botanical survey.
"""
import argparse
from collections import Counter
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import itertools
import json
import math
from pathlib import Path
import random

from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-drifts.py'
BED_IDS = ('DOM_01965', 'DOM_01966')


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as stream:
        stream.write(encode(value))


def surfaces(plan, scene):
    beds = {key: unary_union([Polygon([p[:2] for p in triangle]) for triangle in triangles
                             if Polygon([p[:2] for p in triangle]).area > 1e-7])
            for key, triangles in plan['sourceMulchTrianglesCm'].items()}
    require(set(beds) == set(BED_IDS), 'Only the two original mulch beds may be planted')
    steps = unary_union([Polygon([p[:2] for p in triangle])
                         for triangles in plan['sourceStepTrianglesCm'].values() for triangle in triangles
                         if Polygon([p[:2] for p in triangle]).area > 1e-7])
    terraces = [box((r['x0']-15200)/10, (10800-r['y1'])/10,
                    (r['x1']-15200)/10, (10800-r['y0'])/10)
                for item in [*scene['terraces'], scene['poolDeck']] for r in item['rectsMm']]
    terraces.append(Polygon([((p['x']-15200)/10, (10800-p['y'])/10)
                              for p in scene['pool']['copingFootprintMm']]))
    for surface in scene['surfaces'].values():
        if isinstance(surface, dict) and surface.get('polygonMm'):
            terraces.append(Polygon([((p['x']-15200)/10, (10800-p['y'])/10)
                                       for p in surface['polygonMm']]))
    return beds, steps, unary_union(terraces)


def envelope(mesh):
    lo = [min(lod['expectedBoundsCm']['min'][k] for lod in mesh['lods']) for k in range(3)]
    hi = [max(lod['expectedBoundsCm']['max'][k] for lod in mesh['lods']) for k in range(3)]
    radius = max(math.hypot(x, y) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]))
    return lo[2], hi[2]-lo[2], radius


def ground_height(triangles, xy):
    x, y = xy
    for triangle in triangles:
        if Polygon([p[:2] for p in triangle]).area <= 1e-7:
            continue
        if not Polygon([p[:2] for p in triangle]).covers(Point(x, y)):
            continue
        a, b, c = triangle
        den = (b[1]-c[1])*(a[0]-c[0]) + (c[0]-b[0])*(a[1]-c[1])
        w1 = ((b[1]-c[1])*(x-c[0]) + (c[0]-b[0])*(y-c[1]))/den
        w2 = ((c[1]-a[1])*(x-c[0]) + (a[0]-c[0])*(y-c[1]))/den
        return w1*a[2] + w2*b[2] + (1-w1-w2)*c[2]
    raise ValueError('Detail root is outside the original source triangles')


def build(base_path, assets_path, geometry, output):
    base_path, assets_path, geometry, output = [Path(p).resolve() for p in (base_path, assets_path, geometry, output)]
    require(output.is_relative_to(ROOT/'output/unreal'), 'Use isolated Unreal output')
    require(not output.exists(), 'Garden output is immutable; select a fresh directory')
    base = json.loads(base_path.read_text())
    library = json.loads(assets_path.read_text())
    scene_path, obj_path = geometry/'scene.json', geometry/'dom-mm.obj'
    scene = json.loads(scene_path.read_text())
    require(base['sourceSceneSha256'] == sha(scene_path) and base['sourceObjSha256'] == sha(obj_path),
            'Source geometry differs from the preserved primary planting')
    require(scene['activeDesign'] == {'variant':'C', 'heatingLayout':'B', 'livingLayout':'B'}, 'C/B/B is required')
    require(scene['housePlacement']['streetSetbackMm'] == scene['housePlacement']['eastSetbackMm'] == 3000,
            'Both 3000 mm setbacks must remain unchanged')
    require(len(base['ornamentalPlacements']) == 12, 'Exactly twelve primary compositions must remain')
    meshes = {m['id']: m for m in library['meshes']}
    beds, steps, hardscape = surfaces(base, scene)
    rng = random.Random(6012262026093007)
    placements, occupied = [], []

    def add(key, xy, mesh_id, target_height, band, phase):
        mesh = meshes[mesh_id]
        minimum_z, source_height, source_radius = envelope(mesh)
        # Every leaf keeps its native aspect ratio. No horizontal squeeze to fit.
        scale = target_height/source_height
        radius = source_radius*scale
        point = Point(xy)
        if not beds[key].covers(point) or point.distance(beds[key].boundary) < radius+4.01:
            return False
        if point.distance(steps) < radius+12.01 or point.distance(hardscape) < radius+12.01:
            return False
        primary = [r for r in base['ornamentalPlacements'] if r['sourceBedId'] == key]
        if band == 'middle':
            # Mid-height flowering drifts occupy real gaps, with no crown collisions.
            if any(math.dist(xy, r['positionCm'][:2]) < radius+r['radiusCm']+2.01 for r in primary):
                return False
            if any(other['layer']=='middle' and math.dist(xy, other['positionCm'][:2]) < radius+other['radiusCm']+2.01
                   for other in occupied):
                return False
        else:
            # Low leaf rosettes can naturally extend below tall crowns. Their roots
            # remain separate, and the planted bed still has deliberate mulch gaps.
            if any(math.dist(xy, r['positionCm'][:2]) < 13.5 for r in primary):
                return False
            if any(math.dist(xy, other['positionCm'][:2]) < 13.5 for other in occupied):
                return False
        z = ground_height(base['sourceMulchTrianglesCm'][key], xy)-minimum_z*scale+.08
        row = {'id':f'garden_drift_{len(placements):03}', 'sourceBedId':key,
               'role':mesh['role'], 'meshId':mesh_id, 'positionCm':[float(xy[0]), float(xy[1]), z],
               'scale':[scale]*3, 'uniformScale':scale, 'scaleUnits':'dimensionless Unreal transform',
               'heightCm':target_height, 'actualHeightCm':target_height, 'radiusCm':radius,
               'yawDeg':rng.uniform(0,360), 'cullEndCm':12000, 'collision':'NoCollision',
               'layer':band, 'drift':phase, 'sourceMinimumZCm':minimum_z,
               'sourceCrownRadiusCm':source_radius, 'groundSurfaceZCm':z+minimum_z*scale-.08,
               'evidence':'ILLUSTRATIVE_PERENNIAL_DRIFT_INSIDE_ORIGINAL_UNCHANGED_MULCH'}
        placements.append(row)
        occupied.append(row)
        return True

    # Mid-height perennial groups use alternating soft white and pink accents,
    # with the main tall flowers and grasses retained as the visual anchors.
    for key, bed in beds.items():
        xmin, ymin, xmax, ymax = bed.bounds
        for _ in range(6000):
            x, y = rng.uniform(xmin,xmax), rng.uniform(ymin,ymax)
            wave = math.sin(x/88+math.cos(y/112)) + .55*math.cos(y/74-x/181)
            if wave < -.1 or rng.random() > .40:
                continue
            phase = 'soft-white' if math.sin(x/155-y/138) > -.15 else 'pink-accent'
            candidate = ('ornamental_white_a' if rng.random()<.5 else 'ornamental_white_b') if phase=='soft-white' else (
                'garden_pink_r6_a' if rng.random()<.5 else 'garden_pink_r6_b')
            add(key, (x,y), candidate, rng.uniform(20,31), 'middle', phase)

    # Blue-noise-like jittered rejection sampling creates continuous rosette
    # carpets with curved warm-grass seams, instead of a species checkerboard.
    groundcover = [f'celandine_01_{letter}' for letter in 'abcde']
    grass = [f'grass_medium_02_{letter}' for letter in 'abc']
    for key, bed in beds.items():
        xmin, ymin, xmax, ymax = bed.bounds
        for _ in range(14000):
            x, y = rng.uniform(xmin,xmax), rng.uniform(ymin,ymax)
            field = .5+.28*math.sin(x/87+.75*math.sin(y/105))+.23*math.cos(y/73-x/164)
            if rng.random() > .55+.40*field:
                continue
            seam = abs(math.sin(x/137+y/91+.4*math.cos(y/157)))
            is_grass = seam < .20
            candidate = rng.choice(grass if is_grass else groundcover)
            height = rng.uniform(17,25) if is_grass else rng.uniform(12,21)
            add(key, (x,y), candidate, height, 'low', 'fine-grass-seam' if is_grass else 'leaf-carpet')

    require(200 <= len(placements) <= 550, 'Unexpected garden detail density')
    middle = [r for r in placements if r['layer']=='middle']
    require(len(middle) >= 6, f'Garden requires layered flowering drifts; found {len(middle)}')
    clearances = []
    for row in placements:
        point, radius = Point(row['positionCm'][:2]), row['radiusCm']
        clearances.append({'id':row['id'], 'bedEdgeCm':point.distance(beds[row['sourceBedId']].boundary)-radius,
                           'stepsCm':point.distance(steps)-radius, 'hardscapeCm':point.distance(hardscape)-radius})
    lod_triangles = [sum(meshes[r['meshId']]['lods'][level]['triangles'] for r in placements) for level in range(3)]
    audit = {'status':'PASS_OFFLINE_NOT_NATIVE', 'detailInstances':len(placements),
             'originalPrimaryPlacementsPreserved':12, 'midHeightPerennials':len(middle),
             'lowLeafAndGrassInstances':len(placements)-len(middle),
             'perBed':dict(Counter(r['sourceBedId'] for r in placements)),
             'perAsset':dict(Counter(r['meshId'] for r in placements)),
             'originalMulchAreaM2':sum(s.area for s in beds.values())/10000,
             'minimumFullCrownToBedEdgeCm':min(r['bedEdgeCm'] for r in clearances),
             'minimumFullCrownToStepsCm':min(r['stepsCm'] for r in clearances),
             'minimumFullCrownToHardscapeCm':min(r['hardscapeCm'] for r in clearances),
             'minimumDetailRootDistanceCm':min(math.dist(a['positionCm'][:2],b['positionCm'][:2])
                                               for a,b in itertools.combinations(placements,2)),
             'detailLodTriangleTotalsBeforeCulling':lod_triangles,
             'allDetailScalesUniform':True, 'sourceTexturePixelsChanged':False,
             'groundMethod':'Barycentric Z on the untouched original mulch triangles; 0.08 cm surface offset',
             'layerPolicy':'Low rosettes extend naturally under taller crowns; middle-height perennial crowns have 2 cm separation',
             'individual':clearances}
    garden = deepcopy(base)
    garden.update(owner=OWNER, revision='R7 layered garden drifts', generatedAt=datetime.now(timezone.utc).isoformat(),
                  generatorSha256=sha(__file__), gardenDetailPlacements=placements, gardenDetailAudit=audit,
                  gardenDetailPolicy={'replaceGenericGardenUnderstory':True, 'uniformAllLodScale':True,
                                      'sourceBedsUnchanged':list(BED_IDS), 'sourceMaterialsUnchanged':True,
                                      'nativeAppearanceAndPerformance':'PENDING'})
    garden['inputFiles'].update({str(p):sha(p) for p in (base_path, assets_path, scene_path, obj_path, Path(__file__))})
    for mesh_id in set(r['meshId'] for r in placements):
        row = meshes[mesh_id]
        require(sha(row['glbPath']) == row['glbSha256'], 'Frozen asset GLB changed')
        garden['inputFiles'][row['glbPath']] = row['glbSha256']
    require(garden['ornamentalPlacements'] == base['ornamentalPlacements'], 'Primary garden transforms changed')
    output.mkdir(parents=True)
    write(output/'garden-plan.json', garden)
    write(output/'garden-detail-audit.json', audit)
    summary = {'status':audit['status'], 'gardenPlan':str(output/'garden-plan.json'),
               'gardenPlanSha256':sha(output/'garden-plan.json'),
               **{k:v for k,v in audit.items() if k!='individual'}}
    write(output/'summary.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-plan', type=Path, required=True)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--geometry', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build(args.base_plan,args.assets,args.geometry,args.output)))
