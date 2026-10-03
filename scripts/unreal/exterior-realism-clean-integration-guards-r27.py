"""Closed four-saved-donor source composition from untouched original R16.

No original grass member is removed, restored, reordered or recomposed. R20
coverage regression and R23 roof color/grid-seam experiment are excluded.
CPU guards use actual saved donor receipts, not new native appearance proof.
"""
import copy
import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-realism-clean-integration-guards-r27.py'
BASE=ROOT/'output/unreal/exterior-20261001-r16a'
BASE_SHA='1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122'
SCHEMA='brezi-exterior-realism-clean-four-saved-donor-integration-r27'
STUDY=ROOT/'output/unreal/exterior-realism-clean-integration-20261002-r27-study'
PLAN=STUDY/'realism-clean-integration-plan.json'
CANDIDATE=ROOT/'output/unreal/exterior-20261002-r27a'
INITIAL_STATUS='verified-original-r16-independent-apfs-r27-clone-before-clean-package-copy'
COPY_STATUS='verified-byte-identical-independent-apfs-59-clean-donor-packages-before-integration'
CLONE_STATUS='verified-byte-identical-independent-apfs-r27-project-clone-and-59-native-packages-before-integration'
COPY_OWNER='scripts/unreal/exterior-realism-clean-integration-copy-r27.py'
SOURCE_STATUS='source-only-four-saved-donor-clean-integration-native-pending'
ORIGINAL_BEFORE=ROOT/'output/unreal/exterior-realism-integration-20261002-r22-study/originalBeforeWitness.json'
ORIGINAL_BEFORE_SHA='0ed97839fc63844bfb02e8e311d477302e1f524532b17263bb86b18f47f60c06'
GRASS_GROUPS={f'EX_meadow_-3_2_LawnTuft{i}':count for i,count in enumerate((2230,2190,2288,2241))}
EXPECTED={'originalContentFiles':3975,'copiedNewPackages':59,'savedContentFiles':4034,
    'originalActors':5306,'savedActors':5343,'savedRecordedExteriorHismGroups':1984,'savedRecordedExteriorHismInstances':632538,
    'originalFullSceneHismComponents':2305,'originalFullSceneHismInstances':676432,
    'savedFullSceneHismComponents':2309,'savedFullSceneHismInstances':676944,
    'scopedMaterialGraphs':54,'scopedTextureObjects':77,'originalMaterialGraphs':42,'originalTextureObjects':74,
    'leafGroups':23,'leafInstances':78,'visibilityOriginalGroups':601,'visibilityOriginalInstances':501890,
    'visibilityRetainedInstances':501890,'originalGrassGroupsPreserved':4,'originalGrassMembersPreserved':8949,
    'originalGrassRemovedMembers':0,'newGrassReplacementGroups':0,'roofPbrComponentOverrides':0,
    'neighborAddedActors':32,'neighborRetainedRebinds':5,'neighborEmptyChunkHidden':1,
    'foregroundAddedActors':5,'foregroundNewGroups':4,'foregroundNewRoots':512,'foregroundFloorTriangles':1843}
DONORS={'leaf': ('exterior-20261001-r17a', 'canopy-transmission-native-report.json', 'canopy-transmission-native', 'exterior-canopy-transmission-native.py', '91198a555bbf11d3636d14445a5cb743276f229123a5bb69d6efe47b2fc11647', 'verified-saved-canopy-transmission-component-overlay', '/Game/Brezi/CanopyTransmissionR1', 2), 'visibility': ('exterior-20261001-r19a', 'meadow-visibility-native-report.json', 'meadow-visibility-native', 'exterior-meadow-visibility-native.py', 'b92b4cc3bac23cf4255ab8f1f7471f5b1722a6aff9bbad5ca9e807ddc6e5f55d', 'verified-saved-meadow-ecology-visibility-component-overlay', None, 0), 'neighbors': ('exterior-20261001-r18b', 'neighbor-finish-overlay-report-r3.json', 'neighbor-finish-native-r3', 'exterior-neighbor-finish-native-r3.py', '40ccc7cc686e2beafc05e5248eb8abe371f23bc8ad470c05284d4c442ed950da', 'neighbor-finish-native-overlay-validated', '/Game/Brezi/NeighborFinish20261001R18', 52), 'foreground': ('exterior-20261002-r21b', 'foreground-overlay-report-r2.json', 'foreground-native-r2', 'exterior-canopy-foreground-native-r2.py', '42e1bd9bc9297ce4f1e90a571c125f4df64726793d75dc7fa111ec8e69c3b942', 'foreground-native-overlay-validated', '/Game/Brezi/CanopyForeground20261002R21', 5)}

def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
g=module('r27_frozen_generic','exterior-canopy-transmission-native.py')
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

def compose_original_fields(before,baseline,leaf,visibility,neighbors):
    require(len(before)==5306,'Original full actor population required')
    expected=copy.deepcopy(before)
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
    require(retained_cull_population==501890,'All original601 groups/populations must remain intact')
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
        'originalCullInstances':501890,'retainedCullInstances':501890,'grassRemovedMembers':0,
        'grassAffectedOriginalGroups':0,'neighborRetainedRebinds':5,'neighborEmptyChunkHidden':1}

def verify_grass_preservation(before,expected,baseline):
    rows=[]
    for identity,count in GRASS_GROUPS.items():
        group=baseline['geometry']['groups'][identity]
        require(group['instances']==count,'Original four-group grass population differs')
        original=component(before,group['actor'],'Instances');changed=component(expected,group['actor'],'Instances')
        wanted=copy.deepcopy(original);wanted['instanceCullCm']=[18000,24000]
        require(changed==wanted and original['instanceCount']==count
            and original['orderedInstanceTransformsSha256']==group['transformsSha256'],
            'Clean integration cannot remove/reorder/recompose original grass or change another policy')
        rows.append({'groupId':identity,'actor':group['actor'],'component':'Instances','instances':count,
            'orderedInstanceTransformsSha256':original['orderedInstanceTransformsSha256'],
            'beforeCullCm':original['instanceCullCm'],'afterCullCm':wanted['instanceCullCm']})
    require(sum(r['instances']for r in rows)==8949,'All original8949 grass members must remain')
    return rows


def added_templates(before,reports):
    require(set(reports)==set(DONORS),'Exactly four admitted donor reports required; excluded donors rejected')
    templates={}
    for name,count in (('neighbors',32),('foreground',5)):
        saved=report_witness(reports[name]);added=reports[name]['addedActors']
        require(len(added)==count and set(saved)-set(before)==set(added.values()),'Donor exact added actor identities differ')
        for identity,path in added.items():
            templates[name+':'+identity]={'sourceActor':path,'witness':normalize_extended_added(path,saved[path]),'donor':name}
    require(len(templates)==37,'Exact32 neighbor plus5 foreground templates required')
    # The actual R18 donor retains procedural red roof defaults and no overrides.
    roofs={'neighbor_r18_BU_'+building+'_'+role+'_neighbor_roof_red'
        for building in ('572063','3800911')for role in ('roof','roof_ridge')}
    for identity in roofs:
        row=templates['neighbors:'+identity];parts=[c for c in row['witness']['components']if c.get('mesh')]
        require(len(parts)==1 and parts[0]['overrideMaterials']==[]
            and parts[0]['materials']==[reports['neighbors']['materials']['materials']['neighbor_roof_red']['asset']],
            'Clean templates must preserve actual R18 red roof material without R23 override')
    require(not any('/CurvedGrass' in str(r)or'/RoofPbr' in str(r)for r in templates.values()),'Excluded grass/roof namespace forbidden')
    return templates


def load_donors():
    require(sha(BASE/'exterior-import-report.json')==BASE_SHA,'Original saved R16 report changed')
    evidence_path=ROOT/'output/unreal/exterior-canopy-transmission-20261001-r1-study/canopy-transmission-plan.json'
    evidence=read(evidence_path);base,content,protected=g.validate_plan(evidence,evidence_path)
    reports={};specs={};inputs={str(evidence_path):sha(evidence_path),str(BASE/'exterior-import-report.json'):BASE_SHA,
        str(ROOT/g.OWNER):sha(ROOT/g.OWNER)}
    for name,(directory,filename,stem,helper,h,status,prefix,count)in DONORS.items():
        path=ROOT/'output/unreal'/directory/filename
        require(path.is_file()and sha(path)==h,'Exact actual saved donor required: '+name)
        report=read(path);require(report['owner']=='scripts/unreal/'+helper and report['status']==status
            and report['output']==str(path.parent)and report['project']==str(path.parent/'Project/BreziTwin'),
            'Typed saved donor identity/status differs: '+name)
        require(all(report[k]is False for k in ('nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted')),
            'Donor report has unapproved acceptance flags')
        require(report.get('savedMapUnloadedReloaded',report.get('savedReloaded'))is True,'Donor map not saved/reloaded')
        process=actual_terminal(path,path.parent/(stem+'-process.json'),report['owner'],stem)
        if name=='neighbors':
            expected=read(check_pin(report['expectedActorWitness']));saved=report_witness(report)
            require(len(expected)==5306 and len(saved)==5338 and all(saved[k]==v for k,v in expected.items())
                and set(saved)-set(expected)==set(report['addedActors'].values())
                and digest(saved)==report['savedActorWitnessSha256'],'R18 exact saved counterfactual/new32 differs')
        else:
            require(report['expectedActorWitnessSha256']==report['savedActorWitnessSha256'],'Saved donor expected/witness differs')
        pins_in(report,inputs);pins_in(process,inputs)
        terminal=read(process['receipt']['path']);inputs[terminal['controller']]=sha(terminal['controller'])
        inputs.update(terminal.get('sourcePinsBeforeNative',{}))
        for field in ('inputFiles','pipelineFiles'):
            for file,hash_value in report.get(field,{}).items():
                require(sha(file)==hash_value,'Saved donor source changed: '+file);inputs[file]=hash_value
        inputs[str(path)]=h;inputs[str(ROOT/report['owner'])]=sha(ROOT/report['owner'])
        reports[name]=report;specs[name]={'report':pin(path),'process':process,'nativeHelper':pin(ROOT/report['owner']),
            'newPackagePrefix':prefix,'newPackageCount':count}
    packages=[]
    for name,spec in specs.items():
        if spec['newPackageCount']:
            packages+=donor_package_manifest(Path(spec['report']['path']),reports[name],content,
                spec['newPackagePrefix'],spec['newPackageCount'])
    require(len(packages)==len({r['relativeContentPath']for r in packages})==59,'Exact disjoint59 selected packages required')
    before_common=report_witness(reports['leaf'],True);before_extended=report_witness(reports['neighbors'],True)
    before=union_witness(before_common,before_extended)
    require(report_witness(reports['visibility'],True)==before_common
        and report_witness(reports['foreground'],True)==before_extended,'Four donor original R16 actor bases differ')
    require(sha(ORIGINAL_BEFORE)==ORIGINAL_BEFORE_SHA and read(ORIGINAL_BEFORE)==before,
        'Pinned original full5306 union witness differs; never reuse dirty R22 expected witness')
    inputs[str(ORIGINAL_BEFORE)]=ORIGINAL_BEFORE_SHA
    expected,audit=compose_original_fields(before,base,reports['leaf'],reports['visibility'],reports['neighbors'])
    grass=verify_grass_preservation(before,expected,base)
    templates=added_templates(before,reports)
    geometry=copy.deepcopy(base['geometry'])
    for delta in reports['visibility']['componentCullOverrides']:
        row=geometry['groups'][delta['groupId']];row['cullStartCm'],row['cullEndCm']=delta['afterCullCm']
    require(len(geometry['groups'])==1980 and sum(r['instances']for r in geometry['groups'].values())==632026,
        'Original recorded geometry1980/632026 must preserve every member')
    return {'base':base,'evidence':evidence,'content':content,'protected':protected,'reports':reports,'donors':specs,
        'inputFiles':inputs,'packages':packages,'before':before,'expectedOriginal':expected,'templates':templates,
        'originalGeometryAfter':geometry,'scopeAudit':audit,'preservedGrassGroups':grass}


def compose_all_expected(original,templates,actual_paths):
    require(set(templates)==set(actual_paths)and len(templates)==37 and len(set(actual_paths.values()))==37,
            'Exact37 disjoint new actor identities required')
    expected=copy.deepcopy(original)
    for identity,row in templates.items():
        path=actual_paths[identity];require(path not in expected,'Added actor collides with protected original')
        expected[path]=relocate_template(row['witness'],row['sourceActor'],path)
    require(len(expected)==5343,'Integrated full5343 actor counterfactual required')
    return expected

def validate_content(before,after,packages,view_sha):
    require(set(before)<=set(after)and len(before)==3975 and len(after)==4034,'Exact original3975 plus59 Content members required')
    require(sorted(k for k in before if before[k]!=after[k])==['Brezi/Maps/Brezi.umap','Data/viewpoints.json'],
            'Integration changed another original Content asset/data file')
    require(after['Data/viewpoints.json']['sha256']==view_sha,'Only pinned neighbor diagnostic view data may change')
    expected={r['relativeContentPath']: {'sha256':r['sha256'],'bytes':r['bytes']}for r in packages}
    require({k:after[k]for k in set(after)-set(before)}==expected,'Copied immutable saved donor packages changed')
    return {'changedOriginalFiles':['Brezi/Maps/Brezi.umap','Data/viewpoints.json'],'newPackageFiles':sorted(expected),
        'newUassetPackages':59,'originalContentFileCount':3975,'savedContentFileCount':4034,
        'originalNativeAssetsByteIdentical':3973,'removedOriginalFiles':[]}

def validate_plan(path=PLAN):
    path=Path(path).resolve();require(path==PLAN,'Only registered final R27 plan may execute')
    plan=read(path);require(plan['schema']==SCHEMA and plan['owner']=='scripts/unreal/exterior-realism-clean-integration-study-r27.py'
        and plan['status']==SOURCE_STATUS and plan['audit']==EXPECTED,
        'Unregistered final integration plan')
    require(all(plan[k]is False for k in ('nativeExecuted','nativeAppearanceAccepted','fullPhotorealismAccepted',
        'performanceAccepted','shippingPackageProduced')),'Source plan claims combined acceptance')
    bundle=load_donors()
    require(plan['baseContentInventory']==bundle['evidence']['baseContentInventory']
        and plan['baseProjectProof']==bundle['evidence']['baseProjectProof']
        and plan['reusedBaseEvidencePlan']==pin(ROOT/'output/unreal/exterior-canopy-transmission-20261001-r1-study/canopy-transmission-plan.json')
        and plan['activeDesign']==bundle['base']['activeDesign']and plan['setbacksMm']==bundle['base']['setbacksMm']
        and plan['combinedAppearanceGoNoGo']=='NO_GO_UNTIL_MATCHED_NATIVE_COMBINED_REVIEW'
        and plan['originalGrassInstanceDataNeverWritten']is True and plan['seedRangeMutationApisCalled']is False
        and plan['unavailableSeedRangeReadbackMustRemainExplicit']is True, 'Clean base/design/review/seed-limit contract differs')
    require(plan['baseNativeReport']==pin(BASE/'exterior-import-report.json') and plan['donors']==bundle['donors']
        and read(check_pin(plan['copiedPackages']))==bundle['packages']
        and read(check_pin(plan['originalBeforeWitness']))==bundle['before']
        and read(check_pin(plan['originalExpectedWitness']))==bundle['expectedOriginal']
        and read(check_pin(plan['addedActorTemplates']))==bundle['templates']
        and read(check_pin(plan['originalGeometryAfter']))==bundle['originalGeometryAfter']
        and plan['scopeAudit']==bundle['scopeAudit'],'Integration source counterfactual/saved donors changed')
    owned={'producer':'exterior-realism-clean-integration-study-r27.py','native':'exterior-realism-clean-integration-native-r27.py',
        'guards':'exterior-realism-clean-integration-guards-r27.py','rootCopy':'exterior-realism-clean-integration-copy-r27.py',
        'tests':'test_exterior_realism_clean_integration_r27.py','design':'../../docs/unreal-realism-clean-integration-r27.md'}
    require(set(plan['ownedSources'])==set(owned),'Exact six owned integration source roles required')
    expected_inputs=dict(bundle['inputFiles'])
    for role,filename in owned.items():
        row=plan['ownedSources'][role];live=check_pin(row['live']);snapshot=check_pin(row['snapshot'])
        require(live==(ROOT/'scripts/unreal'/filename).resolve()and snapshot==STUDY/('source-'+live.name)
            and live!=snapshot and row['live']['sha256']==row['snapshot']['sha256'],
                'New integration source snapshot differs')
        expected_inputs[str(live)]=row['live']['sha256'];expected_inputs[str(snapshot)]=row['snapshot']['sha256']
    require(plan['originalBeforeWitness']==pin(ORIGINAL_BEFORE), 'Exact reused original5306 witness pin required')
    require(plan['preservedGrassGroups']==bundle['preservedGrassGroups'] and plan['excludedDonors']==['R20_CURVED_GRASS','R23_CREAM_ROOF'],
        'Clean exclusion/preservation contract differs')
    for key in ('originalExpectedWitness','addedActorTemplates','originalGeometryAfter','copiedPackages'):
        row=plan[key];require(check_pin(row)==STUDY/(key+'.json'),'Canonical integration sidecar required')
        expected_inputs[row['path']]=row['sha256']
    view=bundle['reports']['neighbors']['diagnosticViewpoint']['viewpointFile']
    require(plan['diagnosticViewpoints']==view,'Exact saved original-prefix/R18 diagnostic camera required')
    expected_inputs[view['path']]=view['sha256']
    tests_path=check_pin(plan['sourceGuardTests']);tests=read(tests_path);test_log=check_pin(tests['log'])
    require(tests['status']=='passed'and tests['testCount']==10 and tests['exitCode']==0 and tests['nativeExecuted']is False,
            'Integration counterfactual CPU fixtures failed')
    expected_inputs[str(tests_path)]=sha(tests_path);expected_inputs[str(test_log)]=sha(test_log)
    require(plan['inputFiles']==expected_inputs,'Integration consumed source closure is not exact')
    for file,h in plan['inputFiles'].items():require(sha(file)==h,'Integration consumed source changed: '+file)
    return plan,bundle
