"""Exact-byte two-camera Data copy on one independently owned saved R43b clone.

No Unreal/native invocation or old-stager execution. Uses one authenticated
closed direct-reader result, then checks all clone bytes/inodes and source
closure before/after copying the frozen 26,215-byte camera file unchanged.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-parcel-boundary-camera-copy-stage-r31.py'
SCHEMA = 'brezi-saved-authored-r43r2-boundary-two-camera-exact-data-copy-qa-clone-r31'
STATUS = 'verified-independent-saved-r43r2-exact-two-camera-data-copy-r31'
SOURCE = ROOT/'output/unreal/exterior-20261002-r43b'
QA_OUTPUT = ROOT/'output/unreal/exterior-20261002-r43b-garden-boundary-two-camera-candidate-r31'
READER = ROOT/'scripts/unreal/exterior-editor-source-r31.mjs'
CLONE_SCHEMA = 'brezi-authored-open-boundary-two-camera-independent-qa-project-clone-r31'
CLONE_STATUS = 'verified-byte-identical-independent-apfs-actual-saved-r43b-before-two-camera-data-only-stage-r31'
SAVED_PROJECT_FILES, SAVED_CONTENT_FILES, PROTECTED_FILES = 4271, 4139, 132
DONOR_DATA = {'path': str(ROOT/'output/unreal/exterior-20261002-r39c-neighbor-props-two-camera-candidate-r30/Project/BreziTwin/Content/Data/viewpoints.json'),
    'sha256': '909857062596bcf15951ede6a5d6b8cb60852d7376ac843cde41282f82c206ba', 'bytes': 26215}
DONOR_STAGE = {'path': str(ROOT/'output/unreal/exterior-20261002-r39c-neighbor-props-two-camera-candidate-r30/neighbor-props-camera-stage-receipt-r30.json'),
    'sha256': 'f52d06b5c595e27231ad8bea99e25c4b47d6604286db3b7fb743a8501fdc78a5', 'bytes': 6610}
ORIGINAL_SHA = '25d591b3309a6a0b2297f3eb1fef4d6785379b639662d68049ccc13a12bcd846'
ACTUAL = {
    'sourceNativeReport': {'path': str(SOURCE/'boundary-native-report-r2.json'), 'sha256': '802756b95c06d01351cbdaee7b439ab10728e04f2d884fb971f111e735e9b5d4', 'bytes': 329706},
    'sourceNativeProcess': {'path': str(SOURCE/'garden-boundary-native-r2-process.json'), 'sha256': '70bb0aa0c745cab27f98169dc25f73c17f94f749e0431250e1be6c5fe283dbac', 'bytes': 256940},
    'sourceRawProcess': {'path': str(SOURCE/'garden-boundary-native-r2.log.json'), 'sha256': '7f7e5c89a31682833cb65e59e3138ca5a1d15c2c4379d28d8393b8c000f74e51', 'bytes': 659},
    'sourceCurrentByteAudit': {'path': str(SOURCE/'root-native-success-byte-audit-r43b-r2.json'), 'sha256': 'd4dd77489d5e26e533b4f94cd24a15463c1837171f98ee32ccf5bd07b97eb482', 'bytes': 5411},
    'qaClone': {'path': str(QA_OUTPUT/'garden-boundary-camera-project-clone-r31.json'), 'sha256': '2e8cbc84f10bacac54fc97b3538ea2996e8d629bbcf5012df71498b72472f338', 'bytes': 2371033},
    'sourceOriginalViewpoints': {'path': str(SOURCE/'Project/BreziTwin/Content/Data/viewpoints.json'), 'sha256': ORIGINAL_SHA, 'bytes': 25167},
    'sourceReader': {'path': str(READER), 'sha256': '060aa2ee7c589fe33d9b307e4a79fdbc9b1342026820b1d83e63abde92bedf4c', 'bytes': 20218},
    'sourceReaderReadiness': {'path': str(ROOT/'output/unreal/exterior-context-parcel-boundary-20261002-r43-editor-r31-source-readiness/source-readiness.json'),
        'sha256': 'bafb1073bd0a5be389c4b835d58386f8944f20a58a0db521c490be978c4bcbe8', 'bytes': 5980},
    'sourceConsumer': {'path': str(ROOT/'output/unreal/exterior-context-parcel-boundary-20261002-r43-editor-r31-source-readiness/actual-consumer.json'),
        'sha256': 'c984186b6bebb7c01f997ef9bbc9da5d8078d31735bb10cf1399abba0dd3569e', 'bytes': 2253823},
    'nativeProcessId': 44798, 'rootTerminalSourcePinCount': 1343
}


def require(ok, message):
    if not ok: raise RuntimeError(message)
def read(path): return json.loads(Path(path).read_text())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def bytes_sha(raw): return hashlib.sha256(raw).hexdigest()
def pin(path):
    p = Path(path).resolve();return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}
def checked(row):
    require(type(row) is dict and set(row) == {'path', 'sha256', 'bytes'}, 'Exact regular file pin required')
    p = Path(row['path']);require(p.is_absolute() and p.resolve() == p and p.is_file() and not p.is_symlink()
        and pin(p) == row, 'Immutable consumed pin changed');return p
def write_new(path, value):
    with Path(path).open('x') as f: json.dump(value, f, indent=2, allow_nan=False);f.write('\n')
def require_bound():
    require(all(v is not None for v in ACTUAL.values()), 'Direct R31 reader/readiness/closed consumer not yet bound')
    for k, value in ACTUAL.items():
        if isinstance(value, dict): checked(value)
    require(ACTUAL['sourceReader']['path'] == str(READER), 'Exact new direct reader required')
    r, p, raw, audit = (read(ACTUAL[k]['path']) for k in ('sourceNativeReport', 'sourceNativeProcess', 'sourceRawProcess', 'sourceCurrentByteAudit'))
    require(r['owner'] == 'scripts/unreal/exterior-context-parcel-boundary-native-r43-r2.py'
        and r['schemaVersion'] == 2 and r['status'] == 'verified-saved-three-authored-open-boundary-masters'
        and r['nativeProcessId'] == raw['pid'] == audit['nativeProcessId'] == ACTUAL['nativeProcessId']
        and r['nativeApplied'] is True and r['savedMapUnloadedReloaded'] is True and r['sourceInputsUnchanged'] is True,
        'Actual closed saved R43b required')
    require(raw['code'] == audit['exitCode'] == audit['rootSessionClosedExitCode'] == 0
        and p['reportSha256'] == ACTUAL['sourceNativeReport']['sha256']
        and p['sourcePinsUnchangedAfterNative'] is True
        and len(p['sourcePinsBeforeNative']) == ACTUAL['rootTerminalSourcePinCount']
        and audit['nativeReport'] == ACTUAL['sourceNativeReport'] and audit['nativeProcess'] == ACTUAL['sourceNativeProcess']
        and audit['rawNativeProcess'] == ACTUAL['sourceRawProcess'], 'Native terminal/audit linkage differs')
    return r


def inventory(directory):
    rows = {}
    for p in sorted(Path(directory).rglob('*')):
        require(not p.is_symlink(), 'Project symlink forbidden')
        if p.is_file(): rows[p.relative_to(directory).as_posix()] = {'sha256': sha(p), 'bytes': p.stat().st_size}
    return rows
def protected(project):
    result = {'BreziTwin.uproject': {'sha256': sha(project/'BreziTwin.uproject'), 'bytes': (project/'BreziTwin.uproject').stat().st_size}}
    for folder in ('Config', 'Source', 'Binaries'): result.update({folder+'/'+k: v for k, v in inventory(project/folder).items()})
    return result


def exact_donor_payload(original):
    donor = read(checked(DONOR_STAGE));payload = checked(DONOR_DATA).read_bytes()
    require(donor['schema'] == 'brezi-saved-original-neighbor-props-r39r3-two-camera-data-only-qa-clone-r30'
        and donor['schemaVersion'] == 1 and donor['viewpointFile'] == DONOR_DATA
        and donor['appendedViewCount'] == 2 and donor['changedContentFiles'] == ['Data/viewpoints.json']
        and donor['sceneMapChanged'] is False and donor['nativeExecuted'] is False, 'Exact recorded Data-only donor required')
    proof = donor['originalDataByteInsertionProof'];at, count = proof['insertionOffsetBytes'], proof['insertedBytes']
    require(at == 24500 and count == 1048 and proof['originalFileSha256'] == ORIGINAL_SHA
        and proof['allOriginalDataBytesPreservedOutsideInsertion'] is True
        and bytes_sha(original) == ORIGINAL_SHA and len(original) == 25167
        and payload[:at] == original[:at] and payload[at+count:] == original[at:], 'Complete original Data prefix/suffix differs')
    require(bytes_sha(payload[at:at+count]) == proof['insertedBytesSha256'] == '480f82e38d3d2e7b2c8bdbe0f8dc3a7be016f1b25bdc03f5b4bba6ffa247c300'
        and bytes_sha(original[:at]) == proof['originalPrefixSha256']
        and bytes_sha(original[at:]) == proof['originalSuffixSha256'], 'Exact original recorded 1048-byte insertion differs')
    before, after = json.loads(original), json.loads(payload);views = donor['views']
    require(set(before) == set(after) == {'coordinateSystem', 'defaultView', 'views', 'sun'}
        and after['views'][:-2] == before['views'] and after['views'][-2:] == views
        and all(after[k] == before[k] for k in before if k != 'views'), 'Original view objects/sun/default/coordinate semantics differ')
    require([v['id'] for v in views] == ['exterior-context-yard-572063-close-r18', 'exterior-neighborhood-ground-r38']
        and views[1]['eyeCm'] == [5900, 24700, 165] and views[1]['targetCm'] == [7800, 28500, 185]
        and views[1]['horizontalFovDegrees'] == 72
        and len({v['id'] for v in after['views']}) == len(after['views']), 'Only exact two known views permitted')
    for key in ('cameraProposal', 'frozenCloseSupplement', 'originalTwoCameraContract'): checked(donor[key])
    require(read(donor['frozenCloseSupplement']['path'])['view'] == views[0]
        and read(donor['cameraProposal']['path'])['proposedView'] == views[1]
        and read(donor['originalTwoCameraContract']['path'])['views'] == views, 'Original source camera definitions differ')
    return payload, donor, proof


def validate_clone(clone, source_project, project, content, proof):
    require(clone['schema'] == CLONE_SCHEMA and clone['schemaVersion'] == 1 and clone['status'] == CLONE_STATUS
        and clone['sourceProject'] == str(source_project) and clone['project'] == str(project)
        and clone['sourceNativeReport'] == ACTUAL['sourceNativeReport'] and clone['sourceNativeProcess'] == ACTUAL['sourceNativeProcess']
        and clone['sourceCurrentByteAudit'] == ACTUAL['sourceCurrentByteAudit']
        and clone['nativeExecuted'] is False and clone['viewpointStagingPending'] is True
        and clone['fullSavedSourceReaderValidationPending'] is True and clone['cameraSupplement'] is None,
        'Exact actual independent pending QA clone required')
    expected = {**{'Content/'+k: v for k, v in content.items()}, **proof}
    require(clone['fileCount'] == len(clone['files']) == len(expected) == SAVED_PROJECT_FILES
        and clone['contentFiles'] == len(content) == SAVED_CONTENT_FILES
        and clone['protectedFiles'] == len(proof) == PROTECTED_FILES, 'Whole4271 clone census differs')
    seen = set()
    for row in clone['files']:
        dst = Path(row['destination']);require(dst.is_relative_to(project), 'Own clone path escapes project')
        rel = dst.relative_to(project).as_posix()
        require(rel not in seen and rel in expected and row['source'] == str(source_project/rel)
            and dst == project/rel and row['independentInodes'] is True
            and {k: row[k] for k in ('sha256', 'bytes')} == expected[rel], 'Clone metadata row differs');seen.add(rel)
        a, b = (source_project/rel).stat(), dst.lstat()
        require(dst.is_file() and not dst.is_symlink() and (a.st_dev, a.st_ino) != (b.st_dev, b.st_ino), 'Every Content/protected file must be independently owned')
    require(seen == set(expected), 'Whole clone row coverage differs')


def closed_consumer():
    ready = read(checked(ACTUAL['sourceReaderReadiness']));consumer = read(checked(ACTUAL['sourceConsumer']))
    require(ready['actualConsumer'] == ACTUAL['sourceConsumer'] and ready['actualConsumerExitCode'] == 0
        and ready['reader'] == ACTUAL['sourceReader'], 'One exact final actual reader/consumer readiness required')
    require(consumer['project'] == str(SOURCE/'Project/BreziTwin')
        and consumer['nativeReceiptPath'] == ACTUAL['sourceNativeReport']['path']
        and consumer['summary']['nativeProcessId'] == ACTUAL['nativeProcessId']
        and consumer['summary']['wholeActorCounterfactualValidated'] is True,
        'Closed actual full saved-state consumer required')
    require(set(consumer['additionalClosureFiles']) <= set(consumer['closureFiles'])
        and all(Path(p).is_absolute() and isinstance(s, str) and len(s) == 64 and sha(p) == s
            for p, s in consumer['closureFiles'].items()), 'Complete closed consumer source/current closure changed')
    return consumer


def stage(source, output):
    report = require_bound()
    require(Path(source).resolve() == SOURCE and Path(output).resolve() == QA_OUTPUT, 'Exact actual saved source/owned QA path required')
    source_project, project = SOURCE/'Project/BreziTwin', QA_OUTPUT/'Project/BreziTwin'
    receipt = QA_OUTPUT/'garden-boundary-camera-stage-receipt-r31.json'
    content_path = QA_OUTPUT/'garden-boundary-camera-content-after-r31.json'
    validation_path = QA_OUTPUT/'garden-boundary-camera-source-validation-r31.json'
    require(all(not p.exists() for p in (receipt, content_path, validation_path)), 'All staging outputs must be exclusive new files')
    require(not any('native-report' in p.name or 'overlay-report' in p.name or p.name == 'exterior-import-report.json' for p in QA_OUTPUT.iterdir()), 'No copied native receipts in QA output')
    consumer = closed_consumer();content, proof = consumer['contentInventory'], consumer['projectProof']
    require(content == read(checked(report['afterContentInventory'])) and proof == read(checked(report['protectedProjectProof'])), 'Actual native content/protected inventory binding differs')
    validate_clone(read(checked(ACTUAL['qaClone'])), source_project, project, content, proof)
    require(inventory(project/'Content') == content == inventory(source_project/'Content')
        and protected(project) == proof == protected(source_project), 'Before-stage source and own whole project bytes differ')
    original_path = checked(ACTUAL['sourceOriginalViewpoints']);destination = project/'Content/Data/viewpoints.json'
    require(destination.read_bytes() == original_path.read_bytes(), 'Only pristine source Data accepted')
    payload, donor, insertion = exact_donor_payload(original_path.read_bytes())
    closure = dict(consumer['closureFiles'])
    for row in list(ACTUAL.values())+[DONOR_DATA, DONOR_STAGE]+[donor[k] for k in ('cameraProposal', 'frozenCloseSupplement', 'originalTwoCameraContract')]:
        if isinstance(row, dict): closure[str(checked(row))] = row['sha256']
    closure[str(ROOT/OWNER)] = sha(ROOT/OWNER)
    require(all(sha(p) == s for p, s in closure.items()), 'Exact complete input closure required before copy')
    destination.write_bytes(payload)  # One authorized byte-for-byte Data copy.
    after = inventory(project/'Content')
    require(set(after) == set(content) and sorted(k for k in content if after[k] != content[k]) == ['Data/viewpoints.json']
        and protected(project) == proof and inventory(source_project/'Content') == content and protected(source_project) == proof
        and all(sha(p) == s for p, s in closure.items()), 'Only copied Data bytes may change; source/all4270 others remain exact')
    require(pin(destination)['sha256'] == DONOR_DATA['sha256'] and pin(destination)['bytes'] == DONOR_DATA['bytes'], 'Copied donor bytes differ')
    write_new(content_path, after)
    write_new(validation_path, {'scope': 'AUTHENTICATED_ONE_CLOSED_DIRECT_R31_CONSUMER_PLUS_CURRENT_BYTE_AND_INODE_RECHECK',
        'actualConsumer': ACTUAL['sourceConsumer'], 'sourceReaderReadiness': ACTUAL['sourceReaderReadiness'],
        'summary': consumer['summary'], 'closureFiles': closure, 'directReaderOrCheckerReexecutedByStager': False, 'nativeLaunchedByStaging': False})
    write_new(receipt, {'schema': SCHEMA, 'schemaVersion': 1, 'owner': OWNER, 'status': STATUS,
        'sourceNativeOutput': str(SOURCE), 'project': str(project), 'sourceNativeReport': ACTUAL['sourceNativeReport'],
        'sourceNativeProcess': ACTUAL['sourceNativeProcess'], 'sourceCurrentByteAudit': ACTUAL['sourceCurrentByteAudit'],
        'projectClone': ACTUAL['qaClone'], 'sourceReader': ACTUAL['sourceReader'], 'sourceReaderReadiness': ACTUAL['sourceReaderReadiness'],
        'sourceConsumer': ACTUAL['sourceConsumer'], 'sourceValidation': pin(validation_path), 'stagingHelper': pin(ROOT/OWNER),
        'frozenDonorData': DONOR_DATA, 'originalR30StageReceipt': DONOR_STAGE,
        'cameraProposal': donor['cameraProposal'], 'frozenCloseSupplement': donor['frozenCloseSupplement'],
        'originalTwoCameraContract': donor['originalTwoCameraContract'], 'sourceOriginalViewpoints': ACTUAL['sourceOriginalViewpoints'],
        'viewpointFile': pin(destination), 'afterContentInventory': pin(content_path), 'views': donor['views'],
        'appendedViewCount': 2, 'changedContentFiles': ['Data/viewpoints.json'], 'originalContentFileCount': len(content),
        'protectedFileCount': len(proof), 'originalViewsPrefixPreserved': True, 'originalDataByteInsertionProof': insertion,
        'exactDonorFileCopiedWithoutReserialization': True, 'allOriginalProjectFilesIndependentBeforeStage': True,
        'protectedOriginalNonDataProjectFiles': SAVED_PROJECT_FILES-1, 'lightingUnchanged': True, 'nativeSourceUnchanged': True,
        'directReaderOrCheckerReexecutedByStager': False, 'sceneMapChanged': False, 'nativeExecuted': False,
        'sourceCameraScope': 'FROZEN_R18_CLOSE_PLUS_R37_SOURCE_FRAMING_ONLY_GROUND_VIEW',
        'currentVegetationVisibilityRecomputed': False, 'nativeCameraRuntimeVerified': False, 'walkingOrCollisionAccepted': False,
        'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'shippingPackageProduced': False})
    print(json.dumps({'receipt': pin(receipt), 'appendedViewCount': 2, 'nativeExecuted': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser();parser.add_argument('--source', required=True);parser.add_argument('--output', required=True)
    a = parser.parse_args();stage(a.source, a.output)
