"""Strict original-USD/source/clone closure for one isolated whole-D oak pilot."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'output/unreal/megaplants-english-oak-20261002-r1'
BASE = ROOT/'output/unreal/exterior-20261002-r32a'
OUTPUT = ROOT/'output/unreal/megaplants-english-oak-native-20261002-r1'
PROJECT = OUTPUT/'Project/BreziTwin'
PLAN = SOURCE/'oak-usd-pilot-plan-r1.json'
PREFIX = '/Game/Brezi/EnglishOakPilot20261002R1'
MAP = PREFIX+'/Maps/EnglishOakPilot'
SCHEMA = 'brezi-original-licensed-english-oak-usd-pilot-r1'
BASE_SHA = '99b80074fe1309ee951ea662cf42f75ecd6d0a2bc711f0c76cc5d34e18891a19'
INSPECTION_SHA = 'b9b0d557c8a8836f66424b7ebc06b8723adac763a1ac9ea0b2cfe0d2ff8e3d1a'
EXTRACT_SHA = 'f54766f8e5bc0f40c134bc89a6a14b0473db5aae1ca39ab050d036fcf899324d'
CLONE_SHA = 'e7af55d29e7fc89407d03484c889b9d30c5a346b85c6ef1376237edd33ab17fa'
PLUGIN = {'Name': 'USDImporter', 'Enabled': True, 'TargetAllowList': ['Editor']}

def require(v, message):
    if not v: raise RuntimeError(message)

def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
    return h.hexdigest()

def pin(path):
    p=Path(path).resolve();return {'path':str(p),'sha256':sha(p),'bytes':p.stat().st_size}

def check_pin(row):
    require(pin(row['path'])==row,'Pinned original file changed: '+row['path']);return Path(row['path'])

def read(path): return json.loads(Path(path).read_text())

def write(path,value):
    p=Path(path);require(not p.exists(),'Never overwrite pilot history: '+str(p))
    p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def validate_source(extraction,inspection):
    require(extraction['schema']=='brezi-original-licensed-english-oak-usd-source-r1'
            and extraction['fileCount']==9 and extraction['expandedBytes']==445120561
            and extraction['sourceArchiveUnchanged'] is True,'Exact original nine-file extraction required')
    require(inspection['schema']=='brezi-original-licensed-english-oak-usd-inspection-r1'
            and inspection['allOriginalFilesUnchanged'] is True and inspection['unrealExecuted'] is False,
            'Only actual original source inspection accepted')
    layers=inspection['usdLayers'];require(len(layers)==5,'Exactly five original USD layers required')
    for layer in layers:
        require(layer['stageUpAxis']=='Y' and layer['metersPerUnit']==1.0 and layer['assetAttributes']==[],
                'Original axis/units/no-texture contract differs')
        shaders=[x for x in layer['materialsAndShaders'] if x['type']=='Shader']
        require(len(shaders)==2,'Exactly two original preview shaders required')
        expected={'Tileable_Material':[0.1420000046491623,0.06599999964237213,0.03099999949336052],
                  'TwoSided_Material':[0.08699999749660492,0.15299999713897705,0.020999999716877937]}
        for row in shaders:
            key=row['path'].split('/')[-1]
            authored={a['name']:a['value'] for a in row['attributes'] if a['authored']}
            require(key in expected and authored=={'info:id':'UsdPreviewSurface','inputs:diffuseColor':expected[key]},
                    'Source shader changed or replacement texture/material added')
    selected=next(l for l in layers if Path(l['source']['path']).name=='Tree_English_Oak_Forest_01_D.usd')
    require(selected['rootPrims']==['/Tree_English_Oak_Forest_01_D']
            and selected['treeBaseFanTriangles']==1035730
            and selected['assemblyExpandedFanTrianglesSourceEstimate']==2645037
            and selected['basePlusExpandedFanTrianglesSourceEstimate']==3680767
            and selected['pointInstancers'][0]['instanceCount']==188,
            'Whole original D, not a branch/flattened replacement, is required')
    require(any(a['path']=='/Tree_English_Oak_Forest_01_D' and 'NaniteAssemblyRootAPI' in a['appliedSchemas']
                for a in selected['appliedSchemas']), 'Original Nanite assembly root missing')
    require(any(a['attribute']=='unreal:naniteAssembly:meshType' and a['value']=='skeletalMesh'
                for a in selected['unrealAttributes']), 'Original skeletal assembly route missing')
    return selected

def validate_plan():
    plan=read(PLAN)
    require(plan['schema']==SCHEMA and plan['status']=='source-ready-whole-original-D-native-pilot-pending'
            and plan['nativeExecuted'] is False and plan['materialSubstitutionAllowed'] is False,
            'Only the original-content experimental source plan is accepted')
    require(plan['output']==str(OUTPUT) and plan['project']==str(PROJECT) and plan['map']==MAP
            and plan['namespace']==PREFIX and plan['pluginAddition']==PLUGIN,'Pilot namespace/project widened')
    require(plan['sourceExtraction']['sha256']==EXTRACT_SHA and plan['usdInspection']['sha256']==INSPECTION_SHA
            and plan['baseNativeReport']['sha256']==BASE_SHA and plan['initialRootClone']['sha256']==CLONE_SHA,
            'Only measured original source and actual saved R32 base are accepted')
    for row in plan['inputFiles']:check_pin(row)
    original=read(check_pin(plan['sourceExtraction']));inspection=read(check_pin(plan['usdInspection']))
    selected=validate_source(original,inspection)
    require(plan['selectedUsd']==selected['source'] and plan['stageRoot']==selected['rootPrims'][0],
            'Selected original USD/root differs')
    require(plan['treePlacement']=={'locationCm':[0,0,0],'rotationDegrees':[0,0,0],'scale':[1,1,1]}
            and plan['ground']=={'sizeCm':[4500,4500],'surfaceZCm':-2,'colorLinear':[.18,.18,.18],
                                 'roughness':.8,'specular':.25},'Authored pilot placement widened')
    require(plan['camera']['id']=='english-oak-original-D-close-r1' and plan['camera']['eyeCm']==[2000,-2800,700]
            and plan['camera']['targetCm']==[0,0,650] and plan['camera']['horizontalFovDegrees']==58
            and plan['cameraSourceBoundsAllCornersInside'] is True,'Camera source fit/identity differs')
    base=read(check_pin(plan['baseNativeReport']))
    require(base['schema']=='brezi-context-yard-resolved-ground-and-low-detail-native-r32'
            and base['nativeProcessId']==5443 and base['nativeApplied'] is True
            and base['savedMapUnloadedReloaded'] is True and base['actualCounts']['contentFiles']==4086,
            'Actual saved R32 base required')
    raw=read(check_pin(plan['baseProcessRaw']));terminal=read(check_pin(plan['baseProcessTerminal']))
    require(raw['code']==0 and raw['pid']==5443 and terminal['sourcePinsUnchangedAfterNative'] is True,
            'Actual R32 completed process/source closure required')
    return plan,base

def validate_clone(plan,base,prepared=False):
    clone=read(check_pin(plan['initialRootClone']))
    require(clone['schema']==SCHEMA and clone['status']=='verified-original-r32-independent-apfs-clone-before-english-oak-usd-pilot'
            and clone['fileCount']==4218 and clone['selectedPlan'] is None
            and clone['pluginEnablementPending'] is True and clone['nativeExecuted'] is False,
            'Exact independent initial root clone required')
    require(clone['nativeBaseReport']==plan['baseNativeReport'] and Path(clone['project'])==PROJECT,
            'Clone base/project differs')
    content=read(check_pin(base['afterContentInventory']));protected=read(check_pin(base['protectedProjectProof']))
    expected={**{'Content/'+k:v for k,v in content.items()},**protected}
    require(len(content)==4086 and len(protected)==132 and len(expected)==4218,'Exact original file scope required')
    rows={str(Path(r['destination']).relative_to(PROJECT)):r for r in clone['files']}
    require(set(rows)==set(expected),'Clone original file-set differs')
    for key,value in expected.items():
        row=rows[key];source=Path(row['source']);dest=Path(row['destination'])
        require(row['sha256']==value['sha256'] and row['bytes']==value['bytes'] and row['independentInodes'] is True,
                'Original clone row differs')
        require(source.stat().st_ino!=dest.stat().st_ino or source.stat().st_dev!=dest.stat().st_dev,
                'Original source shares an inode with probe')
        require(sha(source)==value['sha256'] and source.stat().st_size==value['bytes'],'Saved R32 source changed')
        if not(prepared and key=='BreziTwin.uproject'):
            require(sha(dest)==value['sha256'] and dest.stat().st_size==value['bytes'],'Probe original changed: '+key)
    if prepared:
        receipt=read(OUTPUT/'oak-usd-project-preparation.json')
        require(receipt['schema']==SCHEMA and receipt['status']=='verified-own-descriptor-only-usd-plugin-stage-native-pending'
                and receipt['selectedPlan']==pin(PLAN) and receipt['initialRootClone']==plan['initialRootClone']
                and receipt['nativeExecuted'] is False,'Typed descriptor preparation required')
        original=read(rows['BreziTwin.uproject']['source']);actual=read(PROJECT/'BreziTwin.uproject')
        intended=dict(original);intended['Plugins']=[*original['Plugins'],PLUGIN]
        require(actual==intended and receipt['descriptorAfter']==pin(PROJECT/'BreziTwin.uproject'),
                'Only appended Editor USDImporter descriptor delta allowed')
    else:
        require(not any(p['Name']=='USDImporter' for p in read(PROJECT/'BreziTwin.uproject')['Plugins']),
                'Descriptor already modified')
    return clone,expected

def inventory(project):
    project=Path(project)
    return {str(p.relative_to(project)):{'sha256':sha(p),'bytes':p.stat().st_size}
            for p in project.rglob('*') if p.is_file() and
            (p.relative_to(project).parts[0] in {'Content','Config','Source','Binaries'} or p.name=='BreziTwin.uproject')}

def validate_delta(before,after):
    changed={k for k,v in before.items() if after.get(k)!=v}
    added=set(after)-set(before)
    require(changed=={'Content/Data/viewpoints.json'},'Only probe camera Data may change original files')
    require(added and all(k.startswith('Content/Brezi/EnglishOakPilot20261002R1/') and k.endswith('.uasset') or
                         k=='Content/Brezi/EnglishOakPilot20261002R1/Maps/EnglishOakPilot.umap' for k in added),
            'New files escape isolated native namespace')
    require('Content/Brezi/Maps/Brezi.umap' in before and after['Content/Brezi/Maps/Brezi.umap']==before['Content/Brezi/Maps/Brezi.umap'],
            'Main saved architecture map changed')
    return {'changedOriginalFiles':sorted(changed),'newFiles':sorted(added),'originalMainMapUnchanged':True}
