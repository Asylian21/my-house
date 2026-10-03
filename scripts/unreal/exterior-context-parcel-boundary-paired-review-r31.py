"""New R39→R43 original-PNG pairs; no image edits, native or historical replay.

Presentation/camera matching kernels are copied from the frozen R30 source;
that producer is never imported or executed. Publication requires root peer.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import html
import json
import math
import os
from pathlib import Path
import struct
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-parcel-boundary-paired-review-r31.py'
V = ROOT/'output/unreal/exterior-validation-20260930-r1'
PARENT_PRESENTATION_SOURCE = ROOT/'scripts/unreal/exterior-neighbor-props-paired-review-r30.py'
PARENT_PRESENTATION_SHA = '1aaed8657708d6e28a0f53b303d716482095d7c3325f3b84de12003a2e776c61'
BEFORE_SUITE = V/'qa/editor-pilot-r39c-whole-original-neighbor-props-r30-1790963761054-81YFO4/editor-pilot-suite.json'
BEFORE_SUITE_SHA = '74b4786829eb7f415a197ac603cb4c225eb046547ca9322243a8000e85dbc279'
AFTER_SUITE = V/'qa/editor-pilot-r43b-authored-open-boundaries-r31-1790971294433-49tWm6/editor-pilot-suite.json'
AFTER_SUITE_SHA = '71c00d7ccc0ee4f06ac7ef5115945de080497e4e6c6a058f2cebe87185d34677'
VIEWS = ('exterior-context-yard-572063-close-r18', 'exterior-neighborhood-ground-r38')
BEFORE_SOURCE = ROOT/'output/unreal/exterior-20261002-r39c-neighbor-props-two-camera-candidate-r30'
AFTER_SOURCE = ROOT/'output/unreal/exterior-20261002-r43b-garden-boundary-two-camera-candidate-r31'
OUT = V/'r43b-original-garden-boundaries-two-view-comparison-r31-r1.json'
PAGE = V/'r43b-original-garden-boundaries-two-view-comparison-r31-r1.html'
REQUEST_PATH = ROOT/'output/unreal/exterior-context-parcel-boundary-20261002-r43-paired-review-r31/capture-request-bound-r1.json'
REQUEST_SCHEMA = 'brezi-closed-four-original-authored-boundary-paired-review-request-r31'
ROOT_REVIEW_PIN = {'path': str(ROOT/'output/unreal/exterior-context-parcel-boundary-20261002-r43-image-base-selection-r1/root-four-original-image-review-r1.json'),
    'sha256': '4386ac5a7e06c0e2ccac1aa03816e7720ecf65ffed9a9a7df2ea235f36f7ee56', 'bytes': 9984}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def read(p):
    return json.loads(Path(p).read_text())


def pin(p):
    p = Path(p).resolve()
    data = p.read_bytes()
    return {'path': str(p), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def checked(row):
    require(isinstance(row, dict) and set(row) == {'path', 'sha256', 'bytes'}, 'Exact original regular-file pin required')
    p = Path(row['path'])
    require(p.is_absolute() and p.resolve() == p and p.is_file() and not p.is_symlink() and pin(p) == row,
            'Original pinned capture changed: '+str(p))
    return p


def differences(a, b, key=''):
    if type(a) is not type(b):
        return [key]
    if isinstance(a, dict):
        return [key+'.'+k for k in sorted(set(a)^set(b))] + [p for k in sorted(set(a)&set(b))
            for p in differences(a[k], b[k], key+'.'+k)]
    if isinstance(a, list):
        return [key] if len(a) != len(b) else [p for i, (x, y) in enumerate(zip(a, b)) for p in differences(x, y, key+'/'+str(i))]
    same = a == b
    if type(a) is float and a == b == 0:
        same = math.copysign(1, a) == math.copysign(1, b)
    return [] if same else [key]


def static_pp(value):
    # Exclude only explicitly recorded dynamic observations, never a policy cvar.
    result = copy.deepcopy(value)
    for key in ('observedMainViews', 'viewFamilyFrameNumber'):
        result.pop(key, None)
    for key in ('observedRenderThreadSamples', 'viewFamilyFrameNumber', 'linearPreExposure', 'exposureEV'):
        result['renderThreadPreExposure'].pop(key, None)
    for key in ('observedRenderThreadSamples', 'viewFamilyFrameNumber', 'projectionJitterX', 'projectionJitterY'):
        result['renderThreadAntiAliasing'].pop(key, None)
    return result


def closed_suite(row, owner):
    suite = read(checked(row))
    require(suite['owner'] == owner and suite['status'] == 'editor-game-suite-recorded-awaiting-independent-visual-review'
            and suite['sourceInputsUnchanged'] is True and suite['errors'] == []
            and suite['nativeIdleAfter']['activeNativeProcesses'] == []
            and suite['requestedBuild'] == 'Development' and suite['requestedTransport'] == 'UnrealEditor -game'
            and suite['warmupFrames'] == 2400 and suite['benchmarkFrames'] == 300,
            'Only the actual fully closed source-exact Editor capture suite accepted')
    before, after = (read(checked({k: suite[field][k] for k in ('path', 'sha256', 'bytes')}))
                     for field in ('inputClosureBefore', 'inputClosureAfter'))
    require(isinstance(before, dict) and before == after
            and len(before) == suite['inputClosureBefore']['fileCount'] == suite['inputClosureAfter']['fileCount']
            and sum(row['bytes'] for row in before.values()) == suite['inputClosureBefore']['logicalBytes'],
            'Recorded before/after source preservation must be complete')
    return suite


def capture(suite, view, expected=None):
    matches = [c for c in suite['cases'] if c['view'] == view]
    require(len(matches) == 1, 'Exactly one original capture for each fixed view required')
    case = matches[0]
    require(case['outcome'] == {'code': 0, 'signal': None, 'pid': case['processId']}
            and case['shaderAndLoadErrors'] == [] and case['nativeEvidenceValidated'] is True
            and case['sourceFovNativeReadbackAvailable'] is False,
            'Actual native0/error-free original capture required')
    process = pin(case['processReceiptPath'])
    require(read(process['path']) == case, 'Saved original case receipt differs from closed suite')
    png = pin(case['originalCapturePath']); runtime = pin(case['originalRuntimePath'])
    require(png['sha256'] == case['originalCaptureSha256'] and runtime['sha256'] == case['originalRuntimeSha256'],
            'Actual unchanged original image/runtime identity required')
    header = Path(png['path']).read_bytes()[:24]
    require(header[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', header[16:24]) == (1920, 1080),
            'Full unchanged original1920x1080 PNG required')
    r = read(runtime['path'])
    require(r['processId'] == case['processId'] and r['status'] == 'capture-complete'
            and r['activeView'] == view and r['buildConfiguration'] == 'Development'
            and r['screenshotSaved'] is True and r['screenshotPixels'] == [1920, 1080]
            and r['warmupFrames'] == 2400 and r['requestedBenchmarkFrames'] == 300,
            'Actual corresponding camera/runtime capture required')
    if expected:
        require(png == expected['originalPng'] and runtime == expected['originalRuntime']
                and process == expected['process'] and case['processId'] == expected['nativePid'],
                'Exactly the image-selected immediate native-parent original required')
    return {'view': view, 'processId': case['processId'], 'process': process, 'originalPng': png,
            'originalRuntime': runtime, 'sourceCamera': case['sourceCamera'],
            'capturedSourceRecords': suite['inputClosureBefore']['fileCount'], 'runtime': r}


def matched(before, after):
    a, b = before['runtime'], after['runtime']
    pairs = {'authoredCamera': (before['sourceCamera'], after['sourceCamera']),
             'observedCamera': (a['walking']['presentationCamera'], b['walking']['presentationCamera']),
             **{k: (a[k], b[k]) for k in ('renderSettings', 'lighting', 'exteriorLighting')},
             'staticPostProcessIncludingPreExposurePolicy': (static_pp(a['finalViewPostProcessSettings']), static_pp(b['finalViewPostProcessSettings']))}
    mismatch = {k: differences(x, y, k) for k, (x, y) in pairs.items()}
    require(all(not row for row in mismatch.values()), 'Matched camera/render/static-light/postprocess policy differs: '+str(mismatch))
    exposure = [r['finalViewPostProcessSettings']['renderThreadPreExposure'] for r in (a, b)]
    ev = [v['exposureEV'] for v in exposure]
    return {'exactCameraRenderStaticLightAndStaticPostProcess': True, 'differences': mismatch,
            'unlockedExposure': {'beforeEV': ev[0], 'afterEV': ev[1], 'deltaEV': ev[1]-ev[0],
                'beforeLinearPreExposure': exposure[0]['linearPreExposure'], 'afterLinearPreExposure': exposure[1]['linearPreExposure'],
                'fixedExposureComparison': False},
            'excludedDynamicPostProcessObservations': ['observedMainViews', 'viewFamilyFrameNumber',
                'renderThreadPreExposure.observedRenderThreadSamples', 'renderThreadPreExposure.viewFamilyFrameNumber',
                'renderThreadPreExposure.linearPreExposure', 'renderThreadPreExposure.exposureEV',
                'renderThreadAntiAliasing.observedRenderThreadSamples', 'renderThreadAntiAliasing.viewFamilyFrameNumber',
                'renderThreadAntiAliasing.projectionJitterX', 'renderThreadAntiAliasing.projectionJitterY'],
            'observedEditorMeanFrameIntervalMs': [r['frameInterval']['meanMs'] for r in (a, b)],
            'observedApplicationForegroundSamples': [r['focusDuringBenchmark']['applicationForegroundSamples'] for r in (a, b)],
            'observedBenchmarkSamples': [r['frameInterval']['sampleCount'] for r in (a, b)],
            'performanceAccepted': False, 'nativeFovDirectReadbackAvailable': False,
            'dynamicCloudOrTimePhaseMatched': False, 'specificBoundaryPixelCauseIndependentlyIsolated': False}


def page_for(result):
    def url(row):
        return quote(os.path.relpath(row['path'], V), safe='/')
    titles = {'exterior-context-yard-572063-close-r18': 'Susedný dvor – detail',
              'exterior-neighborhood-ground-r38': 'Okolie z úrovne očí'}
    blocks = []
    for pair in result['pairs']:
        before, after = pair['before']['originalPng'], pair['after']['originalPng']
        ev = pair['match']['unlockedExposure']['deltaEV']
        blocks.append(f'''<section><h2>{html.escape(titles[pair['view']])}</h2><p>{html.escape(pair['findings']['visibleFindingSk'])}</p>
<div class="pair" style="--split:50%"><img src="{url(before)}" alt="Pôvodný snímok R39 pred úpravou"><img class="after" src="{url(after)}" alt="Pôvodný snímok R43 po úprave"><span class="divider"></span></div>
<label>Pred úpravou ↔ Po úprave <input type="range" min="0" max="100" value="50" aria-label="Rozdelenie pôvodných snímok pred a po"></label>
<p><a href="{url(before)}">Pôvodný snímok pred úpravou</a> · <a href="{url(after)}">Pôvodný snímok po úprave</a> · zmena automatickej expozície ΔEV {ev:+.6f}</p></section>''')
    return '''<!doctype html><html lang="sk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Otvorené hranice záhrad – pôvodné snímky pred a po</title>
<style>body{margin:0;background:#13191d;color:#e9f0ef;font:16px/1.5 system-ui}main{max-width:1280px;margin:auto;padding:24px}h1{font-size:28px}h2{font-size:18px}p{max-width:1050px}.pair{position:relative;aspect-ratio:16/9;background:#20282a;overflow:hidden}.pair img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}.after{clip-path:inset(0 0 0 var(--split))}.divider{position:absolute;left:var(--split);top:0;bottom:0;border-left:2px solid white}section{margin:30px 0 50px}label{display:flex;gap:16px;align-items:center;margin:12px 0}input{flex:1;min-width:80px}a{color:#a6dcc8}.limit{padding:16px;background:#24302f;border-radius:8px}</style>
<main><h1>Otvorené hranice záhrad – pôvodné snímky pred a po</h1><p class="limit">Nízke otvorené oplotenie pridalo štruktúru vzdialenejšiemu dvoru. Celková fotorealistickosť zatiaľ nedosiahnutá. Zhodné kamery a nastavenia svetla; automatická expozícia zostala voľná. Ide o autorský vizuálny návrh, bez tvrdenia o právnych hraniciach alebo kolíziách.</p>
''' + '\n'.join(blocks) + '''<p>Štyri pôvodné PNG zostali nezmenené. Posuvníky iba odkrývajú pôvodné súbory. Výkon, Shipping ani aktívna verzia týmto porovnaním nie sú schválené; časová fáza oblakov a priame čítanie FOV nie sú overené.</p></main><script>document.querySelectorAll('section').forEach(s=>s.querySelector('input').addEventListener('input',e=>s.querySelector('.pair').style.setProperty('--split',e.target.value+'%')));</script></html>'''


def validate_native_receipts(request, candidate):
    native = read(checked(request['nativeReport'])); process = read(checked(request['nativeProcess']))
    audit = read(checked(request['nativeCurrentByteAudit']))
    require(request['nativeReport']['sha256'] == '802756b95c06d01351cbdaee7b439ab10728e04f2d884fb971f111e735e9b5d4'
        and request['nativeProcess']['sha256'] == '70bb0aa0c745cab27f98169dc25f73c17f94f749e0431250e1be6c5fe283dbac'
        and request['nativeCurrentByteAudit']['sha256'] == 'd4dd77489d5e26e533b4f94cd24a15463c1837171f98ee32ccf5bd07b97eb482',
        'Exact actual R43b native/process/current-byte pins required')
    require(native['nativeProcessId'] == audit['nativeProcessId'] == 44798 and native['schemaVersion'] == 2
        and native['owner'] == 'scripts/unreal/exterior-context-parcel-boundary-native-r43-r2.py'
        and native['status'] == 'verified-saved-three-authored-open-boundary-masters'
        and native['nativeApplied'] is True and native['savedMapUnloadedReloaded'] is True
        and native['sourceInputsUnchanged'] is True and native['oldActorInstanceMaterialOrCollisionSettersCalled'] is False,
        'Only the actual successfully saved authored R43b overlay required')
    require(audit['schema'] == 'brezi-r43b-root-saved-authored-open-boundaries-byte-audit-r2'
        and audit['schemaVersion'] == 2 and audit['nativeReport'] == request['nativeReport']
        and audit['nativeProcess'] == request['nativeProcess']
        and audit['exitCode'] == audit['rootSessionClosedExitCode'] == 0 and audit['nativeIdleAfter'] == []
        and audit['all1343FrozenSourcePinsExact'] is True and audit['all1332PreflightSourcePinsExact'] is True
        and process['reportSha256'] == request['nativeReport']['sha256'] and process['sourcePinsUnchangedAfterNative'] is True,
        'Exact closed process/current-byte audit must remain distinct from visual evidence')
    parent = native['baseNativeReport']
    require(parent == request['beforeNativeReport']
        and parent['sha256'] == '118f451095730e2ff0e62304d959626d4a81be53f03e41dd2229fe91831f4da5',
        'R39c must be the actual immediate native parent')
    checked(parent)
    evidence = candidate['nativeSourceEvidence']
    require(evidence['sourceNativeReport'] == request['nativeReport'] and evidence['sourceNativeProcess'] == request['nativeProcess']
        and evidence['summary']['wholeActorCounterfactualValidated'] is True
        and evidence['summary']['savedActors'] == 5371 and evidence['summary']['fullHismComponents'] == 2329
        and evidence['summary']['fullHismInstances'] == 678205
        and evidence['summary']['fullNativeF32PositionUv0SectionWindingProofTriangles'] == 12566,
        'Actual camera clone must consume the closed saved R43b source receipt')
    for key in ('nativeReceipt', 'sourceConsumer', 'sourceReaderReadiness'):
        checked(evidence[key])
    require(evidence['cameraStageReceipt'] == evidence['nativeReceipt']['path'], 'Camera stage receipt differs')
    stage = read(evidence['nativeReceipt']['path'])
    require(stage['sourceNativeReport'] == request['nativeReport'] and stage['sourceNativeProcess'] == request['nativeProcess']
        and stage['sourceCurrentByteAudit'] == request['nativeCurrentByteAudit']
        and stage['exactDonorFileCopiedWithoutReserialization'] is True
        and stage['changedContentFiles'] == ['Data/viewpoints.json'] and stage['sceneMapChanged'] is False
        and stage['nativeExecuted'] is False and stage['nativeCameraRuntimeVerified'] is False,
        'Data-only staging does not substitute for actual camera runtime or visual proof')
    return native


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--request', required=True, type=Path); args = parser.parse_args()
    require(args.request.resolve() == REQUEST_PATH and ROOT_REVIEW_PIN is not None,
        'Actual root four-original review and exact bound request are required before publication')
    request = read(args.request)
    require(request['schema'] == REQUEST_SCHEMA and request['schemaVersion'] == 1
        and request['rootCaptureClosedExitCode'] == 0 and request['rootProducerPeerAccepted'] is True
        and request['independentProducerPeerAccepted'] is True, 'Gallery producer peers/closed capture are pending')
    require(not OUT.exists() and not PAGE.exists(), 'Only exclusive new gallery outputs may be published')
    require(pin(PARENT_PRESENTATION_SOURCE)['sha256'] == PARENT_PRESENTATION_SHA,
        'Frozen presentation-kernel source changed; it must never be executed here')
    require(checked(request['beforeSuite']) == BEFORE_SUITE and request['beforeSuite']['sha256'] == BEFORE_SUITE_SHA
        and checked(request['afterSuite']) == AFTER_SUITE and request['afterSuite']['sha256'] == AFTER_SUITE_SHA,
        'Only the two exact actual original suites are allowed')
    before_suite = closed_suite(request['beforeSuite'], 'scripts/unreal/exterior-editor-qa-r30-camera.mjs')
    after_suite = closed_suite(request['afterSuite'], 'scripts/unreal/exterior-editor-qa-r31-camera.mjs')
    require(before_suite['source'] == str(BEFORE_SOURCE) and after_suite['source'] == str(AFTER_SOURCE)
        and before_suite['requestedViews'] == after_suite['requestedViews'] == list(VIEWS)
        and before_suite['requestedProfile'] == after_suite['requestedProfile'] == 'cinematic'
        and before_suite['requestedOutput'] == after_suite['requestedOutput'] == 'retina', 'Exact fixed two-view captures required')
    native = validate_native_receipts(request, after_suite)
    root_review = read(checked(request['rootFourOriginalReview']))
    require(request['rootFourOriginalReview'] == ROOT_REVIEW_PIN, 'Exact actual root review required')
    require(root_review['schema'] == 'brezi-r43b-root-four-original-fixed-camera-image-review-r1'
        and root_review['schemaVersion'] == 1 and root_review['rootSessionClosedExitCode'] == 0
        and root_review['allFourOriginalWholePngsViewed'] is True and root_review['pixelsEdited'] is False
        and root_review['beforeSuite'] == request['beforeSuite'] and root_review['afterSuite'] == request['afterSuite']
        and root_review['independentVisualReview'] == request['independentReview'], 'Root review must bind these exact two original pairs')
    review = request['producerOriginalReview']
    require(review['reviewer'] == 'infill_validator' and review['allFourWholeOriginalPngsViewed'] is True
        and review['pixelsEdited'] is False and set(review['findings']) == set(VIEWS), 'Actual independent original-image review required')
    peer = read(checked(request['independentReview']))
    require(request['independentReview']['sha256'] == 'f4b59c33b6b5b88d2c914305d3b2f7cdac3bcec7d62c61f83c41b71d06db79e2'
        and peer['reviewer'] == 'infill_review' and len(peer['pairs']) == 2
        and all(p['originalImagesPersonallyViewedAtFull1920x1080'] is True for p in peer['pairs'])
        and peer['sourceGeometryOrImagesModifiedByReviewer'] is False
        and peer['newRendersOrHistoricalConsumersReexecuted'] is False
        and peer['wholeScenePhotorealismAccepted'] is False and peer['performanceAccepted'] is False
        and peer['shippingVerified'] is False and peer['activeOutputPromoted'] is False,
        'Second reviewer must bind all four unchanged actual original PNGs')
    for item in (root_review, review):
        require(item['fullPhotorealismAccepted'] is False and item['performanceAccepted'] is False
            and item['shippingVerified'] is False and item['activeOutputPromoted'] is False,
            'Original image reviews must retain their scope/acceptance limits')
    pairs = []
    for view, pids in zip(VIEWS, ((12723, 53696), (13376, 54206))):
        before, after = capture(before_suite, view), capture(after_suite, view)
        require((before['processId'], after['processId']) == pids
            and review['originalPngs'][view] == [before['originalPng'], after['originalPng']], 'Exact four originally viewed PNGs required')
        peer_pair = next(p for p in peer['pairs'] if p['view'] == view)
        root_pair = next(p for p in root_review['pairs'] if p['view'] == view)
        require(root_pair['beforeOriginalPng'] == before['originalPng'] and root_pair['afterOriginalPng'] == after['originalPng']
            and root_pair['beforeOriginalRuntime'] == before['originalRuntime']
            and root_pair['afterOriginalRuntime'] == after['originalRuntime']
            and root_pair['nativeProcess'] == after['process'] and root_pair['nativeProcessId'] == pids[1]
            and root_pair['exitCode'] == 0 and root_pair['originalWholeBeforeAndAfterPngViewedByRoot'] is True,
            'Root exact original/runtime/process pairing differs')
        require(peer_pair['baseline']['originalImage'] == before['originalPng']
            and peer_pair['candidate']['originalImage'] == after['originalPng']
            and peer_pair['baseline']['runtime'] == before['originalRuntime']
            and peer_pair['candidate']['runtime'] == after['originalRuntime']
            and peer_pair['baseline']['nativeProcessId'] == pids[0]
            and peer_pair['candidate']['nativeProcessId'] == pids[1], 'Second review original/runtime bindings differ')
        pair = {'view': view, 'before': {k: v for k, v in before.items() if k != 'runtime'},
            'after': {k: v for k, v in after.items() if k != 'runtime'}, 'match': matched(before, after),
            'findings': review['findings'][view]}
        pairs.append(pair)
    consumed = [request[k] for k in ('beforeSuite', 'afterSuite', 'beforeNativeReport', 'nativeReport', 'nativeProcess',
        'nativeCurrentByteAudit', 'rootFourOriginalReview', 'independentReview')]
    consumed += [p[side][key] for p in pairs for side in ('before', 'after') for key in ('process', 'originalPng', 'originalRuntime')]
    result = {'schema': 'brezi-four-original-authored-open-boundary-matched-pairs-r31', 'schemaVersion': 1, 'owner': OWNER,
        'createdAt': datetime.now(timezone.utc).isoformat(), 'producer': pin(ROOT/OWNER), 'request': pin(args.request),
        'presentationKernelSourceOnly': pin(PARENT_PRESENTATION_SOURCE), 'immediateNativeParent': native['baseNativeReport'],
        'candidateNativeReport': request['nativeReport'], 'candidateCurrentByteAudit': request['nativeCurrentByteAudit'],
        'beforeSuite': request['beforeSuite'], 'afterSuite': request['afterSuite'],
        'rootFourOriginalReview': request['rootFourOriginalReview'], 'independentReview': request['independentReview'],
        'producerOriginalReview': review, 'pairs': pairs, 'allFourOriginalPngPixelsUnchanged': True,
        'allSixFenceSegmentsAndTwoGatesIndividuallyVisibleVerified': False, 'nativeCollisionOrContactVerified': False,
        'legalFencePlacementOrOwnershipClaimed': False, 'sourceInventoriesOrHistoricalNativeProofsRerun': False,
        'nativeOrGpuLaunchedByReview': False, 'currentStdoutLogsRevalidatedByReview': False,
        'specificPixelCausalityClaimed': False, 'nativeAppearanceAccepted': False,
        'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'shippingVerified': False,
        'packageVerified': False, 'activeOutputPromoted': False}
    for row in consumed: checked(row)
    with OUT.open('x') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, allow_nan=False); f.write('\n')
    with PAGE.open('x') as f: f.write(page_for(result))
    for row in consumed: checked(row)
    print(json.dumps({'json': pin(OUT), 'html': pin(PAGE)}))


if __name__ == '__main__':
    main()
