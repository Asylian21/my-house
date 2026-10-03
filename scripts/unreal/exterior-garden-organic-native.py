"""Strict source guard for the frozen organic garden proposal, stdlib only.

The caller imports four new owned masters. This helper never imports Unreal,
writes assets, changes ground/collision, or grants native visual acceptance.
"""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-organic-bushy.py'
STUDY = ROOT/'output/unreal/exterior-garden-organic-20261001-r1c-study'
SOURCE_SHA = '1e3706a90a3ca8bd0b2a651820c501887162f1b018ad953409e63f3262e99237'
PINS = {
    'garden-plan.json': 'e599442a7ec887d16ee6e58c7466f4a34bf9a7880ef538bd2861c80ad39523e6',
    'geometry-manifest.json': '482a5ed8c334d74a3fe9caad1acd65569eb96dde55f9addcc213acd12eed0efb',
    'crown-validation.json': '0244ab9f3361ce5c57c8ebe23c55a66d928f3a04e953e3c29f9d6e717ac2d051',
    'garden-organic.glb': '60dae65b41f4d351a53930785479515c51d0b88b3ec01e081cd47e28a17a4cf5',
    'material-manifest.json': 'd2959c325e733ba4ad984779b683bc33bd459bb12b2f26ff71535605c3e133f5',
    'morphology-audit.json': '36d95442db924afb1b2f1138e09353b3d73717167ca1f769249020c6f02dda0b',
}
MAPPING = {'ornamental_white_a': 'garden_white_organic_a', 'ornamental_white_b': 'garden_white_organic_b',
    'garden_rosette_r3_a': 'garden_broadleaf_organic_a', 'garden_rosette_r3_b': 'garden_broadleaf_organic_b'}
MATERIALS = {'garden_blade_green', 'garden_plume_silk', 'regional_green_leaf'}


def require(ok, message):
    if not ok: raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1048576): h.update(block)
    return h.hexdigest()


def _finite(values, count):
    return isinstance(values, (list, tuple)) and len(values) == count and all(
        isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in values)


def _pin(path, digest):
    path = (ROOT/path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == digest,
            'Organic garden source pin differs: '+str(path))
    return path


def _read(pin): return json.loads(_pin(pin['path'], pin['sha256']).read_text())
def _same(a, b):
    try: return json.dumps(a, sort_keys=True, separators=(',', ':'), allow_nan=False) == json.dumps(b, sort_keys=True, separators=(',', ':'), allow_nan=False)
    except (TypeError, ValueError): return False
def _sub(a, b): return [a[i]-b[i] for i in range(len(a))]
def _dot(a, b): return sum(x*y for x, y in zip(a, b))
def _cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]


def _decode(path):
    """Decode the real multiprimitive FLOAT geometry and native handedness."""
    raw = Path(path).read_bytes()
    require(len(raw) >= 28 and struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'Organic GLB header differs')
    size, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4E4F534A and size+28 <= len(raw), 'Organic GLB JSON extent differs')
    doc = json.loads(raw[20:20+size]); offset = 20+size
    length, kind = struct.unpack_from('<II', raw, offset)
    require(kind == 0x004E4942 and offset+8+length == len(raw), 'Organic GLB binary extent differs')
    binary = memoryview(raw)[offset+8:]
    require(set(doc) == {'asset', 'scene', 'scenes', 'nodes', 'meshes', 'buffers', 'bufferViews', 'accessors', 'materials'}
            and doc['asset'] == {'version': '2.0', 'generator': OWNER}
            and doc['scene'] == 0 and doc['scenes'] == [{'nodes': list(range(12))}]
            and len(doc['nodes']) == len(doc['meshes']) == 12 and doc['buffers'] == [{'byteLength': length}],
            'Organic GLB unmeasured scene/skin/animation/extension refused')
    require({m['name'] for m in doc['materials']} == MATERIALS and len(doc['materials']) == 3,
            'Organic GLB material inventory differs')

    def accessor(index, kind, component):
        require(isinstance(index, int) and not isinstance(index, bool) and 0 <= index < len(doc['accessors']), 'Organic accessor index invalid')
        a = doc['accessors'][index]
        require(set(a) <= {'bufferView', 'componentType', 'count', 'type', 'min', 'max'} and a['type'] == kind
                and a['componentType'] == component and isinstance(a['count'], int) and not isinstance(a['count'], bool)
                and a['count'] > 0, 'Organic actual accessor type/modifier differs')
        v = doc['bufferViews'][a['bufferView']]
        count = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[kind]; width = count*4
        require(set(v) == {'buffer', 'byteOffset', 'byteLength', 'target'} and v['buffer'] == 0
                and v['target'] == (34963 if kind == 'SCALAR' else 34962)
                and 0 <= v['byteOffset'] and v['byteOffset']+v['byteLength'] <= len(binary)
                and v['byteLength'] == a['count']*width, 'Organic accessor actual buffer extent differs')
        fmt = '<'+('f' if component == 5126 else 'I')*count
        return [struct.unpack_from(fmt, binary, v['byteOffset']+i*width) for i in range(a['count'])]

    nodes = {}
    for i, node in enumerate(doc['nodes']):
        require(set(node) == {'mesh', 'name'} and node['mesh'] == i and node['name'] not in nodes
                and set(doc['meshes'][i]) == {'name', 'primitives'} and doc['meshes'][i]['name'] == node['name'],
                'Organic node transform/identity differs')
        positions = []; materials = set(); triangles = 0
        for primitive in doc['meshes'][i]['primitives']:
            require(set(primitive) == {'attributes', 'indices', 'material', 'mode'} and primitive['mode'] == 4
                    and set(primitive['attributes']) == {'POSITION', 'NORMAL', 'TANGENT', 'TEXCOORD_0', 'COLOR_0'},
                    'Organic morph/primitive modifier refused')
            material = doc['materials'][primitive['material']]['name']
            require(material not in materials, 'Organic primitive material duplicated'); materials.add(material)
            attrs = primitive['attributes']; source = accessor(attrs['POSITION'], 'VEC3', 5126)
            p = [(100*x, 100*z, 100*y) for x, y, z in source]
            n = [(x, z, y) for x, y, z in accessor(attrs['NORMAL'], 'VEC3', 5126)]
            t = [(x, z, y, -w) for x, y, z, w in accessor(attrs['TANGENT'], 'VEC4', 5126)]
            uv = accessor(attrs['TEXCOORD_0'], 'VEC2', 5126); colors = accessor(attrs['COLOR_0'], 'VEC4', 5126)
            require(len(p) == len(n) == len(t) == len(uv) == len(colors) and all(_finite(v, 3) for v in p+n)
                    and all(_finite(v, 4) for v in t+colors) and all(_finite(v, 2) for v in uv), 'Organic nonfinite/count-mismatched vertex attributes')
            require(all(abs(_dot(v, v)-1) <= .000002 for v in n)
                    and all(abs(_dot(v[:3], v[:3])-1) <= .000002 and v[3] in (-1., 1.) for v in t)
                    and all(abs(_dot(a, b[:3])) <= .000002 for a, b in zip(n, t)), 'Organic normal/tangent frame differs')
            require(all(0 <= value <= 1 for c in colors for value in c), 'Organic vertex color range differs')
            if material == 'regional_green_leaf':
                require(all(.28-1e-7 <= u <= .73+1e-7 and .30-1e-7 <= v <= .74+1e-7 for u, v in uv)
                        and all(c == (1., 1., 1., 1.) for c in colors), 'Organic photographic opaque UV/vertex interpretation differs')
            indices = [v[0] for v in accessor(primitive['indices'], 'SCALAR', 5125)]
            require(len(indices) % 3 == 0 and all(0 <= v < len(p) for v in indices), 'Organic actual triangle indices escape vertices')
            for start in range(0, len(indices), 3):
                a, c, b = indices[start:start+3]  # glTF Y-up -> native handedness.
                cross = _cross(_sub(p[b], p[a]), _sub(p[c], p[a]))
                mean = [(n[a][j]+n[b][j]+n[c][j])/3 for j in range(3)]
                require(math.sqrt(_dot(cross, cross)) > 1e-9 and _dot(cross, mean) > 0, 'Organic degenerate/opposed triangle winding')
                d1, d2 = _sub(uv[b], uv[a]), _sub(uv[c], uv[a])
                require(abs(d1[0]*d2[1]-d1[1]*d2[0]) > 1e-10, 'Organic degenerate triangle UV')
            positions.extend(p); triangles += len(indices)//3
        require(positions, 'Organic empty master')
        nodes[node['name']] = {'vertices': len(positions), 'triangles': triangles, 'materials': materials,
            'bounds': {'min': [min(p[j] for p in positions) for j in range(3)], 'max': [max(p[j] for p in positions) for j in range(3)]},
            'radius': max(math.hypot(p[0], p[1]) for p in positions)}
    return nodes


def _triangle_inside(p, tri):
    a, b, c = tri; v1, v2, q = _sub(b, a), _sub(c, a), _sub(p, a)
    den = v1[0]*v2[1]-v1[1]*v2[0]
    require(abs(den) > 1e-8, 'Organic source bed triangle degenerate')
    u = (q[0]*v2[1]-q[1]*v2[0])/den; v = (v1[0]*q[1]-v1[1]*q[0])/den
    return u >= -1e-10 and v >= -1e-10 and u+v <= 1+1e-10


def _boundary(triangles):
    counts = Counter(); result = []
    for tri in triangles:
        require(len(tri) == 3 and all(_finite(p, 3) for p in tri), 'Organic source bed triangle malformed')
        points = [tuple(p[:2]) for p in tri]
        for a, b in zip(points, points[1:]+points[:1]): counts[tuple(sorted((a, b)))] += 1
    require(counts and all(v in (1, 2) for v in counts.values()), 'Organic source bed is not a triangle union')
    result = [edge for edge, count in counts.items() if count == 1]
    require(result and all(v == 2 for v in Counter(p for edge in result for p in edge).values()), 'Organic source bed union boundary has gaps')
    return result


def _distance(p, a, b):
    d = _sub(b, a); size = _dot(d, d); require(size > 0, 'Organic source boundary edge degenerate')
    t = max(0., min(1., _dot(_sub(p, a), d)/size))
    return math.hypot(p[0]-a[0]-t*d[0], p[1]-a[1]-t*d[1])


def validated_garden(plan, mergedManifest, sceneSha, objSha):
    """Return source evidence only, suitable for the import report."""
    frozen = {name: _pin(STUDY/name, value) for name, value in PINS.items()}
    canonical = json.loads(frozen['garden-plan.json'].read_text())
    require(_same(plan, canonical) and plan['schemaVersion'] == 2 and plan['owner'] == OWNER,
            'Organic immutable plan/owner/schema differs')
    require(sha(ROOT/OWNER) == plan['generatorSha256'] == SOURCE_SHA, 'Organic generator source differs')
    for path, value in plan['inputFiles'].items(): _pin(path, value)
    old = _read(plan['sourceGarden']); report = _read(plan['sourceNativeImport'])
    require(report['savedReloaded'] is True and report['protectedContentUnchanged'] is True
            and report['sourceGeometryCollisionAndTransformsPreserved'] is True and report['originalMaterialAssetsPreserved'] is True,
            'Organic native R10 architecture/ground preservation source missing')
    require(report['gardenPlanting']['instances'] == 461 and report['gardenPlanting']['ornamentalReplacements'] == 12,
            'Organic native source garden census differs')
    require(plan['sourceSceneSha256'] == old['sourceSceneSha256'] == sceneSha
            and plan['sourceObjSha256'] == old['sourceObjSha256'] == objSha, 'Organic scene/OBJ frame differs')
    require(plan['activeDesign'] == old['activeDesign'] == report['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
            and plan['housePlacement'] == old['housePlacement'] and plan['housePlacement']['streetSetbackMm'] == 3000
            and plan['housePlacement']['eastSetbackMm'] == 3000, 'Organic C/B/B or setbacks differ')
    for name in ('sourceMulchTrianglesCm', 'sourceStepTrianglesCm', 'sourceCardPointsCm', 'hideSourceIds'):
        require(plan[name] == old[name], 'Organic protected garden source differs: '+name)
    for name in ('nativeVerified', 'nativeAppearanceAccepted', 'performanceAccepted', 'integrationAuthorized'):
        require(plan['organicStudy'][name] is False, 'Organic source proposal grants unsupported acceptance')
    require(plan['organicStudy']['artistInterpretation'] is True and plan['organicStudy']['surveyedBotany'] is False,
            'Organic artist/survey evidence differs')
    library = _read(plan['organicMasters']); crown = _read(plan['organicCrownProof'])
    require(plan['organicMasters'] == {'path': str(STUDY/'geometry-manifest.json'), 'sha256': PINS['geometry-manifest.json']}
            and plan['organicCrownProof'] == {'path': str(STUDY/'crown-validation.json'), 'sha256': PINS['crown-validation.json']}, 'Organic master/crown exact pins differ')
    require(library['schema'] == 1 and library['owner'] == OWNER and library['generatorSha256'] == SOURCE_SHA
            and library['units'] == 'metres' and library['axes'] == 'glTF Y-up; Unreal native = [100*x,100*z,100*y]'
            and library['inputFiles'] == plan['inputFiles'], 'Organic source library frame/dependencies differ')
    meshes = {m['id']: m for m in library['meshes']}; merged = {m['id']: m for m in mergedManifest['meshes']}
    original_library = _read(library['sourceLibrary'])
    require(len(meshes) == len(library['meshes']) == 4 and set(meshes) == set(MAPPING.values())
            and len(merged) == len(mergedManifest['meshes']) == 100
            and set(merged) == {m['id'] for m in original_library['meshes']} | set(meshes)
            and all(_same(merged.get(k), row) for k, row in meshes.items()), 'Organic merged actual master subset/count differs')
    recipes = json.loads(frozen['material-manifest.json'].read_text())
    source_recipes_path = str(ROOT/'output/unreal/exterior-assets-greenery-20260930-r5/material-manifest.json')
    source_recipes = json.loads(_pin(source_recipes_path, plan['inputFiles'][source_recipes_path]).read_text())
    require(set(recipes) == MATERIALS and all(recipes[k] == source_recipes[k] for k in MATERIALS), 'Organic original material recipes changed')
    nodes = _decode(frozen['garden-organic.glb'])
    require(set(nodes) == {key+'_LOD'+str(i) for key in meshes for i in range(3)}, 'Organic actual 12LOD inventory differs')
    envelopes = {}
    for key, row in meshes.items():
        require(row['placementPolicy'] == 'explicit-only' and row['glbPath'] == str(frozen['garden-organic.glb'])
                and row['glbSha256'] == PINS['garden-organic.glb'] and [l['level'] for l in row['lods']] == [0, 1, 2], 'Organic explicit placement/LOD policy differs')
        expected_mats = MATERIALS if 'white' in key else MATERIALS-{'garden_plume_silk'}
        require(set(row['materialKeys']) == expected_mats, 'Organic master material role differs')
        measured = []
        for lod in row['lods']:
            name = key+'_LOD'+str(lod['level']); actual = nodes[name]
            require(lod['nodeName'] == name and actual['vertices'] == lod['vertices'] and actual['triangles'] == lod['triangles']
                    and 0 < actual['triangles'] <= 20000 and actual['materials'] == expected_mats,
                    'Organic decoded actual LOD count/material differs')
            require(all(abs(actual['bounds'][side][i]-lod['expectedBoundsCm'][side][i]) < 1e-8 for side in ('min', 'max') for i in range(3))
                    and abs(actual['radius']-lod['radialEnvelopeCm']) < 1e-8 and actual['bounds']['min'][2] >= -1e-8,
                    'Organic decoded actual LOD bounds differ')
            measured.append((actual['radius'], actual['bounds']['max'][2]))
        envelopes[key] = (max(r for r, h in measured), max(h for r, h in measured))
    require(crown['status'] == 'verified-decoded-organic-garden-crowns-not-native-accepted' and crown['owner'] == OWNER
            and crown['sourceGarden'] == plan['sourceGarden'] and crown['sourceNativeImport'] == plan['sourceNativeImport']
            and crown['geometryManifest'] == plan['organicMasters'] and crown['originalSourceMulchTrianglesCm'] == old['sourceMulchTrianglesCm']
            and crown['sourceSceneSha256'] == sceneSha and crown['sourceObjSha256'] == objSha
            and crown['activeDesign'] == plan['activeDesign'] and crown['housePlacement'] == plan['housePlacement'], 'Organic crown evidence frame differs')
    proof = {r['id']: r for r in crown['measuredReplacements']}
    require(len(proof) == len(crown['measuredReplacements']) == crown['instances'] == 424, 'Organic crown census differs')
    boundaries = {key: _boundary(tris) for key, tris in old['sourceMulchTrianglesCm'].items()}
    changed = unchanged = white = low = 0; minimum = math.inf
    for field, expected_count in (('ornamentalPlacements', 12), ('gardenDetailPlacements', 461)):
        require(len(plan[field]) == len(old[field]) == expected_count
                and plan['original'+field[0].upper()+field[1:]] == old[field], 'Organic source garden rows differ')
        for row, before in zip(plan[field], old[field]):
            if before['meshId'] not in MAPPING:
                require(row == before, 'Organic unrelated garden row changed'); unchanged += 1; continue
            key = MAPPING[before['meshId']]
            require(row == {**before, 'meshId': key, 'sourceMeshId': before['meshId']}, 'Organic original root/yaw/uniformscale/metadata changed')
            require(_finite(row['positionCm'], 3) and isinstance(row['uniformScale'], (int, float)) and not isinstance(row['uniformScale'], bool)
                    and math.isfinite(row['uniformScale']) and row['uniformScale'] > 0, 'Organic placement scale/frame invalid')
            radius, height = [v*row['uniformScale'] for v in envelopes[key]]
            require(radius <= before['radiusCm']+1e-5 and height <= before['actualHeightCm']+1e-5, 'Organic actual crown/height expanded')
            point = row['positionCm'][:2]; tris = old['sourceMulchTrianglesCm'][row['sourceBedId']]
            require(any(_triangle_inside(point, [p[:2] for p in tri]) for tri in tris), 'Organic root escaped original mulch bed')
            clearance = min(_distance(point, a, b) for a, b in boundaries[row['sourceBedId']])-radius
            require(clearance > 0, 'Organic complete circular allLOD crown escaped original bed')
            measured = {'id': row['id'], 'sourceMeshId': before['meshId'], 'meshId': key, 'actualRadiusCm': radius,
                'actualHeightCm': height, 'originalConservativeRadiusCm': before['radiusCm'], 'originalConservativeHeightCm': before['actualHeightCm'],
                'fullCrownToOriginalBedClearanceCm': clearance}
            require(row['id'] in proof and set(proof[row['id']]) == set(measured)
                    and all(abs(proof[row['id']][k]-v) < 1e-7 if isinstance(v, (int, float)) else proof[row['id']][k] == v for k, v in measured.items()),
                    'Organic independently measured crown receipt differs')
            changed += 1; white += int('white' in key); low += int('broadleaf' in key); minimum = min(minimum, clearance)
    require((changed, unchanged, white, low) == (424, 49, 4, 420) and abs(minimum-crown['minimumFullCrownToBedEdgeCm']) < 1e-7,
            'Organic final source census/minimum clearance differs')
    require(crown['completeActualAllLodCircularCrownsInsideOriginalBeds'] is True and crown['rootsYawsUniformScalesUnchanged'] is True
            and crown['sourceGroundArchitectureCollisionUnchanged'] is True and all(crown[k] is False for k in ('nativeAppearanceAccepted', 'performanceAccepted', 'integrationAuthorized')),
            'Organic crown preservation/acceptance claims differ')
    return {'status': 'verified-source-organic-garden', 'owner': OWNER, 'plan': {'path': str(STUDY/'garden-plan.json'), 'sha256': PINS['garden-plan.json']},
        'geometryManifest': plan['organicMasters'], 'crownProof': plan['organicCrownProof'], 'sourceGarden': plan['sourceGarden'],
        'sourceNativeImport': plan['sourceNativeImport'], 'masterIds': sorted(meshes), 'masters': 4, 'lods': 12,
        'whiteHeroReplacements': white, 'lowerClumpReplacements': low, 'instances': changed, 'allOriginalTransforms': 473,
        'unchangedOtherGardenRows': unchanged, 'minimumFullCrownToOriginalBedClearanceCm': minimum,
        'actualDecodedLodCountsBoundsMaterialsFramesVerified': True, 'allActualLodCircularCrownsInsideOriginalBeds': True,
        'sourceGroundArchitectureCollisionUnchanged': True, 'originalMaterialRecipesAndPixelsUnchanged': True,
        'artistInterpretation': True, 'surveyedBotany': False, 'nativeAppearanceAccepted': False, 'performanceAccepted': False}
