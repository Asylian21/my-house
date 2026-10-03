"""R22 disjoint field composition and exact saved-donor package closure.

No native/GPU execution. Every donor must already have a saved, terminally
successful native receipt. Failed or merely source-selected studies cannot load.
"""
import copy
import importlib.util
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-realism-integration-guards-r22.py'
BASE=ROOT/'output/unreal/exterior-20261001-r16a'
BASE_SHA='1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122'
SCHEMA='brezi-exterior-realism-saved-donor-integration-r22'
STUDY=ROOT/'output/unreal/exterior-realism-integration-20261002-r22-study'
PLAN=STUDY/'realism-integration-plan.json'
CANDIDATE=ROOT/'output/unreal/exterior-20261002-r22a'
EXPECTED={'originalContentFiles':3975,'copiedNewPackages':74,'savedContentFiles':4049,
    'originalActors':5306,'savedActors':5346,'savedRecordedExteriorHismGroups':1987,'savedRecordedExteriorHismInstances':632538,
    'originalFullSceneHismComponents':2305,'originalFullSceneHismInstances':676432,
    'savedFullSceneHismComponents':2312,'savedFullSceneHismInstances':676944,
    'scopedMaterialGraphs':56,'scopedTextureObjects':84,'originalMaterialGraphs':42,'originalTextureObjects':74,
    'leafGroups':23,'leafInstances':78,'visibilityOriginalGroups':601,'visibilityOriginalInstances':501890,
    'visibilityRetainedInstances':501826,'grassReplacementRoots':64,'grassNewGroups':3,
    'neighborAddedActors':32,'neighborRetainedRebinds':5,'neighborEmptyChunkHidden':1,
    'foregroundAddedActors':5,'foregroundNewGroups':4,'foregroundNewRoots':512,
    'foregroundFloorTriangles':1843,'roofComponentOverrides':4,'roofTargetTrianglesUnchanged':332}
DONORS={
    'leaf':('exterior-20261001-r17a','canopy-transmission-native-report.json','canopy-transmission-native',
        'exterior-canopy-transmission-native.py','91198a555bbf11d3636d14445a5cb743276f229123a5bb69d6efe47b2fc11647',
        'verified-saved-canopy-transmission-component-overlay','/Game/Brezi/CanopyTransmissionR1',2),
    'visibility':('exterior-20261001-r19a','meadow-visibility-native-report.json','meadow-visibility-native',
        'exterior-meadow-visibility-native.py','b92b4cc3bac23cf4255ab8f1f7471f5b1722a6aff9bbad5ca9e807ddc6e5f55d',
        'verified-saved-meadow-ecology-visibility-component-overlay',None,0),
    'neighbors':('exterior-20261001-r18b','neighbor-finish-overlay-report-r3.json','neighbor-finish-native-r3',
        'exterior-neighbor-finish-native-r3.py','40ccc7cc686e2beafc05e5248eb8abe371f23bc8ad470c05284d4c442ed950da',
        'neighbor-finish-native-overlay-validated','/Game/Brezi/NeighborFinish20261001R18',52),
    'grass':('exterior-20261002-r20d','curved-grass-native-report-r4.json','curved-grass-native-r4',
        'exterior-curved-grass-native-r4.py','63ff19a28e571ff4a63d0a9e13726c90a01fcc82b691b81dd2b6a35ac01eb4eb',
        'verified-saved-original-curved-grass-root-replacement','/Game/Brezi/CurvedGrass20261001R20',11),
    'foreground':('exterior-20261002-r21b','foreground-overlay-report-r2.json','foreground-native-r2',
        'exterior-canopy-foreground-native-r2.py','42e1bd9bc9297ce4f1e90a571c125f4df64726793d75dc7fa111ec8e69c3b942',
        'foreground-native-overlay-validated','/Game/Brezi/CanopyForeground20261002R21',5),
    'roof':('exterior-20261002-r23a','roof-pbr-native-report.json','roof-pbr-native',
        'exterior-roof-pbr-native.py','be4adfc86cdfc954f57ef2c3064d142be86b74654efee999bc50e560e254880b',
        'verified-saved-original-roof-pbr-component-overlay','/Game/Brezi/RoofPbr20261002R23',4)}
sys.dont_write_bytecode=True
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
g=module('r22_frozen_generic','exterior-canopy-transmission-native.py')
require,read,write,sha,pin,check_pin,digest,now=(getattr(g,k)for k in ('require','read','write','sha','pin','check_pin','digest','now'))
require(sha(ROOT/g.OWNER)=='10cc942f098e130f8f22f0acb9948f4381bdc0226d5db2af17a4665fd701bc6b','Frozen base helper changed')
RENDER_FIELDS=('cast_shadow','cast_hidden_shadow','visible_in_ray_tracing','affect_distance_field_lighting',
               'affect_dynamic_indirect_lighting','affect_indirect_lighting_while_hidden')
PASS_FIELDS=('render_in_main_pass','render_in_depth_pass')


def union_witness(common,extended):
    """Merge independently recorded policy schemas, requiring shared equality."""
    require(set(common)==set(extended),'Independent donor original actor identities differ')
    result=copy.deepcopy(common)
    for path,extra in extended.items():
        row=result[path]
        require({k:v for k,v in row.items()if k in extra and k!='components'}==
                {k:v for k,v in extra.items()if k in row and k!='components'},'Shared donor actor fields differ: '+path)
        row.update({k:copy.deepcopy(v)for k,v in extra.items()if k not in row})
        by_name={c['name']:c for c in extra['components']}
        require(set(by_name)=={c['name']for c in row['components']},'Shared donor component identities differ')
        for c in row['components']:
            e=by_name[c['name']]
            require({k:v for k,v in c.items()if k in e}=={k:v for k,v in e.items()if k in c},
                    'Shared donor component fields differ: '+path+'.'+c['name'])
            c.update({k:copy.deepcopy(v)for k,v in e.items()if k not in c})
    return result


def component(witness,actor,name_or_path):
    require(actor in witness,'Declared target actor missing')
    rows=[c for c in witness[actor]['components']if c['name']==name_or_path or c.get('path')==name_or_path]
    require(len(rows)==1,'Declared target component is ambiguous');return rows[0]


def compose_original_fields(before,baseline,leaf,visibility,neighbors,grass,selected,original_values,grass_guard):
    require(len(before)==5306,'Original full actor population required')
    expected,membership=grass_guard.expected_original_witness(before,selected,original_values,baseline['geometry']['groups'])
    require(membership==grass['originalMemberChanges'],'Saved grass membership scope differs from explicit RemoveAtSwap')
    require(len(leaf['componentBindings'])==23 and leaf['effectiveLeafOverrideInstances']==78,'Exact grove leaf scope required')
    leaf_components=set()
    for delta in leaf['componentBindings']:
        c=component(expected,delta['actor'],delta['component']);original=component(before,delta['actor'],delta['component'])
        require(delta['slot']==1 and delta['component'] not in leaf_components and len(original['materials'])==2
                and original['materials']==[delta['barkSlot0'],delta['before']], 'Exact leaf/bark slot inputs differ')
        override=copy.deepcopy(original['overrideMaterials']);require(len(override)<=2,'Unexpected original leaf override slots')
        override += [None]*(2-len(override));override[1]=delta['after']
        c['materials'][1]=delta['after'];c['overrideMaterials']=override;leaf_components.add(delta['component'])
    targets=visibility['componentCullOverrides'];require(len(targets)==601 and len({r['groupId']for r in targets})==601
        and sum(r['instances']for r in targets)==501890,'Exact original meadow/ecology cull scope differs')
    retained_cull_population=0
    for delta in targets:
        group=baseline['geometry']['groups'][delta['groupId']]
        require(delta['actor']==group['actor'] and delta['afterCullCm']==[18000,24000]
                and delta['beforeCullCm']==[group['cullStartCm'],group['cullEndCm']]
                and delta['instances']==group['instances'],'Visibility target differs from original native group')
        original=component(before,delta['actor'],delta['component']);c=component(expected,delta['actor'],delta['component'])
        require(original['instanceCullCm']==delta['beforeCullCm'] and original['instanceCount']==delta['instances']
                and original['mesh']==group['mesh'],'Visibility original component witness differs')
        c['instanceCullCm']=copy.deepcopy(delta['afterCullCm']);retained_cull_population+=c['instanceCount']
    require(retained_cull_population==501826,'601 cull overlap must remove exactly64 old grass members')
    changes=neighbors['componentChanges']
    required={'village_0_2_wall','village_0_2_roof','village_0_2_darkroof','neighborhood_0_2_wire',
              'neighborhood_0_2_village_wall','neighborhood_0_2_boundary_post'}
    require(len(changes)==6 and {c['sourceMeshId']for c in changes}==required,'Exact rural neighbor partitions required')
    for delta in changes:
        c=component(expected,delta['actor'],delta['componentName']);original=component(before,delta['actor'],delta['componentName'])
        require(original['mesh']==delta['beforeMesh'] and delta['actor']==baseline['geometry']['actors'][delta['sourceMeshId']],
                'Declared original neighbor chunk differs')
        if delta['sourceMeshId']=='village_0_2_darkroof':
            require(delta['operation']=='hide-empty-source-chunk' and delta['afterMesh']==delta['beforeMesh'],
                    'Empty source roof scope widened')
            c['visible']=False;c['hiddenInGame']=True
            for key in ('renderFlags','neighborRenderPolicy'):
                c[key]['cast_shadow']=False;c[key]['cast_hidden_shadow']=False
        else:
            require(delta['operation']=='replace-with-retained-source-chunk','Neighbor scope is not a retained chunk rebind')
            c['mesh']=delta['afterMesh']
    return expected,{'originalActors':5306,'leafGroups':23,'leafInstances':78,'cullGroups':601,
        'originalCullInstances':501890,'retainedCullInstances':501826,'grassRemovedMembers':64,
        'grassAffectedOriginalGroups':4,'neighborRetainedRebinds':5,'neighborEmptyChunkHidden':1}


def normalize_extended_added(path,row):
    result=copy.deepcopy(row)
    for c in result['components']:
        c['path']=path+'.'+c['name']
        if 'neighborRenderPolicy'in c:
            c['renderFlags']={k:c['neighborRenderPolicy'][k]for k in RENDER_FIELDS}
            c['passFlags']={k:c['neighborRenderPolicy'][k]for k in PASS_FIELDS}
    return result


def relocate_template(template,old_path,new_path):
    """Only rewrite owned object identity strings; no geometry/policy inference."""
    def replace(value):
        if isinstance(value,dict):return {k:replace(v)for k,v in value.items()}
        if isinstance(value,list):return [replace(v)for v in value]
        if isinstance(value,str)and(value==old_path or value.startswith(old_path+'.')):
            return new_path+value[len(old_path):]
        return value
    return replace(template)


def actual_terminal(report_path,process_path,owner,stem):
    report=read(report_path);p=read(process_path);raw=Path(p['processFile']);run=read(raw)
    require(process_path==report_path.parent/(stem+'-process.json')
            and raw==report_path.parent/(stem+'.log.json') and Path(p['logFile'])==report_path.parent/(stem+'.log')
            and sha(raw)==p['processFileSha256'] and sha(p['logFile'])==p['logSha256']
            and p['reportSha256']==sha(report_path) and run['code']==0 and run['signal'] is None
            and run['pid']==report['nativeProcessId'],'Donor native terminal proof is not actual success')
    require(run['command']=='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd'
            and run['args'][0]==str(report_path.parent/'Project/BreziTwin/BreziTwin.uproject')
            and '-script='+str(ROOT/owner)in run['args'] and '-nullrhi'in run['args']
            and '-run=pythonscript'in run['args'],'Donor native executable/project/helper differs')
    if 'sourcePinsBeforeNative'in p:
        require(p['sourcePinsUnchangedAfterNative'] is True and p['controllerSha256BeforeNative']==p['controllerSha256AfterNative']==sha(p['controller']),
                'Donor native source closure changed')
        for file,h in p['sourcePinsBeforeNative'].items():require(sha(file)==h,'Donor native consumed source changed')
    else:
        require(report_path.parent.name=='exterior-20261001-r17a'and p['controllerSha256']==sha(p['controller']),
                'Only the exact original R17 process uses the old controller receipt type')
    return {'receipt':pin(process_path),'raw':pin(raw),'log':pin(p['logFile']),'pid':run['pid'],'exitCode':0}


def donor_package_manifest(report_path,report,base_content,prefix,expected_packages):
    inventory=read(check_pin(report['afterContentInventory']))
    require(set(base_content)<=set(inventory),'Donor removed an original native Content file')
    require(all(inventory[k]==base_content[k]for k in base_content if k not in ('Brezi/Maps/Brezi.umap','Data/viewpoints.json')),
            'Donor changed a protected original native package/data file')
    added=sorted(set(inventory)-set(base_content));require(len(added)==expected_packages and all(
        p.startswith(prefix.removeprefix('/Game/')+'/')and p.endswith('.uasset')for p in added),'Saved donor package scope differs')
    rows=[]
    for relative in added:
        source=report_path.parent/'Project/BreziTwin/Content'/relative;row=inventory[relative]
        require(source.is_file() and sha(source)==row['sha256'] and source.stat().st_size==row['bytes'],
                'Actual saved donor package bytes changed')
        rows.append({'source':str(source),'relativeContentPath':relative,'sha256':row['sha256'],'bytes':row['bytes'],
                     'donorReport':str(report_path)})
    return rows


def pins_in(value,inputs):
    if isinstance(value,dict):
        if {'path','sha256','bytes'}<=set(value):
            entry={k:value[k]for k in ('path','sha256','bytes')};check_pin(entry);inputs[entry['path']]=entry['sha256'];return
        for child in value.values():pins_in(child,inputs)
    elif isinstance(value,list):
        for child in value:pins_in(child,inputs)


def report_witness(report,before=False):
    key=('witnessBefore'if before else'witnessAfter')if'witnessBefore'in report else('beforeActorWitness'if before else'savedActorWitness')
    return read(check_pin(report[key]))


def load_donors():
    require(sha(BASE/'exterior-import-report.json')==BASE_SHA,'Original saved R16 report changed')
    evidence_path=ROOT/'output/unreal/exterior-canopy-transmission-20261001-r1-study/canopy-transmission-plan.json'
    evidence=read(evidence_path);base,content,protected=g.validate_plan(evidence,evidence_path)
    reports={};specs={};inputs={str(evidence_path):sha(evidence_path),str(BASE/'exterior-import-report.json'):BASE_SHA}
    for name,(directory,filename,stem,helper,h,status,prefix,count)in DONORS.items():
        path=ROOT/'output/unreal'/directory/filename
        require(path.is_file()and sha(path)==h,'Exact actual saved donor required: '+name)
        report=read(path);require(report['owner']=='scripts/unreal/'+helper and report['status']==status
            and report['output']==str(path.parent)and report['project']==str(path.parent/'Project/BreziTwin'),
            'Typed saved donor identity/status differs: '+name)
        require(all(report[k]is False for k in ('nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted')),
                'Donor report has unapproved acceptance flags')
        require(report.get('savedMapUnloadedReloaded',report.get('savedReloaded'))is True,
                'Donor map was not saved/unloaded/reloaded: '+name)
        process=actual_terminal(path,path.parent/(stem+'-process.json'),report['owner'],stem)
        if name=='neighbors':
            expected=read(check_pin(report['expectedActorWitness']));saved=read(check_pin(report['savedActorWitness']))
            require(len(expected)==5306 and len(saved)==5338 and all(saved[k]==v for k,v in expected.items())
                and set(saved)-set(expected)==set(report['addedActors'].values())
                and digest(saved)==report['savedActorWitnessSha256'],
                'R18 exact original counterfactual/new32 saved witness differs')
        else:
            require(report['expectedActorWitnessSha256']==report['savedActorWitnessSha256'],
                    'Donor full expected/saved witness differs: '+name)
        pins_in(report,inputs);pins_in(process,inputs)
        p=read(process['receipt']['path']);inputs[p['controller']]=sha(p['controller'])
        inputs.update(p.get('sourcePinsBeforeNative',{}))
        for field in ('inputFiles','pipelineFiles'):
            for file,hash_value in report.get(field,{}).items():
                require(sha(file)==hash_value,'Saved donor source changed: '+file);inputs[file]=hash_value
        inputs[str(path)]=h
        reports[name]=report;specs[name]={'report':pin(path),'process':process,'nativeHelper':pin(ROOT/report['owner']),
            'newPackagePrefix':prefix,'newPackageCount':count}
        inputs[str(ROOT/report['owner'])]=sha(ROOT/report['owner'])
    require(reports['roof']['baseNativeReport']==specs['neighbors']['report'],'R23 must derive from exact selected saved R18b')
    require(reports['grass']['all64StoredMatrixAndRecoveredTransformExactMeasuredBeforeSaveAndAfterReload']is True,
            'Grass donor lacks exact faithful native serialization proof')
    packages=[]
    for name,spec in specs.items():
        if spec['newPackageCount']:
            basis=read(check_pin(reports['neighbors']['afterContentInventory']))if name=='roof'else content
            packages+=donor_package_manifest(Path(spec['report']['path']),reports[name],basis,
                spec['newPackagePrefix'],spec['newPackageCount'])
    require(len(packages)==len({r['relativeContentPath']for r in packages})==74,'Exact disjoint74 copied package set required')
    before_common=report_witness(reports['leaf'],True);before_extended=report_witness(reports['neighbors'],True)
    before=union_witness(before_common,before_extended)
    require(report_witness(reports['visibility'],True)==before_common and report_witness(reports['grass'],True)==before_common
        and report_witness(reports['foreground'],True)==before_extended,'Six donor original actor bases are not exact')
    require(report_witness(reports['roof'],True)==report_witness(reports['neighbors']),
            'Actual R23 source scene is not exact saved R18b witness')
    grass=module('r22_saved_original_grass','exterior-curved-grass-native-r4.py')
    grass_plan=read(check_pin(reports['grass']['selectedPlan']));result=grass.validate_plan(grass_plan,Path(reports['grass']['selectedPlan']['path']))
    grass_repair=module('r22_actual_grass_repair','exterior-curved-grass-repair-r4.py');grass_repair.validated_supplement()
    grass.transform_guard.validated_probe(result[5],result[4])
    original_values=read(check_pin(reports['grass']['originalMembersBefore']))
    expected,audit=compose_original_fields(before,base,reports['leaf'],reports['visibility'],reports['neighbors'],
        reports['grass'],result[5],original_values,grass.guard)
    templates=added_templates(before,reports)
    geometry=copy.deepcopy(base['geometry'])
    for change in reports['grass']['originalMemberChanges']:
        row=geometry['groups'][change['groupId']];row['instances']=change['retainedInstances'];row['transformsSha256']=change['retainedTransformsSha256']
    for delta in reports['visibility']['componentCullOverrides']:
        row=geometry['groups'][delta['groupId']];row['cullStartCm'],row['cullEndCm']=delta['afterCullCm']
    require(len(templates)==40 and len(geometry['groups'])==1980
        and sum(r['instances']for r in geometry['groups'].values())==631962,'Original/new actor/population composition differs')
    return {'base':base,'evidence':evidence,'content':content,'protected':protected,'reports':reports,'donors':specs,
        'inputFiles':inputs,'packages':packages,'before':before,'expectedOriginal':expected,'templates':templates,
        'originalGeometryAfter':geometry,'scopeAudit':audit,'grassRows':result[4],'grassSelected':result[5]}


def added_templates(before,reports):
    templates={}
    for name in ('neighbors','foreground'):
        saved=report_witness(reports[name]);added=reports[name]['addedActors']
        require(set(saved)-set(before)==set(added.values()),'Donor added actor witness identities differ: '+name)
        for identity,path in added.items():
            templates[name+':'+identity]={'sourceActor':path,'witness':normalize_extended_added(path,saved[path]),'donor':name}
    grass=reports['grass'];saved=report_witness(grass)
    source_template=before[read(grass['baseNativeReport']['path'])['geometry']['groups']['EX_meadow_-3_2_LawnTuft0']['actor']]
    require(set(saved)-set(before)=={g['actor']for g in grass['newGroups'].values()},'Grass exact3 new donor actor set differs')
    for identity,group in grass['newGroups'].items():
        original=copy.deepcopy(source_template);row=saved[group['actor']]
        for key,value in row.items():
            if key!='components':original[key]=copy.deepcopy(value)
        require(len(original['components'])==len(row['components'])==1,'Grass donor component schema differs')
        original['components'][0].update(copy.deepcopy(row['components'][0]))
        templates['grass:'+identity]={'sourceActor':group['actor'],'witness':original,'donor':'grass'}
    roof=reports['roof'];required={'neighbor_r18_BU_'+b+'_'+r+'_neighbor_roof_red'for b in ('572063','3800911')for r in ('roof','roof_ridge')}
    require(len(roof['componentMaterialOverrides'])==4 and {r['sourceMeshId']for r in roof['componentMaterialOverrides']}==required,
            'Exact four new neighbor roof material targets required')
    for delta in roof['componentMaterialOverrides']:
        row=templates['neighbors:'+delta['sourceMeshId']]
        require(row['sourceActor']==delta['actor'] and delta['slot']==0
            and delta['changedFields']==['materials','overrideMaterials'],'Roof cannot alter another source actor/field')
        c=component({row['sourceActor']:row['witness']},row['sourceActor'],delta['componentName'])
        require(c['mesh']==delta['mesh'] and c['materials']==[delta['beforeMaterial']] and c['overrideMaterials']==[],
                'Roof override input is not exact saved neighbor template')
        c['materials']=[delta['afterMaterial']];c['overrideMaterials']=[delta['afterMaterial']]
    return templates


def compose_all_expected(original,templates,actual_paths):
    require(set(templates)==set(actual_paths)and len(templates)==40 and len(set(actual_paths.values()))==40,
            'Exact40 disjoint new actor identities required')
    expected=copy.deepcopy(original)
    for identity,row in templates.items():
        path=actual_paths[identity];require(path not in expected,'Added actor collides with protected original')
        expected[path]=relocate_template(row['witness'],row['sourceActor'],path)
    require(len(expected)==5346,'Integrated full5346 actor counterfactual required')
    return expected


def validate_content(before,after,packages,view_sha):
    require(set(before)<=set(after)and len(before)==3975 and len(after)==4049,'Exact original3975 plus74 Content members required')
    require(sorted(k for k in before if before[k]!=after[k])==['Brezi/Maps/Brezi.umap','Data/viewpoints.json'],
            'Integration changed another original Content asset/data file')
    require(after['Data/viewpoints.json']['sha256']==view_sha,'Only pinned neighbor diagnostic view data may change')
    expected={r['relativeContentPath']: {'sha256':r['sha256'],'bytes':r['bytes']}for r in packages}
    require({k:after[k]for k in set(after)-set(before)}==expected,'Copied immutable saved donor packages changed')
    return {'changedOriginalFiles':['Brezi/Maps/Brezi.umap','Data/viewpoints.json'],'newPackageFiles':sorted(expected),
        'newUassetPackages':74,'originalContentFileCount':3975,'savedContentFileCount':4049,
        'originalNativeAssetsByteIdentical':3973,'removedOriginalFiles':[]}


def validate_plan(path=PLAN):
    path=Path(path).resolve();require(path==PLAN,'Only registered final R22 plan may execute')
    plan=read(path);require(plan['schema']==SCHEMA and plan['owner']=='scripts/unreal/exterior-realism-integration-study-r22.py'
        and plan['status']=='source-only-saved-donor-integration-native-pending'and plan['audit']==EXPECTED,
        'Unregistered final integration plan')
    require(all(plan[k]is False for k in ('nativeExecuted','nativeAppearanceAccepted','fullPhotorealismAccepted',
        'performanceAccepted','shippingPackageProduced')),'Source plan claims combined acceptance')
    bundle=load_donors()
    require(plan['baseNativeReport']==pin(BASE/'exterior-import-report.json') and plan['donors']==bundle['donors']
        and read(check_pin(plan['copiedPackages']))==bundle['packages']
        and read(check_pin(plan['originalBeforeWitness']))==bundle['before']
        and read(check_pin(plan['originalExpectedWitness']))==bundle['expectedOriginal']
        and read(check_pin(plan['addedActorTemplates']))==bundle['templates']
        and read(check_pin(plan['originalGeometryAfter']))==bundle['originalGeometryAfter']
        and plan['scopeAudit']==bundle['scopeAudit'],'Integration source counterfactual/saved donors changed')
    owned={'producer':'exterior-realism-integration-study-r22.py','native':'exterior-realism-integration-native-r22.py',
        'guards':'exterior-realism-integration-guards-r22.py','rootCopy':'exterior-realism-integration-copy-r22.py',
        'tests':'test_exterior_realism_integration_r22.py','design':'../../docs/unreal-realism-integration-r22.md'}
    require(set(plan['ownedSources'])==set(owned),'Exact six owned integration source roles required')
    expected_inputs=dict(bundle['inputFiles'])
    for role,filename in owned.items():
        row=plan['ownedSources'][role];live=check_pin(row['live']);snapshot=check_pin(row['snapshot'])
        require(live==(ROOT/'scripts/unreal'/filename).resolve()and snapshot==STUDY/('source-'+live.name)
            and live!=snapshot and row['live']['sha256']==row['snapshot']['sha256'],
                'New integration source snapshot differs')
        expected_inputs[str(live)]=row['live']['sha256'];expected_inputs[str(snapshot)]=row['snapshot']['sha256']
    for key in ('originalBeforeWitness','originalExpectedWitness','addedActorTemplates','originalGeometryAfter','copiedPackages'):
        row=plan[key];require(check_pin(row)==STUDY/(key+'.json'),'Canonical integration sidecar required')
        expected_inputs[row['path']]=row['sha256']
    view=bundle['reports']['neighbors']['diagnosticViewpoint']['viewpointFile']
    require(plan['diagnosticViewpoints']==view,'Exact saved original-prefix/R18 diagnostic camera required')
    expected_inputs[view['path']]=view['sha256']
    require(plan['inputFiles']==expected_inputs,'Integration consumed source closure is not exact')
    for file,h in plan['inputFiles'].items():require(sha(file)==h,'Integration consumed source changed: '+file)
    tests=read(check_pin(plan['sourceGuardTests']))
    require(tests['status']=='passed'and tests['testCount']==12 and tests['exitCode']==0 and tests['nativeExecuted']is False,
            'Integration counterfactual CPU fixtures failed')
    return plan,bundle
