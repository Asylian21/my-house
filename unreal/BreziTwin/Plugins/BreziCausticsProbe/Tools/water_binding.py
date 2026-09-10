"""Bind diagnostic transport to the saved production water graph; never author UE assets.

The historical receiver contract stays immutable. Only its old optics.py source
pin is superseded here; all its geometry/viewpoint pins and exact faces still pass.
"""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path
import struct

from verify_contract import verify, verify_topology

PLUGIN = Path(__file__).resolve().parents[1]
RESOURCE = PLUGIN / 'Resources/active-water-binding.json'
HEADER = PLUGIN / 'Source/BreziCausticsProbe/Private/BreziCausticsWaterBinding.h'
WRITER = 'scripts/unreal/optics.py'
SCENE = 'output/unreal/geometry/scene.json'
OBJ = 'output/unreal/geometry/dom-mm.obj'
MATERIAL = 'unreal/BreziTwin/Content/Brezi/OpticsGenerated/M_PoolWater.uasset'
ASSET = '/Game/Brezi/OpticsGenerated/M_PoolWater.M_PoolWater'
STATUS = 'active-water-binding-source-and-saved-graph-validated'
CONSTANTS = ('WAVES', 'ABSORPTION_PER_METRE', 'SCATTERING_PER_METRE')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path, algorithm='sha256'):
    return hashlib.new(algorithm, Path(path).read_bytes()).hexdigest()


def read_json(path):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key: ' + key)
            result[key] = value
        return result
    def invalid(value):
        raise ValueError('Nonfinite JSON number: ' + value)
    return json.loads(Path(path).read_text(), object_pairs_hook=pairs, parse_constant=invalid)


def finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def f32(value):
    require(finite(value), 'Nonfinite/bool numeric input')
    result = struct.unpack('<f', struct.pack('<f', value))[0]
    require(math.isfinite(result), 'Value outside finite float32 range')
    return result


def source_constants(path):
    found = {}
    for node in ast.parse(Path(path).read_text()).body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in CONSTANTS:
                    require(target.id not in found and len(node.targets) == 1, 'Ambiguous optics literal')
                    found[target.id] = ast.literal_eval(node.value)
    require(set(found) == set(CONSTANTS), 'Missing optics literals')
    validate_waves(found['WAVES'])
    for key in CONSTANTS[1:]:
        require(isinstance(found[key], list) and len(found[key]) == 3 and
                all(finite(x) and x >= 0 for x in found[key]), 'Invalid optical coefficients')
    return found


def validate_waves(waves):
    require(isinstance(waves, list) and len(waves) == 12, 'Active binding requires exactly 12 waves')
    for wave in waves:
        require(isinstance(wave, dict) and set(wave) ==
                {'direction', 'wavelengthMetres', 'amplitudeMetres', 'phaseCycles'}, 'Wave schema differs')
        direction = wave['direction']
        require(isinstance(direction, list) and len(direction) == 2 and all(finite(x) for x in direction)
                and abs(sum(x*x for x in direction) - 1) < 1e-12, 'Wave direction is not a unit UE XY vector')
        require(finite(wave['wavelengthMetres']) and wave['wavelengthMetres'] > 0 and
                finite(wave['amplitudeMetres']) and wave['amplitudeMetres'] >= 0 and
                finite(wave['phaseCycles']) and 0 <= wave['phaseCycles'] < 1, 'Invalid wave units/range')


def expected_rows(waves):
    validate_waves(waves)
    result = []
    for index, wave in enumerate(waves):
        dx, dy = wave['direction']; length = wave['wavelengthMetres']
        slope = 2 * math.pi * wave['amplitudeMetres'] / length
        result.append({'index': index, 'cosinePeriod': 1.0,
                       'positionCyclesPerCm': [f32(dx / (100 * length)), f32(dy / (100 * length)), 0.0],
                       'timeCyclesPerSecond': f32(-math.sqrt(9.81 / (2 * math.pi * length))),
                       'phaseCycles': f32(wave['phaseCycles']),
                       'slopeVector': [f32(-slope * dx), f32(-slope * dy), 0.0]})
    return result


def validate_rows(rows, waves):
    require(isinstance(rows, list) and len(rows) == 12, 'Saved row count differs')
    for row, expected in zip(rows, expected_rows(waves)):
        require(isinstance(row, dict) and set(row) == set(expected), 'Saved row schema differs')
        require(type(row['index']) is int and row['index'] == expected['index'], 'Saved row order/index differs')
        for key in ['positionCyclesPerCm', 'slopeVector']:
            require(isinstance(row[key], list) and len(row[key]) == 3 and all(finite(x) for x in row[key]),
                    'Saved vector schema differs')
        require(all(finite(row[key]) for key in ['cosinePeriod', 'timeCyclesPerSecond', 'phaseCycles']),
                'Saved scalar schema differs')
        require(row == expected, 'Saved graph differs from exact float32 authored values at wave ' + str(row['index']))


def validate_normal(normal, waves):
    require(normal['status'] == 'native-water-normal-graph-readback-validated', 'Native normal status differs')
    for key in ['normalOutputConnected', 'worldSpaceNormal', 'absoluteWorldPositionCm', 'sharedTime', 'defaultChannelsVerified']:
        require(normal[key] is True, 'Native normal policy differs: ' + key)
    for key in ['timeIgnoresPause', 'timePeriodOverride', 'internalNodeNamesUsed', 'renderedVerified']:
        require(normal[key] is False, 'Native normal policy differs: ' + key)
    require(type(normal['cosineCount']) is int and normal['cosineCount'] == 12 and
            type(normal['reachableExpressionCount']) is int and normal['reachableExpressionCount'] == 138,
            'Native normal topology count differs')
    require(normal['initialGradient'] == [0, 0, 0] and normal['upVector'] == [0, 0, 1], 'Normal initial/up vector differs')
    validate_rows(normal['waves'], waves)


def validate_evidence(constants, imported, saved, writer_sha, import_sha):
    require(imported['status'] == 'import-validated' and imported['hostProcess']['code'] == 0 and
            imported['hostProcess']['cleanExit'] is True, 'Import was not successfully closed')
    require(saved['status'] == 'fresh-process-saved-water-graph-validated' and
            all(saved[k] is True for k in ['readOnly', 'freshProcess', 'sourceAssetsUnchanged']) and
            saved['renderedVerified'] is False, 'Missing fresh saved graph proof')
    require(saved['importReceiptSha256'] == import_sha, 'Saved proof belongs to another import')
    optics = imported['optics']
    require(optics['status'] == 'optics-authored' and
            saved['sourceWriterSha256'] == optics['writerSha256'] == writer_sha, 'Stale optics writer pin')
    require(imported['pipelineFiles'][WRITER] == writer_sha, 'Import pipeline optics pin differs')
    water = optics['water']; waves = constants['WAVES']
    require(saved['declaredWaves'] == water['waves'] == waves, 'Source/import/saved authored waves differ')
    require(water['absorptionPerMetre'] == constants['ABSORPTION_PER_METRE'] and
            water['scatteringPerMetre'] == constants['SCATTERING_PER_METRE'], 'Optical coefficients differ')
    require(water['ior'] == 1.333 and water['waterLevelMm'] == -12 and water['displacement'] is False and
            water['nativeCoefficientUnit'] == '1/cm; per-metre parameters multiplied by 0.01', 'Water transport policy differs')
    masters = [m for m in optics['masters'] if m['sourceFamily'] == 'real-pool-water']
    require(len(masters) == 1, 'Ambiguous native water master')
    master = masters[0]
    require(master['asset'] == saved['asset'] == ASSET and master['saved'] is True and
            master['shadingModel'] == 'SingleLayerWater' and master['compileErrors'] == [], 'Native master was not saved/compiled')
    require(master['graph'] == saved['graph'], 'Saved native graph differs from final import graph')
    validate_normal(saved['graph']['waterNormalReadback'], waves)
    require(saved['assetHashes'].get(MATERIAL) == optics['generatedAssetHashes'].get(MATERIAL) ==
            imported['finalAssetHashes'].get(MATERIAL) and MATERIAL in saved['assetHashes'], 'Water material pin differs')


def verify_receiver_geometry(contract, scene, obj_path):
    """Exact current records and ordered OBJ faces; no material/geometry equivalence waiver."""
    result = verify_topology(contract)
    by_id = {obj['id']: obj for obj in scene['objects']}
    require(len(by_id) == len(scene['objects']), 'Duplicate current scene identity')
    ids = {obj['id'] for obj in contract['receiverObjects']}
    for obj in contract['receiverObjects']:
        require(obj['id'] in by_id and obj == {k: by_id[obj['id']][k] for k in obj},
                'Current receiver record differs: ' + obj['id'])
    vertices, actual, current = [], [], None
    counts = dict.fromkeys(ids, 0)
    with Path(obj_path).open() as handle:
        for line in handle:
            fields = line.split()
            if not fields:
                continue
            if fields[0] == 'o':
                current = fields[1]
            elif fields[0] == 'v':
                require(len(fields) == 4, 'Unexpected OBJ vertex format')
                x, y, z = map(float, fields[1:]); vertices.append([x / 1000, -y / 1000, z / 1000])
            elif fields[0] == 'f' and current in ids:
                require(len(fields) == 4, 'Nontriangular receiver source face')
                indices = [int(f.split('/')[0]) for f in fields[1:]]
                require(all(0 < i <= len(vertices) for i in indices), 'Invalid receiver vertex index')
                actual.append({'objectId': current, 'sourceFaceIndex': counts[current],
                               'verticesMetres': [vertices[i-1] for i in indices]})
                counts[current] += 1
    require(actual == contract['triangles'], 'Current OBJ receiver triangles differ')
    return {**result, 'allRetainedRecordsEqual': True, 'allOrderedOBJTrianglesEqual': True,
            'currentSceneObjectCount': len(by_id), 'nativeWorldVerified': False}


def root_path(root, relative):
    require(isinstance(relative, str) and not Path(relative).is_absolute(), 'Expected repo-relative evidence path')
    result = (root / relative).resolve()
    require(result.is_relative_to(root.resolve()), 'Evidence escapes repository root')
    return result


def build_binding(root, import_path, readback_path):
    root = Path(root).resolve()
    def rel(path):
        return str(Path(path).resolve().relative_to(root))
    tracked = {}
    def pin(path):
        path = Path(path).resolve(); tracked[rel(path)] = sha(path)
        return {'path': rel(path), 'sha256': tracked[rel(path)]}
    source = root / WRITER
    imported_ref, saved_ref, writer_ref = pin(import_path), pin(readback_path), pin(source)
    imported, saved = read_json(import_path), read_json(readback_path)
    constants = source_constants(source)
    validate_evidence(constants, imported, saved, writer_ref['sha256'], imported_ref['sha256'])
    historical = verify()  # Unchanged historical pin/topology checker, without its obsolete optics pin.
    receiver_path = PLUGIN / 'Resources/receiver-contract.json'
    contract = read_json(receiver_path)
    for relative, expected in contract['sourceSha256'].items():
        if relative != WRITER:
            require(pin(root_path(root, relative))['sha256'] == expected, 'Stale receiver source: ' + relative)
    require(imported['sourceManifestSha256'] == contract['sourceSha256'][SCENE], 'Imported scene differs from receiver scene')
    source_binding = read_json(PLUGIN / 'Resources/source-binding.json')
    proof_path = root / 'output/unreal/hidden-collision-source-proof.json'
    require(pin(proof_path)['sha256'] == source_binding['canonicalProofSha256'], 'Canonical preservation proof differs')
    proof, scene = read_json(proof_path), read_json(root / SCENE)
    require(proof['status'] == 'canonical-geometry-unchanged-auxiliary-source-captured' and
            proof['everyCanonicalObjectRecordIdentical'] is True and
            proof['canonicalObjects'] == len(scene['objects']) == 1895, 'Canonical preservation proof is invalid')
    geometry = verify_receiver_geometry(contract, scene, root / OBJ)
    for relative, expected in saved['assetHashes'].items():
        require(imported['finalAssetHashes'].get(relative) == expected and
                pin(root_path(root, relative))['sha256'] == expected, 'Saved asset bytes changed: ' + relative)
    for path in [receiver_path, PLUGIN / 'Resources/source-binding.json',
                 PLUGIN / 'Resources/receiver-identity-policy.json',
                 PLUGIN / 'Resources/receiver-identity-test-fixture.json',
                 PLUGIN / 'Source/BreziCausticsProbe/Private/BreziCausticsContract.h']:
        pin(path)
    material = {**pin(root / MATERIAL), 'asset': ASSET, 'sha1': sha(root / MATERIAL, 'sha1'),
                'projectRelativePath': 'Content/Brezi/OpticsGenerated/M_PoolWater.uasset'}
    exporter = pin(Path(__file__))
    binding = {
        'schemaVersion': 1, 'status': STATUS, 'diagnosticOnly': True,
        'receiverContractSha256': historical['contractSha256'], 'waveCount': 12,
        'coordinateSystem': 'unreal-axes-centimetres-for-normal',
        'normalFormula': 'normalize(sum(slopeVector*cos(2*pi*((dot(worldCm,positionCyclesPerCm)+gameTime*timeCyclesPerSecond)+phaseCycles)))+float3(0,0,1))',
        'timePolicy': 'View.GameTime; paused material Time; no period override',
        'authoredWaves': constants['WAVES'], 'savedNormalRows': saved['graph']['waterNormalReadback']['waves'],
        'absorptionPerMetre': constants['ABSORPTION_PER_METRE'],
        'scatteringPerMetre': constants['SCATTERING_PER_METRE'], 'iorAirToWater': 1.333,
        'waterObjectId': contract['waterObjectId'], 'waterMeanPlaneMetres': contract['waterMeanPlaneMetres'],
        'sourceWriter': writer_ref, 'material': material,
        'sourceGeometrySha256': {k: v for k, v in contract['sourceSha256'].items() if k != WRITER},
        'provenance': {'importReport': imported_ref, 'savedReadback': saved_ref, 'exporter': exporter,
                       'receiverGeometry': geometry},
        'fileHashes': dict(sorted(tracked.items())),
        'evidence': {'savedNormalGraphVerified': True, 'opticalCoefficientsSourceAndImportVerified': True,
                     'opticalCoefficientNativeValueReadback': False, 'nativeExecutionPerformedByExporter': False,
                     'gpuNormalArithmeticEquivalenceVerified': False, 'productionTransportVerified': False},
        'limitations': ['Saved float32 graph constants are exact; GPU arithmetic/compiler equivalence is not yet measured.',
                        'Optical coefficients are pinned source/import values, not a new native coefficient getter proof.',
                        'Fixed canonical plane with shading normals; no displaced free surface.',
                        'Receiver source geometry proof does not certify live native primitive/material/visibility state.']}
    for relative, digest in tracked.items():
        require(sha(root_path(root, relative)) == digest, 'Input changed during binding export: ' + relative)
    return binding


def binding_bytes(binding):
    return (json.dumps(binding, ensure_ascii=False, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()


def header_text(raw, binding):
    return ('#pragma once\n// Generated by Tools/water_binding.py; diagnostic saved-water binding only.\n'
            'static constexpr const TCHAR* BreziCausticsWaterBindingSha256 = TEXT("' + hashlib.sha256(raw).hexdigest() + '");\n'
            'static constexpr const TCHAR* BreziCausticsWaterBindingSha1 = TEXT("' + hashlib.sha1(raw).hexdigest() + '");\n'
            'static constexpr const TCHAR* BreziCausticsWaterMaterialSha1 = TEXT("' + binding['material']['sha1'] + '");\n'
            'static constexpr const TCHAR* BreziCausticsWaterMaterialRelativePath = TEXT("' + binding['material']['projectRelativePath'] + '");\n')


def load_binding(path, verify_sources=False, root=None):
    """Accept only the reviewed active bytes. Offline capture checks need no current .uasset/source."""
    raw = Path(path).read_bytes()
    require(raw == RESOURCE.read_bytes(), 'Unreviewed active water binding bytes')
    binding = read_json(path)
    require(HEADER.read_text() == header_text(raw, binding), 'Compiled active water pins differ')
    require(binding['schemaVersion'] == 1 and binding['status'] == STATUS and binding['diagnosticOnly'] is True and
            type(binding['waveCount']) is int and binding['waveCount'] == 12, 'Active binding policy differs')
    require(binding['sourceWriter']['path'] == WRITER and binding['material']['path'] == MATERIAL and
            binding['material']['asset'] == ASSET and
            binding['material']['projectRelativePath'] == 'Content/Brezi/OpticsGenerated/M_PoolWater.uasset',
            'Active binding asset identity differs')
    validate_rows(binding['savedNormalRows'], binding['authoredWaves'])
    require(binding['receiverContractSha256'] == sha(PLUGIN / 'Resources/receiver-contract.json'), 'Receiver binding differs')
    if verify_sources:
        require(root is not None, 'Current-source verification requires an explicit root')
        root = Path(root).resolve(); provenance = binding['provenance']
        expected = build_binding(root, root_path(root, provenance['importReport']['path']),
                                 root_path(root, provenance['savedReadback']['path']))
        require(binding == expected, 'Active binding differs from current source/readback/assets')
    return binding


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', required=True)
    parser.add_argument('--import-report', default='output/unreal/import-report.json')
    parser.add_argument('--saved-readback', default='output/unreal/water-wave-study/saved-water-readback-12.json')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args(); root = Path(args.source_root).resolve()
    if args.check:
        binding = load_binding(RESOURCE, verify_sources=True, root=root)
    else:
        require(not RESOURCE.exists() and not HEADER.exists(), 'Refusing to overwrite reviewed binding/header; preserve and explicitly remove them first')
        binding = build_binding(root, root_path(root, args.import_report), root_path(root, args.saved_readback))
        raw = binding_bytes(binding)
        with RESOURCE.open('xb') as handle:
            handle.write(raw)
        with HEADER.open('x') as handle:
            handle.write(header_text(raw, binding))
    print(json.dumps({'status': 'CPU-active-water-binding-validated', 'waveCount': binding['waveCount'],
                      'bindingSha256': sha(RESOURCE), 'headerSha256': sha(HEADER),
                      'materialSha256': binding['material']['sha256'],
                      'geometry': binding['provenance']['receiverGeometry'], 'nativeExecuted': False}, indent=2))


if __name__ == '__main__':
    main()
