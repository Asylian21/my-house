// Exclusive CPU readiness packet for the actual R35R2 frozen-R18 camera QA clone.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence,validateProjectClosure} from './exterior-editor-source-r26.mjs';
const root=fileURLToPath(new URL('../../',import.meta.url));
const owner='scripts/unreal/exterior-context-yard-repair-editor-readiness-r26.mjs';
const source=path.join(root,'output/unreal/exterior-20261002-r35b-yard-close-candidate-r26');
const output=path.join(root,'output/unreal/exterior-context-yard-20261002-r35-editor-r26-readiness-r1');
const sha=async p=>{const h=createHash('sha256');for await(const b of createReadStream(p))h.update(b);return h.digest('hex');};
const pin=async p=>({path:p,sha256:await sha(p),bytes:(await fs.stat(p)).size});
const save=(p,v)=>fs.writeFile(p,JSON.stringify(v,null,2)+'\n',{flag:'wx'});
const owned=[owner,'scripts/unreal/exterior-context-yard-repair-editor-check-r26.py',
 'scripts/unreal/exterior-context-yard-repair-camera-stage-r26.py','scripts/unreal/exterior-editor-source-r26.mjs',
 'scripts/unreal/exterior-editor-qa-r26.mjs','tests/unreal-editor-yard-repair-source-r26.test.mjs'];
const inputBefore={};for(const p of owned)inputBefore[path.join(root,p)]=await sha(path.join(root,p));
const e=await loadEditorSourceEvidence(source,{root});
assert.equal(e.mode,'saved-r35r2-exact-r18-yard-camera-qa-clone');assert.equal(e.summary.nativeProcessId,37031);
assert.equal(e.summary.fullActorCounterfactualValidated,true);assert.equal(e.summary.retiredOriginalEcologyRoots,34);
const closure={};
async function files(directory){const result=[];for(const row of await fs.readdir(directory,{withFileTypes:true})){
 const p=path.join(directory,row.name);assert(!row.isSymbolicLink());if(row.isDirectory())result.push(...await files(p));else if(row.isFile())result.push(p);
 }return result;}
const ownFiles=[...await files(path.join(e.project,'Content')),path.join(e.project,'BreziTwin.uproject'),
 ...await files(path.join(e.project,'Config')),...await files(path.join(e.project,'Source')),...await files(path.join(e.project,'Binaries'))].sort();
assert.equal(ownFiles.length,4224);
for(const p of ownFiles){const v=await pin(p);closure[p]={sha256:v.sha256,bytes:v.bytes};}
validateProjectClosure({project:e.project,contentInventory:e.contentInventory,projectProof:e.projectProof,closure});
const immutable={};for(const p of [...new Set([...e.additionalClosureFiles,...Object.keys(inputBefore)])].sort())immutable[p]=await sha(p);
assert.deepEqual(Object.fromEntries(Object.keys(inputBefore).map(p=>[p,immutable[p]])),inputBefore);
await fs.mkdir(output,{recursive:false});await fs.mkdir(path.join(output,'owned-source'));
const snapshots=[];for(const p of owned){const input=path.join(root,p),destination=path.join(output,'owned-source',path.basename(p));
 await fs.copyFile(input,destination,fs.constants.COPYFILE_EXCL);assert.equal(await sha(destination),inputBefore[input]);snapshots.push({live:await pin(input),snapshot:await pin(destination)});}
const testsPath=path.join(output,'source-tests.log');await fs.copyFile('/private/tmp/brezi-r26-source-tests-r1.log',testsPath,fs.constants.COPYFILE_EXCL);
const tests=await fs.readFile(testsPath,'utf8');assert(tests.includes('# tests 10')&&tests.includes('# pass 10')&&tests.includes('# fail 0'));
const actualCheckerPath=path.join(output,'actual-saved-checker.log');await fs.copyFile('/private/tmp/brezi-r26-checker-actual-r2.log',actualCheckerPath,fs.constants.COPYFILE_EXCL);
const actualChecker=JSON.parse(await fs.readFile(actualCheckerPath,'utf8'));assert.equal(actualChecker.fullActorCounterfactualValidated,true);assert.equal(actualChecker.nativeProcessId,37031);
const stageLog=path.join(output,'camera-stage.log');await fs.copyFile('/private/tmp/brezi-r26-camera-stage-r1.log',stageLog,fs.constants.COPYFILE_EXCL);
const draftHistory=path.join(output,'preserved-unconsumed-draft-checker-header-failure.log');await fs.copyFile('/private/tmp/brezi-r26-checker-actual-r1.log',draftHistory,fs.constants.COPYFILE_EXCL);
const closurePath=path.join(output,'current-project-inputs.json');await save(closurePath,closure);
for(const[p,h]of Object.entries(immutable))assert.equal(await sha(p),h);
const receipt=path.join(output,'editor-source-readiness.json');
await save(receipt,{schema:'brezi-actual-saved-r35r2-editor-camera-source-readiness-r26',schemaVersion:1,owner,
 status:'source-ready-actual-saved-r35r2-exact-r18-camera-editor-pending',source,project:e.project,
 sourceNativeReport:await pin(path.join(root,'output/unreal/exterior-20261002-r35b/context-yard-repair-native-report-r2.json')),
 cameraStageReceipt:await pin(e.nativeReceiptPath),summary:e.summary,
 currentOwnProjectFiles4224Validated:true,currentContentFiles4092Validated:true,currentProtectedFiles132Validated:true,
 currentProjectByteClosure:await pin(closurePath),savedSourceCurrentByteAudit:await pin(path.join(root,'output/unreal/exterior-20261002-r35b/root-native-success-byte-audit-r35b-r1.json')),
 nativeProcessId:37031,nativeSourcePinCount603:603,
 tests:{count:10,pass:10,fail:0,exitCode:0,log:await pin(testsPath)},actualSavedChecker:await pin(actualCheckerPath),cpuDataStageLog:await pin(stageLog),
 preservedUnconsumedDraftHeaderFailure:{log:await pin(draftHistory),scope:'Initial unconsumed draft status-string check; fixed before review/freeze. No native/project operation.'},
 ownedSources:snapshots,immutableInputFilesBefore:immutable,immutableInputFilesAfter:immutable,sourceInputsUnchanged:true,
 runtimeMatchesFrozenR24ExceptSourceAndOwnerFilenames:true,viewId:'exterior-context-yard-572063-close-r18',
 cameraAuditScope:'Frozen R18 original source camera reused; current R35 native occlusion not asserted.',
 nativeLaunchedByReadiness:false,gpuExecuted:false,nativeAppearanceAccepted:false,fullPhotorealismAccepted:false,
 performanceAccepted:false,shippingVerified:false,packageVerified:false});
console.log(JSON.stringify({readiness:await pin(receipt),source,view:'exterior-context-yard-572063-close-r18',currentOwnProjectFiles:4224}));
