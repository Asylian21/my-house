import {readFile,writeFile,mkdir,readdir,lstat} from 'node:fs/promises';
import {resolve,dirname} from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
import {parseArgs} from 'node:util';
import {sealStartupEntry} from '../startup-entry-package.mjs';
import {verifyPackage} from '../package-verify.mjs';
import {compareRawLinkPackaging} from './raw-link-signature.mjs';
const BASE=dirname(fileURLToPath(import.meta.url));
const {values}=parseArgs({options:{'archive-receipt':{type:'string'},'cooked-binding':{type:'string'},output:{type:'string'}}});
const sha=b=>createHash('sha256').update(b).digest('hex'),hash=async p=>sha(await readFile(p));
const need=(ok,why)=>{if(!ok)throw Error(why);};
const read=async p=>JSON.parse(await readFile(p,'utf8'));
for(const key of ['archive-receipt','cooked-binding','output'])need(values[key],'Missing --'+key);
const archiveReceipt=resolve(values['archive-receipt']),cookedBindingReceipt=resolve(values['cooked-binding']);
const archive=await read(archiveReceipt);
need(archive.mode==='archive'&&archive.status==='native-delivery-exited-zero-and-drained'&&archive.nativeExitCode===0
  &&archive.errors.length===0&&archive.remainingOwned.length===0,'Archive did not close cleanly');
const app=archive.appPath,engine=archive.engineRoot,project=archive.projectRoot;
const roles={archiveReceipt,cookedBindingReceipt,cookReceipt:archive.cookReceipt,
  ...Object.fromEntries(Object.entries(archive.inputs).map(([role,ref])=>[role,ref.path]))};
const inputs={};
for(const path of Object.values(roles))inputs[path]=await hash(path);
for(const [role,ref]of Object.entries(archive.inputs))need(inputs[ref.path]===ref.sha256,'Archive input changed: '+role);
const closure=await read(roles.sourceClosure),acceptedGame=await read(roles.acceptedGame),acceptedEditor=await read(roles.acceptedEditor);
need(closure.status==='caustics-delivery-source-frozen'&&acceptedGame.status==='caustics-delivery-game-build-accepted'
  &&acceptedEditor.status==='caustics-delivery-editor-build-accepted','Unaccepted source/native build');
const pins={...closure.fileHashes,...acceptedEditor.fileHashes,...acceptedGame.fileHashes,...inputs};
for(const [path,digest]of Object.entries(pins))need(await hash(path)===digest,'Delivery input changed: '+path);
// Advertise the named launch interface only for the source actually accepted by
// this build. Old packages keep their original raw-console launch behavior.
let renderProfileInterface;
const qualityPolicy=resolve(project,'Source/BreziTwin/BreziRenderQualityPolicy.h');
if(closure.fileHashes[qualityPolicy]){
  const policy=await readFile(qualityPolicy,'utf8');
  need(/inline constexpr int NativeProfileSchemaVersion = 1;/.test(policy),'Unknown native profile schema');
  const sourcePins={};
  for(const name of ['BreziRenderQualityPolicy.h','BreziRenderQuality.cpp','BreziPlayerController.cpp','BreziPlayerController.h']){
    const path=resolve(project,'Source/BreziTwin',name);
    need(closure.fileHashes[path]===await hash(path),'Missing compiled native quality input: '+name);
    sourcePins[path]=closure.fileHashes[path];
  }
  renderProfileInterface={schemaVersion:1,profiles:['native','balanced','performance'],sourcePins};
}
const binding=await read(cookedBindingReceipt);
need(binding.status==='cooked-source-container-lineage-validated'&&binding.archiveReceiptSha256===inputs[archiveReceipt]
  &&binding.cookReceiptSha256===inputs[roles.cookReceipt],'Cooked receipt does not bind actual archive/cook');
const pakRelative='Contents/UE/BreziTwin/Content/Paks',pakDirectory=resolve(app,pakRelative);
const containerNames=binding.containerFiles.map(row=>row.name);
need(new Set(containerNames).size===containerNames.length
  &&JSON.stringify((await readdir(pakDirectory)).sort())===JSON.stringify([...containerNames].sort()),'Cooked container set changed');
for(const row of binding.containerFiles){
  const path=resolve(pakDirectory,row.name),stat=await lstat(path);
  need(dirname(path)===pakDirectory&&stat.isFile()&&!stat.isSymbolicLink()&&stat.size===row.bytes
    &&await hash(path)===row.sha256,'Cooked container bytes changed: '+row.name);
}
const game=resolve(project,'Binaries/Mac/BreziTwin'),packagedGame=resolve(app,'Contents/MacOS/BreziTwin');
const linkedGameProof=compareRawLinkPackaging(await readFile(game),await readFile(packagedGame));
const output=resolve(values.output);await mkdir(output,{recursive:false});
const helpers=[fileURLToPath(import.meta.url),resolve(BASE,'../startup-entry-package.mjs'),
  resolve(BASE,'../package-verify.mjs'),resolve(BASE,'../macho-signature.mjs'),
  resolve(BASE,'./raw-link-signature.mjs')];
for(const path of helpers)inputs[path]=await hash(path);
const seal=await sealStartupEntry({app,source:resolve(project,'Source/BreziTwin/BreziStartupEntry.cpp'),output:resolve(output,'seal'),
  additionalResources:[{source:cookedBindingReceipt,sha256:inputs[cookedBindingReceipt],
    relativePath:'Contents/UE/BreziTwin/Plugins/BreziCausticsProbe/Resources/cooked-runtime-binding.json'}]});
roles.sealReceipt=resolve(output,'seal/startup-entry-package.json');inputs[roles.sealReceipt]=await hash(roles.sealReceipt);
const bundle=await verifyPackage(app,engine);
for(const row of binding.containerFiles)need(bundle.payloadHashes[pakRelative+'/'+row.name]===row.sha256,'Sealed container differs from cooked binding');
for(const [path,digest]of Object.entries({...pins,...inputs}))need(await hash(path)===digest,'Input changed while sealing: '+path);
const report={schemaVersion:1,status:'caustics-delivery-package-validated',generatedAt:new Date().toISOString(),
  app,engine,project,bundle,inputs,...roles,linkedGameProof,renderProfileInterface,
  actualGameLaunchPending:true,performanceAccepted:false,photorealismAccepted:false,
  scope:'Fresh cooked and archived standalone app with compiled continuous provider and sealed cooked binding. Runtime and visual verification remain separate.'};
const path=resolve(output,'package.json');await writeFile(path,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
console.log(JSON.stringify({status:report.status,report:path,sha256:await hash(path),app,files:bundle.fileCount,bytes:bundle.bytes}));
