"""Read-only independent R16 Shipping capture chain audit; no native launch.

The root's separately pinned 19-check receipt supplies whole-bundle hashing,
signature and original donor machine-code evidence. This audit independently
checks raw capture/runtime copies, cameras, settings, PIDs and current 592
post-native source pins. GUI-entry failures and focus limits remain explicit.
"""
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-continuous-shipping-qa-r16a-audit.py'
V = ROOT / 'output/unreal/exterior-validation-20260930-r1'
SOURCE = ROOT / 'output/unreal/exterior-20261001-r16a'
ARTIFACTS = V / 'qa/after-exterior-r16a-continuous-artifacts-1790886800462'
OUTPUT = V / 'continuous-meadow-shipping-qa-r16a-audit-r1.json'
PACKAGE_AUDIT = V / 'continuous-meadow-package-r16a-audit-r1.json'
PACKAGE_AUDIT_SHA = '4baeb8ee53c0069822ee10c4b59e1c4a71c9713847841f8126bac911acf23cc1'
EXPECTED_PIDS = {'exterior-parcels': 10885, 'exterior-canopy-grove': 11100}
EXPECTED_FOCUS = {'exterior-parcels': [300, 300, 300], 'exterior-canopy-grove': [0, 0, 300]}
HOST = str(ROOT / 'scripts/unreal/exterior-source.mjs')
HOST_OLD = '32eed4a8130f8dbc1be3df75d162e0ff9eb340a212749fcc3e53f1d468a1ff52'
HOST_POST = '72509e45e6942cb408e0ad036369fd5f1528cc0848cf21497955a1b29b80ec56'


def sha(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def pin(path):
    p = Path(path).resolve()
    if not p.is_file() or p.is_symlink():
        raise RuntimeError('Missing/nonregular evidence file: ' + str(p))
    return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}


def png_pixels(path):
    with Path(path).open('rb') as f:
        header = f.read(24)
    if len(header) != 24 or header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR':
        raise RuntimeError('Invalid native PNG header')
    return list(struct.unpack('>II', header[16:24]))


def main():
    if OUTPUT.exists():
        raise RuntimeError('Prior audit receipt is immutable; refuse overwrite')
    checks, failures = {}, []
    def check(name, value):
        if name in checks:
            raise RuntimeError('Repeated audit check: ' + name)
        checks[name] = bool(value)
        if not value: failures.append(name)
    package_file = SOURCE / 'model-package.json'
    native_file = SOURCE / 'exterior-import-report.json'
    ownership_file = V / 'post-native-package-input-ownership-r16a-r2.json'
    camera_file = SOURCE / 'Project/BreziTwin/Content/Data/viewpoints.json'
    map_file = SOURCE / 'Project/BreziTwin/Content/Brezi/Maps/Brezi.umap'
    summary_file = ARTIFACTS / 'summary.json'
    base_files = [PACKAGE_AUDIT, package_file, native_file, ownership_file, camera_file, map_file, summary_file,
                  SOURCE / 'package-inputs.json', SOURCE / 'geometry/viewpoints.json']
    input_pins = {str(p): pin(p) for p in base_files}
    package_audit, package, native, ownership, cameras, summary = (
        read(p) for p in (PACKAGE_AUDIT, package_file, native_file, ownership_file, camera_file, summary_file))
    check('rootPackageAuditExactSelectedHash', input_pins[str(PACKAGE_AUDIT)]['sha256'] == PACKAGE_AUDIT_SHA)
    check('rootPackageAudit19ChecksAllPass', package_audit['status'] == 'PASS_PACKAGE_PROVENANCE_ONLY'
          and len(package_audit['checks']) == 19 and all(package_audit['checks'].values()) and package_audit['failures'] == [])
    check('actualModelPackageShippingAnd37FileBytes', package['status'] == 'current-model-packaged'
          and package['gameConfiguration'] == 'Shipping' and package['bundle']['fileCount'] == 37
          and package['bundle']['bytes'] == 2614978506 and package['bundle']['symbolicLinks'] == 0)
    check('packageAuditAndPackageReportPinMatch', package_audit['receiptPins'][str(package_file)] == sha(package_file))
    check('actualNativeReportPinMatchesPackagedExterior', native['status'] == 'exterior-import-validated'
          and native['savedReloaded'] is True and package['exterior']['reportSha256'] == sha(native_file))
    check('originalCBB3000StillBound', native['activeDesign'] == package['activeDesign'] ==
          {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'} and native['setbacksMm'] == {'street': 3000, 'east': 3000})
    check('currentOriginalR16MapAndCameraMatchSavedNativeBytes', all(
        native['afterAssetHashes'][str(p)] == input_pins[str(p)]['sha256'] for p in (map_file, camera_file)))
    check('sourceCameraBytesMatchBothPackageInputReceipts', all(
        package['inputs'][str(p)] == read(SOURCE / 'package-inputs.json')[str(p)] == sha(p)
        for p in (camera_file, SOURCE / 'geometry/viewpoints.json')))
    app = Path(package['appPath'])
    actual_files = [p for p in app.rglob('*') if p.is_file()]
    stat_rows = {p.relative_to(app).as_posix(): p.stat().st_size for p in actual_files}
    delegated_payload = package_audit['actualPayloadFiles']
    check('actualBundleFileSetAndLogicalSizesMatchDelegatedHashAudit', len(stat_rows) == 37
          and sum(stat_rows.values()) == 2614978506 and set(stat_rows) == set(delegated_payload)
          and all(stat_rows[k] == delegated_payload[k]['bytes'] for k in stat_rows)
          and not any(p.is_symlink() for p in app.rglob('*')))
    check('delegatedAll37HashTableMatchesPackageManifest', {k: v['sha256'] for k, v in delegated_payload.items()}
          == package['bundle']['payloadHashes'])
    check('delegatedSignatureAndOriginalShippingCodeProofPresent', package_audit['signatureExitCode'] == 0
          and package_audit['checks']['actualShippingOriginalRawBinaryExactDonor']
          and package_audit['actualTextSha256'] == package['bundle']['launch']['linkedEntry']['codeSection']['sha256'])
    check('postNative592OwnershipTypeAndNativeReportPreserved', ownership['status'] ==
          'frozen-r16a-post-native-host-correction-source-before-package' and len(ownership['inputFiles']) == 592
          and ownership['nativeReportRewritten'] is False and ownership['originalHostFailurePreserved'] is True)
    historical_file = Path(ownership['originalPreNativeOwnership']['path'])
    snapshot_file = Path(ownership['consumedNativeSnapshot']['path'])
    input_pins[str(historical_file)] = pin(historical_file)
    input_pins[str(snapshot_file)] = pin(snapshot_file)
    check('original584AndConsumedSnapshotPinsUnmodified', sha(historical_file) == ownership['originalPreNativeOwnership']['sha256']
          and sha(snapshot_file) == ownership['consumedNativeSnapshot']['sha256'])
    historical = read(historical_file)['inputFiles']; post = ownership['inputFiles']
    changed = {k: [historical[k], post[k]] for k in set(historical) & set(post) if historical[k] != post[k]}
    check('hostR2DeltaExplicitOneChangedAnd8AddedNoRemoved', len(historical) == 584 and len(set(post) - set(historical)) == 8
          and not (set(historical) - set(post)) and changed == {HOST: [HOST_OLD, HOST_POST]}
          and ownership['postNativeHostDelta'] == [{'path': HOST, 'consumedSha256': HOST_OLD, 'currentSha256': HOST_POST}])
    post_before = {path: sha(path) for path in post}
    check('actualCurrent592PostNativeSourcePinsExactBeforeAudit', post_before == post)
    check('summaryOwnR16PackageChainAndTwoDistinctViews', summary['source'] == str(SOURCE)
          and summary['packageReportSha256'] == sha(package_file) and len(summary['results']) == 2
          and len({r['id'] for r in summary['results']}) == 2)
    case_rows = []
    for recorded in summary['results']:
        directory = Path(recorded['evidence'])
        check(recorded['id'] + ':ownedEvidenceDirectory', directory.parent == ARTIFACTS and directory.name == recorded['id'])
        files = {name: pin(directory / name) for name in ('qa.json', 'runtime.json', 'capture.png', 'runtime.log', 'process.log')}
        input_pins.update({r['path']: r for r in files.values()})
        qa, runtime = read(directory / 'qa.json'), read(directory / 'runtime.json')
        view = runtime['activeView']; prefix = view + ':'
        check(prefix + 'selectedViewAndExactCaseReceipt', view in EXPECTED_PIDS and qa == recorded
              and qa['scene'] == view + '-day' and qa['source'] == str(SOURCE) and qa['status'] == 'measured'
              and qa['mode'] == 'retina' and qa['profile'] == 'cinematic' and qa['motion'] == 'static')
        check(prefix + 'actualPidExit0ShippingMetalSM6', runtime['processId'] == qa['outcome']['pid'] == EXPECTED_PIDS[view]
              and qa['outcome']['code'] == 0 and qa['outcome']['signal'] is None
              and runtime['buildConfiguration'] == 'Shipping' and runtime['rhi'] == 'Metal'
              and runtime['shaderPlatform'] == 'METAL_SM6' and runtime['status'] == 'capture-complete'
              and qa['shippingLaunch']['status'] == 'native-report-pid-and-configuration-verified')
        check(prefix + 'qaPackageRuntimePngHashChain', qa['packageReportSha256'] == sha(package_file)
              and qa['runtimeReportSha256'] == files['runtime.json']['sha256']
              and qa['screenshotSha256'] == files['capture.png']['sha256'])
        original_png = Path(runtime['screenshotPath'])
        original_runtime = original_png.with_name(original_png.name.removesuffix('-scene.png') + '.json')
        original_pins = {'png': pin(original_png), 'runtime': pin(original_runtime)}
        input_pins.update({r['path']: r for r in original_pins.values()})
        check(prefix + 'rawOriginalNativeDiagnosticCopiesByteExact', original_pins['png']['sha256'] == files['capture.png']['sha256']
              and original_pins['runtime']['sha256'] == files['runtime.json']['sha256'])
        check(prefix + 'actual1920x1080OriginalPngAndSceneOutput', png_pixels(directory / 'capture.png') == qa['pixels']
              == runtime['screenshotPixels'] == [1920, 1080] and runtime['screenshotSaved'] is True
              and runtime['screenshotKind'] == 'current-scene-render-target-preserving-view-history'
              and runtime['initialGameViewportPixels'] == runtime['finalGameViewportPixels'] == [1920, 1080]
              and runtime['separateSceneRenderTargetThroughoutBenchmark'] is True
              and runtime['sceneTargetMatchesViewportThroughoutBenchmark'] is True)
        camera = next(c for c in cameras['views'] if c['id'] == view)
        native_camera = runtime['walking']['presentationCamera']
        delta = [camera['targetCm'][i] - camera['eyeCm'][i] for i in range(3)]
        length = math.sqrt(sum(v*v for v in delta)); forward = [v / length for v in delta]
        eye_error = math.dist(native_camera['eyeCm'], camera['eyeCm'])
        forward_error = math.dist(native_camera['forward'], forward)
        check(prefix + 'actualSavedCameraEyeAndForward', cameras['coordinateSystem'] == 'unreal-centimeters'
              and runtime['walking']['cameraMode'] == 'orbit' and eye_error <= .5 and forward_error <= .001)
        check(prefix + '2400Warmup300NativeSamplesImportedDaylight', runtime['warmupFrames'] == 2400
              and runtime['requestedBenchmarkFrames'] == runtime['frameInterval']['sampleCount'] == 300
              and runtime['lighting'] == 'imported-daylight' and runtime['exteriorLighting']['ready'] is True
              and runtime['exteriorLighting']['sceneSha256'] == package['sourceManifestSha256'])
        settings = runtime['renderSettings']
        expected_settings = {'r.ScreenPercentage': 100, 'r.TSR.History.ScreenPercentage': 200, 'r.AntiAliasingMethod': 4,
            'r.DynamicRes.OperationMode': 0, 'r.SecondaryScreenPercentage.GameViewport': 100,
            'r.DynamicGlobalIlluminationMethod': 1, 'r.ReflectionMethod': 1, 'r.RayTracing': 1,
            'r.Lumen.HardwareRayTracing': 1, 'foliage.DensityScale': 1, 'sg.FoliageQuality': 3,
            'sg.GlobalIlluminationQuality': 3, 'sg.ShadowQuality': 3, 'r.VSync': 0, 't.MaxFPS': 0}
        check(prefix + 'actualCinematic100200TsrAndGiProfile', all(settings[k] == v for k, v in expected_settings.items())
              and runtime['finalViewPostProcessSettings']['renderThreadAntiAliasing']['antiAliasingMethodName'] == 'TSR'
              and runtime['presentation']['outputMode'] == 'retina' and runtime['presentation']['targetMatchesOutputContract'] is True)
        focus = runtime['focusDuringBenchmark']
        actual_focus = [focus[k] for k in ('applicationForegroundSamples', 'gameWindowActiveSamples', 'sceneViewportKeyboardFocusSamples')]
        check(prefix + 'actualFocusFactsPreservedWithout300AcceptanceGate', focus == qa['foreground']
              and focus['sampleCount'] == 300 and actual_focus == EXPECTED_FOCUS[view])
        entry = qa['entry']; process_log = (directory / 'process.log').read_text()
        check(prefix + 'guiEntryDetectorFailurePreservedSeparately', entry['status'] == 'failed'
              and entry['errors'] == ['Engine initialization after app entry was not observed']
              and entry['pid'] == runtime['processId'] and entry['selfExecCount'] == 1
              and f"pid={runtime['processId']} phase=self-exec" in process_log
              and f"pid={runtime['processId']} phase=enter-engine" in process_log)
        check(prefix + 'shippingRuntimeLoggingUnavailableRecordedHonestly', qa['shippingLaunch']['loggingAvailable'] is False
              and files['runtime.log']['bytes'] == 0)
        case_rows.append({'view': view, 'nativeProcessId': runtime['processId'], 'exitCode': qa['outcome']['code'],
            'shippingNativeCaptureEvidenceValidated': True, 'sourceCamera': camera, 'observedCamera': native_camera,
            'cameraEyeErrorCm': eye_error, 'cameraForwardEuclideanError': forward_error, 'nativeFovObserved': False,
            'focusSamples': {'applicationForeground': actual_focus[0], 'gameWindowActive': actual_focus[1],
                             'sceneViewportKeyboardFocus': actual_focus[2], 'total': focus['sampleCount']},
            'focusConditionEligibleForTiming': all(v == 300 for v in actual_focus),
            'timingEligibleForFocusedBenchmark': all(v == 300 for v in actual_focus),
            'timing': runtime['frameInterval'], 'timingAcceptance': False,
            'timingLimitation': 'Observed native intervals only; no performance acceptance or Editor/Shipping FPS comparison.'
                if all(v == 300 for v in actual_focus) else 'Application and game window inactive for all300samples; timing not eligible for focused performance conclusions.',
            'guiEntryDetector': entry, 'guiEntryDetectorPassed': False, 'runtimeLoggingAvailable': False,
            'runtimeShaderCompileErrorsIndependentlyAssessed': False, 'files': files, 'originalNativeDiagnostics': original_pins,
            'pixels': [1920, 1080], 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False})
    check('bothSelectedNativeViewsObservedExactlyOnce', {r['view'] for r in case_rows} == set(EXPECTED_PIDS))
    post_after = {path: sha(path) for path in post}
    check('actualCurrent592PostNativeSourcePinsExactAfterAudit', post_after == post_before == post)
    check('allOriginalCaptureAndReceiptInputsByteUnchangedDuringAudit', all(pin(row['path']) == row for row in input_pins.values()))
    result = {'owner': OWNER, 'auditSource': pin(__file__), 'status': 'PASS_SHIPPING_NATIVE_ARTIFACT_CHAIN_ONLY' if not failures else 'FAIL',
        'generatedAt': datetime.now(timezone.utc).isoformat(), 'checks': checks, 'checkCount': len(checks),
        'passedCheckCount': sum(checks.values()), 'failures': failures, 'cases': case_rows,
        'nativeShippingArtifactCasesVerified': 2 if not failures else 0,
        'guiEntryDetectorCasesPassed': 0, 'nativeFovObserved': False,
        'sourceOwnership': {'receipt': input_pins[str(ownership_file)], 'currentPostNativePinsIndependentlyVerified': 592,
            'originalPreNativePinsHistoricalCount': 584, 'originalPreNativePinsCurrentUnchangedClaimed': False,
            'postNativeHostDelta': ownership['postNativeHostDelta'], 'addedPostNativePinCount': 8,
            'nativeReportRewritten': False, 'originalHostFailurePreserved': True},
        'packageProvenance': {'audit': input_pins[str(PACKAGE_AUDIT)], 'scope': 'Delegated exact37payloadSHA/signature/originalShippingrawandmachinecode checks to pinned root19checkaudit; currentfile-set/sizes independentlychecked.',
            'payloadFiles': 37, 'logicalBytes': 2614978506, 'rootChecks': 19, 'packagePayloadHashesIndependentlyRepeated': False,
            'actualTextSha256FromRootAudit': package_audit['actualTextSha256'], 'signatureExitCodeFromRootAudit': 0},
        'inputPins': input_pins, 'nativeExecutedByAuditor': False, 'gpuExecutedByAuditor': False,
        'visualAppearanceInspectedByAuditor': False, 'nativeAppearanceAccepted': False,
        'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'editorShippingFpsCompared': False,
        'limitations': ['Both GUI-entry initialization detectors failed; native PID/Shipping/RHI/capture evidence is separate.',
            'Grove focus0/0/300 makes its timing ineligible; parcels300/300/300 does not establish performance acceptance.',
            'Native camera eye/forward observed; FOV is saved-source evidence only.',
            'Shipping runtime logs are empty; runtime shader errors cannot be independently assessed from them.',
            'This audit does not decide visual realism or modify any original report, capture, source, project or package.']}
    OUTPUT.write_text(json.dumps(result, indent=2, ensure_ascii=False, allow_nan=False) + '\n')
    print(json.dumps({'status': result['status'], 'receipt': pin(OUTPUT), 'checks': len(checks),
                      'passed': sum(checks.values()), 'failures': failures, 'nativeCases': result['nativeShippingArtifactCasesVerified'],
                      'performanceAccepted': False}))
    if failures:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
