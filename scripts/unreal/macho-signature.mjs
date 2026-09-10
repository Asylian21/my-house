import { createHash } from "node:crypto";
const sha = bytes => createHash("sha256").update(bytes).digest("hex");
const fail = message => { throw new Error(`Mach-O signature gate: ${message}`); };
const bounded = (offset, size, length) => Number.isSafeInteger(offset) && Number.isSafeInteger(size) && offset >= 0 && size >= 0 && offset <= length && size <= length - offset;
const u64 = (bytes, offset) => { const n = bytes.readBigUInt64LE(offset); if (n > BigInt(Number.MAX_SAFE_INTEGER)) fail("64-bit field exceeds safe range"); return Number(n); };
const cstring = bytes => bytes.toString("ascii").split("\0", 1)[0];

/** Strictly bounded thin arm64 parser; unsupported/fat inputs are rejected. */
export function inspectMachOSignature(bytes) {
  if (!Buffer.isBuffer(bytes) || bytes.length < 32 || bytes.readUInt32LE(0) !== 0xfeedfacf || bytes.readUInt32LE(4) !== 0x100000c)
    fail("expected thin little-endian arm64 MH_MAGIC_64");
  const count = bytes.readUInt32LE(16), size = bytes.readUInt32LE(20), commandsEnd = 32 + size;
  if (!count || count > 10000 || !bounded(32, size, bytes.length)) fail("invalid command table");
  let cursor = 32, signature = null;
  const segments = [], sections = [];
  for (let i = 0; i < count; ++i) {
    if (!bounded(cursor, 8, commandsEnd)) fail("truncated load command");
    const command = bytes.readUInt32LE(cursor), commandSize = bytes.readUInt32LE(cursor + 4);
    if (commandSize < 8 || commandSize % 8 || !bounded(cursor, commandSize, commandsEnd)) fail("invalid load command length");
    if (command === 0x1d) {
      if (signature || commandSize !== 16) fail("duplicate/invalid LC_CODE_SIGNATURE");
      signature = { commandOffset: cursor, offset: bytes.readUInt32LE(cursor + 8), size: bytes.readUInt32LE(cursor + 12) };
      if (signature.offset < commandsEnd || signature.size < 12 || !bounded(signature.offset, signature.size, bytes.length)) fail("signature outside file");
    }
    if (command === 0x19) {
      if (commandSize < 72) fail("short LC_SEGMENT_64");
      const name = cstring(bytes.subarray(cursor + 8, cursor + 24)), fileOffset = u64(bytes, cursor + 40), fileSize = u64(bytes, cursor + 48);
      const sectionCount = bytes.readUInt32LE(cursor + 64);
      if (commandSize !== 72 + sectionCount * 80 || !bounded(fileOffset, fileSize, bytes.length)) fail("invalid segment/sections");
      segments.push({ name, fileOffset, fileSize, commandOffset: cursor, fileSizeFieldOffset: cursor + 48 });
      for (let j = 0; j < sectionCount; ++j) {
        const at = cursor + 72 + j * 80, sectionSize = u64(bytes, at + 40), offset = bytes.readUInt32LE(at + 48), type = bytes.readUInt32LE(at + 64) & 255;
        const zeroFill = [1, 0x0c, 0x12].includes(type);
        if (!zeroFill && sectionSize && (!bounded(offset, sectionSize, bytes.length) || offset < fileOffset || offset + sectionSize > fileOffset + fileSize)) fail("section exceeds segment");
        sections.push({ segment: name, name: cstring(bytes.subarray(at, at + 16)), offset, size: sectionSize, zeroFill });
      }
    }
    cursor += commandSize;
  }
  if (cursor !== commandsEnd || !signature) fail("command count/size mismatch or missing signature");
  const linkedit = segments.filter(s => s.name === "__LINKEDIT");
  if (linkedit.length !== 1 || signature.offset < linkedit[0].fileOffset || signature.offset + signature.size > linkedit[0].fileOffset + linkedit[0].fileSize)
    fail("signature is not inside the unique __LINKEDIT segment");
  for (const section of sections) if (!section.zeroFill && section.size && section.offset < signature.offset + signature.size && section.offset + section.size > signature.offset)
    fail("signature overlaps a code/data section");
  const blob = bytes.subarray(signature.offset, signature.offset + signature.size);
  if (blob.readUInt32BE(0) !== 0xfade0cc0) fail("expected embedded signature superblob");
  const length = blob.readUInt32BE(4), slots = blob.readUInt32BE(8);
  if (length < 12 || length > blob.length || slots > 1000 || 12 + slots * 8 > length) fail("invalid signature superblob table");
  const ranges = [], types = new Set();
  for (let i = 0; i < slots; ++i) {
    const type = blob.readUInt32BE(12 + i * 8), offset = blob.readUInt32BE(16 + i * 8);
    if (types.has(type) || offset < 12 + slots * 8 || !bounded(offset, 8, length)) fail("invalid duplicate signature slot");
    types.add(type); const size = blob.readUInt32BE(offset + 4);
    if (type === 0 && (blob.readUInt32BE(offset) !== 0xfade0c02 || size < 44)) fail("invalid primary CodeDirectory");
    if (size < 8 || !bounded(offset, size, length) || ranges.some(r => offset < r.end && offset + size > r.start)) fail("overlapping signature slot");
    ranges.push({ start: offset, end: offset + size });
  }
  if (!types.has(0)) fail("no primary CodeDirectory");
  // Apple's signer may leave previous signature bytes in its reserved signature
  // allocation. These remain inside LC_CODE_SIGNATURE; codesign validates them.
  return { architecture: "arm64", fileBytes: bytes.length, commandsEnd, signature, superblobLength: length,
    signatureReservedTailSha256: sha(blob.subarray(length)), slotTypes: [...types], segments, sections };
}

/** Exact signing-only policy: normal signer may resize its trailing allocation.
 * LC_CODE_SIGNATURE.datasize and the proven matching __LINKEDIT.filesize field
 * are then the only allowed header changes. No generic ranges, vmsize, moved
 * signature, segment/section offsets, code, or other LINKEDIT payload may change.
 */
export function compareSignatureOnly(before, after) {
  const a = inspectMachOSignature(before), b = inspectMachOSignature(after);
  if (a.signature.commandOffset !== b.signature.commandOffset || a.signature.offset !== b.signature.offset ||
      a.signature.offset + a.signature.size !== before.length || b.signature.offset + b.signature.size !== after.length)
    fail("signature moved or is not the trailing allocation; explicit structural review required");
  const oldLink = a.segments.find(row => row.name === "__LINKEDIT"), newLink = b.segments.find(row => row.name === "__LINKEDIT");
  const delta = b.signature.size - a.signature.size, fields = [];
  if (oldLink.commandOffset !== newLink.commandOffset || oldLink.fileOffset !== newLink.fileOffset ||
      oldLink.fileOffset + oldLink.fileSize !== before.length || newLink.fileOffset + newLink.fileSize !== after.length ||
      newLink.fileSize - oldLink.fileSize !== delta || after.length - before.length !== delta)
    fail("LINKEDIT/file-size change does not exactly match the validated signature allocation delta");
  if (delta !== 0) {
    fields.push({ name: "LC_CODE_SIGNATURE.datasize", offset: a.signature.commandOffset + 12, bytes: 4, before: a.signature.size, after: b.signature.size });
    fields.push({ name: "LC_SEGMENT_64[__LINKEDIT].filesize", offset: oldLink.fileSizeFieldOffset, bytes: 8, before: oldLink.fileSize, after: newLink.fileSize });
  }
  const offset = a.signature.offset, changedHeaderBytes = [], immutableBytes = Buffer.from(before.subarray(0, offset));
  for (let i = 0; i < offset; ++i) {
    if (before[i] === after[i]) continue;
    const field = fields.find(field => i >= field.offset && i < field.offset + field.bytes);
    if (!field) fail(`non-signature payload changed at byte ${i}`);
    changedHeaderBytes.push({ offset: i, before: before[i], after: after[i], field: field.name });
  }
  for (const field of fields) immutableBytes.fill(0, field.offset, field.offset + field.bytes);
  return { status: "signature-only-change-validated", beforeSha256: sha(before), afterSha256: sha(after),
    fullFileBytesUnchanged: before.equals(after), immutableBytesSha256: sha(immutableBytes),
    excludedRanges: { before: [{ offset, bytes: a.signature.size, reason: "validated LC_CODE_SIGNATURE allocation" }],
      after: [{ offset, bytes: b.signature.size, reason: "validated LC_CODE_SIGNATURE allocation" }] },
    classifiedSigningFields: fields, changedHeaderBytes, signatureAllocationUnchanged: delta === 0, architecture: a.architecture,
    signatureBeforeSha256: sha(before.subarray(offset)), signatureAfterSha256: sha(after.subarray(offset)),
    verified: ["all-load-command-bytes-except-listed-validated-size-fields", "all-sections-code-data", "all-other-LINKEDIT-payload", "all-other-file-bytes"],
    beforeStructure: a, afterStructure: b };
}
