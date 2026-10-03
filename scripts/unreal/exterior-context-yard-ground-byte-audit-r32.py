"""CPU-only byte closure of the actual saved R32a; never launches Unreal.

The stored saved/expected witness is checked, not freshly decoded from a map.
The independent Editor source checker owns the semantic source reconstruction.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-ground-byte-audit-r32.py'
OUT = ROOT/'output/unreal/exterior-20261002-r32a'
BASE = ROOT/'output/unreal/exterior-20261002-r30b'
PROJECT = OUT/'Project/BreziTwin'
SCHEMA = 'brezi-context-yard-resolved-ground-and-low-detail-native-r32'
REPORT_SHA = '99b80074fe1309ee951ea662cf42f75ecd6d0a2bc711f0c76cc5d34e18891a19'
BASE_SHA = '67f6b002cd4ad11e0c518815ebf0224e1bb1f932b94361ae91472137dedd776d'
CONFIG = Path('/private/tmp/brezi-r32a-native-config-r1.json')
CONFIG_SHA = '5f4921b034908d78b76a4e6ee2f3d57b1d2a374ba3afa405dbb2f603d670cd7e'
PREFIX = '/Game/Brezi/ContextYardGround20261002R32'
PACKAGES = [PREFIX+'/Geometry/yard-ground-r32/StaticMeshes/'+k+'_LOD0.'+k+'_LOD0'
            for k in ('yard_ground_r32_entry_walk', 'yard_ground_r32_service_court', 'yard_ground_r32_yard_substrate')]
PACKAGES += [PREFIX+'/Materials/M_'+k+'.M_'+k for k in ('yard_gravel_r32', 'yard_substrate_r32')]
PACKAGES += [PREFIX+'/Pipeline/'+k+'.'+k for k in ('Assets', 'Materials', 'Level')]


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink(), 'Regular independent file required: '+str(path))
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def checked(row):
    require(isinstance(row, dict) and set(row) >= {'path', 'sha256', 'bytes'}, 'Typed file pin required')
    require(pin(row['path']) == {k: row[k] for k in ('path', 'sha256', 'bytes')}, 'Pinned file differs: '+str(row['path']))
    return Path(row['path'])


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def inventory(directory):
    directory = Path(directory)
    require(directory.is_dir() and not directory.is_symlink(), 'Independent directory required')
    rows = {}
    for path in sorted(directory.rglob('*')):
        require(not path.is_symlink(), 'Symlink in project inventory')
        if path.is_file():
            rows[path.relative_to(directory).as_posix()] = {'sha256': sha(path), 'bytes': path.stat().st_size}
    return rows


def protected(project):
    rows = {}
    for key in ('Config', 'Source', 'Binaries'):
        rows.update({key+'/'+p: v for p, v in inventory(project/key).items()})
    rows['BreziTwin.uproject'] = {k: v for k, v in pin(project/'BreziTwin.uproject').items() if k != 'path'}
    return rows


def header(report, terminal, raw):
    require(report['schema'] == SCHEMA and report['owner'] == 'scripts/unreal/exterior-context-yard-ground-native-r32.py'
            and report['status'] == 'verified-saved-resolved-context-yard-ground-and-low-detail'
            and report['output'] == str(OUT) and report['project'] == str(PROJECT), 'Closed actual R32a report required')
    require(raw['pid'] == report['nativeProcessId'] == 5443 and raw['code'] == 0 and raw['signal'] is None
            and terminal['sourcePinsUnchangedAfterNative'] is True, 'Actual completed zero-code native process required')
    require(all(report[k] is True for k in ('nativeApplied', 'savedMapUnloadedReloaded', 'sourceInputsUnchanged', 'originalSavedR30bUnchanged')),
            'Actual saved/reloaded/source closure missing')
    require(all(report[k] is False for k in ('nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified', 'packageVerified')),
            'Byte audit cannot upgrade acceptance')
    require(report['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
            and report['setbacksMm'] == {'street': 3000, 'east': 3000}, 'Protected design/placement differs')


def audit():
    rp = OUT/'context-yard-ground-native-report.json'
    tp = OUT/'context-yard-ground-native-process.json'
    require(sha(rp) == REPORT_SHA and sha(CONFIG) == CONFIG_SHA, 'Exact actual report/root config required')
    report, terminal, config = read(rp), read(tp), read(CONFIG)
    require(terminal['reportSha256'] == REPORT_SHA and config['candidate'] == str(OUT)
            and config['stem'] == 'context-yard-ground-native' and config['report'] == rp.name, 'Executed launch binding differs')
    rawp, logp = Path(terminal['processFile']), Path(terminal['logFile'])
    require(rawp == OUT/'context-yard-ground-native.log.json' and logp == OUT/'context-yard-ground-native.log'
            and sha(rawp) == terminal['processFileSha256'] and sha(logp) == terminal['logSha256'], 'Actual process/log pin differs')
    raw = read(rawp)
    header(report, terminal, raw)
    require(str(ROOT/report['owner']) in ''.join(raw['args']) and '-nullrhi' in raw['args'], 'Native helper/CPU-only process differs')
    require(sha(terminal['controller']) == terminal['controllerSha256BeforeNative'] == terminal['controllerSha256AfterNative'], 'Native launch controller changed')
    pf = read(checked(report['sourcePreflight']))
    require(report['selectedPlan'] == config['plan'] | {'bytes': Path(config['plan']['path']).stat().st_size}
            and report['sourcePreflight']['sha256'] == config['readReceipts'][0]['sha256'], 'Exact plan/preflight launch pins differ')
    checked(report['selectedPlan'])
    require(pf['inputFiles'] == report['inputFiles'] and len(pf['inputFiles']) == 528
            and pf['selectedPlan'] == report['selectedPlan'] and pf['testExitCode'] == 0 and pf['nativeExecuted'] is False,
            'Executed528 source preflight differs')
    require(len(terminal['sourcePinsBeforeNative']) == 531
            and all(terminal['sourcePinsBeforeNative'].get(p) == h for p, h in report['inputFiles'].items())
            and terminal['sourcePinsBeforeNative'].get(str(CONFIG)) == CONFIG_SHA, 'Exact531 terminal source closure differs')
    for p, h in terminal['sourcePinsBeforeNative'].items():
        require(sha(p) == h, 'Frozen consumed source differs: '+p)
    require(report['baseNativeReport']['sha256'] == BASE_SHA, 'Only actual R30b parent may be adopted')
    base = read(checked(report['baseNativeReport']))
    require(base['project'] == str(BASE/'Project/BreziTwin'), 'Immediate native parent differs')
    base_content = read(checked(report['baseContentInventory']))
    base_proof = read(checked(report['protectedProjectProof']))
    content = read(checked(report['afterContentInventory']))
    require(report['baseContentInventory'] == base['afterContentInventory'] and report['protectedProjectProof'] == base['protectedProjectProof']
            and len(base_content) == 4078 and len(base_proof) == 132 and len(content) == 4086, 'Actual inventory census/basis differs')
    require(inventory(PROJECT/'Content') == content and protected(PROJECT) == base_proof, 'Current saved candidate bytes differ')
    require(inventory(Path(base['project'])/'Content') == base_content and protected(Path(base['project'])) == base_proof,
            'Current original R30b parent bytes differ')
    clone = read(checked(report['projectClone']))
    require(clone['schema'] == SCHEMA and clone['status'] == 'verified-original-r30b-independent-apfs-r32-clone-before-yard-ground-native'
            and clone['fileCount'] == len(clone['files']) == 4210 and clone['nativeExecuted'] is False
            and clone['selectedNativePlan'] is None and clone['project'] == str(PROJECT)
            and clone['sourceProject'] == base['project'] and clone['nativeBaseReport'] == report['baseNativeReport'], 'Exact original4210 clone provenance differs')
    expected = {'Content/'+k: v for k, v in base_content.items()} | base_proof
    seen, changed = set(), []
    for row in clone['files']:
        a, b = Path(row['source']), Path(row['destination'])
        rel = b.relative_to(PROJECT).as_posix()
        require(rel in expected and rel not in seen and a == Path(base['project'])/rel
                and {k: row[k] for k in ('sha256', 'bytes')} == expected[rel]
                and row['independentInodes'] is True and (a.stat().st_dev, a.stat().st_ino) != (b.stat().st_dev, b.stat().st_ino),
                'Original independent clone row differs')
        seen.add(rel)
        require(a.stat().st_size == row['bytes'] and sha(a) == row['sha256'], 'Original4210 parent bytes changed')
        if b.stat().st_size != row['bytes'] or sha(b) != row['sha256']:
            changed.append(rel)
    require(seen == set(expected) and changed == ['Content/Brezi/Maps/Brezi.umap'], 'Only owned map may change in original candidate')
    packages = sorted(p.split('.')[0].removeprefix('/Game/')+'.uasset' for p in PACKAGES)
    require(report['newPackages'] == PACKAGES and report['assetDelta'] == {'changedOriginalFiles': ['Brezi/Maps/Brezi.umap'],
            'newOwnedPackages': packages, 'originalContentFiles': 4078, 'savedContentFiles': 4086, 'newPackages': 8}
            and set(content) - set(base_content) == set(packages) and set(base_content) <= set(content), 'Closed8 package/map-only delta differs')
    before = read(checked(report['beforeActorWitness']))
    expected_actors = read(checked(report['expectedActorWitness']))
    saved = read(checked(report['savedActorWitness']))
    require(before == read(checked(base['savedActorWitness'])) and len(before) == 5356 and len(saved) == 5360
            and expected_actors == saved and digest(saved) == report['expectedActorWitnessSha256'] == report['savedActorWitnessSha256']
            and digest(before) == report['beforeActorWitnessSha256'], 'Stored full original/declared/saved actor witness differs')
    hisms = [c for a in saved.values() for c in a['components'] if c['class'] == '/Script/Engine.HierarchicalInstancedStaticMeshComponent']
    require(len(hisms) == 2321 and sum(c['instanceCount'] for c in hisms) == 678231, 'Stored full saved HISM census differs')
    require(read(checked(report['originalControlsBefore'])) == read(checked(report['originalControlsSaved'])), 'Stored original raw/control witnesses differ')
    m = report['nativeModuleWitness']
    require(m['source'] == str(Path(base['project'])/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib')
            and m['destination'] == str(PROJECT/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib') and m['independentInodes'] is True
            and pin(m['source'])['sha256'] == pin(m['destination'])['sha256'] == m['sha256'], 'Protected native module byte/inode identity differs')
    return {'schema': 'brezi-context-yard-ground-r32a-byte-audit-root-r1', 'owner': OWNER,
            'status': 'actual-saved-r32a-current-byte-closure-validated', 'recordedAt': datetime.now(timezone.utc).isoformat(),
            'controller': pin(__file__), 'nativeReport': pin(rp), 'terminalProcess': pin(tp), 'rawProcess': pin(rawp), 'nativeLog': pin(logp),
            'rootConfig': pin(CONFIG), 'projectClone': report['projectClone'], 'nativeProcessId': 5443, 'nativeExitCode': 0,
            'currentContentFiles': 4086, 'currentProtectedFiles': 132, 'currentOwnProjectFiles': 4218,
            'all4210OriginalR30bParentFilesCurrentByteExact': True, 'allOriginalCandidateFilesExceptOwnMapByteExact': True,
            'originalCandidateChangedFiles': changed, 'exact8NewOwnedPackages': True, 'newOwnedPackages': packages,
            'savedRecordedActorWitnessMatchesDeclaredExpected': True, 'freshNativeActorDecodePerformedByByteAudit': False,
            'savedActorCount': 5360, 'savedHismComponents': 2321, 'savedHismInstances': 678231,
            'recordedOriginalControlsBeforeAndSavedExact': True, 'frozenSourcePinCount': 531, 'allFrozenPinsCurrentExact': True,
            'nativeApplied': True, 'nativeAppearanceAccepted': False, 'shippingVerified': False, 'packageVerified': False,
            'performanceAccepted': False, 'fullPhotorealismAccepted': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT/'root-native-byte-audit-r32a.json')
    args = parser.parse_args()
    require(not args.output.exists(), 'New audit output must be fresh')
    receipt = audit()
    with args.output.open('x') as f:
        json.dump(receipt, f, indent=2, allow_nan=False)
        f.write('\n')
    print(json.dumps(pin(args.output)), flush=True)


if __name__ == '__main__':
    main()
