"""CPU Data-only frozen R18 camera append on one authorized independent R37 QA clone.

No scene/map/asset/lighting/native operation. The actual successful native report
stays external. Original current vegetation visibility is not recomputed here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-yard-camera-stage-r28.py'
SCHEMA = 'brezi-saved-r37b-yard-camera-qa-clone-r28'
CLONE_STATUS = 'verified-byte-identical-independent-apfs-saved-r37b-yard-qa-clone-before-viewpoint-stage-r28'
STATUS = 'verified-independent-saved-r37b-yard-camera-data-only-qa-clone-r28'
SOURCE = ROOT/'output/unreal/exterior-20261002-r37b'
OUTPUT = ROOT/'output/unreal/exterior-20261002-r37b-yard-close-candidate-r28'
REPORT_SHA = 'f589c0d813ccfc35eba928a91a4545e03b159622fffa7ae2ba247545053c4532'
AUDIT_SHA = '5e2b2e057436049d4eabd34f3420d94b351c519094bfaed44cb10ddf24a56bf2'
CLONE_SHA = 'f07a32ebb18ad367fb3d9c8de76dc1e72331b4bff3785b7ca7a28d6c0a2d2bd5'
READER_SHA = '71d2a5d20b60f2be5e600617c51c4c6a6e823f7437fcd64e8379c01295d29123'
NATIVE_PID = 54956
REPORT_FILENAME = 'garden-yard-integration-native-report-r2.json'
PROCESS_FILENAME = 'garden-yard-integration-native-r2-process.json'
AUDIT_FILENAME = 'root-native-success-byte-audit-r37b-r2.json'
READER = ROOT/'scripts/unreal/exterior-editor-source-r28.mjs'
CAMERA_READER = ROOT/'scripts/unreal/exterior-editor-source-r18.mjs'
CAMERA_READER_SHA = '46035c3982ec8e977873c46c1ff8dfa5a69a10d1aaa2f0d1f216ce89bf87ed2f'
SUPPLEMENT = ROOT/'output/unreal/exterior-context-yard-20261002-camera-r18-supplement/context-yard-camera-supplement.json'
SUPPLEMENT_SHA = '768274f6eb2dab6d7bcd0bee2b930feec8e2665bba7dfafb6e929f35b38ebab1'
VIEW_ID = 'exterior-context-yard-572063-close-r18'


def require(ok, message):
    if not ok: raise RuntimeError(message)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def pin(path):
    p = Path(path).resolve()
    return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}
def checked(row):
    p = Path(row['path'])
    require(p.is_absolute() and p.resolve() == p and p.is_file() and not p.is_symlink()
            and pin(p) == row, 'Exact immutable regular-file pin required')
    return p
def write(path, row):
    with Path(path).open('x') as f: json.dump(row, f, indent=2, allow_nan=False);f.write('\n')


def inventory(directory):
    directory = Path(directory)
    result = {}
    for p in sorted(directory.rglob('*')):
        require(not p.is_symlink(), 'QA project symlinks forbidden')
        if p.is_file(): result[p.relative_to(directory).as_posix()] = {k: pin(p)[k] for k in ('sha256','bytes')}
    return result
def protected(project):
    p = project/'BreziTwin.uproject'
    result = {'BreziTwin.uproject': {k: pin(p)[k] for k in ('sha256','bytes')}}
    for folder in ('Config','Source','Binaries'):
        result.update({folder+'/'+k:v for k,v in inventory(project/folder).items()})
    return result


def supplement():
    require(sha(SUPPLEMENT) == SUPPLEMENT_SHA and sha(CAMERA_READER) == CAMERA_READER_SHA,
            'Frozen exact R18 camera proof differs')
    s = read(SUPPLEMENT)
    for file, digest in s['inputFiles'].items(): require(sha(file) == digest, 'Historical camera source changed')
    original, appended = checked(s['originalViewpoints']), checked(s['appendedViewpoints'])
    code = """import fs from 'node:fs/promises';
const m=await import(process.argv[1]);m.validateYardCameraViews(JSON.parse(await fs.readFile(process.argv[2])),JSON.parse(await fs.readFile(process.argv[3])),JSON.parse(await fs.readFile(process.argv[4])));"""
    subprocess.run(['node','--input-type=module','-e',code,CAMERA_READER.as_uri(),str(original),str(SUPPLEMENT),str(appended)],
                   check=True, text=True, capture_output=True, timeout=30)
    return s


def validate_clone(clone, project, content, proof):
    require(clone['schema'] == SCHEMA and clone['schemaVersion'] == 1 and clone['status'] == CLONE_STATUS
            and clone['project'] == str(project) and clone['sourceProject'] == str(SOURCE/'Project/BreziTwin')
            and clone['sourceNativeReport'] == pin(SOURCE/REPORT_FILENAME)
            and clone['sourceNativeProcess'] == pin(SOURCE/PROCESS_FILENAME)
            and clone['sourceCurrentByteAudit'] == pin(SOURCE/AUDIT_FILENAME)
            and clone['fileCount'] == len(clone['files']) == 4232 and clone['contentFiles'] == len(content) == 4100
            and clone['protectedFiles'] == len(proof) == 132 and clone['nativeExecuted'] is False
            and clone['viewpointStagingPending'] is clone['fullSavedSourceReaderValidationPending'] is True
            and clone['cameraSupplement'] is None, 'Only exact pending independent R37R2 QA clone accepted')
    checked(clone['byteValidationHelper']);checked(clone['rootController'])
    expected = {**{'Content/'+k:v for k,v in content.items()}, **proof}
    seen = set()
    for row in clone['files']:
        destination = Path(row['destination'])
        require(destination.is_relative_to(project), 'QA clone destination escapes owned project')
        relative = destination.relative_to(project).as_posix()
        require(relative in expected and relative not in seen and row['source'] == str(SOURCE/'Project/BreziTwin'/relative)
                and destination == project/relative and row['independentInodes'] is True
                and {'sha256':row['sha256'],'bytes':row['bytes']} == expected[relative], 'QA clone identity/bytes differ')
        seen.add(relative)
        a,b = Path(row['source']).stat(), destination.lstat()
        require(destination.is_file() and not destination.is_symlink() and (a.st_dev,a.st_ino) != (b.st_dev,b.st_ino),
                'Every original file including132 protected files must be independently owned')
    require(seen == set(expected), 'Complete4232 QA clone file proof required')


def stage(source, output):
    require(all(isinstance(v,str) and len(v)==64 for v in (REPORT_SHA,AUDIT_SHA,CLONE_SHA,READER_SHA)) and isinstance(NATIVE_PID,int) and NATIVE_PID>0
            and all(isinstance(v,str) and v.endswith('.json') for v in (REPORT_FILENAME,PROCESS_FILENAME,AUDIT_FILENAME)),
            'Actual successful repaired R37/native-reader/independent-close-clone pins are pending')
    require(sha(READER)==READER_SHA,'Frozen saved-source reader changed')
    require(Path(source).resolve() == SOURCE and Path(output).resolve() == OUTPUT, 'Only the explicitly authorized savedR37R2 QA clone accepted')
    project = OUTPUT/'Project/BreziTwin';source_project = SOURCE/'Project/BreziTwin'
    receipt = OUTPUT/'garden-yard-camera-stage-receipt-r28.json'
    require(not receipt.exists(), 'Staging receipt must be new and immutable')
    require(not any('native-report' in p.name or 'overlay-report' in p.name or p.name == 'exterior-import-report.json'
                    for p in OUTPUT.iterdir()), 'QA clone cannot contain copied native receipts')
    require(sha(SOURCE/REPORT_FILENAME) == REPORT_SHA
            and sha(SOURCE/AUDIT_FILENAME) == AUDIT_SHA, 'Actual saved source/audit changed')
    s = supplement()
    # This performs the new full closed source/counterfactual checker once.
    code = """const m=await import(process.argv[1]);const e=await m.loadEditorSourceEvidence(process.argv[2],{root:process.argv[3]});
console.log(JSON.stringify({project:e.project,nativeReceiptPath:e.nativeReceiptPath,summary:e.summary,contentInventory:e.contentInventory,projectProof:e.projectProof,additionalClosureFiles:e.additionalClosureFiles}));"""
    run = subprocess.run(['node','--input-type=module','-e',code,READER.as_uri(),str(SOURCE),str(ROOT)],
                         text=True,capture_output=True,check=True,timeout=480)
    e = json.loads(run.stdout)
    require(e['project'] == str(source_project) and e['nativeReceiptPath'] == str(SOURCE/REPORT_FILENAME)
            and e['summary']['nativeProcessId'] == NATIVE_PID and e['summary']['wholeActorCounterfactualValidated'] is True,
            'Actual successful closed R37R2 source validation required')
    content, proof = e['contentInventory'], e['projectProof']
    clone_path = OUTPUT/'garden-yard-camera-project-clone-r28.json'
    require(sha(clone_path) == CLONE_SHA, 'Actual root-owned QA clone receipt changed')
    validate_clone(read(clone_path), project, content, proof)
    require(inventory(project/'Content') == content == inventory(source_project/'Content')
            and protected(project) == proof == protected(source_project), 'Current source/own bytes differ before Data stage')
    destination = project/'Content/Data/viewpoints.json'
    require(destination.read_bytes() == checked(s['originalViewpoints']).read_bytes(), 'Exact frozen original camera prefix required')
    closure_paths = set(e['additionalClosureFiles']) | set(s['inputFiles']) | {str(ROOT/OWNER),str(READER),str(CAMERA_READER),str(SUPPLEMENT),str(clone_path),s['originalViewpoints']['path'],s['appendedViewpoints']['path']}
    closure_before = {p:sha(p) for p in sorted(closure_paths)}
    destination.write_bytes(checked(s['appendedViewpoints']).read_bytes())
    after = inventory(project/'Content')
    require(set(after) == set(content) and [k for k in content if content[k] != after[k]] == ['Data/viewpoints.json']
            and after['Data/viewpoints.json'] == {k:s['appendedViewpoints'][k] for k in ('sha256','bytes')}, 'Only exact frozen camera append may change')
    require(protected(project) == proof and inventory(source_project/'Content') == content and protected(source_project) == proof
            and all(sha(p) == h for p,h in closure_before.items()), 'Stage changed original/protected/source closure')
    content_path = OUTPUT/'garden-yard-camera-content-after-r28.json';write(content_path,after)
    validation_path = OUTPUT/'garden-yard-camera-source-validation-r28.json'
    write(validation_path,{'scope':'CPU_SAVED_R37R2_NATIVE_RECEIPTS_AND_SOURCE_COUNTERFACTUAL','sourceNativeOutput':str(SOURCE),
        'reader':pin(READER),'summary':e['summary'],'closureFiles':closure_before,'nativeLaunchedByStaging':False})
    report = read(SOURCE/REPORT_FILENAME)
    write(receipt,{'schema':SCHEMA,'schemaVersion':1,'owner':OWNER,'status':STATUS,'sourceNativeOutput':str(SOURCE),
        'sourceNativeReport':pin(SOURCE/REPORT_FILENAME),
        'sourceNativeProcess':pin(SOURCE/PROCESS_FILENAME),
        'sourceCurrentByteAudit':pin(SOURCE/AUDIT_FILENAME),'project':str(project),
        'projectClone':pin(clone_path),'cameraSupplement':pin(SUPPLEMENT),'sourceReader':pin(READER),'stagingHelper':pin(ROOT/OWNER),
        'historicalCameraReader':pin(CAMERA_READER),'sourceValidation':pin(validation_path),'viewpointFile':pin(destination),
        'viewId':VIEW_ID,'view':s['view'],'historicalR18SourceCameraAudit':s['sourceCameraAudit'],
        'cameraAuditScope':'FROZEN_R18_SOURCE_CAMERA_REUSED_NOT_CURRENT_R37_VEGETATION_VISIBILITY',
        'currentVegetationVisibilityRecomputed':False,'afterContentInventory':pin(content_path),'protectedProjectProof':report['protectedProjectProof'],
        'changedContentFiles':['Data/viewpoints.json'],'originalContentFileCount':4100,'protectedFileCount':132,
        'originalViewsPrefixPreserved':True,'lightingUnchanged':True,'nativeSourceUnchanged':True,
        'allOriginalProjectFilesIndependentBeforeStage':True,'sourceValidationExitCode':0,'sceneMapChanged':False,
        'nativeExecuted':False,'nativeCameraRuntimeVerified':False,'nativeAppearanceAccepted':False,
        'performanceAccepted':False,'fullPhotorealismAccepted':False,'shippingPackageProduced':False})
    print(json.dumps({'receipt':pin(receipt),'viewId':VIEW_ID,'nativeExecuted':False},indent=2))


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();stage(a.source,a.output)
