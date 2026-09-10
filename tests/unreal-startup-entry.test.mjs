import test from 'node:test';
import assert from 'node:assert/strict';
import { inspectStartupEntry } from '../scripts/unreal/startup-entry.mjs';
import { inspectStartupPolicy, inspectLauncherExecution, assertEntryName, startupFlags } from '../scripts/unreal/app-launch.mjs';
function fixture() {
  const b=Buffer.alloc(1280),vm=0x100000000n;
  b.writeUInt32LE(0xfeedfacf,0);b.writeUInt32LE(0x100000c,4);b.writeUInt32LE(2,12);b.writeUInt32LE(5,16);b.writeUInt32LE(288,20);
  const segment=(at,name,offset,size,n)=>{b.writeUInt32LE(0x19,at);b.writeUInt32LE(72+n*80,at+4);b.write(name,at+8);b.writeBigUInt64LE(vm+BigInt(offset),at+24);b.writeBigUInt64LE(16384n,at+32);b.writeBigUInt64LE(BigInt(offset),at+40);b.writeBigUInt64LE(BigInt(size),at+48);b.writeUInt32LE(5,at+60);b.writeUInt32LE(n,at+64);};
  segment(32,'__TEXT',0,1024,1);segment(184,'__LINKEDIT',1024,256,0);
  b.write('__text',104);b.write('__TEXT',120);b.writeBigUInt64LE(vm+512n,136);b.writeBigUInt64LE(128n,144);b.writeUInt32LE(512,152);
  b.writeUInt32LE(0x1d,256);b.writeUInt32LE(16,260);b.writeUInt32LE(1152,264);b.writeUInt32LE(128,268);
  b.writeUInt32LE(0x80000028,272);b.writeUInt32LE(24,276);b.writeBigUInt64LE(576n,280);
  b.writeUInt32LE(2,296);b.writeUInt32LE(24,300);b.writeUInt32LE(1024,304);b.writeUInt32LE(2,308);b.writeUInt32LE(1056,312);b.writeUInt32LE(64,316);
  b.write('\0_main\0_BreziMain\0',1056);b.writeUInt32LE(1,1024);b[1028]=0x0e;b[1029]=1;b.writeBigUInt64LE(vm+512n,1032);
  b.writeUInt32LE(7,1040);b[1044]=0x0f;b[1045]=1;b.writeBigUInt64LE(vm+576n,1048);
  b.fill(0xab,512,640);b.writeUInt32BE(0xfade0cc0,1152);b.writeUInt32BE(64,1156);b.writeUInt32BE(1,1160);b.writeUInt32BE(20,1168);b.writeUInt32BE(0xfade0c02,1172);b.writeUInt32BE(44,1176);return b;
}
test('LC_MAIN must map to app entry while local original main remains',()=>{const r=inspectStartupEntry(fixture());assert.equal(r.entryFileOffset,576);assert.equal(r.originalMainAddress,'0x100000200');});
for(const [name,mutate] of [
 ['wrong LC_MAIN',b=>b.writeBigUInt64LE(512n,280)],['missing LC_MAIN',b=>b.writeUInt32LE(0x777,272)],
 ['duplicate main identity',b=>b.writeUInt32LE(1,1040)],['out-of-bounds symbol table',b=>b.writeUInt32LE(100000,308)],
 ['bad string index',b=>b.writeUInt32LE(10000,1040)],['missing original main',b=>{b[1028]=0x00;}],
 ['nonexecutable TEXT',b=>b.writeUInt32LE(1,92)],['entry outside code',b=>b.writeBigUInt64LE(900n,280)],
 ['entry symbol outside code',b=>b.writeBigUInt64LE(0x100000384n,1048)],['not executable file type',b=>b.writeUInt32LE(6,12)]
])test(`reject ${name}`,()=>{const b=fixture();mutate(b);assert.throws(()=>inspectStartupEntry(b));});
function policy(entry){return {schemaVersion:2,status:'linked-self-exec-startup-policy',entryKind:'same-binary-self-exec',entryFile:'Contents/MacOS/BreziTwin',forcedFlags:[...startupFlags],entrySourceSha256:'a'.repeat(64),sandboxPolicy:'original-main-executable-original-entitlements',linkedEntry:entry};}
test('sealed policy matches linked code and rejects circular final-binary hashes',()=>{
 const entry=inspectStartupEntry(fixture()),p=policy(entry);assert.doesNotThrow(()=>inspectStartupPolicy(p,entry));
 for(const change of [{schemaVersion:1},{entryFile:'Contents/MacOS/BreziStartupLauncher'},{engineSha256:'b'.repeat(64)},{executableSha256:'c'.repeat(64)},{forcedFlags:['-LLM']},{entrySourceSha256:'x'},{sandboxPolicy:'inherit'},{linkedEntry:{...entry,entryFileOffset:512}}])assert.throws(()=>inspectStartupPolicy({...p,...change},entry));
 const changed=fixture();changed[600]^=1;assert.throws(()=>inspectStartupPolicy(p,inspectStartupEntry(changed)));
});
test('single GUI entry rejects old helper or arbitrary plist path',()=>{assert.equal(assertEntryName('BreziTwin'),'Contents/MacOS/BreziTwin');for(const s of ['BreziStartupLauncher','../BreziTwin','/tmp/BreziTwin',null])assert.throws(()=>assertEntryName(s));});
test('same PID optional one self-exec, one UE entry, ordered and clean',()=>{
 const launch={entryKind:'same-binary-self-exec',forcedFlags:[...startupFlags]},outcome={pid:123,code:0,signal:null};
 const re='BreziStartupEntry: pid=123 phase=self-exec forcedFlags=-LLM,-DetectHitchesWithLLM\n',enter='BreziStartupEntry: pid=123 phase=enter-engine forcedFlags=-LLM,-DetectHitchesWithLLM\n',engine='Engine is initialized. Leaving FEngineLoop::Init()\n';
 for(const s of [enter+engine,re+enter+engine])assert.deepEqual(inspectLauncherExecution(launch,outcome,s).errors,[]);
 for(const s of [re+re+enter+engine,enter+enter+engine,enter+re+engine,re+engine,(re+enter+engine).replace('pid=123','pid=124'),re+enter,'BreziStartupLauncher: pid=123\n'+enter+engine])assert(inspectLauncherExecution(launch,outcome,s).errors.length);
 assert(inspectLauncherExecution(launch,{...outcome,signal:'SIGABRT'},re+enter+engine).errors.length);
});
