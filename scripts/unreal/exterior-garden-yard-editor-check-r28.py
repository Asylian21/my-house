"""CPU-only actual R37 R2 saved garden/yard receipt checker.

Source corners and recorded raw controls are decoded independently. This does
not launch Unreal, decode fresh native actors/assets, or grant visual acceptance.
"""
import copy
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-garden-yard-editor-check-r28.py'
HELPER='scripts/unreal/exterior-garden-yard-integration-native-r37-r2.py'
HELPER_SHA='d0651c69e2d1d70563eac5e35746a85c3c06839b1d5c19c846b3dead1a90e188'
REPORT=ROOT/'output/unreal/exterior-20261002-r37b/garden-yard-integration-native-report-r2.json'
REPORT_SHA='f589c0d813ccfc35eba928a91a4545e03b159622fffa7ae2ba247545053c4532'
PLAN_SHA='e571d1eab5d9635aa5ac9a43e71d5cdd0795633121318c2fdc24e664066aa303'
PREFLIGHT_SHA='85814b5295b6157c3c8a421eb27c54c2604ad3ed863aea070768a36b6d6f93e5'
AUDIT=REPORT.parent/'root-native-success-byte-audit-r37b-r2.json'
AUDIT_SHA='5e2b2e057436049d4eabd34f3420d94b351c519094bfaed44cb10ddf24a56bf2'
NATIVE_PID=54956
SOURCE_PIN_COUNT=850
TERMINAL_PIN_COUNT=854
s=importlib.util.spec_from_file_location('r28_exact_saved_r37r2',ROOT/HELPER)
n=importlib.util.module_from_spec(s);s.loader.exec_module(n);g=n.guard
PREFLIGHT=g.STUDY/'source-preflight/source-preflight.json'
require,read,pin,sha,digest=(getattr(g,k)for k in('require','read','pin','sha','digest'))
def side(row):return read(g.checked(row))


def header(r,plan,pf,bundle):
 require(r['schema']==g.SCHEMA and r['schemaVersion']==2 and r['owner']==HELPER
  and r['repairSchema']==g.REPAIR_SCHEMA and r['status']==n.STATUS
  and r['output']==str(g.CANDIDATE)and r['project']==str(g.CANDIDATE/'Project/BreziTwin')
  and r['nativeProcessId']==NATIVE_PID,'Only actual successful R37b R2 accepted')
 true=('nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged','originalSelectedGardenUnchanged',
  'all384Periwinkle36Ferns12Heroes41FlowersRawControlsExact','all78Trees8949GrassAnd13YardShrubsRawControlsExact',
  'all1274ConstructorInputRecoveredStoredMatricesBinary64Exact','all1919SurvivorRawMatricesOrderMainSeedCustomDataExact')
 false=('nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified',
  'wholeR35MapOrR30GardenImported','materialPackagesIndependentlyUnloaded','nativeNormalTangentReadbackAvailable',
  'AdditionalRandomSeedsReadbackAvailable','perInstanceShaderRandomValuePreservationClaimed','existingTransformOrSeedSetterUsed')
 require(all(r[k]is True for k in true)and all(r[k]is False for k in false),'Executed scope or evidence limits changed')
 require(plan['schema']==g.SCHEMA and plan['schemaVersion']==2 and plan['nativeOwner']==HELPER
  and plan['owner']==g.STUDY_OWNER and plan['repairSchema']==g.REPAIR_SCHEMA
  and plan['status']=='source-ready-selected-saved-r36b-yard-and-exact-graph-readers-r2-native-pending'
  and pf['schema']==g.SCHEMA and pf['owner']==HELPER and pf['nativeExecuted']is False
  and pf['status']=='selected-garden-yard-source-preflight-validated-native-pending'
  and pf['cpuTests']==plan['cpuTests']and pf['cpuTests']['testCount']==8 and pf['cpuTests']['exitCode']==0,
  'Only executed immutable R2 source/preflight accepted')
 for key in ('selectedPlan','baseNativeReport','projectClone','moduleOrderWitness','inputFiles'):
  require(r[key]==pf[key],'Executed preflight field differs: '+key)
 require(r['selectedPlan']==pin(g.PLAN)and r['sourcePreflight']==pin(PREFLIGHT)
  and r['baseNativeReport']==plan['baseNativeReport']==bundle['reportPin']
  and r['baseNativeProcess']==plan['baseNativeProcess']==bundle['process']
  and r['baseCurrentByteAudit']==plan['baseCurrentByteAudit']==bundle['audit']
  and r['selectedRootReview']==plan['selectedRootReview']==bundle['review']
  and r['projectClone']==plan['projectClone']==g.CLONE_PIN
  and r['donorInventory']==plan['donorInventory']==pin(bundle['draftSource'].INVENTORY)
  and r['priorFailedAttempt']==plan['priorFailedAttempt']==g.prior_failed_attempt()
  and r['materialReaderDispatch']==plan['materialReaderDispatch']==g.reader_dispatch(bundle)
  and r['actualCounts']==plan['expectedCounts']==g.counts(bundle['before'],bundle['donors'],bundle['report'])
  and len(r['inputFiles'])==SOURCE_PIN_COUNT and r['inputFiles'][str(ROOT/HELPER)]==HELPER_SHA,
  'Actual selected base/repair/clone/source counterfactual differs')
 require(r['activeDesign']==plan['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'}
  and r['setbacksMm']==plan['setbacksMm']=={'street':3000,'east':3000},'C/B/B3000 changed')


def terminal_and_audit(r):
 terminal_path=g.CANDIDATE/'garden-yard-integration-native-r2-process.json';t=read(terminal_path)
 raw=side({'path':t['processFile'],'sha256':t['processFileSha256']})
 require(raw['pid']==r['nativeProcessId']==NATIVE_PID and raw['code']==0 and raw['signal']is None
  and raw['command']=='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd'
  and raw['args'][0]==str(g.CANDIDATE/'Project/BreziTwin/BreziTwin.uproject')
  and '-script='+str(ROOT/HELPER)in raw['args']and '-nullrhi'in raw['args']and '-run=pythonscript'in raw['args']
  and t['sourcePinsUnchangedAfterNative']is True and len(t['sourcePinsBeforeNative'])==TERMINAL_PIN_COUNT
  and t['reportSha256']==REPORT_SHA and sha(t['logFile'])==t['logSha256'],
  'Actual own terminal process/exit0/log/source receipt differs')
 require(all(t['sourcePinsBeforeNative'].get(p)==v for p,v in r['inputFiles'].items()),'Preflight850/terminal854 closure differs')
 for path,value in t['sourcePinsBeforeNative'].items():require(sha(path)==value,'Consumed frozen input changed')
 require(sha(AUDIT)==AUDIT_SHA,'Actual current byte audit changed');a=read(AUDIT)
 require(a['schema']=='brezi-root-r37b-native-success-current-byte-audit-r2'and a['report']==pin(REPORT)
  and a['process']==pin(terminal_path)and a['clone']==r['projectClone']
  and a['expectedRootObservedPid']==NATIVE_PID and a['expectedRootObservedPins']==TERMINAL_PIN_COUNT
  and a['currentProjectFiles']==4232 and a['currentContentFiles']==4100 and a['protectedFiles']==132
  and a['nativeCreatedAssetPackages']==0 and a['sourcePinsBeforeAfterAndCurrentExact']==TERMINAL_PIN_COUNT
  and all(a[k]is True for k in ('all4218SelectedR36SourceProjectFilesExact','all4231PreparedOwnFilesExceptMapExact',
   'allFourteenCopiedDonorPackagesIndependentAndByteExact','storedFullSceneCounterfactualEqual',
   'storedProtectedGardenTreeGrassShrubControlsExact','storedNew1274Binary64ConstructorAndRawControlsExact',
   'stored1919EcologySurvivorsRawOrderSeedCustomExact'))
  and a['newNativeActorOrGeometryDecodeByThisCpuAudit']is False,'Actual byte audit scope differs')
 return a


def counterfactual(r,bundle):
 before,declared,saved=(side(r[k])for k in('beforeActorWitness','expectedActorWitness','savedActorWitness'))
 require(before==bundle['before']and len(before)==5360,'Actual selected full5360 base differs')
 expected=bundle['draftSource'].expected_scene(before,bundle['donors'],r['newActorMapping'])
 require(expected==declared==saved and len(saved)==5364,'Full independent12-target/four-template counterfactual differs')
 for key,row in(('beforeActorWitnessSha256',before),('expectedActorWitnessSha256',expected),('savedActorWitnessSha256',saved)):
  require(r[key]==digest(row),'Full canonical scene witness hash differs')
 cs=[c for a in saved.values()for c in a['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
 require(len(cs)==2325 and sum(c['instanceCount']for c in cs)==678197,'Actual full saved HISM census differs')
 return before,saved


def binary_controls(a,b,source,message):
 require(a==b,message)
 for key in ('recoveredValues','storedMatrices','customData'):
  if key in a:source.exact(a[key],b[key],message+' '+key)


def protected(r,bundle,before,saved):
 a,b=(side(r[k])for k in('protectedControlsBefore','protectedControlsSaved'))
 require(a==b,'All protected native raw controls changed during integration')
 original=side(bundle['report']['originalProtectedControlsSaved']);trees=original['originalTrees']
 targets=dict(trees['original74'])
 r29=read(ROOT/'output/unreal/exterior-20261002-r29a/original-tree-group-native-report.json')
 targets[r29['newOriginalTreeGroup']['actor']]=trees['ownedR29Four']
 targets.update(side(bundle['report']['retainedGardenControlsSaved']))
 targets.update(original['preserved36FernControls'])
 measurements=side(bundle['report']['newSourceNativeMeasurements'])
 for model,row in bundle['report']['newOwnedGroups'].items():targets[row['actor']]=measurements[model]
 oldyard=side(bundle['donors']['reports']['yardRepairR35']['originalControlsSaved'])['all13YardShrubsAnd1274LowRootsRawControls']
 targets.update({p:v for p,v in oldyard.items()if p in before and before[p]['label'].startswith('EX_context_yard_r28_')})
 require(set(a['rawActorControls'])==set(targets),'Only exact selected tree/garden/fern/periwinkle/shrub raw controls required')
 for actor,expected in targets.items():
  got=a['rawActorControls'][actor];binary_controls(got,b['rawActorControls'][actor],bundle['draftSource'],'Protected raw binary64 changed')
  for key in ('recoveredValues','storedMatrices'):
   bundle['draftSource'].exact(got[key],expected[key],'Protected actual selected source raw frame differs')
  for key in ('mainRandomSeed','numCustomDataFloats','customData'):
   if key in expected:require(got[key]==expected[key],'Protected selected source main seed/custom changed')
  require(got['instanceCount']==len(got['recoveredValues'])==len(got['storedMatrices'])
   and before[actor]==saved[actor]and digest(got['recoveredValues'])==saved[actor]['components'][0]['orderedInstanceTransformsSha256']
   and got['additionalRandomSeedsReadbackAvailable']is got['seedRangesReconstructed']is False,'Raw control/order/full component binding differs')
 require(a['original8949Grass']==original['original8949Grass']
  and digest(a['original8949Grass'])==digest(original['original8949Grass'])
  and digest(b['original8949Grass'])==digest(original['original8949Grass']),
  'All8949 original grass numeric/signed-zero controls differ')
 require({k:a[k]for k in a if k not in('rawActorControls','original8949Grass')}=={
  'all78TreeRoots':78,'retained12Heroes41Flowers':53,'original36Ferns':36,'originalPeriwinkleRoots':384,
  'original13YardShrubs':13,'additionalRandomSeedRangesReadbackAvailable':False,'perInstanceShaderRandomValuePreservationClaimed':False},
  'Protected population/readback scope differs')


def new_and_retained(r,bundle,packet,h,saved):
 donors=bundle['donors'];source=bundle['draftSource'];replay=side(r['originalConstructorReplay']);groups=side(r['newGroupNativeControlsSaved'])
 require(set(replay)==set(donors['yardGroups'])and set(groups)=={r['newActorMapping'][v['actor']]for v in donors['yardGroups'].values()},
  'Exactly three1274-root replay/new controls required')
 for model,row in donors['yardGroups'].items():
  m=row['measurement'];wanted=source.replay_record(model,m['preInsertionValues'],m['recoveredValues'],m['actualMatrices'],donors)
  require(replay[model]==wanted,'Original constructor replay proof differs')
  actor=r['newActorMapping'][row['actor']];got=groups[actor]
  binary_controls(got,row['savedControl'],source,'Copied new1274-root controls differ')
  require(digest(got['recoveredValues'])==saved[actor]['components'][0]['orderedInstanceTransformsSha256'],
   'Copied recovered frames unbound to final saved component')
 retained=side(r['retainedEcologySaved']);require(set(retained)==set(donors['ecologyRetained']),'Exactly eight survivor groups required')
 removes=[];supports=[]
 for key,group in packet['ecology']['ecologyGroups'].items():
  old=donors['ecologyOriginal'][key];wanted=h['r35'].guard.expected_control(old,group['selectedSourceIndices'])
  binary_controls(retained[key],wanted,source,'Surviving original1919 native structs/order/mainseed/custom differ')
  require(retained[key]==donors['ecologyRetained'][key]and saved[group['actor']]['components'][0]['instanceCount']==wanted['instanceCount']
   and saved[group['actor']]['components'][0]['orderedInstanceTransformsSha256']==digest(wanted['recoveredValues']),
   'Surviving controls unbound to actual source-index/native witness')
  removes.append({'groupId':key,'actor':group['actor'],'removedOriginalSourceIndices':group['selectedSourceIndices'],
   'removedRoots':len(group['selectedSourceIndices']),
   'nativeRemoveAtSwapOrder':h['r35'].guard.swap_remove_order(old['instanceCount'],group['selectedSourceIndices']),
   'retainedOriginalSourceOrder':wanted['sourceRootIndices'],'onlyActualExistingWrappedStructsReordered':True,
   'transformOrMatrixRecompositionPerformed':False,'seedSetterUsed':False})
  supports.extend(h['r35'].guard.native_support_checks(old,group,packet['ecology']))
 require(sum(c['instanceCount']for c in retained.values())==1919 and r['actualRemoveReadback']==removes
  and len(supports)==34 and side(r['retirementSourceSupport'])==supports,'All34 full threeLOD retirement supports/order differ')


def graph_expectations(bundle):
 recorded=side(bundle['report']['originalProtectedControlsSaved']);graphs={};textures=set()
 n._material_records(recorded,graphs,textures);n._material_records(bundle['report']['materialReport'],graphs,textures)
 r16=ROOT/'output/unreal/exterior-20261001-r16a/exterior-import-report.json'
 require(str(r16)in bundle['report']['inputFiles']and sha(r16)==bundle['report']['inputFiles'][str(r16)],
  'Actual original R16 fullgraph source is not protected by selected source')
 original=read(r16)['materials']['materials'];missing=0
 for row in original.values():
  if row['asset']in graphs and 'graph'not in graphs[row['asset']]:
   require(digest(row['graph'])==row['graphSha256']==graphs[row['asset']]['sha256'],
    'Historical original fullgraph does not match selected exact hash')
   graphs[row['asset']]['graph']=row['graph'];missing+=1
 require(len(graphs)==61 and len(textures)==96 and missing==42 and all('graph'in v for v in graphs.values()),
  'All61 full expectedgraphs/96textures/42historical fullshape bindings required')
 return graphs,sorted(textures)


def graph_diagnostics(r,bundle):
 graphs,textures=graph_expectations(bundle);routes=g.reader_dispatch(bundle);byasset={a:k for k,assets in routes.items()for a in assets}
 phases={};allpins=[]
 for phase in ('before','saved'):
  directory=g.CANDIDATE/'garden-yard-checkpoint'/('material-graphs-'+phase)
  pins=r['materialGraphDiagnosticFiles'][phase]
  require(r['materialGraphDiagnosticDirectories'][phase]==str(directory)and len(pins)==61
   and [p['path']for p in pins]==[str(directory/('graph-'+str(i).zfill(3)+'.json'))for i in range(61)],
   'Exact phase61 ordered complete graph diagnostic pins required')
  observed={}
  for p in pins:
   row=side(p);asset=row['asset'];require(asset in graphs and asset not in observed,'Exact known61 graph identities required')
   expected=graphs[asset];full=row['actualCompleteGraph']
   original_pin=bundle['reportPin']if asset==bundle['report']['materialReport']['asset']else bundle['report']['originalProtectedControlsSaved']
   require(row['schema']==g.REPAIR_SCHEMA and row['reader']==byasset[asset]and row['expectedPinnedSource']==original_pin
    and row['recordedExpectedGraphSha256']==row['actualCompleteGraphSha256']==expected['sha256']==digest(full)
    and full==expected['graph']and row['nativeGraphAcceptanceGranted']is False,'Complete original graph/reader/source differs')
   if row['completeRecordedGraphShapeAvailable']:
    require(row['recordedExpectedCompleteGraph']==expected['graph']and row['fullGraphDifferences']==[],
     'Native full recorded expected shape differs')
   else:require(byasset[asset]=='basic'and row['recordedExpectedCompleteGraph']is row['fullGraphDifferences']is None,
                'Only42 generic original hash-only native expectations allowed')
   observed[asset]=full
  require(set(observed)==set(graphs),'Complete selected61 graph census differs');phases[phase]=observed;allpins.extend(pins)
 require(phases['before']==phases['saved'],'Saved graphs changed during integration')
 wanted={a:{'graphSha256':v['sha256'],'originalGraphExact':True,'reader':byasset[a]}for a,v in graphs.items()}
 donors=bundle['donors']['reports']
 for row in donors['yardR32']['newMaterialReport']['materials'].values():
  require(row['graphSha256']==digest(row['graph']),'Copied exact R32 graph hash differs')
  wanted[row['asset']]={'graphSha256':row['graphSha256'],'exactSavedDonorGraph':True}
 row=donors['yardRepairR35']['repairC']['materialReport'];require(row['graphSha256']==digest(row['graph']),'Copied exact R35 graph hash differs')
 wanted[row['asset']]={'graphSha256':row['graphSha256'],'exactSavedDonorGraph':True}
 require(r['materialReadback']=={'graphs':wanted,'textureAssets':textures,'scopedMaterialGraphs':64,'scopedTextureObjects':96,
  'originalTexturePackageBytesProtected':True,'all96NativeTextureSettingsRecomputed':False,
  'sharedNewYardTextureSettingsVerified':True,'newTextureObjects':0,'materialPackagesIndependentlyUnloaded':False},
  'Exact64 graph/96texture native receipt or settings evidence limit differs')
 return allpins


def geometry(r,bundle,packet,h):
 donors=bundle['donors'];r32=donors['reports']['yardR32'];r35=donors['reports']['yardRepairR35'];proofs={}
 paths={**r32['newMeshes'],**r35['newMeshes']}
 for identity,source in packet['groundRecords'].items():
  corners=h['r32'].guard.corners(source)
  proofs[identity]={'mesh':paths[identity],'triangles':len(corners),
   'nativeOrderedF32PositionUv0Uv1CornerSha256':digest(corners),'fullOrderedNativeGeometryVerified':True,
   'nativeNormalTangentReadbackAvailable':False}
 require(r['geometryReadback']['ground']==proofs and sum(p['triangles']for p in proofs.values())==32878,
  'All32878 full sourceF32P/UV0/UV1/order/winding native receipt hashes differ')
 expected={};count=0
 for model,row in h['r35'].ecology_expected_geometry(packet['ecology']).items():
  lods=[]
  for lod in row['lods']:
   count+=len(lod['corners']);lods.append({'level':lod['level'],'triangles':len(lod['corners']),
    'sourcePrimitives':lod['sourcePrimitives'],'nativeOrderedF32PositionUv0Uv1CornersSha256':digest(lod['corners']),
    'fullNativeSourcePositionUvTopologyWindingVerified':True})
  expected[model]={'asset':row['mesh'],'materials':row['materials'],'lods':lods,
   'nativeNormalTangentReadbackAvailable':False,'freshAllThreeNativeLodsDecoded':True}
 require(count==5220 and r['geometryReadback']['originalEcology']==expected,
  'Full24LOD5220 original ecology P/UV0/UV1/primitive order receipt differs')
 footprints=r['geometryReadback']['newLowRootFootprints'];source=packet['ground']['proposal']['planting']
 require(footprints==r32['savedReadback']['footprints']
  and digest(footprints)==digest(r32['savedReadback']['footprints']),
  'Every1274 native-recorded footprint/radius/height must match original saved R32 observations')
 require(len(footprints)==1274 and len({v['rootId']for v in footprints})==1274,'Exactly1274 native allLOD footprint observations required')
 byid={v['id']:v for v in source}
 for f in footprints:
  root=byid[f['rootId']];bundle['draftSource'].exact(f['actualRootXYZ'],root['positionCm'],'Actual root moved')
  require(f['modelId']==root['modelId']and type(f['actualAllNativeLodRadiusCm'])in(int,float)
   and math.isfinite(f['actualAllNativeLodRadiusCm'])and f['actualAllNativeLodRadiusCm']>0
   and math.isfinite(f['actualAbovePivotHeightCm'])and f['allNativeLodVerticesAndContainingCircleInsideSourceMasks']is True
   and f['originalShrubClearancePreserved']is True,'Native footprint evidence or model identity differs')
 require(r['geometryReadback']['all1274ContainingCirclesAndNativeThreeLodVerticesInsideSourceMasks']is True
  and r['geometryReadback']['nativeNormalTangentReadbackAvailable']is False,'Native mask/readback limits differ')


def source_points(model,f32):
 path=Path(model['glbPath']);require(sha(path)==model['glbSha256'],'Exact old source plant GLB changed')
 raw=path.read_bytes();require(struct.unpack_from('<III',raw)==(0x46546c67,2,len(raw)),'Original typed GLB required')
 length,kind=struct.unpack_from('<II',raw,12);require(kind==0x4e4f534a,'GLB JSON absent')
 doc=json.loads(raw[20:20+length]);blob=raw[28+length:];points=[]
 for lod in model['lods']:
  node=next(v for v in doc['nodes']if v.get('name')==lod['nodeName'])
  require(not any(k in node for k in('translation','rotation','scale','matrix')),'Original source node frame differs')
  for primitive in doc['meshes'][node['mesh']]['primitives']:
   a=doc['accessors'][primitive['attributes']['POSITION']];view=doc['bufferViews'][a['bufferView']]
   require(a['componentType']==5126 and a['type']=='VEC3','Source FLOAT3 positions required')
   offset=view.get('byteOffset',0)+a.get('byteOffset',0);stride=view.get('byteStride',12)
   for i in range(a['count']):
    x,z,y=struct.unpack_from('<fff',blob,offset+i*stride);points.append([f32(x*100),f32(y*100),f32(z*100)])
 require(points,'All source3LOD vertices required');return points


def source_masks(bundle,packet,h):
 layout=read(ROOT/'output/unreal/exterior-context-yard-20261002-r28-study/yard-source-plan.json')
 models={v['id']:v for v in side(layout['inputFiles']['plantGeometry'])['meshes']}
 points={mid:source_points(models[mid],h['r32'].guard.f32)for mid in bundle['donors']['yardGroups']}
 vertices={mid:{'points':v}for mid,v in points.items()}
 proof=h['r32'].verify_footprints(packet['ground'],bundle['donors']['r32Measurements'],vertices)
 require(len(proof)==1274,'All1274 source-frame masks required')
 return sum(len(points[mid])*len(group['sourceRows'])for mid,group in bundle['donors']['yardGroups'].items())


def validate_saved(r,plan,bundle,packet):
 pf=side(r['sourcePreflight']);header(r,plan,pf,bundle);h=n.helpers(plan,bundle)
 before,saved=counterfactual(r,bundle);protected(r,bundle,before,saved)
 new_and_retained(r,bundle,packet,h,saved);diagnostics=graph_diagnostics(r,bundle);geometry(r,bundle,packet,h)
 checked=source_masks(bundle,packet,h)
 after=side(r['afterContentInventory'])
 require(r['assetDelta']==bundle['draftSource'].validate_packages(bundle['content'],bundle['preparedContent'],after,bundle['donors'])
  and len(after)==4100 and side(r['protectedProjectProof'])==bundle['protected']and len(bundle['protected'])==132
  and r['baseContentInventory']==bundle['report']['afterContentInventory']
  and r['newPackages']==[p['asset']for p in bundle['donors']['inventory']['packages']],
  'Fourteen immutable copies/Map-only saved Content/protected closure differs')
 audit=terminal_and_audit(r)
 require(audit['actualCompleteGraphDiagnosticPins']==diagnostics and audit['exactReaderDispatch']==g.reader_dispatch(bundle),
  'Independent root122 diagnostic closure/reader dispatch differs')
 return {'mode':'saved-r37r2-clean-selected-garden-and-yard-integration','nativeProcessId':NATIVE_PID,
  **r['actualCounts'],'wholeActorCounterfactualValidated':True,
  'selected384Periwinkle36Ferns12Heroes41Flowers78Trees8949Grass13ShrubsPreserved':True,
  'originalConstructorReplayAndSaved1274RawControlsBinary64Exact':True,'retained1919RawControlsOrderMainSeedCustomExact':True,
  'completeOriginalMaterialGraphDiagnosticsValidated':122,'fullHistoricalExpectedMaterialShapesValidated':61,
  'nativeHashOnlyExpectedShapesRecoveredFromHistoricalR16':42,'materialSnapshotReaderCounts':{'basic':49,'neighbor':9,'tree':3},
  'fullGroundSourceF32PositionUv0Uv1WindingReceiptTriangles':32878,'originalEcologySourceReceiptLods':24,
  'originalEcologySourceF32PositionUv0Uv1PrimitiveReceiptTriangles':5220,'sourceThreeLodPointsThroughRecordedMatricesChecked':checked,
  'all1274SourceContainingCirclesAndThreeLodVerticesInsideMasks':True,'recordedNativeAllLodMaskExecutionVerified':True,
  'all1274NativeRecordedFootprintsMatchOriginalR32':True,'original8949GrassCanonicalSignedZeroHashExact':True,
  'freshNativeActorOrGeometryDecodePerformedByCpuChecker':False,'savedRawMatricesIndependentlyDecodedFromNativeAssets':False,
  'all96NativeTextureSettingsRecomputed':False,'materialPackagesIndependentlyUnloaded':False,
  'nativeNormalTangentReadbackAvailable':False,'AdditionalRandomSeedsReadbackAvailable':False,
  'perInstanceShaderRandomValuePreservationClaimed':False,'derivedRadiusBitEqualityRequired':False,
  'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False}


def load_actual(path):
 path=Path(path).resolve()
 require(path==REPORT and sha(path)==REPORT_SHA and sha(ROOT/HELPER)==HELPER_SHA
  and sha(g.PLAN)==PLAN_SHA and sha(PREFLIGHT)==PREFLIGHT_SHA,'Only exact actual saved R37R2 source/report eligible')
 r=read(path);plan=read(g.PLAN);bundle=g.selected_base()
 # Initial clone validation checks original map bytes. Saved consumers validate
 # its immutable proof and declared after-inventory instead of replaying it.
 clone=side(g.CLONE_PIN);bundle['clone']=g.CLONE_PIN;bundle['preparedContent']=side(clone['preparedContentInventory'])
 require(clone['schema']==g.CLONE_SCHEMA and clone['status']==g.CLONE_STATUS
  and clone['nativeExecuted']is False and clone['nativePreflightPending']is True,'Exact initial clone proof differs')
 h=n.helpers(plan,bundle);packet=g.source_packet(bundle,h)
 return r,plan,bundle,packet


if __name__=='__main__':
 require(len(sys.argv)==2,'Usage: python3 -B exterior-garden-yard-editor-check-r28.py <actualreport>')
 print(json.dumps(validate_saved(*load_actual(sys.argv[1])),allow_nan=False))
