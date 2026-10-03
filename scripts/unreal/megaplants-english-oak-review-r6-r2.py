#!/usr/bin/env python3
"""Record the actual, unmodified R6 original Oak image review; no UE calls."""
import datetime
import hashlib
import html
import json
import math
import os
from pathlib import Path
import shutil
import struct

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'output/unreal/megaplants-english-oak-20261002-r1'
NATIVE = ROOT / 'output/unreal/megaplants-english-oak-native-20261002-r3'
SUITE = ROOT / 'output/unreal/exterior-validation-20260930-r1/qa/editor-pilot-oak-whole-D-scene-r6-1790933946698-mHzz1l'
OUTPUT = ROOT / 'output/unreal/megaplants-english-oak-20261002-r6-review-r2'
OWNER = 'scripts/unreal/megaplants-english-oak-review-r6-r2.py'
VIEW = 'english-oak-original-D-close-r6'
MAP = '/Game/Brezi/EnglishOakPilot20261002R3/Maps/EnglishOakPilotR6'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def pin(path):
    path = Path(path).resolve()
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return {'path': str(path), 'sha256': digest.hexdigest(), 'bytes': path.stat().st_size}


def check_pin(path, digest):
    result = pin(path)
    require(result['sha256'] == digest, 'Selected original receipt changed: ' + str(path))
    return result


def write(path, value):
    with path.open('x') as stream:
        stream.write(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def variants(inspection):
    rows = []
    for layer in inspection['usdLayers']:
        name = Path(layer['source']['path']).name
        if 'Forest_01_' not in name:
            continue
        bound = layer['defaultTimeRootBoundsSourceUnits'][0]['bounds']
        size = [b - a for a, b in zip(bound['min'], bound['max'])]
        instancer = layer['pointInstancers'][0]
        prototypes = [p for p in instancer['prototypes'] if p['instances'] > 0]
        unique = sum(p['fanTriangulatedCount'] for p in prototypes)
        expanded = sum(p['instances'] * p['fanTriangulatedCount'] for p in prototypes)
        require(expanded == layer['assemblyExpandedFanTrianglesSourceEstimate'], 'Source expansion census differs')
        require(expanded + layer['treeBaseFanTriangles'] == layer['basePlusExpandedFanTrianglesSourceEstimate'], 'Source total census differs')
        require(layer['stageUpAxis'] == 'Y' and layer['metersPerUnit'] == 1.0, 'Source units changed')
        rows.append({
            'variant': name[-5], 'source': layer['source'], 'rootPrim': layer['rootPrims'][0],
            'upAxis': 'Y', 'metersPerUnit': 1.0, 'boundsMetres': bound,
            'sizeXHeightZMetres': size, 'maximumHorizontalSpanMetres': max(size[0], size[2]),
            'wholeEnvelopeWidthToHeightRatio': max(size[0], size[2]) / size[1],
            'pointInstancerMembers': instancer['instanceCount'], 'usedUniquePrototypes': len(prototypes),
            'baseSourceFanTriangles': layer['treeBaseFanTriangles'],
            'uniqueUsedPrototypeSourceFanTriangles': unique,
            'basePlusUniqueUsedPrototypeSourceFanTriangles': unique + layer['treeBaseFanTriangles'],
            'expandedAssemblySourceFanTriangleEstimate': expanded,
            'basePlusExpandedSourceFanTriangleEstimate': expanded + layer['treeBaseFanTriangles'],
            'sourceTextureAssetCount': layer['sourceMaterialTextureAssetCount'],
            'nativeImportedHere': name.endswith('_D.usd'),
            'nativeGeometryCompleteMeasured': False, 'runtimeTriangleCountMeasured': False,
        })
    require([r['variant'] for r in rows] == ['A', 'B', 'C', 'D'], 'Whole variants differ')
    return rows


def main():
    receipt_pins = [
        check_pin(SUITE / 'editor-pilot-suite.json', 'baea27ddfe130d2d3031cdadd43f4ca25d70f6f02b62b873da8f49cd479b750c'),
        check_pin(NATIVE / 'oak-usd-scene-native-report-r6.json', '933739a45dad7d95babb3dfc77231b2126ed9c0f022f8dba9c00d01ffc1633e9'),
        check_pin(NATIVE / 'root-native-scene-success-byte-audit-r6-r1.json', '1846bb514c8e78619df80f6e361646bab391f78783efce3a0cc7f9aa91efb92c'),
        check_pin(SOURCE / 'usd-source-inspection-r1.json', 'b9b0d557c8a8836f66424b7ebc06b8723adac763a1ac9ea0b2cfe0d2ff8e3d1a'),
        check_pin(SOURCE / 'source-extraction-receipt.json', 'f54766f8e5bc0f40c134bc89a6a14b0473db5aae1ca39ab050d036fcf899324d'),
    ]
    suite = read(SUITE / 'editor-pilot-suite.json')
    require(suite['errors'] == [] and suite['sourceInputsUnchanged'] is True and len(suite['cases']) == 1, 'Actual suite did not close unchanged')
    case = suite['cases'][0]
    process_path = Path(case['processReceiptPath'])
    receipt_pins.append(check_pin(process_path, 'd7555087fdd7dd2cd4496c0535e87727294eb7284634b347dc219acbf21c7ee8'))
    process = read(process_path)
    require(case == process, 'Actual suite/process rows differ')
    require(case['outcome'] == {'code': 0, 'signal': None, 'pid': 33231}, 'Actual Editor outcome differs')
    require(case['view'] == VIEW and case['argv'][2] == MAP and '-BreziWalkAudit' not in case['argv'], 'Wrong scene/view or walking audit scope')
    require(suite['probeMap'] == MAP and suite['walkingAuditRequested'] is False, 'Pilot map/scope changed')
    runtime_path, image_path = Path(case['originalRuntimePath']), Path(case['originalCapturePath'])
    runtime_pin = check_pin(runtime_path, case['originalRuntimeSha256'])
    image_pin = check_pin(image_path, case['originalCaptureSha256'])
    require(image_pin['sha256'] == 'a49de847f05b79e575fea31e523c7c3df80f1bb753ed8d236f0bc3cfaa90072b', 'Wrong original PNG')
    receipt_pins += [runtime_pin, image_pin, pin(Path(case['runtimeLogPath'])), pin(Path(case['stdoutPath']))]
    runtime = read(runtime_path)
    header = image_path.read_bytes()[:24]
    require(header[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>II', header[16:24]) == (1920, 1080), 'Original PNG dimensions differ')
    require(runtime['status'] == 'capture-complete' and runtime['processId'] == 33231, 'Runtime capture/PID differs')
    require(runtime['buildConfiguration'] == 'Development' and runtime['rhi'] == 'Metal' and runtime['shaderPlatform'] == 'METAL_SM6', 'Runtime transport differs')
    require(runtime['activeView'] == VIEW and runtime['screenshotSaved'] and runtime['screenshotPixels'] == [1920, 1080], 'Wrong native capture')
    require(runtime['walking']['presentationCamera']['eyeCm'] == [2000, -2800, 700], 'Actual camera changed')
    require(runtime['warmupFrames'] == 2400 and runtime['requestedBenchmarkFrames'] == 300, 'Runtime sampling configuration differs')
    require(runtime['walking']['worldContractValidated'] is False and case['shaderAndLoadErrors'] == [], 'Unexpected scope or native log failure')
    settings = runtime['renderSettings']
    require(all(settings[k] == 3 for k in ['sg.GlobalIlluminationQuality','sg.ShadowQuality','sg.ReflectionQuality','sg.FoliageQuality','sg.PostProcessQuality','sg.EffectsQuality']), 'Recipe4 quality changed')
    require(settings['r.ScreenPercentage'] == 100 and settings['r.TSR.History.ScreenPercentage'] == 200, 'Runtime resolution policy differs')
    before_path, after_path = SUITE / 'inputs-before.json', SUITE / 'inputs-after.json'
    before, after = read(before_path), read(after_path)
    require(before == after and len(before) == 8632, 'Full recorded pre/post closure differs')
    before_pin, after_pin = pin(before_path), pin(after_path)
    require(before_pin['sha256'] == after_pin['sha256'] == suite['inputClosureBefore']['sha256'], 'Pre/post input receipt bytes differ')
    receipt_pins += [before_pin, after_pin]
    extraction = read(SOURCE / 'source-extraction-receipt.json')
    original_source_pins = []
    for expected in extraction['files']:
        current = check_pin(expected['path'], expected['sha256'])
        require(current['bytes'] == expected['bytes'], 'Original source file bytes differ')
        original_source_pins.append(current)
    census = variants(read(SOURCE / 'usd-source-inspection-r1.json'))
    observations = [
        'The complete visible tree has a narrow, young-looking silhouette with a thin trunk, irregular lateral twigs and separated small leaf clusters. Large gaps remain across the crown.',
        'The source D is 8.498m high. This original image does not provide a broad mature oak crown or establish an exterior realism improvement.',
        'Leaves and bark have limited visible surface detail at this framing; the original USD contains constant materials and no texture assets. Photographic bark/leaf fidelity is not established.',
        'The neutral finite ground plane is visibly plain and its outer edge is apparent against the horizon. Its shadow confirms a rendered scene but gives no realistic garden-ground evidence.',
        'The actual camera is 7m above the origin, looking from approximately 34.41m horizontal distance. It is a crown inspection view, not a human-eye-height or matched exterior comparison.',
    ]
    limits = {
        'fullMatureCanopyAppearanceAccepted': False, 'nativeAppearanceAccepted': False,
        'fullPhotorealismAccepted': False, 'performanceAccepted': False,
        'walkingCollisionAccepted': False, 'shippingVerified': False, 'packageVerified': False,
        'matchedExteriorLightingPairClaimed': False, 'fullLightingPropertyCloneClaimed': False,
        'nativeAssemblyNodesReadbackAvailable': False, 'nativeFullGeometryCornerProof': False,
        'importedNormalsTangentsPreserved': False, 'windEvaluationVerified': False,
        'treeAttributedNaniteGpuPassVerified': False, 'editorRuntimeAssemblyCvarReadbackAvailable': False,
    }
    review = {
        'schema': 'brezi-original-licensed-english-oak-r6-independent-image-review-r1', 'owner': OWNER,
        'recordedAtUtc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'status': 'actual-original-image-reviewed-NO_GO-for-mature-canopy-and-full-realism',
        'reviewEvidence': 'Human-readable agent visual observation of the actual original PNG, plus independently checked bounded artifact/runtime hashes; no new UE execution.',
        'producer': pin(__file__), 'inputArtifacts': receipt_pins,
        'originalFiles': original_source_pins, 'originalPixelsModified': False,
        'actualRuntime': {'processId': 33231, 'outcome': case['outcome'], 'mapArgument': MAP, 'activeView': VIEW,
                         'cameraEyeCm': [2000,-2800,700], 'sourceTargetCm': [0,0,650], 'sourceHorizontalFovDegrees': 58,
                         'nativeFovReadbackAvailable': False, 'cameraHeightMetres': 7,
                         'cameraHorizontalDistanceMetres': math.hypot(20,28), 'build': 'Development', 'rhi': 'Metal',
                         'shaderPlatform': 'METAL_SM6', 'warmupFrames': 2400, 'benchmarkFrames': 300,
                         'screenshotPixels': [1920,1080], 'renderSettings': settings,
                         'renderThreadAntiAliasing': runtime['finalViewPostProcessSettings']['renderThreadAntiAliasing'],
                         'focusDuringBenchmark': runtime['focusDuringBenchmark'], 'frameIntervalFacts': runtime['frameInterval'],
                         'performanceInterpretation': 'Retained Editor observations; application foreground 0/300, no performance acceptance or Shipping comparison.',
                         'nativeShaderAndLoadLogErrors': case['shaderAndLoadErrors'],
                         'legacyExteriorLightingFixtureDiagnostic': runtime['exteriorLighting'],
                         'legacyDiagnosticInterpretation': 'The original main-scene fixture controller reports missing EXT-TERRACE-WALL-01 in this isolated probe map; no matched exterior fixture proof is claimed.',
                         'nativeStartupReadback': suite['nativeSourceEvidence']['nativeStartupReadback']},
        'recordedInputClosure': {'fileCount': 8632, 'before': before_pin, 'after': after_pin, 'recordedRowsEqual': True,
                                'all8632FilesIndependentlyRehashedInThisReview': False,
                                'rootWrapperPrePostByteValidationReported': True},
        'visualObservations': observations, 'wholeVariantSourceCensus': census,
        'nextSourceCandidate': {'variant': 'C', 'reason': 'Largest horizontal source envelope (6.325m) and widest envelope-to-height ratio, 505 authored instances, 16.607M expanded source estimate. A is taller/narrower; B has the highest expanded estimate (21.604M).',
                                'selectionBasis': 'Original USD bounds and instancer census only; no opaque leaf occupancy, botanical age, material fidelity or runtime triangle measurement.',
                                'authorizedNativeImportInThisProducer': False, 'additionalDownloadsPerformed': False},
        'limits': limits,
    }
    OUTPUT.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(__file__, OUTPUT / 'review-producer-source.py')
    write(OUTPUT / 'image-review.json', review)
    image_relative = os.path.relpath(image_path, OUTPUT)
    def link(path, label):
        return '<a href="' + html.escape(os.path.relpath(path, OUTPUT), quote=True) + '">' + html.escape(label) + '</a>'
    table = ''.join('<tr><td>' + r['variant'] + '</td><td>' + f"{r['sizeXHeightZMetres'][1]:.3f}" + '</td><td>' + f"{r['sizeXHeightZMetres'][0]:.3f} × {r['sizeXHeightZMetres'][2]:.3f}" + '</td><td>' + str(r['pointInstancerMembers']) + '</td><td>' + format(r['basePlusUniqueUsedPrototypeSourceFanTriangles'], ',') + '</td><td>' + format(r['basePlusExpandedSourceFanTriangleEstimate'], ',') + '</td></tr>' for r in census)
    document = '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Original English Oak D · actual R6 review</title><style>body{margin:0;background:#111720;color:#e7ecf4;font:16px/1.6 system-ui}main{max-width:1280px;margin:auto;padding:28px}h1{font-size:30px;margin:0}p{max-width:1000px}.pill{display:inline-block;background:#56342a;padding:4px 12px;border-radius:7px}a{color:#9fccff}figure{margin:24px 0}img{display:block;width:100%;height:auto}figcaption{padding:12px;background:#1e2837;font-size:14px}.zoom{overflow:auto}figure:has(#natural:checked) .zoom img{width:1920px;max-width:none}table{border-collapse:collapse;width:100%;font-size:14px}td,th{text-align:left;border-bottom:1px solid #344354;padding:9px}code{overflow-wrap:anywhere}li{margin-bottom:8px}</style><main><h1>Original English Oak D · actual R6 image</h1><p class="pill">NO_GO for the mature canopy and full realism goal</p><p>One original Editor-game Development capture. No paired exterior comparison; no pixel changes. The thin, irregular tree is visible, but its sparse young-looking crown does not solve the mature canopy goal.</p><figure><label><input id="natural" type="checkbox"> View original pixels at 1920 × 1080 (scroll horizontally)</label><div class="zoom"><img src="''' + html.escape(image_relative, quote=True) + '''" alt="Actual original English Oak D native R6 capture"></div><figcaption>PID 33231 · Metal / METAL_SM6 · 1920 × 1080 · eye [2000, −2800, 700] cm · target [0, 0, 650] cm · source FOV58 · Recipe4 / Cinematic · warm2400 / sample300. Camera height 7m; not a human-eye-height view. Original PNG SHA256 <code>''' + image_pin['sha256'] + '''</code>.</figcaption></figure><h2>Independent visual observations</h2><ul>''' + ''.join('<li>' + html.escape(x) + '</li>' for x in observations) + '''</ul><h2>Original whole variants — source only</h2><table><thead><tr><th>Variant</th><th>Height m</th><th>Envelope X × Z m</th><th>Instances</th><th>Base + unique prototype fan tris</th><th>Base + expanded estimate</th></tr></thead><tbody>''' + table + '''</tbody></table><p>C is the source candidate for a broader crown. The source envelope/census does not establish opaque leaf coverage, botanical maturity, native geometry completeness or runtime cost. All variants retain the same constant-material limitation; no C import is authorized by this review.</p><h2>Evidence boundary</h2><p>Actual native scene loaded and captured, with no shader/load-log errors reported. The recorded 8,632 input rows and receipt hashes are equal before/after. This review independently hashes its bounded artifacts and all nine original extracted files, without repeating the entire project hash audit.</p><p>Application foreground was 0/300; window active and scene focus were 300/300. Frame samples remain observations, with performance acceptance false. Original main-scene fixture diagnostics report a missing EXT-TERRACE-WALL-01 in the separate map; no matched exterior fixture proof is claimed.</p><p>Native assembly-node/full-corner readback, imported N/T preservation, wind, tree-attributed Nanite GPU execution, walking/collision, Shipping/package and full photorealism remain unverified. Commandlet startup AllowAssemblies=1/Foliage=0 was recorded; the unchanged Editor recorder does not report the runtime assembly cvar.</p><p>''' + link(image_path, 'Original PNG') + ' · ' + link(runtime_path, 'Original runtime JSON') + ' · ' + link(process_path, 'Actual Editor process') + ' · ' + link(SUITE / 'editor-pilot-suite.json', 'Actual suite') + ' · <a href="image-review.json">Independent review JSON</a></p></main></html>'''
    with (OUTPUT / 'index.html').open('x') as stream:
        stream.write(document)
    artifact_pins = [pin(OUTPUT / n) for n in ['review-producer-source.py','image-review.json','index.html']]
    require(all(pin(x['path']) == x for x in receipt_pins + original_source_pins), 'Read-only inputs changed during production')
    write(OUTPUT / 'review-artifact-receipt.json', {'schema': 'brezi-original-oak-r6-image-review-artifacts-r1', 'owner': OWNER,
          'status': 'original-artifacts-unchanged-review-created', 'producer': pin(__file__), 'artifacts': artifact_pins,
          'boundedOriginalInputsUnchanged': True, 'unrealExecuted': False, 'originalPixelsModified': False,
          'fullRealismAccepted': False, 'performanceAccepted': False})
    print(json.dumps({'output': str(OUTPUT), 'review': pin(OUTPUT / 'image-review.json'), 'html': pin(OUTPUT / 'index.html'),
                      'receipt': pin(OUTPUT / 'review-artifact-receipt.json'), 'originalPng': image_pin, 'status': review['status']}))


if __name__ == '__main__':
    main()
