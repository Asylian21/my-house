"""Source-only purposeful Fern02 camera. Root stages independent QA copies."""
import copy
import hashlib
import json
import math
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-fern-camera-r14.py'
OUTPUT = ROOT/'output/unreal/exterior-garden-fern-20261002-camera-r14-supplement'
VIEW_ID = 'exterior-garden-fern-close-r14'
SOURCE = ROOT/'output/unreal/exterior-garden-fern-20261002-r25-study/fern-pilot-source-plan.json'
SOURCE_SHA = 'b3c1453765e310a47416507236c24adff2b3517b4bacd5a882fefa5c0df9709b'
FERN = ROOT/'output/unreal/exterior-20261002-r25b/garden-fern-native-report-r2.json'
FERN_SHA = 'dc96a4927a0b0ec0e8abb3740e7a918e65a6ba6a0881ba77bc29275c1445e0b2'
BASE = ROOT/'output/unreal/exterior-20261002-r22c/realism-integration-native-report-r3.json'
BASE_SHA = '999fc17ea7600136a2097aecefed3d846ff0d7e9baeb7f005480b113b60b1f40'
SCENE = ROOT/'output/unreal/realism-20260926-r5/geometry/scene.json'
SCENE_SHA = '0e2925319fa0effc3727b121ee24f75a3b8e8bd53b3a31d230e29e29a56ed387'
OBJ = SCENE.parent/'dom-mm.obj'
OBJ_SHA = 'a86c83e68e14898fdeb3fd071c24a6bb82d3a6d0e61f52d8e9a757bce4a2634d'
SCHEMA = 'brezi-purposeful-original-fern-matched-camera-r14'


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        while block := f.read(1048576):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')


def checked(row):
    p = Path(row['path']).resolve()
    require(p.is_relative_to(ROOT) and p.is_file() and pin(p) == row, 'Pinned camera input changed')
    return p


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def sub(a, b):
    return [x-y for x, y in zip(a, b)]


def unit(a):
    length = math.sqrt(dot(a, a))
    require(length > 0, 'Camera direction invalid')
    return [v/length for v in a]


def cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def triangle_inside(p, t):
    # Ground membership only; exact original source triangles, no domain edit.
    a, b, c = t
    s = [(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]),
         (c[0]-b[0])*(p[1]-b[1])-(c[1]-b[1])*(p[0]-b[0]),
         (a[0]-c[0])*(p[1]-c[1])-(a[1]-c[1])*(p[0]-c[0])]
    area = (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    return abs(area) > 1e-8 and (min(s) >= -1e-8 or max(s) <= 1e-8)


def subject_triangles():
    # OBJ coordinates are X=sourceX, Y=-nativeY, Z=height, millimetres.
    # Object-local vertices carry global indices; do not decode unrelated meshes.
    vertices, triangles, current, index = {}, [], None, 0
    with OBJ.open() as f:
        for line in f:
            if line.startswith('o '):
                current = line.strip()[2:]
            elif line.startswith('v '):
                index += 1
                if current == 'DOM_00001':
                    x, y, z = map(float, line.split()[1:])
                    vertices[index] = [x/10, -y/10, z/10]
            elif current == 'DOM_00001' and line.startswith('f '):
                ids = [int(s.split('/')[0]) for s in line.split()[1:]]
                require(len(ids) == 3 and all(i in vertices for i in ids), 'Original subject OBJ triangle escapes object')
                triangles.append([vertices[i] for i in ids])
    require(len(triangles) == 27, 'Original subject ground count differs')
    return triangles


def source_bounds(obj):
    bounds = obj['boundsMm']
    return [[bounds['min'][0]/10, -bounds['max'][1]/10, bounds['min'][2]/10],
            [bounds['max'][0]/10, -bounds['min'][1]/10, bounds['max'][2]/10]]


def boxes_overlap(a, b):
    return all(a[0][i] <= b[1][i] and b[0][i] <= a[1][i] for i in range(3))


def crown_box(root, radius, below, height):
    return [[root[0]-radius, root[1]-radius, root[2]-below],
            [root[0]+radius, root[1]+radius, root[2]+height]]


def frame_box(view, bounds):
    f = unit(sub(view['targetCm'], view['eyeCm']))
    right = unit(cross(f, [0, 0, 1]))
    up = unit(cross(right, f))
    tangent = math.tan(math.radians(view['horizontalFovDegrees']/2))
    points = []
    for x in [bounds[0][0], bounds[1][0]]:
        for y in [bounds[0][1], bounds[1][1]]:
            for z in [bounds[0][2], bounds[1][2]]:
                d = sub([x, y, z], view['eyeCm'])
                depth = dot(d, f)
                require(depth > 0, 'Crown source support lies behind camera')
                points.append([dot(d, right)/(depth*tangent), dot(d, up)/(depth*tangent*9/16)])
    maximum = [max(abs(p[i]) for p in points) for i in range(2)]
    require(max(maximum) < .96, 'Complete old/new crown box does not fit close camera')
    return {'conservativeFullBoxCornerCount': 8, 'maximumAbsoluteNormalizedXY': maximum,
            'entireBoxInsideSource16by9Frustum': True}


def derive():
    for p, h in [(SOURCE, SOURCE_SHA), (FERN, FERN_SHA), (BASE, BASE_SHA), (SCENE, SCENE_SHA), (OBJ, OBJ_SHA)]:
        require(sha(p) == h, 'Actual source/saved fern camera basis changed')
    plan, fern, scene = read(SOURCE), read(FERN), read(SCENE)
    require(fern['savedMapUnloadedReloaded'] is True and fern['nativeApplied'] is True
            and fern['nativeProcessId'] == 60976 and fern['changedOriginalRoot'] == 1 and fern['newRoots'] == 0,
            'Purposeful camera requires actual saved single-root fern')
    root = fern['savedRootReadback']
    xyz = root['actualNativeRootXYZ']
    require(xyz == plan['placementProposal']['positionCm'] and root['rootId'] == 'garden_ornamental_10',
            'Exact unchanged original fern root required')
    view = {'id': VIEW_ID, 'label': 'Papraď · pôvodný koreň a kontakt so záhonom',
            'eyeCm': [xyz[0], xyz[1]+250, 130], 'targetCm': [xyz[0], xyz[1], 50],
            'horizontalFovDegrees': 62, 'source': OWNER+': one unchanged root, eye250cm north/130cm high, aim50cm, original62-degree sourceFOV'}
    ground = subject_triangles()
    membership = [i for i, t in enumerate(ground) if triangle_inside(view['eyeCm'], t)]
    require(membership, 'Close camera eye is outside original subject ground')
    old = crown_box(xyz, plan['placementProposal']['originalRoot']['radiusCm'], 0,
                    plan['placementProposal']['originalRoot']['actualHeightCm'])
    new = crown_box(xyz, root['actualNativeAllVertexRadiusCm'], root['actualNativeBelowRootDepthCm'],
                    root['actualNativeAboveRootHeightCm'])
    old_frame, new_frame = frame_box(view, old), frame_box(view, new)
    eye_box = [[v-30 for v in view['eyeCm']], [v+30 for v in view['eyeCm']]]
    # A conservative AABB corridor contains every segment from eye to either
    # full crown box. An empty intersection proves no tagged source occluder,
    # without claiming native sweep or untagged vegetation visibility.
    corridor = [[min(view['eyeCm'][i], old[0][i], new[0][i]) for i in range(3)],
                [max(view['eyeCm'][i], old[1][i], new[1][i]) for i in range(3)]]
    objects = [o for o in scene['objects'] if o['enabled'] and
               (o.get('metadata', {}).get('cameraOccluder') or o.get('metadata', {}).get('babylonCheckCollisions'))]
    eye_hits = [o['id'] for o in objects if boxes_overlap(eye_box, source_bounds(o))]
    corridor_hits = [o['id'] for o in objects if boxes_overlap(corridor, source_bounds(o))]
    require(not eye_hits and not corridor_hits, 'Camera/crown corridor intersects tagged source architecture')
    audit = {'rootId': root['rootId'], 'sourceBedId': 'DOM_01966', 'rootXYZCm': xyz,
             'sourceOnlyCameraProposal': True, 'sourceHorizontalDistanceCm': 250,
             'sourceEyeToRootDistanceCm': math.sqrt(dot(sub(view['eyeCm'], xyz), sub(view['eyeCm'], xyz))),
             'sourceSubjectTrianglesChecked': 27, 'sourceEyeContainingTriangleOrdinals': membership,
             'sourceEyeGroundElevationCm': ground[membership[0]][0][2],
             'sourceEyeClearanceBoxRadiusCm': 30, 'taggedSourceOccluderObjectsChecked': len(objects),
             'sourceEyeClearanceBoxHits': eye_hits, 'sourceWholeCrownSightCorridorHits': corridor_hits,
             'sourceWholeCrownSightCorridorBoundsCm': corridor,
             'original120cmFullCrownConservativeFraming': old_frame,
             'saved35cmFernFullCrownConservativeFraming': new_frame,
             'nativeCameraTransformMeasured': False, 'nativeFovMeasured': False,
             'nativeOcclusionOrPlantVisibilityMeasured': False,
             'untaggedPlantOcclusionChecked': False, 'physicalWalkingTraversalClaimed': False,
             'geometryOrPlantPlacementChanged': False, 'lightingChanged': False}
    return view, audit


def appended_bytes(original, view):
    document = json.loads(original)
    require((json.dumps(document, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode() == original,
            'Original camera serialization changed; refuse re-encoding')
    require(document['coordinateSystem'] == 'unreal-centimeters' and not any(v['id'] == VIEW_ID for v in document['views']),
            'Original camera has duplicate/unapproved view')
    result = copy.deepcopy(document)
    result['views'].append(view)
    payload = (json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()
    prefix = json.dumps(document['views'], indent=2, ensure_ascii=False, allow_nan=False).encode().rsplit(b'\n]', 1)[0]
    require(json.dumps(result['views'], indent=2, ensure_ascii=False, allow_nan=False).encode().startswith(prefix+b','),
            'Existing camera view rows lost byte-exact prefix')
    return payload


def validated_supplement():
    s = read(OUTPUT/'garden-fern-camera-supplement.json')
    require(s['schema'] == SCHEMA and s['owner'] == OWNER and s['status'] == 'source-only-purposeful-fern-camera-native-pending',
            'Known closed fern camera supplement required')
    for p, h in s['inputFiles'].items():
        require(sha(p) == h, 'Purposeful camera input changed')
    view, audit = derive()
    require(s['view'] == view and s['sourceCameraAudit'] == audit, 'Purposeful camera derived source proof changed')
    original, appended = checked(s['originalViewpoints']), checked(s['appendedViewpoints'])
    require(appended.read_bytes() == appended_bytes(original.read_bytes(), view), 'Purposeful camera prefix/row changed')
    require(s['baselineNativeReport'] == pin(BASE) and s['candidateNativeReport'] == pin(FERN), 'Selected actual camera pair differs')
    for key in ['nativeExecuted', 'nativeCameraVerified', 'nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted']:
        require(s[key] is False, 'Source camera cannot grant native/appearance acceptance')
    return s


def build():
    require(not OUTPUT.exists(), 'Camera source supplement is immutable once built')
    view, audit = derive()
    original = BASE.parent/'Project/BreziTwin/Content/Data/viewpoints.json'
    candidate_original = FERN.parent/'Project/BreziTwin/Content/Data/viewpoints.json'
    require(original.read_bytes() == candidate_original.read_bytes() and sha(original) == '25d591b3309a6a0b2297f3eb1fef4d6785379b639662d68049ccc13a12bcd846',
            'Immediate baseline/candidate original views must be byte identical')
    payload = appended_bytes(original.read_bytes(), view)
    OUTPUT.mkdir(parents=True)
    appended = OUTPUT/'viewpoints-r22-prefix-plus-fern-close.json'
    appended.write_bytes(payload)
    snapshot = OUTPUT/'source-exterior-garden-fern-camera-r14.py'
    shutil.copyfile(ROOT/OWNER, snapshot)
    inputs = {str(p): sha(p) for p in [SOURCE, FERN, BASE, SCENE, OBJ, original, candidate_original, ROOT/OWNER, snapshot]}
    write(OUTPUT/'garden-fern-camera-supplement.json', {'schema': SCHEMA, 'owner': OWNER,
        'status': 'source-only-purposeful-fern-camera-native-pending', 'inputFiles': inputs,
        'baselineNativeReport': pin(BASE), 'candidateNativeReport': pin(FERN), 'selectedSourcePlan': pin(SOURCE),
        'originalViewpoints': pin(original), 'appendedViewpoints': pin(appended), 'view': view,
        'sourceCameraAudit': audit, 'originalViewRowsByteExactPrefix': True, 'lightingAndOriginalViewsUnchanged': True,
        'plantPlacementChanged': False, 'nativeExecuted': False, 'nativeCameraVerified': False,
        'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False})
    validated_supplement()
    print(json.dumps({'supplement': pin(OUTPUT/'garden-fern-camera-supplement.json'), 'view': view, 'audit': audit}, indent=2))


if __name__ == '__main__':
    build()
