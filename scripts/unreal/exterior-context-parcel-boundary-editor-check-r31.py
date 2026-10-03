"""CPU saved R43b/R2 receipt checker, bound to actual native0 and byte audit.

Reads frozen source arrays and recorded native sidecars; no native call,
historical producer, initial-clone current-map assertion or fresh UObject decode.
"""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from datetime import datetime
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-parcel-boundary-editor-check-r31.py'
GUARD = ROOT/'scripts/unreal/exterior-context-parcel-boundary-guards-r43-r2.py'
GUARD_SHA = '38c9f3cb66e36f10aa935cac0bcda6fd39a329ed1938829ffbd9d4cf750dc9fe'
NATIVE = ROOT/'scripts/unreal/exterior-context-parcel-boundary-native-r43-r2.py'
NATIVE_SHA = '488553a3cdba3963196ad106565a2874d040acf1c9915e97c8f4eb8021bda763'
MATERIAL = ROOT/'scripts/unreal/exterior-context-parcel-boundary-materials-r43.py'
MATERIAL_SHA = 'fad70bfdd0bd7b9eff2ee289f20a47b1c3d717b7bb683eecbe8d59ff72f873d9'
PLAN = ROOT/'output/unreal/exterior-context-parcel-boundary-20261002-r43-native-study-r2/boundary-native-plan-r2.json'
PLAN_SHA = '6a47ca7a3cc74c7a2d52d1d6c3857388c28b49e5afd49ab9f819250dd7979187'
PREFLIGHT = PLAN.parent/'source-preflight/source-preflight.json'
PREFLIGHT_SHA = 'd0119825edb11f0ea0e23773349ea12cb50ca2bb920bad56927a7197d6c98d44'
REPORT = ROOT/'output/unreal/exterior-20261002-r43b/boundary-native-report-r2.json'
REPORT_SHA = '802756b95c06d01351cbdaee7b439ab10728e04f2d884fb971f111e735e9b5d4'
NATIVE_PROCESS_ID = 44798
PROCESS_PATH = REPORT.parent/'garden-boundary-native-r2-process.json'
PROCESS_SHA = '70bb0aa0c745cab27f98169dc25f73c17f94f749e0431250e1be6c5fe283dbac'
RAW_PATH = REPORT.parent/'garden-boundary-native-r2.log.json'
RAW_SHA = '7f7e5c89a31682833cb65e59e3138ca5a1d15c2c4379d28d8393b8c000f74e51'
ROOT_AUDIT = REPORT.parent/'root-native-success-byte-audit-r43b-r2.json'
ROOT_AUDIT_SHA = 'd4dd77489d5e26e533b4f94cd24a15463c1837171f98ee32ccf5bd07b97eb482'
TERMINAL_SOURCE_COUNT = 1343
MONITOR_SHA = 'a7864b6bf3b51e15fda4426b2766021c1c8ea4d43e41a9d94ffeec89f7662006'
SOURCE_COUNT = 1332


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    p = Path(path).resolve()
    return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}


def checked(row):
    require(type(row) is dict and set(row) == {'path', 'sha256', 'bytes'}, 'Exact immutable pin required')
    p = Path(row['path'])
    require(p.is_absolute() and p.resolve() == p and not p.is_symlink() and pin(p) == row,
            'Pinned actual sidecar changed: '+str(p))
    return p


def read(path):
    return json.loads(Path(path).read_text())


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def module(name, path, expected):
    require(sha(path) == expected, 'Frozen pure kernel changed: '+str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


g = module('_r31_frozen_boundary_pure_guard', GUARD, GUARD_SHA)


def actual_binding_required():
    require(all(v is not None for v in (REPORT_SHA, NATIVE_PROCESS_ID, PROCESS_PATH, PROCESS_SHA,
                RAW_PATH, RAW_SHA, ROOT_AUDIT, ROOT_AUDIT_SHA, TERMINAL_SOURCE_COUNT)),
            'R31 is unbound until actual native0 and independent current-byte closure')


def report_header(report, plan, source, preflight):
    actual_binding_required()
    require(report['schema'] == g.SCHEMA and report['schemaVersion'] == 2
            and report['owner'] == g.NATIVE_OWNER
            and report['status'] == 'verified-saved-three-authored-open-boundary-masters'
            and report['nativeProcessId'] == NATIVE_PROCESS_ID
            and report['project'] == str(g.PROJECT), 'Only exact successful saved R43 report accepted')
    for key in ('nativeApplied', 'savedMapUnloadedReloaded', 'sourceInputsUnchanged',
                'allOriginal5368ActorsAnd2329RawControlsExact', 'allOriginal69GraphsAuxObservedUsageExact',
                'allOriginal108VisibleTextureSettingsExact', 'newActorIdentityNavDrawShadowPolicySourceTemplateVerified'):
        require(report[key] is True, 'Required actual native proof absent: '+key)
    for key in ('oldActorInstanceMaterialOrCollisionSettersCalled', 'providerGeometryClaimed',
                'sourcePixelsEdited', 'nativeNormalTangentNumericReadbackPerformed', 'nativeAppearanceAccepted',
                'nativeCollisionOrContactVerified', 'legalFencePlacementOrOwnershipClaimed',
                'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified', 'activeOutputPromoted'):
        require(report[key] is False, 'Recorded proof tier or scope changed: '+key)
    require(report['activeDesign'] == 'C/B/B' and report['setbacksMm'] == [3000, 3000], 'Design changed')
    require(report['selectedPlan'] == preflight['selectedPlan'] == pin(PLAN)
            and report['sourcePreflight'] == pin(PREFLIGHT)
            and report['sourceProposal'] == plan['sourcePlan'] == pin(g.SOURCE)
            and report['sourceGeometry'] == plan['sourceGeometry'] == source['geometry']
            and report['sourceGlb'] == plan['sourceGlb'], 'Exact source/plan/export provenance required')
    require(report['binding'] == plan['binding'] == preflight['binding']
            and report['actualCounts'] == plan['expectedCounts'] == preflight['expectedCounts'] == g.COUNTS,
            'Native/source whole-scene contract changed')
    require(report['repairSchema'] == plan['repairSchema'] == preflight['repairSchema'] == g.REPAIR_SCHEMA
            and report['actorSpawnRepairEvidence'] == plan['actorSpawnRepairEvidence']
            == preflight['actorSpawnRepairEvidence'] == plan['binding']['actorSpawnRepairEvidence'],
            'Exact class-spawn failure/repair provenance required')
    evidence = report['actorSpawnRepairEvidence']
    require(evidence['actualFailedProcessId'] == 36431 and evidence['actualFailedExitCode'] == 1
            and evidence['actualSavedMapProduced'] is False and evidence['duplicationStackObserved'] is True
            and evidence['newRouteObservedInThisBoundaryNative'] is False,
            'Historical failed evidence cannot claim current success')
    binding = plan['binding']
    for key, target in (('baseNativeReport', 'selectedNativeReport'), ('baseNativeProcess', 'selectedNativeProcess'),
                        ('baseCurrentByteAudit', 'selectedCurrentByteAudit'), ('projectClone', 'projectClone'),
                        ('rootSourceDecision', 'rootSourceDecision')):
        require(report[key] == binding[target], 'Explicit selected source/report route differs: '+key)
    require(report['inputFiles'] == preflight['inputFiles']
            == {**plan['inputFiles'], str(PLAN): PLAN_SHA} and len(report['inputFiles']) == SOURCE_COUNT,
            '1332 consumed source pins must remain separate from terminal closure')
    require(preflight['tests']['exitCode'] == 0 and preflight['tests']['testCount'] == 5
            and preflight['nativeExecuted'] is False and preflight['gpuExecuted'] is False
            and report['moduleOrderWitness'] == preflight['moduleOrderWitness'], 'Executed preflight/order required')
    checked(preflight['tests']['log'])
    require(report['newPackages'] == plan['expectedNewPackageAssets'] == g.expected_new_packages(), '15 package budget changed')


def source_packet(plan, source):
    require(pin(g.SOURCE)['sha256'] == g.SOURCE_SHA and source == read(g.SOURCE), 'Exact corrected R2 source required')
    geometry = read(checked(source['geometry']))
    require(source['geometry']['sha256'] == g.GEOMETRY_SHA, 'Corrected P/N/UV source identity required')
    rows = g.export_rows(geometry)
    require(digest(rows) == plan['exportRowsSha256'], 'Re-derived encoded source recipe differs')
    verify_encoded_glb(checked(plan['sourceGlb']).read_bytes(), rows)
    base = read(checked(plan['binding']['selectedNativeReport']))
    require(base['nativeProcessId'] == 94572 and base['status'] == 'verified-saved-six-whole-original-neighbor-prop-assemblies'
            and base['nativeApplied'] is True and base['savedMapUnloadedReloaded'] is True, 'Selected actual R39c required')
    witness = read(checked(base['savedActorWitness']))
    require(len(witness) == 5368 and digest(witness) == base['savedActorWitnessSha256'], 'Full selected witness required')
    require(plan['newActorTemplate'] == witness[g.TEMPLATE], 'Immutable same-world template differs')
    return {'source': {'plan': source, 'geometry': geometry, 'exportRows': rows},
            'base': {'report': base, 'savedWitness': witness, 'template': witness[g.TEMPLATE]},
            'binding': plan['binding']}


def verify_encoded_glb(raw, rows):
    require(struct.unpack_from('<III', raw) == (0x46546c67, 2, len(raw)), 'Source GLB2 container differs')
    size, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4e4f534a, 'Source JSON required')
    doc = json.loads(raw[20:20+size]); offset = 20+size
    length, kind = struct.unpack_from('<II', raw, offset)
    require(kind == 0x004e4942 and offset+8+length == len(raw), 'Complete original export binary required')
    binary = raw[offset+8:]
    require(doc['nodes'] == [{'name': row['id'], 'mesh': i} for i, row in enumerate(rows)]
            and doc['scenes'] == [{'nodes': [0, 1, 2]}] and doc['scene'] == 0
            and len(doc['meshes']) == 3, 'Exactly three nonmirrored identity source nodes required')
    def values(index, component, arity):
        a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
        require(a['componentType'] == component and a['type'] == {1: 'SCALAR', 2: 'VEC2', 3: 'VEC3'}[arity]
                and v['buffer'] == 0 and not a.get('normalized') and 'sparse' not in a, 'Exact dense accessor required')
        fmt = '<'+('f' if component == 5126 else 'I')*arity
        stride = v.get('byteStride', struct.calcsize(fmt)); start = v.get('byteOffset', 0)+a.get('byteOffset', 0)
        require(stride == struct.calcsize(fmt) and start+a['count']*stride <= len(binary), 'Written accessor range differs')
        result = [list(struct.unpack_from(fmt, binary, start+i*stride)) for i in range(a['count'])]
        return [r[0] for r in result] if arity == 1 else result
    for mesh, row in zip(doc['meshes'], rows):
        require(mesh['name'] == row['id'] and len(mesh['primitives']) == 1, 'One exact authored source master required')
        p = mesh['primitives'][0]
        require(p['mode'] == 4 and set(p['attributes']) == {'POSITION', 'NORMAL', 'TEXCOORD_0'}, 'Authored topology/attrs differ')
        for name, field, arity in (('POSITION', 'gltfPositions', 3), ('NORMAL', 'gltfNormals', 3), ('TEXCOORD_0', 'uv0', 2)):
            g.exact(values(p['attributes'][name], 5126, arity), row[field], 'Complete written source differs: '+name)
        g.exact(values(p['indices'], 5125, 1), row['indices'], 'Written source indices/winding differ')


def validate_geometry(records, rows):
    n = module('_r31_frozen_corner_kernel', NATIVE, NATIVE_SHA)
    require(set(records) == set(g.MATERIAL_ROLES), 'Three native corner proof records required')
    for row in rows:
        got = records[row['material']]
        require(got['id'] == row['id'] and got['material'] == row['material']
                and got['triangles'] == len(row['indices'])//3
                and got['sourceGeometrySha256'] == g.GEOMETRY_SHA
                and got['fullOrderedNativeF32PositionUv0SectionWindingSha256'] == digest(n.expected_corners(row)),
                'Full encoded P/UV0/order/winding receipt differs')
        name = 'boundary_'+row['material']+'_r43'
        require(got['asset'] == g.PREFIX+'/Geometry/StaticMeshes/'+name+'.'+name
                and got['sourceNormalsRetainedInGlb'] is True
                and all(got[k] is False for k in ('nativeNormalTangentNumericReadbackPerformed',
                    'providerGeometryClaimed', 'nativeAppearanceOrContactAccepted')), 'Corner receipt was promoted')
    require(sum(v['triangles'] for v in records.values()) == 12566, 'Full source triangle census differs')


def validate_old_assets(report, bundle):
    base = bundle['base']['report']
    materials = read(checked(report['originalMaterialWitnessBefore']))
    saved_materials = read(checked(report['originalMaterialWitnessSaved']))
    g.exact(materials, saved_materials, 'Every original graph/aux/observed usage must survive saved reload')
    original = read(checked(base['originalMaterialWitnessSaved']))
    require(len(original) == 66 and len(materials) == 69, 'Full original graph scope differs')
    # The two R38-owned usage rows were first observed in R39. In R43 their
    # recorded values are the baseline; only that provenance marker advances.
    recorded = {k: {**v, 'usagePreviouslyRecorded': True} for k, v in original.items()}
    g.exact({k: materials[k] for k in original}, recorded, 'Recorded66 original graphs/aux/usage changed')
    for source in base['materialReport']['materials'].values():
        row = materials[source['asset']]
        g.exact(row['graph'], source['graph'], 'Three selected R39 new full graphs changed')
        require(row['reader'] == 'basic' and row['graphSha256'] == source['graphSha256'] == digest(row['graph'])
                and row['metadata'] == source['metadata'] and row['usagePreviouslyRecorded'] is False
                and row['usage']['instancedStaticMeshes'] is True, 'Selected R39 material proof differs')
    textures = read(checked(report['originalTextureWitnessBefore']))
    g.exact(textures, read(checked(report['originalTextureWitnessSaved'])), 'All108 visible24 texture settings changed')
    old = read(checked(base['originalTextureWitnessSaved']))
    require(len(old) == 97 and len(textures) == 108, 'Original visible texture scope differs')
    g.exact({k: textures[k] for k in old}, old, 'All97 original complete texture settings differ')
    for material in base['materialReport']['materials'].values():
        for texture in material['textures'].values():
            row = textures[texture['asset']]
            g.texture_subset(row, texture['snapshot'])
            require(row['selectedMetadata'] == texture['metadata'] and len(row['values']) == 24,
                    'Original11 source-map metadata/visible field count differs')
    return materials, textures


def validate_raw(report, bundle, saved):
    before = read(checked(report['rawInstanceControlsBefore']))
    g.exact(before, read(checked(report['rawInstanceControlsSaved'])), 'All2329 stored matrix/seed/custom controls changed')
    base = bundle['base']['report']; old = read(checked(base['rawInstanceControlsSaved']))
    require(len(old) == 2325 and len(before) == 2329 and sum(v['instances'] for v in before.values()) == 678205,
            'Exact whole-scene raw census required')
    g.exact({k: before[k] for k in old}, old, 'Original2325 source-bound raw controls changed')
    measurements = read(checked(base['newSourceNativeMeasurements']))
    for key, group in base['newOwnedGroups'].items():
        comp = saved[group['actor']]['components'][0]; m = measurements[key]
        require(comp['path'] in before and comp['instanceCount'] == group['instances'] == len(m['storedMatrices'])
                and comp['orderedInstanceTransformsSha256'] == digest(m['recoveredValues']), 'Original eight props frames/order differ')
        raw = b''.join(struct.pack('<d', float(v)) for matrix in m['storedMatrices'] for plane in matrix for v in plane)
        require(before[comp['path']]['rawMatrixBinary64Sha256'] == hashlib.sha256(raw).hexdigest()
                and before[comp['path']]['numCustomDataFloats'] == 0
                and before[comp['path']]['customDataSha256'] == digest([]), 'Original props stored raw matrices/custom changed')
    return before


def validate_spawn(observed, bundle, groups):
    require(observed['owner'] == g.NATIVE_OWNER and observed['spawnRoute'] == 'EditorActorSubsystem.spawn_actor_from_class'
            and observed['sourceTemplate'] == g.TEMPLATE and observed['numericZeroNormalizationPerformed'] is False
            and observed['originalActorSettersCalled'] is False, 'Actual class-spawn provenance differs')
    rows = observed['actualObservations']
    require(len(rows) == 3 and [r['role'] for r in rows] == list(g.MATERIAL_ROLES), 'Exactly three ordered spawn observations required')
    for row in rows:
        require(row['actor'] == groups[row['role']]['actor'] and row['actor'] not in bundle['base']['savedWitness']
                and row['class'] == '/Script/Engine.StaticMeshActor'
                and row['componentClass'] == '/Script/Engine.StaticMeshComponent'
                and row['existingSourceActorReturned'] is False and row['actorTransformSettersCalled'] is False,
                'Fresh observed StaticMeshActor root differs')
        g.exact(row['actorTransform'], bundle['base']['template']['transform'], 'Spawned actor double identity differs')
        g.exact(row['componentTransform'], bundle['base']['template']['components'][0]['transform'],
                'Spawned component double identity differs')


def new_actor_expected(bundle, role, row, geometry, material):
    require(row['collision'] == 'NoCollision' and row['identityFromAuthenticatedSourceTemplate'] is True
            and row['createdByObservedClassSpawn'] is True, 'Only observed visual identity additions allowed')
    require(row['mesh'] == geometry['asset'] and row['material'] == material['asset'],
            'New actor must bind the proved own geometry and material')
    return g.added_expected(bundle, role, row['actor'], row['mesh'], row['material'])


def validate_saved(report, plan, source, preflight):
    report_header(report, plan, source, preflight)
    bundle = source_packet(plan, source)
    before = read(checked(report['beforeActorWitness']))
    expected_record = read(checked(report['expectedActorWitness']))
    saved = read(checked(report['savedActorWitness']))
    g.exact(before, bundle['base']['savedWitness'], 'Every selected original5368 actor must remain exact')
    require(set(report['newOwnedActors']) == set(g.MATERIAL_ROLES), 'Exactly three new roles required')
    validate_spawn(read(checked(report['newActorSpawnObservations'])), bundle, report['newOwnedActors'])
    added = {}
    for role, row in report['newOwnedActors'].items():
        added[row['actor']] = new_actor_expected(bundle, role, row, report['nativeGeometryReadback'][role],
                                                report['materialReport']['materials'][role])
    require(len(added) == 3 and not set(added)&set(before), 'Distinct fresh actor identities required')
    expected = copy.deepcopy(before); expected.update(added)
    g.exact(expected_record, expected, 'Whole source-template counterfactual differs')
    g.exact(saved, expected, 'Full saved5371 witness must equal independently reconstructed source expectation')
    for key, value in (('beforeActorWitnessSha256', before), ('expectedActorWitnessSha256', expected_record),
                       ('savedActorWitnessSha256', saved)):
        require(report[key] == digest(value), 'Canonical actor receipt hash differs: '+key)
    raw = validate_raw(report, bundle, saved)
    materials, textures = validate_old_assets(report, bundle)
    require(report['nativeGeometryReadback'] == read(checked(report['nativeGeometryReadbackReceipt'])), 'Native corner sidecar differs')
    validate_geometry(report['nativeGeometryReadback'], bundle['source']['exportRows'])
    imported = read(checked(report['importReadback']))
    require(imported['proofs'] == report['nativeGeometryReadback'] and imported['sourceCompleteTriangles'] == 12566
            and imported['nativeNormalTangentNumericReadbackPerformed'] is False, 'Pre-actor full mesh proof differs')
    checked(imported['temporaryActorInventory'])
    require(report['materialReport'] == read(checked(report['newMaterialReport'])), 'Own saved material sidecar differs')
    validate_materials(report['materialReport'], source, plan['binding'])
    content = read(checked(report['afterContentInventory']))
    base_content = read(checked(bundle['base']['report']['afterContentInventory']))
    require(g.validate_content_delta(base_content, content) == report['assetDelta'], 'Map-only15 package delta differs')
    require(report['protectedProjectProof'] == bundle['base']['report']['protectedProjectProof'], 'Protected132 provenance differs')
    return {'mode': 'saved-three-authored-open-boundary-masters', 'nativeProcessId': report['nativeProcessId'],
            'originalActors': len(before), 'savedActors': len(saved), 'newActors': len(added),
            'fullHismComponents': len(raw), 'fullHismInstances': sum(v['instances'] for v in raw.values()),
            'materialGraphs': len(materials)+3, 'textureObjects': len(textures)+6,
            'fullNativeF32PositionUv0SectionWindingProofTriangles': 12566,
            'newPackages': 15, 'contentFiles': len(content), 'protectedFiles': 132,
            'wholeActorCounterfactualValidated': True, 'allOriginalRawMatricesMainSeedAndCustomBeforeSavedExact': True,
            'newClassSpawnObservedExactSourceTemplateIdentity': True,
            'freshNativeActorOrGeometryDecodePerformedByCpuChecker': False,
            'nativeNormalTangentNumericReadbackPerformed': False, 'nativeCollisionOrContactVerified': False,
            'legalFencePlacementOrOwnershipClaimed': False, 'nativeAppearanceAccepted': False,
            'fullPhotorealismAccepted': False, 'performanceAccepted': False,
            'shippingVerified': False, 'activeOutputPromoted': False}


def validate_materials(built, source, binding):
    maps = module('_r31_frozen_material_shape', MATERIAL, MATERIAL_SHA)
    require(built['schema'] == maps.SCHEMA and built['schemaVersion'] == 1 and built['owner'] == maps.OWNER
            and built['nativeBinding'] == binding and built['sourcePlan'] == pin(g.SOURCE)
            and built['materialCount'] == 3 and built['textureObjectCount'] == 6
            and set(built['materials']) == set(g.MATERIAL_ROLES), 'Three complete new material receipts required')
    require(all(built[k] is False for k in maps.LIMITS), 'Material source/readback tier changed')
    for role, row in built['materials'].items():
        asset, paths = maps.assets(role); recipe = source['materials'][role]
        require(row['asset'] == asset and row['recipe'] == recipe and row['compileErrors'] == []
                and row['graphSha256'] == digest(row['graph']), 'Owned graph source/compile receipt differs')
        require(maps.validate_graph(row['graph'], role, recipe, paths) == row['graphAudit'], 'Own full source graph differs')
        flags = row['graph']['flags']
        require(row['policy'] == flags and 'BLEND_OPAQUE' in flags['blend_mode']
                and 'DEFAULT_LIT' in flags['shading_model'] and flags['two_sided'] is False
                and flags['tangent_space_normal'] is True and flags['use_material_attributes'] is False,
                'Opaque DefaultLit own policy differs')
        expected_meta = {'BreziGeneratedBy': maps.OWNER, 'BreziSourcePlanSha256': g.SOURCE_SHA,
                         'BreziR43Role': role, 'BreziSourceLicense': 'CC0-1.0' if role != 'metal' else 'own-artistic-material'}
        require(row['metadata'] == expected_meta and set(row['textures']) == set(paths), 'Own metadata/maps differ')
        for channel, texture in row['textures'].items():
            snapshot = texture['snapshot']; values = snapshot['values']; original = recipe['maps'][channel]
            require(texture['asset'] == paths[channel] and texture['source'] == original
                    and texture['sourceJpg'] == maps.jpg_header(original) and len(values) == 24,
                    'Untouched original texture source differs')
            require(snapshot['size'] == [2048, 2048] and snapshot['downscale'] == {'default': 1., 'perPlatform': {}}
                    and snapshot['alphaCoverageThresholds'] == [0., 0., 0., 0.], 'Complete original texture policy differs')
            # Policy strings come from the actual enum receipt; scalar values remain explicit.
            enums = built['nativeEnumPreflight']
            expected_enums = {'TextureCompressionSettings.TCDefault': '<TextureCompressionSettings.TC_DEFAULT: 0>',
                'TextureCompressionSettings.TCNormalmap': '<TextureCompressionSettings.TC_NORMALMAP: 1>',
                'TextureCompressionSettings.TCMasks': '<TextureCompressionSettings.TC_MASKS: 2>',
                'TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP': '<TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP: 0>',
                'TextureFilter.TF_DEFAULT': '<TextureFilter.TF_DEFAULT: 3>',
                'TextureAddress.TA_WRAP': '<TextureAddress.TA_WRAP: 0>',
                'TexturePowerOfTwoSetting.NONE': '<TexturePowerOfTwoSetting.NONE: 0>',
                'TextureSourceEncoding.TSESRGB': '<TextureSourceEncoding.TSE_S_RGB: 2>',
                'TextureSourceEncoding.TSENONE': '<TextureSourceEncoding.TSE_NONE: 0>'}
            require(all(enums[k] == v for k, v in expected_enums.items()), 'Recorded native original-map enum policy differs')
            wanted = {'srgb': channel == 'diffuse', 'flip_green_channel': channel == 'normal',
                'compression_settings': enums['TextureCompressionSettings.'+('TCDefault' if channel == 'diffuse' else 'TCNormalmap' if channel == 'normal' else 'TCMasks')],
                'mip_gen_settings': enums['TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP'],
                'filter': enums['TextureFilter.TF_DEFAULT'], 'address_x': enums['TextureAddress.TA_WRAP'],
                'address_y': enums['TextureAddress.TA_WRAP'], 'power_of_two_mode': enums['TexturePowerOfTwoSetting.NONE'],
                'resize_during_build_x': 0, 'resize_during_build_y': 0, 'lod_bias': 0, 'max_texture_size': 0,
                'never_stream': False, 'virtual_texture_streaming': False, 'do_scale_mips_for_alpha_coverage': False,
                'adjust_brightness': 1., 'adjust_brightness_curve': 1., 'adjust_vibrance': 0., 'adjust_saturation': 1.,
                'adjust_rgb_curve': 1., 'adjust_hue': 0., 'adjust_min_alpha': 0., 'adjust_max_alpha': 1., 'chroma_key_texture': False}
            require(values == wanted and snapshot['sourceEncoding'] == enums['TextureSourceEncoding.'+('TSESRGB' if channel == 'diffuse' else 'TSENONE')],
                    'Visible24 original photo settings differ')
            require(texture['metadata'] == {**expected_meta, 'BreziR43Role': role+':'+channel,
                    'BreziSourceSha256': original['sha256']}, 'Own untouched photo metadata differs')
    packages = sorted([asset for role in g.MATERIAL_ROLES for asset in [maps.assets(role)[0], *maps.assets(role)[1].values()]])
    require(built['newPackageAssets'] == packages, 'Only3 graphs/6 original photo packages allowed')


def terminal_and_audit(report):
    actual_binding_required()
    require(sha(PROCESS_PATH) == PROCESS_SHA and sha(RAW_PATH) == RAW_SHA and sha(ROOT_AUDIT) == ROOT_AUDIT_SHA,
            'Actual terminal/current-byte pins differ')
    process, raw, audit = read(PROCESS_PATH), read(RAW_PATH), read(ROOT_AUDIT)
    validate_terminal(report, process, raw)
    validate_root_audit(audit, report)
    return audit


def validate_terminal(report, process, raw):
    require(raw['pid'] == report['nativeProcessId'] == NATIVE_PROCESS_ID and raw['code'] == 0 and raw['signal'] is None
            and raw['command'] == '/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd'
            and raw['args'][0] == str(g.PROJECT/'BreziTwin.uproject'), 'Exact own closed native0 process required')
    require(datetime.fromisoformat(raw['endedAt']) >= datetime.fromisoformat(raw['startedAt']), 'Native end must follow start')
    log = REPORT.parent/'garden-boundary-native-r2.log'
    require(all(v in raw['args'] for v in ('-run=pythonscript', '-nullrhi', '-script='+str(NATIVE), '-abslog='+str(log)))
            and process['processFile'] == str(RAW_PATH) and process['processFileSha256'] == RAW_SHA
            and process['logFile'] == str(log) and process['reportSha256'] == REPORT_SHA
            and process['sourcePinsUnchangedAfterNative'] is True
            and process['controllerSha256BeforeNative'] == process['controllerSha256AfterNative'] == MONITOR_SHA,
            'Actual native command/controller/report closure differs')
    require(len(process['sourcePinsBeforeNative']) == TERMINAL_SOURCE_COUNT and len(report['inputFiles']) == SOURCE_COUNT
            and all(process['sourcePinsBeforeNative'].get(k) == v for k, v in report['inputFiles'].items()),
            '1332 consumed source versus1343 terminal pins must remain explicit')


def validate_root_audit(audit, report):
    require(audit['schema'] == 'brezi-r43b-root-saved-authored-open-boundaries-byte-audit-r2'
            and audit['schemaVersion'] == 2 and audit['status']
            == 'verified-saved-native0-only-original-map-changed-15-new-owned-packages-all1343-frozen-pins-exact'
            and audit['nativeReport'] == pin(REPORT) and audit['nativeProcess'] == pin(PROCESS_PATH)
            and audit['rawNativeProcess'] == pin(RAW_PATH) and audit['nativeProcessId'] == NATIVE_PROCESS_ID
            and audit['exitCode'] == audit['rootSessionClosedExitCode'] == 0 and audit['nativeIdleAfter'] == [],
            'Exact independently completed actual root byte audit required')
    require(audit['project'] == str(g.PROJECT) and audit['projectClone'] == report['projectClone']
            and audit['currentContentInventory'] == report['afterContentInventory']
            and audit['currentProtectedProof'] == report['protectedProjectProof']
            and audit['currentContentFiles'] == 4139 and audit['currentProtectedFiles'] == 132
            and audit['currentProjectFiles'] == 4271 and audit['actualCounts'] == report['actualCounts'] == g.COUNTS,
            'Actual current4139+132 source/current scope differs')
    for key in ('candidateOriginal4255NonMapFilesExact', 'onlyOriginalMapChanged', 'selectedR39cAll4256FilesExact',
                'initialIndependentCloneRowsStillIndependent', 'all1343FrozenSourcePinsExact',
                'all1332PreflightSourcePinsExact', 'failedAttemptEvidenceRetained'):
        require(audit[key] is True, 'Required current-byte evidence absent: '+key)
    require(audit['newRelativeContentFiles'] == report['assetDelta']['newRelativeFiles']
            and audit['newOwnedPackageTypes'] == {'meshes': 3, 'materialGraphs': 3, 'originalTextureObjects': 6, 'pipelines': 3}
            and audit['newActorSpawnObservations'] == report['newActorSpawnObservations'], 'Only15 packages/three spawn receipts permitted')
    wanted = ('allOriginal5368ActorsAnd2329RawControlsExact', 'allOriginal69GraphsAuxObservedUsageExact',
              'allOriginal108VisibleTextureSettingsExact', 'newActorIdentityNavDrawShadowPolicySourceTemplateVerified')
    require(set(audit['savedNativeProofFlags']) == set(wanted)
            and all(audit['savedNativeProofFlags'][k] is True and report[k] is True for k in wanted),
            'Stored native proof flags remain separate from CPU decoding')
    for key in ('newNativeActorOrAttributeDecodeByAudit', 'nativeAppearanceAccepted', 'fullPhotorealismAccepted',
                'performanceAccepted', 'shippingVerified', 'activeOutputPromoted'):
        require(audit[key] is False, 'Audit evidence tier changed')


def main():
    p = argparse.ArgumentParser(); p.add_argument('report', type=Path); args = p.parse_args()
    actual_binding_required()
    require(args.report.resolve() == REPORT and sha(REPORT) == REPORT_SHA
            and sha(PLAN) == PLAN_SHA and sha(PREFLIGHT) == PREFLIGHT_SHA, 'Exact actual saved report/source required')
    report = read(REPORT); terminal_and_audit(report)
    summary = validate_saved(report, read(PLAN), read(g.SOURCE), read(PREFLIGHT))
    print(json.dumps(summary, sort_keys=True, allow_nan=False))


if __name__ == '__main__':
    main()
