"""Root-only four original tree replacements on the exact saved R28b clone.

No import, material build, original asset edit or retained-member reconstruction.
Read-only saved-donor APIs retain their owners; all new instance ownership is R29.
"""
import argparse
import copy
from datetime import datetime,timezone
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-original-tree-group-native-r29.py'
REPORT='original-tree-group-native-report.json'
STATUS='verified-saved-four-original-tree-existing-grove-roots'
s=importlib.util.spec_from_file_location('r29_closed_native_scope',ROOT/'scripts/unreal/exterior-original-tree-group-guards-r29.py')
guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard)
require,read,sha,pin,check_pin,digest,exact=(getattr(guard,k)for k in('require','read','sha','pin','check_pin','digest','exact'))
MAP='/Game/Brezi/Maps/Brezi'


def now():return datetime.now(timezone.utc).isoformat()
def report_write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')


def helpers(bundle):
 base=bundle['base'];clean=base['cleanBase'];h=clean['native'].helpers(clean['cleanBundle'])
 # The genuine frozen importer/policy must be installed first. These tree APIs
 # are readback-only here; neither their old scene mutator nor oldbase loader runs.
 h.update(cleanNative=clean['native'],cleanBundle=clean['cleanBundle'],yard=guard.yard,
  tree=bundle['donor']['native'],treeMaterials=guard.module('r29_readonly_saved_tree_materials','exterior-original-tree-materials.py'))
 return h


def validate_clone(plan,bundle):
 project=guard.CANDIDATE/'Project/BreziTwin';origin=guard.BASE/'Project/BreziTwin'
 initial_path=guard.CANDIDATE/'original-tree-group-base-clone-proof.json';copy_path=guard.CANDIDATE/'original-tree-group-package-copy.json';clone_path=guard.CANDIDATE/'original-tree-group-project-clone.json'
 initial,copied,clone=read(initial_path),read(copy_path),read(clone_path)
 require(initial['schema']==guard.SCHEMA and initial['status']==guard.INITIAL_STATUS and initial['nativeBaseReport']==plan['baseNativeReport']and initial['originalTreeSourceProposal']==plan['sourceProposal']
  and initial['selectedPlan']is None and initial['fileCount']==len(initial['files'])==4175 and initial['nativeExecuted']is False and initial['packageCopyPending']is True,'Exact actual initial clone required')
 require(clone['schema']==copied['schema']==guard.SCHEMA and clone['owner']==copied['owner']==guard.COPY_OWNER
  and clone['status']==guard.CLONE_STATUS and copied['status']==guard.COPY_STATUS and clone['selectedPlan']==copied['selectedPlan']==pin(guard.PLAN)
  and clone['baseNativeReport']==copied['baseNativeReport']==plan['baseNativeReport']and clone['sourceProposal']==copied['sourceProposal']==plan['sourceProposal']
  and clone['project']==copied['project']==str(project)and clone['originalBaseCloneProof']==copied['originalBaseCloneProof']==pin(initial_path)
  and clone['packageCopyReceipt']==pin(copy_path)and clone['originalFileCount']==4175 and clone['newCopiedPackageCount']==copied['copiedPackageCount']==17
  and clone['contentFileCount']==4060 and clone['nativeExecuted']is copied['nativeExecuted']is False,'Typed actual copy/clone receipts differ')
 require(all(copied[k]is False for k in('sceneMapChanged','viewpointsChanged','geometryImportedOrGenerated','originalActorOrMemberMutationApisCalled'))
  and clone['originalFilesIndependentAndByteIdentical']is clone['copiedPackagesIndependentAndByteIdentical']is True,'Copy widened native scope')
 expected={'Content/'+k:v for k,v in bundle['content'].items()};expected.update(bundle['protected']);seen=set()
 for row in initial['files']:
  source,destination=Path(row['source']),Path(row['destination']);relative=destination.relative_to(project).as_posix()
  require(relative in expected and relative not in seen and source==origin/relative and row['independentInodes']is True
   and {k:row[k]for k in('sha256','bytes')}==expected[relative]and source.stat().st_size==destination.stat().st_size==row['bytes']
   and(source.stat().st_dev,source.stat().st_ino)!=(destination.stat().st_dev,destination.stat().st_ino),'Original cloned row/path/inode differs');seen.add(relative)
 require(seen==set(expected),'Exact original4175 clone scope required')
 expected_copies=[{**r,'destination':str(project/'Content'/r['relativeContentPath']),'independentInodes':True}for r in bundle['packages']]
 require(copied['copiedPackages']==expected_copies,'Exact17 saved package identities differ')
 for row in expected_copies:
  source,destination=Path(row['source']),Path(row['destination']);require(sha(source)==sha(destination)==row['sha256']and source.stat().st_size==destination.stat().st_size==row['bytes']
   and(source.stat().st_dev,source.stat().st_ino)!=(destination.stat().st_dev,destination.stat().st_ino),'Independent saved package bytes differ')
 content=guard.g.inventory(project/'Content');guard.validate_content(bundle['content'],content,bundle['packages'],False)
 require(guard.g.project_proof(project)==bundle['protected'],'Own protected132 project files changed')
 return pin(clone_path),pin(copy_path),content


def preflight(output):
 require(Path(output).resolve()==guard.STUDY/'source-preflight'and not Path(output).exists(),'Fresh known R29 preflight directory required')
 plan,bundle=guard.validate_plan();h=helpers(bundle);clone,copied,content=validate_clone(plan,bundle)
 require(guard.g.inventory(guard.BASE/'Project/BreziTwin/Content')==bundle['content']and guard.g.project_proof(guard.BASE/'Project/BreziTwin')==bundle['protected'],'Actual saved R28b bytes changed')
 output=Path(output);output.mkdir();command=[sys.executable,'-B',str(ROOT/'scripts/unreal/test_exterior_original_tree_group_r29.py')]
 tested=subprocess.run(command,cwd=ROOT,text=True,capture_output=True,timeout=120);(output/'cpu-source-tests.log').write_text(tested.stdout+tested.stderr)
 require(tested.returncode==0,'Focused R29 CPU guards failed')
 inputs=dict(plan['inputFiles'])
 for pair in plan['ownedSources'].values():
  for row in pair.values():inputs[row['path']]=row['sha256']
 for row in(pin(guard.PLAN),clone,copied,pin(guard.CANDIDATE/'original-tree-group-base-clone-proof.json'),pin(output/'cpu-source-tests.log')):inputs[row['path']]=row['sha256']
 receipt={'schema':guard.SCHEMA,'owner':OWNER,'status':'four-original-tree-group-source-preflight-validated-native-pending','createdAt':now(),'selectedPlan':pin(guard.PLAN),
  'baseNativeReport':plan['baseNativeReport'],'savedTreeDonor':plan['savedTreeDonor'],'projectClone':clone,'packageCopyReceipt':copied,
  'moduleOrderWitness':h['moduleOrderWitness'],'inputFiles':inputs,'tests':{'command':command,'exitCode':0,'testCount':8,'log':pin(output/'cpu-source-tests.log')},
  'expectedCounts':plan['expectedCounts'],'nativeExecuted':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False}
 guard.write(output/'source-preflight.json',receipt);print(json.dumps({'preflight':pin(output/'source-preflight.json'),'nativeExecuted':False}))


def validate_preflight(path,plan):
 require(Path(path).resolve()==guard.STUDY/'source-preflight/source-preflight.json','Known own preflight required');row=read(path)
 require(row['schema']==guard.SCHEMA and row['owner']==OWNER and row['status']=='four-original-tree-group-source-preflight-validated-native-pending'
  and row['selectedPlan']==pin(guard.PLAN)and row['baseNativeReport']==plan['baseNativeReport']and row['savedTreeDonor']==plan['savedTreeDonor']
  and row['expectedCounts']==plan['expectedCounts']and row['tests']['exitCode']==0 and row['tests']['testCount']==8 and row['nativeExecuted']is False,'Typed exact preflight differs')
 for path,h in row['inputFiles'].items():require(sha(path)==h,'Frozen consumed R29 source changed')
 check_pin(row['tests']['log']);return row


def actors(u):return {a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}


def grove_controls(u,bundle,h,skip_target=False):
 scene=actors(u);groups={}
 for row in bundle['fullness']['canopyPlacements']:
  name=f'EX_regional_{int(row["positionCm"][0]//5000)}_{int(row["positionCm"][1]//5000)}_{row["meshId"]}_{row["cullEndCm"]}';groups.setdefault(name,[]).append(row)
 require(len(groups)==23,'Original23 grove groups required');result={}
 for label,rows in groups.items():
  if skip_target and label==guard.GROUP:continue
  matches=[(path,a)for path,a in scene.items()if a.get_actor_label()==label];require(len(matches)==1,'Original grove group identity ambiguous')
  path,a=matches[0];c=a.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
  require(c and c.get_instance_count()==len(rows),'Original grove membership changed')
  values=[h['tree'].transform_value(h['tree'].instance_value(c,i))for i in range(len(rows))]
  require(digest(values)==bundle['base']['witness'][path]['components'][0]['orderedInstanceTransformsSha256'],'Original grove ordered Transform differs')
  for value,row in zip(values,rows):exact(value[0],row['positionCm'],'Original native root differs from selected source')
  result[path]={'rootIds':[r['id']for r in rows],'recoveredValues':values,'storedMatrices':[h['tree'].matrix(c,i)for i in range(len(rows))],
   'mainRandomSeed':int(c.get_editor_property('instancing_random_seed')),'numCustomDataFloats':int(c.get_editor_property('num_custom_data_floats')),
   'customData':[float(v)for v in c.get_editor_property('per_instance_sm_custom_data')],'additionalRandomSeedsReadbackAvailable':False,'seedRangesReconstructed':False}
 require(sum(len(r['rootIds'])for r in result.values())==(74 if skip_target else 78),'Exact original grove root census differs');return result


def measure(u,bundle,h,c):
 require(c.get_instance_count()==4 and c.get_editor_property('num_custom_data_floats')==0 and not c.get_editor_property('per_instance_sm_custom_data'),'Whole target4/custom-data scope differs')
 original=[h['tree'].instance_value(c,i)for i in range(4)];values=[]
 for root,old in zip(bundle['roots'],original):
  exact(h['tree'].vec(old.translation),root['originalSourceRow']['positionCm'],'Exact original selected source root differs')
  value=u.Transform();offset=root['fit']['nativeInstanceOriginOffsetCm'];xyz=[a+b for a,b in zip(h['tree'].vec(old.translation),offset)]
  value.set_editor_property('translation',u.Vector(*xyz));value.set_editor_property('rotation',old.rotation);value.set_editor_property('scale3d',u.Vector(*([root['fit']['uniformScale']]*3)))
  exact(h['tree'].vec(value.rotation,'xyzw'),h['tree'].vec(old.rotation,'xyzw'),'Wrapped original quaternion changed');exact(h['tree'].vec(value.translation),xyz,'Exact root/common-bottom shift changed');values.append(value)
 transient=u.new_object(u.HierarchicalInstancedStaticMeshComponent);require(transient and list(transient.add_instances(values,True,False,False))==list(range(4)),'Faithful unregistered4 native measurements failed')
 measurement={'rootIds':guard.IDS,'inputValues':[h['tree'].transform_value(v)for v in values],
  'recoveredValues':[h['tree'].transform_value(h['tree'].instance_value(transient,i))for i in range(4)],'storedMatrices':[h['tree'].matrix(transient,i)for i in range(4)],
  'nativeUnregisteredTransientMeasurement':True,'originalXYZAndWrappedRotationCopied':True,'oldActorOrMemberMutatedDuringMeasurement':False,
  'nativeMatrixProjectionIsGpuReadback':False,'normalTangentNativeReadbackAvailable':False}
 return values,measurement


def footprint(bundle,h,measurement):
 result=[]
 for root,matrix in zip(bundle['roots'],measurement['storedMatrices']):
  adapted=copy.copy(bundle['donor']['sourceBundle']);adapted['selection']={'originalSourceRow':root['originalSourceRow'],'newActorProposal':{'authoredHeightCm':root['originalSourceRow']['heightCm']}}
  result.append({'rootId':root['rootId'],**h['tree'].actual_matrix_footprint(adapted,matrix,root['originalSourceRow']['positionCm'])})
 require(sum(r['decodedFullOriginalVertices']for r in result)==7109112,'Full4 original source positions required');return result


def base_materials(u,bundle,h):
 clean=h['cleanNative'].verify_materials(u,h['cleanBundle'],h)
 for row in bundle['base']['report']['newMaterials']:
  material=u.EditorAssetLibrary.load_asset(row['asset']);require(material and h['existing'].graph_snapshot(u,material)==row['graph']
   and h['foreground'].world_position_offsets(u,material)==row['worldPositionOffsets'],'Original yard PBR graph/world-position modes changed')
 return {'clean':clean,'yard':bundle['base']['report']['newMaterials'],'scopedMaterialGraphs':56,'scopedTextureObjects':77}


def apply(u,bundle,h,old_c,values,mesh):
 # No retained members: no RemoveAtSwap/reorder/restoration or seed setter.
 old_c.clear_instances();old_c.get_owner().synchronize_instance_bounds();require(old_c.get_instance_count()==0,'Whole target4 were not retired')
 a=u.get_editor_subsystem(u.EditorActorSubsystem).spawn_actor_from_class(u.load_class(None,'/Script/BreziTwin.BreziVegetationPatch'),u.Vector(0,0,0),u.Rotator());require(a,'Cannot spawn one own4-tree actor')
 a.tags=[u.Name('BreziGenerated'),u.Name(guard.TAG)];a.set_actor_label(guard.LABEL);a.set_folder_path('Brezi/OriginalTreeGroup20261002R29');a.set_actor_tick_enabled(False)
 c=a.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent);require(c and a.get_editor_property('root_component')==c and c.get_owner()==a,'New own root HISM unavailable')
 h['rural'].new_component_policy(u,c);require(c.set_static_mesh(mesh),'Cannot bind byte-exact saved original mesh');c.set_editor_property('cast_shadow',True);c.set_editor_property('visible_in_ray_tracing',True);c.set_editor_property('disallow_nanite',False)
 c.set_cull_distances(*bundle['base']['targetWitness']['components'][0]['instanceCullCm']);a.set_detail_density_scaling(False)
 require(list(c.add_instances(values,True,False,False))==list(range(4)),'Only unique ordered4 existing roots may add');a.synchronize_instance_bounds();return a.get_path_name()


def verify(u,bundle,h,new_actor,measurement):
 scene=actors(u);require({p for p,a in scene.items()if a.actor_has_tag(guard.TAG)}=={new_actor},'New owner actor scope widened')
 old=scene[bundle['base']['targetActor']].get_component_by_class(u.HierarchicalInstancedStaticMeshComponent);require(old and old.get_instance_count()==0,'Retired original whole group reappeared')
 c=scene[new_actor].get_component_by_class(u.HierarchicalInstancedStaticMeshComponent);require(c and c.get_instance_count()==4,'Exact new4 group missing')
 exact([h['tree'].transform_value(h['tree'].instance_value(c,i))for i in range(4)],measurement['recoveredValues'],'Saved measured recovered transforms differ')
 exact([h['tree'].matrix(c,i)for i in range(4)],measurement['storedMatrices'],'Saved measured FMatrix differs')
 expected=guard.empty_original(bundle['base']['witness'],bundle['base']['targetActor']);expected[new_actor]=guard.added_expected(bundle['donor']['template'],bundle['donor']['templateActor'],new_actor,measurement,bundle['base']['targetWitness']['components'][0]['instanceCullCm'])
 witness=h['cleanNative'].full_witness(u,h);require(witness==expected and len(witness)==5351,'Full old5350 plus declared source-template actor counterfactual differs')
 hisms=[c for a in witness.values()for c in a['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent'];require(len(hisms)==2313 and sum(c['instanceCount']for c in hisms)==676957,'Full HISM census differs')
 return witness


def main():
 import unreal as u
 output=guard.CANDIDATE;project=output/'Project/BreziTwin';require(Path(os.environ['BREZI_ORIGINAL_TREE_GROUP_OUTPUT']).resolve()==output
  and Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project,'Only own prepared R29 may change')
 require(not(output/REPORT).exists()and not(output/'exterior-import-report.json').exists(),'Fresh own typed report required')
 plan,bundle=guard.validate_plan();require(pin(guard.PLAN)['sha256']==os.environ['BREZI_ORIGINAL_TREE_GROUP_PLAN_SHA256'],'Selected frozen plan differs')
 preflight_path=Path(os.environ['BREZI_ORIGINAL_TREE_GROUP_PREFLIGHT']).resolve();preflight0=validate_preflight(preflight_path,plan)
 require(sha(preflight_path)==os.environ['BREZI_ORIGINAL_TREE_GROUP_PREFLIGHT_SHA256'],'Exact selected preflight differs')
 clone,copied,initial_content=validate_clone(plan,bundle);h=helpers(bundle);require(h['moduleOrderWitness']==preflight0['moduleOrderWitness'],'Frozen-first actual saved policy order differs')
 checkpoint=output/'tree-group-checkpoint';require(not checkpoint.exists(),'Fresh own checkpoint required');checkpoint.mkdir()
 module=project/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib';source_module=guard.BASE/'Project/BreziTwin/Binaries/Mac/libUnrealEditor-BreziTwin.dylib'
 require(sha(module)==sha(source_module)=='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574','Protected module bytes changed')
 report={'schema':guard.SCHEMA,'owner':OWNER,'status':'running','startedAt':now(),'nativeProcessId':os.getpid(),'output':str(output),'project':str(project),
  'selectedPlan':pin(guard.PLAN),'sourceProposal':plan['sourceProposal'],'baseNativeReport':plan['baseNativeReport'],'savedTreeDonor':plan['savedTreeDonor'],'sourcePreflight':pin(preflight_path),
  'projectClone':clone,'packageCopyReceipt':copied,'inputFiles':preflight0['inputFiles'],'activeDesign':plan['activeDesign'],'setbacksMm':plan['setbacksMm'],'moduleOrderWitness':h['moduleOrderWitness'],
  'nativeModuleWitness':{'source':str(source_module),'destination':str(module),'sha256':sha(module),'bytes':module.stat().st_size,'independentInodes':source_module.stat().st_ino!=module.stat().st_ino},
  'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'ecologicalFitVerified':False,'shippingVerified':False,'packageVerified':False,
  'nativeNormalTangentReadbackAvailable':False,'nativeMaterialPackagesIndependentlyUnloaded':False,'nativeMeshPackagesIndependentlyUnloaded':False,'selectedTreeNaniteRenderPassVerified':False,
  'AdditionalRandomSeedsReadbackAvailable':False,'seedRangeReconstructionPerformed':False,'retainedMemberReconstructionPerformed':False,'sourceRootGroundElevationSurveyed':False}
 report_write(output/REPORT,report)
 try:
  levels=u.get_editor_subsystem(u.LevelEditorSubsystem);require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot load own exact saved R28b map')
  before=h['cleanNative'].full_witness(u,h);require(before==bundle['base']['witness'],'Actual entire old5350 actor scene differs')
  materials_before=base_materials(u,bundle,h);grass_before=h['cleanNative'].original_grass_controls(u,h['cleanBundle']);grove_before=grove_controls(u,bundle,h)
  tree_materials=h['treeMaterials'].verify_materials(u,bundle['donor']['report']['materials'],h['existing'].graph_snapshot)
  mesh=u.EditorAssetLibrary.load_asset(bundle['donor']['report']['newMesh']);require(mesh,'Exact copied saved donor mesh missing')
  source_geometry=h['tree'].native_mesh_proof(u,mesh,bundle['donor']['preflight']);require(source_geometry==bundle['donor']['report']['nativeSourceGeometry'],'Copied original mesh/native sample/full census differs')
  require([mesh.get_material(i).get_path_name()for i in range(3)]==[r['asset']for r in bundle['donor']['report']['materials']['materials'].values()],'Saved original3 material bindings differ')
  nanite=h['tree'].nanite_readback(mesh);require(nanite==bundle['donor']['report']['naniteResourceReadback'],'Copied Nanite resource inputs differ')
  old_actor=actors(u)[bundle['base']['targetActor']];old_c=old_actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
  values,measurement=measure(u,bundle,h,old_c);footprints=footprint(bundle,h,measurement)
  new_actor=apply(u,bundle,h,old_c,values,mesh);expected=verify(u,bundle,h,new_actor,measurement)
  remaining_before={k:v for k,v in grove_before.items()if k!=bundle['base']['targetActor']};exact(grove_controls(u,bundle,h,True),remaining_before,'All remaining74 original raw matrices/controls differ')
  for name,value in [('before-actor-witness',before),('expected-actor-witness',expected),('native-source-measurements',measurement),('remaining74-before',remaining_before),('materials-before',materials_before)]:guard.write(checkpoint/(name+'.json'),value)
  require(levels.save_current_level(),'Cannot save own four-tree trial');require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot unload/reload saved trial')
  saved=verify(u,bundle,h,new_actor,measurement);require(saved==expected,'Saved source-template scene differs')
  remaining_saved=grove_controls(u,bundle,h,True);exact(remaining_saved,remaining_before,'Remaining74 stored matrices/recovered frames/mainseed/customdata changed after reload')
  materials_saved=base_materials(u,bundle,h);require(materials_saved==materials_before,'Existing56 graphs77 textures changed')
  h['treeMaterials'].verify_materials(u,bundle['donor']['report']['materials'],h['existing'].graph_snapshot)
  require(h['tree'].native_mesh_proof(u,mesh,bundle['donor']['preflight'])==source_geometry and h['tree'].nanite_readback(mesh)==nanite,'Saved original source mesh/Nanite resources changed')
  exact(h['cleanNative'].original_grass_controls(u,h['cleanBundle']),grass_before,'All original8949 grass raw controls changed')
  content=guard.g.inventory(project/'Content');delta=guard.validate_content(bundle['content'],content,bundle['packages'])
  require(guard.g.project_proof(project)==bundle['protected']and guard.g.inventory(guard.BASE/'Project/BreziTwin/Content')==bundle['content']and guard.g.project_proof(guard.BASE/'Project/BreziTwin')==bundle['protected'],'Protected/actual saved base bytes changed')
  for path,h0 in preflight0['inputFiles'].items():require(sha(path)==h0,'Consumed frozen source changed')
  for name,value in [('saved-actor-witness',saved),('remaining74-saved',remaining_saved),('materials-saved',materials_saved),('after-content-inventory',content)]:guard.write(checkpoint/(name+'.json'),value)
  report.update(status=STATUS,completedAt=now(),nativeApplied=True,savedMapUnloadedReloaded=True,originalSavedR28bUnchanged=True,sourceInputsUnchanged=True,
   actualCounts=plan['expectedCounts'],retiredOriginalGroup={'actor':bundle['base']['targetActor'],'groupId':guard.GROUP,'retiredSourceRootIds':guard.IDS,'retiredMembers':4,'remainingMembers':0,'actorComponentKept':True},
   newOriginalTreeGroup={'actor':new_actor,'rootIds':guard.IDS,'instances':4,'mesh':mesh.get_path_name(),'materialAssets':[m.get_path_name()for m in tree_materials.values()],
     'measurement':pin(checkpoint/'native-source-measurements.json'),'orderedMeasuredTransformAndStoredMatrixSavedExact':True,'nativeStoredMatrixFullVertexMasks':footprints},
   originalRemaining74RawMatricesAndObservedControlsExact=True,original8949GrassRawControlsExact=True,
   beforeActorWitness=pin(checkpoint/'before-actor-witness.json'),expectedActorWitness=pin(checkpoint/'expected-actor-witness.json'),savedActorWitness=pin(checkpoint/'saved-actor-witness.json'),
   beforeActorWitnessSha256=digest(before),expectedActorWitnessSha256=digest(expected),savedActorWitnessSha256=digest(saved),
   remaining74Before=pin(checkpoint/'remaining74-before.json'),remaining74Saved=pin(checkpoint/'remaining74-saved.json'),
   originalMaterialsBefore=pin(checkpoint/'materials-before.json'),originalMaterialsSaved=pin(checkpoint/'materials-saved.json'),
   baseContentInventory=plan['baseContentInventory'],afterContentInventory=pin(checkpoint/'after-content-inventory.json'),protectedProjectProof=plan['baseProjectProof'],assetDelta=delta,
   nativeSourceGeometry=source_geometry,naniteResourceReadback=nanite,copiedPackages=plan['copiedPackages'],materialGraphAssets=59,textureAssets=87,
   sourceInputTrianglesAcross4Instances=8249948,actualRuntimeDrawnTreeTriangleCountMeasured=False)
  report_write(output/REPORT,report);print(json.dumps({'report':pin(output/REPORT),'status':STATUS,'nativeAppearanceAccepted':False}))
 except Exception as error:
  report.update(status='failed',error=str(error),completedAt=now());report_write(output/REPORT,report);raise


if __name__=='__main__':
 if '--preflight'in sys.argv:
  parser=argparse.ArgumentParser();parser.add_argument('--preflight',type=Path,required=True);preflight(parser.parse_args().preflight)
 else:main()
