"""Root-only integration of selected saved R36b garden and fourteen yard packages.

No imports, source pixel edits, donor map loads or quaternion/matrix reconstruction.
Original constructor replay is meshless/unowned; all three saved arrays must match
before any original mutation. New HISM data receives those actual wrapped structs.
"""
import argparse
from datetime import datetime,timezone
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-garden-yard-integration-native-r37-r2.py'
s=importlib.util.spec_from_file_location('r37_actual_selected_scope',ROOT/'scripts/unreal/exterior-garden-yard-integration-guards-r37-r2.py')
guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard)
MAP='/Game/Brezi/Maps/Brezi'
REPORT='garden-yard-integration-native-report-r2.json'
STATUS='verified-saved-clean-selected-garden-and-yard-integration'
MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574'
require,read,pin,sha,write,digest=(getattr(guard,k)for k in ('require','read','pin','sha','write','digest'))
def now():return datetime.now(timezone.utc).isoformat()
def report_write(path,row):Path(path).write_text(json.dumps(row,indent=2,allow_nan=False)+'\n')


def helpers(plan,bundle):
 # Must establish the immutable policy cache before importing dependent kernels.
 clean_plan=read(guard.checked(plan['frozenFirstHelperEvidence']))
 clean=guard.module('r37_frozen_first_clean_native',clean_plan['ownedSources']['native']['live'])
 clean_bundle=clean.guard.load_donors();h=clean.helpers(clean_bundle)
 h.update(cleanNative=clean,cleanBundle=clean_bundle,r21=h['foreground'])
 for key,donor in (('r32',bundle['donors']['reports']['yardR32']),('r35',bundle['donors']['reports']['yardRepairR35'])):
  path=ROOT/donor['owner'];require(donor['inputFiles'][str(path)]==sha(path),'Actual saved donor kernel changed')
  h[key]=guard.module('r37_scoped_'+key+'_kernels',pin(path))
 h['meshHelper']=h['r32'].guard.static_mesh_api()
 h['yardMaterials']=guard.module('r37_two_copied_materials',pin(ROOT/'scripts/unreal/exterior-context-yard-ground-materials-r32.py'))
 h['backdropMaterials']=guard.module('r37_one_copied_material',pin(ROOT/'scripts/unreal/exterior-context-yard-repair-materials-r35.py'))
 h['treeMaterials']=guard.module('r37_r2_original_tree_reader',pin(ROOT/'scripts/unreal/exterior-original-tree-materials.py'))
 guard.checked(plan['synchronizeInstanceBoundsSource'])
 return h


def validate_project(bundle,h,after=False):
 project=guard.CANDIDATE/'Project/BreziTwin';g=h['cleanNative'].guard.g
 content=g.inventory(project/'Content');protected=g.project_proof(project)
 require(protected==bundle['protected']and g.inventory(bundle['project']/'Content')==bundle['content']
         and g.project_proof(bundle['project'])==bundle['protected'],'Selected original or132 protected project bytes changed')
 delta=bundle['draftSource'].validate_packages(bundle['content'],bundle['preparedContent'],content,bundle['donors'])
 if not after:require(content==bundle['preparedContent'],'Fresh prepared candidate differs before native')
 for row in bundle['donors']['inventory']['packages']:
  source=guard.checked(row['source']);own=project/'Content'/row['relativeContentPath']
  require(sha(own)==row['source']['sha256']and own.stat().st_size==row['source']['bytes']
          and (source.stat().st_dev,source.stat().st_ino)!=(own.stat().st_dev,own.stat().st_ino),
          'Every copied saved package must remain byte-exact and independently owned')
 return content,delta


def _raw_control(u,actor,bundle,h,witness,expected=None):
 row=witness[actor];require(len(row['components'])==1,'Unique raw-control component required')
 c=h['cleanNative'].component_lookup(u,actor,row['components'][0]['name'])
 got=bundle['draftNative'].control(c,h)
 require(digest(got['recoveredValues'])==row['components'][0]['orderedInstanceTransformsSha256'],
         'Raw recovered control must bind the actual full scene witness')
 if expected is not None:
  bundle['draftSource'].exact(got['recoveredValues'],expected['recoveredValues'],'Protected original recovered frames differ')
  bundle['draftSource'].exact(got['storedMatrices'],expected['storedMatrices'],'Protected original raw matrices differ')
  for key in ('mainRandomSeed','numCustomDataFloats','customData'):
   if key in expected:require(got[key]==expected[key],'Protected main seed/custom data changed')
 return got


def protected_controls(u,bundle,h,witness):
 # All existing garden/fern/78 tree/shrub raw fields are read only.
 r=bundle['report'];recorded=read(guard.checked(r['originalProtectedControlsSaved']))
 controls={};trees=recorded['originalTrees'];targets=dict(trees['original74'])
 r29=read(ROOT/'output/unreal/exterior-20261002-r29a/original-tree-group-native-report.json')
 targets[r29['newOriginalTreeGroup']['actor']]=trees['ownedR29Four']
 require(sum(len(v['recoveredValues'])for v in targets.values())==78,'All78 original tree controls required')
 targets.update(read(guard.checked(r['retainedGardenControlsSaved'])))
 targets.update(recorded['preserved36FernControls'])
 measurements=read(guard.checked(r['newSourceNativeMeasurements']))
 for model,row in r['newOwnedGroups'].items():targets[row['actor']]=measurements[model]
 old_yard=read(guard.checked(bundle['donors']['reports']['yardRepairR35']['originalControlsSaved']))['all13YardShrubsAnd1274LowRootsRawControls']
 shrubs={p:v for p,v in old_yard.items()if p in witness and witness[p]['label'].startswith('EX_context_yard_r28_')}
 require(len(shrubs)==3 and sum(v['instanceCount']for v in shrubs.values())==13,'All13 retained yard shrubs required')
 targets.update(shrubs)
 for actor,expected in targets.items():controls[actor]=_raw_control(u,actor,bundle,h,witness,expected)
 grass=h['cleanNative'].original_grass_controls(u,h['cleanBundle'])
 require(grass==recorded['original8949Grass'],'All8949 original grass raw matrix/mainseed/custom controls differ')
 return {'rawActorControls':controls,'original8949Grass':grass,'all78TreeRoots':78,
         'retained12Heroes41Flowers':53,'original36Ferns':36,'originalPeriwinkleRoots':384,
         'original13YardShrubs':13,'additionalRandomSeedRangesReadbackAvailable':False,
         'perInstanceShaderRandomValuePreservationClaimed':False}


def _material_records(value,graphs,textures):
 if isinstance(value,dict):
  asset=value.get('asset');graph=value.get('graph')
  if asset and (graph is not None or 'graphSha256'in value):
   record={'sha256':digest(graph)if graph is not None else value['graphSha256']}
   if graph is not None:record['graph']=graph
   if 'usage'in value:record['usage']=value['usage']
   if asset in graphs:require(graphs[asset]['sha256']==record['sha256'],'Conflicting recorded material graph identity')
   graphs[asset]=record
  if asset and '/Textures/'in asset:textures.add(asset)
  if 'verifiedTextureAssets'in value:textures.update(value['verifiedTextureAssets'])
  for v in value.values():_material_records(v,graphs,textures)
 elif isinstance(value,list):
  for v in value:_material_records(v,graphs,textures)


def selected_graph_snapshot(u,material,asset,bundle,h):
 routes=guard.reader_dispatch(bundle)
 require(material.get_path_name()==asset,'Exact selected material object/path required')
 selected=[route for route,assets in routes.items()if asset in assets]
 require(len(selected)==1,'Only explicit selected61 material assets may choose a reader')
 route=selected[0]
 if route=='neighbor':graph=h['neighborMaterial'].graph_snapshot(u,material,h['existing'].graph_snapshot)
 elif route=='tree':graph=h['treeMaterials'].graph_snapshot(u,material,h['existing'].graph_snapshot)
 else:graph=h['existing'].graph_snapshot(u,material)
 return graph,route


def graph_differences(expected,actual,path=''):
 if type(expected)is not type(actual):return [{'path':path,'expectedType':type(expected).__name__,'actualType':type(actual).__name__}]
 if isinstance(expected,dict):
  result=[{'path':path+'/'+str(k),'expectedKeyPresent':k in expected,'actualKeyPresent':k in actual}for k in set(expected)^set(actual)]
  for key in sorted(set(expected)&set(actual)):result.extend(graph_differences(expected[key],actual[key],path+'/'+str(key)))
  return result
 if isinstance(expected,list):
  if len(expected)!=len(actual):return [{'path':path,'expectedLength':len(expected),'actualLength':len(actual)}]
  return [v for i,(a,b)in enumerate(zip(expected,actual))for v in graph_differences(a,b,path+'/'+str(i))]
 return []if expected==actual else[{'path':path,'expected':expected,'actual':actual}]


def compare_recorded_graph(asset,expected,actual,route,source_pin,directory,index):
 """Write complete observed graph/route/source expectation BEFORE rejection."""
 observed=digest(actual);differences=graph_differences(expected['graph'],actual)if'graph'in expected else None
 record={'schema':guard.REPAIR_SCHEMA,'asset':asset,'reader':route,'expectedPinnedSource':source_pin,
         'recordedExpectedGraphSha256':expected['sha256'],'actualCompleteGraphSha256':observed,
         'recordedExpectedCompleteGraph':expected.get('graph'),'actualCompleteGraph':actual,
         'completeRecordedGraphShapeAvailable':'graph'in expected,'fullGraphDifferences':differences,
         'nativeGraphAcceptanceGranted':False}
 write(directory/('graph-'+str(index).zfill(3)+'.json'),record)
 require(observed==expected['sha256']and('graph'not in expected or actual==expected['graph']),
         'Original selected full material graph changed: '+asset+' reader='+route)
 return observed


def material_graph_diagnostic_files(checkpoint):
 return {phase:[pin(path)for path in sorted((checkpoint/('material-graphs-'+phase)).glob('graph-*.json'))]
         for phase in ('before','saved')}


def material_readback(u,bundle,h,packet,checkpoint):
 recorded=read(guard.checked(bundle['report']['originalProtectedControlsSaved']))
 graphs={};textures=set();_material_records(recorded,graphs,textures)
 _material_records(bundle['report']['materialReport'],graphs,textures)
 require(len(graphs)==61 and len(textures)==96,'Actual selected base scoped61 graphs96 textures required')
 require(not checkpoint.exists(),'Exclusive before/saved graph diagnostic directory required');checkpoint.mkdir()
 result={}
 for index,(asset,expected)in enumerate(graphs.items()):
  m=u.EditorAssetLibrary.load_asset(asset);require(isinstance(m,u.Material),'Actual protected material missing')
  graph,route=selected_graph_snapshot(u,m,asset,bundle,h)
  source_pin=bundle['reportPin']if asset==bundle['report']['materialReport']['asset']else bundle['report']['originalProtectedControlsSaved']
  observed=compare_recorded_graph(asset,expected,graph,route,source_pin,checkpoint,index)
  if 'usage'in expected:
   wanted=expected['usage'];got={key:bool(u.MaterialEditingLibrary.has_material_usage(m,
      h['existing'].native_enum(u.MaterialUsage,'INSTANCEDSTATICMESHES')if key=='instancedStaticMeshes'else u.MaterialUsage.MATUSAGE_NANITE))for key in wanted}
   require(got==wanted,'Original recorded native material usage changed')
  result[asset]={'graphSha256':observed,'originalGraphExact':True,'reader':route}
 for asset in textures:
  t=u.EditorAssetLibrary.load_asset(asset);require(isinstance(t,u.Texture2D)and t.get_path_name()==asset,'Original scoped native Texture2D missing')
 r32=bundle['donors']['reports']['yardR32'];r35=bundle['donors']['reports']['yardRepairR35']
 originals={key:u.EditorAssetLibrary.load_asset(recipe['duplicateSource'])for key,recipe in zip(('context_track','context_garden_soil'),packet['recipes'])}
 h['yardMaterials'].verify_saved(u,h,packet['recipes'],originals,r32['newMaterialReport'])
 h['backdropMaterials'].verify_saved(u,h,packet['material'],r35['repairC']['materialReport'])
 for row in r32['newMaterialReport']['materials'].values():result[row['asset']]={'graphSha256':row['graphSha256'],'exactSavedDonorGraph':True}
 row=r35['repairC']['materialReport'];result[row['asset']]={'graphSha256':row['graphSha256'],'exactSavedDonorGraph':True}
 require(len(result)==64,'Exactly64 scoped actual material graphs required')
 return {'graphs':result,'textureAssets':sorted(textures),'scopedMaterialGraphs':len(result),'scopedTextureObjects':len(textures),
         'originalTexturePackageBytesProtected':True,'all96NativeTextureSettingsRecomputed':False,
         'sharedNewYardTextureSettingsVerified':True,'newTextureObjects':0,'materialPackagesIndependentlyUnloaded':False}


def geometry_readback(u,bundle,h,packet):
 donors=bundle['donors'];r32=donors['reports']['yardR32'];r35=donors['reports']['yardRepairR35']
 meshes={**r32['newMeshes'],**r35['newMeshes']};proofs={}
 for identity,source in packet['groundRecords'].items():
  mesh=u.EditorAssetLibrary.load_asset(meshes[identity]);require(mesh,'Copied saved ground mesh missing')
  proof=h['r32'].native_mesh_proof(u,mesh,source,h)
  recorded=(r35['repairB']['hardMeshProofs'].get(identity)or next(v for v in r32['savedReadback']['meshProofs']if v['mesh']==meshes[identity]))
  require(proof==recorded,'Full copied native ground corners differ from source and actual saved donor')
  expected_material=r32['newMaterialReport']['materials']['yard_substrate_r32'if source['role']=='yard_substrate'else'yard_gravel_r32']['asset']
  require(len(mesh.get_editor_property('static_materials'))==1 and mesh.get_material(0).get_path_name()==expected_material,
          'Copied ground default material slot changed')
  proofs[identity]=proof
 require(sum(v['triangles']for v in proofs.values())==32878,'All32878 actual copied ground triangle corners required')
 ecology=h['r35'].native_ecology_geometry(u,packet['ecology'],h)
 require(ecology==r35['repairA']['nativeSelectedEcologyGeometry'],'All24 original ecology LODs5220 corner/section identities differ')
 vertices=h['r32'].native_master_vertices(u,packet['ground'],h)
 footprints=h['r32'].verify_footprints(packet['ground'],donors['r32Measurements'],vertices)
 require(len(footprints)==1274,'All1274 existing-master complete three-LOD source-mask fits required')
 for model,group in donors['yardGroups'].items():
  mesh=u.EditorAssetLibrary.load_asset(group['template']['components'][0]['mesh'])
  require(mesh.get_material(0).get_path_name()==group['template']['components'][0]['materials'][0],
          'Unchanged shared plant master/default material binding differs')
 return {'ground':proofs,'originalEcology':ecology,'newLowRootFootprints':footprints,
         'all1274ContainingCirclesAndNativeThreeLodVerticesInsideSourceMasks':True,
         'nativeNormalTangentReadbackAvailable':False}


def apply_declared_scene(u,plan,bundle,h,before,checkpoint,packet):
 g,kernels,donors=bundle['draftSource'],bundle['draftNative'],bundle['donors']
 require(before==bundle['before'],'Actual selected original full scene differs')
 # All three arrays are compared BEFORE old component changes or retirement.
 wrapped,replay,keep_alive=kernels.replay_wrapped_source_rows(u,donors,h)
 write(checkpoint/'native-constructor-replay.json',replay)
 ecology=kernels.original_ecology_control(u,donors,h)
 freshness=[v for key,group in packet['ecology']['ecologyGroups'].items()
            for v in h['r35'].guard.native_support_checks(ecology[key],group,packet['ecology'])]
 require(len(freshness)==34,'Every exact original retirement must still intersect declared hard source support')
 write(checkpoint/'retirement-source-support.json',freshness)
 require(h['cleanNative'].full_witness(u,h)==before,'Unregistered replay changed original candidate scene')
 kernels.apply_original_component_changes(u,donors,h)
 removed=kernels.retire_exact_original_members(u,donors,h,ecology)
 mapping,raw,declared_new=kernels.spawn_fresh_templates(u,before,donors,wrapped,h)
 expected=g.expected_scene(before,donors,mapping)
 require({p:expected[p]for p in mapping.values()}==declared_new,'New expected actors must come from immutable templates')
 actual=h['cleanNative'].full_witness(u,h);require(actual==expected,'Whole candidate scene differs outside declared scope')
 kernels.verify_new_raw_groups(u,donors,h,mapping)
 require(len(keep_alive)==3,'All three replay components must live through wrapped transfer')
 return {'mapping':mapping,'expected':expected,'replay':replay,'newRawControls':raw,'retirementReadback':removed}


def verify_reloaded_scene(u,bundle,h,applied,packet):
 actual=h['cleanNative'].full_witness(u,h);require(actual==applied['expected'],'Saved whole source counterfactual differs')
 groups=bundle['draftNative'].verify_new_raw_groups(u,bundle['donors'],h,applied['mapping'])
 retained=h['r35'].captured_remaining_ecology(u,packet['ecology'],h,bundle['donors']['ecologyOriginal'])
 require(retained==bundle['donors']['ecologyRetained'],'All1919 original surviving raw structs/order/seed/custom differ')
 return actual,groups,retained


def input_files(plan):
 files={**plan['inputFiles'],str(guard.PLAN):sha(guard.PLAN)}
 require(all(sha(p)==v for p,v in files.items()),'Frozen consumed integration source changed')
 return files


def preflight(output):
 require(output==guard.STUDY/'source-preflight'and not output.exists(),'Fresh known R37 preflight output required')
 plan,bundle=guard.validate_plan();h=helpers(plan,bundle);guard.source_packet(bundle,h)
 content,_=validate_project(bundle,h);require(len(content)==4100,'Prepared actual4100 Content required')
 output.mkdir();receipt={'schema':guard.SCHEMA,'owner':OWNER,'status':'selected-garden-yard-source-preflight-validated-native-pending',
  'createdAt':now(),'selectedPlan':pin(guard.PLAN),'baseNativeReport':bundle['reportPin'],'projectClone':bundle['clone'],
  'inputFiles':input_files(plan),'moduleOrderWitness':h['moduleOrderWitness'],'cpuTests':plan['cpuTests'],
  'expectedCounts':plan['expectedCounts'],'nativeExecuted':False,'gpuExecuted':False,'nativeAppearanceAccepted':False,'performanceAccepted':False}
 write(output/'source-preflight.json',receipt);print(json.dumps({'preflight':pin(output/'source-preflight.json'),'sourcePins':len(receipt['inputFiles']),'nativeExecuted':False}))


def main():
 import unreal as u
 output=guard.CANDIDATE;project=output/'Project/BreziTwin'
 require(Path(os.environ['BREZI_GARDEN_YARD_OUTPUT']).resolve()==output and Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project,
         'Only exact owned R37 candidate may change')
 require(sha(guard.PLAN)==os.environ['BREZI_GARDEN_YARD_PLAN_SHA256'],'Frozen selected R37 plan differs')
 pf_path=Path(os.environ['BREZI_GARDEN_YARD_PREFLIGHT']).resolve()
 require(pf_path==guard.STUDY/'source-preflight/source-preflight.json'and sha(pf_path)==os.environ['BREZI_GARDEN_YARD_PREFLIGHT_SHA256'],'Frozen preflight differs')
 require(not(output/REPORT).exists()and not(output/'exterior-import-report.json').exists(),'Fresh typed integration report required')
 plan,bundle=guard.validate_plan();h=helpers(plan,bundle);pf=read(pf_path)
 require(pf['schema']==guard.SCHEMA and pf['owner']==OWNER and pf['status']=='selected-garden-yard-source-preflight-validated-native-pending'
  and pf['selectedPlan']==pin(guard.PLAN)and pf['baseNativeReport']==bundle['reportPin']and pf['projectClone']==bundle['clone']
  and pf['inputFiles']==input_files(plan)and pf['moduleOrderWitness']==h['moduleOrderWitness']and pf['cpuTests']==plan['cpuTests']
  and pf['nativeExecuted']is False,'Exact executed source preflight required')
 content_before,_=validate_project(bundle,h);packet=guard.source_packet(bundle,h)
 module=project/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib';origin=bundle['project']/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'
 require(sha(module)==sha(origin)==MODULE_SHA and read(project/'Binaries/Mac/UnrealEditor.modules')['BuildId']=='55116800','Original Recipe4 module/build identity differs')
 checkpoint=output/'garden-yard-checkpoint';require(not checkpoint.exists(),'Fresh checkpoint only');checkpoint.mkdir()
 report={'schema':guard.SCHEMA,'schemaVersion':2,'owner':OWNER,'status':'running','startedAt':now(),'nativeProcessId':os.getpid(),
  'repairSchema':guard.REPAIR_SCHEMA,'priorFailedAttempt':plan['priorFailedAttempt'],'materialReaderDispatch':plan['materialReaderDispatch'],
  'output':str(output),'project':str(project),'selectedPlan':pin(guard.PLAN),'sourcePreflight':pin(pf_path),
  'baseNativeReport':bundle['reportPin'],'baseNativeProcess':bundle['process'],'baseCurrentByteAudit':bundle['audit'],
  'selectedRootReview':bundle['review'],'donorInventory':pin(bundle['draftSource'].INVENTORY),'projectClone':bundle['clone'],
  'baseContentInventory':bundle['report']['afterContentInventory'],'protectedProjectProof':bundle['report']['protectedProjectProof'],
  'inputFiles':pf['inputFiles'],'moduleOrderWitness':h['moduleOrderWitness'],
  'nativeModuleWitness':{'source':str(origin),'destination':str(module),'sha256':sha(module),'bytes':module.stat().st_size,'independentInodes':True},
  'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,
  'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},'setbacksMm':{'street':3000,'east':3000},
  'wholeR35MapOrR30GardenImported':False,'materialPackagesIndependentlyUnloaded':False,'nativeNormalTangentReadbackAvailable':False,
  'AdditionalRandomSeedsReadbackAvailable':False,'perInstanceShaderRandomValuePreservationClaimed':False,'existingTransformOrSeedSetterUsed':False}
 report_write(output/REPORT,report)
 try:
  levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
  require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot load own selected garden map')
  before=h['cleanNative'].full_witness(u,h);require(before==bundle['before'],'Actual original selected full scene differs')
  controls_before=protected_controls(u,bundle,h,before);materials=material_readback(u,bundle,h,packet,checkpoint/'material-graphs-before');geometry=geometry_readback(u,bundle,h,packet)
  write(checkpoint/'before-actors.json',before);write(checkpoint/'protected-controls-before.json',controls_before)
  applied=apply_declared_scene(u,plan,bundle,h,before,checkpoint,packet)
  write(checkpoint/'expected-actors.json',applied['expected']);write(checkpoint/'new-groups-before-save.json',applied['newRawControls'])
  require(levels.save_current_level(),'Cannot save own integrated candidate map')
  require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot unload/reload saved integration map')
  saved,groups,retained=verify_reloaded_scene(u,bundle,h,applied,packet)
  controls_saved=protected_controls(u,bundle,h,saved)
  require(controls_saved==controls_before,'All protected selected garden/tree/grass/shrub native controls changed')
  require(material_readback(u,bundle,h,packet,checkpoint/'material-graphs-saved')==materials and geometry_readback(u,bundle,h,packet)==geometry,'Saved material/geometry/mask readback differs')
  counts=plan['expectedCounts'];cs=[c for row in saved.values()for c in row['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
  require((len(saved),len(cs),sum(c['instanceCount']for c in cs))==(counts['savedActors'],counts['fullHismComponents'],counts['fullHismInstances']),
          'Actual saved full actor/HISM/member census differs from declared counterfactual')
  content,delta=validate_project(bundle,h,after=True);require(len(content)==counts['contentFiles'],'Actual final Content count differs')
  require(all(sha(p)==v for p,v in pf['inputFiles'].items()),'Frozen source changed during native')
  for name,row in [('saved-actors',saved),('protected-controls-saved',controls_saved),('new-groups-saved',groups),('retained-ecology-saved',retained),('after-content',content)]:write(checkpoint/(name+'.json'),row)
  report.update(status=STATUS,completedAt=now(),nativeApplied=True,savedMapUnloadedReloaded=True,sourceInputsUnchanged=True,
   beforeActorWitness=pin(checkpoint/'before-actors.json'),expectedActorWitness=pin(checkpoint/'expected-actors.json'),savedActorWitness=pin(checkpoint/'saved-actors.json'),
   beforeActorWitnessSha256=digest(before),expectedActorWitnessSha256=digest(applied['expected']),savedActorWitnessSha256=digest(saved),
   protectedControlsBefore=pin(checkpoint/'protected-controls-before.json'),protectedControlsSaved=pin(checkpoint/'protected-controls-saved.json'),
   originalConstructorReplay=pin(checkpoint/'native-constructor-replay.json'),newGroupNativeControlsSaved=pin(checkpoint/'new-groups-saved.json'),
   retainedEcologySaved=pin(checkpoint/'retained-ecology-saved.json'),retirementSourceSupport=pin(checkpoint/'retirement-source-support.json'),
   newActorMapping=applied['mapping'],actualRemoveReadback=applied['retirementReadback'],materialReadback=materials,geometryReadback=geometry,
   materialGraphDiagnosticDirectories={'before':str(checkpoint/'material-graphs-before'),'saved':str(checkpoint/'material-graphs-saved')},
   materialGraphDiagnosticFiles=material_graph_diagnostic_files(checkpoint),
   afterContentInventory=pin(checkpoint/'after-content.json'),assetDelta=delta,actualCounts=counts,
   newPackages=[r['asset']for r in bundle['donors']['inventory']['packages']],originalSelectedGardenUnchanged=True,
   all384Periwinkle36Ferns12Heroes41FlowersRawControlsExact=True,all78Trees8949GrassAnd13YardShrubsRawControlsExact=True,
   all1274ConstructorInputRecoveredStoredMatricesBinary64Exact=True,all1919SurvivorRawMatricesOrderMainSeedCustomDataExact=True)
  report_write(output/REPORT,report);print(json.dumps({'report':pin(output/REPORT),'status':STATUS,'nativeAppearanceAccepted':False}))
 except Exception as error:
  report.update(status='failed',completedAt=now(),error=str(error),
                materialGraphDiagnosticFiles=material_graph_diagnostic_files(checkpoint))
  report_write(output/REPORT,report);raise


if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--preflight',type=Path);args=parser.parse_args()
 if args.preflight:preflight(args.preflight.resolve())
 else:main()
