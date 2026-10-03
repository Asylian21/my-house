"""Bounded read-only source framing audit; no Unreal or viewpoint writes."""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighborhood-camera-coverage-source-r1.py'
OUT = ROOT/'output/unreal/exterior-garden-yard-20261002-r37-camera-coverage-source-audit-r1'
REPORT = ROOT/'output/unreal/exterior-20261002-r37b/garden-yard-integration-native-report-r2.json'
SUITE = ROOT/'output/unreal/exterior-validation-20260930-r1/qa/editor-pilot-r37b-selected-garden-yard-r28-1790945953708-UNkW4D/editor-pilot-suite.json'
R18 = ROOT/'output/unreal/exterior-20261001-r18b/neighbor-finish-overlay-report-r3.json'
GEOMETRY = ROOT/'output/unreal/exterior-neighbor-finish-20261001-r18-study/neighbor-finish-geometry.json'
LAYOUT = ROOT/'output/unreal/exterior-context-yard-20261002-r28-study/yard-layout.json'
VIEWS = ROOT/'output/unreal/exterior-20261002-r37b/Project/BreziTwin/Content/Data/viewpoints.json'


def read(path): return json.loads(Path(path).read_text())
def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}
def require(value, message):
    if not value: raise ValueError(message)
def dot(a, b): return sum(x*y for x, y in zip(a, b))
def cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
def unit(v): return [x/math.sqrt(dot(v, v)) for x in v]


def project(points, camera):
    eye = camera['eyeCm'];f = unit([b-a for a, b in zip(eye, camera['targetCm'])])
    right = unit(cross([0, 0, 1], f));up = cross(f, right)
    ht = math.tan(math.radians(camera['horizontalFovDegrees']/2));vt = ht/(1920/1080)
    rows = []
    for point in points:
        delta = [b-a for a, b in zip(eye, point)];depth = dot(delta, f)
        require(depth > 0, 'This bounded projection requires positive depth')
        rows.append([depth, dot(delta, right)/(depth*ht), dot(delta, up)/(depth*vt)])
    return {'sourceVertices': len(points), 'depthCm': [min(v[0] for v in rows), max(v[0] for v in rows)],
        'normalizedHorizontal': [min(v[1] for v in rows), max(v[1] for v in rows)],
        'normalizedVertical': [min(v[2] for v in rows), max(v[2] for v in rows)],
        'allSourceVerticesOutsideSameHorizontalPlane': min(v[1] for v in rows) > 1 or max(v[1] for v in rows) < -1,
        'allSourceVerticesWithinSourceFrustum': all(abs(v[1]) <= 1 and abs(v[2]) <= 1 for v in rows),
        'nativeVisibilityOrOcclusionComputed': False}


def main():
    require(not OUT.exists(), 'Fresh audit output required')
    require(pin(REPORT)['sha256'] == 'f589c0d813ccfc35eba928a91a4545e03b159622fffa7ae2ba247545053c4532', 'Selected native report changed')
    report = read(REPORT);suite = read(SUITE);old = read(R18)
    require(report['nativeProcessId'] == 54956 and report['nativeApplied'] is True, 'Actual saved selected report required')
    case = next(c for c in suite['cases'] if c['view'] == 'exterior-neighborhood')
    require(case['outcome'] == {'code': 0, 'signal': None, 'pid': 58097} and suite['sourceInputsUnchanged'] is True
        and case['shaderAndLoadErrors'] == [], 'Actual closed overview required')
    witness = Path(report['savedActorWitness']['path']);image = Path(case['originalCapturePath']);runtime = Path(case['originalRuntimePath'])
    inputs = [REPORT, SUITE, R18, GEOMETRY, LAYOUT, VIEWS, witness, image, runtime, Path(__file__)]
    before = [pin(p) for p in inputs]
    require(pin(witness) == report['savedActorWitness'] and pin(image)['sha256'] == case['originalCaptureSha256']
        and pin(runtime)['sha256'] == case['originalRuntimeSha256'], 'Recorded original evidence changed')
    source = read(GEOMETRY);saved = read(witness);layout = read(LAYOUT)
    views = read(VIEWS)['views'];camera = next(v for v in views if v['id'] == 'exterior-neighborhood')
    require(camera == case['sourceCamera'], 'Actual selected source camera changed')
    meshes = [m for m in source['candidateMeshes'] if m['id'] in old['addedActors']]
    actor_rows = []
    for m in meshes:
        actor = old['addedActors'][m['id']];row = saved[actor]
        components = [c for c in row['components'] if c.get('name') == 'StaticMeshComponent0']
        require(len(components) == 1 and row['label'] == m['id'] and row['hidden'] is False
            and components[0]['visible'] is True and components[0]['hiddenInGame'] is False
            and components[0]['mesh'].endswith('/'+m['id']+'_LOD0.'+m['id']+'_LOD0'), 'Selected neighbor component missing/hidden/foreign')
        require(row['transform'] == [[0., 0., 0.], [0., 0., 0., 1.], [1., 1., 1.]]
            and components[0]['transform'] == row['transform'], 'Source world-baked bounds cannot be projected through a moved actor')
        actor_rows.append({'sourceMeshId': m['id'], 'actor': actor, 'mesh': components[0]['mesh']})
    require(len(actor_rows) == 32, 'Exact three-building finish census required')
    prospective = {'id': 'proposed-neighborhood-ground-source-r1', 'eyeCm': [5900, 24700, 165],
        'targetCm': [7800, 28500, 185], 'horizontalFovDegrees': 72,
        'addedToProject': False, 'cameraWallVegetationGroundAndNativeVisibilityAuditPending': True}
    buildings = []
    for building in ('BU.572063', 'BU.3800911', 'BU.3852341'):
        points = [p for m in meshes if m['buildingSourceId'] == building for p in m['verticesCm']]
        buildings.append({'buildingSourceId': building,
            'sourceBoundsCm': {'minimum': [min(p[i] for p in points) for i in range(3)], 'maximum': [max(p[i] for p in points) for i in range(3)]},
            'overviewProjection': project(points, camera), 'prospectiveGroundProjection': project(points, prospective)})
    require(all(b['overviewProjection']['allSourceVerticesOutsideSameHorizontalPlane'] for b in buildings), 'Overview gap finding changed')
    require(all(b['prospectiveGroundProjection']['allSourceVerticesWithinSourceFrustum'] for b in buildings), 'Proposed source framing does not cover all three buildings')
    roads = [];plants = []
    for actor, row in saved.items():
        if row['hidden']: continue
        for c in row['components']:
            if not c.get('visible', False) or c.get('hiddenInGame', False) or not c.get('mesh'): continue
            if 'road' in row['label']: roads.append({'actor': actor, 'label': row['label'], 'mesh': c['mesh']})
            if 'HierarchicalInstancedStaticMeshComponent' in c['class']: plants.append((actor, c))
    result = {'schema': 'brezi-r37-bounded-source-camera-coverage-audit-r1', 'owner': OWNER,
        'selectedSavedReport': pin(REPORT), 'actualOverviewCapture': pin(image), 'actualOverviewProcessId': 58097,
        'method': 'World-baked R18 source vertices tied to exact saved visible mesh bindings; source horizontal FOV, 1920/1080 aspect; normalized frame edges ±1.',
        'actualSavedNeighborComponents': actor_rows, 'buildings': buildings,
        'currentRoadLabelVisibleComponentCensus': len(roads), 'roadEvidenceSample': roads[:6],
        'currentVisibleHismComponentCensus': len(plants), 'currentHismInstanceCensus': sum(c.get('instanceCount', 0) for _, c in plants),
        'yardSourceBuildingIds': [v['buildingSourceId'] for v in layout['yards']],
        'findings': {'threeTargetNeighborsAbsentFromOverviewDueToSourceCameraFraming': True,
            'existingNeighborGeometryPresentInStoredSavedWitness': True,
            'localRoadAndVegetationComponentsPresentDoesNotProveVisibleCoherentEnvironment': True,
            'originalImageObservation': 'Central house, straight road, flat aerial-photo backdrop and repeated vine strips dominate. No inhabited neighbor scene is visible in this overview.',
            'actualFlatBackdropAndRoadIntegrationQualityGapRemains': True},
        'oneRecommendedNextCamera': prospective,
        'recommendation': 'Audit this one prospective ground camera south-west of the three existing neighbor houses before any additive QA staging. It frames all three source building meshes at roughly 20–60m; a native image remains required to judge occlusion and context coherence.',
        'nativeFovReadbackAvailable': False, 'freshNativeGeometryOrActorDecodePerformed': False,
        'currentVegetationOcclusionComputed': False, 'roadSourceFrustumCoverageComputed': False,
        'nativeCameraSafetyValidated': False, 'projectDataOrCoordinatesChanged': False,
        'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False,
        'sourceInputsBefore': before}
    after = [pin(p) for p in inputs];require(after == before, 'Read-only audit inputs changed')
    result['sourceInputsAfter'] = after;result['sourceInputsUnchanged'] = True
    OUT.mkdir(parents=True)
    path = OUT/'camera-coverage.json';path.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
    print(json.dumps({'status': 'bounded-source-framing-audit-complete-native-camera-pending', 'report': pin(path),
        'threeBuildingProjections': buildings, 'roadComponents': len(roads), 'hismComponents': len(plants)}))


if __name__ == '__main__': main()
