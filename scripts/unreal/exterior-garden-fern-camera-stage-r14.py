"""Root-only CPU data staging in two explicitly prepared independent QA clones."""
import argparse
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-fern-camera-stage-r14.py'
SCHEMA = 'brezi-purposeful-original-fern-matched-camera-qa-clone-r14'
CLONE_STATUS = 'verified-byte-identical-independent-apfs-purposeful-fern-qa-clone-before-viewpoint-stage-r14'
STATUS = 'verified-independent-purposeful-fern-camera-data-only-qa-clone'
READER = ROOT/'scripts/unreal/exterior-editor-source-r11.mjs'
READER_SHA = '3cc0773b4e4df4b4239aa054cde8ae35c01e4b09abb0e177ad8f0fc4a1ead115'
spec = importlib.util.spec_from_file_location('r14_frozen_purposeful_camera', ROOT/'scripts/unreal/exterior-garden-fern-camera-r14.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)
require, read, write, sha, pin = c.require, c.read, c.write, c.sha, c.pin
SOURCE_CASES = {
    str(c.BASE.parent): {'output': ROOT/'output/unreal/exterior-20261002-r22c-fern-close-baseline-r14',
                        'kind': 'original-r22c-six-donor-garden-baseline', 'report': c.BASE,
                        'reportSha': c.BASE_SHA, 'content': 4049, 'pid': 50344,
                        'process': 'realism-integration-native-r3-process.json'},
    str(c.FERN.parent): {'output': ROOT/'output/unreal/exterior-20261002-r25b-fern-close-candidate-r14',
                        'kind': 'saved-r25b-original-fern-single-root', 'report': c.FERN,
                        'reportSha': c.FERN_SHA, 'content': 4058, 'pid': 60976,
                        'process': 'garden-fern-native-r2-process.json'}}


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
    require(str(source) in SOURCE_CASES, 'Only exact saved R22c or R25b can supply this pair')
    row = SOURCE_CASES[str(source)]
    require(sha(READER) == READER_SHA and sha(row['report']) == row['reportSha'], 'Frozen source reader or actual native report changed')
    # Keep the existing full R10/R11 native counterfactual/source/process checks.
    # This is a CPU reader invocation, never an Unreal launch or map operation.
    program = """const {loadEditorSourceEvidence}=await import(process.argv[1]);
const e=await loadEditorSourceEvidence(process.argv[2],{root:process.argv[3]});
console.log(JSON.stringify({mode:e.mode,project:e.project,nativeReceiptPath:e.nativeReceiptPath,
summary:e.summary,contentInventory:e.contentInventory,projectProof:e.projectProof,
additionalClosureFiles:e.additionalClosureFiles}));"""
    run = subprocess.run(['node', '--input-type=module', '-e', program, READER.as_uri(), str(source), str(ROOT)],
                         text=True, capture_output=True, check=True, timeout=120)
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
            and clone['cameraSupplement'] is None and clone['contentFiles'] == len(content)
            and clone['protectedFiles'] == 132 and clone['fileCount'] == len(content)+132,
            'Only the exact pending independent R14 QA clone receipt is accepted')
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
    supplement = c.validated_supplement()
    row, report, evidence = actual_source(source)
    require(output == row['output'] and output != source, 'Unapproved R14 QA output path')
    source_project, project = source/'Project/BreziTwin', output/'Project/BreziTwin'
    receipt = output/'garden-fern-camera-stage-receipt-r14.json'
    require(not receipt.exists(), 'Staging receipts are immutable')
    require(not any(p.name.endswith('.json') and ('native-report' in p.name or 'overlay-report' in p.name or p.name == 'exterior-import-report.json')
                    for p in output.iterdir()), 'A QA clone cannot carry a copied native report')
    content, proof = evidence['contentInventory'], evidence['projectProof']
    clone_path = output/'garden-fern-camera-project-clone-r14.json'
    clone = read(clone_path)
    validate_clone(clone, source, project, content, proof)
    require(inventory(project/'Content') == content == inventory(source_project/'Content')
            and protected(project) == proof == protected(source_project), 'Actual own/source project bytes differ before stage')
    destination = project/'Content/Data/viewpoints.json'
    original = c.checked(supplement['originalViewpoints'])
    require(destination.read_bytes() == original.read_bytes(), 'Independent QA clone lacks exact original camera prefix')
    closure_before = {p: sha(p) for p in set(supplement['inputFiles']) | set(evidence['additionalClosureFiles']) | {str(READER)}}
    destination.write_bytes(c.checked(supplement['appendedViewpoints']).read_bytes())
    after = inventory(project/'Content')
    require(set(after) == set(content) and [k for k in content if content[k] != after[k]] == ['Data/viewpoints.json']
            and after['Data/viewpoints.json'] == {k: supplement['appendedViewpoints'][k] for k in ('sha256', 'bytes')},
            'Only exact appended camera data may change')
    require(protected(project) == proof and inventory(source_project/'Content') == content
            and protected(source_project) == proof, 'Stage changed protected/source project bytes')
    require(all(sha(p) == h for p, h in closure_before.items()), 'Native/source reader closure changed during CPU stage')
    inventory_path = output/'garden-fern-camera-content-after-r14.json'
    write(inventory_path, after)
    validation_path = output/'garden-fern-camera-source-validation-r14.json'
    write(validation_path, {'scope': 'CPU_EXISTING_SAVED_R10_R11_NATIVE_RECEIPT_AND_SOURCE_CHECKS',
        'sourceNativeOutput': str(source), 'reader': pin(READER), 'summary': evidence['summary'],
        'closureFiles': closure_before, 'nativeLaunchedByStaging': False})
    write(receipt, {'schema': SCHEMA, 'owner': OWNER, 'status': STATUS,
        'sourceKind': row['kind'], 'sourceNativeOutput': str(source), 'sourceNativeReport': pin(row['report']),
        'sourceNativeProcess': pin(source/row['process']), 'project': str(project),
        'projectClone': pin(clone_path), 'cameraSupplement': pin(c.OUTPUT/'garden-fern-camera-supplement.json'),
        'stagingHelper': pin(ROOT/OWNER), 'sourceReader': pin(READER), 'sourceValidation': pin(validation_path),
        'viewpointFile': pin(destination), 'viewId': c.VIEW_ID, 'view': supplement['view'],
        'sourceCameraAudit': supplement['sourceCameraAudit'], 'afterContentInventory': pin(inventory_path),
        'protectedProjectProof': report['protectedProjectProof'], 'changedContentFiles': ['Data/viewpoints.json'],
        'originalContentFileCount': len(content), 'protectedFileCount': 132,
        'originalViewsPrefixPreserved': True, 'lightingUnchanged': True, 'nativeSourceUnchanged': True,
        'allOriginalProjectFilesIndependentBeforeStage': True, 'sourceValidationExitCode': 0,
        'sceneMapChanged': False, 'nativeExecuted': False, 'nativeCameraRuntimeVerified': False,
        'nativeAppearanceAccepted': False, 'performanceAccepted': False, 'fullPhotorealismAccepted': False,
        'shippingPackageProduced': False})
    print(json.dumps({'receipt': pin(receipt), 'viewId': c.VIEW_ID, 'sourceKind': row['kind']}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    stage(args.source, args.output)
