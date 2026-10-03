"""Isolated earlier taper with a fuller 3.2–4.6 mm leaf, at unchanged root/cost.

This study keeps the sealed R9a source rows and the R1 long pointed profile.
It measures newly exported triangles and compares their actual CPU render with
R9a and R1. Source ground, recipe, collision and native outputs are untouched.
"""
import argparse
from copy import deepcopy
import importlib.util
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-lawn-tapered-covered.py'
OUTPUT = ROOT/'output/unreal/exterior-lawn-tapered-20261001-r2-study'
R1 = ROOT/'output/unreal/exterior-lawn-tapered-20261001-r1-study'
R1_SOURCE = ROOT/'scripts/unreal/exterior-lawn-tapered.py'
R1_SHA = '265babef031ea662fc37f106c59799e596b81d98525d8af3ac1813faed1f148d'
R1_MANIFEST_SHA = 'ae16378a9b5e05ec20d1d7cc5bb1dcd4ea38c90dec66165194f3197e11d8c8a4'


def load_r1():
    import hashlib
    if hashlib.sha256(R1_SOURCE.read_bytes()).hexdigest() != R1_SHA:
        raise ValueError('Frozen R1 generator changed')
    spec = importlib.util.spec_from_file_location('sealed_tapered_r1', R1_SOURCE)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    if result.sha(R1/'lawn-tapered-manifest.json') != R1_MANIFEST_SHA:
        raise ValueError('Frozen R1 output changed')
    return result


r1 = load_r1()
prior = r1.prior
sha, read, pin, require, write = r1.sha, r1.read, r1.pin, r1.require, r1.write


def mesh(variant, growth, lod, compact, old_record):
    """Five real vertices/three triangles: early maximum and one prolonged tip.

    The width distribution favors mature leaves without clipping any tip or
    moving a source leaf root. Each section inherits its source bend and twist;
    exported normals/tangents are rebuilt from these actual triangles.
    """
    points, uv, uv1, colors, triangles, ranges = [], [], [], [], [], []
    for index, blade in enumerate(prior.blade_parameters(variant, growth, compact)):
        old = old_record['bladeRanges'][index]
        require(np.allclose(blade['rootCm'], old['rootCm'], atol=1e-12), 'Source leaf roots differ')
        q = (blade['widthCm']-.25)/.15
        width = .32+.14*q**.35
        peak = .36+.09*blade['bladeSeed']
        root_fraction = min(.58+.04*((blade['bladeSeed']*7.3) % 1.), .82*blade['widthCm']/width)
        start, first_tri = len(points), len(triangles)
        old_rgb = np.asarray(old_record['colors'])[old['vertexOffset']:old['vertexOffset']+old['vertexCount'], :3].mean(axis=0)
        stations = ((0., [0., 1.]), (peak, [0., 1.]), (1., [.5]))
        color_weights = np.array([1.+.12*t for t, us in stations for _ in us])
        color_weights /= color_weights.mean()
        centers, rings, section_normals = [], [], []
        for t, us in stations:
            middle = prior.center(blade, t)
            tangent = prior.center(blade, t+.0001)-prior.center(blade, t-.0001)
            tangent /= np.linalg.norm(tangent)
            angle = blade['angleRad']+blade['bendRad']*t
            side = np.array([-math.sin(angle), math.cos(angle), 0.])
            normal = np.cross(tangent, side); normal /= np.linalg.norm(normal)
            roll = blade['rollRad']+blade['twistRad']*t
            side = side*math.cos(roll)+normal*math.sin(roll)
            normal = np.cross(tangent, side); normal /= np.linalg.norm(normal)
            section_width = width*(root_fraction if t == 0 else 1. if t < 1 else 0.)
            ring = []
            for u in us:
                ring.append(len(points)); points.append((middle+side*section_width*(u-.5)).tolist())
                uv.append([u, t]); uv1.append([blade['bladeSeed'], float(growth)])
                colors.append([*(old_rgb*color_weights[len(points)-start-1]).tolist(), 1.])
            centers.append(middle.tolist()); rings.append(ring); section_normals.append(normal.tolist())
        lift = max(0., -min(p[2] for p in points[start:]))
        for p in points[start:]: p[2] += lift
        for p in centers: p[2] += lift
        root, shoulder, tip = rings
        triangles.extend([[root[0], root[1], shoulder[0]], [root[1], shoulder[1], shoulder[0]],
            [shoulder[0], shoulder[1], tip[0]]])
        ranges.append({'bladeIndex': index, 'vertexOffset': start, 'vertexCount': 5,
            'triangleOffset': first_tri, 'triangleCount': 3, 'rootCm': blade['rootCm'],
            'centerlineCm': centers, 'sectionNormals': section_normals, 'widthCm': width,
            'peakT': peak, 'rootWidthFraction': root_fraction, 'heightCm': blade['heightCm'],
            'reachCm': blade['reachCm'], 'low': blade['low'], 'tipWidthCm': 0.,
            'basalLiftCm': lift, 'meanVertexColorPreserved': True, 'tipRootColorRatio': 1.12,
            'sourceRollRad': blade['rollRad'], 'sourceTwistRad': blade['twistRad'], 'clipped': False})
    record = {'nodeName': old_record['nodeName'], 'variant': variant, 'growthClass': growth,
        'edgeMaster': compact, 'level': lod, 'positionsCm': points, 'uv0': uv, 'uv1': uv1,
        'colors': colors, 'triangles': triangles, 'bladeRanges': ranges}
    p = np.asarray(points)
    record['expectedBoundsCm'] = {'min': p.min(axis=0).tolist(), 'max': p.max(axis=0).tolist()}
    record['radialEnvelopeCm'] = float(np.linalg.norm(p[:, :2], axis=1).max())
    return record


def build(output=OUTPUT):
    output = Path(output).resolve()
    require(output == OUTPUT and not output.exists(), 'Use fresh isolated immutable R2 study output')
    require(sha(r1.PRIOR/'lawn-natural-plan.json') == r1.PRIOR_SHA, 'Original upright basis changed')
    base = read(r1.PRIOR/'lawn-natural-plan.json')
    old_records = read(r1.PRIOR/'lawn-natural-prototypes.json')
    library = read(r1.PRIOR/'geometry-manifest.json'); recipe = read(r1.PRIOR/'material-manifest.json')[r1.MATERIAL]
    require(recipe['linearColor'] == [.04, .075, .025] and recipe['maps'] == {}, 'Original material basis changed')
    geometry = ROOT/'output/unreal/realism-20260926-r5/geometry'
    rural = Path(base['managedLawnPlan']['path']); original = Path(base['derivedFrom']['path'])
    scene, _, _, _, _, domain, _, _, _ = prior.cover.managed_source(geometry, rural, original)
    require(base['activeDesign'] == scene['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}, 'C/B/B changed')
    require(base['housePlacement'] == scene['house']['placement'] and domain.area/10000 == base['audit']['exactAllowedDomainM2'], 'Original frame/domain changed')
    legacy, _ = prior.legacy_source_proof(); require(legacy == base['audit']['legacyLawnProof'], 'Original40437 placements changed')
    r1_bundle = read(R1/'lawn-tapered-manifest.json')
    inputs = deepcopy(r1_bundle['inputFiles'])
    inputs[str(Path(__file__).resolve())] = sha(__file__)
    for name in ('lawn-tapered-plan.json', 'lawn-tapered-manifest.json', 'tapered.glb', 'tapered-geometry-manifest.json',
                 'lawn-tapered-prototypes.json', 'material-manifest.json', 'anatomy-side-by-side.png', 'geometry-validation.json'):
        inputs[str(R1/name)] = sha(R1/name)
    for path, expected in inputs.items(): require(sha(path) == expected, 'Frozen source dependency changed: '+path)
    rows = deepcopy(base['lawnPlacements']); groups = deepcopy(base['groups'])
    require(len(rows) == 102011 and len(groups) == 40, 'Original density changed')
    output.mkdir(parents=True)
    records = [mesh(r['variant'], r['growthClass'], r['level'], r['edgeMaster'], r) for r in old_records]
    glb = output/'tapered-covered.glb'
    r1.OWNER = OWNER  # Loaded exporter metadata only; frozen source file is never changed.
    r1.write_glb(glb, records, recipe); _, decoded = r1.decode_glb(glb)
    result = r1.measurements(decoded, rows, base, {'audit': base['audit'], 'library': library}, domain)
    native = {r['nodeName']: r for r in decoded}; new_library = deepcopy(library)
    for field in ('coverageReceipt', 'boundaryCoverageReceipt'):
        new_library['baseline'+field[0].upper()+field[1:]] = new_library.pop(field)
    for m in new_library['meshes']:
        old_master = next(old for old in library['meshes'] if old['id'] == m['id'])
        for l in m['lods']:
            actual = native[l['nodeName']]; p = np.asarray(actual['positionsCm'])
            l.update(vertices=len(p), triangles=len(actual['triangles']),
                expectedBoundsCm={'min': p.min(axis=0).tolist(), 'max': p.max(axis=0).tolist()},
                radialEnvelopeCm=float(np.linalg.norm(p[:, :2], axis=1).max()))
            old_lod = next(before for before in old_master['lods'] if before['nodeName'] == l['nodeName'])
            require(l['expectedBoundsCm']['max'][2] <= old_lod['expectedBoundsCm']['max'][2]+.000005, 'Old source height exceeded')
        require(max(l['radialEnvelopeCm'] for l in m['lods']) <= max(l['radialEnvelopeCm'] for l in old_master['lods'])+.000005, 'Old conservative crown exceeded')
        m.update(glbPath=str(glb), glbSha256=sha(glb), heightCm=max(l['expectedBoundsCm']['max'][2] for l in m['lods']))
    status = 'MEASURED_COVERED_TAPER_ANATOMY_STUDY_NOT_NATIVE_ACCEPTED'
    new_library.update(owner=OWNER, generatorSha256=sha(__file__), inputFiles=inputs, status=status)
    write(output/'geometry-manifest.json', new_library)
    write(output/'lawn-tapered-prototypes.json', records)
    (output/'material-manifest.json').write_bytes((r1.PRIOR/'material-manifest.json').read_bytes())
    variant = {'glb': pin(glb), 'geometryManifest': pin(output/'geometry-manifest.json'), 'measurements': result,
        'verticesPerLeaf': 5, 'trianglesPerLeaf': 3, 'actualVSection': False, 'nativeAccepted': False}
    plan = deepcopy(base); plan.update(owner=OWNER, generatorSha256=sha(__file__), inputFiles=inputs,
        geometryManifest=variant['geometryManifest'], priorPlan=pin(r1.PRIOR/'lawn-natural-plan.json'),
        priorTaperStudy=pin(R1/'lawn-tapered-manifest.json'),
        audit={'status': status, 'instances': len(rows), 'groups': len(groups), 'exactAllowedDomainM2': domain.area/10000,
            'originalPlacementRowsAndGroupsUnchanged': True, 'sourceGroundCollisionAndSetbacksUnchanged': True,
            'legacyLawnProof': legacy, 'measurements': result, 'nativeVerified': False, 'nativeAppearanceAccepted': False,
            'performanceAccepted': False, 'integrationAuthorized': False})
    for field in ('coverageReceipt', 'boundaryCoverageReceipt'):
        plan['baseline'+field[0].upper()+field[1:]] = plan.pop(field)
    write(output/'lawn-tapered-plan.json', plan)
    atlas = Image.new('RGB', (2040, 1320), '#eeeae1'); draw = ImageDraw.Draw(atlas)
    center = base['audit']['physicalCoverage']['windows'][0]['centerCm']
    comparisons = [('R9a upright - 3 triangles/leaf', r1.decode_glb(r1.PRIOR/'lawn-natural.glb')[1]),
        ('R1 fine taper - 3 triangles/leaf', r1.decode_glb(R1/'tapered.glb')[1]),
        ('R2 fuller early taper - 3 triangles/leaf', decoded)]
    for col, (label, actual) in enumerate(comparisons):
        for row_index in range(2): atlas.paste(r1.render(actual, rows, center, bool(row_index)), (col*680, 80+row_index*600))
        draw.text((col*680+12, 20), label, fill='#202820')
    draw.text((12, 1300), 'CPU decoded GLB: same25cm roots/camera/light, unchanged recipe, neutral backdrop. No Unreal/shadows/performance acceptance.', fill='#202820')
    atlas.save(output/'anatomy-side-by-side.png')
    widths = [b['widthCm'] for r in records if r['level'] == 0 for b in r['bladeRanges']]
    manifest = {'schemaVersion': 1, 'owner': OWNER, 'generatorSha256': sha(__file__), 'inputFiles': inputs, 'status': status,
        'priorPlan': plan['priorPlan'], 'priorTaperStudy': plan['priorTaperStudy'], 'plan': pin(output/'lawn-tapered-plan.json'),
        'geometryProof': pin(output/'lawn-tapered-prototypes.json'), 'materialManifest': pin(output/'material-manifest.json'),
        'preview': pin(output/'anatomy-side-by-side.png'), 'variant': variant,
        'anatomy': {'widthRangeMm': [10*min(widths), 10*max(widths)], 'meanWidthMm': 10*float(np.mean(widths)),
            'peakTRange': [.36, .45], 'rootWidthFractionRange': [.56, .62], 'tipWidthCm': 0.,
            'rootTipColorRatio': 1.12, 'leafMeanColorPreserved': True, 'sourceHeightReachBendTwistPreserved': True},
        'limits': ['All102011 roots/40groups, source143.598800884m2 domain and source height/reach preserved.',
            'AllLOD geometry identical:18,571,200 actual triangles each; no density or floor change.',
            'Exported geometry, not old coverage receipts, is rasterized at0.25mm in every original interior/boundary window.',
            'Earlier maximum and uninterrupted pointed taper; restrained color mean, unchanged actual recipe.',
            'CPU comparison omits native shadows/SSS/global illumination. Native appearance/performance acceptance is false.']}
    write(output/'lawn-tapered-manifest.json', manifest)
    return {'output': str(output), 'plan': manifest['plan'], 'variant': variant, 'anatomy': manifest['anatomy'], 'preview': manifest['preview']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__); parser.add_argument('--output', default=str(OUTPUT))
    import json
    print(json.dumps(build(**vars(parser.parse_args()))))
