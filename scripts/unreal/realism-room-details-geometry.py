"""Visual-only laundry/lamp construction cues and round sink-cutout corner fills.

Run in Blender with --geometry <source> --output <new output/unreal folder>.
Never changes source geometry. Six door overlays MUST follow their original
moving components; the importer must preserve bVisible=true and
hidden_in_game=false on those originals for UBreziDoors validation. Suppress
their main/depth passes and lighting instead. Static-world overlays are invalid.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/realism-room-details-geometry.py'
HELPER = Path(__file__).with_name('realism-fixtures-geometry.py')
SPEC = importlib.util.spec_from_file_location('room_geometry_primitives', HELPER)
G = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(G)
require, sha, bounds = G.require, G.sha, G.bounds
GLB_NAME = 'realism-room-details.glb'
PREFIX = 'BATHROOM-FITOUT-STACKED-LAUNDRY-2026-08-25 · LAUNDRY-TOWER · '
WHITE, GLASS, STEEL = 'real-bathroom-appliance-white', 'real-interior-black-glass', 'real-interior-steel'
BRASS, GLOW = 'real-interior-brushed-brass', 'real-interior-warm-light'
STONE = 'Kitchen 2026 · čierny kameň · saténový povrch'
EXPECTED = {}
for first, kind, noun in ((938, 'WASHER', 'práčka'), (944, 'DRYER', 'sušička')):
    for index, (suffix, material) in enumerate(((noun, WHITE), ('ovládací panel', GLASS), ('volič programu', WHITE),
            ('otváravé dvierka · rám', WHITE), ('otváravé dvierka · sklo', GLASS), ('madlo dvierok', STEEL))):
        EXPECTED[f'DOM_{first+index:05}'] = (PREFIX+kind+' · '+suffix, material)
EXPECTED.update({
    'DOM_01225': ('C-BOY-109 · DESK · bezdrôtová stolová lampa', BRASS),
    'DOM_01226': ('C-BOY-109 · DESK · mäkké svetlo lampy', GLOW),
    'DOM_00740': ('KITCHEN-RUN · pracovná doska ostrovčeka · minerálny povrch', STONE),
    'DOM_00759': ('KITCHEN-RUN · drez · zapustené dno 600', 'Kitchen 2026 · kartáčovaná oceľ'),
})
HIDE_IDS = [f'DOM_{n:05}' for n in range(938, 950)] + ['DOM_01225', 'DOM_01226']
MOTION_IDS = {f'DOM_{n:05}': 'BATH-105-'+kind+'-DOOR' for kind, indices in
              (('WASHER', range(941, 944)), ('DRYER', range(947, 950))) for n in indices}


def source_records(scene):
    require(scene['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'Only C/B/B supported')
    placement = scene['house']['placement']
    require(placement['streetSetbackMm'] == placement['eastSetbackMm'] == 3000, 'Setbacks changed')
    records = {r['id']: r for r in scene['objects'] if r['id'] in EXPECTED}
    require(len([r for r in scene['objects'] if r['id'] in EXPECTED]) == len(EXPECTED)
            and set(records) == set(EXPECTED), 'Exact source membership required')
    for id_, (name, material) in EXPECTED.items():
        r = records[id_]
        require(r['enabled'] and r['instances'] == 1 and r['name'] == name, 'Source semantic identity differs: '+id_)
        require(r['materialNames'] == [material] and len(r['materialSlots']) == 1, 'Source material differs: '+id_)
        metadata = r.get('metadata', {})
        if id_ in MOTION_IDS:
            require(metadata.get('doorId') == MOTION_IDS[id_] and metadata.get('doorMotion') == 'HINGED'
                    and metadata.get('doorSubject') == 'APPLIANCE_DOOR', 'Appliance motion identity differs: '+id_)
        else:
            require(not metadata.get('doorMotion'), 'Unexpected movable source: '+id_)
    for first in (938, 944):
        b = records[f'DOM_{first:05}']['boundsMm']
        require(all(abs(b['max'][i]-b['min'][i]-size) < .01 for i, size in enumerate((570, 26, 850))),
                'Appliance face envelope changed')
    return records


class Mesh(G.Mesh):
    def __init__(self, id_, source_ids, material_ids, hidden_ids=None, motion_id=None):
        super().__init__(id_, source_ids, material_ids)
        self.hidden_ids = source_ids if hidden_ids is None else hidden_ids
        self.motion_id = motion_id
        self.flat_faces = set()


def center(record):
    b = record['boundsMm']
    return [(b['min'][i]+b['max'][i])/2 for i in range(3)]


def front_rectangle(mesh, halfx, halfz, radius, y, cx, cz):
    return mesh.ring([(x, depth, z) for x, z, depth in G.rounded_rectangle(halfx, halfz, max(.001, radius), y, (cx, cz), 11)])


def cap(mesh, loop, material=0, flat=False):
    middle = mesh.vertex(tuple(sum(mesh.vertices[v][i] for v in loop)/len(loop) for i in range(3)))
    start = len(mesh.faces)
    for j in range(len(loop)):
        mesh.triangle(middle, loop[j], loop[(j+1) % len(loop)], material)
    if flat:
        mesh.flat_faces.update(range(start, len(mesh.faces)))


def lathe(mesh, cx, cy, cz, profile, material=0, segments=96, axis='Y'):
    """Closed revolved profiles; radius-zero ends use one pole, never degenerate rings."""
    loops = []
    for radius, depth in profile:
        if radius == 0:
            loops.append([mesh.vertex((cx, depth, cz) if axis == 'Y' else (cx, cy, depth))])
        else:
            loops.append(mesh.ring([(cx+radius*math.cos(j*math.tau/segments), depth,
                                      cz+radius*math.sin(j*math.tau/segments)) if axis == 'Y' else
                                    (cx+radius*math.cos(j*math.tau/segments), cy+radius*math.sin(j*math.tau/segments), depth)
                                    for j in range(segments)]))
    for a, b in zip(loops, loops[1:]+loops[:1]):
        if len(a) == len(b) == 1:
            continue
        if len(a) == 1 or len(b) == 1:
            pole, ring = (a[0], b) if len(a) == 1 else (b[0], a)
            for i in range(len(ring)):
                mesh.triangle(pole, ring[i], ring[(i+1) % len(ring)], material)
        else:
            mesh.bridge(a, b, material)


def rounded_box(mesh, b, radius, material=0):
    cx, cy, cz = [(b['min'][i]+b['max'][i])/2 for i in range(3)]
    hx, hy, hz = [(b['max'][i]-b['min'][i])/2 for i in range(3)]
    radius = min(radius, hx*.4, hy*.4, hz*.4)
    loops = []
    for side in (-1, 1):
        for j in range(7):
            a = (j if side == -1 else 6-j)*math.pi/12
            section = max(.002, radius*math.sin(a))
            y = cy+side*(hy-radius+radius*math.cos(a))
            loops.append(front_rectangle(mesh, hx-radius+section, hz-radius+section, section, y, cx, cz))
    for a, b_ in zip(loops, loops[1:]):
        mesh.bridge(a, b_, material)
    cap(mesh, loops[0], material, flat=True)
    cap(mesh, loops[-1], material, flat=True)


def appliance(records, first, kind):
    ids = [f'DOM_{first+i:05}' for i in range(6)]
    body_id, controls_id, selector_id, rim_id, glass_id, handle_id = ids
    body = Mesh('RD_'+kind+'_BODY', [body_id], [body_id, handle_id, glass_id])
    b = records[body_id]['boundsMm']; cx, cy, cz = center(records[body_id])
    door_center = center(records[rim_id]); door_z = door_center[2]
    # Rounded enamel face with a genuine opening and shallow stationary liner,
    # all confined to the original 26 mm front-panel envelope.
    rings = []
    for y, inset, radius in ((b['min'][1], 3, .01), (b['min'][1]+.9, 1, 2),
                              (b['min'][1]+3, 0, 3), (b['max'][1]-3, 0, 3),
                              (b['max'][1]-.9, 1, 2), (b['max'][1], 3, .01)):
        rings.append(front_rectangle(body, 285-inset, 425-inset, radius, y, cx, cz))
    for a, b_ in zip(rings, rings[1:]): body.bridge(a, b_)
    front_hole = body.ring([(cx+184*math.cos(j*math.tau/48), b['min'][1], door_z+184*math.sin(j*math.tau/48)) for j in range(48)])
    rear_hole = body.ring([(cx+184*math.cos(j*math.tau/48), b['max'][1], door_z+184*math.sin(j*math.tau/48)) for j in range(48)])
    start = len(body.faces)
    body.bridge(rings[0], front_hole); body.bridge(rings[-1], rear_hole)
    body.flat_faces.update(range(start, len(body.faces)))
    body.bridge(front_hole, rear_hole)
    front, back = b['min'][1]+.2, b['max'][1]-.2
    lathe(body, cx, cy, door_z, [(183, front), (181, front+.8), (164, back-2), (151, back-2),
                                (151, back-.6), (165, back-.6), (183, front+1.7)], material=1)
    lathe(body, cx, cy, door_z, [(0, back-.15), (182.5, back-.15), (182.5, back), (0, back)], material=2)

    controls = Mesh('RD_'+kind+'_CONTROLS', [controls_id], [controls_id])
    rounded_box(controls, records[controls_id]['boundsMm'], 2)

    selector = Mesh('RD_'+kind+'_SELECTOR', [selector_id], [selector_id, controls_id])
    sb = records[selector_id]['boundsMm']; x, y, z = center(records[selector_id])
    f, back = sb['min'][1], sb['max'][1]
    lathe(selector, x, y, z, [(0, f+.2), (26, f+.2), (29.4, f+1), (30, f+3),
                             (30, back-2), (28.5, back-.2), (0, back-.2)])
    rounded_box(selector, {'min': [x-.6, f+.02, z+17], 'max': [x+.6, f+.16, z+24]}, .05, 1)

    rim = Mesh('RD_'+kind+'_DOOR_RIM', [rim_id], [rim_id, glass_id], motion_id=rim_id)
    rb = records[rim_id]['boundsMm']; x, y, z = center(records[rim_id]); f, back = rb['min'][1], rb['max'][1]
    lathe(rim, x, y, z, [(232, back-.1), (234.8, back-2), (235, back-5), (235, f+8),
                         (233, f+3), (229, f+.15), (199, f+.15), (190, f+5), (187, f+12), (187, back-.1)])
    lathe(rim, x, y, z, [(189.5, f+8), (191.5, f+9), (192, f+12), (189.5, f+13), (188.5, f+11)], material=1)

    lens = Mesh('RD_'+kind+'_DOOR_GLASS', [glass_id], [glass_id], motion_id=glass_id)
    gb = records[glass_id]['boundsMm']; x, y, z = center(records[glass_id]); f, back = gb['min'][1], gb['max'][1]
    lathe(lens, x, y, z, [(0, f+29), (75, f+28), (130, f+24), (170, f+16), (184, f+5),
                          (189.5, f+.5), (190, f+4), (189, f+8), (186, back-1), (0, back-.1)], segments=128)
    handle = Mesh('RD_'+kind+'_DOOR_HANDLE', [handle_id], [handle_id], motion_id=handle_id)
    rounded_box(handle, records[handle_id]['boundsMm'], 3)
    return [body, controls, selector, rim, lens, handle]


def lamp(records):
    base_id, globe_id = 'DOM_01225', 'DOM_01226'
    base = Mesh('RD_BOY_LAMP_BASE', [base_id, globe_id], [base_id], hidden_ids=[base_id])
    b = records[base_id]['boundsMm']; cx, cy, _ = center(records[base_id]); lo, hi = b['min'][2], b['max'][2]
    lathe(base, cx, cy, 0, [(0, lo+.05), (87, lo+.05), (89.5, lo+1), (90, lo+3),
                           (90, hi-3), (88, hi-.3), (12, hi-.3), (10, hi-1), (0, hi-1)], axis='Z')
    globe_lo = records[globe_id]['boundsMm']['min'][2]
    # A real support joins the base and globe; no added point light or emission.
    lathe(base, cx, cy, 0, [(0, hi-2), (6, hi-2), (6, globe_lo+6), (0, globe_lo+6)], axis='Z', segments=48)
    lathe(base, cx, cy, 0, [(0, globe_lo-2), (9, globe_lo-2), (10, globe_lo),
                           (10, globe_lo+4), (8, globe_lo+6), (0, globe_lo+6)], axis='Z', segments=48)
    globe = Mesh('RD_BOY_LAMP_GLOBE', [globe_id], [globe_id])
    _, _, z = center(records[globe_id])
    profile = [(0, z-80)] + [(80*math.sin(j*math.pi/48), z-80*math.cos(j*math.pi/48)) for j in range(1, 48)] + [(0, z+80)]
    lathe(globe, cx, cy, z, profile, segments=96, axis='Z')
    return [base, globe]


def corner_fills(records):
    top = records['DOM_00740']['boundsMm']; sink = records['DOM_00759']['boundsMm']
    patches = []
    # Square source hole has black corner wedges around the new R20 basin. A
    # 22 mm cutout radius covers them while remaining inside the original hole.
    for index, (sx, sy) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        mesh = Mesh('RD_SINK_CORNER_'+str(index+1), ['DOM_00740'], ['DOM_00740'], hidden_ids=[])
        x = sink['min'][0] if sx == 1 else sink['max'][0]
        y = sink['min'][1] if sy == 1 else sink['max'][1]
        r = 22
        polygon = [(x, y)] + [(x+sx*(r-r*math.cos(j*math.pi/48)), y+sy*(r-r*math.sin(j*math.pi/48))) for j in range(25)]
        loops = [mesh.ring([(px, py, z) for px, py in polygon]) for z in (top['min'][2], top['max'][2])]
        mesh.bridge(*loops)
        # Corner fan lies entirely in this convex curvilinear triangle.
        for ring in loops:
            for j in range(1, len(ring)-1): mesh.triangle(ring[0], ring[j], ring[j+1])
        mesh.flat_faces = set(range(len(mesh.faces)))
        patches.append(mesh)
    return patches


def build_geometry(scene):
    records = source_records(scene)
    meshes = appliance(records, 938, 'WASHER') + appliance(records, 944, 'DRYER') + lamp(records) + corner_fills(records)
    report = []
    for mesh in meshes:
        row = G.check_mesh(mesh, records)
        row.update(hiddenSourceIds=mesh.hidden_ids, mode='replacement' if mesh.hidden_ids else 'additive',
                   motionSourceId=mesh.motion_id, doorId=MOTION_IDS.get(mesh.motion_id))
        if mesh.id.startswith('RD_SINK_CORNER_'):
            sink = records['DOM_00759']['boundsMm']
            require(all(sink['min'][i]-.01 <= p[i] <= sink['max'][i]+.01 for p in mesh.vertices for i in (0, 1)),
                    'Countertop corner fill left original cutout')
        report.append(row)
    require({id_ for mesh in meshes for id_ in mesh.hidden_ids} == set(HIDE_IDS), 'Hidden source coverage differs')
    require({m.motion_id for m in meshes if m.motion_id} == set(MOTION_IDS), 'Moving overlay coverage differs')
    require(sum(len(m.faces) for m in meshes) < 90000, 'Room detail triangle budget exceeded')
    return meshes, report


def validate_doors(doors, records):
    members = {m['sourceObjectId']: (door, m) for door in doors['doors'] for m in door['members']
               if m['sourceObjectId'] in MOTION_IDS}
    require(set(members) == set(MOTION_IDS), 'Six appliance source door members required')
    for id_, (door, member) in members.items():
        require(door['id'] == MOTION_IDS[id_] and door['kind'] == 'HINGED' and door['subject'] == 'APPLIANCE_DOOR'
                and not door['architectural'] and not member['hidden'], 'Source appliance door contract differs')
        require(member['runtimeTag'].startswith('BreziDoorMember='), 'Stable runtime motion binding missing')
        require(member['sourceName'] == records[id_]['name'], 'Door source identity differs')
        b = records[id_]['boundsMm']
        expected = {'min': [b['min'][0]/10, -b['max'][1]/10, b['min'][2]/10],
                    'max': [b['max'][0]/10, -b['min'][1]/10, b['max'][2]/10]}
        require(max(abs(member['closedBoundsCm'][k][i]-expected[k][i]) for k in ('min', 'max') for i in range(3)) < .01,
                'Door closed source bounds differ')
    return {id_: {'doorId': door['id'], 'runtimeTag': member['runtimeTag'],
                  'collision': member['collision'], 'closedBoundsCm': member['closedBoundsCm']}
            for id_, (door, member) in members.items()}


def build(geometry, output):
    import bpy
    import bmesh
    from mathutils import Matrix
    geometry, output = Path(geometry).resolve(), Path(output).resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Use a new output/unreal directory')
    scene = json.loads((geometry/'scene.json').read_text())
    require(scene['objSha256'] == sha(geometry/'dom-mm.obj'), 'Source OBJ hash differs')
    records = source_records(scene)
    door_contract = json.loads((geometry/'doors.json').read_text())
    require(door_contract['sourceManifestSha256'] == sha(geometry/'scene.json')
            and door_contract['sourceObjSha256'] == sha(geometry/'dom-mm.obj'), 'Door/source contract pins differ')
    doors = validate_doors(door_contract, records)
    meshes, objects = build_geometry(scene)
    output.mkdir(parents=True)
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    colors = {WHITE: ((.72, .72, .7, 1), 0, .28), GLASS: ((.011, .014, .016, 1), .05, .2),
              STEEL: ((.44, .47, .46, 1), .9, .32), BRASS: ((.42, .24, .08, 1), .88, .32),
              GLOW: ((.75, .71, .59, 1), 0, .25), STONE: ((.035, .037, .035, 1), 0, .42)}
    materials = {}
    for id_ in {id_ for mesh in meshes for id_ in mesh.material_ids}:
        mat = bpy.data.materials.new('RD_'+id_); mat.use_nodes = True
        color, metal, roughness = colors[records[id_]['materialNames'][0]]
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = color
        shader.inputs['Metallic'].default_value = metal
        shader.inputs['Roughness'].default_value = roughness
        materials[id_] = mat
    for mesh in meshes:
        data = bpy.data.meshes.new(mesh.id)
        data.from_pydata([tuple(v/1000 for v in p) for p in mesh.vertices], [], mesh.faces)
        data.update()
        for id_ in mesh.material_ids: data.materials.append(materials[id_])
        for index, (face, slot) in enumerate(zip(data.polygons, mesh.materials)):
            face.material_index = slot; face.use_smooth = index not in mesh.flat_faces
        bm = bmesh.new(); bm.from_mesh(data)
        bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(data); bm.free()
        # Source stone uses metric world UVs; the four tiny fills share that
        # scale instead of sampling one constant texel from the inherited map.
        uv = data.uv_layers.new(name='UVMap')
        for polygon in data.polygons:
            for loop_index in polygon.loop_indices:
                v = data.vertices[data.loops[loop_index].vertex_index].co
                plan_x = v.x+scene['sceneCenterMm']['x']/1000
                plan_y = v.y+scene['sceneCenterMm']['y']/1000
                if abs(polygon.normal.z) > .5:
                    uv.data[loop_index].uv = (plan_x, plan_y)
                else:
                    uv.data[loop_index].uv = (plan_y if abs(polygon.normal.x) > .5 else plan_x, v.z)
        obj = bpy.data.objects.new(mesh.id, data); bpy.context.collection.objects.link(obj)
        obj['source_ids'] = ','.join(mesh.source_ids); obj['visual_only'] = True
        if mesh.motion_id: obj['motion_source_id'] = mesh.motion_id
        obj.select_set(True)
    bpy.context.view_layer.update()
    bpy.ops.export_scene.gltf(filepath=str(output/GLB_NAME), export_format='GLB', use_selection=True,
                              export_yup=True, export_extras=True, export_animations=False, export_cameras=False, export_lights=False)
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(output/GLB_NAME))
    actual = {obj.name: obj for obj in bpy.context.scene.objects if obj.type == 'MESH'}
    require(set(actual) == {row['id'] for row in objects}, 'GLB object roundtrip differs')
    max_error = 0
    for row in objects:
        obj = actual[row['id']]; obj.data.transform(obj.matrix_world); obj.matrix_world = Matrix.Identity(4)
        measured = bounds([tuple(float(c)*1000 for c in vertex.co) for vertex in obj.data.vertices])
        error = max(abs(measured[k][i]-row['visualBoundsMm'][k][i]) for k in ('min', 'max') for i in range(3))
        require(error < .01, 'GLB coordinate roundtrip differs')
        require([mat.name.split('.')[0] for mat in obj.data.materials] == ['RD_'+id_ for id_ in row['materialSourceIds']],
                'GLB material slot roundtrip differs')
        max_error = max(max_error, error)
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'offline-geometry-validated',
              'generatedAt': datetime.now(timezone.utc).isoformat(), 'activeDesign': scene['activeDesign'],
              'sourceGeometry': str(geometry), 'sourceSceneSha256': sha(geometry/'scene.json'),
              'sourceManifestSha256': sha(geometry/'scene.json'), 'sourceObjSha256': sha(geometry/'dom-mm.obj'),
              'sourceDoorsSha256': sha(geometry/'doors.json'), 'generatorSha256': sha(__file__),
              'generatorDependencies': {str(HELPER.relative_to(ROOT)): sha(HELPER)},
              'glb': GLB_NAME, 'glbSha256': sha(output/GLB_NAME), 'blenderVersion': bpy.app.version_string,
              'sourceIds': sorted({id_ for mesh in meshes for id_ in mesh.source_ids}),
              'hiddenSourceIds': sorted(HIDE_IDS), 'referenceSourceIds': ['DOM_00759'],
              'objects': objects, 'triangles': sum(row['triangles'] for row in objects), 'roundtripErrorMm': max_error,
              'motionBindings': doors,
              'coordinateSystem': 'Source XYZ mm -> Blender XYZ m/Zup -> glTF m/Yup; Unreal X=x/10,Y=-y/10,Z=z/10.',
              'sourcePolicy': 'Retain original mesh/transforms/collision/tags. NoCollision on new meshes. Six moving visuals attach KEEP_WORLD as separate actors to motionSourceId. Source door bVisible remains true and hidden_in_game remains false; render_in_main_pass, render_in_depth_pass and lighting contribution are disabled. Four countertop patches are additive; source countertop remains unchanged.',
              'nativeImportVerified': False, 'visualQualityVerified': False,
              'limitations': ['Current source black-glass finish remains opaque/tinted; no claim of transmissive glass or a fully modeled internal drum.',
                              'The stationary drum liner is a shallow construction cue within the original 26 mm appliance-front envelope.',
                              'Dynamic attachments require native opening/closing and collision verification before acceptance.']}
    (output/'geometry-report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print('ROOM_DETAILS', json.dumps({'objects': len(objects), 'triangles': report['triangles'], 'roundtripErrorMm': max_error}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--geometry', required=True); parser.add_argument('--output', required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None)
    build(args.geometry, args.output)
