"""Closed R37 selected R36b plus exact saved yard integration.

Only the two actual saved garden reports below can be selected. The frozen
source draft is reused without editing its globals or provenance. No launch,
project copy, source regeneration, or geometry conversion occurs here.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-yard-integration-guards-r37-r2.py'
SCHEMA = 'brezi-r37-clean-selected-garden-plus-saved-yard'
REPAIR_SCHEMA='brezi-r37-exact-material-snapshot-reader-dispatch-r2'
NATIVE_OWNER = 'scripts/unreal/exterior-garden-yard-integration-native-r37-r2.py'
STUDY_OWNER = 'scripts/unreal/exterior-garden-yard-integration-study-r37-r2.py'
STUDY = ROOT/'output/unreal/exterior-garden-yard-integration-20261002-r37-native-study-r2'
PLAN = STUDY/'garden-yard-integration-plan-r2.json'
CANDIDATE = ROOT/'output/unreal/exterior-20261002-r37b'
INITIAL_STATUS = 'verified-selected-saved-garden-independent-apfs-r37-clone-before-yard-package-copy'
COPY_STATUS = 'verified-byte-identical-independent-apfs-r37-fourteen-saved-yard-packages-before-integration'
CLONE_STATUS = 'verified-byte-identical-independent-apfs-r37-selected-garden-and-fourteen-yard-packages-before-native'

SELECTED_BASE_KEY = 'R36b'
SELECTED_REVIEW_PIN = {'path': str(ROOT/'output/unreal/exterior-garden-yard-20261002-r37-base-selection/root-base-selection.json'),
 'sha256': '0623b34a32376545ded6117d439050f8ed09ce9e4734cc8197791b7734af2836', 'bytes': 3153}
CLONE_PIN = {'path': str(CANDIDATE/'garden-yard-project-clone.json'),
 'sha256': 'a456fc5bf8ef660ee2c96e12a473bf44792f92cf3b030c516149fe2e10a12e33', 'bytes': 2182667}
CLONE_SCHEMA = 'brezi-garden-yard-clean-integration-project-clone-r37'
CLONE_STATUS = 'verified-selected-r36b-independent-apfs-clone-plus-fourteen-exact-yard-donor-packages'

ALLOWED_BASES = {
 'R34': {'report': ROOT/'output/unreal/exterior-20261002-r34a/garden-fern-only-native-report.json',
  'sha256': 'd233329bee2ffcb95419c8266ff8c1f50931ba8f642ded23ab20330f1d334cb8',
  'owner': 'scripts/unreal/exterior-garden-fern-only-native-r34.py', 'schemaVersion': 1,
  'status': 'verified-saved-36-original-fern-garden-all-ornamentals-retained', 'pid': 21209,
  'terminal': 'garden-fern-only-native-process.json', 'pins': 472,
  'audit': 'root-native-byte-audit-r34a.json',
  'auditSha256': 'c75becbc961f81dc5e0499399c0890eec50baecfabd3a514b5232abd1d7bca1e'},
 'R36b': {'report': ROOT/'output/unreal/exterior-20261002-r36b/garden-periwinkle-native-report-r2.json',
  'sha256': 'd2057c860c0b5135cd19beaee776145d89c3377a07ff08abee9537f6a15c765e',
  'owner': 'scripts/unreal/exterior-garden-periwinkle-native-r36-r2.py', 'schemaVersion': 2,
  'status': 'verified-saved-384-original-periwinkle-low-garden-composition', 'pid': 47851,
  'terminal': 'garden-periwinkle-native-r2-process.json', 'pins': 588,
  'audit': 'root-native-success-byte-audit-r36b-r2.json',
  'auditSha256': 'a2be8c8a3d5c50ee60b5ee78d1426bb4c322d0de2bcb1c13a6734959159253e8'},
}


def require(condition, message):
 if not condition:
  raise RuntimeError(message)


def sha(path):
 h = hashlib.sha256()
 with Path(path).open('rb') as stream:
  for block in iter(lambda: stream.read(1024*1024), b''):
   h.update(block)
 return h.hexdigest()


def pin(path):
 path = Path(path).resolve()
 return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def read(path):
 return json.loads(Path(path).read_text())


def digest(value):
 return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',', ':'),allow_nan=False).encode()).hexdigest()


def write(path,value):
 with Path(path).open('x') as stream:
  json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def checked(row):
 require(row is not None and set(row)in ({'path','sha256'},{'path','sha256','bytes'})
         and all(pin(row['path'])[key]==value for key,value in row.items()), 'Pending or changed immutable binding pin')
 return Path(row['path'])


def module(name, row):
 path = checked(row)
 s = importlib.util.spec_from_file_location(name, path)
 m = importlib.util.module_from_spec(s)
 s.loader.exec_module(m)
 return m


def draft_packet():
 ready_path = ROOT/'output/unreal/exterior-garden-yard-integration-20261002-source-draft-r1/source-draft-readiness.json'
 require(sha(ready_path) == 'b455351dff7f128c22eae6e4cc82cee72d7e0dea6bc64a23224addf59c389e04',
         'Frozen independent source draft readiness differs')
 ready = read(ready_path)
 for row in ready['ownedSources'].values():
  checked(row)
 g = module('r37_frozen_draft_source', ready['ownedSources'][str(ROOT/'scripts/unreal/exterior-garden-yard-integration-source-draft.py')])
 kernels = module('r37_frozen_draft_native', ready['ownedSources'][str(ROOT/'scripts/unreal/exterior-garden-yard-integration-native-draft.py')])
 return g, kernels, g.load_donors(), pin(ready_path)


def source_process(report, entry):
 terminal_path = Path(report['output'])/entry['terminal']
 terminal = read(terminal_path)
 raw_path = Path(terminal['processFile'])
 raw = read(raw_path)
 require(raw['pid'] == report['nativeProcessId'] == entry['pid'] and raw['code'] == 0
         and raw['signal'] is None and terminal['sourcePinsUnchangedAfterNative'] is True
         and len(terminal['sourcePinsBeforeNative']) == entry['pins']
         and terminal['reportSha256'] == entry['sha256']
         and sha(raw_path) == terminal['processFileSha256']
         and sha(terminal['logFile']) == terminal['logSha256'],
         'Selected actual garden native process/log/source closure differs')
 require(raw['command'] == '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd'
         and raw['args'][0] == str(Path(report['project'])/'BreziTwin.uproject')
         and '-script='+str(ROOT/report['owner']) in raw['args']
         and '-run=pythonscript' in raw['args'] and '-nullrhi' in raw['args'],
         'Selected actual garden executable/project/owner arguments differ')
 for path, value in terminal['sourcePinsBeforeNative'].items():
  require(sha(path) == value, 'Selected native consumed source changed')
 return {'receipt': pin(terminal_path), 'raw': pin(raw_path), 'log': pin(terminal['logFile']),
         'pid': entry['pid'], 'exitCode': 0, 'sourcePinCount': entry['pins']}


def selected_base():
 require(SELECTED_BASE_KEY in ALLOWED_BASES and SELECTED_REVIEW_PIN is not None,
         'Actual original-PNG garden selection has not been bound')
 entry = ALLOWED_BASES[SELECTED_BASE_KEY]
 require(sha(entry['report']) == entry['sha256'], 'Only exact allowed saved garden report eligible')
 report = read(entry['report'])
 require(report['owner'] == entry['owner'] and report['schemaVersion'] == entry['schemaVersion']
         and report['status'] == entry['status'] and report['nativeApplied'] is True
         and report['savedMapUnloadedReloaded'] is True and report['sourceInputsUnchanged'] is True
         and report['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
         and report['setbacksMm'] == {'street': 3000, 'east': 3000},
         'Exact selected native garden identity/design/reload required')
 review = read(checked(SELECTED_REVIEW_PIN))
 require(review['schema'] == 'brezi-root-r37-garden-base-visual-selection-r1'
         and review['selectedBase'] == report['output']
         and review['selectedBaseNativeReport'] == pin(entry['report'])
         and review['rootAndIndependentPeerViewedOriginals'] is True
         and review['selectedOnlyForNextCombinedCandidateReview'] is True
         and review['originalImagePixelsEdited'] is False
         and review['fullPhotorealismAccepted'] is review['performanceAccepted'] is False,
         'Explicit actual original-PNG root selection receipt required')
 checked(review['selectedOriginalR36'])
 checked(review['comparisonOriginalR34'])
 checked(review['actualEditorSuite'])
 checked(review['actualEditorProcess'])
 audit_path = Path(report['output'])/entry['audit']
 require(sha(audit_path) == entry['auditSha256'], 'Selected actual current byte audit changed')
 audit = read(audit_path)
 require(audit.get('nativeReport', audit.get('report')) == pin(entry['report'])
         and review['selectedBaseCurrentByteAudit'] == pin(audit_path),
         'Selected byte audit must bind its exact native report')
 g, kernels, donors, ready = draft_packet()
 before = read(checked(report['savedActorWitness']))
 require(before == read(checked(report['expectedActorWitness']))
         and digest(before)==report['savedActorWitnessSha256']==report['expectedActorWitnessSha256'],
         'Exact actual selected saved full counterfactual required')
 g.selected_target_compatibility(before, donors)
 return {'key': SELECTED_BASE_KEY, 'report': report, 'reportPin': pin(entry['report']),
         'process': source_process(report, entry), 'audit': pin(audit_path), 'review': SELECTED_REVIEW_PIN,
         'project': Path(report['project']), 'before': before,
         'content': read(checked(report['afterContentInventory'])),
         'protected': read(checked(report['protectedProjectProof'])),
         'draftSource': g, 'draftNative': kernels, 'donors': donors, 'draftReadiness': ready}


def counts(before, donors, base_report):
 templates = donors['inventory']['addedYardActorTemplates']
 changed = donors['inventory']['changedOriginalActorTargets']
 counterfactual_original = copy.deepcopy(before)
 for actor, row in changed.items():
  counterfactual_original[actor] = row['recordedFinalYardWitness']
 def census(witness):
  cs = [c for row in witness.values() for c in row['components']
        if c['class'] == '/Script/Engine.HierarchicalInstancedStaticMeshComponent']
  return len(witness), len(cs), sum(c['instanceCount'] for c in cs)
 original = census(before)
 original_after = census(counterfactual_original)
 new_components = [c for row in templates.values() for c in row['components'] if 'instanceCount' in c]
 actual = base_report['actualCounts']
 require(original == (actual['savedActors'], actual['fullHismComponents'], actual['fullHismInstances'])
         and original_after[2] == original[2]-34 and len(new_components) == 3
         and sum(c['instanceCount'] for c in new_components) == 1274,
         'Actual selected full witness/donor-derived projected counts differ')
 return {'originalActors': original[0], 'savedActors': original_after[0]+len(templates),
         'fullHismComponents': original_after[1]+len(new_components),
         'fullHismInstances': original_after[2]+1274,
         'addedActors': 4, 'addedHismGroups': 3, 'newRoots': 1274,
         'retiredOriginalEcologyRoots': 34, 'retainedAffectedEcologyRoots': 1919,
         'newCopiedPackages': 14, 'newTextureObjects': 0,
         'scopedMaterialGraphs': actual['scopedMaterialGraphs']+3,
         'scopedTextureObjects': actual['scopedTextureObjects'],
         'contentFiles': actual['contentFiles']+14, 'protectedFiles': actual['protectedFiles']}


def validate_clone(bundle):
 path = checked(CLONE_PIN)
 row = read(path)
 project = CANDIDATE/'Project/BreziTwin'
 require(row['schema'] == CLONE_SCHEMA and row['schemaVersion']==1 and row['status'] == CLONE_STATUS
         and row['sourceProject'] == str(bundle['project']) and row['project'] == str(project)
         and row['nativeBaseReport'] == bundle['reportPin'] and row['rootBaseSelection'] == bundle['review']
         and row['baseCurrentByteAudit']==bundle['audit']
         and row['donorInventory']==pin(bundle['draftSource'].INVENTORY)
         and row['selectedPlan'] is row['sourceProposal'] is row['sourcePreflight'] is None
         and row['nativeExecuted'] is False and row['nativePreflightPending'] is True,
         'Fresh root-owned selected-base clone contract differs')
 expected = {'Content/'+key: value for key, value in bundle['content'].items()}
 expected.update(bundle['protected'])
 seen = set()
 for item in row['files']:
  source, destination = Path(item['source']), Path(item['destination'])
  relative = destination.relative_to(project).as_posix()
  require(relative in expected and relative not in seen
          and source == bundle['project']/relative and item['independentInodes'] is True
          and {k: item[k] for k in ('sha256', 'bytes')} == expected[relative]
          and source.stat().st_size == destination.stat().st_size == item['bytes']
          and (source.stat().st_dev, source.stat().st_ino) != (destination.stat().st_dev, destination.stat().st_ino),
          'Exact independent original clone row differs')
  seen.add(relative)
 require(seen == set(expected) and row['fileCount'] == len(expected)==4218, 'Complete original clone file set required')
 packages=bundle['donors']['inventory']['packages']
 copies=[{'source':v['source']['path'],'destination':str(project/'Content'/v['relativeContentPath']),
          'sha256':v['source']['sha256'],'bytes':v['source']['bytes'],'independentInodes':True,
          'relativeContentPath':v['relativeContentPath'],'donorReport':v['donorReport'],'asset':v['asset']} for v in packages]
 require(row['copiedDonorPackages']==copies and row['donorPackageCount']==14
         and row['contentFiles']==4086 and row['protectedFiles']==132
         and row['preparedProjectFiles']==4232 and row['preparedContentFiles']==4100,
         'Exact independent fourteen saved donor package rows required')
 prepared=read(checked(row['preparedContentInventory']))
 additions={v['relativeContentPath']:{k:v['source'][k]for k in ('sha256','bytes')}for v in packages}
 require(prepared=={**bundle['content'],**additions}, 'Exact prepared base plus fourteen membership required')
 for item in copies:
  a,b=Path(item['source']),Path(item['destination'])
  require(not b.is_symlink() and a.stat().st_size==b.stat().st_size==item['bytes']
          and (a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino),
          'Copied donor must retain independent own inode and original size')
 checked(row['byteValidationHelper']);checked(row['rootController'])
 bundle['preparedContent']=prepared
 bundle['clone']=pin(path)
 return pin(path)


def validate_plan_header(plan,bundle):
 require(plan['schema'] == SCHEMA
         and plan['schemaVersion']==2 and plan['status']=='source-ready-selected-saved-r36b-yard-and-exact-graph-readers-r2-native-pending'
         and plan['repairSchema']==REPAIR_SCHEMA and plan['priorFailedAttempt']==prior_failed_attempt()
         and plan['materialReaderDispatch']==reader_dispatch(bundle)
         and plan['owner'] == STUDY_OWNER and plan['nativeOwner'] == NATIVE_OWNER
         and plan['baseNativeReport'] == bundle['reportPin'] and plan['selectedRootReview'] == bundle['review']
         and plan['baseNativeProcess'] == bundle['process'] and plan['baseCurrentByteAudit'] == bundle['audit']
         and plan['draftReadiness'] == bundle['draftReadiness']
         and plan['projectClone'] == validate_clone(bundle)
         and plan['expectedCounts'] == counts(bundle['before'], bundle['donors'], bundle['report'])
         and plan['candidateOutput'] == str(CANDIDATE)
         and plan['baseKey']==SELECTED_BASE_KEY
         and plan['copiedPackageScope']==bundle['donors']['inventory']['packages']
         and plan['targetOriginalActorWitnesses']==bundle['donors']['inventory']['changedOriginalActorTargets']
         and plan['addedActorTemplates']==bundle['donors']['inventory']['addedYardActorTemplates']
         and plan['donorInventory']==pin(bundle['draftSource'].INVENTORY)
         and plan['newActorIdentityPolicy'] == 'FRESH_NATIVE_SPAWN_MAPPING_BEFORE_CONFIGURATION_NO_EXISTING_ID_REUSE'
         and plan['rootConstructorReplayPolicy']=='ORIGINAL_R32_SOURCE_XYZ_YAW_SCALE_THEN_EXACT_INPUT_RECOVERED_MATRIX_AND_NATIVE_WRAPPED_ROWS'
         and plan['cpuTests']['testCount']==8 and plan['cpuTests']['exitCode']==0 and plan['cpuTests']['nativeExecuted']is False
         and plan['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}
         and plan['setbacksMm']=={'street':3000,'east':3000}
         and all(plan[k]is False for k in ('nativeApplied','nativeExecuted','gpuExecuted','shippingVerified','packageVerified',
            'wholeR35MapOrR30GardenImported','sourceGeometryRegenerated','sourcePixelsEdited',
            'nativeNormalTangentReadbackAvailable','additionalRandomSeedRangesReadbackAvailable'))
         and plan['nativeAppearanceAccepted'] is plan['fullPhotorealismAccepted'] is plan['performanceAccepted'] is False,
         'Exact selected-base source plan scope differs')
 require(plan['frozenFirstHelperEvidence']==pin(ROOT/'output/unreal/exterior-realism-clean-integration-20261002-r27-study/realism-clean-integration-plan.json')
         and plan['frozenFirstHelperEvidence']['sha256']=='662ea41663142e22ff744530fd0337833389beaed1b1ca590e6a6cd53aa511a4'
         and plan['synchronizeInstanceBoundsSource']==pin(bundle['project']/'Source/BreziTwin/BreziVegetationPatch.cpp'),
         'Exact frozen-first helper and actual selected source method bindings required')
 wanted={'exterior-garden-yard-integration-'+kind+'-r37-r2.py'for kind in ('native','study','guards')}|{'test_exterior_garden_yard_integration_r37_r2.py'}
 require(set(plan['ownedSources'])==set(plan['sourceSnapshots'])==wanted,'Exact four source owners/snapshots required')
 for name,row in plan['ownedSources'].items():
  require(row==pin(ROOT/'scripts/unreal'/name)and plan['sourceSnapshots'][name]==pin(STUDY/name)
          and row['sha256']==plan['sourceSnapshots'][name]['sha256'],'Live/snapshot own source differs')
 checked(plan['cpuTests']['source']);checked(plan['cpuTests']['log'])
 return True


def validate_plan():
 require(PLAN.is_file(), 'R37 final bound source plan is pending')
 bundle = selected_base()
 plan = read(PLAN)
 validate_plan_header(plan,bundle)
 for path, value in plan['inputFiles'].items():
  require(sha(path) == value, 'R37 bound input changed')
 return plan, bundle


def source_packet(bundle,h):
 """Load pinned serialized source arrays, without replaying historical producers."""
 donors=bundle['donors'];r32=donors['reports']['yardR32'];r35=donors['reports']['yardRepairR35']
 proposal=donors['r32Proposal'];plan=donors['r32SourcePlan']
 layout=read(checked(proposal['retainedLayout']))
 lp=read(ROOT/'output/unreal/exterior-context-yard-20261002-r28-study/yard-source-plan.json')
 native=read(checked(lp['inputFiles']['nativeR16']))
 originals={m['id']:m for m in native['savedPlantReadback']}
 polygons=h['r32'].guard.source.old.index_helper()
 masks={k:polygons._PolygonIndex(v)for k,v in read(checked(proposal['sourceExclusionMasks'])).items()}
 ground={'proposal':proposal,'layout':layout,'masks':masks,
         'plantingDomains':{k:polygons._PolygonIndex(v)for k,v in proposal['plantingDomainsCm'].items()},
         'nativeMasters':{k:originals[k]for k in h['r32'].guard.MODELS}}
 repair=read(checked(r35['sourceProposal']))
 coverage=read(checked(repair['repairBHardUnionCoverage']['variant']))
 records={m['id']:copy.deepcopy(m)for m in proposal['meshes']}
 for variant in coverage['variants']:
  row=records[variant['meshId']]
  require(variant['allOtherGeometrySourceArraysSha256']=={k:digest(row[k])for k in ('verticesCm','normals','uv0','indices')},
          'Original complete hard source arrays changed outside UV1.R')
  require(len(row['uv1'])==len(variant['proposedUv1F32'])and all(a[1]==b[1]for a,b in zip(row['uv1'],variant['proposedUv1F32'])),
          'Hard source UV1.G changed')
  row['uv1']=variant['proposedUv1F32']
 ec=read(ROOT/'output/unreal/exterior-canopy-ecology-20260930-r4/canopy-ecology-plan.json')
 require(sha(ROOT/'output/unreal/exterior-canopy-ecology-20260930-r4/canopy-ecology-plan.json')=='27d66e0032c3b8648e5c74f80dc675efb3bee0a4efde00a1549a4502cc86b576','Frozen ecology source changed')
 manifest=read(checked(ec['geometryManifest']));models={m['id']:m for m in manifest['meshes']}
 source_groups={v['id']:v for v in ec['groups']};groups={}
 for row in repair['repairAOriginalEcologyRetirements']['affectedGroups']:
  original=donors['ecologyOriginal'][row['groupId']]
  groups[row['groupId']]={**row,'sourceRows':source_groups[row['groupId']]['instances'],
    'originalWitness':bundle['before'][row['actor']],'mesh':original['mesh']}
 decoded={};paths={}
 for group in groups.values():paths.setdefault(models[group['modelId']]['glbPath'],set()).add(group['modelId'])
 for path,ids in paths.items():
  for model in ids:require(sha(path)==models[model]['glbSha256'],'Original ecology GLB changed')
  decoded.update(h['r35'].guard.decode_ecology(path,ids))
 ecology={'ecologyGroups':groups,'ecologySourceModels':decoded,
          'hardFootprints':{r['id']:r['domainCm']for r in layout['surfaces']if r['role']in ('entry_walk','service_court')}}
 material={'materialVariant':read(checked(repair['repairCSingleBackdropNearPbr']['variant'])),
           'materialSharedTextures':r35['repairC']['materialReport']['sharedTextureWitness'],
           'base':{'native':h['r32']}}
 return {'ground':ground,'groundRecords':records,'ecology':ecology,'material':material,
         'recipes':read(checked(plan['materialCopyProposals']))}


def immutable_inputs(bundle):
 files={}
 def walk(value):
  if isinstance(value,dict):
   if 'path'in value and 'sha256'in value:
    p=Path(value['path']);require(p.is_absolute(),'Absolute source pin required')
    require(sha(p)==value['sha256'],'Immutable source pin changed');files[str(p)]=value['sha256']
   for key,v in value.items():
    if isinstance(key,str)and key.startswith('/')and isinstance(v,str)and len(v)==64:
     require(sha(key)==v,'Recorded consumed source hash changed');files[key]=v
    else:walk(v)
  elif isinstance(value,list):
   for v in value:walk(v)
 walk(bundle['report']);walk(bundle['donors']['inventory']);walk(bundle['review']);walk(bundle['audit']);walk(bundle['clone'])
 for row in (bundle['reportPin'],bundle['draftReadiness'],*bundle['process'].values()):
  if isinstance(row,dict):walk(row)
 for report in bundle['donors']['reports'].values():walk(report)
 # Actual terminal source closures remain immutable evidence, not fresh native output.
 for report,stem in ((bundle['donors']['reports']['yardR32'],'context-yard-ground-native-process.json'),
                     (bundle['donors']['reports']['yardRepairR35'],'context-yard-repair-native-r2-process.json')):
  terminal=Path(report['output'])/stem;walk(pin(terminal));walk(read(terminal))
 clone=read(checked(CLONE_PIN));walk(clone['preparedContentInventory']);walk(clone['byteValidationHelper']);walk(clone['rootController'])
 return files


def reader_dispatch(bundle):
 recorded=read(checked(bundle['report']['originalProtectedControlsSaved']))
 materials=recorded['originalMaterials'];clean=materials['original56']['clean']
 neighbor={row['asset']for row in clean['neighbor']['materials'].values()}
 tree={row['asset']for row in materials['originalTree3']['materials'].values()}
 assets=set(clean['verifiedMaterialAssets'])|{row['asset']for row in materials['original56']['yard']}|tree|{
  recorded['originalFernMaterialReport']['delegate']['asset'],bundle['report']['materialReport']['asset']}
 require(len(assets)==61 and len(neighbor)==9 and len(tree)==3 and not neighbor&tree and neighbor|tree<=assets,
         'Exact source61 material assets and9/3 explicit snapshot owners required')
 result={'basic':sorted(assets-neighbor-tree),'neighbor':sorted(neighbor),'tree':sorted(tree)}
 require(len(result['basic'])==49,'Exactly49 historical basic snapshot assets required')
 return result


def prior_failed_attempt():
 root=ROOT/'output/unreal/exterior-20261002-r37a'
 paths={'report':root/'garden-yard-integration-native-report.json',
        'terminal':root/'garden-yard-integration-native-process.json',
        'raw':root/'garden-yard-integration-native.log.json','log':root/'garden-yard-integration-native.log',
        'audit':root/'root-native-failure-byte-audit-r37a-r1.json'}
 pins={k:pin(v)for k,v in paths.items()}
 hashes={'report':'c9edd3527435941dee5a42d28ab7eaac00d213f7016ca7d0a3e53d124ced6e4c',
         'terminal':'729bb1f2aa334310cd4e5c9c4ee096ead35913af2bda203ca1321f0f2b01c277',
         'raw':'4783a06b5895f2955fc8b03b895cf2d88b0612cb8f473db0aa7a1aa360dd49b7',
         'log':'bb0bc1be1802fbcef66463eee525f639764376188359aee57f645dfa53f66aa6',
         'audit':'06dc57c10ab1b615318ba14c681ec71f5e1f1b9dda176b10c62a7c2a6dc8fc33'}
 require(all(pins[key]['sha256']==value for key,value in hashes.items()),
         'Original immutable failed R37 report/byte audit changed')
 report,terminal,raw,audit=(read(paths[k])for k in ('report','terminal','raw','audit'))
 require(report['owner']=='scripts/unreal/exterior-garden-yard-integration-native-r37.py'
         and report['status']=='failed'and report['error']=='Original selected full material graph changed'
         and report['nativeApplied']is False and raw['pid']==report['nativeProcessId']==53262
         and raw['code']==255 and raw['signal']is None
         and terminal['sourcePinsUnchangedAfterNative']is True and len(terminal['sourcePinsBeforeNative'])==832
         and audit['allPreparedCandidateBytesExact']is audit['all4218SelectedR36SourceProjectFilesExact']is True
         and audit['noCandidateMapOrPackageByteChange']is audit['failedBeforeDeclaredSceneMutation']is True
         and audit['checkpointFiles']==[] and audit['failingMaterialIdentityObserved']is False,
         'Actual R37 first failure/process/byte-scope evidence differs')
 require(terminal['processFileSha256']==pins['raw']['sha256']and terminal['logSha256']==pins['log']['sha256']
         and terminal['reportSha256']==pins['report']['sha256'],'Original failed process/log hash closure differs')
 for path,value in terminal['sourcePinsBeforeNative'].items():require(sha(path)==value,'Original failed attempt source changed')
 return {'schema':'brezi-r37-preserved-before-mutation-reader-schema-failure-r1','actualPid':53262,'actualExitCode':255,
         'files':pins,'sourcePinCount':832,'failingAssetActuallyRecorded':False,'sceneOrAssetMutationOccurred':False}
