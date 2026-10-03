import test from 'node:test';
import assert from 'node:assert/strict';
import { assertRebrandPayloadScope, assertOriginalEntitlements } from '../scripts/unreal/rebrand-dom-app.mjs';

const provenance = 'Contents/Resources/Dom-icon-source.json';
function fixture() {
  const before = Object.fromEntries([
    'Contents/MacOS/BreziTwin', 'Contents/_CodeSignature/CodeResources', 'Contents/Resources/Dom.icns',
    'Contents/Resources/AppIcon.icns', 'Contents/Resources/Assets.car', 'Contents/Resources/BreziStartupPolicy.json',
    'Contents/Info.plist', 'Contents/UE/BreziTwin/Content/Paks/BreziTwin-Mac.ucas',
    'Contents/UE/Engine/Binaries/ThirdParty/libRuntime.dylib',
  ].map((path, index) => [path, String(index).repeat(64)]));
  const after = { ...before, [provenance]: 'f'.repeat(64) };
  for (const path of ['Contents/MacOS/BreziTwin', 'Contents/_CodeSignature/CodeResources',
    'Contents/Resources/Dom.icns', 'Contents/Resources/AppIcon.icns', 'Contents/Resources/Assets.car'])
    after[path] = 'e'.repeat(64);
  return { before, after };
}

test('native icon/signing scope requires provenance and preserves the original startup policy', () => {
  const { before, after } = fixture();
  const receipt = assertRebrandPayloadScope(before, after);
  assert.equal(receipt.changedFiles.length, 5);
  assert.deepEqual(receipt.addedFiles, [provenance]);
  assert.equal(receipt.startupPolicyPreservedByteForByte, true);
});

for (const path of ['Contents/Resources/BreziStartupPolicy.json', 'Contents/Info.plist',
  'Contents/UE/BreziTwin/Content/Paks/BreziTwin-Mac.ucas', 'Contents/UE/Engine/Binaries/ThirdParty/libRuntime.dylib']) {
  test('icon-only scope rejects changed ' + path, () => {
    const { before, after } = fixture();
    after[path] = 'd'.repeat(64);
    assert.throws(() => assertRebrandPayloadScope(before, after), /Unrelated payload changed/);
  });
}

test('removal, unexpected additions, missing provenance and prior provenance are rejected', () => {
  for (const mutate of [
    ({ after }) => { delete after['Contents/UE/Engine/Binaries/ThirdParty/libRuntime.dylib']; },
    ({ after }) => { after['Contents/MacOS/helper'] = 'c'.repeat(64); },
    ({ after }) => { delete after[provenance]; },
    ({ before }) => { before[provenance] = 'b'.repeat(64); },
  ]) {
    const f = fixture(); mutate(f);
    assert.throws(() => assertRebrandPayloadScope(f.before, f.after));
  }
});

test('original GUI entitlements are preserved byte-for-byte, including formatting and permissions', () => {
  const original = '<plist><dict><key>com.apple.security.app-sandbox</key><true/></dict></plist>\n';
  assert.doesNotThrow(() => assertOriginalEntitlements(original, Buffer.from(original)));
  for (const changed of [original.trim(), original.replace('<true/>', '<false/>'), original + '<key>new</key>'])
    assert.throws(() => assertOriginalEntitlements(original, changed), /Original GUI entitlements changed/);
});
