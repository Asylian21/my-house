"""CPU-only closed R38R2 consumer; no Unreal or historical source regeneration.

Reconstructs the two-slot counterfactual and binds full saved material/raw
receipts. G8 is an installed-source inference, not a native GPU format census.
"""
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-soft-coherence-editor-check-r29-r3.py'
HELPER = 'scripts/unreal/exterior-context-yard-soft-coherence-native-r38-r2.py'
HELPER_SHA = 'e8bd757c0958f4245c4d2c2d7bbd577643b15150333ef5074047bb769f631998'
GUARD_SHA = '531d6266cd099c717aaac942175ce3e60b4f6614eeaa652356ab0ab63cc1c94f'
AUDIT_HELPER = 'scripts/unreal/exterior-context-yard-soft-coherence-byte-audit-r38-r2.py'
AUDIT_HELPER_SHA = '2739cebe1d5d9d6778290d445c7172d879ac75b7dfe38105477cc9a636f69b2d'
REPORT = ROOT/'output/unreal/exterior-20261002-r38b/soft-ground-native-report-r2.json'
REPORT_SHA = '077e36066dc49f2c3fa379893c39fc5659e8261385030d86266316e1bde9f2b9'
AUDIT = REPORT.parent/'root-native-success-byte-audit-r38b-r2.json'
AUDIT_SHA = 'a30063dc99bd3fa3fcd7d202aa77209b74f36c06bde77a47fba1c071564c5edb'
PLAN_SHA = 'a7159a67452296998d3323011bd45095141c0e296907a276876b7f40012cf092'
PF_SHA = 'c8827357e8455dd030fa35c0613bd8da7c0ff83dbc0052a93016fb44f74b2ecf'
BASE_SHA = 'f589c0d813ccfc35eba928a91a4545e03b159622fffa7ae2ba247545053c4532'
MONITOR_SHA = '32dd2661ec78718eef9e5503a1c411b565f6542400778a7b13c67fa8c93ab820'
NATIVE_PID, SOURCE_PINS, TERMINAL_PINS = 72504, 1039, 1048


def module(name, p):
    spec = importlib.util.spec_from_file_location(name, p)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


n = module('r29r3_closed_native', ROOT/HELPER)
g = n.g
require, read, pin, sha, digest = (getattr(g, k) for k in ('require', 'read', 'pin', 'sha', 'digest'))
a = module('r29r3_closed_audit_validators', ROOT/AUDIT_HELPER)


def side(row):
    return read(g.checked(row))


def exact(left, right, message):
    require(left == right and digest(left) == digest(right), message)


def header(r, plan, pf):
    require(r['schema'] == g.SCHEMA and r['schemaVersion'] == 2 and r['owner'] == HELPER
            and r['repairSchema'] == g.REPAIR_SCHEMA and r['status'] == n.STATUS
            and r['nativeProcessId'] == NATIVE_PID and r['output'] == str(REPORT.parent)
            and r['project'] == str(REPORT.parent/'Project/BreziTwin'), 'Only actual saved R38b R2 accepted')
    require(plan['schema'] == g.SCHEMA and plan['schemaVersion'] == 2 and plan['owner'] == HELPER
            and plan['repairSchema'] == g.REPAIR_SCHEMA and plan['status'] == 'image-selected-soft-ground-source-validated-native-pending'
            and pf['schema'] == g.SCHEMA and pf['schemaVersion'] == 2 and pf['owner'] == HELPER
            and pf['status'] == 'image-selected-soft-ground-source-preflight-validated-native-pending'
            and pf['repairSchema'] == g.REPAIR_SCHEMA and pf['nativeExecuted'] is False
            and pf['cpuTests'] == plan['cpuTests'] and pf['cpuTests']['exitCode'] == 0
            and pf['cpuTests']['expectedCases'] == 20, 'Exact consumed source plan/preflight required')
    for key in ('binding', 'inputFiles', 'moduleOrderWitness'):
        exact(r[key], pf[key], 'Executed source/preflight field differs: '+key)
    require(r['binding'] == plan['binding'] and r['repairEvidence'] == plan['repairEvidence']
            and r['selectedPlan'] == pf['selectedPlan'] and r['inputFiles'][str(ROOT/HELPER)] == HELPER_SHA
            and len(r['inputFiles']) == SOURCE_PINS, 'Typed repair or actual source closure differs')
    require(r['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
            and r['setbacksMm'] == {'street': 3000, 'east': 3000}, 'C/B/B and both 3000mm setbacks must remain exact')
    true = ('nativeApplied', 'savedMapUnloadedReloaded', 'sourceInputsUnchanged',
            'allOriginalRawMatricesMainSeedsCustomDataExact', 'nativeMaskPropertyPolicyVerified',
            'original64MaterialGraphsAndAuxExact', 'original96TextureSettingsAndPackagesExact')
    false = ('nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified',
             'packageVerified', 'activeOutputPromoted', 'nativeGpuOutsideEquivalenceVerified', 'nativeGpuPixelFormatVerified',
             'nativeTexelsDecoded', 'freshNativeGeometryAttributeReadback', 'nativeNormalTangentReadbackAvailable',
             'originalGeometryAndRootMutationApisCalled', 'sourcePhotoPixelsEdited', 'additionalSeedRangesPreservationClaimed')
    require(all(r[k] is True for k in true) and all(r[k] is False for k in false), 'Executed scope/evidence limits differ')
    require(r['newActors'] == r['newMeshes'] == 0 and r['newPackages'] == sorted([*g.ASSETS.values(), g.MASK_ASSET]),
            'Only two materials and one permission field are new')
    require(r['actualCounts'] == {'savedActors': 5364, 'fullHismComponents': 2325, 'fullHismInstances': 678197,
            'scopedMaterialGraphs': 66, 'scopedTextureObjects': 97, 'contentFiles': 4103, 'protectedFiles': 132, 'newPackages': 3},
            'Actual full census differs')


def terminal_and_audit(r):
    terminal_path = REPORT.parent/'soft-ground-native-r2-process.json'
    t = read(terminal_path)
    raw_path = REPORT.parent/'soft-ground-native-r2.log.json'
    raw = read(raw_path)
    require(t['processFile'] == str(raw_path) and t['processFileSha256'] == sha(raw_path)
            and t['reportSha256'] == REPORT_SHA and raw['pid'] == NATIVE_PID and raw['code'] == 0
            and raw['signal'] is None and raw['endedAt'] and t['sourcePinsUnchangedAfterNative'] is True
            and len(t['sourcePinsBeforeNative']) == TERMINAL_PINS
            and all(t['sourcePinsBeforeNative'].get(p) == v for p, v in r['inputFiles'].items()), 'Actual native process0/source closure required')
    require(raw['command'] == '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd'
            and raw['args'][0] == str(REPORT.parent/'Project/BreziTwin/BreziTwin.uproject')
            and all(v in raw['args'] for v in ('-nullrhi', '-run=pythonscript', '-script='+str(ROOT/HELPER))),
            'Actual own native command differs')
    require(t['controllerSha256BeforeNative'] == t['controllerSha256AfterNative'] == MONITOR_SHA
            and sha(t['controller']) == MONITOR_SHA and t['logFile'] == str(REPORT.parent/'soft-ground-native-r2.log')
            and sha(t['logFile']) == t['logSha256'], 'Actual monitor/log closure differs')
    require(sha(AUDIT) == AUDIT_SHA, 'Actual root byte audit changed')
    audit = read(AUDIT)
    require(audit['schema'] == 'brezi-root-r38-current-byte-and-stored-native-evidence-audit'
            and audit['schemaVersion'] == 2 and audit['status'] == 'verified-current-r38-bytes-and-stored-native-two-slot-counterfactual'
            and audit['nativeReport'] == pin(REPORT) and audit['nativeProcess'] == pin(terminal_path)
            and audit['rawNativeProcess'] == pin(raw_path) and audit['nativeProcessId'] == NATIVE_PID
            and audit['terminalRootSourcePins'] == TERMINAL_PINS and audit['sourceReceiptPins'] == SOURCE_PINS
            and audit['currentProjectFiles'] == 4235 and audit['currentContentFiles'] == 4103
            and audit['protectedFiles'] == 132 and audit['newPackages'] == 3
            and audit['assetDelta'] == r['assetDelta'] and audit['savedActorWitnessSha256'] == r['savedActorWitnessSha256'],
            'Exact closed root current-byte receipt required')
    for k in ('allSourceAndTerminalPinsCurrentExact', 'fullStoredCounterfactualIndependentlyReconstructed',
              'all2325RawControls678197MembersBeforeAndSavedExact', 'all64OriginalGraphsAuxUsage96TexturesExact',
              'actualCompiled70And73GraphsNativeMaskPropertyPolicyValidated'):
        require(audit[k] is True, 'Actual byte-audit stored proof differs: '+k)
    require(audit['freshNativeActorOrAttributeDecodeExecuted'] is False, 'CPU audit cannot claim a fresh native decode')
    return audit


def counterfactual(r, plan, base):
    before, declared, saved = (side(r[k]) for k in ('beforeActorWitness', 'expectedActorWitness', 'savedActorWitness'))
    exact(before, side(base['savedActorWitness']), 'Before must be exact selected full R37b saved witness')
    require(len(before) == 5364 and base['newActorMapping'][g.DONOR668] == g.DONOR668
            and set(plan['targets']) == {'backdrop', 'substrate'}, 'Only actual 197/668 scope required')
    for role, actor in (('backdrop', g.ACTOR197), ('substrate', g.DONOR668)):
        target = plan['targets'][role]
        c = [c for c in before[actor]['components'] if c['name'] == 'StaticMeshComponent0']
        require(len(c) == 1 and target == {'actor': actor, 'component': 'StaticMeshComponent0',
                'originalMesh': c[0]['mesh'], 'originalMaterial': c[0]['materials'][0]}, 'Exact source target differs')
    expected = g.d.counterfactual_two_slots(before, plan['targets'])
    exact(expected, declared, 'Declared full counterfactual differs')
    exact(expected, saved, 'Reloaded full counterfactual differs')
    require(digest(before) == r['beforeActorWitnessSha256']
            and digest(saved) == r['expectedActorWitnessSha256'] == r['savedActorWitnessSha256'], 'Full canonical actor hashes differ')
    return before, saved


def raw_controls(r, saved):
    before, after = side(r['rawInstanceControlsBefore']), side(r['rawInstanceControlsSaved'])
    exact(before, after, 'All raw native matrix/mainseed/custom-data controls changed')
    a.validate_raw(before, after, saved)
    for path, row in after.items():
        require(path == row['actor']+'.'+row['component'] and type(row['mainRandomSeed']) is int
                and type(row['numCustomDataFloats']) is int and row['numCustomDataFloats'] >= 0,
                'Raw component identity or mainseed/custom-data type differs')
        require(row['additionalRandomSeeds'] == {'available': False, 'rangePreservationClaimed': False},
                'Additional seed ranges remain unavailable; no invented preservation claim')


def materials(r, plan, base, source):
    bundle = {'base': {'report': base}, 'plan': source,
              'graphs': side(source['materialGraphs']), 'nativeGraphs': side(plan['nativeMaterialGraphs'])}
    records = n.graph_records(bundle)  # complete historical shapes; no UObject calls or source generation
    before, saved = side(r['originalMaterialWitnessBefore']), side(r['originalMaterialWitnessSaved'])
    exact(before, saved, 'All64 full graphs/aux/usage must remain exact')
    require(set(saved) == set(records) and len(saved) == 64, 'Exact full64 source material set required')
    require({k: sum(v['reader'] == k for v in saved.values()) for k in ('basic', 'neighbor', 'tree')}
            == {'basic': 52, 'neighbor': 9, 'tree': 3}, 'Exact specialized 52/9/3 snapshot dispatch required')
    for asset, row in saved.items():
        exact(row['graph'], records[asset]['graph'], 'Full original source graph changed: '+asset)
        require(row['asset'] == asset and row['reader'] == records[asset]['route']
                and row['graphSha256'] == digest(row['graph'])
                and set(row['aux']) == {'samplerSources', 'worldPositionShaderOffsets'}
                and set(row['usage']) == {'instancedStaticMeshes', 'nanite'}
                and all(type(v) is bool for v in row['usage'].values()), 'Original graph/schema/usage differs')
    require(set(r['materialGraphDiagnosticFiles']) == {'before', 'saved'}, 'Both full graph phases required')
    for phase in ('before', 'saved'):
        rows = r['materialGraphDiagnosticFiles'][phase]
        require(len(rows) == 64, 'Exactly64 complete phase diagnostics required')
        observed = {}
        for index, p in enumerate(rows):
            require(Path(p['path']) == REPORT.parent/'soft-ground-checkpoint'/('graphs-'+phase)/('graph-'+str(index).zfill(3)+'.json'),
                    'Exact native graph diagnostic path/order required')
            d = side(p)
            require(d['asset'] not in observed, 'Duplicate graph diagnostic')
            observed[d['asset']] = d
        exact(observed, saved, 'Complete phase diagnostic graph/aux/usage differs')
    tex_before, tex_saved = side(r['originalTextureWitnessBefore']), side(r['originalTextureWitnessSaved'])
    exact(tex_before, tex_saved, 'All96 native texture settings/metadata differ')
    require(set(tex_saved) == set(base['materialReadback']['textureAssets']) and len(tex_saved) == 96,
            'Exact original96 Texture2D assets required')
    for asset, row in tex_saved.items():
        require(row['asset'] == asset and len(row['values']) == 24 and 'compression_none' not in row['values'],
                'Visible24-field original texture reader required')
    built = side(r['newMaterialReport'])
    exact(built, r['newMaterials'], 'New material sidecar/report differs')
    require(built['schema'] == 'brezi-r38-soft-ground-two-material-one-mask-builder-r2'
            and built['owner'] == 'scripts/unreal/exterior-context-yard-soft-coherence-materials-r38-r2.py'
            and built['sourceStudy'] == r['sourceStudy'], 'Exact own native R2 material route required')
    a.validate_mask(built, bundle)
    mask_values = built['maskTexture']['values']
    expected_enums = {'filter': '<TextureFilter.TF_BILINEAR: 1>',
        'mip_gen_settings': '<TextureMipGenSettings.TMGS_NO_MIPMAPS: 13>',
        'address_x': '<TextureAddress.TA_CLAMP: 1>', 'address_y': '<TextureAddress.TA_CLAMP: 1>',
        'compression_settings': '<TextureCompressionSettings.TC_GRAYSCALE: 3>',
        'power_of_two_mode': '<TexturePowerOfTwoSetting.NONE: 0>'}
    require(all(mask_values[k] == v for k, v in expected_enums.items())
            and built['maskTexture']['sourceEncoding'] == '<TextureSourceEncoding.TSE_NONE: 0>',
            'Exact actually reflected grayscale/filter/encoding enum values required')
    exact(built['nativeGraphAdaptation'], plan['nativeGraphAdaptation'], 'Owned native graph adaptation changed')
    old_assets = [plan['targets'][k]['originalMaterial'] for k in ('backdrop', 'substrate')]
    exact(built['originalGraphWitness'], {p: saved[p]['graph'] for p in old_assets}, 'Builder originals differ')
    exact(built['originalAuxWitness'], {p: saved[p]['aux'] for p in old_assets}, 'Builder old auxiliary routes differ')
    exact(built['sharedTextureWitness'], tex_saved, 'Builder all96 shared texture policies differ')
    old = saved[old_assets[0]]
    expected_aux = {'samplerSources': {**old['aux']['samplerSources'], g.TAG+'fixed-world-yard-mask': '<SamplerSourceMode.SSM_FROM_TEXTURE_ASSET: 0>'},
                    'worldPositionShaderOffsets': old['aux']['worldPositionShaderOffsets']}
    for role in ('backdrop', 'substrate'):
        row = built['materials'][role]
        exact(row['aux'], expected_aux, 'Full original sample/world-position auxiliary route changed')
        require(len(row['graph']['nodes']) == (70 if role == 'backdrop' else 73)
                and row['metadata'] == {'BreziGeneratedBy': built['owner'], 'BreziSourcePlanSha256': g.SOURCE_SHA,
                    'BreziSourceOriginalMaterial': old_assets[0], 'BreziR38Role': role}, 'Owned material graph size/metadata differs')
    exact(built['reflectionPreflight'], {'requiredPropertiesReadableBeforeImport': True, 'textureFieldCount': 24,
          'hiddenCompressionNonePropertyAccessed': False, 'setterAvailabilityActuallyMeasured': False}, 'Reflection evidence limit differs')


def content(r, base):
    before, after = side(base['afterContentInventory']), side(r['afterContentInventory'])
    require(len(before) == 4100 and len(after) == 4103 and len(side(r['protectedProjectProof'])) == 132,
            'Exact current4103 plus132 protected file census required')
    exact(g.validate_content_delta(before, after), r['assetDelta'], 'Only map and exact3 new packages allowed')
    require(r['baseContentInventory'] == base['afterContentInventory']
            and r['protectedProjectProof'] == base['protectedProjectProof'], 'Original protected/source inventories differ')


def validate_saved(r, plan, pf, base, source):
    header(r, plan, pf)
    _, saved = counterfactual(r, plan, base)
    raw_controls(r, saved)
    materials(r, plan, base, source)
    content(r, base)
    return {'mode': 'verified-saved-r38r2-two-slot-soft-ground-editor-source', 'nativeProcessId': NATIVE_PID,
            'originalActors': 5364, 'savedActors': 5364, 'fullHismComponents': 2325, 'fullHismInstances': 678197,
            'wholeActorCounterfactualValidated': True, 'changedOriginalMaterialSlots': 2, 'newActors': 0, 'newMeshes': 0,
            'unchangedRawInstanceComponents': 2325, 'unchangedRawInstanceMembers': 678197,
            'completeOriginalMaterialGraphDiagnostics': 128, 'originalMaterialGraphs': 64, 'originalTextureObjects': 96,
            'newMaterialGraphs': 2, 'newTextureObjects': 1, 'scopedMaterialGraphs': 66, 'scopedTextureObjects': 97,
            'contentFiles': 4103, 'protectedFiles': 132, 'newPackages': 3,
            'freshNativeActorOrGeometryDecodePerformedByCpuChecker': False, 'nativeTexelsDecoded': False,
            'expectedG8FormatByPrimarySourceOnly': True, 'nativeGpuPixelFormatVerified': False,
            'nativeGpuOutsideEquivalenceVerified': False, 'nativeNormalTangentReadbackAvailable': False,
            'AdditionalRandomSeedRangesPreservationClaimed': False, 'sourceFieldRasterRegeneratedByChecker': False,
            'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False,
            'shippingVerified': False, 'packageVerified': False, 'activeOutputPromoted': False}


def main():
    require(len(sys.argv) == 2 and Path(sys.argv[1]).resolve() == REPORT, 'Only the exact actual saved R38b report CLI accepted')
    require(sha(REPORT) == REPORT_SHA and sha(ROOT/HELPER) == HELPER_SHA
            and sha(ROOT/g.OWNER) == GUARD_SHA and sha(ROOT/AUDIT_HELPER) == AUDIT_HELPER_SHA,
            'Exact actual report and frozen native/guard/audit validators required')
    r = read(REPORT)
    require(r['selectedPlan']['sha256'] == PLAN_SHA and r['sourcePreflight']['sha256'] == PF_SHA
            and r['baseNativeReport']['sha256'] == BASE_SHA, 'Selected immutable plan/preflight/base differ')
    plan, pf, base, source = (side(r[k]) for k in ('selectedPlan', 'sourcePreflight', 'baseNativeReport', 'sourceStudy'))
    terminal_and_audit(r)
    print(json.dumps(validate_saved(r, plan, pf, base, source), sort_keys=True))


if __name__ == '__main__':
    main()
