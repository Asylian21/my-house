"""Root-only CPU data staging in two explicitly prepared independent QA clones."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-camera-stage-r23.py'
SCHEMA = 'brezi-saved-r30-r32-matched-context-yard-camera-qa-clone-r23'
CLONE_STATUS = 'verified-byte-identical-independent-apfs-saved-r30-r32-yard-qa-clone-before-viewpoint-stage-r23'
STATUS = 'verified-independent-saved-r30-r32-yard-camera-data-only-qa-clone-r23'
READER = ROOT/'scripts/unreal/exterior-editor-source-r22.mjs'
READER_SHA = '305191a1d44a26219f57d5ec66fb792c1b82e1358210398955f2cbe617ec48a4'
CLONER = ROOT/'scripts/unreal/exterior-context-yard-camera-clone-r23.py'
CLONER_SHA = '606917f12bdfc04b8c8728600163817628f9ddf7b766bc957a9477a96af07c5f'
spec = importlib.util.spec_from_file_location('r23_closed_camera_clone', CLONER)
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
require, read, write, sha, pin = c.require, c.read, c.write, c.sha, c.pin
SOURCE_CASES = {str(row['source']): {**row, 'report': row['source']/row['report'],
    'reportSha': row['sha'], 'process': row['process']+'-process.json'} for row in c.CASES.values()}
SUPPLEMENT = ROOT/'output/unreal/exterior-context-yard-20261002-camera-r18-supplement/context-yard-camera-supplement.json'
SUPPLEMENT_SHA = '768274f6eb2dab6d7bcd0bee2b930feec8e2665bba7dfafb6e929f35b38ebab1'
CAMERA_READER = ROOT/'scripts/unreal/exterior-editor-source-r18.mjs'
CAMERA_READER_SHA = '46035c3982ec8e977873c46c1ff8dfa5a69a10d1aaa2f0d1f216ce89bf87ed2f'
VIEW_ID = 'exterior-context-yard-572063-close-r18'


def validated_supplement():
    require(sha(CLONER) == CLONER_SHA and sha(SUPPLEMENT) == SUPPLEMENT_SHA
            and sha(CAMERA_READER) == CAMERA_READER_SHA, 'Frozen clone/camera-source proof changed')
    supplement = read(SUPPLEMENT)
    for file, digest in supplement['inputFiles'].items():
        require(sha(file) == digest, 'Historical R18 camera input changed')
    original, appended = c.checked(supplement['originalViewpoints']), c.checked(supplement['appendedViewpoints'])
    program = """import fs from 'node:fs/promises';
const m=await import(process.argv[1]);
m.validateYardCameraViews(JSON.parse(await fs.readFile(process.argv[2])),JSON.parse(await fs.readFile(process.argv[3])),JSON.parse(await fs.readFile(process.argv[4])));
console.log('exact frozen R18 camera and old view prefix validated');"""
    subprocess.run(['node','--input-type=module','-e',program,CAMERA_READER.as_uri(),str(original),str(SUPPLEMENT),str(appended)],
                   text=True,capture_output=True,check=True,timeout=30)
    return supplement



def inventory(directory):
    directory = Path(directory)
    result = {}
    for p in sorted(directory.rglob('*')):
        require(not p.is_symlink(), 'QA project symbolic links forbidden')
        if p.is_file():
            result[p.relative_to(directory).as_posix()] = {'sha256': sha(p), 'bytes': p.stat().st_size}
    return result


def protected(project):
    result = {'BreziTwin.uproject': {'sha256': sha(project/'BreziTwin.uproject'),
                                   'bytes': (project/'BreziTwin.uproject').stat().st_size}}
    for prefix in ['Config', 'Source', 'Binaries']:
        result.update({prefix+'/'+k: v for k, v in inventory(project/prefix).items()})
    return result


def actual_source(source):
    source = Path(source).resolve()
    require(str(source) in SOURCE_CASES, 'Only exact saved R30b or R32a can supply this pair')
    row = SOURCE_CASES[str(source)]
    require(sha(READER) == READER_SHA and sha(row['report']) == row['reportSha'], 'Frozen source reader or actual native report changed')
    # Keep the existing full R21/R22 native counterfactual/source/process checks.
    # This is a CPU reader invocation, never an Unreal launch or map operation.
    program = """const {loadEditorSourceEvidence}=await import(process.argv[1]);
const e=await loadEditorSourceEvidence(process.argv[2],{root:process.argv[3]});
console.log(JSON.stringify({mode:e.mode,project:e.project,nativeReceiptPath:e.nativeReceiptPath,
summary:e.summary,contentInventory:e.contentInventory,projectProof:e.projectProof,
additionalClosureFiles:e.additionalClosureFiles}));"""
    run = subprocess.run(['node', '--input-type=module', '-e', program, READER.as_uri(), str(source), str(ROOT)],
                         text=True, capture_output=True, check=True, timeout=360)
    evidence = json.loads(run.stdout)
    require(evidence['project'] == str(source/'Project/BreziTwin') and evidence['nativeReceiptPath'] == str(row['report'])
            and evidence['summary']['nativeProcessId'] == row['pid']
            and len(evidence['contentInventory']) == row['content'] and len(evidence['projectProof']) == 132,
            'Full existing native/source reader evidence differs')
    report = read(row['report'])
    require(read(c.checked(report['afterContentInventory'])) == evidence['contentInventory']
            and read(c.checked(report['protectedProjectProof'])) == evidence['projectProof'], 'Source report inventory/protected proof differs')
    return row, report, evidence


def validate_clone(clone, source, project, content, proof):
    require(clone['schema'] == SCHEMA and clone['status'] == CLONE_STATUS
            and clone['project'] == str(project) and clone['sourceProject'] == str(source/'Project/BreziTwin')
            and clone['sourceNativeReport'] == pin(SOURCE_CASES[str(source)]['report'])
            and clone['nativeExecuted'] is False and clone['viewpointStagingPending'] is True
            and clone['cameraSupplement'] is None and clone['fullSavedSourceReaderValidationPending'] is True
            and clone['cloneHelper'] == pin(CLONER) and clone['sourceKind'] == SOURCE_CASES[str(source)]['kind']
            and clone['sourceNativeProcess'] == pin(source/SOURCE_CASES[str(source)]['process'])
            and clone['sourceCurrentByteAudit'] == pin(source/SOURCE_CASES[str(source)]['audit'])
            and clone['contentFiles'] == len(content)
            and clone['protectedFiles'] == 132 and clone['fileCount'] == len(content)+132,
            'Only the exact pending independent R23 QA clone receipt is accepted')
    expected = {**{'Content/'+k: v for k, v in content.items()}, **proof}
    require(len(clone['files']) == len(expected), 'QA clone witness census differs')
    observed = set()
    for row in clone['files']:
        destination = Path(row['destination'])
        require(destination.is_relative_to(project), 'QA clone witness destination escapes own project')
        relative = destination.relative_to(project).as_posix()
        require(relative in expected and relative not in observed
                and row['source'] == str(source/'Project/BreziTwin'/relative)
                and row['independentInodes'] is True
                and {'sha256': row['sha256'], 'bytes': row['bytes']} == expected[relative],
                'QA clone must cover exact independent original file identities')
        observed.add(relative)
        a, b = Path(row['source']).stat(), destination.stat()
        require((a.st_dev, a.st_ino) != (b.st_dev, b.st_ino), 'Source hardlink is forbidden')
    require(observed == set(expected), 'QA clone original proof is incomplete')


def stage(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    supplement = validated_supplement()
    row, report, evidence = actual_source(source)
    require(output == row['output'] and output != source, 'Unapproved R23 QA output path')
    source_project, project = source/'Project/BreziTwin', output/'Project/BreziTwin'
    receipt = output/'context-yard-camera-stage-receipt-r23.json'
    require(not receipt.exists(), 'Staging receipts are immutable')
    require(not any(p.name.endswith('.json') and ('native-report' in p.name or 'overlay-report' in p.name or p.name == 'exterior-import-report.json')
                    for p in output.iterdir()), 'A QA clone cannot carry a copied native report')
    content, proof = evidence['contentInventory'], evidence['projectProof']
    clone_path = output/'context-yard-camera-project-clone-r23.json'
    clone = read(clone_path)
    validate_clone(clone, source, project, content, proof)
    require(inventory(project/'Content') == content == inventory(source_project/'Content')
            and protected(project) == proof == protected(source_project), 'Actual own/source project bytes differ before stage')
    destination = project/'Content/Data/viewpoints.json'
    original = c.checked(supplement['originalViewpoints'])
    require(destination.read_bytes() == original.read_bytes(), 'Independent QA clone lacks exact original camera prefix')
    closure_before = {p: sha(p) for p in set(supplement['inputFiles']) | set(evidence['additionalClosureFiles']) | {str(ROOT/OWNER), str(clone_path), str(READER), str(CLONER), str(CAMERA_READER), str(SUPPLEMENT), str(original), str(c.checked(supplement['appendedViewpoints']))}}
    destination.write_bytes(c.checked(supplement['appendedViewpoints']).read_bytes())
    after = inventory(project/'Content')
    require(set(after) == set(content) and [k for k in content if content[k] != after[k]] == ['Data/viewpoints.json']
            and after['Data/viewpoints.json'] == {k: supplement['appendedViewpoints'][k] for k in ('sha256', 'bytes')},
            'Only exact appended camera data may change')
    require(protected(project) == proof and inventory(source_project/'Content') == content
            and protected(source_project) == proof, 'Stage changed protected/source project bytes')
    require(all(sha(p) == h for p, h in closure_before.items()), 'Native/source reader closure changed during CPU stage')
    inventory_path = output/'context-yard-camera-content-after-r23.json'
    write(inventory_path, after)
    validation_path = output/'context-yard-camera-source-validation-r23.json'
    write(validation_path, {'scope': 'CPU_EXISTING_SAVED_R21_R22_NATIVE_RECEIPT_AND_SOURCE_CHECKS',
        'sourceNativeOutput': str(source), 'reader': pin(READER), 'summary': evidence['summary'],
        'closureFiles': closure_before, 'nativeLaunchedByStaging': False})
    write(receipt, {'schema': SCHEMA, 'owner': OWNER, 'status': STATUS,
        'sourceKind': row['kind'], 'sourceNativeOutput': str(source), 'sourceNativeReport': pin(row['report']),
        'sourceNativeProcess': pin(source/row['process']), 'project': str(project),
        'projectClone': pin(clone_path), 'cameraSupplement': pin(SUPPLEMENT),
        'stagingHelper': pin(ROOT/OWNER), 'sourceReader': pin(READER), 'historicalCameraReader': pin(CAMERA_READER), 'sourceValidation': pin(validation_path),
        'viewpointFile': pin(destination), 'viewId': VIEW_ID, 'view': supplement['view'],
        'historicalR18SourceCameraAudit': supplement['sourceCameraAudit'],
        'cameraAuditScope': 'FROZEN_R18_ORIGINAL_R27_R28_SOURCE_ONLY_REUSED_CAMERA_NOT_CURRENT_R29_R32_VEGETATION_VISIBILITY',
        'currentR29TreesAndR32LowGrowthVisibilityRecomputed': False, 'afterContentInventory': pin(inventory_path),
        'protectedProjectProof': report['protectedProjectProof'], 'changedContentFiles': ['Data/viewpoints.json'],
        'originalContentFileCount': len(content), 'protectedFileCount': 132,
        'originalViewsPrefixPreserved': True, 'lightingUnchanged': True, 'nativeSourceUnchanged': True,
        'allOriginalProjectFilesIndependentBeforeStage': True, 'sourceValidationExitCode': 0,
        'sceneMapChanged': False, 'nativeExecuted': False, 'nativeCameraRuntimeVerified': False,
        'nativeAppearanceAccepted': False, 'performanceAccepted': False, 'fullPhotorealismAccepted': False,
        'shippingPackageProduced': False})
    print(json.dumps({'receipt': pin(receipt), 'viewId': VIEW_ID, 'sourceKind': row['kind']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    stage(args.source, args.output)
