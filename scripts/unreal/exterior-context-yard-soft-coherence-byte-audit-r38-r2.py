"""Root-usable CPU audit of CLOSED R38 bytes and stored native evidence.

No Unreal launch or new native actor/mesh/texture decode. Failed/running
processes reject before any success receipt can be written.
"""
import importlib.util
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-soft-coherence-byte-audit-r38-r2.py'
s=importlib.util.spec_from_file_location('r38_audit_final_native',ROOT/'scripts/unreal/exterior-context-yard-soft-coherence-native-r38-r2.py')
n=importlib.util.module_from_spec(s);s.loader.exec_module(n);g=n.g
require,read,pin,sha,digest=(getattr(g,k)for k in ('require','read','pin','sha','digest'))
NATIVE_SHA='e8bd757c0958f4245c4d2c2d7bbd577643b15150333ef5074047bb769f631998'
GUARD_SHA='531d6266cd099c717aaac942175ce3e60b4f6614eeaa652356ab0ab63cc1c94f'
PLAN_SHA='a7159a67452296998d3323011bd45095141c0e296907a276876b7f40012cf092'
PF_SHA='c8827357e8455dd030fa35c0613bd8da7c0ff83dbc0052a93016fb44f74b2ecf'
MONITOR_SHA='32dd2661ec78718eef9e5503a1c411b565f6542400778a7b13c67fa8c93ab820'
CONFIG_SHA='b431fc7fbabe8be6e920a3974e7b8c5da0db065c8c0ab3acaaa22c135665c61d'
STEM='soft-ground-native-r2'
AUDIT_FILE='root-native-success-byte-audit-r38b-r2.json'


def enum_token(value,owner,token):
    match=re.fullmatch(r'<([A-Za-z0-9_]+)\.([A-Za-z0-9_]+): (-?[0-9]+)>',value)
    require(match is not None and match[1]==owner and match[2].replace('_','').upper()==token.replace('_','').upper(),
        'Actual native enum policy token differs: '+str(value))


def validate_mask(report,bundle):
    row=report['maskTexture'];require(row['asset']==g.MASK_ASSET,'Exact new permission texture asset required')
    values=dict(row['values'])
    enums={'filter':('TextureFilter','TF_BILINEAR'),'mip_gen_settings':('TextureMipGenSettings','TMGS_NO_MIPMAPS'),
        'address_x':('TextureAddress','TA_CLAMP'),'address_y':('TextureAddress','TA_CLAMP'),
        'compression_settings':('TextureCompressionSettings','TC_GRAYSCALE'),'power_of_two_mode':('TexturePowerOfTwoSetting','NONE')}
    for key,(owner,token)in enums.items():enum_token(values.pop(key),owner,token)
    require(values=={'srgb':False,'resize_during_build_x':0,'resize_during_build_y':0,'lod_bias':0,
        'max_texture_size':0,'never_stream':True,'virtual_texture_streaming':False,'flip_green_channel':False,
        'do_scale_mips_for_alpha_coverage':False,'adjust_brightness':1.,'adjust_brightness_curve':1.,'adjust_vibrance':0.,
        'adjust_saturation':1.,'adjust_rgb_curve':1.,'adjust_hue':0.,'adjust_min_alpha':0.,'adjust_max_alpha':1.,'chroma_key_texture':False},
        'Actual mask resizing/compression/color policy differs')
    enum_token(row['sourceEncoding'],'TextureSourceEncoding','TSE_NONE')
    require(row['size']==[2048,2048]and row['downscale']=={'default':1.,'perPlatform':{}}
        and row['alphaCoverageThresholds']==[0.,0.,0.,0.],'Exact2048 unscaled no-coverage mask required')
    require(row['metadata']=={'BreziGeneratedBy':'scripts/unreal/exterior-context-yard-soft-coherence-materials-r38-r2.py',
        'BreziSourceSha256':g.PNG_SHA,'BreziTechnicalDataRole':'artist-generated-fixed-world-permission-field','BreziSourcePlanSha256':g.SOURCE_SHA},
        'Exact generated-data owner/source metadata required')
    g.validate_policy(report['samplingPolicy']);g.validate_native_graphs(bundle['graphs'],bundle['nativeGraphs'])
    require(set(report['materials'])=={'backdrop','substrate'}and report['newPackageAssets']==sorted([*g.ASSETS.values(),g.MASK_ASSET]),'Exactly two graphs plus one mask required')
    for role,asset in g.ASSETS.items():
        m=report['materials'][role];require(m['asset']==asset and m['graph']==bundle['nativeGraphs'][role]
            and m['graphSha256']==digest(m['graph'])and m['compileErrors']==[],'Actual compiled70/73 full graph differs')
        enum_token(m['aux']['samplerSources'][g.TAG+'fixed-world-yard-mask'],'SamplerSourceMode','SSM_FROM_TEXTURE_ASSET')
    require(report['compressionSourcePolicy']=={'source':'installed Texture.cpp TC_Grayscale with sRGB=false and source L8',
        'expectedFormat':'G8','expectedUncompressedByPrimarySource':True,'formatActuallyReadFromNativeTexture':False,
        'hiddenCompressionNoneGetterOrSetterUsed':False},'Primary G8 inference must remain separate from actual GPU format')
    require(all(report[k]is False for k in ('sourcePhotoPixelsEdited','nativeTexelsDecoded','nativeGpuPixelFormatVerified',
        'nativeGpuOutsideEquivalenceVerified','materialPackagesIndependentlyUnloaded','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted')),
        'Native property proof must not promote pixel/GPU/appearance acceptance')


def validate_raw(before,saved,witness):
    require(before==saved and len(before)==2325,'Every2325 original raw control must remain exact')
    total=0;seen=set()
    for path,row in saved.items():
        require(row['actor']in witness and(row['actor'],row['component'])not in seen,'Actual raw-control actor identity differs')
        cs=[c for c in witness[row['actor']]['components']if c['name']==row['component']]
        require(len(cs)==1 and cs[0]['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent'
            and cs[0]['instanceCount']==row['instances']and type(row['instances'])is int
            and re.fullmatch('[0-9a-f]{64}',row['rawMatrixBinary64Sha256'])
            and re.fullmatch('[0-9a-f]{64}',row['customDataSha256'])
            and row['transformSeedOrInstanceMutationApisCalled']is False,'Stored native raw component proof differs')
        total+=row['instances'];seen.add((row['actor'],row['component']))
    require(total==678197 and seen=={(actor,c['name'])for actor,a in witness.items()for c in a['components']if 'instanceCount'in c},
        'All678197 retained instance controls and exact complete component membership required')


def main():
    require(MONITOR_SHA is not None and CONFIG_SHA is not None,'Actual final root R2 launch pins are not bound yet')
    output=g.CANDIDATE;destination=output/AUDIT_FILE
    require(not destination.exists(),'Success audit is append-only; previous evidence immutable')
    require(sha(ROOT/n.OWNER)==NATIVE_SHA and sha(ROOT/g.OWNER)==GUARD_SHA,'Consumed final native/guard bytes differ')
    process_path=output/(STEM+'-process.json');raw_path=output/(STEM+'.log.json');report_path=output/n.REPORT
    process,raw,report=read(process_path),read(raw_path),read(report_path)
    require(raw['code']==0 and raw['signal']is None and type(raw['pid'])is int and raw['pid']>0 and raw['endedAt'],
        'Only an actually CLOSED successful native process can be audited')
    require(report['schema']==g.SCHEMA and report['schemaVersion']==2 and report['owner']==n.OWNER
        and report['status']==n.STATUS and report['nativeApplied']is True and report['savedMapUnloadedReloaded']is True
        and report['sourceInputsUnchanged']is True and report['nativeProcessId']==raw['pid']and report['repairSchema']==g.REPAIR_SCHEMA,'Actual saved typed R38 report required')
    require(process['processFile']==str(raw_path)and process['processFileSha256']==sha(raw_path)
        and process['reportSha256']==sha(report_path)and process['sourcePinsUnchangedAfterNative']is True
        and process['controllerSha256BeforeNative']==process['controllerSha256AfterNative']==MONITOR_SHA
        and sha(process['controller'])==MONITOR_SHA and sha(process['logFile'])==process['logSha256'],'Actual process/report/log/monitor pins differ')
    root_pins=process['sourcePinsBeforeNative'];configs=[p for p,v in root_pins.items()if v==CONFIG_SHA]
    require(len(configs)==1,'Exactly one root launch config pin required');config=read(configs[0])
    require(config['candidate']==str(output)and config['helper']==pin(ROOT/n.OWNER)and config['report']==n.REPORT and config['stem']==STEM,
        'Actual root launch config differs from scoped owner')
    require(all(sha(p)==v for p,v in root_pins.items()),'Terminal root consumed source bytes changed')
    require(sha(g.PLAN)==PLAN_SHA,'Exact final source plan required');plan=read(g.PLAN)
    pf_path=g.STUDY/'source-preflight/source-preflight.json';require(sha(pf_path)==PF_SHA,'Exact preflight required');pf=read(pf_path)
    require(report['selectedPlan']==pin(g.PLAN)and report['sourcePreflight']==pin(pf_path)and report['inputFiles']==pf['inputFiles']
        and len(pf['inputFiles'])==1039 and set(pf['inputFiles'])<=set(root_pins)
        and all(root_pins[p]==v for p,v in pf['inputFiles'].items()),'All1039 source receipts must bind actual terminal closure')
    bundle=g.load_contract();g.validate_clone(bundle,True);h=n.helpers(bundle)
    require(report['binding']==plan['binding']==bundle['binding'],'Actual report/source/selected base binding differs')
    content,delta=n.project_state(bundle,h,True)
    require(len(content)==4103 and read(g.checked(report['afterContentInventory']))==content and report['assetDelta']==delta,
        'Current4103 Content/map-only exact3-package inventory differs')
    before=read(g.checked(report['beforeActorWitness']));expected=read(g.checked(report['expectedActorWitness']));saved=read(g.checked(report['savedActorWitness']))
    require(before==bundle['base']['before']and expected==bundle['expected']==saved and len(saved)==5364
        and digest(before)==report['beforeActorWitnessSha256']and digest(expected)==report['expectedActorWitnessSha256']==report['savedActorWitnessSha256'],
        'Full saved5364 independently reconstructed two-slot counterfactual differs')
    raw_before=read(g.checked(report['rawInstanceControlsBefore']));raw_saved=read(g.checked(report['rawInstanceControlsSaved']))
    validate_raw(raw_before,raw_saved,saved)
    old_before=read(g.checked(report['originalMaterialWitnessBefore']));old_saved=read(g.checked(report['originalMaterialWitnessSaved']));records=n.graph_records(bundle)
    require(old_before==old_saved and set(old_saved)==set(records)and len(old_saved)==64,'All64 original graphs/aux/usage differ')
    for asset,row in old_saved.items():require(row['graph']==records[asset]['graph']and row['graphSha256']==digest(row['graph'])
        and row['reader']==records[asset]['route'],'Original complete source graph/dispatch differs')
    diagnostics=report['materialGraphDiagnosticFiles']
    require(set(diagnostics)=={'before','saved'}and all(len(v)==64 for v in diagnostics.values()),'Both64 full diagnostic records required')
    for phase,rows in diagnostics.items():
        actual={}
        for row in rows:
            value=read(g.checked(row));require(value['asset']not in actual,'Duplicate native graph diagnostic');actual[value['asset']]=value
        require(actual==old_saved,'Complete observed graph diagnostics differ from actual stored witness')
    tex_before=read(g.checked(report['originalTextureWitnessBefore']));tex_saved=read(g.checked(report['originalTextureWitnessSaved']))
    require(tex_before==tex_saved and set(tex_saved)==set(bundle['base']['report']['materialReadback']['textureAssets'])and len(tex_saved)==96,
        'All96 original native texture settings and metadata differ')
    built=read(g.checked(report['newMaterialReport']));require(built==report['newMaterials'],'New material sidecar/report differs');validate_mask(built,bundle)
    require(built['originalGraphWitness']=={p:old_saved[p]['graph']for p in (bundle['originalBackdropAsset'],bundle['originalSubstrateAsset'])}
        and built['originalAuxWitness']=={p:old_saved[p]['aux']for p in (bundle['originalBackdropAsset'],bundle['originalSubstrateAsset'])}
        and built['sharedTextureWitness']==tex_saved,'Builder shared/original graph and auxiliary witnesses differ')
    require(report['actualCounts']=={'savedActors':5364,'fullHismComponents':2325,'fullHismInstances':678197,'scopedMaterialGraphs':66,
        'scopedTextureObjects':97,'contentFiles':4103,'protectedFiles':132,'newPackages':3},'Actual unchanged scene plus2/1 census differs')
    require(report['newPackages']==built['newPackageAssets']and report['allOriginalRawMatricesMainSeedsCustomDataExact']is True
        and report['original64MaterialGraphsAndAuxExact']is True and report['original96TextureSettingsAndPackagesExact']is True
        and report['nativeMaskPropertyPolicyVerified']is True,'All stored native preservation gates required')
    require(all(report[k]is False for k in ('nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified',
        'activeOutputPromoted','nativeGpuOutsideEquivalenceVerified','nativeGpuPixelFormatVerified','nativeTexelsDecoded',
        'freshNativeGeometryAttributeReadback','nativeNormalTangentReadbackAvailable','originalGeometryAndRootMutationApisCalled','sourcePhotoPixelsEdited')),
        'Stored property/source audit cannot promote fresh geometry/GPU/appearance acceptance')
    result={'schema':'brezi-root-r38-current-byte-and-stored-native-evidence-audit','schemaVersion':2,'owner':OWNER,
        'status':'verified-current-r38-bytes-and-stored-native-two-slot-counterfactual','repairSchema':g.REPAIR_SCHEMA,'repairEvidence':bundle['repairEvidence'],'nativeReport':pin(report_path),'nativeProcess':pin(process_path),
        'rawNativeProcess':pin(raw_path),'nativeProcessId':raw['pid'],'auditController':pin(ROOT/OWNER),'selectedPlan':pin(g.PLAN),
        'sourcePreflight':pin(pf_path),'projectClone':bundle['base']['clone'],'baseNativeReport':bundle['base']['reportPin'],
        'selectedRootImageDecision':bundle['base']['selection'],'currentContentFiles':4103,'protectedFiles':132,'currentProjectFiles':4235,
        'unchangedOriginalBaseContentFiles':4100,'unchangedOriginalBaseProtectedFiles':132,'newPackages':3,'assetDelta':delta,
        'sourceReceiptPins':1039,'terminalRootSourcePins':len(root_pins),'allSourceAndTerminalPinsCurrentExact':True,
        'fullStoredCounterfactualIndependentlyReconstructed':True,'savedActorWitnessSha256':digest(saved),
        'all2325RawControls678197MembersBeforeAndSavedExact':True,'all64OriginalGraphsAuxUsage96TexturesExact':True,
        'actualCompiled70And73GraphsNativeMaskPropertyPolicyValidated':True,'freshNativeActorOrAttributeDecodeExecuted':False,
        'nativeTexelsDecoded':False,'nativeGpuOutsideEquivalenceVerified':False,'nativeGpuPixelFormatVerified':False,
        'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,
        'activeOutputPromoted':False}
    g.write(destination,result);print(json.dumps({'audit':pin(destination),'status':result['status'],'nativeProcessId':raw['pid']}))


if __name__=='__main__':main()
