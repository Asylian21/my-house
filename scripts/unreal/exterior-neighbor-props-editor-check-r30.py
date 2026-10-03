"""Typed R30 saved R39c/R3 consumer; no Unreal or historical generation.

Only the closed R39c native report, terminal process, source plan/preflight
and root current-byte audit are accepted.
Stored native equality is distinct from fresh native decoding by this CPU.
"""
import argparse
import importlib.util
import hashlib
import json
import math
from pathlib import Path
from datetime import datetime
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighbor-props-editor-check-r30.py'
GUARD = ROOT/'scripts/unreal/exterior-neighbor-props-guards-r39-r3.py'
GUARD_SHA = '58cb7abb17e008b1e77e0a08a088ab2c698d600c9dc151b5a51de7cf9a4cdf95'
HELPER = ROOT/'scripts/unreal/exterior-neighbor-props-native-r39-r3.py'
REPORT = ROOT/'output/unreal/exterior-20261002-r39c/neighbor-props-native-report-r3.json'
CLONE_SHA = 'c98868ea51686a34f68139e3f6cc48c2a4edff9516c92f23973bb8ca60f956b5'
SCHEMA_VERSION = 3
REPAIR_SCHEMA = 'brezi-r39-exact-new-local-zero-constructor-repair-r3'

# Actual closed native0 and independent current-byte evidence, not anticipated success.
HELPER_SHA = '8b49f73e164b99803c0cb2625590179719b56d757e987308ec7eb2c4bd66765d'
PLAN_SHA = '85ec3bb423fe8205b551629b2c4f374c715cd2adb2f5ea265c5dc38ada6aa7c5'
PREFLIGHT_SHA = '3bc9b4cb47603c572afb1502b4e591406d03b810084555bfc64f43f2d60be0b7'
REPORT_SHA = '118f451095730e2ff0e62304d959626d4a81be53f03e41dd2229fe91831f4da5'
PROCESS_PATH = REPORT.parent/'neighbor-props-native-r39-r3-process.json'
PROCESS_SHA = '2bbb88ee2d71a0d81469c267f263c22beaea4f2d49eba05618d9c8896c2e96e0'
ROOT_AUDIT_PATH = REPORT.parent/'root-native-success-byte-audit-r39c-r3.json'
ROOT_AUDIT_SHA = '7f70d6eb3c59e87305313ba35b7cf7324fde14e80507b5d06e3eaecce7f17ad5'
NATIVE_PROCESS_ID = 94572
TERMINAL_SOURCE_COUNT = 1294
PREFLIGHT_SOURCE_COUNT = 1288


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


g = None


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def read(path):
    return json.loads(Path(path).read_text())


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def checked(row):
    path = Path(row['path']).resolve()
    require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == row['sha256']
            and path.stat().st_size == row['bytes'], 'Exact consumed sidecar changed: '+str(path))
    return path


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def guard_module():
    global g
    require_actual_binding()
    require(sha(GUARD) == GUARD_SHA, 'Frozen actual R39-r3 guard changed')
    if g is None:
        g = module('_r30_frozen_r39r3_guards', GUARD)
    return g


def require_actual_binding():
    values = (GUARD_SHA, CLONE_SHA, HELPER_SHA, PLAN_SHA, PREFLIGHT_SHA, REPORT_SHA, PROCESS_PATH,
              PROCESS_SHA, ROOT_AUDIT_PATH, ROOT_AUDIT_SHA, NATIVE_PROCESS_ID,
              TERMINAL_SOURCE_COUNT, PREFLIGHT_SOURCE_COUNT)
    require(all(v is not None for v in values),
            'UNBOUND R30 draft: actual saved native0/current-byte evidence is required')
    require(type(NATIVE_PROCESS_ID) is int and NATIVE_PROCESS_ID > 0,
            'Actual successful native process identity required')


def saved_bundle():
    """Only direct recorded selected-source readers; no historical source replay.

    The frozen R3 loader's False option validates initial clone metadata, source
    and read-only calibration receipts, while avoiding pristine-map assertions
    and fresh inventory scans after the candidate map has been saved.
    """
    guard = guard_module()
    require(sha(guard.CLONE) == CLONE_SHA, 'Exact initial R39c clone receipt changed')
    return guard.load_contract(validate_current=False)


def report_header(report, plan, preflight, bundle):
    guard_module()
    require(sha(HELPER) == HELPER_SHA and report['schema'] == g.SCHEMA
            and report['schemaVersion'] == SCHEMA_VERSION and report['owner'] == g.NATIVE_OWNER
            and report['status'] == 'verified-saved-six-whole-original-neighbor-prop-assemblies'
            and report['nativeProcessId'] == NATIVE_PROCESS_ID
            and report['project'] == str(g.PROJECT) and report['output'] == str(g.CANDIDATE)
            and report['nativeApplied'] is True and report['savedMapUnloadedReloaded'] is True
            and report['sourceInputsUnchanged'] is True and report['actualCounts'] == g.COUNTS,
            'Only the exact successful saved whole-original R39 scene is accepted')
    require(report['selectedPlan'] == pin(g.PLAN) and report['selectedPlan']['sha256'] == PLAN_SHA
            and report['sourcePreflight']['sha256'] == PREFLIGHT_SHA
            and report['binding'] == plan['binding'] == preflight['binding'] == bundle['binding']
            and report['sourceProposal'] == bundle['source']['proposalPin']
            and report['baseNativeReport'] == bundle['base']['reportPin']
            and report['baseNativeProcess'] == pin(g.BASE_PROCESS)
            and report['baseCurrentByteAudit'] == pin(g.BASE_AUDIT)
            and report['selectedRootImageDecision'] == pin(g.IMAGE_DECISION)
            and report['projectClone'] == pin(g.CLONE),
            'Actual report/source/base/image/clone bindings differ')
    require(plan['schema'] == preflight['schema'] == g.SCHEMA
            and plan['schemaVersion'] == preflight['schemaVersion'] == SCHEMA_VERSION
            and plan['nativeOwner'] == preflight['owner'] == g.NATIVE_OWNER
            and plan['status'] == 'image-selected-whole-original-neighbor-props-source-ready-native-r3-pending'
            and preflight['status'] == 'image-selected-whole-original-neighbor-props-preflight-validated-native-r3-pending'
            and plan['expectedCounts'] == preflight['expectedCounts'] == g.COUNTS
            and preflight['tests']['exitCode'] == 0 and preflight['tests']['testCount'] == 9
            and report['inputFiles'] == preflight['inputFiles']
            and len(report['inputFiles']) == PREFLIGHT_SOURCE_COUNT,
            'The actual mandatory source/preflight contract differs')
    require(report['repairSchema'] == plan['repairSchema'] == preflight['repairSchema'] == REPAIR_SCHEMA
            and REPAIR_SCHEMA == g.REPAIR_SCHEMA, 'Only exact local-constructor R3 repair accepted')
    for key in ('repairEvidence', 'nodePoseCalibration', 'constructorRepairEvidence', 'constructorCalibration'):
        g.require(g.binary_exact(report[key], plan[key]) and g.binary_exact(plan[key], preflight[key]),
                  'Exact repair/calibration receipt changed: '+key)
    g.require(g.binary_exact(report['nodePoseCalibration'], bundle['nodePoseCalibration'])
              and g.binary_exact(report['constructorCalibration'], bundle['constructorCalibration'])
              and g.binary_exact(report['repairEvidence'], g.repair_evidence())
              and g.binary_exact(report['constructorRepairEvidence'], g.constructor_repair_evidence()),
              'Actual diagnostic-measured calibration must remain immutable')
    require(report['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
            and report['setbacksMm'] == {'street': 3000, 'east': 3000}, 'C/B/B and fixed setbacks required')
    false_fields = ('sourceOriginalGeometryAndPhotoPixelsEdited',
        'originalActorTransformInstanceOrMaterialSettersCalled', 'nativeAppearanceAccepted',
        'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified', 'packageVerified',
        'activeOutputPromoted', 'nativeNormalTangentReadbackAvailable', 'nativeGpuPixelFormatVerified',
        'allSixAssemblyActorsIndividuallyVisibleVerified', 'actualNativeSurfaceContactCollisionOrSurveyVerified',
        'oldAdditionalRandomSeedRangesPreservationClaimed', 'nativeTangentsNumericallyVerified')
    require(all(report[k] is False for k in false_fields), 'Native evidence limit was promoted')
    true_fields = ('allOriginal5364ActorsAnd2325RawControlsExact',
        'allOriginal66MaterialGraphsAuxObservedUsageExact', 'allOriginal97TextureSettingsAndSourceBytesExact',
        'allFourOriginalPartsFullNativeIdentityVerified',
        'allSixIntendedAssembliesAndOriginalHoseNodePosesIndependentlyCompared',
        'allEightMeasuredPosesExactBeforeAppliedAndSaved', 'sourceNormalsPreservedAndDerivedUvTangentsRequested')
    require(all(report[k] is True for k in true_fields), 'Actual required saved proof is absent')


def validate_material_record(maps, built, model, row):
    """Validate serialized native settings; this function never reads a UObject."""
    token = maps.api().token
    policy = row['policy']
    require(policy == row['graph']['flags'] and digest(policy) == digest(row['graph']['flags']),
            'Recorded complete graph flags and native material settings differ')
    require(token(policy['blend_mode']) == 'BLENDOPAQUE'
            and token(policy['shading_model']) in ('DEFAULTLIT', 'MSMDEFAULTLIT')
            and policy['two_sided'] is True and policy['tangent_space_normal'] is True
            and policy['use_material_attributes'] is False
            and math.isfinite(policy['opacity_mask_clip_value']), 'Exact opaque/two-sided DefaultLit settings required')
    expected_metadata = {'BreziGeneratedBy': maps.OWNER, 'BreziR39SourceStudySha256': g.SOURCE_SHA,
                         'BreziR39Model': model, 'BreziR39Role': 'material', 'BreziSourceLicense': 'CC0-1.0'}
    require(row['metadata'] == expected_metadata, 'Owned whole-model material metadata differs')
    preflight = built['nativeEnumPreflight']
    for role, texture in row['textures'].items():
        values = texture['snapshot']
        simple = {'srgb': role == 'albedo', 'flip_green_channel': role == 'normalGL',
                  'lod_bias': 0, 'max_texture_size': 0, 'virtual_texture_streaming': False,
                  'never_stream': False, 'do_scale_mips_for_alpha_coverage': False,
                  'alphaCoverageThresholds': [0., 0., 0., 0.], 'pixels': [2048, 2048]}
        require(all(values[k] == v for k, v in simple.items()), 'Recorded native map policy differs: '+role)
        compression = 'TCNormalmap' if role == 'normalGL' else 'TCDefault' if role == 'albedo' else 'TCMasks'
        encoding = 'TSESRGB' if role == 'albedo' else 'TSENONE'
        fields = {'compression_settings': 'TextureCompressionSettings.'+compression,
                  'sourceEncoding': 'TextureSourceEncoding.'+encoding,
                  'address_x': 'TextureAddress.TA_WRAP', 'address_y': 'TextureAddress.TA_WRAP',
                  'mip_gen_settings': 'TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP',
                  'power_of_two_mode': 'TexturePowerOfTwoSetting.NONE'}
        require(all(values[k] == preflight[v] for k, v in fields.items()),
                'Measured enum/source encoding policy differs: '+role)
        expected = {**expected_metadata, 'BreziR39Role': role, 'source_sha256': texture['source']['sha256']}
        require(texture['metadata'] == expected, 'Untouched original map ownership differs: '+role)


def validate_saved(report, plan, bundle, preflight):
    report_header(report, plan, preflight, bundle)
    n = module('_r30_exact_saved_r39_native_pure_kernels', HELPER)
    before = read(checked(report['beforeActorWitness']))
    expected_record = read(checked(report['expectedActorWitness']))
    saved = read(checked(report['savedActorWitness']))
    require(before == bundle['base']['savedWitness']
            and digest(before) == digest(bundle['base']['savedWitness']) and len(before) == 5364,
            'Every selected old actor must remain the immutable baseline')
    for key, value in (('beforeActorWitnessSha256', before),
                       ('expectedActorWitnessSha256', expected_record), ('savedActorWitnessSha256', saved)):
        require(digest(value) == report[key], 'Canonical full actor witness differs: '+key)
    measurements = read(checked(report['newSourceNativeMeasurements']))
    require(report['privateMaterialBindingAdapter'] == n.material_adapter_evidence(),
            'Only private frozen material binding loader may adapt to R3')
    n.validate_measurement_receipt(bundle, measurements)
    g.validate_constructor_measurements(measurements, bundle)
    parts = {p['key']: p for rows in bundle['source']['parts'].values() for p in rows}
    require(set(report['newOwnedGroups']) == set(parts) == set(measurements),
            'Every whole original source part requires its own measured group')
    require(plan['templateActor'] == n.TEMPLATE
            and plan['templateActorWitness'] == n.template_contract(bundle),
            'Exact immutable render-policy template required')
    added = {}
    for key, group in report['newOwnedGroups'].items():
        m = measurements[key]
        require(group['part'] == key and group['assemblyRootIds'] == m['assemblyRootIds']
                and group['instances'] == len(m['assemblyRootIds']) and group['actor'] not in before,
                'Exact ordered six-assembly/eight-part mapping differs')
        wanted_mesh = g.PREFIX+'/Geometry/StaticMeshes/'+parts[key]['modelId']+'_part_'+str(parts[key]['nodeIndex'])
        recipe = bundle['source']['recipes'][parts[key]['modelId']]
        wanted_material = g.PREFIX+'/'+recipe['key']+'/Materials/M_'+recipe['key']
        require(group['mesh'] == wanted_mesh+'.'+wanted_mesh.rsplit('/', 1)[-1]
                and group['material'] == wanted_material+'.'+wanted_material.rsplit('/', 1)[-1],
                'Only exact canonical original master/material bindings are allowed')
        added[group['actor']] = n.added_expected(bundle, key, group['actor'],
                                                group['mesh'], group['material'], m)
    expected = g.expected_counterfactual(before, added)
    require(expected == expected_record == saved
            and digest(expected) == digest(expected_record) == digest(saved),
            'Full old5364 + four measured source-template counterfactual differs')
    hisms = [v for actor in saved.values() for v in actor['components']
             if v['class'] == '/Script/Engine.HierarchicalInstancedStaticMeshComponent']
    require((len(saved), len(hisms), sum(v['instanceCount'] for v in hisms)) == (5368, 2329, 678205),
            'Actual full saved actor/HISM census differs')

    original_raw = read(checked(report['rawInstanceControlsBefore']))
    saved_raw = read(checked(report['rawInstanceControlsSaved']))
    n.exact(original_raw, saved_raw, 'Original wrapped matrices/main-seed/custom/order changed')
    n.exact(original_raw, bundle['base']['rawControls'], 'Recorded old raw controls differ from selected actual state')
    require(len(saved_raw) == 2325 and sum(v['instances'] for v in saved_raw.values()) == 678197,
            'All original raw members are required')

    graphs_before = read(checked(report['originalMaterialWitnessBefore']))
    graphs_saved = read(checked(report['originalMaterialWitnessSaved']))
    require(graphs_before == graphs_saved and set(graphs_before) == set(bundle['base']['materialRecords']),
            'Complete before/saved original graph identity differs')
    for asset, row in graphs_before.items():
        source = bundle['base']['materialRecords'][asset]
        require(row['asset'] == asset and row['reader'] == source['route']
                and row['graph'] == source['graph']
                and digest(row['graph']) == row['graphSha256'] == digest(source['graph'])
                and row['aux'] == source['aux'] and row['usagePreviouslyRecorded'] is source['usageRecordedInSelectedNativeReceipt'],
                'Original full graph/aux/source reader changed')
        require(set(row['usage']) == {'instancedStaticMeshes', 'nanite'}
                and all(type(v) is bool for v in row['usage'].values()), 'Actual observed original usage flags required')
        if source['usageRecordedInSelectedNativeReceipt']:
            require(row['usage'] == source['usage'], 'Actual original64 usage flags changed')
        if 'metadata' in source:
            require(row['metadata'] == source['metadata'], 'Original R38 material ownership changed')
    for phase, expected_graphs in (('before', graphs_before), ('saved', graphs_saved)):
        rows = [read(checked(p)) for p in report['materialGraphDiagnosticFiles'][phase]]
        require(len(rows) == 66 and len({r['asset'] for r in rows}) == 66
                and {r['asset']: r for r in rows} == expected_graphs,
                'Complete132 observed original graph diagnostics required')
    textures = read(checked(report['originalTextureWitnessBefore']))
    require(textures == read(checked(report['originalTextureWitnessSaved'])) == bundle['base']['textureRecords']
            and len(textures) == 97 and all(set(r['values']) == g.TEXTURE_FIELDS for r in textures.values()),
            'All original97 visible24 texture settings must remain exact')

    built = read(checked(report['newMaterialReport']))
    require(built == report['materialReport'] and built['nativeBinding'] == bundle['binding']
            and built['materialCount'] == 3 and built['textureObjectCount'] == 11,
            'Exact original-map material report differs')
    material_file = ROOT/'scripts/unreal/exterior-neighbor-props-materials-r39.py'
    require(sha(material_file) == n.MATERIAL_SHA, 'Actually consumed material writer changed')
    maps = n.material_module()
    require(set(n.material_packet(bundle)) == {'source', 'base', 'binding'},
            'Private original material packet must retain its exact three-key API')
    require(built['schema'] == maps.SCHEMA and built['owner'] == maps.OWNER
            and set(built['materials']) == set(g.MODEL_IDS)
            and built['newPackageAssets'] == maps.validate_recipes(bundle['source']),
            'Three graph/eleven original-map package closure differs')
    require(built['sourceStudy'] == bundle['source']['proposalPin']
            and built['sourceRecipeContract'] == pin(maps.SOURCE_CONTRACT),
            'Frozen source recipe/whole models required')
    require(built['sourcePngBitDepthDoesNotProveGpuFormat'] is True
            and all(built[k] is False for k in ('nativeSourceTexelsDecoded', 'nativeGpuPixelFormatVerified',
                'nativeNormalTangentReadbackAvailable', 'materialPackagesIndependentlyUnloaded',
                'sourceOpticalModelExactlyReproduced', 'nativeAppearanceAccepted',
                'fullPhotorealismAccepted', 'performanceAccepted')), 'Owned material evidence cannot widen')
    for model, row in built['materials'].items():
        recipe = bundle['source']['recipes'][model]
        asset, assets = maps.assets(recipe)
        require(row['asset'] == asset and row['recipe'] == recipe
                and digest(row['graph']) == row['graphSha256'] and row['compileErrors'] == []
                and row['instancedStaticMeshUsage'] is True and set(row['textures']) == set(assets),
                'Actual compiled original prop graph/usage differs')
        maps.validate_graph(row['graph'], recipe, assets)
        validate_material_record(maps, built, model, row)
        for role, texture in row['textures'].items():
            require(texture['asset'] == assets[role] and texture['source'] == recipe['maps'][role]
                    and texture['sourcePng'] == maps.png_header(texture['source']),
                    'Untouched published PNG identity differs')

    geometry = read(checked(report['nativeGeometryReadbackReceipt']))
    require(geometry == report['nativeGeometryReadback'] and set(geometry) == set(parts),
            'Full four-part source/native geometry closure differs')
    import_proof = read(checked(report['importReadback']))
    imported = {r['sourcePart']: r for r in import_proof['sourcePartProofs']}
    require(len(imported) == len(import_proof['sourcePartProofs']) == 4
            and set(imported) == set(parts) and import_proof['fullOriginalMeshTriangles'] == 26601
            and import_proof['hoseOriginalPartsPreserved'] == 2
            and import_proof['originalSourcePoseReadbackActuallyMeasured'] is True,
            'All complete whole-model parts require actual pre-mutation identity proof')
    for key, part in parts.items():
        expected_hash = digest(n.expected_corners(part))
        for row in (geometry[key], imported[key]):
            require(row['sourcePart'] == key and row['triangles'] == part['triangles']
                    and row['vertices'] == part['vertices'] and row['sections'] == 1
                    and row['fullOrderedNativeF32PositionUv0TopologyWindingSha256'] == expected_hash
                    and row['sourceIdentityFromCountAlone'] is False
                    and row['sourceIdentityFromNameOrLabel'] is False
                    and row['nativeNormalTangentReadbackAvailable'] is False
                    and row['nativeGeneratedTangentsActuallyMeasured'] is False,
                    'Every ordered original F32 P/UV0 corner/section/winding must match')
        n.exact(imported[key]['actualImportedNodePose'],
                [g.native_node_translation(part), [0., 0., 0., 1.], [1., 1., 1.]],
                'Whole original nonbaked node offset differs')
        require(geometry[key]['asset'] == report['newOwnedGroups'][key]['mesh'],
                'Saved exact source-geometry/group identity differs')
    content = read(checked(report['afterContentInventory']))
    assets = g.expected_new_packages(bundle['source'])
    delta = g.validate_content_delta(bundle['base']['content'], content, assets)
    require(report['newPackages'] == assets and report['assetDelta'] == delta,
            'Only map and exact21 own assets may change')
    return {'mode': 'saved-six-whole-original-neighbor-prop-assemblies',
        'nativeProcessId': NATIVE_PROCESS_ID, 'originalActors': 5364, 'savedActors': 5368,
        'newActors': 4, 'wholeAssemblyRoots': 6, 'newOriginalPartInstances': 8,
        'fullSceneHismComponents': 2329, 'fullSceneHismInstances': 678205,
        'fullHismComponents': 2329, 'fullHismInstances': 678205,
        'retainedOriginalHismComponents': 2325, 'retainedOriginalHismInstances': 678197,
        'scopedMaterialGraphs': 69, 'scopedTextureObjects': 108,
        'newPackages': 21, 'contentFiles': 4124, 'protectedFiles': 132,
        'wholeActorCounterfactualValidated': True, 'allIntendedSourceAssembliesAndHoseNodePosesCompared': True,
        'fullNativeF32PositionUv0TopologyProofTriangles': 26601,
        'sourceInstanceTriangles': 44445, 'freshNativeActorGeometryOrMatrixDecodeExecuted': False,
        'freshNativeActorOrGeometryDecodePerformedByCpuChecker': False,
        'storedNewMatricesIndependentlyDecodedAfterSaveByCpuChecker': False,
        'allMeasuredConstructorAndNativeSerializationValuesExact': True,
        'sourceQuaternionZeroConventionChanged': False, 'epsilonOrToleranceUsed': False,
        'nativeNormalTangentReadbackAvailable': False, 'nativeGpuPixelFormatVerified': False,
        'nativeSurfaceContactOrSurveyVerified': False, 'nativeAppearanceAccepted': False,
        'fullPhotorealismAccepted': False, 'performanceAccepted': False,
        'shippingVerified': False, 'packageVerified': False, 'activeOutputPromoted': False}


RAW_PATH = REPORT.parent/'neighbor-props-native-r39-r3.log.json'
RAW_SHA = 'c8d059ca2b877d91d95ea2509dfedf323b1d773538af470b61cba32f73910598'
MONITOR_SHA = '489b4c685d086f883b36ae040710708fae068f6197bead5e7c73f4b85174e50e'
AUDIT_CONTROLLER_SHA = '7a8bdc55052efdc94bf2df1a419612856ce24d6e0a50921ae94c13ee14ae89c0'


def validate_terminal(report, terminal, raw):
    guard_module()
    require(raw['code'] == 0 and raw['signal'] is None and raw['pid'] == NATIVE_PROCESS_ID
            and raw['command'] == '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd'
            and raw['args'][0] == str(g.PROJECT/'BreziTwin.uproject'),
            'Only the actual fully closed own native0 process is accepted')
    require(datetime.fromisoformat(raw['endedAt']) >= datetime.fromisoformat(raw['startedAt']),
            'Actual process end must follow its start')
    require(terminal['processFile'] == str(RAW_PATH) and terminal['processFileSha256'] == RAW_SHA
            and terminal['reportSha256'] == REPORT_SHA and terminal['sourcePinsUnchangedAfterNative'] is True
            and terminal['controllerSha256BeforeNative'] == terminal['controllerSha256AfterNative'] == MONITOR_SHA,
            'Actual monitor/report/unchanged source terminal differs')
    log = REPORT.parent/'neighbor-props-native-r39-r3.log'
    require(terminal['logFile'] == str(log)
            and all(v in raw['args'] for v in ('-nullrhi', '-run=pythonscript',
                '-script='+str(HELPER), '-abslog='+str(log))),
            'Exact actual root-only import command and log required')
    require(len(terminal['sourcePinsBeforeNative']) == TERMINAL_SOURCE_COUNT
            and len(report['inputFiles']) == PREFLIGHT_SOURCE_COUNT
            and all(terminal['sourcePinsBeforeNative'].get(k) == v for k, v in report['inputFiles'].items()),
            '1288 consumed source and1294 terminal pins must stay distinct and exact')
    return True


def validate_root_audit(audit, report):
    guard_module()
    require(audit['schema'] == 'brezi-r39c-root-saved-whole-original-neighbor-props-byte-audit-r3'
            and audit['schemaVersion'] == 3 and audit['status']
            == 'verified-saved-native0-only-original-map-changed-21-new-owned-packages-all1294-frozen-pins-exact'
            and audit['nativeReport'] == pin(REPORT) and audit['nativeProcess'] == pin(PROCESS_PATH)
            and audit['rawNativeProcess'] == pin(RAW_PATH) and audit['nativeProcessId'] == NATIVE_PROCESS_ID
            and audit['exitCode'] == audit['rootSessionClosedExitCode'] == 0,
            'Exact independently completed current-byte success audit required')
    require(audit['project'] == str(g.PROJECT) and audit['projectClone'] == report['projectClone']
            and audit['currentContentInventory'] == report['afterContentInventory']
            and audit['currentProtectedProof'] == report['protectedProjectProof']
            and audit['currentContentFiles'] == 4124 and audit['currentProtectedFiles'] == 132
            and audit['currentProjectFiles'] == 4256 and audit['actualCounts'] == report['actualCounts'] == g.COUNTS,
            'Only actual typed current4124+132 and original clone provenance accepted')
    for key in ('candidateOriginal4234NonMapFilesExact', 'onlyOriginalMapChanged',
                'selectedR38bAll4235FilesExact', 'initialIndependentCloneRowsStillIndependent',
                'all1294FrozenSourcePinsExact', 'all1288PreflightSourcePinsExact', 'failedAttemptEvidenceRetained'):
        require(audit[key] is True, 'Actual required independent byte proof missing: '+key)
    require(audit['newRelativeContentFiles'] == report['assetDelta']['newRelativeContentFiles']
            and audit['newOwnedPackageTypes'] == {'meshes': 4, 'materialGraphs': 3,
                                                 'originalTextureObjects': 11, 'pipelines': 3},
            'Only four meshes/three graphs/eleven maps/three pipelines allowed')
    require(set(audit['savedNativeProofFlags']) == {
        'allOriginal5364ActorsAnd2325RawControlsExact', 'allOriginal66MaterialGraphsAuxObservedUsageExact',
        'allOriginal97TextureSettingsAndSourceBytesExact', 'allFourOriginalPartsFullNativeIdentityVerified',
        'allSixIntendedAssembliesAndOriginalHoseNodePosesIndependentlyCompared',
        'allEightMeasuredPosesExactBeforeAppliedAndSaved'}
        and all(v is True and report[k] is True for k, v in audit['savedNativeProofFlags'].items()),
        'Stored native whole-scene proof flags cannot stand in for fresh decoding')
    require(all(audit[k] is False for k in ('newNativeActorOrAttributeDecodeByAudit',
        'nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted',
        'shippingVerified', 'activeOutputPromoted')), 'Audit evidence tier was promoted')
    require(audit['rootController']['sha256'] == AUDIT_CONTROLLER_SHA,
            'Actual corrected audit controller identity differs')
    return True


def terminal_and_audit(report):
    require_actual_binding()
    require(sha(REPORT) == REPORT_SHA and sha(PROCESS_PATH) == PROCESS_SHA
            and sha(RAW_PATH) == RAW_SHA and sha(ROOT_AUDIT_PATH) == ROOT_AUDIT_SHA,
            'Actual closed native report/process/current-byte audit changed')
    terminal, raw, audit = read(PROCESS_PATH), read(RAW_PATH), read(ROOT_AUDIT_PATH)
    validate_terminal(report, terminal, raw)
    validate_root_audit(audit, report)
    require(sha(terminal['logFile']) == terminal['logSha256']
            and sha(terminal['controller']) == MONITOR_SHA, 'Actual process log/monitor changed')
    for row in (audit['rootController'], audit['byteValidationHelper']):
        path = Path(row['path'])
        require(path.is_absolute() and path.is_file() and not path.is_symlink()
                and sha(path) == row['sha256'] and path.stat().st_size == row['bytes'],
                'Actual audit controller/read-only byte helper changed')
    return audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('report', type=Path)
    args = parser.parse_args()
    require_actual_binding()
    require(args.report.resolve() == REPORT, 'Only exact image-selected R39 candidate report accepted')
    report = read(REPORT)
    terminal_and_audit(report)
    bundle = saved_bundle()
    plan, preflight = (read(checked(report[k])) for k in ('selectedPlan', 'sourcePreflight'))
    print(json.dumps(validate_saved(report, plan, bundle, preflight), sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
