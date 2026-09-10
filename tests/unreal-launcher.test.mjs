import test from "node:test";
import assert from "node:assert/strict";
import { compareSignatureOnly, inspectMachOSignature } from "../scripts/unreal/macho-signature.mjs";
import { assertEntryName, inspectLauncherExecution, startupFlags } from "../scripts/unreal/app-launch.mjs";
function fixture(size = 128) {
  const bytes = Buffer.alloc(1152 + size);
  bytes.writeUInt32LE(0xfeedfacf, 0); bytes.writeUInt32LE(0x100000c, 4);
  bytes.writeUInt32LE(3, 16); bytes.writeUInt32LE(240, 20);
  const segment = (at, name, fileOffset, fileSize, sections) => {
    bytes.writeUInt32LE(0x19, at); bytes.writeUInt32LE(72 + sections * 80, at + 4); bytes.write(name, at + 8, "ascii");
    bytes.writeBigUInt64LE(BigInt(fileOffset), at + 40); bytes.writeBigUInt64LE(BigInt(fileSize), at + 48);
    bytes.writeUInt32LE(sections, at + 64);
  };
  segment(32, "__TEXT", 0, 1024, 1); bytes.write("__text", 104, "ascii"); bytes.write("__TEXT", 120, "ascii");
  bytes.writeBigUInt64LE(32n, 144); bytes.writeUInt32LE(512, 152);
  segment(184, "__LINKEDIT", 1024, 128 + size, 0);
  bytes.writeUInt32LE(0x1d, 256); bytes.writeUInt32LE(16, 260); bytes.writeUInt32LE(1152, 264); bytes.writeUInt32LE(size, 268);
  bytes.fill(0x71, 512, 544); bytes.fill(0x9d, 1024, 1152);
  bytes.writeUInt32BE(0xfade0cc0, 1152); bytes.writeUInt32BE(64, 1156); bytes.writeUInt32BE(1, 1160);
  bytes.writeUInt32BE(0, 1164); bytes.writeUInt32BE(20, 1168); bytes.writeUInt32BE(0xfade0c02, 1172); bytes.writeUInt32BE(44, 1176);
  return bytes;
}
test("only genuine trailing signature size + exact LINKEDIT size delta is admitted", () => {
  const proof = compareSignatureOnly(fixture(128), fixture(96));
  assert.equal(proof.status, "signature-only-change-validated");
  assert.deepEqual(proof.classifiedSigningFields.map(row => row.name), ["LC_CODE_SIGNATURE.datasize", "LC_SEGMENT_64[__LINKEDIT].filesize"]);
  assert.deepEqual(proof.changedHeaderBytes.map(row => row.offset), [232, 233, 268]);
});
test("same allocation can change signature bytes only", () => {
  const before = fixture(), after = Buffer.from(before); after[1200] ^= 1;
  const proof = compareSignatureOnly(before, after); assert.equal(proof.signatureAllocationUnchanged, true); assert.deepEqual(proof.changedHeaderBytes, []);
});
for (const [name, mutate] of [
  ["code byte", b => { b[512] ^= 1; }],
  ["same-size hidden header edit", b => { b[28] ^= 1; }],
  ["remaining LINKEDIT payload", b => { b[1030] ^= 1; }],
  ["LINKEDIT vmsize", b => { b[216] ^= 1; }],
  ["moved signature", b => { b.writeUInt32LE(1168, 264); }],
  ["signature size mismatch", b => { b.writeUInt32LE(112, 268); }],
  ["LINKEDIT delta mismatch", b => { b.writeBigUInt64LE(255n, 232); }],
  ["bad segment identity", b => { b[193] = 65; }],
  ["truncated command table", b => { b.writeUInt32LE(248, 20); }],
  ["zero-sized command", b => { b.writeUInt32LE(0, 36); }],
  ["invalid command count", b => { b.writeUInt32LE(10001, 16); }],
  ["malformed superblob table", b => { b.writeUInt32BE(50, 1160); }],
  ["slot outside blob", b => { b.writeUInt32BE(999, 1168); }],
  ["short slot", b => { b.writeUInt32BE(4, 1176); }],
  ["invalid primary CodeDirectory", b => { b.writeUInt32BE(0, 1172); }],
  ["code section overlap with signature", b => { b.writeBigUInt64LE(1280n, 80); b.writeUInt32LE(1152, 152); }],
]) test(`reject ${name}`, () => { const before = fixture(), after = Buffer.from(before); mutate(after); assert.throws(() => compareSignatureOnly(before, after)); });
test("nontrailing signature is rejected", () => assert.throws(() => compareSignatureOnly(fixture(), Buffer.concat([fixture(), Buffer.alloc(16)]))));
test("wrong architecture/fat/malformed files are unsupported", () => {
  for (const value of [Buffer.alloc(3), Buffer.alloc(300), Buffer.from(fixture())]) {
    if (value.length > 1000) value.writeUInt32LE(7, 4);
    assert.throws(() => inspectMachOSignature(value));
  }
});
test("entry-point gate rejects bypass, path traversal and arbitrary plist values", () => {
  assert.equal(assertEntryName("BreziTwin"), "Contents/MacOS/BreziTwin");
  for (const name of ["BreziStartupLauncher", "../BreziTwin", "/tmp/BreziStartupLauncher", "other", null]) assert.throws(() => assertEntryName(name));
});
test("recorded exec marker must match original parent PID and exact flags", () => {
  const launch = { entryKind: "same-binary-self-exec", forcedFlags: [...startupFlags] }, outcome = { pid: 1234, code: 0, signal: null };
  const log = "BreziStartupEntry: pid=1234 phase=enter-engine forcedFlags=-LLM,-DetectHitchesWithLLM\nEngine is initialized. Leaving FEngineLoop::Init()\n";
  assert.deepEqual(inspectLauncherExecution(launch, outcome, log).errors, []);
  for (const invalid of [log.replace("pid=1234", "pid=2345"), log + log, log.replace(",-DetectHitchesWithLLM", ""), log.split("\n")[0]])
    assert(inspectLauncherExecution(launch, outcome, invalid).errors.length);
  assert(inspectLauncherExecution(launch, { ...outcome, code: 1 }, log).errors.length);
});
