"""Validate an actual GPU capture against independent double-precision first-hit rays.

python3 <plugin>/Tools/validate_capture.py /absolute/capture/dir
No GPU/Unreal calls. Failed validation always invalidates an earlier success receipt.
"""
import hashlib
import importlib.util
import json
import math
import struct
import sys
from collections import Counter
from pathlib import Path
BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('receiver_reference', BASE / 'receiver_reference.py')
ref = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ref)
identity_spec = importlib.util.spec_from_file_location('receiver_identity_policy', BASE / 'identity_policy.py')
identity = importlib.util.module_from_spec(identity_spec)
identity_spec.loader.exec_module(identity)
water_spec = importlib.util.spec_from_file_location('water_binding', BASE / 'water_binding.py')
water = importlib.util.module_from_spec(water_spec)
water_spec.loader.exec_module(water)
# Deliberately independent of the helper's pin: policy expansion needs explicit review here too.
REVIEWED_IDENTITY_POLICY_SHA256 = 'eebb440994ea88ed58a358e3412b5c72cf4ea72fffb701186ac904dbed17bd43'
UNEXPLAINED_IDENTITY_THRESHOLD = 0.001


def load_identity_policy(contract_path):
    policy_path = BASE.parent / 'Resources/receiver-identity-policy.json'
    policy_hash = hashlib.sha256(policy_path.read_bytes()).hexdigest()
    require(policy_hash == REVIEWED_IDENTITY_POLICY_SHA256, 'Unreviewed identity policy bytes in validator')
    require(identity.REVIEWED_POLICY_SHA256 == REVIEWED_IDENTITY_POLICY_SHA256,
            'Independent identity policy pins disagree')
    policy = identity.IdentityPolicy(contract_path, policy_path, ref)
    require(policy.policy['unexplainedMismatchThreshold'] == UNEXPLAINED_IDENTITY_THRESHOLD,
            'Unexplained identity mismatch threshold changed')
    return policy

def require(condition, message):
    if not condition:
        raise AssertionError(message)


def _validate(directory, allow_synthetic=False):
    directory = Path(directory)
    meta = json.loads((directory / 'capture.json').read_text())
    contract = json.loads((directory / 'receiver-contract.json').read_text())
    binding = json.loads((BASE.parent / 'Resources/source-binding.json').read_text())
    contract_hash = hashlib.sha256((directory / 'receiver-contract.json').read_bytes()).hexdigest()
    require(contract_hash == binding['contractSha256'], 'Capture receiver is not the compiled reviewed contract')
    require(meta.get('sourceContractSha256') == contract_hash, 'Capture source binding is absent or stale')
    identity_policy = load_identity_policy(directory / 'receiver-contract.json')
    # Historical captures retain their frozen four-wave contract. Current captures
    # must explicitly carry the separately reviewed saved-material binding.
    water_path = directory / 'active-water-binding.json'
    has_water_metadata = 'waterBindingSha256' in meta
    require(water_path.is_file() == has_water_metadata, 'Missing water binding or attempted legacy downgrade')
    water_state = None
    if has_water_metadata:
        water_state = water.load_binding(water_path, verify_sources=False)
        require(meta['waterBindingSha256'] == hashlib.sha256(water_path.read_bytes()).hexdigest(), 'Capture water bytes differ from metadata')
        require(water_state['receiverContractSha256'] == contract_hash, 'Water binding names another receiver')
        require(meta.get('waveCount') == water_state['waveCount'] == 12, 'Current wave count differs')
    else:
        require('waveCount' not in meta, 'Wave metadata without reviewed binding')
    optical_state = water_state if water_state else contract
    require(meta.get('syntheticCPUFixture') is not True or allow_synthetic, 'Synthetic fixture cannot be claimed as native GPU evidence')
    require(meta.get('finiteSolarDiskImplemented') is False, 'Validation condition failed')
    require(contract['coordinateSystem'] == 'unreal-axes-metres' and contract['iorAirToWater'] == 1.333, 'Validation condition failed')
    require(meta['productionLightingBound'] is False and meta['sunVisibilityImplemented'] is False, 'Validation condition failed')
    (nx, ny) = meta['launchSize']
    (ax, ay) = meta['atlasSize']
    require(all((type(v) is int and 0 < v <= 2048 for v in [nx, ny, ax, ay])), 'Invalid or unbounded dimensions')
    require(meta.get('syntheticCPUFixture') is True or [nx, ny, ax, ay] == [512, 230, 512, 256], 'Native launch/atlas dimensions changed')
    require(math.isfinite(meta['shaderTimeSeconds']) and len(meta['sunRayDirection']) == 3 and all((math.isfinite(v) for v in meta['sunRayDirection'])), 'Validation condition failed')
    objects = contract['receiverObjects']
    ids = [r['id'] for r in objects]
    floor_index = ids.index('DOM_01720')
    floor = objects[floor_index]
    (low, high) = (floor['boundsMm']['min'], floor['boundsMm']['max'])
    (x0, x1) = (low[0] / 1000, high[0] / 1000)
    (y0, y1) = (-high[1] / 1000, -low[1] / 1000)
    z = contract['waterMeanPlaneMetres']
    zf = high[2] / 1000
    raw = (directory / 'photons-f32le.bin').read_bytes()
    require(meta['photonStrideBytes'] == 48 and len(raw) == nx * ny * 48, 'Photon length/stride')
    atlas_raw = (directory / 'atlas-rgba16f-le.bin').read_bytes()
    require(len(atlas_raw) == ax * ay * 8, 'Atlas length')
    photons = list(struct.iter_unpack('<12f', raw))
    atlas = list(struct.iter_unpack('<4e', atlas_raw))
    require(all((math.isfinite(v) for p in photons for v in p)), 'Nonfinite photon')
    require(all((math.isfinite(v) and v >= 0 for p in atlas for v in p)), 'Nonfinite or negative HDR atlas')
    triangles = []
    for t in contract['triangles']:
        (a, b, c) = t['verticesMetres']
        triangles.append({'sourceObjectId': t['objectId'], 'sourceFaceIndex': t['sourceFaceIndex'], 'verticesMetres': [a, b, c], 'a': a, 'e1': ref.sub(b, a), 'e2': ref.sub(c, a), 'low': tuple((min((v[i] for v in [a, b, c])) for i in range(3))), 'high': tuple((max((v[i] for v in [a, b, c])) for i in range(3)))})
    bvh = ref.BVH(triangles)
    incident = ref.unit(meta['sunRayDirection'])
    require(incident[2] < 0, 'Validate daylight separately from upward/disabled probes')
    seconds = meta['shaderTimeSeconds']
    require(all((abs(p[11] - seconds) < 1e-06 for p in photons)), 'Mixed shader times')
    extinction = [a + s for (a, s) in zip(optical_state['absorptionPerMetre'], optical_state['scatteringPerMetre'])]
    area = (x1 - x0) * (y1 - y0)
    pixel_area = area / (ax * ay)
    incoming = -incident[2] * area
    packet = incoming / (nx * ny)
    counts = Counter()
    cpu_counts = Counter()
    mismatch = 0
    listed_ambiguities = []
    unexplained_mismatches = []
    max_hit_error = 0
    max_fresnel_error = 0
    max_extinction_error = 0
    max_path_error = 0
    received = [0.0, 0.0, 0.0]
    reflected = 0.0
    extinguished = [0.0, 0.0, 0.0]
    floor_flux = [0.0, 0.0, 0.0]
    cpu_floor_flux = [0.0, 0.0, 0.0]
    reconstructed = [[0.0, 0.0, 0.0] for _ in range(ax * ay)]
    for (index, p) in enumerate(photons):
        status = int(p[3])
        require(p[3] == status and 0 <= status <= 3, 'Invalid status/BVH overflow')
        counts[status] += 1
        x = x0 + (index % nx + 0.5) * (x1 - x0) / nx
        y = y0 + (index // nx + 0.5) * (y1 - y0) / ny
        (direction, f) = ref.refract(incident, ref.normal(x, y, seconds, optical_state['authoredWaves']))
        (hit, distance) = bvh.first((x, y, z), direction)
        require(hit, 'CPU daylight first hit unexpectedly missing')
        (ti, u, v) = hit
        expected_id = triangles[ti]['sourceObjectId']
        cpu_counts[expected_id] += 1
        oi = int(p[9])
        require(0 <= oi < len(ids) and p[9] == oi, 'Missing/invalid object identity in enclosed daylight pool')
        native_ti = int(p[10])
        require(p[10] == native_ti and 0 <= native_ti < len(triangles), 'Missing/invalid source triangle identity')
        named = triangles[native_ti]
        require(named['sourceObjectId'] == ids[oi], 'Source triangle belongs to another object')
        delta = ref.sub(p[:3], named['a'])
        normal = ref.cross(named['e1'], named['e2'])
        normal_length = math.sqrt(ref.dot(normal, normal))
        require(normal_length > 0 and abs(ref.dot(delta, normal)) / normal_length < 0.002, 'Hit is outside named source triangle plane')
        d00 = ref.dot(named['e1'], named['e1'])
        d01 = ref.dot(named['e1'], named['e2'])
        d11 = ref.dot(named['e2'], named['e2'])
        d20 = ref.dot(delta, named['e1'])
        d21 = ref.dot(delta, named['e2'])
        denom = d00 * d11 - d01 * d01
        bu = (d11 * d20 - d01 * d21) / denom
        bv = (d00 * d21 - d01 * d20) / denom
        require(bu >= -0.0001 and bv >= -0.0001 and (bu + bv <= 1.0001), 'Hit is outside named source triangle footprint')
        require((status == 0) == (oi == floor_index and abs(p[2] - zf) < 0.0005), 'Floor receiver classification changed')
        mismatch += ids[oi] != expected_id
        if ids[oi] != expected_id:
            evidence = {'photonIndex': index, 'cpuObjectId': expected_id, 'gpuObjectId': ids[oi],
                        'cpuTriangleIndex': ti, 'gpuTriangleIndex': native_ti}
            try:
                proof = identity_policy.explain((x, y, z), direction, p, ti)
            except ValueError as error:
                unexplained_mismatches.append({**evidence, 'reason': str(error)})
            else:
                listed_ambiguities.append({**evidence, 'proof': proof})
        if ids[oi] == expected_id:
            max_hit_error = max(max_hit_error, math.dist(p[:3], ref.add((x, y, z), ref.mul(direction, distance))))
            max_path_error = max(max_path_error, abs(p[7] - distance))
        max_fresnel_error = max(max_fresnel_error, abs(p[8] - f))
        require(0 <= p[8] <= 1 and p[7] > 0, 'Validation condition failed')
        reflected += packet * p[8]
        for ch in range(3):
            received[ch] += p[4 + ch]
            extinguished[ch] += packet * (1 - p[8]) - p[4 + ch]
            require(p[4 + ch] >= 0 and p[4 + ch] <= packet * (1 - p[8]) + 1e-09, 'Validation condition failed')
            expected_power = packet * (1 - p[8]) * math.exp(-extinction[ch] * p[7])
            max_extinction_error = max(max_extinction_error, abs(p[4 + ch] - expected_power) / max(expected_power, 1e-30))
            if expected_id == 'DOM_01720':
                cpu_floor_flux[ch] += packet * (1 - f) * math.exp(-extinction[ch] * distance)
        if status != 0:
            continue
        require(oi == floor_index and abs(p[2] - zf) < 0.0005, 'Nonfloor photon deposited into floor atlas')
        for ch in range(3):
            floor_flux[ch] += p[4 + ch]
        u = (p[0] - x0) / (x1 - x0) * ax - 0.5
        v = (p[1] - y0) / (y1 - y0) * ay - 0.5
        (ix, iy) = (math.floor(u), math.floor(v))
        (fx, fy) = (u - ix, v - iy)
        splats = [(xx, yy, wx * wy) for (xx, wx) in [(ix, 1 - fx), (ix + 1, fx)] for (yy, wy) in [(iy, 1 - fy), (iy + 1, fy)] if 0 <= xx < ax and 0 <= yy < ay]
        weight = sum((w for (_, _, w) in splats))
        require(weight > 0, 'Validation condition failed')
        for (xx, yy, w) in splats:
            for ch in range(3):
                reconstructed[yy * ax + xx][ch] += p[4 + ch] * w / weight / pixel_area
    require(counts[2] == 0 and counts[3] == 0, 'Escaped/upward rays in enclosed daylight probe')
    energy = [abs(reflected + received[c] + extinguished[c] - incoming) / incoming for c in range(3)]
    atlas_flux = [sum((p[c] for p in atlas)) * pixel_area for c in range(3)]
    atlas_energy = [abs(atlas_flux[c] - floor_flux[c]) / floor_flux[c] for c in range(3)]
    cpu_flux_error = [abs(cpu_floor_flux[c] - floor_flux[c]) / cpu_floor_flux[c] for c in range(3)]
    spatial_l1 = [sum((abs(a[c] - b[c]) for (a, b) in zip(atlas, reconstructed))) / sum((p[c] for p in reconstructed)) for c in range(3)]
    require(max(energy) < 1e-05, 'Validation condition failed')
    require(mismatch == len(listed_ambiguities) + len(unexplained_mismatches), 'Identity partition is incomplete')
    require(len(unexplained_mismatches) / (nx * ny) < UNEXPLAINED_IDENTITY_THRESHOLD,
            'Unexplained first-hit object mismatch exceeds 0.1%')
    require(max_hit_error < 0.002 and max_path_error < 0.002 and (max_fresnel_error < 2e-05) and (max_extinction_error < 0.0001), 'Snell location/Fresnel disagreement')
    require(max(cpu_flux_error) < 0.005, 'Integrated floor flux differs from CPU by >0.5%')
    require(max(atlas_energy) < 0.003, 'HDR additive deposit loses/gains >0.3% energy')
    require(max(spatial_l1) < 0.01, 'HDR atlas differs spatially from exact bilinear splats by >1% L1')
    report = {'status': 'synthetic-validator-fixture-passed' if meta.get('syntheticCPUFixture') else 'GPU-capture-CPU-source-reference-validated', 'shaderTimeSeconds': seconds, 'sampleCount': nx * ny, 'statusCounts': dict(counts), 'cpuFirstHitObjects': dict(cpu_counts), 'sourceHitObjectMismatches': mismatch, 'maxMatchingHitPositionErrorMetres': max_hit_error, 'maxFresnelError': max_fresnel_error, 'maxExtinctionRelativeError': max_extinction_error, 'maxMatchingUnderwaterPathErrorMetres': max_path_error, 'energyBalanceRelativeErrorRGB': energy, 'cpuFloorFluxRelativeErrorRGB': cpu_flux_error, 'atlasFluxRelativeErrorRGB': atlas_energy, 'atlasSpatialRelativeL1RGB': spatial_l1, 'atlasMaximumRGB': [max((p[c] for p in atlas)) for c in range(3)], 'hashes': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in [directory / 'capture.json', directory / 'receiver-contract.json', directory / 'photons-f32le.bin', directory / 'atlas-rgba16f-le.bin']}, 'limitations': ['Validation covers this frozen capture only.', 'No calibrated production lighting, visibility shadows, solar disk, multi-bounce or photorealism proof.', 'Pixel-area normalization conserves integrated deposited floor flux within explicit half-float tolerance; nonfloor power is retained separately.']}
    if not meta.get('syntheticCPUFixture'):
        report['status'] = ('GPU-capture-source-transport-validated-with-listed-f32-ambiguities'
                            if listed_ambiguities else 'GPU-capture-source-transport-validated')
    report['receiverIdentity'] = {
        'exactObjectIdentityMatches': nx * ny - mismatch,
        'listedFloat32Ambiguities': len(listed_ambiguities),
        'unexplainedObjectIdentityMismatches': len(unexplained_mismatches),
        'originalObjectMismatchRatio': mismatch / (nx * ny),
        'unexplainedObjectMismatchRatio': len(unexplained_mismatches) / (nx * ny),
        'unexplainedMismatchThreshold': UNEXPLAINED_IDENTITY_THRESHOLD,
        'policySha256': REVIEWED_IDENTITY_POLICY_SHA256,
        'policyScope': identity_policy.policy['policyScope'],
        'exactTriangleIdentityForAllPhotonsClaimed': False,
        'receiverIdentityRewritten': False,
        'floorEquivalenceAllowed': False,
        'productionUseAllowed': False,
        'maxListedAmbiguityHitErrorMetres': max((r['proof']['observedPointDifferenceMetres'] for r in listed_ambiguities), default=0),
        'listedAmbiguityEvidence': listed_ambiguities,
        'unexplainedMismatchEvidence': unexplained_mismatches,
    }
    report['waterState'] = {'source': 'current-saved-material' if water_state else 'historical-receiver-contract', 'waveCount': len(optical_state['authoredWaves']), 'waterBindingSha256': meta.get('waterBindingSha256')}
    report['validatorInputsSha256'] = {
        name: hashlib.sha256((BASE / name).read_bytes()).hexdigest()
        for name in ['validate_capture.py', 'identity_policy.py', 'receiver_reference.py', 'water_binding.py']
    }
    report['limitations'].append('Exact source object matches, listed float32 ambiguities and unexplained mismatches are counted separately. Listed wall/coping coincidences are diagnostic nonfloor transport only; source triangle, material and BRDF identities are never merged.')
    return report

def _write_report(directory, report):
    temporary = directory / 'reference-validation.json.tmp'
    temporary.write_text(json.dumps(report, indent=2) + '\n')
    temporary.replace(directory / 'reference-validation.json')

def validate(directory, allow_synthetic=False):
    directory = Path(directory)
    _write_report(directory, {'status': 'validation-pending', 'gpuValidated': False})
    try:
        report = _validate(directory, allow_synthetic=allow_synthetic)
    except Exception as error:
        _write_report(directory, {'status': 'validation-failed', 'gpuValidated': False, 'error': str(error)})
        raise
    _write_report(directory, report)
    return report
if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    print(json.dumps(validate(sys.argv[1]), indent=2))
