"""Root-only whole-original Periwinkle garden overlay on actual saved R34.

Four entire old low components clear. Six original forms keep original wrapped
XY/rotation; declared bottom offsets and uniform scales are measured before
mutation. All53 heroes/flowers,36 ferns and unrelated raw controls stay exact.
"""
import argparse
from datetime import datetime,timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import subprocess
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-garden-periwinkle-native-r36-r2.py'
s=importlib.util.spec_from_file_location('r36_r2_owned_native_guards',ROOT/'scripts/unreal/exterior-garden-periwinkle-native-guards-r36-r2.py')
guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard)
require,read,sha,pin,check_pin,digest,exact,write=(getattr(guard,k)for k in ['require','read','sha','pin','check_pin','digest','exact','write'])
MAP='/Game/Brezi/Maps/Brezi'
REPORT='garden-periwinkle-native-report-r2.json'
STATUS='verified-saved-384-original-periwinkle-low-garden-composition'
PREFIX=guard.PREFIX
TEST_COUNT=29 # Seventeen native-route fixtures plus twelve immutable-source/R2 provenance fixtures.
def now():return datetime.now(timezone.utc).isoformat()
def report_write(path,row):Path(path).write_text(json.dumps(row,indent=2,allow_nan=False)+'\n')
def actors(u):return {a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
def helpers(base):
 require(set(base['bundle'])=={'source','base','groups','reference'},'Exact actual R34 source/base/groups/reference packet required')
 return base['native'].helpers(base['bundle']['base'])


def garden_controls(u,bundle,h,witness,retired=False):
 result={};cleared={v['actor']for v in bundle['groups'].values()}if retired else set()
 for actor,original in bundle['originalControls'].items():
  wanted={**original}
  if actor in cleared:
   for key in ('rootIds','recoveredValues','storedMatrices'):wanted[key]=[]
  row=bundle['base']['witness'][actor];component=row['components'][0]['name'];c=h['cleanNative'].component_lookup(u,actor,component)
  require(c.get_instance_count()==len(wanted['rootIds']),'Actual original garden component member count differs')
  observed={'rootIds':wanted['rootIds'],'recoveredValues':[h['tree'].transform_value(h['tree'].instance_value(c,i))for i in range(c.get_instance_count())],
   'storedMatrices':[h['tree'].matrix(c,i)for i in range(c.get_instance_count())],
   'mainRandomSeed':int(c.get_editor_property('instancing_random_seed')),'numCustomDataFloats':int(c.get_editor_property('num_custom_data_floats')),
   'customData':[float(v)for v in c.get_editor_property('per_instance_sm_custom_data')],
   'additionalRandomSeedsReadbackAvailable':False,'seedRangesReconstructed':False}
  exact(observed,wanted,'Actual original garden raw matrices/order/mainseed/custom data differ')
  require(digest(observed['recoveredValues'])==witness[actor]['components'][0]['orderedInstanceTransformsSha256'],'Original garden actual frames must bind full scene witness')
  result[actor]=observed
 require(len(result)==19 and sum(len(r['rootIds'])for r in result.values())==(53 if retired else 437),'Exact19 groups437-before/53 heroes-flowers-after required')
 if not retired:guard.validate_native_controls(result,bundle)
 return result


def old_controls(u,bundle,h,witness):
 base=bundle['base'];n=base['native'];reference=base['bundle'];parent=reference['base'];r=base['report']
 require(reference is bundle['reference'],'One genuine actual R34 bundle required')
 materials=n.old_materials(u,parent,h);trees=n.old_tree_controls(u,parent,h);grass=h['cleanNative'].original_grass_controls(u,h['cleanBundle'])
 require(materials==read(check_pin(r['originalMaterialsSaved']))and trees==read(check_pin(r['originalTreesSaved']))and grass==read(check_pin(r['originalGrassSaved'])),
  'Actual original R34 saved material/tree/8949grass controls differ')
 maps=guard.module('r36_original_saved_fern_material','exterior-garden-fern-only-materials-r34.py')
 fern=maps.verify_materials(u,r['materialReport'],reference['source']['recipe'],h['existing'].graph_snapshot)
 meshes={model:u.EditorAssetLibrary.load_asset(v['mesh'])for model,v in r['newOwnedGroups'].items()};new={model:v['actor']for model,v in r['newOwnedGroups'].items()}
 n.verify_new(u,reference,h,new,bundle['oldFernMeasurements'],meshes,{'fern':fern})
 fern_controls={}
 for model,path in new.items():
  c=h['cleanNative'].component_lookup(u,path,'Instances');count=c.get_instance_count();m=bundle['oldFernMeasurements'][model]
  observed={'rootIds':m['rootIds'],'recoveredValues':[h['tree'].transform_value(h['tree'].instance_value(c,i))for i in range(count)],
   'storedMatrices':[h['tree'].matrix(c,i)for i in range(count)],'mainRandomSeed':int(c.get_editor_property('instancing_random_seed')),
   'numCustomDataFloats':int(c.get_editor_property('num_custom_data_floats')),'customData':[float(v)for v in c.get_editor_property('per_instance_sm_custom_data')],
   'additionalRandomSeedsReadbackAvailable':False,'seedRangesReconstructed':False}
  exact(observed['recoveredValues'],m['recoveredValues'],'Actual saved36 fern frames differ');exact(observed['storedMatrices'],m['storedMatrices'],'Actual saved36 fern matrices differ')
  require(digest(observed['recoveredValues'])==witness[path]['components'][0]['orderedInstanceTransformsSha256'],'Existing fern measured frames must bind full witness')
  fern_controls[path]=observed
 require(len(fern_controls)==3 and sum(len(v['rootIds'])for v in fern_controls.values())==36,'All3 owned old fern groups36members required')
 return {'originalMaterials':materials,'originalTrees':trees,'original8949Grass':grass,'preserved36FernControls':fern_controls,'originalFernMaterialReport':r['materialReport']}


def measure(u,bundle,h):
 source=bundle['source'];lookup={};recorded={identity:control['recoveredValues'][index]for control in bundle['originalControls'].values()for index,identity in enumerate(control['rootIds'])}
 for group in bundle['groups'].values():
  c=h['cleanNative'].component_lookup(u,group['actor'],group['component'])
  for i,row in enumerate(group['rows']):require(row['id']not in lookup,'Duplicate original source root');lookup[row['id']]=(c,i)
 require(len(lookup)==384,'All384 exact existing low roots required');values={};proof={}
 for model in source['models']:
  rows=[r for r in source['placements']if r['model']==model];transient=u.new_object(u.HierarchicalInstancedStaticMeshComponent)
  require(rows and transient and transient.get_path_name().startswith('/Engine/Transient.')and transient.get_editor_property('static_mesh')is None,'Meshless unowned transient required')
  desired=[];inputs=[];old_values=[]
  for row in rows:
   c,index=lookup[row['rootId']];old=h['tree'].instance_value(c,index);transform=u.Transform()
   transform.set_editor_property('translation',old.translation);transform.set_editor_property('rotation',old.rotation)
   translation=transform.get_editor_property('translation');translation.set_editor_property('z',row['positionCm'][2]);transform.set_editor_property('translation',translation)
   transform.set_editor_property('scale3d',u.Vector(*row['scale']));old_value=h['tree'].transform_value(old);pre=h['tree'].transform_value(transform)
   exact(old_value,recorded[row['rootId']],'Actual saved original recovered root controls differ')
   exact(pre,[old_value[0][:2]+[row['positionCm'][2]],old_value[1],row['scale']],'Exact fit inputZ/scale and original wrapped rotation required')
   exact(pre[0][:2],old_value[0][:2],'Original native XY must be copied exactly')
   require(transient.add_instance(transform,False)==len(inputs),'Unique ordered transient insertion required')
   inputs.append(pre);old_values.append(old_value);desired.append(transform)
  recovered=[h['tree'].transform_value(h['tree'].instance_value(transient,i))for i in range(len(rows))];matrices=[h['tree'].matrix(transient,i)for i in range(len(rows))]
  for pre,got,matrix in zip(inputs,recovered,matrices):exact(got[0],pre[0],'Measured source assigned XYZ changed');exact(matrix[3][:3],pre[0],'Stored translation differs')
  proof[model]={'rootIds':[r['rootId']for r in rows],'originalValues':old_values,'inputValues':inputs,'recoveredValues':recovered,'storedMatrices':matrices,
   'actualUnregisteredMeshlessTransientMeasurement':True,'wrappedOriginalXYAndRotationCopied':True,'hostQuaternionReconstructionPerformed':False,
   'sourceUniformScaleAssigned':True,'sourceVerticalBottomOffsetAssigned':True,'nativeNormalTangentReadbackAvailable':False}
  transient.clear_instances();require(transient.get_instance_count()==0,'Transient members remained');values[model]=desired
 require(sum(len(v)for v in values.values())==384,'Exactly384 whole original source replacements required')
 guard.validate_measurements(proof,bundle);return values,proof


def clear_original(u,bundle,h,controls):
 proof=[]
 for label,group in bundle['groups'].items():
  c=h['cleanNative'].component_lookup(u,group['actor'],group['component']);original=controls[group['actor']]
  require(c.get_instance_count()==len(original['rootIds'])==len(group['rows'])and original['numCustomDataFloats']==0 and original['customData']==[],'Only entire reviewed nonempty low components may clear')
  c.clear_instances();c.get_owner().synchronize_instance_bounds();require(c.get_instance_count()==0,'Entire original low component did not clear')
  require(int(c.get_editor_property('instancing_random_seed'))==original['mainRandomSeed']and int(c.get_editor_property('num_custom_data_floats'))==0 and not c.get_editor_property('per_instance_sm_custom_data'), 'Whole component clearing changed mainseed/custom data')
  proof.append({'groupId':label,'actor':group['actor'],'rootIds':original['rootIds'],'retiredRoots':len(original['rootIds']),
   'entireComponentMembersCleared':True,'actorOrComponentDeleted':False,'survivorRecompositionPerformed':False,'seedSetterPerformed':False,
   'AdditionalRandomSeedsReadbackAvailable':False,'perInstanceShaderRandomValuePreservationClaimed':False})
 require(len(proof)==4 and sum(r['retiredRoots']for r in proof)==384,'Exact4whole low groups384members required');return proof


def cyclic(face):return min(tuple(face[i:]+face[:i])for i in range(3))
def mesh_proof(u,mesh,row,subsystem):
 require(subsystem and mesh.get_num_lods()==1 and len(mesh.get_editor_property('static_materials'))==1 and not mesh.get_editor_property('has_navigation_data'),'Single original provider LOD/slot/no navigation required')
 settings=subsystem.get_lod_build_settings(mesh,0)
 require(all(settings.get_editor_property(k)==v for k,v in {'use_full_precision_u_vs':True,'generate_lightmap_u_vs':False,'recompute_normals':False,'recompute_tangents':True,'remove_degenerates':False}.items()),'Original normals/UV and requested derived-tangent policy differs')
 description=mesh.get_static_mesh_description(0);require(description and description.get_triangle_count()==mesh.get_num_triangles(0)==row['triangles']and mesh.get_num_sections(0)==1,'Full original provider native triangle/section census differs')
 expected=[];actual=[]
 for at in range(0,len(row['indices']),3):expected.append(cyclic([tuple(row['expectedNativeVerticesCm'][i]+row['uv0'][i]+row['uv1'][i])for i in row['indices'][at:at+3]]))
 for index in range(row['triangles']):
  triangle=u.TriangleID(id_value=index);require(int(description.get_triangle_polygon_group(triangle).id_value)==0,'Single original source material section/order required');face=[]
  for corner in range(3):
   vi=description.get_triangle_vertex_instance(triangle,corner);position=description.get_vertex_position(description.get_vertex_instance_vertex(vi))
   face.append(tuple(float(getattr(position,k))for k in 'xyz')+tuple(float(getattr(description.get_vertex_instance_uv(vi,channel),k))for channel in (0,1)for k in 'xy'))
  actual.append(cyclic(face))
 require(actual==expected,'Full original native F32 P/UV0/UV1/ordered topology/winding differs')
 return {'asset':mesh.get_path_name(),'lodCount':1,'triangles':row['triangles'],'sections':1,'nativeCornerSha256':digest(actual),
  'fullOrderedNativeF32PositionUV0UV1WindingVerified':True,'originalProviderLodChainPresent':False,'allSixOriginalSourceAttributeBytesPreserved':True,
  'nativeNormalTangentReadbackAvailable':False,'nativeColor0Color1ReadbackAvailable':False,'sourceTangentsPresent':False,
  'nativeTangentsRequestedFromOriginalUv0':True,'nativeTangentGenerationNumericallyVerified':False,'nativeNaniteRequested':False,'meshPackageIndependentlyUnloaded':False}

def material_contract(source,materials):
 require(source['recipe']['key']=='ph_original_periwinkle_r36'and set(materials)=={source['recipe']['key']}
  and {r['materialKey']for r in source['models'].values()}==set(materials),'Exactly one original recipe/model material key required')
 return materials

def imported_corner_identity(u,mesh,row):
 # Counts only select the candidate source form. Complete corners establish it.
 require(mesh and mesh.get_path_name().startswith(PREFIX+'/Geometry/')
  and mesh.get_class().get_path_name()=='/Script/Engine.StaticMesh'
  and mesh.get_num_lods()==1 and len(mesh.get_editor_property('static_materials'))==1,
  'Only one-LOD/one-slot own original imported StaticMesh permitted')
 description=mesh.get_static_mesh_description(0)
 require(description and description.get_triangle_count()==mesh.get_num_triangles(0)==row['triangles']
  and mesh.get_num_sections(0)==1,'Full original source identity triangle/section census differs')
 expected=[cyclic([tuple(row['expectedNativeVerticesCm'][i]+row['uv0'][i]+row['uv1'][i])for i in row['indices'][at:at+3]])for at in range(0,len(row['indices']),3)]
 actual=[]
 for index in range(row['triangles']):
  triangle=u.TriangleID(id_value=index)
  require(int(description.get_triangle_polygon_group(triangle).id_value)==0,'Source identity material section/order differs');face=[]
  for corner in range(3):
   vi=description.get_triangle_vertex_instance(triangle,corner);p=description.get_vertex_position(description.get_vertex_instance_vertex(vi))
   face.append(tuple(float(getattr(p,k))for k in 'xyz')+tuple(float(getattr(description.get_vertex_instance_uv(vi,channel),k))for channel in (0,1)for k in 'xy'))
  actual.append(cyclic(face))
 require(actual==expected,'Full imported original native F32 P/UV0/UV1/order/winding identity differs')
 return {'sourceNodeId':row['id'],'asset':mesh.get_path_name(),'triangles':row['triangles'],'sections':1,
  'nativeCornerSha256':digest(actual),'fullOrderedNativeF32PositionUV0UV1WindingVerified':True,
  'sourceIdentityFromTriangleCountAlone':False,'sourceIdentityFromActorOrMeshName':False,
  'navigationAndBuildSettingsNotRequiredForInitialSourceIdentity':True,'nativeNormalTangentColor0Color1ReadbackAvailable':False}


def temporary_inventory(u,temporary,h):
 # Observation deliberately precedes all source identity/class/container gates.
 rows=[]
 for actor in temporary:
  components=actor.get_components_by_class(u.ActorComponent)
  statics={c.get_path_name():c for c in actor.get_components_by_class(u.StaticMeshComponent)}
  primitive_paths=[c.get_path_name()for c in actor.get_components_by_class(u.PrimitiveComponent)]
  scene_paths=[c.get_path_name()for c in actor.get_components_by_class(u.SceneComponent)]
  parent=actor.get_attach_parent_actor();parts=[]
  for c in components:
   part={'path':c.get_path_name(),'class':c.get_class().get_path_name(),'name':c.get_name()}
   if c.get_path_name()in statics:
    mesh=c.get_editor_property('static_mesh');part['staticMesh']=mesh.get_path_name()if mesh else None
   parts.append(part)
  rows.append({'actor':actor.get_path_name(),'class':actor.get_class().get_path_name(),'label':actor.get_actor_label(),
   'worldTransform':h['tree'].transform_value(actor.get_actor_transform()),'attachParent':parent.get_path_name()if parent else None,
   'components':parts,'staticMeshComponents':list(statics),'primitiveComponents':primitive_paths,'sceneComponents':scene_paths})
 return {'schema':guard.REPAIR_SCHEMA,'schemaVersion':2,'owner':OWNER,'scope':'ACTUAL_NEW_IMPORT_DELTA_BEFORE_ANY_BINDING_GATE',
  'actors':rows,'actorCount':len(rows),'actorLabelsUsedForSourceIdentity':False,'sourceMeshIdentityVerifiedAtThisCheckpoint':False,
  'originalR1TemporaryActorLabelsRecovered':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False}


def geometry_identity_bindings(u,source,temporary,inventory):
 require(len(temporary)==inventory['actorCount']==len(inventory['actors'])and
  {a.get_path_name()for a in temporary}=={r['actor']for r in inventory['actors']},'Exact observed temporary delta required')
 routing=guard.source_triangle_count_bindings(source['models']);found={};bindings=[];containers=[];mesh_rows=[]
 identity=[[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]];paths={a.get_path_name()for a in temporary}
 for actor,row in zip(temporary,inventory['actors']):
  require(actor.get_path_name()==row['actor']and row['worldTransform']==identity
   and (row['attachParent']is None or row['attachParent']in paths),'Imported source identity world pose/parent differs')
  all_components={r['path']for r in row['components']};statics=actor.get_components_by_class(u.StaticMeshComponent)
  if statics:
   require(len(statics)==1 and row['class']in ('/Script/Engine.StaticMeshActor','/Script/Engine.Actor')
    and row['primitiveComponents']==row['staticMeshComponents']and all_components==set(row['sceneComponents']),
    'Imported mesh actor must have exactly one rendering primitive and only scene components')
   mesh=statics[0].get_editor_property('static_mesh')
   require(mesh and mesh.get_path_name().startswith(PREFIX+'/Geometry/'),'Only fresh own imported mesh permitted')
   count=mesh.get_num_triangles(0);require(count in routing,'No complete original source candidate matches native triangle count')
   key=routing[count];require(key not in found,'Duplicate original geometry candidate forbidden')
   proof=imported_corner_identity(u,mesh,source['models'][key]);found[key]=mesh;mesh_rows.append(row)
   bindings.append({**proof,'actualTemporaryActor':row['actor'],'actualTemporaryActorLabel':row['label'],
    'originalProviderMeshName':source['models'][key]['originalSourceMeshName'],'meshNameUsedForSourceIdentity':False,
    'actorLabelUsedForSourceIdentity':False,'uniqueTriangleCountUsedOnlyForCandidateRouting':True})
  else:
   require(row['class']=='/Script/Engine.Actor'and not row['primitiveComponents']and not row['staticMeshComponents']
    and all_components==set(row['sceneComponents'])and len(all_components)<=1 and row['attachParent']is None,
    'Only a new identity generic nonrendering scene container may accompany source meshes')
   containers.append(row)
 require(len(containers)<=1 and set(found)==set(source['models'])and len(found)==len({m.get_path_name()for m in found.values()})==6,
  'Six unique full-source geometry identities and at most one closed nonrendering container required')
 container_paths={r['actor']for r in containers}
 require(all(r['attachParent']is None or r['attachParent']in container_paths for r in mesh_rows),
  'Imported source mesh may attach only to the closed new scene container')
 return found,bindings,containers


def import_geometry(u,bundle,materials,h,checkpoint):
 material_contract(bundle['source'],materials)
 source=bundle['source'];assets=u.EditorAssetLibrary;actor_system=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem);pipelines=[]
 subsystem=h['meshHelper'].static_mesh_subsystem(u)
 for original,name in [('GLTFSceneAssets','Assets'),('GLTFMaterials','Materials'),('LevelActors','Level')]:
  target=PREFIX+'/Pipeline/'+name;require(not assets.does_asset_exist(target),'Fresh owned import pipeline required')
  p=assets.duplicate_asset('/Game/Brezi/Pipeline/'+original,target);require(p,'Cannot create owned import pipeline');pipelines.append(p)
 for k,v in {'combine_static_meshes_behavior':u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,'collision':False,'build_nanite':False,'generate_lightmap_u_vs':False}.items():
  pipelines[0].get_editor_property('mesh_pipeline').set_editor_property(k,v)
 for k,v in {'remove_degenerates':False,'recompute_normals':False,'recompute_tangents':True,'use_full_precision_u_vs':True}.items():pipelines[0].get_editor_property('common_meshes_properties').set_editor_property(k,v)
 mp=pipelines[0].get_editor_property('material_pipeline');mp.set_editor_property('import_materials',False);mp.get_editor_property('texture_pipeline').set_editor_property('import_textures',False)
 pipelines[2].set_editor_property('scene_hierarchy_type',u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
 params=u.ImportAssetParameters()
 for k,v in {'is_automated':True,'replace_existing':False,'force_show_dialog':False,'override_pipelines':[u.SoftObjectPath(p.get_path_name())for p in pipelines],
  'import_level':levels.get_current_level()}.items():params.set_editor_property(k,v)
 before=set(actors(u));manager=u.InterchangeManager.get_interchange_manager_scripted()
 imported=manager.import_scene(PREFIX+'/Geometry',manager.create_source_data(str(check_pin(source['draft']['glb']))),params)
 temporary=[a for path,a in actors(u).items()if path not in before]
 inventory=temporary_inventory(u,temporary,h);write(checkpoint/'import-temporary-actors-before-binding.json',inventory)
 require(imported,'Six original Periwinkle forms import failed')
 h['meshHelper'].finish_static_mesh_compilation(u,synchronous=True)
 found,bindings,containers=geometry_identity_bindings(u,source,temporary,inventory);result={}
 write(checkpoint/'full-source-import-geometry-identities.json',{'bindings':bindings,'nonrenderingContainers':containers,
  'allSixFullSourceGeometryIdentitiesVerified':True,'fullIdentityTriangles':sum(v['triangles']for v in bindings)})
 for key,row in source['models'].items():
  mesh=found[key]
  target=PREFIX+'/Geometry/StaticMeshes/'+row['exportName']
  if mesh.get_path_name().split('.')[0]!=target:require(assets.rename_asset(mesh.get_path_name().split('.')[0],target),'Cannot canonicalize own master');mesh=assets.load_asset(target)
  mesh.set_material(0,materials[row['materialKey']]);mesh.set_editor_property('has_navigation_data',False)
  require(mesh.get_num_lods()==1,'No cloned or reduced source LODs allowed');settings=subsystem.get_lod_build_settings(mesh,0)
  for k,v in {'use_full_precision_u_vs':True,'generate_lightmap_u_vs':False,'recompute_normals':False,'recompute_tangents':True,'remove_degenerates':False}.items():settings.set_editor_property(k,v)
  subsystem.set_lod_build_settings(mesh,0,settings);assets.set_metadata_tag(mesh,'BreziGeneratedBy',OWNER);assets.set_metadata_tag(mesh,'BreziR36OriginalAttributeSource',digest(row['attributes']))
  assets.set_metadata_tag(mesh,'BreziR36OriginalSourceNode',key);assets.set_metadata_tag(mesh,'BreziR36OriginalProviderMeshName',row['originalSourceMeshName'])
  observed=next(v for v in bindings if v['sourceNodeId']==key)
  assets.set_metadata_tag(mesh,'BreziR36ObservedImportedActorLabel',observed['actualTemporaryActorLabel'])
  require(assets.save_loaded_asset(mesh,only_if_is_dirty=False),'Cannot save owned original master');result[key]=mesh
 h['meshHelper'].finish_static_mesh_compilation(u,synchronous=True)
 for key,mesh in result.items():mesh_proof(u,mesh,source['models'][key],subsystem)
 for actor in reversed(temporary):require(actor_system.destroy_actor(actor),'Cannot remove owned import actor')
 require(set(actors(u))==before,'Import temporary actor delta was not fully removed')
 canonical={m.get_path_name().split('.')[0]for m in result.values()};removed=[]
 for path in assets.list_assets(PREFIX+'/Geometry',recursive=True,include_folder=False):
  value=assets.load_asset(path)
  if value and value.get_path_name().split('.')[0]in canonical:continue
  require(value and value.get_class().get_name()in ['InterchangeSceneImportAsset','ObjectRedirector'],'Unexpected owned import artifact')
  removed.append(value.get_path_name());require(assets.delete_asset(path),'Cannot remove own import metadata')
 for p in pipelines:require(assets.save_loaded_asset(p,only_if_is_dirty=False),'Cannot save owned import pipeline')
 return result,[p.get_path_name()for p in pipelines],removed,bindings,pin(checkpoint/'import-temporary-actors-before-binding.json'),containers


def apply_new(u,bundle,h,values,meshes,materials,measurements):
 material_contract(bundle['source'],materials)
 system=u.get_editor_subsystem(u.EditorActorSubsystem);result={};expected={}
 for model in bundle['source']['models']:
  a=system.spawn_actor_from_class(u.load_class(None,'/Script/BreziTwin.BreziVegetationPatch'),u.Vector(0,0,0),u.Rotator());require(a,'Cannot spawn own original-shape group')
  a.tags=[u.Name('BreziGenerated'),u.Name(guard.TAG)];a.set_actor_label('R36_'+model);a.set_folder_path('Brezi/GardenPeriwinkle20261002R36');a.set_actor_tick_enabled(False)
  c=a.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent);require(c and a.get_editor_property('root_component')==c and c.get_owner()==a,'Own HISM root/owner predicate failed')
  h['rural'].new_component_policy(u,c);require(c.set_static_mesh(meshes[model]),'Cannot bind original master');c.set_editor_property('cast_shadow',True);c.set_editor_property('visible_in_ray_tracing',True)
  require(a.set_detail_density_scaling(False),'Cannot preserve authored unmanaged detail policy')
  fit=next(r for r in bundle['source']['placements']if r['model']==model);old_group=next(g for g in bundle['groups'].values()if fit['rootId']in [r['id']for r in g['rows']])
  template=old_group['witness'];policy=template['components'][0]
  for section in ['renderFlags','passFlags','drawPolicy','additionalRenderFlags']:
   for key,value in policy[section].items():
    if key=='cached_max_draw_distance':require(c.get_editor_property(key)==value,'Derived new draw-distance cache differs')
    else:c.set_editor_property(key,value)
  c.set_cull_distances(*policy['instanceCullCm'])
  require(list(c.add_instances(values[model],True,False,False))==list(range(len(values[model]))),'Only unique measured source roots may add');a.synchronize_instance_bounds()
  path=a.get_path_name();result[model]=path;expected[path]=guard.added_expected(template,old_group['actor'],path,model,meshes[model].get_path_name(),
   materials[bundle['source']['models'][model]['materialKey']].get_path_name(),measurements[model])
 return result,expected


def verify_new(u,bundle,h,new,measurements,meshes,materials):
 material_contract(bundle['source'],materials)
 scene=actors(u);require({p for p,a in scene.items()if a.actor_has_tag(guard.TAG)}==set(new.values()),'Owned actor namespace widened')
 for model,path in new.items():
  a=scene[path];c=a.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent);m=measurements[model]
  require(c and a.get_editor_property('root_component')==c and c.get_owner()==a and c.get_instance_count()==len(m['rootIds']), 'Own source group root/owner/census differs')
  require(c.get_editor_property('static_mesh').get_path_name()==meshes[model].get_path_name()and c.get_num_materials()==1
   and c.get_material(0).get_path_name()==materials[bundle['source']['models'][model]['materialKey']].get_path_name(),'Saved exact original master/default material differs')
  exact([h['tree'].transform_value(h['tree'].instance_value(c,i))for i in range(c.get_instance_count())],m['recoveredValues'],'Measured new recovered frames differ')
  exact([h['tree'].matrix(c,i)for i in range(c.get_instance_count())],m['storedMatrices'],'Measured new stored FMatrix differs')


def primary_api():
 root=Path('/Users/Shared/Epic Games/UE_5.8/Engine/Source');paths={
  'hismRemoval':root/'Runtime/Engine/Private/HierarchicalInstancedStaticMesh.cpp',
  'instanceStorage':root/'Runtime/Engine/Classes/Components/InstancedStaticMeshComponent.h',
  'rootComponent':root/'Runtime/Engine/Classes/GameFramework/Actor.h',
  'materialPipeline':root.parent/'Plugins/Interchange/Runtime/Source/Pipelines/Public/InterchangeGenericAssetsPipeline.h',
  'originalNodeSceneDisplayLabel':root.parent/'Plugins/Interchange/Runtime/Source/Import/Private/GLTF/InterchangeGLTFTranslator.cpp',
  'originalNodeActorFactoryLabel':root.parent/'Plugins/Interchange/Runtime/Source/Pipelines/Private/InterchangeGenericScenesPipeline.cpp',
  'actorFactoryLabelSetter':root.parent/'Plugins/Interchange/Runtime/Source/Import/Private/Scene/InterchangeActorHelper.cpp',
  'originalGlTFBasis':root.parent/'Plugins/Interchange/Runtime/Source/Parsers/GLTFCore/Private/GLTF/ConversionUtilities.h',
  'originalGlTFAttributes':root.parent/'Plugins/Interchange/Runtime/Source/Parsers/GLTFCore/Private/GLTF/GLTFMesh.cpp',
  'originalGlTFIndices':root.parent/'Plugins/Interchange/Runtime/Source/Parsers/GLTFCore/Private/GLTFMeshFactory.cpp'}
 require('PerInstanceSMData'in paths['instanceStorage'].read_text()and 'RemoveAtSwap'in paths['hismRemoval'].read_text()
  and 'K2_GetRootComponent'in paths['rootComponent'].read_text()and 'MaterialPipeline'in paths['materialPipeline'].read_text()
  and 'GltfNode.Name'in paths['originalNodeSceneDisplayLabel'].read_text()
  and 'FString ActorName = SceneNode->GetDisplayLabel();'in paths['originalNodeActorFactoryLabel'].read_text()
  and 'SpawnedActor->SetActorLabel(FactoryNode->GetDisplayLabel());'in paths['actorFactoryLabelSetter'].read_text()
  and 'ConvertVec3'in paths['originalGlTFBasis'].read_text()and 'GetPositions'in paths['originalGlTFAttributes'].read_text()
  and 'Indices[(TriangleIndex * 3 + Corner)]'in paths['originalGlTFIndices'].read_text(), 'Installed primary APIs differ')
 return {k:pin(v)for k,v in paths.items()}


def input_files(plan,bundle):
 files=dict(plan['inputFiles']);files[str(guard.PLAN)]=sha(guard.PLAN)
 for path,value in files.items():require(sha(path)==value,'Consumed frozen source changed: '+path)
 return files


def preflight(output,bundle=None):
 output=Path(output).resolve();require(output==guard.STUDY/'source-preflight'and not output.exists(),'Fresh typed R36 preflight required')
 plan,bundle=guard.validate_plan(bundle)
 base=bundle['base'];clone=guard.validate_clone(base);h=helpers(base);g=base['native'].guard.old.guard.g
 for project in [base['project'],guard.CANDIDATE/'Project/BreziTwin']:
  require(g.inventory(project/'Content')==base['content']and g.project_proof(project)==base['protected'],'Actual saved parent or independent clone bytes differ')
 output.mkdir();tests=ROOT/'scripts/unreal/test_exterior_garden_periwinkle_native_r36_r2.py';command=[sys.executable,'-B',str(tests)]
 run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=240);log=output/'cpu-guards.log';log.write_text(run.stdout+run.stderr)
 require(run.returncode==0,'Meaningful new native-source CPU fixtures failed');files=input_files(plan,bundle)
 row={'schema':guard.SCHEMA,'schemaVersion':2,'owner':OWNER,'status':'source-preflight-validated-whole384-original-periwinkle-native-r2-pending',
  'createdAt':now(),'selectedPlan':pin(guard.PLAN),'sourceProposal':pin(guard.PROPOSAL),'sourceGeometryDescriptor':bundle['source']['draft']['geometry'],
  'baseNativeReport':base['reportPin'],'baseNativeProcess':base['process'],'baseCurrentByteAudit':base['audit'],'projectClone':clone,
  'moduleOrderWitness':h['moduleOrderWitness'],'repairSchema':guard.REPAIR_SCHEMA,'importIdentityEvidence':plan['importIdentityEvidence'],'primaryApi':primary_api(),'inputFiles':files,'expectedCounts':guard.COUNTS,
  'tests':{'command':command,'source':pin(tests),'exitCode':0,'testCount':TEST_COUNT,'log':pin(log)},
  'nativeExecuted':False,'gpuExecuted':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False}
 write(output/'source-preflight.json',row);print(json.dumps({'preflight':pin(output/'source-preflight.json'),'nativeExecuted':False}))


def validate_preflight(path,plan,bundle):
 require(Path(path).resolve()==guard.STUDY/'source-preflight/source-preflight.json','Only new typed R36 source preflight accepted');row=read(path)
 require(row['schema']==guard.SCHEMA and row['schemaVersion']==2 and row['owner']==OWNER
  and row['status']=='source-preflight-validated-whole384-original-periwinkle-native-r2-pending'
  and row['selectedPlan']==pin(guard.PLAN)and row['sourceProposal']==pin(guard.PROPOSAL)
  and row['sourceGeometryDescriptor']==bundle['source']['draft']['geometry']and row['baseNativeReport']==bundle['base']['reportPin']
  and row['baseNativeProcess']==bundle['base']['process']and row['baseCurrentByteAudit']==bundle['base']['audit']
  and row['projectClone']==guard.validate_clone(bundle['base'])and row['expectedCounts']==guard.COUNTS
  and row['repairSchema']==guard.REPAIR_SCHEMA and row['importIdentityEvidence']==plan['importIdentityEvidence']
  and row['tests']['source']==pin(ROOT/'scripts/unreal/test_exterior_garden_periwinkle_native_r36_r2.py')
  and row['tests']['exitCode']==0 and row['tests']['testCount']==TEST_COUNT and row['nativeExecuted']is False and row['gpuExecuted']is False,
  'Exact typed executed source/count/preflight binding required')
 require(row['inputFiles']==input_files(plan,bundle)and row['primaryApi']==primary_api(),'Consumed source closure or installed API differs')
 check_pin(row['tests']['log']);return row


def main():
 import unreal as u
 output=guard.CANDIDATE;project=output/'Project/BreziTwin'
 require(Path(os.environ['BREZI_GARDEN_PERIWINKLE_OUTPUT']).resolve()==output
  and Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project,'Only prepared original-R34 R36 project permitted')
 require(not(output/REPORT).exists()and not(output/'exterior-import-report.json').exists(),'Fresh typed native report only')
 plan,bundle=guard.validate_plan();source,base=bundle['source'],bundle['base'];pfpath=Path(os.environ['BREZI_GARDEN_PERIWINKLE_PREFLIGHT']).resolve()
 require(sha(pfpath)==os.environ['BREZI_GARDEN_PERIWINKLE_PREFLIGHT_SHA256']and sha(guard.PLAN)==os.environ['BREZI_GARDEN_PERIWINKLE_PLAN_SHA256'],'Exact source plan/preflight SHA required')
 pf=validate_preflight(pfpath,plan,bundle);h=helpers(base);require(h['moduleOrderWitness']==pf['moduleOrderWitness'],'Frozen-first helper cache order changed')
 maps=guard.module('r36_owned_five_original_map_material','exterior-garden-periwinkle-materials-r36.py');maps.preflight_enums(u);maps.validate_recipe(source['recipe'])
 g=base['native'].guard.old.guard.g
 for path in [project,base['project']]:require(g.inventory(path/'Content')==base['content']and g.project_proof(path)==base['protected'],'Original or candidate byte closure differs before native')
 module=project/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib';original_module=base['project']/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'
 require(sha(module)==sha(original_module)=='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574'and module.stat().st_ino!=original_module.stat().st_ino,'Actual own original Recipe4 module required')
 checkpoint=output/'garden-periwinkle-checkpoint-r2';require(not checkpoint.exists(),'Fresh owned native checkpoint required');checkpoint.mkdir()
 report={'schema':guard.SCHEMA,'schemaVersion':2,'owner':OWNER,'status':'running','startedAt':now(),'nativeProcessId':os.getpid(),
  'output':str(output),'project':str(project),'repairSchema':guard.REPAIR_SCHEMA,'importIdentityEvidence':plan['importIdentityEvidence'],'immutableSourceGuard':pin(guard.ORIGINAL_GUARD),'selectedPlan':pin(guard.PLAN),'sourceProposal':pin(guard.PROPOSAL),
  'sourceGeometryDescriptor':source['draft']['geometry'],'sourcePreflight':pin(pfpath),'baseNativeReport':base['reportPin'],
  'baseNativeProcess':base['process'],'baseCurrentByteAudit':base['audit'],'baseContentInventory':base['report']['afterContentInventory'],
  'protectedProjectProof':base['report']['protectedProjectProof'],'projectClone':pf['projectClone'],'inputFiles':pf['inputFiles'],'moduleOrderWitness':h['moduleOrderWitness'],
  'nativeModuleWitness':{'source':str(original_module),'destination':str(module),'sha256':sha(module),'bytes':module.stat().st_size,'independentInodes':True},
  'activeDesign':plan['activeDesign'],'setbacksMm':plan['setbacksMm'],'nativeApplied':False,'nativeAppearanceAccepted':False,
  'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,'ecologicalFitVerified':False,
  'surveyedPlacementVerified':False,'nativeNormalTangentReadbackAvailable':False,'nativeColor0Color1ReadbackAvailable':False,
  'meshMaterialPackagesIndependentlyUnloaded':False,'AdditionalRandomSeedsReadbackAvailable':False,'retainedTransformRecompositionPerformed':False,
  'seedMutationPerformed':False,'perInstanceShaderRandomValuePreservationClaimed':False,'yardIntegrationApplied':False}
 report_write(output/REPORT,report)
 try:
  levels=u.get_editor_subsystem(u.LevelEditorSubsystem);require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot open own exact saved R34 clone')
  before=h['cleanNative'].full_witness(u,h);require(before==base['witness'],'Whole actual saved R34 actor witness differs')
  old_before=old_controls(u,bundle,h,before);original=garden_controls(u,bundle,h,before)
  values,measurements=measure(u,bundle,h);footprints=guard.source_footprints(measurements,bundle)
  require(h['cleanNative'].full_witness(u,h)==before,'Unregistered numeric measurement changed original scene')
  for name,value in [('before-actors',before),('original-garden-controls',original),('original-protected-controls-before',old_before),('source-native-measurements',measurements),('source-crown-mask-proof',footprints)]:write(checkpoint/(name+'.json'),value)
  material,material_report=maps.build_materials(u,source['recipe'],h['existing'].graph_snapshot);materials={source['recipe']['key']:material}
  meshes,pipelines,removed,node_bindings,temp_inventory,containers=import_geometry(u,bundle,materials,h,checkpoint);require(h['cleanNative'].full_witness(u,h)==before,'Owned asset import modified old scene')
  retired=clear_original(u,bundle,h,original);expected=guard.expected_original(before,bundle)
  require(h['cleanNative'].full_witness(u,h)==expected,'Original scene differs outside four whole low-member clearings')
  new,added=apply_new(u,bundle,h,values,meshes,materials,measurements);expected.update(added)
  verify_new(u,bundle,h,new,measurements,meshes,materials);require(h['cleanNative'].full_witness(u,h)==expected and len(expected)==5360,'Full source-template5360 counterfactual differs')
  retained=garden_controls(u,bundle,h,expected,retired=True);write(checkpoint/'expected-actors.json',expected);write(checkpoint/'retained-garden-controls-before-save.json',retained)
  require(levels.save_current_level(),'Cannot save whole-original low composition');require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot unload/reload owned saved map')
  material_saved=maps.verify_materials(u,material_report,source['recipe'],h['existing'].graph_snapshot);materials_saved={source['recipe']['key']:material_saved}
  meshes_saved={key:u.EditorAssetLibrary.load_asset(mesh.get_path_name())for key,mesh in meshes.items()}
  verify_new(u,bundle,h,new,measurements,meshes_saved,materials_saved);saved=h['cleanNative'].full_witness(u,h);require(saved==expected,'Saved/reloaded full counterfactual differs')
  retained_saved=garden_controls(u,bundle,h,saved,retired=True);exact(retained_saved,retained,'53original hero/flower raw controls changed on save/reload')
  old_saved=old_controls(u,bundle,h,saved);exact(old_saved,old_before,'All unrelated material/78tree/8949grass/36fern raw controls changed')
  geometry={key:mesh_proof(u,mesh,source['models'][key],h['meshHelper'].static_mesh_subsystem(u))for key,mesh in meshes_saved.items()}
  require(sum(r['triangles']for r in geometry.values())==34350,'Full six-original provider34350 triangle proof required')
  hisms=[c for a in saved.values()for c in a['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
  require(len(hisms)==2322 and sum(c['instanceCount']for c in hisms)==676957,'Saved full HISM population differs')
  packages=[m.get_path_name().split('.')[0]for m in meshes_saved.values()]+[p.split('.')[0]for p in material_report['newPackageAssets']+pipelines]
  content=g.inventory(project/'Content');delta=guard.validate_content(base['content'],content,packages)
  require(g.project_proof(project)==base['protected']and g.inventory(base['project']/'Content')==base['content']and g.project_proof(base['project'])==base['protected'],'Original base/protected project changed')
  for name,value in [('saved-actors',saved),('retained-garden-controls-saved',retained_saved),('original-protected-controls-saved',old_saved),('after-content',content)]:write(checkpoint/(name+'.json'),value)
  require(all(sha(p)==v for p,v in pf['inputFiles'].items()),'Frozen consumed source changed during native')
  report.update(status=STATUS,completedAt=now(),nativeApplied=True,savedMapUnloadedReloaded=True,sourceInputsUnchanged=True,originalSavedR34Unchanged=True,
   wholeOriginalLowGroupRetirements=retired,beforeActorWitness=pin(checkpoint/'before-actors.json'),expectedActorWitness=pin(checkpoint/'expected-actors.json'),savedActorWitness=pin(checkpoint/'saved-actors.json'),
   beforeActorWitnessSha256=digest(before),expectedActorWitnessSha256=digest(expected),savedActorWitnessSha256=digest(saved),
   originalGardenControls=pin(checkpoint/'original-garden-controls.json'),retainedGardenControlsBeforeSave=pin(checkpoint/'retained-garden-controls-before-save.json'),retainedGardenControlsSaved=pin(checkpoint/'retained-garden-controls-saved.json'),
   originalProtectedControlsBefore=pin(checkpoint/'original-protected-controls-before.json'),originalProtectedControlsSaved=pin(checkpoint/'original-protected-controls-saved.json'),
   newSourceNativeMeasurements=pin(checkpoint/'source-native-measurements.json'),sourceCrownMaskProof=footprints,
   newOwnedGroups={model:{'actor':actor,'mesh':meshes_saved[model].get_path_name(),'material':material_saved.get_path_name(),'instances':len(measurements[model]['rootIds']),'rootIds':measurements[model]['rootIds']}for model,actor in new.items()},
   nativeGeometryReadback=geometry,materialReport=material_report,afterContentInventory=pin(checkpoint/'after-content.json'),assetDelta=delta,
   newPackages=packages,importPipelineAssets=pipelines,removedOwnImportMetadata=removed,originalSourceNodeNativeMeshBindings=node_bindings,importTemporaryActorInventory=temp_inventory,observedNonrenderingImportContainers=containers,
   allSixImportedMastersIdentifiedByFullSourceCorners=True,actorLabelsUsedForSourceMeshIdentity=False,actualCounts=guard.COUNTS,
   allOriginal12Ornamentals41Flowers36FernsRawControlsExact=True,allOriginal8949GrassAnd78TreesRawControlsExact=True,
   all384SourceOriginalRootsRetiredOnceAndReplacedOnce=True,allOriginalSourceSixAttributesAndIndexBinBytesPreserved=True,
   contactWorldBottomArithmeticCapCm=1e-7,derivedContactFloatingPointBitEqualityClaimed=False,
   sourceHeightRoleChanges384Explicit=True,sourceGroundElevationSurveyed=False)
  report_write(output/REPORT,report);print(json.dumps({'report':pin(output/REPORT),'nativeAppearanceAccepted':False}))
 except Exception as error:
  report.update(status='failed',completedAt=now(),error=str(error));report_write(output/REPORT,report);raise


if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--preflight',type=Path);a=p.parse_args()
 if a.preflight:preflight(a.preflight)
 else:main()
