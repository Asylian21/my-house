import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,writeFile,rm} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {join} from 'node:path';
import {createHash} from 'node:crypto';
import {prepareSealResources} from '../scripts/unreal/startup-entry-package.mjs';

test('post-cook JSON joins the final signing pass with exact bytes and no payload replacement',async()=>{
  const dir=await mkdtemp(join(tmpdir(),'brezi-seal-resource-'));
  try {
    const source=join(dir,'binding.json'),bytes=Buffer.from('{"status":"fixture"}\n');
    await writeFile(source,bytes);
    const entry={source,relativePath:'Contents/UE/BreziTwin/Plugins/BreziCausticsProbe/Resources/cooked-runtime-binding.json',
      sha256:createHash('sha256').update(bytes).digest('hex')};
    assert.deepEqual((await prepareSealResources(join(dir,'BreziTwin.app'),{},[entry]))[0].bytes,bytes);
    for(const resources of [[{...entry,sha256:'0'.repeat(64)}],[entry,entry],
      [{...entry,relativePath:'../escape.json'}],[{...entry,relativePath:'Contents/Resources/../../escape.json'}],
      [{...entry,relativePath:'Contents/MacOS/BreziTwin'}],[{...entry,relativePath:'Contents/Resources/BreziStartupPolicy.json'}]])
      await assert.rejects(prepareSealResources(join(dir,'BreziTwin.app'),{},resources));
    await assert.rejects(prepareSealResources(join(dir,'BreziTwin.app'),{[entry.relativePath]:entry.sha256},[entry]));
    await writeFile(source,'changed');
    await assert.rejects(prepareSealResources(join(dir,'BreziTwin.app'),{},[entry]));
  } finally {await rm(dir,{recursive:true,force:true});}
});
