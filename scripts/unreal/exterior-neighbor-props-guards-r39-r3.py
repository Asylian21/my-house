"""Exact new-local scalar constructor repair over immutable original R39 inputs.

Only a measured new-local zero-bit setter route is admitted. No epsilon,
global zero normalization, old actor setter, original source edit, count-only
geometry identity, or historical producer replay is available here.
"""
import copy
import importlib.util
import math
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighbor-props-guards-r39-r3.py'
R2_GUARD = ROOT/'scripts/unreal/exterior-neighbor-props-guards-r39-r2.py'
R2_GUARD_SHA = 'd4dea091bd55177b8b95da52a25e84dfe445e53f9c219b20ca2cae0d3d1dc00c'
spec = importlib.util.spec_from_file_location('_r39r3_immutable_original_r2_guard', R2_GUARD)
old = importlib.util.module_from_spec(spec); spec.loader.exec_module(old)
for name in ('require', 'read', 'write', 'sha', 'pin', 'checked', 'digest', 'module',
             'c', 'SCHEMA', 'PREFIX', 'TAG', 'MODEL_IDS', 'SOURCE', 'SOURCE_SHA',
             'COUNTS', 'TEXTURE_FIELDS', 'BASE', 'BASE_REPORT', 'BASE_REPORT_SHA',
             'BASE_PROCESS', 'BASE_PROCESS_SHA', 'BASE_AUDIT', 'BASE_AUDIT_SHA',
             'IMAGE_DECISION', 'IMAGE_DECISION_SHA', 'BASE_NATIVE_SHA',
             'inventories', 'validate_base_header', 'validate_placements',
             'complete_materials', 'validate_material_records',
             'expected_counterfactual', 'expected_new_packages', 'validate_content_delta',
             'native_node_translation', 'node_pose_calibration', 'repair_evidence'):
    globals()[name] = getattr(old, name)
require(sha(R2_GUARD) == R2_GUARD_SHA, 'Immutable measured-node R2 guard changed')
NATIVE_OWNER = 'scripts/unreal/exterior-neighbor-props-native-r39-r3.py'
REPAIR_SCHEMA = 'brezi-r39-exact-new-local-zero-constructor-repair-r3'
CANDIDATE = ROOT/'output/unreal/exterior-20261002-r39c'
PROJECT = CANDIDATE/'Project/BreziTwin'
STUDY = ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-native-study-r3'
PLAN = STUDY/'neighbor-props-native-plan-r3.json'
CLONE = CANDIDATE/'neighbor-props-project-clone-r39-r3.json'
CLONE_SHA = 'c98868ea51686a34f68139e3f6cc48c2a4edff9516c92f23973bb8ca60f956b5'
CLONE_SCHEMA = old.CLONE_SCHEMA
CLONE_STATUS = 'verified-byte-identical-independent-apfs-image-selected-r38b-before-whole-original-neighbor-props-exact-local-zero-constructor-repair-r39-r3'
FAILURE = old.CANDIDATE/'neighbor-props-native-report-r2.json'
FAILURE_SHA = '61b45ad51a071c16bfab85ea711ce793e6054bd4e1a67b975eddb0ce03bafc80'
FAILURE_PROCESS = old.CANDIDATE/'neighbor-props-native-r39-r2-process.json'
FAILURE_PROCESS_SHA = 'a32031fd3ac9146a8f11cca428e408f2aedaf818eca7577809e19e9816b80038'
FAILURE_RAW = old.CANDIDATE/'neighbor-props-native-r39-r2.log.json'
FAILURE_RAW_SHA = 'd4876569fecd2be662bd3ea7061858c988b75063063e75dd6abe6cba6ca94993'
FAILURE_AUDIT = old.CANDIDATE/'root-native-failure-byte-audit-r39b-r2.json'
FAILURE_AUDIT_SHA = '60e978186ad471861f5a9b959ce982f4fc90a25b8f2a9e33a07d74050edd78ec'
R2_NATIVE = ROOT/'scripts/unreal/exterior-neighbor-props-native-r39-r2.py'
R2_NATIVE_SHA = 'c3bae8d5023ae0bb90cf1f4a3a56e8c6d8418fbcdee6ba4ea4ecc5c178fa3b71'
FIRST_OBSERVATION = ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-transform-constructor-diagnostic-r1/transform-constructor-report.json'
FIRST_OBSERVATION_SHA = 'b53382a4a2aa91e49a248832a8d35d01f90fb84dd68bafccfa98a772907a105c'
FIRST_LAUNCH = ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-transform-diagnostic-launch-r1'
FIRST_PROCESS = FIRST_LAUNCH/'transform-constructor-diagnostic-r1-process.json'
FIRST_PROCESS_SHA = '92fbd5d3061409433b7c5f39c39dcef5091ca8d589507a4b84e678aa3991065e'
FIRST_RAW = FIRST_LAUNCH/'transform-constructor-diagnostic-r1.log.json'
FIRST_RAW_SHA = '4b5d18e376f5e8bacdb2603a27dc25905a6b9ffca44a74511da926cdda9d6167'
FIRST_AUDIT = FIRST_LAUNCH/'root-readonly-diagnostic-current-byte-audit-r2.json'
FIRST_AUDIT_SHA = '567d86745a2f56427abbcf0c1303117ad3aff436cd0fa8c961a93db9fbe572ce'
COMPOSITION_HELPER = ROOT/'scripts/unreal/exterior-neighbor-props-transform-composition-diagnostic-r2.py'
COMPOSITION_HELPER_SHA = 'f6bf834e31ce2926cc91635dd2f319bfd49a9aab6950a2e2aa7b149f426779aa'
COMPOSITION_REPORT = ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-transform-composition-diagnostic-r2/transform-composition-report.json'
COMPOSITION_REPORT_SHA = 'e289dc82f4f6aaab89c9a9147a483b36ecfecf7f9e39819f0cc0ff5af043f163'
COMPOSITION_LAUNCH = ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-transform-diagnostic-launch-r2-retry-r1'
COMPOSITION_PROCESS = COMPOSITION_LAUNCH/'transform-composition-diagnostic-r2-process.json'
COMPOSITION_PROCESS_SHA = 'd627f59c279a86c0159352275bfa5d16914d8e81613f8e09a5f101f86292ce68'
COMPOSITION_RAW = COMPOSITION_LAUNCH/'transform-composition-diagnostic-r2.log.json'
COMPOSITION_RAW_SHA = 'cf3fea02acd00af1ec50c616b2b4a4d3a4c31b43a530175b5e0b9cf7ce1e959c'
COMPOSITION_AUDIT = COMPOSITION_LAUNCH/'root-readonly-composition-current-byte-audit-r1.json'
COMPOSITION_AUDIT_SHA = 'bdae30ee39165733cfc8048460f3f39abcd6f7b87fdf48068ed517bca4ae41bd'
COMPOSITION_PID = 74650
COMPOSITION_TERMINAL_PIN_COUNT = 29
TRANSFORM_FIELDS = (('translation', 'xyz'), ('rotation', 'xyzw'), ('scale3d', 'xyz'))
PART_IDS = (MODEL_IDS[0]+':0', MODEL_IDS[0]+':1', MODEL_IDS[1]+':0', MODEL_IDS[2]+':0')


def binary_exact(a, b):
    if isinstance(a, bool) or isinstance(b, bool):
        return type(a) is type(b) and a == b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isfinite(a) and math.isfinite(b) and struct.pack('<d', float(a)) == struct.pack('<d', float(b))
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(binary_exact(x, y) for x, y in zip(a, b))
    if isinstance(a, dict) and isinstance(b, dict):
        return set(a) == set(b) and all(binary_exact(a[k], b[k]) for k in a)
    return type(a) is type(b) and a == b


def binary64_record(value):
    require(type(value) in (int, float) and math.isfinite(value), 'Finite real scalar required')
    f = float(value)
    return {'value': f, 'pythonFloatHex': f.hex(), 'binary64LittleEndian': struct.pack('<d', f).hex()}


def validate_binary64_record(record, wanted=None):
    require(isinstance(record, dict) and set(record) == {'value', 'pythonFloatHex', 'binary64LittleEndian'}
            and binary_exact(record, binary64_record(record['value'])), 'Exact binary64 witness required')
    if wanted is not None:
        require(binary_exact(record['value'], wanted), 'Original requested binary64 scalar changed')
    return float(record['value'])


def validate_packed(record, values):
    if isinstance(values, list):
        require(isinstance(record, list) and len(record) == len(values), 'Complete packed numeric array required')
        for a, b in zip(record, values): validate_packed(a, b)
    else:
        validate_binary64_record(record, values)


def validate_transform(value):
    require(isinstance(value, list) and len(value) == 3
            and [len(row) for row in value] == [3, 4, 3], 'Exact Transform numeric shape required')
    for row in value:
        require(isinstance(row, list) and all(type(x) in (int, float) and math.isfinite(x) for x in row),
                'Finite Transform coefficients required')
    return value


def validate_new_local_scalar_event(event, axis, wanted, wrapper_type):
    require(event['axis'] == axis and event['newLocalWrapperType'] == wrapper_type,
            'Exact new-local scalar field required')
    before = validate_binary64_record(event['before'])
    validate_binary64_record(event['requested'], wanted)
    validate_binary64_record(event['after'], wanted)
    need = before == 0. and float(wanted) == 0. and not binary_exact(before, wanted)
    require(type(event['zeroBitMismatchIntermediateUsed']) is bool
            and event['zeroBitMismatchIntermediateUsed'] is need and event['requestedBitsObservedExact'] is True,
            'Only an observed new-local differing zero bit may use the finite intermediate')
    if need:
        validate_binary64_record(event['finiteIntermediateRequested'], 1.)
        validate_binary64_record(event['finiteIntermediateObserved'], 1.)
    else:
        require('finiteIntermediateRequested' not in event and 'finiteIntermediateObserved' not in event,
                'No finite intermediate for a nonzero or already exact field')
    return True


def validate_constructor_receipt(receipt, wanted):
    validate_transform(wanted)
    require(binary_exact(receipt['expectedValues'], wanted)
            and binary_exact(receipt['actualValues'], wanted) and receipt['exactMismatchPaths'] == []
            and receipt['onlyZeroBitMismatchUsesIntermediate'] is True
            and receipt['allOtherValuesWrittenWithoutAdaptation'] is True,
            'Exact unchanged requested constructor values required')
    validate_packed(receipt['binary64Actual'], wanted)
    events = receipt['newLocalScalarEvents']
    require(isinstance(events, list) and len(events) == 3, 'Every new local Transform field must be observed')
    for (field, axes), numbers, observed in zip(TRANSFORM_FIELDS, wanted, events):
        require(observed['property'] == field and len(observed['scalarWrites']) == len(axes),
                'Complete ordered scalar writes required')
        kind = 'Quat' if field == 'rotation' else 'Vector'
        for axis, number, event in zip(axes, numbers, observed['scalarWrites']):
            validate_new_local_scalar_event(event, axis, number, kind)
        after = observed['afterTransformCopyBack']
        require(after['axes'] == list(axes) and after['typeName'] == kind
                and after['nativeStructMemoryPointerOrOwnershipDecoded'] is False
                and binary_exact(after['values'], numbers) and binary_exact(after['editorPropertyValues'], numbers),
                'Exact requested coefficients must survive Transform copy-back')
        validate_packed(after['binary64'], numbers)
    return receipt


def numeric_mismatch_paths(a, b, path=''):
    if type(a) in (int, float) and type(b) in (int, float):
        return [] if binary_exact(a,b) else [{'path':path,'actual':binary64_record(a),'expected':binary64_record(b)}]
    require(isinstance(a,list) and isinstance(b,list) and len(a)==len(b), 'Exact compared numeric shape required')
    return [row for i,(x,y) in enumerate(zip(a,b)) for row in numeric_mismatch_paths(x,y,path+'/'+str(i))]


def prior_failure_and_constructors():
    for path, wanted in ((FAILURE, FAILURE_SHA), (FAILURE_PROCESS, FAILURE_PROCESS_SHA),
            (FAILURE_RAW, FAILURE_RAW_SHA), (FAILURE_AUDIT, FAILURE_AUDIT_SHA),
            (R2_NATIVE, R2_NATIVE_SHA), (FIRST_OBSERVATION, FIRST_OBSERVATION_SHA),
            (FIRST_PROCESS, FIRST_PROCESS_SHA), (FIRST_RAW, FIRST_RAW_SHA), (FIRST_AUDIT, FIRST_AUDIT_SHA)):
        require(sha(path) == wanted, 'Exact closed constructor failure/observation changed: '+str(path))
    failed, terminal, raw, audit = (read(p) for p in (FAILURE, FAILURE_PROCESS, FAILURE_RAW, FAILURE_AUDIT))
    require(failed['schema'] == SCHEMA and failed['schemaVersion'] == 2 and failed['repairSchema'] == old.REPAIR_SCHEMA
            and failed['owner'] == old.NATIVE_OWNER and failed['nativeProcessId'] == 47288
            and failed['status'] == 'failed' and failed['nativeApplied'] is False
            and failed['savedMapUnloadedReloaded'] is False
            and failed['error'] == 'Authored double XYZ/yaw/uniform scale constructor differs',
            'Exact pre-old-mutation authored constructor failure required')
    require(raw['pid'] == 47288 and raw['code'] == 255 and raw['signal'] is None
            and terminal['reportSha256'] == FAILURE_SHA and terminal['sourcePinsUnchangedAfterNative'] is True
            and len(terminal['sourcePinsBeforeNative']) == 1263,
            'Actual unchanged-source failed constructor terminal required')
    require(audit['nativeReport'] == pin(FAILURE) and audit['nativeProcess'] == pin(FAILURE_PROCESS)
            and audit['rawNativeProcess'] == pin(FAILURE_RAW) and audit['nativeProcessId'] == 47288 and audit['exitCode'] == 255
            and audit['candidateOriginal4235FilesExact'] is True and audit['selectedR38bAll4235FilesExact'] is True
            and audit['all1263FrozenSourcePinsExact'] is True and audit['originalMapByteExact'] is True
            and audit['oldNativeActorMutationOrMapSaveReached'] is False
            and len(audit['newOwnedPartialContentFiles']) == 21,
            'Original source/map bytes and complete retained failed history required')
    observed, observed_terminal, observed_raw, observed_audit = (read(p) for p in
        (FIRST_OBSERVATION, FIRST_PROCESS, FIRST_RAW, FIRST_AUDIT))
    require(observed['status'] == 'completed-read-only-six-authored-transform-observations'
            and observed['nativeProcessId'] == 56781 and observed['fullConstructorRowsObserved'] == 6
            and observed['sourceInputsUnchanged'] is True and observed['localValueStructWritesOnly'] is True
            and observed['sceneActorsAssetsOrMapsMutated'] is False and observed['assetsImportedOrSaved'] is False
            and observed['levelLoadedCreatedOrSaved'] is False and observed['epsilonOrToleranceRelaxationProposed'] is False,
            'Exact read-only six-root observation required')
    require(observed_raw['pid'] == 56781 and observed_raw['code'] == 0 and observed_raw['signal'] is None
            and observed_terminal['reportSha256'] == FIRST_OBSERVATION_SHA
            and observed_terminal['sourcePinsUnchangedAfterNative'] is True
            and len(observed_terminal['sourcePinsBeforeNative']) == 14
            and observed_audit['nativeReport'] == pin(FIRST_OBSERVATION)
            and observed_audit['nativeProcess'] == pin(FIRST_PROCESS)
            and observed_audit['rawNativeProcess'] == pin(FIRST_RAW)
            and observed_audit['mapAndProtectedFilesUnchanged'] is True
            and observed_audit['all21PriorOwnedPartialPackageBytesExact'] is True
            and observed_audit['all14DiagnosticSourcePinsExact'] is True,
            'Actually completed original-preserved constructor observation required')
    source_rows = read(SOURCE)['placements']; wanted_ids = {r['id'] for r in source_rows}
    rows = {r['assembly']['id']: r for r in observed['rows']}
    require(len(source_rows) == len(rows) == 6 and set(rows) == wanted_ids,
            'Exact original six assembly IDs required')
    for source in source_rows:
        row = rows[source['id']]; expected = row['expectedOriginalFrozenConstructorValues']; diff = row['exactMismatchAxes']
        wanted = [expected[k] for k in ('translation', 'rotation', 'scale3d')]
        validate_transform(wanted)
        require(binary_exact(row['assembly'], {k:source[k] for k in ('id','modelId','positionCm','yawDegrees','uniformScale')})
                and binary_exact(wanted[0], source['positionCm'])
                and binary_exact(wanted[2], [source['uniformScale']]*3)
                and binary_exact(wanted[1][:2], [0., 0.]) and 'constructorObservationError' not in row
                and len(diff) == 1 and diff[0]['axis'] == 'rotation.y',
                'Original authored inputs and positive-zero policy must remain exact')
        validate_binary64_record(diff[0]['actual'], -0.); validate_binary64_record(diff[0]['expected'], 0.)
        for field in ('translation', 'rotation', 'scale3d'):
            actual = row['actualFinalConstructor'][field]['values']; target = expected[field]
            if field == 'rotation': target = [target[0], -0., *target[2:]]
            require(binary_exact(actual, target), 'Only actual recorded rotation.y sign-bit mismatch allowed')
    parts = {}
    for model, reference in audit['completedImportFullPartIdentityCheckpoints'].items():
        checkpoint = read(checked(reference))
        for part in checkpoint['parts']:
            key = part['sourcePart']
            require(key.startswith(model+':') and key not in parts, 'Unique prior original imported source part required')
            parts[key] = part
    require(set(parts) == set(PART_IDS) and sum(p['triangles'] for p in parts.values()) == 26601,
            'All four full original part identity checkpoints required')
    return rows, parts, audit


def validate_composition_probe(probe, source, first_rows, parts):
    require(probe['schema'] == 'brezi-eight-local-original-prop-compositions-readonly-diagnostic-r39-r2'
            and probe['schemaVersion'] == 2 and probe['status'] == 'completed-read-only-eight-original-part-composition-observations'
            and probe['observationErrors'] == [] and probe['sourceInputsUnchanged'] is True
            and probe['fullRootConstructorsObserved'] == 6 and probe['fullSourceNodesObserved'] == 4
            and probe['composedMembersObserved'] == 8,
            'Actually complete exact local constructor/composition observations required')
    require(probe['newLocalValueStructsAndUnownedMeshlessHismOnly'] is True
            and all(probe[k] is False for k in ('sceneActorsAssetsOrMapsMutated', 'assetsImportedOrSaved',
                'levelLoadedCreatedOrSaved', 'componentRegisteredOrAttached', 'newGeometryAttributeDecodePerformed',
                'sourceGeometryOrPhotoPixelsEdited', 'nativeMemoryOwnershipClaimedFromPythonObjectIds',
                'epsilonOrToleranceRelaxationProposed', 'historicalExactFunctionOrZeroConventionsGloballyChanged',
                'nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted', 'activeOutputPromoted')),
            'New-local read-only observation scope cannot widen')
    placements = source['proposal']['placements']
    require(set(probe['sixRootConstructors']) == set(first_rows)
            and set(probe['sourceNodes']) == set(probe['compositions']) == set(parts),
            'Every original root and full source part must be recorded exactly once')
    for row in placements:
        key = row['id']; expected = first_rows[key]['expectedOriginalFrozenConstructorValues']
        wanted = [expected[k] for k in ('translation', 'rotation', 'scale3d')]
        receipt = validate_constructor_receipt(probe['sixRootConstructors'][key], wanted)
        require(binary_exact(receipt['authoredAssemblyInputs'], {k:row[k] for k in ('id','modelId','positionCm','yawDegrees','uniformScale')}),
                'Original authored root identity/placement changed')
    for key, part in parts.items():
        receipt = validate_constructor_receipt(probe['sourceNodes'][key], part['actualImportedNodePose'])
        require(binary_exact(receipt['actualImportedSourcePart'], part)
                and receipt['createdLocalValueComparedToPriorActuallyImportedPose'] is True,
                'Exact actually imported unchanged original node pose required')
        value = probe['compositions'][key]
        ids = [r['id'] for r in placements if r['modelId'] == key.rsplit(':', 1)[0]]
        require(value['part'] == key and value['assemblyRootIds'] == ids
                and value['actualInstanceCount'] == len(ids) and value['transientInstancesAfterClear'] == 0
                and value['unownedMeshless'] is True and value['registeredOrAttached'] is False
                and value['transientPath'].startswith('/Engine/Transient.'),
                'Exact ordered unowned meshless part observations required')
        fields = ('assemblyInputValues','originalImportedNodeValues','independentRootTransformPointValues',
                  'composedInputValues','recoveredValues','storedMatrices','inputMismatchPaths',
                  'recoveredMismatchPaths','matrixTranslationMismatchPaths')
        require(all(isinstance(value[k], list) and len(value[k]) == len(ids) for k in fields),
                'Complete ordered input/recovered/matrix observation arrays required')
        for i, root_id in enumerate(ids):
            root = probe['sixRootConstructors'][root_id]['actualValues']; node = receipt['actualValues']
            require(binary_exact(value['assemblyInputValues'][i], root)
                    and binary_exact(value['originalImportedNodeValues'][i], node),
                    'Composition inputs must be the exact observed original constructors')
            composed = validate_transform(value['composedInputValues'][i])
            recovered = validate_transform(value['recoveredValues'][i])
            independent = validate_transform(value['independentRootTransformPointValues'][i])
            matrix = value['storedMatrices'][i]
            require(isinstance(matrix, list) and len(matrix) == 4
                    and all(isinstance(row, list) and len(row) == 4 for row in matrix)
                    and all(type(n) in (int,float) and math.isfinite(n) for row in matrix for n in row),
                    'Full finite stored FMatrix observation required')
            require(binary_exact(composed, independent) and binary_exact(independent[1:], root[1:])
                    and value['inputMismatchPaths'][i] == []
                    and value['matrixTranslationMismatchPaths'][i] == []
                    and binary_exact(matrix[3][:3], composed[0]) and binary_exact(matrix[3][3], 1.),
                    'Composition and absolute stored root position must preserve exact inputs')
            # Serialization quaternion/scale differences are observations, not a new epsilon.
            require(binary_exact(value['recoveredMismatchPaths'][i], numeric_mismatch_paths(recovered,composed)),
                    'Serialization difference paths and exact values must describe the actual arrays')
        validate_packed(value['composedInputsBinary64'], value['composedInputValues'])
        validate_packed(value['recoveredValuesBinary64'], value['recoveredValues'])
        validate_packed(value['storedMatricesBinary64'], value['storedMatrices'])
    return {'sixRootConstructors': copy.deepcopy(probe['sixRootConstructors']),
            'sourceNodes': copy.deepcopy(probe['sourceNodes']), 'compositions': copy.deepcopy(probe['compositions']),
            'allOriginalDesiredValuesPreservedBinary64': True,
            'nativeSerializationValuesMeasuredNotRelaxed': True, 'epsilonOrToleranceUsed': False}


def validate_constructor_measurements(measurements, bundle):
    calibration = bundle['constructorCalibration']['compositions']
    require(set(measurements) == set(calibration), 'All four exact calibrated part measurements required')
    for key, expected in calibration.items():
        got = measurements[key]
        require(got['assemblyRootIds'] == expected['assemblyRootIds'], 'Calibrated source root order changed')
        for field in ('assemblyInputValues','originalImportedNodeValues','composedInputValues','recoveredValues','storedMatrices'):
            require(binary_exact(got[field], expected[field]) and digest(got[field]) == digest(expected[field]),
                    'Exact recorded original constructor/native serialization array changed: '+key+'/'+field)
    return True


def constructor_repair_evidence(source=None):
    require(all(v is not None for v in (COMPOSITION_REPORT_SHA, COMPOSITION_PROCESS, COMPOSITION_PROCESS_SHA,
        COMPOSITION_RAW, COMPOSITION_RAW_SHA, COMPOSITION_AUDIT, COMPOSITION_AUDIT_SHA, COMPOSITION_PID,
        COMPOSITION_TERMINAL_PIN_COUNT)), 'Actual closed composition report/terminal/audit remains pending')
    require(sha(COMPOSITION_HELPER) == COMPOSITION_HELPER_SHA, 'Frozen read-only composition route changed')
    for path, wanted in ((COMPOSITION_REPORT, COMPOSITION_REPORT_SHA), (COMPOSITION_PROCESS, COMPOSITION_PROCESS_SHA),
                         (COMPOSITION_RAW, COMPOSITION_RAW_SHA), (COMPOSITION_AUDIT, COMPOSITION_AUDIT_SHA)):
        require(sha(path) == wanted, 'Actual read-only composition evidence changed: '+str(path))
    first, parts, failed_audit = prior_failure_and_constructors()
    probe, terminal, raw, audit = (read(p) for p in (COMPOSITION_REPORT, COMPOSITION_PROCESS, COMPOSITION_RAW, COMPOSITION_AUDIT))
    require(probe['owner'] == COMPOSITION_HELPER.relative_to(ROOT).as_posix()
            and probe['nativeProcessId'] == COMPOSITION_PID and probe['project'] == str(old.PROJECT)
            and raw['pid'] == COMPOSITION_PID and raw['code'] == 0 and raw['signal'] is None
            and terminal['reportSha256'] == COMPOSITION_REPORT_SHA and terminal['sourcePinsUnchangedAfterNative'] is True
            and len(terminal['sourcePinsBeforeNative']) == COMPOSITION_TERMINAL_PIN_COUNT,
            'Actual completed source-exact composition diagnostic terminal required')
    # Actual root audit field contract is bound only after its closed receipt exists.
    require(audit['schema'] == 'brezi-root-readonly-local-composition-current-byte-audit-r1'
            and audit['nativeReport'] == pin(COMPOSITION_REPORT) and audit['nativeProcess'] == pin(COMPOSITION_PROCESS)
            and audit['nativeProcessId'] == COMPOSITION_PID and audit['exitCode'] == 0
            and audit['originalMapAndProtected132Exact'] is True and audit['newContentPackages'] == 0
            and audit['candidateOriginal4235FilesExact'] is True and audit['all29DiagnosticSourcePinsExact'] is True
            and audit['currentContentFiles'] == 4124 and audit['actualSixRootFourNodeEightCompositionsObserved'] is True
            and audit['actualIndependentPointAndMatrixTranslationBitExact'] is True
            and audit['nativeRecoveredQuaternionScaleDifferencesRetainedAsObserved'] is True
            and audit['all21PriorOwnedPartialPackageBytesExact'] is True,
            'Read-only composition must preserve original and prior partial package bytes')
    require(terminal['processFile'] == str(COMPOSITION_RAW) and terminal['processFileSha256'] == COMPOSITION_RAW_SHA
            and sha(terminal['logFile']) == terminal['logSha256']
            and raw['command'] == '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd'
            and raw['args'][0] == str(old.PROJECT/'BreziTwin.uproject')
            and '-run=pythonscript' in raw['args'] and '-nullrhi' in raw['args']
            and '-script='+str(COMPOSITION_HELPER) in raw['args'],
            'Exact own read-only command/log process closure required')
    require(all(sha(path) == wanted for path,wanted in terminal['sourcePinsBeforeNative'].items())
            and all(sha(path) == wanted for path,wanted in probe['inputFiles'].items()),
            'Actual composition terminal and source inputs changed')
    require(all(checked(row) for row in probe['primaryApi'].values()), 'Pinned exact installed primary API required')
    wanted_evidence = {'priorReadOnlyConstructorReport': pin(FIRST_OBSERVATION),
        'priorReadOnlyConstructorProcess': pin(FIRST_PROCESS), 'priorReadOnlyConstructorRaw': pin(FIRST_RAW),
        'priorReadOnlyConstructorCurrentByteAudit': pin(FIRST_AUDIT), 'sourceProposal': pin(SOURCE),
        'failedNativeReport': pin(FAILURE), 'failedNativeProcess': pin(FAILURE_PROCESS),
        'failedRawProcess': pin(FAILURE_RAW), 'rootFailureByteAudit': pin(FAILURE_AUDIT)}
    require(all(probe['evidence'][k] == v for k,v in wanted_evidence.items()),
            'Actual original failure/desired-constructor evidence linkage changed')
    if source is None: source = {'proposal': read(SOURCE)}
    calibration = validate_composition_probe(probe, source, first, parts)
    return {'schema': REPAIR_SCHEMA, 'failedNativeReport': pin(FAILURE), 'failedNativeProcess': pin(FAILURE_PROCESS),
        'failedRawProcess': pin(FAILURE_RAW), 'rootCurrentFailureByteAudit': pin(FAILURE_AUDIT),
        'failedNativeProcessId': 47288, 'failedNativeExitCode': 255,
        'priorReadOnlyConstructorReport': pin(FIRST_OBSERVATION), 'priorReadOnlyConstructorProcess': pin(FIRST_PROCESS),
        'priorReadOnlyConstructorCurrentByteAudit': pin(FIRST_AUDIT),
        'readOnlyCompositionReport': pin(COMPOSITION_REPORT), 'readOnlyCompositionProcess': pin(COMPOSITION_PROCESS),
        'readOnlyCompositionRaw': pin(COMPOSITION_RAW), 'readOnlyCompositionCurrentByteAudit': pin(COMPOSITION_AUDIT),
        'readOnlyCompositionHelper': pin(COMPOSITION_HELPER), 'readOnlyCompositionProcessId': COMPOSITION_PID,
        'recordedCalibrationSha256': digest(calibration), 'sixAuthoredAssemblyRoots': 6, 'eightOriginalPartMembers': 8,
        'originalDesiredPositiveZeroPolicyPreserved': True, 'newLocalConditionalFiniteIntermediateOnly': True,
        'originalMapSaveReached': False, 'sourceGeometryOrPixelsEdited': False,
        'epsilonOrToleranceRelaxationProposed': False, 'globalZeroCanonicalizationUsed': False,
        'partialFailedProjectMapCopied': False, 'nativeFullGeometryAcceptedFromDiagnostic': False}


def expected_binding():
    require(CLONE_SHA is not None, 'Actual fresh original R38b R39c clone remains pending')
    for path, wanted in ((SOURCE,SOURCE_SHA),(BASE_REPORT,BASE_REPORT_SHA),(BASE_PROCESS,BASE_PROCESS_SHA),
                        (BASE_AUDIT,BASE_AUDIT_SHA),(IMAGE_DECISION,IMAGE_DECISION_SHA),(CLONE,CLONE_SHA)):
        require(sha(path) == wanted, 'Exact selected original/source binding changed: '+str(path))
    return {'schema': SCHEMA, 'schemaVersion': 3, 'nativeOwner': NATIVE_OWNER, 'repairSchema': REPAIR_SCHEMA,
        'sourceProposal': pin(SOURCE), 'selectedNativeReport': pin(BASE_REPORT), 'selectedNativeProcess': pin(BASE_PROCESS),
        'selectedCurrentByteAudit': pin(BASE_AUDIT), 'selectedRootImageDecision': pin(IMAGE_DECISION),
        'selectedNativeProcessId': 72504, 'projectClone': pin(CLONE), 'candidateProject': str(PROJECT),
        'scope': {'wholeAssemblyRoots': 6, 'renderingSourceMeshInstances': 8, 'newHismActors': 4,
                  'changedOldActors': 0, 'oldRootsMovedRemovedOrReconstructed': 0},
        'measuredNodePoseRepairEvidence': old.repair_evidence(),
        'exactConstructorRepairEvidence': constructor_repair_evidence(),
        'activeOutputPromoted': False, 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
        'performanceAccepted': False, 'shippingVerified': False}


def require_native_binding(binding):
    expected = expected_binding()
    require(binary_exact(binding, expected) and digest(binding) == digest(expected),
            'Only exact measured new-local constructor/fresh original R38b clone binding allowed')
    return True


def validate_clone_header(clone, binding, content, protected):
    require_native_binding(binding)
    require(clone['schema'] == CLONE_SCHEMA and clone['schemaVersion'] == 3 and clone['status'] == CLONE_STATUS
            and clone['sourceNativeReport'] == binding['selectedNativeReport']
            and clone['sourceNativeProcess'] == binding['selectedNativeProcess']
            and clone['sourceCurrentByteAudit'] == binding['selectedCurrentByteAudit']
            and clone['rootImageBaseSelection'] == binding['selectedRootImageDecision']
            and clone['sourceModelProposal'] == binding['sourceProposal']
            and clone['sourceProject'] == str(BASE/'Project/BreziTwin') and clone['project'] == str(PROJECT)
            and clone['wholeOriginalPropsNativePending'] is True and clone['nativeExecuted'] is False
            and clone['activeOutputPromoted'] is False and clone['sourcePhotoPixelsEdited'] is False,
            'Exact independent original R38b R3 clone provenance required')
    repair = binding['measuredNodePoseRepairEvidence']
    node = clone['measuredNodePoseRepairEvidence']
    require(node['schema'] == 'brezi-actual-original-node-double-centimeter-pose-repair-r39-r2'
            and all(node[k] == repair[k] for k in ('failedNativeReport','failedNativeProcess',
                'rootCurrentFailureByteAudit','observedOriginalNodeCheckpoint','failedNativeProcessId'))
            and binary_exact(node['actualOriginalCoilTranslationCm'],read(old.FAILURE_AUDIT)['actualCoilTranslationCm'])
            and all(node[k] is False for k in ('originalMapSaveReached','sourceGeometryOrPixelsEdited',
                'epsilonOrToleranceRelaxationProposed','partialFailedProjectMapCopied')),
            'Original measured node repair must remain unchanged in the fresh R3 clone')
    exact = binding['exactConstructorRepairEvidence']
    expected = {'schema':'brezi-actual-new-local-zero-bit-constructor-repair-r39-r3',
        'failedNativeReport':exact['failedNativeReport'],'failedNativeProcess':exact['failedNativeProcess'],
        'rootCurrentFailureByteAudit':exact['rootCurrentFailureByteAudit'],
        'actualSixRootConstructorDiagnostic':exact['priorReadOnlyConstructorReport'],
        'actualEightPartCompositionDiagnostic':exact['readOnlyCompositionReport'],
        'actualCompositionDiagnosticProcess':exact['readOnlyCompositionProcess'],
        'rootCurrentReadOnlyCompositionByteAudit':exact['readOnlyCompositionCurrentByteAudit'],
        'failedNativeProcessId':47288,'actualCompositionNativeProcessId':74650,
        'originalMapSaveReached':False,'sourceGeometryOrPixelsEdited':False,'epsilonOrToleranceRelaxationProposed':False,
        'historicalExactOrZeroConventionsGloballyChanged':False,'newLocalZeroBitMismatchIntermediateOnly':True,
        'partialFailedProjectMapCopied':False}
    require(binary_exact(clone['exactLocalZeroConstructorRepairEvidence'],expected)
            and digest(clone['exactLocalZeroConstructorRepairEvidence']) == digest(expected),
            'Fresh clone must bind the actual exact-local repair without adopting failed partial assets')
    require(clone['fileCount'] == len(clone['files']) == 4235 and clone['contentFiles'] == len(content) == 4103
            and clone['protectedFiles'] == len(protected) == 132, 'Exact original4235 clone census required')
    wanted = {'Content/'+k:v for k,v in content.items()}; wanted.update(protected); seen = set()
    for row in clone['files']:
        dst = Path(row['destination']); require(dst.is_relative_to(PROJECT), 'Clone row outside own R39c project')
        rel = dst.relative_to(PROJECT).as_posix()
        require(rel in wanted and rel not in seen and row['source'] == str(BASE/'Project/BreziTwin'/rel)
                and row['independentInodes'] is True and {k:row[k] for k in ('sha256','bytes')} == wanted[rel],
                'Exact source/inventory/independent clone row required')
        seen.add(rel)
    require(seen == set(wanted), 'Complete original clone coverage required')


def validate_clone(bundle, after=False):
    base, binding = bundle['base'], bundle['binding']
    clone = read(checked(binding['projectClone'])); validate_clone_header(clone,binding,base['content'],base['protected'])
    for row in clone['files']:
        src,dst = Path(row['source']),Path(row['destination'])
        require(src.is_file() and dst.is_file() and src.stat().st_ino != dst.stat().st_ino
                and src.stat().st_size == row['bytes'], 'Original independent clone provenance changed')
        if not after: require(dst.stat().st_size == row['bytes'], 'Pristine R39c candidate changed before native')
    content,protected = inventories(PROJECT); original,original_protected = inventories(base['project'])
    require(original == base['content'] and original_protected == protected == base['protected'],
            'Actual original R38b/source/protected132 bytes changed')
    if not after: require(content == base['content'], 'Fresh R39c must be original R38b only before native')
    return content


def load_contract(validate_current=True):
    """Read closed actual sidecars/source; never replay a historical checker/producer."""
    binding = expected_binding()
    r,image,terminal,audit = (read(p) for p in (BASE_REPORT,IMAGE_DECISION,BASE_PROCESS,BASE_AUDIT))
    validate_base_header(r,image,terminal,audit)
    plan,pf,parent,study = (read(checked(r[k])) for k in ('selectedPlan','sourcePreflight','baseNativeReport','sourceStudy'))
    saved,raw,content,protected = (read(checked(r[k])) for k in
        ('savedActorWitness','rawInstanceControlsSaved','afterContentInventory','protectedProjectProof'))
    require(digest(saved) == r['savedActorWitnessSha256'] and len(saved) == 5364
            and len(raw) == 2325 and sum(v['instances'] for v in raw.values()) == 678197,
            'Recorded immutable selected whole actor/raw state required')
    source = c.load_source(); validate_placements(source,saved,parent)
    materials,textures = complete_materials(r)
    require(sha(ROOT/r['owner']) == BASE_NATIVE_SHA, 'Actual selected native reader changed')
    native = module('_r39r3_actual_selected_frozen_reader',ROOT/r['owner'])
    first,parts,_ = prior_failure_and_constructors(); probe = read(checked(binding['exactConstructorRepairEvidence']['readOnlyCompositionReport']))
    calibration = validate_composition_probe(probe,source,first,parts)
    base = {'report':r,'reportPin':pin(BASE_REPORT),'plan':plan,'preflight':pf,'parentReport':parent,'sourceStudy':study,
        'savedWitness':saved,'content':content,'protected':protected,'project':Path(r['project']),
        'process':terminal,'processPin':pin(BASE_PROCESS),'audit':audit,'auditPin':pin(BASE_AUDIT),'native':native,
        'rawControls':raw,'materialRecords':materials,'textureRecords':textures,'readerPacket':{'base':{'report':parent}},
        'savedSourceValidationInheritedFromExactR1Preflight': read(checked(read(old.FAILURE)['sourcePreflight']))['tests']}
    bundle = {'source':source,'base':base,'binding':binding,'nodePoseCalibration':node_pose_calibration(source),
              'constructorCalibration':calibration}
    validate_clone_header(read(checked(binding['projectClone'])),binding,content,protected)
    if validate_current: validate_clone(bundle)
    return bundle
