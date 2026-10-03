"""Root-only independent APFS copies of17 already-saved R24 tree packages.

Fresh R28b-derived candidate only. No native import, map/actor/member API,
geometry generation or modification of any original/donor package.
"""
import ctypes
import importlib.util
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-original-tree-group-copy-r29.py'


def main():
    spec=importlib.util.spec_from_file_location('r29_copy_closed_scope',ROOT/'scripts/unreal/exterior-original-tree-group-guards-r29.py')
    guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
    plan,bundle=guard.validate_plan();g=guard.g;output=guard.CANDIDATE
    project=output/'Project/BreziTwin';base=guard.BASE/'Project/BreziTwin'
    receipt=output/'original-tree-group-package-copy.json';clone=output/'original-tree-group-project-clone.json'
    initial_path=output/'original-tree-group-base-clone-proof.json'
    guard.require(not receipt.exists()and not clone.exists(),'Copied receipts are immutable; use a fresh candidate')
    initial=guard.read(initial_path)
    guard.require(initial['status']==guard.INITIAL_STATUS and initial['packageCopyPending']is True
        and initial['selectedPlan']is None and initial['nativeExecuted']is False and initial['fileCount']==4175
        and len(initial['files'])==4175 and initial['nativeBaseReport']==plan['baseNativeReport']
        and initial['originalTreeSourceProposal']==plan['sourceProposal'],'Actual root-owned pending R28b clone proof required')
    guard.require(len(bundle['content'])==4043 and len(bundle['protected'])==132
        and g.inventory(project/'Content')==bundle['content']and g.project_proof(project)==bundle['protected']
        and g.inventory(base/'Content')==bundle['content']and g.project_proof(base)==bundle['protected'],
        'Actual saved base/fresh candidate bytes differ before package copy')
    expected_original={'Content/'+key:value for key,value in bundle['content'].items()};expected_original.update(bundle['protected']);seen=set()
    for row in initial['files']:
        source,destination=Path(row['source']),Path(row['destination'])
        guard.require(source.is_relative_to(base)and destination.is_relative_to(project)
            and source.relative_to(base)==destination.relative_to(project)and row['independentInodes']is True,
            'Initial clone path/independence proof differs')
        relative=str(destination.relative_to(project));guard.require(relative in expected_original and relative not in seen,'Unknown/duplicate initial clone file')
        seen.add(relative);guard.require({k:row[k]for k in('sha256','bytes')}==expected_original[relative]
            and source.stat().st_size==destination.stat().st_size==row['bytes']
            and(source.stat().st_dev,source.stat().st_ino)!=(destination.stat().st_dev,destination.stat().st_ino),
            'An original package was hardlinked or its initial hash/size differs')
    guard.require(seen==set(expected_original),'Exact original4175 clone file set required')
    packages=bundle['packages'];guard.require(len(packages)==len({r['relativeContentPath']for r in packages})==17,'Exactly17 disjoint saved tree packages required')
    libc=ctypes.CDLL('/usr/lib/libSystem.B.dylib',use_errno=True)
    libc.clonefile.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_int];libc.clonefile.restype=ctypes.c_int
    copied=[]
    for row in packages:
        relative=row['relativeContentPath'];source=Path(row['source']);destination=project/'Content'/relative
        guard.require(not Path(relative).is_absolute()and '..'not in Path(relative).parts
            and relative.startswith('Brezi/OriginalTree20261002R24/')and relative.endswith('.uasset')
            and relative not in bundle['content']and not destination.exists(),'Unowned/overlapping package copy target')
        guard.require(source.is_file()and guard.sha(source)==row['sha256']and source.stat().st_size==row['bytes'],'Actual saved donor package changed')
        destination.parent.mkdir(parents=True,exist_ok=True)
        result=libc.clonefile(str(source).encode(),str(destination).encode(),0)
        guard.require(result==0,'Independent APFS tree package copy failed errno '+str(ctypes.get_errno()))
        guard.require(guard.sha(destination)==row['sha256']and destination.stat().st_size==row['bytes']
            and(source.stat().st_dev,source.stat().st_ino)!=(destination.stat().st_dev,destination.stat().st_ino),
            'Copied bytes or independent inodes differ')
        copied.append({**row,'destination':str(destination),'independentInodes':True})
    expected=dict(bundle['content']);expected.update({r['relativeContentPath']:{'sha256':r['sha256'],'bytes':r['bytes']}for r in copied})
    guard.require(len(expected)==4060 and g.inventory(project/'Content')==expected and g.project_proof(project)==bundle['protected']
        and g.inventory(base/'Content')==bundle['content']and g.project_proof(base)==bundle['protected'],
        'Exact17 additions/original map/protected bytes required after copy')
    guard.validate_plan()
    guard.write(receipt,{'schema':guard.SCHEMA,'owner':OWNER,'status':guard.COPY_STATUS,'selectedPlan':guard.pin(guard.PLAN),
        'baseNativeReport':plan['baseNativeReport'],'sourceProposal':plan['sourceProposal'],'originalBaseCloneProof':guard.pin(initial_path),
        'project':str(project),'copiedPackages':copied,'copiedPackageCount':17,'originalContentFilesUnchanged':4043,
        'protectedOriginalFilesUnchanged':132,'nativeExecuted':False,'sceneMapChanged':False,'viewpointsChanged':False,
        'geometryImportedOrGenerated':False,'originalActorOrMemberMutationApisCalled':False})
    guard.write(clone,{'schema':guard.SCHEMA,'owner':OWNER,'status':guard.CLONE_STATUS,'selectedPlan':guard.pin(guard.PLAN),
        'baseNativeReport':plan['baseNativeReport'],'sourceProposal':plan['sourceProposal'],'project':str(project),
        'originalFileCount':4175,'newCopiedPackageCount':17,'contentFileCount':4060,'originalBaseCloneProof':guard.pin(initial_path),
        'packageCopyReceipt':guard.pin(receipt),'baseContentInventory':plan['baseContentInventory'],'baseProjectProof':plan['baseProjectProof'],
        'originalFilesIndependentAndByteIdentical':True,'copiedPackagesIndependentAndByteIdentical':True,'nativeExecuted':False})
    print(__import__('json').dumps({'packageCopy':guard.pin(receipt),'projectClone':guard.pin(clone),'copiedPackages':17,'nativeExecuted':False}))


if __name__=='__main__':main()
