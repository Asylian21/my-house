"""UNBOUND Data-only exact two-camera insertion on a future saved R39c QA clone.

No Unreal import or asset/map operation. The direct saved consumer closes
before staging; an immutable reader/readiness pin is mandatory before any write.
All original UTF-8 camera bytes remain untouched outside the two-entry insertion.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighbor-props-camera-stage-r30.py'
SCHEMA = 'brezi-saved-original-neighbor-props-r39r3-two-camera-data-only-qa-clone-r30'
CLONE_SCHEMA = 'brezi-original-neighbor-props-two-camera-independent-qa-project-clone-r30'
STATUS = 'verified-independent-saved-original-r39r3-two-camera-data-only-qa-clone-r30'
SOURCE = ROOT/'output/unreal/exterior-20261002-r39c'
READER = ROOT/'scripts/unreal/exterior-editor-source-r30.mjs'
CLOSE_SUPPLEMENT = ROOT/'output/unreal/exterior-context-yard-20261002-camera-r18-supplement/context-yard-camera-supplement.json'
CLOSE_SUPPLEMENT_SHA = '768274f6eb2dab6d7bcd0bee2b930feec8e2665bba7dfafb6e929f35b38ebab1'
CAMERA_PROPOSAL = ROOT/'output/unreal/exterior-context-yard-soft-coherence-20261002-r38-editor-r29-r3-camera/camera-proposal.json'
TEMPLATE = ROOT/'scripts/unreal/exterior-soft-ground-camera-stage-r29-r3.py'
TEMPLATE_SHA = 'ce4658f17dc0d25b2b70f346c1955818b9d68acd6c612628de542593b9a1f6c3'
TEMPLATE_RECEIPT = ROOT/'output/unreal/exterior-20261002-r38b-two-camera-candidate-r29-r3/soft-ground-camera-stage-receipt-r29-r3.json'
TEMPLATE_RECEIPT_SHA = '3808d7d6a63c81b3ac83ed9aa44912af64de1a588561c4debbfdd6316d72d020'
CAMERA_PROPOSAL_SHA = 'ab77379c4f97dd351b15c4e48d0791825ec3f5eab685efddc659bad6cb9ec996'
QA_OUTPUT = ROOT/'output/unreal/exterior-20261002-r39c-neighbor-props-two-camera-candidate-r30'
CLONE_STATUS = 'verified-byte-identical-independent-apfs-actual-saved-r39c-before-two-camera-data-only-stage-r30'
SAVED_PROJECT_FILES, SAVED_CONTENT_FILES, PROTECTED_FILES = 4256, 4124, 132
ACTUAL = {'sourceNativeReport': {'path': '/Users/davidzita/www/dom/output/unreal/exterior-20261002-r39c/neighbor-props-native-report-r3.json',
                        'sha256': '118f451095730e2ff0e62304d959626d4a81be53f03e41dd2229fe91831f4da5',
                        'bytes': 648457},
 'sourceNativeProcess': {'path': '/Users/davidzita/www/dom/output/unreal/exterior-20261002-r39c/neighbor-props-native-r39-r3-process.json',
                         'sha256': '2bbb88ee2d71a0d81469c267f263c22beaea4f2d49eba05618d9c8896c2e96e0',
                         'bytes': 248226},
 'sourceCurrentByteAudit': {'path': '/Users/davidzita/www/dom/output/unreal/exterior-20261002-r39c/root-native-success-byte-audit-r39c-r3.json',
                            'sha256': '7f70d6eb3c59e87305313ba35b7cf7324fde14e80507b5d06e3eaecce7f17ad5',
                            'bytes': 6270},
 'sourceReader': {'path': '/Users/davidzita/www/dom/scripts/unreal/exterior-editor-source-r30.mjs',
                  'sha256': '8bbcb822f0b6065a5839f85811b611cc3a4da880b6c0d1d4f9d5c0984a8c307f', 'bytes': 26142},
 'sourceReaderReadiness': {'path': '/Users/davidzita/www/dom/output/unreal/exterior-neighbor-props-20261002-r30-editor-source-readiness/source-readiness.json',
                           'sha256': 'c1dfe8ed7e774b604a58cc0f12ee144aa5a7d567ce7def2288354ce9ffb08fb1', 'bytes': 7749},
 'nativeProcessId': 94572,
 'rootTerminalSourcePinCount': 1294,
 'qaClone': {'path': '/Users/davidzita/www/dom/output/unreal/exterior-20261002-r39c-neighbor-props-two-camera-candidate-r30/neighbor-props-camera-project-clone-r30.json',
             'sha256': '5254c26639a576bcc69d58e9f0f605d00a7132722048429df0bbddd8cadc9e28',
             'bytes': 2358560},
 'sourceOriginalViewpoints': {'path': '/Users/davidzita/www/dom/output/unreal/exterior-20261002-r39c/Project/BreziTwin/Content/Data/viewpoints.json',
                              'sha256': '25d591b3309a6a0b2297f3eb1fef4d6785379b639662d68049ccc13a12bcd846',
                              'bytes': 25167}}



def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def read(p):
    return json.loads(Path(p).read_text())


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pin(p):
    p = Path(p).resolve()
    return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}


def checked(row):
    require(isinstance(row, dict) and set(row) == {'path', 'sha256', 'bytes'}, 'Exact regular-file pin required')
    p = Path(row['path'])
    require(p.is_absolute() and p.resolve() == p and p.is_file() and not p.is_symlink()
            and pin(p) == row, 'Exact immutable input changed')
    return p


def require_bound():
    require(all(v is not None for v in ACTUAL.values()),
            'UNBOUND R30 staging requires actual saved R39c native0/audit/clone/direct-reader readiness')
    require(isinstance(ACTUAL['nativeProcessId'], int) and ACTUAL['nativeProcessId'] > 0
            and isinstance(ACTUAL['rootTerminalSourcePinCount'], int) and ACTUAL['rootTerminalSourcePinCount'] > 0,
            'Actual successful native process and complete source-pin count required')
    for k in ('sourceNativeReport', 'sourceNativeProcess', 'sourceCurrentByteAudit', 'sourceReader',
              'sourceReaderReadiness', 'qaClone', 'sourceOriginalViewpoints'):
        checked(ACTUAL[k])


def inventory(directory):
    directory = Path(directory)
    rows = {}
    for p in sorted(directory.rglob('*')):
        require(not p.is_symlink(), 'QA symlinks forbidden')
        if p.is_file():
            rows[p.relative_to(directory).as_posix()] = {k: pin(p)[k] for k in ('sha256', 'bytes')}
    return rows


def protected(project):
    rows = {'BreziTwin.uproject': {k: pin(project/'BreziTwin.uproject')[k] for k in ('sha256', 'bytes')}}
    for folder in ('Config', 'Source', 'Binaries'):
        rows.update({folder+'/'+k: v for k, v in inventory(project/folder).items()})
    return rows


def camera_append(original, close_view, ground_view):
    require(set(original) == {'coordinateSystem', 'defaultView', 'views', 'sun'}
            and isinstance(original['views'], list), 'Original whole camera document schema required')
    require(close_view['id'] == 'exterior-context-yard-572063-close-r18', 'Exact frozen R18 close view required')
    require(ground_view['id'] == 'exterior-neighborhood-ground-r38'
            and ground_view['eyeCm'] == [5900, 24700, 165]
            and ground_view['targetCm'] == [7800, 28500, 185]
            and ground_view['horizontalFovDegrees'] == 72, 'Exact source ground camera required')
    ids = [v['id'] for v in original['views']]
    require(len(ids) == len(set(ids)) and not set(ids).intersection({close_view['id'], ground_view['id']}),
            'No original duplicate camera or nested camera-stage history allowed')
    out = copy.deepcopy(original)
    out['views'].extend([copy.deepcopy(close_view), copy.deepcopy(ground_view)])
    require(out['views'][:-2] == original['views']
            and all(out[k] == original[k] for k in original if k != 'views'), 'Original complete camera prefix changed')
    return out


def append_camera_bytes(original_bytes, close_view, ground_view):
    """Insert two new entries without reserializing any old Data bytes."""
    original = json.loads(original_bytes)
    appended = camera_append(original, close_view, ground_view)
    marker = b'\n  "views": ['
    require(original_bytes.count(marker) == 1, 'Pinned original root views layout required')
    start = original_bytes.index(marker)+len(marker)-1
    depth, quoted, escaped, end = 0, False, False, None
    for i in range(start, len(original_bytes)):
        c = original_bytes[i]
        if quoted:
            if escaped:
                escaped = False
            elif c == 92:
                escaped = True
            elif c == 34:
                quoted = False
        elif c == 34:
            quoted = True
        elif c == 91:
            depth += 1
        elif c == 93:
            depth -= 1
            if depth == 0:
                end = i
                break
    require(end is not None, 'Complete original root views array required')
    insert_at = end
    while insert_at > start and original_bytes[insert_at-1] in b' \t\r\n':
        insert_at -= 1
    require(original['views'] and original_bytes[insert_at-1:insert_at] == b'}', 'Nonempty whole original view list required')
    new_entries = []
    for view in (close_view, ground_view):
        entry = '\n'.join('    '+line for line in json.dumps(view, indent=2, ensure_ascii=False, allow_nan=False).splitlines())
        new_entries.append(entry.encode())
    insertion = b',\n'+b',\n'.join(new_entries)
    payload = original_bytes[:insert_at]+insertion+original_bytes[insert_at:]
    require(json.loads(payload) == appended and payload[:insert_at] == original_bytes[:insert_at]
            and payload[insert_at+len(insertion):] == original_bytes[insert_at:],
            'Original Data prefix/suffix bytes changed outside exact two-view insertion')
    digest = lambda b: hashlib.sha256(b).hexdigest()
    return payload, appended, {'insertionOffsetBytes': insert_at, 'insertedBytes': len(insertion),
        'originalFileSha256': digest(original_bytes), 'insertedBytesSha256': digest(insertion),
        'originalPrefixSha256': digest(original_bytes[:insert_at]),
        'originalSuffixSha256': digest(original_bytes[insert_at:]),
        'allOriginalDataBytesPreservedOutsideInsertion': True}


def validate_clone(clone, source_project, project, content, proof):
    require(clone['schema'] == CLONE_SCHEMA and clone['schemaVersion'] == 1
            and clone['status'] == CLONE_STATUS
            and clone['sourceProject'] == str(source_project) and clone['project'] == str(project)
            and clone['sourceNativeReport'] == ACTUAL['sourceNativeReport']
            and clone['sourceNativeProcess'] == ACTUAL['sourceNativeProcess']
            and clone['sourceCurrentByteAudit'] == ACTUAL['sourceCurrentByteAudit']
            and clone['nativeExecuted'] is False and clone['viewpointStagingPending'] is True
            and clone['fullSavedSourceReaderValidationPending'] is True
            and clone['cameraSupplement'] is None, 'Only the typed actual pending independent R39R3 clone accepted')
    expected = {**{'Content/'+k: v for k, v in content.items()}, **proof}
    require(clone['fileCount'] == len(clone['files']) == len(expected) == SAVED_PROJECT_FILES
            and clone['contentFiles'] == len(content) == SAVED_CONTENT_FILES
            and clone['protectedFiles'] == len(proof) == PROTECTED_FILES,
            'Complete saved-source project clone required')
    seen = set()
    for row in clone['files']:
        dst = Path(row['destination'])
        require(dst.is_relative_to(project), 'Own QA clone path escapes project')
        rel = dst.relative_to(project).as_posix()
        require(rel in expected and rel not in seen and row['source'] == str(source_project/rel)
                and dst == project/rel and row['independentInodes'] is True
                and {'sha256': row['sha256'], 'bytes': row['bytes']} == expected[rel], 'Clone file proof changed')
        seen.add(rel)
        a, b = (source_project/rel).stat(), dst.lstat()
        require(dst.is_file() and not dst.is_symlink() and (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino),
                'Every Content and protected file needs independent ownership')
    require(seen == set(expected), 'Missing complete clone file rows')


def write_new(p, value):
    with Path(p).open('x') as f:
        json.dump(value, f, indent=2, allow_nan=False)
        f.write('\n')


def stage(source, output):
    require_bound()  # No filesystem mutation is reachable while this owned draft is unbound.
    require(Path(source).resolve() == SOURCE and Path(output).resolve() == QA_OUTPUT,
            'Only the exact actual saved R39R3 source and independently owned QA clone accepted')
    require(ACTUAL['sourceReader']['path'] == str(READER)
            and sha(TEMPLATE) == TEMPLATE_SHA and sha(TEMPLATE_RECEIPT) == TEMPLATE_RECEIPT_SHA
            and sha(CAMERA_PROPOSAL) == CAMERA_PROPOSAL_SHA,
            'Final owned reader and exact immutable two-camera source contract required')
    source_project = SOURCE/'Project/BreziTwin'
    out = QA_OUTPUT; project = out/'Project/BreziTwin'
    receipt = out/'neighbor-props-camera-stage-receipt-r30.json'
    after_path = out/'neighbor-props-camera-content-after-r30.json'
    validation_path = out/'neighbor-props-camera-source-validation-r30.json'
    require(all(not p.exists() for p in (receipt, after_path, validation_path)), 'Owned staging outputs must be new')
    require(not any('native-report' in p.name or 'overlay-report' in p.name or p.name == 'exterior-import-report.json'
                    for p in out.iterdir()), 'QA clone may not carry copied native receipts')
    code = """const m=await import(process.argv[1]);const e=await m.loadEditorSourceEvidence(process.argv[2],{root:process.argv[3]});
console.log(JSON.stringify({project:e.project,nativeReceiptPath:e.nativeReceiptPath,summary:e.summary,contentInventory:e.contentInventory,projectProof:e.projectProof,additionalClosureFiles:e.additionalClosureFiles}));"""
    run = subprocess.run(['node', '--input-type=module', '-e', code, READER.as_uri(), str(SOURCE), str(ROOT)],
                         capture_output=True, text=True, check=True, timeout=480)
    e = json.loads(run.stdout)
    require(e['project'] == str(source_project) and e['nativeReceiptPath'] == ACTUAL['sourceNativeReport']['path']
            and e['summary']['nativeProcessId'] == ACTUAL['nativeProcessId']
            and e['summary']['wholeActorCounterfactualValidated'] is True,
            'Closed actual R39R3 saved-state/source counterfactual consumer required')
    content, proof = e['contentInventory'], e['projectProof']
    validate_clone(read(checked(ACTUAL['qaClone'])), source_project, project, content, proof)
    require(inventory(project/'Content') == content == inventory(source_project/'Content')
            and protected(project) == proof == protected(source_project), 'Before-stage source/own project bytes changed')
    require(sha(CLOSE_SUPPLEMENT) == CLOSE_SUPPLEMENT_SHA, 'Frozen R18 close supplement changed')
    supplement = read(CLOSE_SUPPLEMENT); proposal = read(CAMERA_PROPOSAL)
    checked(proposal['sourceCoverageAudit'])
    original_path = checked(ACTUAL['sourceOriginalViewpoints'])
    destination = project/'Content/Data/viewpoints.json'
    require(original_path == source_project/'Content/Data/viewpoints.json'
            and destination.read_bytes() == original_path.read_bytes(), 'Actual original saved camera bytes required')
    payload, appended, insertion_proof = append_camera_bytes(original_path.read_bytes(), supplement['view'], proposal['proposedView'])
    historical = read(TEMPLATE_RECEIPT)
    require(historical['schema'] == 'brezi-saved-r38r2-two-camera-data-only-qa-clone-r29-r3'
            and appended['views'][-2:] == historical['views']
            and insertion_proof == historical['originalDataByteInsertionProof']
            and insertion_proof['insertedBytes'] == 1048
            and insertion_proof['insertedBytesSha256'] == '480f82e38d3d2e7b2c8bdbe0f8dc3a7be016f1b25bdc03f5b4bba6ffa247c300',
            'Only the exact historical frozen1,048-byte camera insertion is authorized')
    closure_paths = set(e['additionalClosureFiles']) | {str(ROOT/OWNER), str(TEMPLATE), str(TEMPLATE_RECEIPT), str(CLOSE_SUPPLEMENT), str(CAMERA_PROPOSAL),
        proposal['sourceCoverageAudit']['path'], *(ACTUAL[k]['path'] for k in ('sourceNativeReport', 'sourceNativeProcess',
        'sourceCurrentByteAudit', 'sourceReader', 'sourceReaderReadiness', 'qaClone'))}
    closure_before = {p: sha(p) for p in sorted(closure_paths)}
    destination.write_bytes(payload)
    after = inventory(project/'Content')
    require(set(after) == set(content) and [k for k in content if content[k] != after[k]] == ['Data/viewpoints.json']
            and protected(project) == proof and inventory(source_project/'Content') == content
            and protected(source_project) == proof and all(sha(p) == h for p, h in closure_before.items()),
            'Only two exact new Data views may change; source/map/assets/protected closure must stay exact')
    write_new(after_path, after)
    write_new(validation_path, {'scope': 'CPU_CLOSED_SAVED_R39R3_NATIVE_RECEIPTS_AND_SOURCE_COUNTERFACTUAL',
        'summary': e['summary'], 'closureFiles': closure_before, 'nativeLaunchedByStaging': False})
    write_new(receipt, {'schema': SCHEMA, 'schemaVersion': 1, 'owner': OWNER, 'status': STATUS,
        'sourceNativeOutput': str(SOURCE), 'project': str(project), 'sourceNativeReport': ACTUAL['sourceNativeReport'],
        'sourceNativeProcess': ACTUAL['sourceNativeProcess'], 'sourceCurrentByteAudit': ACTUAL['sourceCurrentByteAudit'],
        'projectClone': ACTUAL['qaClone'], 'sourceReader': ACTUAL['sourceReader'], 'sourceValidation': pin(validation_path),
        'stagingHelper': pin(ROOT/OWNER), 'cameraProposal': pin(CAMERA_PROPOSAL), 'frozenCloseSupplement': pin(CLOSE_SUPPLEMENT),
        'originalTwoCameraContract': pin(TEMPLATE_RECEIPT), 'originalStagingSource': pin(TEMPLATE),
        'sourceOriginalViewpoints': ACTUAL['sourceOriginalViewpoints'], 'viewpointFile': pin(destination),
        'afterContentInventory': pin(after_path), 'views': appended['views'][-2:], 'appendedViewCount': 2,
        'changedContentFiles': ['Data/viewpoints.json'], 'originalContentFileCount': len(content), 'protectedFileCount': len(proof),
        'originalViewsPrefixPreserved': True, 'originalDataByteInsertionProof': insertion_proof,
        'lightingUnchanged': True, 'nativeSourceUnchanged': True,
        'allOriginalProjectFilesIndependentBeforeStage': True, 'protectedOriginalNonDataProjectFiles': SAVED_PROJECT_FILES-1,
        'sceneMapChanged': False, 'nativeExecuted': False,
        'sourceCameraScope': 'FROZEN_R18_CLOSE_PLUS_R37_SOURCE_FRAMING_ONLY_GROUND_VIEW',
        'currentVegetationVisibilityRecomputed': False, 'nativeCameraRuntimeVerified': False,
        'walkingOrCollisionAccepted': False, 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
        'performanceAccepted': False, 'shippingPackageProduced': False})
    print(json.dumps({'receipt': pin(receipt), 'appendedViewCount': 2, 'nativeExecuted': False}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--source', required=True); p.add_argument('--output', required=True)
    a = p.parse_args(); stage(a.source, a.output)
