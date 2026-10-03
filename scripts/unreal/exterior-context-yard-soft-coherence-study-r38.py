"""Source-only two-material proposal for coherent, fixed-world yard ground.

This does not import, compile, copy or modify an Unreal project. R37 selection,
saved report and target relocation are deliberately unbound. Old radial/camera
response stays the exact source subgraph outside the conservative yard mask.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-soft-coherence-study-r38.py'
OUTPUT = ROOT/'output/unreal/exterior-context-yard-soft-coherence-20261002-r38-source-study'
FIXTURE = ROOT/'output/unreal/exterior-context-yard-soft-coherence-20261002-r38-raster-fixture-r1'
PREFIX = '/Game/Brezi/ContextYardSoftCoherence20261002R38'
MASK_ASSET = PREFIX+'/Textures/T_soft_permission_r38.T_soft_permission_r38'
TAG = 'BreziYardSoftR38:'
SCHEMA = 'brezi-fixed-world-yard-soft-ground-coherence-source-r38'
TARGETS = ('BU.572063', 'BU.3800911', 'BU.3852341')
FALLOFF_CM = 150.0
QUANTIZATION_GUARD_CM = 1.0
MASK_SIMPLIFICATION_CM = .25
MASK_RESOLUTION = 2048
SOURCES = {
    'yardR28': 'output/unreal/exterior-context-yard-20261002-r28-study/yard-source-plan.json',
    'backdropR35': 'output/unreal/exterior-20261002-r35b/context-yard-repair-native-report-r2.json',
    'groundR32': 'output/unreal/exterior-20261002-r32a/context-yard-ground-native-report.json',
    'originalR16': 'output/unreal/exterior-20261001-r16a/exterior-import-report.json',
}
EXPECTED_SHA = {
    'backdropR35': '22f38c206686040bb8027b2f5cd7abc479ff2749a5edd78cafabed8191ecc7ed',
    'groundR32': '99b80074fe1309ee951ea662cf42f75ecd6d0a2bc711f0c76cc5d34e18891a19',
    'originalR16': '1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122',
}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def checked(row):
    p = Path(row['path'])
    require(sha(p) == row['sha256'] and ('bytes' not in row or p.stat().st_size == row['bytes']), 'Source pin differs: '+str(p))
    return p


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def polygons(geometry):
    if geometry.is_empty:
        return []
    if geometry.geom_type == 'Polygon':
        return [geometry]
    return [p for g in geometry.geoms for p in polygons(g)]


def segment_distance(point, a, b):
    dx, dy = b[0]-a[0], b[1]-a[1]
    den = dx*dx+dy*dy
    require(den > 0, 'Nonzero polygon edges required')
    t = max(0., min(1., ((point[0]-a[0])*dx+(point[1]-a[1])*dy)/den))
    return math.hypot(point[0]-a[0]-t*dx, point[1]-a[1]-t*dy)


def ring_inside(point, ring):
    # Exact CPU boundary exclusion; native floating-point shader evaluation
    # remains unmeasured. Conservative 1 cm source erosion is separate.
    inside = False
    x, y = point
    for a, b in zip(ring, ring[1:]+ring[:1]):
        if segment_distance(point, a, b) == 0.:
            return False
        if (a[1] > y) != (b[1] > y) and x < a[0]+(b[0]-a[0])*(y-a[1])/(b[1]-a[1]):
            inside = not inside
    return inside


def mask_weight(point, mask):
    require(len(point) == 2 and all(math.isfinite(v) for v in point), 'Finite world XY required')
    weight = 0.
    for p in mask['polygons']:
        bounds = p['boundsCm']
        if not (bounds[0] < point[0] < bounds[2] and bounds[1] < point[1] < bounds[3]):
            continue
        rings = p['ringsCm']
        if not ring_inside(point, rings[0]) or any(ring_inside(point, h) for h in rings[1:]):
            continue
        d = min(segment_distance(point, a, b) for ring in rings for a, b in zip(ring, ring[1:]+ring[:1]))
        t = min(1., d/mask['interiorFalloffCm'])
        weight = max(weight, t*t*(3.-2.*t))
    return weight


def outside_preserving_mix(old, common, local):
    require(math.isfinite(local) and 0. <= local <= 1., 'Mask is in [0,1]')
    if local <= 0.:
        return copy.deepcopy(old)
    if isinstance(old, (list, tuple)):
        return [a+(b-a)*local for a, b in zip(old, common)]
    return old+(common-old)*local


def hlsl_mask(mask):
    lines = ['// Artist-authored fixed world-cm permission mask; no camera input.', 'float2 P = Position.xy;', 'float Result = 0.0;']
    for j, p in enumerate(mask['polygons']):
        b = p['boundsCm']
        lines.append('if (P.x > %.9g && P.y > %.9g && P.x < %.9g && P.y < %.9g) {' % tuple(b))
        lines.append('float D2 = 22500.0; bool Inside = false; bool Hole = false;')
        for k, ring in enumerate(p['ringsCm']):
            name = 'R%d_%d' % (j, k)
            pairs = ','.join('float2(%.9g,%.9g)' % tuple(xy) for xy in ring)
            lines.append('const float2 %s[%d] = {%s};' % (name, len(ring), pairs))
            # A hole farther than the 150 cm falloff cannot affect coverage.
            rb = [min(x[i] for x in ring) for i in (0, 1)]+[max(x[i] for x in ring) for i in (0, 1)]
            lines.append('if (P.x >= %.9g && P.y >= %.9g && P.x <= %.9g && P.y <= %.9g) {' % (rb[0]-150., rb[1]-150., rb[2]+150., rb[3]+150.))
            lines.append('bool RingInside = false;')
            lines.append('[loop] for (int I=0; I<%d; ++I) {' % len(ring))
            lines.append('float2 A=%s[I], B=%s[(I+1)%%%d]; float2 E=B-A; float EE=dot(E,E);' % (name, name, len(ring)))
            lines.append('float2 BoxDelta=max(max(min(A,B)-P,P-max(A,B)),0.0);')
            lines.append('if (dot(BoxDelta,BoxDelta)<D2) { float T=saturate(dot(P-A,E)/EE); float2 Delta=P-(A+T*E); D2=min(D2,dot(Delta,Delta)); }')
            lines.append('if ((A.y>P.y)!=(B.y>P.y)) { if (P.x<A.x+(B.x-A.x)*(P.y-A.y)/(B.y-A.y)) RingInside=!RingInside; }')
            lines.append('}')
            lines.append('Inside=RingInside;' if k == 0 else 'Hole=Hole||RingInside;')
            lines.append('}')
        lines.append('if (Inside && !Hole && D2>0.0) { float T=saturate(sqrt(D2)/150.0); Result=max(Result,T*T*(3.0-2.0*T)); }')
        lines.append('}')
    lines.append('return Result;')
    return '\n'.join(lines)


def raster_layout(mask):
    points = [xy for p in mask['polygons'] for r in p['ringsCm'] for xy in r]
    bounds = [math.floor(min(p[i] for p in points)/100)*100-200 for i in (0, 1)]
    bounds += [math.ceil(max(p[i] for p in points)/100)*100+200 for i in (0, 1)]
    step = [(bounds[i+2]-bounds[i])/MASK_RESOLUTION for i in (0, 1)]
    return {'boundsCm': bounds, 'dimensions': [MASK_RESOLUTION, MASK_RESOLUTION], 'worldCmPerTexelXY': step,
            'minimumCenterToMaskBoundaryCm': math.hypot(*step)+1., 'bilinearSupportDiagonalCm': math.hypot(*step),
            'additionalWorldFloatGuardCm': 1., 'interiorFalloffAfterRasterGuardCm': FALLOFF_CM,
            'worldUv': 'U=(WorldX-minX)/width; V=(maxY-WorldY)/height; absolute fixed world cm',
            'plannedNativePolicy': {'srgb': False, 'compressionNone': True, 'mipGenSettings': 'NO_MIPMAPS',
                'addressX': 'CLAMP', 'addressY': 'CLAMP', 'powerOfTwoMode': 'NONE', 'sampleChannel': 'R',
                'noMipsOrBlockCompressionMayBeSubstituted': True}, 'nativeImportedPixelsDecoded': False}


def rasterize_mask(mask):
    """One source-only, uncompressed 8-bit field; license photographs untouched.

    Each nonzero center is farther from the complete polygon boundary than
    the entire bilinear sample support diagonal plus 1 cm. Exhaustive center
    inequalities establish CPU support containment; GPU sampling is pending.
    """
    import io
    import numpy as np
    import shapely
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    from PIL import Image
    geometry = unary_union([Polygon(p['ringsCm'][0], p['ringsCm'][1:]) for p in mask['polygons']])
    layout = raster_layout(mask); b = layout['boundsCm']; sx, sy = layout['worldCmPerTexelXY']; n = MASK_RESOLUTION
    pixels = np.zeros((n, n), dtype=np.uint8)
    boundary = geometry.boundary; guard = layout['minimumCenterToMaskBoundaryCm']
    count = 0; min_distance = math.inf; support_examples = []
    for start in range(0, n, 32):
        rr, cc = np.meshgrid(np.arange(start, min(start+32, n)), np.arange(n), indexing='ij')
        xx = b[0]+(cc+.5)*sx; yy = b[3]-(rr+.5)*sy
        inside = shapely.contains_xy(geometry, xx, yy)
        if not inside.any():
            continue
        d = np.asarray(shapely.distance(shapely.points(xx[inside], yy[inside]), boundary))
        t = np.clip((d-guard)/FALLOFF_CM, 0., 1.)
        values = np.floor(255.*t*t*(3.-2.*t)).astype(np.uint8)
        block = pixels[start:start+len(rr)]; block[inside] = values
        positive = values > 0
        if positive.any():
            require(bool(np.all(d[positive] > guard)), 'Every nonzero center must exceed full bilinear support guard')
            count += int(positive.sum()); min_distance = min(min_distance, float(d[positive].min()))
            xyp = np.column_stack((xx[inside][positive], yy[inside][positive]))
            # Bounded illustrative corners supplement the exhaustive distance
            # inequality; they do not replace it or claim native texel proof.
            support_examples.append(xyp[len(xyp)//2].tolist())
    require(count > 0 and not pixels[0].any() and not pixels[-1].any() and not pixels[:, 0].any() and not pixels[:, -1].any(), 'Positive interior and exact zero clamped image border required')
    raw = pixels.tobytes(); encoded = io.BytesIO(); Image.fromarray(pixels, mode='L').save(encoded, format='PNG')
    proof = {'schema': SCHEMA, 'sourceMaskSha256': digest(mask), 'layout': layout, 'pixelBits': 8, 'mode': 'L',
             'originalLicensedPhotoPixelsEdited': False, 'generatedArtistPermissionField': True,
             'nonzeroTexels': count, 'minimumNonzeroCenterBoundaryDistanceCm': min_distance,
             'exhaustiveNonzeroCenterDistanceGuardChecked': True, 'sourceBilinearSupportInsideQuantizedMask': True,
             'bilinearSupportExamplesCm': support_examples, 'rawPixelsSha256': hashlib.sha256(raw).hexdigest(),
             'exactZeroAllFourImageBorders': True, 'runtimeMipCompressionPolicyVerified': False,
             'nativeGpuBoundaryZeroVerified': False, 'nativeApplied': False}
    return pixels, encoded.getvalue(), proof


def custom(role, code, inputs, width=3):
    return {'role': TAG+role, 'class': 'MaterialExpressionCustom',
            'values': {'code': code, 'output_type': '<CustomMaterialOutputType.CMOT_FLOAT%d: %d>' % (width, {1: 0, 3: 2}[width])},
            'inputs': [[key, value[0], value[1]] for key, value in inputs.items()]}


def graph_proposals(original, substrate, mask):
    require(len(original['nodes']) == 58 and original['roots']['BASE_COLOR'] == ['BreziExterior:licensed-ortho-basecolor', ''], 'Exact saved backdrop basis required')
    n = {x['role']: x for x in original['nodes']}
    require(n['BreziExterior:near-terrain-pbr-color']['values']['code'] == 'return lerp(Terrain,Scan,.65*Near);', 'Use actual saved .65, not stale recipe')
    require(n['BreziExterior:near-terrain-normal-strength']['values']['code'] == 'return .65*Near;', 'Actual .65 normal endpoint required')
    additions = [
        {'role': TAG+'common-near-one', 'class': 'MaterialExpressionConstant', 'values': {'r': 1.}, 'inputs': []},
        {'role': TAG+'common-normal-strength', 'class': 'MaterialExpressionConstant', 'values': {'r': f32(.65)}, 'inputs': []},
        {'role': TAG+'common-artist-flat-up', 'class': 'MaterialExpressionConstant3Vector', 'values': {'constant': [0., 0., 1., 1.]}, 'inputs': []},
    ]
    layout = raster_layout(mask); b = layout['boundsCm']
    uvcode = 'return float2((Position.x-%.9g)/%.9g,(%.9g-Position.y)/%.9g);' % (b[0], b[2]-b[0], b[3], b[3]-b[1])
    additions.append({'role': TAG+'fixed-world-mask-uv', 'class': 'MaterialExpressionCustom',
        'values': {'code': uvcode, 'output_type': '<CustomMaterialOutputType.CMOT_FLOAT2: 1>'},
        'inputs': [['Position', 'BreziExterior:world-position', 'XYZ']]})
    sample = copy.deepcopy(n['BreziExterior:roughness-terrain-detail-0']); sample['role'] = TAG+'fixed-world-yard-mask'
    sample['values']['texture'] = MASK_ASSET
    sample['inputs'] = [['UVs', TAG+'fixed-world-mask-uv', ''], ['Tex', None, None], ['Apply View MipBias', None, None]]
    additions.append(sample)
    # The two existing flat artistic surfaces have different microrelief vertex
    # normals/Z. An explicit shared flat-up endpoint prevents that difference
    # reintroducing a material edge. This is no surveyed/physical normal claim.
    land = copy.deepcopy(n['BreziExterior:distant-landcover-art-direction'])
    land['role'] = TAG+'common-flat-landcover'
    require('Position.z' in land['values']['code'], 'Known flat-landcover source code required')
    land['values']['code'] = land['values']['code'].replace('Position.z', '0.0')
    next(e for e in land['inputs'] if e[0] == 'VertexNormal')[1:] = [TAG+'common-artist-flat-up', '']
    additions.append(land)
    for oldrole, newrole in (('near-terrain-pbr-color', 'common-color'), ('ortho-terrain-slope-normal', 'common-normal'), ('ortho-terrain-roughness', 'common-roughness')):
        row = copy.deepcopy(n['BreziExterior:'+oldrole]); row['role'] = TAG+newrole
        for edge in row['inputs']:
            if edge[0] == 'Near':
                edge[1:] = [TAG+'common-near-one', '']
            if edge[0] == 'Strength':
                edge[1:] = [TAG+'common-normal-strength', '']
            if edge[0] == 'VertexNormal':
                edge[1:] = [TAG+'common-artist-flat-up', '']
            if edge[0] == 'Terrain':
                edge[1:] = [TAG+'common-flat-landcover', '']
        additions.append(row)
    for root, endpoint, width in (('BASE_COLOR', 'color', 3), ('NORMAL', 'normal', 3), ('ROUGHNESS', 'roughness', 1)):
        code = 'if (Local<=0.0) return Old; return '+('normalize(lerp(Old,Common,Local));' if root == 'NORMAL' else 'lerp(Old,Common,Local);')
        additions.append(custom('final-'+endpoint, code, {'Old': tuple(original['roots'][root]), 'Common': (TAG+'common-'+endpoint, ''), 'Local': (TAG+'fixed-world-yard-mask', 'R')}, width))
    backdrop = copy.deepcopy(original); backdrop['nodes'] += additions
    for root, endpoint in (('BASE_COLOR', 'color'), ('NORMAL', 'normal'), ('ROUGHNESS', 'roughness')):
        backdrop['roots'][root] = [TAG+'final-'+endpoint, '']
    backdrop['nodes'].sort(key=lambda x: x['role'])
    floor = copy.deepcopy(backdrop)
    alpha_roles = {'uv1', 'coverage-r', 'temporal-dither'}
    alpha = [copy.deepcopy(x) for x in substrate['nodes'] if x['role'].split(':')[-1] in alpha_roles]
    require(len(alpha) == 3, 'Exact original substrate three-node coverage route required')
    # The saved R32 UV1-R/dither route is retained verbatim, including node roles.
    floor['nodes'] += alpha; floor['nodes'].sort(key=lambda x: x['role'])
    floor['flags'] = copy.deepcopy(substrate['flags']); floor['roots']['OPACITY_MASK'] = copy.deepcopy(substrate['roots']['OPACITY_MASK'])
    require(len(backdrop['nodes']) == 70 and len(floor['nodes']) == 73, 'Bounded graph budget changed')
    return {'backdrop': backdrop, 'substrate': floor}


def validate_graphs(original, substrate, graphs):
    # Explicit exact source subgraph preservation; this is not shader bytecode.
    original_nodes = {n['role']: n for n in original['nodes']}
    for key, graph in graphs.items():
        nodes = {n['role']: n for n in graph['nodes']}
        require(len(nodes) == len(graph['nodes']) and all(nodes[r] == row for r, row in original_nodes.items()), 'Every original node/input/texture/code stays exact')
        for root, route in original['roots'].items():
            if root not in ('BASE_COLOR', 'NORMAL', 'ROUGHNESS') and not (key == 'substrate' and root == 'OPACITY_MASK'):
                require(graph['roots'][root] == route, 'Undeclared graph root changed')
        uv = nodes[TAG+'fixed-world-mask-uv']; mask = nodes[TAG+'fixed-world-yard-mask']
        require(uv['inputs'] == [['Position', 'BreziExterior:world-position', 'XYZ']] and 'Camera' not in uv['values']['code'], 'Local mask must not follow camera')
        require(mask['values']['texture'] == MASK_ASSET and mask['inputs'] == [['UVs', TAG+'fixed-world-mask-uv', ''], ['Tex', None, None], ['Apply View MipBias', None, None]], 'Exact fixed-world field sample route required')
        for endpoint in ('color', 'normal', 'roughness'):
            final = nodes[TAG+'final-'+endpoint]
            require(final['values']['code'].startswith('if (Local<=0.0) return Old;'), 'Outside branch must return original source value directly')
    require(graphs['backdrop']['flags'] == original['flags'], 'Original opaque backdrop policy must stay exact')
    alpha = [n for n in substrate['nodes'] if n['role'].split(':')[-1] in {'uv1', 'coverage-r', 'temporal-dither'}]
    floor_nodes = {n['role']: n for n in graphs['substrate']['nodes']}
    require(all(floor_nodes[n['role']] == n for n in alpha) and graphs['substrate']['flags'] == substrate['flags'], 'Substrate UV1 opacity/dither/policy differs')
    common_roles = [TAG+r for r in ('common-near-one', 'common-normal-strength', 'common-artist-flat-up', 'common-flat-landcover', 'common-color', 'common-normal', 'common-roughness', 'fixed-world-mask-uv', 'fixed-world-yard-mask', 'final-color', 'final-normal', 'final-roughness')]
    require(all(next(n for n in graphs['backdrop']['nodes'] if n['role'] == r) == floor_nodes[r] for r in common_roles), 'Both surfaces must share exact common response and phase')
    return {'original58NodesAndConnectionsExact': True, 'sameTwelveNewResponseNodesOnBothSurfaces': True, 'opaqueNodes': 70, 'maskedNodes': 73,
            'outsideOriginalSourceValueDirectBranch': True, 'outsideGpuByteEquivalenceVerified': False,
            'substrateOriginalThreeNodeUv1CoverageRouteExact': True, 'newCameraDependentNodes': 0}


def build_source():
    from shapely.geometry import Polygon, shape, mapping
    from shapely.ops import unary_union
    inputs = {k: pin(ROOT/v) for k, v in SOURCES.items()}
    for key, expected in EXPECTED_SHA.items():
        require(inputs[key]['sha256'] == expected, 'Known actual report revision changed')
    records = {k: read(checked(p)) for k, p in inputs.items()}
    yard = records['yardR28']; r35 = records['backdropR35']; r32 = records['groundR32']
    require(yard['activeDesign'] == r35['activeDesign'] == r32['activeDesign'] == {'variant': 'C', 'livingLayout': 'B', 'heatingLayout': 'B'}
            and yard['setbacksMm'] == r35['setbacksMm'] == r32['setbacksMm'] == {'street': 3000, 'east': 3000}, 'C/B/B 3000 protections differ')
    require(r35['nativeApplied'] is True and r35['savedMapUnloadedReloaded'] is True and r32['nativeApplied'] is True, 'Use actually saved historical materials')
    inputs['buildingPlan'] = yard['inputFiles']['buildings']; inputs['originalExclusions'] = yard['masks']
    inputs['originalYardLayout'] = yard['layout']; inputs['originalYardProducer'] = pin(ROOT/'scripts/unreal/exterior-context-yard-study-r28.py')
    buildings = read(checked(inputs['buildingPlan']))['buildings']; masks = read(checked(inputs['originalExclusions']))
    require(set(masks) == {'protected', 'subject', 'roads', 'buildings', 'cultivatedGround'}, 'Exact original five masks required')
    exclusions = unary_union([shape(v).buffer(20) for v in masks.values()])
    domains = {}
    for key in TARGETS:
        row = next(b for b in buildings if b['id'] == key)
        foot = unary_union([Polygon(r[0], r[1:]) for r in row['polygonsCm']])
        domains[key] = foot.buffer(700).difference(exclusions)
    allowed = unary_union(list(domains.values()))
    inner = allowed.buffer(-QUANTIZATION_GUARD_CM).simplify(MASK_SIMPLIFICATION_CM, preserve_topology=True)
    result = []
    for p in sorted(polygons(inner), key=lambda x: x.bounds):
        rings = [[[f32(x), f32(y)] for x, y in ring.coords[:-1]] for ring in [p.exterior]+list(p.interiors)]
        quantized = Polygon(rings[0], rings[1:])
        require(quantized.is_valid and allowed.covers(quantized) and quantized.disjoint(exclusions), 'F32 shader polygon leaves original permission/exclusion masks')
        result.append({'ringsCm': rings, 'boundsCm': list(quantized.bounds), 'areaM2': quantized.area/10000})
    mask = {'coordinateSystem': 'absolute-world-centimeters-XY', 'sourceOriginalYardEnvelopeCm': 700,
            'originalExclusionBufferCm': 20, 'conservativeF32PermissionErosionCm': QUANTIZATION_GUARD_CM,
            'sourceMaskSimplificationMaximumCm': MASK_SIMPLIFICATION_CM,
            'interiorFalloffCm': FALLOFF_CM, 'polygons': result,
            'allowedOriginalDomain': mapping(allowed), 'allowedOriginalAreaM2': allowed.area/10000,
            'quantizedMaskAreaM2': sum(p['areaM2'] for p in result), 'targetBuildingSourceIds': list(TARGETS)}
    mask['segments'] = sum(len(r) for p in result for r in p['ringsCm'])
    mask['maximumSegmentsInsideSinglePolygonBounds'] = max(sum(len(r) for r in p['ringsCm']) for p in result)
    mask['permissionAreaRemovedM2'] = mask['allowedOriginalAreaM2']-mask['quantizedMaskAreaM2']
    require(mask['segments'] <= 512 and len(result) <= 12, 'Bounded shader mask budget exceeded')
    original = r35['repairC']['materialReport']['graph']; substrate = r32['newMaterialReport']['materials']['yard_substrate_r32']['graph']
    require(digest(original) == r35['repairC']['materialReport']['graphSha256'], 'Actual58 graph source digest differs')
    graphs = graph_proposals(original, substrate, mask); graph_audit = validate_graphs(original, substrate, graphs)
    maps = records['originalR16']['materials']['materials']['context_distant_terrain']['recipe']
    require(maps['license'] == 'CC0-1.0' and maps['sourceUrl'] == 'https://polyhaven.com/a/sparse_grass', 'Use existing licensed original photo maps')
    for role, row in maps['maps'].items():
        inputs['originalPhoto_'+role] = pin(checked(row))
    photo_objects = sorted({n['values']['texture'] for n in original['nodes'] if n['class'] == 'MaterialExpressionTextureSample' and '-terrain-detail-' in n['role']})
    require(len(photo_objects) == 3, 'Exactly three original sparse-grass native textures required')
    witness = read(checked(r35['savedActorWitness']))
    target_witness = {k: v for k, v in witness.items() if k.endswith(('StaticMeshActor_197', 'StaticMeshActor_668'))}
    require(len(target_witness) == 2, 'Exact backdrop/substrate historical targets required')
    inputs['historicalR35SavedWitness'] = r35['savedActorWitness']
    return {'inputs': inputs, 'mask': mask, 'graphs': graphs, 'graphAudit': graph_audit, 'originalGraph': original, 'substrateGraph': substrate,
            'targetWitness': target_witness, 'photoNativeObjects': photo_objects,
            'domains': domains, 'allowed': allowed, 'exclusions': exclusions}


def diagram(mask):
    points = [xy for p in mask['polygons'] for r in p['ringsCm'] for xy in r]
    lo = [min(p[i] for p in points)-200 for i in (0, 1)]; hi = [max(p[i] for p in points)+200 for i in (0, 1)]
    scale = min(950/(hi[0]-lo[0]), 700/(hi[1]-lo[1]))
    def xy(p): return (25+(p[0]-lo[0])*scale, 65+(hi[1]-p[1])*scale)
    svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1000" height="820" role="img" aria-label="Source-only fixed-world yard mask and 150 centimeter inward fade">', '<rect width="100%" height="100%" fill="#f5f3ea"/>', '<text x="25" y="27" font-family="sans-serif" font-size="20">R38: fixed-world soft-ground permission mask (source only)</text>', '<text x="25" y="51" font-family="sans-serif" font-size="13">Existing R28 yards; original protected/road/building/cultivated exclusions. No geometry or vegetation change.</text>']
    from shapely.geometry import Polygon
    for p in mask['polygons']:
        poly = Polygon(p['ringsCm'][0], p['ringsCm'][1:]); core = poly.buffer(-FALLOFF_CM)
        for g, color in ((poly, '#ccd7af'), (core, '#66844b')):
            for q in polygons(g):
                path = ' '.join('M '+' L '.join('%.2f %.2f' % xy(z) for z in ring.coords)+' Z' for ring in [q.exterior]+list(q.interiors))
                svg.append('<path d="'+path+'" fill="'+color+'" fill-rule="evenodd" stroke="#34492a" stroke-width=".7"/>')
    svg += ['<text x="25" y="790" font-family="sans-serif" font-size="14">Light band: 0–150 cm smooth inward blend. Dark: common .65 artistic PBR endpoint. Native pixels unverified.</text>', '</svg>']
    return '\n'.join(svg)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument('--cpu-log', type=Path, required=True); args = parser.parse_args()
    require(not OUTPUT.exists(), 'Fresh isolated R38 source output only')
    log = args.cpu_log.read_text(); require('Ran 10 tests' in log and '\nOK\n' in log, 'Actual focused ten-case source fixture log required')
    data = build_source(); OUTPUT.mkdir()
    def write(name, value):
        p = OUTPUT/name
        with p.open('x') as f: json.dump(value, f, separators=(',', ':'), allow_nan=False); f.write('\n')
        return pin(p)
    inputs = {**data['inputs'], 'producer': pin(ROOT/OWNER), 'fixtures': pin(ROOT/'scripts/unreal/test_exterior_context_yard_soft_coherence_source_r38.py'), 'cpuLog': pin(args.cpu_log)}
    mask = write('fixed-world-yard-mask.json', data['mask']); graphs = write('proposed-material-graphs.json', data['graphs'])
    fixture_proof = read(FIXTURE/'permission-field-proof.json')
    require(fixture_proof['sourceMaskSha256'] == digest(data['mask']) and fixture_proof['producer'] == pin(ROOT/OWNER)
            and fixture_proof['fixtures'] == pin(ROOT/'scripts/unreal/test_exterior_context_yard_soft_coherence_source_r38.py'), 'Actual tested permission field source differs')
    checked(fixture_proof['png']); field = OUTPUT/'fixed-world-permission-field.png'; field.write_bytes(Path(fixture_proof['png']['path']).read_bytes())
    field_proof = write('permission-field-proof.json', fixture_proof)
    hlsl = OUTPUT/'rejected-polygon-loop-mask.hlsl'; hlsl.write_text('// REJECTED native proposal: source367-edge pixel loop. Use generated field instead.\n'+hlsl_mask(data['mask'])+'\n')
    svg = OUTPUT/'fixed-world-yard-mask.svg'; svg.write_text(diagram(data['mask']))
    plan = {'schema': SCHEMA, 'schemaVersion': 1, 'owner': OWNER, 'status': 'source-only-material-coherence-proposal-native-base-pending',
            'activeDesign': {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'setbacksMm': {'street': 3000, 'east': 3000},
            'selectedNativeBase': None, 'selectedNativeReport': None, 'selectedRootImageDecision': None, 'projectClone': None, 'nativeEntryOwner': None,
            'inputs': inputs, 'mask': mask, 'materialGraphs': graphs, 'permissionField': pin(field), 'permissionFieldProof': field_proof,
            'rejectedPolygonLoopHlsl': pin(hlsl), 'diagram': pin(svg),
            'targets': {'backdropOriginalActor197': {'historicalWitness': next(v for k, v in data['targetWitness'].items() if k.endswith('_197')),
                        'proposedAsset': PREFIX+'/Materials/M_backdrop_soft_r38.M_backdrop_soft_r38'},
                        'substrateDonorActor668': {'historicalWitness': next(v for k, v in data['targetWitness'].items() if k.endswith('_668')),
                        'futureActorResolver': 'actual selected R37 report.newActorMapping[exact R32 donor actor668]; pending',
                        'proposedAsset': PREFIX+'/Materials/M_substrate_soft_r38.M_substrate_soft_r38'}},
            'commonPhotographicLayer': {'sourceUrl': 'https://polyhaven.com/a/sparse_grass', 'license': 'CC0-1.0',
                  'nativeTextures': data['photoNativeObjects'], 'worldTileCm': 200, 'yawDegrees': 0,
                  'threePhaseStochasticUvWeightsGradients': 'Exact saved R35 nodes/inputs; no new phases or sampler settings',
                  'artisticColorNormalCoefficient': .65, 'photometricCalibrationAccepted': False,
                  'commonEndpointIgnoresTinyMeshZAndVertexNormalDifferences': 'Explicit local artist-flat up and flat landcover endpoint; outside original vertex/slope inputs unchanged',
                  'outerSubstratePaletteDeliberatelyReplaced': 'R32 farm-soil/Grass004 response becomes same proposed backdrop response; bed/court materials unchanged'},
            'graphAudit': data['graphAudit'], 'counterfactual': {'onlyTwoComponentSlot0BindingsProposed': True, 'newMaterials': 2,
                  'newPhotoTextureObjects': 0, 'newGeneratedPermissionTextureObjectProposed': 1, 'newTextureObjectsActuallyBuilt': 0,
                  'newGeometry': 0, 'sourcePixelsEdited': False, 'geometryTransformsRootsAllOtherMaterialBindingsUnchanged': True,
                  'actualR37CounterfactualConstructed': False},
            'sourceBudget': {'opaqueNodes': 70, 'maskedNodes': 73, 'maskPolygons': len(data['mask']['polygons']),
                  'maskSegments': data['mask']['segments'], 'maximumSegmentsWithinOneBounds': data['mask']['maximumSegmentsInsideSinglePolygonBounds'],
                  'polygonLoopsAtPixelFrequencyProposed': False, 'sharedMaskTextureSamplesPerMaterial': 1,
                  'maskResolution': [MASK_RESOLUTION, MASK_RESOLUTION], 'uncompressedRgba8UpperBudgetBytes': MASK_RESOLUTION*MASK_RESOLUTION*4,
                  'shaderCompileMeasured': False, 'gpuCostMeasured': False},
            'cpuTests': {'count': 10, 'exitCode': 0, 'log': pin(args.cpu_log)},
            'limits': {'artistAuthoredYardEnvelopeNotSurveyOrLegalParcel': True, 'originalRadialAndOldCameraSubgraphOutsideExact': True,
                  'newMaskAndCommonEndpointCameraIndependent': True, 'falloffInheritsOriginalOutsideCameraResponse': True,
                  'cpuOutsideDirectBranchBinaryValuesTested': True, 'compiledOutsideGpuByteEquivalenceVerified': False,
                  'sourceRasterSupportInsideOriginalAllowedDomain': True, 'nativeMaskTexelsCompressionMipsFilteringUnverified': True,
                  'nativeGraphBuilt': False, 'nativeApplied': False, 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
                  'performanceAccepted': False, 'shippingVerified': False, 'packageVerified': False}}
    planpin = write('soft-ground-coherence-source-plan.json', plan)
    require(all(pin(row['path']) == row for row in inputs.values()), 'Consumed source bytes changed during proposal')
    print(json.dumps({'plan': planpin, 'maskAreaM2': data['mask']['quantizedMaskAreaM2'], 'segments': data['mask']['segments'], 'nativeBasePending': True}))


if __name__ == '__main__':
    main()
