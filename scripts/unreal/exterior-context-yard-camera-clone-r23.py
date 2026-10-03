"""Root-only APFS project copies for two closed saved-source R23 QA cases.

No Unreal, map or camera mutation. Staging subsequently runs the full frozen
saved-source readers; this copy receipt proves current bytes and independence.
"""
import argparse
import ctypes
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-camera-clone-r23.py'
SCHEMA = 'brezi-saved-r30-r32-matched-context-yard-camera-qa-clone-r23'
CLONE_STATUS = 'verified-byte-identical-independent-apfs-saved-r30-r32-yard-qa-clone-before-viewpoint-stage-r23'
CASES = {
    'baseline': {'source': ROOT/'output/unreal/exterior-20261002-r30b',
        'output': ROOT/'output/unreal/exterior-20261002-r30b-yard-close-baseline-r23',
        'kind': 'saved-r30b-original-shape-garden-yard-baseline',
        'report': 'garden-composition-native-report-r3.json',
        'sha': '67f6b002cd4ad11e0c518815ebf0224e1bb1f932b94361ae91472137dedd776d',
        'process': 'garden-composition-native-r3', 'pid': 89358, 'content': 4078,
        'audit': 'root-native-byte-audit-r30b.json',
        'auditSha': 'fb3798681a7db54ea0c3ed74effaca1068a3bb486ea36c4736e6f88eff5ad7cb'},
    'candidate': {'source': ROOT/'output/unreal/exterior-20261002-r32a',
        'output': ROOT/'output/unreal/exterior-20261002-r32a-yard-close-candidate-r23',
        'kind': 'saved-r32a-resolved-yard-ground-low-detail-candidate',
        'report': 'context-yard-ground-native-report.json',
        'sha': '99b80074fe1309ee951ea662cf42f75ecd6d0a2bc711f0c76cc5d34e18891a19',
        'process': 'context-yard-ground-native', 'pid': 5443, 'content': 4086,
        'audit': 'root-native-byte-audit-r32a.json',
        'auditSha': '5be46410d8abed8630ab5a706fd447dc69b2f4568de6d270b18520fde8978906'}}


def require(value, message):
    if not value:
        raise AssertionError(message)


def read(p):
    return json.loads(Path(p).read_text())


def sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1024*1024), b''):
            h.update(b)
    return h.hexdigest()


def pin(p):
    p = Path(p).resolve()
    return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}


def checked(row):
    p = Path(row['path'])
    require(p.is_absolute() and p.resolve() == p and not p.is_symlink()
            and p.is_file() and pin(p) == row, 'Pinned source file changed')
    return p


def write(p, value):
    p = Path(p)
    require(not p.exists(), 'Owned receipts are immutable')
    p.write_text(json.dumps(value, indent=2, ensure_ascii=False)+'\n')


def inventory(directory):
    directory = Path(directory)
    result = {}
    for p in sorted(directory.rglob('*')):
        require(not p.is_symlink(), 'Project symbolic links forbidden')
        if p.is_file():
            result[p.relative_to(directory).as_posix()] = {k: pin(p)[k] for k in ('sha256', 'bytes')}
    return result


def protected(project):
    result = {'BreziTwin.uproject': {k: pin(project/'BreziTwin.uproject')[k] for k in ('sha256', 'bytes')}}
    for prefix in ('Config', 'Source', 'Binaries'):
        result.update({prefix+'/'+k: v for k, v in inventory(project/prefix).items()})
    return result


def clone(case_name):
    row = CASES[case_name]
    source, output = row['source'], row['output']
    project, own = source/'Project/BreziTwin', output/'Project/BreziTwin'
    require(not output.exists(), 'A fresh owned QA output is required')
    report_path, audit_path = source/row['report'], source/row['audit']
    require(sha(report_path) == row['sha'] and sha(audit_path) == row['auditSha'], 'Actual saved report/current byte audit changed')
    report = read(report_path)
    require(report['output'] == str(source) and report['project'] == str(project)
            and report['nativeProcessId'] == row['pid'] and report['savedMapUnloadedReloaded'] is True
            and report['nativeApplied'] is True, 'Actual saved native source required')
    process_path = source/(row['process']+'.log.json')
    terminal_path = source/(row['process']+'-process.json')
    proc, terminal = read(process_path), read(terminal_path)
    require(proc['pid'] == row['pid'] and proc['code'] == 0 and proc['signal'] is None
            and terminal['reportSha256'] == row['sha'] and terminal['processFile'] == str(process_path)
            and terminal['processFileSha256'] == sha(process_path)
            and terminal['logSha256'] == sha(terminal['logFile'])
            and terminal['sourcePinsUnchangedAfterNative'] is True, 'Actual native exit-zero receipt required')
    content = read(checked(report['afterContentInventory']))
    proof = read(checked(report['protectedProjectProof']))
    require(len(content) == row['content'] and len(proof) == 132
            and inventory(project/'Content') == content and protected(project) == proof,
            'Current saved source Content/protected bytes differ')
    files = {**{'Content/'+k: v for k, v in content.items()}, **proof}
    require(len(files) == row['content']+132, 'Project-only census differs')
    libc = ctypes.CDLL('/usr/lib/libSystem.B.dylib', use_errno=True)
    libc.clonefile.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int]
    libc.clonefile.restype = ctypes.c_int
    receipts = []
    for relative, expected in sorted(files.items()):
        a, b = project/relative, own/relative
        b.parent.mkdir(parents=True, exist_ok=True)
        require(libc.clonefile(str(a).encode(), str(b).encode(), 0) == 0,
                'APFS clone failed errno '+str(ctypes.get_errno()))
        require({k: pin(b)[k] for k in ('sha256', 'bytes')} == expected
                and (a.stat().st_dev, a.stat().st_ino) != (b.stat().st_dev, b.stat().st_ino),
                'Copied bytes/independent inode differ')
        receipts.append({'source': str(a), 'destination': str(b), **expected, 'independentInodes': True})
    require(inventory(own/'Content') == content and protected(own) == proof
            and inventory(project/'Content') == content and protected(project) == proof
            and sha(report_path) == row['sha'] and sha(audit_path) == row['auditSha'],
            'Own/source exact bytes differ after copy')
    receipt = output/'context-yard-camera-project-clone-r23.json'
    write(receipt, {'schema': SCHEMA, 'owner': OWNER, 'status': CLONE_STATUS,
        'sourceKind': row['kind'], 'project': str(own), 'sourceProject': str(project),
        'sourceNativeReport': pin(report_path), 'sourceNativeProcess': pin(terminal_path),
        'sourceCurrentByteAudit': pin(audit_path), 'cloneHelper': pin(ROOT/OWNER),
        'fileCount': len(files), 'contentFiles': len(content), 'protectedFiles': 132,
        'logicalBytes': sum(v['bytes'] for v in files.values()), 'files': receipts,
        'nativeExecuted': False, 'cameraSupplement': None, 'viewpointStagingPending': True,
        'fullSavedSourceReaderValidationPending': True, 'sceneMapChanged': False})
    print(json.dumps({'receipt': pin(receipt), 'files': len(files), 'nativeExecuted': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--case', choices=sorted(CASES), required=True)
    clone(parser.parse_args().case)
