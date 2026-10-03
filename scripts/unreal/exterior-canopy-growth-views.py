"""Append one static grove-floor diagnostic camera on pinned rendered geometry.

The camera retains the same framing with connected canopy growth and unflared ecology.
Its source-ground audit does not certify native shading or the separate visual litter overlay.
It creates no walking route, tree, collision, geometry or native Unreal asset.
Rendered backdrop elevation and interpreted tree roots are not survey evidence.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import sys

import numpy as np
from PIL import Image, ImageDraw
import shapely
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
OWNER = 'scripts/unreal/exterior-canopy-growth-views.py'
REGION = 'village_nearest_grove'
STATUS = 'PASS_STATIC_ECOLOGY_CAMERA_GEOMETRY_NATIVE_PENDING'
sys.path.insert(0, str(HERE))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def pin(path): return {'path': str(Path(path).resolve()), 'sha256': sha(path)}


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, ensure_ascii=False, allow_nan=False)
        stream.write('\n')


def helper():
    spec = importlib.util.spec_from_file_location('ecology_view_ground', HERE/'exterior-regional-vegetation.py')
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def verified_inputs(paths):
    """Resolve common architectural frame and exact original 78-row identity."""
    data = {key: read(path) for key, path in paths.items()}
    context, terrain, buildings, scene, ecology, canopy, diagnostic = (
        data[key] for key in ('Context', 'Terrain', 'Buildings', 'Scene', 'Ecology', 'Canopy', 'Diagnostic'))
    require(context['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'C/B/B required')
    require(context['activeDesign'] == scene['activeDesign'] == ecology['activeDesign'] == canopy['activeDesign'], 'Architectural frame differs')
    placement = context['housePlacement']
    require(placement == scene['house']['placement'] == ecology['housePlacement'] == canopy['housePlacement'], 'Placement differs')
    require(placement['streetSetbackMm'] == placement['eastSetbackMm'] == 3000, 'Setbacks differ')
    require(sha(paths['Scene']) == context['sourceSceneSha256'] == terrain['sourceSceneSha256'] == buildings['sourceSceneSha256']
            == ecology['sourceSceneSha256'] == canopy['sourceSceneSha256'], 'Scene pin differs')
    require(sha(paths['Scene'].parent/'dom-mm.obj') == context['sourceObjSha256'] == ecology['sourceObjSha256']
            == canopy['sourceObjSha256'], 'Source OBJ differs')
    require(ecology['owner'] == 'scripts/unreal/exterior-canopy-ecology-unflared.py' and ecology['kind'] == 'grove-ground-ecology', 'Wrong ecological source')
    require(canopy['owner'] == 'scripts/unreal/exterior-canopy-growth.py' and canopy['kind'] == 'isolated-grove-canopy-growth-study', 'Wrong canopy source')
    require(ecology['regionId'] == canopy['regionId'] == REGION, 'Wrong grove')
    require(all(row['ecologyFamily'] != 'flare' for row in ecology['ecologyPlacements']), 'Decorative flares must remain omitted')
    require(ecology['audit']['instances'] == 24773 and ecology['audit']['groups'] == 130, 'Unflared source census differs')
    original = [row for row in context['regionalVegetationPlacements'] if row['regionId'] == REGION]
    require(len(original) == 78 and ecology['existingTrees'] == canopy['originalCanopyPlacements'] == original, 'Original grove rows differ')
    require(len(canopy['canopyPlacements']) == 78, 'Replacement table differs')
    for old, new in zip(original, canopy['canopyPlacements']):
        require(new['sourceMeshId'] == old['meshId'] and
                {k: v for k, v in new.items() if k not in ('meshId', 'sourceMeshId')} ==
                {k: v for k, v in old.items() if k != 'meshId'}, 'Grove root metadata changed')
    require(len(diagnostic['views']) == 3 and {v['id'] for v in diagnostic['views']} ==
            {'exterior-canopy-close', 'exterior-canopy-lod', 'exterior-canopy-grove'}, 'Prior diagnostic inventory differs')
    require(diagnostic['status'] == 'PASS_STATIC_CAMERA_GEOMETRY_AND_PLAN_REVIEW_NATIVE_PENDING', 'Prior diagnostic review differs')
    inputs = {str(path): sha(path) for path in paths.values()}
    for plan in (ecology, canopy):
        require(plan['sourceContext'] == pin(paths['Context']), 'Source context differs')
        for path, expected in plan['inputFiles'].items():
            require(sha(path) == expected, 'Source dependency drift: '+path)
            require(path not in inputs or inputs[path] == expected, 'Ambiguous source dependency')
            inputs[path] = expected
        manifest = plan['geometryManifest']
        require(sha(manifest['path']) == manifest['sha256'], 'Geometry manifest drift')
        inputs[manifest['path']] = manifest['sha256']
        for row in read(manifest['path'])['meshes']:
            require(sha(row['glbPath']) == row['glbSha256'], 'Source GLB drift')
            inputs[row['glbPath']] = row['glbSha256']
    inputs[str(Path(__file__).resolve())] = sha(__file__)
    inputs[str(HERE/'exterior-regional-vegetation.py')] = sha(HERE/'exterior-regional-vegetation.py')
    return data, original, inputs


class SolidTriangles:
    """Exact segment test against unchanged rendered ground and building faces."""
    def __init__(self, context, terrain, buildings, regional):
        triangles, ids = [], []
        meshes = buildings['meshes']+terrain['meshes']+[m for m in context['meshes'] if m['material'] in regional.GROUND]
        for mesh in meshes:
            vertex = np.asarray(mesh['verticesCm'], dtype=float)
            index = np.asarray(mesh['indices'], dtype=int).reshape(-1, 3)
            triangles.extend(vertex[index]); ids.extend([mesh['id']]*len(index))
        self.triangles, self.ids = np.asarray(triangles), ids
        self.edge1 = self.triangles[:, 1]-self.triangles[:, 0]
        self.edge2 = self.triangles[:, 2]-self.triangles[:, 0]

    def blockers(self, eye, target):
        eye = np.asarray(eye); ray = np.asarray(target)-eye
        cross = np.cross(np.broadcast_to(ray, self.edge2.shape), self.edge2)
        determinant = np.einsum('ij,ij->i', self.edge1, cross)
        valid = abs(determinant) > 1e-8
        inverse = np.divide(1., determinant, out=np.zeros_like(determinant), where=valid)
        offset = eye-self.triangles[:, 0]
        u = inverse*np.einsum('ij,ij->i', offset, cross)
        q = np.cross(offset, self.edge1)
        v = inverse*np.einsum('j,ij->i', ray, q)
        fraction = inverse*np.einsum('ij,ij->i', self.edge2, q)
        hits = np.flatnonzero(valid & (u >= -1e-9) & (v >= -1e-9) & (u+v <= 1+1e-9) &
                             (fraction > 1e-5) & (fraction < 1-1e-5))
        return [{'meshId': self.ids[int(i)], 'fraction': float(fraction[i])} for i in hits]


def frustum_features(view, ecology):
    """Conservative bounds identify useful small features; pixels decide visibility."""
    library = {row['id']: row for row in read(ecology['geometryManifest']['path'])['meshes']}
    eye = np.asarray(view['eyeCm']); forward = np.asarray(view['targetCm'])-eye
    forward /= np.linalg.norm(forward)
    right = np.cross(forward, [0, 0, 1]); right /= np.linalg.norm(right); up = np.cross(right, forward)
    horizontal = math.tan(math.radians(view['horizontalFovDegrees']/2)); vertical = horizontal/(16/9)
    visible = []
    for row in ecology['ecologyPlacements']:
        master = library[row['meshId']]
        lo = np.min([lod['expectedBoundsCm']['min'] for lod in master['lods']], axis=0)
        hi = np.max([lod['expectedBoundsCm']['max'] for lod in master['lods']], axis=0)
        corners = np.asarray([[x, y, z] for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])])
        angle = math.radians(row['yawDeg']); c, s = math.cos(angle), math.sin(angle)
        rotation = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        points = corners@rotation.T*row['scale'][0]+np.asarray(row['positionCm'])-eye
        z, x, y = points@forward, points@right, points@up
        wholly_out = any((np.all(z <= 0), np.all(x > z*horizontal), np.all(-x > z*horizontal),
                          np.all(y > z*vertical), np.all(-y > z*vertical)))
        distance = math.dist(eye, row['positionCm'])
        if not wholly_out and distance < 800:
            visible.append({'meshId': row['meshId'], 'ecologyFamily': row['ecologyFamily'],
                            'positionCm': row['positionCm'], 'distanceCm': distance})
    return {'nearEightMetreIntersectingBounds': len(visible),
            'nearEightMetreFeaturesByFamily': dict(Counter(r['ecologyFamily'] for r in visible)),
            'nearestFeatureDistanceCm': min(r['distanceCm'] for r in visible),
            'limit': 'Conservative all-LOD bounds at 16:9; actual leaf alpha, vegetation occlusion, shading and native LOD selection require rendered review.'}


def camera_audit(view, data, original):
    regional = helper(); context, terrain, buildings, scene, ecology = (
        data[key] for key in ('Context', 'Terrain', 'Buildings', 'Scene', 'Ecology'))
    sampler = regional.GroundSampler(context, terrain)
    eye, target = np.asarray(view['eyeCm']), np.asarray(view['targetCm'])
    require(view['id'] == 'exterior-canopy-floor' and view['source'] == OWNER and view['horizontalFovDegrees'] == 55., 'Unreviewed floor view')
    require(all(np.isfinite(p).all() and p.shape == (3,) for p in (eye, target)), 'Invalid coordinates')
    require(200 < float(np.linalg.norm(target-eye)) < 400, 'Floor details outside review distance')
    domain = shapely.from_geojson(ecology['ecologyDomainCm'])
    corridor = LineString([eye[:2], target[:2]])
    require(domain.contains(corridor.buffer(20)), 'Camera corridor leaves existing ecology domain')
    blocked = regional.constraints(context, buildings, scene)
    blocked['cultivatedGround'] = shapely.from_geojson(ecology['exclusionDomainsCm']['cultivatedGround'])
    clearance = {key: float(corridor.distance(value)) for key, value in blocked.items() if not value.is_empty}
    require(min(clearance.values()) >= 100, 'Camera corridor crosses protected/private/road/building/cultivated land')
    ground = []
    for fraction in np.linspace(0, 1, 65):
        p = eye+(target-eye)*fraction; z, identity = sampler.sample(p[:2])
        ground.append({'fraction': float(fraction), 'positionCm': p.tolist(), 'groundZCm': z,
                       'meshId': identity, 'clearanceCm': float(p[2]-z),
                       'measuredElevation': identity.startswith('context_distant_terrain_')})
    require(60 <= ground[0]['clearanceCm'] <= 100 and ground[-1]['clearanceCm'] >= 12-1e-7, 'Camera/target ground clearance differs')
    require(min(row['clearanceCm'] for row in ground) >= 12-1e-7, 'Centre line crosses rendered ground')
    solid = SolidTriangles(context, terrain, buildings, regional); hits = solid.blockers(eye, target)
    require(not hits, 'Rendered solid blocks centre line')
    root = next(row for row in original if row['id'] == view['targetTreeId'])
    root_distance = math.dist(eye[:2], root['positionCm'][:2])
    require(200 <= root_distance <= 400 and math.dist(target[:2], root['positionCm'][:2]) >= 50, 'Basal root framing differs')
    # The camera is deliberately inside the existing conservative crown union.
    # Ground feature vegetation can enter the frame; this is a static diagnostic.
    nearest_root = min(math.dist(eye[:2], row['positionCm'][:2]) for row in original)
    require(nearest_root > 150, 'Camera too close to an existing trunk root')
    features = frustum_features(view, ecology)
    require(all(features['nearEightMetreFeaturesByFamily'].get(key, 0) > 0 for key in ('litter', 'twig', 'herb', 'grass')), 'View misses ecological detail families')
    return {'viewId': view['id'], 'targetOriginalTree': deepcopy(root),
            'eyeHeightAboveRenderedGroundCm': ground[0]['clearanceCm'],
            'eyeGroundMeshId': ground[0]['meshId'], 'eyeGroundZCm': ground[0]['groundZCm'],
            'eyeGroundMeasured': ground[0]['measuredElevation'],
            'targetGroundMeshId': ground[-1]['meshId'], 'targetGroundZCm': ground[-1]['groundZCm'],
            'targetGroundMeasured': ground[-1]['measuredElevation'],
            'targetDistanceMetres': float(np.linalg.norm(target-eye))/100,
            'targetRootDistanceMetres': root_distance/100,
            'nearestOriginalRootDistanceCm': nearest_root,
            'centreLineExclusionClearanceCm': clearance,
            'minimumEcologyDomainCorridorClearanceCm': float(corridor.distance(domain.boundary)),
            'minimumCentreRayGroundClearanceCm': min(row['clearanceCm'] for row in ground),
            'centreRayGroundSamples': ground, 'centreRaySolidBlockers': hits,
            'rayTestTriangleCount': len(solid.triangles), **features}


def chart(path, view, ecology):
    root = next(row for row in ecology['existingTrees'] if row['id'] == view['targetTreeId'])
    centre = np.asarray(root['positionCm'][:2]); image = Image.new('RGB', (900, 900), '#ecebe3'); draw = ImageDraw.Draw(image)
    def px(point): return tuple(np.rint([450+(point[0]-centre[0])*.75, 450-(point[1]-centre[1])*.75]).astype(int))
    for row in ecology['ecologyPlacements']:
        q = px(row['positionCm']); radius = max(1, round(row['radiusCm']*.75))
        if -radius < q[0] < 900+radius and -radius < q[1] < 900+radius:
            color = {'flare': '#6a5043', 'litter': '#a79b71', 'twig': '#684d35', 'herb': '#51734c', 'grass': '#7d8c59'}[row['ecologyFamily']]
            draw.ellipse((q[0]-radius, q[1]-radius, q[0]+radius, q[1]+radius), outline=color)
    eye, target = px(view['eyeCm']), px(view['targetCm'])
    draw.line((eye, target), fill='#9c2e26', width=4)
    for point, label in ((eye, '80cm camera'), (target, '12cm floor target'), (px(root['positionCm']), 'unchanged root _3')):
        draw.ellipse((point[0]-5, point[1]-5, point[0]+5, point[1]+5), fill='#912c22')
        draw.text((point[0]+10, point[1]-5), label, fill='#171717')
    draw.text((20, 20), 'Existing grove ecology / 12m square / source XY only, not native acceptance', fill='#171717')
    image.save(path)


def build(context, terrain, buildings, scene, ecology, canopy, diagnostic, output):
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Output must be a fresh output/unreal directory')
    paths = {key: Path(value).resolve() for key, value in zip(
        ('Context', 'Terrain', 'Buildings', 'Scene', 'Ecology', 'Canopy', 'Diagnostic'),
        (context, terrain, buildings, scene, ecology, canopy, diagnostic))}
    data, original, inputs = verified_inputs(paths)
    root = next(row for row in original if row['id'] == 'village_nearest_grove_3')
    xy = np.asarray(root['positionCm'][:2]); eye_xy, target_xy = xy+[0, -280], xy+[0, -60]
    sampler = helper().GroundSampler(data['Context'], data['Terrain'])
    z, _ = sampler.sample(eye_xy); tz, _ = sampler.sample(target_xy)
    view = {'id': 'exterior-canopy-floor', 'label': 'Podrasť hája · kontakt so zemou',
            'eyeCm': [*eye_xy.tolist(), z+80], 'targetCm': [*target_xy.tolist(), tz+12],
            'horizontalFovDegrees': 55., 'source': OWNER, 'targetRegionId': REGION,
            'targetTreeId': root['id'],
            'rationale': 'Low static 80cm view, 2.8m from the unchanged root, observes basal contact, individual litter, twigs and low living leaves at useful scale.'}
    audit = camera_audit(view, data, original)
    result = {'schemaVersion': 1, 'owner': OWNER, 'generatorSha256': sha(__file__), 'status': STATUS,
              'sourceSceneSha256': data['Context']['sourceSceneSha256'], 'sourceObjSha256': data['Context']['sourceObjSha256'],
              'activeDesign': data['Context']['activeDesign'], 'housePlacement': data['Context']['housePlacement'],
              **{'source'+key: pin(path) for key, path in paths.items() if key != 'Diagnostic'},
              'priorDiagnosticViews': pin(paths['Diagnostic']), 'inputFiles': inputs,
              'views': [view], 'cameraAudits': [audit],
              'policy': {'appendOnly': True, 'existingViewsChanged': False, 'existingDiagnosticViewIds': [v['id'] for v in data['Diagnostic']['views']],
                         'existingTreeTransformsPreserved': True, 'treeCount': 78, 'nativeExecution': False,
                         'newGeometry': False, 'newCollision': False,
                         'evidence': 'Existing interpreted 2024 orthophoto canopy region. Roots, tree sizes and species remain illustrative, not a census or survey.',
                         'groundLimit': 'Highest unchanged rendered ground triangles only. This view uses context_unresolved_flat_backdrop, explicitly unmeasured elevation.',
                         'nativeAppearanceAccepted': False}}
    # Write only after every source and static geometric guard has passed.
    output.mkdir(parents=True)
    write(output/'viewpoints.json', result); chart(output/'plan-view.png', view, data['Ecology'])
    write(output/'summary.json', {'status': STATUS, 'manifest': pin(output/'viewpoints.json'),
          'generator': pin(__file__), 'targetOriginalTreeId': root['id'],
          'eyeHeightCm': audit['eyeHeightAboveRenderedGroundCm'], 'targetDistanceMetres': audit['targetDistanceMetres'],
          'nearFeatures': audit['nearEightMetreFeaturesByFamily'], 'nativeAppearanceAccepted': False})
    require(all(sha(path) == expected for path, expected in inputs.items()), 'Source changed during camera generation')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('context', 'terrain', 'buildings', 'scene', 'ecology', 'canopy', 'diagnostic', 'output'):
        parser.add_argument('--'+name, required=True)
    args = parser.parse_args(); result = build(**vars(args))
    print(json.dumps({'output': str(Path(args.output).resolve()/'viewpoints.json'),
                      'status': result['status'], 'audit': {k: v for k, v in result['cameraAudits'][0].items()
                      if k not in ('targetOriginalTree', 'centreRayGroundSamples')}}, indent=2))
