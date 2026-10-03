"""Additive exterior materials: CC0 plants/PBR and licensed georeferenced ortho.

This module never changes a source material, actor, map, lighting or collision.
``build_materials(vegetation_manifest, ortho_manifest=None)`` returns materials
and a saved-input/graph report; the optional ortho is distant BaseColor only. The
caller saves/reloads its map and calls ``verify_materials(report)`` afterwards.
Atlas foliage is masked (including shadows), not translucent. Wind is omitted:
source atlas UVs do not provide a verified per-vertex root attachment weight.
"""
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
from types import SimpleNamespace
import re
import struct
import zlib

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-materials.py'
PREFIX = '/Game/Brezi/Exterior20260926'
GROUND_ASSETS = ROOT / 'output/unreal/exterior-ground-assets-20260926-r2'
TAG = 'BreziExterior:'
CONTEXT_KEYS = {'context_meadow', 'context_fallow', 'context_crop', 'context_arable', 'context_track',
                'context_garden_soil', 'context_soil_exposure', 'context_mulch', 'context_distant_terrain', 'context_parcel_line',
                'context_boundary_post', 'context_vine_post', 'context_wire', 'context_village_wall',
                'context_village_roof', 'context_village_darkroof'}
ROOTS = ('BASE_COLOR', 'NORMAL', 'ROUGHNESS', 'METALLIC', 'SPECULAR',
         'AMBIENT_OCCLUSION', 'OPACITY_MASK', 'SUBSURFACE_COLOR', 'OPACITY',
         'WORLD_POSITION_OFFSET', 'EMISSIVE_COLOR')
FIELD_MACRO_KEYS = {'context_meadow','context_fallow','context_crop','context_arable'}
PROJECTION_KEYS = FIELD_MACRO_KEYS | {'context_track'}
AUTHORED_FOLIAGE_KEYS = {'garden_blade_green', 'garden_plume_silk', 'garden_lavender_violet',
                         'garden_petal_rose', 'lawn_natural_blade', 'canopy_understory_stem'}
DITHER_FUNCTION = '/Engine/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA.DitherTemporalAA'
GROUND_ORTHO_BLEND_CM = (5000., 15000.)
SOIL_EXPOSURE_FADE_CM = (4000., 10000.)
FLOOR_ALBEDO_SHA = '9ecd60bb97fa26139de6729b4baa817672acdee34f1853618c8930dde7833da7'
FLOOR_ENCODING_PROOF = ROOT/'output/unreal/exterior-texture-encoding-probe-analysis-20260930-r2/diagnostic.json'
FLOOR_ENCODING_PROOF_SHA = 'c1ab90a731e9baafed80f6326cc05278e0db0b21f7e8160f7672b13cd3cf1f70'
CONTEXT_ENCODING_PROOF = ROOT/'output/unreal/exterior-texture-encoding-context-probe-20260930-r2/native-report.json'
CONTEXT_ENCODING_PROOF_SHA = '888c64e51705b71ef4dcd01f1fc42b1bfb40c63a3959daa77d7247a778c8112c'
CONTEXT_ENCODING_DIAGNOSTIC = ROOT/'output/unreal/exterior-texture-encoding-context-analysis-20261001-r1/diagnostic.json'
CONTEXT_ENCODING_DIAGNOSTIC_SHA = 'e78a81a31e88808d5f45fa73de82dff855816f4da488155993d0a6a9c4084b60'
CONTEXT_ENCODING_SOURCES = {
    '5b2aa6ce68bf82c1ae3b3433eeefc2a4ec6aae441740b6fbc42db16a2e2597b0':
        ('farm_soil', 'ground', 'https://polyhaven.com/a/farm_soil', {'context_arable','context_garden_soil','context_soil_exposure'}),
    '7b235e32340475f582baea7f5deb1b452f118c5ae61a68dca4001b0f7fbf97d3':
        ('nettle', 'foliage', 'https://polyhaven.com/a/nettle_plant', {'ph_nettle_plant'}),
    '78a6bc3b6465277379cc7db062316ca34fd9f6334b112b0c279a1033d68c77e7':
        ('tree_small_02_trunk', 'bark', 'https://polyhaven.com/a/tree_small_02', {'ph_tree_small_02_trunk'}),
    'fc386b9d205ba38fc7cda66a2499680e6443a7b3fc91496a3d5890e4f98f71a4':
        ('shrub_04', 'foliage', 'https://polyhaven.com/a/shrub_04', {'ph_shrub_04'}),
    '2bd96cd167ea4a79a68a98b5de3b33be426c1d272024cde39bca9e8b98a4a33d':
        ('periwinkle', 'foliage', 'https://polyhaven.com/a/periwinkle_plant', {'ph_periwinkle_plant'}),
}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def native_enum(kind, token):
    names = [n for n in dir(kind) if n.replace('_', '').replace('MSM', '').replace('MATUSAGE', '') == token]
    require(len(names) == 1, 'Cannot resolve native material enum: ' + token)
    return getattr(kind, names[0])


def floor_encoding_inputs():
    """Pin the isolated Metal float32 proof, never change its source pixels."""
    require(sha(FLOOR_ENCODING_PROOF)==FLOOR_ENCODING_PROOF_SHA,'Floor source encoding native proof drift')
    proof=json.loads(FLOOR_ENCODING_PROOF.read_text())
    require(proof['status']=='VERIFIED_NATIVE_SOURCE_ENCODING_MISMATCH'
            and proof['accuracy']['stableSamplesPassing']==proof['accuracy']['stableSamplesTested']==12
            and proof['accuracy']['correctedStableMaximumAbsoluteError']<.015
            and proof['interpretation']['r8AndProviderPinsUnchanged'] is True,
            'Floor source encoding native proof failed')
    directory=Path(proof['sourceStudy']['path']);prepared=json.loads((directory/'prepared.json').read_text())
    inputs={str(FLOOR_ENCODING_PROOF):FLOOR_ENCODING_PROOF_SHA}
    for name in ('prepared.json','native-report.json','native-process.json','native.log','provider-samples.json','probe-source.py'):
        path=directory/name;inputs[str(path)]=sha(path)
    sealed=next(row['files'] for row in proof['preservedAttempts'] if row['revision']=='r7')
    require(all(sealed.get(p)==h for p,h in inputs.items() if p!=str(FLOOR_ENCODING_PROOF)),
            'Floor source encoding native evidence bytes differ')
    # Keep the actual immutable native script and copied packages. The live
    # diagnostic controller is not a replay dependency of the recorded proof.
    for p,h in {**prepared['inputPins'],**prepared['protectedR8AndProviderPins']}.items():
        path=Path(p)
        if path.is_relative_to(ROOT) and path!=ROOT/'scripts/unreal/exterior-texture-encoding-probe.py':inputs[p]=h
    require(all(Path(p).is_relative_to(ROOT) and sha(p)==h for p,h in inputs.items()),
            'Floor source encoding proof input drift')
    return inputs


def context_encoding_inputs():
    """Use only the five albedos measured against source-selected GPU samples."""
    require(sha(CONTEXT_ENCODING_PROOF)==CONTEXT_ENCODING_PROOF_SHA,'Context source encoding native proof drift')
    require(sha(CONTEXT_ENCODING_DIAGNOSTIC)==CONTEXT_ENCODING_DIAGNOSTIC_SHA,'Context source encoding diagnostic drift')
    diagnostic=json.loads(CONTEXT_ENCODING_DIAGNOSTIC.read_text())
    require(diagnostic['status']=='CAUSAL_SRGB_SOURCE_ENCODING_PROVEN_FOR_EXACT_FIVE_R8_ALBEDOS'
            and set(diagnostic['provenAlbedoSha256'])==set(CONTEXT_ENCODING_SOURCES),
            'Context source encoding diagnostic scope differs')
    proof=json.loads(CONTEXT_ENCODING_PROOF.read_text());directory=CONTEXT_ENCODING_PROOF.parent
    prepared=json.loads((directory/'prepared.json').read_text());process=json.loads((directory/'native-process.json').read_text())
    require(proof['status']=='native-source-encoding-and-gpu-samples-recorded-no-material-correction'
            and proof['gpuSamplingVerified'] is True and proof['r8AssetsUnchanged'] is True
            and proof['providerPixelsConvertedOrEdited'] is False and process['returncode']==0
            and proof['nativeProcessId']==process['pid']
            and proof['preparedSha256']==process['preparedSha256']==sha(directory/'prepared.json')
            and proof['gpuLinearControl']['actual']==[.125,.25,.5,0.],
            'Context source encoding native measurement failed')
    require(set(proof['textures'])=={row[0] for row in CONTEXT_ENCODING_SOURCES.values()},'Context source encoding measured scope differs')
    for source_sha,(name,kind,url,keys) in CONTEXT_ENCODING_SOURCES.items():
        row=proof['textures'][name];accuracy=row['sourceOnlyStableComparison']
        require(prepared['textures'][name]['sourcePixels']['sha256']==source_sha
                and prepared['textures'][name]['sourcePage']==url
                and set(prepared['textures'][name]['r8MaterialKeys'])==keys
                and accuracy['count']==(8 if name=='shrub_04' else 12)
                and accuracy['absoluteToleranceRgb']==.015
                and accuracy['explicitSourceSRGBMaxAbsLinearRgbError']<=.015
                and accuracy['originalMaxAbsLinearRgbError']>.25
                and row['allSamplesAlphaComparison']['originalVsExplicitMaxAbsAlphaDifference']==0.,
                'Context source encoding causal RGB/unchanged alpha evidence differs: '+name)
        original=row['original'];changed=row['duplicate']['after']
        settings=copy.deepcopy(original['sourceColorSettings']);settings['encoding_override']='<TextureSourceEncoding.TSE_S_RGB: 2>'
        require(original['dimensions']==changed['dimensions']==[2048,2048]
                and original['properties']==changed['properties']
                and changed['sourceColorSettings']==settings
                and row['onlyIntendedChange']=='source_color_settings.encoding_override=TSE_S_RGB',
                'Context source encoding changed more than the measured transfer: '+name)
    inputs={str(CONTEXT_ENCODING_PROOF):CONTEXT_ENCODING_PROOF_SHA,
            str(CONTEXT_ENCODING_DIAGNOSTIC):CONTEXT_ENCODING_DIAGNOSTIC_SHA}
    for name in ('prepared.json','native-process.json'):
        path=directory/name;inputs[str(path)]=sha(path)
    for p,h in {**prepared['inputPins'],**prepared['protectedR8AndProviderPins']}.items():
        path=Path(p)
        require(sha(path)==h,'Context source encoding measured dependency drift: '+p)
        if path.is_relative_to(ROOT) and path!=ROOT/'scripts/unreal/exterior-texture-encoding-context-probe.py':inputs[p]=h
    for p,row in diagnostic['closure']['immutableEvidenceCopies'].items():inputs[p]=row['sha256']
    inputs.update(diagnostic['closure']['generatedOwnedProbeAssetPins'])
    require(all(Path(p).is_relative_to(ROOT) and sha(p)==h for p,h in inputs.items()),'Context source encoding proof input drift')
    # The process log has later TraceServer output; the immutable raw report,
    # frozen native script and original source/packages prove this RGB transfer.
    # Nettle's existing sharp alpha error is unchanged, not declared corrected.
    return inputs


def source_encoding_proof(recipe,key=None):
    source_sha=recipe.get('maps',{}).get('albedo',{}).get('sha256')
    if source_sha==FLOOR_ALBEDO_SHA and recipe.get('kind')=='ground' and recipe.get('sourceUrl')=='https://polyhaven.com/a/forest_leaves_04':
        if key is None or key=='canopy_floor_litter':return {'path':str(FLOOR_ENCODING_PROOF),'sha256':FLOOR_ENCODING_PROOF_SHA}
    if source_sha in CONTEXT_ENCODING_SOURCES:
        name,kind,url,keys=CONTEXT_ENCODING_SOURCES[source_sha]
        if recipe.get('kind')==kind and recipe.get('sourceUrl')==url and (key is None or key in keys):
            return {'path':str(CONTEXT_ENCODING_PROOF),'sha256':CONTEXT_ENCODING_PROOF_SHA}
    return None


def texture_source_encoding(role,recipe):
    encoding=recipe.get('sourceEncodingOverride','None') if role=='albedo' else 'None'
    require(encoding in ('None','sRGB'),'Unreviewed exterior source encoding')
    if encoding=='sRGB':
        require(source_encoding_proof(recipe) is not None
                and recipe.get('sourceEncodingProof')==source_encoding_proof(recipe),
                'Unproven exterior source encoding override')
    return encoding


def _ground_source(asset):
    """Resolve relocated local assets against their recorded provider hashes."""
    if asset == 'wood_chips':
        receipt = json.loads((ROOT / 'scripts/unreal/planting-surfaces/inputs.json').read_text())
        maps = {}
        for role, key in [('albedo', 'Diffuse'), ('normal', 'nor_gl'), ('roughness', 'Rough')]:
            spec = receipt['maps'][key]; path = ROOT / spec['path']; raw = path.read_bytes()
            require(hashlib.md5(raw).hexdigest() == spec['md5'] and len(raw) == spec['bytes'] and hashlib.sha256(raw).hexdigest() == spec['sha256'], 'Mulch scan differs from provider receipt')
            maps[role] = {'path': str(path), 'sha256': spec['sha256']}
        return {'maps': maps, 'tileCm': receipt['material']['tileMm']/10,
                'normalConvention': 'OpenGL', 'sourceUrl': 'https://polyhaven.com/a/wood_chips', 'license': 'CC0-1.0'}
    if asset == 'farm_soil':
        source = json.loads((GROUND_ASSETS / 'manifest.json').read_text())
        require(source['license'] == 'CC0-1.0' and source['sourceUrl'] == 'https://polyhaven.com/a/farm_soil', 'Unreviewed new ground scan')
        for spec in source['maps'].values():
            raw = Path(spec['path']).read_bytes()
            require(hashlib.md5(raw).hexdigest() == spec['md5'] and len(raw) == spec['size'] and hashlib.sha256(raw).hexdigest() == spec['sha256'], 'New ground scan differs from provider receipt')
        source['tileCm'] = 200.
        return source
    lock = json.loads((ROOT / 'scripts/archviz/assets.lock.json').read_text())
    if asset not in lock['assets']:
        lock = json.loads((ROOT / 'output/archviz/assets/manifest.json').read_text())
    source = lock['assets'][asset]
    require(lock['license'] == 'CC0-1.0', 'Unreviewed ground license')
    maps = {}
    for target, role in [('albedo', 'diffuse'), ('normal', 'normal'), ('roughness', 'roughness')]:
        spec = source['maps'][role]
        path = ROOT / 'output/archviz/assets' / asset / Path(spec['path']).name
        require(path.is_file(), 'Missing local exterior ground scan: ' + str(path))
        data = path.read_bytes()
        require(hashlib.md5(data).hexdigest() == spec['md5'] and len(data) == spec['size'],
                'Local exterior ground scan differs from provider receipt: ' + str(path))
        maps[target] = {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest()}
    return {'maps': maps, 'tileCm': float(source['tileSizeMetres']) * 100,
            'normalConvention': 'OpenGL', 'sourceUrl': source['page'], 'license': lock['license']}


def context_recipes():
    sparse, gravel, soil, mulch = (_ground_source(k) for k in ('sparse_grass', 'gravel_floor_02', 'farm_soil', 'wood_chips'))
    lawn = json.loads((ROOT / 'scripts/unreal/lawn-ground/reference.json').read_text())
    green = {'maps': {k: {'path': str(ROOT / lawn['maps'][v]['path']), 'sha256': lawn['maps'][v]['sha256']}
                      for k, v in [('albedo', 'Diffuse'), ('normal', 'nor_gl'), ('roughness', 'Rough')]},
             'tileCm': 140., 'normalConvention': 'OpenGL', 'license': 'CC0-1.0',
             'sourceUrl': lawn['provider']['page'], 'technique': 'Procedural', 'scanClaim': False}
    recipes = {}
    for key, source, tint, strength, scale, cover in [
        ('context_meadow', sparse, [.86, .94, .86], .65, .78, [.70, .78]),
        ('context_fallow', sparse, [.86, .85, .78], .70, .74, [.30, .38]),
        ('context_crop', sparse, [.82, .88, .76], .45, .72, [.70, .78]),
        ('context_arable', soil, [.90, .88, .82], .75, .35, [.04, .10]),
        ('context_track', gravel, [.82, .78, .70], .65, .28, None),
        ('context_garden_soil', soil, [.94, 1., 1.04], .85, .65, [.025, .11]),
        ('context_soil_exposure', soil, [.65, .53, .40], .75, .30, None),
        ('context_mulch', mulch, [.94, .98, 1.], 1., .62, None),
        ('context_distant_terrain', sparse, [1., 1., 1.], .0, 1., None),
    ]:
        recipes[key] = {**copy.deepcopy(source), 'kind': 'ground', 'tint': tint,
                        'normalStrength': strength, 'yawDegrees': 0.0,
                        'macroStrength': .05, 'albedoScale': scale, 'cropRows': key in ('context_crop', 'context_arable'),
                        'artDirection': 'R8 separates meadow, fallow, crop and cultivated soil with restrained saturation and distinct ground cover; bounded artist response, not measured site reflectance'}
        if cover:
            recipes[key].update(groundCover=copy.deepcopy(green), coverRange=cover)
    recipes['context_distant_terrain']['terrain'] = True
    recipes['context_soil_exposure'].update(featherUV=True, opacityMaskClipValue=.333,
        artDirection='R9 dark earth exposure with authored UV0.x coverage and the native engine temporal dither; original ground is retained below the visual overlay')
    recipes['context_parcel_line'] = {'kind': 'marker', 'linearColor': [.53, .52, .46], 'roughness': .96}
    recipes['context_boundary_post'] = {'kind': 'wood', 'linearColor': [.19, .16, .12], 'roughness': .89}
    recipes['context_vine_post'] = {'kind': 'wood', 'linearColor': [.17, .16, .135], 'roughness': .88}
    recipes['context_wire'] = {'kind': 'metal', 'linearColor': [.12, .13, .135], 'roughness': .7, 'metallic': .8}
    for key, palette, roughness in [('context_village_wall', [.25, .245, .225], .88),
                                    ('context_village_roof', [.14, .052, .027], .86),
                                    ('context_village_darkroof', [.03, .035, .037], .80)]:
        recipes[key] = {'kind': 'village', 'linearColor': palette, 'roughness': roughness, 'specular': .25,
                        'artDirection': 'R4 subdued distant plaster/tile palette with at most 5% world-space variation; building colours and heights are visual estimates, not surveyed finishes'}
    return recipes


def derivation_inputs(key, recipe):
    folder = Path(recipe['maps']['albedo']['path']).parent
    receipt_path = folder/'derivation-report.json'
    manifest_path = folder/'derived-material-manifest.json'
    require(receipt_path.is_file() and manifest_path.is_file(), 'Albedo derivation receipts missing')
    receipt = json.loads(receipt_path.read_text())
    require(receipt.get('status') == 'derived-rgb-atlases-cpu-validated-awaiting-native', 'Unexpected albedo derivation status')
    entry = receipt['materials'][key]
    require(entry['derivedAlbedo'] == recipe['maps']['albedo'], 'Derived atlas receipt differs')
    require(all(entry[field] == value for field, value in recipe['albedoDerivation'].items()), 'Albedo derivation proof differs')
    inputs = {str(receipt_path): sha(receipt_path), str(manifest_path): sha(manifest_path), **receipt['inputFiles']}
    for path, expected in inputs.items():
        resolved = Path(path).resolve()
        require(resolved.is_relative_to(ROOT) and resolved.is_file() and sha(resolved) == expected, 'Albedo derivation receipt input drift')
    return inputs


def prepare_orthophoto(path):
    """Validate the licensed export and its affine frame before any native write."""
    path = (ROOT / path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(), 'Orthophoto manifest path invalid')
    source = json.loads(path.read_text())
    require(source.get('schemaVersion') == 1 and source.get('sourceCurrencyYear') == 2024,
            'Unreviewed orthophoto schema/currency')
    license_info = source.get('license', {})
    require(license_info.get('spdx') == 'CC-BY-4.0' and license_info.get('attribution') == 'ČÚZK, 2024'
            and license_info.get('url') == 'https://creativecommons.org/licenses/by/4.0/', 'Orthophoto attribution/license missing')
    inputs = {str(path): sha(path), **source['inputFiles']}
    for filename, expected in inputs.items():
        p = Path(filename).resolve()
        require(p.is_relative_to(ROOT) and p.is_file() and sha(p) == expected, 'Orthophoto input drift: '+filename)
    frame = source['worldFrame']; axis = frame['siteAxis']; datum = frame['cadastralDatumSjtskMm']
    offset = {k: frame['sceneCenterMm'][k]+frame['housePlacement']['translationMm'][k] for k in ('x', 'y')}
    origin = [(datum[k]+axis['u'+k]*offset['x']+axis['v'+k]*offset['y'])/1000 for k in ('x', 'y')]
    require(all(abs(a-b) < 1e-7 for a,b in zip(origin, source['worldOriginNationalMetres'])), 'Orthophoto origin/frame differs')
    blend = source['materialProposal']['distanceBlendCm']
    require(isinstance(blend, list) and len(blend) == 2
            and all(isinstance(v, (int, float)) and math.isfinite(v) for v in blend)
            and tuple(blend) in ((30000, 90000), (18000, 36000)), 'Unreviewed orthophoto distance blend')
    layers = source['layers']
    require(len(layers) == 2 and {v['id'] for v in layers} == {'far16km', 'detail2km'}, 'Orthophoto layer set differs')
    for layer in layers:
        xmin,ymin,xmax,ymax = layer['bboxMetres']; width,height = xmax-xmin,ymax-ymin
        require(width > 0 and height > 0 and layer['crs'] == 'EPSG:5514', 'Orthophoto extent invalid')
        rows = layer['worldCmToUvRows']
        expected = [[axis['ux']*.01/width, -axis['vx']*.01/width, (origin[0]-xmin)/width],
                    [-axis['uy']*.01/height, axis['vy']*.01/height, (ymax-origin[1])/height]]
        require(len(rows) == 2 and all(len(row) == 3 for row in rows)
                and all(math.isfinite(v) and abs(v-expected[i][j]) < 1e-12 for i,row in enumerate(rows) for j,v in enumerate(row)),
                'Orthophoto affine mapping differs from cadastral frame')
        require(layer['sRGB'] is True and layer['pixelFormat'] == 'RGBA8' and layer['sourceCurrencyYear'] == 2024
                and layer['width'] == layer['height'] == 4096 and layer['alphaSemantic'].startswith('provider coverage'),
                'Orthophoto pixel/coverage interpretation differs')
        require(inputs.get(layer['rgbaPath']) == layer['rgbaSha256'], 'Orthophoto image not sealed by inputs')
        with Path(layer['rgbaPath']).open('rb') as stream: header = stream.read(29)
        require(header[:8] == b'\x89PNG\r\n\x1a\n' and struct.unpack('>IIBB', header[16:26]) == (4096,4096,8,6),
                'Orthophoto image is not 4096 RGBA8 PNG')
    return {'manifestPath': str(path), 'manifestSha256': sha(path), 'license': copy.deepcopy(license_info),
            'layers': copy.deepcopy(layers), 'inputFiles': inputs, 'distanceBlendCm': copy.deepcopy(blend),
            'detailEdgeFeatherCm': 10000, 'sampledCoverageThreshold': .99,
            'limitation': 'Aerial photograph includes acquisition lighting/shadows and roofs; BaseColor macro only, not a lighting-neutral reflectance measurement. Geometry evidence status remains unchanged.'}


def prepare_manifest(vegetation_manifest=None, context_overrides=None):
    recipes = context_recipes()
    if vegetation_manifest is not None:
        raw = json.loads(Path(vegetation_manifest).read_text()) if isinstance(vegetation_manifest, (str, Path)) else copy.deepcopy(vegetation_manifest)
        supplied = raw.get('materials', raw)
        require(isinstance(supplied, dict), 'Exterior material manifest must be a mapping')
        require(not (set(supplied) & CONTEXT_KEYS), 'Vegetation cannot replace context material recipes')
        recipes.update(supplied)
    for key, values in (context_overrides or {}).items():
        require(key in CONTEXT_KEYS and set(values) <= {'yawDegrees', 'tint', 'macroStrength'},
                'Unreviewed exterior context override')
        recipes[key].update(copy.deepcopy(values))
    for key, recipe in recipes.items():
        require(re.fullmatch(r'[a-z][a-z0-9_]{0,80}', key), 'Unsafe exterior material key')
        require(not ({'orthophoto', 'groundOrthophoto', 'projectionMask', 'fieldMacro', 'terrainOrthophotoCameraBlend'} & set(recipe)), 'Geographic data must use validated optional manifest')
        require(recipe.get('powerOfTwoMode') in (None,'stretch'), 'Unreviewed exterior texture resize mode')
        kind = recipe.get('kind')
        if 'sourceEncodingOverride' in recipe or 'sourceEncodingProof' in recipe:
            require(source_encoding_proof(recipe,key) is not None and recipe.get('sourceEncodingOverride')=='sRGB'
                    and recipe.get('sourceEncodingProof')==source_encoding_proof(recipe,key),
                    'Unreviewed exterior source encoding recipe')
        require(kind in ('foliage', 'bark', 'ground', 'marker', 'wood', 'metal', 'village', 'authored-foliage'), 'Unknown exterior material kind')
        if 'stochasticGround' in recipe:
            require(key=='canopy_floor_litter' and kind=='ground' and recipe['stochasticGround'] is False,
                    'Unreviewed directly registered ground recipe')
        if 'twoSided' in recipe:
            require(type(recipe['twoSided']) is bool and kind in ('foliage', 'bark', 'authored-foliage'), 'Unreviewed two-sided geometry recipe')
        if 'featherUV' in recipe:
            require(key in ('context_soil_exposure','canopy_floor_litter') and kind == 'ground' and recipe['featherUV'] is True
                    and not recipe.get('terrain') and 'groundCover' not in recipe, 'Unreviewed feathered ground recipe')
            if key=='canopy_floor_litter':
                require(recipe.get('sourceUrl')=='https://polyhaven.com/a/forest_leaves_04'
                        and recipe.get('tileCm')==150. and recipe.get('distanceFadeCm')==[12000.,18000.],
                        'Grove litter photographic scale/fade differs')
        if kind == 'authored-foliage':
            require(key in AUTHORED_FOLIAGE_KEYS and recipe.get('maps') == {} and recipe.get('twoSided') is True,
                    'Unreviewed authored foliage recipe')
            require(len(recipe.get('linearColor', [])) == 3 and all(math.isfinite(v) and 0 <= v <= 1 for v in recipe['linearColor']),
                    'Unbounded authored foliage colour')
            for field, lo, hi in [('roughness', .38, .98), ('specular', 0., .5), ('subsurfaceScale', 0., .35)]:
                require(math.isfinite(recipe.get(field, -1)) and lo <= recipe[field] <= hi, 'Unbounded authored foliage response: ' + field)
        recipe.setdefault('tint', [1., 1., 1.])
        require(len(recipe['tint']) == 3 and all(math.isfinite(x) and 0 <= x <= 2 for x in recipe['tint']), 'Invalid linear texture tint')
        if kind in ('foliage', 'bark', 'ground'):
            require(recipe.get('license') == 'CC0-1.0' and str(recipe.get('sourceUrl', recipe.get('page', ''))).startswith('https://'),
                    'Texture provenance missing: ' + key)
            require(recipe.get('normalConvention') in ('OpenGL', 'DirectX'), 'Normal convention must be explicit')
            needed = {'albedo', 'normal', 'roughness'} | ({'alpha'} if kind == 'foliage' else set())
            roles = set(recipe.get('maps', {}))
            require(needed <= roles <= needed | ({'mask'} if kind == 'foliage' else set()), 'Missing/unexpected texture roles: ' + key)
            sources = [recipe] + ([recipe['groundCover']] if 'groundCover' in recipe else [])
            for source in sources:
                require(source.get('license') == 'CC0-1.0' and source.get('normalConvention') == recipe['normalConvention'], 'Ground layer interpretation differs')
                for role, spec in source['maps'].items():
                    path = (ROOT / spec['path']).resolve()
                    require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == spec['sha256'],
                            'Exterior texture hash/path differs: ' + key + '/' + role)
                    spec['path'] = str(path)
            if key=='canopy_floor_litter':
                spec=recipe['maps']['albedo']
                with Path(spec['path']).open('rb') as stream:header=stream.read(29)
                require(recipe.get('sourceUrl')=='https://polyhaven.com/a/forest_leaves_04'
                        and spec['sha256']==FLOOR_ALBEDO_SHA and header[:8]==b'\x89PNG\r\n\x1a\n'
                        and struct.unpack('>IIBB',header[16:26])==(2048,2048,16,2),
                        'Floor source encoding requires proven original16bit RGB diffuse')
                floor_encoding_inputs()
                recipe['sourceEncodingOverride']='sRGB'
                recipe['sourceEncodingProof']={'path':str(FLOOR_ENCODING_PROOF),'sha256':FLOOR_ENCODING_PROOF_SHA}
            elif recipe['maps']['albedo']['sha256'] in CONTEXT_ENCODING_SOURCES:
                proof=source_encoding_proof(recipe,key)
                require(proof is not None,'Context source encoding recipe scope differs: '+key)
                context_encoding_inputs()
                recipe['sourceEncodingOverride']='sRGB';recipe['sourceEncodingProof']=proof
            if recipe.get('albedoDerivation'):
                proof = recipe['albedoDerivation']
                require(kind == 'foliage' and proof.get('operation') == 'nearest-opaque-rgb-padding'
                        and proof.get('opaqueThreshold') == .99 and proof.get('opaqueRGBByteExact') is True
                        and proof.get('alphaMapUnmodified') is True, 'Unreviewed albedo derivation')
                require(proof['sourceAlpha'] == recipe['maps']['alpha'], 'Derived colour alpha witness differs')
                for field in ('sourceAlbedo', 'sourceAlpha', 'sourceGenerator'):
                    spec = proof[field]; path = Path(spec['path']).resolve()
                    require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == spec['sha256'], 'Albedo derivation source drift: '+field)
                require(Path(proof['sourceGenerator']['path']).resolve() == ROOT/'scripts/unreal/exterior-alpha-dilate.py', 'Foreign albedo derivative generator')
                derivation_inputs(key, recipe)
            for field, default, lo, hi in [('albedoScale', 1., .1, 1.2), ('specular', .25, 0., .5),
                                          ('normalStrength', 1., 0., 1.5), ('subsurfaceScale', .2, 0., .35)]:
                recipe.setdefault(field, default)
                require(math.isfinite(recipe[field]) and lo <= recipe[field] <= hi, 'Unbounded material response: ' + field)
            recipe.setdefault('uvScale', 1.)
            require(math.isfinite(recipe['uvScale']) and 0 < recipe['uvScale'] <= 32, 'Invalid model UV scale')
        if kind == 'ground':
            require(1 <= recipe['tileCm'] <= 5000 and math.isfinite(recipe['yawDegrees']), 'Invalid metric ground mapping')
            require(0 <= recipe['macroStrength'] <= .4, 'Unbounded ground variation')
            if 'groundCover' in recipe:
                require(set(recipe['groundCover']['maps']) == {'albedo', 'normal', 'roughness'}, 'Incomplete ground layer')
                require(0 <= recipe['coverRange'][0] <= recipe['coverRange'][1] <= 1, 'Unbounded cover mix')
        if kind == 'foliage' or recipe.get('featherUV'):
            recipe.setdefault('opacityMaskClipValue', .333)
            require(.1 <= recipe['opacityMaskClipValue'] <= .7, 'Unbounded foliage alpha cutoff')
        if 'leafCalibration' in recipe:
            calibration = recipe['leafCalibration']
            require(key == 'ph_periwinkle_plant' and kind == 'foliage'
                    and calibration.get('operation') == 'artist-green-leaf-calibration'
                    and calibration.get('brightness') in (.78,.60) and calibration.get('saturation') == .88
                    and calibration.get('selector') == 'linear-source-green-chroma'
                    and calibration.get('providerBugFix') is False, 'Unreviewed leaf artist calibration')
            spec = calibration['sourceMaterialManifest']; p = Path(spec['path']).resolve()
            require(p.is_relative_to(ROOT) and p.is_file() and sha(p) == spec['sha256'], 'Leaf calibration source manifest drift')
            original = json.loads(p.read_text())[key]
            require(digest(original) == calibration['sourceRecipeSha256']
                    and original == {k:v for k,v in recipe.items() if k not in ('leafCalibration','sourceEncodingOverride','sourceEncodingProof')},
                    'Leaf calibration changed provider maps/response')
        require(not recipe.get('windCm', 0), 'Atlas root weights unavailable; wind must remain disabled')
    # Native garden review approved a bounded leaf-only response after the
    # immutable provider recipe and its calibration provenance are verified.
    if recipes.get('ph_periwinkle_plant', {}).get('leafCalibration'):
        recipes['ph_periwinkle_plant']['leafCalibration']['brightness'] = .60
    require(len(recipes) <= 39 + int('canopy_floor_litter' in recipes), 'Exterior material budget exceeded')
    return {'schemaVersion': 1, 'materials': recipes}


# Hashed triangular tiles use three translations with matched maps and explicit
# derivatives of the continuous metric UV. Every triangle edge shares vertices.
NOISE = '''struct EN {
float hash(float2 p){return frac(sin(dot(p,float2(127.1,311.7)))*43758.5453);}
float value(float2 p){float2 i=floor(p),f=frac(p);f=f*f*(3.0-2.0*f);
return lerp(lerp(hash(i),hash(i+float2(1,0)),f.x),lerp(hash(i+float2(0,1)),hash(i+1),f.x),f.y);}
}; EN en;
'''
MACRO = NOISE + '''return float3(en.value(Position.xy/570.0),en.value(Position.xy/2300.0+19.0),en.value(Position.xy/123.0+7.0));'''
TRIANGLE = '''float2 q=float2(UV.x-UV.y*.577350269,UV.y*1.154700538)/1.7;
float2 cell=floor(q),f=frac(q); bool upper=f.x+f.y>1.0;
float3 w=upper?float3(1.0-f.y,1.0-f.x,f.x+f.y-1.0):float3(1.0-f.x-f.y,f.x,f.y);
float2 v0=cell+(upper?float2(1,0):float2(0,0));
float2 v1=cell+(upper?float2(0,1):float2(1,0));
float2 v2=cell+(upper?float2(1,1):float2(0,1));
'''
GROUND_WEIGHTS = TRIANGLE + 'w=w*w*w; return w/max(dot(w,float3(1,1,1)),.00001);'
GROUND_PHASE = NOISE + TRIANGLE + '''float2 vertex=Phase<.5?v0:(Phase<1.5?v1:v2);
return UV+float2(en.hash(vertex),en.hash(vertex+float2(73,117)))*7.0;'''
GROUND_UV = '''float a=radians(YawDegrees),c=cos(a),s=sin(a);
return float2(c*Position.x+s*Position.y,-s*Position.x+c*Position.y)/TileCm;'''
GROUND_NORMAL = '''float a=radians(YawDegrees),c=cos(a),s=sin(a);
float3 n=normalize(float3(MapNormal.xy*Strength,max(MapNormal.z,.1)));
float3 N=normalize(VertexNormal);
float3 T=normalize(float3(c,s,-(N.x*c+N.y*s)/max(N.z,.05)));
float3 B=normalize(cross(N,T));
return normalize(T*n.x+B*n.y+N*n.z);'''
GROUND_COLOR = '''float3 color=Scan*Tint*AlbedoScale;
float variation=1.0+Strength*(Macro.x-.5)+Strength*.55*(Macro.y-.5);
float dry=smoothstep(.65,.92,Macro.y)*Strength*.25;
color=lerp(color,color*float3(1.13,1.025,.87),dry);
return saturate(color*variation*Rows);'''
MODEL_COLOR = '''float variation=.94+Random*.12;
float3 tint=lerp(float3(.97,1.015,.96),float3(1.035,.985,1.015),Random);
return saturate(Scan*Tint*tint*variation*AlbedoScale);'''
LEAF_CALIBRATION = '''float green=(Scan.g-max(Scan.r,Scan.b))/max(Scan.g,.00001);
float mask=smoothstep(.04,.18,green);
float luma=dot(Color,float3(.2126,.7152,.0722));
float3 calibrated=lerp(float3(luma,luma,luma),Color,Saturation)*Brightness;
return lerp(Color,calibrated,mask);'''
ORTHO_UV = '''float3 p=float3(Position.xy,1.0); return float2(dot(RowU,p),dot(RowV,p));'''
ORTHO_RADIAL = '''return smoothstep(BlendRange.x,BlendRange.y,length(Position.xy));'''
ORTHO_CAMERA = '''return smoothstep(BlendRange.x,BlendRange.y,length(Position-Camera));'''
GROUND_ORTHO_WEIGHT = '''float inside=(all(ProjectionUV>=0.0)&&all(ProjectionUV<=1.0))?1.0:0.0;
return DistanceBlend*inside*saturate(Permission)*step(.99,Coverage);'''
SOIL_EXPOSURE_COVERAGE = NOISE + '''float density=en.value(Position.xy/240.0+19.0)*.55;
density+=en.value(Position.xy/75.0+73.0)*.30+en.value(Position.xy/18.0+117.0)*.15;
float broken=lerp(.06,.94,smoothstep(.24,.76,density));
float near=1.0-smoothstep(FadeRange.x,FadeRange.y,length(Position-Camera));
return saturate(smoothstep(0.0,1.0,EdgeCoverage)*broken*near);'''
GROVE_LITTER_COVERAGE = '''float near=1.0-smoothstep(FadeRange.x,FadeRange.y,length(Position-Camera));
return saturate(smoothstep(0.0,1.0,EdgeCoverage)*near);'''
ORTHO_VALID = '''float inside=(all(UV>=0.0)&&all(UV<=1.0))?1.0:0.0;
return inside*step(.99,Coverage);'''
ORTHO_DETAIL_WEIGHT = '''float2 edge=min(UV,1.0-UV)*ExtentCm.xy;
return Valid*smoothstep(0.0,10000.0,min(edge.x,edge.y));'''
ORTHO_COLOR = '''float3 macro=lerp(Fallback,Far,FarValid);
macro=lerp(macro,Detail,DetailWeight);
return lerp(Fallback,macro,DistanceBlend);'''
SEASONAL_FIELD_COLOR = '''float y=dot(Source,float3(.2126,.7152,.0722));
float warmth=(Source.r-Source.g)/max(Source.r+Source.g,.00001);
float dry=smoothstep(-.02,.10,warmth);
float earth=1.0-smoothstep(.82,1.10,Source.b/max(Source.g,.00001));
float lit=smoothstep(.008,.035,y)*(1.0-smoothstep(.45,.70,y));
float w=saturate(Mask)*dry*earth*lit*.88;
float3 target=float3(.065,.115,.030)*pow(max(y,.004)/.18,.82);
float targetY=dot(target,float3(.2126,.7152,.0722));
target+=clamp(Source/max(y,.004)-1.0,-.8,.8)*targetY*.07;
target=clamp(target,0.0,.32);
return lerp(Source,target,w);'''
FIELD_MACRO_COLOR = '''float valid=(all(UV>=0.0)&&all(UV<=1.0))?1.0:0.0;
valid*=step(.99,Domain)*step(.99,Coverage);
float factor=clamp(1.0+(FactorChannel-128.0/255.0)*.70,Range.x,Range.y);
return Source*lerp(1.0,factor,saturate(Weight)*valid);'''
TERRAIN_COLOR = NOISE + '''float a=en.value(Position.xy/18000.0), b=en.value(Position.xy/70000.0+23.0);
float slope=1.0-saturate(VertexNormal.z);
float woodland=saturate(smoothstep(5000.,16000.,Position.z)*.65+slope*2.7+(b-.4)*.35);
float3 field=lerp(float3(.075,.099,.037),float3(.105,.101,.047),a*.68);
float3 wooded=lerp(float3(.023,.042,.015),float3(.041,.060,.024),a);
return lerp(field,wooded,woodland)*(.87+.25*b);'''


def _smoothstep(low, high, value):
    t = min(1., max(0., (value-low)/(high-low)))
    return t*t*(3.-2.*t)


def calibrated_leaf(color, source_rgb, brightness=.78, saturation=.88):
    """Linear-light witness; pink petals/neutral stems receive zero chroma mask."""
    mask = _smoothstep(.04,.18,(source_rgb[1]-max(source_rgb[0],source_rgb[2]))/max(source_rgb[1],.00001))
    luma = sum(a*b for a,b in zip(color, (.2126,.7152,.0722)))
    return tuple(c+(brightness*(luma*(1-saturation)+c*saturation)-c)*mask for c in color)


def prepare_seasonal_fields(path, ortho):
    """Only the separately reviewed, source-preserving geographic field study."""
    require(ortho is not None, 'Seasonal fields require licensed orthophoto')
    path=(ROOT/path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(), 'Seasonal manifest path invalid')
    source=json.loads(path.read_text())
    require(source.get('schemaVersion')==1 and source.get('status')=='CPU_GEOGRAPHY_REVIEWED_AWAITING_NATIVE',
            'Seasonal geography has not passed CPU review')
    require(source.get('orthoManifest')=={'path':ortho['manifestPath'],'sha256':ortho['manifestSha256']},
            'Seasonal source orthophoto differs')
    require(source.get('parameters')=={'strength':.88,'referenceLuminance':.18,'greenLinearRgb':[.065,.115,.030],
            'textureExponent':.82,'chromaResidual':.07,'maximumLinearReflectance':.32}, 'Unreviewed seasonal response')
    require(source.get('sourceObservationUnchanged') is True, 'Seasonal source observation claim changed')
    inputs={str(path):sha(path),**source['inputFiles']}
    review=source['visualReview'];shader=source['shader']
    for spec in (review,shader):inputs[spec['path']]=spec['sha256']
    layers=source['layers'];original={v['id']:v for v in ortho['layers']}
    require(len(layers)==2 and {v['id'] for v in layers}==set(original), 'Seasonal atlas set differs')
    for layer in layers:
        original_layer=original[layer['id']]
        require(layer['width']==layer['height']==4096 and layer['sRGB'] is False and layer['addressMode']=='clamp'
                and layer['samplerMipPolicy']=='explicit-level-zero-for-geographic-containment', 'Seasonal mask interpretation differs')
        require(layer['worldCmToUvRows']==original_layer['worldCmToUvRows']
                and layer['sourceRgbaSha256']==original_layer['rgbaSha256'], 'Seasonal map geography/source differs')
        inputs[layer['maskPath']]=layer['maskSha256']
    for filename,expected in inputs.items():
        p=Path(filename).resolve()
        require(p.is_relative_to(ROOT) and p.is_file() and sha(p)==expected, 'Seasonal input drift: '+filename)
    require(json.loads(Path(review['path']).read_text())['status']=='CPU_GEOGRAPHY_CANDIDATE_PASS_AWAITING_NATIVE',
            'Seasonal visual candidate rejected')
    require(Path(shader['path']).read_text().strip()==SEASONAL_FIELD_COLOR, 'Unreviewed seasonal shader')
    for layer in layers:
        with Path(layer['maskPath']).open('rb') as stream:header=stream.read(29)
        require(header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>IIBB',header[16:26])==(4096,4096,8,0),
                'Seasonal mask must be 4096 linear R8 PNG')
    return {'manifestPath':str(path),'manifestSha256':sha(path),'layers':copy.deepcopy(layers),
            'parameters':source['parameters'],'inputFiles':inputs,'visualReview':copy.deepcopy(review),
            'attribution':source['attribution'],'claim':source['claim'],
            'samplerPolicy':'Uncompressed G8, no mipmaps, resident; explicit mip0 shader sample and Clamp preserve the inward field mask.'}


def prepare_field_macro(path):
    """Bounded image-derived luminance only, on four owned context field keys."""
    path=(ROOT/path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(), 'Field macro manifest path invalid')
    source=json.loads(path.read_text())
    require(source.get('schemaVersion')==1 and source.get('kind')=='field-macro-scalar'
            and source.get('status')=='FROZEN_FOR_NATIVE_QA_NOT_ACCEPTED'
            and source.get('selectedCandidate')=='moderate' and source.get('factorRange')==[.75,1.10], 'Unreviewed field macro candidate')
    require(set(source['allowedMaterialKeys'])==FIELD_MACRO_KEYS and len(source['allowedMaterialKeys'])==4, 'Field macro material scope differs')
    expected_rows=[[1/56000,0,.5],[0,-1/56000,.5]]
    require(source['worldBoundsCm']==[-28000.,-28000.,28000.,28000.] and source['worldCmToUvRows']==expected_rows
            and source['fieldRadiusCm']==25500 and source['radialFadeCm']==[21000,25500], 'Field macro affine/radial frame differs')
    sampling=source['sampling'];policy=source['nativeTexturePolicy'];texture=source['texture'];license_info=source['license']
    require(sampling['containmentMip']==0 and sampling['rawUvValidityRequired'] is True
            and sampling['hardContainmentThreshold']==.99 and sampling['addressMode']=='clamp'
            and policy=={'compression':'TC_VectorDisplacementmap','samplerType':'LinearColor','sRGB':False,
                         'neverStream':True,'containmentSamplerMip':0,'automaticViewMipBias':False,'factorSamplerMip':'automatic'},
            'Field macro sampling policy differs')
    require(texture['width']==texture['height']==1024 and texture['sRGB'] is False
            and texture['pixelFormat']=='RGBA8' and texture['addressMode']=='clamp', 'Field macro texture interpretation differs')
    require(source['sourceCurrencyYear']==2024 and license_info['spdx']=='CC-BY-4.0'
            and license_info['attribution']=='ČÚZK, 2024', 'Field macro attribution missing')
    require(source['statistics']['neutralOutsideExact'] is True and source['summary']['protectedIntersections']==0
            and source['summary']['unsupportedPixels']==0, 'Field macro containment evidence failed')
    inputs={str(path):sha(path),**source['inputFiles']}
    for spec in (texture,source['review']['cpuPreview'],source['summary']['domainTextureLabels']):inputs[spec['path']]=spec['sha256']
    for filename,expected in inputs.items():
        p=Path(filename).resolve()
        require(p.is_relative_to(ROOT) and p.is_file() and sha(p)==expected, 'Field macro input drift: '+filename)
    with Path(texture['path']).open('rb') as stream:header=stream.read(29)
    require(header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>IIBB',header[16:26])==(1024,1024,8,6), 'Field macro must be1024 RGBA8 PNG')
    return {'manifestPath':str(path),'manifestSha256':sha(path),'inputFiles':inputs,
            'texture':copy.deepcopy(texture),'worldCmToUvRows':copy.deepcopy(expected_rows),'factorRange':[.75,1.10],
            'allowedMaterialKeys':sorted(FIELD_MACRO_KEYS),'license':copy.deepcopy(license_info),
            'sourceSceneSha256':source['sourceSceneSha256'],'sourceObjSha256':source['sourceObjSha256'],
            'sampling':copy.deepcopy(sampling),'nativeTexturePolicy':copy.deepcopy(policy),
            'limitations':copy.deepcopy(source['limitations'])}


def field_macro_multiplier(factor_channel, containment_rgba, uv):
    """Scalar witness: neutral outside validity, bounded within reviewed fields."""
    valid=all(0<=v<=1 for v in uv) and containment_rgba[1]>=.99 and containment_rgba[2]>=.99
    if not valid:return 1.
    factor=min(1.10,max(.75,1+(factor_channel-128/255)*.70))
    return 1+(factor-1)*min(1.,max(0.,containment_rgba[3]))


def prepare_projection(path, ortho):
    """Validate a continuous geometry-only RGB permission mask before writes."""
    require(ortho is not None, 'RGB projection requires licensed orthophoto')
    path=(ROOT/path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(), 'RGB projection manifest path invalid')
    source=json.loads(path.read_text());owner='scripts/unreal/exterior-ortho-projection-mask.py'
    require(source.get('schemaVersion')==1 and source.get('kind')=='ortho-projection-protection'
            and source.get('owner')==owner, 'Unreviewed RGB projection mask')
    require(source.get('orthoManifest')=={'path':ortho['manifestPath'],'sha256':ortho['manifestSha256']},
            'RGB projection active orthophoto differs')
    require(set(source['allowedMaterialKeys'])==PROJECTION_KEYS and len(source['allowedMaterialKeys'])==5,
            'RGB projection material scope differs')
    require(source['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}
            and source['housePlacement']['streetSetbackMm']==source['housePlacement']['eastSetbackMm']==3000,
            'RGB projection design/setbacks differ')
    require([h for p,h in ortho['inputFiles'].items() if p.endswith('/geometry/scene.json')]==[source['sourceSceneSha256']],
            'RGB projection architectural frame differs')
    texture=source['texture'];bounds=source['worldBoundsCm'];rows=source['worldCmToUvRows']
    require(len(bounds)==4 and all(isinstance(v,(int,float)) and math.isfinite(v) for v in bounds)
            and bounds[2]>bounds[0] and bounds[3]>bounds[1], 'RGB projection world bounds invalid')
    expected=[[1/(bounds[2]-bounds[0]),0.,-bounds[0]/(bounds[2]-bounds[0])],
              [0.,-1/(bounds[3]-bounds[1]),bounds[3]/(bounds[3]-bounds[1])]]
    require(len(rows)==2 and all(len(row)==3 and all(math.isfinite(v) and abs(v-expected[i][j])<1e-12
            for j,v in enumerate(row)) for i,row in enumerate(rows))
            and texture['worldCmToUvRows']==rows and texture['worldBoundsCm']==bounds,
            'RGB projection affine frame differs')
    require(texture['width']==texture['height']==1024 and texture['pixelFormat']=='RGBA8'
            and texture['sRGB'] is False and texture['lossless'] is True, 'RGB projection texture interpretation differs')
    require(texture['channels']=={'R':'Smooth RGB projection permission;0=protected;1=ordinary context',
            'G':'Mask geographic extent coverage1; explicit UV-bounds guard required','B':'Unused0',
            'A':'Opaque255; original ortho provider alpha sampled separately'}
            and texture['permissionMipPolicy']=='Ordinary resident mips; geometric smoothing'
            and texture['coverageMipPolicy']=='Original provider ortho alpha and mask extent sampled/gated at mip0',
            'RGB projection channel/sampling policy differs')
    policy=source['policy']
    require(all(policy.get(key) is True for key in ('protectionOnly','noDarkPixelExclusion','noFieldBoundaryExclusion',
            'noCanopyExclusion','noRoadExclusion','providerCoverageSeparate','subjectSiteProtected'))
            and policy['sourceGroundOrGeometryChanged'] is False and policy['officialBuildingBufferCm']==150.
            and policy['geometricFeatherCm']==300.
            and abs(policy['rasterBilinearGuardCm']-math.hypot((bounds[2]-bounds[0])/1024,(bounds[3]-bounds[1])/1024))<1e-6,
            'RGB projection protection-only policy differs')
    summary=source['summary']
    require(summary['status']=='PASS' and summary['textureCount']==1 and set(summary['groundMaterialKeys'])==PROJECTION_KEYS
            and summary['ordinaryGroundCentroidsTested']>0 and summary['ordinaryGroundCentroidMinimumPermission']>=1-1e-12
            and summary['primarySiteMaximumPermission']==0 and summary['darkOrdinaryContextPixelsPermitted']>0
            and summary['darkOrdinaryMinimumPermission']==1 and summary['greenChannelMinimum']==summary['greenChannelMaximum']==255
            and summary['blueChannelMaximum']==0 and summary['alphaChannelMinimum']==255
            and source['subjectSiteAudit']['allPrivateGeometryXYProtected'] is True,
            'RGB projection continuity/protection evidence failed')
    inputs={str(path):sha(path),**source['inputFiles'],texture['path']:texture['sha256']}
    require(inputs.get(str(ROOT/owner))==source['generatorSha256']==sha(ROOT/owner), 'RGB projection generator drift')
    require([h for p,h in inputs.items() if p.endswith('/geometry/scene.json')]==[source['sourceSceneSha256']]
            and [h for p,h in inputs.items() if p.endswith('/geometry/dom-mm.obj')]==[source['sourceObjSha256']],
            'RGB projection source geometry pins differ')
    for filename,expected_sha in inputs.items():
        resolved=Path(filename).resolve()
        require(resolved.is_relative_to(ROOT) and resolved.is_file() and sha(resolved)==expected_sha,
                'RGB projection input drift: '+filename)
    with Path(texture['path']).open('rb') as stream:header=stream.read(29)
    require(header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>IIBB',header[16:26])==(1024,1024,8,6),
            'RGB projection must be1024 RGBA8 PNG')
    actual=_projection_channels(texture['path'])
    require(all(actual[key]==summary[key] for key in actual),
            'RGB projection actual protection pixel counts differ from manifest')
    return {'manifestPath':str(path),'manifestSha256':sha(path),'owner':owner,'inputFiles':inputs,
            'texture':copy.deepcopy(texture),'worldCmToUvRows':copy.deepcopy(rows),'worldBoundsCm':copy.deepcopy(bounds),
            'allowedMaterialKeys':sorted(PROJECTION_KEYS),'policy':copy.deepcopy(policy),'summary':copy.deepcopy(summary),
            'orthoManifest':copy.deepcopy(source['orthoManifest']),'limitations':copy.deepcopy(source['limits'])}


def _projection_channels(path):
    """Check actual RGBA bytes with stdlib, available in embedded UE Python."""
    data=Path(path).read_bytes()
    require(data[28]==0, 'RGB projection PNG must be non-interlaced')
    compressed=bytearray();offset=8
    while offset+12<=len(data):
        length=struct.unpack('>I',data[offset:offset+4])[0];kind=data[offset+4:offset+8]
        require(offset+12+length<=len(data), 'RGB projection PNG chunk truncated')
        if kind==b'IDAT':compressed.extend(data[offset+8:offset+8+length])
        offset+=12+length
        if kind==b'IEND':break
    try:raw=zlib.decompress(compressed)
    except zlib.error as exc:raise RuntimeError('RGB projection PNG channel decode failed') from exc
    stride=1024*4
    require(len(raw)==1024*(stride+1), 'RGB projection PNG channel payload differs')
    previous=bytearray(stride);red_min,red_max=255,0
    counts={'protectedPixels':0,'featherPixels':0,'ordinaryPixels':0}
    for y in range(1024):
        start=y*(stride+1);kind=raw[start];row=bytearray(raw[start+1:start+1+stride])
        require(kind<=4, 'RGB projection PNG filter unsupported')
        for i in range(stride) if kind else ():
            left=row[i-4] if i>=4 else 0;up=previous[i];diagonal=previous[i-4] if i>=4 else 0
            if kind==1:predictor=left
            elif kind==2:predictor=up
            elif kind==3:predictor=(left+up)//2
            else:
                estimate=left+up-diagonal;distances=(abs(estimate-left),abs(estimate-up),abs(estimate-diagonal))
                predictor=(left,up,diagonal)[distances.index(min(distances))]
            row[i]=(row[i]+predictor)&255
        require(row[1::4]==b'\xff'*1024 and row[2::4]==b'\x00'*1024 and row[3::4]==b'\xff'*1024,
                'RGB projection actual G/B/A channels differ from extent/unused/opaque contract')
        red=row[0::4];zeros=red.count(0);ones=red.count(255)
        counts['protectedPixels']+=zeros;counts['ordinaryPixels']+=ones
        counts['featherPixels']+=1024-zeros-ones
        red_min=min(red_min,min(red));red_max=max(red_max,max(red));previous=row
    require(red_min==0 and red_max==255, 'RGB projection actual protection channel has no protected/ordinary range')
    return counts


def texture_compression(u,role):
    if role in ('field_macro','ortho_projection','ground_condition'):return native_enum(u.TextureCompressionSettings,'TCVECTORDISPLACEMENTMAP')
    if role=='season_mask':return native_enum(u.TextureCompressionSettings,'TCGRAYSCALE')
    return u.TextureCompressionSettings.TC_NORMALMAP if role=='normal' else u.TextureCompressionSettings.TC_DEFAULT if role=='albedo' else u.TextureCompressionSettings.TC_MASKS


def orthophoto_uv(position_cm, layer):
    return tuple(row[0]*position_cm[0]+row[1]*position_cm[1]+row[2] for row in layer['worldCmToUvRows'])


def _orthophoto_layer_weights(position_cm, layers, coverage):
    weights = {}
    for layer in layers:
        uv = orthophoto_uv(position_cm, layer)
        valid = float(all(0 <= v <= 1 for v in uv) and coverage[layer['id']] >= .99)
        if layer['id'] == 'detail2km':
            box = layer['bboxMetres']
            edge = min(min(uv[i],1-uv[i])*(box[i+2]-box[i])*100 for i in range(2))
            valid *= _smoothstep(0,10000,edge)
        weights[layer['id']] = valid
    return weights


def _orthophoto_mix(weights, amount):
    detail = weights['detail2km']*amount
    far = weights['far16km']*(1-weights['detail2km'])*amount
    return {'detail': detail, 'far': far, 'fallback': 1-detail-far}


def orthophoto_weights(position_cm, layers, coverage, distance_blend_cm=(30000, 90000)):
    """CPU coverage/edge witness; zero-alpha and out-of-extent remain fallback."""
    weights = _orthophoto_layer_weights(position_cm, layers, coverage)
    require(tuple(distance_blend_cm) in ((30000,90000),(18000,36000)), 'Unreviewed orthophoto distance blend')
    radial = _smoothstep(*distance_blend_cm,math.hypot(*position_cm[:2]))
    return _orthophoto_mix(weights, radial)


def ground_orthophoto_weights(position_cm, camera_cm, layers, coverage, projection_uv, permission_rgba):
    """Camera-distance witness with continuous protection-only permission."""
    require(len(position_cm) == len(camera_cm) == 3, 'Camera ground blend needs world XYZ')
    valid = float(all(0 <= v <= 1 for v in projection_uv) and permission_rgba[1] >= .99)
    amount = _smoothstep(*GROUND_ORTHO_BLEND_CM, math.dist(position_cm, camera_cm))*valid*min(1.,max(0.,permission_rgba[0]))
    return _orthophoto_mix(_orthophoto_layer_weights(position_cm, layers, coverage), amount)


def soil_exposure_coverage(position_cm, camera_cm, edge_coverage):
    """Bounded spatial coverage; native DitherTemporalAA provides dithering."""
    def noise(x, y):
        def hashed(a, b):
            value = math.sin(a*127.1+b*311.7)*43758.5453
            return value-math.floor(value)
        ix, iy = math.floor(x), math.floor(y)
        fx, fy = _smoothstep(0,1,x-ix), _smoothstep(0,1,y-iy)
        lo = hashed(ix,iy)*(1-fx)+hashed(ix+1,iy)*fx
        hi = hashed(ix,iy+1)*(1-fx)+hashed(ix+1,iy+1)*fx
        return lo*(1-fy)+hi*fy
    density = sum(noise(position_cm[0]/scale+offset, position_cm[1]/scale+offset)*weight
                  for scale,offset,weight in ((240.,19.,.55),(75.,73.,.30),(18.,117.,.15)))
    broken = .06+.88*_smoothstep(.24,.76,density)
    near = 1-_smoothstep(*SOIL_EXPOSURE_FADE_CM, math.dist(position_cm,camera_cm))
    return _smoothstep(0,1,edge_coverage)*broken*near


def ground_uv(position, tile_cm, yaw_degrees):
    """CPU mapping witness for axis/orientation and scale regression tests."""
    a = math.radians(yaw_degrees)
    return ((math.cos(a)*position[0]+math.sin(a)*position[1])/tile_cm,
            (-math.sin(a)*position[0]+math.cos(a)*position[1])/tile_cm)


def ground_normal(normal, strength, yaw_degrees, vertex_normal=(0., 0., 1.)):
    def unit(v):
        length = math.sqrt(sum(x*x for x in v))
        return tuple(x/length for x in v)
    a = math.radians(yaw_degrees)
    x, y, z = unit((normal[0]*strength, normal[1]*strength, max(normal[2], .1)))
    n = unit(vertex_normal)
    t = unit((math.cos(a), math.sin(a), -(n[0]*math.cos(a)+n[1]*math.sin(a))/max(n[2], .05)))
    b = unit((n[1]*t[2]-n[2]*t[1], n[2]*t[0]-n[0]*t[2], n[0]*t[1]-n[1]*t[0]))
    return unit(tuple(t[i]*x+b[i]*y+n[i]*z for i in range(3)))


def ground_triangle(uv):
    q = ((uv[0]-uv[1]*.577350269)/1.7, uv[1]*1.154700538/1.7)
    cell = tuple(math.floor(x) for x in q); f = tuple(q[i]-cell[i] for i in range(2))
    upper = sum(f) > 1.
    w = (1-f[1], 1-f[0], sum(f)-1) if upper else (1-sum(f), f[0], f[1])
    offsets = ((1, 0), (0, 1), (1, 1)) if upper else ((0, 0), (1, 0), (0, 1))
    total = sum(x**3 for x in w)
    return {tuple(cell[i]+offset[i] for i in range(2)): weight**3/total for offset, weight in zip(offsets, w)}


def prepare_dither_function(u):
    """Load the installed engine function directly; never author a substitute."""
    engine = Path(os.environ.get('UNREAL_ENGINE_ROOT', '/Users/Shared/Epic Games/UE_5.8')).resolve()
    source = engine/'Engine/Content/Functions/Engine_MaterialFunctions02/Utility/DitherTemporalAA.uasset'
    require(source.is_file(), 'Missing installed temporal soil feather function package')
    function = u.load_object(None, DITHER_FUNCTION)
    require(function is not None and function.get_path_name() == DITHER_FUNCTION
            and function.get_class().get_name() == 'MaterialFunction', 'Missing/foreign native temporal soil feather function')
    return function, {'asset': DITHER_FUNCTION, 'class': 'MaterialFunction', 'source': str(source),
                      'sourceSha256': sha(source), 'coverage': 'Authored mesh UV0.x times bounded multiscale world coverage and 40-100m camera fade; native DitherTemporalAA Alpha Threshold input'}


def graph_snapshot(u, material):
    lib = u.MaterialEditingLibrary
    def value(v):
        if isinstance(v, (str, bool, int)): return v
        # Affine UV coefficients are about 1e-7. Decimal-place rounding would
        # hide metres of mapping drift; pin the full stored native float.
        if isinstance(v, float): return v
        if hasattr(v, 'r'): return [float(getattr(v, k)) for k in ('r', 'g', 'b', 'a')]
        if hasattr(v, 'get_path_name'): return v.get_path_name()
        return str(v)
    fields = {'MaterialExpressionConstant': ['r'], 'MaterialExpressionConstant3Vector': ['constant'],
              'MaterialExpressionCustom': ['code', 'output_type'],
              'MaterialExpressionTextureSample': ['texture', 'sampler_type', 'mip_value_mode', 'automatic_view_mip_bias'],
              'MaterialExpressionTextureCoordinate': ['coordinate_index', 'u_tiling', 'v_tiling'],
              'MaterialExpressionComponentMask': ['r', 'g', 'b', 'a'],
              'MaterialExpressionMaterialFunctionCall': ['material_function']}
    nodes = []
    for node in lib.get_material_expressions(material):
        pins = list(lib.get_material_expression_input_names(node))
        inputs = list(lib.get_inputs_for_material_expression(material, node))
        nodes.append({'role': str(node.get_editor_property('desc')), 'class': node.get_class().get_name(),
                      'values': {k: value(node.get_editor_property(k)) for k in fields.get(node.get_class().get_name(), [])},
                      'inputs': [[str(pin), str(other.get_editor_property('desc')) if other else None,
                                  str(lib.get_input_node_output_name_for_material_expression(node, other)) if other else None]
                                 for pin, other in zip(pins, inputs)]})
    roots = {}
    for key in ROOTS:
        prop = getattr(u.MaterialProperty, 'MP_' + key)
        node = lib.get_material_property_input_node(material, prop)
        roots[key] = [str(node.get_editor_property('desc')), str(lib.get_material_property_input_node_output_name(material, prop))] if node else None
    return {'nodes': sorted(nodes, key=lambda row: row['role']), 'roots': roots,
            'flags': {k: value(material.get_editor_property(k)) for k in
                      ('blend_mode', 'shading_model', 'two_sided', 'tangent_space_normal', 'opacity_mask_clip_value', 'use_material_attributes')}}


class Writer:
    def __init__(self, u, prefix, dither_function=None):
        require(prefix == PREFIX or prefix.startswith(PREFIX + '/'), 'Exterior namespace escaped')
        self.u, self.prefix = u, prefix
        self.assets, self.lib = u.EditorAssetLibrary, u.MaterialEditingLibrary
        self.textures, self.texture_report = {}, {}
        self.dither_function = dither_function

    def node(self, material, role, cls, **props):
        node = self.lib.create_material_expression(material, cls, -600, 0)
        require(node is not None, 'Cannot create exterior expression ' + role)
        node.set_editor_property('desc', TAG + role)
        for k, v in props.items(): node.set_editor_property(k, v)
        return node

    def scalar(self, m, role, value):
        return self.node(m, role, self.u.MaterialExpressionConstant, r=float(value))

    def vector(self, m, role, value):
        return self.node(m, role, self.u.MaterialExpressionConstant3Vector, constant=self.u.LinearColor(*value, 1))

    def connect(self, source, channel, target, pin):
        require(self.lib.connect_material_expressions(source, channel, target, pin), 'Exterior connection failed: ' + pin)

    def out(self, node, prop, channel=''):
        require(self.lib.connect_material_property(node, channel, getattr(self.u.MaterialProperty, 'MP_' + prop)), 'Exterior output failed: ' + prop)

    def custom(self, m, role, code, inputs, width=3):
        pins = []
        for name in inputs:
            pin = self.u.CustomInput(); pin.set_editor_property('input_name', name); pins.append(pin)
        node = self.node(m, role, self.u.MaterialExpressionCustom, code=code, description=TAG+role, inputs=pins,
                         output_type=getattr(self.u.CustomMaterialOutputType, 'CMOT_FLOAT'+str(width)))
        for name, entry in inputs.items(): self.connect(entry[0], entry[1], node, name)
        return node

    def texture(self, role, recipe):
        u = self.u; spec = recipe['maps'][role]
        flip = role == 'normal' and recipe['normalConvention'] == 'OpenGL'
        coverage = float(recipe['opacityMaskClipValue']) if role == 'alpha' else 0.
        address = recipe.get('addressMode', 'wrap')
        resize = recipe.get('powerOfTwoMode')
        encoding=texture_source_encoding(role,recipe)
        require(address in ('wrap','clamp'), 'Unknown exterior texture address mode')
        key = role + '_' + spec['sha256'][:16] + ('_flip' if flip else '') + (('_c'+str(round(coverage*1000))) if coverage else '') + ('_clamp' if address == 'clamp' else '') + ('_pot' if resize else '') + ('_srcsrgb' if encoding=='sRGB' else '')
        if key in self.textures: return self.textures[key]
        name = 'T_Exterior_' + key; path = self.prefix + '/Textures/' + name
        require(not self.assets.does_asset_exist(path), 'Use new output for exterior textures: ' + path)
        task = u.AssetImportTask()
        for k, v in {'filename': spec['path'], 'destination_path': self.prefix+'/Textures', 'destination_name': name,
                     'automated': True, 'replace_existing': False, 'save': False}.items(): task.set_editor_property(k, v)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
        tex = self.assets.load_asset(path); require(isinstance(tex, u.Texture2D), 'Exterior texture import failed: '+path)
        compression = texture_compression(u,role)
        texture_address = u.TextureAddress.TA_CLAMP if address == 'clamp' else u.TextureAddress.TA_WRAP
        settings = {'srgb': role == 'albedo', 'flip_green_channel': flip, 'compression_settings': compression,
                    'address_x': texture_address, 'address_y': texture_address,
                    'lod_bias': 0, 'max_texture_size': 0, 'virtual_texture_streaming': False,
                    'mip_gen_settings': u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP,
                    'power_of_two_mode': u.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO if resize == 'stretch' else u.TexturePowerOfTwoSetting.NONE,
                    'do_scale_mips_for_alpha_coverage': role == 'alpha',
                    'alpha_coverage_thresholds': u.Vector4(coverage, 0., 0., 0.)}
        if role=='season_mask':
            settings.update(mip_gen_settings=native_enum(u.TextureMipGenSettings,'TMGSNOMIPMAPS'),never_stream=True)
        if role in ('field_macro','ortho_projection','ground_condition'):settings['never_stream']=True
        for k, v in settings.items(): tex.set_editor_property(k, v)
        if encoding=='sRGB' or role=='ground_condition':
            color=tex.get_editor_property('source_color_settings')
            color.set_editor_property('encoding_override',native_enum(u.TextureSourceEncoding,'TSESRGB' if encoding=='sRGB' else 'TSENONE'))
            tex.set_editor_property('source_color_settings',color)
        for k, v in {'BreziGeneratedBy': OWNER, 'source_sha256': spec['sha256'], 'BreziSourceLicense': recipe['license'],
                     'BreziSourcePage': recipe.get('sourceUrl', recipe.get('page')),
                     'BreziSourceEncodingOverride':encoding}.items(): self.assets.set_metadata_tag(tex, k, v)
        if role=='ground_condition':self.assets.set_metadata_tag(tex,'BreziAuthoredTechnicalRole','ground_condition')
        require(self.assets.save_loaded_asset(tex, only_if_is_dirty=False), 'Cannot save exterior texture')
        source_encoding=tex.get_editor_property('source_color_settings').get_editor_property('encoding_override')
        require(source_encoding==native_enum(u.TextureSourceEncoding,'TSESRGB' if encoding=='sRGB' else 'TSENONE'),
                'Exterior source encoding readback differs')
        self.textures[key] = tex
        self.texture_report[key] = {'asset': tex.get_path_name(), 'role': role, 'sourceSha256': spec['sha256'],
                                    'sourcePath': spec['path'], 'normalConvention': recipe['normalConvention'],
                                    'sourceLicense': recipe['license'], 'sourcePage': recipe.get('sourceUrl', recipe.get('page')),
                                    'sourceEncodingOverride':encoding,
                                    'sourceEncodingReadback':'TSE_S_RGB' if encoding=='sRGB' else 'TSE_NONE',
                                    'addressMode': address,
                                    'powerOfTwoMode': resize,
                                    'alphaCoverageThresholds': [coverage, 0., 0., 0.],
                                    'width': int(tex.blueprint_get_size_x()), 'height': int(tex.blueprint_get_size_y())}
        require(0 < self.texture_report[key]['width'] <= 8192 and 0 < self.texture_report[key]['height'] <= 8192, 'Exterior texture dimensions outside budget')
        if 'expectedDimensions' in recipe:
            require([self.texture_report[key][k] for k in ('width','height')] == recipe['expectedDimensions'], 'Orthophoto native dimensions differ')
        return tex

    def sample(self, m, role, recipe, uv, phase='', derivatives=None):
        sampler = native_enum(self.u.MaterialSamplerType,'SAMPLERTYPELINEARCOLOR') if role in ('field_macro','ortho_projection','ground_condition') else native_enum(self.u.MaterialSamplerType,'SAMPLERTYPELINEARGRAYSCALE') if role=='season_mask' else self.u.MaterialSamplerType.SAMPLERTYPE_COLOR if role == 'albedo' else self.u.MaterialSamplerType.SAMPLERTYPE_NORMAL if role == 'normal' else self.u.MaterialSamplerType.SAMPLERTYPE_MASKS
        node = self.node(m, role+phase, self.u.MaterialExpressionTextureSample, texture=self.texture(role, recipe), sampler_type=sampler)
        self.connect(uv, '', node, 'UVs')
        if role=='ground_condition':node.set_editor_property('automatic_view_mip_bias',False)
        if derivatives:
            node.set_editor_property('mip_value_mode', self.u.TextureMipValueMode.TMVM_DERIVATIVE)
            for derivative, pin in zip(derivatives, ('DDX(UVs)', 'DDY(UVs)')):
                self.connect(derivative, '', node, pin)
        return node

    def ground_layer(self, m, recipe, uv, label):
        derivatives = [self.custom(m, label+'-gradient-'+axis, 'return '+axis+'(UV);', {'UV': (uv, '')}, 2)
                       for axis in ('ddx', 'ddy')]
        if recipe.get('stochasticGround') is False:
            # The bounded grove overlay samples the unchanged photograph in
            # the same metric frame as its offline displacement geometry.
            return {role:self.sample(m,role,recipe,uv,'-'+label+'-registered',derivatives)
                    for role in recipe['maps']}
        weights = self.custom(m, label+'-weights', GROUND_WEIGHTS, {'UV': (uv, '')})
        phases = [self.custom(m, label+'-phase-'+str(i), GROUND_PHASE,
                             {'UV': (uv, ''), 'Phase': (self.scalar(m, label+'-index-'+str(i), i), '')}, 2) for i in range(3)]
        result = {}
        for role in recipe['maps']:
            nodes = [self.sample(m, role, recipe, phase, '-'+label+'-'+str(i), derivatives) for i, phase in enumerate(phases)]
            result[role] = self.custom(m, label+'-'+role+'-blend', 'return A*W.x+B*W.y+C*W.z;',
                                      {**{name: (node, 'RGB') for name, node in zip(('A', 'B', 'C'), nodes)}, 'W': (weights, '')})
        return result

    def ortho_terrain(self, m, recipe, pos, vertex, fallback):
        ortho = recipe['orthophoto']
        blend_range = self.vector(m, 'ortho-distance-blend-cm', [*ortho['distanceBlendCm'], 0])
        distance = self.custom(m, 'ortho-radial-distance', ORTHO_RADIAL,
                               {'Position': (pos,''), 'BlendRange': (blend_range,'')}, 1)
        near = self.custom(m, 'near-terrain-pbr-weight', 'return 1.0-DistanceBlend;', {'DistanceBlend': (distance,'')}, 1)
        yaw = self.scalar(m, 'terrain-detail-yaw', recipe['yawDegrees'])
        uv = self.custom(m, 'terrain-detail-metric-uv', GROUND_UV,
                         {'Position': (pos,''), 'YawDegrees': (yaw,''), 'TileCm': (self.scalar(m,'terrain-detail-tile-cm',recipe['tileCm']),'')}, 2)
        scans = self.ground_layer(m, recipe, uv, 'terrain-detail')
        fallback = self.custom(m, 'near-terrain-pbr-color', 'return lerp(Terrain,Scan,.30*Near);',
                               {'Terrain': (fallback,''), 'Scan': (scans['albedo'],''), 'Near': (near,'')})
        strength = self.custom(m, 'near-terrain-normal-strength', 'return .30*Near;', {'Near': (near,'')}, 1)
        normal = self.custom(m, 'ortho-terrain-slope-normal', GROUND_NORMAL,
                             {'MapNormal': (scans['normal'],''), 'Strength': (strength,''), 'YawDegrees': (yaw,''), 'VertexNormal': (vertex,'')})
        rough = self.custom(m, 'ortho-terrain-roughness', 'return lerp(.93,clamp(Scan.r,.63,.98),Near);', {'Scan': (scans['roughness'],''), 'Near': (near,'')}, 1)
        # Preserve the radial PBR/normal/roughness response while RGB uses the
        # same camera distance as neighbouring context grounds and flat joins.
        camera = self.node(m, 'terrain-ortho-camera-position', self.u.MaterialExpressionCameraPositionWS)
        rgb_distance = self.custom(m, 'terrain-ortho-camera-distance', ORTHO_CAMERA,
                                   {'Position':(pos,''), 'Camera':(camera,''),
                                    'BlendRange':(self.vector(m,'terrain-ortho-camera-blend-cm',
                                        [*recipe['terrainOrthophotoCameraBlend']['cameraDistanceBlendCm'],0]),'')}, 1)
        return self.ortho_color(m, ortho, pos, fallback, rgb_distance, exact_coverage=True), normal, rough

    def ortho_color(self, m, ortho, pos, fallback, distance, exact_coverage=False):
        """Shared licensed affine/coverage gates, independent of blend distance."""
        samples, valid = {}, {}
        seasonal={v['id']:v for v in ortho.get('seasonalFields',{}).get('layers',[])}
        for layer in ortho['layers']:
            label = 'ortho-'+layer['id']
            mapping = self.custom(m, label+'-affine-uv', ORTHO_UV,
                                  {'Position': (pos,''), **{name: (self.vector(m,label+'-'+name,row),'') for name,row in zip(('RowU','RowV'),layer['worldCmToUvRows'])}}, 2)
            texture_recipe = {'maps': {'albedo': {'path': layer['rgbaPath'], 'sha256': layer['rgbaSha256']}},
                              'normalConvention': 'DirectX', 'license': ortho['license']['spdx'],
                              'sourceUrl': ortho['license']['datasetPolicy'], 'addressMode': 'clamp',
                              'expectedDimensions': [layer['width'],layer['height']]}
            sample = self.sample(m, 'albedo', texture_recipe, mapping, '-'+label)
            samples[layer['id']] = (sample,'RGB')
            coverage = sample
            if exact_coverage:
                sample.set_editor_property('automatic_view_mip_bias',False)
                coverage = self.sample(m, 'albedo', texture_recipe, mapping, '-'+label+'-coverage-mip0')
                coverage.set_editor_property('automatic_view_mip_bias',False)
                coverage.set_editor_property('mip_value_mode',native_enum(self.u.TextureMipValueMode,'TMVMMIPLEVEL'))
                self.connect(self.scalar(m,label+'-coverage-mip-zero',0.),'',coverage,'Level')
            if layer['id'] in seasonal:
                mask_spec=seasonal[layer['id']]
                mask_recipe={'maps':{'season_mask':{'path':mask_spec['maskPath'],'sha256':mask_spec['maskSha256']}},
                             'normalConvention':'DirectX','license':ortho['license']['spdx'],
                             'sourceUrl':ortho['license']['datasetPolicy'],'addressMode':'clamp','expectedDimensions':[4096,4096]}
                mask=self.sample(m,'season_mask',mask_recipe,mapping,'-'+label)
                mask.set_editor_property('mip_value_mode',native_enum(self.u.TextureMipValueMode,'TMVMMIPLEVEL'))
                mask.set_editor_property('automatic_view_mip_bias',False)
                # MaterialEditingLibrary resolves the graph's shortened pin name
                # (UE 5.8 MaterialGraphNode.cpp: MipLevel -> Level).
                self.connect(self.scalar(m,label+'-mask-mip-zero',0.),'',mask,'Level')
                color=self.custom(m,label+'-seasonal-field-color',SEASONAL_FIELD_COLOR,{'Source':(sample,'RGB'),'Mask':(mask,'R')})
                samples[layer['id']]=(color,'')
            valid[layer['id']] = self.custom(m, label+'-coverage-and-extent', ORTHO_VALID,
                                             {'UV': (mapping,''), 'Coverage': (coverage,'A')}, 1)
            if layer['id'] == 'detail2km':
                box = layer['bboxMetres']; extent = [(box[2]-box[0])*100,(box[3]-box[1])*100,0]
                valid[layer['id']] = self.custom(m, label+'-edge-feather-100m', ORTHO_DETAIL_WEIGHT,
                                                 {'UV': (mapping,''), 'Valid': (valid[layer['id']],''), 'ExtentCm': (self.vector(m,label+'-extent-cm',extent),'')}, 1)
        color = self.custom(m, 'licensed-ortho-basecolor', ORTHO_COLOR,
                            {'Fallback': (fallback,''), 'Far': samples['far16km'], 'FarValid': (valid['far16km'],''),
                             'Detail': samples['detail2km'], 'DetailWeight': (valid['detail2km'],''), 'DistanceBlend': (distance,'')})
        return color

    def ortho_ground(self, m, recipe, pos, fallback):
        ortho = recipe['groundOrthophoto']
        projection = recipe['projectionMask'];texture = projection['texture']
        mapping = self.custom(m, 'ground-ortho-projection-world-uv', ORTHO_UV,
                              {'Position':(pos,''), **{name:(self.vector(m,'ground-projection-'+name,row),'')
                               for name,row in zip(('RowU','RowV'),projection['worldCmToUvRows'])}}, 2)
        texture_recipe = {'maps':{'ortho_projection':{'path':texture['path'],'sha256':texture['sha256']}},
                          'normalConvention':'DirectX','license':ortho['license']['spdx'],'sourceUrl':ortho['license']['datasetPolicy'],
                          'addressMode':'clamp','expectedDimensions':[texture['width'],texture['height']]}
        permission = self.sample(m,'ortho_projection',texture_recipe,mapping,'-permission')
        coverage = self.sample(m,'ortho_projection',texture_recipe,mapping,'-coverage-mip0')
        for sample in (permission,coverage):sample.set_editor_property('automatic_view_mip_bias',False)
        coverage.set_editor_property('mip_value_mode',native_enum(self.u.TextureMipValueMode,'TMVMMIPLEVEL'))
        self.connect(self.scalar(m,'ground-projection-coverage-mip-zero',0.),'',coverage,'Level')
        camera = self.node(m, 'ground-ortho-camera-position', self.u.MaterialExpressionCameraPositionWS)
        distance = self.custom(m, 'ground-ortho-camera-distance', ORTHO_CAMERA,
                               {'Position': (pos,''), 'Camera': (camera,''),
                                'BlendRange': (self.vector(m,'ground-ortho-distance-blend-cm',[*GROUND_ORTHO_BLEND_CM,0]),'')}, 1)
        clipped = self.custom(m, 'ground-ortho-protected-field-weight', GROUND_ORTHO_WEIGHT,
                              {'DistanceBlend': (distance,''), 'ProjectionUV': (mapping,''),
                               'Permission': (permission,'R'), 'Coverage': (coverage,'G')}, 1)
        return self.ortho_color(m, ortho, pos, fallback, clipped, exact_coverage=True)

    def field_macro(self,m,recipe,pos,color):
        macro=recipe['fieldMacro'];spec=macro['texture']
        uv=self.custom(m,'field-macro-world-uv',ORTHO_UV,
                       {'Position':(pos,''),**{name:(self.vector(m,'field-macro-'+name,row),'')
                        for name,row in zip(('RowU','RowV'),macro['worldCmToUvRows'])}},2)
        texture_recipe={'maps':{'field_macro':{'path':spec['path'],'sha256':spec['sha256']}},
                        'normalConvention':'DirectX','license':macro['license']['spdx'],
                        'sourceUrl':macro['license']['datasetPolicy'],'addressMode':'clamp','expectedDimensions':[1024,1024]}
        factor=self.sample(m,'field_macro',texture_recipe,uv,'-factor')
        containment=self.sample(m,'field_macro',texture_recipe,uv,'-containment')
        for sample in (factor,containment):sample.set_editor_property('automatic_view_mip_bias',False)
        containment.set_editor_property('mip_value_mode',native_enum(self.u.TextureMipValueMode,'TMVMMIPLEVEL'))
        self.connect(self.scalar(m,'field-macro-mip-zero',0.),'',containment,'Level')
        # Native readback resolves output by source node, not input pin. Separate
        # scalar nodes keep G/B/A independently sealed when used by one Custom.
        channels = {}
        for name, channel in [('Domain','G'), ('Coverage','B'), ('Weight','A')]:
            masked = self.node(m, 'field-macro-'+name.lower()+'-channel', self.u.MaterialExpressionComponentMask,
                               r=False, g=channel == 'G', b=channel == 'B', a=channel == 'A')
            self.connect(containment, 'RGBA', masked, '')
            channels[name] = masked
        color = self.custom(m,'field-macro-basecolor',FIELD_MACRO_COLOR,
                           {'Source':(color,''),'UV':(uv,''),'FactorChannel':(factor,'R'),
                            **{name:(node,'') for name,node in channels.items()},
                            'Range':(self.vector(m,'field-macro-factor-range',macro['factorRange']+[0.]),'')})
        return color, uv, channels

    def create(self, key, recipe):
        u = self.u; kind = recipe['kind']; atlas_foliage = kind == 'foliage'
        authored_foliage = kind == 'authored-foliage'; foliage = atlas_foliage or authored_foliage; ground = kind == 'ground'
        path = self.prefix + '/Materials/M_' + key
        require(not self.assets.does_asset_exist(path), 'Refusing to overwrite exterior material: ' + path)
        m = u.AssetToolsHelpers.get_asset_tools().create_asset('M_'+key, self.prefix+'/Materials', u.Material, u.MaterialFactoryNew())
        require(m is not None, 'Cannot create exterior material')
        flags = {'blend_mode': u.BlendMode.BLEND_MASKED if atlas_foliage or recipe.get('featherUV') else u.BlendMode.BLEND_OPAQUE,
                 'shading_model': native_enum(u.MaterialShadingModel, 'TWOSIDEDFOLIAGE') if foliage else u.MaterialShadingModel.MSM_DEFAULT_LIT,
                 'two_sided': foliage or (kind == 'bark' and recipe.get('twoSided', False)), 'tangent_space_normal': not ground,
                 'opacity_mask_clip_value': recipe.get('opacityMaskClipValue', .333), 'use_material_attributes': False}
        for k, v in flags.items(): m.set_editor_property(k, v)
        self.lib.set_base_material_usage(m, native_enum(u.MaterialUsage, 'INSTANCEDSTATICMESHES'), True)
        self.lib.set_base_material_usage(m, u.MaterialUsage.MATUSAGE_NANITE, True)
        if kind in ('foliage', 'bark'):
            uv = self.node(m, 'model-uv', u.MaterialExpressionTextureCoordinate, coordinate_index=0,
                           u_tiling=float(recipe['uvScale']), v_tiling=float(recipe['uvScale']))
            samples = {role: self.sample(m, role, recipe, uv) for role in recipe['maps']}
            random = self.node(m, 'instance-random', u.MaterialExpressionPerInstanceRandom)
            color = self.custom(m, 'scan-color', MODEL_COLOR, {'Scan': (samples['albedo'], 'RGB'),
                'Tint': (self.vector(m, 'linear-tint', recipe['tint']), ''), 'Random': (random, ''),
                'AlbedoScale': (self.scalar(m, 'provider-albedo-value', recipe['albedoScale']), '')})
            if 'leafCalibration' in recipe:
                calibration = recipe['leafCalibration']
                color = self.custom(m, 'artist-green-leaf-calibration', LEAF_CALIBRATION,
                                    {'Color': (color,''), 'Scan': (samples['albedo'],'RGB'),
                                     'Brightness': (self.scalar(m,'artist-leaf-brightness',calibration['brightness']),''),
                                     'Saturation': (self.scalar(m,'artist-leaf-saturation',calibration['saturation']),'')})
            normal = self.custom(m, 'provider-normal-strength', 'return normalize(float3(MapNormal.xy*Strength,max(MapNormal.z,.1)));',
                                 {'MapNormal': (samples['normal'], 'RGB'), 'Strength': (self.scalar(m, 'normal-strength', recipe['normalStrength']), '')})
            rough = self.custom(m, 'scan-roughness', 'return clamp(Scan.r,.38,.98);', {'Scan': (samples['roughness'], 'RGB')}, 1)
            if foliage:
                self.out(samples['alpha'], 'OPACITY_MASK', 'R')
                mask = samples.get('mask') or self.scalar(m, 'leaf-mask-fallback', 1.)
                self.out(self.custom(m, 'leaf-transmission', 'return Color*Strength*Mask;',
                                    {'Color': (color, ''), 'Strength': (self.scalar(m, 'leaf-transmission-scale', recipe['subsurfaceScale']), ''),
                                     'Mask': (mask, 'R' if 'mask' in samples else '')}), 'SUBSURFACE_COLOR')
                self.out(self.scalar(m, 'leaf-thickness', .65), 'OPACITY')
        elif authored_foliage:
            vertex = self.node(m, 'authored-plant-vertex-color', u.MaterialExpressionVertexColor)
            palette = self.vector(m, 'authored-plant-linear-color', recipe['linearColor'])
            color = self.node(m, 'authored-plant-color', u.MaterialExpressionMultiply)
            self.connect(vertex, '', color, 'A'); self.connect(palette, '', color, 'B')
            normal = self.vector(m, 'authored-plant-geometry-normal', [0., 0., 1.])
            rough = self.scalar(m, 'authored-plant-roughness', recipe['roughness'])
            transmission = self.node(m, 'authored-plant-transmission', u.MaterialExpressionMultiply)
            self.connect(color, '', transmission, 'A')
            self.connect(self.scalar(m, 'authored-plant-transmission-scale', recipe['subsurfaceScale']), '', transmission, 'B')
            self.out(transmission, 'SUBSURFACE_COLOR')
            self.out(self.scalar(m, 'authored-plant-thickness', .65), 'OPACITY')
        elif ground and recipe.get('terrain'):
            pos = self.node(m, 'world-position', u.MaterialExpressionWorldPosition)
            normal = self.node(m, 'surveyed-vertex-normal', u.MaterialExpressionVertexNormalWS)
            color = self.custom(m, 'distant-landcover-art-direction', TERRAIN_COLOR,
                                {'Position': (pos, ''), 'VertexNormal': (normal, '')})
            rough = self.scalar(m, 'terrain-roughness', .93)
            if 'orthophoto' in recipe:
                color, normal, rough = self.ortho_terrain(m,recipe,pos,normal,color)
        elif ground:
            pos = self.node(m, 'world-position', u.MaterialExpressionWorldPosition)
            vertex = self.node(m, 'surveyed-vertex-normal', u.MaterialExpressionVertexNormalWS)
            yaw = self.scalar(m, 'ground-yaw', recipe['yawDegrees'])
            uv = self.custom(m, 'metric-ground-uv', GROUND_UV, {'Position': (pos, ''), 'YawDegrees': (yaw, ''), 'TileCm': (self.scalar(m, 'tile-cm', recipe['tileCm']), '')}, 2)
            macro = self.custom(m, 'land-use-macro', MACRO, {'Position': (pos, '')})
            samples = self.ground_layer(m, recipe, uv, 'earth')
            if 'groundCover' in recipe:
                cover_recipe = recipe['groundCover']
                cover_uv = self.custom(m, 'cover-metric-uv', 'return UV*Scale;', {'UV': (uv, ''), 'Scale': (self.scalar(m, 'cover-relative-scale', recipe['tileCm']/cover_recipe['tileCm']), '')}, 2)
                cover = self.ground_layer(m, cover_recipe, cover_uv, 'cover')
                amount = self.custom(m, 'irregular-ground-cover', 'return lerp(Range.x,Range.y,smoothstep(.22,.78,Macro.x*.7+Macro.z*.3));',
                                     {'Macro': (macro, ''), 'Range': (self.vector(m, 'cover-range', recipe['coverRange']+[0.]), '')}, 1)
                for role in samples:
                    samples[role] = self.custom(m, 'groundcover-'+role, 'return lerp(Earth,Cover,Amount);',
                                                {'Earth': (samples[role], ''), 'Cover': (cover[role], ''), 'Amount': (amount, '')})
            rows = self.scalar(m, 'no-crop-rows', 1.)
            if recipe.get('cropRows'):
                rows = self.custom(m, 'subtle-crop-rows', '''float y=UV.y*TileCm/90.0; float fade=1.0-saturate(fwidth(y)); return 1.0-.035*(.5+.5*cos(y*6.2831853))*fade;''', {'UV': (uv, ''), 'TileCm': (self.scalar(m, 'row-tile-cm', recipe['tileCm']), '')}, 1)
            color = self.custom(m, 'natural-ground-color', GROUND_COLOR, {'Scan': (samples['albedo'], ''), 'Tint': (self.vector(m, 'linear-tint', recipe['tint']), ''),
                'Macro': (macro, ''), 'Strength': (self.scalar(m, 'macro-strength', recipe['macroStrength']), ''), 'Rows': (rows, ''),
                'AlbedoScale': (self.scalar(m, 'ground-albedo-response', recipe['albedoScale']), '')})
            if 'fieldMacro' in recipe:
                color, field_uv, field_channels = self.field_macro(m,recipe,pos,color)
            if 'groundOrthophoto' in recipe:
                color = self.ortho_ground(m,recipe,pos,color)
            normal = self.custom(m, 'world-ground-normal', GROUND_NORMAL, {'MapNormal': (samples['normal'], ''), 'Strength': (self.scalar(m, 'normal-strength', recipe['normalStrength']), ''), 'YawDegrees': (yaw, ''), 'VertexNormal': (vertex, '')})
            rough = self.custom(m, 'ground-roughness', 'return clamp(Scan.r,.63,.98);', {'Scan': (samples['roughness'], '')}, 1)
            if recipe.get('featherUV'):
                require(self.dither_function is not None, 'Native soil feather function must be validated before material writes')
                coverage = self.node(m, 'soil-exposure-coverage-uv0', u.MaterialExpressionTextureCoordinate,
                                     coordinate_index=0, u_tiling=1., v_tiling=1.)
                alpha_channel = self.node(m, 'soil-exposure-coverage-u', u.MaterialExpressionComponentMask,
                                          r=True, g=False, b=False, a=False)
                # MaterialEditingLibrary shortens the single ComponentMask
                # input 'Input' to NAME_None; use its supported first input.
                self.connect(coverage, '', alpha_channel, '')
                camera = self.node(m, 'soil-exposure-camera-position', u.MaterialExpressionCameraPositionWS)
                coverage_code=GROVE_LITTER_COVERAGE if key=='canopy_floor_litter' else SOIL_EXPOSURE_COVERAGE
                fade_range=recipe.get('distanceFadeCm',SOIL_EXPOSURE_FADE_CM)
                broken = self.custom(m, 'soil-exposure-spatial-camera-coverage', coverage_code,
                                     {'Position': (pos,''), 'Camera': (camera,''), 'EdgeCoverage': (alpha_channel,''),
                                      'FadeRange': (self.vector(m,'soil-exposure-fade-range-cm',[*fade_range,0]),'')}, 1)
                dither = self.node(m, 'soil-exposure-native-temporal-dither', u.MaterialExpressionMaterialFunctionCall)
                require(dither.set_material_function(self.dither_function), 'Cannot bind native soil feather function')
                alpha = [str(pin) for pin in self.lib.get_material_expression_input_names(dither) if 'alpha' in str(pin).lower()]
                require(len(alpha) == 1, 'Native soil feather alpha input is ambiguous')
                self.connect(broken, '', dither, alpha[0])
                self.out(dither, 'OPACITY_MASK')
        else:
            pos = self.node(m, 'world-position', u.MaterialExpressionWorldPosition)
            code = NOISE + ('float v=.95+.10*(en.value(Position.xy/1200.0)*.65+en.value(Position.xy/2300.0+19.0)*.35); return Palette*v;' if kind == 'village' else
                            'float v=.91+.18*en.value(Position.xy/7.0); return Palette*v;' if kind in ('marker', 'metal') else
                            'float grain=sin(Position.z*.14+en.value(Position.xy*2.0)*6.0); float v=.83+.11*grain+.17*en.value(Position.xy/3.0);return Palette*v;')
            color = self.custom(m, 'estimated-village-finish' if kind == 'village' else 'weathered-marker' if kind == 'marker' else 'weathered-wood', code,
                                {'Position': (pos, ''), 'Palette': (self.vector(m, 'linear-palette', recipe['linearColor']), '')})
            normal = self.vector(m, 'flat-tangent-normal', [0., 0., 1.])
            rough = self.scalar(m, 'marker-roughness', recipe['roughness'])
        for node, root in [(color, 'BASE_COLOR'), (normal, 'NORMAL'), (rough, 'ROUGHNESS')]: self.out(node, root)
        self.out(self.scalar(m, 'dielectric', recipe.get('metallic', 0.)), 'METALLIC')
        self.out(self.scalar(m, 'surface-specular', recipe.get('specular', .25)), 'SPECULAR')
        self.out(self.scalar(m, 'unbaked-occlusion', 1.), 'AMBIENT_OCCLUSION')
        require(not list(self.lib.recompile_material(m) or []), 'Exterior material shader compilation failed: '+key)
        encoded = json.dumps(recipe, sort_keys=True)
        self.assets.set_metadata_tag(m, 'BreziGeneratedBy', OWNER)
        self.assets.set_metadata_tag(m, 'BreziExteriorRecipe', encoded)
        require(self.assets.save_loaded_asset(m, only_if_is_dirty=False), 'Cannot save exterior material: '+key)
        graph = graph_snapshot(u, m)
        require(len(graph['nodes']) <= (110 if 'groundOrthophoto' in recipe else 80), 'Exterior material node budget exceeded')
        return m, {'asset': m.get_path_name(), 'recipe': recipe, 'graph': graph, 'graphSha256': digest(graph)}


def build_materials(vegetation_manifest=None, prefix=PREFIX, context_overrides=None, unreal_module=None, ortho_manifest=None, seasonal_fields_manifest=None, field_macro_manifest=None, projection_manifest=None, transition=None, lawn_photo=None):
    if unreal_module is None:
        import unreal as unreal_module
    manifest = prepare_manifest(vegetation_manifest, context_overrides)
    ortho = prepare_orthophoto(ortho_manifest) if ortho_manifest is not None else None
    seasonal=prepare_seasonal_fields(seasonal_fields_manifest,ortho) if seasonal_fields_manifest is not None else None
    field_macro=prepare_field_macro(field_macro_manifest) if field_macro_manifest is not None else None
    projection=prepare_projection(projection_manifest,ortho) if projection_manifest is not None else None
    if field_macro:
        for key in FIELD_MACRO_KEYS:manifest['materials'][key]['fieldMacro']={k:v for k,v in field_macro.items() if k!='inputFiles'}
    if seasonal:
        seasonal['nearArableStage']={'material':'context_arable','coverRange':[.52,.60],
                                    'claim':'Artist-authored low growing crop stage with retained soil, row pattern and original PBR response; not current crop observation.'}
        manifest['materials']['context_arable']['coverRange']=[.52,.60]
        manifest['materials']['context_arable']['artDirection']+='; R7 opt-in seasonal low growing crop stage, retaining soil and original row/PBR response'
        ortho['seasonalFields']={k:v for k,v in seasonal.items() if k!='inputFiles'}
    if ortho:
        manifest['materials']['context_distant_terrain']['orthophoto'] = {k:v for k,v in ortho.items() if k != 'inputFiles'}
        manifest['materials']['context_distant_terrain']['terrainOrthophotoCameraBlend'] = {
            'cameraDistanceBlendCm':list(GROUND_ORTHO_BLEND_CM), 'sourceManifestRadialBlendCm':copy.deepcopy(ortho['distanceBlendCm']),
            'response':'RGB only; matches context ground camera distance; retained radial PBR normal/roughness response',
            'providerPixelsAndAffineUnchanged':True, 'providerAlphaMip':0, 'actorBindingsChanged':False}
        if projection:
            # RGB permission is continuous across field boundaries, roads,
            # canopies and dark pixels. Scalar field contrast is independent.
            for key in PROJECTION_KEYS:
                manifest['materials'][key]['groundOrthophoto'] = {
                    **{k:copy.deepcopy(v) for k,v in ortho.items() if k not in ('inputFiles','seasonalFields')},
                    'cameraDistanceBlendCm': list(GROUND_ORTHO_BLEND_CM),
                    'protectedDomain': 'Geometry-only projection red permission and mip0 extent coverage; private subject site/buildings protected'}
                manifest['materials'][key]['projectionMask']={k:copy.deepcopy(v) for k,v in projection.items() if k!='inputFiles'}
    transition_module = transition_prepared = None
    if transition is not None:
        transition_spec = importlib.util.spec_from_file_location('exterior_transition_materials', ROOT/'scripts/unreal/exterior-neighborhood-transition-materials.py')
        transition_module = importlib.util.module_from_spec(transition_spec)
        transition_spec.loader.exec_module(transition_module)
        transition_prepared = transition_module.prepare_transition(transition)
    photo_module = photo_prepared = photo_api = None
    if lawn_photo is not None:
        photo_spec = importlib.util.spec_from_file_location('exterior_lawn_photo_materials', ROOT/'scripts/unreal/exterior-lawn-photo-materials-study.py')
        photo_module = importlib.util.module_from_spec(photo_spec)
        photo_spec.loader.exec_module(photo_module)
        photo_api = SimpleNamespace(prepare_manifest=prepare_manifest, source_encoding_proof=source_encoding_proof,
                                    derivation_inputs=derivation_inputs, digest=digest, graph_snapshot=graph_snapshot)
        photo_prepared = photo_module.prepare(lawn_photo, photo_api)
    dither_function, dither_receipt = prepare_dither_function(unreal_module) if any(recipe.get('featherUV') for recipe in manifest['materials'].values()) else (None, None)
    writer = Writer(unreal_module, prefix, dither_function)
    materials, records = {}, {}
    for key, recipe in manifest['materials'].items():
        materials[key], records[key] = writer.create(key, recipe)
    transition_report = transition_module.append_transition(writer,materials,records,transition_prepared,
                        {'graph_snapshot':graph_snapshot,'digest':digest,'OWNER':OWNER,'TAG':TAG}) if transition_module else None
    photo_report = photo_module.append_photographic_material(writer,materials,records,photo_api,photo_prepared) if photo_module else None
    dependencies = [ROOT / 'scripts/archviz/assets.lock.json', ROOT / 'output/archviz/assets/manifest.json',
                    ROOT / 'scripts/unreal/lawn-ground/reference.json', GROUND_ASSETS / 'manifest.json',
                    GROUND_ASSETS / 'farm_soil-files.json', GROUND_ASSETS / 'farm_soil-info.json',
                    ROOT / 'scripts/unreal/planting-surfaces/inputs.json']
    if isinstance(vegetation_manifest, (str, Path)):
        dependencies.append((ROOT / vegetation_manifest).resolve())
    inputs = {str(p): sha(p) for p in dependencies}
    if dither_receipt: inputs[dither_receipt['source']] = dither_receipt['sourceSha256']
    if ortho: inputs.update(ortho['inputFiles'])
    if seasonal:inputs.update(seasonal['inputFiles'])
    if field_macro:inputs.update(field_macro['inputFiles'])
    if projection:inputs.update(projection['inputFiles'])
    pipeline = {str(Path(__file__).resolve()): sha(__file__)}
    if transition_prepared:
        inputs.update(transition_prepared['inputFiles'])
        pipeline.update(transition_prepared['pipelineFiles'])
    if photo_report:
        inputs.update(photo_report['inputFiles'])
        pipeline.update(photo_report['pipelineFiles'])
    if projection:pipeline[str(ROOT/projection['owner'])]=sha(ROOT/projection['owner'])
    for key, recipe in manifest['materials'].items():
        for source in [recipe] + ([recipe['groundCover']] if 'groundCover' in recipe else []):
            for spec in source.get('maps', {}).values():
                inputs[spec['path']] = spec['sha256']
        if recipe.get('albedoDerivation'):
            inputs.update(derivation_inputs(key, recipe))
            proof = recipe['albedoDerivation']
            for field in ('sourceAlbedo','sourceAlpha','sourceGenerator'):
                spec = proof[field]; inputs[spec['path']] = spec['sha256']
            spec = proof['sourceGenerator']; pipeline[spec['path']] = spec['sha256']
        if recipe.get('leafCalibration'):
            spec = recipe['leafCalibration']['sourceMaterialManifest']; inputs[spec['path']] = spec['sha256']
        if recipe.get('sourceEncodingProof'):
            inputs.update(floor_encoding_inputs() if recipe['sourceEncodingProof']['path']==str(FLOOR_ENCODING_PROOF) else context_encoding_inputs())
    report = {'schemaVersion': 1, 'owner': OWNER, 'sourceSha256': sha(__file__), 'prefix': prefix,
              'status': 'saved-materials-awaiting-reload', 'materials': records, 'textures': writer.texture_report,
              'inputFiles': inputs, 'pipelineFiles': pipeline,
              'renderingPolicy': 'Masked atlas TwoSidedFoliage with coverage-preserving mipmaps; opaque authored plant geometry with vertex-colour variation; bounded transmission; native DitherTemporalAA with spatial soil breakup and 40-100m camera fade; stochastic registered PBR ground layers; optional licensed world-affine ortho macro with exact extent/coverage gates and protected field camera blend 50-150m; slope-aware world normal; no WPO/displacement/lighting mutation'}
    if dither_receipt: report['engineMaterialFunctions'] = [dither_receipt]
    if ortho:
        report['orthophoto'] = {k:v for k,v in ortho.items() if k not in ('inputFiles','layers')}
        report['terrainOrthophotoCameraBlend'] = {
            'materialKeys':['context_distant_terrain'],
            **copy.deepcopy(manifest['materials']['context_distant_terrain']['terrainOrthophotoCameraBlend'])}
        if projection:
            report['groundOrthophoto'] = {'materialKeys': sorted(PROJECTION_KEYS),
                                         'cameraDistanceBlendCm': list(GROUND_ORTHO_BLEND_CM),
                                         'protectedSiteGate': 'Smooth red protection-only permission, exact UV extent/mip0 green coverage and separate provider alpha mip0',
                                         'sourceObservationUnchanged': True, 'response': 'BaseColor only; original ground normal and roughness retained'}
            report['orthoProjection']={k:v for k,v in projection.items() if k not in ('inputFiles','texture')}
    if seasonal:report['seasonalFields']={k:v for k,v in seasonal.items() if k not in ('inputFiles','layers')}
    if field_macro:report['fieldMacro']={k:v for k,v in field_macro.items() if k not in ('inputFiles','texture')}
    if transition_report:report['neighborhoodTransition']=transition_report
    if photo_report:report['photographicLawn']=photo_report
    require(len(report['textures']) <= 72 + int('canopy_floor_litter' in report['materials']) + int(transition_report is not None), 'Exterior texture budget exceeded')
    return materials, report


def verify_materials(report, unreal_module=None):
    if unreal_module is None:
        import unreal as unreal_module
    u = unreal_module; assets = u.EditorAssetLibrary
    require(report['owner'] == OWNER and report['sourceSha256'] == sha(__file__), 'Exterior material source drift')
    for path, expected in {**report['inputFiles'], **report['pipelineFiles']}.items():
        require(sha(path) == expected, 'Exterior material dependency changed: ' + path)
    for expected in report.get('engineMaterialFunctions', []):
        _, actual = prepare_dither_function(u)
        require(actual == expected, 'Native soil feather function changed')
    for key, entry in report['materials'].items():
        m = assets.load_asset(entry['asset'])
        require(isinstance(m, u.Material) and m.get_path_name().startswith(report['prefix']+'/Materials/'), 'Exterior material missing/foreign')
        require(assets.get_metadata_tag(m, 'BreziGeneratedBy') == OWNER and
                assets.get_metadata_tag(m, 'BreziExteriorRecipe') == json.dumps(entry['recipe'], sort_keys=True), 'Exterior material recipe changed')
        require(digest(graph_snapshot(u, m)) == entry['graphSha256'], 'Saved exterior material graph differs: '+key)
        for usage in (native_enum(u.MaterialUsage, 'INSTANCEDSTATICMESHES'), u.MaterialUsage.MATUSAGE_NANITE):
            require(u.MaterialEditingLibrary.has_material_usage(m, usage), 'Exterior material usage missing')
    for entry in report['textures'].values():
        tex = assets.load_asset(entry['asset']); role = entry['role']
        require(isinstance(tex, u.Texture2D) and tex.get_path_name().startswith(report['prefix']+'/Textures/'), 'Exterior texture missing/foreign')
        require(assets.get_metadata_tag(tex, 'BreziGeneratedBy') == OWNER and assets.get_metadata_tag(tex, 'source_sha256') == entry['sourceSha256'], 'Exterior texture source drift')
        require(assets.get_metadata_tag(tex, 'BreziSourceLicense') == entry['sourceLicense']
                and assets.get_metadata_tag(tex, 'BreziSourcePage') == entry['sourcePage'], 'Exterior texture provenance drift')
        technical_role=assets.get_metadata_tag(tex,'BreziAuthoredTechnicalRole')
        if technical_role or role=='ground_condition':
            require(technical_role==role=='ground_condition' and entry['sourceLicense']=='LicenseRef-Project-Authored'
                    and entry['sourcePage']==str(ROOT/'scripts/unreal/exterior-neighborhood-transition-study.py')
                    and entry['sourceEncodingOverride']=='None' and entry['addressMode']=='clamp'
                    and [entry['width'],entry['height']]==[1024,1024], 'Saved authored condition role/provenance differs')
        encoding=entry['sourceEncodingOverride']
        require(encoding in ('None','sRGB') and assets.get_metadata_tag(tex,'BreziSourceEncodingOverride')==encoding,
                'Saved exterior source encoding receipt differs')
        if encoding=='sRGB':
            scoped=entry['sourceSha256']==FLOOR_ALBEDO_SHA and entry['sourcePage']=='https://polyhaven.com/a/forest_leaves_04'
            if entry['sourceSha256'] in CONTEXT_ENCODING_SOURCES:
                scoped=entry['sourcePage']==CONTEXT_ENCODING_SOURCES[entry['sourceSha256']][2]
            require(role=='albedo' and scoped,
                    'Saved exterior source encoding scope differs')
        actual_encoding=tex.get_editor_property('source_color_settings').get_editor_property('encoding_override')
        require(actual_encoding==native_enum(u.TextureSourceEncoding,'TSESRGB' if encoding=='sRGB' else 'TSENONE')
                and entry['sourceEncodingReadback']==('TSE_S_RGB' if encoding=='sRGB' else 'TSE_NONE'),
                'Saved exterior source encoding interpretation differs')
        compression = texture_compression(u,role)
        address = u.TextureAddress.TA_CLAMP if entry['addressMode'] == 'clamp' else u.TextureAddress.TA_WRAP
        expected = {'srgb': role == 'albedo', 'flip_green_channel': role == 'normal' and entry['normalConvention'] == 'OpenGL',
                    'compression_settings': compression, 'address_x': address, 'address_y': address,
                    'lod_bias': 0, 'max_texture_size': 0, 'virtual_texture_streaming': False,
                    'mip_gen_settings': u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP,
                    'power_of_two_mode': u.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO if entry['powerOfTwoMode'] == 'stretch' else u.TexturePowerOfTwoSetting.NONE,
                    'do_scale_mips_for_alpha_coverage': role == 'alpha'}
        if role=='season_mask':expected.update(mip_gen_settings=native_enum(u.TextureMipGenSettings,'TMGSNOMIPMAPS'),never_stream=True)
        if role in ('field_macro','ortho_projection','ground_condition'):expected['never_stream']=True
        require(all(tex.get_editor_property(k) == v for k, v in expected.items()), 'Saved exterior texture interpretation differs')
        coverage = tex.get_editor_property('alpha_coverage_thresholds')
        require(all(abs(float(getattr(coverage, axis))-value) < 1e-6 for axis, value in zip(('x', 'y', 'z', 'w'), entry['alphaCoverageThresholds'])), 'Saved alpha mip coverage differs')
        require([int(tex.blueprint_get_size_x()), int(tex.blueprint_get_size_y())] == [entry['width'], entry['height']], 'Saved exterior texture size differs')
    return {'status': 'verified-saved-exterior-materials', 'materials': len(report['materials']), 'textures': len(report['textures'])}
