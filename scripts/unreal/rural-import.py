"""Additive rural parcel context after a verified photoreal stage.

Only the saved map and new Rural20260923 packages may change. Imported source
geometry/collision stays authoritative; visual road clones retain exact topology.
The JSON coordinates are Unreal centimetres, including explicitly authored LODs.
"""
from collections import Counter
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import struct
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/rural-import.py'
MAP = '/Game/Brezi/Maps/Brezi'
PREFIX = '/Game/Brezi/Rural20260923'
TAG = 'BreziRural20260923'
EXTENSIONS = {'.uasset', '.uexp', '.ubulk', '.umap'}
SCREENS = [1., .18, .055]
TREE_SCREENS = [1., .45, .12]


def lod_screens(record):
    # Large crowns must reduce earlier than 60cm weeds. The authored tree LODs
    # retain leaf area, so window views keep the canopy without near-mesh cost.
    return TREE_SCREENS if record['material'] in ('leaf','bark') else SCREENS


def require(ok, message):
    if not ok: raise RuntimeError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_text())
def relative(path): return str(Path(path).resolve().relative_to(ROOT))
def now(): return datetime.now(timezone.utc).isoformat()
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
def write(path, value): Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n')
def vec(value, axes='xyz'): return [float(getattr(value, key)) for key in axes]
def transform(value): return {key: vec(getattr(value, key), axes) for key, axes in [('translation','xyz'), ('rotation','xyzw'), ('scale3d','xyz')]}


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts/unreal'/filename)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def inventory(content):
    return {relative(p): sha(p) for p in sorted(content.rglob('*')) if p.is_file() and p.suffix in EXTENSIONS}


def validate_changes(before, after, content):
    map_file = relative(content/'Maps/Brezi.umap')
    require(set(before) <= set(after), 'Removed a protected baseline asset')
    for name, value in before.items():
        require(name == map_file or after[name] == value, 'Protected package changed: '+name)
    for name in after.keys()-before.keys():
        require((ROOT/name).is_relative_to(content/'Rural20260923'), 'New asset outside Rural20260923: '+name)


def restore(output):
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT/'output/unreal'), 'Output outside workspace')
    state = read(output/'rural-checkpoint/state.json')
    require(state['status'] == 'failed-recoverable', 'No recoverable recorded rural failure')
    try: os.kill(state['nativeProcessId'], 0)
    except ProcessLookupError: pass
    else: raise RuntimeError('Native process still running')
    content = output/'Project/BreziTwin/Content/Brezi'
    current = inventory(content)
    require(current == state['failedInventory'], 'Assets changed after failure')
    validate_changes(state['baselineInventory'], current, content)
    backup = output/'rural-checkpoint/Brezi.umap'
    require(sha(backup) == state['baselineInventory'][relative(content/'Maps/Brezi.umap')], 'Backup differs')
    # Validate every restore input before creating history or changing the map.
    # A drifted runtime sun file must leave the failed attempt fully untouched.
    viewpoints_restore = None
    if 'baselineViewpointsSha256' in state:
        staged=output/'Project/BreziTwin/Content/Data/viewpoints.json'; saved=output/'rural-checkpoint/viewpoints.json'
        require(sha(staged)==state['failedViewpointsSha256'] and sha(saved)==state['baselineViewpointsSha256'], 'Staged viewpoints drift after failure')
        viewpoints_restore = (saved, staged)
    history = output/'rural-history'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    history.mkdir(parents=True)
    for name in ['rural-import-report.json', 'rural-import.log', 'rural-import.log.json', 'rural-checkpoint/state.json']:
        path = output/name
        if path.is_file(): shutil.copy2(path, history/path.name)
    shutil.copy2(backup, content/'Maps/Brezi.umap')
    if viewpoints_restore is not None:
        shutil.copy2(*viewpoints_restore)
    for name in current.keys()-state['baselineInventory'].keys(): (ROOT/name).unlink()
    require(inventory(content) == state['baselineInventory'], 'Restore was not exact')
    state['status'] = 'restored'; write(output/'rural-checkpoint/state.json', state)


def validate_plan(plan, scene):
    require(scene['activeDesign'] == {'variant':'C', 'heatingLayout':'B', 'livingLayout':'B'}, 'C/B/B required')
    placement = scene['house']['placement']
    require(placement['streetSetbackMm'] == placement['eastSetbackMm'] == 3000, 'Setbacks changed')
    ids = [row['id'] for row in plan['meshes']]
    require(len(ids) == len(set(ids)) and ids, 'Duplicate/empty rural mesh identities')
    require(len(plan['groups']) == len({g['id'] for g in plan['groups']}), 'Duplicate group identity')
    for record in plan['meshes']:
        require(record['id'].replace('_','').isalnum(), 'Unsafe mesh identity')
        for level in [record, *record.get('lods', [])]:
            points, indices = level['verticesCm'], level['indices']
            require(points and indices and len(indices)%3 == 0, 'Empty/invalid mesh: '+record['id'])
            require(all(len(p)==3 and all(math.isfinite(v) for v in p) for p in points), 'Nonfinite mesh coordinates')
            require(all(isinstance(i,int) and 0<=i<len(points) for i in indices), 'Mesh index out of bounds')
            require(len(level.get('uvs', points)) == len(points), 'UV count differs')
    by_id = {r['id']:r for r in plan['meshes']}
    for group in plan['groups']:
        require(group['meshId'] in by_id and group['instances'], 'Missing/empty group mesh')
        require(by_id[group['meshId']]['material'] not in ('drygrass','weed','leaf','bark') or len(by_id[group['meshId']].get('lods',[])) == 2, 'Every rural vegetation HISM needs three explicit LODs')
        require(0 <= group['cullStartCm'] < group['cullEndCm'] <= 150000, 'Unbounded rural HISM culling')
        for row in group['instances']:
            require(len(row['positionCm'])==len(row['scale'])==3 and all(math.isfinite(v) for v in [*row['positionCm'], *row['scale'], row['yawDeg']]) and min(row['scale'])>0, 'Invalid rural instance')
    records = {r['id']:r for r in scene['objects']}
    replaced = [r['sourceId'] for r in plan['replacementMaterials']]
    hidden = plan['hideSourceIds']
    require(len(replaced)==len(set(replaced)) and len(hidden)==len(set(hidden)), 'Duplicate source override')
    require(not set(replaced)&set(hidden), 'Cannot hide and replace same source')
    for identity in set(replaced)|set(hidden):
        row = records.get(identity)
        require(row and row['enabled'], 'Missing source context object: '+identity)
        replacement = next((r for r in plan['replacementMaterials'] if r['sourceId']==identity),None)
        legacy_hedge = (row['sourceId'].startswith('Zadná hranica · ')
                        and row['materialNames'] in [['real-hedge-dark'],['real-hedge-mid'],['real-hedge-light']]
                        and row.get('metadata',{}).get('entityId')=='SITE-FENCE'
                        and row.get('metadata',{}).get('babylonCheckCollisions') is False)
        require((replacement and replacement.get('semanticId')==row['sourceId'] and replacement['material'] in ('road','curb','field')) or (identity in hidden and 'hlinená krajnica' in row['sourceId']) or (identity in hidden and legacy_hedge) or (identity in hidden and row['sourceId'].startswith('Riedka náletová vegetácia krajnice ') and row['group']=='Landscape' and row['materialNames']==['real-plant-grass'] and row['triangles']==2 and row['metadata'].get('babylonCheckCollisions') is False), 'Unreviewed source context semantic: '+identity)
        require(not row.get('metadata',{}).get('doorMotion'), 'Door is protected')
    require(plan.get('managedLawnKeepPolygonsCm'), 'Explicit managed lawn domain required')


def write_glb(path, plan):
    """One exact cm->m/axis conversion; no dependency on a modelling application."""
    binary = bytearray(); accessors, views, meshes, nodes = [], [], [], []
    def accessor(values, kind, component=5126, target=34962):
        flat = [v for row in values for v in (row if isinstance(row,(tuple,list)) else [row])]
        while len(binary)%4: binary.append(0)
        start = len(binary); binary.extend(struct.pack('<'+('f' if component==5126 else 'I')*len(flat), *flat))
        views.append({'buffer':0,'byteOffset':start,'byteLength':len(binary)-start,'target':target})
        rec = {'bufferView':len(views)-1,'componentType':component,'count':len(values),'type':kind}
        if kind=='VEC3': rec.update(min=[min(p[i] for p in values) for i in range(3)],max=[max(p[i] for p in values) for i in range(3)])
        accessors.append(rec); return len(accessors)-1
    for record in plan['meshes']:
        for lod, level in enumerate([record, *record.get('lods',[])]):
            points, indices = level['verticesCm'], level['indices']
            normals = [[0.,0.,0.] for _ in points]
            for n in range(0,len(indices),3):
                a,b,c = (points[i] for i in indices[n:n+3]); ab=[b[i]-a[i] for i in range(3)]; ac=[c[i]-a[i] for i in range(3)]
                normal = [ac[1]*ab[2]-ac[2]*ab[1], ac[2]*ab[0]-ac[0]*ab[2], ac[0]*ab[1]-ac[1]*ab[0]]
                for index in indices[n:n+3]: normals[index] = [normals[index][i]+normal[i] for i in range(3)]
            normals = [[n[0]/(math.sqrt(sum(v*v for v in n)) or 1), n[2]/(math.sqrt(sum(v*v for v in n)) or 1), n[1]/(math.sqrt(sum(v*v for v in n)) or 1)] for n in normals]
            positions = [[x/100,z/100,y/100] for x,y,z in points]
            uv = level.get('uvs', [[x/100,y/100] for x,y,_ in points])
            attrs = {'POSITION':accessor(positions,'VEC3'),'NORMAL':accessor(normals,'VEC3'),'TEXCOORD_0':accessor(uv,'VEC2')}
            identity = record['id']+'_LOD'+str(lod)
            meshes.append({'name':identity,'primitives':[{'attributes':attrs,'indices':accessor(indices,'SCALAR',5125,34963),'material':0}]})
            nodes.append({'name':identity,'mesh':len(meshes)-1})
    document = {'asset':{'version':'2.0','generator':OWNER},'scene':0,'scenes':[{'nodes':list(range(len(nodes)))}],
                'nodes':nodes,'meshes':meshes,'accessors':accessors,'bufferViews':views,'buffers':[{'byteLength':len(binary)}],
                'materials':[{'name':'RuralPlaceholder','doubleSided':True,'pbrMetallicRoughness':{'baseColorFactor':[.3,.3,.2,1],'metallicFactor':0,'roughnessFactor':.8}}]}
    js = json.dumps(document,separators=(',',':')).encode(); js += b' '*((-len(js))%4); binary += b'\0'*((-len(binary))%4)
    Path(path).write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary)


def source_components(u, ids):
    result = {}
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        matches = set(map(str,actor.get_editor_property('tags'))) & ids
        if not matches or actor.actor_has_tag('BreziWalkSupportProxy'): continue
        require(len(matches)==1, 'Ambiguous source context actor')
        identity = next(iter(matches))
        candidates = [c for c in actor.get_components_by_class(u.StaticMeshComponent) if c.get_editor_property('static_mesh') and str(u.EditorAssetLibrary.get_metadata_tag(c.get_editor_property('static_mesh'),'source_object_id')) == identity]
        require(identity not in result and len(candidates)==1, 'Ambiguous source context component: '+identity)
        result[identity] = candidates[0]
    require(set(result)==ids, 'Missing source context components: '+repr(ids-set(result)))
    return result


def witness(u):
    result = {}
    for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if a.actor_has_tag(TAG): continue
        for c in a.get_components_by_class(u.StaticMeshComponent):
            mesh = c.get_editor_property('static_mesh')
            if not mesh: continue
            result[a.get_path_name()+'/'+c.get_name()] = {
                'mesh':mesh.get_path_name(),'transform':transform(c.get_world_transform()),'actorTransform':transform(a.get_actor_transform()),
                'collision':str(c.get_collision_enabled()),'profile':str(c.get_collision_profile_name()),
                'pawn':str(c.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN)),
                'visible':bool(c.is_visible()),'hiddenInGame':bool(c.get_editor_property('hidden_in_game')),
                'actorHidden':bool(a.get_editor_property('hidden')),
                'materials':[c.get_material(i).get_path_name() if c.get_material(i) else None for i in range(c.get_num_materials())],
                'instances':c.get_instance_count() if isinstance(c,u.InstancedStaticMeshComponent) else None,
                **{p:bool(c.get_editor_property(p)) for p in ['cast_shadow','cast_hidden_shadow','affect_distance_field_lighting','affect_dynamic_indirect_lighting','affect_indirect_lighting_while_hidden','visible_in_ray_tracing']}}
    return result


def set_nanite(u, mesh, enabled):
    settings = mesh.get_editor_property('nanite_settings'); settings.set_editor_property('enabled',enabled)
    settings.set_editor_property('fallback_target',u.NaniteFallbackTarget.PERCENT_TRIANGLES)
    settings.set_editor_property('fallback_percent_triangles',1.); settings.set_editor_property('fallback_relative_error',0.)
    mesh.set_editor_property('nanite_settings',settings)
    require(bool(mesh.get_editor_property('nanite_settings').get_editor_property('enabled'))==enabled, 'Nanite setting not applied')


def apply_source(u, plan, materials):
    targets = source_components(u,set(plan['hideSourceIds'])|{r['sourceId'] for r in plan['replacementMaterials']})
    edits = {}
    for row in plan['replacementMaterials']:
        identity = row['sourceId']; c = targets[identity]; mesh = c.get_editor_property('static_mesh')
        require(c.get_num_materials()==1, 'Review multi-material context override: '+identity)
        original = mesh.get_path_name()
        if row.get('nanite') and not mesh.get_editor_property('nanite_settings').get_editor_property('enabled'):
            mesh = u.EditorAssetLibrary.duplicate_asset(original,PREFIX+'/SourceClones/'+identity)
            require(mesh, 'Cannot duplicate source road/curb for Nanite')
            # UE duplicate_asset does not carry package metadata on this build.
            # Keep the same source identity on the exact geometry clone.
            u.EditorAssetLibrary.set_metadata_tag(mesh,'source_object_id',identity)
            u.EditorAssetLibrary.set_metadata_tag(mesh,'BreziGeneratedBy',OWNER)
            set_nanite(u,mesh,True); c.set_static_mesh(mesh)
            require(u.EditorAssetLibrary.save_loaded_asset(mesh,False), 'Cannot save Nanite clone')
        c.set_material(0,materials[row['material']])
        if row.get('nanite'): c.set_editor_property('disallow_nanite',False)
        edits[identity] = {'component':c.get_owner().get_path_name()+'/'+c.get_name(),'sourceMesh':original,
                           'mesh':mesh.get_path_name(),'material':materials[row['material']].get_path_name(),
                           'nanite':bool(mesh.get_editor_property('nanite_settings').get_editor_property('enabled')),'action':'replace-material'}
    for identity in plan['hideSourceIds']:
        c=targets[identity]
        c.set_visibility(False,False); c.set_hidden_in_game(True,False)
        for prop in ['cast_shadow','cast_hidden_shadow','affect_distance_field_lighting','affect_dynamic_indirect_lighting','affect_indirect_lighting_while_hidden','visible_in_ray_tracing']:
            c.set_editor_property(prop,False)
        edits[identity]={'component':c.get_owner().get_path_name()+'/'+c.get_name(),'action':'hide-placeholder','collisionPreserved':True}
    return edits


def inside(point, polygon):
    result=False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        if (a[1]>point[1])!=(b[1]>point[1]) and point[0]<(b[0]-a[0])*(point[1]-a[1])/(b[1]-a[1])+a[0]: result=not result
    return result


def instance_value(c, i):
    value=c.get_instance_transform(i,False)
    if isinstance(value,tuple):
        require(value[0] is True,'Cannot read HISM instance'); value=value[1]
    return value


def trim_lawn(u, plan):
    groups={}; polygons=plan['managedLawnKeepPolygonsCm']
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        if not actor.actor_has_tag('BreziPhotorealLawn'): continue
        c=actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        require(c, 'Managed lawn HISM missing')
        old=c.get_instance_count(); keep=[]
        for i in range(old):
            value=instance_value(c,i)
            if any(inside(vec(value.translation)[:2],p) for p in polygons): keep.append(value)
        require(keep, 'Rural domain would remove entire managed lawn group')
        c.clear_instances(); inserted=list(c.add_instances(keep,True,False,False))
        require(inserted==list(range(len(keep))), 'Managed lawn insertion changed')
        actor.synchronize_instance_bounds()
        # HISM stores float32 matrices, and GetInstanceTransform decomposes
        # those matrices. Verify every re-added source transform with the same
        # established native lawn tolerances before pinning its serialized form.
        canonical=[]; position_error=scale_error=rotation_error=0.
        for i,wanted_value in enumerate(keep):
            actual=transform(instance_value(c,i)); wanted=transform(wanted_value)
            pe=max(abs(a-b) for a,b in zip(actual['translation'],wanted['translation']))
            se=max(abs(a-b) for a,b in zip(actual['scale3d'],wanted['scale3d']))
            qe=min(max(abs(a-sign*b) for a,b in zip(actual['rotation'],wanted['rotation'])) for sign in (1,-1))
            require(pe<.002 and se<2e-6 and qe<2e-5, 'Managed lawn re-add changed source instance membership/transform')
            canonical.append(actual); position_error=max(position_error,pe); scale_error=max(scale_error,se); rotation_error=max(rotation_error,qe)
        groups[actor.get_path_name()]={'component':actor.get_path_name()+'/'+c.get_name(),'before':old,'kept':len(keep),'removed':old-len(keep),
                                      'transformsSha256':digest(canonical),'originalSelectedTransformsSha256':digest([transform(v) for v in keep]),
                                      'sourceInstanceOrderPreserved':True,'maximumReinsertPositionErrorCm':position_error,
                                      'maximumReinsertScaleError':scale_error,'maximumReinsertQuaternionError':rotation_error}
    return {'groups':groups,'keepPolygonsCm':polygons,'removed':sum(g['removed'] for g in groups.values()),'retained':sum(g['kept'] for g in groups.values())}


def new_component_policy(u, c):
    c.set_mobility(u.ComponentMobility.STATIC); c.set_collision_profile_name('NoCollision'); c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    c.set_editor_property('can_ever_affect_navigation',False); c.set_editor_property('generate_overlap_events',False)
    c.set_component_tick_enabled(False); c.set_editor_property('affect_distance_field_lighting',False)


def instance_transform(u,row):
    angle=math.radians(row['yawDeg'])/2; t=u.Transform()
    t.set_editor_property('translation',u.Vector(*row['positionCm'])); t.set_editor_property('rotation',u.Quat(0.,0.,math.sin(angle),math.cos(angle)))
    t.set_editor_property('scale3d',u.Vector(*row['scale'])); return t


def import_geometry(u, plan, path, materials, helper):
    actors=u.get_editor_subsystem(u.EditorActorSubsystem); assets=u.EditorAssetLibrary
    subsystem=helper.static_mesh_subsystem(u); helper.finish_static_mesh_compilation(u,synchronous=True)
    pipelines=[]
    for source,name in [('GLTFSceneAssets','Assets'),('GLTFMaterials','Materials'),('LevelActors','Level')]:
        pipeline=assets.duplicate_asset('/Game/Brezi/Pipeline/'+source,PREFIX+'/Pipeline/'+name)
        require(pipeline,'Cannot duplicate rural pipeline'); pipelines.append(pipeline)
    mp=pipelines[0].get_editor_property('mesh_pipeline')
    for key,value in [('combine_static_meshes_behavior',u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE),('collision',False),('build_nanite',False),('generate_lightmap_u_vs',False)]: mp.set_editor_property(key,value)
    common=pipelines[0].get_editor_property('common_meshes_properties')
    for key,value in [('remove_degenerates',False),('recompute_normals',False),('recompute_tangents',True),('use_full_precision_u_vs',True)]: common.set_editor_property(key,value)
    pipelines[2].set_editor_property('scene_hierarchy_type',u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
    params=u.ImportAssetParameters()
    for key,value in [('is_automated',True),('replace_existing',False),('force_show_dialog',False),('override_pipelines',[u.SoftObjectPath(p.get_path_name()) for p in pipelines]),('import_level',u.get_editor_subsystem(u.LevelEditorSubsystem).get_current_level())]: params.set_editor_property(key,value)
    old={a.get_path_name() for a in actors.get_all_level_actors()}; manager=u.InterchangeManager.get_interchange_manager_scripted()
    require(manager.import_scene(PREFIX+'/Meshes',manager.create_source_data(str(path)),params),'Rural GLB import failed')
    expected={r['id']+'_LOD'+str(lod):(r,lod) for r in plan['meshes'] for lod in range(1+len(r.get('lods',[])))}
    imported={}; temporary=[]
    for actor in actors.get_all_level_actors():
        if actor.get_path_name() in old: continue
        temporary.append(actor)
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            mesh=c.get_editor_property('static_mesh'); require(mesh and mesh.get_path_name().startswith(PREFIX+'/'),'Foreign imported mesh')
            matches=[name for name in expected if name in mesh.get_name()]
            require(len(matches)==1 and matches[0] not in imported,'Ambiguous rural mesh '+mesh.get_name())
            name=matches[0]; row,_=expected[name]; mesh.set_material(0,materials[row['material']]); mesh.set_editor_property('has_navigation_data',False)
            assets.set_metadata_tag(mesh,'BreziGeneratedBy',OWNER); imported[name]=mesh
    require(set(imported)==set(expected),'Incomplete rural import')
    meshes={}
    for row in plan['meshes']:
        mesh=imported[row['id']+'_LOD0']
        for lod in range(1,1+len(row.get('lods',[]))):
            require(subsystem.set_lod_from_static_mesh(mesh,lod,imported[row['id']+'_LOD'+str(lod)],0,True)==lod,'Cannot attach rural authored LOD')
        for lod in range(1+len(row.get('lods',[]))):
            settings=subsystem.get_lod_build_settings(mesh,lod); settings.set_editor_property('use_full_precision_u_vs',True); settings.set_editor_property('generate_lightmap_u_vs',False)
            subsystem.set_lod_build_settings(mesh,lod,settings)
        set_nanite(u,mesh,bool(row.get('nanite',False))); helper.finish_static_mesh_compilation(u)
        if row.get('lods'):
            mesh.modify(True); require(subsystem.set_lod_screen_sizes(mesh,lod_screens(row)),'Cannot set rural LOD screens')
        require(assets.save_loaded_asset(mesh,False),'Cannot save rural mesh'); meshes[row['id']]=mesh
    for mesh in imported.values(): require(assets.save_loaded_asset(mesh,False),'Cannot save rural prototype')
    for actor in temporary: require(actors.destroy_actor(actor),'Cannot remove temporary imported actor')
    result={'meshes':{key:value.get_path_name() for key,value in meshes.items()},'actors':{},'groups':{}}
    grouped={g['meshId'] for g in plan['groups']}
    for row in plan['meshes']:
        if row['id'] in grouped: continue
        actor=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0),u.Rotator()); require(actor,'Cannot spawn rural static actor')
        actor.tags=[u.Name('BreziGenerated'),u.Name(TAG)]; actor.set_actor_label(row['id']); actor.set_folder_path('Brezi/Rural20260923'); actor.set_actor_tick_enabled(False)
        c=actor.get_component_by_class(u.StaticMeshComponent); c.set_static_mesh(meshes[row['id']]); new_component_policy(u,c)
        c.set_editor_property('cast_shadow',bool(row.get('castShadow',True)))
        result['actors'][row['id']]=actor.get_path_name()
    for group in plan['groups']:
        actor=actors.spawn_actor_from_class(u.load_class(None,'/Script/BreziTwin.BreziVegetationPatch'),u.Vector(0,0,0),u.Rotator()); require(actor,'Cannot spawn rural HISM')
        actor.tags=[u.Name('BreziGenerated'),u.Name(TAG)]; actor.set_actor_label(group['id']); actor.set_folder_path('Brezi/Rural20260923'); actor.set_actor_tick_enabled(False)
        c=actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent); require(c,'Missing rural HISM component')
        c.set_static_mesh(meshes[group['meshId']]); new_component_policy(u,c); c.set_cull_distances(group['cullStartCm'],group['cullEndCm'])
        c.set_editor_property('cast_shadow',bool(group.get('castShadow',True))); c.set_editor_property('visible_in_ray_tracing',True)
        indices=list(c.add_instances([instance_transform(u,row) for row in group['instances']],True,False,False))
        require(indices==list(range(len(group['instances']))),'Rural HISM insertion differs'); actor.synchronize_instance_bounds()
        result['groups'][group['id']]={'actor':actor.get_path_name(),'mesh':meshes[group['meshId']].get_path_name(),'instances':len(indices)}
    for pipeline in pipelines: require(assets.save_loaded_asset(pipeline,False),'Cannot save rural pipeline')
    return result


def mesh_proof(u,mesh,level,lod):
    description=mesh.get_static_mesh_description(lod); triangles=len(level['indices'])//3
    require(description and description.get_triangle_count()==triangles and mesh.get_num_triangles(lod)==triangles,'Rural native LOD triangle count differs')
    uv=level.get('uvs',[[x/100,y/100] for x,y,_ in level['verticesCm']])
    # GLB stores metres and UVs as float32; UE scales positions by 100 and
    # stores MeshDescription vertices as float32. Compare the exact documented
    # two-rounding representation, avoiding arbitrary decimal bins at .005cm.
    # This also correctly merges coincident source vertices whose tiny double
    # differences cannot be represented in the exported GLB.
    f32=lambda value:struct.unpack('<f',struct.pack('<f',value))[0]
    converted=[[f32(f32(v/100)*100) for v in point] for point in level['verticesCm']]
    converted_uv=[[f32(v) for v in tex] for tex in uv]
    def corner(point,tex): return tuple(point)+tuple(tex)
    def cyclic(values): return min(tuple(values[i:]+values[:i]) for i in range(3))
    expected=Counter(cyclic([corner(converted[i],converted_uv[i]) for i in level['indices'][j:j+3]]) for j in range(0,len(level['indices']),3))
    observed=Counter()
    for index in range(triangles):
        face=[]
        for j in range(3):
            vi=description.get_triangle_vertex_instance(u.TriangleID(id_value=index),j)
            point=vec(description.get_vertex_position(description.get_vertex_instance_vertex(vi)))
            tex=vec(description.get_vertex_instance_uv(vi,0),'xy'); face.append(corner(point,tex))
        observed[cyclic(face)]+=1
    require(expected==observed,'Rural native float32 cm positions/UV/winding differ: '+mesh.get_path_name()+' LOD'+str(lod))
    return {'triangles':triangles,'topologyUVAndCmScaleVerified':True,'nativeFloat32RepresentationExact':True,
            'maximumSourcePositionFloat32ErrorCm':max(abs(a-b) for original,actual in zip(level['verticesCm'],converted) for a,b in zip(original,actual)),
            'maximumSourceUVFloat32Error':max(abs(a-b) for original,actual in zip(uv,converted_uv) for a,b in zip(original,actual))}


def verify_geometry(u,plan,report,materials,helper):
    helper.finish_static_mesh_compilation(u); subsystem=helper.static_mesh_subsystem(u)
    actors={a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    expected=set(report['actors'].values())|{r['actor'] for r in report['groups'].values()}
    require({p for p,a in actors.items() if a.actor_has_tag(TAG)}==expected,'Rural actor inventory differs')
    proofs={}
    for row in plan['meshes']:
        mesh=u.EditorAssetLibrary.load_asset(report['meshes'][row['id']]); require(mesh,'Rural mesh missing')
        require(mesh.get_material(0)==materials[row['material']] and not mesh.get_editor_property('has_navigation_data'),'Rural material/navigation differs')
        require(bool(mesh.get_editor_property('nanite_settings').get_editor_property('enabled'))==bool(row.get('nanite',False)),'Rural Nanite differs')
        proofs[row['id']]=[mesh_proof(u,mesh,level,lod) for lod,level in enumerate([row,*row.get('lods',[])])]
        if row.get('lods'): require(all(abs(a-b)<1e-5 for a,b in zip(subsystem.get_lod_screen_sizes(mesh),lod_screens(row))) and mesh.get_num_lods()==3,'Rural three LOD policy differs')
    for path in expected:
        actor=actors[path]; c=actor.get_component_by_class(u.StaticMeshComponent)
        require(c and c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION and str(c.get_collision_profile_name())=='NoCollision' and not c.get_editor_property('can_ever_affect_navigation') and not c.get_editor_property('generate_overlap_events'),'Rural collision/navigation differs')
        require(c.is_visible() and not c.get_editor_property('hidden_in_game') and not actor.is_actor_tick_enabled() and not c.is_component_tick_enabled(),'Rural visibility/tick differs')
        require(transform(actor.get_actor_transform())==transform(u.Transform()) and transform(c.get_world_transform())==transform(u.Transform()),'Rural actor world transform differs')
    for group in plan['groups']:
        entry=report['groups'][group['id']]; c=actors[entry['actor']].get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        require(c.get_editor_property('static_mesh').get_path_name()==entry['mesh'] and c.get_instance_count()==len(group['instances']),'Rural HISM mesh/count differs')
        require(c.get_editor_property('instance_start_cull_distance')==group['cullStartCm'] and c.get_editor_property('instance_end_cull_distance')==group['cullEndCm'],'Rural HISM culling differs')
        for i,row in enumerate(group['instances']):
            actual=transform(instance_value(c,i)); wanted=transform(instance_transform(u,row))
            require(max(abs(a-b) for key in ['translation','scale3d'] for a,b in zip(actual[key],wanted[key]))<.003,'Rural HISM position/scale differs')
            require(min(max(abs(a-sign*b) for a,b in zip(actual['rotation'],wanted['rotation'])) for sign in (1,-1))<.00003,'Rural HISM rotation differs')
    report.update(savedReloaded=True,meshProofs=proofs,instanceCount=sum(len(g['instances']) for g in plan['groups']),lodScreenSizes=SCREENS,treeLodScreenSizes=TREE_SCREENS,allNewVisualsNoCollision=True)
    return report


def main():
    import unreal as u
    output=Path(os.environ['BREZI_RURAL_OUTPUT']).resolve(); require(output.is_relative_to(ROOT/'output/unreal'),'Require isolated output')
    project=output/'Project/BreziTwin'; content=project/'Content/Brezi'; geometry=output/'geometry'
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project,'Wrong native project')
    baseline_file=output/'photoreal-import-report.json'; baseline=read(baseline_file)
    require(baseline['status']=='photoreal-import-validated','Validated photoreal baseline required')
    before=inventory(content); require(before=={**baseline['finalAssetHashes'],relative(content/'Maps/Brezi.umap'):baseline['mapFileSha256']},'Photoreal baseline changed')
    require(not any((ROOT/k).is_relative_to(content/'Rural20260923') for k in before),'Fresh rural namespace required')
    inputs={relative(baseline_file):sha(baseline_file),**baseline['inputFiles'],**baseline['pipelineFiles']}
    for name,value in inputs.items(): require(sha(ROOT/name)==value,'Baseline pinned input changed: '+name)
    scene=read(geometry/'scene.json'); plan_file=geometry/'rural-context-geometry.json'; plan=read(plan_file); validate_plan(plan,scene)
    inputs[relative(plan_file)]=sha(plan_file)
    for name,value in {**plan.get('inputFiles',{}),**plan.get('pipelineFiles',{})}.items(): require(sha(ROOT/name)==value,'Rural plan pin changed: '+name); inputs[name]=value
    sys.path.insert(0,str(ROOT/'scripts/unreal'))
    helper=module('rural_lawn_helper','lawn-geometry.py'); material_module=module('rural_materials','rural-materials.py')
    actors=u.get_editor_subsystem(u.EditorActorSubsystem); levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
    require(u.EditorLoadingAndSavingUtils.new_blank_map(False),'Unload startup map failed'); require(levels.load_level(MAP),'Load baseline map failed')
    require(not any(a.actor_has_tag(TAG) for a in actors.get_all_level_actors()),'Rural actors already exist')
    folder=output/'rural-checkpoint'; folder.mkdir(exist_ok=True); backup=folder/'Brezi.umap'
    if backup.exists(): require(sha(backup)==sha(content/'Maps/Brezi.umap'),'Checkpoint drift')
    else: shutil.copy2(content/'Maps/Brezi.umap',backup)
    staged_viewpoints=project/'Content/Data/viewpoints.json'; viewpoints_backup=folder/'viewpoints.json'
    # The runner validates the full staged camera contract, including its added
    # Archviz room arrivals. Only the unchanged source sun belongs to this pass.
    require(read(staged_viewpoints)['sun']==read(geometry/'viewpoints.json')['sun'], 'Staged sun differs before rural lighting')
    if viewpoints_backup.exists(): require(sha(viewpoints_backup)==sha(staged_viewpoints),'Viewpoints checkpoint drift')
    else: shutil.copy2(staged_viewpoints,viewpoints_backup)
    state={'owner':OWNER,'status':'in-progress','nativeProcessId':os.getpid(),'baselineInventory':before,'baselineViewpointsSha256':sha(staged_viewpoints)}; write(folder/'state.json',state)
    report={'schemaVersion':1,'owner':OWNER,'status':'pending','startedAt':now(),'baselineReportSha256':sha(baseline_file),
            'activeDesign':scene['activeDesign'],'setbacksMm':{'street':3000,'right':3000},'inputFiles':inputs,
            'nativeRenderedVerified':False,'visualQualityVerified':False,'frameTimeVerified':False,
            'pipelineFiles':{relative(p):sha(p) for p in sorted((ROOT/'scripts/unreal').glob('rural-*')) if p.is_file()}}
    report['pipelineFiles'][relative(ROOT/'scripts/unreal/lawn-geometry.py')]=sha(ROOT/'scripts/unreal/lawn-geometry.py')
    try:
        initial=witness(u); materials=material_module.build_materials(road_yaw_degrees=plan.get('roadYawDegrees',0))
        materials={key:u.EditorAssetLibrary.load_asset(value) if isinstance(value,str) else value for key,value in materials.items()}
        report['materials']={key:value.get_path_name() for key,value in materials.items()}
        report['sourceEdits']=apply_source(u,plan,materials); report['managedLawn']=trim_lawn(u,plan)
        expected_source=witness(u)
        permitted={r['component']:({'mesh','materials'} if r['action']=='replace-material' else {'visible','hiddenInGame','cast_shadow','cast_hidden_shadow','affect_distance_field_lighting','affect_dynamic_indirect_lighting','affect_indirect_lighting_while_hidden','visible_in_ray_tracing'}) for r in report['sourceEdits'].values()}
        permitted.update({r['component']:{'instances'} for r in report['managedLawn']['groups'].values()})
        require(set(initial)==set(expected_source),'Source actor/component inventory changed')
        for key,before_row in initial.items():
            for field,value in before_row.items(): require(field in permitted.get(key,set()) or expected_source[key][field]==value,'Protected source component changed: '+key+' '+field)
        glb=geometry/'rural-context-native.glb'; write_glb(glb,plan); inputs[relative(glb)]=sha(glb)
        report['geometry']=import_geometry(u,plan,glb,materials,helper)
        sun=[a for a in actors.get_all_level_actors() if a.actor_has_tag('BreziSun')]; require(len(sun)==1,'Canonical sun missing')
        light=sun[0].get_component_by_class(u.DirectionalLightComponent); light.set_editor_property('light_source_angle',.75)
        original_rotation=vec(sun[0].get_actor_rotation(),'pitch yaw roll'.split())
        require(sun[0].set_actor_rotation(u.Rotator(pitch=-48.,yaw=original_rotation[1],roll=0.),False),'Cannot author summer sun rotation')
        light.set_intensity(80000.)
        report['sun']={'actor':sun[0].get_path_name(),'rotation':vec(sun[0].get_actor_rotation(),'pitch yaw roll'.split()),'lux':float(light.get_editor_property('intensity')),
                       'sourceAngleDegrees':.75,'sourceDirectionPreserved':False,'originalRotation':original_rotation,
                       'lightingIntent':'Illustrative clear summer daylight, 48 degree altitude, preserved source azimuth; photo-informed, not a solar-time or illumination measurement.',
                       'canonicalSourceViewpointsPreserved':True}
        staged_views=read(staged_viewpoints); staged_views['sun']['dayRotationDegrees']=report['sun']['rotation']
        write(staged_viewpoints,staged_views); report['stagedViewpointsSha256']=sha(staged_viewpoints)
        inputs[relative(staged_viewpoints)]=report['stagedViewpointsSha256']
        require(levels.save_current_level(),'Save rural map failed'); require(u.EditorAssetLibrary.save_directory(PREFIX,only_if_is_dirty=True,recursive=True),'Save rural assets failed')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False),'Unload rural map failed'); require(levels.load_level(MAP),'Reload rural map failed')
        require(witness(u)==expected_source,'Saved source component witness differs')
        report['protectedSourceWitnessSha256']=digest(expected_source)
        report['geometry']=verify_geometry(u,plan,report['geometry'],materials,helper)
        if hasattr(material_module,'verify_materials'): report['materialReadback']=material_module.verify_materials(report['materials'])
        by_path={a.get_path_name():a for a in actors.get_all_level_actors()}
        for path,entry in report['managedLawn']['groups'].items():
            c=by_path[path].get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
            require(c.get_instance_count()==entry['kept'] and digest([transform(instance_value(c,i)) for i in range(c.get_instance_count())])==entry['transformsSha256'],'Saved managed lawn transform sequence differs')
        for row in plan['replacementMaterials']:
            c=source_components(u,{row['sourceId']})[row['sourceId']]; mesh=c.get_editor_property('static_mesh')
            require(c.get_material(0).get_path_name()==report['sourceEdits'][row['sourceId']]['material'],'Saved rural material override differs')
            if row.get('nanite'): require(mesh.get_editor_property('nanite_settings').get_editor_property('enabled') and not c.get_editor_property('disallow_nanite'),'Saved road/curb Nanite differs')
        sun=by_path[report['sun']['actor']]; light=sun.get_component_by_class(u.DirectionalLightComponent)
        require(vec(sun.get_actor_rotation(),'pitch yaw roll'.split())==report['sun']['rotation'] and abs(float(light.get_editor_property('light_source_angle'))-.75)<1e-5 and float(light.get_editor_property('intensity'))==report['sun']['lux'],'Saved summer sun differs')
        from hidden_collision import verify_hidden_collision_contract
        from doors import verify_doors_contract
        report['hiddenCollision']=verify_hidden_collision_contract(scene,geometry); report['doors']=verify_doors_contract(scene,geometry)
        current=inventory(content); validate_changes(before,current,content)
        report['mapFileSha256']=current.pop(relative(content/'Maps/Brezi.umap')); report['finalAssetHashes']=current
        for name,value in inputs.items(): require(sha(ROOT/name)==value,'Input changed during rural import: '+name)
        for name,value in report['pipelineFiles'].items(): require(sha(ROOT/name)==value,'Pipeline changed during rural import: '+name)
        report.update(status='rural-import-validated',generatedAt=now(),savedReloaded=True,protectedBaselineAssetsUnchanged=True,sourceCollisionPreserved=True,
                      evidenceLimits=['Authored visual context from supplied photographs; no survey certification.','Native rendered appearance and exterior/interior frame times require separate runtime QA.'])
        write(output/'rural-import-report.json',report); state.update(status='complete',reportSha256=sha(output/'rural-import-report.json')); write(folder/'state.json',state)
        u.log('BREZI_RURAL_IMPORT validated')
    except Exception as error:
        report.update(status='failed',generatedAt=now(),error=str(error)); write(output/'rural-import-report.json',report)
        current=inventory(content)
        try: validate_changes(before,current,content); state['status']='failed-recoverable'
        except Exception: state['status']='failed-protected-drift'
        state['failedInventory']=current; state['failedViewpointsSha256']=sha(staged_viewpoints); write(folder/'state.json',state); raise


if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='--restore': restore(sys.argv[2])
    else: main()
