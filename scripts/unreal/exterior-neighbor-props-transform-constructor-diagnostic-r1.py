"""Six new local value-struct observations; no actor, asset, import or map API.

This diagnostic records the strict failed constructor before proposing any repair.
Its completed status is an observation receipt, never a props/native acceptance.
"""
import json
import math
import os
from pathlib import Path
import struct
import hashlib
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighbor-props-transform-constructor-diagnostic-r1.py'
OUTPUT = ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-transform-constructor-diagnostic-r1'
PROJECT = ROOT/'output/unreal/exterior-20261002-r39b/Project/BreziTwin'
REPORT = OUTPUT/'transform-constructor-report.json'
SOURCE = ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-source-study/neighbor-props-source-proposal.json'
SOURCE_SHA = 'a408e466ff67579b9ff6cc5c1534d27ca71f1d44dba83b8768f0137efef8f67a'
FAILED = PROJECT.parents[1]/'neighbor-props-native-report-r2.json'
FAILED_SHA = '61b45ad51a071c16bfab85ea711ce793e6054bd4e1a67b975eddb0ce03bafc80'
PROCESS = PROJECT.parents[1]/'neighbor-props-native-r39-r2-process.json'
PROCESS_SHA = 'a32031fd3ac9146a8f11cca428e408f2aedaf818eca7577809e19e9816b80038'
RAW = PROJECT.parents[1]/'neighbor-props-native-r39-r2.log.json'
RAW_SHA = 'd4876569fecd2be662bd3ea7061858c988b75063063e75dd6abe6cba6ca94993'
AUDIT = PROJECT.parents[1]/'root-native-failure-byte-audit-r39b-r2.json'
AUDIT_SHA = '60e978186ad471861f5a9b959ce982f4fc90a25b8f2a9e33a07d74050edd78ec'
NATIVE = ROOT/'scripts/unreal/exterior-neighbor-props-native-r39-r2.py'
NATIVE_SHA = 'c3bae8d5023ae0bb90cf1f4a3a56e8c6d8418fbcdee6ba4ea4ecc5c178fa3b71'
ENGINE = Path('/Users/Shared/Epic Games/UE_5.8/Engine')


def require(value, message):
    if not value:
        raise RuntimeError(message)


def read(path):
    return json.loads(Path(path).read_text())


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}


def binary64(value):
    value = float(value)
    require(math.isfinite(value), 'Only finite observed scalar values may be published')
    return {'value': value, 'binary64LittleEndian': struct.pack('<d', value).hex(), 'pythonFloatHex': value.hex()}


def exact_mismatches(actual, expected, names):
    require(len(actual) == len(expected) == len(names), 'Exact axis schema required')
    result = []
    for name, got, wanted in zip(names, actual, expected):
        a, e = binary64(got), binary64(wanted)
        if a['binary64LittleEndian'] != e['binary64LittleEndian']:
            result.append({'axis': name, 'actual': a, 'expected': e, 'numericDifference': float(got)-float(wanted)})
    return result


def struct_info(value, axes):
    got = [float(getattr(value, axis)) for axis in axes]
    return {'typeModule': type(value).__module__, 'typeName': type(value).__name__, 'pythonWrapperId': id(value),
            'repr': repr(value), 'axes': list(axes), 'values': got,
            'binary64': [binary64(v) for v in got],
            'editorPropertyValues': [float(value.get_editor_property(axis)) for axis in axes],
            'nativeStructMemoryPointerOrOwnershipDecoded': False}


def transform_info(value):
    rows = {key: struct_info(value.get_editor_property(key), axes) for key, axes in
            (('translation', 'xyz'), ('rotation', 'xyzw'), ('scale3d', 'xyz'))}
    rows.update(typeModule=type(value).__module__, typeName=type(value).__name__, pythonWrapperId=id(value), repr=repr(value))
    return rows


def expected_input(row):
    angle = math.radians(row['yawDegrees'])/2.
    return {'translation': row['positionCm'], 'rotation': [0., 0., math.sin(angle), math.cos(angle)],
            'scale3d': [row['uniformScale']]*3}


def capture_authored_root(u, row, publish):
    record = {'assembly': {k: row[k] for k in ('id', 'modelId', 'positionCm', 'yawDegrees', 'uniformScale')},
              'expectedOriginalFrozenConstructorValues': expected_input(row), 'stages': [], 'nativeYawRoutes': []}
    def save(stage, transform=None, wrapped=None, axes=None, key=None):
        item = {'stage': stage}
        if transform is not None:
            item['transform'] = transform_info(transform)
        if wrapped is not None:
            item['localWrappedProperty'] = struct_info(wrapped, axes)
            item['obtainedBy'] = 'get_editor_property('+key+') on this new local Transform'
            item['propertyWrapperReadAfterUpdate'] = struct_info(transform.get_editor_property(key), axes)
            item['localPythonWrapperEqualsFreshPropertyObject'] = wrapped is transform.get_editor_property(key)
        record['stages'].append(item)
        publish(record)
    try:
        t = u.Transform()
        save('new-Transform-defaults', t)
        for key, axes in (('translation', 'xyz'), ('rotation', 'xyzw'), ('scale3d', 'xyz')):
            local = t.get_editor_property(key)
            wanted = record['expectedOriginalFrozenConstructorValues'][key]
            save(key+'-wrapper-before-scalar-writes', t, local, axes, key)
            for axis, value in zip(axes, wanted):
                local.set_editor_property(axis, value)
                save(key+'-after-local-'+axis+'-write', t, local, axes, key)
            t.set_editor_property(key, local)
            save(key+'-after-Transform-property-copy-back', t, local, axes, key)
        final = transform_info(t)
        record['actualFinalConstructor'] = final
        record['exactMismatchAxes'] = []
        for key, axes in (('translation', 'xyz'), ('rotation', 'xyzw'), ('scale3d', 'xyz')):
            record['exactMismatchAxes'].extend(exact_mismatches(final[key]['values'],
                record['expectedOriginalFrozenConstructorValues'][key], [key+'.'+axis for axis in axes]))
        record['frozenStrictConstructorWouldPass'] = not record['exactMismatchAxes']
        publish(record)
    except Exception as error:
        record['constructorObservationError'] = {'type': type(error).__name__, 'message': str(error)}
        publish(record)
    # A separate reflected, local Rotator->Quaternion observation; no choice of
    # a replacement convention, normalization, tolerance, or actor setter here.
    try:
        rot = u.Rotator()
        route = {'route': 'new Rotator wrapped pitch/roll=0,yaw=authored -> Quaternion ScriptMethod',
                 'default': struct_info(rot, ('pitch', 'yaw', 'roll')), 'scalarWrites': []}
        record['nativeYawRoutes'].append(route)
        publish(record)
        for axis, value in (('pitch', 0.), ('yaw', row['yawDegrees']), ('roll', 0.)):
            rot.set_editor_property(axis, value)
            route['scalarWrites'].append({'axis': axis, 'requested': binary64(value), 'actual': struct_info(rot, ('pitch', 'yaw', 'roll'))})
            publish(record)
        try:
            q = rot.quaternion()
            route['quaternionScriptMethod'] = struct_info(q, 'xyzw')
            route['quaternionVsFrozenExpectedMismatchAxes'] = exact_mismatches(route['quaternionScriptMethod']['values'],
                record['expectedOriginalFrozenConstructorValues']['rotation'], ['rotation.'+a for a in 'xyzw'])
        except Exception as error:
            route['quaternionScriptMethodUnavailable'] = {'type': type(error).__name__, 'message': str(error)}
        try:
            q = u.MathLibrary.conv_rotator_to_quaternion(rot)
            route['reflectedMathLibraryQuaternion'] = struct_info(q, 'xyzw')
        except Exception as error:
            route['reflectedMathLibraryQuaternionUnavailable'] = {'type': type(error).__name__, 'message': str(error)}
        publish(record)
    except Exception as error:
        record['nativeYawRouteObservationError'] = {'type': type(error).__name__, 'message': str(error)}
        publish(record)
    return record


def primary_api():
    paths = {'reflectedDoubleTransforms': ENGINE/'Source/Runtime/CoreUObject/Public/UObject/NoExportTypes.h',
             'structPropertyAccess': ENGINE/'Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyWrapperStruct.cpp',
             'reflectedRotatorQuaternion': ENGINE/'Source/Runtime/Engine/Classes/Kismet/KismetMathLibrary.h'}
    require(all(path.is_file() for path in paths.values()), 'Installed reflection source missing')
    require('FQuat Rotation;' in paths['reflectedDoubleTransforms'].read_text()
            and 'GetEditorProperty' in paths['structPropertyAccess'].read_text()
            and 'Conv_RotatorToQuaternion(FRotator InRot)' in paths['reflectedRotatorQuaternion'].read_text(),
            'Installed reflection routes changed')
    return {key: pin(path) for key, path in paths.items()}


def main():
    import unreal as u
    require(Path(os.environ['BREZI_NEIGHBOR_PROPS_TRANSFORM_DIAGNOSTIC_OUTPUT']).resolve() == OUTPUT,
            'One exact fresh diagnostic output only')
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == PROJECT,
            'Only actual failed R39b project context required; no project mutation')
    require(not OUTPUT.exists(), 'Do not overwrite a historical diagnostic')
    evidence = {}
    for key, path, wanted in (('sourceProposal', SOURCE, SOURCE_SHA), ('failedNativeReport', FAILED, FAILED_SHA),
        ('failedNativeProcess', PROCESS, PROCESS_SHA), ('failedRawProcess', RAW, RAW_SHA),
        ('rootFailureByteAudit', AUDIT, AUDIT_SHA), ('frozenConstructorOwner', NATIVE, NATIVE_SHA)):
        row = pin(path);require(row['sha256'] == wanted, 'Exact constructor-boundary source/evidence changed: '+str(path));evidence[key] = row
    failure, terminal, raw, audit = (read(p) for p in (FAILED, PROCESS, RAW, AUDIT))
    require(failure['status'] == 'failed' and failure['error'] == 'Authored double XYZ/yaw/uniform scale constructor differs'
            and failure['nativeApplied'] is False and failure['savedMapUnloadedReloaded'] is False
            and failure['nativeProcessId'] == raw['pid'] == 47288 and raw['code'] == 255 and raw['signal'] is None
            and terminal['sourcePinsUnchangedAfterNative'] is True and len(terminal['sourcePinsBeforeNative']) == 1263,
            'Exact actually closed constructor failure required')
    require(audit['nativeReport'] == evidence['failedNativeReport'] and audit['nativeProcess'] == evidence['failedNativeProcess']
            and audit['rawNativeProcess'] == evidence['failedRawProcess'] and audit['candidateOriginal4235FilesExact'] is True
            and audit['selectedR38bAll4235FilesExact'] is True and audit['all1263FrozenSourcePinsExact'] is True
            and audit['originalMapByteExact'] is True and audit['oldNativeActorMutationOrMapSaveReached'] is False,
            'Root verified the failed original-preserved state')
    source = read(SOURCE);rows = source['placements'];require(len(rows) == 6, 'Exactly six original authored rows required')
    primary = primary_api()
    files = {row['path']: row['sha256'] for row in [*evidence.values(), *primary.values(), pin(ROOT/OWNER)]}
    OUTPUT.mkdir()
    report = {'schema': 'brezi-six-local-transform-constructor-readonly-diagnostic-r39-r1', 'schemaVersion': 1,
        'owner': OWNER, 'status': 'running', 'nativeProcessId': os.getpid(), 'project': str(PROJECT),
        'startedAt': datetime.now(timezone.utc).isoformat(), 'evidence': evidence, 'primaryApi': primary, 'inputFiles': files,
        'rows': [], 'sceneActorsAssetsOrMapsMutated': False, 'assetsImportedOrSaved': False, 'levelLoadedCreatedOrSaved': False,
        'localValueStructWritesOnly': True, 'nativeGeometryOrMatrixDecodePerformed': False,
        'nativeMemoryOwnershipClaimedFromPythonObjectIds': False, 'normalizationOrSignedZeroCauseAssumed': False,
        'replacementConstructorSelected': False, 'epsilonOrToleranceRelaxationProposed': False,
        'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'activeOutputPromoted': False}
    def persist():
        REPORT.write_text(json.dumps(report, indent=2, sort_keys=True, allow_nan=False)+'\n')
    persist()
    for row in rows:
        index = len(report['rows']);report['rows'].append({'assembly': row['id'], 'pending': True})
        def publish(observation):
            report['rows'][index] = observation;persist()
        capture_authored_root(u, row, publish)
    require(all(pin(path)['sha256'] == wanted for path, wanted in files.items()), 'Read-only diagnostic source changed')
    report.update(status='completed-read-only-six-authored-transform-observations', completedAt=datetime.now(timezone.utc).isoformat(),
                  sourceInputsUnchanged=True, fullConstructorRowsObserved=sum('actualFinalConstructor' in r for r in report['rows']))
    persist()
    print(json.dumps({'report': pin(REPORT), 'status': report['status'], 'fullConstructorRowsObserved': report['fullConstructorRowsObserved']}), flush=True)


if __name__ == '__main__':
    main()
