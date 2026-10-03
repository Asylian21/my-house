"""Publish only original, closed R28 images: two fixed-camera pairs and one overview.

The capture request remains null until actual suites close. No Unreal launch,
image processing, historical producer replay or source-project validation replay.
"""
import argparse
import datetime
import hashlib
import html
import json
import math
import os
from pathlib import Path
import struct
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-yard-paired-review-r28.py'
SCHEMA = 'brezi-original-selected-garden-yard-review-r28'
V = ROOT/'output/unreal/exterior-validation-20260930-r1'
DIRECT = ROOT/'output/unreal/exterior-20261002-r37b'
CLOSE = ROOT/'output/unreal/exterior-20261002-r37b-yard-close-candidate-r28'
VIEWS = ('exterior-garden', 'exterior-neighborhood', 'exterior-context-yard-572063-close-r18')
TITLES = {'exterior-garden': 'Záhrada', 'exterior-neighborhood': 'Celé okolie · samostatný prehľad',
          'exterior-context-yard-572063-close-r18': 'Susedný dvor · detail vstupu'}
COMPARATOR_ROLES = {
    'exterior-garden': {'role': 'immediate-selected-native-parent-r36b', 'label': 'Zvolený pôvodný základ R36 · záhrada'},
    'exterior-neighborhood': {'role': 'no-matched-original-comparator', 'label': None},
    'exterior-context-yard-572063-close-r18': {
        'role': 'saved-yard-donor-r35b-not-immediate-garden-native-parent',
        'label': 'Pôvodný uložený donor dvora R35 · rovnaká kamera'},
}
BASELINES = {
    'exterior-garden': {
        'suitePath': str(V/'qa/editor-pilot-r36b-original-periwinkle-r27-1790941328543-iu83Ja/editor-pilot-suite.json'),
        'suiteSha256': 'e7d8879409b9a46f8b28d32f23f51327d81d76f05b0d3dd9b82b04be00015454',
        'owner': 'scripts/unreal/exterior-editor-qa-r27.mjs', 'source': str(ROOT/'output/unreal/exterior-20261002-r36b'),
        'processId': 49987, 'originalPngSha256': '901ae6e5b48b0fe9c8fc0dfca00e592d2209b5f09b07f299b0fd2d543e75527d',
        'originalRuntimeSha256': '31351a0017aaca965986787b2c4587973c849114c9401abb2360f176f833ee09',
    },
    'exterior-neighborhood': None,
    'exterior-context-yard-572063-close-r18': {
        'suitePath': str(V/'qa/editor-pilot-r35b-yard572063-repair-r26-1790937844652-UluAfx/editor-pilot-suite.json'),
        'suiteSha256': 'ca89bf4eee78d176bd497f4063ee9e88aa8f3408c9bf7c5c383de3cd23415748',
        'owner': 'scripts/unreal/exterior-editor-qa-r26.mjs',
        'source': str(ROOT/'output/unreal/exterior-20261002-r35b-yard-close-candidate-r26'),
        'processId': 42228, 'originalPngSha256': '39826ba5eb181371ee2a98bdc1f45e4c4dfd1e47b83d9ef61e3ceccaedd98184',
        'originalRuntimeSha256': 'b0abd4fc59c5bb80cc230a548a05ddce84e4f48b8e3a9bc1dec61ac5b41a64a0',
    },
}
NATIVE_REPORT = DIRECT/'garden-yard-integration-native-report-r2.json'
NATIVE_SHA = 'f589c0d813ccfc35eba928a91a4545e03b159622fffa7ae2ba247545053c4532'
BYTE_AUDIT = DIRECT/'root-native-success-byte-audit-r37b-r2.json'
AUDIT_SHA = '5e2b2e057436049d4eabd34f3420d94b351c519094bfaed44cb10ddf24a56bf2'
ROOT_REVIEW = ROOT/'output/unreal/exterior-garden-yard-20261002-r37-image-base-selection-r1/root-image-base-selection.json'
ROOT_REVIEW_SHA = '530cac388ce376202dfd086bbcd1c4a02b30e232b772695218b67bfdb24d55a8'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def read(path):
    return json.loads(Path(path).read_text())


def pin(path):
    p = Path(path).resolve()
    h = hashlib.sha256()
    with p.open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return {'path': str(p), 'sha256': h.hexdigest(), 'bytes': p.stat().st_size}


def fixed(path, digest):
    require(isinstance(digest, str) and len(digest) == 64, 'Actual immutable SHA256 required')
    row = pin(path)
    require(row['sha256'] == digest, 'Fixed original artifact changed: '+str(path))
    return row


def write(path, value):
    with Path(path).open('x') as f:
        json.dump(value, f, indent=2, ensure_ascii=False, allow_nan=False)
        f.write('\n')


def difference(a, b, prefix=''):
    if type(a) is not type(b):
        return [{'path': prefix, 'before': a, 'after': b}]
    if isinstance(a, dict):
        rows = []
        for key in sorted(set(a)|set(b)):
            path = prefix+'.'+key if prefix else key
            if key not in a or key not in b:
                rows.append({'path': path, 'before': a.get(key), 'after': b.get(key), 'presenceChanged': True})
            else:
                rows.extend(difference(a[key], b[key], path))
        return rows
    if isinstance(a, list):
        if len(a) != len(b):
            return [{'path': prefix, 'before': a, 'after': b}]
        return [row for i, (x, y) in enumerate(zip(a, b)) for row in difference(x, y, prefix+'['+str(i)+']')]
    # Preserve an observed signed-zero difference rather than hiding it.
    equal = a == b and not (isinstance(a, float) and a == 0 and math.copysign(1, a) != math.copysign(1, b))
    return [] if equal else [{'path': prefix, 'before': a, 'after': b}]


def static_pp(pp):
    result = {k: v for k, v in pp.items() if k not in
              ('observedMainViews', 'viewFamilyFrameNumber', 'renderThreadPreExposure', 'renderThreadAntiAliasing')}
    result['renderThreadAntiAliasing'] = {k: v for k, v in pp['renderThreadAntiAliasing'].items() if k not in
        ('observedRenderThreadSamples', 'viewFamilyFrameNumber', 'projectionJitterX', 'projectionJitterY')}
    return result


def load_stdout_observations(row):
    if row is None:
        return None, {}
    receipt_pin = fixed(row['path'], row['sha256'])
    require(receipt_pin['bytes'] == row['bytes'], 'Observed stdout receipt size changed')
    receipt = read(receipt_pin['path'])
    require(receipt['schema'] == 'brezi-observed-original-capture-stdout-append-r28'
            and receipt['owner'] == OWNER and receipt['originalLogsEdited'] is False
            and receipt['nativeOrGpuLaunched'] is False, 'Own read-only stdout observation required')
    entries = {x['stdoutPath']: x for x in receipt['entries']}
    require(len(entries) == len(receipt['entries']) <= 5, 'Unique bounded observed stdout cases required')
    return receipt_pin, entries


def original_log(case, suite_pin, role, observations):
    field = 'stdoutPath' if role == 'stdout' else 'runtimeLogPath'
    current = pin(case[field])
    require(Path(current['path']).is_relative_to(Path(suite_pin['path']).parent), 'Log outside its own suite')
    recorded = case['rawLogHashes'][role]
    if (current['sha256'], current['bytes']) == (recorded['sha256'], recorded['bytes']):
        return {'current': current, 'recordedAtProcessClosure': recorded, 'wholeLogUnchanged': True,
                'recordedPrefixExact': True, 'observedLaterAppend': None}
    require(role == 'stdout' and current['path'] in observations, 'Unexpected original runtime log change')
    row = observations[current['path']]
    require(row['suite'] == suite_pin and row['processId'] == case['processId'] and row['view'] == case['view']
            and row['recordedAtProcessClosure'] == recorded and row['current'] == current,
            'Exactly pinned same-case stdout observation required')
    data = Path(current['path']).read_bytes()
    prefix, append = data[:recorded['bytes']], data[recorded['bytes']:]
    require(hashlib.sha256(prefix).hexdigest() == recorded['sha256'] and len(append) == 855
            and row['append']['bytes'] == len(append) and row['append']['sha256'] == hashlib.sha256(append).hexdigest()
            and row['append']['text'] == append.decode('utf-8')
            and row['append']['text'].startswith('Opening shared memory\n')
            and 'Daemon is exiting without errors.\n' in row['append']['text'],
            'Recorded stdout prefix or exactly observed 855-byte daemon append changed')
    return {'current': current, 'recordedAtProcessClosure': recorded, 'wholeLogUnchanged': False,
            'recordedPrefixExact': True, 'observedLaterAppend': row['append'],
            'scope': 'Post-process UnrealTraceServer lifecycle output; no modification by review, no whole-stdout-unchanged claim'}


def closed_case(spec, view, candidate=False, stdout_observations=None):
    require(isinstance(spec, dict) and type(spec.get('processId')) is int and spec['processId'] > 0,
            'Actual closed process identity required for '+view)
    suite_pin = fixed(spec['suitePath'], spec['suiteSha256'])
    suite = read(suite_pin['path'])
    require(suite['owner'] == spec['owner'] and suite['source'] == spec['source'], 'Suite owner/source mismatch')
    require(suite['status'] == 'editor-game-suite-recorded-awaiting-independent-visual-review'
            and suite['errors'] == [] and suite['sourceInputsUnchanged'] is True, 'Closed unchanged Editor suite required')
    require((suite['requestedBuild'], suite['requestedTransport'], suite['requestedProfile'], suite['requestedOutput'])
            == ('Development', 'UnrealEditor -game', 'cinematic', 'retina'), 'Expected Editor render transport required')
    require(suite['warmupFrames'] == 2400 and suite['benchmarkFrames'] == 300, 'Warmup/sample flags changed')
    if candidate:
        require(suite['requestedViews'] == ([VIEWS[2]] if view == VIEWS[2] else list(VIEWS[:2])),
                'Actual declared R28 view set changed')
    for key in ('shippingVerified', 'packageVerified', 'performanceAccepted', 'fullPhotorealismAccepted'):
        require(suite[key] is False, 'Unaccepted pilot scope changed: '+key)
    selected = [c for c in suite['cases'] if c['view'] == view]
    require(len(selected) == 1 and suite['requestedViews'].count(view) == 1, 'Unique actual view required')
    case = selected[0]
    process_pin = pin(case['processReceiptPath'])
    require(read(process_pin['path']) == case and case['processId'] == spec['processId']
            and case['outcome'] == {'code': 0, 'signal': None, 'pid': spec['processId']}
            and case['nativeEvidenceValidated'] is True and case['sourceFovNativeReadbackAvailable'] is False
            and case['shaderAndLoadErrors'] == [], 'Actual process0/native evidence differs')
    require(case['originalCaptureSha256'] == spec['originalPngSha256']
            and case['originalRuntimeSha256'] == spec['originalRuntimeSha256'], 'Bound original PNG/runtime identity differs')
    png = fixed(case['originalCapturePath'], spec['originalPngSha256'])
    runtime_pin = fixed(case['originalRuntimePath'], spec['originalRuntimeSha256'])
    for row in (png, runtime_pin, process_pin):
        require(Path(row['path']).is_relative_to(Path(suite_pin['path']).parent), 'Case artifact outside its own suite')
    with Path(png['path']).open('rb') as f:
        header = f.read(24)
    require(header[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', header[16:24]) == (1920, 1080),
            'Original PNG1920x1080 header required')
    runtime = read(runtime_pin['path'])
    require(runtime['processId'] == spec['processId'] and runtime['status'] == 'capture-complete'
            and runtime['activeView'] == view and runtime['buildConfiguration'] == 'Development'
            and runtime['rhi'] == 'Metal' and runtime['shaderPlatform'] == 'METAL_SM6'
            and runtime['screenshotPixels'] == [1920, 1080] and runtime['screenshotSaved'] is True
            and runtime['screenshotKind'] == 'current-scene-render-target-preserving-view-history'
            and runtime['warmupFrames'] == 2400 and runtime['requestedBenchmarkFrames'] == 300,
            'Actual native capture or render flags differ')
    before = fixed(suite['inputClosureBefore']['path'], suite['inputClosureBefore']['sha256'])
    after = fixed(suite['inputClosureAfter']['path'], suite['inputClosureAfter']['sha256'])
    closure = read(before['path'])
    require(before['sha256'] == after['sha256'] and closure == read(after['path'])
            and len(closure) == suite['inputClosureBefore']['fileCount'] == suite['inputClosureAfter']['fileCount'],
            'Recorded source closure changed')
    logs = {}
    for role in ('stdout', 'runtime'):
        logs[role] = original_log(case, suite_pin, role, stdout_observations or {})
    if candidate:
        expected_source = CLOSE if view == VIEWS[2] else DIRECT
        expected_owner = 'scripts/unreal/exterior-editor-qa-r28-close.mjs' if view == VIEWS[2] else 'scripts/unreal/exterior-editor-qa-r28.mjs'
        require(spec['source'] == str(expected_source) and spec['owner'] == expected_owner, 'Known actual R37 R28 source required')
    frame = runtime['frameInterval']
    require(frame['status'] == 'measured' and frame['sampleCount'] == 300
            and math.isfinite(frame['meanMs']) and frame['meanMs'] > 0, 'Finite observed frame intervals required')
    return {'suite': suite_pin, 'process': process_pin, 'case': case, 'originalPng': png, 'originalRuntime': runtime_pin,
            'originalRuntimeLogs': logs,
            'runtime': runtime, 'sourceClosureBefore': before, 'sourceClosureAfter': after,
            'recordedSourceClosureFiles': len(closure), 'allSourceFilesIndependentlyRehashedByReview': False,
            'observedTiming': {'meanIntervalMs': frame['meanMs'], 'reciprocalMeanIntervalFps': 1000/frame['meanMs'],
                'method': '1000 divided by observed mean frame interval; no GPU or Shipping performance verdict',
                'frameInterval': frame, 'focus': runtime['focusDuringBenchmark'], 'performanceAccepted': False}}


def compare(before, after):
    rb, ra = before['runtime'], after['runtime']
    camera = difference(before['case']['sourceCamera'], after['case']['sourceCamera'])
    native_camera = difference(rb['walking']['presentationCamera'], ra['walking']['presentationCamera'])
    require(not camera and not native_camera, 'Unmatched camera cannot be presented as a fixed-camera pair')
    evb = rb['finalViewPostProcessSettings']['renderThreadPreExposure']['exposureEV']
    eva = ra['finalViewPostProcessSettings']['renderThreadPreExposure']['exposureEV']
    return {'sourceCameraExact': True, 'observedCameraExact': True, 'sourceCameraDifferences': camera,
            'observedCameraDifferences': native_camera, 'renderSettingDifferences': difference(rb['renderSettings'], ra['renderSettings']),
            'lightingDifferences': difference(rb['lighting'], ra['lighting']),
            'exteriorFixtureDifferences': difference(rb['exteriorLighting'], ra['exteriorLighting']),
            'fullPostProcessObservationDifferences': difference(rb['finalViewPostProcessSettings'], ra['finalViewPostProcessSettings']),
            'staticPostProcessSettingDifferences': difference(static_pp(rb['finalViewPostProcessSettings']), static_pp(ra['finalViewPostProcessSettings'])),
            'exposure': {'mode': 'automatic-unlocked', 'beforeEV': evb, 'afterEV': eva, 'deltaEV': eva-evb,
                         'fixedExposureComparison': False},
            'nativeFovDirectReadbackAvailable': False, 'sourceHorizontalFovDegrees': before['case']['sourceCamera']['horizontalFovDegrees'],
            'originalPixelsModified': False, 'individualMaterialOrGeometryPixelCauseIsolated': False,
            'dynamicCloudAndTimePhaseControlEstablished': False,
            'performanceComparisonAccepted': False}


def reviewed(row):
    require(isinstance(row, dict) and set(row) == {'root', 'independent'}, 'Two separate original-image review observations required')
    for who in ('root', 'independent'):
        reviewer = row[who]
        require(reviewer['viewedEveryOriginalInThisPanel'] is True and isinstance(reviewer['observations'], list)
                and reviewer['observations'] and all(isinstance(v, str) and v.strip() for v in reviewer['observations'])
                and isinstance(reviewer['limits'], list) and reviewer['limits']
                and type(reviewer['boundedVisibleGain']) is bool, 'Actual bounded visual review required: '+who)
    return row


def validate_request(request):
    require(request['schema'] == SCHEMA and request['schemaVersion'] == 1
            and request['status'] == 'actual-closed-captures-and-two-original-image-reviews-bound'
            and list(request['panels']) == list(VIEWS), 'Final actual closed three-panel request required')
    for view in VIEWS:
        panel = request['panels'][view]
        require(panel['baseline'] == BASELINES[view], 'Fixed known comparator changed')
        spec = panel['candidate']
        require(isinstance(spec, dict) and type(spec.get('processId')) is int and spec['processId'] > 0,
                'Actual closed process identity required for '+view)
        source = CLOSE if view == VIEWS[2] else DIRECT
        owner = 'scripts/unreal/exterior-editor-qa-r28-close.mjs' if view == VIEWS[2] else 'scripts/unreal/exterior-editor-qa-r28.mjs'
        require(spec['source'] == str(source) and spec['owner'] == owner, 'Known actual R37 R28 source required')
        require(Path(spec['suitePath']).is_absolute() and Path(spec['suitePath']).is_relative_to(V/'qa')
                and Path(spec['suitePath']).name == 'editor-pilot-suite.json', 'Own validation suite path required')
        for key in ('suiteSha256', 'originalPngSha256', 'originalRuntimeSha256'):
            value = spec[key]
            require(isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value),
                    'Actual capture identity still pending: '+key)
        visual = reviewed(panel['visualReview'])
        if BASELINES[view] is None:
            require(all(visual[who]['boundedVisibleGain'] is False for who in ('root', 'independent')),
                    'Candidate-only overview cannot claim a before/after visible gain')
    return request


def root_review(request, panels):
    observed = fixed(ROOT_REVIEW, ROOT_REVIEW_SHA)
    require(request['rootOriginalImageReviewReceipt'] == observed, 'Fixed actual root original-image review required')
    row = read(observed['path'])
    require(row['schema'] == 'brezi-root-r37-actual-image-base-selection-for-r38-only'
            and row['status'] == 'selected-saved-r37b-only-as-next-scoped-ground-pilot-base'
            and row['selectedNativeBase'] == str(DIRECT) and row['selectedNativeReport']['sha256'] == NATIVE_SHA
            and row['selectedCurrentByteAudit']['sha256'] == AUDIT_SHA and row['selectedNativeProcessId'] == 54956,
            'Known scoped root review identity required')
    for key in ('fullPhotorealismAccepted', 'nativeAppearanceAccepted', 'performanceAccepted', 'shippingVerified',
                'packageVerified', 'activeOutputPromoted', 'photoPixelsEdited'):
        require(row[key] is False, 'Root image review cannot promote global acceptance')
    require([x['view'] for x in row['actualCameraCaptures']] == list(VIEWS), 'Root original capture set changed')
    for capture, panel in zip(row['actualCameraCaptures'], panels):
        after = panel['candidate']
        require(capture['suite'] == after['suite'] and capture['process'] == after['process']
                and capture['originalPng'] == after['originalPng'] and capture['originalRuntime'] == after['originalRuntime']
                and capture['nativePid'] == after['case']['processId'] and capture['rootSessionClosedExitCode'] == 0
                and capture['originalWholePngViewedByRoot'] is True, 'Root capture/PID/whole-original view binding changed')
    return observed


def figure(row, label, output):
    url = quote(os.path.relpath(row['originalPng']['path'], output), safe='/')
    timing = row['observedTiming']
    return '<figure><figcaption><strong>'+html.escape(label)+'</strong><span>PID '+str(row['case']['processId'])+' · '+f'{timing["meanIntervalMs"]:.2f} ms · {timing["reciprocalMeanIntervalFps"]:.2f}'+' pozorovaných FPS*</span></figcaption><a href="'+url+'" target="_blank" rel="noopener"><img src="'+url+'" alt="'+html.escape(label)+' · pôvodný výstup Unreal Engine" loading="lazy"></a><a class="original" href="'+url+'" target="_blank" rel="noopener">Otvoriť pôvodný PNG 1920 × 1080</a></figure>'


def page(panels, output):
    sections = []
    for panel in panels:
        images = []
        if panel['baseline']:
            images.append(figure(panel['baseline'], panel['comparatorRole']['label'], output))
        images.append(figure(panel['candidate'], 'Spoločná scéna R37', output))
        notes = []
        for who, label in (('root', 'Kontrola hlavného autora'), ('independent', 'Nezávislá kontrola')):
            observation = panel['visualReview'][who]
            notes.append('<h3>'+label+'</h3><ul>'+''.join('<li>'+html.escape(s)+'</li>' for s in observation['observations'])+'</ul><p><strong>Limity:</strong> '+html.escape(' '.join(observation['limits']))+'</p>')
        if panel['comparison']:
            ev = panel['comparison']['exposure']
            explanation = 'Rovnaká zdrojová a zaznamenaná kamera. Automatická expozícia nebola uzamknutá; rozdiel '+f'{ev["deltaEV"]:+.6f}'+' EV. Všetky rozdiely svetla, renderu a statického postprocessu sú v dôkazovom zázname.'
            if panel['view'] == VIEWS[2]:
                explanation += ' Kontrolná snímka je uložený donor dvora R35, nie bezprostredný rodič záhradnej scény R36. Porovnanie kontroluje zachovanie podoby dvora v spoločnej scéne.'
        else:
            explanation = 'Samostatná pôvodná snímka celého okolia. Chýba zodpovedajúca kontrolná kamera, preto z nej nevyvodzujeme zmenu pred a po.'
        sections.append('<section id="'+html.escape(panel['view'])+'"><h2>'+html.escape(TITLES[panel['view']])+'</h2><p>'+html.escape(explanation)+'</p><div class="images '+('single' if not panel['baseline'] else '')+'">'+''.join(images)+'</div>'+''.join(notes)+'</section>')
    return '''<!doctype html><html lang="sk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Záhrada a okolie · pôvodné snímky R37</title><style>
*{box-sizing:border-box}body{margin:0;background:#10171d;color:#edf2ef;font:16px/1.6 system-ui,sans-serif}main{max-width:1800px;margin:auto;padding:30px 24px}h1{font-size:clamp(28px,3vw,42px);line-height:1.15}h2{font-size:27px}h3{font-size:18px;margin-bottom:4px}p,ul{max-width:1100px;color:#cad7d0}a{color:#b9ebd3}section{padding:24px 0;border-top:1px solid #344840}.images{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:22px 0}.images.single{grid-template-columns:1fr;max-width:1300px}figure{margin:0;border:1px solid #344840;border-radius:10px;overflow:hidden;background:#19261f}figcaption{padding:13px 16px}figcaption strong,figcaption span{display:block}figcaption span{font-size:13px;color:#b9cbc0}img{width:100%;height:auto;display:block}.original{display:block;padding:11px 16px}li{margin:.4em 0}.limit{padding:15px 20px;background:#273526;border:1px solid #59673b}footer{font-size:14px;color:#c0cbc5;border-top:1px solid #344840;padding-top:20px}@media(max-width:900px){main{padding:20px 14px}.images{grid-template-columns:1fr}}</style><main>
<h1>Záhrada a okolie: kontrola spoločnej scény</h1><p>Priame pôvodné snímky Unreal Engine. Dve porovnania používajú rovnaké kamery; široký pohľad na okolie je samostatná kontrola súdržnosti miesta. Dom C / B / B, architektúra a odstupy 3 000 mm zostali chránené.</p><p>Unreal Editor Development · Metal SM6 · Cinematic · 1920 × 1080 · 2 400 zahrievacích a 300 meraných snímok.</p><p class="limit">Celková fotorealistickosť, výkon a Shipping zostávajú neschválené. Ide o umeleckú úpravu okolia bez tvrdenia geodetickej presnosti. Riadenie dynamickej fázy oblakov a času medzi samostatnými spusteniami nie je preukázané.</p>'''+''.join(sections)+'''<footer>* Pozorované FPS = 1 000 / priemerný zaznamenaný interval. Aktivita aplikácie, okna a klávesového fokusu je uložená samostatne; tieto čísla neznamenajú prijatie výkonu. Snímky sa iba prispôsobujú šírke stránky: žiadne úpravy pixelov, normalizácia expozície ani orezanie. <a href="paired-review.json">Dôkazový záznam vrátane svetla, kamery, postprocessu a EV</a>. Natívne vrcholy/normály/tangenty ani viditeľnosť všetkých vegetačných skupín týmto prehliadačom znovu nedekódujeme. Pri niektorých stdout logoch sa po ukončení aplikácie pripojil výstup pomocného UnrealTraceServera; pôvodný zaznamenaný prefix zostal presný. Úplné aktuálne logy a pripojené bajty sú pripnuté samostatne, nie označené za nezmenené.</footer></main></html>'''


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--request', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    request_pin = pin(args.request)
    request = validate_request(read(request_pin['path']))
    stdout_receipt, stdout_observations = load_stdout_observations(request.get('observedStdoutAppendReceipt'))
    panels = []
    for view in VIEWS:
        requested = request['panels'][view]
        require(requested['baseline'] == BASELINES[view], 'Fixed known comparator changed')
        after = closed_case(requested['candidate'], view, True, stdout_observations)
        before = closed_case(BASELINES[view], view, False, stdout_observations) if BASELINES[view] else None
        panels.append({'view': view, 'mode': 'fixed-camera-original-pair' if before else 'candidate-only-original-overview',
                       'comparatorRole': COMPARATOR_ROLES[view],
                       'baseline': before, 'candidate': after, 'comparison': compare(before, after) if before else None,
                       'visualReview': reviewed(requested['visualReview']), 'unmatchedBeforeAfterGainClaimed': False})
    root_receipt = root_review(request, panels)
    native = fixed(NATIVE_REPORT, NATIVE_SHA)
    audit = fixed(BYTE_AUDIT, AUDIT_SHA)
    report = read(native['path'])
    require(report['schemaVersion'] == 2 and report['status'] == 'verified-saved-clean-selected-garden-and-yard-integration'
            and report['savedMapUnloadedReloaded'] is True, 'Actual saved R37R2 native scene required')
    output = Path(args.output).resolve()
    require(output.parent == V and output.name.startswith('r37b-garden-yard-original-review-r28-'), 'Exclusive owned validation review output required')
    output.mkdir(exist_ok=False)
    (output/'index.html').write_text(page(panels, output))
    receipt = {'schema': SCHEMA, 'schemaVersion': 1, 'owner': OWNER,
               'recordedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
               'status': 'actual-original-pairs-and-overview-reviewed-full-realism-NO_GO',
               'producer': pin(ROOT/OWNER), 'request': request_pin, 'nativeReport': native, 'rootByteAudit': audit,
               'observedStdoutAppendReceipt': stdout_receipt,
               'rootOriginalImageReviewReceipt': root_receipt,
               'panels': panels, 'originalPixelsModified': False, 'recordedRuntimeSourceClosuresChecked': True,
               'allRuntimeSourceClosureFilesIndependentlyRehashedByReview': False,
               'freshNativeActorOrGeometryDecodePerformedByReview': False,
               'nativeNormalTangentReadbackAvailable': False, 'nativeTexturePixelsDecodedByReview': False,
               'dynamicCloudAndTimePhaseControlEstablished': False,
               'allScopedInstancesActualVisibilityMeasured': False, 'browserVerifiedByProducer': False,
               'html': pin(output/'index.html'), 'fullPhotorealismAccepted': False,
               'nativeAppearanceAccepted': False, 'performanceAccepted': False, 'shippingVerified': False,
               'packageVerified': False, 'activeSelectorPromotionApproved': False}
    write(output/'paired-review.json', receipt)
    (output/'producer-source.py').write_bytes((ROOT/OWNER).read_bytes())
    (output/'capture-request.json').write_bytes(Path(request_pin['path']).read_bytes())
    write(output/'artifact-receipt.json', {'owner': OWNER, 'files': [pin(output/n) for n in
        ('index.html', 'paired-review.json', 'producer-source.py', 'capture-request.json')],
        'originalPngs': [row['originalPng'] for panel in panels for row in (panel['baseline'], panel['candidate']) if row],
        'originalPixelsChanged': False})
    print(json.dumps({'review': pin(output/'paired-review.json'), 'html': pin(output/'index.html'),
                      'pairedViews': 2, 'candidateOnlyViews': 1, 'performanceAccepted': False}))


if __name__ == '__main__':
    main()
