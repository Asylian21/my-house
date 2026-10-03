#!/usr/bin/env python3
"""Record a bounded independent review of two original R18 Editor-game captures.

No engine, project, image or historical receipt writes. Images were inspected by
the owning reviewer; this producer verifies their original byte/runtime chain.
"""
import hashlib
import html
import json
import math
import os
import pathlib
import struct

ROOT = pathlib.Path(__file__).resolve().parents[2]
VALIDATION = ROOT / 'output/unreal/exterior-validation-20260930-r1'
OUTPUT = VALIDATION / 'context-yard-camera-r18-paired-review-r1'
VIEW = 'exterior-context-yard-572063-close-r18'
CASES = [
    ('baseline', 'editor-pilot-r27a-yard572063-baseline-r18-1790917066288-RDhhoB', 82915,
     '5162f1b8c5ba8d64a2765a91d4c0c2f1d82890f6bed5fda646f7593e65e0d26c',
     'a65da0d08c217b4b841517c5d279907e2ed9e5f7bb72d2a923661e5714acdc27'),
    ('candidate', 'editor-pilot-r28b-yard572063-candidate-r18-1790917219634-JfopZg', 83233,
     '87efe762af23f993d6e3a0895804db622ab41cd17c08c3b055f192d0ad892768',
     '0a7d0864ac8db9c54c5d3f710573a061ba41e37d7fa4207163d07c81af34f0c9'),
]


def require(value, message):
    if not value:
        raise AssertionError(message)


def read(path):
    return json.loads(pathlib.Path(path).read_text())


def pin(path):
    path = pathlib.Path(path).resolve()
    data = path.read_bytes()
    return dict(path=str(path), sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))


def verify(declared):
    actual = pin(declared['path'])
    require(actual['sha256'] == declared['sha256'] and actual['bytes'] == declared['bytes'],
            'Declared artifact bytes changed: ' + actual['path'])
    return actual


def case(role, name, expected_pid, expected_png, current_stdout_sha):
    directory = VALIDATION / 'qa' / name
    suite_path = directory / 'editor-pilot-suite.json'
    suite = read(suite_path)
    require(len(suite['cases']) == 1 and suite['requestedViews'] == [VIEW], 'Wrong suite scope')
    require(suite['sourceInputsUnchanged'] is True and not suite['errors'], 'Suite source/errors')
    closures = [verify(suite[k]) for k in ['inputClosureBefore', 'inputClosureAfter']]
    before, after = [read(p['path']) for p in closures]
    require(before == after and len(before) == suite['inputClosureBefore']['fileCount'],
            'Recorded pre/post file dictionaries differ')
    c = suite['cases'][0]
    require(c['processId'] == expected_pid and c['outcome'] == dict(code=0, signal=None, pid=expected_pid),
            'Capture process did not close correctly')
    process_path = pathlib.Path(c['processReceiptPath'])
    require(read(process_path) == c, 'Case differs from original terminal process receipt')
    require(not c['shaderAndLoadErrors'] and c['nativeEvidenceValidated'] is True, 'Native/errors proof')
    require(c['view'] == VIEW and c['sourceFovNativeReadbackAvailable'] is False, 'Camera scope')
    image = pin(c['originalCapturePath'])
    runtime_pin = pin(c['originalRuntimePath'])
    require(image['sha256'] == expected_png == c['originalCaptureSha256'], 'Original PNG changed')
    require(runtime_pin['sha256'] == c['originalRuntimeSha256'], 'Original runtime changed')
    raw_png = pathlib.Path(image['path']).read_bytes()
    require(raw_png[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', raw_png[16:24]) == (1920, 1080),
            'Original PNG dimensions/signature')
    runtime = read(runtime_pin['path'])
    require(runtime['processId'] == expected_pid and runtime['buildConfiguration'] == 'Development'
            and runtime['rhi'] == 'Metal' and runtime['shaderPlatform'] == 'METAL_SM6'
            and runtime['activeView'] == VIEW and runtime['screenshotSaved'] is True
            and runtime['screenshotPixels'] == [1920, 1080]
            and runtime['warmupFrames'] == 2400 and runtime['requestedBenchmarkFrames'] == 300,
            'Actual runtime scope changed')
    camera = runtime['walking']['presentationCamera']
    require(camera['eyeCm'] == c['sourceCamera']['eyeCm'] and camera['physicalEyeCm'] == camera['eyeCm']
            and not camera['occluded'] and not camera['firstPersonFallback'], 'Actual camera moved')
    target = c['sourceCamera']['targetCm']
    delta = [target[i] - camera['eyeCm'][i] for i in range(3)]
    length = math.sqrt(sum(v*v for v in delta))
    require(max(abs(delta[i]/length - camera['forward'][i]) for i in range(3)) < 1e-14,
            'Actual direction differs from fixed source target')
    logs = []
    for key, hash_key in [('runtimeLogPath', 'runtime'), ('stdoutPath', 'stdout')]:
        actual = pin(c[key]); declared = c['rawLogHashes'][hash_key]
        if hash_key == 'runtime':
            require(actual['sha256'] == declared['sha256'] and actual['bytes'] == declared['bytes'], 'Original runtime log changed')
            logs.append(dict(**actual, recordedTerminalSnapshotWholeFileEqual=True))
        else:
            data = pathlib.Path(actual['path']).read_bytes()
            require(actual['sha256'] == current_stdout_sha and len(data) == declared['bytes'] + 855
                    and hashlib.sha256(data[:declared['bytes']]).hexdigest() == declared['sha256'],
                    'Current stdout or its recorded terminal prefix changed')
            suffix = data[declared['bytes']:]
            require(suffix.startswith(b'Opening shared memory\n')
                    and b'Daemon is exiting without errors.\n' in suffix
                    and suffix.endswith(b'Listening cancelled, closing port...\n'), 'Unexpected stdout append')
            logs.append(dict(**actual, recordedTerminalSnapshotWholeFileEqual=False,
                             recordedTerminalPrefix=declared, recordedTerminalPrefixExactlyPreserved=True,
                             laterSuffixBytes=len(suffix), laterSuffixSha256=hashlib.sha256(suffix).hexdigest(),
                             laterSuffixObservation='UnrealTraceServer startup and daemon shutdown messages after the capture-process terminal snapshot'))
    evidence = suite['nativeSourceEvidence']
    evidence_pins = [verify(evidence[k]) for k in ['nativeReceipt', 'sourceNativeReport', 'sourceNativeProcess']]
    native_process = read(evidence['sourceNativeProcess']['path'])
    raw_native = pin(native_process['processFile'])
    require(raw_native['sha256'] == native_process['processFileSha256'], 'Native raw process changed')
    native_outcome = read(raw_native['path'])
    require(native_outcome['code'] == 0 and native_outcome['signal'] is None
            and native_process['sourcePinsUnchangedAfterNative'] is True, 'Saved source native failed')
    flags = ['shippingVerified', 'packageVerified', 'nativeAppearanceAccepted', 'performanceAccepted', 'fullPhotorealismAccepted']
    require(all(suite[k] is False and c[k] is False for k in flags), 'Unreviewed acceptance was asserted')
    post = runtime['finalViewPostProcessSettings']
    return dict(role=role, suite=pin(suite_path), process=pin(process_path), processId=expected_pid,
                outcome=c['outcome'], originalCapture=image, originalRuntime=runtime_pin, originalLogs=logs,
                recordedInputClosures=closures, recordedInputFileCount=len(before), recordedInputDictionariesEqual=True,
                sourceInputsIndependentlyRehashedHere=False, sourceNativeEvidence=evidence_pins,
                sourceNativeRawProcess=raw_native, sourceNativePid=native_outcome['pid'],
                sourceCamera=c['sourceCamera'], actualCamera=camera, nativeFovReadbackAvailable=False,
                renderSettings=runtime['renderSettings'], focus=runtime['focusDuringBenchmark'],
                composedPostProcess={k: post[k] for k in ['autoExposureMinEV','autoExposureMaxEV','autoExposureBias',
                    'antiAliasingMethod','lumenFinalGatherQuality','lumenReflectionQuality','lumenSceneLightingQuality',
                    'lumenSceneDetail','lumenSceneViewDistance','lumenMaxTraceDistance']},
                renderThreadPreExposure=post['renderThreadPreExposure'], shaderAndLoadErrors=[],
                shaderReadiness=c['shaderReadiness'], runtimeScope='UE5.8 Editor-game Development, Metal SM6; original Recipe4',
                originalImageActuallyViewedByReviewer=True, pngDimensions=[1920,1080])


def main():
    require(not OUTPUT.exists(), 'Owned paired review already exists; do not overwrite')
    cases = [case(*row) for row in CASES]
    a, b = cases
    require(a['sourceCamera'] == b['sourceCamera'] and a['actualCamera'] == b['actualCamera']
            and a['renderSettings'] == b['renderSettings']
            and a['composedPostProcess'] == b['composedPostProcess'], 'Pair camera/settings do not match')
    source_camera = ROOT / 'output/unreal/exterior-context-yard-20261002-camera-r18-supplement/context-yard-camera-supplement.json'
    source_pin = pin(source_camera)
    require(source_pin['sha256'] == '768274f6eb2dab6d7bcd0bee2b930feec8e2665bba7dfafb6e929f35b38ebab1', 'Frozen camera changed')
    review = dict(schema='brezi-context-yard-original-editor-paired-review-r18', owner='scripts/unreal/exterior-context-yard-paired-review-r18.py',
                  status='reviewed-original-pair-purposeful-yard-gain-with-ground-artifacts', cases=cases,
                  producer=pin(__file__), frozenCameraSupplement=source_pin,
                  pairCameraSettingsAndComposedPostProcessEqual=True, finalRenderThreadPreExposureEqual=False,
                  exposureEVDifference=b['renderThreadPreExposure']['exposureEV']-a['renderThreadPreExposure']['exposureEV'],
                  visualFindings=[
                      'The first-yard doorway, complete approach and service court are visible in both original images; no crown obscures the frame.',
                      'Candidate adds a connected doorway approach, gravel service court, two soil beds and two visible shrubs to the previously empty green yard.',
                      'The large gravel court and rectangular soil beds remain conspicuously flat with sharp geometric borders.',
                      'Detached dark triangular and dashed patches around the gravel remain a clear visual defect; no causal inference is made from image darkness alone.',
                      'Existing low foreground vegetation and leaf-litter continue across the camera foreground; unchanged architecture and broad green surroundings remain visually simple.'
                  ], sourceInferenceSeparate='R32 source study separately measured the old coarse worn-edge UV feather layout; its proposed repair has not been natively captured.',
                  limitedPurposefulLayoutGainObserved=True, cameraReviewable=True, nativeAppearanceAccepted=False,
                  fullPhotorealismAccepted=False, performanceAccepted=False, shippingVerified=False, packageVerified=False,
                  timingEligible=False, timingReason='Both captures record application foreground 0/300, window and viewport focus 300/300; no FPS comparison.',
                  selectorPromoted=False, globalVisibilityOrWalkingAccepted=False,
                  limits=['Visual review covers this one fixed first-yard view only.', 'Native FOV is not independently recorded.',
                          'Source snapshots are byte-verified as recorded pre/post dictionaries; this bounded review does not repeat all original project file hashes.',
                          'Final render-thread exposure differs by approximately 0.0106EV; composed exposure bounds and lighting/render settings match.',
                          'Both stdout files acquired855 later UnrealTraceServer bytes; recorded prefixes remain byte-exact, current full files are pinned separately.',
                          'No independent texture/material unloading, per-material GPU pass or Shipping/performance acceptance is asserted.'])
    OUTPUT.mkdir()
    (OUTPUT/'paired-review.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n')
    cards=''.join('<figure><figcaption>'+html.escape(c['role'].title())+' · PID'+str(c['processId'])+'</figcaption><a href="'+html.escape(os.path.relpath(c['originalCapture']['path'],OUTPUT))+'"><img src="'+html.escape(os.path.relpath(c['originalCapture']['path'],OUTPUT))+'" alt="'+c['role']+' original Editor scene"></a><p>Original 1920×1080 PNG · '+c['originalCapture']['sha256'][:16]+'…</p></figure>' for c in cases)
    findings=''.join('<li>'+html.escape(t)+'</li>' for t in review['visualFindings'])
    page='''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>R18 first-yard original pair</title><style>body{margin:0;background:#171b1f;color:#edf1f5;font:16px/1.55 system-ui}main{max-width:1900px;margin:auto;padding:24px}h1{font-size:27px}p{max-width:1050px}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px}figure{margin:0;min-width:0}figcaption{font-weight:700;padding:8px 0}img{width:100%;height:auto;display:block}figure p{font-size:12px;overflow-wrap:anywhere;color:#aebbc7}.verdict{border-left:4px solid #e2b66e;padding:12px 18px;background:#232a30}a{color:#9bd0ff}@media(max-width:1100px){.pair{grid-template-columns:1fr}}</style><main><h1>First-yard R18 · original matched Editor pair</h1><p class="verdict">The entrance and yard are now reviewable. Purposeful layout gain is visible; sharp floor borders, coarse dark worn-edge patches and the plain green surroundings keep full realism at NO_GO.</p><p>Actual UE5.8 Editor-game Development / Metal SM6 · same source eye, direction, FOV76 and original Recipe4 settings · warm2400/sample300. Original images below are linked without alterations. Both processes closed0 and recorded input dictionaries match before/after.</p><div class="pair">'''+cards+'''</div><ul>'''+findings+'''</ul><p>Application foreground0/300 in both captures: no performance acceptance or FPS comparison. Render-thread exposure differs by0.0106EV. Native FOV unavailable. No Shipping, full-realism or selector promotion.</p><p><a href="paired-review.json">Exact capture/runtime/process/source pins and review scope</a></p></main></html>'''
    (OUTPUT/'index.html').write_text(page)
    print(json.dumps(dict(status=review['status'], review=pin(OUTPUT/'paired-review.json'), gallery=pin(OUTPUT/'index.html'),
                          pids=[c['processId'] for c in cases], sourceFiles=sum(c['recordedInputFileCount'] for c in cases),
                          nativeAppearanceAccepted=False, performanceAccepted=False, fullPhotorealismAccepted=False)))


if __name__ == '__main__':
    main()
