"""Root-only additive yard overlay on actual saved clean R27.

Four generated ground meshes, two existing-PBR feather material copies and
three existing-master HISM groups/13 new roots. No old actor setter is used.
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
OWNER='scripts/unreal/exterior-context-yard-native-r28-r2.py'
spec=importlib.util.spec_from_file_location('yard_r28_native_scope',ROOT/'scripts/unreal/exterior-context-yard-native-guards-r28-r2.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
require,read,sha,pin,check_pin,digest=(getattr(guard,k)for k in('require','read','sha','pin','check_pin','digest'))
PREFIX,TAG=guard.PREFIX,guard.TAG
STATUS='verified-saved-purposeful-context-yards-overlay'
REPORT='context-yard-native-report-r2.json'
MAP='/Game/Brezi/Maps/Brezi'


def now():return datetime.now(timezone.utc).isoformat()
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def vec(value,axes='xyz'):return [float(getattr(value,k))for k in axes]
def value(transform):return [vec(transform.translation),vec(transform.rotation,'xyzw'),vec(transform.scale3d)]
def matrix(component,index):
 m=component.get_editor_property('per_instance_sm_data')[index].get_editor_property('transform')
 return [vec(getattr(m,plane),'xyzw')for plane in('x_plane','y_plane','z_plane','w_plane')]
def binary64(value):
 if isinstance(value,(list,tuple)):return b''.join(binary64(v)for v in value)
 require(type(value)in(float,int),'Numeric binary64 frame field required');return struct.pack('<d',value)
def exact(a,b,message):require(binary64(a)==binary64(b),message)
def root_record(row):
 return {'positionCm':row['positionCm'],'yawDeg':row['yawDegrees'],'scale':[row['uniformScale']]*3}


def decode_glb(path,meshes):
 payload=Path(path).read_bytes();require(struct.unpack_from('<III',payload)==(0x46546c67,2,len(payload)),'Generated GLB header/length differs')
 size,kind=struct.unpack_from('<II',payload,12);require(kind==0x4e4f534a,'Generated GLB JSON missing');doc=json.loads(payload[20:20+size])
 offset=20+size;size,kind=struct.unpack_from('<II',payload,offset);require(kind==0x004e4942 and offset+8+size==len(payload),'Generated GLB BIN length differs');blob=payload[offset+8:]
 def values(index):
  a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3}[a['type']]
  require(a['componentType']in(5125,5126),'Generated GLB accessor type differs')
  xs=struct.unpack_from('<'+('f'if a['componentType']==5126 else'I')*(width*a['count']),blob,v['byteOffset'])
  return [list(xs[i:i+width])for i in range(0,len(xs),width)]
 require(len(doc['nodes'])==len(doc['meshes'])==4 and 'materials'not in doc,'Closed four generated meshes required')
 result=[]
 for mesh,entry in zip(meshes,doc['meshes']):
  primitive=entry['primitives'][0];attrs=primitive['attributes']
  require(len(entry['primitives'])==1 and primitive['mode']==4 and entry['name']==mesh['id']+'_LOD0'
   and set(attrs)=={'POSITION','NORMAL','TEXCOORD_0','TEXCOORD_1'},'Closed generated mesh/node/attribute route differs')
  require(values(attrs['POSITION'])==[[guard.f32(x/100),guard.f32(z/100),guard.f32(y/100)]for x,y,z in mesh['verticesCm']]
   and values(attrs['NORMAL'])==[[guard.f32(x),guard.f32(z),guard.f32(y)]for x,y,z in mesh['normals']], 'Generated R21-basis F32 positions/normals differ')
  require([r[0]for r in values(primitive['indices'])]==mesh['indices'],'Generated ordered source indices changed')
  for channel,key in((0,'uv0'),(1,'uv1')):require(values(attrs['TEXCOORD_'+str(channel)])==[[guard.f32(v)for v in row]for row in mesh[key]],'Generated F32 UV channel changed')
  result.append({'id':mesh['id'],'triangles':len(mesh['indices'])//3,'sourceCornerSha256':digest(guard.corners(mesh)),
   'generatedR21AxisRouteCmToMetres':True,'nativeNormalTangentReadbackAvailable':False})
 return result


def source_closure(bundle,base):
 test_file=ROOT/'scripts/unreal/test_exterior_context_yard_native_r28_r2.py'
 repair=guard.api_repair()
 rows={str(guard.SOURCE):sha(guard.SOURCE),str(ROOT/OWNER):sha(ROOT/OWNER),str(ROOT/guard.OWNER):sha(ROOT/guard.OWNER),str(test_file):sha(test_file)}
 def collect(v):
  if isinstance(v,dict):
   if{'path','sha256','bytes'}<=set(v):
    row={k:v[k]for k in('path','sha256','bytes')};check_pin(row);rows[row['path']]=row['sha256'];return
   for child in v.values():collect(child)
  elif isinstance(v,list):
   for child in v:collect(child)
 collect(bundle['plan']);collect(bundle['layoutPlan']);collect(bundle['recipes']);collect(base['report']);collect(base['cleanPlan']);collect(base['process']);collect(repair);rows[str(ROOT/'scripts/unreal/exterior-context-yard-api-repair-r28-r2.py')]=sha(ROOT/'scripts/unreal/exterior-context-yard-api-repair-r28-r2.py');rows[str(ROOT/'output/unreal/exterior-context-yard-20261002-r28-native-api-repair-r2/api-repair-supplement.json')]=sha(ROOT/'output/unreal/exterior-context-yard-20261002-r28-native-api-repair-r2/api-repair-supplement.json')
 terminal=read(base['process']['receipt']['path']);rows.update(terminal['sourcePinsBeforeNative']);rows[terminal['controller']]=sha(terminal['controller'])
 for name in('exterior-canopy-foreground-native-r2.py','exterior-grove-substrate-native.py','exterior-canopy-native.py'):
  path=ROOT/'scripts/unreal'/name;rows[str(path)]=sha(path)
 for file,h in rows.items():require(sha(file)==h,'Actual consumed source changed: '+file)
 return rows


def validate_clone(base):
 output=guard.CANDIDATE;project=output/'Project/BreziTwin';path=output/'context-yard-project-clone.json';clone=read(path);origin=guard.BASE/'Project/BreziTwin'
 require(clone['status']=='verified-byte-identical-independent-apfs-r28b-project-clone-before-context-yard-native-r2'
  and clone['baseNativeReport']==base['reportPin']and clone['selectedSourceGeometry']==pin(guard.SOURCE)
  and clone['nativeApiRepairPending']is True and clone['selectedNativeApiRepair']is None
  and clone['nativeExecuted']is False and clone['fileCount']==len(clone['files'])==4166,'Typed own actual clean R27 clone required')
 expected={'Content/'+k:v for k,v in base['content'].items()};expected.update(base['protected']);seen={}
 for row in clone['files']:
  a,b=Path(row['source']),Path(row['destination']);require(a.is_relative_to(origin)and b.is_relative_to(project)
   and a.relative_to(origin)==b.relative_to(project)and row['independentInodes']is True,'Clone identity/independence differs')
  relative=str(b.relative_to(project));require(relative not in seen and relative in expected,'Unknown/duplicate clone file')
  require({k:row[k]for k in('sha256','bytes')}==expected[relative]and a.stat().st_size==b.stat().st_size==row['bytes']
   and sha(a)==sha(b)==row['sha256']and(a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino),'Clone bytes/inodes differ')
  seen[relative]=row
 require(set(seen)==set(expected),'Exact all4166 cloned file set required')
 require(guard.g.inventory(project/'Content')==base['content']and guard.g.project_proof(project)==base['protected'],'Fresh own candidate inventory differs')
 return pin(path)


def preflight(output):
 require(not output.exists()and output.is_relative_to(ROOT/'output/unreal'),'Fresh own CPU preflight output required')
 bundle=guard.load_source();base=guard.saved_base();clone=validate_clone(base)
 require(guard.g.inventory(guard.BASE/'Project/BreziTwin/Content')==base['content']and guard.g.project_proof(guard.BASE/'Project/BreziTwin')==base['protected'],'Actual saved clean base bytes changed')
 r21=guard.module('yard_r28_primary_R21_api','exterior-canopy-foreground-native-r2.py');api=r21.primary_actor_api();closure=source_closure(bundle,base);closure[api['path']]=api['sha256']
 closure[clone['path']]=clone['sha256'];output.mkdir(parents=True)
 test_file=ROOT/'scripts/unreal/test_exterior_context_yard_native_r28_r2.py';command=[sys.executable,'-B',str(test_file)]
 tests=subprocess.run(command,text=True,capture_output=True,timeout=120)
 write(output/'native-source-tests.json',{'status':'passed'if tests.returncode==0 else'failed','testCount':11,'exitCode':tests.returncode,
  'command':command,'testSource':pin(test_file),'nativeExecuted':False})
 (output/'native-source-tests.log').write_text(tests.stdout+tests.stderr);require(tests.returncode==0,'Yard native-source fixtures failed')
 receipt={'schema':guard.SCHEMA,'owner':OWNER,'status':'context-yard-source-preflight-validated-native-pending','createdAt':now(),
  'nativeApiRepairSupplement':pin(ROOT/'output/unreal/exterior-context-yard-20261002-r28-native-api-repair-r2/api-repair-supplement.json'),
  'sourceGeometryPlan':pin(guard.SOURCE),'sourceGLB':bundle['plan']['glb'],'decodedGLB':decode_glb(check_pin(bundle['plan']['glb']),bundle['geometry']['meshes']),
  'baseNativeReport':base['reportPin'],'baseActualProcess':base['process'],'candidateProjectClone':clone,'primaryActorApi':api,
  'baseContentInventory':base['report']['afterContentInventory'],'baseProjectProof':base['report']['protectedProjectProof'],
  'inputFiles':closure,'sourceGuardTests':pin(output/'native-source-tests.json'),'sourceGuardTestsLog':pin(output/'native-source-tests.log'),
  'sourceMaskValidation':pin(ROOT/'output/unreal/exterior-context-yard-20261002-r28-source-mask-validation/source-mask-validation.json'),
  'audit':bundle['plan']['audit'],'nativeExecuted':False,'nativeApplied':False,
  'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingAccepted':False}
 write(output/'source-preflight.json',receipt);print(json.dumps({'preflight':pin(output/'source-preflight.json'),'audit':receipt['audit']}))


def validate_preflight(path,bundle,base):
 row=read(path);require(row['schema']==guard.SCHEMA and row['owner']==OWNER and row['status']=='context-yard-source-preflight-validated-native-pending'
  and row['sourceGeometryPlan']==pin(guard.SOURCE)and row['baseNativeReport']==base['reportPin']and row['baseActualProcess']==base['process']
  and row['candidateProjectClone']==pin(guard.CANDIDATE/'context-yard-project-clone.json')and row['audit']==bundle['plan']['audit']
  and row['nativeExecuted']is False,'Typed actual clean-base yard preflight differs')
 require(row['nativeApiRepairSupplement']==pin(ROOT/'output/unreal/exterior-context-yard-20261002-r28-native-api-repair-r2/api-repair-supplement.json'),'Exact measured R2 API supplement differs');guard.api_repair()
 require(row['decodedGLB']==decode_glb(check_pin(row['sourceGLB']),bundle['geometry']['meshes']),'Generated sourceGLB full route changed')
 expected=source_closure(bundle,base);expected[row['primaryActorApi']['path']]=row['primaryActorApi']['sha256'];expected[row['candidateProjectClone']['path']]=row['candidateProjectClone']['sha256']
 require(expected==row['inputFiles'],'Exact native source closure differs')
 tests=read(check_pin(row['sourceGuardTests']));masks=read(check_pin(row['sourceMaskValidation']));check_pin(row['sourceGuardTestsLog'])
 require(tests['status']==masks['status']=='passed'and tests['testCount']==11 and masks['testCount']==7
  and tests['exitCode']==masks['exitCode']==0 and tests['nativeExecuted']is masks['nativeExecuted']is False,'Focused18 source/native-contract fixtures required')
 for file,h in row['inputFiles'].items():require(sha(file)==h,'Frozen consumed source changed')
 return row


def create_material(u,recipe,existing,r21):
 assets=u.EditorAssetLibrary;lib=u.MaterialEditingLibrary;source=assets.load_asset(recipe['sourceNativeMaterial']);target=recipe['newMaterial']
 require(source and not assets.does_asset_exist(target),'Fresh existing-PBR material copy required')
 original=existing.graph_snapshot(u,source);require(original==recipe['originalGraph']and digest(original)==recipe['sourceGraphSha256'],'Original soil/world-PBR graph changed')
 offsets=r21.world_position_offsets(u,source);material=assets.duplicate_asset(recipe['sourceNativeMaterial'],target)
 require(material and existing.graph_snapshot(u,material)==original and r21.world_position_offsets(u,material)==offsets,'Initial graph copy/world-position mode changed')
 def node(role,cls):
  v=lib.create_material_expression(material,cls,-700,800);require(v,'Cannot add own feather node');v.set_editor_property('desc',guard.NODE_TAG+role);return v
 uv=node('uv1',u.MaterialExpressionTextureCoordinate);uv.set_editor_property('coordinate_index',1)
 coverage=node('coverage-r',u.MaterialExpressionComponentMask)
 for key,v in{'r':True,'g':False,'b':False,'a':False}.items():coverage.set_editor_property(key,v)
 dither=node('temporal-dither',u.MaterialExpressionMaterialFunctionCall);function=assets.load_asset(recipe['nativeDitherFunction'])
 require(function and dither.set_material_function(function),'Installed native DitherTemporalAA unavailable')
 alpha=[str(v)for v in lib.get_material_expression_input_names(dither)if'alpha'in str(v).lower()]
 require(len(alpha)==1 and[str(v)for v in lib.get_material_expression_input_names(coverage)]==['None'],'Exact native dither/mask pin schema differs')
 require(lib.connect_material_expressions(uv,'',coverage,'')and lib.connect_material_expressions(coverage,'',dither,alpha[0])
  and lib.connect_material_property(dither,'Result',u.MaterialProperty.MP_OPACITY_MASK),'Cannot connect fresh UV1 feather root')
 material.set_editor_property('blend_mode',u.BlendMode.BLEND_MASKED);material.set_editor_property('opacity_mask_clip_value',.5)
 errors=list(lib.recompile_material(material));require(not errors,'Fresh yard material shader compilation failed')
 graph=existing.graph_snapshot(u,material);guard.validate_graph_copy(original,graph)
 require(r21.world_position_offsets(u,material)==offsets,'Original absolute world-position mode changed')
 assets.set_metadata_tag(material,'BreziGeneratedBy',OWNER);require(assets.save_loaded_asset(material,False),'Cannot save own material copy')
 return material,{'asset':material.get_path_name(),'recipe':recipe,'graph':graph,'graphSha256':digest(graph),'worldPositionOffsets':offsets,'compileErrors':errors,'newTextureObjects':0}


def native_mesh_proof(u,mesh,source):
 subsystem=guard.static_mesh_api().static_mesh_subsystem(u);description=mesh.get_static_mesh_description(0);expected=guard.corners(source)
 require(mesh.get_num_lods()==1 and description and description.get_triangle_count()==mesh.get_num_triangles(0)==len(expected)
  and mesh.get_num_sections(0)==1 and not mesh.get_editor_property('has_navigation_data')and not mesh.get_editor_property('nanite_settings').get_editor_property('enabled'),'Ground LOD/count/section/nav/Nanite differs')
 settings=subsystem.get_lod_build_settings(mesh,0)
 require(all(settings.get_editor_property(k)==v for k,v in{'use_full_precision_u_vs':True,'generate_lightmap_u_vs':False,'recompute_normals':False,'recompute_tangents':True,'remove_degenerates':False}.items()),'Generated UV/normal/tangent build policy differs')
 actual=[]
 for j in range(len(expected)):
  face=[]
  for c in range(3):
   vi=description.get_triangle_vertex_instance(u.TriangleID(id_value=j),c);point=vec(description.get_vertex_position(description.get_vertex_instance_vertex(vi)))
   face.append(tuple(point+vec(description.get_vertex_instance_uv(vi,0),'xy')+vec(description.get_vertex_instance_uv(vi,1),'xy')))
  actual.append(guard.cyclic(face))
 require(actual==expected,'All generated R21-route native F32 positions/UV0/UV1/ordered topology/winding differ')
 return {'mesh':mesh.get_path_name(),'triangles':len(actual),'nativeOrderedF32PositionUv0Uv1CornerSha256':digest(actual),
  'fullOrderedNativeGeometryVerified':True,'nativeNormalTangentReadbackAvailable':False}


def import_geometry(u,bundle,materials,compilation):
 assets=u.EditorAssetLibrary;actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem);pipelines=[]
 for original,name in(('GLTFSceneAssets','Assets'),('GLTFMaterials','Materials'),('LevelActors','Level')):
  path=PREFIX+'/Pipeline/'+name;require(not assets.does_asset_exist(path),'Fresh own import pipelines required');v=assets.duplicate_asset('/Game/Brezi/Pipeline/'+original,path);require(v,'Cannot copy importer pipeline');pipelines.append(v)
 mp=pipelines[0].get_editor_property('mesh_pipeline')
 for key,v in{'combine_static_meshes_behavior':u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,'collision':False,'build_nanite':False,'generate_lightmap_u_vs':False}.items():mp.set_editor_property(key,v)
 common=pipelines[0].get_editor_property('common_meshes_properties')
 for key,v in{'remove_degenerates':False,'recompute_normals':False,'recompute_tangents':True,'use_full_precision_u_vs':True}.items():common.set_editor_property(key,v)
 material_pipeline=pipelines[0].get_editor_property('material_pipeline');material_pipeline.set_editor_property('import_materials',False);material_pipeline.get_editor_property('texture_pipeline').set_editor_property('import_textures',False)
 pipelines[2].set_editor_property('scene_hierarchy_type',u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
 params=u.ImportAssetParameters()
 for key,v in{'is_automated':True,'replace_existing':False,'force_show_dialog':False,'override_pipelines':[u.SoftObjectPath(v.get_path_name())for v in pipelines],'import_level':levels.get_current_level()}.items():params.set_editor_property(key,v)
 before={a.get_path_name()for a in actors.get_all_level_actors()};manager=u.InterchangeManager.get_interchange_manager_scripted()
 require(manager.import_scene(PREFIX+'/Geometry',manager.create_source_data(str(check_pin(bundle['plan']['glb']))),params),'Generated yard GLB import failed')
 temporary=[a for a in actors.get_all_level_actors()if a.get_path_name()not in before];meshes={};records={m['id']:m for m in bundle['geometry']['meshes']}
 for actor in temporary:
  for c in actor.get_components_by_class(u.StaticMeshComponent):
   mesh=c.get_editor_property('static_mesh');require(mesh and mesh.get_path_name().startswith(PREFIX+'/Geometry/'),'Unexpected own imported object')
   matches=[key for key in records if key+'_LOD0'==mesh.get_name()];require(len(matches)==1,'Ambiguous imported ground mesh');meshes[matches[0]]=mesh
 require(set(meshes)==set(records),'Exactly four generated surface meshes required')
 subsystem=compilation.static_mesh_subsystem(u)
 for key,mesh in meshes.items():
  row=records[key];material=materials.get(row['role'])or assets.load_asset(bundle['layout']['existingMaterialReferences'][row['materialKey']]['asset']);require(material,'Original gravel/new soil material missing');mesh.set_material(0,material);mesh.set_editor_property('has_navigation_data',False)
  settings=subsystem.get_lod_build_settings(mesh,0)
  for k,v in{'use_full_precision_u_vs':True,'generate_lightmap_u_vs':False,'recompute_normals':False,'recompute_tangents':True,'remove_degenerates':False}.items():settings.set_editor_property(k,v)
  subsystem.set_lod_build_settings(mesh,0,settings);assets.set_metadata_tag(mesh,'BreziGeneratedBy',OWNER);require(assets.save_loaded_asset(mesh,False),'Cannot save own ground mesh')
 compilation.finish_static_mesh_compilation(u,synchronous=True)
 for key,mesh in meshes.items():native_mesh_proof(u,mesh,records[key])
 for actor in reversed(temporary):require(actors.destroy_actor(actor),'Cannot destroy own temporary importer actor')
 for pipeline in pipelines:require(assets.save_loaded_asset(pipeline,False),'Cannot save own pipeline')
 known={m.get_path_name().split('.')[0]for m in meshes.values()};removed=[]
 for path in assets.list_assets(PREFIX+'/Geometry',recursive=True,include_folder=False):
  if path.split('.')[0]in known:continue
  obj=assets.load_asset(path);require(obj and obj.get_class().get_name()in('InterchangeAssetImportData','InterchangeSceneImportAsset'),'Unknown import package must not be deleted')
  require(assets.delete_asset(path),'Cannot remove own scene-only importer metadata');removed.append(path)
 return meshes,[v.get_path_name()for v in pipelines],removed


def measure_groups(u,bundle,rural):
 result={}
 for mid in guard.MODELS:
  rows=[r for r in bundle['layout']['planting']if r['modelId']==mid];component=u.new_object(u.HierarchicalInstancedStaticMeshComponent)
  transforms=[rural.instance_transform(u,root_record(r))for r in rows];pre=[value(v)for v in transforms]
  exact([v[0]for v in pre],[r['positionCm']for r in rows],'Authored source root XYZ changed before transient measurement')
  indices=list(component.add_instances(transforms,True,False,False));require(indices==list(range(len(rows))),'Transient source frame order differs')
  result[mid]={'sourceRootIds':[r['id']for r in rows],'preInsertionValues':pre,
   'recoveredValues':[value(rural.instance_value(component,i))for i in indices],'actualMatrices':[matrix(component,i)for i in indices],
   'nativeUnregisteredTransientMeasurement':True,'oldActorOrMemberMutated':False}
 return result


def source_expected_added(base,added,meshes,materials,measurements,bundle):
 floor_path=base['report']['newForegroundActors']['canopy_foreground_r21_surface'];group_path=next(v for k,v in base['report']['newForegroundActors'].items()if k!='canopy_foreground_r21_surface')
 result={}
 for identity,path in added.items():
  ground=identity in meshes;template=base['witness'][floor_path if ground else group_path];old_path=floor_path if ground else group_path
  row=guard.clean.relocate_template(copy.deepcopy(template),old_path,path);row['label']=identity;row['tags']=sorted(['BreziGenerated',TAG]+([]if ground else['BreziLawnDetail']))
  c=row['components'][0]
  if ground:
   mesh=meshes[identity];c['mesh']=mesh.get_path_name();c['materials']=[mesh.get_material(0).get_path_name()];c['maxDrawDistanceCm']=24000.
   c['drawPolicy']['ld_max_draw_distance']=c['drawPolicy']['cached_max_draw_distance']=24000.
  else:
   mid=identity.removeprefix('EX_context_yard_r28_');source=bundle['nativeMasters'][mid];c['mesh']=source['mesh'];c['materials']=source['materials'];c['instanceCount']=len(measurements[mid]['sourceRootIds'])
   c['orderedInstanceTransformsSha256']=digest(measurements[mid]['recoveredValues']);c['instanceCullCm']=[18000,24000]
   c['renderFlags']['cast_shadow']=c['neighborRenderPolicy']['cast_shadow']=True
  result[path]=row
 return result


def apply_scene(u,bundle,meshes,measurements,rural):
 actors=u.get_editor_subsystem(u.EditorActorSubsystem);added={}
 def configure(actor,identity,shadow):
  require(actor,'Cannot create own yard actor');actor.tags=[u.Name('BreziGenerated'),u.Name(TAG)];actor.set_actor_label(identity);actor.set_folder_path('Brezi/ContextYard20261002R28');actor.set_actor_tick_enabled(False)
  c=actor.get_component_by_class(u.StaticMeshComponent);require(c,'Own yard root component missing');rural.new_component_policy(u,c);c.set_editor_property('cast_shadow',shadow);c.set_editor_property('visible_in_ray_tracing',True);added[identity]=actor.get_path_name();return c
 for identity,mesh in meshes.items():
  actor=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0),u.Rotator());c=configure(actor,identity,False);c.set_static_mesh(mesh);c.set_cull_distance(24000.)
 for mid in guard.MODELS:
  identity='EX_context_yard_r28_'+mid;actor=actors.spawn_actor_from_class(u.load_class(None,'/Script/BreziTwin.BreziVegetationPatch'),u.Vector(0,0,0),u.Rotator());c=configure(actor,identity,True)
  actor.tags=[u.Name('BreziGenerated'),u.Name(TAG),u.Name('BreziLawnDetail')];c.set_static_mesh(u.EditorAssetLibrary.load_asset(bundle['nativeMasters'][mid]['mesh']));c.set_cull_distances(18000,24000)
  require(actor.set_detail_density_scaling(True),'Cannot enable own source quality-classification density');rows=[r for r in bundle['layout']['planting']if r['modelId']==mid]
  indices=list(c.add_instances([rural.instance_transform(u,root_record(r))for r in rows],True,False,False));require(indices==list(range(len(rows))),'Own13 root insertion ordering differs');actor.synchronize_instance_bounds()
  exact([value(rural.instance_value(c,i))for i in indices],measurements[mid]['recoveredValues'],'Actual HISM recovered frames differ from faithful transient source measurement')
  exact([matrix(c,i)for i in indices],measurements[mid]['actualMatrices'],'Actual HISM matrices differ from faithful transient source measurement')
 return added


def native_master_vertices(u,bundle):
 result={};subsystem=guard.static_mesh_api().static_mesh_subsystem(u)
 for mid in guard.MODELS:
  source=bundle['nativeMasters'][mid];mesh=u.EditorAssetLibrary.load_asset(source['mesh']);require(mesh and mesh.get_num_lods()==3
   and list(subsystem.get_lod_screen_sizes(mesh))==source['lodScreens']and [mesh.get_num_triangles(i)for i in range(3)]==source['lodTriangles'],'Actual existing shrub three-LOD binding differs')
  points=[];counts=[]
  for lod in range(3):
   desc=mesh.get_static_mesh_description(lod);require(desc and desc.get_triangle_count()==source['lodTriangles'][lod],'Existing shrub full native source description unavailable')
   unique={}
   for j in range(desc.get_triangle_count()):
    for corner in range(3):
     vi=desc.get_triangle_vertex_instance(u.TriangleID(id_value=j),corner);vertex=desc.get_vertex_instance_vertex(vi);identity=int(vertex.id_value)
     if identity not in unique:unique[identity]=vec(desc.get_vertex_position(vertex))
   points.extend(unique.values());counts.append(len(unique))
  result[mid]={'points':points,'uniqueNativeVerticesPerLod':counts,'sourceMesh':source['mesh'],'allThreeNativeLodsDecoded':True}
 return result


def verify_footprints(bundle,measurements,native_vertices):
 rows=[]
 for mid,measured in measurements.items():
  roots=[r for r in bundle['layout']['planting']if r['modelId']==mid]
  for source,value0,stored in zip(roots,measured['recoveredValues'],measured['actualMatrices']):
   exact(value0[0],source['positionCm'],'Actual new root XYZ differs from authored ground placement');domain=bundle['soil'][source['buildingSourceId']];radius=0.;height=0.
   for point in native_vertices[mid]['points']:
    local=[sum(point[j]*stored[j][k]for j in range(3))for k in range(3)];world=[stored[3][k]+local[k]for k in range(3)]
    require(domain.contains(world[:2])and all(not mask.contains(world[:2])for mask in bundle['masks'].values()),'Actual all-LOD shrub vertex escapes its source bed/exclusions')
    radius=max(radius,math.hypot(*local[:2]));height=max(height,local[2])
   require(radius<source['radialEnvelopeCm']and domain.distance(value0[0][:2],radius+1)>radius
    and all(mask.distance(value0[0][:2],radius+21)>radius+20 for mask in bundle['masks'].values()),'Actual full containing crown circle crosses source bed or masks')
   rows.append({'rootId':source['id'],'modelId':mid,'actualRootXYZ':value0[0],'actualNativeAllLodRadiusCm':radius,'actualNativeAbovePivotHeightCm':height,
    'sourceConservativeAllLodRadiusCm':source['radialEnvelopeCm'],'allNativeLodVerticesAndContainingCrownInsideSourceBedAndExclusions':True})
 require(len(rows)==13,'Actual13 all-LOD footprints required');return rows


def verify_saved(u,bundle,base,h,added,meshes,materials,measurements,native_vertices):
 witness=base['native'].full_witness(u,h);actors={a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
 require({p for p,a in actors.items()if a.actor_has_tag(TAG)}==set(added.values()),'Own yard actor namespace widened')
 for mid in guard.MODELS:
  c=actors[added['EX_context_yard_r28_'+mid]].get_component_by_class(u.HierarchicalInstancedStaticMeshComponent);indices=range(len(measurements[mid]['sourceRootIds']))
  exact([value(h['rural'].instance_value(c,i))for i in indices],measurements[mid]['recoveredValues'],'Saved native recovered source frames changed')
  exact([matrix(c,i)for i in indices],measurements[mid]['actualMatrices'],'Saved native raw source matrices changed')
 mesh_proofs=[native_mesh_proof(u,meshes[row['id']],row)for row in bundle['geometry']['meshes']]
 for recipe in bundle['recipes']:
  material=materials[recipe['id'].removeprefix('context_yard_r28_')];guard.validate_graph_copy(recipe['originalGraph'],h['existing'].graph_snapshot(u,material))
 expected=copy.deepcopy(base['witness']);expected.update(source_expected_added(base,added,meshes,materials,measurements,bundle))
 require(witness==expected and len(expected)==5350,'Full original5343 plus exact7 source-template actor counterfactual differs')
 hisms=[c for r in witness.values()for c in r['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
 require(len(hisms)==2312 and sum(c['instanceCount']for c in hisms)==676957,'Whole saved HISM census differs')
 return expected,{'meshes':mesh_proofs,'footprints':verify_footprints(bundle,measurements,native_vertices),'fullActorCounterfactualValidated':True,
  'savedActors':5350,'fullHismComponents':2312,'fullHismInstances':676957,'newRoots':13,'newGroups':3,'newGroundActors':4,
  'nativeNormalTangentReadbackAvailable':False,'nativeAppearanceAccepted':False,'performanceAccepted':False}


def main():
 import unreal as u
 output=guard.CANDIDATE;project=output/'Project/BreziTwin';require(Path(os.environ['BREZI_CONTEXT_YARD_OUTPUT']).resolve()==output
  and Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project,'Only own fresh R28a may change')
 require(not(output/REPORT).exists()and not(output/'exterior-import-report.json').exists(),'Fresh typed own overlay only')
 bundle=guard.load_source();base=guard.saved_base();preflight_path=Path(os.environ['BREZI_CONTEXT_YARD_PREFLIGHT']).resolve();preflight0=validate_preflight(preflight_path,bundle,base);clone=validate_clone(base)
 h=base['native'].helpers(base['cleanBundle']);r21=h['foreground'];compilation=guard.module('yard_r28_frozen_mesh_compilation','lawn-geometry.py')
 report={'schema':guard.SCHEMA,'owner':OWNER,'status':'running','startedAt':now(),'nativeProcessId':os.getpid(),'output':str(output),'project':str(project),
  'sourceGeometryPlan':pin(guard.SOURCE),'sourcePreflight':pin(preflight_path),'baseNativeReport':base['reportPin'],'baseActualProcess':base['process'],'projectClone':clone,
  'inputFiles':preflight0['inputFiles'],'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},'setbacksMm':{'street':3000,'east':3000},
  'baseContentInventory':base['report']['afterContentInventory'],'protectedProjectProof':base['report']['protectedProjectProof'],
  'nativeModuleWitness':{'source':str(guard.BASE/'Project/BreziTwin/Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),'destination':str(project/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),
   'sha256':base['report']['nativeModuleWitness']['sha256'],'bytes':2818384,'independentInodes':True},
  'nativeApiRepairSupplement':preflight0['nativeApiRepairSupplement'],
  'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,
  'materialPackagesIndependentlyUnloaded':False,'nativeNormalTangentReadbackAvailable':False,'landUseOrDoorObserved':False,'measuredElevation':False}
 write(output/REPORT,report)
 try:
  actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
  require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot load own saved clean map')
  before=base['native'].full_witness(u,h);require(before==base['witness'],'Actual original full5343 actor scene differs')
  materials_before=base['native'].verify_materials(u,base['cleanBundle'],h);require(materials_before==base['materials'],'Actual original54/77 materials differ')
  grass_before=base['native'].original_grass_controls(u,base['cleanBundle']);require(grass_before==read(check_pin(base['report']['originalGrassControlsSaved'])),'Original8949 grass controls changed')
  native_vertices=native_master_vertices(u,bundle);measurements=measure_groups(u,bundle,h['rural']);verify_footprints(bundle,measurements,native_vertices)
  write(output/'yard-witness-before.json',before);write(output/'yard-native-source-frame-measurements.json',measurements)
  materials={};material_reports=[]
  for recipe in bundle['recipes']:
   material,record=create_material(u,recipe,h['existing'],r21);materials[recipe['id'].removeprefix('context_yard_r28_')]=material;material_reports.append(record)
  meshes,pipelines,removed=import_geometry(u,bundle,materials,compilation);added=apply_scene(u,bundle,meshes,measurements,h['rural'])
  expected,proof=verify_saved(u,bundle,base,h,added,meshes,materials,measurements,native_vertices);write(output/'yard-witness-expected.json',expected)
  require(levels.save_current_level(),'Cannot save own purposeful yard scene')
  require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot unload/reload own saved yard map')
  saved,proof_saved=verify_saved(u,bundle,base,h,added,meshes,materials,measurements,native_vertices);require(proof_saved==proof,'Saved own source geometry/footprints changed')
  require(base['native'].verify_materials(u,base['cleanBundle'],h)==materials_before and base['native'].original_grass_controls(u,base['cleanBundle'])==grass_before,'Original scoped materials/grass data changed')
  content=guard.g.inventory(project/'Content');packages=[v.get_path_name()for v in meshes.values()]+[v.get_path_name()for v in materials.values()]+pipelines
  packages=[p.split('.')[0].removeprefix('/Game/')+'.uasset'for p in packages];delta=guard.validate_content(base['content'],content,packages)
  require(guard.g.project_proof(project)==base['protected']and guard.g.inventory(guard.BASE/'Project/BreziTwin/Content')==base['content']
   and guard.g.project_proof(guard.BASE/'Project/BreziTwin')==base['protected'],'Original base/protected bytes changed')
  for file,h0 in preflight0['inputFiles'].items():require(sha(file)==h0,'Consumed source changed during native overlay')
  write(output/'yard-witness-saved.json',saved);write(output/'yard-content-after.json',content)
  report.update(status=STATUS,completedAt=now(),nativeApplied=True,savedMapUnloadedReloaded=True,originalSavedR27Unchanged=True,sourceInputsUnchanged=True,
   beforeActorWitness=pin(output/'yard-witness-before.json'),expectedActorWitness=pin(output/'yard-witness-expected.json'),savedActorWitness=pin(output/'yard-witness-saved.json'),
   beforeActorWitnessSha256=digest(before),expectedActorWitnessSha256=digest(expected),savedActorWitnessSha256=digest(saved),
   commandletSubsystemAccessor=guard.api_repair()['accessor'],staticMeshEditorSubsystemVerifiedAvailable=True,assetEditorSubsystemVerifiedAvailable=True,
   nativeSourceFrameMeasurements=pin(output/'yard-native-source-frame-measurements.json'),newMaterials=material_reports,newMeshes={k:v.get_path_name()for k,v in meshes.items()},
   addedActors=added,savedReadback=proof_saved,afterContentInventory=pin(output/'yard-content-after.json'),newContentPackages=packages,assetDelta=delta,
   importPipelineAssets=pipelines,removedOwnImportMetadata=removed,scopedMaterialGraphs=56,scopedTextureObjects=77,newTextureObjects=0,
   originalActorCount=5343,savedActorCount=5350,newGroundActors=4,newHismGroups=3,newShrubRoots=13,newPackageCount=9,
   originalGrassMembersPreserved=8949,allOriginalActorPoliciesAndTransformsPreserved=True,originalPlantAssetsBytePreserved=True)
  write(output/REPORT,report);print(json.dumps({'report':pin(output/REPORT),'status':STATUS,'savedActors':5350,'newRoots':13,'surfaceTriangles':2969}))
 except Exception as error:
  report.update(status='failed',completedAt=now(),error=str(error));write(output/REPORT,report);raise


if __name__=='__main__':
 if '--preflight'in sys.argv:
  parser=argparse.ArgumentParser();parser.add_argument('--preflight',type=Path,required=True);args=parser.parse_args();preflight(args.preflight.resolve())
 else:main()
