"""Standalone R21 foreground overlay. Root alone launches Unreal.

BREZI_FOREGROUND_OUTPUT selects an independent original-R16 clone;
BREZI_FOREGROUND_PREFLIGHT selects the CPU-produced, decoded GLB receipt.
One floor, four own-tag HISM actors, one new masked104-node graph copy and
three new pipeline packages only. No old mesh/material/texture/tree mutation.
"""
from collections import Counter
import argparse
import copy
from datetime import datetime,timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-canopy-foreground-native-r2.py'
spec=importlib.util.spec_from_file_location('foreground_r21_guard',ROOT/'scripts/unreal/exterior-canopy-foreground-guards.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
require,sha,read,digest,pin=guard.require,guard.sha,guard.read,guard.digest,guard.pin
PREFIX,TAG=guard.PREFIX,guard.TAG
MAP='/Game/Brezi/Maps/Brezi'
BASE=ROOT/'output/unreal/exterior-20261001-r16a'
REPORT='foreground-overlay-report-r2.json'


def write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def now():return datetime.now(timezone.utc).isoformat()
def vec(v,axes='xyz'):return [float(getattr(v,k))for k in axes]


def owned_hism_root(actor,component):
    # Actor.h RootComponent is reflected through BlueprintGetter; the plain
    # C++ GetRootComponent is inline and is not a Python method in UE5.8.
    return actor.get_editor_property('root_component')==component and component.get_owner()==actor


def primary_actor_api():
    path=Path('/Users/Shared/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Classes/GameFramework/Actor.h')
    require(sha(path)=='255c6a18c75d860e38282c7ec1561a72c9f2d4b19b41043a0df5ba668659dba9','Reviewed installed Actor.h API bytes changed')
    text=path.read_text();require('UPROPERTY(BlueprintGetter=K2_GetRootComponent' in text and 'TObjectPtr<USceneComponent> RootComponent;' in text and 'inline USceneComponent* GetRootComponent() const' in text,'Reviewed reflective root-property API differs')
    return pin(path)


def world_position_offsets(u,material):
    return {str(n.get_editor_property('desc')):str(n.get_editor_property('world_position_shader_offset'))for n in u.MaterialEditingLibrary.get_material_expressions(material)if n.get_class().get_name()=='MaterialExpressionWorldPosition'}


def write_glb(path,mesh):
    binary=bytearray();accessors=[];views=[]
    def accessor(values,kind,component=5126,target=34962):
        flat=[v for row in values for v in (row if isinstance(row,(list,tuple))else[row])]
        binary.extend(b'\0'*((-len(binary))%4));start=len(binary)
        binary.extend(struct.pack('<'+('f'if component==5126 else'I')*len(flat),*flat))
        views.append({'buffer':0,'byteOffset':start,'byteLength':len(binary)-start,'target':target})
        row={'bufferView':len(views)-1,'componentType':component,'count':len(values),'type':kind}
        if kind=='VEC3':row.update(min=[min(v[k]for v in values)for k in range(3)],max=[max(v[k]for v in values)for k in range(3)])
        accessors.append(row);return len(accessors)-1
    points=mesh['verticesCm'];normals=[[0.,0.,0.]for _ in points]
    for j in range(0,len(mesh['indices']),3):
        ids=mesh['indices'][j:j+3];a,b,c=[points[i]for i in ids];v=[c[k]-a[k]for k in range(3)];w=[b[k]-a[k]for k in range(3)]
        n=[v[1]*w[2]-v[2]*w[1],v[2]*w[0]-v[0]*w[2],v[0]*w[1]-v[1]*w[0]]
        for i in ids:normals[i]=[normals[i][k]+n[k]for k in range(3)]
    normals=[[v/math.sqrt(sum(k*k for k in n))for v in n]for n in normals]
    attributes={'POSITION':accessor([[x/100,z/100,y/100]for x,y,z in points],'VEC3'),
                'NORMAL':accessor([[x,z,y]for x,y,z in normals],'VEC3'),
                'TEXCOORD_0':accessor(mesh['uv0'],'VEC2'),'TEXCOORD_1':accessor(mesh['uv1'],'VEC2')}
    prim={'attributes':attributes,'indices':accessor(mesh['indices'],'SCALAR',5125,34963),'mode':4}
    name=mesh['id']+'_LOD0';doc={'asset':{'version':'2.0','generator':OWNER},'scene':0,'scenes':[{'nodes':[0]}],'nodes':[{'name':name,'mesh':0}],
        'meshes':[{'name':name,'primitives':[prim]}],'accessors':accessors,'bufferViews':views,'buffers':[{'byteLength':len(binary)}]}
    encoded=json.dumps(doc,separators=(',',':'),allow_nan=False).encode();encoded+=b' '*((-len(encoded))%4);binary+=b'\0'*((-len(binary))%4)
    Path(path).write_bytes(struct.pack('<III',0x46546c67,2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary)


def decode_glb(path,mesh):
    payload=Path(path).read_bytes();magic,version,total=struct.unpack_from('<III',payload)
    require((magic,version,total)==(0x46546c67,2,len(payload)),'GLB header/length differs')
    size,kind=struct.unpack_from('<II',payload,12);require(kind==0x4e4f534a,'GLB JSON missing')
    doc=json.loads(payload[20:20+size]);offset=20+size;size,kind=struct.unpack_from('<II',payload,offset)
    require(kind==0x004e4942 and offset+8+size==len(payload),'GLB BIN length differs');binary=payload[offset+8:]
    def values(index):
        a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
        require(a['componentType']in(5125,5126) and a['count']>0,'GLB accessor type differs')
        data=struct.unpack_from('<'+('f'if a['componentType']==5126 else'I')*(a['count']*width),binary,v.get('byteOffset',0)+a.get('byteOffset',0))
        return [list(data[j:j+width])for j in range(0,len(data),width)]
    require(len(doc['meshes'])==len(doc['nodes'])==1 and doc['meshes'][0]['name']==mesh['id']+'_LOD0' and len(doc['meshes'][0]['primitives'])==1,'GLB closed mesh/node scope differs')
    primitive=doc['meshes'][0]['primitives'][0];attributes=primitive['attributes']
    require(set(attributes)=={'POSITION','NORMAL','TEXCOORD_0','TEXCOORD_1'} and primitive['mode']==4 and [v[0]for v in values(primitive['indices'])]==mesh['indices'],'GLB ordered indices or attributes differ')
    require(values(attributes['POSITION'])==[[guard.f32(x/100),guard.f32(z/100),guard.f32(y/100)]for x,y,z in mesh['verticesCm']],'GLB exact source F32 axis/metre positions differ')
    for channel,key in ((0,'uv0'),(1,'uv1')):require(values(attributes['TEXCOORD_'+str(channel)])==[[guard.f32(v)for v in row]for row in mesh[key]],'GLB exact F32 UV'+str(channel)+' differs')
    normals=values(attributes['NORMAL']);require(len(normals)==len(mesh['verticesCm']) and all(guard.finite(n,3)and n[1]>0 and abs(sum(v*v for v in n)-1)<2e-6 for n in normals),'Exported artist surface normal invalid')
    return {'meshes':1,'triangles':1843,'orderedIndicesAndPositionsUV0UV1SourceF32Verified':True,'nativeNormalTangentReadbackAvailable':False,'expectedNativeOrderedF32CornersSha256':digest(guard.geometry_corners(mesh))}


def preflight(output):
    require(not output.exists() and output.resolve().is_relative_to(ROOT/'output/unreal'),'Fresh CPU preflight directory required')
    bundle=guard.load_source();actor_api=primary_actor_api();output.mkdir(parents=True);glb=output/'canopy-foreground-r21.glb';write_glb(glb,bundle['geometry']['mesh']);decoded=decode_glb(glb,bundle['geometry']['mesh'])
    pipeline={str(ROOT/'scripts/unreal'/name):value for name,value in guard.DEPENDENCIES.items()}
    for name in (OWNER,'scripts/unreal/exterior-canopy-foreground-guards.py'):pipeline[str(ROOT/name)]=sha(ROOT/name)
    receipt={'schemaVersion':2,'owner':OWNER,'status':'foreground-source-preflight-validated-native-pending','createdAt':now(),'sourceStudy':pin(guard.STUDY/'foreground-transition-plan.json'),
             'sourceAudit':bundle['audit'],'decodedGLB':decoded,'sourceGLB':pin(glb),'runtimeQualitySource':pin(guard.RUNTIME_SOURCE),'primaryActorApi':actor_api,'pipelineFiles':pipeline,'inputFiles':{**{row['path']:row['sha256']for row in bundle['plan']['inputFiles'].values()},str(guard.RUNTIME_SOURCE):guard.RUNTIME_SOURCE_SHA,actor_api['path']:actor_api['sha256']},
             'nativeExecuted':False,'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False}
    write(output/'source-preflight.json',receipt);print(json.dumps({'preflight':pin(output/'source-preflight.json'),'sourceGLB':pin(glb),'sourceAudit':bundle['audit']}))


def validated_preflight(path,bundle):
    receipt=read(path);require(receipt['schemaVersion']==2 and receipt['owner']==OWNER and receipt['status']=='foreground-source-preflight-validated-native-pending' and receipt['nativeExecuted'] is False and receipt['sourceStudy']==pin(guard.STUDY/'foreground-transition-plan.json'),'Typed foreground CPU preflight differs')
    require(receipt['sourceAudit']==bundle['audit'],'Semantic source preflight differs')
    require(receipt['primaryActorApi']==primary_actor_api(),'Reviewed primary Actor root API pin differs')
    require(receipt['runtimeQualitySource']==pin(guard.RUNTIME_SOURCE),'Original C++ runtime classification source differs')
    for path,expected in receipt['pipelineFiles'].items():require(sha(path)==expected,'Executed source pipeline changed: '+path)
    require(str(ROOT/OWNER)in receipt['pipelineFiles'] and str(ROOT/'scripts/unreal/exterior-canopy-foreground-guards.py')in receipt['pipelineFiles'],'Own native/guard source pin missing')
    glb=guard.check_pin(receipt['sourceGLB']);require(decode_glb(glb,bundle['geometry']['mesh'])==receipt['decodedGLB'],'Decoded source GLB differs from source preflight')
    return receipt,glb


def create_material(u,bundle,existing):
    assets=u.EditorAssetLibrary;lib=u.MaterialEditingLibrary;recipe=bundle['material'];target=PREFIX+'/Materials/M_'+guard.MATERIAL_ID
    source=assets.load_asset(recipe['sourceNativeMaterial']);require(source and not assets.does_asset_exist(target),'Fresh copied PBR material required')
    original=existing.graph_snapshot(u,source);require(digest(original)==guard.SOURCE_GRAPH_SHA and len(original['nodes'])==104,'Actual protected104-node meadow graph differs')
    original_offsets=world_position_offsets(u,source)
    material=assets.duplicate_asset(recipe['sourceNativeMaterial'],target);require(material and existing.graph_snapshot(u,material)==original and world_position_offsets(u,material)==original_offsets,'Duplicated original PBR graph/absolute world-position mode differs')
    def node(role,cls):
        result=lib.create_material_expression(material,cls,-700,800);require(result,'Cannot create R21 feather expression');result.set_editor_property('desc',guard.NODE_TAG+role);return result
    uv=node('uv1',u.MaterialExpressionTextureCoordinate);uv.set_editor_property('coordinate_index',1)
    coverage=node('coverage-r',u.MaterialExpressionComponentMask)
    for name,value in {'r':True,'g':False,'b':False,'a':False}.items():coverage.set_editor_property(name,value)
    dither=node('temporal-dither',u.MaterialExpressionMaterialFunctionCall);function=assets.load_asset(recipe['nativeDitherFunction'])
    require(function and dither.set_material_function(function),'Cannot initialize installed native dither function ports')
    alpha=[str(n)for n in lib.get_material_expression_input_names(dither)if 'alpha'in str(n).lower()];require(len(alpha)==1,'Native dither Alpha Threshold input is ambiguous')
    # UE shortens the single mask input to NAME_None; empty name selects the
    # first supported input, exactly as the successful original grove shader.
    require([str(n)for n in lib.get_material_expression_input_names(coverage)]==['None'],'Native mask single input schema differs')
    require(lib.connect_material_expressions(uv,'',coverage,'') and lib.connect_material_expressions(coverage,'',dither,alpha[0]) and lib.connect_material_property(dither,'Result',u.MaterialProperty.MP_OPACITY_MASK),'Cannot connect new UV1 feather root')
    material.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED);material.set_editor_property('opacity_mask_clip_value',.5)
    errors=list(lib.recompile_material(material));require(not errors,'New feather material compile errors: '+str(errors))
    graph=existing.graph_snapshot(u,material);guard.validate_graph_copy(original,graph)
    assets.set_metadata_tag(material,'BreziGeneratedBy',OWNER);assets.set_metadata_tag(material,'BreziSourceStudySha256',guard.PLAN_SHA)
    require(assets.save_loaded_asset(material,False),'Cannot save own feather material')
    return material,{'asset':material.get_path_name(),'sourceAsset':source.get_path_name(),'sourceGraphSha256':digest(original),'graph':graph,'graphSha256':digest(graph),'originalWorldPositionShaderOffsets':original_offsets,'copiedWorldPositionShaderOffsets':world_position_offsets(u,material),'compileErrors':errors,'newNodes':3,'originalPBRNodesPreserved':104,'newTextureObjects':0,'nativeAppearanceAccepted':False}


def native_mesh_proof(u,mesh,row):
    expected=guard.geometry_corners(row);description=mesh.get_static_mesh_description(0)
    require(description and mesh.get_num_lods()==1 and mesh.get_num_triangles(0)==description.get_triangle_count()==1843,'Native floor triangle/LOD count differs')
    observed=[]
    for i in range(1843):
        face=[]
        for corner in range(3):
            vi=description.get_triangle_vertex_instance(u.TriangleID(id_value=i),corner)
            point=vec(description.get_vertex_position(description.get_vertex_instance_vertex(vi)))
            uv0=vec(description.get_vertex_instance_uv(vi,0),'xy');uv1=vec(description.get_vertex_instance_uv(vi,1),'xy');face.append(tuple(point+uv0+uv1))
        observed.append(guard.cyclic(face))
    require(observed==expected,'Actual ordered native F32 position/UV0/UV1/connectivity/winding differs')
    return {'mesh':mesh.get_path_name(),'sourceGeometrySha256':digest(row),'triangles':1843,'orderedNativeF32CornersSha256':digest(observed),'positionUV0UV1TopologyWindingVerified':True,'nativeFloat32RepresentationExact':True,'triangleOrderPreserved':True,'nativeNormalTangentReadbackAvailable':False}


def import_floor(u,glb,bundle,material,compilation):
    assets=u.EditorAssetLibrary;actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem);pipelines=[]
    for original,name in [('GLTFSceneAssets','Assets'),('GLTFMaterials','Materials'),('LevelActors','Level')]:
        destination=PREFIX+'/Pipeline/'+name;require(not assets.does_asset_exist(destination),'Fresh own import pipeline required')
        pipeline=assets.duplicate_asset('/Game/Brezi/Pipeline/'+original,destination);require(pipeline,'Cannot duplicate own import pipeline');pipelines.append(pipeline)
    mp=pipelines[0].get_editor_property('mesh_pipeline')
    for k,v in {'combine_static_meshes_behavior':u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,'collision':False,'build_nanite':False,'generate_lightmap_u_vs':False}.items():mp.set_editor_property(k,v)
    common=pipelines[0].get_editor_property('common_meshes_properties')
    for k,v in {'remove_degenerates':False,'recompute_normals':False,'recompute_tangents':True,'use_full_precision_u_vs':True}.items():common.set_editor_property(k,v)
    materials=pipelines[0].get_editor_property('material_pipeline');materials.set_editor_property('import_materials',False);materials.get_editor_property('texture_pipeline').set_editor_property('import_textures',False)
    pipelines[2].set_editor_property('scene_hierarchy_type',u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
    params=u.ImportAssetParameters()
    for k,v in {'is_automated':True,'replace_existing':False,'force_show_dialog':False,'override_pipelines':[u.SoftObjectPath(p.get_path_name())for p in pipelines],'import_level':levels.get_current_level()}.items():params.set_editor_property(k,v)
    before={a.get_path_name()for a in actors.get_all_level_actors()};manager=u.InterchangeManager.get_interchange_manager_scripted();require(manager.import_scene(PREFIX+'/Geometry',manager.create_source_data(str(glb)),params),'R21 source floor GLB import failed')
    temporary=[a for a in actors.get_all_level_actors()if a.get_path_name()not in before];meshes={}
    for actor in temporary:
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            mesh=c.get_editor_property('static_mesh');require(mesh and mesh.get_path_name().startswith(PREFIX+'/Geometry/')and guard.MESH_ID+'_LOD0'in mesh.get_name(),'Unexpected imported floor mesh')
            meshes[mesh.get_path_name()]=mesh
    require(len(meshes)==1,'Exactly one native floor mesh required');mesh=next(iter(meshes.values()));mesh.set_material(0,material);mesh.set_editor_property('has_navigation_data',False)
    subsystem=compilation.static_mesh_subsystem(u);settings=subsystem.get_lod_build_settings(mesh,0)
    for k,v in {'use_full_precision_u_vs':True,'generate_lightmap_u_vs':False,'recompute_normals':False,'recompute_tangents':True,'remove_degenerates':False}.items():settings.set_editor_property(k,v)
    subsystem.set_lod_build_settings(mesh,0,settings);require(not mesh.get_editor_property('nanite_settings').get_editor_property('enabled'),'New floor Nanite must remain false')
    assets.set_metadata_tag(mesh,'BreziGeneratedBy',OWNER);assets.set_metadata_tag(mesh,'BreziSourceStudySha256',guard.PLAN_SHA)
    require(assets.save_loaded_asset(mesh,False),'Cannot save own source floor');compilation.finish_static_mesh_compilation(u,synchronous=True);native_mesh_proof(u,mesh,bundle['geometry']['mesh'])
    for actor in reversed(temporary):require(actors.destroy_actor(actor),'Cannot remove own temporary floor importer actor')
    for pipeline in pipelines:require(assets.save_loaded_asset(pipeline,False),'Cannot save own pipeline')
    removed=[]
    for path in assets.list_assets(PREFIX+'/Geometry',recursive=True,include_folder=False):
        if path.split('.')[0]==mesh.get_path_name().split('.')[0]:continue
        asset=assets.load_asset(path);require(asset and asset.get_class().get_name()=='InterchangeSceneImportAsset','Unexpected new importer package')
        removed.append(asset.get_path_name());require(assets.delete_asset(path),'Cannot remove own transient reimport metadata')
    return mesh,[p.get_path_name()for p in pipelines],removed


def apply_scene(u,bundle,mesh,rural):
    actors=u.get_editor_subsystem(u.EditorActorSubsystem);added={}
    def configure(actor,identity):
        require(actor,'Cannot create own R21 actor');actor.tags=[u.Name('BreziGenerated'),u.Name(TAG)];actor.set_actor_label(identity);actor.set_folder_path('Brezi/CanopyForeground20261002R21');actor.set_actor_tick_enabled(False)
        c=actor.get_component_by_class(u.StaticMeshComponent);require(c,'New R21 component missing');rural.new_component_policy(u,c)
        c.set_editor_property('cast_shadow',False);c.set_editor_property('visible_in_ray_tracing',True);added[identity]=actor.get_path_name();return c
    floor=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0),u.Rotator());c=configure(floor,guard.MESH_ID);c.set_static_mesh(mesh);c.set_cull_distance(6000.)
    for group in bundle['roots']['groups']:
        actor=actors.spawn_actor_from_class(u.load_class(None,'/Script/BreziTwin.BreziVegetationPatch'),u.Vector(0,0,0),u.Rotator());c=configure(actor,group['id']);actor.tags=[u.Name('BreziGenerated'),u.Name(TAG),u.Name('BreziLawnDetail')];c.set_static_mesh(u.EditorAssetLibrary.load_asset(group['nativeMesh']))
        require(c.get_editor_property('static_mesh'),'Existing native source master missing');c.set_cull_distances(4500,6000);require(actor.set_detail_density_scaling(True),'Cannot enable detail density on own NoCollision HISM')
        indices=list(c.add_instances([rural.instance_transform(u,r)for r in group['instances']],True,False,False));require(indices==list(range(len(group['instances']))),'Own closed-group root insertion order differs');actor.synchronize_instance_bounds()
    return added


def verify_scene(u,bundle,added,mesh_path,material_path,rural,existing,compilation):
    actors={a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()};require({p for p,a in actors.items()if a.actor_has_tag(TAG)}==set(added.values()) and set(added)=={guard.MESH_ID}|{g['id']for g in bundle['roots']['groups']},'Closed own R21 actor namespace differs')
    assets=u.EditorAssetLibrary;mesh=assets.load_asset(mesh_path);material=assets.load_asset(material_path);require(mesh and material and mesh.get_material(0)==material and not mesh.get_editor_property('has_navigation_data')and not mesh.get_editor_property('nanite_settings').get_editor_property('enabled'),'Saved floor material/nav/Nanite differs')
    compilation.finish_static_mesh_compilation(u,synchronous=True);proof=native_mesh_proof(u,mesh,bundle['geometry']['mesh']);graph=existing.graph_snapshot(u,material);original=bundle['inputs']['nativeR16']['materials']['materials']['context_meadow']['graph'];guard.validate_graph_copy(original,graph)
    offsets=world_position_offsets(u,material);source_offsets=world_position_offsets(u,assets.load_asset(bundle['material']['sourceNativeMaterial']));require(offsets==source_offsets,'Saved copied world-position shader mode differs')
    rows=[]
    for identity,path in added.items():
        actor=actors[path];c=actor.get_component_by_class(u.StaticMeshComponent)
        require(c and not actor.is_actor_tick_enabled()and not c.is_component_tick_enabled()and c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION and str(c.get_collision_profile_name())=='NoCollision' and not c.get_editor_property('can_ever_affect_navigation')and not c.get_editor_property('generate_overlap_events'),'Saved new actor tick/collision/nav differs')
        require(c.is_visible()and not c.get_editor_property('hidden_in_game')and not c.get_editor_property('cast_shadow')and c.get_editor_property('visible_in_ray_tracing'),'Saved new actor render policy differs')
        require(rural.transform(actor.get_actor_transform())==rural.transform(u.Transform())and rural.transform(c.get_world_transform())==rural.transform(u.Transform()),'New actor/component origin differs')
        if identity==guard.MESH_ID:require(c.get_editor_property('static_mesh')==mesh and c.get_editor_property('ld_max_draw_distance')==6000.,'Floor origin/master/cull differs');continue
        group=next(g for g in bundle['roots']['groups']if g['id']==identity);master=c.get_editor_property('static_mesh');model=bundle['roots']['models'][group['meshId']]
        require(isinstance(c,u.HierarchicalInstancedStaticMeshComponent)and owned_hism_root(actor,c) and master.get_path_name()==group['nativeMesh']and c.get_instance_count()==len(group['instances'])and actor.get_detail_density_scaling()and actor.actor_has_tag('BreziLawnDetail')and c.get_editor_property('instance_start_cull_distance')==4500 and c.get_editor_property('instance_end_cull_distance')==6000,'Saved own HISM identity/count/density/quality-classification/cull differs')
        require([c.get_material(i).get_path_name()for i in range(c.get_num_materials())]==group['nativeMaterials']and [master.get_material(i).get_path_name()for i in range(len(master.get_editor_property('static_materials')))]==group['nativeMaterials'],'Original master material binding differs')
        screens=list(compilation.static_mesh_subsystem(u).get_lod_screen_sizes(master));require(master.get_num_lods()==3 and screens==model['lodScreens']and [master.get_num_triangles(i)for i in range(3)]==[v['triangles']for v in model['decodedLods']],'Existing master LOD census/screens differs')
        observed=[]
        for i,row in enumerate(group['instances']):
            actual=rural.transform(rural.instance_value(c,i));wanted=rural.transform(rural.instance_transform(u,row))
            require(max(abs(a-b)for key in ('translation','scale3d')for a,b in zip(actual[key],wanted[key]))<.003 and min(max(abs(a-sign*b)for a,b in zip(actual['rotation'],wanted['rotation']))for sign in(-1,1))<.00003,'Saved ordered native root position/uniformscale/yaw differs')
            observed.append(actual)
        rows.append({'id':identity,'actor':path,'meshId':group['meshId'],'nativeMesh':master.get_path_name(),'materials':group['nativeMaterials'],'instances':len(observed),'orderedInstanceTransformsSha256':digest(observed),'allOrderedSourceTransformsCompared':True,'translationScaleToleranceCm':.003,'quaternionTolerance':.00003,'detailDensityScaling':True,'cullCm':[4500,6000],'lodTriangles':[master.get_num_triangles(i)for i in range(3)],'lodScreens':screens,'ownNamespaceVerified':True,'runtimeQualityClassificationTag':'BreziLawnDetail','runtimeQualityPredicateSourceVerified':True})
    require(sum(r['instances']for r in rows)==512,'Saved512 root census differs')
    return {'floor':proof,'materialGraph':graph,'materialGraphSha256':digest(graph),'worldPositionShaderOffsets':offsets,'groups':rows,'savedGroups':4,'savedInstances':512,'allNewVisualsNoCollision':True,'runtimeQualityPredicateSourceVerified':True,'runtimeQualityLightingDiagnosticReadbackAvailable':False,'runtimeQualityLimit':'Own owner tag plus standard BreziLawnDetail classification meets the unchanged R16 C++ predicate; actual runtime lighting/profile behavior is subsequent capture evidence.'}


def main():
    import unreal as u
    output=Path(os.environ['BREZI_FOREGROUND_OUTPUT']).resolve();project=output/'Project/BreziTwin';base_project=BASE/'Project/BreziTwin';content=project/'Content';base_content=base_project/'Content'
    require(output.is_relative_to(ROOT/'output/unreal')and output!=BASE and Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project,'Require own isolated R16 clone')
    require(not(output/REPORT).exists(),'Fresh foreground native report required');bundle=guard.load_source();preflight_path=Path(os.environ['BREZI_FOREGROUND_PREFLIGHT']).resolve();preflight,glb=validated_preflight(preflight_path,bundle)
    generic=guard.module('exterior-neighbor-finish-native-r3.py');existing=guard.module('exterior-materials.py');texture_helper=guard.module('exterior-neighbor-finish-materials.py');rural=guard.module('rural-import.py');performance=guard.module('performance-optimize.py');compilation=guard.module('lawn-geometry.py')
    base_report_path=BASE/'exterior-import-report.json';require(sha(base_report_path)==guard.BASE_REPORT_SHA,'Original R16 saved receipt drift');baseline=bundle['inputs']['nativeR16'];base_rows=generic.detailed_inventory(base_content);before=generic.detailed_inventory(content)
    receipt_rows={str(Path(p).relative_to(base_content)):h for p,h in baseline['afterAssetHashes'].items()};require({p:r['sha256']for p,r in base_rows.items()}==receipt_rows and before==base_rows and len(before)==3975,'All3975 candidate Content bytes must match frozen original R16')
    require(all((base_content/p).stat().st_ino!=(content/p).stat().st_ino for p in base_rows),'All3975 candidate Content files require independent inodes')
    protected=generic.protected_project_proof(base_project,project);protected['owner']=OWNER;protected['status']='foreground-protected-project-byte-validated';require(protected['fileCount']==132,'Original132 protected files required');native_module=generic.native_module_witness(project,base_project)
    clone_path=output/'foreground-project-clone.json';clone=read(clone_path);guard.validate_clone(clone,base_rows,protected,base_project,project)
    for key in ('byteValidationHelper','baseByteInventoryReferencePlan'):guard.check_pin(clone[key])
    checkpoint=output/'foreground-native-checkpoint';require(not checkpoint.exists(),'Fresh native foreground checkpoint required');checkpoint.mkdir();base_inventory_file=checkpoint/'base-content-inventory.json';protected_before_file=checkpoint/'protected-before.json';write(base_inventory_file,base_rows);write(protected_before_file,protected)
    report={'schemaVersion':2,'owner':OWNER,'status':'foreground-native-overlay-running','startedAt':now(),'output':str(output),'project':str(project),'baseline':str(BASE),'nativeProcessId':os.getpid(),
        'sourceStudy':pin(guard.STUDY/'foreground-transition-plan.json'),'sourcePreflight':pin(preflight_path),'baseNativeReport':pin(base_report_path),'projectClone':pin(clone_path),'sourceAudit':bundle['audit'],'pipelineFiles':preflight['pipelineFiles'],
        'inputFiles':{**preflight['inputFiles'],bundle['plan']['geometry']['path']:bundle['plan']['geometry']['sha256'],bundle['plan']['roots']['path']:bundle['plan']['roots']['sha256'],bundle['plan']['materialRecipe']['path']:bundle['plan']['materialRecipe']['sha256'],str(preflight_path):sha(preflight_path),str(glb):sha(glb),str(clone_path):sha(clone_path),**{clone[k]['path']:clone[k]['sha256']for k in ('byteValidationHelper','baseByteInventoryReferencePlan')}},
        'baseContentInventory':pin(base_inventory_file),'protectedProjectBefore':pin(protected_before_file),'nativeModuleWitness':native_module,'activeDesign':guard.DESIGN,'setbacksMm':{'street':3000,'east':3000},
        'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,'landUseObserved':False,'measuredElevation':False}
    report_path=output/REPORT;write(report_path,report)
    try:
        actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem);require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot load cloned original R16 map')
        before_actors=generic.original_witness(u,actors,performance);require(len(before_actors)==5306,'Original5306 actors required');before_materials=generic.original_material_witness(u,baseline,existing.graph_snapshot,texture_helper)
        before_actor_file=checkpoint/'before-actor-witness.json';material_file=checkpoint/'original-material-texture-witness.json';write(before_actor_file,before_actors);write(material_file,before_materials);report.update(beforeActorWitness=pin(before_actor_file),originalMaterialTextureWitness=pin(material_file));write(report_path,report)
        material,material_report=create_material(u,bundle,existing);mesh,pipelines,metadata=import_floor(u,glb,bundle,material,compilation);added=apply_scene(u,bundle,mesh,rural)
        applied=verify_scene(u,bundle,added,mesh.get_path_name(),material.get_path_name(),rural,existing,compilation)
        applied_actors=generic.original_witness(u,actors,performance);expected=copy.deepcopy(before_actors)
        for path in added.values():expected[path]=applied_actors[path]
        guard.validate_actor_delta(before_actors,expected,applied_actors,list(added.values()));expected_file=checkpoint/'expected-actor-witness.json';write(expected_file,expected)
        require(levels.save_current_level(),'Cannot save own additive foreground map');require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot reload saved foreground map')
        saved=verify_scene(u,bundle,added,mesh.get_path_name(),material.get_path_name(),rural,existing,compilation);require(saved==applied,'Saved/reloaded foreground mesh/graph/groups differ')
        after_actors=generic.original_witness(u,actors,performance);guard.validate_actor_delta(before_actors,expected,after_actors,list(added.values()))
        after_materials=generic.original_material_witness(u,baseline,existing.graph_snapshot,texture_helper);require(before_materials==after_materials,'Original42graphs74textures changed')
        after=generic.detailed_inventory(content);known=[mesh.get_path_name(),material.get_path_name(),*pipelines];packages=[p.split('.')[0].replace('/Game/','')+'.uasset'for p in known];guard.validate_content_delta(before,after,packages)
        protected_after=generic.protected_project_proof(base_project,project);protected_after['owner']=OWNER;protected_after['status']='foreground-protected-project-byte-validated';require(protected_after==protected,'Original132 protected bytes/inodes changed')
        saved_actor_file=checkpoint/'saved-actor-witness.json';after_content_file=checkpoint/'after-content-inventory.json';protected_file=checkpoint/'protected-after.json';write(saved_actor_file,after_actors);write(after_content_file,after);write(protected_file,protected_after)
        for path,h in report['inputFiles'].items():require(sha(path)==h,'Consumed source changed during native overlay')
        for path,h in report['pipelineFiles'].items():require(sha(path)==h,'Executed pipeline changed during native overlay')
        report.update(status='foreground-native-overlay-validated',completedAt=now(),savedReloaded=True,nativeApplied=True,savedReadback=saved,newMaterial=material_report,newMesh=mesh.get_path_name(),importPipelineAssets=pipelines,removedOwnedReimportMetadata=metadata,addedActors=added,
            expectedActorWitness=pin(expected_file),savedActorWitness=pin(saved_actor_file),beforeActorWitnessSha256=digest(before_actors),expectedActorWitnessSha256=digest(expected),savedActorWitnessSha256=digest(after_actors),
            originalActorCount=5306,savedActorCount=5311,allOriginalActorsAndWitnessedPoliciesPreserved=True,originalMaterialTextureBeforeSha256=digest(before_materials),originalMaterialTextureSavedSha256=digest(after_materials),originalMaterialGraphsPreserved=42,originalTextureObjectsPreserved=74,
            originalPlantMeshesPreserved=len(baseline['savedPlantReadback']),originalPlantLODsPreserved=sum(len(p['lodTriangles'])for p in baseline['savedPlantReadback']),protectedProjectProof=pin(protected_file),afterContentInventory=pin(after_content_file),newContentPackages=packages,newContentPackageCount=5,newTextureObjects=0,onlyOriginalMapChanged=True,nativeNormalTangentReadbackAvailable=False)
        write(report_path,report);print(json.dumps({'report':pin(report_path),'status':report['status'],'savedGroups':4,'savedInstances':512,'surfaceTriangles':1843}))
    except Exception as error:
        report.update(status='foreground-native-overlay-failed',failedAt=now(),error=str(error));write(report_path,report);raise


if __name__=='__main__':
    if '--preflight'in sys.argv:
        parser=argparse.ArgumentParser();parser.add_argument('--preflight',type=Path,required=True);args=parser.parse_args();preflight(args.preflight.resolve())
    else:main()
