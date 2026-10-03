"""Publish two matched, unchanged original PNG pairs only after native closure.

No Unreal, image edits, asset inventory replay, or historical producer calls.
This review consumes the closed capture receipts and their actual runtime facts.
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
OWNER = 'scripts/unreal/exterior-neighbor-props-paired-review-r30.py'
V = ROOT/'output/unreal/exterior-validation-20260930-r1'
SELECTION = ROOT/'output/unreal/exterior-soft-ground-20261002-r38-image-base-selection-r1/root-image-base-selection-r1.json'
SELECTION_SHA = 'b2c0ee46147b88824a2214a074c6c745d47454a118e4c151cf494f92c4304d4b'
SUITE = V/'qa/editor-pilot-r39c-whole-original-neighbor-props-r30-1790963761054-81YFO4/editor-pilot-suite.json'
VIEWS = ('exterior-context-yard-572063-close-r18', 'exterior-neighborhood-ground-r38')
SOURCE = ROOT/'output/unreal/exterior-20261002-r39c-neighbor-props-two-camera-candidate-r30'
OUT = V/'r39c-original-neighbor-props-two-view-comparison-r30-r1.json'
PAGE = V/'r39c-original-neighbor-props-two-view-comparison-r30-r1.html'
REQUEST_SCHEMA = 'brezi-closed-four-original-neighbor-props-paired-review-request-r30'


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
                'Exactly the image-selected immediate R38 base original required')
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
            'dynamicCloudOrTimePhaseMatched': False, 'specificPropPixelCauseIndependentlyIsolated': False}


def page_for(result):
    def url(row):
        return quote(os.path.relpath(row['path'], V), safe='/')
    titles = {'exterior-context-yard-572063-close-r18': 'Susedný dvor – detail',
              'exterior-neighborhood-ground-r38': 'Okolie z úrovne očí'}
    captions = {
        'exterior-context-yard-572063-close-r18': 'Hadica na fasáde a prázdny hlinený kvetináč pridali drobný znak používaného dvora. Ich osadenie pôsobí vierohodne, snímka však neoveruje kontakt ani kolízie. Rovná sivá plocha, jednoduché okná a dvere, pravidelná strecha, riedka výsadba a otvorené hranice parciel stále pôsobia počítačovo.',
        'exterior-neighborhood-ground-r38': 'Širší pohľad zachováva domy, stromy aj terén. Pri strednom dome sú čitateľné hadica a prázdny kvetináč; viditeľnosť všetkých šiestich zostáv nie je overená. Opakované jednoduché domy, otvorené parcely, plošný zelenohnedý terén a koruny stromov zatiaľ bránia fotorealistickému výsledku.'}
    blocks = []
    for pair in result['pairs']:
        before, after = pair['before']['originalPng'], pair['after']['originalPng']
        ev = pair['match']['unlockedExposure']['deltaEV']
        caption = html.escape(captions[pair['view']])
        blocks.append(f'''<section><h2>{html.escape(titles[pair['view']])}</h2><p>{caption}</p>
<div class="pair" style="--split:50%"><img src="{url(before)}" alt="Pôvodný snímok pred úpravou"><img class="after" src="{url(after)}" alt="Pôvodný snímok po úprave"><span class="divider"></span></div>
<label>Pred úpravou ↔ Po úprave <input type="range" min="0" max="100" value="50" aria-label="Rozdelenie porovnania"></label>
<p><a href="{url(before)}">Pôvodný snímok pred úpravou</a> · <a href="{url(after)}">Pôvodný snímok po úprave</a> · zmena expozície ΔEV {ev:+.6f}</p></section>''')
    return '''<!doctype html><html lang="sk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Susedné dvory – pôvodné snímky pred a po</title>
<style>body{margin:0;background:#13191d;color:#e9f0ef;font:16px/1.5 system-ui}main{max-width:1280px;margin:auto;padding:24px}h1{font-size:28px}h2{font-size:18px}p{max-width:1050px}.pair{position:relative;aspect-ratio:16/9;background:#20282a;overflow:hidden}.pair img{position:absolute;inset:0;width:100%;height:100%;object-fit:contain}.after{clip-path:inset(0 0 0 var(--split))}.divider{position:absolute;left:var(--split);top:0;bottom:0;border-left:2px solid white}section{margin:30px 0 50px}label{display:flex;gap:16px;align-items:center;margin:12px 0}input{flex:1;min-width:80px}a{color:#a6dcc8}.limit{padding:16px;background:#24302f;border-radius:8px}</style>
<main><h1>Susedné dvory – pôvodné snímky pred a po</h1><p class="limit">Doplnky dvory oživili. Celková fotorealistickosť zatiaľ nedosiahnutá; výkon a aktívna verzia ešte neoverené. Zhodné kamery a svetlo; automatická expozícia. Časová fáza oblakov nie je overená.</p>
''' + '\n'.join(blocks) + '''<p>Pôvodné snímky PNG zostali nezmenené. Posuvníky iba odkrývajú dva pôvodné súbory.</p></main><script>document.querySelectorAll('section').forEach(s=>s.querySelector('input').addEventListener('input',e=>s.querySelector('.pair').style.setProperty('--split',e.target.value+'%')));</script></html>'''


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--request', required=True, type=Path); args = parser.parse_args()
    request = read(args.request)
    require(request.get('schema') == REQUEST_SCHEMA and request.get('candidateSuite') is not None
            and request.get('independentReview') is not None and request.get('rootCaptureClosedExitCode') == 0,
            'Unbound gallery: actual closed captures and independent four-original review are pending')
    require(not OUT.exists() and not PAGE.exists(), 'New paired publication outputs only')
    selection_pin = pin(SELECTION); require(selection_pin['sha256'] == SELECTION_SHA, 'Immediate image-selected R38 base receipt changed')
    selection = read(SELECTION); baseline = {r['view']: r for r in selection['actualCameraCaptures'] if r['view'] in VIEWS}
    require(set(baseline) == set(VIEWS), 'Both exact baseline originals required')
    candidate = closed_suite(request['candidateSuite'], 'scripts/unreal/exterior-editor-qa-r30-camera.mjs')
    require(checked(request['candidateSuite']) == SUITE and candidate['source'] == str(SOURCE)
            and candidate['requestedViews'] == list(VIEWS), 'Only exact root-owned two-view R39 capture suite required')
    native = read(checked(request['nativeReport'])); audit = read(checked(request['nativeCurrentByteAudit']))
    require(native['nativeProcessId'] == 94572 and native['schemaVersion'] == 3
            and native['nativeApplied'] is True and native['savedMapUnloadedReloaded'] is True
            and native['sourceInputsUnchanged'] is True and audit['nativeReport'] == request['nativeReport']
            and audit['exitCode'] == 0 and audit['all1294FrozenSourcePinsExact'] is True,
            'Exact closed saved R39 base and current byte-audit required')
    root_review = read(checked(request['rootFourOriginalReview']))
    next_selection = read(checked(request['rootNextScopedBaseSelection']))
    require(root_review['allFourOriginalWholePngsViewed'] is True and root_review['pixelsEdited'] is False
            and root_review['rootSessionClosedExitCode'] == 0
            and next_selection['sourceNativeReport'] == request['nativeReport']
            and next_selection['localPropCueAcceptedForNextTrialOnly'] is True
            and next_selection['fullPhotorealismAccepted'] is False
            and next_selection['activeOutputPromoted'] is False,
            'Exact root original-image review and narrow next-trial selection required')
    review = request['independentReview']
    require(review['reviewer'] == 'infill_review' and review['allFourWholeOriginalPngsViewed'] is True
            and review['fullPhotorealismAccepted'] is False and review['performanceAccepted'] is False
            and set(review['findings']) == set(VIEWS), 'Actual independent original-image review required')
    pairs = []
    for view in VIEWS:
        old = closed_suite(baseline[view]['suite'], 'scripts/unreal/exterior-editor-qa-r29-r3-camera.mjs')
        before, after = capture(old, view, baseline[view]), capture(candidate, view)
        require(review['originalPngs'][view] == [before['originalPng'], after['originalPng']], 'Review must bind both exact original images')
        pair = {'view': view, 'before': {k: v for k, v in before.items() if k != 'runtime'},
                'after': {k: v for k, v in after.items() if k != 'runtime'}, 'match': matched(before, after), 'findings': review['findings'][view]}
        pairs.append(pair)
    result = {'schema': 'brezi-four-original-neighbor-props-matched-pairs-r30', 'schemaVersion': 1, 'owner': OWNER,
        'createdAt': datetime.now(timezone.utc).isoformat(), 'producer': pin(ROOT/OWNER), 'request': pin(args.request),
        'immediateNativeParent': selection['selectedNativeReport'], 'candidateNativeReport': request['nativeReport'],
        'candidateCurrentByteAudit': request['nativeCurrentByteAudit'], 'candidateSuite': request['candidateSuite'],
        'rootFourOriginalReview': request['rootFourOriginalReview'], 'rootNextScopedBaseSelection': request['rootNextScopedBaseSelection'],
        'imageSelectedParent': selection_pin, 'pairs': pairs, 'independentReview': review,
        'allFourOriginalPngPixelsUnchanged': True, 'wholeSixAssembliesIndividuallyVisibleVerified': False,
        'sourceInventoriesOrHistoricalNativeProofsRerun': False, 'nativeOrGpuLaunchedByReview': False,
        'currentStdoutLogsRevalidatedByReview': False, 'specificPixelCausalityClaimed': False,
        'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False,
        'shippingVerified': False, 'packageVerified': False, 'activeOutputPromoted': False}
    with OUT.open('x') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, allow_nan=False); f.write('\n')
    with PAGE.open('x') as f:
        f.write(page_for(result))
    print(json.dumps({'json': pin(OUT), 'html': pin(PAGE)}))


if __name__ == '__main__':
    main()
