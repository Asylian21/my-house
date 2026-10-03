"""Standalone bounded R30 garden overlay. Root alone launches native/Editor.

38 roots keep their original wrapped XYZ/yaw, receive whole provider shapes
and uniform scales. 435 survivors keep exact native stored data/order/controls.
Unknown AdditionalRandomSeeds are neither reconstructed nor assigned.
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
OWNER='scripts/unreal/exterior-garden-composition-native-r30.py'
s=importlib.util.spec_from_file_location('r30_owned_source_guards',ROOT/'scripts/unreal/exterior-garden-composition-guards-r30.py')
guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard)
require,read,sha,pin,check_pin,digest,exact,write=(getattr(guard,k)for k in ['require','read','sha','pin','check_pin','digest','exact','write'])
MAP='/Game/Brezi/Maps/Brezi'
REPORT='garden-composition-native-report.json'
STATUS='verified-saved-38-original-shape-garden-composition'
PREFIX=guard.PREFIX


def now():return datetime.now(timezone.utc).isoformat()
def report_write(path,row):Path(path).write_text(json.dumps(row,indent=2,allow_nan=False)+'\n')
def actors(u):return {a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
def helpers(base):return guard.old.helpers(base['bundle'])


def garden_controls(u,groups,h,witness):
 result={}
 for label,group in groups.items():
  c=h['cleanNative'].component_lookup(u,group['actor'],group['component']);count=c.get_instance_count()
  values=[h['tree'].transform_value(h['tree'].instance_value(c,i))for i in range(count)]
  require(count==len(group['rows'])and digest(values)==witness[group['actor']]['components'][0]['orderedInstanceTransformsSha256'],
   'Whole garden ordered native/source frames differ')
  for value,row in zip(values,group['rows']):exact(value[0],row['positionCm'],'Original garden native XYZ/source correspondence differs')
  result[group['actor']]={'rootIds':[r['id']for r in group['rows']],'recoveredValues':values,
   'storedMatrices':[h['tree'].matrix(c,i)for i in range(count)],'mainRandomSeed':int(c.get_editor_property('instancing_random_seed')),
   'numCustomDataFloats':int(c.get_editor_property('num_custom_data_floats')),
   'customData':[float(v)for v in c.get_editor_property('per_instance_sm_custom_data')],
   'additionalRandomSeedsReadbackAvailable':False,'seedRangesReconstructed':False}
 require(len(result)==19 and sum(len(v['rootIds'])for v in result.values())==473,'Original19garden groups/473 roots required');return result


def retained_controls(u,groups,original,source,h,witness):
 remove={r['rootId']for r in source['placements']};result={}
 for group in groups.values():
  actor=group['actor'];c=h['cleanNative'].component_lookup(u,actor,group['component']);control=original[actor]
  keep=[i for i,r in enumerate(control['rootIds'])if r not in remove]
  desired={**control,'rootIds':[control['rootIds'][i]for i in keep],
   'recoveredValues':[control['recoveredValues'][i]for i in keep],'storedMatrices':[control['storedMatrices'][i]for i in keep]}
  require(c.get_instance_count()==len(keep),'Retained garden census differs')
  observed={'rootIds':desired['rootIds'],'recoveredValues':[h['tree'].transform_value(h['tree'].instance_value(c,i))for i in range(len(keep))],
   'storedMatrices':[h['tree'].matrix(c,i)for i in range(len(keep))],'mainRandomSeed':int(c.get_editor_property('instancing_random_seed')),
   'numCustomDataFloats':int(c.get_editor_property('num_custom_data_floats')),
   'customData':[float(v)for v in c.get_editor_property('per_instance_sm_custom_data')],
   'additionalRandomSeedsReadbackAvailable':False,'seedRangesReconstructed':False}
  exact(observed,desired,'Retained raw matrices/order/recovered frames/mainseed/custom data differ')
  require(digest(observed['recoveredValues'])==witness[actor]['components'][0]['orderedInstanceTransformsSha256'],
   'Retained sidecar not bound to full saved component witness');result[actor]=observed
 require(sum(len(r['rootIds'])for r in result.values())==435,'Exact435 retained source members required');return result


def measure(u,bundle,h):
 source,groups=bundle['source'],bundle['groups'];native={}
 for group in groups.values():
  c=h['cleanNative'].component_lookup(u,group['actor'],group['component'])
  for i,row in enumerate(group['rows']):native[row['id']]=(c,i)
 values={};proof={}
 for model in source['models']:
  rows=[r for r in source['placements']if r['model']==model];desired=[];inputs=[]
  require(len(rows)==(12 if model.startswith('fern_')else 1),'Only12each fern and1each tall original shape allowed')
  transient=u.new_object(u.HierarchicalInstancedStaticMeshComponent)
  require(transient and transient.get_path_name().startswith('/Engine/Transient.')and transient.get_editor_property('static_mesh')is None,
   'Meshless unowned transient required')
  for row in rows:
   c,index=native[row['rootId']];old=h['tree'].instance_value(c,index);value=u.Transform()
   value.set_editor_property('translation',old.translation);value.set_editor_property('rotation',old.rotation)
   value.set_editor_property('scale3d',u.Vector(*row['scale']))
   old_value=h['tree'].transform_value(old);input_value=h['tree'].transform_value(value)
   exact(input_value,[old_value[0],old_value[1],row['scale']],'Wrapped original XYZ/rotation or uniform source scale changed')
   require(transient.add_instance(value,False)==len(inputs),'Unique ordered transient measurement failed')
   desired.append(value);inputs.append(input_value)
  recovered=[h['tree'].transform_value(h['tree'].instance_value(transient,i))for i in range(len(rows))]
  matrices=[h['tree'].matrix(transient,i)for i in range(len(rows))]
  for pre,got,matrix in zip(inputs,recovered,matrices):exact(pre[0],got[0],'Measured original XYZ changed');exact(matrix[3][:3],pre[0],'Stored translation differs')
  proof[model]={'rootIds':[r['rootId']for r in rows],'inputValues':inputs,'recoveredValues':recovered,'storedMatrices':matrices,
   'actualUnregisteredMeshlessTransientMeasurement':True,'wrappedOriginalXYZAndRotationCopied':True,'hostQuaternionReconstructionPerformed':False,
   'sourceUniformScaleAssigned':True,'nativeNormalTangentReadbackAvailable':False}
  transient.clear_instances();require(transient.get_instance_count()==0,'Transient members remained');values[model]=desired
 require(sum(len(v)for v in values.values())==38,'Only38 measured source replacements allowed');return values,proof


def source_footprints(source,measurements):
 mask=guard.module('r30_original_bed_and_step_predicates','exterior-garden-organic-native.py');garden=source['garden'];byid={r['rootId']:r for r in source['placements']};result=[]
 steps=[triangle for rows in garden['sourceStepTrianglesCm'].values()for triangle in rows]
 for model,m in measurements.items():
  row=source['models'][model];points=row['expectedNativeVerticesCm']
  for identity,value,matrix in zip(m['rootIds'],m['recoveredValues'],m['storedMatrices']):
   fit=byid[identity];root=fit['originalRow'];exact(value[0],root['positionCm'],'Measured original source root/contact changed')
   local=[[sum(p[j]*matrix[j][axis]for j in range(3))for axis in range(3)]for p in points]
   radius=max(math.hypot(p[0],p[1])for p in local);triangles=garden['sourceMulchTrianglesCm'][fit['sourceBedId']]
   boundary=mask._boundary(triangles);distance=min(mask._distance(value[0][:2],a,b)for a,b in boundary)
   step_distance=min(mask._distance(value[0][:2],a,b)for a,b in mask._boundary(steps))
   require(radius<root['radiusCm']and radius<distance and radius<step_distance
    and not any(mask._triangle_inside(value[0][:2],tri)for tri in steps),'Complete native-matrix crown circle escapes old crown/bed/steps')
   world=[[value[0][axis]+p[axis]for axis in range(3)]for p in local]
   require(all(any(mask._triangle_inside(p[:2],tri)for tri in triangles)for p in world),'All native-matrix projected original vertices must fit bed')
   require(min(p[2]for p in local)>=0 and value[0][2]==fit['positionCm'][2],'Root contact/bottom shift changed')
   result.append({'rootId':identity,'model':model,'decodedSourceF32VerticesChecked':len(world),'actualStoredMatrix':matrix,
    'originalNativeXYZExact':True,'oldContainingCircleRadiusCm':root['radiusCm'],'actualContainingCircleRadiusCm':radius,
    'bedBoundaryCircleClearanceCm':distance-radius,'stepBoundaryCircleClearanceCm':step_distance-radius,
    'aboveRootHeightCm':max(p[2]for p in local),'originalAuthoredHeightCm':root['actualHeightCm'],
    'sourceRequestedHeightCm':fit['requestedHeightCm'],'sourceHeightRoleChanged':fit['heightRoleChanged'],
    'actualHeightBitEqualityToSourceClaimed':False,'allVerticesAndFullCircleInOriginalBed':True,'fullCircleExcludesOriginalSteps':True,
    'sourceNativeFloatGeometryProjectionIsGpuReadback':False,'normalTangentReadbackAvailable':False})
 require(len(result)==38 and sum(r['decodedSourceF32VerticesChecked']for r in result)==32848,'Full38 crowns/32848 source vertices required');return result


def filter_original(u,bundle,h,controls):
 source,groups=bundle['source'],bundle['groups'];proof=[]
 for f in source['proposal']['sourceGroupFilters']:
  group=groups[f['groupId']];actor=actors(u)[group['actor']];c=h['cleanNative'].component_lookup(u,group['actor'],group['component'])
  control=controls[group['actor']];desired=guard.expected_control(control,f['removeSourceOrderedIndices']);order=guard.swap_remove_order(len(control['rootIds']),f['removeSourceOrderedIndices'])
  require(c.remove_instances(f['removeSourceOrderedIndices']),'Cannot remove exact selected native indices')
  exact([h['tree'].matrix(c,i)for i in range(len(order))],[control['storedMatrices'][i]for i in order],'Actual forced RemoveAtSwap order differs from installed contract')
  post=c.get_editor_property('per_instance_sm_data');keep=[i for i in range(len(control['rootIds']))if i not in f['removeSourceOrderedIndices']]
  reorder=[order.index(i)for i in keep]
  # Existing post-removal wrapped structs only: no Transform recomposition,
  # UpdateInstanceTransform, AddInstance or seed setter for survivors.
  c.set_editor_property('per_instance_sm_data',[post[i]for i in reorder]);actor.synchronize_instance_bounds()
  exact([h['tree'].matrix(c,i)for i in range(len(keep))],desired['storedMatrices'],'Retained native matrix bytes/order changed')
  exact([h['tree'].transform_value(h['tree'].instance_value(c,i))for i in range(len(keep))],desired['recoveredValues'],'Retained recovered Transform bytes/order changed')
  require(c.get_editor_property('instancing_random_seed')==control['mainRandomSeed']and c.get_editor_property('num_custom_data_floats')==0
   and not c.get_editor_property('per_instance_sm_custom_data'),'Observed mainseed/custom data changed during filtering')
  proof.append({'actor':group['actor'],'groupId':f['groupId'],'actualRemovedOriginalIndices':f['removeSourceOrderedIndices'],
   'removedRootIds':f['removeRootIds'],'nativeRemoveAtSwapSurvivorOrder':order,'restoredOriginalSurvivorOrder':keep,
   'directExistingWrappedStructOrderOnly':True,'survivorTransformRecompositionPerformed':False,'seedMutationPerformed':False,
   'additionalRandomSeedsReadbackAvailable':False,'perInstanceShaderRandomValuePreservationClaimed':False})
 for f in source['proposal']['wholeOneMemberHeroGroupRetirements']:
  group=groups[f['groupId']];c=h['cleanNative'].component_lookup(u,group['actor'],group['component']);control=controls[group['actor']]
  require(c.get_instance_count()==1 and control['numCustomDataFloats']==0 and control['customData']==[],'Whole hero one-member scope differs')
  c.clear_instances();c.get_owner().synchronize_instance_bounds();require(c.get_instance_count()==0,'Whole one-member hero retirement failed')
 return proof


def cyclic(face):return min(tuple(face[i:]+face[:i])for i in range(3))
def mesh_proof(u,mesh,row,subsystem):
 require(mesh.get_num_lods()==1 and len(mesh.get_editor_property('static_materials'))==1 and not mesh.get_editor_property('has_navigation_data'),
  'One original provider LOD, one slot, no navigation required')
 require(subsystem,'Pinned module-initializing StaticMeshEditor accessor required');settings=subsystem.get_lod_build_settings(mesh,0)
 require(all(settings.get_editor_property(k)==v for k,v in {'use_full_precision_u_vs':True,'generate_lightmap_u_vs':False,
  'recompute_normals':False,'recompute_tangents':True,'remove_degenerates':False}.items()),'Original normals/UV and requested derived-tangent build policy differs')
 d=mesh.get_static_mesh_description(0);require(d and d.get_triangle_count()==mesh.get_num_triangles(0)==row['triangles']and mesh.get_num_sections(0)==1,'Actual original triangle/section census differs')
 expected=[cyclic([tuple(row['expectedNativeVerticesCm'][i]+row['uv0'][i])for i in row['indices'][j:j+3]])for j in range(0,len(row['indices']),3)]
 got=[]
 for index in range(row['triangles']):
  face=[]
  for corner in range(3):
   vi=d.get_triangle_vertex_instance(u.TriangleID(id_value=index),corner);p=d.get_vertex_position(d.get_vertex_instance_vertex(vi));uv=d.get_vertex_instance_uv(vi,0)
   face.append(tuple(float(getattr(p,k))for k in 'xyz')+tuple(float(getattr(uv,k))for k in 'xy'))
  got.append(cyclic(face))
 require(got==expected,'Full original native F32 position/UV0/ordered topology/winding differs')
 return {'asset':mesh.get_path_name(),'lodCount':1,'triangles':row['triangles'],'sections':1,'nativeCornerSha256':digest(got),
  'fullOrderedNativeF32PositionUV0WindingVerified':True,'originalProviderLodChainPresent':False,'sourceNormalBytesPreserved':True,
  'sourceTangentsPresent':False,'nativeTangentsRequestedFromOriginalUv':True,'nativeTangentGenerationNumericallyVerified':False,
  'nativeNormalTangentReadbackAvailable':False,'nativeNaniteRequested':False,'meshPackageIndependentlyUnloaded':False}


def import_geometry(u,bundle,materials,h):
 source=bundle['source'];assets=u.EditorAssetLibrary;actor_system=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem);pipelines=[]
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
 require(manager.import_scene(PREFIX+'/Geometry',manager.create_source_data(str(check_pin(source['draft']['glb']))),params),'Five original forms import failed')
 temporary=[a for path,a in actors(u).items()if path not in before];found=[c.get_editor_property('static_mesh')for a in temporary for c in a.get_components_by_class(u.StaticMeshComponent)]
 require(len(found)==5 and all(found)and len({m.get_path_name()for m in found})==5,'Exactly five distinct original masters required');result={}
 subsystem=h['meshHelper'].static_mesh_subsystem(u)
 for key,row in source['models'].items():
  matches=[m for m in found if m.get_name()==row['exportName']or m.get_name().endswith('_'+row['exportName'])];require(len(matches)==1,'Original imported master name ambiguous');mesh=matches[0]
  target=PREFIX+'/Geometry/StaticMeshes/'+row['exportName']
  if mesh.get_path_name().split('.')[0]!=target:require(assets.rename_asset(mesh.get_path_name().split('.')[0],target),'Cannot canonicalize own master');mesh=assets.load_asset(target)
  mesh.set_material(0,materials[row['materialKey']]);mesh.set_editor_property('has_navigation_data',False)
  require(mesh.get_num_lods()==1,'No cloned or reduced source LODs allowed');settings=subsystem.get_lod_build_settings(mesh,0)
  for k,v in {'use_full_precision_u_vs':True,'generate_lightmap_u_vs':False,'recompute_normals':False,'recompute_tangents':True,'remove_degenerates':False}.items():settings.set_editor_property(k,v)
  subsystem.set_lod_build_settings(mesh,0,settings);assets.set_metadata_tag(mesh,'BreziGeneratedBy',OWNER);assets.set_metadata_tag(mesh,'BreziR30OriginalAttributeSource',digest(row['sourceAttributeByteSha256']))
  require(assets.save_loaded_asset(mesh,only_if_is_dirty=False),'Cannot save owned original master');result[key]=mesh
 h['meshHelper'].finish_static_mesh_compilation(u,synchronous=True)
 for key,mesh in result.items():mesh_proof(u,mesh,source['models'][key],subsystem)
 for actor in reversed(temporary):require(actor_system.destroy_actor(actor),'Cannot remove owned import actor')
 canonical={m.get_path_name().split('.')[0]for m in result.values()};removed=[]
 for path in assets.list_assets(PREFIX+'/Geometry',recursive=True,include_folder=False):
  value=assets.load_asset(path)
  if value and value.get_path_name().split('.')[0]in canonical:continue
  require(value and value.get_class().get_name()in ['InterchangeSceneImportAsset','ObjectRedirector'],'Unexpected owned import artifact')
  removed.append(value.get_path_name());require(assets.delete_asset(path),'Cannot remove own import metadata')
 for p in pipelines:require(assets.save_loaded_asset(p,only_if_is_dirty=False),'Cannot save owned import pipeline')
 return result,[p.get_path_name()for p in pipelines],removed


def apply_new(u,bundle,h,values,meshes,materials,measurements):
 system=u.get_editor_subsystem(u.EditorActorSubsystem);result={};expected={}
 for model in bundle['source']['models']:
  a=system.spawn_actor_from_class(u.load_class(None,'/Script/BreziTwin.BreziVegetationPatch'),u.Vector(0,0,0),u.Rotator());require(a,'Cannot spawn own original-shape group')
  a.tags=[u.Name('BreziGenerated'),u.Name(guard.TAG)];a.set_actor_label('R30_'+model);a.set_folder_path('Brezi/GardenComposition20261002R30');a.set_actor_tick_enabled(False)
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
 scene=actors(u);require({p for p,a in scene.items()if a.actor_has_tag(guard.TAG)}==set(new.values()),'Owned actor namespace widened')
 for model,path in new.items():
  a=scene[path];c=a.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent);m=measurements[model]
  require(c and a.get_editor_property('root_component')==c and c.get_owner()==a and c.get_instance_count()==len(m['rootIds']), 'Own source group root/owner/census differs')
  require(c.get_editor_property('static_mesh').get_path_name()==meshes[model].get_path_name()and c.get_num_materials()==1
   and c.get_material(0).get_path_name()==materials[bundle['source']['models'][model]['materialKey']].get_path_name(),'Saved exact original master/default material differs')
  exact([h['tree'].transform_value(h['tree'].instance_value(c,i))for i in range(c.get_instance_count())],m['recoveredValues'],'Measured new recovered frames differ')
  exact([h['tree'].matrix(c,i)for i in range(c.get_instance_count())],m['storedMatrices'],'Measured new stored FMatrix differs')


def old_materials(u,base,h):
 original=guard.old.base_materials(u,base['bundle'],h)
 h['treeMaterials'].verify_materials(u,base['bundle']['donor']['report']['materials'],h['existing'].graph_snapshot)
 return {'original56':original,'originalTree3':base['bundle']['donor']['report']['materials'],'scopedMaterialGraphs':59,'scopedTextureObjects':87}


def old_tree_controls(u,base,h):
 remaining=guard.old.grove_controls(u,base['bundle'],h,True)
 exact(remaining,read(check_pin(base['report']['remaining74Saved'])),'Actual remaining74 tree raw controls differ from immutable base')
 group=base['report']['newOriginalTreeGroup'];c=h['cleanNative'].component_lookup(u,group['actor'],'Instances')
 m=read(check_pin(group['measurement']));require(c.get_instance_count()==4,'Actual saved R29 tree group differs')
 owned={'recoveredValues':[h['tree'].transform_value(h['tree'].instance_value(c,i))for i in range(4)],
  'storedMatrices':[h['tree'].matrix(c,i)for i in range(4)],'mainRandomSeed':int(c.get_editor_property('instancing_random_seed')),
  'numCustomDataFloats':int(c.get_editor_property('num_custom_data_floats')),
  'customData':[float(v)for v in c.get_editor_property('per_instance_sm_custom_data')],
  'additionalRandomSeedsReadbackAvailable':False,'seedRangesReconstructed':False}
 exact(owned['recoveredValues'],m['recoveredValues'],'Actual original4 recovered tree frames differ');exact(owned['storedMatrices'],m['storedMatrices'],'Actual original4 stored tree matrices differ')
 return {'original74':remaining,'ownedR29Four':owned}


def primary_api():
 root=Path('/Users/Shared/Epic Games/UE_5.8/Engine/Source');paths={
  'hismRemoval':root/'Runtime/Engine/Private/HierarchicalInstancedStaticMesh.cpp',
  'instanceStorage':root/'Runtime/Engine/Classes/Components/InstancedStaticMeshComponent.h',
  'rootComponent':root/'Runtime/Engine/Classes/GameFramework/Actor.h',
  'materialPipeline':root.parent/'Plugins/Interchange/Runtime/Source/Pipelines/Public/InterchangeGenericAssetsPipeline.h'}
 require('PerInstanceSMData'in paths['instanceStorage'].read_text()and 'RemoveAtSwap'in paths['hismRemoval'].read_text()
  and 'K2_GetRootComponent'in paths['rootComponent'].read_text()and 'MaterialPipeline'in paths['materialPipeline'].read_text(), 'Installed primary APIs differ')
 return {k:pin(v)for k,v in paths.items()}


def input_files(plan,bundle):
 files=dict(plan['inputFiles']);terminal=read(bundle['base']['process']['receipt']['path']);files.update(terminal['sourcePinsBeforeNative'])
 for row in plan['ownedSources'].values():files[row['path']]=row['sha256']
 for path in [guard.PLAN,guard.CANDIDATE/'garden-composition-project-clone.json']:
  files[str(path)]=sha(path)
 for row in primary_api().values():files[row['path']]=row['sha256']
 return files


def preflight(output):
 require(Path(output).resolve()==guard.STUDY/'source-preflight'and not Path(output).exists(),'Fresh typed preflight path required')
 plan,bundle=guard.validate_plan();source,base=bundle['source'],bundle['base'];clone=guard.validate_clone(source,base);h=helpers(base)
 for project in [base['project'],guard.CANDIDATE/'Project/BreziTwin']:
  require(guard.old.guard.g.inventory(project/'Content')==base['content']and guard.old.guard.g.project_proof(project)==base['protected'],
   'Current actual base/clone full byte inventory differs')
 output=Path(output).resolve();output.mkdir();command=[sys.executable,'-B',str(ROOT/'scripts/unreal/test_exterior_garden_composition_r30.py')]
 run=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=120);log=output/'cpu-guards.log';log.write_text(run.stdout+run.stderr);require(run.returncode==0,'Meaningful R30 CPU guards failed')
 inputs=input_files(plan,bundle);inputs[str(log)]=sha(log)
 row={'schema':guard.SCHEMA,'owner':OWNER,'status':'source-preflight-validated-38-garden-roots-native-pending','createdAt':now(),
  'selectedPlan':pin(guard.PLAN),'sourceProposal':pin(guard.PROPOSAL),'sourceDraft':pin(guard.GEOMETRY/'source-native-draft.json'),
  'baseNativeReport':base['reportPin'],'baseNativeProcess':base['process'],'baseCurrentByteAudit':base['audit'],'projectClone':clone,
  'moduleOrderWitness':h['moduleOrderWitness'],'primaryApi':primary_api(),'inputFiles':inputs,'expectedCounts':guard.COUNTS,
  'tests':{'command':command,'exitCode':0,'testCount':12,'log':pin(log)},'nativeExecuted':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False}
 write(output/'source-preflight.json',row);print(json.dumps({'preflight':pin(output/'source-preflight.json'),'nativeExecuted':False}))


def validate_preflight(path,plan,bundle):
 require(Path(path).resolve()==guard.STUDY/'source-preflight/source-preflight.json','Known typed preflight only');row=read(path)
 require(row['schema']==guard.SCHEMA and row['owner']==OWNER and row['status']=='source-preflight-validated-38-garden-roots-native-pending'
  and row['selectedPlan']==pin(guard.PLAN)and row['sourceProposal']==pin(guard.PROPOSAL)and row['sourceDraft']==pin(guard.GEOMETRY/'source-native-draft.json')
  and row['baseNativeReport']==bundle['base']['reportPin']and row['baseNativeProcess']==bundle['base']['process']and row['projectClone']==guard.validate_clone(bundle['source'],bundle['base'])
  and row['expectedCounts']==guard.COUNTS and row['tests']['exitCode']==0 and row['tests']['testCount']==12 and row['nativeExecuted']is False,'Exact source/base/count preflight differs')
 expected=input_files(plan,bundle);expected[row['tests']['log']['path']]=row['tests']['log']['sha256'];require(row['inputFiles']==expected,'Exact preflight closure differs')
 require(row['primaryApi']==primary_api(),'Installed source API pins changed')
 check_pin(row['tests']['log'])
 for p,value in row['inputFiles'].items():require(sha(p)==value,'Consumed immutable source changed')
 return row


def main():
 import unreal as u
 output=guard.CANDIDATE;project=output/'Project/BreziTwin'
 require(Path(os.environ['BREZI_GARDEN_COMPOSITION_OUTPUT']).resolve()==output and Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project,'Wrong own R30 project')
 require(not(output/REPORT).exists()and not(output/'exterior-import-report.json').exists(),'Fresh own typed report only')
 plan,bundle=guard.validate_plan();source,base=bundle['source'],bundle['base'];pfpath=Path(os.environ['BREZI_GARDEN_COMPOSITION_PREFLIGHT']).resolve()
 require(sha(pfpath)==os.environ['BREZI_GARDEN_COMPOSITION_PREFLIGHT_SHA256']and sha(guard.PLAN)==os.environ['BREZI_GARDEN_COMPOSITION_PLAN_SHA256'],'Selected source/preflight changed')
 pf=validate_preflight(pfpath,plan,bundle);h=helpers(base);require(h['moduleOrderWitness']==pf['moduleOrderWitness'],'Actual frozen-first policy differs')
 maps=guard.module('r30_owned_original_materials','exterior-garden-composition-materials-r30.py');maps.preflight_enums(u);maps.validate_recipe(source['recipe'])
 for p in [project,base['project']]:require(guard.old.guard.g.inventory(p/'Content')==base['content']and guard.old.guard.g.project_proof(p)==base['protected'],'Original/current candidate bytes differ')
 module=project/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib';require(sha(module)=='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574','Protected native module changed')
 checkpoint=output/'garden-composition-checkpoint';require(not checkpoint.exists(),'Fresh checkpoint required');checkpoint.mkdir()
 report={'schema':guard.SCHEMA,'owner':OWNER,'status':'running','startedAt':now(),'nativeProcessId':os.getpid(),'output':str(output),'project':str(project),
  'selectedPlan':pin(guard.PLAN),'sourceProposal':pin(guard.PROPOSAL),'sourceDraft':pin(guard.GEOMETRY/'source-native-draft.json'),'sourcePreflight':pin(pfpath),
  'baseNativeReport':base['reportPin'],'baseNativeProcess':base['process'],'baseCurrentByteAudit':base['audit'],'baseContentInventory':base['report']['afterContentInventory'],
  'protectedProjectProof':base['report']['protectedProjectProof'],'projectClone':pf['projectClone'],'inputFiles':pf['inputFiles'],'moduleOrderWitness':h['moduleOrderWitness'],
  'nativeModuleWitness':{'source':str(base['project']/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),'destination':str(module),'sha256':sha(module),
   'bytes':module.stat().st_size,'independentInodes':module.stat().st_ino!=(base['project']/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib').stat().st_ino},
  'activeDesign':plan['activeDesign'],'setbacksMm':plan['setbacksMm'],'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,
  'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,'ecologicalFitVerified':False,'surveyedPlacementVerified':False,
  'nativeNormalTangentReadbackAvailable':False,'meshMaterialPackagesIndependentlyUnloaded':False,'AdditionalRandomSeedsReadbackAvailable':False,
  'retainedTransformRecompositionPerformed':False,'seedMutationPerformed':False,'perInstanceShaderRandomValuePreservationClaimed':False}
 report_write(output/REPORT,report)
 try:
  levels=u.get_editor_subsystem(u.LevelEditorSubsystem);require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot load own saved R29 clone')
  before=h['cleanNative'].full_witness(u,h);require(before==base['witness'],'All5351 original actors/policies differ')
  materials_before=old_materials(u,base,h);grass_before=h['cleanNative'].original_grass_controls(u,h['cleanBundle']);trees_before=old_tree_controls(u,base,h)
  controls=garden_controls(u,bundle['groups'],h,before);values,measurement=measure(u,bundle,h);footprints=source_footprints(source,measurement)
  require(h['cleanNative'].full_witness(u,h)==before,'Transient source measurement changed original scene')
  materials,material_report=maps.build_materials(u,source['recipe'],h['existing'].graph_snapshot)
  meshes,pipelines,removed=import_geometry(u,bundle,materials,h);require(h['cleanNative'].full_witness(u,h)==before,'Own asset import changed original actors')
  filter_proof=filter_original(u,bundle,h,controls);expected=guard.expected_original(before,bundle['groups'],controls,source['proposal'])
  require(h['cleanNative'].full_witness(u,h)==expected,'Original scene exceeds exact2partial+2whole garden filter')
  new,added=apply_new(u,bundle,h,values,meshes,materials,measurement);expected.update(added)
  verify_new(u,bundle,h,new,measurement,meshes,materials);require(h['cleanNative'].full_witness(u,h)==expected,'Full5356 actor counterfactual differs')
  retained=retained_controls(u,bundle['groups'],controls,source,h,expected)
  for name,value in [('before-actors',before),('expected-actors',expected),('original-garden-controls',controls),('retained-garden-controls-before-save',retained),
   ('source-native-measurements',measurement),('old-materials-before',materials_before),('old-tree-controls-before',trees_before),
   ('old-grass-controls-before',grass_before)]:write(checkpoint/(name+'.json'),value)
  require(levels.save_current_level(),'Cannot save bounded garden candidate');require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot unload/reload bounded candidate')
  saved=h['cleanNative'].full_witness(u,h);require(saved==expected,'Saved full5356 counterfactual differs')
  hisms=[c for a in saved.values()for c in a['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
  require(len(saved)==5356 and len(hisms)==2318 and sum(c['instanceCount']for c in hisms)==676957,'Saved fullscene count/population differs')
  materials_saved=maps.verify_materials(u,material_report,source['recipe'],h['existing'].graph_snapshot)
  meshes_saved={k:u.EditorAssetLibrary.load_asset(m.get_path_name())for k,m in meshes.items()};verify_new(u,bundle,h,new,measurement,meshes_saved,materials_saved)
  geometry={k:mesh_proof(u,m,source['models'][k],h['meshHelper'].static_mesh_subsystem(u))for k,m in meshes_saved.items()}
  saved_retained=retained_controls(u,bundle['groups'],controls,source,h,saved);exact(saved_retained,retained,'Saved435 raw matrices/order/mainseed/custom differ')
  materials_old_saved=old_materials(u,base,h);require(materials_old_saved==materials_before,'Original59graphs/87textures observed witnesses changed')
  grass_saved=h['cleanNative'].original_grass_controls(u,h['cleanBundle']);trees_saved=old_tree_controls(u,base,h)
  exact(grass_saved,grass_before,'Original8949 grass controls changed')
  exact(trees_saved,trees_before,'Original78 tree matrices/order/mainseed/custom controls changed')
  # R29 original-tree group and all74 other grove actors remain byte-exact in
  # the complete actor counterfactual; no tree member setters are used here.
  packages=[m.get_path_name().split('.')[0]for m in meshes_saved.values()]+[p.split('.')[0]for p in pipelines]+[p.split('.')[0]for p in material_report['newPackageAssets']]
  content=guard.old.guard.g.inventory(project/'Content');delta=guard.validate_content(base['content'],content,packages)
  require(guard.old.guard.g.project_proof(project)==base['protected']and guard.old.guard.g.inventory(base['project']/'Content')==base['content']
   and guard.old.guard.g.project_proof(base['project'])==base['protected'],'Protected or original R29 project changed')
  for p,value in pf['inputFiles'].items():require(sha(p)==value,'Frozen consumed source changed')
  for name,value in [('saved-actors',saved),('retained-garden-controls-saved',saved_retained),('old-materials-saved',materials_old_saved),('after-content',content),
   ('old-tree-controls-saved',trees_saved),('old-grass-controls-saved',grass_saved)]:write(checkpoint/(name+'.json'),value)
  report.update(status=STATUS,completedAt=now(),nativeApplied=True,savedMapUnloadedReloaded=True,sourceInputsUnchanged=True,originalSavedR29Unchanged=True,
   actualCounts=guard.COUNTS,newOwnedGroups={k:{'actor':v,'rootIds':measurement[k]['rootIds'],'instances':len(measurement[k]['rootIds']),
    'mesh':meshes_saved[k].get_path_name(),'material':materials_saved[source['models'][k]['materialKey']].get_path_name()}for k,v in new.items()},
   originalPartialFilters=filter_proof,wholeOneMemberHeroRetirements=source['proposal']['wholeOneMemberHeroGroupRetirements'],
   originalGarden435RawMatricesOrderMainSeedCustomDataExact=True,original8949GrassRawControlsExact=True,allOriginal78TreeRawControlsExact=True,allOriginalGroveActorsFullWitnessExact=True,
   sourceHeightRoleChanges36Explicit=True,twoTallHeroAuthoredSourceHeightRecipesPreserved=True,sourceCrownMaskProof=footprints,
   newSourceNativeMeasurements=pin(checkpoint/'source-native-measurements.json'),nativeGeometryReadback=geometry,materialReport=material_report,
   importPipelineAssets=pipelines,discardedTransientImportMetadata=removed,newPackages=packages,assetDelta=delta,
   beforeActorWitness=pin(checkpoint/'before-actors.json'),expectedActorWitness=pin(checkpoint/'expected-actors.json'),savedActorWitness=pin(checkpoint/'saved-actors.json'),
   beforeActorWitnessSha256=digest(before),expectedActorWitnessSha256=digest(expected),savedActorWitnessSha256=digest(saved),
   originalGardenControls=pin(checkpoint/'original-garden-controls.json'),retainedGardenControlsBeforeSave=pin(checkpoint/'retained-garden-controls-before-save.json'),
   retainedGardenControlsSaved=pin(checkpoint/'retained-garden-controls-saved.json'),originalMaterialsBefore=pin(checkpoint/'old-materials-before.json'),
   originalMaterialsSaved=pin(checkpoint/'old-materials-saved.json'),afterContentInventory=pin(checkpoint/'after-content.json'),
   originalTreesBefore=pin(checkpoint/'old-tree-controls-before.json'),originalTreesSaved=pin(checkpoint/'old-tree-controls-saved.json'),
   originalGrassBefore=pin(checkpoint/'old-grass-controls-before.json'),originalGrassSaved=pin(checkpoint/'old-grass-controls-saved.json'),
   uniqueSourceTriangles=4478,instancedSourceTriangles=46806,sourceGroundElevationSurveyed=False)
  report_write(output/REPORT,report);print(json.dumps({'report':pin(output/REPORT),'status':STATUS,'nativeAppearanceAccepted':False}))
 except Exception as error:
  report.update(status='failed',completedAt=now(),error=str(error));report_write(output/REPORT,report);raise


if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--preflight',type=Path);args=parser.parse_args()
 if args.preflight:preflight(args.preflight)
 else:main()
