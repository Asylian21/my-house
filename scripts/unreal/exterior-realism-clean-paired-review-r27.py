"""Review closed R22c/R27a original captures; create fresh comparison artifacts only."""
import hashlib
import html
import json
from pathlib import Path
import re
import struct
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-realism-clean-paired-review-r27.py'
OUT = ROOT / 'output/unreal/exterior-validation-20260930-r1'
BEFORE = OUT / 'qa/editor-pilot-r22c-integrated-r10-1790903900548-CzNNn7/editor-pilot-suite.json'
AFTER = OUT / 'qa/editor-pilot-r27a-clean-integration-r13-1790909195856-YzhP5f/editor-pilot-suite.json'
TEMPLATE = OUT / 'r22c-four-view-paired-review-r1.html'
AUDIT = OUT / 'clean-realism-integration-four-view-paired-review-r1.json'
PAGE = OUT / 'r27a-clean-four-view-paired-review-r1.html'
VIEWS = ['exterior-canopy-close', 'exterior-parcels', 'neighbor-finish-close-r18', 'exterior-garden']
BASE_PIDS = [53435, 53772, 54177, 54382]
NEW_PIDS = [67274, 67565, 67825, 68000]
FINDINGS = [
    {
        'title': 'Koruny a podsadba', 'visibleGain': False,
        'finding': 'V tomto páre je obraz takmer rovnaký. Z tejto kamery nemožno tvrdiť nové pokrytie blízkeho porastu.',
        'limits': 'Riedke vzpriamené trávy a drobné byliny na plochom zelenom podklade zostávajú. Husté oblé koruny a opakované tmavé listové masy sú stále dominantné.',
    },
    {
        'title': 'Okolité parcely', 'visibleGain': False,
        'finding': 'Široký pohľad na parcely je vizuálne takmer rovnaký. Súvislý porast bol prítomný už v R22c.',
        'limits': 'Rovnomerná jemná tráva, opakované žlté trsy a vzdialený plochý mapový podklad ostávajú. Zachovanie 8 949 pôvodných tráv je natívny zdrojový fakt, nie dôkaz viditeľného zlepšenia v tomto zábere.',
    },
    {
        'title': 'Susedné domy', 'visibleGain': True,
        'finding': 'Na blízkom dome zmizla krémová strešná mriežka R23 a vrátila sa červená procedurálna strecha R18. Hĺbka ostení a tiene parapetov sú zachované v oboch scénach.',
        'limits': 'Červené škridly sa stále pravidelne opakujú. Svetlosivé ploché výplne okien a závesy, jednoduché steny a dvere aj prázdny zelený priestor zostávajú neprirodzené. Nejde o návrat fotografickej strechy ani o dôkaz realistického skla.',
    },
    {
        'title': 'Vlastná záhrada', 'visibleGain': False,
        'finding': 'Vlastná záhrada je v tomto páre vizuálne takmer nezmenená.',
        'limits': 'Opakované hviezdicové listy, podobné fialové kvety, vysoké biele trsy, rovnomerný trávnik a ostrý obdĺžnikový lem záhona ostávajú. Hlavná oblasť požadovaná používateľom ešte potrebuje podstatné zlepšenie.',
    },
]


def read(path):
    return json.loads(Path(path).read_text())


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}


def verify_pin(declared):
    measured = pin(declared['path'])
    assert measured['sha256'] == declared['sha256'] and measured['bytes'] == declared['bytes']
    return measured


def url(path):
    return quote(Path(path).resolve().relative_to(OUT).as_posix(), safe='/')


def case_proof(case, expected_pid):
    assert case['outcome'] == {'code': 0, 'signal': None, 'pid': expected_pid}
    assert case['nativeEvidenceValidated'] is True and not case['shaderAndLoadErrors']
    assert case['sourceFovNativeReadbackAvailable'] is False
    for flag in ('shippingVerified', 'packageVerified', 'nativeAppearanceAccepted', 'performanceAccepted', 'fullPhotorealismAccepted'):
        assert case[flag] is False
    png = pin(case['originalCapturePath'])
    runtime = pin(case['originalRuntimePath'])
    assert png['sha256'] == case['originalCaptureSha256'] and runtime['sha256'] == case['originalRuntimeSha256']
    raw = Path(png['path']).read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', raw[16:24]) == (1920, 1080)
    process = read(case['processReceiptPath'])
    assert process['outcome'] == case['outcome'] and process['nativeEvidenceValidated'] is True
    assert process['originalCaptureSha256'] == png['sha256'] and process['originalRuntimeSha256'] == runtime['sha256']
    return {'pid': expected_pid, 'originalPng': png, 'originalRuntime': runtime, 'process': pin(case['processReceiptPath'])}


def suite_proof(suite, path, expected_mode, expected_report_sha):
    assert suite['status'] == 'editor-game-suite-recorded-awaiting-independent-visual-review'
    assert suite['sourceInputsUnchanged'] is True and not suite['errors']
    assert suite['requestedViews'] == VIEWS and [c['view'] for c in suite['cases']] == VIEWS
    assert suite['requestedBuild'] == 'Development' and suite['requestedTransport'] == 'UnrealEditor -game'
    assert suite['requestedProfile'] == 'cinematic' and suite['requestedOutput'] == 'retina'
    evidence = suite['nativeSourceEvidence']
    assert evidence['mode'] == expected_mode and evidence['nativeReceipt']['sha256'] == expected_report_sha
    native = verify_pin(evidence['nativeReceipt'])
    assert read(native['path'])['savedMapUnloadedReloaded'] is True
    before = verify_pin(suite['inputClosureBefore'])
    after = verify_pin(suite['inputClosureAfter'])
    assert before['sha256'] == after['sha256'] and before['bytes'] == after['bytes']
    closure = read(before['path'])
    assert closure == read(after['path']) and len(closure) == suite['inputClosureBefore']['fileCount'] == suite['inputClosureAfter']['fileCount']
    return {'suite': pin(path), 'nativeReport': native, 'inputClosureBefore': before, 'inputClosureAfter': after,
            'unchangedCapturedInputFileCount': len(closure), 'closureFilesIdentical': True,
            'currentWholeInputClosureRehashedByThisReview': False, 'nativeSummary': evidence['summary']}


def main():
    assert not AUDIT.exists() and not PAGE.exists(), 'Fresh immutable review paths required'
    before, after = read(BEFORE), read(AFTER)
    before_proof = suite_proof(before, BEFORE, 'saved-six-donor-exterior-realism-integration',
                               '999fc17ea7600136a2097aecefed3d846ff0d7e9baeb7f005480b113b60b1f40')
    after_proof = suite_proof(after, AFTER, 'saved-four-donor-clean-exterior-realism-integration',
                              '5575c0e37a9d48733b5c7ed3746f1731cc2b7958634a845c87b9700ff4fc9498')
    assert before['nativeSourceEvidence']['baseNativeReport'] == after['nativeSourceEvidence']['baseNativeReport']
    assert after_proof['nativeSummary']['excludedDonors'] == ['R20_CURVED_GRASS', 'R23_CREAM_ROOF']
    assert after_proof['nativeSummary']['originalGrassMembersPreserved'] == 8949
    assert after_proof['nativeSummary']['grassMemberMutations'] == 0
    source_audit = pin(ROOT / 'output/unreal/exterior-realism-clean-integration-20261002-r27-editor-r13-source-audit/cpu-native-source-audit.json')
    comparisons, cards = [], []
    for i, (x, y, finding) in enumerate(zip(before['cases'], after['cases'], FINDINGS)):
        baseline = case_proof(x, BASE_PIDS[i])
        candidate = case_proof(y, NEW_PIDS[i])
        rb, ra = read(x['originalRuntimePath']), read(y['originalRuntimePath'])
        assert x['sourceCamera'] == y['sourceCamera'] and x['observed']['actualCamera'] == y['observed']['actualCamera']
        assert rb['renderSettings'] == ra['renderSettings'] and rb['rhi'] == ra['rhi'] == 'Metal'
        assert rb['shaderPlatform'] == ra['shaderPlatform'] == 'METAL_SM6'
        assert rb['screenshotPixels'] == ra['screenshotPixels'] == [1920, 1080]
        assert rb['warmupFrames'] == ra['warmupFrames'] == 2400
        assert rb['requestedBenchmarkFrames'] == ra['requestedBenchmarkFrames'] == 300
        assert rb['screenshotKind'] == ra['screenshotKind'] == 'current-scene-render-target-preserving-view-history'
        pb, pa = rb['finalViewPostProcessSettings'], ra['finalViewPostProcessSettings']
        differing_pp = [k for k in pb if pb[k] != pa[k]]
        assert set(pb) == set(pa) and differing_pp == ['renderThreadPreExposure']
        pp_policy = {k: v for k, v in pb.items() if k != 'renderThreadPreExposure'}
        evb, eva = pb['renderThreadPreExposure']['exposureEV'], pa['renderThreadPreExposure']['exposureEV']
        exposure = {'mode': 'automatic-unlocked', 'beforeEV': evb, 'afterEV': eva, 'deltaEV': eva-evb, 'fixedExposureComparison': False}
        for case in (x, y):
            facts, focus = case['observed']['frameIntervalFacts'], case['observed']['foregroundTimingFacts']
            assert facts['status'] == 'measured' and facts['sampleCount'] == focus['sampleCount'] == 300
            assert focus['gameWindowActiveSamples'] == focus['sceneViewportKeyboardFocusSamples'] == 300
            assert focus['applicationForegroundSamples'] == 0
        timing = {'baseline': x['observed']['frameIntervalFacts'], 'candidate': y['observed']['frameIntervalFacts'],
                  'baselineFocus': x['observed']['foregroundTimingFacts'], 'candidateFocus': y['observed']['foregroundTimingFacts'],
                  'performanceAccepted': False}
        comparisons.append({'view': VIEWS[i], 'baseline': baseline, 'candidate': candidate,
                            'sourceCamera': x['sourceCamera'], 'observedCamera': x['observed']['actualCamera'],
                            'renderSettings': rb['renderSettings'], 'composedPostProcessPolicy': pp_policy,
                            'pairChecks': {'sourceCameraExact': True, 'observedCameraExact': True, 'renderSettingsExact': True,
                                           'composedPostProcessExceptExposureExact': True, 'postProcessDifferenceFields': differing_pp,
                                           'nativeFovDirectReadbackAvailable': False, 'pixels': [1920, 1080], 'rhi': 'Metal',
                                           'shaderPlatform': 'METAL_SM6', 'warmupFrames': 2400, 'benchmarkFrames': 300},
                            'exposure': exposure, 'visualFindings': finding, 'editorTimingObservation': timing,
                            'shaderReadiness': {'errorsBoth': [], 'pendingShaderCountAtCaptureObserved': False,
                                               'noErrorLogIsFullReadinessProof': False}})
        title, first, second = html.escape(finding['title']), url(baseline['originalPng']['path']), url(candidate['originalPng']['path'])
        cards.append(f'''<section class="card" id="view-{i}"><div class="heading"><h2>{title}</h2><span>R22c → R27a</span></div>
<div class="compare" data-view="{VIEWS[i]}"><img class="original" src="{first}" alt="Referenčný pôvodný PNG R22c: {title}"><img class="candidate" src="{second}" alt="Pôvodný PNG R27a: {title}"><div class="divider"></div><span class="tag before">R22c · pôvodný PNG</span><span class="tag after">R27a · pôvodný PNG</span></div>
<div class="controls"><button type="button" data-value="0">R22c</button><input type="range" min="0" max="100" value="50" aria-label="Podiel záberu R27a: {title}"><button type="button" data-value="100">R27a</button><output>50 % nový</output></div>
<div class="notes"><p><b>Čo vidno:</b> {html.escape(finding['finding'])}</p><p><b>Čo stále prekáža:</b> {html.escape(finding['limits'])}</p></div>
<details><summary>Kamera a skutočné merania</summary><p>Referenčný proces {BASE_PIDS[i]} / R27a {NEW_PIDS[i]} · oba exit 0 · Metal SM6 · 1920 × 1080 · 2 400 zahrievacích + 300 meraných snímok.</p>
<p>Zdrojová aj pozorovaná poloha a smer kamery, renderovacie nastavenia a zložené PP okrem expozície sú presne rovnaké. Natívny readback FOV chýba. Automatická expozícia: {evb:.6f} → {eva:.6f} EV (Δ {eva-evb:+.6f}); expozícia nebola uzamknutá.</p>
<p>Priemerný interval snímok: {timing['baseline']['meanMs']:.3f} → {timing['candidate']['meanMs']:.3f} ms. V oboch behoch bolo herné okno aktívne a malo fokus počas 300/300 snímok; systémové app-foreground bolo 0/300. Tieto pozorovania nie sú výkonnostným prijatím.</p>
<p><a href="{first}">PNG R22c</a> <code>{baseline['originalPng']['sha256']}</code><br><a href="{second}">PNG R27a</a> <code>{candidate['originalPng']['sha256']}</code></p></details></section>''')
    template = TEMPLATE.read_text()
    style = re.search(r'<style>(.*?)</style>', template, re.S).group(1)
    script = re.search(r'<script>(.*?)</script>', template, re.S).group(1)
    nav = ''.join(f'<a href="#view-{i}">{html.escape(f["title"])}</a>' for i, f in enumerate(FINDINGS))
    page = f'''<!doctype html><html lang="sk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>R27a · štyri pôvodné porovnania s R22c</title><style>{style}</style>
<header><div class="status">Odstránená krémová strešná mriežka · plná fotorealistickosť NO_GO</div><h1>R22c a čistá scéna R27a</h1><p class="intro">Štyri spárované kamery a osem nezmenených originálnych PNG z Unreal Engine. Jasný rozdiel vidno na červenej streche susedného domu; koruny, parcely a záhrada pôsobia takmer rovnako. R27a je samostatná štvorica overených úprav postavená na R16, s vynechaním tráv R20 a strechy R23. R22c je bezprostredná obrazová referencia, nie natívny rodič R27a. Automatická expozícia sa líši.</p><nav>{nav}</nav></header>
<main>{''.join(cards)}</main><footer><p>Všetkých 8 pôvodných PNG bolo nezávisle prezretých. Obrázky neboli upravené ani generované AI. Počty zachovaných tráv, aktorov či aktív nie sú počtom detailov pozorovaných v obraze. R27a zatiaľ neobsahuje pôvodný strom R24 ani papraď R25. Husté opakované koruny, ploché zelené podklady, jednoduché byliny a kvety aj prázdne dvory zostávajú. Vizuálne zlepšenie tejto strechy nie je celková fotorealistická, výkonnostná ani Shipping akceptácia.</p><a href="{AUDIT.name}">Presný záznam pôvodu, meraní a obmedzení</a></footer><script>{script}</script></html>'''
    PAGE.write_text(page)
    receipt = {'schemaVersion': 1, 'owner': OWNER, 'status': 'actual-four-matched-editor-pairs-reviewed-roof-restoration-full-no-go',
               'producer': pin(ROOT / OWNER), 'htmlStyleAndSliderTemplate': pin(TEMPLATE),
               'baseline': {'revision': 'R22c', **before_proof}, 'candidate': {'revision': 'R27a', **after_proof},
               'sourceAudit': source_audit, 'comparisonHtml': pin(PAGE), 'comparisons': comparisons,
               'comparisonScope': {'sameImmediateNativeBase': False, 'sameOriginalR16NativeBase': True,
                                   'reference': 'Immediate previously rendered six-donor R22c scene; R27 is a separate four-donor R16-based composition.',
                                   'candidateExcludedDonors': ['R20_CURVED_GRASS', 'R23_CREAM_ROOF'],
                                   'candidateIncludesR24Tree': False, 'candidateIncludesR25Fern': False,
                                   'sourceGrassPreservationIsVisibleCoverageGain': False},
               'visualReview': {'originalImagesIndependentlyViewed': 8, 'pairedViews': 4, 'originalPngsEdited': False,
                                'boundedVisibleGainViews': ['neighbor-finish-close-r18'],
                                'almostUnchangedViews': ['exterior-canopy-close', 'exterior-parcels', 'exterior-garden'],
                                'allSceneViewAcceptance': False, 'photographicRoofRestorationClaim': False,
                                'realisticGlazingVerified': False},
               'browserVerifiedByThisReview': False, 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
               'performanceAccepted': False, 'shippingVerified': False, 'packageVerified': False,
               'activeSelectorPromotionApproved': False, 'goNoGo': 'BOUNDED_ROOF_RESTORATION; FULL_REALISM_NO_GO'}
    AUDIT.write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'audit': pin(AUDIT), 'html': pin(PAGE), 'originalImagesUnchanged': True,
                      'pairs': 4, 'images': 8, 'exposureDeltasEV': [r['exposure']['deltaEV'] for r in comparisons]}))


if __name__ == '__main__':
    main()
