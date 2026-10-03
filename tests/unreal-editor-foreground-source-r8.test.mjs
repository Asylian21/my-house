import assert from 'node:assert/strict';
import test from 'node:test';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateForegroundHeader,validateForegroundProcess,validateForegroundContent,validateForegroundActors} from '../scripts/unreal/exterior-editor-source-r8.mjs';

const root=fileURLToPath(new URL('../',import.meta.url)),source=path.join(root,'output/unreal/exterior-20261002-r21b');
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const report=await read(path.join(source,'foreground-overlay-report-r2.json'));
const [proc,beforeContent,afterContent,before,expected,saved,plan]=await Promise.all([
  read(path.join(source,'foreground-native-r2.log.json')),read(report.baseContentInventory.path),read(report.afterContentInventory.path),
  read(report.beforeActorWitness.path),read(report.expectedActorWitness.path),read(report.savedActorWitness.path),read(report.sourceStudy.path)]);
const roots=await read(plan.roots.path);

test('R8 accepts actual saved R21b header and rejects old/failed/running/accepted claims',()=>{
  validateForegroundHeader(report,{source,root});
  for(const change of [{schemaVersion:1},{owner:'scripts/unreal/exterior-canopy-foreground-native.py'},{status:'foreground-native-overlay-failed'},
    {status:'foreground-native-overlay-running'},{performanceAccepted:true},{fullPhotorealismAccepted:true},{savedActorCount:5312},{measuredElevation:true}])
    assert.throws(()=>validateForegroundHeader({...report,...change},{source,root}));
});

test('R8 actual process0 is required with reviewed script, source project and completed timestamps',()=>{
  const context={project:report.project,root,logFile:path.join(source,'foreground-native-r2.log')};validateForegroundProcess(proc,report,context);
  for(const change of [{code:255},{code:null},{signal:'SIGTERM'},{endedAt:null},{pid:proc.pid+1},
    {args:proc.args.map(a=>a.startsWith('-script=')?'-script='+path.join(root,'scripts/unreal/exterior-canopy-foreground-native.py'):a)}])
    assert.throws(()=>validateForegroundProcess({...proc,...change},report,context));
});

test('R8 actual3980 Content inventory permits exact5 known packages and only original map delta',()=>{
  validateForegroundContent(beforeContent,afterContent,report.newContentPackages);
  const original=Object.keys(beforeContent).find(k=>k.endsWith('.uasset')),altered={...afterContent,[original]:{...afterContent[original],sha256:'0'.repeat(64)}};
  assert.throws(()=>validateForegroundContent(beforeContent,altered,report.newContentPackages));
  assert.throws(()=>validateForegroundContent(beforeContent,{...afterContent,'Brezi/CanopyForeground20261002R21/unplanned.uasset':{sha256:'0'.repeat(64),bytes:1}},report.newContentPackages));
});

test('R8 actual5311 full actor witness preserves5306 originals and closes5 own actors plus quality tags',()=>{
  const args={before,expected,saved,report,groups:roots.groups};validateForegroundActors(args);
  const original=Object.keys(before)[0],altered={...saved,[original]:{...saved[original],actorTick:!saved[original].actorTick}};
  assert.throws(()=>validateForegroundActors({...args,saved:altered}));
  const id=roots.groups[0].id,p=report.addedActors[id],wrongTag={...saved,[p]:{...saved[p],tags:saved[p].tags.filter(t=>t!=='BreziLawnDetail')}};
  assert.throws(()=>validateForegroundActors({...args,expected:wrongTag,saved:wrongTag}));
  // The source loop stores named transform dictionaries; the full witness
  // stores lists. The actual two hashes differ, without a transform mismatch.
  const c=saved[p].components.find(c=>c.instanceCount),rb=report.savedReadback.groups.find(g=>g.id===id);
  assert.notEqual(c.orderedInstanceTransformsSha256,rb.orderedInstanceTransformsSha256);
});
