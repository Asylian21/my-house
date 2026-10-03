"""Root-only exact74 APFS copies into its already prepared original R22 clone."""
import ctypes
import importlib.util
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-realism-integration-copy-r22.py'
sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('r22_copy_closed_guard',ROOT/'scripts/unreal/exterior-realism-integration-guards-r22.py')
guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard)
g=guard.g


def main():
    plan,bundle=guard.validate_plan();output=guard.CANDIDATE;project=output/'Project/BreziTwin';base=guard.BASE/'Project/BreziTwin'
    receipt=output/'realism-integration-package-copy.json';clone=output/'realism-integration-project-clone.json'
    guard.require(not receipt.exists()and not clone.exists(),'Copied package receipts are immutable; root must prepare a fresh candidate')
    initial=guard.read(output/'realism-integration-base-clone-proof.json')
    guard.require(initial['status']=='verified-original-r16-independent-apfs-clone-final-integration-plan-pending'
        and initial['finalIntegrationPlanPending']is True,'Actual root-owned original clone proof required')
    guard.require(g.inventory(project/'Content')==bundle['content']and g.project_proof(project)==bundle['protected']
        and g.inventory(base/'Content')==bundle['content']and g.project_proof(base)==bundle['protected'],
        'Original/fresh root project bytes differ before saved package copy')
    for directory,rows in (('Content',bundle['content']),('',bundle['protected'])):
        for relative in rows:
            a,b=base/directory/relative,project/directory/relative
            guard.require((a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino),'Original native hardlink forbidden')
    libc=ctypes.CDLL('/usr/lib/libSystem.B.dylib',use_errno=True)
    libc.clonefile.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int];libc.clonefile.restype=ctypes.c_int
    copied=[]
    for row in bundle['packages']:
        source=Path(row['source']);destination=project/'Content'/row['relativeContentPath']
        guard.require(not destination.exists()and source.is_file()and guard.sha(source)==row['sha256'],
            'Saved source package changed or fresh target already exists')
        destination.parent.mkdir(parents=True,exist_ok=True)
        result=libc.clonefile(str(source).encode(),str(destination).encode(),0)
        guard.require(result==0,'APFS independent saved package clone failed errno '+str(ctypes.get_errno()))
        guard.require(guard.sha(destination)==row['sha256']and destination.stat().st_size==row['bytes']
            and (source.stat().st_dev,source.stat().st_ino)!=(destination.stat().st_dev,destination.stat().st_ino),
            'Copied native package bytes/inodes differ')
        copied.append({**row,'destination':str(destination),'independentInodes':True})
    expected=dict(bundle['content']);expected.update({r['relativeContentPath']:{'sha256':r['sha256'],'bytes':r['bytes']}for r in copied})
    guard.require(len(copied)==74 and g.inventory(project/'Content')==expected and g.project_proof(project)==bundle['protected'],
        'Exact74 saved packages/original protected bytes required after copy')
    guard.validate_plan()
    guard.write(receipt,{'schema':guard.SCHEMA,'owner':OWNER,'status':'verified-byte-identical-independent-apfs-saved-donor-packages-copied',
        'selectedPlan':guard.pin(guard.PLAN),'baseNativeReport':plan['baseNativeReport'],'originalBaseCloneProof':guard.pin(output/'realism-integration-base-clone-proof.json'),
        'project':str(project),'copiedPackages':copied,'copiedPackageCount':74,'originalContentFilesUnchanged':3975,
        'protectedOriginalFilesUnchanged':132,'nativeExecuted':False,'sceneMapChanged':False,'viewpointsChanged':False})
    guard.write(clone,{'schema':guard.SCHEMA,'owner':OWNER,
        'status':'verified-byte-identical-independent-apfs-r22a-project-clone-before-realism-integration-native-r1',
        'selectedPlan':guard.pin(guard.PLAN),'baseNativeReport':plan['baseNativeReport'],'project':str(project),
        'originalFileCount':4107,'newCopiedPackageCount':74,'contentFileCount':4049,
        'originalBaseCloneProof':guard.pin(output/'realism-integration-base-clone-proof.json'),'packageCopyReceipt':guard.pin(receipt),
        'baseContentInventory':plan['baseContentInventory'],'baseProjectProof':plan['baseProjectProof'],
        'originalFilesIndependentAndByteIdentical':True,'copiedPackagesIndependentAndByteIdentical':True,'nativeExecuted':False})
    print(__import__('json').dumps({'packageCopy':guard.pin(receipt),'projectClone':guard.pin(clone),'copiedPackages':74,'nativeExecuted':False}))


if __name__=='__main__':main()
