"""NEW R25 draft: original-source and single-root counterfactual guards.

The immutable source plan intentionally has no native base. A later preflight
must pin a terminal, actually saved R22 receipt; absence is a blocking error.
This module never imports Unreal, loads a native project or modifies source.
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
OWNER = 'scripts/unreal/exterior-garden-fern-guards-r25.py'
SCHEMA = 'brezi-original-fern-own-garden-single-root-overlay-r25'
SOURCE = ROOT/'output/unreal/exterior-garden-fern-20261002-r25-study/fern-pilot-source-plan.json'
SOURCE_SHA = 'b3c1453765e310a47416507236c24adff2b3517b4bacd5a882fefa5c0df9709b'
SOURCE_PRODUCER = ROOT/'scripts/unreal/exterior-garden-fern-study-r25.py'
SOURCE_PRODUCER_SHA = '30c08165145f91adcfca1d89ee33a6528445ec1b535b1c8e4c6e3d6922fd408e'
FREEZE = ROOT/'output/unreal/exterior-garden-fern-20261002-r25-source-review/source-freeze.json'
FREEZE_SHA = 'ed8011107fb4b1c97423ed8477b923e97af7083679443b73b53e01a75654192f'
PREFIX = '/Game/Brezi/GardenFern20261002R25'
MODEL = 'garden_fern_original_b_r25'
GROUP = 'EX_ornamental_0_-1_garden_feather_r3_b_18000'
NUMERICAL_CROWN_CAP_CM = .002
BASE_OWNER = 'scripts/unreal/exterior-realism-integration-native-r22-r3.py'
BASE_HELPER_SHA = 'f93ea98e9599ac85abd2842dc8c08d50f7977366fa1bb3ae35b5923bfd12cbae'
BASE_REPORT = ROOT/'output/unreal/exterior-20261002-r22c/realism-integration-native-report-r3.json'
BASE_REPORT_SHA = '999fc17ea7600136a2097aecefed3d846ff0d7e9baeb7f005480b113b60b1f40'
NATIVE_OUTPUT = ROOT/'output/unreal/exterior-20261002-r25a'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def checked(record):
    path = Path(record['path']).resolve()
    require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == record['sha256']
            and ('bytes' not in record or path.stat().st_size == record['bytes']), 'Source pin changed: '+str(path))
    return path


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def source():
    require(sha(SOURCE) == SOURCE_SHA and sha(SOURCE_PRODUCER) == SOURCE_PRODUCER_SHA
            and sha(FREEZE) == FREEZE_SHA, 'Frozen original Fern source changed')
    plan = read(SOURCE)
    require(plan['schema'] == 'brezi-original-fern-own-garden-source-pilot-r25'
            and plan['owner'] == 'scripts/unreal/exterior-garden-fern-study-r25.py'
            and plan['status'] == 'source-only-original-fern-own-garden-pilot-native-base-pending'
            and plan['generatorSha256'] == SOURCE_PRODUCER_SHA, 'Typed original source plan required')
    require(all(plan['audit'][k] is False for k in ('nativeApplied', 'nativeGeometryReadbackPerformed',
            'nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified')),
            'Source plan cannot claim native or acceptance')
    freeze = read(FREEZE)
    for row in freeze['files']:
        checked(row)
    for path, value in plan['inputFiles'].items():
        require(sha(path) == value, 'Frozen original source input changed')
    geometry = read(checked(plan['selectedOriginalGeometry']))
    producer = module('r25_frozen_original_source_reader', SOURCE_PRODUCER)
    gltf_path = checked(plan['sourceGltf'])
    document = read(gltf_path)
    binaries = [(gltf_path.parent/b['uri']).read_bytes() for b in document['buffers']]
    rows = producer.decode(document, binaries)
    selected = next(r for r in rows if r['node'] == plan['selectedNode'])
    require(digest(geometry) == digest({k: selected[k] for k in ('_positions', '_normals', '_uv', '_indices')}),
            'Selected original FLOAT geometry/UV/order changed')
    require(selected['vertices'] == 1660 and selected['triangles'] == 2384
            and sum(r['triangles'] for r in rows) == 6232 and len(rows) == 4,
            'Original distinct four-clump geometry census differs')
    require(not selected['sourceTangentsPresent'] and not selected['extensions']
            and selected['degenerateTriangles'] == selected['opposedMeanNormalTriangles']
            == selected['degenerateUvTriangles'] == 0, 'Original fern geometry/attribute contract differs')
    garden = read(checked(plan['sourceGarden']))
    root = next(r for r in garden['ornamentalPlacements'] if r['id'] == 'garden_ornamental_10')
    proposal = plan['placementProposal']
    require(proposal['originalRoot'] == root and proposal['positionCm'] == root['positionCm']
            and proposal['yawDeg'] == root['yawDeg'] and proposal['scale'] == [proposal['uniformScale']]*3,
            'Original single source root/frame/uniform fit changed')
    original_guard = producer.load_guard()
    boundaries = original_guard._boundary(garden['sourceMulchTrianglesCm'][root['sourceBedId']])
    clearance = min(original_guard._distance(root['positionCm'][:2], a, b) for a, b in boundaries)
    # Derived distances use inequalities. The pinned authoring scale, positions,
    # normals/UV/indices are exact controls; cross-runtime libm is not equality proof.
    radius = max(math.hypot(p[0]*proposal['uniformScale'], p[1]*proposal['uniformScale'])
                 for p in selected['_nativePositions'])
    require(radius <= root['radiusCm']+NUMERICAL_CROWN_CAP_CM
            and radius+NUMERICAL_CROWN_CAP_CM < clearance, 'Complete source crown exceeds original own bed')
    angle = math.radians(root['yawDeg'])
    c, s = math.cos(angle), math.sin(angle)
    native = [[f32(x*100), f32(z*100), f32(y*100)] for x, y, z in geometry['_positions']]
    uv = [[f32(x) for x in v] for v in geometry['_uv']]
    indices = [i for j in range(0, len(geometry['_indices']), 3)
               for i in (geometry['_indices'][j], geometry['_indices'][j+2], geometry['_indices'][j+1])]
    for p in native:
        world = [root['positionCm'][0]+proposal['uniformScale']*(c*p[0]-s*p[1]),
                 root['positionCm'][1]+proposal['uniformScale']*(s*p[0]+c*p[1])]
        require(any(original_guard._triangle_inside(world, t)
                    for t in garden['sourceMulchTrianglesCm'][root['sourceBedId']]), 'Native FLOAT source vertex leaves mulch')
    row = {'id': MODEL, 'vertices': len(native), 'triangles': len(indices)//3,
           'expectedNativeVerticesCm': native, 'uv0': uv, 'indices': indices,
           'sourceNormalAttributePreservedInExport': True, 'sourceTangentAttributePresent': False,
           'nativeNormalsTangentsReadbackAvailable': False}
    return {'plan': plan, 'garden': garden, 'root': root, 'geometry': geometry,
            'gltf': document, 'binaries': binaries, 'selected': selected, 'row': row}


def write_glb(path, bundle):
    """One mesh, original source accessor bytes. Four provider sources remain untouched."""
    doc = bundle['gltf']
    primitive = copy.deepcopy(doc['meshes'][0]['primitives'][0])
    require(doc['nodes'][0]['name'] == 'fern_02_b' and primitive['attributes']
            == {'POSITION': 0, 'NORMAL': 1, 'TEXCOORD_0': 2} and primitive['indices'] == 3,
            'Original selected source accessor layout changed')
    primitive.pop('material')
    primitive['mode'] = 4
    views = copy.deepcopy(doc['bufferViews'][:4])
    extent = max(v.get('byteOffset', 0)+v['byteLength'] for v in views)
    binary = bundle['binaries'][0][:extent]
    for index, view in enumerate(views):
        view['target'] = 34963 if index == 3 else 34962
    name = MODEL+'_LOD0'
    new_doc = {'asset': {'version': '2.0', 'generator': OWNER}, 'scene': 0,
        'scenes': [{'nodes': [0]}], 'nodes': [{'name': name, 'mesh': 0}],
        'meshes': [{'name': name, 'primitives': [primitive]}],
        'accessors': copy.deepcopy(doc['accessors'][:4]), 'bufferViews': views,
        'buffers': [{'byteLength': len(binary)}]}
    encoded = json.dumps(new_doc, separators=(',', ':'), allow_nan=False).encode()
    encoded += b' '*((-len(encoded)) % 4)
    binary += b'\0'*((-len(binary)) % 4)
    Path(path).write_bytes(struct.pack('<III', 0x46546C67, 2, 28+len(encoded)+len(binary))
        +struct.pack('<II', len(encoded), 0x4E4F534A)+encoded
        +struct.pack('<II', len(binary), 0x004E4942)+binary)
    return decode_glb(path, bundle)


def decode_glb(path, bundle):
    raw = Path(path).read_bytes()
    require(struct.unpack_from('<III', raw) == (0x46546C67, 2, len(raw)), 'Own GLB header invalid')
    size, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4E4F534A, 'Own GLB JSON missing')
    doc = json.loads(raw[20:20+size])
    start = 20+size
    length, kind = struct.unpack_from('<II', raw, start)
    require(kind == 0x004E4942 and start+8+length == len(raw), 'Own GLB binary extent invalid')
    binary = raw[start+8:]
    expected = bundle['gltf']
    require(doc['nodes'] == [{'name': MODEL+'_LOD0', 'mesh': 0}]
            and len(doc['meshes']) == 1 and doc['accessors'] == expected['accessors'][:4]
            and not doc.get('materials') and not doc.get('textures')
            and not doc.get('extensionsUsed'), 'Own isolated original subset contract differs')
    for old_view, view in zip(expected['bufferViews'][:4], doc['bufferViews']):
        old_start = old_view.get('byteOffset', 0)
        new_start = view.get('byteOffset', 0)
        require(view['byteLength'] == old_view['byteLength']
                and binary[new_start:new_start+view['byteLength']]
                == bundle['binaries'][0][old_start:old_start+old_view['byteLength']],
                'Original FLOAT attribute/index bytes changed')
    return {'meshCount': 1, 'vertices': 1660, 'triangles': 2384,
            'originalPositionNormalUvIndexBytesPreserved': True,
            'providerFourClumpsAndResourcesUntouched': True, 'sourceTangentsPresent': False,
            'nativeGeometryReadback': False, **pin(path)}


def component(witness, actor, name):
    require(actor in witness, 'Original target actor missing')
    rows = [r for r in witness[actor]['components'] if r['name'] == name]
    require(len(rows) == 1, 'Original target component ambiguous')
    return rows[0]


def expected_witness(before, actor, component_name, old_mesh, new_mesh, new_material, value):
    expected = copy.deepcopy(before)
    original = component(before, actor, component_name)
    require(len(before) == 5346 and original['mesh'] == old_mesh and original['instanceCount'] == 1
            and original['instanceCullCm'] == [14400, 18000], 'Exact inherited single-root actor scope differs')
    changed = component(expected, actor, component_name)
    changed.update(mesh=new_mesh, materials=[new_material], overrideMaterials=[],
                   orderedInstanceTransformsSha256=digest([value]))
    return expected


def verify_counterfactual(before, saved, actor, component_name, old_mesh, new_mesh, new_material, value):
    expected = expected_witness(before, actor, component_name, old_mesh, new_mesh, new_material, value)
    require(saved == expected, 'Single garden-root change exceeds full5346 actor counterfactual')
    return expected


def validate_content(before, after, packages):
    require(set(before) <= set(after) and len(before) == 4049, 'Original saved R22 Content missing')
    changed = [p for p in before if before[p] != after[p]]
    require(changed == ['Brezi/Maps/Brezi.umap'], 'Only candidate map may change among original files')
    require(len(set(packages)) == len(packages) == 9 and all(p.startswith(PREFIX+'/') for p in packages),
            'Exactly1mesh+1graph+4texture+3pipeline packages required')
    expected = {p.removeprefix('/Game/') for p in packages}
    added = sorted(set(after)-set(before))
    require(all(Path(p).suffix in ('.uasset', '.uexp', '.ubulk')
                and str(Path(p).with_suffix('')) in expected for p in added)
            and {p for p in added if p.endswith('.uasset')} == {p+'.uasset' for p in expected},
            'New R25 package namespace/population differs')
    return {'changedFiles': changed, 'newFiles': added, 'removedFiles': [],
            'newUassetPackages': 9, 'originalViewpointsByteIdentical': True,
            'protectedOriginalContentFilesByteIdentical': len(before)-1}


def validate_base_header(report):
    require(report['schema'] == 'brezi-exterior-realism-saved-donor-integration-r22'
            and report['owner'] == BASE_OWNER
            and report['status'] == 'verified-saved-six-donor-exterior-realism-integration'
            and report['savedMapUnloadedReloaded'] is True and report['sourceInputsUnchanged'] is True,
            'Actual completed saved R22 R3 required')
    require(report['output'] == str(BASE_REPORT.parent)
            and report['project'] == str(BASE_REPORT.parent/'Project/BreziTwin')
            and report['scopedMaterialGraphs'] == 56 and report['scopedTextureObjects'] == 84
            and report['actualFullSceneHismComponents'] == 2312
            and report['actualFullSceneHismInstances'] == 676944
            and report['actualRecordedExteriorHismGroups'] == 1987
            and report['actualRecordedExteriorHismInstances'] == 632538,
            'Actual saved R22 population/material scope differs')
    require(report['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
            and report['setbacksMm'] == {'street': 3000, 'east': 3000}, 'Protected C/B/B or3000mm setbacks changed')
    require(all(report[k] is False for k in ('nativeAppearanceAccepted', 'fullPhotorealismAccepted',
            'performanceAccepted', 'shippingPackageProduced')), 'Base receipt cannot grant scene acceptance')


def validate_clone(base):
    path = NATIVE_OUTPUT/'garden-fern-project-clone.json'
    data = read(path)
    source_project = Path(base['report']['project'])
    project = NATIVE_OUTPUT/'Project/BreziTwin'
    require(data['schema'] == SCHEMA and data['status']
            == 'verified-byte-identical-independent-apfs-r25a-original-r22-project-clone-before-fern-native'
            and data['sourcePlan'] == pin(SOURCE) and data['nativeBaseReport'] == base['reportPin']
            and data['sourceProject'] == str(source_project) and data['project'] == str(project)
            and data['fileCount'] == 4181 and data['contentFiles'] == 4049 and data['protectedFiles'] == 132
            and data['nativeExecuted'] is False and data['nativePreflightPending'] is True
            and data['sourcePreflight'] is None,
            'Immutable initial root clone must retain typed source/base and historical pending state')
    require(data['baseContentInventory'] == base['report']['afterContentInventory']
            and data['baseProtectedProjectProof'] == base['report']['protectedProjectProof'],
            'Initial clone base inventory pins differ')
    expected = {**{'Content/'+p: row for p, row in base['content'].items()}, **base['protected']}
    observed = {}
    for row in data['files']:
        relative = str(Path(row['destination']).relative_to(project))
        require(relative not in observed and row['source'] == str(source_project/relative)
                and row['independentInodes'] is True, 'Initial clone member scope/ownership differs')
        observed[relative] = {'sha256': row['sha256'], 'bytes': row['bytes']}
        a, b = source_project/relative, project/relative
        require(a.stat().st_size == b.stat().st_size == row['bytes']
                and (a.stat().st_dev, a.stat().st_ino) != (b.stat().st_dev, b.stat().st_ino),
                'Initial candidate member is missing/resized/hardlinked')
    require(observed == expected and len(data['files']) == len(observed) == 4181,
            'Initial clone must close every exact4049Content+132protected member')
    return pin(path)


def saved_native_base():
    """A source-selected, failed or merely live R22 trial cannot become the base."""
    require(BASE_REPORT.is_file(), 'Actual saved R22 base is pending; native preparation is blocked')
    require(sha(BASE_REPORT) == BASE_REPORT_SHA, 'Selected actual saved R22 report changed')
    report = read(BASE_REPORT)
    validate_base_header(report)
    directory = BASE_REPORT.parent
    raw_path = directory/'realism-integration-native-r3.log.json'
    process_path = directory/'realism-integration-native-r3-process.json'
    raw = read(raw_path)
    process = read(process_path)
    require(raw['code'] == 0 and raw['signal'] is None and raw['pid'] == report['nativeProcessId']
            and raw['command'] == '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd'
            and raw['args'][0] == str(directory/'Project/BreziTwin/BreziTwin.uproject')
            and '-run=pythonscript' in raw['args'] and '-nullrhi' in raw['args']
            and '-script='+str(ROOT/BASE_OWNER) in raw['args'], 'Actual original R22 native process must exit0')
    require(process['processFile'] == str(raw_path) and process['processFileSha256'] == sha(raw_path)
            and process['reportSha256'] == sha(BASE_REPORT) and process['sourcePinsUnchangedAfterNative'] is True
            and sha(process['logFile']) == process['logSha256'], 'Sealed actual R22 terminal/process/report differs')
    require(len(process['sourcePinsBeforeNative']) == 430
            and process['controllerSha256BeforeNative'] == process['controllerSha256AfterNative']
            == sha(process['controller']), 'Actual R22 terminal430 ownership/controller witness differs')
    for path, value in process['sourcePinsBeforeNative'].items():
        require(sha(path) == value, 'Actual R22 terminal consumed source changed')
    require(sha(ROOT/BASE_OWNER) == BASE_HELPER_SHA, 'Consumed saved R22 native helper changed')
    for path, value in report['inputFiles'].items():
        require(sha(path) == value, 'Consumed saved R22 source input changed')
    witness = read(checked(report['savedActorWitness']))
    require(len(witness) == 5346 and digest(witness) == report['savedActorWitnessSha256']
            == report['expectedActorWitnessSha256'], 'Saved full5346 actor witness differs')
    content = read(checked(report['afterContentInventory']))
    require(len(content) == 4049, 'Actual saved R22 Content4049 required')
    protected = read(checked(report['protectedProjectProof']))
    require(len(protected) == 132, 'Actual protected project132 required')
    native = module('r25_actual_saved_r22_native_dependency', ROOT/BASE_OWNER)
    _, base_bundle = native.guard.validate_plan()
    native.repair.validate_supplement()
    materials = read(checked(report['materialsSaved']))
    old = source()['plan']['originalSavedGroup']
    matches = [c for c in witness[old['actor']]['components'] if c.get('mesh') == old['mesh']]
    require(len(matches) == 1 and matches[0]['instanceCount'] == 1
            and matches[0]['orderedInstanceTransformsSha256'] == old['transformsSha256']
            and matches[0]['instanceCullCm'] == [14400, 18000], 'Single original garden root changed in saved R22')
    return {'report': report, 'reportPin': pin(BASE_REPORT), 'raw': pin(raw_path), 'process': pin(process_path),
            'witness': witness, 'content': content, 'protected': protected, 'materials': materials,
            'native': native, 'nativeBundle': base_bundle,
            'targetActor': old['actor'], 'targetComponent': matches[0]['name'], 'oldMesh': old['mesh']}
