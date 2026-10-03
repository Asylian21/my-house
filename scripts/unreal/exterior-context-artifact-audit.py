"""Read-only native context-view artifact audit, separate from appearance approval.

Requires an independently audited saved import and a sealed Shipping package.
The caller supplies the exact view identities and package hash. Artifact-only
mode records unavailable foreground timing honestly without accepting quality
or performance. Does not launch Unreal or modify any source/project/selector.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-artifact-audit.py'
DESIGN = {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
SETBACKS = {'street': 3000, 'east': 3000}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def resolve(path):
    return (ROOT / Path(path)).resolve()


def read(path):
    return json.loads(resolve(path).read_text())


def sha(path):
    digest = hashlib.sha256()
    with resolve(path).open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def pin(path, value):
    path = resolve(path)
    require(path.is_file() and sha(path) == value, 'Pinned evidence differs: ' + str(path))
    return path


def receipt(path):
    return {'path': str(resolve(path)), 'sha256': sha(path)}


def png_size(path):
    with resolve(path).open('rb') as stream:
        header = stream.read(24)
    require(header[:8] == b'\x89PNG\r\n\x1a\n' and header[12:16] == b'IHDR', 'Invalid PNG')
    return list(struct.unpack('>II', header[16:24]))


def timing(runtime, qa, artifact_only):
    focus, frame = runtime['focusDuringBenchmark'], runtime['frameInterval']
    require(frame['status'] == 'measured' and frame['sampleCount'] == focus['sampleCount'] == 300,
            'Exact frame/focus population differs')
    require(focus == qa['foreground'] and frame == qa['frame'], 'Copied QA timing/focus differs')
    keys = ('applicationForegroundSamples', 'gameWindowActiveSamples', 'sceneViewportKeyboardFocusSamples')
    require(all(type(focus[key]) is int and 0 <= focus[key] <= 300 for key in keys), 'Invalid focus counts')
    valid = (all(focus[key] == 300 for key in keys) and focus['applicationForegroundThroughoutBenchmark'] is True)
    require(artifact_only or valid, 'Foreground timing unavailable: all application/window/keyboard samples required')
    require(all(type(frame[key]) in (int, float) and math.isfinite(frame[key]) and frame[key] > 0
                for key in ('meanMs', 'p50Ms', 'p95Ms', 'p99Ms', 'maxMs')), 'Invalid measured frame intervals')
    return {'timingEligible': valid, 'timingValid': valid, 'timingInvalid': not valid,
            'timingInvalidReason': None if valid else 'Incomplete application/window/keyboard foreground coverage; no active-play FPS claim.',
            'sampleCount': 300, **{key: focus[key] for key in keys}, 'frameReceipt': frame,
            'performanceAccepted': False}


def audit(source, summary_path, package_sha, import_audit_path, import_audit_sha, scenes, artifact_only=False):
    source, summary_path = resolve(source), resolve(summary_path)
    require(source.is_relative_to(ROOT / 'output/unreal'), 'Candidate outside immutable output tree')
    require(len(scenes) == len(set(scenes)) == 3, 'Exactly three distinct declared context views required')
    import_audit = read(pin(import_audit_path, import_audit_sha))
    require(resolve(import_audit['source']) == source and import_audit['status'] == 'PASS_READ_ONLY_R10_ENCODING_GREENERY_RECEIPTS_NATIVE_ACCEPTANCE_PENDING',
            'Independent import audit identity/status differs')
    require(import_audit['nativeVisualAccepted'] is False and import_audit['performanceAccepted'] is False,
            'Import-only source evidence cannot grant appearance/performance approval')
    imported = read(source / 'exterior-import-report.json')
    pin(source / 'exterior-import-report.json', import_audit['nativeImport']['receipt']['sha256'])
    require(imported['activeDesign'] == DESIGN and imported['setbacksMm'] == SETBACKS and imported['savedReloaded'] is True,
            'Canonical saved scene/design/setbacks differ')
    for key in ('protectedContentUnchanged', 'sourceGeometryCollisionAndTransformsPreserved', 'originalMaterialAssetsPreserved'):
        require(imported[key] is True, 'Saved preservation proof differs: ' + key)
    package_path = pin(source / 'model-package.json', package_sha)
    package = read(package_path)
    require(package['status'] == 'current-model-packaged' and package['gameConfiguration'] == 'Shipping'
            and package['activeDesign'] == DESIGN and package['exterior']['reportSha256'] == sha(source / 'exterior-import-report.json'),
            'Exact Shipping package/import/canonical design differs')
    require(package['cook']['cookCompleted'] is True and not package['cook']['failures']
            and package['bundle']['status'] == 'bundle-validated' and package['bundle']['payloadHashScope'] == 'all-bundle-files',
            'Package cook/bundle proof incomplete')
    app = resolve(package['appPath'])
    require(package['bundle']['payloadHashes'], 'Empty payload seal')
    for relative, digest in package['bundle']['payloadHashes'].items():
        target = resolve(app / relative)
        require(target.is_relative_to(app), 'Bundle path escape')
        pin(target, digest)
    launch = package['bundle']['launch']
    pin(launch['executable'], launch['executableSha256'])
    summary = read(summary_path)
    require(resolve(summary['source']) == source and summary['packageReportSha256'] == package_sha,
            'Context suite candidate/package differs')
    rows = summary['results']
    require(len(rows) == len({r['id'] for r in rows}) == len({r['evidence'] for r in rows}) == 3
            and {r['scene'] for r in rows} == set(scenes), 'Exact context suite identity differs')
    managed = {key: value for key, value in imported['geometry']['groups'].items() if value['qualityDetail']}
    require(len({value['actor'] for value in managed.values()}) == len(managed), 'Duplicate managed native actors')
    hidden = {row['actor'] for row in imported['naturalLawn']['hiddenOriginalGroups']}
    require(len(hidden) == 4 and imported['naturalLawn']['savedReadback']['instances'] == 40437,
            'Original hidden lawn scope differs')
    canonical_details = canonical_settings = None
    result = []
    for row in rows:
        evidence = resolve(row['evidence'])
        require(evidence.parent == summary_path.parent and evidence.name == row['id'], 'Context result evidence path differs')
        qa_path = evidence / 'qa.json'
        qa = read(qa_path)
        require(qa == row and qa['phase'] == summary['phase'] and resolve(qa['source']) == source
                and qa['packageReportSha256'] == package_sha and qa['status'] == 'measured', 'QA copied identity differs')
        require(qa['outcome']['code'] == 0 and qa['outcome']['signal'] is None, 'Native process failed')
        runtime_path = pin(evidence / 'runtime.json', qa['runtimeReportSha256'])
        image = pin(evidence / 'capture.png', qa['screenshotSha256'])
        runtime = read(runtime_path)
        require(runtime['status'] == 'capture-complete' and type(runtime['processId']) is int and runtime['processId'] > 0
                and runtime['processId'] == qa['outcome']['pid'] and runtime['buildConfiguration'] == 'Shipping'
                and runtime['rhi'] == 'Metal' and runtime['shaderPlatform'] == 'METAL_SM6', 'Actual native PID/RHI/build differs')
        require(qa['shippingLaunch'] == {'status': 'native-report-pid-and-configuration-verified', 'loggingAvailable': False},
                'Native Shipping launch proof differs')
        require(qa['profile'] == 'cinematic' and qa['mode'] == 'retina' and qa['motion'] == 'static'
                and qa['software'] is False and qa['statOverlays'] is False and runtime['activeView'] == qa['scene'].removesuffix('-day'),
                'Native context view/profile/presentation differs')
        arguments = qa['args']
        for argument in ('-BreziRenderProfile=cinematic', '-BreziOutput=retina', '-BreziCaptureScene',
                         '-BreziWarmupFrames=2400', '-BreziBenchmarkFrames=300', '-BreziView=' + runtime['activeView']):
            require(arguments.count(argument) == 1, 'Native requested argument absent/duplicate: ' + argument)
        require(not any('nullrhi' in argument.lower() for argument in arguments), 'Software/null RHI arguments')
        require(runtime['screenshotSaved'] is True and png_size(image) == runtime['screenshotPixels'] == qa['pixels'] == [1920, 1080]
                and runtime['screenshotKind'] == 'current-scene-render-target-preserving-view-history', 'Native PNG mode/dimensions differ')
        for key in ('initialGameViewportPixels', 'finalGameViewportPixels', 'requestedSceneCapturePixels',
                    'reportedRenderTargetPixels', 'rhiRenderTargetTexturePixels',
                    'minimumSceneRenderTargetPixelsDuringBenchmark', 'minimumSceneRHITexturePixelsDuringBenchmark',
                    'maximumSceneRHITexturePixelsDuringBenchmark'):
            require(runtime[key] == [1920, 1080], 'Exact native viewport/render-target dimensions differ: ' + key)
        require(runtime['viewportChangedDuringBenchmark'] is False and runtime['sceneTargetMatchesViewportThroughoutBenchmark'] is True
                and runtime['renderPercentagesNativeThroughoutBenchmark'] is True and runtime['warmupFrames'] == 2400
                and runtime['requestedBenchmarkFrames'] == 300, 'Native warmup/render-target contract differs')
        require(runtime['walking']['contractLoaded'] is True and runtime['walking']['worldContractValidated'] is True
                and runtime['walking']['sceneSha256'] == package['sourceManifestSha256'], 'Runtime architectural source frame differs')
        require(qa['settings'] == runtime['renderSettings'] and qa['postprocess'] == runtime['finalViewPostProcessSettings'],
                'Native settings/postprocess copied receipt differs')
        settings = runtime['renderSettings']
        for key, value in {'foliage.DensityScale': 1, 'r.Brezi.DetailLighting': 1, 'r.ScreenPercentage': 100,
                           'r.SecondaryScreenPercentage.GameViewport': 100, 'r.DynamicRes.OperationMode': 0}.items():
            require(settings[key] == value, 'Full-density native Cinematic setting differs: ' + key)
        details = {value['actor']: value for value in runtime['detailLightingState']}
        require(len(details) == len(runtime['detailLightingState']) and runtime['detailLightingState'] == qa['detailLightingState']
                and not (set(details) & hidden), 'Runtime detail identity/hidden old lawn differs')
        for group in managed.values():
            require(group['actor'] in details, 'Saved managed group absent at runtime')
            value = details[group['actor']]
            require(value['instanceCount'] == group['instances'] and value['qualityEnabled'] is True
                    and value['managedDetail'] is True and value['authoredFlagsCaptured'] is True, 'Runtime saved detail count/policy differs')
            for key in ('castShadow', 'visibleInRayTracing', 'affectDistanceFieldLighting'):
                require(value[key] is True, 'Cinematic managed detail flag differs: ' + key)
        require(canonical_details is None or details == canonical_details, 'Context views have inconsistent detail group state')
        require(canonical_settings is None or settings == canonical_settings, 'Context views have inconsistent native render settings')
        canonical_details, canonical_settings = details, settings
        result.append({'id': qa['id'], 'scene': qa['scene'], 'qa': receipt(qa_path), 'runtime': receipt(runtime_path),
                       'capture': receipt(image), 'nativePid': runtime['processId'], 'rhi': 'Metal', 'buildConfiguration': 'Shipping',
                       'pixels': [1920, 1080], 'warmupFrames': 2400, 'runtimeDetailGroups': len(details),
                       'savedManagedDetailGroupsVerified': len(managed), 'savedManagedDetailInstancesVerified': sum(g['instances'] for g in managed.values()),
                       'legacyHiddenLawnActorsAbsent': 4, 'startupLogObservation': qa['entry'],
                       **timing(runtime, qa, artifact_only), 'nativeVisualAccepted': False})
    return {'schemaVersion': 1, 'owner': OWNER, 'sourceSha256': sha(ROOT / OWNER), 'status': 'verified-native-context-artifacts',
            'generatedAtUtc': datetime.now(timezone.utc).isoformat(), 'source': str(source), 'activeDesign': DESIGN, 'setbacksMm': SETBACKS,
            'importAudit': receipt(import_audit_path), 'nativeImport': receipt(source / 'exterior-import-report.json'),
            'shippingPackage': receipt(package_path), 'summary': receipt(summary_path), 'declaredScenes': list(scenes), 'results': result,
            'bundlePayloadFilesVerified': len(package['bundle']['payloadHashes']), 'artifactOnly': artifact_only,
            'timingEligibleViews': sum(row['timingEligible'] for row in result), 'timingInvalidViews': sum(row['timingInvalid'] for row in result),
            'nativeVisualAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'promotionPerformed': False,
            'limits': 'Source-bound native artifact verification only. Focus eligibility does not establish performance acceptance; no occlusion or photorealism judgment. Legacy startup log observation is retained separately from actual native PID/RHI evidence.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', required=True)
    parser.add_argument('--summary', required=True)
    parser.add_argument('--package-sha256', required=True)
    parser.add_argument('--import-audit', required=True)
    parser.add_argument('--import-audit-sha256', required=True)
    parser.add_argument('--scene', action='append', required=True)
    parser.add_argument('--artifact-only', action='store_true')
    parser.add_argument('--receipt', required=True)
    args = parser.parse_args()
    target = resolve(args.receipt)
    require(target.is_relative_to(ROOT / 'output/unreal') and not target.is_relative_to(resolve(args.source)) and not target.exists(),
            'Use a fresh external receipt')
    result = audit(args.source, args.summary, args.package_sha256, args.import_audit,
                   args.import_audit_sha256, args.scene, args.artifact_only)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'receipt': str(target), 'sha256': sha(target), 'views': len(result['results']),
                      'timingEligibleViews': result['timingEligibleViews'], 'timingInvalidViews': result['timingInvalidViews']}))


if __name__ == '__main__':
    main()
