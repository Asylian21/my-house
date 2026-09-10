/** Packaging handoff only. Canonical seal-to-final comparator is unchanged. */
import {createHash} from 'node:crypto';
import {inspectMachOSignature,compareSignatureOnly} from '../macho-signature.mjs';
const sha=b=>createHash('sha256').update(b).digest('hex');
export function compareRawLinkPackaging(before,after){
 const a=inspectMachOSignature(before),b=inspectMachOSignature(after),x=a.segments.find(s=>s.name==='__LINKEDIT'),y=b.segments.find(s=>s.name==='__LINKEDIT');
 if(x.commandOffset!==y.commandOffset)throw Error('LINKEDIT command moved');
 const at=x.commandOffset+32,oldSize=before.readBigUInt64LE(at),newSize=after.readBigUInt64LE(at),round=n=>(BigInt(n)+16383n)/16384n*16384n;
 if(oldSize!==round(x.fileSize)||newSize!==round(y.fileSize))throw Error('LINKEDIT vmsize is not exact16KiB round-up of its validated filesize');
 const normalized=Buffer.from(before);normalized.writeBigUInt64LE(newSize,at);
 // This synthetic in-memory input changes exactly one independently proved size
 // field. The existing comparator rejects every other non-signature byte change.
 const strictRemainderProof=compareSignatureOnly(normalized,after);
 return {status:'raw-linked-code-preserved-through-packaging-signature',actualRawLinkSha256:sha(before),actualPackagedSha256:sha(after),validatedVmSizeField:{offset:at,bytes:8,before:Number(oldSize),after:Number(newSize),rule:'exact alignUp(validated __LINKEDIT filesize,16384) on both thin arm64 images'},strictRemainderInput:'in-memory raw link with only the independently validated vmsize field normalized; actual files never edited',strictRemainderProof};
}
