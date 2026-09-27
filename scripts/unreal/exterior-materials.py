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
import json
import math
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-materials.py'
PREFIX = '/Game/Brezi/Exterior20260926'
GROUND_ASSETS = ROOT / 'output/unreal/exterior-ground-assets-20260926-r2'
TAG = 'BreziExterior:'
CONTEXT_KEYS = {'context_meadow', 'context_fallow', 'context_crop', 'context_arable', 'context_track',
                'context_garden_soil', 'context_mulch', 'context_distant_terrain', 'context_parcel_line',
                'context_boundary_post', 'context_vine_post', 'context_wire', 'context_village_wall',
                'context_village_roof', 'context_village_darkroof'}
ROOTS = ('BASE_COLOR', 'NORMAL', 'ROUGHNESS', 'METALLIC', 'SPECULAR',
         'AMBIENT_OCCLUSION', 'OPACITY_MASK', 'SUBSURFACE_COLOR', 'OPACITY',
         'WORLD_POSITION_OFFSET', 'EMISSIVE_COLOR')
FIELD_MACRO_KEYS = {'context_meadow','context_fallow','context_crop','context_arable'}


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
        ('context_meadow', sparse, [.92, 1., .92], .65, .82, [.70, .78]),
        ('context_fallow', sparse, [.97, .99, .90], .70, .80, [.60, .68]),
        ('context_crop', sparse, [.94, 1., .92], .45, .82, [.88, .94]),
        ('context_arable', sparse, [1., .95, .85], .75, .69, [.07, .13]),
        ('context_track', gravel, [.95, .92, .86], .65, .42, None),
        ('context_garden_soil', soil, [.94, 1., 1.04], .85, .95, [.025, .11]),
        ('context_mulch', mulch, [1., 1., 1.], 1., .92, None),
        ('context_distant_terrain', sparse, [1., 1., 1.], .0, 1., None),
    ]:
        recipes[key] = {**copy.deepcopy(source), 'kind': 'ground', 'tint': tint,
                        'normalStrength': strength, 'yawDegrees': 0.0,
                        'macroStrength': .05, 'albedoScale': scale, 'cropRows': key in ('context_crop', 'context_arable'),
                        'artDirection': 'R3 lowers R2 cloud-like grass/earth blend amplitude; bounded artist response, not measured site reflectance'}
        if cover:
            recipes[key].update(groundCover=copy.deepcopy(green), coverRange=cover)
    recipes['context_distant_terrain']['terrain'] = True
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
        require('orthophoto' not in recipe and 'fieldMacro' not in recipe, 'Geographic data must use validated optional manifest')
        require(recipe.get('powerOfTwoMode') in (None,'stretch'), 'Unreviewed exterior texture resize mode')
        kind = recipe.get('kind')
        require(kind in ('foliage', 'bark', 'ground', 'marker', 'wood', 'metal', 'village'), 'Unknown exterior material kind')
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
        if kind == 'foliage':
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
                    and original == {k:v for k,v in recipe.items() if k != 'leafCalibration'},
                    'Leaf calibration changed provider maps/response')
        require(not recipe.get('windCm', 0), 'Atlas root weights unavailable; wind must remain disabled')
    require(len(recipes) <= 30, 'Exterior material budget exceeded')
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


def texture_compression(u,role):
    if role=='field_macro':return native_enum(u.TextureCompressionSettings,'TCVECTORDISPLACEMENTMAP')
    if role=='season_mask':return native_enum(u.TextureCompressionSettings,'TCGRAYSCALE')
    return u.TextureCompressionSettings.TC_NORMALMAP if role=='normal' else u.TextureCompressionSettings.TC_DEFAULT if role=='albedo' else u.TextureCompressionSettings.TC_MASKS


def orthophoto_uv(position_cm, layer):
    return tuple(row[0]*position_cm[0]+row[1]*position_cm[1]+row[2] for row in layer['worldCmToUvRows'])


def orthophoto_weights(position_cm, layers, coverage, distance_blend_cm=(30000, 90000)):
    """CPU coverage/edge witness; zero-alpha and out-of-extent remain fallback."""
    weights = {}
    for layer in layers:
        uv = orthophoto_uv(position_cm, layer)
        valid = float(all(0 <= v <= 1 for v in uv) and coverage[layer['id']] >= .99)
        if layer['id'] == 'detail2km':
            box = layer['bboxMetres']
            edge = min(min(uv[i],1-uv[i])*(box[i+2]-box[i])*100 for i in range(2))
            valid *= _smoothstep(0,10000,edge)
        weights[layer['id']] = valid
    require(tuple(distance_blend_cm) in ((30000,90000),(18000,36000)), 'Unreviewed orthophoto distance blend')
    radial = _smoothstep(*distance_blend_cm,math.hypot(*position_cm[:2]))
    detail = weights['detail2km']*radial
    far = weights['far16km']*(1-weights['detail2km'])*radial
    return {'detail': detail, 'far': far, 'fallback': 1-detail-far}


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
              'MaterialExpressionTextureCoordinate': ['coordinate_index', 'u_tiling', 'v_tiling']}
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
    def __init__(self, u, prefix):
        require(prefix == PREFIX or prefix.startswith(PREFIX + '/'), 'Exterior namespace escaped')
        self.u, self.prefix = u, prefix
        self.assets, self.lib = u.EditorAssetLibrary, u.MaterialEditingLibrary
        self.textures, self.texture_report = {}, {}

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
        require(address in ('wrap','clamp'), 'Unknown exterior texture address mode')
        key = role + '_' + spec['sha256'][:16] + ('_flip' if flip else '') + (('_c'+str(round(coverage*1000))) if coverage else '') + ('_clamp' if address == 'clamp' else '') + ('_pot' if resize else '')
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
        if role=='field_macro':settings['never_stream']=True
        for k, v in settings.items(): tex.set_editor_property(k, v)
        for k, v in {'BreziGeneratedBy': OWNER, 'source_sha256': spec['sha256'], 'BreziSourceLicense': recipe['license'],
                     'BreziSourcePage': recipe.get('sourceUrl', recipe.get('page'))}.items(): self.assets.set_metadata_tag(tex, k, v)
        require(self.assets.save_loaded_asset(tex, only_if_is_dirty=False), 'Cannot save exterior texture')
        self.textures[key] = tex
        self.texture_report[key] = {'asset': tex.get_path_name(), 'role': role, 'sourceSha256': spec['sha256'],
                                    'sourcePath': spec['path'], 'normalConvention': recipe['normalConvention'],
                                    'sourceLicense': recipe['license'], 'sourcePage': recipe.get('sourceUrl', recipe.get('page')),
                                    'addressMode': address,
                                    'powerOfTwoMode': resize,
                                    'alphaCoverageThresholds': [coverage, 0., 0., 0.],
                                    'width': int(tex.blueprint_get_size_x()), 'height': int(tex.blueprint_get_size_y())}
        require(0 < self.texture_report[key]['width'] <= 8192 and 0 < self.texture_report[key]['height'] <= 8192, 'Exterior texture dimensions outside budget')
        if 'expectedDimensions' in recipe:
            require([self.texture_report[key][k] for k in ('width','height')] == recipe['expectedDimensions'], 'Orthophoto native dimensions differ')
        return tex

    def sample(self, m, role, recipe, uv, phase='', derivatives=None):
        sampler = native_enum(self.u.MaterialSamplerType,'SAMPLERTYPELINEARCOLOR') if role=='field_macro' else native_enum(self.u.MaterialSamplerType,'SAMPLERTYPELINEARGRAYSCALE') if role=='season_mask' else self.u.MaterialSamplerType.SAMPLERTYPE_COLOR if role == 'albedo' else self.u.MaterialSamplerType.SAMPLERTYPE_NORMAL if role == 'normal' else self.u.MaterialSamplerType.SAMPLERTYPE_MASKS
        node = self.node(m, role+phase, self.u.MaterialExpressionTextureSample, texture=self.texture(role, recipe), sampler_type=sampler)
        self.connect(uv, '', node, 'UVs')
        if derivatives:
            node.set_editor_property('mip_value_mode', self.u.TextureMipValueMode.TMVM_DERIVATIVE)
            for derivative, pin in zip(derivatives, ('DDX(UVs)', 'DDY(UVs)')):
                self.connect(derivative, '', node, pin)
        return node

    def ground_layer(self, m, recipe, uv, label):
        derivatives = [self.custom(m, label+'-gradient-'+axis, 'return '+axis+'(UV);', {'UV': (uv, '')}, 2)
                       for axis in ('ddx', 'ddy')]
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
                                             {'UV': (mapping,''), 'Coverage': (sample,'A')}, 1)
            if layer['id'] == 'detail2km':
                box = layer['bboxMetres']; extent = [(box[2]-box[0])*100,(box[3]-box[1])*100,0]
                valid[layer['id']] = self.custom(m, label+'-edge-feather-100m', ORTHO_DETAIL_WEIGHT,
                                                 {'UV': (mapping,''), 'Valid': (valid[layer['id']],''), 'ExtentCm': (self.vector(m,label+'-extent-cm',extent),'')}, 1)
        color = self.custom(m, 'licensed-ortho-basecolor', ORTHO_COLOR,
                            {'Fallback': (fallback,''), 'Far': samples['far16km'], 'FarValid': (valid['far16km'],''),
                             'Detail': samples['detail2km'], 'DetailWeight': (valid['detail2km'],''), 'DistanceBlend': (distance,'')})
        return color, normal, rough

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
        return self.custom(m,'field-macro-basecolor',FIELD_MACRO_COLOR,
                           {'Source':(color,''),'UV':(uv,''),'FactorChannel':(factor,'R'),
                            'Domain':(containment,'G'),'Coverage':(containment,'B'),'Weight':(containment,'A'),
                            'Range':(self.vector(m,'field-macro-factor-range',macro['factorRange']+[0.]),'')})

    def create(self, key, recipe):
        u = self.u; kind = recipe['kind']; foliage = kind == 'foliage'; ground = kind == 'ground'
        path = self.prefix + '/Materials/M_' + key
        require(not self.assets.does_asset_exist(path), 'Refusing to overwrite exterior material: ' + path)
        m = u.AssetToolsHelpers.get_asset_tools().create_asset('M_'+key, self.prefix+'/Materials', u.Material, u.MaterialFactoryNew())
        require(m is not None, 'Cannot create exterior material')
        flags = {'blend_mode': u.BlendMode.BLEND_MASKED if foliage else u.BlendMode.BLEND_OPAQUE,
                 'shading_model': native_enum(u.MaterialShadingModel, 'TWOSIDEDFOLIAGE') if foliage else u.MaterialShadingModel.MSM_DEFAULT_LIT,
                 'two_sided': foliage, 'tangent_space_normal': not ground,
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
            if 'fieldMacro' in recipe:color=self.field_macro(m,recipe,pos,color)
            normal = self.custom(m, 'world-ground-normal', GROUND_NORMAL, {'MapNormal': (samples['normal'], ''), 'Strength': (self.scalar(m, 'normal-strength', recipe['normalStrength']), ''), 'YawDegrees': (yaw, ''), 'VertexNormal': (vertex, '')})
            rough = self.custom(m, 'ground-roughness', 'return clamp(Scan.r,.63,.98);', {'Scan': (samples['roughness'], '')}, 1)
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
        require(len(graph['nodes']) <= 80, 'Exterior material node budget exceeded')
        return m, {'asset': m.get_path_name(), 'recipe': recipe, 'graph': graph, 'graphSha256': digest(graph)}


def build_materials(vegetation_manifest=None, prefix=PREFIX, context_overrides=None, unreal_module=None, ortho_manifest=None, seasonal_fields_manifest=None, field_macro_manifest=None):
    if unreal_module is None:
        import unreal as unreal_module
    manifest = prepare_manifest(vegetation_manifest, context_overrides)
    ortho = prepare_orthophoto(ortho_manifest) if ortho_manifest is not None else None
    seasonal=prepare_seasonal_fields(seasonal_fields_manifest,ortho) if seasonal_fields_manifest is not None else None
    field_macro=prepare_field_macro(field_macro_manifest) if field_macro_manifest is not None else None
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
    writer = Writer(unreal_module, prefix)
    materials, records = {}, {}
    for key, recipe in manifest['materials'].items():
        materials[key], records[key] = writer.create(key, recipe)
    dependencies = [ROOT / 'scripts/archviz/assets.lock.json', ROOT / 'output/archviz/assets/manifest.json',
                    ROOT / 'scripts/unreal/lawn-ground/reference.json', GROUND_ASSETS / 'manifest.json',
                    GROUND_ASSETS / 'farm_soil-files.json', GROUND_ASSETS / 'farm_soil-info.json',
                    ROOT / 'scripts/unreal/planting-surfaces/inputs.json']
    if isinstance(vegetation_manifest, (str, Path)):
        dependencies.append((ROOT / vegetation_manifest).resolve())
    inputs = {str(p): sha(p) for p in dependencies}
    if ortho: inputs.update(ortho['inputFiles'])
    if seasonal:inputs.update(seasonal['inputFiles'])
    if field_macro:inputs.update(field_macro['inputFiles'])
    pipeline = {str(Path(__file__).resolve()): sha(__file__)}
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
    report = {'schemaVersion': 1, 'owner': OWNER, 'sourceSha256': sha(__file__), 'prefix': prefix,
              'status': 'saved-materials-awaiting-reload', 'materials': records, 'textures': writer.texture_report,
              'inputFiles': inputs, 'pipelineFiles': pipeline,
              'renderingPolicy': 'Masked TwoSidedFoliage with red-channel coverage-preserving mipmaps; provider albedo values and explicitly recorded leaf artist calibration; bounded transmission; stochastic registered PBR ground layers; optional licensed world-affine ortho macro with extent/coverage gates; slope-aware world normal; no WPO/displacement/lighting mutation'}
    if ortho:
        report['orthophoto'] = {k:v for k,v in ortho.items() if k not in ('inputFiles','layers')}
    if seasonal:report['seasonalFields']={k:v for k,v in seasonal.items() if k not in ('inputFiles','layers')}
    if field_macro:report['fieldMacro']={k:v for k,v in field_macro.items() if k not in ('inputFiles','texture')}
    require(len(report['textures']) <= 72, 'Exterior texture budget exceeded')
    return materials, report


def verify_materials(report, unreal_module=None):
    if unreal_module is None:
        import unreal as unreal_module
    u = unreal_module; assets = u.EditorAssetLibrary
    require(report['owner'] == OWNER and report['sourceSha256'] == sha(__file__), 'Exterior material source drift')
    for path, expected in {**report['inputFiles'], **report['pipelineFiles']}.items():
        require(sha(path) == expected, 'Exterior material dependency changed: ' + path)
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
        compression = texture_compression(u,role)
        address = u.TextureAddress.TA_CLAMP if entry['addressMode'] == 'clamp' else u.TextureAddress.TA_WRAP
        expected = {'srgb': role == 'albedo', 'flip_green_channel': role == 'normal' and entry['normalConvention'] == 'OpenGL',
                    'compression_settings': compression, 'address_x': address, 'address_y': address,
                    'lod_bias': 0, 'max_texture_size': 0, 'virtual_texture_streaming': False,
                    'mip_gen_settings': u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP,
                    'power_of_two_mode': u.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO if entry['powerOfTwoMode'] == 'stretch' else u.TexturePowerOfTwoSetting.NONE,
                    'do_scale_mips_for_alpha_coverage': role == 'alpha'}
        if role=='season_mask':expected.update(mip_gen_settings=native_enum(u.TextureMipGenSettings,'TMGSNOMIPMAPS'),never_stream=True)
        if role=='field_macro':expected['never_stream']=True
        require(all(tex.get_editor_property(k) == v for k, v in expected.items()), 'Saved exterior texture interpretation differs')
        coverage = tex.get_editor_property('alpha_coverage_thresholds')
        require(all(abs(float(getattr(coverage, axis))-value) < 1e-6 for axis, value in zip(('x', 'y', 'z', 'w'), entry['alphaCoverageThresholds'])), 'Saved alpha mip coverage differs')
        require([int(tex.blueprint_get_size_x()), int(tex.blueprint_get_size_y())] == [entry['width'], entry['height']], 'Saved exterior texture size differs')
    return {'status': 'verified-saved-exterior-materials', 'materials': len(report['materials']), 'textures': len(report['textures'])}
