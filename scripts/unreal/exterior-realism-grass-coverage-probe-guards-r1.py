"""Strict original R16 four-group raw matrix capture contract; source only."""
import hashlib
import importlib.util
import math
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
OWNER='scripts/unreal/exterior-realism-grass-coverage-probe-guards-r1.py'
SCHEMA='brezi-original-r16-grass-coverage-raw-matrix-probe-r1'
STUDY=ROOT/'output/unreal/exterior-realism-grass-coverage-20261002-r1-study'
PLAN=STUDY/'raw-matrix-probe-plan.json'
OUTPUT=ROOT/'output/unreal/exterior-realism-grass-coverage-20261002-r1-probe'
NATIVE='scripts/unreal/exterior-realism-grass-coverage-probe-r1.py'
s=importlib.util.spec_from_file_location('coverage_original_closed_composer',ROOT/'scripts/unreal/exterior-realism-integration-native-r22-r3.py')
n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
require,sha,read,write,pin,check_pin,digest,now=(getattr(n,k)for k in ('require','sha','read','write','pin','check_pin','digest','now'))
GROUP_COUNTS={'EX_meadow_-3_2_LawnTuft0':2230,'EX_meadow_-3_2_LawnTuft1':2190,
    'EX_meadow_-3_2_LawnTuft2':2288,'EX_meadow_-3_2_LawnTuft3':2241}


def sources():
    return {'native':ROOT/NATIVE,'guards':ROOT/OWNER,
        'producer':ROOT/'scripts/unreal/exterior-realism-grass-coverage-probe-study-r1.py',
        'tests':ROOT/'scripts/unreal/test_exterior_realism_grass_coverage_probe_r1.py',
        'design':ROOT/'docs/unreal-original-grass-coverage-matrix-probe-r1.md'}


def binary64_matrix_hash(rows):
    h=hashlib.sha256()
    require(isinstance(rows,list),'Ordered matrix list required')
    for matrix in rows:
        require(isinstance(matrix,list)and len(matrix)==4,'Each matrix must contain4 planes')
        for plane in matrix:
            require(isinstance(plane,list)and len(plane)==4,'Each native plane must contain4 coordinates')
            require(all(type(v)is float and math.isfinite(v)for v in plane),'Native finite binary64 coordinates required')
            h.update(struct.pack('<4d',*plane))
    return h.hexdigest()


def binary64_equal(a,b):
    if isinstance(a,list)and isinstance(b,list):return len(a)==len(b)and all(binary64_equal(x,y)for x,y in zip(a,b))
    return type(a)is float and type(b)is float and math.isfinite(a)and math.isfinite(b)and struct.pack('<d',a)==struct.pack('<d',b)


def validate_original_values(values,base,original):
    require(set(values)==set(original)==set(GROUP_COUNTS),'Only exact4 original grass groups may be captured')
    for group,count in GROUP_COUNTS.items():
        record=base['geometry']['groups'][group]
        require(record['instances']==count==len(values[group])and values[group]==original[group]
            and digest(values[group])==record['transformsSha256'],'Original ordered native root frames changed: '+group)
    require(sum(map(len,values.values()))==8949,'All8949 original members required')


def source_basis():
    require(sha(ROOT/n.OWNER)=='f93ea98e9599ac85abd2842dc8c08d50f7977366fa1bb3ae35b5923bfd12cbae','Frozen composer changed')
    plan,bundle=n.guard.validate_plan();donor=bundle['reports']['grass']
    original=read(check_pin(donor['originalMembersBefore']));validate_original_values(original,bundle['base'],original)
    groups={key:bundle['base']['geometry']['groups'][key]for key in GROUP_COUNTS}
    return plan,bundle,donor,original,groups


def validate_plan(path=PLAN):
    require(Path(path).resolve()==PLAN,'Only exact frozen raw-matrix probe plan eligible')
    plan=read(path);basis,bundle,donor,original,groups=source_basis()
    require(plan['schema']==SCHEMA and plan['owner']=='scripts/unreal/exterior-realism-grass-coverage-probe-study-r1.py'
        and plan['status']=='source-only-original-grass-raw-matrix-probe-native-pending'
        and plan['baseNativeReport']==basis['baseNativeReport']and plan['originalMembers']==donor['originalMembersBefore']
        and plan['groupControls']==groups and plan['groupCounts']==GROUP_COUNTS and plan['instances']==8949,
        'Original four-group identity/frame/count basis changed')
    require(plan['baseContentInventory']==basis['baseContentInventory']and plan['baseProjectProof']==basis['baseProjectProof']
        and plan['originalComposerPlan']==pin(n.guard.PLAN)and plan['originalSavedGrassDonor']==basis['donors']['grass']['report']
        and plan['frozenComposerRepair']==pin(n.repair.SUPPLEMENT),
        'Frozen saved source provenance changed')
    require(plan['probeOutput']==str(OUTPUT)and plan['sourceProject']==str(n.guard.BASE/'Project/BreziTwin')
        and plan['futureRestorationCullPolicyCm']==[18000,24000]
        and all(plan[k]is False for k in ('nativeExecuted','sourceSceneMutated','appearanceAccepted','performanceAccepted','shippingAccepted')),
        'Probe cannot apply a restoration/visibility change or claim acceptance')
    require(set(plan['ownedSources'])==set(sources()),'Exact probe source roles required')
    expected=dict(n.repair.validate_supplement()['inputFiles']);expected[str(n.repair.SUPPLEMENT)]=sha(n.repair.SUPPLEMENT)
    for role,path in sources().items():
        record=plan['ownedSources'][role];require(record['live']==pin(path)
            and Path(record['snapshot']['path'])==STUDY/('source-'+path.name)
            and check_pin(record['snapshot']).read_bytes()==path.read_bytes(),'Probe source snapshot changed')
        for key in ('live','snapshot'):expected[record[key]['path']]=record[key]['sha256']
    for record in plan['engineSourceEvidence'].values():expected[record['path']]=record['sha256'];check_pin(record)
    expected[plan['sourceTests']['path']]=plan['sourceTests']['sha256'];tests=read(check_pin(plan['sourceTests']))
    require(tests['status']=='passed'and tests['exitCode']==0 and tests['testCount']==6,'Probe CPU guards must pass')
    require(plan['inputFiles']==expected,'Exact raw-matrix probe source closure changed')
    for file,value in expected.items():require(sha(file)==value,'Probe source input changed: '+file)
    return plan,bundle,original
