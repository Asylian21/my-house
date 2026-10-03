"""Root-only scoped authored R43 boundaries; all selected R39c state preserved."""
import argparse, copy, hashlib, importlib.util, io, json, os, struct, sys, unittest
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2];OWNER='scripts/unreal/exterior-context-parcel-boundary-native-r43.py'
def module(n,p):
 s=importlib.util.spec_from_file_location(n,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=module('_r43_bound_guard',ROOT/'scripts/unreal/exterior-context-parcel-boundary-guards-r43.py')
require,read,write,pin,sha,digest,exact=(getattr(g,k)for k in ('require','read','write','pin','sha','digest','exact'))
REPORT='boundary-native-report.json';STATUS='verified-saved-three-authored-open-boundary-masters';MAP='/Game/Brezi/Maps/Brezi'
MATERIAL=ROOT/'scripts/unreal/exterior-context-parcel-boundary-materials-r43.py';TEST_COUNT=13
R39=module('_r43_immutable_props_math_readers',ROOT/'scripts/unreal/exterior-neighbor-props-native-r39-r3.py')
def now():return datetime.now(timezone.utc).isoformat()
def report_write(p,v):Path(p).write_text(json.dumps(v,indent=2,sort_keys=True,allow_nan=False)+'\n')
def helpers(bundle):
 require(set(bundle)=={'source','base','binding'}and set(bundle['base']['readerPacket'])=={'base'},'Exact current base observer packet required');return bundle['base']['native'].helpers(bundle['base']['readerPacket'])
def actors(u):return {a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
def full(u,h):return h['cleanNative'].full_witness(u,h)
def cyclic(v):return min(tuple(v[i:]+v[:i])for i in range(3))
def expected_corners(row):return [cyclic([tuple(row['expectedNativeVerticesCm'][i]+row['uv0'][i])for i in row['indices'][a:a+3]])for a in range(0,len(row['indices']),3)]
def full_geometry(u,mesh,row):
 require(mesh and mesh.get_class().get_path_name()=='/Script/Engine.StaticMesh'and mesh.get_path_name().startswith(g.PREFIX+'/Geometry/')and mesh.get_num_lods()==1 and len(mesh.get_editor_property('static_materials'))==1,'Only own one-LOD single-section master permitted')
 d=mesh.get_static_mesh_description(0);count=len(row['indices'])//3;require(d and d.get_triangle_count()==mesh.get_num_triangles(0)==count and mesh.get_num_sections(0)==1,'Full authored/native triangle census differs');actual=[]
 for ordinal in range(count):
  t=u.TriangleID(id_value=ordinal);require(int(d.get_triangle_polygon_group(t).id_value)==0,'Single-section ordered identity differs');face=[]
  for corner in range(3):
   vi=d.get_triangle_vertex_instance(t,corner);p=d.get_vertex_position(d.get_vertex_instance_vertex(vi));uv=d.get_vertex_instance_uv(vi,0);face.append(tuple(float(getattr(p,k))for k in 'xyz')+tuple(float(getattr(uv,k))for k in 'xy'))
  actual.append(cyclic(face))
 exact(actual,expected_corners(row),'Full ordered encoded native F32 P/UV0/section/winding differs')
 return {'id':row['id'],'material':row['material'],'asset':mesh.get_path_name(),'triangles':count,'fullOrderedNativeF32PositionUv0SectionWindingSha256':digest(actual),'sourceGeometrySha256':g.GEOMETRY_SHA,'sourceNormalsRetainedInGlb':True,'nativeNormalTangentNumericReadbackPerformed':False,'providerGeometryClaimed':False,'nativeAppearanceOrContactAccepted':False}
def bind_geometry(u,meshes,rows):
 require(len(meshes)==len(rows)==3 and len({m.get_path_name()for m in meshes})==3,'Three distinct complete masters required');result={};proof={}
 for mesh in meshes:
  candidate=[r for r in rows if len(r['indices'])//3==mesh.get_num_triangles(0)];matches=[]
  for r in candidate:
   try:got=full_geometry(u,mesh,r)
   except RuntimeError:continue
   matches.append((r,got))
  require(len(matches)==1,'Distinct counts route only; full corner identity must uniquely match');r,got=matches[0];require(r['material']not in result,'Duplicate full source identity');result[r['material']]=mesh;proof[r['material']]=got
 return result,proof
def old_materials(u,bundle,h,directory):
 require(not directory.exists(),'Fresh actual graph checkpoint required');directory.mkdir();result={}
 for i,(asset,row)in enumerate(sorted(bundle['base']['materialRecords'].items())):
  m=u.EditorAssetLibrary.load_asset(asset);require(isinstance(m,u.Material),'Protected graph missing');graph=bundle['base']['native'].graph_snapshot(u,m,h,row['route']);aux=h['materials'].aux_snapshot(u,m)
  usage={'instancedStaticMeshes':bool(u.MaterialEditingLibrary.has_material_usage(m,h['existing'].native_enum(u.MaterialUsage,'INSTANCEDSTATICMESHES'))),'nanite':bool(u.MaterialEditingLibrary.has_material_usage(m,u.MaterialUsage.MATUSAGE_NANITE))}
  got={'asset':asset,'reader':row['route'],'graph':graph,'graphSha256':digest(graph),'aux':aux,'usage':usage,'usagePreviouslyRecorded':row['usageRecorded']}
  if 'metadata'in row:got['metadata']={k:u.EditorAssetLibrary.get_metadata_tag(m,k)for k in row['metadata']}
  write(directory/('graph-'+str(i).zfill(3)+'.json'),got);exact(graph,row['graph'],'Protected full graph changed: '+asset)
  if row['aux']is not None:exact(aux,row['aux'],'Protected sampler/world-position auxiliaries changed')
  for k,v in row['usage'].items():require(usage[k]==v,'Protected material usage changed')
  if 'metadata'in row:require(got['metadata']==row['metadata'],'Protected material metadata changed')
  result[asset]=got
 require(len(result)==69,'All69 current original graphs required');return result
def old_textures(u,bundle,h):
 result={}
 for asset,row in bundle['base']['textureRecords'].items():
  t=u.EditorAssetLibrary.load_asset(asset);require(isinstance(t,u.Texture2D),'Protected Texture2D missing');got=h['materials'].texture_snapshot(u,t)
  if 'partialSnapshot'in row:
   g.texture_subset(got,row['partialSnapshot']);got['selectedMetadata']={k:u.EditorAssetLibrary.get_metadata_tag(t,k)for k in row['metadata']};require(got['selectedMetadata']==row['metadata'],'Protected new R39 source-map metadata changed')
  else:exact(got,row,'Protected actual old97 complete visible texture settings changed')
  result[asset]=got
 require(len(result)==108,'All108 actual original textures required');return result
def raw_controls(u,bundle,witness):
 got=bundle['base']['native'].raw_instance_controls(u,witness);old={k:v for k,v in got.items()if k in bundle['base']['rawControls']};exact(old,bundle['base']['rawControls'],'All2325 original raw controls changed');require(len(got)==2329 and sum(v['instances']for v in got.values())==678205,'All current2329 raw controls required')
 scene=actors(u)
 for key,row in bundle['base']['report']['newOwnedGroups'].items():
  a=scene[row['actor']];c=a.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent);m=bundle['base']['measurements'][key]
  require(c and c.get_instance_count()==row['instances']and c.get_path_name()in got,'Current props raw component binding differs')
  exact([R39.matrix(c,i)for i in range(c.get_instance_count())],m['storedMatrices'],'Current original props stored matrices changed')
  exact([R39.transform_value(R39.instance_value(c,i))for i in range(c.get_instance_count())],m['recoveredValues'],'Current original props recovered values/order changed')
 return got

def import_geometry(u,bundle,h,materials,directory):
 assets=u.EditorAssetLibrary;system=u.get_editor_subsystem(u.EditorActorSubsystem);level=u.get_editor_subsystem(u.LevelEditorSubsystem);subsystem=h['meshHelper'].static_mesh_subsystem(u);require(subsystem,'Installed native mesh accessor missing');pipelines=[]
 for source,name in [('GLTFSceneAssets','Assets'),('GLTFMaterials','Materials'),('LevelActors','Level')]:
  p=g.PREFIX+'/Pipeline/'+name;require(not assets.does_asset_exist(p),'Fresh owned pipeline only');v=assets.duplicate_asset('/Game/Brezi/Pipeline/'+source,p);require(v,'Cannot copy owned pipeline');pipelines.append(v)
 for k,v in {'combine_static_meshes_behavior':u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,'collision':False,'build_nanite':False,'generate_lightmap_u_vs':False}.items():pipelines[0].get_editor_property('mesh_pipeline').set_editor_property(k,v)
 for k,v in {'bake_meshes':False,'bake_pivot_meshes':False,'import_lods':False,'remove_degenerates':False,'recompute_normals':False,'recompute_tangents':True,'use_full_precision_u_vs':True}.items():pipelines[0].get_editor_property('common_meshes_properties').set_editor_property(k,v)
 mp=pipelines[0].get_editor_property('material_pipeline');mp.set_editor_property('import_materials',False);mp.get_editor_property('texture_pipeline').set_editor_property('import_textures',False);pipelines[2].set_editor_property('scene_hierarchy_type',u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
 params=u.ImportAssetParameters()
 for k,v in {'is_automated':True,'replace_existing':False,'force_show_dialog':False,'override_pipelines':[u.SoftObjectPath(p.get_path_name())for p in pipelines],'import_level':level.get_current_level()}.items():params.set_editor_property(k,v)
 before=full(u,h);paths=set(actors(u));manager=u.InterchangeManager.get_interchange_manager_scripted();returned=manager.import_scene(g.PREFIX+'/Geometry/Boundary',manager.create_source_data(str(g.checked(bundle['source']['glbPin']))),params)
 temporary=[a for p,a in actors(u).items()if p not in paths];inventory=R39.temporary_inventory(u,temporary,R39.transform_value);write(directory/'import-objects-before-gates.json',inventory);require(returned,'Owned authored scene import failed');h['meshHelper'].finish_static_mesh_compilation(u,synchronous=True)
 meshes=[];containers=[]
 for a in temporary:
  comps=a.get_components_by_class(u.StaticMeshComponent)
  if comps:
   require(len(comps)==1 and len(a.get_components_by_class(u.ActorComponent))==1 and a.get_editor_property('root_component')==comps[0]and comps[0].get_owner()==a,'One owned imported rendering root required');mesh=comps[0].get_editor_property('static_mesh');require(mesh and mesh not in meshes,'Distinct own imported mesh required');meshes.append(mesh)
  else:
   components=a.get_components_by_class(u.ActorComponent);require(a.get_class().get_path_name()=='/Script/Engine.Actor'and len(components)==1 and components[0].get_class().get_path_name()=='/Script/Engine.SceneComponent'and not a.get_components_by_class(u.PrimitiveComponent),'Only one closed nonrendering Scene container permitted');containers.append(a.get_path_name())
 require(len(containers)<=1 and len(temporary)==3+len(containers),'Only three source roots and optional Scene container permitted');bound,proof=bind_geometry(u,meshes,bundle['source']['exportRows']);write(directory/'import-full-identities.json',proof)
 for role,mesh in list(bound.items()):
  name='boundary_'+role+'_r43';target=g.PREFIX+'/Geometry/StaticMeshes/'+name
  if mesh.get_path_name().split('.')[0]!=target:require(assets.rename_asset(mesh.get_path_name().split('.')[0],target),'Cannot canonicalize own master');mesh=assets.load_asset(target)
  mesh.set_material(0,materials[role]);mesh.set_editor_property('has_navigation_data',False);settings=subsystem.get_lod_build_settings(mesh,0)
  for k,v in {'use_full_precision_u_vs':True,'generate_lightmap_u_vs':False,'recompute_normals':False,'recompute_tangents':True,'remove_degenerates':False}.items():settings.set_editor_property(k,v)
  subsystem.set_lod_build_settings(mesh,0,settings)
  for k,v in {'BreziGeneratedBy':OWNER,'BreziR43SourcePlanSha256':g.SOURCE_SHA,'BreziR43AuthoredRole':role}.items():assets.set_metadata_tag(mesh,k,v)
  require(assets.save_loaded_asset(mesh,only_if_is_dirty=False),'Cannot save own master');bound[role]=mesh
 h['meshHelper'].finish_static_mesh_compilation(u,synchronous=True)
 proof={r['material']:full_geometry(u,bound[r['material']],r)for r in bundle['source']['exportRows']}
 for a in reversed(temporary):require(system.destroy_actor(a),'Cannot remove import-only actor')
 exact(full(u,h),before,'Temporary import modified original complete scene');require(set(actors(u))==paths,'Temporary actors remain');canonical={m.get_path_name().split('.')[0]for m in bound.values()};removed=[]
 for p in assets.list_assets(g.PREFIX+'/Geometry',recursive=True,include_folder=False):
  obj=assets.load_asset(p)
  if obj and obj.get_path_name().split('.')[0]in canonical:continue
  require(obj and obj.get_class().get_name()in ('InterchangeSceneImportAsset','ObjectRedirector'),'Unexpected own geometry artifact');removed.append(obj.get_path_name());require(assets.delete_asset(p),'Cannot remove own import metadata/redirector')
 for p in pipelines:require(assets.save_loaded_asset(p,only_if_is_dirty=False),'Cannot save own pipeline')
 return bound,{'proofs':proof,'temporaryActorInventory':pin(directory/'import-objects-before-gates.json'),'sourceCompleteTriangles':12566,'containers':containers,'removedOwnImportMetadata':removed,'pipelineAssets':[p.get_path_name()for p in pipelines],'nativeNormalTangentNumericReadbackPerformed':False}

def apply_new(u,bundle,h,meshes,materials):
 scene=actors(u);system=u.get_editor_subsystem(u.EditorActorSubsystem);require(g.TEMPLATE in scene,'Identity visual template unavailable');new={};added={}
 for role in g.MATERIAL_ROLES:
  # Same-world duplicate, no inactive UWorld/constructor quaternion guess.
  a=system.duplicate_actor(scene[g.TEMPLATE],None,u.Vector(0,0,0));require(a and a.get_path_name()not in scene,'Fresh same-world identity template copy required');a.set_editor_property('tags',[u.Name(g.TAG+role)]);a.set_actor_label('EX_boundary_r43_'+role);c=a.get_editor_property('static_mesh_component')
  require(a.get_editor_property('root_component')==c and c.get_owner()==a and len(a.get_components_by_class(u.ActorComponent))==1,'Sole new owned root policy required');require(c.set_static_mesh(meshes[role]),'Cannot bind authored master');c.set_material(0,materials[role]);c.set_collision_enabled(u.CollisionEnabled.NO_COLLISION);c.set_editor_property('cast_shadow',role!='gravel')
  path=a.get_path_name();expected=g.added_expected(bundle,role,path,meshes[role].get_path_name(),materials[role].get_path_name());new[role]=path;added[path]=expected
 got=full(u,h)
 for path,row in added.items():exact(got[path],row,'Source-template new identity/nav/draw/shadow policy differs')
 return new,added

def primary_api():
 e=Path('/Users/Shared/Epic Games/UE_5.8/Engine');files={'basis':e/'Plugins/Interchange/Runtime/Source/Parsers/GLTFCore/Private/GLTF/ConversionUtilities.h','attributes':e/'Plugins/Interchange/Runtime/Source/Parsers/GLTFCore/Private/GLTF/GLTFMesh.cpp','indices':e/'Plugins/Interchange/Runtime/Source/Parsers/GLTFCore/Private/GLTFMeshFactory.cpp','actors':e/'Source/Editor/UnrealEd/Public/Subsystems/EditorActorSubsystem.h','staticMeshComponent':e/'Source/Runtime/Engine/Classes/Components/StaticMeshComponent.h','primitiveComponent':e/'Source/Runtime/Engine/Classes/Components/PrimitiveComponent.h','materials':e/'Source/Editor/MaterialEditor/Public/MaterialEditingLibrary.h'}
 require('Vec.X, Vec.Z, Vec.Y'in files['basis'].read_text()and 'GetVec2Array(Buffer)'in files['attributes'].read_text()and 'Indices[(TriangleIndex * 3 + Corner)]'in files['indices'].read_text()and 'DuplicateActor(AActor* ActorToDuplicate, UWorld* ToWorld = nullptr'in files['actors'].read_text(),'Installed source/identity pipeline changed');return {k:pin(v)for k,v in files.items()}
def validate_plan(bundle=None):
 bundle=g.load_contract()if bundle is None else bundle;plan=read(g.PLAN);require(plan['schema']==g.SCHEMA and plan['owner']=='scripts/unreal/exterior-context-parcel-boundary-native-study-r43.py'and plan['nativeOwner']==OWNER and plan['status']=='accepted-authored-boundary-source-ready-native-pending'and plan['binding']==bundle['binding']and plan['expectedCounts']==g.COUNTS and plan['nativeExecuted']is False and plan['gpuExecuted']is False and plan['newActorTemplate']==bundle['base']['template'],'Exact own source/native plan required')
 require(plan['expectedNewPackageAssets']==g.expected_new_packages()and plan['primaryApi']==primary_api(),'Own package/API scope differs');bundle['source']['glbPin']=plan['sourceGlb'];g.checked(plan['sourceGlb']);require(plan['exportRowsSha256']==digest(bundle['source']['exportRows']),'Complete authored export recipe differs')
 require(all(sha(p)==v for p,v in plan['inputFiles'].items()),'Consumed frozen source differs');return plan,bundle
def preflight(directory,bundle=None):
 directory=Path(directory).resolve();require(directory==g.STUDY/'source-preflight'and not directory.exists(),'One fresh mandatory preflight');plan,bundle=validate_plan(bundle);h=helpers(bundle);g.validate_clone(bundle);directory.mkdir();tests=module('_r43_focused_native_fixture',ROOT/'scripts/unreal/test_exterior_context_parcel_boundary_native_r43.py');tests.Contracts.BUNDLE=bundle;maps=module('_r43_focused_material_fixture',ROOT/'scripts/unreal/test_exterior_context_parcel_boundary_materials_r43.py');suite=unittest.TestSuite([unittest.defaultTestLoader.loadTestsFromTestCase(tests.Contracts),unittest.defaultTestLoader.loadTestsFromTestCase(maps.BoundaryMaterials)]);stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);log=directory/'cpu-guards.log';log.write_text(stream.getvalue());require(result.wasSuccessful()and result.testsRun==TEST_COUNT,'Focused suite failed: '+str(result.testsRun));files={**plan['inputFiles'],str(g.PLAN):sha(g.PLAN)};require(all(sha(p)==v for p,v in files.items()),'Source changed during mandatory suite')
 pf={'schema':g.SCHEMA,'schemaVersion':1,'owner':OWNER,'status':'accepted-authored-boundary-source-preflight-validated-native-pending','createdAt':now(),'selectedPlan':pin(g.PLAN),'binding':bundle['binding'],'expectedCounts':g.COUNTS,'inputFiles':files,'moduleOrderWitness':h['moduleOrderWitness'],'tests':{'exitCode':0,'testCount':TEST_COUNT,'log':pin(log),'nativeApisActuallyExercised':False},'nativeExecuted':False,'gpuExecuted':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'activeOutputPromoted':False};write(directory/'source-preflight.json',pf);print(json.dumps({'preflight':pin(directory/'source-preflight.json'),'testCount':TEST_COUNT}),flush=True);return pf
def validate_preflight(path,plan,bundle):
 pf=read(path);require(pf['selectedPlan']==pin(g.PLAN)and pf['binding']==bundle['binding']and pf['inputFiles']=={**plan['inputFiles'],str(g.PLAN):sha(g.PLAN)}and pf['tests']['exitCode']==0 and pf['tests']['testCount']==TEST_COUNT and pf['nativeExecuted']is False,'Executed preflight binding required');g.checked(pf['tests']['log']);require(all(sha(p)==v for p,v in pf['inputFiles'].items()),'Exact preflight consumed bytes required');return pf

def main():
 import unreal as u
 require(Path(os.environ['BREZI_GARDEN_BOUNDARY_OUTPUT']).resolve()==g.CANDIDATE and Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==g.PROJECT,'Exact own fresh R43 project required');require(sha(g.PLAN)==os.environ['BREZI_GARDEN_BOUNDARY_PLAN_SHA256'],'Exact own plan SHA required');p=Path(os.environ['BREZI_GARDEN_BOUNDARY_PREFLIGHT']);require(sha(p)==os.environ['BREZI_GARDEN_BOUNDARY_PREFLIGHT_SHA256']and not(g.CANDIDATE/REPORT).exists(),'Exact executed preflight/fresh report required');plan,bundle=validate_plan();pf=validate_preflight(p,plan,bundle);h=helpers(bundle);require(h['moduleOrderWitness']==pf['moduleOrderWitness'],'Frozen reader order changed');maps=module('_r43_material_builder',MATERIAL);maps.preflight_enums(u);directory=g.CANDIDATE/'boundary-checkpoint';require(not directory.exists(),'Fresh checkpoint');directory.mkdir();base=bundle['base'];r={'schema':g.SCHEMA,'schemaVersion':1,'owner':OWNER,'status':'running','startedAt':now(),'nativeProcessId':os.getpid(),'project':str(g.PROJECT),'selectedPlan':pin(g.PLAN),'sourcePreflight':pin(p),'sourceProposal':pin(g.SOURCE),'sourceGeometry':bundle['source']['geometryPin'],'sourceGlb':bundle['source']['glbPin'],'rootSourceDecision':pin(g.DECISION),'binding':bundle['binding'],'baseNativeReport':base['reportPin'],'baseNativeProcess':base['processPin'],'baseCurrentByteAudit':base['auditPin'],'projectClone':pin(g.CLONE),'protectedProjectProof':base['report']['protectedProjectProof'],'inputFiles':pf['inputFiles'],'nativeApplied':False,'savedMapUnloadedReloaded':False,'sourceInputsUnchanged':False,'activeDesign':'C/B/B','setbacksMm':[3000,3000],'oldActorInstanceMaterialOrCollisionSettersCalled':False,'providerGeometryClaimed':False,'sourcePixelsEdited':False,'nativeNormalTangentNumericReadbackPerformed':False,'nativeAppearanceAccepted':False,'nativeCollisionOrContactVerified':False,'legalFencePlacementOrOwnershipClaimed':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'activeOutputPromoted':False};report_write(g.CANDIDATE/REPORT,r)
 try:
  module_file=g.PROJECT/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib';source_module=base['project']/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib';require(sha(module_file)==sha(source_module)and module_file.stat().st_ino!=source_module.stat().st_ino,'Canonical module must remain exact/independent');g.validate_clone(bundle);levels=u.get_editor_subsystem(u.LevelEditorSubsystem);require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot load own candidate map');before=full(u,h);exact(before,base['savedWitness'],'Complete selected5368 actor state changed');raw=raw_controls(u,bundle,before);mat=old_materials(u,bundle,h,directory/'graphs-before');tex=old_textures(u,bundle,h)
  for name,v in [('before-actors',before),('raw-controls-before',raw),('old-materials-before',mat),('old-textures-before',tex)]:write(directory/(name+'.json'),v)
  reader=lambda unreal,m:h['existing'].graph_snapshot(unreal,m);materials,built=maps.build_materials(u,bundle,bundle['binding'],reader);require(set(materials)==set(g.MATERIAL_ROLES)and len(built['newPackageAssets'])==9,'Exact3 graphs/6 map objects required')
  for asset in built['newPackageAssets']:
   obj=u.EditorAssetLibrary.load_asset(asset);require(obj and u.EditorAssetLibrary.save_loaded_asset(obj,only_if_is_dirty=False),'Cannot save own photographic material/texture package')
  meshes,imported=import_geometry(u,bundle,h,materials,directory);exact(full(u,h),before,'Original actor state changed before three additions');new,added=apply_new(u,bundle,h,meshes,materials);expected=g.expected_counterfactual(before,added);exact(full(u,h),expected,'Full original+three counterfactual differs before save');write(directory/'expected-actors.json',expected);require(levels.save_current_level(),'Cannot save own boundary map');require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot unload/reload own saved boundary map');saved=full(u,h);exact(saved,expected,'Whole saved original+three actor counterfactual differs');materials_saved=maps.verify_materials(u,bundle,bundle['binding'],built,reader);meshes_saved={role:u.EditorAssetLibrary.load_asset(m.get_path_name())for role,m in meshes.items()};geometry={row['material']:full_geometry(u,meshes_saved[row['material']],row)for row in bundle['source']['exportRows']};require(sum(v['triangles']for v in geometry.values())==12566,'Full12566 corner proof required');raw_saved=raw_controls(u,bundle,saved);mat_saved=old_materials(u,bundle,h,directory/'graphs-saved');tex_saved=old_textures(u,bundle,h);exact(raw_saved,raw,'All2329 raw state changed across reload');exact(mat_saved,mat,'All69 graph/aux/observed usage changed across reload');exact(tex_saved,tex,'All108 complete visible texture states changed across reload');content=g.validate_clone(bundle,after=True);delta=g.validate_content_delta(base['content'],content)
  for name,v in [('saved-actors',saved),('raw-controls-saved',raw_saved),('old-materials-saved',mat_saved),('old-textures-saved',tex_saved),('new-materials',built),('geometry-readback',geometry),('import-readback',imported),('after-content',content)]:write(directory/(name+'.json'),v)
  require(all(sha(path)==v for path,v in pf['inputFiles'].items()),'Immutable consumed source changed');require(len(saved)==5371,'Saved actor census differs')
  r.update(status=STATUS,completedAt=now(),nativeApplied=True,savedMapUnloadedReloaded=True,sourceInputsUnchanged=True,moduleOrderWitness=h['moduleOrderWitness'],nativeModuleWitness={'source':str(source_module),'destination':str(module_file),'sha256':sha(module_file),'bytes':module_file.stat().st_size,'independentInodes':True},beforeActorWitness=pin(directory/'before-actors.json'),expectedActorWitness=pin(directory/'expected-actors.json'),savedActorWitness=pin(directory/'saved-actors.json'),beforeActorWitnessSha256=digest(before),expectedActorWitnessSha256=digest(expected),savedActorWitnessSha256=digest(saved),rawInstanceControlsBefore=pin(directory/'raw-controls-before.json'),rawInstanceControlsSaved=pin(directory/'raw-controls-saved.json'),originalMaterialWitnessBefore=pin(directory/'old-materials-before.json'),originalMaterialWitnessSaved=pin(directory/'old-materials-saved.json'),originalTextureWitnessBefore=pin(directory/'old-textures-before.json'),originalTextureWitnessSaved=pin(directory/'old-textures-saved.json'),newMaterialReport=pin(directory/'new-materials.json'),materialReport=built,nativeGeometryReadback=geometry,nativeGeometryReadbackReceipt=pin(directory/'geometry-readback.json'),importReadback=pin(directory/'import-readback.json'),newOwnedActors={role:{'actor':path,'mesh':meshes_saved[role].get_path_name(),'material':materials_saved[role].get_path_name(),'collision':'NoCollision','identityFromAuthenticatedSourceTemplate':True}for role,path in new.items()},afterContentInventory=pin(directory/'after-content.json'),assetDelta=delta,newPackages=g.expected_new_packages(),actualCounts=g.COUNTS,allOriginal5368ActorsAnd2329RawControlsExact=True,allOriginal69GraphsAuxObservedUsageExact=True,allOriginal108VisibleTextureSettingsExact=True,newActorIdentityNavDrawShadowPolicySourceTemplateVerified=True)
  report_write(g.CANDIDATE/REPORT,r);print(json.dumps({'report':pin(g.CANDIDATE/REPORT),'status':STATUS}),flush=True)
 except Exception as e:r.update(status='failed',completedAt=now(),error=str(e));report_write(g.CANDIDATE/REPORT,r);raise
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--preflight',type=Path);args=p.parse_args();preflight(args.preflight)if args.preflight else main()
