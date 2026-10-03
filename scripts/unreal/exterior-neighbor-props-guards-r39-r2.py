"""R39 R2: exact observed double node pose, original source/geometry unchanged.

The failed R1 remains immutable. No tolerance, producer replay, UObject API,
or unseen native geometry acceptance is introduced by this source adapter.
"""
import copy
import struct
from pathlib import Path
import sys
import importlib.util
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighbor-props-guards-r39-r2.py'
R1_GUARD = ROOT/'scripts/unreal/exterior-neighbor-props-guards-r39.py'
R1_GUARD_SHA = 'd1014718e23b14c70f7772d6a49b29560ccf0c00a04ef47a53256ce1a7df2189'
spec = importlib.util.spec_from_file_location('_r39r2_immutable_original_guard', R1_GUARD)
old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
for name in ('require', 'read', 'write', 'sha', 'pin', 'checked', 'digest', 'module',
             'c', 'SCHEMA', 'PREFIX', 'TAG', 'MODEL_IDS', 'SOURCE', 'SOURCE_SHA',
             'COUNTS', 'TEXTURE_FIELDS', 'BASE', 'BASE_REPORT', 'BASE_REPORT_SHA',
             'BASE_PROCESS', 'BASE_PROCESS_SHA', 'BASE_AUDIT', 'BASE_AUDIT_SHA',
             'IMAGE_DECISION', 'IMAGE_DECISION_SHA', 'BASE_NATIVE_SHA',
             'inventories', 'validate_base_header', 'validate_placements',
             'complete_materials', 'validate_material_records',
             'expected_counterfactual', 'expected_new_packages', 'validate_content_delta'):
    globals()[name] = getattr(old, name)
require(sha(R1_GUARD) == R1_GUARD_SHA, 'Immutable original R39 guard changed')
NATIVE_OWNER = 'scripts/unreal/exterior-neighbor-props-native-r39-r2.py'
REPAIR_SCHEMA = 'brezi-r39-measured-f64-source-node-pose-repair-r2'
CANDIDATE = ROOT/'output/unreal/exterior-20261002-r39b'
PROJECT = CANDIDATE/'Project/BreziTwin'
STUDY = ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-native-study-r2'
PLAN = STUDY/'neighbor-props-native-plan-r2.json'
CLONE = CANDIDATE/'neighbor-props-project-clone-r39-r2.json'
CLONE_SHA = 'cce057e15704ace0b4cb2ed88a4d1a7675d4d77c6bc180f38144a12bb6f32ac7'
CLONE_SCHEMA = old.CLONE_SCHEMA
CLONE_STATUS = 'verified-byte-identical-independent-apfs-image-selected-r38b-before-whole-original-neighbor-props-measured-node-pose-repair-r39-r2'
FAILURE = old.CANDIDATE/'neighbor-props-native-report.json'
FAILURE_SHA = 'cc4ebdbf9d71d469f7f8cb9d098bdb21161cea368109185f04cdfe488d468ece'
FAILURE_PROCESS = old.CANDIDATE/'neighbor-props-native-r39-process.json'
FAILURE_PROCESS_SHA = 'e27d4611c17ac5329b124260b16c569ba8812cf5fe2e15855fa391e21c87baca'
FAILURE_AUDIT = old.CANDIDATE/'root-native-failure-byte-audit-r39a-r1.json'
FAILURE_AUDIT_SHA = 'ae57517a57a6f3eaf50c19c625edde2bebad6c292537e3db233a3a465dc829b3'
CHECKPOINT = old.CANDIDATE/'neighbor-props-checkpoint/garden_hose_wall_mounted_01-objects-before-gates.json'
CHECKPOINT_SHA = 'abf0ce7ba87c028a5be69adc3a3a401728c136535cfbb1494ca48fb46ec92985'
R1_NATIVE = ROOT/'scripts/unreal/exterior-neighbor-props-native-r39.py'
R1_NATIVE_SHA = '20644150bbf8c19baf93816f7e5ef80426b23c3e678fe0b0c11edc00a3ffe4cf'
R1_PLAN_SHA = 'ab6784144b0b041a62c5551245b586b06ce574961478bc0462c668f6811ec640'
R1_PF_SHA = '284093e472dd78aec3e4a35163c06c6530f153af3f7df68f9eb2846a249a6caf'


def binary_equal(a, b):
    return len(a) == len(b) and all(struct.pack('<d', float(x)) == struct.pack('<d', float(y)) for x, y in zip(a, b))


def native_node_translation(part):
    """F64 cm from original JSON/FLOAT32 meters; never round the cm to FLOAT32."""
    proposal = read(SOURCE)
    require(sha(SOURCE) == SOURCE_SHA and part['modelId'] in MODEL_IDS,
            'Exact unchanged original source proposal required')
    nodes = proposal['models'][part['modelId']]['originalNodes']
    index = part['nodeIndex']
    require(type(index) is int and 0 <= index < len(nodes)
            and part['key'] == part['modelId']+':'+str(index)
            and part['nodeName'] == nodes[index]['name'], 'Exact original source-node identity required')
    value = nodes[index].get('translation', [0., 0., 0.])
    require(part['sourceNodeTranslationMeters'] == value
            and part['proposedNativeNodeTranslationCm'] == c.native_vec(value)
            and all(c.f32(x) == x for x in value),
            'Preserve the authored source node and historical F32-cm proposal')
    return [100. * value[0], 100. * value[2], 100. * value[1]]


def repair_evidence():
    for p, wanted in ((FAILURE, FAILURE_SHA), (FAILURE_PROCESS, FAILURE_PROCESS_SHA),
                      (FAILURE_AUDIT, FAILURE_AUDIT_SHA), (CHECKPOINT, CHECKPOINT_SHA),
                      (R1_NATIVE, R1_NATIVE_SHA)):
        require(sha(p) == wanted, 'Immutable measured R1 failure evidence changed: '+str(p))
    failure, process, audit, checkpoint = (read(p) for p in
        (FAILURE, FAILURE_PROCESS, FAILURE_AUDIT, CHECKPOINT))
    require(failure['schema'] == SCHEMA and failure['schemaVersion'] == 1
            and failure['owner'] == old.NATIVE_OWNER and failure['nativeProcessId'] == 29845
            and failure['status'] == 'failed' and failure['nativeApplied'] is False
            and failure['savedMapUnloadedReloaded'] is False
            and failure['error'] == 'Original unbaked source-node pose differs; preserve checkpoint and repair explicitly',
            'Exact failed pose boundary required')
    require(failure['selectedPlan']['sha256'] == R1_PLAN_SHA
            and failure['sourcePreflight']['sha256'] == R1_PF_SHA,
            'Failed run must retain its exact actually executed R1 source contract')
    pf = read(checked(failure['sourcePreflight']))
    require(pf['tests']['testCount'] == 30 and pf['tests']['exitCode'] == 0
            and failure['inputFiles'] == pf['inputFiles'] and len(failure['inputFiles']) == 1236,
            'Prior executed thirty-case proof is inherited, never rerun here')
    checked(pf['tests']['log'])
    raw = read(checked({'path': process['processFile'], 'sha256': process['processFileSha256'],
                        'bytes': Path(process['processFile']).stat().st_size}))
    require(raw['pid'] == 29845 and raw['code'] == 255 and raw['signal'] is None
            and process['reportSha256'] == FAILURE_SHA and process['sourcePinsUnchangedAfterNative'] is True
            and len(process['sourcePinsBeforeNative']) == 1240,
            'Actual failed native process and terminal closure required')
    require(audit['nativeReport'] == pin(FAILURE) and audit['nativeProcess'] == pin(FAILURE_PROCESS)
            and audit['nativeProcessId'] == 29845 and audit['exitCode'] == 255
            and audit['candidateOriginal4235FilesExact'] is True
            and audit['selectedR38bAll4235FilesExact'] is True
            and audit['all1240FrozenSourcePinsExact'] is True and audit['originalMapByteExact'] is True
            and audit['oldNativeActorMutationOrMapSaveReached'] is False
            and len(audit['newOwnedPartialContentFiles']) == 14
            and sum(v['bytes'] for v in audit['newOwnedPartialContentFiles'].values()) == 128146639
            and audit['currentContentFiles'] == 4117 and audit['currentProtectedFiles'] == 132
            and audit['observedOriginalNodeCheckpoint'] == pin(CHECKPOINT)
            and audit['nativeFullGeometryAccepted'] is False,
            'Exact original-preserved/material-only failed state required')
    require(checkpoint['owner'] == old.NATIVE_OWNER and checkpoint['geometryIdentityEstablished'] is False
            and checkpoint['labelsUsedForIdentity'] is False and len(checkpoint['objects']) == 3,
            'Historical pose observation cannot become native geometry acceptance')
    return {'schema': REPAIR_SCHEMA, 'failedNativeReport': pin(FAILURE),
        'failedNativeProcess': pin(FAILURE_PROCESS), 'rootCurrentFailureByteAudit': pin(FAILURE_AUDIT),
        'observedOriginalNodeCheckpoint': pin(CHECKPOINT), 'failedNativeProcessId': 29845,
        'failedNativeExitCode': 255, 'inheritedExecutedR1Preflight': failure['sourcePreflight'],
        'inheritedExecutedR1TestCount': 30, 'originalMapSaveReached': False,
        'sourceGeometryOrPixelsEdited': False, 'epsilonOrToleranceRelaxationProposed': False,
        'partialFailedProjectMapCopied': False, 'nativeFullGeometryAcceptedFromFailure': False}


def node_pose_calibration(source):
    evidence = repair_evidence(); checkpoint = read(checked(evidence['observedOriginalNodeCheckpoint']))
    seen = {row['label']: row for row in checkpoint['objects'] if row['primitiveComponents']}
    require(set(seen) == {'garden_hose_wall_bracket', 'garden_hose'}, 'Exact two measured hose-node observations required')
    result = {}
    for parts in source['parts'].values():
        for part in parts:
            value = native_node_translation(part)
            row = {'part': part['key'], 'sourceNodeTranslationMeters': part['sourceNodeTranslationMeters'],
                'originalProposedF32CentimeterTranslation': part['proposedNativeNodeTranslationCm'],
                'expectedF64CentimeterTranslation': value, 'epsilonOrToleranceUsed': False,
                'originalSourceGeometryAndNodeJsonEdited': False,
                'actualNodePoseObservedInR1Failure': part['modelId'] == MODEL_IDS[0],
                'futureFullOriginalCornerIdentityRequired': True,
                'checkpointLabelsUsedForFutureGeometryIdentity': False}
            if row['actualNodePoseObservedInR1Failure']:
                got = seen[part['nodeName']]
                require(got['class'] == '/Script/Engine.StaticMeshActor' and len(got['components']) == 1
                        and got['components'][0]['class'] == '/Script/Engine.StaticMeshComponent'
                        and got['components'][0]['isActorRoot'] is True
                        and got['components'][0]['owner'] == got['actor']
                        and got['primitiveComponents'] == [got['components'][0]['path']]
                        and binary_equal(got['transform'][0], value)
                        and got['transform'][1:] == [[0., 0., 0., 1.], [1., 1., 1.]],
                        'Actual root rendering node must match the original exact double cm route')
                row.update(observedCheckpoint=pin(CHECKPOINT), observedActor=got['actor'],
                           actualObservedNativeNodePose=got['transform'])
            result[part['key']] = row
    require(len(result) == 4 and result[MODEL_IDS[0]+':1']['expectedF64CentimeterTranslation']
            != result[MODEL_IDS[0]+':1']['originalProposedF32CentimeterTranslation'],
            'The measured nonzero coil route is an explicit source-policy repair')
    audit = read(FAILURE_AUDIT)
    require(binary_equal(audit['actualCoilTranslationCm'], result[MODEL_IDS[0]+':1']['expectedF64CentimeterTranslation'])
            and audit['actualCoilMatchesOriginalJsonDoubleYUpBasisThenCentimeterScale'] is True,
            'Root independently recorded exact original coil calibration required')
    return result


def expected_binding():
    result = old.expected_binding()
    require(sha(CLONE) == CLONE_SHA, 'Exact fresh R39b independent clone changed')
    result.update(schemaVersion=2, nativeOwner=NATIVE_OWNER, repairSchema=REPAIR_SCHEMA,
                  measuredNodePoseRepairEvidence=repair_evidence(), projectClone=pin(CLONE), candidateProject=str(PROJECT))
    return result


def require_native_binding(binding):
    expected = expected_binding()
    require(binding == expected and digest(binding) == digest(expected),
            'Only exact measured-node R2/fresh original R38b clone binding allowed')
    return True


def validate_clone_header(clone, binding, content, protected):
    require_native_binding(binding)
    evidence = clone['measuredNodePoseRepairEvidence']
    require(clone['schema'] == CLONE_SCHEMA and clone['schemaVersion'] == 2 and clone['status'] == CLONE_STATUS
            and clone['sourceNativeReport'] == binding['selectedNativeReport']
            and clone['sourceNativeProcess'] == binding['selectedNativeProcess']
            and clone['sourceCurrentByteAudit'] == binding['selectedCurrentByteAudit']
            and clone['rootImageBaseSelection'] == binding['selectedRootImageDecision']
            and clone['sourceModelProposal'] == binding['sourceProposal']
            and clone['sourceProject'] == str(BASE/'Project/BreziTwin') and clone['project'] == str(PROJECT)
            and clone['wholeOriginalPropsNativePending'] is True and clone['nativeExecuted'] is False
            and clone['activeOutputPromoted'] is False and clone['sourcePhotoPixelsEdited'] is False,
            'Exact independent original R38b R2 clone provenance required')
    repair = binding['measuredNodePoseRepairEvidence']
    require(evidence['schema'] == 'brezi-actual-original-node-double-centimeter-pose-repair-r39-r2'
            and all(evidence[k] == repair[k] for k in ('failedNativeReport', 'failedNativeProcess',
                'rootCurrentFailureByteAudit', 'observedOriginalNodeCheckpoint', 'failedNativeProcessId'))
            and all(evidence[k] is False for k in ('originalMapSaveReached', 'sourceGeometryOrPixelsEdited',
                'epsilonOrToleranceRelaxationProposed', 'partialFailedProjectMapCopied'))
            and evidence['actualOriginalCoilTranslationCm'] == read(FAILURE_AUDIT)['actualCoilTranslationCm'],
            'Fresh clone must authenticate the measured failed boundary without copied partial assets')
    require(clone['fileCount'] == len(clone['files']) == 4235 and clone['contentFiles'] == len(content) == 4103
            and clone['protectedFiles'] == len(protected) == 132, 'Exact original4235 clone census required')
    wanted = {'Content/'+k: v for k, v in content.items()}; wanted.update(protected); seen = set()
    for row in clone['files']:
        dst = Path(row['destination']); require(dst.is_relative_to(PROJECT), 'Clone row outside own R39b project')
        rel = dst.relative_to(PROJECT).as_posix()
        require(rel in wanted and rel not in seen and row['source'] == str(BASE/'Project/BreziTwin'/rel)
                and row['independentInodes'] is True and {k: row[k] for k in ('sha256', 'bytes')} == wanted[rel],
                'Exact source/inventory/independent clone row required')
        seen.add(rel)
    require(seen == set(wanted), 'Complete original clone coverage required')


def validate_clone(bundle, after=False):
    base, binding = bundle['base'], bundle['binding']
    clone = read(checked(binding['projectClone'])); validate_clone_header(clone, binding, base['content'], base['protected'])
    for row in clone['files']:
        src, dst = Path(row['source']), Path(row['destination'])
        require(src.is_file() and dst.is_file() and src.stat().st_ino != dst.stat().st_ino
                and src.stat().st_size == row['bytes'], 'Original independent clone provenance changed')
        if not after: require(dst.stat().st_size == row['bytes'], 'Pristine R39b candidate changed before native')
    content, protected = inventories(PROJECT); original, original_protected = inventories(base['project'])
    require(original == base['content'] and original_protected == protected == base['protected'],
            'Actual original R38b/source/protected132 bytes changed')
    if not after: require(content == base['content'], 'Fresh R39b must be original R38b only before native')
    return content


def load_contract(validate_current=True):
    """Read closed actual sidecars and source only; no historical checker replay."""
    binding = expected_binding()
    r, image, terminal, audit = (read(p) for p in (BASE_REPORT, IMAGE_DECISION, BASE_PROCESS, BASE_AUDIT))
    validate_base_header(r, image, terminal, audit)
    plan, pf, parent, study = (read(checked(r[k])) for k in ('selectedPlan', 'sourcePreflight', 'baseNativeReport', 'sourceStudy'))
    saved, raw, content, protected = (read(checked(r[k])) for k in
        ('savedActorWitness', 'rawInstanceControlsSaved', 'afterContentInventory', 'protectedProjectProof'))
    require(digest(saved) == r['savedActorWitnessSha256'] and len(saved) == 5364
            and len(raw) == 2325 and sum(v['instances'] for v in raw.values()) == 678197,
            'Recorded immutable selected whole actor/raw state required')
    source = c.load_source(); validate_placements(source, saved, parent)
    materials, textures = complete_materials(r)
    require(sha(ROOT/r['owner']) == BASE_NATIVE_SHA, 'Actual selected native reader changed')
    native = module('_r39r2_actual_selected_frozen_reader', ROOT/r['owner'])
    base = {'report': r, 'reportPin': pin(BASE_REPORT), 'plan': plan, 'preflight': pf,
        'parentReport': parent, 'sourceStudy': study, 'savedWitness': saved,
        'content': content, 'protected': protected, 'project': Path(r['project']),
        'process': terminal, 'processPin': pin(BASE_PROCESS), 'audit': audit, 'auditPin': pin(BASE_AUDIT),
        'native': native, 'rawControls': raw, 'materialRecords': materials, 'textureRecords': textures,
        'readerPacket': {'base': {'report': parent}},
        'savedSourceValidationInheritedFromExactR1Preflight': read(checked(read(FAILURE)['sourcePreflight']))['tests']}
    bundle = {'source': source, 'base': base, 'binding': binding, 'nodePoseCalibration': node_pose_calibration(source)}
    validate_clone_header(read(checked(binding['projectClone'])), binding, content, protected)
    if validate_current: validate_clone(bundle)
    return bundle
