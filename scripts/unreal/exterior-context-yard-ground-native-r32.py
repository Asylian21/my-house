"""Root-only R32 saved ground/detail overlay on actual successful R30b.

Existing floors receive source-bounded mesh/material overrides, the old coarse
worn-edge component hides, and one clipped substrate plus1274 new low roots add.
All original roots, building/road/light/navigation policies remain protected.
"""
import argparse
import copy
from datetime import datetime,timezone
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-ground-native-r32.py'
s=importlib.util.spec_from_file_location('r32_closed_native_source',ROOT/'scripts/unreal/exterior-context-yard-ground-native-guards-r32.py')
guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard)
require,read,sha,pin,check_pin,digest,write=(getattr(guard,k)for k in('require','read','sha','pin','check_pin','digest','write'))
PREFIX,TAG=guard.PREFIX,guard.TAG
REPORT='context-yard-ground-native-report.json'
STATUS='verified-saved-resolved-context-yard-ground-and-low-detail'
MAP='/Game/Brezi/Maps/Brezi'


def now():return datetime.now(timezone.utc).isoformat()
def report_write(path,row):Path(path).write_text(json.dumps(row,indent=2,allow_nan=False)+'\n')
def vec(value,axes='xyz'):return [float(getattr(value,k))for k in axes]
def value(transform):return [vec(transform.translation),vec(transform.rotation,'xyzw'),vec(transform.scale3d)]
def matrix(component,index):
 m=component.get_editor_property('per_instance_sm_data')[index].get_editor_property('transform')
 return [vec(getattr(m,p),'xyzw')for p in('x_plane','y_plane','z_plane','w_plane')]
def binary64(v):
 if isinstance(v,(list,tuple)):return b''.join(binary64(x)for x in v)
 require(type(v)in(float,int),'Numeric measured frame required');return struct.pack('<d',v)
def exact(a,b,message):require(binary64(a)==binary64(b),message)
def root_record(row):return {'positionCm':row['positionCm'],'yawDeg':row['yawDegrees'],'scale':[row['uniformScale']]*3}


def helpers(base):
 # Establish the immutable policy cache first, through successful R30/R29/R27.
 h=base['native'].helpers(base['r30Bundle']['base']);h['r21']=h['foreground']
 h['meshHelper']=guard.static_mesh_api();return h


def all_controls(u,base,h,witness):
 n=base['native'];b=base['r30Bundle'];r=base['report']
 grass=h['cleanNative'].original_grass_controls(u,h['cleanBundle']);trees=n.old_tree_controls(u,b['base'],h)
 retained=n.retained_controls(u,b['groups'],read(check_pin(r['originalGardenControls'])),b['source'],h,witness)
 require(grass==read(check_pin(r['originalGrassSaved']))and trees==read(check_pin(r['originalTreesSaved']))
  and retained==read(check_pin(r['retainedGardenControlsSaved'])),'Actual original grass/tree/garden raw controls differ')
 original=n.old_materials(u,b['base'],h)
 require(original==read(check_pin(r['originalMaterialsSaved'])),'Original59 observed graphs/87textures differ')
 maps=guard.module('r32_r30_original_material_readback','exterior-garden-composition-materials-r30.py')
 maps.verify_materials(u,r['materialReport'],b['source']['recipe'],h['existing'].graph_snapshot)
 measurements=read(check_pin(r['newSourceNativeMeasurements']))
 meshes={k:u.EditorAssetLibrary.load_asset(v['mesh'])for k,v in r['newOwnedGroups'].items()}
 materials={k:u.EditorAssetLibrary.load_asset(v['asset'])for k,v in r['materialReport']['materials'].items()}
 n.verify_new(u,b,h,{k:v['actor']for k,v in r['newOwnedGroups'].items()},measurements,meshes,materials)
 return {'grass':grass,'trees':trees,'retainedGarden':retained,'observedOldMaterials':original,'r30MaterialReport':r['materialReport']}


def measure_groups(u,bundle,h):
 values={};records={}
 for mid in guard.MODELS:
  rows=[r for r in bundle['proposal']['planting']if r['modelId']==mid];component=u.new_object(u.HierarchicalInstancedStaticMeshComponent)
  require(component and component.get_path_name().startswith('/Engine/Transient.')and component.get_editor_property('static_mesh')is None,
   'Unregistered meshless transient required')
  transforms=[h['rural'].instance_transform(u,root_record(r))for r in rows];pre=[value(v)for v in transforms]
  exact([v[0]for v in pre],[r['positionCm']for r in rows],'Source input positions changed')
  exact([v[2]for v in pre],[[r['uniformScale']]*3 for r in rows],'Source input uniform scales changed')
  indices=list(component.add_instances(transforms,True,False,False));require(indices==list(range(len(rows))),'Transient source frame order differs')
  recovered=[value(h['rural'].instance_value(component,i))for i in indices];stored=[matrix(component,i)for i in indices]
  exact([v[0]for v in recovered],[r['positionCm']for r in rows],'Native source root XYZ changed during insertion')
  records[mid]={'rootIds':[r['id']for r in rows],'preInsertionValues':pre,'recoveredValues':recovered,'actualMatrices':stored,
   'nativeUnregisteredMeshlessTransientMeasured':True,'originalActorOrMemberMutated':False}
  component.clear_instances();require(component.get_instance_count()==0,'Transient source rows remained');values[mid]=transforms
 require(sum(len(v)for v in values.values())==1274,'Exactly1274 source new roots required');return values,records


def native_master_vertices(u,bundle,h):
 result={};subsystem=h['meshHelper'].static_mesh_subsystem(u)
 for mid in guard.MODELS:
  source=bundle['nativeMasters'][mid];mesh=u.EditorAssetLibrary.load_asset(source['mesh'])
  require(mesh and mesh.get_num_lods()==3 and list(subsystem.get_lod_screen_sizes(mesh))==source['lodScreens']
   and [mesh.get_num_triangles(i)for i in range(3)]==source['lodTriangles']
   and [mesh.get_material(i).get_path_name()for i in range(len(mesh.get_editor_property('static_materials')))]==source['materials'],
   'Existing low master three-LOD/slot/screen/triangle binding differs')
  points=[];counts=[]
  for lod in range(3):
   desc=mesh.get_static_mesh_description(lod);require(desc and desc.get_triangle_count()==source['lodTriangles'][lod],'Existing complete native LOD unavailable')
   unique={}
   for j in range(desc.get_triangle_count()):
    for corner in range(3):
     vi=desc.get_triangle_vertex_instance(u.TriangleID(id_value=j),corner);vertex=desc.get_vertex_instance_vertex(vi);identity=int(vertex.id_value)
     if identity not in unique:unique[identity]=vec(desc.get_vertex_position(vertex))
   points.extend(unique.values());counts.append(len(unique))
  result[mid]={'points':points,'uniqueNativeVerticesPerLod':counts,'sourceMesh':source['mesh'],'allThreeNativeLodsDecoded':True}
 return result


def verify_footprints(bundle,measurements,native_vertices):
 result=[]
 for mid,m in measurements.items():
  roots=[r for r in bundle['proposal']['planting']if r['modelId']==mid]
  require(m['rootIds']==[r['id']for r in roots],'Measured whole-root identity differs')
  for root,recovered,stored in zip(roots,m['recoveredValues'],m['actualMatrices']):
   exact(recovered[0],root['positionCm'],'Actual source root XYZ moved');domain=bundle['plantingDomains'][root['buildingSourceId']];radius=0.;height=-math.inf
   for point in native_vertices[mid]['points']:
    local=[sum(point[j]*stored[j][k]for j in range(3))for k in range(3)];world=[stored[3][k]+local[k]for k in range(3)]
    require(domain.contains(world[:2])and all(not mask.contains(world[:2])for mask in bundle['masks'].values()),
     'Actual all-LOD low-growth vertex escapes original source planting/mask domain')
    radius=max(radius,math.hypot(*local[:2]));height=max(height,local[2])
   require(domain.distance(recovered[0][:2],radius+1)>radius
    and all(not mask.contains(recovered[0][:2])and mask.distance(recovered[0][:2],radius+21)>radius+20 for mask in bundle['masks'].values()),
    'Complete actual containing circle crosses source planting/exclusion')
   for shrub in bundle['layout']['planting']:
    require(math.dist(recovered[0][:2],shrub['positionCm'][:2])>radius+shrub['radialEnvelopeCm']+12.,'Actual low growth overlaps retained13 shrub crown')
   result.append({'rootId':root['id'],'modelId':mid,'actualRootXYZ':recovered[0],'actualAllNativeLodRadiusCm':radius,
    'actualAbovePivotHeightCm':height,'allNativeLodVerticesAndContainingCircleInsideSourceMasks':True,'originalShrubClearancePreserved':True})
 require(len(result)==1274,'All1274 complete native low-growth masks required');return result


def native_mesh_proof(u,mesh,source,h):
 subsystem=h['meshHelper'].static_mesh_subsystem(u);description=mesh.get_static_mesh_description(0);expected=guard.corners(source)
 require(mesh.get_num_lods()==1 and description and description.get_triangle_count()==mesh.get_num_triangles(0)==len(expected)
  and mesh.get_num_sections(0)==1 and not mesh.get_editor_property('has_navigation_data')
  and not mesh.get_editor_property('nanite_settings').get_editor_property('enabled'),'Ground actual LOD/count/section/nav/Nanite differs')
 settings=subsystem.get_lod_build_settings(mesh,0)
 require(all(settings.get_editor_property(k)==v for k,v in {'use_full_precision_u_vs':True,'generate_lightmap_u_vs':False,
  'recompute_normals':False,'recompute_tangents':True,'remove_degenerates':False}.items()),'Generated source UV/normal/tangent topology policy differs')
 actual=[]
 for j in range(len(expected)):
  face=[]
  for corner in range(3):
   vi=description.get_triangle_vertex_instance(u.TriangleID(id_value=j),corner)
   point=vec(description.get_vertex_position(description.get_vertex_instance_vertex(vi)))
   face.append(tuple(point+vec(description.get_vertex_instance_uv(vi,0),'xy')+vec(description.get_vertex_instance_uv(vi,1),'xy')))
  actual.append(guard.cyclic(face))
 require(actual==expected,'Full generated native ordered F32 position/UV0/UV1/winding differs')
 return {'mesh':mesh.get_path_name(),'triangles':len(actual),'nativeOrderedF32PositionUv0Uv1CornerSha256':digest(actual),
  'fullOrderedNativeGeometryVerified':True,'nativeNormalTangentReadbackAvailable':False}


def import_geometry(u,bundle,materials,h):
 assets=u.EditorAssetLibrary;actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem);pipelines=[]
 for original,name in(('GLTFSceneAssets','Assets'),('GLTFMaterials','Materials'),('LevelActors','Level')):
  path=PREFIX+'/Pipeline/'+name;require(not assets.does_asset_exist(path),'Fresh own import pipeline required')
  p=assets.duplicate_asset('/Game/Brezi/Pipeline/'+original,path);require(p,'Cannot copy own importer');pipelines.append(p)
 mp=pipelines[0].get_editor_property('mesh_pipeline')
 for k,v in {'combine_static_meshes_behavior':u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,'collision':False,'build_nanite':False,'generate_lightmap_u_vs':False}.items():mp.set_editor_property(k,v)
 common=pipelines[0].get_editor_property('common_meshes_properties')
 for k,v in {'remove_degenerates':False,'recompute_normals':False,'recompute_tangents':True,'use_full_precision_u_vs':True}.items():common.set_editor_property(k,v)
 material_pipeline=pipelines[0].get_editor_property('material_pipeline');material_pipeline.set_editor_property('import_materials',False)
 material_pipeline.get_editor_property('texture_pipeline').set_editor_property('import_textures',False)
 pipelines[2].set_editor_property('scene_hierarchy_type',u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
 params=u.ImportAssetParameters()
 for k,v in {'is_automated':True,'replace_existing':False,'force_show_dialog':False,'override_pipelines':[u.SoftObjectPath(v.get_path_name())for v in pipelines],
  'import_level':levels.get_current_level()}.items():params.set_editor_property(k,v)
 before={a.get_path_name()for a in actors.get_all_level_actors()};manager=u.InterchangeManager.get_interchange_manager_scripted()
 require(manager.import_scene(PREFIX+'/Geometry',manager.create_source_data(str(check_pin(bundle['plan']['sourceGlb']))),params),'Own generated R32 source import failed')
 temporary=[a for a in actors.get_all_level_actors()if a.get_path_name()not in before];meshes={};records={r['id']:r for r in bundle['proposal']['meshes']}
 for actor in temporary:
  for c in actor.get_components_by_class(u.StaticMeshComponent):
   mesh=c.get_editor_property('static_mesh');require(mesh and mesh.get_path_name().startswith(PREFIX+'/Geometry/'),'Unexpected import object')
   matches=[k for k in records if k+'_LOD0'==mesh.get_name()];require(len(matches)==1,'Ambiguous generated source master');meshes[matches[0]]=mesh
 require(set(meshes)==set(records),'Exactly3 generated ground masters required')
 subsystem=h['meshHelper'].static_mesh_subsystem(u)
 for identity,mesh in meshes.items():
  row=records[identity];material=materials['yard_substrate_r32'if row['role']=='yard_substrate'else'yard_gravel_r32']
  mesh.set_material(0,material);mesh.set_editor_property('has_navigation_data',False)
  settings=subsystem.get_lod_build_settings(mesh,0)
  for k,v in {'use_full_precision_u_vs':True,'generate_lightmap_u_vs':False,'recompute_normals':False,'recompute_tangents':True,'remove_degenerates':False}.items():settings.set_editor_property(k,v)
  subsystem.set_lod_build_settings(mesh,0,settings);assets.set_metadata_tag(mesh,'BreziGeneratedBy',OWNER)
  require(assets.save_loaded_asset(mesh,False),'Cannot save generated master')
 h['meshHelper'].finish_static_mesh_compilation(u,synchronous=True)
 for identity,mesh in meshes.items():native_mesh_proof(u,mesh,records[identity],h)
 for actor in reversed(temporary):require(actors.destroy_actor(actor),'Cannot destroy own import actor')
 for pipeline in pipelines:require(assets.save_loaded_asset(pipeline,False),'Cannot save own importer')
 known={m.get_path_name().split('.')[0]for m in meshes.values()};removed=[]
 for path in assets.list_assets(PREFIX+'/Geometry',recursive=True,include_folder=False):
  if path.split('.')[0]in known:continue
  obj=assets.load_asset(path);require(obj and obj.get_class().get_name()in('InterchangeAssetImportData','InterchangeSceneImportAsset'), 'Unknown import package may not be deleted')
  require(assets.delete_asset(path),'Cannot remove own scene-only importer metadata');removed.append(path)
 return meshes,[v.get_path_name()for v in pipelines],removed


def apply_scene(u,bundle,h,targets,meshes,materials,values):
 lookup=h['cleanNative'].component_lookup
 for role in('entry_walk','service_court'):
  t=targets[role];c=lookup(u,t['actor'],t['component']);require(c.get_editor_property('static_mesh').get_path_name()==t['originalMesh'],'Old floor binding changed')
  require(c.set_static_mesh(meshes['yard_ground_r32_'+role]),'Cannot rebind exact own-floor replacement');c.set_material(0,materials['yard_gravel_r32'])
 t=targets['worn_edge'];c=lookup(u,t['actor'],t['component']);c.set_visibility(False,False);c.set_hidden_in_game(True,False)
 actors=u.get_editor_subsystem(u.EditorActorSubsystem);added={}
 def configure(a,identity,shadow):
  require(a,'Cannot create owned R32 actor');a.tags=[u.Name('BreziGenerated'),u.Name(TAG)];a.set_actor_label(identity)
  a.set_folder_path('Brezi/ContextYardGround20261002R32');a.set_actor_tick_enabled(False)
  c=a.get_component_by_class(u.StaticMeshComponent);require(c,'Own root component missing');h['rural'].new_component_policy(u,c)
  c.set_editor_property('cast_shadow',shadow);c.set_editor_property('visible_in_ray_tracing',True);added[identity]=a.get_path_name();return c
 identity='yard_ground_r32_yard_substrate';a=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0),u.Rotator())
 c=configure(a,identity,False);require(c.set_static_mesh(meshes[identity]),'Cannot bind own substrate');c.set_cull_distance(24000.)
 for mid in guard.MODELS:
  identity='EX_yard_ground_r32_'+mid;a=actors.spawn_actor_from_class(u.load_class(None,'/Script/BreziTwin.BreziVegetationPatch'),u.Vector(0,0,0),u.Rotator())
  c=configure(a,identity,True);a.tags=[u.Name('BreziGenerated'),u.Name(TAG),u.Name('BreziLawnDetail')]
  require(c.set_static_mesh(u.EditorAssetLibrary.load_asset(bundle['nativeMasters'][mid]['mesh'])),'Cannot bind unchanged low master')
  c.set_cull_distances(18000,24000);require(a.set_detail_density_scaling(True),'Cannot assign own low-detail classification')
  require(list(c.add_instances(values[mid],True,False,False))==list(range(len(values[mid]))),'Exact new-root order differs');a.synchronize_instance_bounds()
 return added


def verify_saved(u,bundle,base,h,targets,added,meshes,materials,measurements,native_vertices,material_report):
 witness=h['cleanNative'].full_witness(u,h);actors={a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
 require({p for p,a in actors.items()if a.actor_has_tag(TAG)}==set(added.values()),'Owned R32 actor scope widened')
 for mid in guard.MODELS:
  c=actors[added['EX_yard_ground_r32_'+mid]].get_component_by_class(u.HierarchicalInstancedStaticMeshComponent);count=len(measurements[mid]['rootIds'])
  require(c and c.get_instance_count()==count,'Exact new group/member census required')
  exact([value(h['rural'].instance_value(c,i))for i in range(count)],measurements[mid]['recoveredValues'],'Actual saved new-root recovered frames differ from faithful transient')
  exact([matrix(c,i)for i in range(count)],measurements[mid]['actualMatrices'],'Actual saved new-root stored matrices differ from faithful transient')
 mesh_assets={k:v.get_path_name()for k,v in meshes.items()};mat_assets={k:v.get_path_name()for k,v in materials.items()}
 expected=guard.expected_original(base['witness'],targets,mesh_assets,mat_assets)
 expected.update(guard.added_expected(base,targets,added,mesh_assets,mat_assets,measurements,bundle))
 require(witness==expected and len(witness)==5360,'Full original5356 only3 declared component changes plus4 additions differs')
 hisms=[c for a in witness.values()for c in a['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
 require(len(hisms)==2321 and sum(c['instanceCount']for c in hisms)==678231,'Full saved native HISM census differs')
 proofs=[native_mesh_proof(u,meshes[r['id']],r,h)for r in bundle['proposal']['meshes']]
 return expected,{'meshProofs':proofs,'footprints':verify_footprints(bundle,measurements,native_vertices),'fullActorCounterfactualValidated':True,
  'counts':guard.COUNTS,'nativeNormalTangentReadbackAvailable':False,'nativeAppearanceAccepted':False,'performanceAccepted':False}


def input_files(plan,bundle):
 rows=dict(plan['inputFiles'])
 for row in [pin(guard.PLAN),bundle['base']['reportPin'],*bundle['base']['process'].values()]:
  if isinstance(row,dict)and'path'in row:rows[row['path']]=row['sha256']
 for p,value0 in rows.items():require(sha(p)==value0,'Consumed source changed')
 return rows


def preflight(output):
 require(not output.exists(),'Fresh native source preflight output required');plan,bundle=guard.validate_plan()
 clone=guard.validate_clone(bundle['source'],bundle['base']);h=helpers(bundle['base']);output.mkdir()
 test_path=ROOT/'scripts/unreal/test_exterior_context_yard_ground_native_r32.py';command=[sys.executable,'-B',str(test_path)]
 result=subprocess.run(command,text=True,capture_output=True,timeout=120);(output/'source-tests.log').write_text(result.stdout+result.stderr)
 require(result.returncode==0,'R32 focused native contract fixtures failed')
 receipt={'schema':guard.SCHEMA,'owner':OWNER,'status':'yard-ground-source-preflight-validated-native-pending','createdAt':now(),
  'selectedPlan':pin(guard.PLAN),'baseNativeReport':bundle['base']['reportPin'],'baseNativeProcess':bundle['base']['process'],
  'projectClone':clone,'inputFiles':input_files(plan,bundle),'moduleOrderWitness':h['moduleOrderWitness'],
  'sourceSummary':bundle['source']['summary'],'testSource':pin(test_path),'testLog':pin(output/'source-tests.log'),'testExitCode':0,
  'nativeExecuted':False,'nativeAppearanceAccepted':False,'performanceAccepted':False,'fullPhotorealismAccepted':False}
 write(output/'source-preflight.json',receipt);print(json.dumps({'preflight':pin(output/'source-preflight.json'),'nativeExecuted':False}))


def validate_preflight(path,plan,bundle):
 pf=read(path);require(pf['schema']==guard.SCHEMA and pf['owner']==OWNER and pf['status']=='yard-ground-source-preflight-validated-native-pending'
  and pf['selectedPlan']==pin(guard.PLAN)and pf['baseNativeReport']==bundle['base']['reportPin']and pf['baseNativeProcess']==bundle['base']['process']
  and pf['projectClone']==pin(guard.CANDIDATE/'context-yard-ground-project-clone.json')and pf['inputFiles']==input_files(plan,bundle)
  and pf['sourceSummary']==bundle['source']['summary']and pf['testExitCode']==0 and pf['nativeExecuted']is False,'Exact R32 native preflight differs')
 check_pin(pf['testLog']);check_pin(pf['testSource']);return pf


def main():
 import unreal as u
 output=guard.CANDIDATE;project=output/'Project/BreziTwin'
 require(Path(os.environ['BREZI_YARD_GROUND_OUTPUT']).resolve()==output and Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project,
  'Only fresh owned R32 project may change')
 require(not(output/REPORT).exists()and not(output/'exterior-import-report.json').exists(),'Fresh own typed overlay report only')
 plan,contract=guard.validate_plan();bundle,base,targets=contract['source'],contract['base'],contract['targets']
 pf_path=Path(os.environ['BREZI_YARD_GROUND_PREFLIGHT']).resolve()
 require(sha(pf_path)==os.environ['BREZI_YARD_GROUND_PREFLIGHT_SHA256']and sha(guard.PLAN)==os.environ['BREZI_YARD_GROUND_PLAN_SHA256'],'Frozen launch source differs')
 pf=validate_preflight(pf_path,plan,contract);h=helpers(base);require(h['moduleOrderWitness']==pf['moduleOrderWitness'],'Frozen policy cache witness differs')
 clone=guard.validate_clone(bundle,base);maps=guard.module('r32_exact_owned_materials','exterior-context-yard-ground-materials-r32.py');maps.preflight_enums(u)
 for p in [project,base['project']]:require(guard.g.inventory(p/'Content')==base['content']and guard.g.project_proof(p)==base['protected'],'Original/fresh project bytes differ')
 checkpoint=output/'yard-ground-checkpoint';require(not checkpoint.exists(),'Fresh checkpoint only');checkpoint.mkdir()
 module=project/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'
 report={'schema':guard.SCHEMA,'owner':OWNER,'status':'running','startedAt':now(),'nativeProcessId':os.getpid(),'output':str(output),'project':str(project),
  'selectedPlan':pin(guard.PLAN),'sourceStudy':pin(guard.source.PLAN),'sourcePreflight':pin(pf_path),'baseNativeReport':base['reportPin'],
  'baseNativeProcess':base['process'],'projectClone':clone,'inputFiles':pf['inputFiles'],'moduleOrderWitness':h['moduleOrderWitness'],
  'baseContentInventory':base['report']['afterContentInventory'],'protectedProjectProof':base['report']['protectedProjectProof'],
  'nativeModuleWitness':{'source':str(base['project']/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),'destination':str(module),'sha256':sha(module),
   'bytes':module.stat().st_size,'independentInodes':module.stat().st_ino!=(base['project']/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib').stat().st_ino},
  'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},'setbacksMm':{'street':3000,'east':3000},
  'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,
  'materialPackagesIndependentlyUnloaded':False,'nativeNormalTangentReadbackAvailable':False,'measuredElevation':False,
  'AdditionalRandomSeedsReadbackAvailable':False,'existingMemberTransformOrSeedSetterUsed':False}
 report_write(output/REPORT,report)
 try:
  levels=u.get_editor_subsystem(u.LevelEditorSubsystem);require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot load own actual R30 clone')
  before=h['cleanNative'].full_witness(u,h);require(before==base['witness'],'Whole5356 original actor witness differs')
  controls_before=all_controls(u,base,h,before);native_vertices=native_master_vertices(u,bundle,h)
  values,measurements=measure_groups(u,bundle,h);footprints=verify_footprints(bundle,measurements,native_vertices)
  require(h['cleanNative'].full_witness(u,h)==before,'Transient root measurement mutated original scene')
  base_materials={key:u.EditorAssetLibrary.load_asset(row['duplicateSource'])for row,key in zip(bundle['recipes'],['context_track','context_garden_soil'])}
  materials,material_report=maps.prepare(u,h,bundle['recipes'],base_materials);meshes,pipelines,removed=import_geometry(u,bundle,materials,h)
  require(h['cleanNative'].full_witness(u,h)==before,'Own asset import mutated original scene')
  added=apply_scene(u,bundle,h,targets,meshes,materials,values)
  expected,proof=verify_saved(u,bundle,base,h,targets,added,meshes,materials,measurements,native_vertices,material_report)
  for name,row in [('before-actors',before),('expected-actors',expected),('source-frame-measurements',measurements),('original-controls-before',controls_before)]:write(checkpoint/(name+'.json'),row)
  require(levels.save_current_level(),'Cannot save own ground/detail overlay')
  require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot unload/reload own saved ground/detail overlay')
  materials_saved=maps.verify_saved(u,h,bundle['recipes'],base_materials,material_report)
  meshes_saved={k:u.EditorAssetLibrary.load_asset(v.get_path_name())for k,v in meshes.items()}
  saved,proof_saved=verify_saved(u,bundle,base,h,targets,added,meshes_saved,materials_saved,measurements,native_vertices,material_report)
  require(saved==expected and proof_saved==proof,'Saved exact full geometry/mask/actor proof differs')
  controls_saved=all_controls(u,base,h,saved);require(controls_saved==controls_before,'Old observed matrix/material/control witnesses changed')
  packages=[v.get_path_name()for v in meshes_saved.values()]+material_report['newPackageAssets']+pipelines
  content=guard.g.inventory(project/'Content');delta=guard.validate_content(base['content'],content,packages)
  require(guard.g.project_proof(project)==base['protected']and guard.g.inventory(base['project']/'Content')==base['content']
   and guard.g.project_proof(base['project'])==base['protected'],'Original base or132 protected bytes changed')
  for p,value0 in pf['inputFiles'].items():require(sha(p)==value0,'Frozen consumed source changed during native')
  for name,row in [('saved-actors',saved),('original-controls-saved',controls_saved),('after-content',content)]:write(checkpoint/(name+'.json'),row)
  report.update(status=STATUS,completedAt=now(),nativeApplied=True,savedMapUnloadedReloaded=True,sourceInputsUnchanged=True,originalSavedR30bUnchanged=True,
   targets=targets,addedActors=added,newMeshes={k:v.get_path_name()for k,v in meshes_saved.items()},newMaterialReport=material_report,
   nativeSourceFrameMeasurements=pin(checkpoint/'source-frame-measurements.json'),savedReadback=proof_saved,
   beforeActorWitness=pin(checkpoint/'before-actors.json'),expectedActorWitness=pin(checkpoint/'expected-actors.json'),savedActorWitness=pin(checkpoint/'saved-actors.json'),
   beforeActorWitnessSha256=digest(before),expectedActorWitnessSha256=digest(expected),savedActorWitnessSha256=digest(saved),
   originalControlsBefore=pin(checkpoint/'original-controls-before.json'),originalControlsSaved=pin(checkpoint/'original-controls-saved.json'),
   afterContentInventory=pin(checkpoint/'after-content.json'),assetDelta=delta,newPackages=packages,importPipelineAssets=pipelines,
   removedOwnImportMetadata=removed,actualCounts=guard.COUNTS,newTextureObjects=0,existingRootsPreserved=True,
   originalBedsAnd13ShrubsPreserved=True,allGroundNativeOrderedF32PositionsUV0UV1WindingVerified=True)
  report_write(output/REPORT,report);print(json.dumps({'report':pin(output/REPORT),'status':STATUS,'nativeAppearanceAccepted':False}))
 except Exception as error:
  report.update(status='failed',completedAt=now(),error=str(error));report_write(output/REPORT,report);raise


if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--preflight',type=Path);args=parser.parse_args()
 if args.preflight:preflight(args.preflight.resolve())
 else:main()
