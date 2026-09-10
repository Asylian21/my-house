import { createHash } from 'node:crypto';
import { inspectMachOSignature } from './macho-signature.mjs';
const sha = bytes => createHash('sha256').update(bytes).digest('hex');
const fail = message => { throw Error(`Startup entry gate: ${message}`); };
const bounded = (offset, size, limit) => Number.isSafeInteger(offset) && Number.isSafeInteger(size) && offset >= 0 && size >= 0 && offset <= limit && size <= limit - offset;
const u64 = (bytes, at) => {const n=bytes.readBigUInt64LE(at);if(n>BigInt(Number.MAX_SAFE_INTEGER)) fail('unsafe 64-bit field');return Number(n);};
export function inspectStartupEntry(bytes) {
  const structure=inspectMachOSignature(bytes);
  if(bytes.readUInt32LE(12)!==2) fail('not MH_EXECUTE');
  let at=32, entry=null, table=null, text=null;
  for(let i=0;i<bytes.readUInt32LE(16);++i) {
    const cmd=bytes.readUInt32LE(at), size=bytes.readUInt32LE(at+4);
    if(cmd===0x80000028) {if(entry || size!==24) fail('duplicate/malformed LC_MAIN');entry={commandOffset:at,fileOffset:u64(bytes,at+8),stackSize:u64(bytes,at+16)};}
    if(cmd===2) {
      if(table || size!==24) fail('duplicate/malformed LC_SYMTAB');
      table={offset:bytes.readUInt32LE(at+8),count:bytes.readUInt32LE(at+12),stringsOffset:bytes.readUInt32LE(at+16),stringsSize:bytes.readUInt32LE(at+20)};
      if(!bounded(table.offset,table.count*16,bytes.length) || !bounded(table.stringsOffset,table.stringsSize,bytes.length)) fail('symbol table bounds');
    }
    if(cmd===0x19 && bytes.subarray(at+8,at+24).toString('ascii').split('\0')[0]==='__TEXT') {
      if(text) fail('duplicate TEXT segment');
      text={address:u64(bytes,at+24),fileOffset:u64(bytes,at+40),fileSize:u64(bytes,at+48),initialProtection:bytes.readUInt32LE(at+60)};
    }
    at+=size;
  }
  if(!entry || !table || !text || text.fileOffset!==0 || !(text.initialProtection&4)) fail('missing executable TEXT, symbols or LC_MAIN');
  const code=structure.sections.filter(s=>s.segment==='__TEXT' && s.name==='__text' && !s.zeroFill && s.size>0);
  if(code.length!==1 || !bounded(entry.fileOffset-code[0].offset,1,code[0].size)) fail('LC_MAIN is outside unique __text');
  const wanted=new Map([['_BreziMain',[]],['_main',[]]]);
  for(let i=0;i<table.count;++i) {
    const p=table.offset+i*16, type=bytes[p+4], index=bytes.readUInt32LE(p);
    if(type&0xe0 || (type&0x0e)!==0x0e) continue;
    if(index>=table.stringsSize) fail('invalid symbol string index');
    const start=table.stringsOffset+index,end=bytes.indexOf(0,start);
    if(end<start || end>=table.stringsOffset+table.stringsSize) fail('unterminated symbol');
    const name=bytes.toString('utf8',start,end);
    if(wanted.has(name)) wanted.get(name).push(u64(bytes,p+8));
  }
  if([...wanted.values()].some(rows=>rows.length!==1)) fail('expected exactly one _BreziMain and original _main symbol');
  const address=wanted.get('_BreziMain')[0], originalAddress=wanted.get('_main')[0];
  if(address===originalAddress || address-text.address!==entry.fileOffset ||
      !bounded(originalAddress-text.address-code[0].offset,1,code[0].size)) fail('LC_MAIN does not resolve to distinct app entry with original main preserved');
  return {status:'linked-self-exec-entry-validated',architecture:'arm64',symbol:'_BreziMain',originalMainSymbol:'_main',
    commandOffset:entry.commandOffset,entryFileOffset:entry.fileOffset,entryAddress:`0x${address.toString(16)}`,
    originalMainAddress:`0x${originalAddress.toString(16)}`,stackSize:entry.stackSize,
    codeSection:{segment:'__TEXT',name:'__text',offset:code[0].offset,bytes:code[0].size,sha256:sha(bytes.subarray(code[0].offset,code[0].offset+code[0].size))}};
}
