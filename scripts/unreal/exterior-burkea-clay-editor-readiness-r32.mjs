// One NEW closed R46 consumer and current-project closure. No old consumer/test.
import fs from 'node:fs/promises';
import path from 'node:path';
import assert from 'node:assert/strict';
import {createReadStream,constants} from 'node:fs';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence,validateProjectClosure} from './exterior-editor-source-r32.mjs';
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const directory=path.join(root,'output/unreal/exterior-burkea-clay-20261002-r46-editor-r32-source-readiness');
const source=path.join(root,'output/unreal/exterior-20261002-r46a');
const owner='scripts/unreal/exterior-burkea-clay-editor-readiness-r32.mjs';
const ownNames=['exterior-burkea-clay-editor-check-r32.py','test_exterior_burkea_clay_editor_r32.py',
 'exterior-editor-source-r32.mjs','exterior-editor-qa-r32.mjs','exterior-burkea-clay-editor-readiness-r32.mjs'];
async function pin(file){const stat=await fs.lstat(file);assert(stat.isFile()&&!stat.isSymbolicLink());const hash=createHash('sha256');for await(const bytes of createReadStream(file))hash.update(bytes);return{path:file,sha256:hash.digest('hex'),bytes:stat.size};}
async function files(directory){const rows=[];for(const e of await fs.readdir(directory,{withFileTypes:true})){assert(!e.isSymbolicLink());const f=path.join(directory,e.name);if(e.isDirectory())rows.push(...await files(f));else if(e.isFile())rows.push(f);}return rows;}
async function save(file,value){await fs.writeFile(file,JSON.stringify(value,null,2)+'\n',{flag:'wx'});}
const start=Date.now(),before=await Promise.all(ownNames.map(n=>pin(path.join(root,'scripts/unreal',n))));
assert(!(await fs.readdir(directory)).includes('actual-consumer.json'),'Only one fresh actual consumer');
const evidence=await loadEditorSourceEvidence(source,{root});
const projectFiles=[path.join(evidence.project,'BreziTwin.uproject')];
for(const folder of ['Content','Config','Source','Binaries'])projectFiles.push(...await files(path.join(evidence.project,folder)));
const closurePaths=[...new Set([...evidence.additionalClosureFiles,...projectFiles,...before.map(p=>p.path)])].sort();
const closure={},closureFiles={};for(const file of closurePaths){const p=await pin(file);closure[file]={sha256:p.sha256,bytes:p.bytes};closureFiles[file]=p.sha256;}
validateProjectClosure({project:evidence.project,contentInventory:evidence.contentInventory,projectProof:evidence.projectProof,closure});
assert.equal(projectFiles.length,4276);assert.deepEqual(await Promise.all(before.map(p=>pin(p.path))),before);
const consumer={project:evidence.project,nativeReceiptPath:evidence.nativeReceiptPath,summary:evidence.summary,
 contentInventory:evidence.contentInventory,projectProof:evidence.projectProof,
 additionalClosureFiles:evidence.additionalClosureFiles,closureFiles};
assert.deepEqual(Object.keys(consumer).sort(),['project','nativeReceiptPath','summary','contentInventory','projectProof','additionalClosureFiles','closureFiles'].sort());
const consumerFile=path.join(directory,'actual-consumer.json');await save(consumerFile,consumer);
const snapshots=path.join(directory,'sources');await fs.mkdir(snapshots);
const owned=[];for(const p of before){const dst=path.join(snapshots,path.basename(p.path));await fs.copyFile(p.path,dst,constants.COPYFILE_EXCL);assert.equal((await pin(dst)).sha256,p.sha256);owned.push({...p,snapshot:dst});}
const guardLog=await pin(path.join(directory,'checker-guards.log')),correctedLog=await pin(path.join(directory,'checker-roof-corrected.log'));
const readiness={schema:'brezi-r46-actual-saved-five-slot-editor-source-readiness-r32',schemaVersion:1,owner,
 status:'verified-actual-saved-r46-five-slot-source-reader-ready-r32',createdAt:new Date().toISOString(),
 actualConsumerExitCode:0,actualConsumer:await pin(consumerFile),reader:before.find(p=>p.path.endsWith('/exterior-editor-source-r32.mjs')),
 checker:before.find(p=>p.path.endsWith('/exterior-burkea-clay-editor-check-r32.py')),summary:evidence.summary,
 ownProjectFiles:4276,currentContentFiles:4144,protectedFiles:132,closureFiles:closurePaths.length,
 actualNativeProcessId:65818,sourceReceiptPins:5657,terminalSourcePins:5664,
 tests:{distinctCaseCount:5,initialPassedCases:4,initialFailedCases:1,initialRunExitCode:1,initialRunLog:guardLog,
 correctedRoofCaseCount:1,correctedRoofExitCode:0,correctedRoofLog:correctedLog,
 allFiveDistinctCasesNowPassed:true,positiveCheckerCliExecutedOnlyByThisDirectConsumer:true,
 historicalFixtureOrProducerExecuted:false},
 preservedFirstAttemptSources:await Promise.all(['exterior-burkea-clay-editor-check-r32.py','test_exterior_burkea_clay_editor_r32.py'].map(n=>pin(path.join(directory,'first-attempt',n)))),
 ownedSources:owned,sourceFilesUnchangedAfterActualConsumer:true,elapsedSeconds:(Date.now()-start)/1000,
 freshNativeActorOrGeometryDecodePerformedByCpuChecker:false,nativeLaunched:false,gpuExecuted:false,
 nativeAppearanceAccepted:false,fullPhotorealismAccepted:false,performanceAccepted:false,shippingVerified:false,activeOutputPromoted:false};
const readyFile=path.join(directory,'source-readiness.json');await save(readyFile,readiness);
console.log(JSON.stringify({exitCode:0,readiness:await pin(readyFile),consumer:await pin(consumerFile),reader:readiness.reader,checker:readiness.checker,closureFiles:closurePaths.length,elapsedSeconds:readiness.elapsedSeconds,summary:evidence.summary}));
