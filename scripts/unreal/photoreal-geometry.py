"""Visual-only C/B/B furniture/roof refinement; source collision stays authoritative.

Build with Blender --background --python-exit-code 1 --python <this file> --
  --geometry <validated geometry> --output <new detail directory>.

Native integration, after component material overrides: apply_geometry(output,
geometry). The existing map must already be loaded. This module never saves it.
It imports owned visual meshes and disables source rendering only; source mesh,
transform, collision and door components remain untouched.
"""
import argparse
import hashlib
import json
import math
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/photoreal-geometry.py'
PREFIX = '/Game/Brezi/Photoreal/Geometry'
TAG = 'BreziPhotorealGeometry'


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')


def recipe(record):
    """Semantic selection deliberately excludes doors, structure and light emitters."""
    if not record.get('enabled') or record.get('metadata', {}).get('doorMotion'):
        return None
    name = record['name'].lower()
    materials = ' '.join(record['materialNames']).lower()
    if any(word in name for word in ('navigačný', 'animované', 'krídlo', 'garážové', 'garage-door')):
        return None
    if record['group'] == 'Roof' and record['materialNames'] == ['real-roof-edge']:
        if name.startswith('hrebeňový profil '):
            return {'kind': 'folded-ridge', 'bevelMm': .7}
        if any(word in name for word in ('orezaný falc', 'žľab', 'okapová', 'strešná hrana', 'nárožný', 'hrebeňov', 'oplechovanie')):
            return {'kind': 'metal-bevel', 'bevelMm': .75}
    interior = name.startswith(('living-103-', 'kitchen-run'))
    lounge = name.startswith(('lounge pohovka', 'lounge ležadlo', 'záhradné kreslo', 'operadlo záhradného kresla'))
    if (interior or lounge) and any(word in materials for word in ('upholstery', 'fabric')):
        if any(word in name for word in ('sedák', 'vankúš', 'operadlo', 'výplň', 'opierka')) or name.startswith('lounge ležadlo'):
            return {'kind': 'upholstery', 'bevelMm': 18 if record['triangles'] <= 12 else 0,
                    'depressionMm': 4.0, 'foldMm': 1.4, 'pipingRadiusMm': .65}
        if record['triangles'] <= 12:
            return {'kind': 'soft-bevel', 'bevelMm': 12}
    if interior and any(word in materials for word in ('dub', 'living warm oak', 'living warm cabinet', 'kameň', 'living warm stone')):
        # Existing rounded plinths retain their authored form.
        if record['triangles'] < 512:
            return {'kind': 'furniture-bevel', 'bevelMm': 2 if 'kameň' in materials or 'stone' in materials else 2.5}
    if name.startswith('nízky stolík · doska'):
        return {'kind': 'furniture-bevel', 'bevelMm': 2.5}
    return None


def load_source(geometry):
    geometry = Path(geometry).resolve()
    scene = json.loads((geometry / 'scene.json').read_text())
    require(scene.get('activeDesign') == {'variant': 'C', 'livingLayout': 'B', 'heatingLayout': 'B'}, 'Only active C/B/B is supported')
    placement = scene['house']['placement']
    require(placement['streetSetbackMm'] == placement['eastSetbackMm'] == 3000, 'Setback contract changed')
    require(sha(geometry / 'dom-mm.obj') == scene['objSha256'], 'Source OBJ hash mismatch')
    return scene


def bounds(obj):
    import numpy as np
    points = np.asarray([tuple(v.co) for v in obj.data.vertices])
    return {'min': points.min(axis=0).tolist(), 'max': points.max(axis=0).tolist()}


def clean_mesh(obj):
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-7)
    # Weld exported face seams before beveling; keep all UV loop data intact.
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data)
    bm.free()
    obj.data.update()


def apply_bevel(obj, millimeters, smooth=False):
    import bpy
    bpy.context.view_layer.objects.active = obj
    modifier = obj.modifiers.new('Physical edge radius', 'BEVEL')
    modifier.width = millimeters / 1000
    modifier.segments = 4 if smooth else 3
    modifier.limit_method = 'ANGLE'
    modifier.angle_limit = math.radians(32)
    modifier.use_clamp_overlap = True
    modifier.harden_normals = True
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    if smooth:
        for face in obj.data.polygons:
            face.use_smooth = True
    else:
        modifier = obj.modifiers.new('Preserve broad planar highlights', 'WEIGHTED_NORMAL')
        modifier.keep_sharp = True
        modifier.weight = 50
        bpy.ops.object.modifier_apply(modifier=modifier.name)


def folded_ridge(obj):
    """Replace a rectangular visual ridge with a folded 1.2 mm crown in its envelope."""
    import bpy
    import numpy as np
    box = bounds(obj)
    lo, hi = np.array(box['min']), np.array(box['max'])
    length_axis = 0 if hi[0] - lo[0] > hi[1] - lo[1] else 1
    width_axis = 1 - length_axis
    center = (lo + hi) / 2
    half_width = (hi[width_axis] - lo[width_axis]) / 2
    # Crown, two folded flanges and short hem returns. All inside source bounds.
    outline = [(-half_width, lo[2] + .005), (-half_width + .004, lo[2] + .005),
               (0, hi[2]), (half_width - .004, lo[2] + .005), (half_width, lo[2] + .005),
               (half_width, lo[2] + .001), (half_width - .005, lo[2] + .001),
               (0, hi[2] - .0012), (-half_width + .005, lo[2] + .001), (-half_width, lo[2] + .001)]
    vertices = []
    for end in (lo[length_axis], hi[length_axis]):
        for w, z in outline:
            p = center.copy(); p[length_axis] = end; p[width_axis] += w; p[2] = z
            vertices.append(tuple(p))
    count = len(outline)
    faces = [tuple(reversed(range(count))), tuple(range(count, 2 * count))]
    faces.extend((i, (i + 1) % count, (i + 1) % count + count, i + count) for i in range(count))
    original = obj.data
    mesh = bpy.data.meshes.new(obj.name + '_folded')
    mesh.from_pydata(vertices, [], faces); mesh.update()
    for mat in original.materials:
        mesh.materials.append(mat)
    obj.data = mesh
    uv = mesh.uv_layers.new(name='UVMap')
    for loop in mesh.loops:
        p = mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (p[length_axis], p[width_axis])
    clean_mesh(obj)


def upholstery(obj, spec, identity):
    """Subdivide then depress actual mesh surfaces; retain the original support plane."""
    import bmesh
    import numpy as np
    from mathutils import Vector
    bm = bmesh.new(); bm.from_mesh(obj.data)
    # Imported rounded boxes contain only one long quad through their centre.
    # Subdivision creates enough real geometry for a restrained drape at 1–2 m.
    bmesh.ops.subdivide_edges(bm, edges=list(bm.edges), cuts=3, use_grid_fill=True)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    bm.to_mesh(obj.data); bm.free(); obj.data.update()
    points = np.asarray([tuple(v.co) for v in obj.data.vertices])
    center = points.mean(axis=0)
    _, eigenvectors = np.linalg.eigh(np.cov((points-center).T))
    # Columns are thin -> broad; PCA preserves the source tilted back cushions.
    frame = eigenvectors
    if np.linalg.det(frame) < 0:
        frame[:, 2] *= -1
    local = (points - center) @ frame
    midpoint = (local.min(axis=0) + local.max(axis=0)) / 2
    center += frame @ midpoint
    local -= midpoint
    half = np.max(np.abs(local), axis=0)
    phase = int(hashlib.sha256(identity.encode()).hexdigest()[:8], 16) / 0xffffffff * math.tau
    support_z = points[:, 2].min()
    max_displacement = 0
    for vertex, p in zip(obj.data.vertices, local):
        q = p / half
        a, b = q[1], q[2]
        envelope = max(0, (1-a*a)) * max(0, (1-b*b))
        normal_local = np.asarray(tuple(vertex.normal)) @ frame
        face_weight = abs(normal_local[0]) ** 6
        depression = spec['depressionMm'] / 1000 * math.exp(-((a-.07)**2/.4+(b+.12)**2/.7)) * envelope
        # Fine asymmetric folds radiate a short distance inward from the seam.
        fold = spec['foldMm']/1000 * (.5+.5*math.sin(23*a+2*math.sin(5*b)+phase))
        fold *= math.exp(-((abs(b)-.78)/.16)**2) * max(0, 1-a*a)
        amount = (depression + fold) * face_weight
        # Neither the contact/support plane nor outside corners move outward.
        support = min(1., max(0., (float(vertex.co.z)-support_z)/.02))
        amount *= support
        vertex.co -= vertex.normal * amount
        max_displacement = max(max_displacement, amount)
    for polygon in obj.data.polygons:
        polygon.use_smooth = True
    obj.data.update()
    return center, frame, half, max_displacement


def piping_mesh(obj, frame_data, radius):
    """Piping follows an actual deformed-mesh equator; no guessed rectangular path."""
    import bpy
    import numpy as np
    from mathutils import Vector
    center, frame, half, _ = frame_data
    # A non-grid slice avoids ambiguous triangle edges lying exactly in-plane.
    slice_center = center + frame[:, 0] * half[0] * .071
    obj.data.calc_loop_triangles()
    segments = []
    epsilon = 1e-8
    for triangle in obj.data.loop_triangles:
        points = [np.asarray(tuple(obj.data.vertices[i].co)) for i in triangle.vertices]
        signed = [float((p-slice_center) @ frame[:, 0]) for p in points]
        hits = []
        for j in range(3):
            a, b = j, (j+1)%3
            if abs(signed[a]) < epsilon:
                hits.append(points[a])
            elif signed[a] * signed[b] < 0:
                hits.append(points[a] + (points[b]-points[a]) * signed[a]/(signed[a]-signed[b]))
        unique = {tuple(np.round(p, 7)): p for p in hits}
        if len(unique) == 2:
            segments.append(tuple(unique.values()))
    require(segments, 'No upholstery seam section: ' + obj.name)
    adjacency, coords = {}, {}
    for a, b in segments:
        ka, kb = tuple(np.round(a, 6)), tuple(np.round(b, 6))
        if ka == kb: continue
        coords[ka], coords[kb] = a, b
        adjacency.setdefault(ka, set()).add(kb); adjacency.setdefault(kb, set()).add(ka)
    require(all(len(v) == 2 for v in adjacency.values()), 'Seam section must be one closed manifold contour: ' + obj.name)
    start = min(adjacency); chain = [start]; previous = None; current = start
    while True:
        choices = adjacency[current] - ({previous} if previous else set())
        following = sorted(choices)[0]
        if following == start: break
        require(following not in chain, 'Self-intersecting seam contour')
        chain.append(following); previous, current = current, following
    require(len(chain) == len(adjacency), 'Disconnected seam section')
    # Six-sided 1.3 mm cord; center is embedded half its radius in the cloth.
    vertices, faces = [], []
    points = [coords[key] for key in chain]
    axis = frame[:, 0]
    for index, point in enumerate(points):
        tangent = points[(index+1)%len(points)]-points[(index-1)%len(points)]
        tangent /= np.linalg.norm(tangent)
        outward = np.cross(tangent, axis)
        if np.dot(outward, point-center) < 0: outward *= -1
        outward /= np.linalg.norm(outward)
        for j in range(6):
            angle = j * math.tau / 6
            vertices.append(tuple(point + outward*(radius*.3+radius*math.cos(angle)) + axis*(radius*math.sin(angle))))
    for i in range(len(points)):
        for j in range(6):
            faces.append((i*6+j, i*6+(j+1)%6, ((i+1)%len(points))*6+(j+1)%6, ((i+1)%len(points))*6+j))
    mesh = bpy.data.meshes.new(obj.name + '_seam'); mesh.from_pydata(vertices, [], faces); mesh.update()
    seam = bpy.data.objects.new(obj.name + '_seam', mesh); bpy.context.collection.objects.link(seam)
    for mat in obj.data.materials: mesh.materials.append(mat)
    uv = mesh.uv_layers.new(name='UVMap')
    for loop in mesh.loops:
        p = mesh.vertices[loop.vertex_index].co
        uv.data[loop.index].uv = (float((np.array(p)-center) @ frame[:, 1]), float((np.array(p)-center) @ frame[:, 2]))
    for polygon in mesh.polygons: polygon.use_smooth = True
    bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); seam.select_set(True)
    bpy.context.view_layer.objects.active = obj; bpy.ops.object.join()
    return len(points)


def build(geometry, output):
    import bpy
    from mathutils import Matrix
    geometry, output = Path(geometry).resolve(), Path(output).resolve()
    require(output.is_relative_to(ROOT / 'output/unreal'), 'Output must stay in output/unreal')
    require(not (output / 'photoreal-details.glb').exists(), 'Use a new directory; detail builds are immutable')
    scene = load_source(geometry)
    selected = {r['id']: (r, recipe(r)) for r in scene['objects'] if recipe(r)}
    output.mkdir(parents=True, exist_ok=True)
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    bpy.ops.wm.obj_import(filepath=str(geometry / 'dom-mm.obj'), forward_axis='Y', up_axis='Z',
                          global_scale=.001, use_split_objects=True, use_split_groups=False)
    records = []
    for obj in list(bpy.context.scene.objects):
        if obj.name not in selected:
            bpy.data.objects.remove(obj, do_unlink=True); continue
        rec, spec = selected[obj.name]
        obj.data.transform(obj.matrix_world); obj.matrix_world = Matrix.Identity(4)
        initial = bounds(obj)
        clean_mesh(obj)
        obj.name = 'PH_' + rec['id']; obj.data.name = obj.name
        if spec['kind'] == 'folded-ridge': folded_ridge(obj)
        if spec.get('bevelMm'): apply_bevel(obj, spec['bevelMm'], spec['kind'] in ('upholstery', 'soft-bevel'))
        detail = {}
        if spec['kind'] == 'upholstery':
            frame = upholstery(obj, spec, rec['name'])
            detail = {'maxDeformationMm': frame[3]*1000,
                      'pipingContourVertices': piping_mesh(obj, frame, spec['pipingRadiusMm']/1000)}
        result = bounds(obj)
        outward = max([0.] + [(initial['min'][i]-result['min'][i])*1000 for i in range(3)]
                       + [(result['max'][i]-initial['max'][i])*1000 for i in range(3)])
        require(outward <= 1.1, 'Refinement exceeds visual envelope: ' + rec['id'])
        require({m.name for m in obj.data.materials} == set(rec['materialSlots']), 'Source material slots changed')
        obj['photoreal_source_id'] = rec['id']; obj['source_name'] = rec['name']; obj['visual_only'] = True
        obj.data.calc_loop_triangles()
        records.append({'id': obj.name, 'sourceId': rec['id'], 'sourceName': rec['name'],
                        'materialSlots': [m.name for m in obj.data.materials], 'recipe': spec,
                        'sourceBoundsMm': rec['boundsMm'], 'visualBoundsMm': {k: [v*1000 for v in values] for k,values in result.items()},
                        'outwardEnvelopeMm': outward, 'triangles': len(obj.data.loop_triangles), **detail})
    require(len(records) == len(selected), 'Missing selected source geometry')
    bpy.context.view_layer.update()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(output / 'photoreal-details.glb'), export_format='GLB',
                              use_selection=True, export_yup=True, export_extras=True,
                              export_animations=False, export_cameras=False, export_lights=False)
    # Independent exported-container roundtrip validates coordinates/material names.
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    bpy.ops.import_scene.gltf(filepath=str(output / 'photoreal-details.glb'))
    actual = {o.name: o for o in bpy.context.scene.objects if o.type == 'MESH'}
    require(set(actual) == {r['id'] for r in records}, 'GLB roundtrip identities differ')
    max_error = 0
    for r in records:
        obj = actual[r['id']]; obj.data.transform(obj.matrix_world); obj.matrix_world = Matrix.Identity(4)
        measured = bounds(obj)
        error = max(abs(measured[k][i]*1000-r['visualBoundsMm'][k][i]) for k in ('min','max') for i in range(3))
        require(error < .05, 'GLB roundtrip coordinate error: ' + r['id'])
        max_error = max(max_error, error)
    report = {'schemaVersion': 1, 'owner': OWNER, 'status': 'offline-geometry-validated',
              'generatedAt': datetime.now(timezone.utc).isoformat(), 'activeDesign': scene['activeDesign'],
              'sourceGeometry': str(geometry), 'sourceSceneSha256': sha(geometry/'scene.json'),
              'sourceObjSha256': sha(geometry/'dom-mm.obj'), 'generatorSha256': sha(__file__),
              'glbSha256': sha(output/'photoreal-details.glb'), 'blenderVersion': bpy.app.version_string,
              'objects': sorted(records, key=lambda r:r['id']), 'counts': dict(Counter(r['recipe']['kind'] for r in records)),
              'triangles': sum(r['triangles'] for r in records), 'roundtripErrorMm': max_error,
              'nativeImportVerified': False, 'visualQualityVerified': False,
              'collisionPolicy': 'Original source components retained; visual-only imported overlays have NoCollision.',
              'limitations': ['Geometric detail is authored from current source, not a scanned furniture asset.',
                              'Offline geometry validation does not establish native render or visual acceptance.']}
    write(output/'geometry-report.json', report)
    print('PHOTOREAL_GEOMETRY', json.dumps({k:report[k] for k in ('counts','triangles','roundtripErrorMm')}))
    return report


def apply_geometry(output, geometry):
    """Native UE entrypoint. Materials must already be assigned on source components."""
    import unreal as u
    output, geometry = Path(output).resolve(), Path(geometry).resolve()
    report = json.loads((output/'geometry-report.json').read_text())
    require(report['owner'] == OWNER and report['sourceSceneSha256'] == sha(geometry/'scene.json')
            and report['sourceObjSha256'] == sha(geometry/'dom-mm.obj')
            and report['glbSha256'] == sha(output/'photoreal-details.glb'), 'Detail source pins differ')
    scene = load_source(geometry); records = {r['id']:r for r in scene['objects']}
    actor_system = u.get_editor_subsystem(u.EditorActorSubsystem)
    level_system = u.get_editor_subsystem(u.LevelEditorSubsystem)
    sources = {}
    for actor in actor_system.get_all_level_actors():
        require(TAG not in [str(t) for t in actor.tags], 'Geometry detail already exists; use fresh cloned map')
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = component.get_editor_property('static_mesh')
            if not mesh: continue
            id_ = str(u.EditorAssetLibrary.get_metadata_tag(mesh, 'source_object_id'))
            if id_ in {r['sourceId'] for r in report['objects']}:
                require(id_ not in sources, 'Ambiguous source component: ' + id_)
                require(not records[id_].get('metadata',{}).get('doorMotion'), 'Door geometry is protected')
                require(component.get_editor_property('mobility') == u.ComponentMobility.STATIC, 'Only static furniture/roof supported')
                sources[id_] = (actor, component, mesh, component.get_collision_enabled(), component.get_world_transform())
    require(set(sources) == {r['sourceId'] for r in report['objects']}, 'Missing native source furniture/roof')
    pipelines = []
    for source, name in [('GLTFSceneAssets','Assets'), ('GLTFMaterials','Materials'), ('LevelActors','Level')]:
        asset = u.EditorAssetLibrary.duplicate_asset('/Game/Brezi/Pipeline/'+source, PREFIX+'/Pipeline/'+name)
        require(asset, 'Cannot create detail import pipeline')
        pipelines.append(asset)
    mesh_pipeline = pipelines[0].get_editor_property('mesh_pipeline')
    for name,value in [('combine_static_meshes_behavior',u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE),
                       ('collision',False),('build_nanite',False),('generate_lightmap_u_vs',False)]:
        mesh_pipeline.set_editor_property(name,value)
    pipelines[2].set_editor_property('scene_hierarchy_type',u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
    params = u.ImportAssetParameters(); params.set_editor_property('is_automated',True)
    params.set_editor_property('replace_existing',False); params.set_editor_property('force_show_dialog',False)
    params.set_editor_property('override_pipelines',[u.SoftObjectPath(p.get_path_name()) for p in pipelines])
    params.set_editor_property('import_level',level_system.get_current_level())
    before = {a.get_path_name() for a in actor_system.get_all_level_actors()}
    manager = u.InterchangeManager.get_interchange_manager_scripted()
    require(manager.import_scene(PREFIX,manager.create_source_data(str(output/'photoreal-details.glb')),params), 'Detail Interchange import failed')
    selected = {r['id']:r for r in report['objects']}; imported = {}
    for actor in actor_system.get_all_level_actors():
        if actor.get_path_name() in before: continue
        actor.tags = [*actor.tags, u.Name(TAG)]; actor.set_folder_path('Brezi/Photoreal/Geometry')
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = component.get_editor_property('static_mesh')
            require(mesh, 'Imported detail component lacks mesh')
            matches = set(re.findall(r'PH_DOM_\d+', actor.get_actor_label()+' '+mesh.get_name())) & set(selected)
            require(len(matches)==1, 'Cannot resolve detail identity: '+actor.get_actor_label())
            id_ = matches.pop(); rec = selected[id_]
            require(id_ not in imported, 'Duplicate detail mesh')
            source_actor, source, source_mesh, collision, transform = sources[rec['sourceId']]
            original_slots = records[rec['sourceId']]['materialSlots']
            require(component.get_num_materials()==len(rec['materialSlots']), 'Imported material slot count changed')
            for index, slot in enumerate(rec['materialSlots']):
                material = source.get_material(original_slots.index(slot))
                require(material, 'Source material missing: '+rec['sourceId'])
                component.set_material(index,material)
            component.set_mobility(u.ComponentMobility.STATIC)
            component.set_collision_profile_name('NoCollision'); component.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
            component.set_editor_property('cast_shadow',True)
            # Rendering flags alone are changed on the original component. Its
            # query/physics support and source triangles remain in place.
            source.set_visibility(False,False); source.set_hidden_in_game(True,False)
            for prop in ('cast_shadow', 'cast_hidden_shadow', 'affect_distance_field_lighting',
                         'affect_dynamic_indirect_lighting', 'affect_indirect_lighting_while_hidden', 'visible_in_ray_tracing'):
                source.set_editor_property(prop,False)
            require(source.get_editor_property('static_mesh')==source_mesh and source.get_collision_enabled()==collision,
                    'Original source mesh/collision changed')
            require(component.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION, 'Visual detail gained collision')
            actor.set_actor_label(id_+' · '+rec['sourceName'])
            u.EditorAssetLibrary.set_metadata_tag(mesh,'photoreal_source_id',rec['sourceId'])
            imported[id_] = {'sourceId':rec['sourceId'],'mesh':mesh.get_path_name(),'actor':actor.get_path_name(),
                             'sourceMesh':source_mesh.get_path_name(),
                             'sourceCollision':str(collision),'materials':[component.get_material(i).get_path_name() for i in range(component.get_num_materials())]}
            require(u.EditorAssetLibrary.save_loaded_asset(mesh),'Cannot save visual detail mesh')
    require(set(imported)==set(selected), 'Imported geometry detail membership differs')
    for pipeline in pipelines: u.EditorAssetLibrary.save_loaded_asset(pipeline)
    return {'owner':OWNER,'geometryReportSha256':sha(output/'geometry-report.json'),'objects':imported,
            'sourceCollisionPreserved':True,'mapSavedReloaded':False,'visualQualityVerified':False}


def verify_geometry(output, geometry, report):
    """Read back after the caller saves/reloads; geometry and bindings, not appearance."""
    import unreal as u
    output, geometry = Path(output).resolve(), Path(geometry).resolve()
    require(report['owner']==OWNER and report['geometryReportSha256']==sha(output/'geometry-report.json'), 'Geometry report pin differs')
    offline = json.loads((output/'geometry-report.json').read_text())
    require(offline['sourceSceneSha256']==sha(geometry/'scene.json'), 'Geometry source changed')
    records = {r['id']:r for r in offline['objects']}
    actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    components = {a.get_path_name():a.get_components_by_class(u.StaticMeshComponent) for a in actors}
    source_components = {}
    for actor in actors:
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = component.get_editor_property('static_mesh')
            if not mesh: continue
            id_ = str(u.EditorAssetLibrary.get_metadata_tag(mesh,'source_object_id'))
            if id_ in {r['sourceId'] for r in offline['objects']}:
                require(id_ not in source_components, 'Duplicate source component on reload')
                source_components[id_] = component
    max_error = 0.
    for id_, entry in report['objects'].items():
        require(entry['actor'] in components, 'Detail actor missing after reload: '+id_)
        matches = [c for c in components[entry['actor']] if c.get_editor_property('static_mesh')
                   and c.get_editor_property('static_mesh').get_path_name()==entry['mesh']]
        require(len(matches)==1,'Detail mesh missing after reload: '+id_)
        component = matches[0]; source = source_components[entry['sourceId']]
        require(component.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION, 'Detail collision was enabled')
        require(component.is_visible() and not component.get_editor_property('hidden_in_game'), 'Detail is invisible')
        require(not source.is_visible() and source.get_editor_property('hidden_in_game'), 'Original rendering was not suppressed')
        require(str(source.get_collision_enabled())==entry['sourceCollision']
                and source.get_editor_property('static_mesh').get_path_name()==entry['sourceMesh'], 'Original collision/mesh changed')
        for prop in ('cast_shadow','cast_hidden_shadow','affect_distance_field_lighting',
                     'affect_dynamic_indirect_lighting','affect_indirect_lighting_while_hidden','visible_in_ray_tracing'):
            require(not source.get_editor_property(prop),'Hidden source retained lighting contribution: '+prop)
        require([component.get_material(i).get_path_name() for i in range(component.get_num_materials())]==entry['materials'],
                'Detail material binding changed on reload')
        origin, extent, _ = u.SystemLibrary.get_component_bounds(component)
        lo, hi = origin-extent, origin+extent
        actual = {'min':[float(lo.x),float(lo.y),float(lo.z)],'max':[float(hi.x),float(hi.y),float(hi.z)]}
        b = records[id_]['visualBoundsMm']
        expected = {'min':[b['min'][0]/10,-b['max'][1]/10,b['min'][2]/10],
                    'max':[b['max'][0]/10,-b['min'][1]/10,b['max'][2]/10]}
        error = max(abs(actual[key][i]-expected[key][i]) for key in ('min','max') for i in range(3))
        require(math.isfinite(error) and error<.05, 'Native overlay bounds differ: '+id_)
        max_error = max(max_error,error)
    report.update(mapSavedReloaded=True,maxNativeBoundsErrorCm=max_error,objectsVerified=len(report['objects']),
                  hiddenSourceLightingDisabled=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--geometry',required=True); parser.add_argument('--output',required=True)
    args = parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else None)
    build(args.geometry,args.output)
