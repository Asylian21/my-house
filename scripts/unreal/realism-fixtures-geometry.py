"""Source-bounded kitchen fixture visuals; never edits authoritative scene geometry.

Blender --background --factory-startup --python-exit-code 1 --python <this file>
  -- --geometry <validated geometry> --output <new output/unreal directory>

The pure Python geometry builder also supports CPU checks without Blender. The
native import stage must retain all original components/collision and bind the
current source materials using materialBindings; these are visual overlays.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/realism-fixtures-geometry.py'
GLB_NAME = 'realism-fixtures.glb'
METAL = 'Kitchen 2026 · kartáčovaná oceľ'
DARK = 'Kitchen 2026 · zapustené profily'
EXPECTED = {
    'DOM_00759': ('KITCHEN-RUN · drez · zapustené dno 600', METAL),
    **{f'DOM_{n:05}': ('KITCHEN-RUN · drez · nerezová stena', METAL) for n in range(760, 764)},
    'DOM_00764': ('KITCHEN-RUN · drez · sitko', DARK),
    'DOM_00765': ('KITCHEN-RUN · batéria · subtilná oceľ', METAL),
    'DOM_00766': ('KITCHEN-RUN · batéria · páčka', METAL),
}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def sub(a, b):
    return tuple(x-y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def norm(p):
    return math.sqrt(sum(x*x for x in p))


def unit(p):
    length = norm(p)
    require(length > 1e-10, 'Zero length geometric direction')
    return tuple(x/length for x in p)


def bounds(points):
    return {op: [fn(p[i] for p in points) for i in range(3)]
            for op, fn in (('min', min), ('max', max))}


def union_bounds(records):
    return {op: [fn(r['boundsMm'][op][i] for r in records) for i in range(3)]
            for op, fn in (('min', min), ('max', max))}


def source_records(scene):
    require(scene.get('activeDesign') == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'},
            'Only C/B/B is supported')
    placement = scene['house']['placement']
    require(placement['streetSetbackMm'] == placement['eastSetbackMm'] == 3000, 'Setback contract differs')
    records = {r['id']: r for r in scene['objects'] if r['id'] in EXPECTED}
    require(set(records) == set(EXPECTED), 'Exact eight fixture sources are required')
    require(len([r for r in scene['objects'] if r['id'] in EXPECTED]) == 8, 'Duplicate fixture source ID')
    for id_, (name, material) in EXPECTED.items():
        record = records[id_]
        require(record['enabled'] and record['name'] == name, 'Fixture semantic identity differs: '+id_)
        require(record['materialNames'] == [material] and len(record['materialSlots']) == 1,
                'Fixture material identity differs: '+id_)
        require(not record.get('metadata', {}).get('doorMotion'), 'Movable door geometry is protected')
        b = record['boundsMm']
        require(all(math.isfinite(b[k][i]) for k in ('min', 'max') for i in range(3)), 'Non-finite source bounds')
    b = records['DOM_00759']['boundsMm']
    require(all(abs(b['max'][i]-b['min'][i]-size) < .01 for i, size in enumerate((600, 400, 3))),
            'Review changed nominal 600 x 400 mm basin')
    return records


class Mesh:
    def __init__(self, id_, source_ids, material_ids):
        self.id = id_
        self.source_ids = source_ids
        self.material_ids = material_ids
        self.vertices = []
        self.faces = []
        self.materials = []

    def vertex(self, point):
        self.vertices.append(tuple(point))
        return len(self.vertices)-1

    def ring(self, points):
        return [self.vertex(p) for p in points]

    def triangle(self, a, b, c, material=0):
        self.faces.append((a, b, c))
        self.materials.append(material)

    def bridge(self, a, b, material=0):
        require(len(a) == len(b), 'Ring vertex count differs')
        for i in range(len(a)):
            j = (i+1) % len(a)
            self.triangle(a[i], a[j], b[j], material)
            self.triangle(a[i], b[j], b[i], material)


def rounded_rectangle(hx, hy, radius, z, center, segments=23):
    """CCW perimeter including arc endpoints; straight portions stay straight."""
    require(0 < radius <= min(hx, hy), 'Invalid rounded rectangle radius')
    points = []
    for q, (x, y) in enumerate(((hx-radius, hy-radius), (-hx+radius, hy-radius),
                               (-hx+radius, -hy+radius), (hx-radius, -hy+radius))):
        for j in range(segments+1):
            angle = (q+j/segments)*math.pi/2
            points.append((center[0]+x+radius*math.cos(angle), center[1]+y+radius*math.sin(angle), z))
    return points


def circle(radius, z, center, count=96):
    return [(center[0]+radius*math.cos(i*math.tau/count), center[1]+radius*math.sin(i*math.tau/count), z)
            for i in range(count)]


def basin(records):
    mesh = Mesh('RF_SINK_BOWL', [f'DOM_{n:05}' for n in range(759, 764)], ['DOM_00759'])
    b = records['DOM_00759']['boundsMm']
    center = [(b['min'][i]+b['max'][i])/2 for i in range(2)]
    z0 = b['min'][2]
    rings = []

    def rect(hx, hy, radius, height):
        rings.append(mesh.ring(rounded_rectangle(hx, hy, radius, z0+height, center)))

    # One continuous steel shell: softly rolled upper lip, drafted walls,
    # 24 mm floor fillet, slightly draining floor, and a real drain opening.
    rect(298.3, 198.3, 20, 197.2)
    rect(291, 191, 22, 29)
    for j in range(1, 13):
        angle = j/12*math.pi/2
        inset = 24*(1-math.cos(angle))
        rect(291-inset, 191-inset, 22, 29-24*math.sin(angle))
    # Local support rings keep the fillet and drain wall normals from being
    # interpolated across the broad, nearly planar floor in the exported GLB.
    rect(264, 164, 22, 4.99)
    rings.append(mesh.ring(circle(38, z0+4.31, center)))
    rings.append(mesh.ring(circle(34.7, z0+4.3, center)))
    rings.append(mesh.ring(circle(34.7, z0+3.0, center)))
    rect(267, 167, 22, 3.7)
    for j in range(11, -1, -1):
        angle = j/12*math.pi/2
        inset = 24*(1-math.cos(angle))
        rect(291-inset+1.3, 191-inset+1.3, 23.3, 29-24*math.sin(angle)-1.3)
    rect(299.6, 199.6, 21.3, 197.2)
    for j in range(1, 8):
        angle = j/8*math.pi
        offset = .65*math.cos(angle)
        rect(298.95+offset, 198.95+offset, 20.65+offset, 197.2+.65*math.sin(angle))
    for a, next_ in zip(rings, rings[1:]+rings[:1]):
        mesh.bridge(a, next_)
    return mesh


def filleted_path(points, cut=22, samples=16):
    """Quadratic fillets retain end poses and tangency to the source segments."""
    result = [points[0]]
    for i in range(1, len(points)-1):
        before, joint, after = points[i-1:i+2]
        incoming, outgoing = sub(joint, before), sub(after, joint)
        distance = min(cut, norm(incoming)*.3, norm(outgoing)*.3)
        u, v = unit(incoming), unit(outgoing)
        a = tuple(joint[k]-distance*u[k] for k in range(3))
        b = tuple(joint[k]+distance*v[k] for k in range(3))
        result.append(a)
        for j in range(1, samples+1):
            t = j/samples
            result.append(tuple((1-t)**2*a[k]+2*t*(1-t)*joint[k]+t*t*b[k] for k in range(3)))
    result.append(points[-1])
    return result


def spout(records):
    mesh = Mesh('RF_SINK_SPOUT', ['DOM_00765'], ['DOM_00765'])
    b = records['DOM_00765']['boundsMm']
    x = (b['min'][0]+b['max'][0])/2
    y = b['max'][1]-12
    z0 = b['min'][2]
    # The original 24 mm tube has a slightly tilted upper ring. Lower its
    # centreline 0.35 mm so the true circular section stays inside that envelope.
    path = filleted_path([(x, y, z0), (x, y, z0+280), (x, y-35, z0+319.65),
                          (x, y-180, z0+319.65), (x, y-215, z0+280)])
    loops = [[], []]
    for i, point in enumerate(path):
        tangent = unit(sub(path[min(len(path)-1, i+1)], path[max(0, i-1)]))
        transverse = (0, -tangent[2], tangent[1])
        for wall, radius in enumerate((12, 10.6)):
            loops[wall].append(mesh.ring([
                (point[0]+radius*math.cos(j*math.tau/64),
                 point[1]+radius*math.sin(j*math.tau/64)*transverse[1],
                 point[2]+radius*math.sin(j*math.tau/64)*transverse[2]) for j in range(64)]))
    for wall in loops:
        for a, b_ in zip(wall, wall[1:]):
            mesh.bridge(a, b_)
    mesh.bridge(loops[0][0], loops[1][0])
    mesh.bridge(loops[0][-1], loops[1][-1])
    return mesh


def lever(records):
    # The authored handle floated 10 mm from the tube. Its small swivel joins
    # those two parts inside their combined, unchanged fixture envelope.
    mesh = Mesh('RF_SINK_LEVER', ['DOM_00765', 'DOM_00766'], ['DOM_00766'])
    b = records['DOM_00766']['boundsMm']
    center = [(b['min'][i]+b['max'][i])/2 for i in range(2)]
    radii = [(b['max'][i]-b['min'][i])/2 for i in range(2)]
    bottom, top = b['min'][2], b['max'][2]
    first = mesh.vertex((*center, bottom))
    loops = []
    for end in (0, 1):
        for j in range(1 if end == 0 else 0, 9 if end == 0 else 8):
            angle = (j/8+end)*math.pi/2
            z = bottom+4*(1-math.cos(angle)) if end == 0 else top-4-4*math.cos(angle)
            loops.append(mesh.ring([(center[0]+radii[0]*math.sin(angle)*math.cos(k*math.tau/48),
                                     center[1]+radii[1]*math.sin(angle)*math.sin(k*math.tau/48), z)
                                    for k in range(48)]))
    last = mesh.vertex((*center, top))
    for a, b_ in zip(loops, loops[1:]):
        mesh.bridge(a, b_)
    for i in range(48):
        mesh.triangle(first, loops[0][(i+1) % 48], loops[0][i])
        mesh.triangle(last, loops[-1][i], loops[-1][(i+1) % 48])
    stem = records['DOM_00765']['boundsMm']
    stem_x = (stem['min'][0]+stem['max'][0])/2
    hub_loops = []
    for x, radius in ((stem_x+9, 3.8), (stem_x+10, 4.6), (center[0]-.8, 4.6), (center[0], 3.8)):
        hub_loops.append(mesh.ring([(x, center[1]+radius*math.cos(j*math.tau/48),
                                     bottom+6+radius*math.sin(j*math.tau/48)) for j in range(48)]))
    for a, b_ in zip(hub_loops, hub_loops[1:]):
        mesh.bridge(a, b_)
    for loop in (hub_loops[0], hub_loops[-1]):
        center_vertex = mesh.vertex(tuple(sum(mesh.vertices[v][axis] for v in loop)/len(loop) for axis in range(3)))
        for i in range(len(loop)):
            mesh.triangle(center_vertex, loop[i], loop[(i+1) % len(loop)])
    return mesh


def torus(mesh, center, major, radial, vertical, z, material=0, segments=96, cross_segments=12):
    loops = []
    for j in range(cross_segments):
        angle = j*math.tau/cross_segments
        loops.append(mesh.ring(circle(major+radial*math.cos(angle), z+vertical*math.sin(angle), center, segments)))
    for a, b_ in zip(loops, loops[1:]+loops[:1]):
        mesh.bridge(a, b_, material)


def cylinder(mesh, center, radius, z0, z1, material=0, segments=96):
    a, b = mesh.ring(circle(radius, z0, center, segments)), mesh.ring(circle(radius, z1, center, segments))
    bottom, top = mesh.vertex((*center, z0)), mesh.vertex((*center, z1))
    mesh.bridge(a, b, material)
    for i in range(segments):
        j = (i+1) % segments
        mesh.triangle(bottom, a[j], a[i], material)
        mesh.triangle(top, b[i], b[j], material)


def drain(records):
    mesh = Mesh('RF_SINK_DRAIN', ['DOM_00764'], ['DOM_00759', 'DOM_00764'])
    b = records['DOM_00764']['boundsMm']
    center = [(b['min'][i]+b['max'][i])/2 for i in range(2)]
    z0 = b['min'][2]
    # A low steel rim and basket lattice reveal a recessed dark drain below.
    # Both finishes are rebound to the original current scene materials.
    torus(mesh, center, 31.4, 3.4, .55, z0+2.1)
    for radius in (10.5, 19.5, 27.4):
        torus(mesh, center, radius, .85, .3, z0+1.65)
    cylinder(mesh, center, 30, z0+.05, z0+.3, material=1)
    cylinder(mesh, center, 4, z0+.3, z0+1.95)
    # Six small steel bridges over the recessed holes; each is a closed tube.
    for spoke in range(6):
        angle = spoke*math.tau/6
        loops = []
        for length in (3.5, 28.2):
            points = []
            for j in range(12):
                a = j*math.tau/12
                side = .7*math.cos(a)
                points.append((center[0]+length*math.cos(angle)-side*math.sin(angle),
                               center[1]+length*math.sin(angle)+side*math.cos(angle), z0+1.65+.3*math.sin(a)))
            loops.append(mesh.ring(points))
        mesh.bridge(*loops)
        for loop in loops:
            center_vertex = mesh.vertex(tuple(sum(mesh.vertices[v][axis] for v in loop)/len(loop) for axis in range(3)))
            for i in range(len(loop)):
                mesh.triangle(center_vertex, loop[i], loop[(i+1) % len(loop)])
    return mesh


def check_mesh(mesh, records):
    require(mesh.vertices and mesh.faces, 'Empty fixture mesh')
    require(all(math.isfinite(v) for p in mesh.vertices for v in p), 'Non-finite fixture vertex')
    areas = [norm(cross(sub(mesh.vertices[b], mesh.vertices[a]), sub(mesh.vertices[c], mesh.vertices[a])))/2
             for a, b, c in mesh.faces]
    require(min(areas) > 1e-7, 'Degenerate fixture triangle: '+mesh.id)
    edges = Counter(tuple(sorted((f[i], f[(i+1) % 3]))) for f in mesh.faces for i in range(3))
    require(set(edges.values()) == {2}, 'Fixture mesh must have closed manifold edges: '+mesh.id)
    source_bounds = union_bounds([records[id_] for id_ in mesh.source_ids])
    actual = bounds(mesh.vertices)
    outward = max([0.] + [source_bounds['min'][i]-actual['min'][i] for i in range(3)]
                  + [actual['max'][i]-source_bounds['max'][i] for i in range(3)])
    require(outward < .01, f'Fixture extends outside authoritative source envelope: {mesh.id}: {outward}')
    require(len(mesh.faces) <= 20000, 'Fixture triangle budget exceeded')
    return {'id': mesh.id, 'sourceIds': mesh.source_ids,
            'materialSourceId': mesh.material_ids[0], 'materialSlot': 0,
            'materialSourceIds': mesh.material_ids,
            'materialBindings': [{'sourceId': id_, 'sourceSlot': 0} for id_ in mesh.material_ids],
            'sourceBoundsMm': source_bounds, 'visualBoundsMm': actual,
            'expectedWorldBoundsCm': {'min': [actual['min'][0]/10, -actual['max'][1]/10, actual['min'][2]/10],
                                      'max': [actual['max'][0]/10, -actual['min'][1]/10, actual['max'][2]/10]},
            'vertices': len(mesh.vertices), 'triangles': len(mesh.faces),
            'minimumTriangleAreaMm2': min(areas), 'nonManifoldEdges': 0, 'outwardEnvelopeMm': outward}


def build_geometry(scene):
    records = source_records(scene)
    meshes = [basin(records), drain(records), spout(records), lever(records)]
    checks = [check_mesh(mesh, records) for mesh in meshes]
    require({id_ for mesh in meshes for id_ in mesh.source_ids} == set(EXPECTED), 'Source coverage differs')
    require(sum(len(mesh.faces) for mesh in meshes) < 45000, 'Fixture total triangle budget exceeded')
    return meshes, checks


def build(geometry, output):
    import bpy
    import bmesh
    from mathutils import Matrix
    geometry, output = Path(geometry).resolve(), Path(output).resolve()
    require(output.is_relative_to(ROOT/'output/unreal'), 'Output must stay in output/unreal')
    require(not output.exists(), 'Use a new directory; fixture builds are immutable')
    scene = json.loads((geometry/'scene.json').read_text())
    require(scene['objSha256'] == sha(geometry/'dom-mm.obj'), 'Source OBJ hash differs')
    meshes, objects = build_geometry(scene)
    output.mkdir(parents=True)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    materials = {}
    for id_, color, metallic, roughness in (('DOM_00759', (.42, .45, .43, 1), .9, .38),
                                           ('DOM_00764', (.036, .033, .027, 1), 0, .64)):
        material = bpy.data.materials.new('RF_'+id_)
        material.use_nodes = True
        shader = material.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = color
        shader.inputs['Metallic'].default_value = metallic
        shader.inputs['Roughness'].default_value = roughness
        materials[id_] = material
    materials['DOM_00765'] = materials['DOM_00759']
    materials['DOM_00766'] = materials['DOM_00759']
    for mesh in meshes:
        data = bpy.data.meshes.new(mesh.id)
        data.from_pydata([tuple(v/1000 for v in p) for p in mesh.vertices], [], mesh.faces)
        data.update()
        for id_ in mesh.material_ids:
            data.materials.append(materials[id_])
        for face, slot in zip(data.polygons, mesh.materials):
            face.material_index = slot
            face.use_smooth = True
        bm = bmesh.new()
        bm.from_mesh(data)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
        bm.to_mesh(data)
        bm.free()
        obj = bpy.data.objects.new(mesh.id, data)
        bpy.context.collection.objects.link(obj)
        obj['fixture_source_ids'] = ','.join(mesh.source_ids)
        obj['visual_only'] = True
        obj.select_set(True)
    bpy.context.view_layer.update()
    bpy.ops.export_scene.gltf(filepath=str(output/GLB_NAME), export_format='GLB', use_selection=True,
                              export_yup=True, export_extras=True, export_animations=False,
                              export_cameras=False, export_lights=False)
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(output/GLB_NAME))
    actual = {obj.name: obj for obj in bpy.context.scene.objects if obj.type == 'MESH'}
    require(set(actual) == {obj['id'] for obj in objects}, 'GLB fixture identity roundtrip differs')
    maximum_error = 0
    for record in objects:
        obj = actual[record['id']]
        obj.data.transform(obj.matrix_world)
        obj.matrix_world = Matrix.Identity(4)
        result = bounds([tuple(float(c)*1000 for c in v.co) for v in obj.data.vertices])
        error = max(abs(result[k][i]-record['visualBoundsMm'][k][i]) for k in ('min', 'max') for i in range(3))
        require(error < .01, 'GLB fixture coordinate roundtrip differs')
        require(len(obj.data.materials) == len(record['materialBindings']), 'GLB material slot count differs')
        expected_materials = ['RF_'+('DOM_00759' if id_ in ('DOM_00765', 'DOM_00766') else id_)
                              for id_ in record['materialSourceIds']]
        require(all(material.name.split('.')[0] == name for material, name in zip(obj.data.materials, expected_materials)),
                'GLB fixture material order differs')
        maximum_error = max(maximum_error, error)
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'offline-geometry-validated',
              'generatedAt': datetime.now(timezone.utc).isoformat(), 'activeDesign': scene['activeDesign'],
              'sourceGeometry': str(geometry), 'sourceSceneSha256': sha(geometry/'scene.json'),
              'sourceManifestSha256': sha(geometry/'scene.json'), 'sourceObjSha256': sha(geometry/'dom-mm.obj'),
              'generatorSha256': sha(__file__), 'glb': GLB_NAME, 'glbSha256': sha(output/GLB_NAME),
              'blenderVersion': bpy.app.version_string, 'sourceIds': sorted(EXPECTED),
              'objects': objects, 'triangles': sum(o['triangles'] for o in objects),
              'roundtripErrorMm': maximum_error,
              'coordinateSystem': 'Source OBJ XYZ millimetres -> Blender XYZ metres/Z-up -> glTF metres/Y-up; Unreal X=x/10,Y=-y/10,Z=z/10.',
              'fixtureDesign': {'nominalBowlOpeningMm': [600, 400], 'nominalCounterToBowlBottomMm': 200,
                                'actualSourceSteelEnvelopeMm': [604, 404, 198],
                                'spoutOuterDiameterMm': 24, 'spoutWallThicknessMm': 1.4,
                                'floorFilletRadiusMm': 24, 'upperInsideCornerRadiusMm': 20,
                                'leverSwivel': 'Joins the formerly disconnected handle inside the original combined faucet/lever bounds.'},
              'sourcePolicy': 'Hide only sourceIds visual/lighting contributions; retain original mesh, transforms and collision. NoCollision on all four imported visual meshes.',
              'nativeImportVerified': False, 'visualQualityVerified': False,
              'limitations': ['Authored cosmetic geometry, not a measured manufacturer asset.',
                              'No change to the authoritative nominal sink dimensions or source geometry.',
                              'Offline manifold/bounds/GLB checks do not establish native visual acceptance.']}
    (output/'geometry-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print('REALISM_FIXTURES', json.dumps({'objects': len(objects), 'sourceIds': report['sourceIds'],
                                       'triangles': report['triangles'], 'roundtripErrorMm': maximum_error}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--geometry', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None)
    build(args.geometry, args.output)
