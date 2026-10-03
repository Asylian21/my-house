"""Fresh anatomy study on unchanged upright lawn roots; CPU GLB renders only.

Compare the sealed upright grass with an earlier, narrower taper at unchanged
triangle cost and an actual longitudinal V fold at twice that cost. Coverage
loss is measured from exported GLB triangles, never concealed by a new floor,
density change, wider LOD or material calibration. No Unreal process is used.
"""
import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

import numpy as np
import shapely
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-lawn-tapered.py'
FROZEN = ROOT/'output/unreal/exterior-20260930-r9a/source-freeze/scripts/unreal'
PRIOR = ROOT/'output/unreal/exterior-lawn-upright-20260930-r4-study'
OUTPUT = ROOT/'output/unreal/exterior-lawn-tapered-20261001-r1-study'
PRIOR_SHA = '60a5faa40bbd9033099b69177e90c9916ceeeff466a8ea8b359186a568078df8'
FROZEN_SHA = {
    'exterior-lawn-upright.py': 'dd26f5745d21ebe3622533dccacc8a0ceaaa9818f87b2249285797eb77550b16',
    'exterior-lawn-coverage.py': '1c3f748485fc314d148a20e85ba132e6b9df3d397a2e172e261e8784e9b630a5',
    'exterior-lawn-natural.py': '68e865c2fc388b1209b91d5296583e00565e985166ab73f10fc1d922fa7fa2d0',
}
MATERIAL = 'lawn_natural_blade'


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def pin(path): return {'path': str(Path(path).resolve()), 'sha256': sha(path)}
def require(ok, message):
    if not ok: raise ValueError(message)
def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, separators=(',', ':'), allow_nan=False); stream.write('\n')


for _name, _sha in FROZEN_SHA.items():
    require(sha(FROZEN/_name) == _sha, 'Sealed R9a geometry dependency changed')
sys.path.insert(0, str(FROZEN))
_spec = importlib.util.spec_from_file_location('sealed_taper_prior', FROZEN/'exterior-lawn-upright.py')
prior = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(prior)
prior.ROOT = ROOT  # Source snapshot location is not the original workspace root.


def mesh(variant, growth, lod, compact, folded, old_record):
    points, uv, uv1, colors, triangles, ranges = [], [], [], [], [], []
    for index, blade in enumerate(prior.blade_parameters(variant, growth, compact)):
        old = old_record['bladeRanges'][index]
        require(np.allclose(blade['rootCm'], old['rootCm'], atol=1e-12), 'Prior leaf roots differ')
        width = .20 + (blade['widthCm']-.25)*(.10/.15)
        peak = .30 + .15*blade['bladeSeed']
        fold = .16 + .08*((blade['bladeSeed']*13.7) % 1.)
        start, first_tri = len(points), len(triangles)
        old_rgb = np.asarray(old_record['colors'])[old['vertexOffset']:old['vertexOffset']+old['vertexCount'], :3].mean(axis=0)
        stations = ((0., [0., .5, 1.] if folded else [0., 1.]),
                    (peak, [0., .5, 1.] if folded else [0., 1.]), (1., [.5]))
        color_weights = np.array([1.+.12*t for t, us in stations for _ in us])
        color_weights /= color_weights.mean()  # Redistribute; preserve each old leaf's mean RGB.
        centers, rings, section_normals = [], [], []
        for t, us in stations:
            middle = prior.center(blade, t)
            tangent = prior.center(blade, t+.0001)-prior.center(blade, t-.0001)
            tangent /= np.linalg.norm(tangent)
            angle = blade['angleRad']+blade['bendRad']*t
            side = np.array([-math.sin(angle), math.cos(angle), 0.])
            normal = np.cross(tangent, side); normal /= np.linalg.norm(normal)
            roll = blade['rollRad']+blade['twistRad']*t
            side = side*math.cos(roll)+normal*math.sin(roll)
            normal = np.cross(tangent, side); normal /= np.linalg.norm(normal)
            section_width = width*(.45 if t == 0 else 1. if t < 1 else 0.)
            ring = []
            for u in us:
                ridge = section_width*.5*math.tan(fold) if folded and u == .5 and t < 1 else 0.
                ring.append(len(points)); points.append((middle+side*section_width*(u-.5)+normal*ridge).tolist())
                uv.append([u, t]); uv1.append([blade['bladeSeed'], float(growth)])
                colors.append([*(old_rgb*color_weights[len(points)-start-1]).tolist(), 1.])
            centers.append(middle.tolist()); rings.append(ring); section_normals.append(normal.tolist())
        lift = max(0., -min(p[2] for p in points[start:]))
        for p in points[start:]: p[2] += lift
        for p in centers: p[2] += lift
        root, shoulder, tip = rings
        if folded:
            triangles.extend([[root[0], root[1], shoulder[0]], [root[1], shoulder[1], shoulder[0]],
                [root[1], root[2], shoulder[1]], [root[2], shoulder[2], shoulder[1]],
                [shoulder[0], shoulder[1], tip[0]], [shoulder[1], shoulder[2], tip[0]]])
        else:
            triangles.extend([[root[0], root[1], shoulder[0]], [root[1], shoulder[1], shoulder[0]],
                [shoulder[0], shoulder[1], tip[0]]])
        ranges.append({'bladeIndex': index, 'vertexOffset': start, 'vertexCount': len(points)-start,
            'triangleOffset': first_tri, 'triangleCount': len(triangles)-first_tri,
            'rootCm': blade['rootCm'], 'centerlineCm': centers, 'sectionNormals': section_normals,
            'widthCm': width, 'peakT': peak, 'rootWidthFraction': .45, 'heightCm': blade['heightCm'],
            'reachCm': blade['reachCm'], 'low': blade['low'], 'foldRad': fold if folded else 0.,
            'actualLongitudinalVSection': folded, 'tipWidthCm': 0., 'basalLiftCm': lift,
            'meanVertexColorPreserved': True, 'tipRootColorRatio': 1.12})
    record = {'nodeName': old_record['nodeName'], 'variant': variant, 'growthClass': growth,
        'edgeMaster': compact, 'level': lod, 'positionsCm': points, 'uv0': uv, 'uv1': uv1,
        'colors': colors, 'triangles': triangles, 'bladeRanges': ranges}
    record['expectedBoundsCm'] = {k: np.asarray(points).min(axis=0).tolist() if k == 'min' else np.asarray(points).max(axis=0).tolist() for k in ('min', 'max')}
    record['radialEnvelopeCm'] = float(np.linalg.norm(np.asarray(points)[:, :2], axis=1).max())
    return record


def write_glb(path, records, recipe):
    """Export newly recomputed geometry frames, with the unchanged actual recipe."""
    data = bytearray(); doc = {'asset': {'version': '2.0', 'generator': OWNER}, 'scene': 0,
        'scenes': [{'nodes': list(range(len(records)))}], 'nodes': [], 'meshes': [], 'accessors': [], 'bufferViews': [],
        'materials': [{'name': MATERIAL, 'doubleSided': True, 'pbrMetallicRoughness':
            {'baseColorFactor': [*recipe['linearColor'], 1.], 'metallicFactor': 0., 'roughnessFactor': recipe['roughness']}}]}
    def acc(values, kind, dtype='<f4', target=34962):
        a = np.asarray(values, dtype=dtype); data.extend(b'\0'*(-len(data) % 4)); offset = len(data); data.extend(a.tobytes())
        doc['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': a.nbytes, 'target': target})
        row = {'bufferView': len(doc['bufferViews'])-1, 'componentType': 5126 if dtype == '<f4' else 5125, 'count': len(a), 'type': kind}
        if kind == 'VEC3': row.update(min=a.min(axis=0).tolist(), max=a.max(axis=0).tolist())
        doc['accessors'].append(row); return len(doc['accessors'])-1
    for r in records:
        n, tangent = prior.cover.natural.basis(r)
        p = np.asarray(r['positionsCm'])[:, [0, 2, 1]]/100
        t = np.asarray(tangent); t = np.column_stack([t[:, :3][:, [0, 2, 1]], -t[:, 3]])
        attr = {'POSITION': acc(p, 'VEC3'), 'NORMAL': acc(np.asarray(n)[:, [0, 2, 1]], 'VEC3'),
            'TANGENT': acc(t, 'VEC4'), 'TEXCOORD_0': acc(r['uv0'], 'VEC2'), 'TEXCOORD_1': acc(r['uv1'], 'VEC2'),
            'COLOR_0': acc(r['colors'], 'VEC4')}
        indices = acc(np.asarray(r['triangles'])[:, [0, 2, 1]].reshape(-1), 'SCALAR', '<u4', 34963)
        doc['meshes'].append({'name': r['nodeName'], 'primitives': [{'attributes': attr, 'indices': indices, 'material': 0}]})
        doc['nodes'].append({'name': r['nodeName'], 'mesh': len(doc['meshes'])-1})
    data.extend(b'\0'*(-len(data) % 4)); doc['buffers'] = [{'byteLength': len(data)}]
    raw = json.dumps(doc, separators=(',', ':'), allow_nan=False).encode(); raw += b' '*(-len(raw) % 4)
    with path.open('xb') as stream:
        stream.write(struct.pack('<4sII', b'glTF', 2, 28+len(raw)+len(data)))
        stream.write(struct.pack('<II', len(raw), 0x4e4f534a)); stream.write(raw)
        stream.write(struct.pack('<II', len(data), 0x004e4942)); stream.write(data)


def decode_glb(path):
    raw = Path(path).read_bytes(); magic, version, length = struct.unpack_from('<4sII', raw)
    require((magic, version, length) == (b'glTF', 2, len(raw)), 'GLB header differs')
    size, kind = struct.unpack_from('<II', raw, 12); require(kind == 0x4e4f534a, 'GLB JSON missing')
    doc = json.loads(raw[20:20+size]); count, kind = struct.unpack_from('<II', raw, 20+size)
    require(kind == 0x004e4942 and 28+size+count == len(raw), 'GLB buffer missing')
    binary = raw[28+size:]
    def accessor(index):
        a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
        width = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        return np.frombuffer(binary, {5126: '<f4', 5125: '<u4'}[a['componentType']],
            count=a['count']*width, offset=v.get('byteOffset', 0)+a.get('byteOffset', 0)).reshape(-1, width)
    records = []
    for node in doc['nodes']:
        primitive = doc['meshes'][node['mesh']]['primitives'][0]; a = primitive['attributes']
        records.append({'nodeName': node['name'], 'positionsCm': (accessor(a['POSITION'])[:, [0, 2, 1]]*100).astype(float).tolist(),
            'triangles': accessor(primitive['indices']).reshape(-1, 3)[:, [0, 2, 1]].tolist(),
            'normals': accessor(a['NORMAL'])[:, [0, 2, 1]].astype(float).tolist(),
            'tangents': np.column_stack([accessor(a['TANGENT'])[:, :3][:, [0, 2, 1]], -accessor(a['TANGENT'])[:, 3]]).astype(float).tolist(),
            'uv0': accessor(a['TEXCOORD_0']).astype(float).tolist(), 'uv1': accessor(a['TEXCOORD_1']).astype(float).tolist(),
            'colors': accessor(a['COLOR_0']).astype(float).tolist()})
    return doc, records


def measurements(decoded, rows, base, old, domain):
    windows = []
    for w in old['audit']['physicalCoverage']['windows']:
        result, _ = prior.cover.raster_coverage(decoded, rows, w['centerCm'])
        for lod in result['lods']:
            lod['studyTargetsMet'] = lod['projectedCoverage'] >= .75 and lod['tenCmBinCoverageP10'] >= .55 and lod['bareTenCmBins'] == 0
        windows.append(result)
    boundary = []
    for w in old['audit']['boundaryCoverage']['windows']:
        result, _ = prior.boundary_raster(decoded, rows, w['originCm'], w['axisUnitXY'], w['inwardUnitXY'], w['widthCm'], w['lengthCm'])
        for lod in result['lods']:
            lod['studyTargetsMet'] = all(b['physicalCoverFraction'] > gate for b, gate in zip(lod['boundaryBands'], (.12, .40, .50)))
        boundary.append(result)
    lookup = {r['nodeName']: r for r in decoded}
    budgets = [sum(len(g['instances'])*len(lookup[g['meshId']+'_LOD'+str(i)]['triangles']) for g in base['groups']) for i in range(3)]
    envelopes = {m['id']: max(float(np.linalg.norm(np.asarray(lookup[l['nodeName']]['positionsCm'])[:, :2], axis=1).max()) for l in m['lods']) for m in old['library']['meshes']}
    xy = np.array([r['positionCm'][:2] for r in rows]); distance = shapely.distance(shapely.points(xy), domain.boundary)
    radius = np.array([envelopes[r['meshId']]*r['scale'][0] for r in rows])
    clearance = float(((distance-radius)*10-1).min())
    require(shapely.contains_xy(domain, *xy.T).all() and clearance > 0, 'Actual decoded leaf crowns escaped original domain')
    return {'method': 'Actual exported GLB triangles, 0.25mm interior/boundary raster, unchanged102011 roots and everyLOD; no floor geometry.',
        'physicalCoverage': windows, 'boundaryCoverage': boundary, 'allInstancesTriangleBudgetByLod': budgets,
        'withinOriginal20MTriangleBudget': budgets[0] <= 20000000, 'minimumAdditionalCrownClearanceMm': clearance,
        'interiorTargetsMet': all(l['studyTargetsMet'] for w in windows for l in w['lods']),
        'boundaryTargetsMet': all(l['studyTargetsMet'] for w in boundary for l in w['lods']),
        'nativeAppearanceAccepted': False, 'nativePerformanceAccepted': False}


def render(decoded, rows, center, side_view=False):
    """CPU barycentric z-buffer: actual GLB faces/normals/colour, same display light."""
    width, height = 680, 600; image = np.empty((height, width, 3)); image[:] = [.19, .19, .17]
    depth = np.full((height, width), -np.inf)
    camera = np.array([.22, .92, .32 if side_view else .72]); camera /= np.linalg.norm(camera)
    right = np.array([camera[1], -camera[0], 0.]); right /= np.linalg.norm(right); up = np.cross(right, camera)
    light = np.array([-.4, -.65, 1.]); light /= np.linalg.norm(light)
    lookup = {r['nodeName']: r for r in decoded}; center = np.asarray(center); scale = 18.
    for row in rows:
        delta = np.asarray(row['positionCm'][:2])-center
        if max(abs(delta)) > 12.5: continue
        r = lookup[row['meshId']+'_LOD0']; p = np.asarray(r['positionsCm'])*row['scale'][0]; n = np.asarray(r['normals'])
        angle = math.radians(row['yawDeg']); c, s = math.cos(angle), math.sin(angle); rotation = np.array([[c, s], [-s, c]])
        p[:, :2] = p[:, :2]@rotation+delta; n[:, :2] = n[:, :2]@rotation
        screen = np.column_stack([p@right*scale+width/2, height*.77-p@up*scale, p@camera])
        color = np.asarray(r['colors'])[:, :3]*np.array([.04, .075, .025])
        for face in r['triangles']:
            q = screen[face]; lo = np.maximum(np.floor(q[:, :2].min(axis=0)).astype(int), [0, 0]); hi = np.minimum(np.ceil(q[:, :2].max(axis=0)).astype(int), [width-1, height-1])
            if np.any(hi < lo): continue
            x, y = np.meshgrid(np.arange(lo[0], hi[0]+1)+.5, np.arange(lo[1], hi[1]+1)+.5)
            den = (q[1, 1]-q[2, 1])*(q[0, 0]-q[2, 0])+(q[2, 0]-q[1, 0])*(q[0, 1]-q[2, 1])
            if abs(den) < 1e-10: continue
            a = ((q[1, 1]-q[2, 1])*(x-q[2, 0])+(q[2, 0]-q[1, 0])*(y-q[2, 1]))/den
            b = ((q[2, 1]-q[0, 1])*(x-q[2, 0])+(q[0, 0]-q[2, 0])*(y-q[2, 1]))/den; w = np.stack([a, b, 1.-a-b], axis=-1)
            z = w@q[:, 2]; old_depth = depth[lo[1]:hi[1]+1, lo[0]:hi[0]+1]; inside = (w.min(axis=-1) >= -1e-8) & (z > old_depth)
            if not inside.any(): continue
            normal = w@n[face]; normal /= np.maximum(np.linalg.norm(normal, axis=-1, keepdims=True), 1e-12)
            brightness = .25+1.85*np.abs(normal@light)
            rgb = np.clip((w@color[face])*brightness[:, :, None], 0, 1)
            image[lo[1]:hi[1]+1, lo[0]:hi[0]+1][inside] = rgb[inside]; old_depth[inside] = z[inside]
    srgb = np.where(image <= .0031308, image*12.92, 1.055*image**(1/2.4)-.055)
    return Image.fromarray(np.clip(srgb*255, 0, 255).astype('uint8'))


def build(output=OUTPUT):
    output = Path(output).resolve(); require(output == OUTPUT and not output.exists(), 'Use fresh isolated immutable R1 study output')
    require(sha(PRIOR/'lawn-natural-plan.json') == PRIOR_SHA, 'Original upright basis changed')
    base = read(PRIOR/'lawn-natural-plan.json'); old_records = read(PRIOR/'lawn-natural-prototypes.json'); old_lookup = {r['nodeName']: r for r in old_records}
    library = read(PRIOR/'geometry-manifest.json'); material = read(PRIOR/'material-manifest.json'); recipe = material[MATERIAL]
    require(recipe['linearColor'] == [.04, .075, .025] and recipe['maps'] == {}, 'Original material basis changed')
    geometry = ROOT/'output/unreal/realism-20260926-r5/geometry'; rural = Path(base['managedLawnPlan']['path']); original = Path(base['derivedFrom']['path'])
    scene, _, _, _, source, domain, exclusions, _, keep = prior.cover.managed_source(geometry, rural, original)
    require(base['activeDesign'] == scene['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'C/B/B changed')
    require(base['housePlacement'] == scene['house']['placement'] and domain.area/10000 == base['audit']['exactAllowedDomainM2'], 'Original frame/domain changed')
    legacy, legacy_inputs = prior.legacy_source_proof(); require(legacy == base['audit']['legacyLawnProof'], 'Original40437 placements changed')
    inputs = {str(Path(__file__).resolve()): sha(__file__)}
    inputs.update({str(FROZEN/n): h for n, h in FROZEN_SHA.items()})
    for module in list(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name and Path(name).is_relative_to(FROZEN): inputs[str(Path(name).resolve())] = sha(name)
    for p in [geometry/'scene.json', geometry/'dom-mm.obj', rural, rural.parent/'scene.json', rural.parent/'dom-mm.obj', original,
              *legacy_inputs, *[PRIOR/n for n in ('lawn-natural-plan.json', 'geometry-manifest.json', 'material-manifest.json', 'lawn-natural.glb', 'lawn-natural-prototypes.json')]]:
        inputs[str(p)] = sha(p)
    rows = deepcopy(base['lawnPlacements']); groups = deepcopy(base['groups']); output.mkdir(parents=True)
    _, baseline = decode_glb(PRIOR/'lawn-natural.glb'); variants = {}; records_by_variant = {}
    for name, folded in [('tapered', False), ('folded', True)]:
        records = []
        for r in old_records:
            records.append(mesh(r['variant'], r['growthClass'], r['level'], r['edgeMaster'], folded, r))
        glb = output/(name+'.glb'); write_glb(glb, records, recipe); _, decoded = decode_glb(glb)
        measurements_old = {'audit': base['audit'], 'library': library}
        result = measurements(decoded, rows, base, measurements_old, domain)
        native = {r['nodeName']: r for r in decoded}
        new_library = deepcopy(library)
        for field in ('coverageReceipt', 'boundaryCoverageReceipt'):
            new_library['baseline'+field[0].upper()+field[1:]] = new_library.pop(field)
        for m in new_library['meshes']:
            for l in m['lods']:
                actual = native[l['nodeName']]; p = np.asarray(actual['positionsCm'])
                l.update(vertices=len(p), triangles=len(actual['triangles']), expectedBoundsCm={'min': p.min(axis=0).tolist(), 'max': p.max(axis=0).tolist()},
                    radialEnvelopeCm=float(np.linalg.norm(p[:, :2], axis=1).max()))
            require(max(l['radialEnvelopeCm'] for l in m['lods']) <= max(l['radialEnvelopeCm'] for l in next(old for old in library['meshes'] if old['id'] == m['id'])['lods'])+.000005, 'New anatomy exceeded prior conservative crown')
            m.update(glbPath=str(glb), glbSha256=sha(glb), heightCm=max(l['expectedBoundsCm']['max'][2] for l in m['lods']))
        new_library.update(owner=OWNER, generatorSha256=sha(__file__), inputFiles=inputs,
            status='MEASURED_TAPERED_ANATOMY_STUDY_NOT_NATIVE_ACCEPTED', revision=name+' on unchanged upright roots')
        manifest_path = output/(name+'-geometry-manifest.json'); write(manifest_path, new_library)
        variants[name] = {'glb': pin(glb), 'geometryManifest': pin(manifest_path), 'measurements': result,
            'verticesPerLeaf': 7 if folded else 5, 'trianglesPerLeaf': 6 if folded else 3,
            'actualVSection': folded, 'nativeAccepted': False}; records_by_variant[name] = records
    write(output/'lawn-tapered-prototypes.json', records_by_variant)
    (output/'material-manifest.json').write_bytes((PRIOR/'material-manifest.json').read_bytes())
    plan = deepcopy(base); plan.update(owner=OWNER, generatorSha256=sha(__file__), inputFiles=inputs,
        geometryManifest=variants['tapered']['geometryManifest'], priorPlan=pin(PRIOR/'lawn-natural-plan.json'),
        audit={'status': 'MEASURED_TAPERED_ANATOMY_STUDY_NOT_NATIVE_ACCEPTED', 'instances': len(rows), 'groups': len(groups),
            'exactAllowedDomainM2': domain.area/10000, 'originalPlacementRowsAndGroupsUnchanged': True,
            'sourceGroundCollisionAndSetbacksUnchanged': True, 'legacyLawnProof': legacy, 'variants': variants,
            'nativeVerified': False, 'nativeAppearanceAccepted': False, 'performanceAccepted': False, 'integrationAuthorized': False})
    for field in ('coverageReceipt', 'boundaryCoverageReceipt'):
        plan['baseline'+field[0].upper()+field[1:]] = plan.pop(field)
    require(plan['lawnPlacements'] == base['lawnPlacements'] and plan['groups'] == base['groups'], 'Original source placement drift')
    write(output/'lawn-tapered-plan.json', plan)
    atlas = Image.new('RGB', (2040, 1320), '#eeeae1'); draw = ImageDraw.Draw(atlas)
    center = base['audit']['physicalCoverage']['windows'][0]['centerCm']
    decoded_variants = [('R9a upright - 3 triangles/leaf', baseline), ('Earlier fine taper - 3 triangles/leaf', decode_glb(output/'tapered.glb')[1]),
        ('Actual V fold - 6 triangles/leaf', decode_glb(output/'folded.glb')[1])]
    for col, (label, decoded) in enumerate(decoded_variants):
        for row_index in range(2): atlas.paste(render(decoded, rows, center, bool(row_index)), (col*680, 80+row_index*600))
        draw.text((col*680+12, 20), label, fill='#202820')
    draw.text((12, 1300), 'CPU render of decoded GLB: same25cm roots/camera/light, neutral display backdrop, smooth imported normals. No Unreal/shadows/performance acceptance.', fill='#202820')
    atlas.save(output/'anatomy-side-by-side.png')
    manifest = {'schemaVersion': 1, 'owner': OWNER, 'generatorSha256': sha(__file__), 'inputFiles': inputs,
        'status': 'MEASURED_TAPERED_ANATOMY_STUDY_NOT_NATIVE_ACCEPTED', 'priorPlan': plan['priorPlan'],
        'plan': pin(output/'lawn-tapered-plan.json'), 'geometryProof': pin(output/'lawn-tapered-prototypes.json'),
        'materialManifest': pin(output/'material-manifest.json'), 'preview': pin(output/'anatomy-side-by-side.png'),
        'variants': variants, 'limits': ['No new density strategy; all102011 roots/40groups unchanged.',
            'Narrow taper can lose physical cover; actual exported geometry is measured at0.25mm.',
            'Actual V-fold costs twice the original leaf geometry at unchanged density; no performance acceptance.',
            'Same material recipe; mean vertex RGB per leaf preserved with only1.12 tip/root ratio.',
            'CPU display light/backdrop omit native shadows/SSS/global illumination and never replace original ground.']}
    write(output/'lawn-tapered-manifest.json', manifest)
    return {'output': str(output), 'plan': manifest['plan'], 'variants': variants, 'preview': manifest['preview']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', default=str(OUTPUT))
    print(json.dumps(build(**vars(parser.parse_args()))))
