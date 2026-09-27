"""Twenty bounded cushion visuals, with the accepted PH meshes as the comparison.

CPU build: python3 <this file> --geometry <inherited geometry> --output <new study>
Preview only: Blender --background --factory-startup --python <this file> --
  --preview <study>. Neither mode opens or modifies Unreal packages.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/realism-upholstery-geometry.py'
GLB_NAME = 'realism-upholstery.glb'
SOFA_SEATS = (1443, 1445, 1447, 1449)
SOFA_BACKS = (1444, 1446, 1448)
CHAIR_SEATS = tuple(range(1466, 1512, 9))
CHAIR_BACKS = tuple(range(1473, 1519, 9))
NUMBERS = sorted((*SOFA_SEATS, *SOFA_BACKS, 1452, *CHAIR_SEATS, *CHAIR_BACKS))
IDS = tuple(f'DOM_{n:05}' for n in NUMBERS)
HELPER = Path(__file__).with_name('realism-fixtures-geometry.py')
SPEC = importlib.util.spec_from_file_location('upholstery_primitives', HELPER)
G = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(G)
require, sha, bounds = G.require, G.sha, G.bounds


def dot(a, b): return sum(x*y for x, y in zip(a, b))
def add(a, b): return tuple(x+y for x, y in zip(a, b))
def mul(a, s): return tuple(x*s for x in a)
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def expected(number):
    if number in CHAIR_SEATS or number in CHAIR_BACKS:
        index = (number-(1466 if number in CHAIR_SEATS else 1473))//9
        chair = ('W' if index < 3 else 'E')+str(index % 3+1)
        suffix = 'klasický čalúnený sedák' if number in CHAIR_SEATS else 'čalúnená výplň operadla'
        return f'LIVING-103-DINING · DINING-CHAIR-{chair} · {suffix}', 'Living warm fabric | real-interior-upholstery'
    if number in SOFA_SEATS:
        suffix = f'sedák {SOFA_SEATS.index(number)+1} · piesková tkanina' if number != 1449 else 'sedák ležadla · piesková tkanina'
    elif number in SOFA_BACKS: suffix = f'chrbtový vankúš {SOFA_BACKS.index(number)+1}'
    else: suffix = 'ľanový vankúš · tlmená oliva'
    return 'LIVING-103-SOFA-L · TAILORED · '+suffix, ('Living warm accent | real-interior-accent-fabric'
            if number == 1452 else 'Living warm sofa | real-interior-upholstery')


def source_records(scene):
    require(scene['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'Only C/B/B supported')
    placement = scene['house']['placement']
    require(placement['streetSetbackMm'] == placement['eastSetbackMm'] == 3000, 'Setbacks changed')
    selected = [row for row in scene['objects'] if row['id'] in IDS]
    require(len(selected) == len(IDS) and {row['id'] for row in selected} == set(IDS), 'Exact twenty cushion sources required')
    records = {row['id']: row for row in selected}
    for number, id_ in zip(NUMBERS, IDS):
        row = records[id_]; name, material = expected(number)
        require(row['name'] == name and row['materialNames'] == [material] and len(row['materialSlots']) == 1,
                'Cushion semantic identity changed: '+id_)
        require(row['enabled'] and row['instances'] == 1 and not row.get('metadata', {}).get('doorMotion'), 'Unexpected moving/disabled cushion')
        require(row.get('metadata', {}).get('babylonCheckCollisions') is False, 'Cushion collision contract changed')
    return records


def read_obj(path, ids):
    """Read just named OBJ objects, retaining the source world points and triangles."""
    result, current, index = {}, None, 0
    with Path(path).open() as handle:
        for line in handle:
            if line.startswith('o '):
                identity = line[2:].strip()
                current = {'vertices': [], 'faces': [], 'indices': {}} if identity in ids else None
                if current is not None: result[identity] = current
            elif line.startswith('v '):
                index += 1
                if current is not None:
                    current['indices'][index] = len(current['vertices'])
                    current['vertices'].append(tuple(map(float, line.split()[1:4])))
            elif line.startswith('f ') and current is not None:
                face = [current['indices'][int(token.split('/')[0])] for token in line.split()[1:]]
                for j in range(1, len(face)-1): current['faces'].append((face[0], face[j], face[j+1]))
    require(set(result) == set(ids), 'OBJ source cohort missing')
    for row in result.values(): del row['indices']
    return result


def frame_for(number, points):
    center = tuple(sum(p[i] for p in points)/len(points) for i in range(3))
    if number in SOFA_BACKS or number == 1452:
        yy = sum((p[1]-center[1])**2 for p in points)
        zz = sum((p[2]-center[2])**2 for p in points)
        yz = sum((p[1]-center[1])*(p[2]-center[2]) for p in points)
        eigen = (yy+zz+math.hypot(yy-zz, 2*yz))/2
        vertical = G.unit((0, yz, eigen-yy))
        if vertical[2] < 0: vertical = mul(vertical, -1)
        width = (-1., 0., 0.); normal = G.cross(width, vertical)
        axes = (width, vertical, normal)
        tilt = math.atan2(-vertical[1], vertical[2])
        require(abs(abs(tilt)-(.15 if number == 1452 else .085)) < 1e-5, 'Source cushion tilt changed')
    elif number in CHAIR_BACKS:
        sign = 1 if number < 1493 else -1
        axes = ((0., sign, 0.), (0., 0., 1.), (sign, 0., 0.)); tilt = 0.
    else: axes = ((1., 0., 0.), (0., 1., 0.), (0., 0., 1.)); tilt = 0.
    local = [tuple(dot(G.sub(p, center), axis) for axis in axes) for p in points]
    b = bounds(local); middle = [(b['min'][i]+b['max'][i])/2 for i in range(3)]
    center = tuple(center[j]+sum(middle[i]*axes[i][j] for i in range(3)) for j in range(3))
    half = [(b['max'][i]-b['min'][i])/2 for i in range(3)]
    require(min(half) >= 20 and max(half) < 900, 'Unexpected cushion dimensions')
    return {'centerMm': center, 'axes': axes, 'halfMm': half, 'sourceTiltRadians': tilt}


def recipe(number):
    if number in CHAIR_BACKS: return {'radiusMm': 18., 'crownMm': 3., 'seamRadiusMm': .50, 'kind': 'chair-back'}
    if number in CHAIR_SEATS: return {'radiusMm': 16., 'crownMm': 7., 'seamRadiusMm': .60, 'kind': 'chair-seat'}
    if number in SOFA_BACKS: return {'radiusMm': 45., 'crownMm': 16., 'seamRadiusMm': .65, 'kind': 'sofa-back'}
    if number == 1452: return {'radiusMm': 55., 'crownMm': 20., 'seamRadiusMm': .65, 'kind': 'accent-cushion'}
    return {'radiusMm': 34., 'crownMm': 15., 'seamRadiusMm': .65, 'kind': 'sofa-seat'}


def deform(p, half, spec):
    """Broad low crown: an eased shoulder, not an inflated ellipsoid.

    Only inward displacement. The central thickness and the lower support
    plane stay fixed; the edge shoulder rolls down toward a sewn border.
    """
    loft = math.prod(max(0., math.cos(math.pi*p[i]/(2*half[i])))**.8 for i in (0, 1))
    weight = (abs(p[2])/half[2])**3
    crown = spec['crownMm']*(1-loft)*weight
    # Flat seat underside remains a stable support surface.
    if spec['kind'].endswith('seat') and p[2] < 0: crown *= .12
    return (p[0], p[1], p[2]-math.copysign(crown, p[2]))


def transformed(p, frame):
    return tuple(frame['centerMm'][j]+sum(p[i]*frame['axes'][i][j] for i in range(3)) for j in range(3))


class Mesh(G.Mesh):
    def __init__(self, source_id):
        super().__init__('RU_'+source_id, [source_id], [source_id])
        self.local = []; self.uvs = []; self.parts = []


def surface(mesh, frame, spec):
    half = frame['halfMm']; radius = min(spec['radiusMm'], min(half)*.8)
    core = [h-radius for h in half]
    values = []
    for h, c in zip(half, core):
        values.append([-h, -c-radius*.75, -c-radius*.35, -c-radius*.1]
                      + [c*(-1+j/4) for j in range(9)]
                      + [c+radius*.1, c+radius*.35, c+radius*.75, h])
    welded = {}
    def vertex(p):
        q = tuple(max(-core[i], min(core[i], p[i])) for i in range(3))
        delta = G.unit(G.sub(p, q)); rolled = add(q, mul(delta, radius))
        final = deform(rolled, half, spec); key = tuple(round(x, 7) for x in final)
        if key not in welded:
            welded[key] = mesh.vertex(transformed(final, frame)); mesh.local.append(final)
            mesh.uvs.append((final[0]/1000, final[1]/1000))
        return welded[key]
    for axis in range(3):
        u, v = (axis+1) % 3, (axis+2) % 3
        for sign in (-1, 1):
            grid = []
            for y in values[v]:
                row = []
                for x in values[u]:
                    p = [0., 0., 0.]; p[axis] = sign*half[axis]; p[u] = x; p[v] = y
                    row.append(vertex(p))
                grid.append(row)
            for j in range(len(grid)-1):
                for i in range(len(grid[0])-1):
                    a, b, c, d = grid[j][i], grid[j][i+1], grid[j+1][i], grid[j+1][i+1]
                    faces = ((a, b, c), (b, d, c))
                    for face in faces: mesh.triangle(*(face if sign > 0 else tuple(reversed(face))))
    mesh.parts.append({'kind': 'closed-cushion', 'firstFace': 0, 'faceCount': len(mesh.faces)})
    return radius


def seam(mesh, frame, spec, radius):
    half = frame['halfMm']; section = radius*math.sin(math.pi/4)
    z = half[2]-radius+radius*math.cos(math.pi/4)
    raw = G.rounded_rectangle(half[0]-radius+section, half[1]-radius+section,
                              section, z, (0, 0), segments=11)
    path = [deform(p, half, spec) for p in raw]
    loops = []; start = len(mesh.faces); tube = spec['seamRadiusMm']
    for index, p in enumerate(path):
        tangent = G.unit(G.sub(path[(index+1) % len(path)], path[index-1]))
        # Surface normal evaluated from the undeformed rounded-box corner.
        q = tuple(max(-half[i]+radius, min(half[i]-radius, raw[index][i])) for i in range(3))
        normal = G.unit(G.sub(raw[index], q)); across = G.unit(G.cross(tangent, normal))
        loop = []
        for j in range(8):
            angle = j*math.tau/8
            # A fine same-fabric welt is partially embedded, with 0.7–0.85 mm
            # exposed crown. This is visible construction, not a dark stripe.
            point = add(p, add(mul(normal, tube*math.cos(angle)+.2), mul(across, tube*math.sin(angle))))
            loop.append(mesh.vertex(transformed(point, frame))); mesh.local.append(point)
            mesh.uvs.append((index/len(path), j/8))
        loops.append(loop)
    for a, b in zip(loops, loops[1:]+loops[:1]): mesh.bridge(a, b)
    mesh.parts.append({'kind': 'restrained-shoulder-welt', 'firstFace': start, 'faceCount': len(mesh.faces)-start})


def orient_parts(mesh):
    for part in mesh.parts:
        indices = range(part['firstFace'], part['firstFace']+part['faceCount'])
        anchor = mesh.vertices[mesh.faces[part['firstFace']][0]]
        volume = sum(dot(G.sub(mesh.vertices[a], anchor), G.cross(G.sub(mesh.vertices[b], anchor), G.sub(mesh.vertices[c], anchor)))
                     for a, b, c in (mesh.faces[i] for i in indices))/6
        require(abs(volume) > 1e-4, 'Zero volume cushion part')
        if volume < 0:
            for i in indices: mesh.faces[i] = tuple(reversed(mesh.faces[i]))
        part['signedVolumeMm3'] = abs(volume)


def build_geometry(scene, obj_sources):
    records = source_records(scene); meshes, rows = [], []
    require(set(obj_sources) == set(IDS), 'Unexpected OBJ cohort')
    for number, id_ in zip(NUMBERS, IDS):
        points = obj_sources[id_]['vertices']; source = records[id_]
        actual = bounds(points)
        require(max(abs(actual[key][i]-source['boundsMm'][key][i]) for key in ('min', 'max') for i in range(3)) < .001,
                'OBJ/manifest bounds differ: '+id_)
        frame = frame_for(number, points); spec = recipe(number); mesh = Mesh(id_)
        radius = surface(mesh, frame, spec); seam(mesh, frame, spec, radius); orient_parts(mesh)
        # Source rounded corners are discretely sampled. A denser analytic
        # shoulder can exceed that sampled AABB by hundredths of a mm. Apply
        # at most a submillimetre uniform contraction about the unchanged
        # source centre; never clamp individual vertices or change the tilt.
        visual = bounds(mesh.vertices); center = frame['centerMm']; scale = 1.
        for key in ('min', 'max'):
            for axis in range(3):
                distance = abs(visual[key][axis]-center[axis])
                if distance: scale = min(scale, abs(source['boundsMm'][key][axis]-center[axis])/distance)
        correction = max(G.norm(G.sub(p, center)) for p in mesh.vertices)*(1-scale)
        require(correction < .5, f'Cushion envelope would require more than a sub-mm fit: {id_} {correction}')
        mesh.vertices = [add(center, mul(G.sub(p, center), scale)) for p in mesh.vertices]
        mesh.local = [mul(p, scale) for p in mesh.local]
        for part in mesh.parts: part['signedVolumeMm3'] *= scale**3
        row = G.check_mesh(mesh, records)
        directed = Counter((face[i], face[(i+1) % 3]) for face in mesh.faces for i in range(3))
        require(all(count == directed[(b, a)] for (a, b), count in directed.items()), 'Cushion winding is inconsistent')
        row.update(hiddenSourceIds=[], hiddenVisualSourceIds=['PH_'+id_], mode='visual-replacement',
                   materialBindings=[{'sourceId': id_, 'sourceSlot': 0, 'visualSourceId': 'PH_'+id_}],
                   sourceName=source['name'], frame=frame, recipe=spec, parts=mesh.parts,
                   sampledEnvelopeFitScale=scale, sampledEnvelopeFitMaxMm=correction,
                   sourceVertexSha256=digest(points), sourceTriangles=len(obj_sources[id_]['faces']))
        meshes.append(mesh); rows.append(row)
    require(sum(len(m.faces) for m in meshes) <= 100000, 'Upholstery triangle budget exceeded')
    return meshes, rows


def write_glb(path, meshes, palettes=None):
    """CPU glTF writer, preserving smooth normals and source XYZ millimetres."""
    binary = bytearray(); views, accessors, nodes, gl_meshes, materials = [], [], [], [], []
    def accessor(values, kind, integer=False):
        flat = [x for row in values for x in (row if isinstance(row, (list, tuple)) else [row])]
        while len(binary) % 4: binary.append(0)
        offset = len(binary); binary.extend(struct.pack('<'+('I' if integer else 'f')*len(flat), *flat))
        views.append({'buffer': 0, 'byteOffset': offset, 'byteLength': len(binary)-offset, 'target': 34963 if integer else 34962})
        item = {'bufferView': len(views)-1, 'componentType': 5125 if integer else 5126, 'count': len(values), 'type': kind}
        if kind == 'VEC3': item.update(bounds(values))
        accessors.append(item); return len(accessors)-1
    for mesh in meshes:
        normals = [[0., 0., 0.] for _ in mesh.vertices]
        for a, b, c in mesh.faces:
            normal = G.cross(G.sub(mesh.vertices[b], mesh.vertices[a]), G.sub(mesh.vertices[c], mesh.vertices[a]))
            for index in (a, b, c): normals[index] = add(normals[index], normal)
        normals = [G.unit(n) for n in normals]
        convert = lambda p: [p[0], p[2], -p[1]]
        attributes = {'POSITION': accessor([convert(mul(p, .001)) for p in mesh.vertices], 'VEC3'),
                      'NORMAL': accessor([convert(n) for n in normals], 'VEC3'),
                      'TEXCOORD_0': accessor(mesh.uvs, 'VEC2')}
        material = len(materials); color = (palettes or {}).get(mesh.source_ids[0], [.42, .36, .28])
        materials.append({'name': 'RU_'+mesh.source_ids[0], 'pbrMetallicRoughness': {'baseColorFactor': [*color, 1], 'metallicFactor': 0, 'roughnessFactor': .86}})
        gl_meshes.append({'name': mesh.id, 'primitives': [{'attributes': attributes, 'indices': accessor([i for f in mesh.faces for i in f], 'SCALAR', True), 'material': material}]})
        nodes.append({'name': mesh.id, 'mesh': len(gl_meshes)-1, 'extras': {'sourceId': mesh.source_ids[0], 'visualOnly': True}})
    doc = {'asset': {'version': '2.0', 'generator': OWNER}, 'scene': 0, 'scenes': [{'nodes': list(range(len(nodes)))}],
           'nodes': nodes, 'meshes': gl_meshes, 'materials': materials, 'accessors': accessors, 'bufferViews': views, 'buffers': [{'byteLength': len(binary)}]}
    header = json.dumps(doc, separators=(',', ':')).encode(); header += b' '*((-len(header)) % 4); binary += b'\0'*((-len(binary)) % 4)
    Path(path).write_bytes(struct.pack('<III', 0x46546c67, 2, 28+len(header)+len(binary))+struct.pack('<II', len(header), 0x4e4f534a)+header+struct.pack('<II', len(binary), 0x004e4942)+binary)


def inspect_glb(path, rows):
    raw = Path(path).read_bytes(); magic, version, size = struct.unpack_from('<III', raw)
    require((magic, version, size) == (0x46546c67, 2, len(raw)), 'Malformed GLB header')
    length, kind = struct.unpack_from('<II', raw, 12); require(kind == 0x4e4f534a, 'Missing glTF document')
    doc = json.loads(raw[20:20+length]); offset = 20+length
    binary_size, kind = struct.unpack_from('<II', raw, offset); require(kind == 0x004e4942, 'Missing GLB buffer')
    binary = raw[offset+8:offset+8+binary_size]
    def read(index):
        a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
        width = {'VEC3': 3, 'VEC2': 2, 'SCALAR': 1}[a['type']]
        fmt = 'I' if a['componentType'] == 5125 else 'f'
        values = struct.unpack_from('<'+fmt*(a['count']*width), binary, v.get('byteOffset', 0)+a.get('byteOffset', 0))
        return [values[i:i+width] for i in range(0, len(values), width)]
    require({node['name'] for node in doc['nodes']} == {row['id'] for row in rows}, 'GLB cohort differs')
    by_name = {row['id']: row for row in rows}; error = 0.
    for node in doc['nodes']:
        row = by_name[node['name']]; primitives = doc['meshes'][node['mesh']]['primitives']
        require(len(primitives) == 1, 'Each cushion must have exactly one inherited material slot')
        p = primitives[0]; points = read(p['attributes']['POSITION']); normals = read(p['attributes']['NORMAL'])
        coords = [(x*1000, -z*1000, y*1000) for x, y, z in points]
        b = bounds(coords); current = max(abs(b[key][i]-row['visualBoundsMm'][key][i]) for key in ('min', 'max') for i in range(3))
        require(current < .01, 'GLB millimetre roundtrip differs'); error = max(error, current)
        require(all(abs(G.norm(n)-1) < 1e-5 for n in normals), 'Non-unit GLB shading normal')
        require(len(read(p['indices'])) == row['triangles']*3, 'GLB triangle count differs')
        require(doc['materials'][p['material']]['name'] == 'RU_'+row['sourceIds'][0], 'GLB material order differs')
    return {'roundtripErrorMm': error, 'glbObjectCount': len(doc['nodes']), 'glbNormalUnitVerified': True}


def build(geometry, output):
    geometry, output = Path(geometry).resolve(), Path(output).resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Use a new output/unreal directory')
    scene = json.loads((geometry/'scene.json').read_text()); photo_path = geometry.parent/'photoreal-import-report.json'
    photo = json.loads(photo_path.read_text())
    require(scene['objSha256'] == sha(geometry/'dom-mm.obj'), 'Source OBJ hash differs')
    source = read_obj(geometry/'dom-mm.obj', IDS); meshes, rows = build_geometry(scene, source)
    for row in rows:
        ph = photo['geometry']['objects']['PH_'+row['sourceIds'][0]]
        require(ph['sourceId'] == row['sourceIds'][0] and len(ph['materials']) == 1, 'Inherited visual source differs')
        row['inheritedVisualSource'] = ph
    palettes = {}
    for id_ in IDS:
        ph = photo['geometry']['objects']['PH_'+id_]
        match = [r for r in photo['interior']['materials'].values() if r.get('asset') == ph['materials'][0]]
        if match: palettes[id_] = match[0]['recipe']['solidColorLinear']
    output.mkdir(parents=True); write_glb(output/GLB_NAME, meshes, palettes)
    roundtrip = inspect_glb(output/GLB_NAME, rows)
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'offline-geometry-validated', 'generatedAt': datetime.now(timezone.utc).isoformat(),
              'activeDesign': scene['activeDesign'], 'sourceGeometry': str(geometry), 'sourceSceneSha256': sha(geometry/'scene.json'),
              'sourceManifestSha256': sha(geometry/'scene.json'), 'sourceObjSha256': scene['objSha256'], 'photorealReportSha256': sha(photo_path),
              'generatorSha256': sha(__file__), 'generatorDependencies': {str(HELPER.relative_to(ROOT)): sha(HELPER)},
              'glb': GLB_NAME, 'glbSha256': sha(output/GLB_NAME), 'sourceIds': list(IDS), 'hiddenSourceIds': [],
              'hiddenVisualSourceIds': ['PH_'+id_ for id_ in IDS], 'objects': rows, 'triangles': sum(len(m.faces) for m in meshes),
              **roundtrip,
              'sourcePolicy': 'Preserve original DOM actors, meshes, poses, materials and collision unchanged. Hide only exact inherited PH visual components, including shadow/GI/ray tracing contribution. New RU visual meshes use current PH slot0 material, NoCollision and no navigation.',
              'coordinateSystem': 'Source XYZ mm/Zup -> glTF (X,Z,-Y) metres; expected UE X=x/10,Y=-y/10,Z=z/10.',
              'nativeImportVerified': False, 'visualQualityVerified': False,
              'limitations': ['Cosmetic authored upholstery, not manufacturer geometry or a textile simulation.', 'Acceptance requires comparison with existing PH meshes, then native matched-view review.']}
    (output/'geometry-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'objects': len(rows), 'triangles': report['triangles'], 'output': str(output)})); return report


def preview(output):
    """Same camera/light/material before and after; accepted PH baseline, not boxes."""
    import bpy
    import bmesh
    from mathutils import Vector
    output = Path(output).resolve(); report = json.loads((output/'geometry-report.json').read_text())
    require(report['generatorSha256'] == sha(__file__) and report['glbSha256'] == sha(output/GLB_NAME), 'Study is not pinned to this generator')
    geometry = Path(report['sourceGeometry']); photo_path = geometry.parent/'photoreal-import-report.json'
    require(sha(photo_path) == report['photorealReportSha256'], 'Inherited native geometry receipt changed')
    photo = json.loads(photo_path.read_text()); scene_doc = json.loads((geometry/'scene.json').read_text())
    baseline_path = next(ROOT/p for p, value in photo['inputFiles'].items() if p.endswith('/photoreal-details.glb') and sha(ROOT/p) == value)
    scene_by_id = {r['id']: r for r in scene_doc['objects']}
    context_ids = {f'DOM_{n:05}' for n in (*range(1438, 1453), *range(1466, 1475))}
    original = read_obj(geometry/'dom-mm.obj', context_ids)
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(baseline_path))
    ph = {}
    for obj in list(bpy.context.scene.objects):
        if obj.type == 'MESH' and obj.name.startswith('PH_') and obj.name[3:] in context_ids:
            ph[obj.name[3:]] = obj
        else: bpy.data.objects.remove(obj, do_unlink=True)
    require(set(IDS).intersection(context_ids) <= set(ph), 'Accepted PH comparison meshes are missing')
    shared_materials = {}
    def material(id_):
        row = scene_by_id[id_]; slot = row['materialSlots'][0]
        if slot in shared_materials: return shared_materials[slot]
        name = row['materialNames'][0]; entry = photo['interior']['materials'].get(slot)
        palette = entry['recipe']['solidColorLinear'] if entry and entry['recipe']['kind'] == 'woven-linen' else [.32, .235, .157]
        mat = bpy.data.materials.new('Comparison_'+slot); mat.use_nodes = True
        shader = mat.node_tree.nodes.get('Principled BSDF'); shader.inputs['Base Color'].default_value = (*palette, 1)
        shader.inputs['Roughness'].default_value = .86 if entry else .55
        if entry:
            shader.inputs['Sheen Weight'].default_value = .20
            shader.inputs['Sheen Roughness'].default_value = .86
        shared_materials[slot] = mat; return mat
    context = {}
    for id_ in context_ids-set(IDS):
        if id_ in ph: obj = ph[id_]
        else:
            mesh = bpy.data.meshes.new('CONTEXT_'+id_)
            mesh.from_pydata([mul(p, .001) for p in original[id_]['vertices']], [], original[id_]['faces']); mesh.update()
            bm = bmesh.new(); bm.from_mesh(mesh); bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-7)
            bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(mesh); bm.free()
            for face in mesh.polygons: face.use_smooth = len(original[id_]['faces']) > 512
            obj = bpy.data.objects.new('CONTEXT_'+id_, mesh); bpy.context.collection.objects.link(obj)
        obj.data.materials.clear(); obj.data.materials.append(material(id_)); context[id_] = obj
    before = {id_: obj for id_, obj in ph.items() if id_ in IDS}
    for id_, obj in before.items(): obj.data.materials.clear(); obj.data.materials.append(material(id_))
    names = {obj.name for obj in bpy.context.scene.objects}
    bpy.ops.import_scene.gltf(filepath=str(output/GLB_NAME))
    after = {obj.name[3:]: obj for obj in bpy.context.scene.objects if obj.name not in names and obj.type == 'MESH'}
    require(set(after) == set(IDS), 'New visual cohort differs after Blender GLB import')
    for id_, obj in after.items(): obj.data.materials.clear(); obj.data.materials.append(material(id_))
    bpy.ops.mesh.primitive_plane_add(size=200, location=(0, 0, .0)); floor = bpy.context.object
    mat = bpy.data.materials.new('NeutralFloor'); mat.use_nodes = True
    mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'].default_value = (.26, .27, .26, 1)
    mat.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value = .85
    floor.data.materials.append(mat)
    scene = bpy.context.scene; scene.render.engine = 'CYCLES'; scene.cycles.samples = 32
    scene.cycles.use_denoising = True; scene.cycles.device = 'CPU'
    scene.render.resolution_x = 1600; scene.render.resolution_y = 1100; scene.render.resolution_percentage = 100
    scene.world.color = (.18, .18, .18); scene.view_settings.view_transform = 'AgX'; scene.view_settings.exposure = 0
    camera_data = bpy.data.cameras.new('ComparisonCamera'); camera = bpy.data.objects.new('ComparisonCamera', camera_data)
    bpy.context.collection.objects.link(camera); scene.camera = camera; camera_data.type = 'ORTHO'
    light_data = bpy.data.lights.new('LargeSoftbox', 'AREA'); light_data.energy = 1600; light_data.shape = 'DISK'; light_data.size = 5
    light = bpy.data.objects.new('LargeSoftbox', light_data); bpy.context.collection.objects.link(light)
    previews = output/'preview'; require(not previews.exists(), 'Use a new immutable preview directory'); previews.mkdir()
    evidence = []
    configurations = [
        ('sofa', {f'DOM_{n:05}' for n in range(1438, 1453)}, (10.8, 5.2, .60), (15.4, 10.7, 3.7), 4.5),
        ('dining-chair', {f'DOM_{n:05}' for n in range(1466, 1475)}, (7.40, 4.95, .46), (10.2, 7.6, 1.65), 1.32),
        ('sofa-cushion-close', {'DOM_01443', 'DOM_01444', 'DOM_01439'}, (9.80, 4.55, .51), (12.6, 8.0, 1.85), 1.38),
    ]
    for view, show, target, location, scale in configurations:
        camera.location = location; camera.rotation_euler = (Vector(target)-camera.location).to_track_quat('-Z', 'Y').to_euler(); camera_data.ortho_scale = scale
        light.location = (target[0]-2, target[1]+2, target[2]+4)
        light.rotation_euler = (Vector(target)-light.location).to_track_quat('-Z', 'Y').to_euler()
        for state, selected in (('before', before), ('after', after)):
            for id_, obj in context.items(): obj.hide_render = id_ not in show
            for collection in (before, after):
                for id_, obj in collection.items(): obj.hide_render = collection is not selected or id_ not in show
            path = previews/f'{view}-{state}.png'; scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True)
            evidence.append({'view': view, 'state': state, 'path': str(path), 'sha256': sha(path), 'target': target, 'camera': location, 'orthographicScale': scale})
    (previews/'preview-report.json').write_text(json.dumps({'owner': OWNER, 'generatorSha256': sha(__file__), 'glbSha256': report['glbSha256'],
        'acceptedBaselineGlb': str(baseline_path), 'acceptedBaselineGlbSha256': sha(baseline_path), 'blenderVersion': bpy.app.version_string,
        'images': evidence, 'materials': 'Same inherited linear cloth palettes and roughness for both, neutral geometry study; not the Unreal cloth shader.',
        'nativeRenderedVerified': False}, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--geometry'); parser.add_argument('--output'); parser.add_argument('--preview')
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None)
    if args.preview: preview(args.preview)
    else:
        require(args.geometry and args.output, 'geometry and output are required'); build(args.geometry, args.output)
