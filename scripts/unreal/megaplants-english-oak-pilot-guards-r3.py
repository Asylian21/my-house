"""Strict original-USD/source/clone closure for one isolated whole-D oak pilot."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'output/unreal/megaplants-english-oak-20261002-r1'
BASE = ROOT/'output/unreal/exterior-20261002-r32a'
OUTPUT = ROOT/'output/unreal/megaplants-english-oak-native-20261002-r3'
PROJECT = OUTPUT/'Project/BreziTwin'
PLAN = SOURCE/'oak-usd-pilot-plan-r3.json'
PREFIX = '/Game/Brezi/EnglishOakPilot20261002R3'
MAP = PREFIX+'/Maps/EnglishOakPilot'
SCHEMA = 'brezi-original-licensed-english-oak-usd-pilot-r1'
BASE_SHA = '99b80074fe1309ee951ea662cf42f75ecd6d0a2bc711f0c76cc5d34e18891a19'
INSPECTION_SHA = 'b9b0d557c8a8836f66424b7ebc06b8723adac763a1ac9ea0b2cfe0d2ff8e3d1a'
EXTRACT_SHA = 'f54766f8e5bc0f40c134bc89a6a14b0473db5aae1ca39ab050d036fcf899324d'
CLONE_SHA = 'b10bea225840e8ec90dce3d03bf201c705ef23020f62f8870e8833a395a9d05c'
PLUGIN = {'Name': 'USDImporter', 'Enabled': True, 'TargetAllowList': ['Editor']}

def startup_config(original):
    require('r.Nanite.AllowAssemblies' not in original, 'Original startup config already contains an assembly override')
    require(original.count('[SystemSettings]\n') == 1, 'Exactly one original SystemSettings section required')
    return original.replace('[SystemSettings]\n', '[SystemSettings]\nr.Nanite.AllowAssemblies=1\n', 1)

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
    require(plan['sourceRevision']==3 and plan['startupConfigDelta']=={'relativePath':'Config/DefaultEngine.ini',
            'section':'SystemSettings','key':'r.Nanite.AllowAssemblies','value':'1'}
            and plan['nameOnlySelectionAllowed'] is False, 'Exact startup assembly repair required')
    diagnostic=read(check_pin(plan['actualReadOnlyPartDiagnostic']))
    require(plan['actualReadOnlyPartDiagnostic']['sha256']=='47840c9b0592df5b62f725502cf622eaaf00baf41eb505d4d86ac4db5af9d4d7'
            and diagnostic['schema']=='brezi-original-oak-preserved-partial-usd-assets-read-only-diagnostic-r2'
            and diagnostic['owner']=='scripts/unreal/megaplants-english-oak-partial-diagnostic-r2.py'
            and diagnostic['status']=='completed-read-only-original-partial-usd-asset-observation'
            and diagnostic['nativeProcessId']==20684 and diagnostic['partialProjectUnchanged'] is True
            and diagnostic['originalSavedR32ProjectUnchanged'] is True and diagnostic['startupAllowAssemblies']==0,
            'Measured preserved-partial diagnostic required')
    diagnostic_raw=read(check_pin(plan['actualPartDiagnosticProcessRaw']))
    diagnostic_terminal=read(check_pin(plan['actualPartDiagnosticProcessTerminal']))
    require(diagnostic_raw['pid']==20684 and diagnostic_raw['code']==0
            and diagnostic_terminal['sourcePinsUnchangedAfterNative'] is True,
            'Actual read-only part diagnostic process/source closure required')
    root_observed=[r for r in diagnostic['assets'] if r['name']=='SK_Tree_English_Oak_Forest_01_D']
    require(len(root_observed)==1 and root_observed[0]['class']=='/Script/Engine.SkeletalMesh'
            and root_observed[0]['assembly']['available'] is True, 'Measured actual skeletal root assembly required')
    parts=root_observed[0]['assembly']['value']['parts']
    require(len(parts)==11 and all(r['toTuple']['available'] is True and len(r['toTuple']['value'])==1
            and r['getObjectFromSoftPath']['available'] is True
            and r['toTuple']['value'][0]==r['getObjectFromSoftPath']['value']['path']
            and r['getObjectFromSoftPath']['value']['class']=='/Script/Engine.SkeletalMesh' for r in parts),
            'Actual single-string soft-path and skeletal native resolution must agree for all eleven parts')
    for row in plan['inputFiles']:check_pin(row)
    original=read(check_pin(plan['sourceExtraction']));inspection=read(check_pin(plan['usdInspection']))
    selected=validate_source(original,inspection)
    require(plan['selectedUsd']==selected['source'] and plan['stageRoot']==selected['rootPrims'][0],
            'Selected original USD/root differs')
    require(plan['treePlacement']=={'locationCm':[0,0,0],'rotationDegrees':[0,0,0],'scale':[1,1,1]}
            and plan['ground']=={'sizeCm':[4500,4500],'surfaceZCm':-2,'colorLinear':[.18,.18,.18],
                                 'roughness':.8,'specular':.25},'Authored pilot placement widened')
    require(plan['camera']['id']=='english-oak-original-D-close-r3' and plan['camera']['eyeCm']==[2000,-2800,700]
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
        if not(prepared and key in {'BreziTwin.uproject','Config/DefaultEngine.ini'}):
            require(sha(dest)==value['sha256'] and dest.stat().st_size==value['bytes'],'Probe original changed: '+key)
    if prepared:
        receipt=read(OUTPUT/'oak-usd-project-preparation-r3.json')
        require(receipt['schema']==SCHEMA and receipt['status']=='verified-own-usd-plugin-and-startup-assembly-only-stage-native-pending-r3'
                and receipt['selectedPlan']==pin(PLAN) and receipt['initialRootClone']==plan['initialRootClone']
                and receipt['nativeExecuted'] is False
                and receipt['descriptorBefore']==pin(BASE/'Project/BreziTwin/BreziTwin.uproject'),
                'Typed descriptor preparation with immutable source-before pin required')
        original=read(rows['BreziTwin.uproject']['source']);actual=read(PROJECT/'BreziTwin.uproject')
        intended=dict(original);intended['Plugins']=[*original['Plugins'],PLUGIN]
        require(actual==intended and receipt['descriptorAfter']==pin(PROJECT/'BreziTwin.uproject'),
                'Only appended Editor USDImporter descriptor delta allowed')
        require(receipt['startupConfigBefore']==pin(BASE/'Project/BreziTwin/Config/DefaultEngine.ini')
                and receipt['startupConfigAfter']==pin(PROJECT/'Config/DefaultEngine.ini')
                and (PROJECT/'Config/DefaultEngine.ini').read_text()==startup_config((BASE/'Project/BreziTwin/Config/DefaultEngine.ini').read_text()),
                'Only exact startup AllowAssemblies=1 config delta allowed')
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
    relative_prefix='Content/'+PREFIX.removeprefix('/Game/')+'/'
    require(added and all(k.startswith(relative_prefix) and k.endswith('.uasset') or
                         k=='Content/'+MAP.removeprefix('/Game/')+'.umap' for k in added),
            'New files escape isolated native namespace')
    require('Content/Brezi/Maps/Brezi.umap' in before and after['Content/Brezi/Maps/Brezi.umap']==before['Content/Brezi/Maps/Brezi.umap'],
            'Main saved architecture map changed')
    return {'changedOriginalFiles':sorted(changed),'newFiles':sorted(added),'originalMainMapUnchanged':True}
