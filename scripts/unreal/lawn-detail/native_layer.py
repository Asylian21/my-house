"""Explicit editor-only additive lawn stage; import after existing saved-map passes.

No module-level Unreal import. Assets live in a versioned owned namespace. All
non-owned actors are read only. Each map reload is followed by fresh lookup;
rollback never dereferences pre-reload UObject references. No native run here.
"""
import importlib.util
import json
import math
import os
from pathlib import Path
import re
import uuid
from native_assets import Assets, IDS, OWNER, PREFIX, digest, require, sha, source_mesh, values, mesh_proof

ROOT=next(p for p in Path(__file__).resolve().parents if (p/'lib/twin-site.ts').is_file())
MAP='/Game/Brezi/Maps/Brezi'
TAG='BreziLawnDetail'
DATA='BreziLawnDescriptor'
META=('BreziGeneratedBy','BreziLawnRecipe',DATA)
ACTOR_CLASS='/Script/BreziTwin.BreziVegetationPatch'


def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


def vec(value,axes=('x','y','z')):return [float(getattr(value,k)) for k in axes]
def transform(value):return {'p':vec(value.translation),'q':vec(value.rotation,('x','y','z','w')),'s':vec(value.scale3d)}


def make_transform(u,value):
    result=u.Transform()
    result.set_editor_property('translation',u.Vector(*value['p']))
    result.set_editor_property('rotation',u.Quat(*value['q']))
    result.set_editor_property('scale3d',u.Vector(*value['s']))
    return result


def planned_transform(u,row):
    scale=row['uniformScale']
    half=math.radians(row['yawDegreesUnreal'])/2
    # NativeMakeFunc is exposed as a struct constructor, not MathLibrary.make_transform.
    return make_transform(u,{'p':row['positionUnrealCm'],'q':[0.,0.,math.sin(half),math.cos(half)],'s':[scale]*3})


def read_instances(component):
    rows=[]
    for i in range(component.get_instance_count()):
        value=component.get_instance_transform(i,False)
        if isinstance(value,tuple) and len(value)==2 and value[0] is True:value=value[1]
        require(value is not None and hasattr(value,'translation'),'HISM instance getter failed');rows.append(transform(value))
    return rows


def close_transforms(actual,expected):
    require(len(actual)==len(expected),'Grass instance count differs');maximum={'p':0.,'q':0.,'s':0.}
    for a,e in zip(actual,expected):
        require(set(a)==set(e)=={'p','q','s'},'Invalid instance transform record')
        for k,tolerance in (('p',.002),('q',2e-5),('s',2e-6)):
            require(len(a[k])==len(e[k])==(4 if k=='q' else 3) and all(math.isfinite(x) for x in a[k]+e[k]),'Nonfinite/malformed grass transform')
            error=max(abs(x-y) for x,y in zip(a[k],e[k]))
            if k=='q':error=min(error,max(abs(x+y) for x,y in zip(a[k],e[k])))
            require(error<=tolerance,'Grass instance transform differs: '+k);maximum[k]=max(maximum[k],error)
    return maximum


def actor_system(u):return u.get_editor_subsystem(u.EditorActorSubsystem)


def layer(u,allow_states=('active',)):
    result={};assets=u.EditorAssetLibrary
    for actor in actor_system(u).get_all_level_actors():
        owned=assets.get_metadata_tag(actor,'BreziGeneratedBy')==OWNER
        require(not owned or actor.actor_has_tag(TAG),'Owned lawn actor lost its tag')
        if not actor.actor_has_tag(TAG):continue
        require(owned and actor.get_class().get_path_name()==ACTOR_CLASS,'Refusing unowned lawn-tagged actor')
        d=json.loads(assets.get_metadata_tag(actor,DATA));recipe=assets.get_metadata_tag(actor,'BreziLawnRecipe')
        require(re.fullmatch('[0-9a-f]{64}',recipe or '') and d['recipe']==recipe and d['prototypeId'] in IDS
                and d['sourceObjectId']=='DOM_00001' and d['state'] in allow_states
                and d['groupId']=='LAWN_'+d['prototypeId'] and re.fullmatch('[0-9a-f]{32}',d['transaction']), 'Invalid or incomplete owned lawn layer')
        require(not any(str(t).startswith('DOM_') for t in actor.get_editor_property('tags')),'Lawn actor must not impersonate canonical source')
        key=(d['transaction'],d['groupId']);require(key not in result,'Duplicated grass group')
        cs=actor.get_components_by_class(u.StaticMeshComponent)
        require(len(cs)==1 and isinstance(cs[0],u.HierarchicalInstancedStaticMeshComponent),'Unexpected lawn component topology')
        c=cs[0];mesh=c.get_editor_property('static_mesh')
        require(mesh is not None and mesh.get_path_name()==d['mesh'] and mesh.get_path_name().startswith(PREFIX+'/R_'+recipe[:16]+'/')
                and assets.get_metadata_tag(mesh,'BreziGeneratedBy')==OWNER and assets.get_metadata_tag(mesh,'BreziLawnRecipe')==recipe,
                'Owned layer mesh provenance differs')
        require(c.get_num_materials()==1 and c.get_material(0).get_path_name()==d['material'] and not c.get_editor_property('override_materials'), 'Grass component material override differs')
        require(c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION and str(c.get_collision_profile_name())=='NoCollision'
                and not c.get_editor_property('can_ever_affect_navigation') and not c.is_component_tick_enabled() and not actor.is_actor_tick_enabled(), 'Grass collision/navigation/tick policy differs')
        require(c.get_editor_property('instance_start_cull_distance')==600 and c.get_editor_property('instance_end_cull_distance')==1200,'Grass cull distances differ')
        close_transforms([transform(actor.get_actor_transform()),transform(c.get_world_transform())],[transform(u.Transform()),transform(u.Transform())])
        require(not c.get_editor_property('hidden_in_game') and not actor.get_editor_property('hidden'), 'Unexpected independent lawn hidden state')
        expected_visible=d['state']=='active'
        require(bool(c.get_editor_property('visible'))==expected_visible and actor.actor_has_tag('BreziGenerated')
                and TAG in map(str,c.get_editor_property('component_tags')),'Lawn visibility/component ownership differs')
        require(c.get_instance_count()==d['instanceCount'] and d['instanceCount']>0,'Grass descriptor count differs')
        result[key]=(actor,c,d)
    return result


def old_snapshot(u,actors):
    result=[]
    for key,(a,c,d) in sorted(actors.items()):
        result.append({'descriptor':d,'originalActorPath':a.get_path_name(),'label':a.get_actor_label(),
            'actorTags':list(map(str,a.get_editor_property('tags'))),'componentTags':list(map(str,c.get_editor_property('component_tags'))),
            'instances':read_instances(c),'castShadow':bool(c.get_editor_property('cast_shadow')),
            'visibleInRayTracing':bool(c.get_editor_property('visible_in_ray_tracing')),
            'affectDistanceFieldLighting':bool(c.get_editor_property('affect_distance_field_lighting'))})
    return result


def preserved_snapshot(u):
    """All non-owned actor identity/transforms + every static mesh binding/flags.

    Asset bytes are checked separately. This does not claim arbitrary UObject
    property equivalence; only this explicit observable scope is compared.
    """
    from materials import _asset_hashes
    rows={};paths=set()
    for a in actor_system(u).get_all_level_actors():
        if a.actor_has_tag(TAG):continue
        components=[]
        for c in a.get_components_by_class(u.StaticMeshComponent):
            mesh=c.get_editor_property('static_mesh')
            if mesh is None:continue
            paths.add(mesh.get_path_name());materials=[c.get_material(i) for i in range(c.get_num_materials())]
            paths.update(m.get_path_name() for m in materials if m and m.get_path_name().startswith('/Game/Brezi/'))
            components.append({'name':c.get_name(),'mesh':mesh.get_path_name(),'transform':transform(c.get_world_transform()),
                'materials':[m.get_path_name() if m else None for m in materials],
                'overrides':[m.get_path_name() if m else None for m in c.get_editor_property('override_materials')],
                'visible':bool(c.get_editor_property('visible')),'hiddenInGame':bool(c.get_editor_property('hidden_in_game')),
                'collision':str(c.get_collision_enabled()),'profile':str(c.get_collision_profile_name()),
                'pawn':str(c.get_collision_response_to_channel(u.CollisionChannel.ECC_PAWN)),
                'tags':list(map(str,c.get_editor_property('component_tags')))})
        rows[a.get_path_name()]={'class':a.get_class().get_path_name(),'tags':list(map(str,a.get_editor_property('tags'))),
            'transform':transform(a.get_actor_transform()),'hidden':bool(a.get_editor_property('hidden')),'components':sorted(components,key=lambda c:c['name'])}
    lawn=[r for r in rows.values() if 'DOM_00001' in r['tags']]
    require(len(lawn)==1 and len(lawn[0]['components'])==1 and lawn[0]['components'][0]['visible']
            and not lawn[0]['components'][0]['hiddenInGame'] and not lawn[0]['hidden'],'Canonical base lawn is absent/hidden')
    return {'actors':rows,'assetHashes':_asset_hashes([p for p in paths if p.startswith('/Game/Brezi/')])}


def descriptor(group,recipe,tx,mesh,material):
    return {'recipe':recipe,'transaction':tx,'sourceObjectId':'DOM_00001','state':'staged','groupId':group['id'],
        'prototypeId':group['prototypeId'],'instanceCount':len(group['instances']),
        'orderedInstanceIdsSha256':digest([r['id'] for r in group['instances']]),'mesh':mesh,'material':material,
        'geometryBoundsUnrealCm':group['geometryBoundsUnrealCm'],'componentBoundsUnrealCm':group['componentBoundsUnrealCm']}


def spawn(u,d,instance_values,label=None,actor_tags=None,component_tags=None,flags=None):
    actor=actor_system(u).spawn_actor_from_class(u.load_class(None,ACTOR_CLASS),u.Vector(0,0,0),u.Rotator())
    require(actor is not None,'Cannot spawn serializable lawn HISM')
    # Tag immediately, so partially populated own actors can be removed on failure.
    actor.set_editor_property('tags',[u.Name(t) for t in (actor_tags or ['BreziGenerated',TAG,'BreziLawnSource=DOM_00001'])])
    a=u.EditorAssetLibrary;a.set_metadata_tag(actor,'BreziGeneratedBy',OWNER);a.set_metadata_tag(actor,'BreziLawnRecipe',d['recipe']);a.set_metadata_tag(actor,DATA,json.dumps(d,allow_nan=False))
    actor.set_actor_label(label or 'Trávnik · '+d['prototypeId']);actor.set_actor_tick_enabled(False)
    c=actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent);require(c is not None,'Lawn HISM component missing')
    c.set_editor_property('component_tags',[u.Name(t) for t in (component_tags or ['BreziGenerated',TAG])])
    c.set_visibility(False);c.set_hidden_in_game(False);c.set_static_mesh(a.load_asset(d['mesh']))
    c.set_collision_profile_name('NoCollision');c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION)
    c.set_editor_property('can_ever_affect_navigation',False);c.set_component_tick_enabled(False);c.set_cull_distances(600,1200)
    flags=flags or {'castShadow':True,'visibleInRayTracing':True,'affectDistanceFieldLighting':True}
    for key,name in [('castShadow','cast_shadow'),('visibleInRayTracing','visible_in_ray_tracing'),('affectDistanceFieldLighting','affect_distance_field_lighting')]:c.set_editor_property(name,flags[key])
    indices=list(c.add_instances([make_transform(u,r) for r in instance_values],True,False,False))
    require(indices==list(range(len(instance_values))),'Grass insertion ordering differs');actor.synchronize_instance_bounds()
    c.set_visibility(d['state']=='active');return actor


def state(u,tx,value):
    for _,(a,c,d) in layer(u,('staged','active','retiring')).items():
        if d['transaction']!=tx:continue
        d=dict(d,state=value);u.EditorAssetLibrary.set_metadata_tag(a,DATA,json.dumps(d,allow_nan=False));c.set_visibility(value=='active')


def verify_group(u,item,expected,visible):
    a,c,d=item;require(d['state']==('active' if visible else 'staged'),'Grass phase mismatch')
    actual=read_instances(c);errors=close_transforms(actual,[transform(planned_transform(u,r)) for r in expected['instances']])
    origin,extent,_=u.SystemLibrary.get_component_bounds(c)
    bounds={'min':[getattr(origin,k)-getattr(extent,k) for k in ('x','y','z')],'max':[getattr(origin,k)+getattr(extent,k) for k in ('x','y','z')]}
    be=max(abs(bounds[k][i]-expected['componentBoundsUnrealCm'][k][i]) for k in ('min','max') for i in range(3))
    require(be<=.05,'Serialized HISM component bounds differ')
    require(c.get_editor_property('cast_shadow') and c.get_editor_property('visible_in_ray_tracing')
            and c.get_editor_property('affect_distance_field_lighting'),'Grass lighting participation differs')
    require(d['orderedInstanceIdsSha256']==digest([r['id'] for r in expected['instances']]),'Grass source instance order differs')
    return {'actor':a.get_path_name(),'groupId':expected['id'],'prototypeId':expected['prototypeId'],'instances':len(actual),
            'nativeOrderedTransformsSha256':digest(actual),'maximumTransformErrors':errors,'nativeComponentBoundsUnrealCm':bounds,
            'maxComponentBoundsErrorCm':be,'serializedReloadVerified':True,'clusterTreeBuildRequested':True,
            'internalClusterTreeBytesReadBack':False,'collision':'NoCollision','navigation':False,'tick':False,'cullStartCm':600,'cullEndCm':1200}


def phase_proof(u,tx,groups,visible,old=None,final=False):
    # World-bound wrappers live only in this helper frame, never in its caller.
    observed=layer(u,('active',) if final else ('active','staged','retiring'))
    expected={(tx,g) for g in groups};actual={key for key in observed if key[0]==tx}
    require(actual==expected and (not final or set(observed)==expected),'Own grass phase inventory differs')
    receipts=[verify_group(u,observed[(tx,g)],groups[g],visible) for g in sorted(groups)]
    if old is not None:
        previous={k:v for k,v in observed.items() if k[0]!=tx}
        require(values(old_snapshot(u,previous))==values(old),'Previous active layer changed before activation')
    return receipts


def remove_previous(u,tx):
    for key,(actor,_,_) in layer(u,('active','retiring')).items():
        if key[0]!=tx:require(actor_system(u).destroy_actor(actor),'Cannot remove previous owned lawn actor')


def restore_layer(u,tx,old):
    for actor in list(actor_system(u).get_all_level_actors()):
        if not actor.actor_has_tag(TAG):continue
        require(u.EditorAssetLibrary.get_metadata_tag(actor,'BreziGeneratedBy')==OWNER,'Rollback refuses unowned actor')
        d=json.loads(u.EditorAssetLibrary.get_metadata_tag(actor,DATA))
        if d['transaction']==tx:require(actor_system(u).destroy_actor(actor),'Rollback new actor removal failed')
    survivors=layer(u,('active','retiring'))
    for r in old:
        d=r['descriptor'];key=(d['transaction'],d['groupId'])
        if key not in survivors:spawn(u,d,r['instances'],r['label'],r['actorTags'],r['componentTags'],r)
    for old_tx in {r['descriptor']['transaction'] for r in old}:state(u,old_tx,'active')


def prepare_contract(scene,geometry_dir):
    geometry=Path(geometry_dir);placement=module('brezi_lawn_placement',Path(__file__).with_name('placement.py'))
    contract=placement.verify_inputs(scene,geometry);plan=contract['plan']
    require(tuple(placement.IDS)==IDS and plan['status']=='lawn-detail-placement-validated' and plan['sourceObjectId']=='DOM_00001'
            and plan['densityTuftsPerM2']==100 and plan['seed']==601226 and plan['cullStartCm']==600 and plan['cullEndCm']==1200,'Unsupported native lawn policy')
    groups={g['id']:g for g in plan['groups']};require(len(groups)==len(plan['groups'])==4 and {g['prototypeId'] for g in groups.values()}==set(IDS),'Exact four grass groups required')
    require(all(g['id']=='LAWN_'+g['prototypeId'] and g['instances'] for g in groups.values()),'Grass group identity differs')
    ids=[r['id'] for g in groups.values() for r in g['instances']]
    require(len(ids)==len(set(ids))==plan['instanceCount'],'Duplicate/missing grass source instance IDs')
    pins=dict(contract['pipelineFiles'])
    for p in (Path(__file__),Path(__file__).with_name('native_assets.py')):pins[str(p.relative_to(ROOT))]=sha(p)
    # Pin the actual existing native actor implementation too; no C++ changes.
    for name in ('BreziVegetationPatch.h','BreziVegetationPatch.cpp', 'BreziRendererSettingsAudit.h','BreziRendererSettingsAudit.cpp'):
        p=ROOT/'unreal/BreziTwin/Source/BreziTwin'/name;pins[str(p.relative_to(ROOT))]=sha(p)
    recipe=digest(pins);prefix=PREFIX+'/R_'+recipe[:16]
    return placement,contract,groups,pins,recipe,prefix


def apply_lawn_detail(scene,geometry_dir):
    import unreal as u
    from materials import _asset_hashes
    geometry=Path(geometry_dir)
    placement,contract,groups,pins,recipe,prefix=prepare_contract(scene,geometry)
    plan=contract['plan']
    tx=uuid.uuid4().hex
    destination=geometry.parent/'lawn-detail'/'native-runs'/tx;destination.mkdir(parents=True,exist_ok=False)
    report={'schemaVersion':1,'status':'pending','nativeApplied':False,'recipeSha256':recipe,'pipelineFiles':pins,
        'sourceManifestSha256':plan['sourceManifestSha256'],'sourceObjSha256':plan['sourceObjSha256'],'sourceObjectId':'DOM_00001',
        'transaction':tx,'nativeProcessId':os.getpid(),'prototypeIds':list(IDS),'instanceCount':sum(len(g['instances']) for g in groups.values()),
        'preservedBaseLawn':False,'renderedVerified':False,'photorealismVerified':False,'performanceAccepted':False,
        'rollbackAttempted':False,'rollbackVerified':False,'limitations':['Illustrative CC0 Bermuda tufts; species/product and .35 transmission are authored choices.',
            'Saved source geometry/UV and HISM transforms do not prove numeric native normals, resident texture mips, cooked fading, shadows, HWRT appearance or performance.',
            'Rollback reconstructs deleted owned actors from plain state; Unreal object paths can change. Canonical actor paths/bindings must remain identical.']}
    def write():
        file=destination/'report.json';tmp=destination/'report.tmp';tmp.write_text(json.dumps(report,indent=2,allow_nan=False)+'\n');tmp.replace(file)
    def pinned():
        for p,h in pins.items():require(sha(ROOT/p)==h,'Lawn pipeline input changed '+p)
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
    require(u.EditorLevelLibrary.get_editor_world().get_path_name().split('.')[0]==MAP,'Lawn stage requires saved canonical map loaded')
    require(u.EditorAssetLibrary.does_asset_exist(MAP),'Canonical map not saved')
    require(u.load_class(None,ACTOR_CLASS) is not None,'Native vegetation class is not compiled')
    registry=u.AssetRegistryHelpers.get_asset_registry();registry.scan_paths_synchronous(['/Game/Brezi','/Interchange/Pipelines'],force_rescan=True)
    before=preserved_snapshot(u);old=old_snapshot(u,layer(u));old_transactions={r['descriptor']['transaction'] for r in old}
    require(not old or (len(old)==4 and len(old_transactions)==1 and {r['descriptor']['prototypeId'] for r in old}==set(IDS)),'Previous lawn layer is incomplete')
    (destination/'preserved-before.json').write_text(json.dumps(before,allow_nan=False)+'\n')
    (destination/'old-layer.json').write_text(json.dumps(old,allow_nan=False)+'\n')
    old_paths=set()
    for r in old:
        old_prefix=PREFIX+'/R_'+r['descriptor']['recipe'][:16]
        old_paths.update(u.EditorAssetLibrary.list_assets(old_prefix,recursive=True,include_folder=False))
    old_asset_hashes=_asset_hashes(old_paths)
    report['preservedPriorLayerAssetHashes']=old_asset_hashes
    report['preservedBeforeSha256']=sha(destination/'preserved-before.json');report['oldLayerSha256']=sha(destination/'old-layer.json');write()
    def reload(save=True):
        if save:require(levels.save_current_level(),'Lawn map save failed')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False) and levels.load_level(MAP),'Lawn map reload failed')
        require(values(preserved_snapshot(u))==values(before),'Non-owned actor/asset state changed during lawn stage')
        require(_asset_hashes(old_paths)==old_asset_hashes,'Prior own layer asset bytes changed');pinned()
    writer=Assets(u,prefix,recipe,contract['prototypeReport'],placement.PROTOTYPES)
    rows={p['id']:p for p in contract['prototypeReport']['prototypes'] if p['id'] in IDS}
    sources={i:source_mesh(placement.PROTOTYPES/rows[i]['file'],rows[i]) for i in IDS}
    changed=False;meshes=None;material=None
    try:
        pinned();material,material_report=writer.material();meshes,proofs=writer.meshes(material,sources)
        mesh_paths={i:m.get_path_name() for i,m in meshes.items()};material_path=material.get_path_name()
        report.update(material=material_report,meshes=proofs,assetHashes=_asset_hashes(writer.paths),
            importSettings={'collision':False,'nanite':False,'generateLightmapUVs':False,'recomputeNormals':False,
                'recomputeTangents':False,'removeDegenerates':False,'fullPrecisionUVs':True,'highPrecisionTangentBasis':True,
                'pipelineReadbackVerified':True,'nativeNumericNormalsVerified':False});write()
        # No canonical setter occurs in this stage. Only fresh owned HISM actors.
        changed=True
        for group in groups.values():
            d=descriptor(group,recipe,tx,mesh_paths[group['prototypeId']],material_path)
            spawn(u,d,[transform(planned_transform(u,r)) for r in group['instances']])
        meshes=None;material=None
        reload();phase_proof(u,tx,groups,False,old=old)
        for old_tx in old_transactions:state(u,old_tx,'retiring')
        state(u,tx,'active');reload();phase_proof(u,tx,groups,True)
        report['stagedSavedReloadVerified']=True
        # Helpers finish and release all world-bound Python wrappers before reload.
        remove_previous(u,tx)
        reload();report['groups']=phase_proof(u,tx,groups,True,final=True)
        material=u.EditorAssetLibrary.load_asset(material_path);report['material']=writer.material_proof(material)
        report['meshes']={i:mesh_proof(u,u.EditorAssetLibrary.load_asset(path),sources[i],material) for i,path in mesh_paths.items()}
        require(_asset_hashes(writer.paths)==report['assetHashes'],'Own lawn asset bytes changed across reload')
        # Map is intentional scene mutation; all input/protected asset bytes stay fixed.
        map_file=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_content_dir()))/'Brezi/Maps/Brezi.umap'
        report.update(status='lawn-detail-authored-validated',nativeApplied=True,preservedBaseLawn=True,
            priorLayerRemoved=bool(old),mapFileSha256=sha(map_file),serializedSavedReloadVerified=True,
            preservedAfterSha256=digest(preserved_snapshot(u)))
        pinned();write();return report
    except Exception as error:
        report.update(status='failed',error=str(error),nativeApplied=False)
        # A traceback can retain helper frames and their world-bound wrappers.
        error.__traceback__=None;meshes=None;material=None
        if changed:
            report['rollbackAttempted']=True
            try:
                # A failed save/load can leave either map current. Start from disk,
                # remove only exact own tx groups, then rebuild missing old groups.
                require(u.EditorLoadingAndSavingUtils.new_blank_map(False) and levels.load_level(MAP),'Rollback map reload failed')
                restore_layer(u,tx,old)
                reload();restored=old_snapshot(u,layer(u))
                expected=values(old);actual=values(restored)
                for row in expected+actual:row.pop('originalActorPath',None)
                require(actual==expected,'Restored owned layer descriptors/transforms differ')
                report['rollbackVerified']=True
            except Exception as rollback_error:report['rollbackError']=str(rollback_error)
        write();raise
