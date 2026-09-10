#!/usr/bin/env python3
"""CPU-only expectations for the reviewed three-deck migration; no native acceptance."""
from pathlib import Path
from collections import defaultdict
from itertools import product
import argparse
import copy
import hashlib
import json
import math
import struct

HERE = Path(__file__).resolve().parent
CHANGED = {'DOM_01708': 936, 'DOM_01713': 420, 'DOM_01719': 768}
PRIOR_SHA = 'af9cc202a4fb4a204a47f915e457f249e4180e43b1fc55bf105c02ae1b743737'
MAP = 'Content/Brezi/Maps/Brezi.umap'
TOLERANCE_CM = .0002  # Existing source/native tolerance: .002 mm.


def need(ok, message):
    if not ok:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def sha(path, algorithm='sha256'):
    path = Path(path)
    need(path.is_file() and not path.is_symlink(), 'Missing/linked input: ' + str(path))
    h = hashlib.new(algorithm)
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def read(path):
    return json.loads(Path(path).read_text(), parse_constant=lambda v: (_ for _ in ()).throw(ValueError('Nonfinite JSON ' + v)))


def file_under(root, relative):
    p = Path(relative)
    need(not p.is_absolute() and '..' not in p.parts, 'Unsafe relative input')
    result = root / p
    need(result.resolve().is_relative_to(root.resolve()), 'Input escapes root')
    return result


def source_faces(path, ids):
    positions, out, current = [], {i: [] for i in ids}, None
    with Path(path).open() as stream:
        for line in stream:
            a = line.split()
            if not a:
                continue
            if a[0] == 'o':
                current = a[1]
            elif a[0] == 'v':
                p = [float(a[1])/10, -float(a[2])/10, float(a[3])/10]
                need(all(math.isfinite(v) for v in p), 'Nonfinite OBJ')
                positions.append(p)
            elif a[0] == 'f' and current in out:
                indices = [int(v.split('/')[0]) for v in a[1:]]
                need(len(indices) == 3 and all(0 < i <= len(positions) for i in indices), 'OBJ face invalid')
                out[current].append([positions[i-1] for i in indices])
    return out


def decode_glb(path):
    data = Path(path).read_bytes()
    need(struct.unpack_from('<III', data) == (0x46546c67, 2, len(data)), 'GLB header differs')
    n, kind = struct.unpack_from('<II', data, 12)
    need(kind == 0x4e4f534a and n % 4 == 0, 'GLB JSON chunk differs')
    obj = json.loads(data[20:20+n]); offset = 20+n
    size, kind = struct.unpack_from('<II', data, offset)
    need(kind == 0x004e4942 and offset+8+size == len(data), 'GLB BIN chunk differs')
    need(len(obj['buffers']) == 1 and 'uri' not in obj['buffers'][0], 'External GLB buffers')
    return obj, data[offset+8:]


def accessor(g, binary, index):
    a = g['accessors'][index]; view = g['bufferViews'][a['bufferView']]
    need(not a.get('sparse') and not a.get('normalized'), 'Unsupported GLB accessor')
    code, width = {5126: ('f', 4), 5123: ('H', 2), 5125: ('I', 4)}[a['componentType']]
    size = width * {'VEC3': 3, 'SCALAR': 1}[a['type']]
    need(view['buffer'] == 0 and view.get('byteStride', size) == size, 'Unsupported GLB stride')
    start = view.get('byteOffset', 0)+a.get('byteOffset', 0); end = start+a['count']*size
    need(view.get('byteOffset', 0) <= start < end <= view.get('byteOffset', 0)+view['byteLength'] <= len(binary), 'GLB accessor bounds')
    values = list(struct.iter_unpack('<'+code*(size//width), binary[start:end]))
    need(all(math.isfinite(x) for row in values for x in row), 'Nonfinite GLB')
    return values


def glb_triangles(g, binary, id_):
    matches = [(i, n) for i, n in enumerate(g['nodes']) if n.get('name') == id_]
    need(len(matches) == 1, 'GLB node multiplicity: '+id_)
    index, node = matches[0]
    need(index in g['scenes'][g.get('scene', 0)]['nodes'] and not any(index in n.get('children', []) for n in g['nodes']), 'GLB non-root')
    need(not any(k in node for k in ('matrix', 'translation', 'rotation', 'scale', 'children', 'skin')), 'GLB identity transform changed')
    need(node['extras']['source_object_id'] == id_, 'GLB source ID differs')
    mesh = g['meshes'][node['mesh']]
    need(mesh['name'] == id_ and len(mesh['primitives']) == 1, 'GLB mesh scope differs')
    p = mesh['primitives'][0]
    need(p.get('mode', 4) == 4 and not p.get('extensions') and not p.get('targets'), 'Unsupported GLB primitive')
    positions = [[100*v[0], 100*v[2], 100*v[1]] for v in accessor(g, binary, p['attributes']['POSITION'])]
    indices = [v[0] for v in accessor(g, binary, p['indices'])]
    need(len(indices) % 3 == 0 and all(0 <= i < len(positions) for i in indices), 'GLB indices invalid')
    need(set(indices) == set(range(len(positions))), 'Unused GLB position')
    return index, [[positions[i] for i in indices[k:k+3]] for k in range(0, len(indices), 3)]


def cyclic_bijection(expected, actual):
    """One-to-one winding-preserving triangle proof; centroid buckets are only candidates."""
    need(len(expected) == len(actual), 'Triangle count differs')
    def bucket(t):
        return tuple(math.floor(sum(p[k] for p in t)/3/TOLERANCE_CM) for k in range(3))
    buckets = defaultdict(list)
    for i, triangle in enumerate(expected):
        buckets[bucket(triangle)].append(i)
    used = set(); maximum = 0.
    for triangle in actual:
        key = bucket(triangle); candidates = []
        for delta in product((-1, 0, 1), repeat=3):
            candidates.extend(buckets.get(tuple(key[k]+delta[k] for k in range(3)), []))
        matches = []
        for i in candidates:
            if i in used:
                continue
            error = min(max(abs(triangle[k][axis]-expected[i][(k+shift)%3][axis])
                            for k in range(3) for axis in range(3)) for shift in range(3))
            if error <= TOLERANCE_CM:
                matches.append((i, error))
        need(len(matches) == 1, 'Triangle winding/position/multiplicity differs')
        used.add(matches[0][0]); maximum = max(maximum, matches[0][1])
    need(len(used) == len(expected), 'Triangle coverage incomplete')
    return maximum


def validate_native(review, adoption, verification, processes, project):
    need(review['status'] == 'shared-deck-source-to-native-reload-validated', 'Native review incomplete')
    need(review['changedObjectIds'] == sorted(CHANGED) and review['unchangedSourceObjects'] == 1892, 'Revision scope differs')
    for key in ('nativeProcessesExitedZeroAndDrained', 'mapSavedAndFreshProcessReloadVerified', 'previousProjectContentUnchanged', 'nativeUv0AndMeshDescriptionUv1Verified'):
        need(review[key] is True, 'Native proof absent: '+key)
    need(adoption['status'] == 'native-deck-imported-and-map-saved-fresh-process-verification-pending', 'Adoption status differs')
    need(verification['status'] == 'native-deck-fresh-process-reload-validated' and verification['freshProcessReloadVerified'] is True, 'Fresh reload absent')
    need(set(adoption['objects']) == set(verification['objects']) == set(adoption['replacements']) == set(CHANGED), 'Native selected scope differs')
    for report in (review, adoption, verification):
        need(Path(report['project']).resolve() == project, 'Native project differs')
    for report in (adoption, verification):
        need(report['worldComparison']['actorCount'] == 1968 and report['worldComparison']['onlyThreeMeshPathsChanged'] is True, 'Native world scope differs')
    for phase, process, pid in zip(('adopt', 'verify'), processes, (review['nativeAdoptionPid'], review['nativeVerificationPid'])):
        need(process['pid'] == pid and type(pid) is int and pid > 0, 'Native PID join differs')
        need(process['status'] == 'native-deck-phase-exited-zero-and-drained' and process['nativeExitCode'] == 0, 'Native exit failed')
        need(process['remainingOwned'] == [] and process['errors'] == [] and process['argvObservationGaps'] == [], 'Native process closure failed')
        need(process['previousContentUnchanged'] is True and process['scriptsUnchanged'] is True, 'Native protection failed')
        need(Path(process['projectRoot']).resolve() == project and process['environmentSet']['BREZI_DECK_PHASE'] == phase, 'Native phase/project differs')
    need(processes[0]['pid'] != processes[1]['pid'], 'Reload reused native PID')
    need(processes[1]['contentDelta'] == {}, 'Read-only reload mutated Content')
    for id_, count in CHANGED.items():
        before, after = adoption['objects'][id_], verification['objects'][id_]
        need(after['savedReloadVerified'] is True and after['meshDescriptionUV1ExactFloat32'] is True, 'UV1 saved reload absent')
        for key in ('mesh', 'material', 'uv1Sha256', 'naniteSettings'):
            need(before[key] == after[key], 'Saved deck identity/UV1/settings differ')
        for report in (before, after):
            p = report['sourceProof']
            need(p['triangleCount'] == count and p['nativeVertexInstanceCoverageComplete'] is True and p['canonicalTriangleConnectivityMultiplicityAndWindingVerified'] is True, 'Native topology proof differs')
            need(p['nativeUv0Preserved'] is True and p['maximumVertexErrorMm'] <= .002 and p['maximumUv0Error'] <= 2e-6, 'Native source tolerance failed')


def derive_binding(*, repo_root, source_dir, project, previous_binding, native_context, native_review_sha256):
    """Return (binding, CPU report) without writing. Explicit caller paths, reviewed migration only."""
    root, source, project = (Path(p).resolve() for p in (repo_root, source_dir, project))
    previous_binding, native_context = Path(previous_binding).resolve(), Path(native_context).resolve()
    need(sha(previous_binding) == PRIOR_SHA, 'Previous reviewed binding changed')
    prior = read(previous_binding); context = read(native_context)
    need(Path(context['project']).resolve() == project and Path(context['source']).resolve() == source, 'Context paths differ')
    review_path = Path(context['nativeReview']); need(sha(review_path) == native_review_sha256 == context['nativeReviewSha256'], 'Native review pin differs')
    review = read(review_path); pins = {}
    def pin(path, expected=None):
        path = Path(path).resolve(); value = sha(path)
        need(expected is None or value == expected, 'Input pin differs: '+str(path))
        pins[str(path.relative_to(root))] = value
        return value
    # The mutable context pointer is read for path selection, never a frozen input dependency.
    pin(previous_binding, PRIOR_SHA); pin(review_path, native_review_sha256); pin(Path(__file__).resolve())
    for path, value in review['fileHashes'].items():
        pin(path, value)
    reports = [read(context[k]) for k in ('adoptionReport', 'verificationReport', 'adoptionProcess', 'verificationProcess')]
    adoption, verification, ap, vp = reports
    for key in ('adoptionReport', 'verificationReport', 'adoptionProcess', 'verificationProcess', 'delta'):
        need(str(Path(context[key])) in review['fileHashes'], 'Review does not pin '+key)
    validate_native(review, adoption, verification, (ap, vp), project)
    delta = read(context['delta'])
    need(delta['status'] == 'shared-deck-geometry-delta-validated' and delta['changedObjectIds'] == sorted(CHANGED), 'CPU delta scope differs')
    need(delta['unchangedObjectCount'] == 1892 and delta['modelDimensionsMaterialsAndHatchUnchanged'] is True and delta['hiddenCollisionBytesUnchanged'] is True, 'CPU delta preservation absent')
    need(Path(delta['candidate']).resolve() == source, 'Delta source path differs')
    scene_path, obj_path, glb_path = [source/name for name in ('scene.json', 'dom-mm.obj', 'brezi-twin.glb')]
    scene_sha = pin(scene_path, delta['candidateSceneSha256']); obj_sha = pin(obj_path, delta['candidateObjSha256']); glb_sha = pin(glb_path)
    scene, bridge = read(scene_path), read(source/'bridge-report.json'); pin(source/'bridge-report.json')
    need(bridge['status'] == 'geometry-converted' and bridge['sceneSha256'] == scene_sha and bridge['sourceObjSha256'] == obj_sha, 'GLB bridge lineage differs')
    for rel, value in bridge['sourceFiles'].items():
        pin(file_under(root, rel), value)
    need(vp['inputPins'][str(glb_path)] == glb_sha and vp['inputPins'][str(scene_path)] == scene_sha and vp['inputPins'][str(obj_path)] == obj_sha, 'Native/source input join differs')
    for row in verification['objects'].values():
        need(row['sourceProof']['sourceObjSha256'] == obj_sha, 'Native source proof is stale')
    old_source = Path(delta['base']); old_scene = read(old_source/'scene.json')
    pin(old_source/'scene.json', prior['sourceSceneSha256']); pin(old_source/'dom-mm.obj', prior['sourceObjSha256'])
    need(delta['baseSceneSha256'] == prior['sourceSceneSha256'] and delta['baseObjSha256'] == prior['sourceObjSha256'], 'Delta prior origin differs')
    records = {r['id']: r for r in scene['objects']}; old_records = {r['id']: r for r in old_scene['objects']}
    need(len(records) == len(scene['objects']) == len(old_records) == 1895 and records.keys() == old_records.keys(), 'Scene object scope differs')
    need(all(records[id_] == row for id_, row in old_records.items() if id_ not in CHANGED), 'Unrelated scene record changed')
    need(all(records[id_]['triangles'] == n for id_, n in CHANGED.items()), 'Deck revision topology differs')
    walking_path = source/'walking.json'; walking = read(walking_path); pin(walking_path)
    old_walking = read(old_source/'walking.json')
    need({k: v for k, v in walking.items() if k != 'provenance'} == {k: v for k, v in old_walking.items() if k != 'provenance'}, 'Walking constraints changed')
    need(walking['provenance']['sceneSha256'] == scene_sha and walking['provenance']['sourceObjSha256'] == obj_sha, 'Walking source provenance differs')
    resource = previous_binding.parent
    receiver_path, water_path = resource/'receiver-contract.json', resource/'active-water-binding.json'
    pin(receiver_path, prior['receiverContractSha256']); pin(water_path, prior['activeWaterBindingSha256'])
    receiver, water = read(receiver_path), read(water_path)
    imp_path = root/'output/unreal/import-report.json'; pin(imp_path, prior['importReportSha256']); historical_import = read(imp_path)
    need(historical_import['status'] == 'import-validated' and historical_import['mapFileSha256'] == prior['mapSha256'], 'Historical import origin differs')
    need(water['provenance']['importReport']['sha256'] == prior['importReportSha256'] and water['waveCount'] == 12 and len(water['savedNormalRows']) == 12, 'Saved water provenance differs')
    ids = [r['id'] for r in prior['objects']]
    need(len(ids) == len(set(ids)) == 46 and set(ids) == {r['id'] for r in receiver['receiverObjects']} | {prior['waterObjectId']}, 'Receiver/water scope differs')
    faces = source_faces(obj_path, ids); g, binary = decode_glb(glb_path); rows = []; maximum = 0.
    for old in prior['objects']:
        id_ = old['id']; record = records[id_]
        need(digest(record) == old['sourceRecordSha256'], 'Retained full source record changed: '+id_)
        need(record['enabled'] is True and record['instances'] == 1 and record['triangles'] == old['sourceTriangles'], 'Retained source policy differs')
        need(faces[id_] == old['trianglesCm'], 'Frozen source geometry/order differs: '+id_)
        index, triangles = glb_triangles(g, binary, id_)
        maximum = max(maximum, cyclic_bijection(faces[id_], triangles))
        row = copy.deepcopy(old); row['glbNodeIndex'] = index; rows.append(row)
    need(sum(r['sourceTriangles'] for r in rows if r['role'] == 'receiver') == 1076 and next(r for r in rows if r['role'] == 'water')['sourceTriangles'] == 4608, 'Triangle scope differs')
    assets = copy.deepcopy(prior['assetFileHashes']); need(len(assets) == 55, 'Receiver asset scope differs')
    for rel, value in assets.items():
        p = file_under(project, rel); pin(p, value['sha256']); need(sha(p, 'sha1') == value['sha1'], 'Receiver SHA1 differs')
    map_path = project/MAP; map_sha = pin(map_path, review['fileHashes'][str(map_path)])
    need(map_sha != prior['mapSha256'], 'Map revision absent')
    additional = {}
    for id_, replacement in adoption['replacements'].items():
        path = replacement['mesh'].split('.')[0]
        need(path.startswith('/Game/Brezi/MaterialStudies/DeckGap/'), 'New deck ownership differs')
        rel = 'Content/'+path.removeprefix('/Game/')+'.uasset'
        need(rel not in assets and replacement['mesh'] == verification['objects'][id_]['mesh'], 'Deck asset scope differs')
        additional[rel] = pin(project/rel, review['fileHashes'][str(project/rel)])
    expected_delta = set(review['newSuccessfulContentFiles'])
    need(set(ap['contentDelta']) == expected_delta and {p.removeprefix('Content/') for p in set(additional) | {MAP}} <= expected_delta and len(expected_delta) == 5, 'Native Content delta differs')
    need(ap['contentDelta'][MAP.removeprefix('Content/')]['before'] == prior['mapSha256'], 'Native prior map differs')
    for rel, change in ap['contentDelta'].items():
        need(change['after'] == pin(project/'Content'/rel), 'Native Content after-hash differs')
        if rel != MAP.removeprefix('Content/'):
            need(change['before'] is None, 'New deck namespace overwrote prior asset')
    revision = {'kind': 'reviewed-three-deck-migration', 'changedObjectIds': sorted(CHANGED), 'nativeReview': {'path': str(review_path.relative_to(root)), 'sha256': native_review_sha256},
        'adoptionReportSha256': sha(context['adoptionReport']), 'freshReloadReportSha256': sha(context['verificationReport']),
        'adoptionProcessSha256': sha(context['adoptionProcess']), 'freshReloadProcessSha256': sha(context['verificationProcess']),
        'nativeAdoptionPid': ap['pid'], 'nativeFreshReloadPid': vp['pid'], 'mapSavedAndFreshProcessReloadVerified': True,
        'requiredAdditionalPackages': additional, 'mapSha256': map_sha, 'currentWalking': {'path': str(walking_path.relative_to(root)), 'sha256': sha(walking_path)},
        'frozenReceiverOrigin': {'sceneSha256': prior['sourceSceneSha256'], 'objSha256': prior['sourceObjSha256'], 'previousBindingSha256': PRIOR_SHA},
        'receiverAndWaterSourceRecordsUnchanged': True, 'receiverAndWaterOrderedObjTrianglesUnchanged': True,
        'glbCyclicTriangleBijectionPassed': True, 'maximumGlbVertexErrorMm': maximum*10,
        'nativeTransportPending': True, 'nativeVisualAcceptance': False, 'packagedAppContainsRevision': False}
    state = {'kind': 'reviewed-three-deck-revision-state-not-full-import', 'mapSha256': map_sha, 'receiverAssetHashes': assets,
        'replacements': adoption['replacements'], 'nativeReviewSha256': native_review_sha256, 'freshReloadReportSha256': sha(context['verificationReport'])}
    binding = {k: copy.deepcopy(v) for k, v in prior.items() if k not in ('sourceFileHashes', 'runtimeProof', 'nativeAuthoredStateSha256')}
    binding.update({'sourceSceneSha256': scene_sha, 'sourceObjSha256': obj_sha, 'sourceGlbSha256': glb_sha, 'mapSha256': map_sha,
        'objects': rows, 'sourceFileHashes': dict(sorted(pins.items())), 'sourceRevision': revision,
        'importReportRole': 'historical-base-only-not-current-map', 'nativeAuthoredStateSha256': digest(state), 'nativeAuthoredStateKind': state['kind'],
        'historicalProvenance': {'importReportSha256': prior['importReportSha256'], 'mapSha256': prior['mapSha256'], 'nativeAuthoredStateSha256': prior['nativeAuthoredStateSha256'], 'nativeAcceptanceReused': False},
        'runtimeProof': {'requiresPerFrameWorldPoseVisibilityMaterialIdentity': True, 'requiresEditorStartupNativeTriangleBijection': True,
            'allSourceAssetsCandidateByteEqual': True, 'nativeExecuted': False, 'nativeTransportPending': True,
            'opaqueTlasCoverageVerified': False, 'fullGlassAlphaTransmissionVerified': False, 'fullPhysicalValidated': False}})
    report = {'status': 'scene-revision-cpu-validated-native-transport-pending', 'sourceRevision': revision, 'sourceFileCount': len(pins),
        'receiverCount': 45, 'waterCount': 1, 'receiverTriangles': 1076, 'waterTriangles': 4608, 'preservedAssetFiles': 55,
        'historicalImportIsCurrent': False, 'nativeAuthoredStateDescriptor': state,
        'limitations': ['Native adoption/fresh reload is historical input evidence, not CPU execution.', 'New 46-object live binding and two transport phases have not run.',
            'Changed decks can affect incoming opaque TLAS visibility despite unchanged receivers.', 'GLB proof checks positions/topology/winding; native normals, Nanite clusters and render UV1 are not newly certified.']}
    # Every immutable dependency is checked again before returning any result.
    for rel, value in pins.items():
        need(sha(file_under(root, rel)) == value, 'Input changed during export: '+rel)
    return binding, report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('repo-root', 'source-dir', 'project', 'previous-binding', 'native-context', 'native-review-sha256', 'output'):
        parser.add_argument('--'+name, required=True)
    args = vars(parser.parse_args()); output = Path(args.pop('output')).resolve()
    need(output.is_relative_to(Path(args['repo_root']).resolve()/'output') and not output.is_relative_to(Path(args['project']).resolve()) and not output.exists(), 'Output must be a new workspace output directory outside the project')
    binding, report = derive_binding(**args)
    output.mkdir(parents=True)
    path = output/'binding.json'; path.write_text(json.dumps(binding, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    report['binding'] = {'path': str(path), 'sha256': sha(path), 'sha1': sha(path, 'sha1')}
    (output/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
    print(json.dumps({'status': report['status'], 'binding': report['binding'], 'reportSha256': sha(output/'report.json')}))


if __name__ == '__main__':
    main()
