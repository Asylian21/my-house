// CPU receipt fixtures derived from already saved R17 JSON. These tests never
// run Unreal and do not create new native, image, package, or performance proof.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {fileURLToPath} from 'node:url';
import {validateTransmissionEvidence,validateOverlayAssetDelta,validateOverlayActorDelta,validateProjectClosure}
  from '../scripts/unreal/exterior-editor-source-r3.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const source=path.join(root,'output/unreal/exterior-20261001-r17a');
const read=async file=>JSON.parse(await fs.readFile(file,'utf8'));
const overlay=await read(path.join(source,'canopy-transmission-native-report.json'));
const plan=await read(overlay.selectedPlan.path),base=await read(overlay.baseNativeReport.path);
const beforeContent=await read(overlay.baseContentInventory.path),afterContent=await read(overlay.afterContentInventory.path);
const beforeActors=await read(overlay.witnessBefore.path),afterActors=await read(overlay.witnessAfter.path);
const originalMaterials=await read(overlay.originalMaterialsBefore.path);
const process=await read(path.join(source,'canopy-transmission-native.log.json'));
const canonicalHashes={beforeActors:overlay.beforeActorWitnessSha256,afterActors:overlay.savedActorWitnessSha256,
  originalMaterials:overlay.originalMaterialsWitnessSha256};
const fixture={overlay,plan,base,beforeContent,afterContent,beforeActors,afterActors,originalMaterials,process,canonicalHashes};
const fakeHash=value=>createHash('sha256').update(JSON.stringify(value)).digest('hex');

test('CPU fixture accepts the typed saved overlay and preserves denied acceptance claims',()=>{
  const result=validateTransmissionEvidence(fixture);
  assert.equal(result.targetGroups,23);assert.equal(result.targetInstances,78);
  for(const key of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingPackageProduced'])
    assert.equal(result[key],false);
});

test('CPU fixture rejects a failed or unrelated native command despite a saved success receipt',()=>{
  assert.throws(()=>validateTransmissionEvidence({...fixture,process:{...process,code:1}}));
  assert.throws(()=>validateTransmissionEvidence({...fixture,process:{...process,args:['/foreign/project.uproject',...process.args.slice(1)]}}));
});

test('CPU fixture rejects rehashed actor policy drift beyond the exact leaf overrides',()=>{
  const changed=structuredClone(afterActors),id=plan.targets[0].baseGroup.actor;
  changed[id].components[0].instanceEndCullDistance=123;
  const rehashed=fakeHash(changed);
  assert.throws(()=>validateTransmissionEvidence({...fixture,afterActors:changed,
    overlay:{...overlay,expectedActorWitnessSha256:rehashed,savedActorWitnessSha256:rehashed},
    canonicalHashes:{...canonicalHashes,afterActors:rehashed}}));
});

test('CPU fixture rejects same-master substitution outside the protected grove and bark changes',()=>{
  // Deliberately construct a counterfactual outside actor with the same master.
  // The real saved R17 scene only uses these nine masters in the selected grove.
  const counterfeit=structuredClone(fixture),target=counterfeit.plan.targets[0];
  const outsider=Object.keys(counterfeit.beforeActors).find(key=>!plan.targets.some(t=>t.baseGroup.actor===key));
  const original=target.baseGroup.actor;
  counterfeit.beforeActors[outsider]=structuredClone(beforeActors[original]);
  counterfeit.afterActors[outsider]=structuredClone(afterActors[original]);
  counterfeit.afterActors[original]=structuredClone(beforeActors[original]);
  target.baseGroup.actor=outsider;counterfeit.overlay.componentBindings[0].actor=outsider;
  const beforeHash=fakeHash(counterfeit.beforeActors),afterHash=fakeHash(counterfeit.afterActors);
  counterfeit.overlay.beforeActorWitnessSha256=beforeHash;
  counterfeit.overlay.expectedActorWitnessSha256=afterHash;counterfeit.overlay.savedActorWitnessSha256=afterHash;
  counterfeit.canonicalHashes={...canonicalHashes,beforeActors:beforeHash,afterActors:afterHash};
  assert.throws(()=>validateTransmissionEvidence(counterfeit));
  const changed=structuredClone(afterActors),selected=plan.targets[0];
  changed[selected.baseGroup.actor].components.find(c=>c.mesh===selected.baseGroup.mesh).materials[0]=selected.newLeafAsset;
  assert.throws(()=>validateOverlayActorDelta(beforeActors,changed,plan.targets,overlay.componentBindings));
});

test('CPU fixture rejects a self-consistent extra Content package and a changed original graph receipt',()=>{
  const changed={...afterContent,'Brezi/Foreign.uasset':{sha256:'a'.repeat(64),bytes:50}};
  assert.throws(()=>validateOverlayAssetDelta(beforeContent,changed,{...overlay.assetDelta,
    newFiles:[...overlay.assetDelta.newFiles,'Brezi/Foreign.uasset'].sort()},plan.variants));
  const materials=structuredClone(originalMaterials),key=Object.keys(materials.graphs)[0];
  materials.graphs[key].graphSha256='b'.repeat(64);
  const rehashed=fakeHash(materials);
  assert.throws(()=>validateTransmissionEvidence({...fixture,originalMaterials:materials,
    overlay:{...overlay,originalMaterialsWitnessSha256:rehashed},canonicalHashes:{...canonicalHashes,originalMaterials:rehashed}}));
});

test('CPU own-project closure fixtures enforce exact saved Content and protected source/binary bytes',()=>{
  const project='/candidate/Project/BreziTwin',contentInventory={'Brezi/Maps/Brezi.umap':{sha256:'a'.repeat(64),bytes:12}},
    projectProof={'Source/BreziTwin/Game.cpp':{sha256:'b'.repeat(64),bytes:13}},
    closure={[path.join(project,'Content/Brezi/Maps/Brezi.umap')]:contentInventory['Brezi/Maps/Brezi.umap'],
      [path.join(project,'Source/BreziTwin/Game.cpp')]:projectProof['Source/BreziTwin/Game.cpp']};
  validateProjectClosure({project,contentInventory,projectProof,closure});
  assert.throws(()=>validateProjectClosure({project,contentInventory,projectProof,closure:{...closure,
    [path.join(project,'Content/unreported.uasset')]:{sha256:'c'.repeat(64),bytes:10}}}));
  assert.throws(()=>validateProjectClosure({project,contentInventory,projectProof:{'../foreign.cpp':{sha256:'b'.repeat(64),bytes:13}},closure}));
  assert.throws(()=>validateProjectClosure({project,contentInventory,projectProof,closure:{...closure,
    [path.join(project,'Source/BreziTwin/Game.cpp')]:{sha256:'b'.repeat(64),bytes:14}}}));
  assert.throws(()=>validateProjectClosure({project,contentInventory,projectProof,closure:{...closure,
    [path.join(project,'Binaries/unapproved.dylib')]:{sha256:'c'.repeat(64),bytes:10}}}));
});
