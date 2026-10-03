"""Root-only R35 exact saved-R32 scoped yard repair; no garden composition here.

A removes34 whole original ecology clumps, B replaces only hard-mesh UV1.R,
C rebinds one backdrop component to one two-expression material copy.
"""
import argparse
import copy
from datetime import datetime,timezone
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-repair-native-r35-r2.py'
STUDY_OWNER='scripts/unreal/exterior-context-yard-repair-native-study-r35-r2.py'
s=importlib.util.spec_from_file_location('r35_scoped_source_guards',ROOT/'scripts/unreal/exterior-context-yard-repair-guards-r35.py')
guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard)
require,read,sha,pin,digest=(getattr(guard,k)for k in('require','read','sha','pin','digest'))
SCHEMA='brezi-context-yard-scoped-repair-native-r35'
REPAIR_SCHEMA='brezi-context-yard-native-source-bundle-route-repair-r35-r2'
FAILED=ROOT/'output/unreal/exterior-20261002-r35a'
PREFIX='/Game/Brezi/ContextYardRepair20261002R35'
CANDIDATE=ROOT/'output/unreal/exterior-20261002-r35b'
PLAN=ROOT/'output/unreal/exterior-context-yard-20261002-r35-native-study-r2/yard-repair-native-plan.json'
REPORT='context-yard-repair-native-report-r2.json'
STATUS='verified-saved-scoped-hardcourt-ecology-coverage-near-pbr-repair'
MAP='/Game/Brezi/Maps/Brezi'
CLONE_STATUS='verified-original-r32a-independent-apfs-r35-clone-before-scoped-yard-repair'
COUNTS={'originalActors':5360,'savedActors':5360,'fullHismComponents':2321,'fullHismInstances':678197,
 'originalEcologyRootsRetired':34,'affectedOriginalEcologyGroups':8,'retainedAffectedOriginalEcologyRoots':1919,
 'originalEcologyRootsRetained':24739,'reboundHardGroundComponents':2,'reboundBackdropMaterialComponents':1,
 'newMeshAssets':2,'newMaterialGraphs':1,'newTextureObjects':0,'newPipelineAssets':3,'newPackages':6,
 'uniqueHardMeshTriangles':4519,'scopedMaterialGraphs':64,'scopedTextureObjects':95,'contentFiles':4092,'protectedFiles':132}

def now():return datetime.now(timezone.utc).isoformat()
def write(path,row):
 with Path(path).open('x')as f:json.dump(row,f,indent=2,allow_nan=False);f.write('\n')
def report_write(path,row):Path(path).write_text(json.dumps(row,indent=2,allow_nan=False)+'\n')
def vec(value,axes='xyz'):return [float(getattr(value,k))for k in axes]
def value(transform):return [vec(transform.translation),vec(transform.rotation,'xyzw'),vec(transform.scale3d)]
def matrix(c,i):
 m=c.get_editor_property('per_instance_sm_data')[i].get_editor_property('transform')
 return [vec(getattr(m,k),'xyzw')for k in ('x_plane','y_plane','z_plane','w_plane')]
def binary64(v):
 if isinstance(v,(list,tuple)):return b''.join(binary64(x)for x in v)
 require(type(v)in (float,int),'Measured numeric frame required');return struct.pack('<d',v)
def exact(a,b,message):require(binary64(a)==binary64(b),message)
def module(name,file):
 p=ROOT/'scripts/unreal'/file;s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m

def helpers(bundle):
 base=bundle['base'];h=base['native'].helpers(base['sourceBundle']['base'])
 require('moduleOrderWitness'in h and 'cleanNative'in h and 'meshHelper'in h,'Actual frozen-first R32 helper route required')
 return h

def clone_validation(bundle):
 base=bundle['base'];project=CANDIDATE/'Project/BreziTwin';path=CANDIDATE/'context-yard-repair-project-clone.json';c=read(path)
 require(c['schema']==SCHEMA and c['status']==CLONE_STATUS and c['nativeBaseReport']==base['reportPin']
  and c['sourceProposal']==pin(ROOT/'output/unreal/exterior-context-yard-20261002-r35-source-repair-proposal/source-repair-proposal.json')
  and c['sourceProject']==str(base['project'])and c['project']==str(project)and c['fileCount']==len(c['files'])==4218
  and c['contentFiles']==4086 and c['protectedFiles']==132 and c['selectedPlan']is None and c['sourcePreflight']is None
  and c['nativeExecuted']is False and c['nativePreflightPending']is True,'Exact fresh independent R32 clone required')
 expected={'Content/'+k:v for k,v in base['content'].items()};expected.update(base['protected']);seen=set()
 for row in c['files']:
  relative=str(Path(row['destination']).relative_to(project));require(relative in expected and relative not in seen,'Exact project-only clone keys required');seen.add(relative)
  source=base['project']/relative;target=project/relative
  require(row['source']==str(source)and row['destination']==str(target)and row['independentInodes']is True
   and {'sha256':row['sha256'],'bytes':row['bytes']}==expected[relative],'Original clone row provenance differs')
  a,b=source.stat(),target.lstat();require(target.is_file()and not target.is_symlink()and a.st_size==b.st_size==row['bytes']and(a.st_dev!=b.st_dev or a.st_ino!=b.st_ino),'Independent byte-size clone required before native')
 require(len(seen)==4218,'All actual original project files required');return pin(path)

def input_files(plan,bundle):
 files=dict(plan['inputFiles']);files[str(PLAN)]=sha(PLAN)
 for p,h in files.items():require(sha(p)==h,'Consumed new-source closure differs')
 return files

def validate_plan_header(plan,bundle):
 base_material_contract(bundle)
 require(plan['repairSchema']==REPAIR_SCHEMA and plan['priorFailedAttempt']==prior_failed_attempt(),'Exact R2 repair and failed historical attempt required')
 require(plan['schema']==SCHEMA and plan['schemaVersion']==1 and plan['owner']==STUDY_OWNER and plan['nativeOwner']==OWNER
  and plan['status']=='source-ready-exact-saved-r32-three-scoped-repairs-native-pending'
  and plan['expectedCounts']==COUNTS and plan['candidateOutput']==str(CANDIDATE)
  and plan['baseNativeReport']==bundle['base']['reportPin']
  and plan['baseNativeProcess']==bundle['base']['process']and plan['baseCurrentByteAudit']==bundle['base']['audit']
  and plan['sourceProposal']==pin(guard.PROPOSAL)
  and plan['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}and plan['setbacksMm']=={'street':3000,'east':3000}
  and all(plan[k]is False for k in ('nativeApplied','nativeExecuted','gpuExecuted','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified')),
  'Exact typed source-only scoped native plan required')
 require(plan['affectedOriginalEcologyGroupIndices']=={k:v['selectedSourceIndices']for k,v in bundle['ecologyGroups'].items()}
  and plan['hardTargets']=={k:{x:v[x]for x in ('actor','component','currentMesh','currentMaterials','currentOverrides')}for k,v in bundle['floorTargets'].items()}
  and plan['backdropTarget']==bundle['backdropTarget'],'Typed exact source target selection differs')
 return True

def captured_ecology(u,bundle,h):
 result={};actors={a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
 for identity,group in bundle['ecologyGroups'].items():
  c=h['cleanNative'].component_lookup(u,group['actor'],group['component']);count=c.get_instance_count()
  require(c.get_editor_property('static_mesh').get_path_name()==group['mesh'] and count==len(group['sourceRows']),'Current original ecology binding differs')
  row={'groupId':identity,'actor':group['actor'],'component':group['component'],'mesh':group['mesh'],'instanceCount':count,
   'rootIds':[identity+':'+str(i)for i in range(count)],'sourceRootIndices':list(range(count)),
   'recoveredValues':[value(h['rural'].instance_value(c,i))for i in range(count)],'storedMatrices':[matrix(c,i)for i in range(count)],
   'mainRandomSeed':int(c.get_editor_property('instancing_random_seed')),'numCustomDataFloats':int(c.get_editor_property('num_custom_data_floats')),
   'customData':list(c.get_editor_property('per_instance_sm_custom_data')),'additionalRandomSeedsReadbackAvailable':False,'seedRangesReconstructed':False}
  guard.validate_native_controls(row,group,bundle);result[identity]=row
 require(len(result)==8 and sum(v['instanceCount']for v in result.values())==1953,'Exact eight affected original groups required')
 return result

def captured_remaining_ecology(u,bundle,h,original):
 result={}
 for identity,group in bundle['ecologyGroups'].items():
  c=h['cleanNative'].component_lookup(u,group['actor'],group['component']);expected=guard.expected_control(original[identity],group['selectedSourceIndices']);count=c.get_instance_count()
  require(count==expected['instanceCount']and c.get_editor_property('static_mesh').get_path_name()==expected['mesh'],'Exact retained ecology mesh/count required')
  row=copy.deepcopy(expected);row['recoveredValues']=[value(h['rural'].instance_value(c,i))for i in range(count)];row['storedMatrices']=[matrix(c,i)for i in range(count)]
  row['mainRandomSeed']=int(c.get_editor_property('instancing_random_seed'));row['numCustomDataFloats']=int(c.get_editor_property('num_custom_data_floats'));row['customData']=list(c.get_editor_property('per_instance_sm_custom_data'))
  exact(row['recoveredValues'],expected['recoveredValues'],'Actual retained recovered frames/order changed');exact(row['storedMatrices'],expected['storedMatrices'],'Actual retained stored double matrices/order changed')
  require(row==expected,'Observed original mainseed/customdata/member identity controls changed');result[identity]=row
 require(sum(v['instanceCount']for v in result.values())==1919,'All1919 actual affected survivors required');return result

def ecology_expected_geometry(bundle):
 result={}
 for model,source in bundle['ecologySourceModels'].items():
  owners=[g for g in bundle['ecologyGroups'].values()if g['modelId']==model]
  require(owners and len({g['mesh']for g in owners})==1,'One actual native source master per model required')
  bindings=[guard.component(g['originalWitness'],g['component'])['materials']for g in owners]
  require(all(v==bindings[0]for v in bindings),'Original component material bindings disagree')
  lods=[]
  for level,lod in enumerate(source['lods']):
   require(lod['level']==level and len(lod['parts'])==len(bindings[0]),'Source primitive/native material section order differs')
   faces=[];sections=[]
   for section,part in enumerate(lod['parts']):
    require(len(part['indices'])==3*part['triangles'],'Full primitive source index census required')
    for at in range(0,len(part['indices']),3):
     face=[tuple(part['positionsCm'][i]+part['uv0'][i]+part['uv1'][i])for i in part['indices'][at:at+3]]
     faces.append(guard.cyclic(face));sections.append(section)
   require(len(faces)==lod['triangles'],'All original source triangles required')
   lods.append({'level':level,'corners':faces,'sections':sections,'sourcePrimitives':[{'section':i,'sourceMaterialName':p['materialName'],'triangles':p['triangles']}for i,p in enumerate(lod['parts'])]})
  require(len(lods)==3,'All three source LODs required')
  result[model]={'mesh':owners[0]['mesh'],'materials':bindings[0],'lods':lods}
 return result

def native_ecology_geometry(u,bundle,h):
 proofs={}
 for model,source in ecology_expected_geometry(bundle).items():
  mesh=u.EditorAssetLibrary.load_asset(source['mesh']);require(mesh and mesh.get_num_lods()==3,'Existing full threeLOD ecology master required');lods=[]
  require([mesh.get_material(i).get_path_name()for i in range(len(mesh.get_editor_property('static_materials')))]==source['materials'],'Actual original ecology material slots differ')
  for level,expected in enumerate(source['lods']):
   description=mesh.get_static_mesh_description(level);require(description and mesh.get_num_triangles(level)==description.get_triangle_count()==len(expected['corners'])and mesh.get_num_sections(level)==len(source['materials']),'Exact original ecology native LOD triangle/section count required')
   actual=[]
   for j in range(description.get_triangle_count()):
    triangle=u.TriangleID(id_value=j);require(int(description.get_triangle_polygon_group(triangle).id_value)==expected['sections'][j],'Actual source primitive/material triangle order differs');face=[]
    for corner in range(3):
     vi=description.get_triangle_vertex_instance(triangle,corner);p=description.get_vertex_position(description.get_vertex_instance_vertex(vi))
     face.append(tuple(vec(p)+vec(description.get_vertex_instance_uv(vi,0),'xy')+vec(description.get_vertex_instance_uv(vi,1),'xy')))
    actual.append(guard.cyclic(face))
   require(actual==expected['corners'],'Full original ecology F32 positions/UV0/UV1/order/winding differs')
   lods.append({'level':level,'triangles':len(actual),'sourcePrimitives':expected['sourcePrimitives'],'nativeOrderedF32PositionUv0Uv1CornersSha256':digest(actual),'fullNativeSourcePositionUvTopologyWindingVerified':True})
  proofs[model]={'asset':source['mesh'],'materials':source['materials'],'lods':lods,'nativeNormalTangentReadbackAvailable':False,'freshAllThreeNativeLodsDecoded':True}
 return proofs

def prior_failed_attempt():
 paths={'report':'context-yard-repair-native-report.json','receipt':'context-yard-repair-native-process.json',
  'raw':'context-yard-repair-native.log.json','log':'context-yard-repair-native.log','byteAudit':'root-native-failure-byte-audit-r35a-r1.json'}
 pins={k:pin(FAILED/v)for k,v in paths.items()};r=read(pins['report']['path']);t=read(pins['receipt']['path']);raw=read(pins['raw']['path']);audit=read(pins['byteAudit']['path'])
 require(pins['report']['sha256']=='f7c4af362f1056e923391c6c72af50280a9dbfe519e3d2005efe32b099f5510c'
  and pins['byteAudit']['sha256']=='faf7202aa24e0c9ff66170d8c5686da2db7497a9febb8f5be34cdc13e03906af'
  and r['owner']=='scripts/unreal/exterior-context-yard-repair-native-r35.py'and r['status']=='failed'and r['error']=="'recipes'"and r['nativeApplied']is False
  and raw['pid']==r['nativeProcessId']==34679 and raw['code']==255 and raw['signal']is None
  and t['reportSha256']==pins['report']['sha256']and t['processFileSha256']==pins['raw']['sha256']and t['logSha256']==pins['log']['sha256']
  and t['sourcePinsUnchangedAfterNative']is True and len(t['sourcePinsBeforeNative'])==578
  and audit['all4218OriginalCandidateFilesExact']is audit['all4218OriginalR32SourceFilesExact']is audit['noNewContentPackages']is audit['originalMainMapExact']is True,
  'Exact failed unmutated R35a ownership and process evidence required')
 return pins

def base_material_contract(bundle):
 # R32 native.validate_plan() returns separate source-study and saved-parent bundles.
 # all_controls takes the parent, while material verification takes source recipes.
 packet=bundle['base']['sourceBundle']
 require(set(packet)=={'source','base','targets'},'Exact R32 native source/parent/targets packet required')
 source=packet['source'];recipes=source['recipes'];declared=guard.checked(source['plan']['materialCopyProposals'])
 require(recipes==declared and [v['id']for v in recipes]==['yard_gravel_r32','yard_substrate_r32'],
  'Exact pinned two R32 source material recipes required')
 return packet['base'],recipes

def base_controls(u,bundle,h,witness):
 base=bundle['base'];r=base['report'];n=base['native'];parent,recipes=base_material_contract(bundle);old=n.all_controls(u,parent,h,witness)
 require(old==read(r['originalControlsSaved']['path']),'Actual original grass/garden/tree/old-material controls differ from saved R32')
 maps=module('r35_verify_original_r32_two_materials','exterior-context-yard-ground-materials-r32.py')
 originals={key:u.EditorAssetLibrary.load_asset(row['duplicateSource'])for row,key in zip(recipes,['context_track','context_garden_soil'])}
 maps.verify_saved(u,h,recipes,originals,r['newMaterialReport'])
 yard={}
 for actor,row in bundle['base']['witness'].items():
  if not(row['label'].startswith('EX_context_yard_r28_')or row['label'].startswith('EX_yard_ground_r32_')):continue
  components=[v for v in row['components']if v['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
  require(len(components)==1,'Unique protected original yard HISM required');c=h['cleanNative'].component_lookup(u,actor,components[0]['name']);count=c.get_instance_count()
  yard[actor]={'instanceCount':count,'recoveredValues':[value(h['rural'].instance_value(c,i))for i in range(count)],'storedMatrices':[matrix(c,i)for i in range(count)],
   'mainRandomSeed':int(c.get_editor_property('instancing_random_seed')),'numCustomDataFloats':int(c.get_editor_property('num_custom_data_floats')),'customData':list(c.get_editor_property('per_instance_sm_custom_data')),
   'additionalRandomSeedsReadbackAvailable':False,'seedRangesReconstructed':False}
  require(digest(yard[actor]['recoveredValues'])==witness[actor]['components'][0]['orderedInstanceTransformsSha256'],'Protected yard raw frames must bind current full scene')
 require(len(yard)==6 and sum(v['instanceCount']for v in yard.values())==1287,'All13 yard shrubs plus1274 yard low roots must remain observed')
 return {'actualOriginalR32Controls':old,'all13YardShrubsAnd1274LowRootsRawControls':yard}

def remove_original_members(u,bundle,h,controls):
 result=[];actors={a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
 for identity,group in bundle['ecologyGroups'].items():
  control=controls[identity];remove=group['selectedSourceIndices'];desired=guard.expected_control(control,remove);order=guard.swap_remove_order(control['instanceCount'],remove)
  c=h['cleanNative'].component_lookup(u,group['actor'],group['component']);require(c.remove_instances(remove),'Cannot remove exact selected old indices')
  exact([matrix(c,i)for i in range(len(order))],[control['storedMatrices'][i]for i in order],'Actual internal reverse-sorted RemoveAtSwap sequence differs')
  post=c.get_editor_property('per_instance_sm_data');keep=desired['sourceRootIndices'];lookup={source:i for i,source in enumerate(order)}
  c.set_editor_property('per_instance_sm_data',[post[lookup[i]]for i in keep]);actors[group['actor']].synchronize_instance_bounds()
  exact([matrix(c,i)for i in range(len(keep))],desired['storedMatrices'],'Existing surviving wrapped matrices/order changed')
  result.append({'groupId':identity,'actor':group['actor'],'removedOriginalSourceIndices':remove,'removedRoots':len(remove),'nativeRemoveAtSwapOrder':order,
   'retainedOriginalSourceOrder':keep,'onlyActualExistingWrappedStructsReordered':True,'transformOrMatrixRecompositionPerformed':False,'seedSetterUsed':False})
 captured_remaining_ecology(u,bundle,h,controls);return result

def import_hard_geometry(u,bundle,h):
 assets=u.EditorAssetLibrary;actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem);pipelines=[]
 for old,name in [('GLTFSceneAssets','Assets'),('GLTFMaterials','Materials'),('LevelActors','Level')]:
  target=PREFIX+'/Pipeline/'+name;require(not assets.does_asset_exist(target),'Fresh own pipeline namespace required');p=assets.duplicate_asset('/Game/Brezi/Pipeline/'+old,target);require(p,'Cannot create own pipeline');pipelines.append(p)
 mesh_pipeline=pipelines[0].get_editor_property('mesh_pipeline')
 for k,v in {'combine_static_meshes_behavior':u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,'collision':False,'build_nanite':False,'generate_lightmap_u_vs':False}.items():mesh_pipeline.set_editor_property(k,v)
 common=pipelines[0].get_editor_property('common_meshes_properties')
 for k,v in {'remove_degenerates':False,'recompute_normals':False,'recompute_tangents':True,'use_full_precision_u_vs':True}.items():common.set_editor_property(k,v)
 material_pipeline=pipelines[0].get_editor_property('material_pipeline');material_pipeline.set_editor_property('import_materials',False);material_pipeline.get_editor_property('texture_pipeline').set_editor_property('import_textures',False)
 pipelines[2].set_editor_property('scene_hierarchy_type',u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
 params=u.ImportAssetParameters()
 for k,v in {'is_automated':True,'replace_existing':False,'force_show_dialog':False,'override_pipelines':[u.SoftObjectPath(v.get_path_name())for v in pipelines],'import_level':levels.get_current_level()}.items():params.set_editor_property(k,v)
 before={a.get_path_name()for a in actors.get_all_level_actors()};manager=u.InterchangeManager.get_interchange_manager_scripted()
 require(manager.import_scene(PREFIX+'/Geometry',manager.create_source_data(bundle['proposal']['repairBHardUnionCoverage']['sourceGlbVariant']['path']),params),'New byte-only sourceGLB import failed')
 temporary=[a for a in actors.get_all_level_actors()if a.get_path_name()not in before];imported={};records=bundle['floorRecords']
 for actor in temporary:
  for c in actor.get_components_by_class(u.StaticMeshComponent):
   mesh=c.get_editor_property('static_mesh');require(mesh and mesh.get_path_name().startswith(PREFIX+'/Geometry/'),'Only own imported meshes permitted')
   name=mesh.get_name();require(name in {k+'_LOD0'for k in records}|{'yard_ground_r32_yard_substrate_LOD0'},'Unknown geometry outside source3-node GLB')
   key=name[:-5];require(key not in imported,'Duplicate imported mesh identity');imported[key]=mesh
 require(set(imported)==set(records)|{'yard_ground_r32_yard_substrate'},'Exactly3 serialized source meshes must import')
 subsystem=h['meshHelper'].static_mesh_subsystem(u);materials={key:u.EditorAssetLibrary.load_asset(bundle['floorTargets'][key]['currentMaterials'][0])for key in records}
 for identity in records:
  mesh=imported[identity];mesh.set_material(0,materials[identity]);mesh.set_editor_property('has_navigation_data',False);settings=subsystem.get_lod_build_settings(mesh,0)
  for k,v in {'use_full_precision_u_vs':True,'generate_lightmap_u_vs':False,'recompute_normals':False,'recompute_tangents':True,'remove_degenerates':False}.items():settings.set_editor_property(k,v)
  subsystem.set_lod_build_settings(mesh,0,settings);assets.set_metadata_tag(mesh,'BreziGeneratedBy',OWNER);require(assets.save_loaded_asset(mesh,False),'Cannot save own hard mesh')
 h['meshHelper'].finish_static_mesh_compilation(u,synchronous=True)
 for actor in reversed(temporary):require(actors.destroy_actor(actor),'Cannot destroy temporary own import actor')
 unused=imported.pop('yard_ground_r32_yard_substrate');unused_path=unused.get_path_name();require(unused_path.startswith(PREFIX+'/Geometry/'),'Only unused own new substrate may delete');require(assets.delete_asset(unused_path),'Cannot remove unused exact own substrate copy')
 for pipeline in pipelines:require(assets.save_loaded_asset(pipeline,False),'Cannot save own importer')
 known={m.get_path_name().split('.')[0]for m in imported.values()};removed=[unused_path]
 for path in assets.list_assets(PREFIX+'/Geometry',recursive=True,include_folder=False):
  if path.split('.')[0]in known:continue
  obj=assets.load_asset(path);require(obj and obj.get_class().get_name()in ('InterchangeAssetImportData','InterchangeSceneImportAsset'),'Any foreign package deletion rejected')
  require(assets.delete_asset(path),'Cannot remove own unused scene metadata');removed.append(path)
 return imported,[p.get_path_name()for p in pipelines],removed

def geometry_proofs(u,bundle,h,meshes):
 proof={}
 for identity,mesh in meshes.items():proof[identity]=bundle['base']['native'].native_mesh_proof(u,mesh,bundle['floorRecords'][identity],h)
 require(sum(v['triangles']for v in proof.values())==4519,'Exact4519 unchanged source hard triangles required');return proof

def apply_bindings(u,bundle,h,meshes,material):
 for identity,target in bundle['floorTargets'].items():
  c=h['cleanNative'].component_lookup(u,target['actor'],target['component']);require(c.get_editor_property('static_mesh').get_path_name()==target['currentMesh']and [c.get_material(i).get_path_name()for i in range(c.get_num_materials())]==target['currentMaterials'],'Current hard-mesh/material freshness differs')
  require(c.set_static_mesh(meshes[identity]),'Cannot bind own UV-only hard-mesh copy')
 target=bundle['backdropTarget'];c=h['cleanNative'].component_lookup(u,target['actualActor'],target['actualComponent']);c.set_material(0,material)

def verify_saved(u,bundle,h,controls,meshes,material):
 paths={k:v.get_path_name()for k,v in meshes.items()};witness=h['cleanNative'].full_witness(u,h);expected=guard.expected_counterfactual(bundle['base']['witness'],bundle,paths,material.get_path_name())
 require(witness==expected and len(witness)==5360,'Whole source-derived actor counterfactual differs')
 hisms=[c for a in witness.values()for c in a['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
 require(len(hisms)==2321 and sum(c['instanceCount']for c in hisms)==678197,'Full affected source/native census differs')
 retained=captured_remaining_ecology(u,bundle,h,controls);proof=geometry_proofs(u,bundle,h,meshes)
 return witness,retained,proof

def current_content(base,project,packages):
 g=base['native'].guard.g;content=g.inventory(project/'Content');new={p.split('.')[0].removeprefix('/Game/')+'.uasset'for p in packages}
 require(len(packages)==len(new)==6 and all(p.startswith(PREFIX+'/')for p in packages)and not(set(base['content'])&new),'Exactly6 new own packages required')
 require(set(content)==set(base['content'])|new and [k for k in base['content']if base['content'][k]!=content[k]]==['Brezi/Maps/Brezi.umap'],'Only old map and6 newpackages allowed')
 require(g.project_proof(project)==base['protected']and g.inventory(base['project']/'Content')==base['content']and g.project_proof(base['project'])==base['protected'],'Original base/protected132 bytes changed')
 return content,{'changedOriginalFiles':['Brezi/Maps/Brezi.umap'],'newOwnedPackages':sorted(new),'originalContentFiles':4086,'savedContentFiles':4092,'newPackages':6}

def preflight(output,bundle=None):
 require(not output.exists(),'Fresh preflight only');plan=read(PLAN);bundle=guard.validate_source()if bundle is None else bundle;clone=clone_validation(bundle);h=helpers(bundle)
 validate_plan_header(plan,bundle);require(plan['projectClone']==clone,'Exact typed native initial clone required')
 g=bundle['base']['native'].guard.g;project=CANDIDATE/'Project/BreziTwin';require(g.inventory(project/'Content')==bundle['base']['content']and g.project_proof(project)==bundle['base']['protected'],'Actual current fresh clone bytes differ')
 output.mkdir();tests=ROOT/'scripts/unreal/test_exterior_context_yard_repair_native_r35_r2.py';run=subprocess.run([sys.executable,'-B',str(tests)],capture_output=True,text=True,timeout=300);(output/'source-tests.log').write_text(run.stdout+run.stderr);require(run.returncode==0,'Focused new-source native/material contract fixtures failed')
 receipt={'schema':SCHEMA,'owner':OWNER,'status':'scoped-yard-repair-source-preflight-validated-native-pending','createdAt':now(),'selectedPlan':pin(PLAN),'baseNativeReport':bundle['base']['reportPin'],
  'projectClone':clone,'inputFiles':input_files(plan,bundle),'moduleOrderWitness':h['moduleOrderWitness'],'tests':{'source':pin(tests),'log':pin(output/'source-tests.log'),'exitCode':0},
  'expectedCounts':COUNTS,'nativeExecuted':False,'gpuExecuted':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False}
 write(output/'source-preflight.json',receipt);print(json.dumps({'preflight':pin(output/'source-preflight.json'),'sourceInputs':len(receipt['inputFiles'])}))

def main():
 import unreal as u
 output=Path(os.environ['BREZI_YARD_REPAIR_OUTPUT']).resolve();require(output==CANDIDATE,'Only prepared R35b candidate permitted');project=output/'Project/BreziTwin';plan=read(PLAN)
 require(sha(PLAN)==os.environ['BREZI_YARD_REPAIR_PLAN_SHA256'],'Frozen native plan hash differs');pf_path=Path(os.environ['BREZI_YARD_REPAIR_PREFLIGHT']).resolve();require(sha(pf_path)==os.environ['BREZI_YARD_REPAIR_PREFLIGHT_SHA256'],'Frozen native preflight differs')
 pf=read(pf_path);bundle=guard.validate_source();validate_plan_header(plan,bundle);base=bundle['base'];clone=clone_validation(bundle);require(plan['projectClone']==clone,'Exact initial prepared clone required');h=helpers(bundle);maps=module('r35_exact_one_near_material','exterior-context-yard-repair-materials-r35.py');maps.preflight_enums(u,h)
 require(pf['schema']==SCHEMA and pf['owner']==OWNER and pf['status']=='scoped-yard-repair-source-preflight-validated-native-pending'and pf['selectedPlan']==pin(PLAN)and pf['projectClone']==clone and pf['inputFiles']==input_files(plan,bundle)and pf['moduleOrderWitness']==h['moduleOrderWitness']and pf['tests']['exitCode']==0,'Exact executed source preflight required')
 require(base['native'].guard.g.inventory(project/'Content')==base['content']and base['native'].guard.g.project_proof(project)==base['protected'],'Fresh candidate bytes differ')
 require(all(sha(p)==v for p,v in pf['inputFiles'].items()),'Launch frozen source changed');checkpoint=output/'yard-repair-checkpoint';require(not checkpoint.exists(),'Fresh native checkpoint only');checkpoint.mkdir()
 mod=project/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib';source_mod=base['project']/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib';require(sha(mod)==sha(source_mod)=='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574'and mod.stat().st_ino!=source_mod.stat().st_ino,'Actual own oldRecipe4 module required')
 report={'schema':SCHEMA,'schemaVersion':1,'owner':OWNER,'status':'running','startedAt':now(),'nativeProcessId':os.getpid(),'output':str(output),'project':str(project),
  'repairSchema':REPAIR_SCHEMA,'priorFailedAttempt':plan['priorFailedAttempt'],'selectedPlan':pin(PLAN),'sourceProposal':pin(ROOT/'output/unreal/exterior-context-yard-20261002-r35-source-repair-proposal/source-repair-proposal.json'),'sourcePreflight':pin(pf_path),'baseNativeReport':base['reportPin'],'baseNativeProcess':base['process'],'projectClone':clone,
  'inputFiles':pf['inputFiles'],'moduleOrderWitness':h['moduleOrderWitness'],'baseContentInventory':base['report']['afterContentInventory'],'protectedProjectProof':base['report']['protectedProjectProof'],
  'nativeModuleWitness':{'source':str(source_mod),'destination':str(mod),'sha256':sha(mod),'bytes':mod.stat().st_size,'independentInodes':True},
  'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},'setbacksMm':{'street':3000,'east':3000},'nativeApplied':False,
  'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,
  'nativeNormalTangentReadbackAvailable':False,'materialPackagesIndependentlyUnloaded':False,'AdditionalRandomSeedsReadbackAvailable':False,'perInstanceShaderRandomValuePreservationClaimed':False,'sourceGroundElevationSurveyed':False,'tallGardenCompositionApplied':False}
 report_write(output/REPORT,report)
 try:
  levels=u.get_editor_subsystem(u.LevelEditorSubsystem);require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot load own exactR32 clone map')
  before=h['cleanNative'].full_witness(u,h);require(before==base['witness'],'Whole actualR32 base differs');old_controls=base_controls(u,bundle,h,before)
  controls=captured_ecology(u,bundle,h);bundle['nativeEcologyControls']=controls;source_geometry=native_ecology_geometry(u,bundle,h)
  freshness=[row for identity,group in bundle['ecologyGroups'].items()for row in guard.native_support_checks(controls[identity],group,bundle)];require(len(freshness)==34,'All34 current actual-matrix source support intersections required')
  write(checkpoint/'before-actors.json',before);write(checkpoint/'ecology-controls-before.json',controls);write(checkpoint/'old-controls-before.json',old_controls);write(checkpoint/'native-source-support-freshness.json',freshness);write(checkpoint/'native-original-ecology-geometry.json',source_geometry)
  material,material_report=maps.prepare(u,h,bundle);meshes,pipelines,removed=import_hard_geometry(u,bundle,h);geometry_proofs(u,bundle,h,meshes)
  require(h['cleanNative'].full_witness(u,h)==before,'Own asset import/materialcopy mutated original scene')
  removals=remove_original_members(u,bundle,h,controls);apply_bindings(u,bundle,h,meshes,material);expected,retained,geometry=verify_saved(u,bundle,h,controls,meshes,material)
  write(checkpoint/'expected-actors.json',expected);write(checkpoint/'retained-ecology-before-save.json',retained)
  require(levels.save_current_level(),'Cannot save scoped repair map');require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot unload/reload scoped repair map')
  saved_material=maps.verify_saved(u,h,bundle,material_report);saved_meshes={k:u.EditorAssetLibrary.load_asset(v.get_path_name())for k,v in meshes.items()}
  saved,retained_saved,geometry_saved=verify_saved(u,bundle,h,controls,saved_meshes,saved_material);require(saved==expected and retained_saved==retained and geometry_saved==geometry,'Saved full counterfactual/retained controls/geometry differs')
  old_saved=base_controls(u,bundle,h,saved);require(old_saved==old_controls and digest(old_saved)==digest(old_controls),'All original garden/8949grass/78trees/13shrubs/1274low-root raw controls changed')
  packages=[v.get_path_name()for v in saved_meshes.values()]+material_report['newPackageAssets']+pipelines;content,delta=current_content(base,project,packages)
  require(all(sha(p)==v for p,v in pf['inputFiles'].items()),'Consumed immutable source changed during native')
  for name,row in [('saved-actors',saved),('retained-ecology-saved',retained_saved),('old-controls-saved',old_saved),('after-content',content)]:write(checkpoint/(name+'.json'),row)
  report.update(status=STATUS,completedAt=now(),nativeApplied=True,savedMapUnloadedReloaded=True,sourceInputsUnchanged=True,originalSavedR32Unchanged=True,
   repairA={'retiredRoots':34,'affectedGroups':8,'retainedAffectedRoots':1919,'actualRemoveReadback':removals,'freshNativeMatrixAllSourceThreeLodSupportIntersections':34,'nativeSelectedEcologyGeometry':source_geometry,'AdditionalRandomSeedsReadbackAvailable':False,'perInstanceShaderRandomValuePreservationClaimed':False},
   repairB={'hardMeshProofs':geometry_saved,'uniqueHardMeshTriangles':4519,'onlySourceHardUv1CoverageRChanged':True,'allOriginalPositionNormalsIndexUv0Uv1GSourceBytesPreserved':True,'nativeNormalsTangentsReadbackAvailable':False,'sourceCoveragePixelsCausallyProven':False},
   repairC={'target':bundle['backdropTarget'],'materialReport':material_report,'otherFourteenMaterialComponentsUnchanged':True,'nearResponseCoefficientOriginal':.30,'nearResponseCoefficientProposed':.65,'wholeComponentScopeNotTinySpatialOverlay':True},
   beforeActorWitness=pin(checkpoint/'before-actors.json'),expectedActorWitness=pin(checkpoint/'expected-actors.json'),savedActorWitness=pin(checkpoint/'saved-actors.json'),
   beforeActorWitnessSha256=digest(before),expectedActorWitnessSha256=digest(expected),savedActorWitnessSha256=digest(saved),originalEcologyControls=pin(checkpoint/'ecology-controls-before.json'),
   retainedEcologyBeforeSave=pin(checkpoint/'retained-ecology-before-save.json'),retainedEcologySaved=pin(checkpoint/'retained-ecology-saved.json'),nativeFreshnessSupport=pin(checkpoint/'native-source-support-freshness.json'),
   originalControlsBefore=pin(checkpoint/'old-controls-before.json'),originalControlsSaved=pin(checkpoint/'old-controls-saved.json'),afterContentInventory=pin(checkpoint/'after-content.json'),
   assetDelta=delta,newPackages=packages,importPipelineAssets=pipelines,removedOnlyOwnUnusedImportAssets=removed,newMeshes={k:v.get_path_name()for k,v in saved_meshes.items()},actualCounts=COUNTS,
   existingUnrelatedRootsMatricesPoliciesUnchanged=True,allOriginal8949GrassAnd78TreesRawControlsExact=True,allOriginalGardenRawControlsExact=True)
  report_write(output/REPORT,report);print(json.dumps({'report':pin(output/REPORT),'status':STATUS,'nativeAppearanceAccepted':False}))
 except Exception as error:
  report.update(status='failed',completedAt=now(),error=str(error));report_write(output/REPORT,report);raise

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--preflight',type=Path);a=p.parse_args()
 if a.preflight:preflight(a.preflight.resolve())
 else:main()
