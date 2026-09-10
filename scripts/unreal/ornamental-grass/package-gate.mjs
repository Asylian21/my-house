import fs from 'node:fs';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {createHash} from 'node:crypto';
const sha=x=>createHash('sha256').update(x).digest('hex');
const hash=x=>typeof x==='string'&&/^[a-f0-9]{64}$/.test(x);
const need=(x,m)=>{if(!x)throw new Error(`Ornamental grass: ${m}`)};
const stable=x=>Array.isArray(x)?x.map(stable):x&&typeof x==='object'?Object.fromEntries(Object.keys(x).sort().map(k=>[k,stable(x[k])])):x;
const equal=(a,b)=>JSON.stringify(stable(a))===JSON.stringify(stable(b));
const ids=Array.from({length:18},(_,i)=>`DOM_${String(1841+i).padStart(5,'0')}`);
const own='scripts/unreal/ornamental-grass/';
export function validateOrnamentalReceipt(imported,here=path.dirname(fileURLToPath(import.meta.url))) {
 let root=here;while(!fs.existsSync(path.join(root,'lib/twin-site.ts'))){const parent=path.dirname(root);need(parent!==root,'root absent');root=parent;}
 const ref=JSON.parse(fs.readFileSync(path.join(here,'reference.json'))),input=path.join(here,'inputs/authored-v1');
 const bytes=fs.readFileSync(path.join(input,'ornamental.json')),source=JSON.parse(bytes);
 need(sha(bytes)===ref.reportSha256&&sha(fs.readFileSync(path.join(input,'generate.py')))===ref.generatorSha256,'authored input bytes changed');
 const r=imported.ornamentalGrass;
 const inactive=r?.status==='source-cards-retained-prototype-rejected'&&r.nativeApplied===false;
 need((inactive||r?.status==='ornamental-saved-reload-validated'&&r.nativeApplied===true)&&r.recipeExcludesReadOnlyMaterialsHelper===true,'verified ornamental presentation absent');
 need(r.sourceManifestSha256===imported.sourceManifestSha256&&r.sourceManifestSha256===source.sourceManifestSha256&&r.sourceObjSha256===source.sourceObjSha256&&equal(r.sourceIds,ids),'source identity differs');
 const expected={...source.sourceFiles,[own+'inputs/authored-v1/ornamental.json']:ref.reportSha256,[own+'inputs/authored-v1/generate.py']:ref.generatorSha256};
 for(const g of source.groups)expected[own+'inputs/authored-v1/'+g.file]=g.sha256;
 const helpers=['scripts/unreal/tv-oak/tv_oak.py','scripts/unreal/lawn-ground/lawn_ground.py','scripts/unreal/lawn-ground/source.py','scripts/unreal/lawn-ground/graph.py','scripts/unreal/lawn-detail/native_assets.py','scripts/unreal/materials.py','unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.h','unreal/BreziTwin/Source/BreziTwin/BreziRendererSettingsAudit.cpp'];
 for(const name of ['ornamental.py','package-gate.mjs','reference.json'])expected[own+name]=sha(fs.readFileSync(path.join(here,name)));
 for(const name of helpers)expected[name]=sha(fs.readFileSync(path.join(root,name)));
 need(equal(r.pipelineFiles,expected),'pipeline scope differs');
 for(const [file,digest]of Object.entries(expected)){
  const local=file.startsWith(own)?path.join(here,file.slice(own.length)):path.join(root,file);
  need(hash(digest)&&fs.realpathSync(local)===local&&sha(fs.readFileSync(local))===digest&&imported.pipelineFiles?.[file]===digest,'input omitted/changed: '+file);
 }
 const recipeFiles={...expected};delete recipeFiles['scripts/unreal/materials.py'];
 need(r.recipeSha256===sha(JSON.stringify(stable({files:recipeFiles,transmission:.35}))),'owned recipe differs');
 if(inactive){
  need(r.newActorCount===0&&r.sourceCardsHidden===0&&r.sourceCardsRetained===18&&r.sourceObjectsDeleted===0&&r.visualAcceptance==='prototype-rejected-in-native-4k-review','inactive prototype scope differs');
  need(equal(Object.keys(r.sourceAfter??{}).sort(),ids),'retained source coverage differs');
  for(const id of ids){const c=r.sourceAfter[id];need(c.visible===true&&c.hiddenInGame===false&&c.actorHidden===false&&hash(c.nativeFacesSha256)&&c.sourceProof?.triangleMultiplicityAndWindingVerified===true&&c.sourceProof.maximumPositionErrorCm>=0&&c.sourceProof.maximumPositionErrorCm<=.0002&&c.sourceProof.maximumUv0Error>=0&&c.sourceProof.maximumUv0Error<=.000002,'retained source card differs');}
  return {status:'ornamental-prototype-disabled-source-cards-validated',actorCount:0,sourceCardsRetained:18};
 }
 need(r.newActorCount===6&&r.sourceCardsHidden===18&&r.sourceObjectsDeleted===0&&r.actorMetadataWrittenToSources===false&&r.collision===false&&r.navigation===false&&r.tick===false&&r.stagedProofEqualsFinal===true,'mutation scope differs');
 for(const name of ['stagedReload','stagedActorsReload','activeReload','finalReload']){const p=r[name];need(p?.mapSaved===true&&p.worldUnloaded===true&&p.ownedAssetsAbsentBeforeReload===true&&p.mapReloaded===true,'saved roundtrip absent');}
 need(Array.isArray(r.groups)&&r.groups.length===6&&new Set(r.groups.map(g=>g.descriptor.groupId)).size===6&&hash(r.sourcePreservationSnapshotSha256),'group proof absent');
 const prefix=`/Game/Brezi/OrnamentalGrass/R_${r.recipeSha256.slice(0,16)}/`,assetPrefix='unreal/BreziTwin/Content'+prefix.slice(5);
 for(const row of r.groups){const d=row.descriptor,g=source.groups.find(x=>x.id===d.groupId),p=r.meshProofs?.[d.groupId];
  need(g&&d.transaction===r.transaction&&d.state==='active'&&d.recipe===r.recipeSha256&&equal(d.sourceIds,g.sourceIds)&&equal(d.transform,{p:g.rootUnrealCm,q:[0,0,0,1],s:[1,1,1]})&&equal(d.boundsUnrealCm,g.boundsUnrealCm),'native group placement differs');
  need(d.mesh.startsWith(prefix)&&d.material.startsWith(prefix)&&p?.mesh===d.mesh&&p.triangles===1584&&hash(p.nativeFacesSha256)&&p.sourceProof?.triangleMultiplicityAndWindingVerified===true&&p.sourceProof.maximumPositionErrorCm>=0&&p.sourceProof.maximumPositionErrorCm<=.0002&&p.sourceProof.maximumUv0Error>=0&&p.sourceProof.maximumUv0Error<=.000002,'native triangle/UV proof differs');
  need(p.material?.asset===d.material&&p.material.graphNodes===5&&p.material.opaque===true&&p.material.twoSidedFoliage===true&&equal(p.material.baseColorLinear,g.material.baseColorLinear)&&p.material.roughness===g.material.roughness&&p.material.metallic===0&&p.material.authoredTransmissionScale===.35&&p.material.opacity===.5&&p.material.noWpoPdo===true,'material proof differs');
  need(equal(Object.keys(d.originalCardVisibility).sort(),[...g.sourceIds].sort())&&Object.values(d.originalCardVisibility).every(v=>typeof v==='boolean'),'prior source visibility absent');
  for(const [file,digest]of Object.entries(d.assetHashes))need(r.assetHashes?.[file]===digest,'descriptor asset unbound');
 }
 need(equal(Object.keys(r.sourceBefore).sort(),ids)&&equal(Object.keys(r.sourceAfter).sort(),ids),'source coverage differs');
 for(const id of ids){const a=r.sourceBefore[id],b=r.sourceAfter[id];need(b.visible===false&&equal({...b,visible:a.visible},a)&&hash(b.nativeFacesSha256)&&b.sourceProof?.triangleMultiplicityAndWindingVerified===true,'source card changed beyond visibility');}
 need(Object.keys(r.assetHashes??{}).filter(p=>p.endsWith('.uasset')).length===13&&Object.keys(r.protectedAssetHashes??{}).length>=1878,'asset scope missing');
 for(const [file,digest]of Object.entries(r.assetHashes))need(file.startsWith(assetPrefix)&&hash(digest)&&imported.finalAssetHashes?.[file]===digest,'owned asset omitted or changed');
 for(const [file,digest]of Object.entries(r.protectedAssetHashes))need(hash(digest)&&imported.finalAssetHashes?.[file]===digest,'protected asset omitted or changed');
 return {status:'ornamental-package-inputs-validated',actorCount:6,sourceCardsRetained:18,renderedVerified:false};
}
