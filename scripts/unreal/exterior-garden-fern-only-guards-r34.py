"""Source-only fern-only R34 scope, original geometry and retained-control guards.

Reuses exactly36 verified R30 fern placements on actual saved R29. The twelve
original ornamental members stay untouched. No native R34 execution is claimed.
"""
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-fern-only-guards-r34.py'
PREFIX = '/Game/Brezi/GardenFernOnly20261002R34'
TAG = 'BreziGardenFernOnly20261002R34'
STUDY = ROOT/'output/unreal/exterior-garden-fern-only-20261002-r34-study'
MODELS = ('fern_02_a', 'fern_02_c', 'fern_02_d')
OLD_GUARD_SHA = 'bcaff452b18ee2f54804b3e39d6977020de2e8acd12be268041407a726564557'
BASE_SHA = 'a11b95edf10e79fed7d1ff5c43b350634f825aedbf0ab58e8ee22642e73679fd'
R30_SHA = '67f6b002cd4ad11e0c518815ebf0224e1bb1f932b94361ae91472137dedd776d'
COUNTS = {'originalActors': 5351, 'proposedSavedActors': 5354, 'proposedFullHismComponents': 2316,
          'proposedFullHismInstances': 676957, 'originalGardenRoots': 473, 'retainedOriginalGardenRoots': 437,
          'newOriginalFernRoots': 36, 'originalOrnamentalMembersPreserved': 12, 'originalFlowersPreserved': 41,
          'originalLowStarsPreserved': 384, 'newMeshAssets': 3, 'newMaterialGraphs': 1, 'newTextureObjects': 4,
          'newPipelineAssets': 3, 'newPackages': 11, 'proposedScopedMaterialGraphs': 60,
          'proposedScopedTextureObjects': 91, 'proposedContentFiles': 4071, 'protectedFiles': 132}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def checked(row):
    require(pin(row['path']) == {k: row[k] for k in ('path', 'sha256', 'bytes')}, 'Source pin differs: '+row['path'])
    return Path(row['path'])


def module(name, file):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts/unreal'/file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


def reference():
    path = ROOT/'scripts/unreal/exterior-garden-composition-guards-r30-r3.py'
    require(sha(path) == OLD_GUARD_SHA, 'Frozen R30 source guard changed')
    old = module('r34_readonly_frozen_r30_source', path.name)
    source, base = old.load_source(), old.saved_base()
    groups = old.bind_groups(source, base)
    require(base['reportPin']['sha256'] == BASE_SHA and len(groups) == 19, 'Actual R29 garden baseline required')
    r30p = ROOT/'output/unreal/exterior-20261002-r30b/garden-composition-native-report-r3.json'
    require(sha(r30p) == R30_SHA, 'Historical verified R30 receipt changed')
    r30 = read(r30p)
    require(r30['status'] == 'verified-saved-38-original-shape-garden-composition'
            and r30['nativeApplied'] is True and r30['savedMapUnloadedReloaded'] is True
            and read(checked(r30['beforeActorWitness'])) == base['witness'], 'Historical R30 before not original R29')
    controls = read(checked(r30['originalGardenControls']))
    measurements = read(checked(r30['newSourceNativeMeasurements']))
    require(len(controls) == 19 and sum(len(v['rootIds']) for v in controls.values()) == 473, 'All473 original native rows required')
    for group in groups.values():
        row = controls[group['actor']]
        require(row['rootIds'] == [v['id'] for v in group['rows']]
                and digest(row['recoveredValues']) == group['witness']['components'][0]['orderedInstanceTransformsSha256']
                and len(row['storedMatrices']) == len(row['recoveredValues']) == len(row['rootIds']), 'Original current garden controls not bound to R29')
    placements = copy.deepcopy(source['placements'][:36])
    require(len(placements) == 36 and all(p['model'] in MODELS and p['heightRoleChanged'] is True for p in placements),
            'Only exact36 low R30 fern fits allowed')
    models = {k: copy.deepcopy(source['models'][k]) for k in MODELS}
    for key, value in models.items():
        value['exportName'] = 'R34_'+key+'_LOD0'
    return {'old': old, 'source': source, 'base': base, 'groups': groups, 'r30': r30,
            'r30Pin': pin(r30p), 'controls': controls, 'measurements': {k: measurements[k] for k in MODELS},
            'placements': placements, 'models': models}


def selection(proposal, ref):
    all_rows = ref['source']['garden']['gardenDetailPlacements']+ref['source']['garden']['ornamentalPlacements']
    selected = [p['rootId'] for p in ref['placements']]
    retained = [r for r in all_rows if r['id'] not in selected]
    heroes = ref['source']['garden']['ornamentalPlacements']
    require(proposal['proposedPlacements'] == ref['placements'] and len(selected) == len(set(selected)) == 36,
            'Cannot expand or alter exact36 fern fits')
    require(proposal['wholeOneMemberHeroGroupRetirements'] == []
            and proposal['preservedOrnamentalRootIds'] == [r['id'] for r in heroes]
            and all(r in retained for r in heroes) and len(heroes) == 12, 'All12 original ornamental rows must remain unchanged')
    require(proposal['sourceGroupFilters'] == ref['source']['proposal']['sourceGroupFilters']
            and sum(len(v['removeRootIds']) for v in proposal['sourceGroupFilters']) == 36, 'Only2 exact original low group filters allowed')
    require(proposal['originalAllRowsSha256'] == digest(all_rows) and proposal['retainedSourceRowsSha256'] == digest(retained)
            and proposal['expectedCounts'] == COUNTS and len(retained) == 437, 'Ordered437 retained source rows differ')
    require(len([r for r in retained if r['role'] == 'groundcover']) == 384,
            'No unreviewed broad low-star replacement allowed')
    for p in ref['placements']:
        require(p['positionCm'] == p['originalRow']['positionCm'] and p['yawDeg'] == p['originalRow']['yawDeg']
                and p['radiusCm'] < p['originalRow']['radiusCm'] and p['preservedRole'] == 'groundcover', 'Original contact/role/crown expanded')
    return retained


def retained_controls(ref):
    controls = copy.deepcopy(ref['controls'])
    for row in ref['source']['proposal']['sourceGroupFilters']:
        actor = ref['groups'][row['groupId']]['actor']
        controls[actor] = ref['old'].expected_control(controls[actor], row['removeSourceOrderedIndices'])
    require(sum(len(v['rootIds']) for v in controls.values()) == 437, 'Exactly437 retained native control rows required')
    ornamental_ids = {p['id'] for p in ref['source']['garden']['ornamentalPlacements']}
    for actor, row in ref['controls'].items():
        if ornamental_ids & set(row['rootIds']):
            require(controls[actor] == row, 'Ornamental raw matrix/order/mainseed/custom controls changed')
    return controls


def footprints(ref):
    old = ref['old']
    mask = module('r34_exact_original_organic_bed', 'exterior-garden-organic-native.py')
    garden = ref['source']['garden']
    steps = old.step.validated_steps(garden['sourceStepTrianglesCm'])
    fits = {p['rootId']: p for p in ref['placements']}
    proof = []
    for key, measured in ref['measurements'].items():
        require(measured['rootIds'] == [p['rootId'] for p in ref['placements'] if p['model'] == key]
                and len(measured['rootIds']) == 12 and measured['actualUnregisteredMeshlessTransientMeasurement'] is True,
                'Historical actual36 native-measured identity differs')
        for identity, value, matrix in zip(measured['rootIds'], measured['recoveredValues'], measured['storedMatrices']):
            fit, model = fits[identity], ref['models'][key]
            old.exact(value[0], fit['originalRow']['positionCm'], 'Historical measured original source XYZ differs')
            points = model['expectedNativeVerticesCm']
            local = [[sum(p[j]*matrix[j][k] for j in range(3)) for k in range(3)] for p in points]
            radius = max(math.hypot(p[0], p[1]) for p in local)
            triangles = garden['sourceMulchTrianglesCm'][fit['sourceBedId']]
            boundary = mask._boundary(triangles)
            bed_distance = min(mask._distance(value[0][:2], a, b) for a, b in boundary)
            step = old.step.circle_clearance(steps, value[0][:2], radius)
            require(radius < fit['originalRow']['radiusCm'] and radius < bed_distance
                    and radius < step['minimumOriginalProjectedRawEdgeDistanceCm'], 'Full original crown crosses bed/steps/old envelope')
            world = [[value[0][k]+p[k] for k in range(3)] for p in local]
            require(all(any(mask._triangle_inside(p[:2], t) for t in triangles) for p in world)
                    and min(p[2] for p in local) >= 0, 'Complete F32 original crown leaves bed or root contact')
            proof.append({'rootId': identity, 'model': key, 'sourceF32VerticesThroughPriorActualNativeMatrix': len(world),
                          'allVerticesInsideOriginalBed': True, 'fullCircleExcludesOriginalSteps': True,
                          'completeCircleBelowOriginalRadius': True, 'sourceBottomAndContactPreserved': True,
                          'sourceOnlyBedCircleClearanceCm': bed_distance-radius,
                          'sourceOnlyStepCircleClearanceCm': step['minimumOriginalProjectedRawEdgeDistanceCm']-radius,
                          'historicalR30MeasuredFrameUsedForSourceProofOnly': True, 'nativeR34FrameMeasured': False})
    require(len(proof) == 36 and sum(p['sourceF32VerticesThroughPriorActualNativeMatrix'] for p in proof) == 32124,
            'Complete36 source crowns/32124 original points required')
    return proof


def export_glb(models):
    binary, views, accessors, meshes, nodes = bytearray(), [], [], [], []
    def add(rows, raw, component, kind, target):
        binary.extend(b'\0'*((-len(binary)) % 4))
        offset = len(binary)
        binary.extend(raw)
        views.append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(raw), 'target': target})
        a = {'bufferView': len(views)-1, 'componentType': component, 'count': len(rows), 'type': kind}
        if kind == 'VEC3' and component == 5126:
            a.update(min=[min(r[k] for r in rows) for k in range(3)], max=[max(r[k] for r in rows) for k in range(3)])
        accessors.append(a)
        return len(accessors)-1
    for key in MODELS:
        row = models[key]
        attrs = {'POSITION': add(row['positionMeters'], b''.join(struct.pack('<fff', *v) for v in row['positionMeters']), 5126, 'VEC3', 34962)}
        for role in ('NORMAL', 'TEXCOORD_0'):
            attrs[role] = add(*row['_attributeBytes'][role], 34962)
        indices = add([(v,) for v in row['indices']], row['_indexBytes'], row['indexComponentType'], 'SCALAR', 34963)
        meshes.append({'name': row['exportName'], 'primitives': [{'attributes': attrs, 'indices': indices, 'mode': 4}]})
        nodes.append({'name': row['exportName'], 'mesh': len(meshes)-1})
    doc = {'asset': {'version': '2.0', 'generator': OWNER}, 'scene': 0, 'scenes': [{'nodes': list(range(3))}],
           'nodes': nodes, 'meshes': meshes, 'accessors': accessors, 'bufferViews': views, 'buffers': [{'byteLength': len(binary)}]}
    encoded = json.dumps(doc, separators=(',', ':'), allow_nan=False).encode()
    encoded += b' '*((-len(encoded)) % 4)
    binary.extend(b'\0'*((-len(binary)) % 4))
    return struct.pack('<III', 0x46546c67, 2, 28+len(encoded)+len(binary))+struct.pack('<II', len(encoded), 0x4e4f534a)+encoded+struct.pack('<II', len(binary), 0x004e4942)+binary


def decode_export(raw, models):
    require(struct.unpack_from('<III', raw) == (0x46546c67, 2, len(raw)), 'Own GLB frame differs')
    size, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4e4f534a, 'Own GLB JSON missing')
    d = json.loads(raw[20:20+size])
    size2, kind2 = struct.unpack_from('<II', raw, 20+size)
    require(kind2 == 0x004e4942 and 28+size+size2 == len(raw) and len(d['nodes']) == len(d['meshes']) == 3
            and not d.get('materials') and not d.get('textures'), 'Only3 original geometry forms allowed')
    old = module('r34_original_attribute_accessor', 'exterior-garden-composition-geometry-r30.py')
    blob = raw[28+size:]
    for i, key in enumerate(MODELS):
        row = models[key]
        require(d['nodes'][i] == {'name': row['exportName'], 'mesh': i}, 'Source original display translation applied')
        p = d['meshes'][i]['primitives'][0]
        require(set(p['attributes']) == {'POSITION', 'NORMAL', 'TEXCOORD_0'} and p['mode'] == 4, 'Original attributes changed')
        for role in ('NORMAL', 'TEXCOORD_0'):
            require(old.accessor(d, [blob], p['attributes'][role])[1] == row['_attributeBytes'][role][1], 'Original normal/UV bytes changed')
        require(old.accessor(d, [blob], p['indices'])[1] == row['_indexBytes'], 'Original triangle order/winding/connectivity changed')
        require(old.accessor(d, [blob], p['attributes']['POSITION'])[0] == [tuple(p) for p in row['positionMeters']], 'Only declared rooted original F32 POSITION allowed')
    return {'models': 3, 'vertices': 2677, 'triangles': 3848, 'originalNormalUvIndexBytesExact': True,
            'positionBottomShiftExplicitF32': True, 'originalWindingPreserved': True,
            'sourceTangentAttributePresent': False, 'derivedTangentAttributeInvented': False,
            'nativeR34ReadbackPerformed': False}


def load_source():
    p = read(STUDY/'fern-only-source-plan.json')
    require(p['schema'] == 'brezi-garden-fern-only-source-r34' and p['owner'] == 'scripts/unreal/exterior-garden-fern-only-study-r34.py'
            and p['status'] == 'source-only-36-fern-fits-original-ornamentals-retained-native-pending', 'Closed R34 source plan required')
    for row in p['inputFiles']:
        checked(row)
    ref = reference()
    selection(p, ref)
    require(p['actualNativeBase']['report'] == ref['base']['reportPin'] and p['actualNativeBase']['process'] == ref['base']['process']
            and p['nativeClone'] is None and p['futureYardIntegration']['gardenNativeReport'] is None
            and p['futureYardIntegration']['ownGardenVisualAcceptanceRequired'] is True, 'Actual base/future scope distinction differs')
    descriptor = read(checked(p['geometryDescriptor']))
    require(descriptor['models'] == [{k: v for k, v in ref['models'][m].items() if not k.startswith('_')} for m in MODELS], 'Exactly3 original master descriptors required')
    decode_export(checked(p['sourceGlb']).read_bytes(), ref['models'])
    require(read(checked(p['plannedRetainedNativeControls']))['controls'] == retained_controls(ref), 'Planned437 exact raw controls differ')
    footprints(ref)
    for key in ('nativeApplied', 'nativeGeometryVerified', 'nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified', 'packageVerified'):
        require(p[key] is False, 'Source-only plan fabricates acceptance')
    return p, ref
