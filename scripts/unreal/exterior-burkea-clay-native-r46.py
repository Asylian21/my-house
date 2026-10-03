"""Root-only combined material pilot; exactly five existing component setters."""
import argparse, copy, io, json, os, subprocess, sys, unittest
from datetime import datetime,timezone
from pathlib import Path
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
import importlib.util
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
g=module('_r46_guard',ROOT/'scripts/unreal/exterior-burkea-clay-guards-r46.py')
require,read,write,pin,sha,digest,exact=(getattr(g,k)for k in ('require','read','write','pin','sha','digest','exact'))
OWNER='scripts/unreal/exterior-burkea-clay-native-r46.py'
REPORT='combined-material-native-report-r46.json'
STATUS='verified-saved-five-slot-burkea-and-clay-roof-material-pilot'
MAP='/Game/Brezi/Maps/Brezi'
TEST_COUNT=10
LIMITS={'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,
    'shippingVerified':False,'activeOutputPromoted':False,'physicalLeafOrRoofOpticsAccepted':False,
    'nativeNormalTangentNumericReadbackPerformed':False,'sourcePhotoPixelsEdited':False,
    'materialPackagesIndependentlyUnloaded':False,'materialCompileDiagnosticsExhaustivelyRead':False,
    'additionalSeedRangesPreservationClaimed':False,'cloudPhaseOrDynamicExposureLocked':False}
def now():return datetime.now(timezone.utc).isoformat()
def report_write(path,value):Path(path).write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n')
def helpers(bundle):
    require(set(bundle)=={'source','base','binding'}and set(bundle['base']['readerPacket'])=={'base'},'Exact current full observer packet required')
    return bundle['base']['native'].helpers(bundle['base']['readerPacket'])
def full(u,h):return h['cleanNative'].full_witness(u,h)
def actors(u):return {a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
def private_leaf_adapter(bundle):
    g.require_native_binding(bundle['binding']);m=g.module('_r46_private_immutable_leaf_kernel',g.LEAF_KERNEL,g.LEAF_KERNEL_SHA)
    # No frozen module/global mutation: only this new private instance's binder
    # accepts the leaf projection of the authenticated three-key R46 packet.
    def bound(packet):
        require(set(packet)=={'source','base','binding'}and packet['binding']==bundle['binding'],'Exact isolated leaf adapter packet')
        g.require_native_binding(packet['binding']);exact(packet['source'],bundle['source']['leaf'],'Exact frozen leaf-only source projection')
        require(packet['base']is bundle['base'],'Actual authenticated base identity required')
        return True
    m.require_native_binding=bound
    return m,{'source':bundle['source']['leaf'],'base':bundle['base'],'binding':bundle['binding']}
def old_assets(u,bundle,h,directory):
    require(not directory.exists(),'Fresh full72 graph observations required');directory.mkdir();base=bundle['base'];graphs={};textures={}
    leaf,_=private_leaf_adapter(bundle)
    for i,(asset,row)in enumerate(sorted(base['materialRecords'].items())):
        material=u.EditorAssetLibrary.load_asset(asset);require(isinstance(material,u.Material),'Protected Material absent')
        graph=base['native'].graph_snapshot(u,material,h,row['route']);aux=h['materials'].aux_snapshot(u,material);usage=leaf._usage(u,h,material)
        observed={'asset':asset,'reader':row['route'],'graph':graph,'graphSha256':digest(graph),'aux':aux,'usage':usage,
            'auxPreviouslyRecorded':row['auxPreviouslyRecorded'],'usagePreviouslyRecorded':row['usagePreviouslyRecorded'],
            'metadata':{k:u.EditorAssetLibrary.get_metadata_tag(material,k)for k in row['metadata']}}
        write(directory/('graph-'+str(i).zfill(3)+'.json'),observed)
        exact(graph,row['graph'],'Protected full graph changed: '+asset);require(digest(graph)==row['graphSha256'],'Protected graph hash differs')
        if row['aux']is not None:exact(aux,row['aux'],'Recorded old sampler/world-position policy differs')
        for key,value in row['recordedUsage'].items():require(usage[key]==value,'Recorded old usage differs')
        exact(observed['metadata'],row['metadata'],'Protected material metadata changed');graphs[asset]=observed
    for asset,row in sorted(base['textureRecords'].items()):
        texture=u.EditorAssetLibrary.load_asset(asset);require(isinstance(texture,u.Texture2D),'Protected Texture2D absent')
        snapshot=h['materials'].texture_snapshot(u,texture);exact(snapshot,row['snapshot'],'Protected full visible24 texture policy differs')
        meta={k:u.EditorAssetLibrary.get_metadata_tag(texture,k)for k in row['metadata']}
        exact(meta,row['metadata'],'Protected selected texture provenance differs');textures[asset]={'snapshot':snapshot,'metadata':meta}
    require(len(graphs)==72 and len(textures)==114,'All72 graphs and114 texture settings required')
    return {'graphs':graphs,'textures':textures}
def raw_controls(u,bundle,witness):
    raw=bundle['base']['native'].raw_instance_controls(u,witness)
    require(len(raw)==2329 and sum(v['instances']for v in raw.values())==678205,'All2329 native raw records required')
    exact(raw,bundle['base']['rawControls'],'All original raw matrices/order/mainseed/custom fields changed');return raw
def locate_targets(u,bundle,before,leaf):
    scene=actors(u);source=bundle['source'];target=before[leaf.ACTOR]
    c,defaults=leaf._target(u,before,target);roof=[]
    for row in source['roof']['proposal']['targets']:
        require(row['actor']in scene,'Exact existing roof actor missing')
        cs=[v for v in scene[row['actor']].get_components_by_class(u.StaticMeshComponent)if v.get_path_name()==row['component']]
        require(len(cs)==1,'One exact existing roof component required');component=cs[0]
        require(component.get_editor_property('static_mesh').get_path_name()==row['currentMesh']
            and component.get_material(0).get_path_name()==row['currentMaterial']
            and [v.get_path_name()if v else None for v in component.get_editor_property('override_materials')]==row['currentOverrideMaterials'],
            'Exact original roof mesh/material/default overrides required')
        roof.append((component,leaf._mesh_defaults(component.get_editor_property('static_mesh'))))
    require(len(roof)==4,'Exactly four existing roof slot targets');return c,defaults,roof
def primary_api():
    e=Path('/Users/Shared/Epic Games/UE_5.8/Engine')
    paths={'materials':e/'Source/Editor/MaterialEditor/Public/MaterialEditingLibrary.h',
        'componentSlots':e/'Source/Runtime/Engine/Classes/Components/MeshComponent.h',
        'assets':e/'Source/Editor/UnrealEd/Public/Subsystems/EditorAssetSubsystem.h',
        'twoSidedTransmission':e/'Shaders/Private/ShadingModels.ush'}
    require('GetMaterialExpressions'in paths['materials'].read_text()and 'SetMaterial('in paths['componentSlots'].read_text(), 'Installed reflected material/slot routes required')
    return {k:pin(p)for k,p in paths.items()}
def native_idle():
    rows=subprocess.check_output(['ps','-axo','pid=,comm='],text=True).splitlines();active=[]
    for row in rows:
        fields=row.strip().split(None,1)
        if len(fields)==2 and Path(fields[1]).name in ('UnrealEditor','UnrealEditor-Cmd','ShaderCompileWorker','BreziTwin','BreziTwin-Mac-Development','BreziTwin-Mac-Shipping'):
            active.append({'pid':int(fields[0]),'executable':fields[1]})
    require(active==[],'Root-only native/GPU must be idle for CPU preflight');return active
def validate_plan(bundle=None):
    bundle=g.load_contract()if bundle is None else bundle;plan=read(g.PLAN)
    require(plan['schema']==g.SCHEMA and plan['schemaVersion']==1 and plan['owner']=='scripts/unreal/exterior-burkea-clay-native-study-r46.py'
        and plan['nativeOwner']==OWNER and plan['status']=='selected-five-slot-material-source-ready-native-pending'
        and plan['binding']==bundle['binding']and plan['expectedCounts']==g.COUNTS and plan['expectedNewPackages']==g.expected_packages(bundle['source'])
        and plan['primaryApi']==primary_api()and plan['nativeExecuted']is False and plan['gpuExecuted']is False,'Exact own combined source plan required')
    require(plan['expectedActorWitnessSha256']==digest(g.expected_counterfactual(bundle['base']['savedWitness'],bundle)), 'Pure independent five-slot counterfactual changed')
    require(all(sha(p)==v for p,v in plan['inputFiles'].items()),'Frozen plan inputs changed');return plan,bundle
def validate_preflight(path,plan,bundle):
    pf=read(path);require(pf['schema']==g.SCHEMA and pf['schemaVersion']==1 and pf['selectedPlan']==pin(g.PLAN)
        and pf['binding']==bundle['binding']and pf['inputFiles']=={**plan['inputFiles'],str(g.PLAN):sha(g.PLAN)}
        and pf['tests']['exitCode']==0 and pf['tests']['testCount']==TEST_COUNT and pf['nativeExecuted']is False,'Actual once-executed combined preflight required')
    g.checked(pf['tests']['log']);require(all(sha(p)==v for p,v in pf['inputFiles'].items()),'Exact consumed source hashes required');return pf
def preflight(directory,bundle=None):
    directory=Path(directory).resolve();require(directory==g.STUDY/'source-preflight'and not directory.exists(),'One fresh mandatory preflight')
    idle=native_idle();plan,bundle=validate_plan(bundle);h=helpers(bundle);g.validate_clone(bundle);directory.mkdir()
    tests=module('_r46_changed_contracts',ROOT/'scripts/unreal/test_exterior_burkea_clay_native_r46.py');tests.Contracts.BUNDLE=bundle
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(tests.Contracts);stream=io.StringIO();result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    log=directory/'cpu-guards.log';log.write_text(stream.getvalue());require(result.wasSuccessful()and result.testsRun==TEST_COUNT,'Changed-contract suite failed: '+str(result.testsRun))
    inputs={**plan['inputFiles'],str(g.PLAN):sha(g.PLAN)};require(all(sha(p)==v for p,v in inputs.items()),'Sources changed during focused suite')
    pf={'schema':g.SCHEMA,'schemaVersion':1,'owner':OWNER,'status':'five-slot-material-source-preflight-validated-native-pending',
        'createdAt':now(),'selectedPlan':pin(g.PLAN),'binding':bundle['binding'],'expectedCounts':g.COUNTS,'inputFiles':inputs,
        'moduleOrderWitness':h['moduleOrderWitness'],'tests':{'exitCode':0,'testCount':TEST_COUNT,'log':pin(log),'nativeApisActuallyExercised':False},
        'nativeIdleAtPreflight':idle,'nativeExecuted':False,'gpuExecuted':False,**LIMITS}
    write(directory/'source-preflight.json',pf);print(json.dumps({'preflight':pin(directory/'source-preflight.json'),'tests':TEST_COUNT}),flush=True);return pf
def main():
    import unreal as u
    require(Path(os.environ['BREZI_BURKEA_CLAY_OUTPUT']).resolve()==g.CANDIDATE
        and Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==g.PROJECT,'Only exact own R46 candidate')
    require(sha(g.PLAN)==os.environ['BREZI_BURKEA_CLAY_PLAN_SHA256'],'Exact own plan SHA')
    path=Path(os.environ['BREZI_BURKEA_CLAY_PREFLIGHT']);require(sha(path)==os.environ['BREZI_BURKEA_CLAY_PREFLIGHT_SHA256']and not(g.CANDIDATE/REPORT).exists(),'Executed preflight and fresh report')
    plan,bundle=validate_plan();pf=validate_preflight(path,plan,bundle);base=bundle['base'];h=helpers(bundle)
    require(h['moduleOrderWitness']==pf['moduleOrderWitness'],'Frozen full observer module order changed')
    leaf,leaf_packet=private_leaf_adapter(bundle);leaf.require_native_binding(leaf_packet);roof=g.module('_r46_final_roof',g.ROOF,g.ROOF_SHA)
    roof.validate_binding(bundle,bundle['binding']);roof.preflight(u)
    directory=g.CANDIDATE/'combined-material-checkpoint';require(not directory.exists(),'Fresh checkpoints required');directory.mkdir()
    report={'schema':g.SCHEMA,'schemaVersion':1,'owner':OWNER,'status':'running','startedAt':now(),'nativeProcessId':os.getpid(),
        'project':str(g.PROJECT),'selectedPlan':pin(g.PLAN),'sourcePreflight':pin(path),'binding':bundle['binding'],
        'sourceProposals':{k:v['proposalPin']for k,v in bundle['source'].items()},'baseNativeReport':base['reportPin'],
        'baseNativeProcess':base['processPin'],'baseCurrentByteAudit':base['auditPin'],'rootImageDecision':pin(g.DECISION),
        'projectClone':pin(g.CLONE),'protectedProjectProof':base['report']['protectedProjectProof'],'inputFiles':pf['inputFiles'],
        'activeDesign':'C/B/B','setbacksMm':[3000,3000],'nativeApplied':False,'savedMapUnloadedReloaded':False,'sourceInputsUnchanged':False,
        'oldActorGeometryRootCollisionNavOrMeshDefaultSettersCalled':False,'oldMaterialOrTextureSettersCalled':False,
        'combinedCaptureCannotIsolateLeafTransmissionFromRoofIndirectLighting':True,**LIMITS}
    report_write(g.CANDIDATE/REPORT,report)
    try:
        own=g.PROJECT/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib';original=base['project']/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'
        require(sha(own)==sha(original)and own.stat().st_ino!=original.stat().st_ino,'Exact independent canonical module required')
        g.validate_clone(bundle);levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Load own cloned map')
        before=full(u,h);exact(before,base['savedWitness'],'Whole selected5371 before witness differs')
        raw=raw_controls(u,bundle,before);assets=old_assets(u,bundle,h,directory/'graphs-before')
        expected=g.expected_counterfactual(before,bundle);c,defaults,roof_targets=locate_targets(u,bundle,before,leaf)
        for name,value in [('before-actors',before),('expected-actors',expected),('raw-before',raw),('assets-before',assets)]:write(directory/(name+'.json'),value)
        leaf_material,leaf_report=leaf._create_own_material(u,leaf_packet,h,base['materialRecords'][leaf.LEAF])
        reader=lambda unreal,m:h['existing'].graph_snapshot(unreal,m)
        roof_material,roof_report=roof.build_materials(u,bundle,bundle['binding'],reader)
        exact(full(u,h),before,'Old scene changed before five declared setters')
        c.set_material(1,leaf_material)
        for component,_ in roof_targets:component.set_material(0,roof_material)
        exact(leaf._mesh_defaults(c.get_editor_property('static_mesh')),defaults,'Old tree mesh defaults changed')
        for component,old_defaults in roof_targets:exact(leaf._mesh_defaults(component.get_editor_property('static_mesh')),old_defaults,'Old roof mesh defaults changed')
        exact(full(u,h),expected,'Full before-save five-slot counterfactual differs')
        require(levels.save_current_level(),'Save own material-slot map')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Unload/reload saved own map')
        saved=full(u,h);exact(saved,expected,'Whole saved five-slot counterfactual differs')
        leaf_saved=leaf._verify_own_material(u,h,base['materialRecords'][leaf.LEAF],leaf_report)
        roof_saved=roof.verify_materials(u,bundle,bundle['binding'],roof_report,reader)
        new_saved={'leaf':{'asset':leaf_saved.get_path_name(),'graph':leaf._leaf_graph(u,h,leaf_saved),
            'aux':h['materials'].aux_snapshot(u,leaf_saved),'usage':leaf._usage(u,h,leaf_saved)},
            'roof':{'asset':roof_saved.get_path_name(),'graph':reader(u,roof_saved),'aux':h['materials'].aux_snapshot(u,roof_saved)}}
        raw_saved=raw_controls(u,bundle,saved);assets_saved=old_assets(u,bundle,h,directory/'graphs-saved')
        exact(raw_saved,raw,'All2329 raw before/saved fields differ');exact(assets_saved,assets,'All72 graph/aux/usage and114 texture metadata/settings differ')
        content=g.validate_clone(bundle,after=True);delta=g.validate_content_delta(base['content'],content,bundle['source'])
        built={'leaf':leaf_report,'roof':roof_report};require(sorted(leaf_report['newPackageAssets']+roof_report['newPackageAssets'])==g.expected_packages(bundle['source']),'Exactly5 owned packages')
        for name,value in [('saved-actors',saved),('raw-saved',raw_saved),('assets-saved',assets_saved),('new-materials',built),('new-materials-saved',new_saved),('after-content',content)]:write(directory/(name+'.json'),value)
        require(all(sha(p)==v for p,v in pf['inputFiles'].items()),'Consumed source changed')
        report.update(status=STATUS,completedAt=now(),nativeApplied=True,savedMapUnloadedReloaded=True,sourceInputsUnchanged=True,
            moduleOrderWitness=h['moduleOrderWitness'],nativeModuleWitness={'source':str(original),'destination':str(own),'sha256':sha(own),'bytes':own.stat().st_size,'independentInodes':True},
            beforeActorWitness=pin(directory/'before-actors.json'),expectedActorWitness=pin(directory/'expected-actors.json'),savedActorWitness=pin(directory/'saved-actors.json'),
            beforeActorWitnessSha256=digest(before),expectedActorWitnessSha256=digest(expected),savedActorWitnessSha256=digest(saved),
            rawInstanceControlsBefore=pin(directory/'raw-before.json'),rawInstanceControlsSaved=pin(directory/'raw-saved.json'),
            originalAssetWitnessBefore=pin(directory/'assets-before.json'),originalAssetWitnessSaved=pin(directory/'assets-saved.json'),
            newMaterialReport=pin(directory/'new-materials.json'),materialReport=built,savedNewMaterialReadback=pin(directory/'new-materials-saved.json'),
            afterContentInventory=pin(directory/'after-content.json'),assetDelta=delta,newPackages=g.expected_packages(bundle['source']),actualCounts=g.COUNTS,
            wholeActorCounterfactualValidated=True,all5371ActorFieldsExceptFiveDeclaredSlotsExact=True,all2329RawControlsExact=True,
            all72OriginalGraphAuxObservedUsageExact=True,all114OriginalVisible24TexturePoliciesAndSelectedMetadataExact=True)
        report_write(g.CANDIDATE/REPORT,report);print(json.dumps({'report':pin(g.CANDIDATE/REPORT),'status':STATUS}),flush=True)
    except Exception as error:
        report.update(status='failed',completedAt=now(),error=str(error));report_write(g.CANDIDATE/REPORT,report);raise
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preflight',type=Path);args=parser.parse_args()
    preflight(args.preflight)if args.preflight else main()
