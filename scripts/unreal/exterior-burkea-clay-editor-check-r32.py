"""Saved R46 receipt consumer, bound to actual native0 and root byte closure.

No Unreal import, historical producer/checker, pristine-clone map assertion,
or fresh UObject decode. Only recorded source and saved sidecars are consumed.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
import struct
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-burkea-clay-editor-check-r32.py'
GUARD = ROOT/'scripts/unreal/exterior-burkea-clay-guards-r46.py'
GUARD_SHA = 'ae56551b27570d67096cf2e6de619c335d121cf91983c29d76eb8afd3a823804'
NATIVE = ROOT/'scripts/unreal/exterior-burkea-clay-native-r46.py'
NATIVE_SHA = '5f22c171d838cea0edc6e4f5d57efd9a8e8aa1dfa0d42ace0fc564495b49a7fe'
PLAN = ROOT/'output/unreal/exterior-burkea-clay-20261002-r46-native-study/combined-material-native-plan.json'
PLAN_SHA = '75ecc7256fab9c031b00e5c9f36cce22d9ba7bdb1616d1b1ca230b07992a5929'
PREFLIGHT = PLAN.parent/'source-preflight/source-preflight.json'
PREFLIGHT_SHA = 'f00ae16b2edb3d65d0636675602630a0a1ab36db2dc3b6cef435694fa353e6c1'
REPORT = ROOT/'output/unreal/exterior-20261002-r46a/combined-material-native-report-r46.json'
SOURCE_COUNT = 5657
# Root session23363 and current-byte audit5804 both fully closed0.
ACTUAL = {'reportSha': '0d73546f2ae59f89376a2676ff5839d1be0a8344a986d586db32ccbe2623dced',
          'nativeProcessId': 65818,
          'process': {'path': str(REPORT.parent/'combined-material-native-r46-process.json'),
                      'sha256': 'b2d7c972f8d4f3e64c7e20a9eaf45be29a26b5ba8f163f000483e9db60f42865', 'bytes': 1269468},
          'rawProcess': {'path': str(REPORT.parent/'combined-material-native-r46.log.json'),
                         'sha256': '59b0a1abf3b806cb7351256908165194afd99f434ff6b70809d0797f9256bf2f', 'bytes': 647},
          'rootByteAudit': {'path': str(REPORT.parent/'root-native-success-byte-audit-r46a-r1.json'),
                           'sha256': '4b816e8b0b41d696cbf6a37e826c17124e460a7af1e7d5505aa9c2bbbca392cf', 'bytes': 4463},
          'monitorSha': '883c768f29c117b368110a4e2fe853290117b7f023824b64c6a63273a1646c65',
          'terminalSourceCount': 5664}
TRUE_FLAGS = ('nativeApplied', 'savedMapUnloadedReloaded', 'sourceInputsUnchanged',
              'wholeActorCounterfactualValidated', 'all5371ActorFieldsExceptFiveDeclaredSlotsExact',
              'all2329RawControlsExact', 'all72OriginalGraphAuxObservedUsageExact',
              'all114OriginalVisible24TexturePoliciesAndSelectedMetadataExact')
FALSE_FLAGS = ('oldActorGeometryRootCollisionNavOrMeshDefaultSettersCalled',
               'oldMaterialOrTextureSettersCalled', 'nativeAppearanceAccepted',
               'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified',
               'activeOutputPromoted', 'physicalLeafOrRoofOpticsAccepted',
               'nativeNormalTangentNumericReadbackPerformed', 'sourcePhotoPixelsEdited',
               'materialPackagesIndependentlyUnloaded', 'materialCompileDiagnosticsExhaustivelyRead',
               'additionalSeedRangesPreservationClaimed', 'cloudPhaseOrDynamicExposureLocked')


def require(ok, message):
    if not ok: raise RuntimeError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path): return json.loads(Path(path).read_bytes())
def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()
def pin(path):
    p = Path(path).resolve();return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}
def checked(row):
    require(type(row) is dict and set(row) == {'path', 'sha256', 'bytes'}, 'Exact immutable pin required')
    p = Path(row['path'])
    require(p.is_absolute() and p.resolve() == p and not p.is_symlink() and pin(p) == row,
            'Source or saved sidecar changed: '+str(p));return p
def module(name, path, expected):
    require(sha(path) == expected, 'Frozen source kernel changed: '+str(path))
    s = importlib.util.spec_from_file_location(name, path);m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m);return m
def exact(a, b, message):
    if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)) and not isinstance(b, bool):
        require(math.isfinite(a) and math.isfinite(b) and struct.pack('<d', float(a)) == struct.pack('<d', float(b)), message)
    elif type(a) is dict and type(b) is dict:
        require(set(a) == set(b), message)
        for key in a: exact(a[key], b[key], message)
    elif type(a) is list and type(b) is list:
        require(len(a) == len(b), message)
        for x, y in zip(a, b): exact(x, y, message)
    else: require(type(a) is type(b) and a == b, message)


def actual_binding_required():
    require(all(v is not None for v in ACTUAL.values()), 'R32 awaits closed actual R46 success/current-byte bindings')
    require(type(ACTUAL['nativeProcessId']) is int and ACTUAL['nativeProcessId'] > 0
            and ACTUAL['terminalSourceCount'] >= SOURCE_COUNT, 'Actual process/terminal census required')


def saved_bundle(g):
    # This observer reads authenticated records only. Do not call pre-save
    # validate_clone()/validate_plan() or any historical saved consumer.
    p = g.observer();bundle = {'source': p.load_sources(), 'base': p.load_observed_base(),
                              'binding': g.expected_binding()}
    g.require_native_binding(bundle['binding']);g.validate_clone_header(bundle)
    return bundle


def report_header(r, plan, pf, bundle, g):
    actual_binding_required()
    require(r['schema'] == g.SCHEMA and r['schemaVersion'] == 1 and r['owner'] == g.NATIVE_OWNER
            and r['status'] == 'verified-saved-five-slot-burkea-and-clay-roof-material-pilot'
            and r['nativeProcessId'] == ACTUAL['nativeProcessId'] and r['project'] == str(g.PROJECT),
            'Only exact saved R46 family accepted')
    for key in TRUE_FLAGS: require(r[key] is True, 'Native saved proof missing: '+key)
    for key in FALSE_FLAGS: require(r[key] is False, 'Evidence or mutation scope changed: '+key)
    require(r['combinedCaptureCannotIsolateLeafTransmissionFromRoofIndirectLighting'] is True,
            'Combined capture causal limit must remain explicit')
    require(r['activeDesign'] == 'C/B/B' and r['setbacksMm'] == [3000, 3000], 'Design changed')
    require(plan['schema'] == pf['schema'] == g.SCHEMA and plan['schemaVersion'] == pf['schemaVersion'] == 1
            and plan['owner'] == 'scripts/unreal/exterior-burkea-clay-native-study-r46.py'
            and plan['nativeOwner'] == pf['owner'] == g.NATIVE_OWNER
            and plan['status'] == 'selected-five-slot-material-source-ready-native-pending'
            and pf['status'] == 'five-slot-material-source-preflight-validated-native-pending', 'Typed frozen source contract changed')
    exact(r['binding'], bundle['binding'], 'Exact selected source binding changed')
    exact(plan['binding'], r['binding'], 'Source plan binding changed');exact(pf['binding'], r['binding'], 'PF binding changed')
    require(r['selectedPlan'] == pf['selectedPlan'] == pin(PLAN) and r['sourcePreflight'] == pin(PREFLIGHT)
            and r['inputFiles'] == pf['inputFiles'] == {**plan['inputFiles'], str(PLAN): PLAN_SHA}
            and len(r['inputFiles']) == SOURCE_COUNT, 'Consumed source and terminal closure are distinct')
    require(r['actualCounts'] == plan['expectedCounts'] == pf['expectedCounts'] == g.COUNTS
            and r['newPackages'] == plan['expectedNewPackages'] == g.expected_packages(bundle['source']), 'Exact five-package budget changed')
    require(pf['tests']['exitCode'] == 0 and pf['tests']['testCount'] == 10
            and pf['tests']['nativeApisActuallyExercised'] is False
            and plan['nativeExecuted'] is False and plan['gpuExecuted'] is False
            and pf['nativeExecuted'] is False and pf['gpuExecuted'] is False
            and r['moduleOrderWitness'] == pf['moduleOrderWitness'], 'Once-executed source preflight required')
    checked(pf['tests']['log'])
    require(r['sourceProposals'] == plan['sourceProposals'] == {k:v['proposalPin'] for k,v in bundle['source'].items()},
            'Frozen leaf and roof source identities changed')
    for key, expected in [('baseNativeReport', bundle['base']['reportPin']),
                          ('baseNativeProcess', bundle['base']['processPin']),
                          ('baseCurrentByteAudit', bundle['base']['auditPin']),
                          ('rootImageDecision', r['binding']['rootImageDecision']),
                          ('projectClone', r['binding']['projectClone'])]:
        require(r[key] == expected, 'Selected evidence route changed: '+key);checked(r[key])
    require(plan['materialReaderDispatch'] == bundle['base']['materialReaderDispatch']
            and plan['oldCompleteMaterialGraphs'] == 72 and plan['oldCompleteVisible24TextureSnapshots'] == 114
            and plan['previouslyUnrecordedAuxAndUsageCapturedBeforeAndSaved'] == 3,
            'Exact 60/9/3 full-schema dispatch and missing historical policy limits required')


def validate_scene(r, plan, bundle, g):
    before = read(checked(r['beforeActorWitness']));expected = read(checked(r['expectedActorWitness']))
    saved = read(checked(r['savedActorWitness']))
    exact(before, bundle['base']['savedWitness'], 'Actual selected full scene changed')
    independent = g.expected_counterfactual(before, bundle)
    exact(expected, independent, 'Declared five-slot scene differs from independent source')
    exact(saved, independent, 'Saved scene differs from five-slot counterfactual')
    require(len(before) == len(saved) == 5371 and r['beforeActorWitnessSha256'] == digest(before)
            and r['expectedActorWitnessSha256'] == r['savedActorWitnessSha256'] == plan['expectedActorWitnessSha256'] == digest(independent)
            and plan['originalActorWitnessSha256'] == digest(before), 'Whole scene hashes changed')
    hism = [c for row in saved.values() for c in row['components']
            if c['class'] == '/Script/Engine.HierarchicalInstancedStaticMeshComponent']
    require(len(hism) == 2329 and sum(c['instanceCount'] for c in hism) == 678205, 'Full HISM census changed')
    raw = read(checked(r['rawInstanceControlsBefore']));after = read(checked(r['rawInstanceControlsSaved']))
    exact(raw, bundle['base']['rawControls'], 'Original native matrix/order/mainseed/custom controls changed')
    exact(after, raw, 'Raw controls changed across save/reload')
    require(len(raw) == 2329 and sum(v['instances'] for v in raw.values()) == 678205
            and digest(raw) == digest(after) == plan['originalRawControlsSha256'], 'Signed-zero-sensitive complete raw hashes changed')
    return saved


def validate_old_assets(r, bundle):
    before = read(checked(r['originalAssetWitnessBefore']));saved = read(checked(r['originalAssetWitnessSaved']))
    exact(before, saved, 'All old material/texture fields changed across save/reload')
    base = bundle['base'];require(set(before) == {'graphs', 'textures'}
        and set(before['graphs']) == set(base['materialRecords']) and len(before['graphs']) == 72
        and set(before['textures']) == set(base['textureRecords']) and len(before['textures']) == 114, 'Complete original asset sets required')
    for asset, original in base['materialRecords'].items():
        row = before['graphs'][asset]
        require(row['asset'] == asset and row['reader'] == original['route']
                and row['graphSha256'] == original['graphSha256'] == digest(row['graph'])
                and row['auxPreviouslyRecorded'] is original['auxPreviouslyRecorded']
                and row['usagePreviouslyRecorded'] is original['usagePreviouslyRecorded'], 'Specialized full graph provenance changed')
        exact(row['graph'], original['graph'], 'Complete original graph shape changed')
        if original['aux'] is not None: exact(row['aux'], original['aux'], 'Recorded old sampler/WP auxiliary changed')
        require(set(row['usage']) == {'instancedStaticMeshes', 'nanite'}, 'Both native usage fields required')
        for key, value in original['recordedUsage'].items(): require(row['usage'][key] is value, 'Recorded old usage changed')
        exact(row['metadata'], original['metadata'], 'Recorded original material metadata changed')
    for asset, original in base['textureRecords'].items():
        exact(before['textures'][asset], {'snapshot': original['snapshot'], 'metadata': original['metadata']},
              'Full native size/visible24/encoding/downscale/selected metadata changed')
    return before


def validate_leaf(row, saved, original, source, g):
    leaf = g.leaf_math();kernel = module('_r32_recorded_leaf_constants', g.LEAF_KERNEL, g.LEAF_KERNEL_SHA)
    require(row['asset'] == kernel.OWN and row['originalAsset'] == kernel.LEAF
            and row['newPackageAssets'] == [kernel.OWN] and row['newTextureObjects'] == 0
            and row['compileErrors'] == [], 'Only one saved owned leaf graph required')
    expected = leaf.proposed_graph(original);exact(row['graph'], expected, 'Only one encoded F32 scalar may change')
    require(row['graphSha256'] == digest(expected) and row['oldEncodedF32'] == kernel.OLD
            and row['newArtisticEncodedF32'] == kernel.NEW, 'Original .08 to encoded .24 recipe changed')
    exact(row['aux'], original['aux'], 'Original leaf sampler/WP policy changed')
    exact(row['usage'], original['recordedUsage'], 'Original leaf usage changed')
    require(row['metadata'] == {'BreziGeneratedBy': kernel.OWNER,
        'BreziR44SourceProposalSha256': source['proposalPin']['sha256'], 'BreziR44OriginalLeafAsset': kernel.LEAF,
        'BreziR44ArtisticTransmissionF32': repr(kernel.NEW)}, 'Leaf provenance changed')
    exact(saved, {key:row[key] for key in ('asset', 'graph', 'aux', 'usage')}, 'Saved leaf readback changed')
    for key in ('materialPackagesIndependentlyUnloaded', 'numericNativeNormalTangentReadbackPerformed',
                'physicalLeafOpticsAccepted', 'nativeAppearanceAccepted'):
        require(row[key] is False, 'Leaf evidence promoted')


def roof_metadata(roof, source, role, original=None):
    expected = {'BreziGeneratedBy': roof.OWNER, 'BreziR46Role': 'roof:'+role,
                'BreziR46RoofSourceProposalSha256': source['proposalPin']['sha256'], 'BreziSourceLicense': 'CC0-1.0'}
    if original is not None: expected['BreziSourceSha256'] = original['sha256']
    return expected


def validate_roof(row, saved, source, bundle, g):
    roof = module('_r32_owned_roof_pure_validation', g.ROOF, g.ROOF_SHA);proposal = source['proposal'];material = row['material']
    require(row['schema'] == roof.SCHEMA and row['schemaVersion'] == 1 and row['owner'] == roof.OWNER
            and row['nativeBinding'] == bundle['binding'] and row['sourceProposal'] == source['proposalPin']
            and row['newPackageAssets'] == sorted(proposal['proposedAssets'].values())
            and row['newMaterialGraphs'] == 1 and row['newTextureObjects'] == 3 and row['fourOwnedPackagesSaved'] is True,
            'Exact roof material/three original photos required')
    for key, value in roof.LIMITS.items(): require(row[key] is value, 'Roof evidence limit changed')
    require(row['pureApiSources'] == [pin(roof.POLICY), pin(roof.CONTRACT), pin(roof.KERNEL)], 'Pinned pure graph/policy sources changed')
    require(material['asset'] == proposal['proposedAssets']['material'] and material['compileErrors'] == []
            and material['graphSha256'] == digest(material['graph'])
            and roof.kernel().validate_graph(material['graph'], proposal) == material['graphAudit'], 'Eight-node original photo graph changed')
    flags = material['graph']['flags'];require(flags == material['policy'], 'Complete saved roof flags differ')
    require(flags['blend_mode'] == '<BlendMode.BLEND_OPAQUE: 0>'
            and flags['shading_model'] == '<MaterialShadingModel.MSM_DEFAULT_LIT: 1>'
            and flags['two_sided'] is False and flags['tangent_space_normal'] is True
            and flags['use_material_attributes'] is False
            and flags['opacity_mask_clip_value'] == 0.33329999446868896
            and set(flags) == {'blend_mode','shading_model','two_sided','tangent_space_normal',
                               'use_material_attributes','opacity_mask_clip_value'}, 'Full five-field/default clip policy required')
    require(material['aux'] == {'samplerSources': {roof.contract().TAG+key:
        '<SamplerSourceMode.SSM_FROM_TEXTURE_ASSET: 0>' for key in ('diffuse','normalGL','roughness')},
        'worldPositionShaderOffsets': {}}, 'Exact three from-asset samplers/no new WP offsets required')
    require(material['metadata'] == roof_metadata(roof, source, 'material'), 'Roof graph provenance differs')
    exact(saved, {key:material[key] for key in ('asset', 'graph', 'aux')}, 'Saved roof full graph/aux readback changed')
    require(set(row['textures']) == {'diffuse', 'normalGL', 'roughness'}, 'Three distinct original map roles required')
    # The proven original R43 role policy is identical. Compare native visible
    # settings, not source PNG texels or original16-bit precision in the GPU.
    prototype = bundle['base']['report']['materialReport']['materials']['wood']['textures']
    for channel, record in row['textures'].items():
        original = proposal['source']['originalMaps'][channel]
        checked({key:original[key] for key in ('path','sha256','bytes')})
        role = 'normal' if channel == 'normalGL' else channel;native = copy.deepcopy(prototype[role]['snapshot'])
        native['asset'] = proposal['proposedAssets'][channel]
        native['metadata'] = {'BreziGeneratedBy': roof.OWNER, 'BreziSourceSha256': original['sha256'],
                              'BreziTechnicalDataRole': '', 'BreziSourcePlanSha256': ''}
        require(record['asset'] == native['asset'] and record['source'] == original
                and record['metadata'] == roof_metadata(roof, source, channel, original)
                and record['snapshotSha256'] == digest(record['snapshot'])
                and record['native16BitSourcePrecisionVerified'] is False
                and record['nativePixelFormatOrTexelsReadBack'] is False, 'Original map provenance or precision tier changed')
        exact(record['snapshot'], native, 'Full visible24 native original-map role policy changed')


def validate_saved(r, plan, pf, bundle):
    g = module('_r32_frozen_combined_guard', GUARD, GUARD_SHA)
    report_header(r, plan, pf, bundle, g);validate_scene(r, plan, bundle, g)
    assets = validate_old_assets(r, bundle)
    built = read(checked(r['newMaterialReport']));exact(built, r['materialReport'], 'Recorded new material packet differs')
    saved_new = read(checked(r['savedNewMaterialReadback']))
    require(set(built) == set(saved_new) == {'leaf', 'roof'}, 'Exactly two new graph readbacks required')
    leaf = g.leaf_math();original = bundle['base']['materialRecords'][leaf.LEAF]
    validate_leaf(built['leaf'], saved_new['leaf'], original, bundle['source']['leaf'], g)
    validate_roof(built['roof'], saved_new['roof'], bundle['source']['roof'], bundle, g)
    require(sorted(built['leaf']['newPackageAssets']+built['roof']['newPackageAssets']) == g.expected_packages(bundle['source']), 'Five package union changed')
    content = read(checked(r['afterContentInventory']))
    require(g.validate_content_delta(bundle['base']['content'], content, bundle['source']) == r['assetDelta']
            and r['protectedProjectProof'] == bundle['base']['report']['protectedProjectProof']
            and len(read(checked(r['protectedProjectProof']))) == 132, 'Map-only plus5/protected132 receipt changed')
    return {'mode':'saved-r46-five-slot-material-pilot', 'nativeProcessId':r['nativeProcessId'],
        'originalActors':5371, 'savedActors':5371, 'fullHismComponents':2329, 'fullHismInstances':678205,
        'materialGraphs':74, 'textureObjects':117, 'contentFiles':4144, 'protectedFiles':132,
        'originalMaterialGraphsValidated':72, 'originalTexturePoliciesValidated':114,
        'changedMaterialSlots':5, 'newMaterialGraphs':2, 'newTextureObjects':3, 'newPackages':5,
        'wholeActorCounterfactualValidated':True, 'allRawControlsValidated':True,
        'freshNativeActorOrGeometryDecodePerformedByCpuChecker':False,
        'sourcePngTexelsOrGpuPrecisionDecodedByCpuChecker':False,
        'previouslyUnrecordedOwnThreeAuxUsageBoundBeforeAndSaved':True,
        'savedNewTextureEqualityIsNativeReceiptGateNotFreshCpuDecode':True,
        'combinedCaptureCannotIsolateLeafTransmissionFromRoofIndirectLighting':True,
        **{key:False for key in FALSE_FLAGS if key not in ('oldActorGeometryRootCollisionNavOrMeshDefaultSettersCalled', 'oldMaterialOrTextureSettersCalled')}}


def terminal_and_audit(r):
    actual_binding_required();process = read(checked(ACTUAL['process']));raw = read(checked(ACTUAL['rawProcess']))
    audit = read(checked(ACTUAL['rootByteAudit']))
    require(raw['pid'] == r['nativeProcessId'] == ACTUAL['nativeProcessId'] and raw['code'] == 0 and raw['signal'] is None,
            'Closed actual own native0 required')
    require(raw['args'][0] == str(REPORT.parent/'Project/BreziTwin/BreziTwin.uproject')
            and all(a in raw['args'] for a in ('-nullrhi', '-run=pythonscript', '-script='+str(NATIVE), '-abslog='+process['logFile']))
            and process['reportSha256'] == ACTUAL['reportSha'] and process['processFileSha256'] == ACTUAL['rawProcess']['sha256']
            and process['sourcePinsUnchangedAfterNative'] is True
            and process['controllerSha256BeforeNative'] == process['controllerSha256AfterNative'] == ACTUAL['monitorSha']
            and len(process['sourcePinsBeforeNative']) == ACTUAL['terminalSourceCount']
            and all(process['sourcePinsBeforeNative'].get(k) == v for k,v in r['inputFiles'].items()), 'Actual native command/source closure changed')
    require(audit['schema'] == 'brezi-r46a-root-saved-five-slot-material-byte-audit-r1' and audit['schemaVersion'] == 1
            and audit['status'] == 'verified-saved-native0-only-original-map-changed-five-new-owned-material-photo-packages-all5664-frozen-pins-exact'
            and audit['nativeReport'] == pin(REPORT) and audit['nativeProcess'] == ACTUAL['process']
            and audit['rawNativeProcess'] == ACTUAL['rawProcess'] and audit['nativeProcessId'] == ACTUAL['nativeProcessId']
            and audit['exitCode'] == audit['rootSessionClosedExitCode'] == 0 and audit['nativeIdleAfter'] == [],
            'Exact fully closed root native/current-byte envelope required')
    require(audit['project'] == r['project'] and audit['projectClone'] == r['projectClone']
            and audit['currentContentInventory'] == r['afterContentInventory']
            and audit['currentProtectedProof'] == r['protectedProjectProof']
            and audit['currentProjectFiles'] == 4276 and audit['currentContentFiles'] == 4144
            and audit['currentProtectedFiles'] == 132 and audit['actualCounts'] == r['actualCounts']
            and audit['newRelativeContentFiles'] == r['assetDelta']['newRelativeFiles']
            and audit['newOwnedPackageTypes'] == {'materials':2,'textures':3}, 'Actual byte scope changed')
    for key in ('candidateOriginal4270NonMapFilesExact','onlyOriginalMapChanged','selectedR43bAll4271FilesExact',
                'initialIndependentCloneRowsStillIndependent','all5664FrozenSourcePinsExact','all5657PreflightSourcePinsExact'):
        require(audit[key] is True, 'Required actual byte evidence missing: '+key)
    required = set(TRUE_FLAGS)-{'nativeApplied','savedMapUnloadedReloaded','sourceInputsUnchanged'}
    require(set(audit['savedNativeProofFlags']) == required and all(audit['savedNativeProofFlags'][k] is True and r[k] is True for k in required),
            'Saved native proof flags changed')
    for key in ('newNativeActorOrAttributeDecodeByAudit','nativeAppearanceAccepted','fullPhotorealismAccepted',
                'performanceAccepted','shippingVerified','activeOutputPromoted'):
        require(audit[key] is False, 'Root audit evidence tier changed')
    return audit


def main():
    parser = argparse.ArgumentParser();parser.add_argument('report', type=Path);args = parser.parse_args()
    actual_binding_required()
    require(args.report.resolve() == REPORT and sha(REPORT) == ACTUAL['reportSha']
            and sha(PLAN) == PLAN_SHA and sha(PREFLIGHT) == PREFLIGHT_SHA, 'Exact actual saved report/source pins required')
    r = read(REPORT);terminal_and_audit(r)
    g = module('_r32_saved_recorded_guard', GUARD, GUARD_SHA)
    print(json.dumps(validate_saved(r, read(PLAN), read(PREFLIGHT), saved_bundle(g)), sort_keys=True, allow_nan=False))


if __name__ == '__main__': main()
