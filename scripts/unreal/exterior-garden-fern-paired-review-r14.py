"""Read-only R14 purposeful close pair; emit fresh audit/side-by-side HTML only."""
import hashlib
import html
import json
from pathlib import Path
import struct
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-fern-paired-review-r14.py'
OUT = ROOT / 'output/unreal/exterior-validation-20260930-r1'
BEFORE = OUT / 'qa/editor-pilot-r22c-fern-close-baseline-r14-1790910393927-Ej1YPn/editor-pilot-suite.json'
AFTER = OUT / 'qa/editor-pilot-r25b-fern-close-candidate-r14-1790910571027-2eCO08/editor-pilot-suite.json'
AUDIT = OUT / 'garden-fern-purposeful-paired-review-r14-r1.json'
PAGE = OUT / 'r25b-fern-purposeful-close-comparison-r14-r1.html'
VIEW = 'exterior-garden-fern-close-r14'


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}


def read(path):
    return json.loads(Path(path).read_text())


def verify_pin(row):
    actual = pin(row['path'])
    assert actual['sha256'] == row['sha256'] and actual['bytes'] == row['bytes']
    return actual


def url(path):
    return quote(Path(path).resolve().relative_to(OUT).as_posix(), safe='/')


def suite_proof(path, editor_pid, native_pid, native_sha, source_kind, expected_closure_count):
    suite = read(path)
    assert suite['status'] == 'editor-game-suite-recorded-awaiting-independent-visual-review'
    assert suite['sourceInputsUnchanged'] is True and suite['errors'] == []
    assert suite['requestedViews'] == [VIEW] and len(suite['cases']) == 1
    assert suite['requestedBuild'] == 'Development' and suite['requestedTransport'] == 'UnrealEditor -game'
    assert suite['requestedProfile'] == 'cinematic' and suite['requestedOutput'] == 'retina'
    before = verify_pin(suite['inputClosureBefore'])
    after = verify_pin(suite['inputClosureAfter'])
    assert before['sha256'] == after['sha256'] and before['bytes'] == after['bytes']
    assert read(before['path']) == read(after['path'])
    assert len(read(before['path'])) == expected_closure_count == suite['inputClosureBefore']['fileCount'] == suite['inputClosureAfter']['fileCount']
    case = suite['cases'][0]
    assert case['view'] == VIEW and case['outcome'] == {'code': 0, 'signal': None, 'pid': editor_pid}
    assert case['nativeEvidenceValidated'] is True and case['shaderAndLoadErrors'] == []
    assert case['sourceFovNativeReadbackAvailable'] is False
    assert case['status'] == 'editor-game-capture-recorded-awaiting-visual-review'
    for flag in ('shippingVerified', 'packageVerified', 'nativeAppearanceAccepted', 'performanceAccepted', 'fullPhotorealismAccepted'):
        assert case[flag] is False and suite[flag] is False
    capture = pin(case['originalCapturePath'])
    runtime_pin = pin(case['originalRuntimePath'])
    assert capture['sha256'] == case['originalCaptureSha256'] and runtime_pin['sha256'] == case['originalRuntimeSha256']
    process = read(case['processReceiptPath'])
    assert process['outcome'] == case['outcome'] and process['nativeEvidenceValidated'] is True
    assert process['originalCaptureSha256'] == capture['sha256'] and process['originalRuntimeSha256'] == runtime_pin['sha256']
    raw = Path(capture['path']).read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', raw[16:24]) == (1920, 1080)
    evidence = suite['nativeSourceEvidence']
    assert evidence['mode'] == 'purposeful-original-fern-matched-camera-qa-clone'
    assert evidence['summary']['sourceKind'] == source_kind
    assert evidence['originalNativeSourceUnchanged'] is True
    native = verify_pin(evidence['sourceNativeReport'])
    assert native['sha256'] == native_sha and read(native['path'])['savedMapUnloadedReloaded'] is True
    native_process_pin = verify_pin(evidence['sourceNativeProcess'])
    native_process = read(native_process_pin['path'])
    assert native_process['reportSha256'] == native_sha and native_process['sourcePinsUnchangedAfterNative'] is True
    raw_native_pin = pin(native_process['processFile'])
    assert raw_native_pin['sha256'] == native_process['processFileSha256']
    raw_native = read(raw_native_pin['path'])
    assert raw_native['pid'] == native_pid and raw_native['code'] == 0 and raw_native['signal'] is None
    stage_pin = verify_pin(evidence['nativeReceipt'])
    stage = read(stage_pin['path'])
    assert stage['schema'] == 'brezi-purposeful-original-fern-matched-camera-qa-clone-r14'
    assert stage['status'] == 'verified-independent-purposeful-fern-camera-data-only-qa-clone'
    assert stage['changedContentFiles'] == ['Data/viewpoints.json']
    assert stage['sceneMapChanged'] is False and stage['nativeSourceUnchanged'] is True
    assert stage['lightingUnchanged'] is True and stage['originalViewsPrefixPreserved'] is True
    assert stage['sourceValidationExitCode'] == 0
    assert stage['view'] == case['sourceCamera']
    supplement = verify_pin(stage['cameraSupplement'])
    assert supplement == verify_pin(evidence['cameraSupplement'])
    assert supplement['sha256'] == '9081c0830b4c11eed3787abb5b0bc49ecfedd4a145040c20b09d3bef981298ea'
    viewpoint = verify_pin(stage['viewpointFile'])
    assert next(v for v in read(viewpoint['path'])['views'] if v['id'] == VIEW) == case['sourceCamera']
    assert stage['sourceCameraAudit']['untaggedPlantOcclusionChecked'] is False
    assert stage['sourceCameraAudit']['nativeOcclusionOrPlantVisibilityMeasured'] is False
    return suite, case, read(runtime_pin['path']), {
        'suite': pin(path), 'editorPid': editor_pid, 'editorExitCode': 0, 'originalPng': capture, 'originalRuntime': runtime_pin,
        'editorProcess': pin(case['processReceiptPath']), 'sourceNativeReport': native,
        'sourceNativeProcess': native_process_pin, 'sourceRawNativeProcess': raw_native_pin,
        'nativePid': native_pid, 'stageReceipt': stage_pin, 'cameraSupplement': supplement,
        'stagedViewpointFile': viewpoint, 'stageSourceCameraAudit': stage['sourceCameraAudit'],
        'capturedInputClosure': {'before': before, 'after': after, 'fileCount': expected_closure_count,
                                'closuresIdentical': True, 'currentWholeClosureRehashedByThisReview': False},
        'sourceSummary': evidence['summary'],
    }


def main():
    assert not AUDIT.exists() and not PAGE.exists(), 'Fresh immutable review paths required'
    bs, bc, br, baseline = suite_proof(BEFORE, 69670, 50344,
        '999fc17ea7600136a2097aecefed3d846ff0d7e9baeb7f005480b113b60b1f40',
        'original-r22c-six-donor-garden-baseline', 4643)
    cs, cc, cr, candidate = suite_proof(AFTER, 70044, 60976,
        'dc96a4927a0b0ec0e8abb3740e7a918e65a6ba6a0881ba77bc29275c1445e0b2',
        'saved-r25b-original-fern-single-root', 4782)
    assert bc['sourceCamera'] == cc['sourceCamera']
    assert bc['observed']['actualCamera'] == cc['observed']['actualCamera']
    assert baseline['stagedViewpointFile']['sha256'] == candidate['stagedViewpointFile']['sha256']
    assert br['renderSettings'] == cr['renderSettings']
    for key, expected in [('rhi', 'Metal'), ('shaderPlatform', 'METAL_SM6'), ('screenshotPixels', [1920, 1080]),
                          ('warmupFrames', 2400), ('requestedBenchmarkFrames', 300),
                          ('screenshotKind', 'current-scene-render-target-preserving-view-history')]:
        assert br[key] == cr[key] == expected
    bp, cp = br['finalViewPostProcessSettings'], cr['finalViewPostProcessSettings']
    assert set(bp) == set(cp)
    different_pp = [k for k in bp if bp[k] != cp[k]]
    assert different_pp == ['renderThreadPreExposure']
    be, ce = bp['renderThreadPreExposure']['exposureEV'], cp['renderThreadPreExposure']['exposureEV']
    delta = ce-be
    for case in (bc, cc):
        focus = case['observed']['foregroundTimingFacts']
        assert case['observed']['frameIntervalFacts']['sampleCount'] == focus['sampleCount'] == 300
        assert focus['applicationForegroundSamples'] == 0
        assert focus['gameWindowActiveSamples'] == focus['sceneViewportKeyboardFocusSamples'] == 300
    assert candidate['sourceSummary']['changedExistingRoots'] == 1
    assert candidate['sourceSummary']['newActors'] == candidate['sourceSummary']['newRoots'] == 0
    assert candidate['sourceSummary']['nativeTrianglesByLod'] == [2384, 2384, 2384]
    before_height = candidate['sourceSummary']['originalAboveRootHeightCm']
    after_height = candidate['sourceSummary']['actualAboveRootHeightCm']
    first, second = url(baseline['originalPng']['path']), url(candidate['originalPng']['path'])
    PAGE.write_text(f'''<!doctype html><html lang="sk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Papraď · skutočný detail R22c a R25b</title><style>
*{{box-sizing:border-box}}body{{margin:0;background:#111713;color:#edf1e9;font:16px/1.55 system-ui,sans-serif}}header,main,footer{{max-width:2200px;margin:auto;padding:24px}}header{{padding-top:36px}}h1{{font-size:clamp(28px,4vw,46px);line-height:1.15;margin:8px 0 16px}}h2{{font-size:21px;margin:0 0 12px}}.status{{font-weight:700;color:#f7cb8a}}.intro{{max-width:1050px;color:#c5cec2}}.images{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}figure{{margin:0;background:#1c251d;border:1px solid #40513b;border-radius:10px;overflow:hidden}}figure img{{display:block;width:100%;height:auto;aspect-ratio:16/9;object-fit:contain}}figcaption{{padding:16px}}figcaption p{{margin:7px 0}}a{{color:#bddaa6}}a:focus-visible{{outline:3px solid #f7cb8a;outline-offset:4px}}.facts{{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin:28px 0}}.facts section{{background:#1c251d;border:1px solid #40513b;border-radius:10px;padding:20px}}.facts p{{margin:7px 0}}details{{border-top:1px solid #40513b;padding-top:20px}}summary{{cursor:pointer;font-weight:700}}code{{font-size:12px;overflow-wrap:anywhere}}footer{{color:#b5c4ac;font-size:14px}}@media(max-width:800px){{.images,.facts{{grid-template-columns:1fr}}header,main,footer{{padding:16px}}}}
</style><header><div class="status">Rozpoznateľná nízka papraď · celková realistickosť NO_GO</div><h1>Jeden pôvodný koreň, výrazne menšia rastlina</h1><p class="intro">Pôvodné nezmenené PNG z rovnakého detailného pohľadu v Unreal Engine. Vysoký pravidelný trs v R22c nahradila nízka papraď Fern 02 v R25b. Jej členené listy vidno pri zemi, no veľká časť zostáva zakrytá pôvodnými širokými listami v popredí. Väčšia otvorenosť záhona je najmä dôsledkom výšky {before_height:.0f} → {after_height:.2f} cm. Nejde o zlepšenie celej záhrady.</p></header>
<main><div class="images"><figure><img src="{first}" alt="Pôvodný PNG R22c: vysoký pravidelný modrosivý trs v strede záhona"><figcaption><h2>R22c · pôvodný vysoký trs</h2><p>Editor proces 69 670 · exit 0</p><a href="{first}">Otvoriť pôvodný PNG v plnom rozlíšení</a></figcaption></figure>
<figure><img src="{second}" alt="Pôvodný PNG R25b: nízka papraď s členenými listami, čiastočne zakrytá veľkými listami v popredí"><figcaption><h2>R25b · pôvodný model paprade</h2><p>Editor proces 70 044 · exit 0</p><a href="{second}">Otvoriť pôvodný PNG v plnom rozlíšení</a></figcaption></figure></div>
<div class="facts"><section><h2>Viditeľný prínos</h2><p>Nízko v strede záhona pribudla rozpoznateľná členitá silueta papraďových listov. Vysoká modrosivá pravidelná kostra pôvodného trsu zmizla.</p><p>Nový tvar je vhodnejší ako nízka podsadba, ale znížil pôvodnú výškovú dominantu. Toto je umelecká voľba jedného koreňa, bez tvrdenia botanickej či ekologickej zhody.</p></section>
<section><h2>Otvorené riziká</h2><p>Papraď výrazne zakrývajú zachované veľké listy v popredí a susedný porast. Zdrojové zahrnutie celej koruny v zábere samo nepotvrdzuje jej viditeľnosť.</p><p>Opakované hviezdicové listy, trávy a fialové kvety, rovný mulchový pás, ostré okraje a jednoduché povrchy steny a plotu ostávajú. Kontakt koreňa s podkladom je čiastočne skrytý.</p></section></div>
<details><summary>Presná kamera, merania a pôvod obrázkov</summary><p>Zdrojová aj skutočne pozorovaná kamera sú presne zhodné. Oko [1432.3084822728883, −377.1794510218074, 130] cm; zdrojový cieľ [1432.3084822728883, −627.1794510218074, 50] cm. Zdrojový FOV je 62°; natívny readback FOV chýba. Kamera je účelový umelecky odvodený diagnostický pohľad.</p><p>Oba behy: Editor Development / Metal SM6, 1920 × 1080, 2 400 zahrievacích + 300 meraných snímok. Renderovacie nastavenia a zložené PP okrem expozície sú presne rovnaké. Automatická expozícia {be:.6f} → {ce:.6f} EV (Δ {delta:+.6f}) nebola uzamknutá.</p>
<p>Priemerný interval snímok {br['frameInterval']['meanMs']:.3f} → {cr['frameInterval']['meanMs']:.3f} ms. Herné okno/fokus boli aktívne počas 300/300 snímok, systémové app-foreground 0/300; tieto pozorovania nie sú výkonnostným prijatím.</p><p>PNG R22c <code>{baseline['originalPng']['sha256']}</code><br>PNG R25b <code>{candidate['originalPng']['sha256']}</code></p><a href="{AUDIT.name}">Zdrojový, natívny a obrazový audit</a></details></main>
<footer>Oba pôvodné PNG boli nezávisle prezreté a zostali nezmenené. Samostatné QA kópie pridali iba jeden pohľad do viewpoints.json; pôvodné scény R22c a R25b zostali zachované. Zdrojové/natívne počty nie sú viditeľným pokrytím záhrady. Nameraný normálový či tangentový readback, formát GPU alpha textúry, fyzikálna optika, výkon, Shipping a plná fotorealistickosť nie sú týmto párom potvrdené.</footer></html>''')
    receipt = {
        'schemaVersion': 1, 'owner': OWNER, 'status': 'actual-purposeful-fern-close-editor-pair-reviewed-bounded-shape-gain-full-no-go',
        'producer': pin(ROOT / OWNER), 'baseline': baseline, 'candidate': candidate, 'comparisonHtml': pin(PAGE),
        'pairChecks': {'sameImmediateNativeBase': True, 'candidateNativeBase': 'Saved R22c; R25b changes exactly one existing own-garden root mesh/material/uniform scale.',
                      'sourceCameraExact': True, 'observedCameraExact': True, 'stagedViewpointBytesExact': True,
                      'renderSettingsExact': True, 'composedPostProcessExceptExposureExact': True,
                      'postProcessDifferenceFields': different_pp, 'sourceInputsUnchangedBoth': True,
                      'sourceNativeSceneCameraRenderMismatches': [], 'sourceFovNativeReadbackAvailable': False,
                      'pixels': [1920, 1080], 'rhi': 'Metal', 'shaderPlatform': 'METAL_SM6', 'warmupFrames': 2400, 'benchmarkFrames': 300},
        'sourceCamera': bc['sourceCamera'], 'observedCamera': bc['observed']['actualCamera'],
        'renderSettings': br['renderSettings'], 'composedPostProcessPolicy': {k: v for k, v in bp.items() if k != 'renderThreadPreExposure'},
        'exposure': {'mode': 'automatic-unlocked', 'beforeEV': be, 'afterEV': ce, 'deltaEV': delta, 'fixedExposureComparison': False},
        'visualFindings': {
            'originalImagesIndependentlyViewed': 2, 'boundedVisibleGain': True,
            'gain': ['Recognizable pinnate fern fronds are visible low in the central bed.',
                     'The tall regular silver-blue branched seed-head clump is removed; new shape reads as low understory.'],
            'risks': ['Much of the fern is obscured by unchanged large foreground leaves and surrounding plants.',
                      'Opening above the root is mainly the intended 120cm-to-35.27cm height reduction; original height/volume is not preserved.',
                      'Root-to-ground contact is partly hidden; no pixel claim of complete crown or contact visibility.',
                      'Repeating star-shaped low leaves, grasses, purple flowers, flat mulch strip, sharp edges and simple wall/fence remain.'],
            'sourceFrustumInclusionIsUnoccludedVisibility': False,
            'sourceCameraAuditUntypedPlantOcclusionWasChecked': False,
            'sourceHeightDifferenceIsUnexpectedMismatch': False, 'wholeGardenAppearanceGainVerified': False,
            'botanicalOrEcologicalFitClaimed': False, 'physicallyCalibratedMaterialAppearanceVerified': False,
        },
        'geometryAndMaterialEvidenceLimits': {'changedRootId': 'garden_ornamental_10', 'changedExistingRoots': 1, 'newRoots': 0,
            'nativeTrianglesByLod': [2384, 2384, 2384], 'providerLodChainClaimed': False,
            'sourceAlphaBits': 16, 'nativeSourcePixelFormatReadbackAvailable': False, 'nativeGpuPixelFormatReadbackAvailable': False,
            'nativeNormalTangentReadbackAvailable': False, 'materialAndMeshPackagesIndependentlyReloaded': False,
            'oldAboveRootHeightCm': before_height, 'newAboveRootHeightCm': after_height, 'heightEquivalenceClaimed': False},
        'editorTimingObservation': {'baseline': br['frameInterval'], 'candidate': cr['frameInterval'],
                                   'baselineFocus': br['focusDuringBenchmark'], 'candidateFocus': cr['focusDuringBenchmark'], 'performanceAccepted': False},
        'shaderReadiness': {'errorsBoth': [], 'pendingShaderCountAtCaptureObserved': False, 'noErrorLogIsFullReadinessProof': False},
        'browserVerifiedByThisReview': False, 'originalPngsEdited': False, 'newNativeOrGpuRunPerformed': False,
        'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False,
        'shippingVerified': False, 'packageVerified': False, 'activeSelectorPromotionApproved': False,
        'goNoGo': 'BOUNDED_SINGLE_ROOT_FERN_SHAPE_GAIN_WITH_OCCLUSION_AND_HEIGHT_CHANGE; FULL_REALISM_NO_GO',
    }
    AUDIT.write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'audit': pin(AUDIT), 'html': pin(PAGE), 'deltaEV': delta, 'imagesUnchanged': True, 'sourceCameraRenderMismatches': []}))


if __name__ == '__main__':
    main()
