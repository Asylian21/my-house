"""Root-only exact59 independent APFS copies into a fresh original R16 clone.

No Unreal/map/actor execution. The four-donor selected plan and already saved
native reports are validated before and after copying only their new packages.
"""
import ctypes
import importlib.util
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-realism-clean-integration-copy-r27.py'
sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('r27_copy_closed_guard',ROOT/'scripts/unreal/exterior-realism-clean-integration-guards-r27.py')
guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard)
g=guard.g


def main():
    plan,bundle=guard.validate_plan();output=guard.CANDIDATE
    project=output/'Project/BreziTwin';base=guard.BASE/'Project/BreziTwin'
    receipt=output/'realism-clean-integration-package-copy.json'
    clone=output/'realism-clean-integration-project-clone.json'
    initial_path=output/'clean-realism-integration-base-clone-proof.json'
    guard.require(not receipt.exists()and not clone.exists(),'Copied receipts are immutable; a fresh candidate is required')
    initial=guard.read(initial_path)
    guard.require(initial['status']==guard.INITIAL_STATUS and initial['packageCopyPending']is True
        and initial['selectedPlan']is None and initial['nativeExecuted']is False and initial['fileCount']==4107
        and initial['baseNativeReport']==plan['baseNativeReport'],'Actual root-owned original R16 pending clone proof required')
    guard.require(g.inventory(project/'Content')==bundle['content']and g.project_proof(project)==bundle['protected']
        and g.inventory(base/'Content')==bundle['content']and g.project_proof(base)==bundle['protected'],
        'Original/fresh root project bytes differ before package copy')
    for directory,rows in (('Content',bundle['content']),('',bundle['protected'])):
        for relative in rows:
            a,b=base/directory/relative,project/directory/relative
            guard.require((a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino),'Original native hardlink forbidden')
    guard.require(len(bundle['packages'])==59 and len({r['relativeContentPath']for r in bundle['packages']})==59,
        'Exactly59 disjoint declared four-donor packages required')
    libc=ctypes.CDLL('/usr/lib/libSystem.B.dylib',use_errno=True)
    libc.clonefile.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int];libc.clonefile.restype=ctypes.c_int
    copied=[]
    for row in bundle['packages']:
        source=Path(row['source']);destination=project/'Content'/row['relativeContentPath']
        guard.require(not destination.exists()and source.is_file()and guard.sha(source)==row['sha256']
            and source.stat().st_size==row['bytes'],'Saved package changed or target already exists')
        destination.parent.mkdir(parents=True,exist_ok=True)
        result=libc.clonefile(str(source).encode(),str(destination).encode(),0)
        guard.require(result==0,'Independent APFS saved package copy failed errno '+str(ctypes.get_errno()))
        guard.require(guard.sha(destination)==row['sha256']and destination.stat().st_size==row['bytes']
            and (source.stat().st_dev,source.stat().st_ino)!=(destination.stat().st_dev,destination.stat().st_ino),
            'Copied package bytes or independent inodes differ')
        copied.append({**row,'destination':str(destination),'independentInodes':True})
    expected=dict(bundle['content'])
    expected.update({r['relativeContentPath']:{'sha256':r['sha256'],'bytes':r['bytes']}for r in copied})
    guard.require(len(copied)==59 and len(expected)==4034 and g.inventory(project/'Content')==expected
        and g.project_proof(project)==bundle['protected'],'Exact59 packages/original protected bytes required after copy')
    guard.validate_plan()
    guard.write(receipt,{'schema':guard.SCHEMA,'owner':OWNER,'status':guard.COPY_STATUS,
        'selectedPlan':guard.pin(guard.PLAN),'baseNativeReport':plan['baseNativeReport'],'originalBaseCloneProof':guard.pin(initial_path),
        'project':str(project),'copiedPackages':copied,'copiedPackageCount':59,'originalContentFilesUnchanged':3975,
        'protectedOriginalFilesUnchanged':132,'nativeExecuted':False,'sceneMapChanged':False,'viewpointsChanged':False,
        'excludedDonors':['R20_CURVED_GRASS','R23_CREAM_ROOF'],'originalGrassInstanceDataNeverWritten':True})
    guard.write(clone,{'schema':guard.SCHEMA,'owner':OWNER,'status':guard.CLONE_STATUS,
        'selectedPlan':guard.pin(guard.PLAN),'baseNativeReport':plan['baseNativeReport'],'project':str(project),
        'originalFileCount':4107,'newCopiedPackageCount':59,'contentFileCount':4034,
        'originalBaseCloneProof':guard.pin(initial_path),'packageCopyReceipt':guard.pin(receipt),
        'baseContentInventory':plan['baseContentInventory'],'baseProjectProof':plan['baseProjectProof'],
        'originalFilesIndependentAndByteIdentical':True,'copiedPackagesIndependentAndByteIdentical':True,'nativeExecuted':False})
    print(__import__('json').dumps({'packageCopy':guard.pin(receipt),'projectClone':guard.pin(clone),'copiedPackages':59,'nativeExecuted':False}))


if __name__=='__main__':main()
