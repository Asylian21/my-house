"""One source-only R19 visibility study, derived from saved R16 placements.

No Unreal/native/GPU invocation. Writes only the new owned study directory.
"""
import argparse
from collections import Counter
import importlib.util
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-meadow-visibility-study.py'
NATIVE = ROOT / 'scripts/unreal/exterior-meadow-visibility-native.py'
OUTPUT = ROOT / 'output/unreal/exterior-meadow-visibility-20261001-r1-study'
spec = importlib.util.spec_from_file_location('visibility_study_guards', NATIVE)
n = importlib.util.module_from_spec(spec)
spec.loader.exec_module(n)


def dot(a, b): return sum(x * y for x, y in zip(a, b))
def norm(v): return math.sqrt(dot(v, v))


def camera_basis(camera):
    forward = [camera['targetCm'][i] - camera['eyeCm'][i] for i in range(3)]
    length = norm(forward)
    forward = [v / length for v in forward]
    right = [forward[1], -forward[0], 0.]
    length = norm(right)
    right = [v / length for v in right]
    up = [right[1] * forward[2], -right[0] * forward[2],
          right[0] * forward[1] - right[1] * forward[0]]
    tangent = math.tan(math.radians(camera['horizontalFovDegrees'] / 2))
    return forward, right, up, tangent


def in_frustum(delta, basis):
    forward, right, up, tangent = basis
    depth = dot(delta, forward)
    return depth > 0 and abs(dot(delta, right)) <= depth * tangent and abs(dot(delta, up)) <= depth * tangent * 9 / 16


def inside_ring(point, ring):
    inside = False
    for a, b in zip(ring, ring[1:] + ring[:1]):
        if (a[1] > point[1]) != (b[1] > point[1]) and point[0] < (
                b[0] - a[0]) * (point[1] - a[1]) / (b[1] - a[1]) + a[0]:
            inside = not inside
    return inside


def inside_geojson(point, geometry):
    polygons = [geometry['coordinates']] if geometry['type'] == 'Polygon' else geometry['coordinates']
    return any(inside_ring(point, polygon[0]) and not any(inside_ring(point, hole) for hole in polygon[1:])
               for polygon in polygons)


def bounds_union(bounds):
    low = [min(b['min'][i] for b in bounds) for i in range(3)]
    high = [max(b['max'][i] for b in bounds) for i in range(3)]
    return {'min': low, 'max': high}


def model_radius(bounds, average_scale):
    # The union AABB diagonal is a source upper-radius approximation. This
    # applies UE's min(maxScale*sphereRadius, scaledBoxDiagonal) transform.
    # Native RenderData sphere/cluster state is not measured here.
    extent = [(bounds['max'][i] - bounds['min'][i]) * .5 for i in range(3)]
    source_radius = norm(extent)
    return min(max(average_scale) * source_radius, norm([extent[i] * average_scale[i] for i in range(3)]))


def modeled_lod(distance, radius, screens, horizontal_fov):
    multiple = .5 / math.tan(math.radians(horizontal_fov / 2)) * 16 / 9
    # UE HISM starts at index1; .025 / .007 for the original LawnTufts.
    for index in range(1, len(screens)):
        threshold = multiple * radius / (screens[index] * .5)
        if distance < threshold:
            return index - 1
    return len(screens) - 1


def source_diagnostic(report, scope, inputs):
    placement_groups = n.read(inputs['savedPlacements']['path'])
    by_id = {g['id']: g for g in placement_groups}
    targets = scope['targets']
    n.require(all(t['groupId'] in by_id and len(by_id[t['groupId']]['instances']) == t['baseGroup']['instances']
                  for t in targets), 'Saved placement target coverage/count differs')
    prototypes = n.read(inputs['meadowPrototypes']['path'])
    ecology_geometry = n.read(inputs['ecologyGeometry']['path'])
    bounds = {}
    for master in report['nativeMeadow']['prototypes']:
        matching = [r for r in prototypes if r['id'].startswith(master + '_LOD')]
        n.require(len(matching) == 3 and [len(r['faces']) for r in matching] == [256, 64, 24],
                  'Original source prototype triangle population differs')
        bounds[master] = bounds_union([{'min': [v / 10 for v in row['boundsMm']['min']],
                                       'max': [v / 10 for v in row['boundsMm']['max']]} for row in matching])
    for row in ecology_geometry['meshes']:
        bounds[row['id']] = bounds_union([lod['expectedBoundsCm'] for lod in row['lods']])
    plants = {p['id']: p for p in report['savedPlantReadback']}
    lods = {key: {'screens': row['lodScreens'], 'triangles': [p['triangles'] for p in row['lodProofs']]}
            for key, row in report['nativeMeadow']['prototypes'].items()}
    lods.update({key: {'screens': row['lodScreens'], 'triangles': row['lodTriangles']}
                 for key, row in plants.items() if key in n.ECOLOGY_IDS})
    group_radii = {}
    for target in targets:
        rows = by_id[target['groupId']]['instances']
        scale = [(min(r['scale'][i] for r in rows) + max(r['scale'][i] for r in rows)) * .5 for i in range(3)]
        group_radii[target['groupId']] = model_radius(bounds[target['masterId']], scale)
    views = [v for v in n.read(inputs['savedCameras']['path'])['views']
             if v['id'] in ('exterior-parcels', 'exterior-canopy-grove', 'exterior-canopy-close')]
    costs = {}
    distance_bins = [500, 1000, 2000, 5000, 7200, 9000, 12000, 18000, 24000, 36000]
    for camera in views:
        basis = camera_basis(camera)
        camera_result = {}
        for scope_id in ('local-meadow', 'grove-ecology'):
            policies = {key: {'radialRoots': 0, 'frustumRootPoints': 0, 'modeledRadialLodInstances': [0, 0, 0],
                             'modeledFrustumLodInstances': [0, 0, 0], 'modeledRadialTriangles': 0,
                             'modeledFrustumTriangles': 0}
                        for key in ('original', '18000/24000', '30000/36000-comparison-only')}
            bins, visible_bins = Counter(), Counter()
            uniform_lod_totals = [0, 0, 0]
            for target in [t for t in targets if t['scope'] == scope_id]:
                model = lods[target['masterId']]
                rows = by_id[target['groupId']]['instances']
                for index in range(3): uniform_lod_totals[index] += len(rows) * model['triangles'][index]
                radius = group_radii[target['groupId']]
                for row in rows:
                    delta = [row['positionCm'][i] - camera['eyeCm'][i] for i in range(3)]
                    distance = norm(delta)
                    ground_distance = math.hypot(*delta[:2])
                    frustum = in_frustum(delta, basis)
                    upper = next((cut for cut in distance_bins if ground_distance < cut), 999999)
                    bins[upper] += 1
                    if frustum: visible_bins[upper] += 1
                    lod = modeled_lod(distance, radius, model['screens'], camera['horizontalFovDegrees'])
                    for key, end in [('original', target['baseGroup']['cullEndCm']), ('18000/24000', 24000),
                                     ('30000/36000-comparison-only', 36000)]:
                        if distance >= end: continue
                        result = policies[key]
                        result['radialRoots'] += 1
                        result['modeledRadialLodInstances'][lod] += 1
                        result['modeledRadialTriangles'] += model['triangles'][lod]
                        if frustum:
                            result['frustumRootPoints'] += 1
                            result['modeledFrustumLodInstances'][lod] += 1
                            result['modeledFrustumTriangles'] += model['triangles'][lod]
            camera_result[scope_id] = {'policies': policies,
                'groundDistanceBinsUpperExclusiveCm': dict(sorted(bins.items())),
                'frustumGroundDistanceBinsUpperExclusiveCm': dict(sorted(visible_bins.items())),
                'allPopulationSinglePassTriangleCostsByUniformLod': uniform_lod_totals}
        costs[camera['id']] = {'camera': camera, 'scopes': camera_result}
    # Source zone tags are matched on exact retained root XY, independent of
    # later continuous height-only overrides. Rounded1e-4cm avoids serialization noise.
    context = n.read(inputs['originalContext']['path'])
    yard = n.read(inputs['originalYard']['path'])
    tags = {}
    for array, rows in ([(key, context[key]) for key in ('meadowBladePlacements', 'meadowUnderstoryPlacements')]
                        + [('yardBladePlacements', yard['yardBladePlacements'])]):
        for row in rows:
            tags[(round(row['positionCm'][0], 4), round(row['positionCm'][1], 4))] = (
                array, row.get('sourceMeshId'), row.get('sourceFinish'))
    del context, yard
    population_tags = Counter()
    for target in [t for t in targets if t['scope'] == 'local-meadow']:
        for row in by_id[target['groupId']]['instances']:
            key = (round(row['positionCm'][0], 4), round(row['positionCm'][1], 4))
            n.require(key in tags, 'Actual retained meadow root has no original source zone')
            population_tags[tags[key][0]] += 1
    close = next(v for v in views if v['id'] == 'exterior-canopy-close')
    low_rows = [(group, row) for group in placement_groups if group['role'] in ('grass', 'groundcover', 'flower', 'ornamental', 'shrub')
                for row in group['instances']]
    closest = min(low_rows, key=lambda pair: math.dist(pair[1]['positionCm'][:2], close['eyeCm'][:2]))
    group, row = closest
    nearest_low = {'groupId': group['id'], 'masterId': group['meshId'], 'role': group['role'],
                   'positionCm': row['positionCm'], 'groundDistanceM': math.dist(row['positionCm'][:2], close['eyeCm'][:2]) / 100}
    ecology_rows = [(by_id[t['groupId']], row) for t in targets if t['scope'] == 'grove-ecology'
                    for row in by_id[t['groupId']]['instances']]
    forward = [close['targetCm'][i] - close['eyeCm'][i] for i in range(2)]
    length = math.hypot(*forward)
    forward = [v / length for v in forward]
    probes = []
    for forward_m in (2, 5, 10, 15, 20, 25, 35, 50):
        xy = [close['eyeCm'][i] + forward[i] * forward_m * 100 for i in range(2)]
        group, row = min(ecology_rows, key=lambda pair: math.dist(pair[1]['positionCm'][:2], xy))
        probes.append({'forwardM': forward_m, 'pointXYcm': xy,
                       'nearestExistingEcologyRootM': math.dist(row['positionCm'][:2], xy) / 100,
                       'groupId': group['id'], 'masterId': group['meshId'], 'rootPositionCm': row['positionCm']})
    ecology = n.read(inputs['ecologyPlan']['path'])
    ecology_domain = json.loads(ecology['ecologyDomainCm'])
    exclusion_domains = {key: json.loads(value) for key, value in ecology['exclusionDomainsCm'].items()}
    for probe in probes:
        point = probe['pointXYcm']
        probe['insideOriginalGroveRegion'] = inside_ring(point, ecology['sourceRegion']['polygonCm'])
        probe['insideExistingCanopyEcologyDomain'] = inside_geojson(point, ecology_domain)
        probe['originalExclusionDomainsAtPoint'] = [key for key, value in exclusion_domains.items()
                                                   if inside_geojson(point, value)]
    masks = {'regionId': ecology['regionId'], 'sourceRegion': ecology['sourceRegion'],
             'existingCanopyDomainAreaM2': report['canopyEcology']['audit']['domainAreaM2'],
             'domainGeoJSONSha256': n.digest(ecology_domain),
             'exclusionDomainGeoJSONSha256': {k: n.digest(v) for k, v in exclusion_domains.items()},
             'groundSource': 'context_unresolved_flat_backdrop', 'measuredElevation': False,
             'groundZcm': -25., 'plantRootZcm': -24.92,
             'footprintPolicy': report['canopyEcology']['audit']['fullFootprintPolicy'],
             'newPlantingRequiresNewPlacementPlan': True,
             'interpretation': 'Current crown union leaves the close foreground unplanted. A distance override cannot fill it.'}
    return {'status': 'source-only-saved-placement-occupancy-and-visibility-estimate',
            'owner': OWNER, 'nativeExecuted': False, 'performanceAccepted': False,
            'nativeAppearanceAccepted': False, 'selectedPolicyCm': list(n.PROPOSED), 'costsByCamera': costs,
            'localMeadowSourceArrayCounts': dict(population_tags), 'nearestAnyLowPlantToCloseCamera': nearest_low,
            'closeCenterlineNearestEcologyRoots': probes, 'groveOriginalAllowedMasks': masks,
            'nearSourceEmptyForegroundFixed': False,
            'diagnosticLimits': {'rootPointFrustum': '16:9 source camera point test; excludes root bounds, occlusion and HISM cluster overdraw.',
                'lodModel': 'Installed UE5.8 index1 distance formula; source allLOD AABB radius; group min/max average scale; native RenderData bounds not measured.',
                'runtimeCvars': 'ViewDistanceScale=1, foliage.LODDistanceScale=1, foliage.MinimumScreenSize=0.000005 modeled from defaults; actual game values not recorded.',
                'triangleCosts': 'Source main-view model only; no GPU timings, shadow passes, dither overlap or performance acceptance.',
                'fadeStart': '180m is the saved start parameter; visual fading requires material support and is not claimed.',
                '360m': 'Comparison counts only; not a second selected candidate or native override.'}}


def produce(base, output):
    base, output = Path(base).resolve(), Path(output).resolve()
    n.require(base == n.BASE and output == OUTPUT and not output.exists(), 'Only the new owned originalR16 R19 study may be written')
    n.require(n.sha(n.EVIDENCE_PLAN) == n.EVIDENCE_PLAN_SHA, 'Immutable original base evidence differs')
    evidence = n.read(n.EVIDENCE_PLAN)
    report, content, protected = n.g.validate_plan(evidence, n.EVIDENCE_PLAN)
    scope = n.canonical_scope(report)
    frozen = base / 'source-freeze/consumed-native-r1/workspace'
    def frozen_path(path): return frozen / Path(path).relative_to(ROOT)
    inputs = {key: n.pin(path) for key, path in {
        'savedPlacements': base / 'exterior-placements.json',
        'savedCameras': base / 'Project/BreziTwin/Content/Data/viewpoints.json',
        'meadowPrototypes': frozen / 'output/unreal/rural-context-20260923-r4/lawn-geometry/prototypes.json',
        'originalContext': frozen / 'output/unreal/exterior-context-20260927-r8/context-plan.json',
        'originalYard': frozen_path(report['yardPlanting']['plan']),
        'ecologyPlan': frozen_path(report['canopyEcology']['plan']),
        'ecologyGeometry': frozen / 'output/unreal/exterior-canopy-ecology-20260930-r4/geometry-manifest.json',
        'testRecordedOriginalWitness': ROOT / 'output/unreal/exterior-20261001-r17a/canopy-transmission-witness-before.json'}.items()}
    engine = Path(evidence['engineEvidence']['editorModules']['path']).parents[3]
    engine_evidence = {key: n.pin(engine / path) for key, path in {
        'hismCpp': 'Engine/Source/Runtime/Engine/Private/HierarchicalInstancedStaticMesh.cpp',
        'ismCpp': 'Engine/Source/Runtime/Engine/Private/InstancedStaticMesh.cpp',
        'ismHeader': 'Engine/Source/Runtime/Engine/Classes/Components/InstancedStaticMeshComponent.h',
        'sceneManagementCpp': 'Engine/Source/Runtime/Engine/Private/SceneManagement.cpp',
        'boxSphereBoundsHeader': 'Engine/Source/Runtime/Core/Public/Math/BoxSphereBounds.h'}.items()}
    n.require('void UInstancedStaticMeshComponent::SetCullDistances(int32 StartCullDistance, int32 EndCullDistance)' in
              Path(engine_evidence['ismCpp']['path']).read_text(), 'Installed native setter differs')
    diagnostic = source_diagnostic(report, scope, inputs)
    environment = dict(__import__('os').environ, PYTHONDONTWRITEBYTECODE='1')
    tests = subprocess.run([sys.executable, str(ROOT / 'scripts/unreal/test_exterior_meadow_visibility.py'), '-v'],
                           cwd=ROOT, env=environment, text=True, capture_output=True)
    n.require(tests.returncode == 0, 'Source guard tests failed:\n' + tests.stdout + tests.stderr)
    output.mkdir()
    sources = {}
    for key, original, name in [
        ('generator', Path(__file__).resolve(), 'generator-source.py'),
        ('nativeHelper', NATIVE, 'native-helper-source.py'),
        ('tests', ROOT / 'scripts/unreal/test_exterior_meadow_visibility.py', 'test-source.py'),
        ('design', ROOT / 'docs/unreal-meadow-visibility-r1.md', 'design.md')]:
        target = output / name
        shutil.copy2(original, target)
        sources[key] = {'live': n.pin(original), 'snapshot': n.pin(target)}
    n.write(output / 'source-diagnostic.json', diagnostic)
    n.write(output / 'source-guard-tests.json', {'status': 'passed', 'exitCode': tests.returncode,
            'nativeExecuted': False, 'stdout': tests.stdout, 'stderr': tests.stderr,
            'command': [sys.executable, str(ROOT / 'scripts/unreal/test_exterior_meadow_visibility.py'), '-v']})
    plan = {'schema': n.SCHEMA, 'schemaVersion': 1, 'owner': OWNER, 'status': n.STATUS,
            'generatedAt': n.now(), 'activeDesign': report['activeDesign'], 'setbacksMm': report['setbacksMm'],
            'baseNativeReport': evidence['baseNativeReport'], 'reusedBaseEvidencePlan': n.pin(n.EVIDENCE_PLAN),
            'reusedBaseEvidenceOnly': 'OriginalR16 native inventory/module/source proofs; no transmission variant or mutation reused.',
            'immutableGenericHelper': n.pin(n.SHARED), 'newSourceFiles': sources,
            'diagnosticInputs': inputs, 'engineEvidence': engine_evidence,
            'sourceDiagnostic': n.pin(output / 'source-diagnostic.json'),
            'sourceGuardTests': n.pin(output / 'source-guard-tests.json'),
            'nativeExecuted': False, 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
            'performanceAccepted': False, 'shippingPackageProduced': False, **scope}
    plan_path = output / 'meadow-visibility-plan.json'
    n.write(plan_path, plan)
    n.validate_plan(plan, plan_path)
    n.write(output / 'summary.json', {'status': n.STATUS, 'selectedPlan': n.pin(plan_path), 'audit': scope['audit'],
        'sourceGuardTestsPassed': True, 'nativeExecuted': False, 'nativeAppearanceAccepted': False,
        'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'nearSourceEmptyForegroundFixed': False,
        'nextEvidence': 'Root-only fresh independentR19 clone/native save; matched source cameras parcels+grove; no full realism claim.'})
    files = {p.name: n.pin(p) for p in sorted(output.iterdir()) if p.is_file()}
    n.write(output / 'source-receipt.json', {'status': 'frozen-source-only-meadow-ecology-visibility-study',
            'owner': OWNER, 'generatedAt': n.now(), 'files': files, 'fileCount': len(files),
            'nativeExecuted': False, 'nativeAppearanceAccepted': False, 'performanceAccepted': False})
    print(json.dumps({'status': n.STATUS, 'plan': n.pin(plan_path), 'receipt': n.pin(output / 'source-receipt.json'),
                      'audit': scope['audit'], 'nativeExecuted': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default=str(n.BASE))
    parser.add_argument('--output', default=str(OUTPUT))
    args = parser.parse_args()
    produce(args.base, args.output)
