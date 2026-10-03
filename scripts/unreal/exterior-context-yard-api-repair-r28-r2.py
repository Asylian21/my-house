"""Measured commandlet subsystem repair. No scene, asset or Unreal operations."""
import ast
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-api-repair-r28-r2.py'
OUTPUT=ROOT/'output/unreal/exterior-context-yard-20261002-r28-native-api-repair-r2'
SUPPLEMENT=OUTPUT/'api-repair-supplement.json'
Lawn=ROOT/'scripts/unreal/lawn-geometry.py'
LAWN_SHA='bc5bd49c01e880d45022a75ba80a3a3fd971272a86906a7a94d0618df4504d2f'
FAILURE=ROOT/'output/unreal/exterior-20261002-r28a'
FAILURE_SHA='41d272ae650c28a9f407c60dfbe1f38aea6736cec5e63c14f3351831f63f008d'
ERROR="'NoneType' object has no attribute 'get_lod_screen_sizes'"
s=importlib.util.spec_from_file_location('yard_r2_repair_original_scope',ROOT/'scripts/unreal/exterior-context-yard-native-guards-r28.py')
old=importlib.util.module_from_spec(s);s.loader.exec_module(old)
require,read,sha,pin,check_pin=(getattr(old,k)for k in('require','read','sha','pin','check_pin'))


def api_evidence():
 require(sha(Lawn)==LAWN_SHA,'Exact proven lawn subsystem accessor changed')
 tree=ast.parse(Lawn.read_text());function=next(n for n in tree.body if isinstance(n,ast.FunctionDef)and n.name=='static_mesh_subsystem')
 text=ast.get_source_segment(Lawn.read_text(),function)
 require("u.load_module('StaticMeshEditor')"in text and 'u.AssetEditorSubsystem'in text,'Proven module registration/dependency gates missing')
 return {'helper':pin(Lawn),'function':'static_mesh_subsystem','functionAstSha256':old.digest(ast.dump(function,include_attributes=False)),
  'moduleToLoadIfUnregistered':'StaticMeshEditor','requiresStaticMeshEditorSubsystem':True,'requiresAssetEditorSubsystem':True,
  'primaryModuleSource':pin(Path('/Users/Shared/Epic Games/UE_5.8/Engine/Source/Editor/StaticMeshEditor/Private/StaticMeshEditorModule.cpp')),
  'primarySubsystemHeader':pin(Path('/Users/Shared/Epic Games/UE_5.8/Engine/Source/Editor/StaticMeshEditor/Public/StaticMeshEditorSubsystem.h'))}


def failure_evidence():
 report=FAILURE/'context-yard-native-report.json';raw=FAILURE/'context-yard-native.log.json';terminal=FAILURE/'context-yard-native-process.json'
 require(sha(report)==FAILURE_SHA,'Measured failed R28 history changed')
 r,p,t=read(report),read(raw),read(terminal)
 require(r['owner']=='scripts/unreal/exterior-context-yard-native-r28.py'and r['status']=='failed'and r['error']==ERROR
  and r['nativeProcessId']==p['pid']==69104 and p['code']==255 and p['signal']is None,'Only actual subsystem-None failure is repairable')
 require(t['processFile']==str(raw)and t['processFileSha256']==sha(raw)and t['reportSha256']==FAILURE_SHA
  and t['logFile']==str(FAILURE/'context-yard-native.log')and t['logSha256']==sha(t['logFile'])
  and t['sourcePinsUnchangedAfterNative']is True and len(t['sourcePinsBeforeNative'])==296,'Failed controller closure differs')
 require(p['command']=='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd'
  and p['args'][0]==str(FAILURE/'Project/BreziTwin/BreziTwin.uproject')
  and all(a in p['args']for a in('-nullrhi','-run=pythonscript','-script='+str(ROOT/r['owner']))),'Failed native invocation differs')
 for file,h in t['sourcePinsBeforeNative'].items():require(sha(file)==h,'Failed source no longer byte exact')
 audit_path=FAILURE/'failed-native-content-byte-audit-root-r1.json';require(sha(audit_path)=='f66d282429c8d6e9ca7965941e2db4c5de804e5f1de1d9a9f8ee726a193a578a','Actual failed byte audit changed')
 audit=read(audit_path);require(audit['failedNativeReport']==pin(report)and audit['contentFileCount']==4034 and audit['protectedFileCount']==132
  and audit['newPackageCount']==0 and all(audit[k]is True for k in('all4034OriginalContentFilesUnchanged','mapByteIdenticalToActualSavedR27',
  'allProtectedFilesUnchanged','originalSavedR27Unchanged','sourcePinsUnchangedAfterNative','failureBeforeMaterialCreationAndImport'))
  and audit['nativeApplied']is audit['mapSaveExecuted']is False,'Actual failure must preserve all old native bytes')
 return {'report':pin(report),'rawProcess':pin(raw),'terminalProcess':pin(terminal),'log':pin(t['logFile']),
  'nativeProcessId':69104,'exitCode':255,'sourcePinsUnchanged':296,'failureBeforeMaterialCreationImportAndMapSave':True,'failedByteAudit':pin(audit_path)}


def validate():
 row=read(SUPPLEMENT)
 require(row['schema']=='brezi-context-yard-measured-commandlet-api-repair-r28-r2'and row['owner']==OWNER
  and row['status']=='source-only-measured-subsystem-registration-repair-native-pending','Typed R2 API repair required')
 require(row['actualFailure']==failure_evidence()and row['accessor']==api_evidence(),'Actual failure/API evidence differs')
 require(row['sourceGeometryPlan']==pin(old.SOURCE)and row['baseNativeReport']==pin(old.BASE/'realism-clean-integration-native-report.json')
  and row['candidate']==str(ROOT/'output/unreal/exterior-20261002-r28b'),'R2 may not widen source/base/candidate scope')
 require(row['replacementCallSites']==['native_mesh_proof','native_master_vertices']
  and row['geometryLodFrameMaskGatesChanged']is False and row['sourceGeometryChanged']is False
  and row['nativeExecuted']is False,'Only two commandlet-compatible API accessors may change')
 for name,pair in row['ownedSources'].items():
  a,b=check_pin(pair['live']),check_pin(pair['snapshot']);require(a!=b and pair['live']['sha256']==pair['snapshot']['sha256'],'Owned repair snapshot differs: '+name)
 return row


def produce():
 require(not OUTPUT.exists(),'Use one fresh immutable API repair output')
 failure,api=failure_evidence(),api_evidence();OUTPUT.mkdir(parents=True)
 owned={}
 for key,name in [('native','exterior-context-yard-native-r28-r2.py'),('guard','exterior-context-yard-native-guards-r28-r2.py'),
                  ('tests','test_exterior_context_yard_native_r28_r2.py'),('repair',Path(OWNER).name)]:
  live=ROOT/'scripts/unreal'/name;snapshot=OUTPUT/name;snapshot.write_bytes(live.read_bytes());owned[key]={'live':pin(live),'snapshot':pin(snapshot)}
 row={'schema':'brezi-context-yard-measured-commandlet-api-repair-r28-r2','owner':OWNER,
  'status':'source-only-measured-subsystem-registration-repair-native-pending','actualFailure':failure,'accessor':api,
  'sourceGeometryPlan':pin(old.SOURCE),'baseNativeReport':pin(old.BASE/'realism-clean-integration-native-report.json'),
  'candidate':str(ROOT/'output/unreal/exterior-20261002-r28b'),'ownedSources':owned,
  'replacementCallSites':['native_mesh_proof','native_master_vertices'],'geometryLodFrameMaskGatesChanged':False,
  'sourceGeometryChanged':False,'nativeExecuted':False,'nativeAppearanceAccepted':False,'performanceAccepted':False}
 SUPPLEMENT.write_text(json.dumps(row,indent=2)+'\n');validate();print(json.dumps({'repair':pin(SUPPLEMENT),'accessor':api,'nativeExecuted':False}))


if __name__=='__main__':produce()
