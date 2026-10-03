"""R46 source-only observed R43 packet; this module never selects a base.

The coordinator must authenticate a new image decision and independent clone
before using this packet for a native trial. No historical producer or native
observer is executed here. Complete native snapshots keep their own schemas.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-burkea-clay-base-packet-r46.py'
BASE = ROOT/'output/unreal/exterior-20261002-r43b'
REPORT = BASE/'boundary-native-report-r2.json'
REPORT_SHA = '802756b95c06d01351cbdaee7b439ab10728e04f2d884fb971f111e735e9b5d4'
PROCESS = BASE/'garden-boundary-native-r2-process.json'
PROCESS_SHA = '70bb0aa0c745cab27f98169dc25f73c17f94f749e0431250e1be6c5fe283dbac'
RAW = BASE/'garden-boundary-native-r2.log.json'
RAW_SHA = '7f7e5c89a31682833cb65e59e3138ca5a1d15c2c4379d28d8393b8c000f74e51'
AUDIT = BASE/'root-native-success-byte-audit-r43b-r2.json'
AUDIT_SHA = 'd4dd77489d5e26e533b4f94cd24a15463c1837171f98ee32ccf5bd07b97eb482'
OBSERVER = ROOT/'scripts/unreal/exterior-context-yard-soft-coherence-native-r38-r2.py'
OBSERVER_SHA = 'e8bd757c0958f4245c4d2c2d7bbd577643b15150333ef5074047bb769f631998'
LEAF_PROPOSAL = ROOT/'output/unreal/exterior-burkea-transmission-20261002-r44-source-proposal/burkea-transmission-source-proposal.json'
LEAF_SHA = '94d8cfcea6ada48380d87e66b2295c361f42e4599c53b23c1ede703ff0a317d7'
ROOF_PROPOSAL = ROOT/'output/unreal/exterior-clay-roof-photo-20261002-r45-unbound-proposal/clay-roof-photo-proposal.json'
ROOF_SHA = 'b1c2d14be64ff121683a358d0d614e9cbfae67a411cfe45a5ae44a1faf8798ea'
FUTURE_BINDING = {'selectedNativeReport': None, 'selectedNativeProcess': None,
    'selectedCurrentByteAudit': None, 'rootImageDecision': None, 'projectClone': None,
    'candidateProject': None, 'nativePlan': None, 'nativeReport': None}
SNAPSHOT_FIELDS = {'asset', 'values', 'size', 'sourceEncoding', 'downscale',
    'alphaCoverageThresholds', 'metadata'}


def require(ok, message):
    if not ok: raise RuntimeError(message)
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
def read(path): return json.loads(Path(path).read_bytes())
def pin(path):
    p = Path(path).resolve();return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}
def checked(row):
    require(type(row) is dict and set(row) == {'path', 'sha256', 'bytes'}, 'Exact authenticated pin required')
    p = Path(row['path']);require(p.is_absolute() and p.resolve() == p and not p.is_symlink()
        and pin(p) == row, 'Immutable source/recorded receipt changed');return p
def fixed(path, expected):
    require(sha(path) == expected, 'Fixed actual R43/source receipt changed');return pin(path)
def module(name, path, expected):
    fixed(path, expected);s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def load_sources():
    result = {}
    for key, path, expected in (('leaf', LEAF_PROPOSAL, LEAF_SHA), ('roof', ROOF_PROPOSAL, ROOF_SHA)):
        row = fixed(path, expected);proposal = read(path)
        require(all(v is None for v in proposal['futureBinding'].values()), 'Frozen source must remain unbound')
        result[key] = {'proposalPin': row, 'proposal': proposal}
    return result


def _metadata_union(*records):
    result = {}
    for record in records:
        require(type(record) is dict and all(isinstance(k, str) and isinstance(v, str)
            for k, v in record.items()), 'Recorded-only metadata must be a string table')
        for key, value in record.items():
            require(key not in result or result[key] == value, 'Conflicting recorded metadata')
            result[key] = value
    return result


def _texture_record(asset, snapshot, extra_metadata, provenance):
    require(snapshot['asset'] == asset and set(snapshot) in
        (SNAPSHOT_FIELDS, SNAPSHOT_FIELDS | {'selectedMetadata'}), 'Only full R43 native texture schema accepted')
    # Never pass size/values24 to a historical pixels/flat24 subset parser.
    full = copy.deepcopy(snapshot);selected = full.pop('selectedMetadata', {})
    require(set(full) == SNAPSHOT_FIELDS and len(full['values']) == 24
        and len(full['size']) == 2 and len(full['alphaCoverageThresholds']) == 4,
        'Complete native visible24 snapshot required')
    metadata = _metadata_union(full['metadata'], selected, extra_metadata)
    return {'snapshot': full, 'metadata': metadata, 'provenance': provenance,
        'metadataExhaustivelyEnumerated': False}


def material_tables(report):
    old_pin = report['originalMaterialWitnessSaved'];old = read(checked(old_pin))
    texture_pin = report['originalTextureWitnessSaved'];textures = read(checked(texture_pin))
    own_pin = report['newMaterialReport'];own = read(checked(own_pin))
    require(len(old) == 69 and len(textures) == 108 and own == report['materialReport']
        and set(own['materials']) == {'wood', 'metal', 'gravel'}, 'Actual R43 69+3 /108+6 records required')
    materials, texture_records = {}, {}
    for asset, row in old.items():
        require(row['asset'] == asset and row['reader'] in ('basic', 'neighbor', 'tree')
            and digest(row['graph']) == row['graphSha256']
            and set(row['usage']) == {'instancedStaticMeshes', 'nanite'}, 'Recorded complete old material differs')
        materials[asset] = {'asset': asset, 'route': row['reader'], 'reader': row['reader'], 'graph': copy.deepcopy(row['graph']),
            'graphSha256': row['graphSha256'], 'aux': copy.deepcopy(row['aux']),
            'recordedUsage': copy.deepcopy(row['usage']), 'metadata': copy.deepcopy(row.get('metadata', {})),
            'provenance': {'receipt': old_pin, 'asset': asset}, 'auxPreviouslyRecorded': True,
            'usagePreviouslyRecorded': True}
    for asset, row in textures.items():
        texture_records[asset] = _texture_record(asset, row, {}, {'receipt': texture_pin, 'asset': asset})
    for role, row in own['materials'].items():
        asset = row['asset'];require(asset not in materials and row['compileErrors'] == []
            and digest(row['graph']) == row['graphSha256'] and row['graph']['flags'] == row['policy'],
            'Exact own R43 full graph/flags required')
        materials[asset] = {'asset': asset, 'route': 'basic', 'reader': 'basic', 'graph': copy.deepcopy(row['graph']),
            'graphSha256': row['graphSha256'], 'aux': None, 'recordedUsage': {},
            'metadata': copy.deepcopy(row['metadata']), 'recordedPolicy': copy.deepcopy(row['policy']),
            'provenance': {'receipt': own_pin, 'role': role}, 'auxPreviouslyRecorded': False,
            'usagePreviouslyRecorded': False}
        for channel, texture in row['textures'].items():
            asset_t = texture['asset'];require(asset_t not in texture_records, 'Distinct own R43 texture required')
            texture_records[asset_t] = _texture_record(asset_t, texture['snapshot'], texture['metadata'],
                {'receipt': own_pin, 'role': role, 'channel': channel})
    routes = {k: sorted(a for a, v in materials.items() if v['route'] == k)
        for k in ('basic', 'neighbor', 'tree')}
    require({k: len(v) for k, v in routes.items()} == {'basic': 60, 'neighbor': 9, 'tree': 3}
        and len(materials) == 72 and len(texture_records) == 114, 'Closed actual 72/114 dispatch required')
    return materials, texture_records, routes


def load_observed_base():
    """Authenticate saved observations, without choosing a future native base."""
    refs = {k: fixed(p, s) for k, p, s in (('report', REPORT, REPORT_SHA), ('process', PROCESS, PROCESS_SHA),
        ('raw', RAW, RAW_SHA), ('audit', AUDIT, AUDIT_SHA))}
    r, process, raw, audit = (read(refs[k]['path']) for k in ('report', 'process', 'raw', 'audit'))
    require(r['owner'] == 'scripts/unreal/exterior-context-parcel-boundary-native-r43-r2.py'
        and r['schema'] == 'brezi-selected-r39c-authored-open-boundary-native-r43' and r['schemaVersion'] == 2
        and r['status'] == 'verified-saved-three-authored-open-boundary-masters'
        and r['nativeApplied'] is True and r['savedMapUnloadedReloaded'] is True
        and r['sourceInputsUnchanged'] is True and raw['pid'] == r['nativeProcessId'] == 44798
        and raw['code'] == 0 and raw['signal'] is None, 'Actual saved R43 native0 required')
    require(process['reportSha256'] == REPORT_SHA and process['processFile'] == str(RAW)
        and process['processFileSha256'] == RAW_SHA and process['sourcePinsUnchangedAfterNative'] is True
        and len(process['sourcePinsBeforeNative']) == 1343, 'Closed actual R43 terminal identity required')
    require(audit['nativeReport'] == refs['report'] and audit['nativeProcess'] == refs['process']
        and audit['rawNativeProcess'] == refs['raw'] and audit['nativeProcessId'] == 44798
        and audit['exitCode'] == audit['rootSessionClosedExitCode'] == 0
        and audit['candidateOriginal4255NonMapFilesExact'] is True and audit['onlyOriginalMapChanged'] is True
        and audit['selectedR39cAll4256FilesExact'] is True and audit['all1343FrozenSourcePinsExact'] is True
        and audit['all1332PreflightSourcePinsExact'] is True, 'Actual current-byte audit scope required')
    for key, value in {'savedActors': 5371, 'fullHismComponents': 2329, 'fullHismInstances': 678205,
        'savedMaterialGraphs': 72, 'savedTextureObjects': 114, 'savedContentFiles': 4139, 'protectedFiles': 132}.items():
        require(r['actualCounts'][key] == audit['actualCounts'][key] == value, 'Actual R43 census changed')
    witness = read(checked(r['savedActorWitness']));raw_controls = read(checked(r['rawInstanceControlsSaved']))
    content = read(checked(r['afterContentInventory']));protected = read(checked(r['protectedProjectProof']))
    require(len(witness) == 5371 and digest(witness) == r['savedActorWitnessSha256']
        and len(raw_controls) == 2329 and sum(v['instances'] for v in raw_controls.values()) == 678205
        and len(content) == 4139 and len(protected) == 132, 'Complete saved scene/raw/current-byte records required')
    mats, textures, routes = material_tables(r)
    r39 = read(checked(r['baseNativeReport']));r38 = read(checked(r39['baseNativeReport']))
    r37 = read(checked(r38['baseNativeReport']))
    require(r['inputFiles'][str(OBSERVER)] == OBSERVER_SHA, 'Exact frozen observer binding required')
    return {'report': r, 'reportPin': refs['report'], 'processPin': refs['process'], 'rawProcessPin': refs['raw'],
        'auditPin': refs['audit'], 'project': Path(r['project']), 'savedWitness': witness,
        'rawControls': raw_controls, 'content': content, 'protected': protected,
        'materialRecords': mats, 'textureRecords': textures, 'materialReaderDispatch': routes,
        'expectedMaterialAssets': sorted(mats), 'expectedTextureAssets': sorted(textures),
        'native': module('_r46_private_frozen_full_observer', OBSERVER, OBSERVER_SHA),
        'readerPacket': {'base': {'report': r37}}, 'observedCounts': copy.deepcopy(r['actualCounts']),
        'selectedForFutureNative': False, 'futureBinding': copy.deepcopy(FUTURE_BINDING)}


if __name__ == '__main__':
    raise RuntimeError('R46 base observer draft has no producer or native entry; future selection remains unbound')
