"""Standalone isolated R18 native overlay; root launches Unreal, never this agent.

BREZI_NEIGHBOR_OUTPUT must name a fresh independent clone. Original source R16
receipt defaults remain frozen; no copied exterior report is forged or edited.
Only the candidate map, exact appended diagnostic view and new R18 packages can change. Source guards work in
ordinary Python. Native success requires actual saved/reloaded geometry proof.
"""
from collections import Counter
import copy
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import shutil
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/unreal'))
OWNER='scripts/unreal/exterior-neighbor-finish-native-r2.py'
PREFIX='/Game/Brezi/NeighborFinish20261001R18'
TAG='BreziNeighborFinish20261001R18'
MAP='/Game/Brezi/Maps/Brezi'
DEFAULT_BASELINE=ROOT/'output/unreal/exterior-20261001-r16a'
BASELINE_REPORT_SHA='1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122'
RENDER_FIELDS=('cast_shadow','cast_hidden_shadow','affect_distance_field_lighting','affect_dynamic_indirect_lighting',
               'affect_indirect_lighting_while_hidden','visible_in_ray_tracing','render_in_main_pass','render_in_depth_pass')


def module(name,filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/filename)
    result=importlib.util.module_from_spec(spec);spec.loader.exec_module(result);return result


guard=module('neighbor_finish_guard','exterior-neighbor-finish-guards.py')
require,sha,read,digest=guard.require,guard.sha,guard.read,guard.digest


def write(path,value):Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def now():return datetime.now(timezone.utc).isoformat()
def detailed_inventory(content):return {str(p.relative_to(content)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(content.rglob('*')) if p.is_file()}
def inventory(content):return {p:r['sha256'] for p,r in detailed_inventory(content).items()}
def pin(path):return {'path':str(path),'sha256':sha(path),'bytes':Path(path).stat().st_size}
def protected_files(project):return sorted(p for p in project.rglob('*') if p.is_file() and (p.relative_to(project).parts[0] in {'Binaries','Config','Source'} or p.relative_to(project).parts==('BreziTwin.uproject',)))


def protected_project_proof(baseline_project,project):
    source={str(p.relative_to(baseline_project)):p for p in protected_files(baseline_project)}
    destination={str(p.relative_to(project)):p for p in protected_files(project)}
    require(set(source)==set(destination),'Original Config/Source/Binaries/descriptor membership changed')
    files={}
    for relative,p in source.items():
        other=destination[relative];source_sha=sha(p);destination_sha=sha(other)
        require(source_sha==destination_sha and p.stat().st_size==other.stat().st_size and p.stat().st_ino!=other.stat().st_ino,'Protected project bytes/inodes differ: '+relative)
        files[relative]={'source':str(p),'destination':str(other),'sha256':source_sha,'bytes':p.stat().st_size,'independentInodes':True}
    return {'schemaVersion':1,'owner':OWNER,'status':'neighbor-finish-protected-project-byte-validated','fileCount':len(files),'files':files,'originalProjectBytesPreserved':True}


def native_module_witness(project,baseline_project):
    relative=Path('Binaries/Mac/libUnrealEditor-BreziTwin.dylib');source=baseline_project/relative;destination=project/relative
    expected='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574'
    require(sha(source)==sha(destination)==expected and source.stat().st_size==destination.stat().st_size==2818384 and source.stat().st_ino!=destination.stat().st_ino,'Own original R16 native module bytes/inodes differ')
    return {'source':str(source),'destination':str(destination),'sha256':expected,'bytes':2818384,'independentInodes':True}
def vec(v,axes='xyz'):return [float(getattr(v,k)) for k in axes]


def export_records(bundle):
    rows=copy.deepcopy(bundle['geometry']['candidateMeshes'])
    for original in bundle['geometry']['unchangedRemainderMeshes']:
        if not original['indices']:continue
        row=copy.deepcopy(original);row['id']='neighbor_r18_retained_'+original['id'];row['sourceMeshId']=original['id'];rows.append(row)
    require(len(rows)==37 and sum(len(r['indices'])//3 for r in rows)==6815,'37 complete new/retained export meshes required')
    return rows


def write_glb(path,rows):
    """Exact source positions/UV0 and original authored normals/tangents.

    glTF (X,Z,Y) is a reflection of the UE frame, so tangent handedness flips.
    Source triangle order is serialized unchanged and separately decoded.
    """
    binary=bytearray();accessors=[];views=[];meshes=[];nodes=[]
    def accessor(values,kind,component=5126,target=34962):
        flat=[v for row in values for v in (row if isinstance(row,(tuple,list)) else [row])]
        binary.extend(b'\0'*((-len(binary))%4));start=len(binary)
        binary.extend(struct.pack('<'+('f' if component==5126 else 'I')*len(flat),*flat))
        views.append({'buffer':0,'byteOffset':start,'byteLength':len(binary)-start,'target':target})
        record={'bufferView':len(views)-1,'componentType':component,'count':len(values),'type':kind}
        if kind=='VEC3':record.update(min=[min(p[k] for p in values) for k in range(3)],max=[max(p[k] for p in values) for k in range(3)])
        accessors.append(record);return len(accessors)-1
    for row in rows:
        positions=row['verticesCm'];normals=row.get('normals')
        if normals is None:
            normals=[[0.,0.,0.] for _ in positions]
            for points,index in zip(guard.triangles(row),[row['indices'][j:j+3] for j in range(0,len(row['indices']),3)]):
                a,b,c=points;normal=guard.cross([c[k]-a[k] for k in range(3)],[b[k]-a[k] for k in range(3)])
                for i in index:normals[i]=[normals[i][k]+normal[k] for k in range(3)]
            normals=[[x/(math.sqrt(guard.dot(v,v)) or 1) for x in v] if guard.dot(v,v)>0 else [0.,0.,1.] for v in normals]
        attributes={'POSITION':accessor([[x/100,z/100,y/100] for x,y,z in positions],'VEC3'),
                    'NORMAL':accessor([[x,z,y] for x,y,z in normals],'VEC3'),'TEXCOORD_0':accessor(row['uvs'],'VEC2')}
        if 'tangents' in row:
            attributes['TANGENT']=accessor([[t[0],t[2],t[1],-sign] for t,sign in zip(row['tangents'],row['tangentHandedness'])],'VEC4')
        name=row['id']+'_LOD0';meshes.append({'name':name,'primitives':[{'attributes':attributes,'indices':accessor(row['indices'],'SCALAR',5125,34963),'mode':4}]})
        nodes.append({'name':name,'mesh':len(meshes)-1})
    document={'asset':{'version':'2.0','generator':OWNER},'scene':0,'scenes':[{'nodes':list(range(len(nodes)))}],
              'nodes':nodes,'meshes':meshes,'accessors':accessors,'bufferViews':views,'buffers':[{'byteLength':len(binary)}]}
    encoded=json.dumps(document,separators=(',',':'),allow_nan=False).encode();encoded+=b' '*((-len(encoded))%4);binary+=b'\0'*((-len(binary))%4)
    Path(path).write_bytes(struct.pack('<III',0x46546c67,2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary)


def decode_glb(path,rows):
    payload=Path(path).read_bytes();magic,version,size=struct.unpack_from('<III',payload)
    require(magic==0x46546c67 and version==2 and size==len(payload),'GLB header/length differs')
    length,kind=struct.unpack_from('<II',payload,12);require(kind==0x4e4f534a,'GLB JSON chunk missing')
    document=json.loads(payload[20:20+length]);offset=20+length;binary_len,binary_kind=struct.unpack_from('<II',payload,offset)
    require(binary_kind==0x004e4942,'GLB BIN chunk missing');binary=payload[offset+8:offset+8+binary_len]
    def values(index):
        a=document['accessors'][index];v=document['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']]
        format='f' if a['componentType']==5126 else 'I';start=v.get('byteOffset',0)+a.get('byteOffset',0)
        flat=struct.unpack_from('<'+format*(a['count']*width),binary,start)
        return [list(flat[j:j+width]) for j in range(0,len(flat),width)]
    require(len(document['meshes'])==len(rows)==37,'Decoded GLB mesh count differs')
    for mesh,row in zip(document['meshes'],rows):
        require(mesh['name']==row['id']+'_LOD0' and len(mesh['primitives'])==1,'GLB source mesh order/name differs')
        primitive=mesh['primitives'][0];attributes=primitive['attributes']
        require([v[0] for v in values(primitive['indices'])]==row['indices'],'GLB original source triangle order changed')
        require(values(attributes['POSITION'])==[[guard.f32(x/100),guard.f32(z/100),guard.f32(y/100)] for x,y,z in row['verticesCm']],'GLB axis/metre conversion differs')
        require(values(attributes['TEXCOORD_0'])==[[guard.f32(v) for v in uv] for uv in row['uvs']],'GLB metric UV0 differs')
        if 'normals' in row:
            require(values(attributes['NORMAL'])==[[guard.f32(x),guard.f32(z),guard.f32(y)] for x,y,z in row['normals']],'GLB authored normal differs')
            require(values(attributes['TANGENT'])==[[guard.f32(t[0]),guard.f32(t[2]),guard.f32(t[1]),-s] for t,s in zip(row['tangents'],row['tangentHandedness'])],'GLB reflected tangent basis differs')
    return {'sourceGLBDecoded':True,'sourcePositionUVOrderVerified':True,'sourceCandidateNormalTangentExportVerified':True,
            'meshCount':37,'triangles':6815,'sha256':sha(path),'nativeGeometryDecoded':False}


def native_mesh_proof(u,mesh,row):
    expected=guard.native_corner_sequence(row);description=mesh.get_static_mesh_description(0)
    require(description and mesh.get_num_lods()==1 and mesh.get_num_triangles(0)==len(expected) and description.get_triangle_count()==len(expected),'Native R18 mesh count/LOD differs')
    observed=[]
    for i in range(len(expected)):
        face=[]
        for corner in range(3):
            vi=description.get_triangle_vertex_instance(u.TriangleID(id_value=i),corner)
            point=vec(description.get_vertex_position(description.get_vertex_instance_vertex(vi)))
            uv=vec(description.get_vertex_instance_uv(vi,0),'xy');face.append(tuple(point+uv))
        observed.append(guard.cyclic(face))
    require(observed==expected,'Native ordered float32 position/UV/connectivity/winding differs: '+row['id'])
    return {'sourceMeshId':row['id'],'triangles':len(expected),'orderedNativeF32CornersSha256':digest(observed),
            'sourceGeometrySha256':digest(row),'nativeFloat32RepresentationExact':True,'triangleOrderPreserved':True,
            'positionUVTopologyWindingVerified':True,'nativeNormalTangentReadbackAvailable':False}


def original_witness(u,actors,base):
    rows=base.witness(u,actors)
    for actor in actors.get_all_level_actors():
        actor_row=rows[actor.get_path_name()];actor_row['actorTick']=bool(actor.is_actor_tick_enabled())
        if isinstance(actor,u.BreziVegetationPatch):actor_row['detailDensityScaling']=bool(actor.get_detail_density_scaling())
        components={c.get_name():c for c in actor.get_components_by_class(u.SceneComponent)}
        for row in rows[actor.get_path_name()]['components']:
            component=components[row['name']];parent=component.get_attach_parent()
            row['attachParent']=parent.get_path_name() if parent else None
            row['mobility']=str(component.get_editor_property('mobility'))
            if isinstance(component,u.StaticMeshComponent):
                row['overrideMaterials']=[m.get_path_name() if m else None for m in component.get_editor_property('override_materials')]
                row['neighborRenderPolicy']={k:bool(component.get_editor_property(k)) for k in RENDER_FIELDS}
                row['additionalRenderFlags']={k:bool(component.get_editor_property(k)) for k in
                    ('cast_dynamic_shadow','cast_static_shadow','cast_contact_shadow','cast_far_shadow','receives_decals','use_as_occluder','never_distance_cull')}
                row['drawPolicy']={k:component.get_editor_property(k) for k in ('min_draw_distance','ld_max_draw_distance','cached_max_draw_distance','bounds_scale')}
                row['overlapEvents']=bool(component.get_editor_property('generate_overlap_events'))
                row['componentTick']=bool(component.is_component_tick_enabled())
                row['maxDrawDistanceCm']=float(component.get_editor_property('ld_max_draw_distance'))
            if isinstance(component,u.InstancedStaticMeshComponent):
                row['instanceCullCm']=[int(component.get_editor_property(k)) for k in ('instance_start_cull_distance','instance_end_cull_distance')]
    return rows


def original_material_witness(u,baseline,existing_snapshot,materials_helper):
    material_rows=baseline['materials']['materials'];texture_rows=baseline['materials']['textures']
    require(len(material_rows)==42 and len(texture_rows)==74,'Frozen original42graphs/74textures required')
    graphs={};textures={}
    for key,row in material_rows.items():
        material=u.EditorAssetLibrary.load_asset(row['asset']);require(material,'Protected original material missing')
        graph=existing_snapshot(u,material);require(graph==row['graph'],'Protected original graph differs from R16 receipt: '+key)
        graphs[key]={'asset':material.get_path_name(),'graph':graph}
    for key,row in texture_rows.items():
        texture=u.EditorAssetLibrary.load_asset(row['asset']);require(isinstance(texture,u.Texture2D),'Protected original texture missing')
        textures[key]={'asset':texture.get_path_name(),'snapshot':materials_helper.texture_snapshot(texture)}
    return {'graphs':graphs,'textures':textures}


def affected_components(u,actors,baseline,bundle):
    actor_lookup={a.get_path_name():a for a in actors.get_all_level_actors()};result={}
    for identity in guard.PARTITIONS:
        path=baseline['geometry']['actors'][identity];actor=actor_lookup.get(path);require(actor,'R16 affected actor missing')
        mesh_path=baseline['geometry']['meshes'][identity]
        components=[c for c in actor.get_components_by_class(u.StaticMeshComponent) if c.get_editor_property('static_mesh') and c.get_editor_property('static_mesh').get_path_name()==mesh_path]
        require(len(components)==1,'Affected chunk component ambiguous')
        component=components[0];require(component.get_num_materials()==1 and component.is_visible() and not component.get_editor_property('hidden_in_game'),'Affected original chunk material/visibility differs')
        frame=component.get_world_transform();require(vec(frame.translation)==[0.,0.,0.] and vec(frame.scale3d)==[1.,1.,1.] and vec(frame.rotation,'xyzw') in [[0.,0.,0.,1.],[0.,0.,0.,-1.]],'Original source chunk is not in the exact zero-origin frame')
        require(component.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION and not component.get_editor_property('can_ever_affect_navigation'),'Original visual chunk collision/navigation differs')
        native_mesh_proof(u,component.get_editor_property('static_mesh'),bundle['originalChunks'][identity])
        refs=[c for a in actors.get_all_level_actors() for c in a.get_components_by_class(u.StaticMeshComponent) if c.get_editor_property('static_mesh') and c.get_editor_property('static_mesh').get_path_name()==mesh_path]
        require(len(refs)==1,'Original source chunk has unreviewed additional component references')
        result[identity]=component
    return result


def import_geometry(u,path,rows,materials,mesh_helper):
    assets=u.EditorAssetLibrary;actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
    pipelines=[]
    for original,name in [('GLTFSceneAssets','Assets'),('GLTFMaterials','Materials'),('LevelActors','Level')]:
        target=PREFIX+'/Pipeline/'+name;require(not assets.does_asset_exist(target),'Fresh R18 import pipeline namespace required')
        pipeline=assets.duplicate_asset('/Game/Brezi/Pipeline/'+original,target);require(pipeline,'Cannot duplicate R18 import pipeline');pipelines.append(pipeline)
    mp=pipelines[0].get_editor_property('mesh_pipeline')
    for k,v in {'combine_static_meshes_behavior':u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,'collision':False,'build_nanite':False,'generate_lightmap_u_vs':False}.items():mp.set_editor_property(k,v)
    properties=pipelines[0].get_editor_property('common_meshes_properties')
    for k,v in {'remove_degenerates':False,'recompute_normals':False,'recompute_tangents':True,'use_full_precision_u_vs':True}.items():properties.set_editor_property(k,v)
    pipelines[1].set_editor_property('import_materials',False)
    pipelines[2].set_editor_property('scene_hierarchy_type',u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
    params=u.ImportAssetParameters()
    for k,v in {'is_automated':True,'replace_existing':False,'force_show_dialog':False,'override_pipelines':[u.SoftObjectPath(p.get_path_name()) for p in pipelines],'import_level':levels.get_current_level()}.items():params.set_editor_property(k,v)
    before={a.get_path_name() for a in actors.get_all_level_actors()};manager=u.InterchangeManager.get_interchange_manager_scripted()
    require(manager.import_scene(PREFIX+'/Geometry',manager.create_source_data(str(path)),params),'R18 source GLB import failed')
    expected={r['id']+'_LOD0':r for r in rows};imported={};temporary=[];subsystem=mesh_helper.static_mesh_subsystem(u)
    for actor in actors.get_all_level_actors():
        if actor.get_path_name() in before:continue
        temporary.append(actor)
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            mesh=component.get_editor_property('static_mesh');require(mesh and mesh.get_path_name().startswith(PREFIX+'/'),'Foreign R18 imported asset')
            names=[key for key in expected if mesh.get_name()==key or mesh.get_name().endswith('_'+key) or actor.get_actor_label()==key]
            require(len(names)==1 and names[0] not in imported,'Ambiguous R18 imported mesh')
            row=expected[names[0]];mesh.set_material(0,materials[row['material']]);mesh.set_editor_property('has_navigation_data',False)
            settings=subsystem.get_lod_build_settings(mesh,0)
            for k,v in {'use_full_precision_u_vs':True,'generate_lightmap_u_vs':False,'recompute_normals':False,'recompute_tangents':True,'remove_degenerates':False}.items():settings.set_editor_property(k,v)
            subsystem.set_lod_build_settings(mesh,0,settings)
            assets.set_metadata_tag(mesh,'BreziGeneratedBy',OWNER);assets.set_metadata_tag(mesh,'BreziR18SourceMeshId',row['id'])
            require(assets.save_loaded_asset(mesh,only_if_is_dirty=False),'Cannot save R18 mesh');imported[names[0]]=mesh
    require(set(imported)==set(expected),'Exactly37 imported native meshes required');mesh_helper.finish_static_mesh_compilation(u,synchronous=True)
    meshes={row['id']:imported[row['id']+'_LOD0'] for row in rows}
    for row in rows:native_mesh_proof(u,meshes[row['id']],row)
    for actor in reversed(temporary):require(actors.destroy_actor(actor),'Cannot remove temporary R18 imported actor')
    for pipeline in pipelines:require(assets.save_loaded_asset(pipeline,only_if_is_dirty=False),'Cannot save R18 import pipeline')
    metadata=[];expected_paths={m.get_path_name().split('.')[0] for m in meshes.values()}
    for asset_path in assets.list_assets(PREFIX+'/Geometry',recursive=True,include_folder=False):
        asset=assets.load_asset(asset_path);require(asset,'Unexpected missing R18 imported asset')
        if asset.get_path_name().split('.')[0] in expected_paths:continue
        require(asset.get_class().get_name()=='InterchangeSceneImportAsset','Unexpected R18 importer artifact class')
        metadata.append(asset.get_path_name());require(assets.delete_asset(asset_path),'Cannot remove owned transient scene-reimport metadata')
    return meshes,[p.get_path_name() for p in pipelines],metadata


def apply_scene(u,bundle,rows,meshes,components,rural):
    changes=[];added={};actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    for identity,component in components.items():
        actor=component.get_owner();change={'sourceMeshId':identity,'actor':actor.get_path_name(),'componentName':component.get_name(),'beforeMesh':component.get_editor_property('static_mesh').get_path_name()}
        if identity=='village_0_2_darkroof':
            component.set_visibility(False,False);component.set_hidden_in_game(True,False)
            component.set_editor_property('cast_shadow',False);component.set_editor_property('cast_hidden_shadow',False)
            change.update(operation='hide-empty-source-chunk',afterMesh=change['beforeMesh'],changedFields=['visible','hiddenInGame','cast_shadow','cast_hidden_shadow'])
        else:
            replacement=meshes['neighbor_r18_retained_'+identity];previous=component.get_material(0)
            require(component.set_static_mesh(replacement),'Cannot replace selected original visual chunk')
            require(component.get_material(0)==previous,'Unselected original effective material changed')
            change.update(operation='replace-with-retained-source-chunk',afterMesh=replacement.get_path_name(),changedFields=['mesh'])
        changes.append(change)
    for row in bundle['geometry']['candidateMeshes']:
        actor=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0),u.Rotator());require(actor,'Cannot spawn owned R18 visual')
        actor.set_editor_property('tags',[u.Name(TAG)]);actor.set_actor_label(row['id']);actor.set_folder_path('Brezi/NeighborFinish20261001R18');actor.set_actor_tick_enabled(False)
        component=actor.get_component_by_class(u.StaticMeshComponent);require(component.set_static_mesh(meshes[row['id']]),'Cannot bind R18 candidate mesh')
        rural.new_component_policy(u,component);component.set_editor_property('cast_shadow',bool(row['castShadow']));component.set_cull_distance(65000.)
        added[row['id']]=actor.get_path_name()
    require(len(added)==32,'R18 actor count differs');return changes,added


def verify_scene(u,bundle,rows,mesh_paths,changes,added,materials,mesh_helper,rural):
    actors=u.get_editor_subsystem(u.EditorActorSubsystem);lookup={a.get_path_name():a for a in actors.get_all_level_actors()}
    require({p for p,a in lookup.items() if a.actor_has_tag(TAG)}==set(added.values()),'R18 owned actor inventory differs')
    mesh_helper.finish_static_mesh_compilation(u,synchronous=True);subsystem=mesh_helper.static_mesh_subsystem(u);proofs={}
    for row in rows:
        mesh=u.EditorAssetLibrary.load_asset(mesh_paths[row['id']]);require(mesh and mesh.get_material(0)==materials[row['material']] and not mesh.get_editor_property('has_navigation_data'),'Saved R18 mesh/material/nav binding differs')
        require(not mesh.get_editor_property('nanite_settings').get_editor_property('enabled'),'Unexpected R18 Nanite')
        settings=subsystem.get_lod_build_settings(mesh,0)
        require(settings.get_editor_property('use_full_precision_u_vs') and not settings.get_editor_property('generate_lightmap_u_vs') and not settings.get_editor_property('recompute_normals'),'Saved R18 metric UV/normal build policy differs')
        proofs[row['id']]=native_mesh_proof(u,mesh,row)
    for change in changes:
        actor=lookup[change['actor']];component=next(c for c in actor.get_components_by_class(u.StaticMeshComponent) if c.get_name()==change['componentName'])
        require(component.get_editor_property('static_mesh').get_path_name()==change['afterMesh'],'Old solid source chunk remains behind openings')
        if change['operation']=='hide-empty-source-chunk':require(not component.is_visible() and component.get_editor_property('hidden_in_game') and not component.get_editor_property('cast_shadow') and not component.get_editor_property('cast_hidden_shadow'),'Empty old roof still renders')
    for row in bundle['geometry']['candidateMeshes']:
        actor=lookup[added[row['id']]];component=actor.get_component_by_class(u.StaticMeshComponent)
        require(component.get_editor_property('static_mesh').get_path_name()==mesh_paths[row['id']] and component.get_material(0)==materials[row['material']],'Saved added actor mesh/material differs')
        require(component.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION and str(component.get_collision_profile_name())=='NoCollision' and not component.get_editor_property('can_ever_affect_navigation') and not component.get_editor_property('generate_overlap_events'),'Saved candidate collision/nav differs')
        require(component.is_visible() and not component.get_editor_property('hidden_in_game') and not actor.is_actor_tick_enabled() and not component.is_component_tick_enabled(),'Saved candidate visibility/tick differs')
        require(component.get_editor_property('mobility')==u.ComponentMobility.STATIC and bool(component.get_editor_property('cast_shadow')) is row['castShadow'] and not component.get_editor_property('affect_distance_field_lighting'),'Saved R18 visual mobility/shadow policy differs')
        require(rural.transform(actor.get_actor_transform())==rural.transform(u.Transform()) and rural.transform(component.get_world_transform())==rural.transform(u.Transform()),'Saved source world-space placement differs')
        require(abs(component.get_editor_property('ld_max_draw_distance')-65000)<.1,'Saved R18 visual cull differs')
    return {'meshProofs':proofs,'meshCount':37,'candidateMeshCount':32,'candidateTriangles':5095,'retainedTriangles':1720,
            'allNativeF32PositionUVTopologyOrderVerified':True,'nativeWindowOpeningsVerified':35,
            'old919TargetTrianglesRetiredFromRendering':True,'oldSourceAssetsPreserved':True,
            'allAddedVisualsNoCollision':True,'nativeNormalTangentReadbackAvailable':False,'nativeAppearanceAccepted':False}


def main():
    import unreal as u
    output=Path(os.environ['BREZI_NEIGHBOR_OUTPUT']).resolve();baseline=Path(os.environ.get('BREZI_NEIGHBOR_BASELINE',str(DEFAULT_BASELINE))).resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and baseline==DEFAULT_BASELINE and output!=baseline and not output.is_relative_to(baseline) and not baseline.is_relative_to(output),'Independent isolated original R16 native clone required')
    project=output/'Project/BreziTwin';content=project/'Content';baseline_project=baseline/'Project/BreziTwin';baseline_content=baseline_project/'Content'
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project,'Wrong native project: never apply to original baseline')
    receipt=DEFAULT_BASELINE/'exterior-import-report.json';require(sha(receipt)==BASELINE_REPORT_SHA,'Frozen R16 native baseline receipt drift')
    baseline_report=read(receipt);require(baseline_report['status']=='exterior-import-validated' and baseline_report['activeDesign']==guard.DESIGN and baseline_report['setbacksMm']=={'street':3000,'east':3000},'Validated R16 C/B/B baseline required')
    bundle=guard.validated_candidate();rows=export_records(bundle);materials_helper=module('neighbor_finish_materials','exterior-neighbor-finish-materials.py')
    diagnostic=module('neighbor_finish_diagnostic','exterior-neighbor-finish-diagnostic-r3.py');supplement=diagnostic.validated_supplement()
    existing=module('neighbor_existing_material_witness','exterior-materials.py');rural=module('neighbor_rural_readback','rural-import.py');base=module('neighbor_actor_witness','performance-optimize.py');mesh_helper=module('neighbor_compilation','lawn-geometry.py')
    report_path=output/'neighbor-finish-overlay-report-r2.json';require(not report_path.exists(),'Fresh isolated overlay report required')
    baseline_rows=detailed_inventory(baseline_content);baseline_before={p:r['sha256'] for p,r in baseline_rows.items()};before=inventory(content)
    original_receipt_hashes={str(Path(p).relative_to(baseline_content)):h for p,h in baseline_report['afterAssetHashes'].items()}
    require(baseline_before==original_receipt_hashes,'Actual original R16 Content differs from frozen saved native receipt')
    require(set(before)==set(baseline_before) and all(before[p]==h for p,h in baseline_before.items() if p!='Data/viewpoints.json'),'Candidate Content must preserve all original R16 assets/data')
    require(before['Data/viewpoints.json'] in [supplement['originalViewpoints']['sha256'],supplement['appendedViewpoints']['sha256']],'Only typed R2 diagnostic viewpoint delta is allowed')
    require(not any(p.startswith('Brezi/NeighborFinish20261001R18/') for p in before),'Fresh R18 asset namespace required')
    protected_before=protected_project_proof(baseline_project,project);native_module=native_module_witness(project,baseline_project)
    clone_receipt=output/'neighbor-finish-project-clone.json';clone=read(clone_receipt)
    require(clone['status']=='verified-byte-identical-independent-apfs-r18-project-clone-before-neighbor-native' and clone['nativeExecuted'] is False and clone['baseNativeReport']==pin(receipt) and clone['selectedPlan']==pin(guard.STUDY/'neighbor-finish-plan.json'),'Typed parent clone provenance differs')
    clone_protected={str(Path(row['destination']).relative_to(project)):row for row in clone['files'] if Path(row['destination']).relative_to(project).parts[0]!='Content'}
    require(clone_protected==protected_before['files'] and clone['fileCount']==len(clone['files'])==len(baseline_rows)+protected_before['fileCount'],'Original protected project differs from independently pinned clone receipt')
    checkpoint=output/'neighbor-finish-checkpoint';require(not checkpoint.exists(),'Fresh native checkpoint required');checkpoint.mkdir()
    base_inventory_file=checkpoint/'base-content-inventory.json';write(base_inventory_file,baseline_rows)
    protected_before_file=checkpoint/'protected-project-before.json';write(protected_before_file,protected_before)
    supplement_path=diagnostic.OUTPUT/'neighbor-finish-diagnostic-supplement.json'
    inputs={**bundle['inputPins'],str(receipt):BASELINE_REPORT_SHA,str(clone_receipt):sha(clone_receipt),**supplement['inputFiles'],str(supplement_path):sha(supplement_path),supplement['appendedViewpoints']['path']:supplement['appendedViewpoints']['sha256']}
    pipelines={str(ROOT/filename):sha(ROOT/filename) for filename in [OWNER,'scripts/unreal/exterior-neighbor-finish-guards.py','scripts/unreal/exterior-neighbor-finish-materials.py','scripts/unreal/exterior-neighbor-finish-diagnostic-r3.py','scripts/unreal/exterior-materials.py','scripts/unreal/rural-import.py','scripts/unreal/performance-optimize.py','scripts/unreal/lawn-geometry.py','scripts/unreal/performance_scene_policy.py']}
    report={'schemaVersion':2,'owner':OWNER,'status':'neighbor-finish-native-overlay-running','startedAt':now(),'output':str(output),'project':str(project),'baseline':str(baseline),'nativeProcessId':os.getpid(),'inputFiles':inputs,'pipelineFiles':pipelines,
            'activeDesign':guard.DESIGN,'setbacksMm':{'street':3000,'east':3000},'sourceStudy':pin(guard.STUDY/'neighbor-finish-plan.json'),'sourceAudit':bundle['audit'],'baseNativeReport':pin(receipt),
            'baseContentInventory':pin(base_inventory_file),'projectClone':pin(clone_receipt),'protectedProjectBefore':pin(protected_before_file),'nativeModuleWitness':native_module,'diagnosticSupplement':pin(supplement_path),'beforeContentHashes':before,
            'nativeApplied':False,'nativeWindowOpeningsVerified':False,'nativeAppearanceAccepted':False,'performanceAccepted':False,'fullPhotorealismAccepted':False,'shippingVerified':False,'packageVerified':False}
    write(report_path,report)
    try:
        report['diagnosticViewpoint']=diagnostic.append_to_clone(project,supplement)
        report['diagnosticViewpoint']['nativeCameraReadbackAvailable']=False
        report['diagnosticViewpoint']['nativeCameraEvidenceLimit']='The saved viewpoint JSON is exact; actual native camera transform is a subsequent matched capture receipt, not a saved camera actor.'
        actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False) and levels.load_level(MAP),'Cannot load cloned R16 map')
        shutil.copy2(content/'Brezi/Maps/Brezi.umap',checkpoint/'Brezi.umap')
        components=affected_components(u,actors,baseline_report,bundle)
        before_witness=original_witness(u,actors,base);before_witness_file=checkpoint/'original-actor-witness.json';write(before_witness_file,before_witness);report['beforeActorWitness']=pin(before_witness_file)
        protected_materials=original_material_witness(u,baseline_report,existing.graph_snapshot,materials_helper);material_witness_file=checkpoint/'original-material-texture-witness.json';write(material_witness_file,protected_materials);report['originalMaterialTextureWitness']=pin(material_witness_file)
        native_materials,material_report=materials_helper.build_materials(u,bundle['recipes'],existing.graph_snapshot)
        native_materials.update({name:u.EditorAssetLibrary.load_asset(baseline_report['materials']['materials'][name]['asset']) for name in set(r['material'] for r in rows)-set(native_materials)})
        require(all(native_materials.values()),'Original retained material lookup missing')
        glb=output/'neighbor-finish-overlay.glb';write_glb(glb,rows);report['sourceGLB']=decode_glb(glb,rows);report['sourceGLB']['path']=str(glb)
        meshes,pipeline_assets,discarded_metadata=import_geometry(u,glb,rows,native_materials,mesh_helper)
        changes,added=apply_scene(u,bundle,rows,meshes,components,rural)
        expected_witness=guard.expected_original_witness(before_witness,changes);expected_witness_file=checkpoint/'expected-original-actor-witness.json';write(expected_witness_file,expected_witness);report['expectedActorWitness']=pin(expected_witness_file)
        after_witness=original_witness(u,actors,base);guard.verify_original_witness(before_witness,after_witness,changes,list(added.values()))
        report.update(materials=material_report,componentChanges=changes,addedActors=added,meshes={k:v.get_path_name() for k,v in meshes.items()},importPipelineAssets=pipeline_assets,discardedTransientImportMetadata=discarded_metadata,beforeActorWitnessSha256=digest(before_witness),afterActorWitnessSha256=digest(after_witness))
        verify_scene(u,bundle,rows,report['meshes'],changes,added,native_materials,mesh_helper,rural)
        require(levels.save_current_level(),'Cannot save candidate neighbor overlay map')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False) and levels.load_level(MAP),'Cannot reload saved neighbor overlay map')
        saved_materials=materials_helper.verify_materials(u,material_report,existing.graph_snapshot)
        saved_materials.update({name:u.EditorAssetLibrary.load_asset(baseline_report['materials']['materials'][name]['asset']) for name in set(r['material'] for r in rows)-set(saved_materials)})
        report['savedReadback']=verify_scene(u,bundle,rows,report['meshes'],changes,added,saved_materials,mesh_helper,rural)
        saved_witness=original_witness(u,actors,base);report['originalActorReadback']=guard.verify_original_witness(before_witness,saved_witness,changes,list(added.values()))
        require(saved_witness==after_witness,'Full original-plus32-added actor witness changed after reload')
        saved_witness_file=checkpoint/'saved-actor-witness.json';write(saved_witness_file,saved_witness);report['savedActorWitness']=pin(saved_witness_file);report['savedActorWitnessSha256']=digest(saved_witness)
        protected_after_materials=original_material_witness(u,baseline_report,existing.graph_snapshot,materials_helper);require(protected_after_materials==protected_materials,'Original42graphs/74textureobjects changed after reload')
        saved_material_witness_file=checkpoint/'saved-original-material-texture-witness.json';write(saved_material_witness_file,protected_after_materials);report['savedOriginalMaterialTextureWitness']=pin(saved_material_witness_file)
        after_rows=detailed_inventory(content);after={p:r['sha256'] for p,r in after_rows.items()};after_inventory_file=checkpoint/'after-content-inventory.json';write(after_inventory_file,after_rows);report['afterContentInventory']=pin(after_inventory_file)
        new_assets=list(report['meshes'].values())+[r['asset'] for r in material_report['materials'].values()]+[r['asset'] for r in material_report['textures'].values()]+pipeline_assets
        require(len(new_assets)==len(set(new_assets))==52,'Exactly37meshes9materials3textures3pipelines required')
        packages={p.split('.')[0].removeprefix('/Game/') for p in new_assets};report['contentProtection']=guard.validate_content_delta(baseline_before,after,supplement,packages)
        require(detailed_inventory(baseline_content)==baseline_rows,'Original baseline Content bytes changed')
        protected_after=protected_project_proof(baseline_project,project);require(protected_after==protected_before and native_module_witness(project,baseline_project)==native_module,'Original132 project files/native module changed')
        protected_file=checkpoint/'protected-project-proof.json';write(protected_file,protected_after);report['protectedProjectProof']=pin(protected_file)
        require((content/'Data/viewpoints.json').read_bytes()==Path(supplement['appendedViewpoints']['path']).read_bytes(),'Saved typed diagnostic viewpoint differs')
        for path,h in {**inputs,**pipelines}.items():require(sha(path)==h,'Frozen source/helper changed during native overlay: '+path)
        report.update(status='neighbor-finish-native-overlay-validated',endedAt=now(),afterContentHashes=after,savedReloaded=True,nativeApplied=True,nativeWindowOpeningsVerified=35,originalMaterialGraphsPreserved=42,originalTextureObjectsPreserved=74,originalBaselineProjectBytesPreserved=True)
        write(report_path,report);print(json.dumps({'status':report['status'],'report':str(report_path),'nativeAppearanceAccepted':False}))
    except Exception as error:
        report.update(status='neighbor-finish-native-overlay-failed',endedAt=now(),error=str(error),nativeApplied=False,nativeWindowOpeningsVerified=False,failedContentHashes=inventory(content))
        write(report_path,report);raise


if __name__=='__main__':main()
