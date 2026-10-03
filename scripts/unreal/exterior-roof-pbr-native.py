"""R23 standalone material-only overlay. Only root launches native/GPU.

A CPU preflight closes original source bytes. Native success requires a fresh
independent R18b clone, full scene/old-material counterfactual and saved reload.
"""
import copy
from datetime import datetime,timezone
import importlib.util
import json
import os
import subprocess
import re
import time
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.dont_write_bytecode=True
OWNER='scripts/unreal/exterior-roof-pbr-native.py'
SCHEMA='brezi-original-roof-pbr-component-overlay-r1'
STATUS='verified-saved-original-roof-pbr-component-overlay'
MAP='/Game/Brezi/Maps/Brezi'
MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574'
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
guard=module('r23_roof_source_guards','exterior-roof-pbr-guards.py')
materials=module('r23_roof_materials','exterior-roof-pbr-materials.py')
require,read,sha,pin,check_pin,digest=guard.require,guard.read,guard.sha,guard.pin,guard.check_pin,guard.digest
def write(path,value):Path(path).write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
def now():return datetime.now(timezone.utc).isoformat()
def pipelines(bundle):return {**bundle['base']['pipelineFiles'],str(guard.GENERIC):guard.GENERIC_SHA,**{str(ROOT/'scripts/unreal'/name):sha(ROOT/'scripts/unreal'/name)for name in ('exterior-roof-pbr-native.py','exterior-roof-pbr-guards.py','exterior-roof-pbr-materials.py','test_exterior_roof_pbr.py')}}
def preflight(output):
    output=Path(output).resolve();require(output.is_relative_to(ROOT/'output/unreal')and not output.exists(),'Fresh CPU preflight output required');bundle=guard.load_source();output.mkdir(parents=True)
    before=dict(bundle['inputPins']);before.update(pipelines(bundle));before[str(guard.PLAN)]=guard.PLAN_SHA;before[str(ROOT/'docs/unreal-roof-pbr-r23.md')]=sha(ROOT/'docs/unreal-roof-pbr-r23.md')
    start=time.monotonic();test=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/unreal/test_exterior_roof_pbr.py')],cwd=ROOT,capture_output=True,text=True,timeout=60)
    (output/'source-guard-tests.log').write_text(test.stdout+test.stderr);match=re.search(r'Ran (\d+) tests? in ',test.stdout+test.stderr)
    write(output/'source-guard-tests.json',dict(status='passed'if test.returncode==0 else'failed',exitCode=test.returncode,testCount=int(match.group(1))if match else None,elapsedSeconds=time.monotonic()-start,nativeExecuted=False,nativeAppearanceAccepted=False))
    require(test.returncode==0 and match and int(match.group(1))==6,'CPU tests failed; preserve this preflight')
    for file,h in before.items():require(sha(file)==h,'Source changed during preflight')
    receipt=dict(schema=SCHEMA,owner=OWNER,status='source-only-roof-pbr-preflight-validated-native-pending',createdAt=now(),sourceStudy=pin(guard.PLAN),baseNativeReport=bundle['plan']['baseNativeReport'],sourceVisualReview=bundle['sourceVisualReview'],
        sourceGuardTests=pin(output/'source-guard-tests.json'),sourceGuardTestsLog=pin(output/'source-guard-tests.log'),design=pin(ROOT/'docs/unreal-roof-pbr-r23.md'),audit=bundle['audit'],sourceMeasurement=bundle['sourceMeasurement'],inputFiles=bundle['inputPins'],pipelineFiles=pipelines(bundle),
        nativeExecuted=False,nativeApplied=False,nativeGeometryDecodedOrSaved=False,nativeAppearanceAccepted=False,fullPhotorealismAccepted=False,performanceAccepted=False,shippingPackageProduced=False,sourceInputsUnchanged=True)
    write(output/'source-preflight.json',receipt);print(json.dumps(dict(preflight=pin(output/'source-preflight.json'),audit=bundle['audit'],nativeExecuted=False)))
def validate_preflight(path,bundle):
    p=Path(path).resolve();receipt=read(p)
    require(receipt['schema']==SCHEMA and receipt['owner']==OWNER and receipt['status']=='source-only-roof-pbr-preflight-validated-native-pending'and receipt['sourceStudy']==pin(guard.PLAN)and receipt['baseNativeReport']==bundle['plan']['baseNativeReport'],'Unapproved preflight')
    require(receipt['audit']==bundle['audit']and receipt['sourceMeasurement']==bundle['sourceMeasurement']and receipt['sourceVisualReview']==bundle['sourceVisualReview']and receipt['inputFiles']==bundle['inputPins']and receipt['pipelineFiles']==pipelines(bundle),'CPU preflight closure changed')
    require(all(receipt[k]is False for k in ('nativeExecuted','nativeApplied','nativeGeometryDecodedOrSaved','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingPackageProduced'))and receipt['sourceInputsUnchanged']is True,'CPU receipt claims native acceptance')
    test=read(check_pin(receipt['sourceGuardTests']));check_pin(receipt['sourceGuardTestsLog']);check_pin(receipt['design'])
    require(test['status']=='passed'and test['exitCode']==0 and test['testCount']==6 and test['nativeExecuted']is False and test['nativeAppearanceAccepted']is False,'CPU test receipt failed or claims native proof')
    require(receipt['design']==pin(ROOT/'docs/unreal-roof-pbr-r23.md'),'Selected source design changed')
    for file,h in {**receipt['inputFiles'],**receipt['pipelineFiles']}.items():require(sha(file)==h,'Preflight source pin changed')
    return receipt

def existing_materials(u,bundle,r18,existing):
    base=read(bundle['base']['baseNativeReport']['path']);require(len(base['materials']['materials'])==42 and len(base['materials']['textures'])==74,'Inherited original material/texture count differs')
    assets=u.EditorAssetLibrary;graphs={};textures={}
    def metadata(asset,names):return {name:assets.get_metadata_tag(asset,name)for name in names}
    for key,row in base['materials']['materials'].items():
        m=assets.load_asset(row['asset']);require(isinstance(m,u.Material),'Original material missing');graph=existing.graph_snapshot(u,m)
        require(graph==row['graph']and digest(graph)==row['graphSha256'],'Original graph differs from actual R16')
        graphs['original:'+key]=dict(asset=row['asset'],graph=graph,metadata=metadata(m,['BreziGeneratedBy','BreziExteriorRecipe']),usage={k:bool(u.MaterialEditingLibrary.has_material_usage(m,v))for k,v in [('instanced',materials.native_enum(u,'MaterialUsage','INSTANCEDSTATICMESHES')),('nanite',u.MaterialUsage.MATUSAGE_NANITE)]})
    for key,row in bundle['base']['materials']['materials'].items():
        m=assets.load_asset(row['asset']);require(isinstance(m,u.Material),'R18 material missing');graph=r18.graph_snapshot(u,m,existing.graph_snapshot)
        require(graph==row['graph'],'Existing R18 graph differs from actual saved receipt')
        graphs['neighbor:'+key]=dict(asset=row['asset'],graph=graph,metadata=metadata(m,['BreziGeneratedBy','BreziR18Recipe','BreziR18NativeParameters']),usage={k:bool(u.MaterialEditingLibrary.has_material_usage(m,v))for k,v in [('instanced',materials.native_enum(u,'MaterialUsage','INSTANCEDSTATICMESHES')),('nanite',u.MaterialUsage.MATUSAGE_NANITE)]})
    for family,rows in [('original',base['materials']['textures']),('neighbor',bundle['base']['materials']['textures'])]:
        for key,row in rows.items():
            tex=assets.load_asset(row['asset']);require(isinstance(tex,u.Texture2D),'Existing texture missing');snapshot=materials.texture_snapshot(tex)
            if family=='neighbor':require(r18.texture_snapshot(tex)==row['snapshot'],'Existing R18 texture differs from native saved receipt')
            textures[family+':'+key]=dict(asset=row['asset'],snapshot=snapshot,metadata=metadata(tex,['BreziGeneratedBy','source_sha256','BreziSourceLicense','BreziSourcePage','BreziSourceEncodingOverride']))
    require(len(graphs)==51 and len(textures)==77,'All existing51graphs77textures required');return dict(graphs=graphs,textures=textures)

def native_roof_proofs(u,bundle,neighbor):
    assets=u.EditorAssetLibrary;result=[]
    for target in bundle['targets']:
        mesh=assets.load_asset(target['mesh']);require(isinstance(mesh,u.StaticMesh),'Existing target roof mesh missing')
        require(mesh.get_material(0).get_path_name()==target['oldMaterial'],'Old static mesh default material was changed')
        result.append(neighbor.native_mesh_proof(u,mesh,bundle['sourceRows'][target['sourceMeshId']]))
    require(sum(p['triangles']for p in result)==332,'Native unchanged target triangle count differs');return result

def main():
    import unreal as u
    bundle=guard.load_source();preflight_path=Path(os.environ['BREZI_ROOF_PBR_PREFLIGHT']).resolve();pre=validate_preflight(preflight_path,bundle)
    output=Path(os.environ['BREZI_ROOF_PBR_OUTPUT']).resolve();require(output==ROOT/'output/unreal/exterior-20261002-r23a','Only fresh selected R23a may change')
    project=output/'Project/BreziTwin';donor=guard.BASE/'Project/BreziTwin';g=guard.generic()
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project and Path(u.Paths.engine_dir()).resolve()==Path('/Users/Shared/Epic Games/UE_5.8/Engine'),'Wrong project/engine')
    require(not(output/'exterior-import-report.json').exists()and not(output/'neighbor-finish-overlay-report-r3.json').exists(),'Do not copy/spoof exterior or donor overlay reports')
    receipt=output/'roof-pbr-native-report.json';require(not receipt.exists(),'Existing attempts are immutable')
    for p in (donor,project):require(g.inventory(p/'Content')==bundle['content']and g.project_proof(p)==bundle['projectProof'],'Fresh clone/donor project bytes differ')
    for folder,rows in [('Content',bundle['content']),('',bundle['projectProof'])]:
        for relative in rows:
            a,b=donor/folder/relative,project/folder/relative;require((a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino),'Donor hardlink forbidden')
    clone_path=output/'roof-pbr-project-clone.json';clone=read(clone_path)
    require(clone['status']=='verified-byte-identical-independent-apfs-r23-project-clone-before-roof-native'and clone['baseNativeReport']==bundle['plan']['baseNativeReport']and clone['selectedPlan']==pin(guard.PLAN)and clone['fileCount']==len(bundle['content'])+132 and clone['nativeExecuted']is False,'Typed independent clone receipt differs')
    module_relative=Path('Binaries/Mac/libUnrealEditor-BreziTwin.dylib');require(sha(donor/module_relative)==sha(project/module_relative)==MODULE_SHA and (project/module_relative).stat().st_size==2818384,'Recorder module bytes differ')
    engine_modules=Path('/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor.modules');require(read(project/'Binaries/Mac/UnrealEditor.modules')['BuildId']==read(engine_modules)['BuildId']=='55116800','Recorder/engine BuildId mismatch')
    # Frozen R18's actual witness/geometry APIs, not a new ownership alias.
    neighbor=module('r23_exact_saved_neighbor_witness','exterior-neighbor-finish-native-r3.py')
    existing=module('r23_exact_material_witness','exterior-materials.py');witness=module('r23_exact_actor_witness','performance-optimize.py');r18=module('r23_exact_neighbor_material_witness','exterior-neighbor-finish-materials.py')
    closure={**pre['inputFiles'],**pre['pipelineFiles'],str(guard.PLAN):guard.PLAN_SHA,str(preflight_path):sha(preflight_path),str(clone_path):sha(clone_path),str(engine_modules):sha(engine_modules),**{pre[k]['path']:pre[k]['sha256']for k in ('sourceGuardTests','sourceGuardTestsLog','design')}}
    state=dict(schema=SCHEMA,owner=OWNER,status='running',nativeProcessId=os.getpid(),startedAt=now(),output=str(output),project=str(project),sourceStudy=pin(guard.PLAN),selectedPreflight=pin(preflight_path),baseNativeReport=bundle['plan']['baseNativeReport'],baseContentInventory=bundle['base']['afterContentInventory'],baseProtectedProjectProof=bundle['base']['protectedProjectProof'],projectClone=pin(clone_path),activeDesign=bundle['base']['activeDesign'],setbacksMm=bundle['base']['setbacksMm'],inputFiles=closure,pipelineFiles=pre['pipelineFiles'],sourceMeasurement=bundle['sourceMeasurement'],sourceAudit=bundle['audit'],nativeModuleWitness=dict(source=str(donor/module_relative),destination=str(project/module_relative),sha256=MODULE_SHA,bytes=2818384,independentInodes=True),nativeAppearanceAccepted=False,fullPhotorealismAccepted=False,performanceAccepted=False,shippingPackageProduced=False,nativeApplied=False,nativeMaterialPackagesIndependentlyReloaded=False)
    write(receipt,state)
    try:
        # All enum names, including their narrow prefixes, resolve before assets.
        state['nativeEnumPreflight']=materials.enum_preflight(u)
        levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot load exact own R18b map')
        before=neighbor.original_witness(u,actors,witness);require(before==bundle['baseSaved'],'Actual R18b full5338 actor witness differs')
        expected,changes=guard.expected_witness(before,bundle['targets']);old=existing_materials(u,bundle,r18,existing)
        proofs_before=native_roof_proofs(u,bundle,neighbor)
        write(output/'roof-pbr-witness-before.json',before);write(output/'roof-pbr-witness-expected.json',expected);write(output/'roof-pbr-existing-materials-before.json',old)
        material,material_report=materials.build(u,bundle['recipe'],existing.graph_snapshot,guard.PLAN_SHA)
        lookup={a.get_path_name():a for a in actors.get_all_level_actors()}
        for target in bundle['targets']:
            a=lookup[target['actor']];cs=[c for c in a.get_components_by_class(u.StaticMeshComponent)if c.get_name()==target['componentName']and c.get_editor_property('static_mesh')and c.get_editor_property('static_mesh').get_path_name()==target['mesh']]
            require(len(cs)==1 and cs[0].get_num_materials()==1 and cs[0].get_material(0).get_path_name()==target['oldMaterial'],'Actual target component differs');cs[0].set_material(0,material)
        require(neighbor.original_witness(u,actors,witness)==expected,'Mutation exceeds exact four component slot overrides')
        require(levels.save_current_level(),'Cannot save own roof map');require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot reload saved roof map')
        materials.verify(u,material_report,existing.graph_snapshot,bundle['recipe'],guard.PLAN_SHA)
        after=neighbor.original_witness(u,actors,witness);require(after==expected,'Saved scene differs from exact5338actor counterfactual')
        saved_old=existing_materials(u,bundle,r18,existing);require(saved_old==old,'Any existing51graphs77textures changed')
        proofs=native_roof_proofs(u,bundle,neighbor);require(proofs==proofs_before,'Existing source roof geometry changed')
        after_content=g.inventory(project/'Content');delta=guard.validate_content_delta(bundle['content'],after_content,[v['asset']for v in material_report['textures'].values()])
        require(g.project_proof(project)==bundle['projectProof']and g.inventory(donor/'Content')==bundle['content']and g.project_proof(donor)==bundle['projectProof'],'Protected or original donor bytes changed')
        for file,h in closure.items():require(sha(file)==h,'Frozen input/source changed during native')
        write(output/'roof-pbr-witness-saved.json',after);write(output/'roof-pbr-existing-materials-saved.json',saved_old);write(output/'roof-pbr-content-after.json',after_content);write(output/'roof-pbr-protected-project-proof.json',bundle['projectProof'])
        state.update(status=STATUS,endedAt=now(),savedMapUnloadedReloaded=True,nativeApplied=True,componentMaterialOverrides=changes,actualSavedTargetGeometry=proofs,materialReport=material_report,beforeActorWitnessSha256=digest(before),expectedActorWitnessSha256=digest(expected),savedActorWitnessSha256=digest(after),existingMaterialsBeforeSha256=digest(old),existingMaterialsSavedSha256=digest(saved_old),beforeActorWitness=pin(output/'roof-pbr-witness-before.json'),expectedActorWitness=pin(output/'roof-pbr-witness-expected.json'),savedActorWitness=pin(output/'roof-pbr-witness-saved.json'),existingMaterialsBefore=pin(output/'roof-pbr-existing-materials-before.json'),existingMaterialsSaved=pin(output/'roof-pbr-existing-materials-saved.json'),afterContentInventory=pin(output/'roof-pbr-content-after.json'),protectedProjectProof=pin(output/'roof-pbr-protected-project-proof.json'),assetDelta=delta,existingActorCount=5338,existingMaterialGraphsPreserved=51,existingTextureObjectsPreserved=77,geometryChanges=0,originalStaticMeshSlotChanges=0,newImportPipelineAssets=0,originalR18bUnchanged=True,originalContentExceptMapByteIdentical=True,baselineRecordedPlantLibrary=dict(masters=135,lods=405,newNativePlantLodReadbackPerformed=False),nativeNormalTangentReadbackAvailable=False)
        write(receipt,state);print(json.dumps(dict(status=STATUS,report=pin(receipt),nativeAppearanceAccepted=False)))
    except Exception as error:
        state.update(status='failed',error=str(error),endedAt=now(),nativeApplied=False);write(receipt,state);raise

if __name__=='__main__':
    if '--preflight-output'in sys.argv:preflight(sys.argv[sys.argv.index('--preflight-output')+1])
    else:main()
