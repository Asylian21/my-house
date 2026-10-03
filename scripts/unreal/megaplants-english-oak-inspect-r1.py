#!/usr/bin/env python3
"""CPU-only original USD census using UE's bundled OpenUSD, without Unreal startup."""
import collections
import gc
import hashlib
import json
import math
from pathlib import Path
import sys

from pxr import Gf, Sdf, Usd, UsdGeom, UsdShade

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'output/unreal/megaplants-english-oak-20261002-r1'

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()

def pin(path):
    p = Path(path).resolve()
    return {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}

def require(v, message):
    if not v:
        raise ValueError(message)

def small(v):
    if v is None or isinstance(v, (str, int, float, bool)):
        return v
    if isinstance(v, Sdf.AssetPath):
        return {'authoredPath': v.path, 'resolvedPath': v.resolvedPath}
    if isinstance(v, dict):
        return {str(k): small(x) for k, x in v.items()}
    try:
        if len(v) <= 16:
            return [small(x) for x in v]
        return {'arrayCount': len(v)}
    except TypeError:
        return str(v)

def array_info(v):
    if v is None:
        return {'count': 0, 'hasValue': False}
    result = {'count': len(v), 'hasValue': True}
    try:
        b = memoryview(v).tobytes()
        result.update(binaryBytes=len(b), nativeArraySha256=hashlib.sha256(b).hexdigest())
    except TypeError:
        result['nativeArraySha256'] = None
    return result

def bounds(points):
    lo = [float('inf')] * 3
    hi = [float('-inf')] * 3
    for p in points:
        for j in range(3):
            n = float(p[j])
            require(math.isfinite(n), 'Nonfinite original point')
            lo[j] = min(lo[j], n)
            hi[j] = max(hi[j], n)
    return {'min': lo, 'max': hi}

def bbox(b):
    r = b.ComputeAlignedRange()
    return {'min': list(r.GetMin()), 'max': list(r.GetMax())}

def mesh_row(prim):
    m = UsdGeom.Mesh(prim)
    p = m.GetPointsAttr().Get()
    counts = m.GetFaceVertexCountsAttr().Get()
    indices = m.GetFaceVertexIndicesAttr().Get()
    require(p is not None and counts is not None and indices is not None,
            'Original mesh has missing topology')
    require(sum(counts) == len(indices) and min(counts) >= 3,
            'Invalid polygon cardinality')
    require(min(indices) >= 0 and max(indices) < len(p), 'Out-of-range mesh index')
    path = str(prim.GetPath())
    category = ('pointInstancerPrototype' if '/Prototypes/' in path else
                'abstractClassLibrary' if prim.IsAbstract() else 'treeBaseGeometry')
    primvars = []
    for pv in UsdGeom.PrimvarsAPI(prim).GetPrimvars():
        if not pv.HasAuthoredValue():
            continue
        primvars.append({'name': pv.GetPrimvarName(), 'type': str(pv.GetTypeName()),
                         'interpolation': pv.GetInterpolation(),
                         'elementSize': pv.GetElementSize(),
                         'data': array_info(pv.Get()) if hasattr(pv.Get(), '__len__') else small(pv.Get()),
                         'indices': array_info(pv.GetIndices())})
    subsets = []
    for child in prim.GetChildren():
        if child.IsA(UsdGeom.Subset):
            sub = UsdGeom.Subset(child)
            faces = sub.GetIndicesAttr().Get()
            require(all(0 <= i < len(counts) for i in faces), 'Out-of-range material subset')
            subsets.append({'path': str(child.GetPath()), 'elementType': sub.GetElementTypeAttr().Get(),
                            'familyName': sub.GetFamilyNameAttr().Get(), 'faces': array_info(faces),
                            'fanTriangulatedCount': sum(counts[i]-2 for i in faces),
                            'materialTargets': [str(x) for x in child.GetRelationship('material:binding').GetTargets()]})
    normals = m.GetNormalsAttr().Get()
    return {'path': path, 'category': category, 'isAbstract': prim.IsAbstract(),
            'points': array_info(p), 'faceVertexCounts': array_info(counts),
            'faceVertexIndices': array_info(indices), 'polygonFaces': len(counts),
            'faceSizeHistogram': dict(collections.Counter(counts)),
            'fanTriangulatedCount': sum(n-2 for n in counts),
            'localBoundsSourceUnits': bounds(p), 'orientation': m.GetOrientationAttr().Get(),
            'doubleSided': m.GetDoubleSidedAttr().Get(),
            'subdivisionScheme': m.GetSubdivisionSchemeAttr().Get(),
            'normals': array_info(normals), 'normalsInterpolation': m.GetNormalsInterpolation(),
            'primvars': primvars, 'materialSubsets': subsets,
            'skeletonTargets': [str(x) for x in prim.GetRelationship('skel:skeleton').GetTargets()]}

def inspect_stage(path):
    layer = Sdf.Layer.FindOrOpen(str(path))
    require(layer is not None, 'USD layer failed to parse')
    s = Usd.Stage.Open(layer, load=Usd.Stage.LoadAll)
    require(s is not None, 'USD stage failed to compose')
    prims = list(s.TraverseAll())
    assets, unreal_paths, schemas, materials, meshes, skeletons, instances = [], [], [], [], [], [], []
    for prim in prims:
        schemas.append({'path': str(prim.GetPath()), 'appliedSchemas': list(prim.GetAppliedSchemas())}) if prim.GetAppliedSchemas() else None
        for a in prim.GetAuthoredAttributes():
            value = a.Get()
            if a.GetTypeName() in (Sdf.ValueTypeNames.Asset, Sdf.ValueTypeNames.AssetArray):
                assets.append({'prim': str(prim.GetPath()), 'attribute': a.GetName(), 'value': small(value)})
            if 'unreal' in a.GetName().lower():
                unreal_paths.append({'prim': str(prim.GetPath()), 'attribute': a.GetName(), 'type': str(a.GetTypeName()), 'value': small(value)})
        if prim.IsA(UsdGeom.Mesh):
            meshes.append(mesh_row(prim))
        if prim.IsA(UsdShade.Material) or prim.IsA(UsdShade.Shader):
            materials.append({'path': str(prim.GetPath()), 'type': prim.GetTypeName(),
                              'attributes': [{'name': a.GetName(), 'type': str(a.GetTypeName()),
                                              'authored': a.HasAuthoredValueOpinion(), 'value': small(a.Get()),
                                              'connections': [str(c) for c in a.GetConnections()]}
                                             for a in prim.GetAttributes()]})
        if prim.GetTypeName() == 'Skeleton':
            j = prim.GetAttribute('joints').Get()
            skeletons.append({'path': str(prim.GetPath()), 'joints': array_info(j),
                              'jointNames': small(prim.GetAttribute('jointNames').Get()),
                              'bindTransforms': array_info(prim.GetAttribute('bindTransforms').Get()),
                              'restTransforms': array_info(prim.GetAttribute('restTransforms').Get())})
        if prim.IsA(UsdGeom.PointInstancer):
            i = UsdGeom.PointInstancer(prim)
            proto = i.GetProtoIndicesAttr().Get()
            targets = i.GetPrototypesRel().GetTargets()
            require(proto is not None and all(0 <= n < len(targets) for n in proto), 'Invalid original assembly')
            hist = collections.Counter(proto)
            prototypes = []
            for n, target in enumerate(targets):
                prefix = str(target) + '/'
                # Prototypes occur later in traversal; census is calculated after all meshes.
                prototypes.append({'index': n, 'path': str(target), 'instances': hist[n]})
            cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default', 'render'], useExtentsHint=False)
            instances.append({'path': str(prim.GetPath()), 'instanceCount': len(proto),
                              'prototypeIndices': array_info(proto), 'prototypes': prototypes,
                              'positions': array_info(i.GetPositionsAttr().Get()),
                              'orientations': array_info(i.GetOrientationsAttr().Get()),
                              'scales': array_info(i.GetScalesAttr().Get()),
                              'defaultTimeWorldBoundsSourceUnits': bbox(cache.ComputeWorldBound(prim))})
    expanded = 0
    for row in instances:
        for prototype in row['prototypes']:
            prefix = prototype['path'] + '/'
            selected = [r for r in meshes if r['path'].startswith(prefix)]
            prototype['meshPaths'] = [r['path'] for r in selected]
            prototype['fanTriangulatedCount'] = sum(r['fanTriangulatedCount'] for r in selected)
            expanded += prototype['instances'] * prototype['fanTriangulatedCount']
    roots = [p for p in s.GetPseudoRoot().GetChildren() if p.IsDefined() and not p.IsAbstract()]
    cache = UsdGeom.BBoxCache(Usd.TimeCode.Default(), ['default', 'render'], useExtentsHint=False)
    base = sum(m['fanTriangulatedCount'] for m in meshes if m['category'] == 'treeBaseGeometry')
    result = {'source': pin(path), 'format': layer.GetFileFormat().formatId,
              'stageUpAxis': UsdGeom.GetStageUpAxis(s), 'metersPerUnit': UsdGeom.GetStageMetersPerUnit(s),
              'authoredUpAxis': s.HasAuthoredMetadata('upAxis'), 'authoredMetersPerUnit': s.HasAuthoredMetadata('metersPerUnit'),
              'defaultPrim': str(s.GetDefaultPrim().GetPath()) if s.GetDefaultPrim() else None,
              'rootPrims': [str(p.GetPath()) for p in roots],
              'layerReferences': list(layer.GetExternalReferences()),
              'usedOriginalLayers': [pin(l.realPath) for l in s.GetUsedLayers() if l.realPath],
              'primTypeHistogramIncludingAbstractAndPrototypes': dict(collections.Counter(p.GetTypeName() for p in prims)),
              'variantSets': [{'path': str(p.GetPath()), 'sets': list(p.GetVariantSets().GetNames())}
                              for p in prims if p.GetVariantSets().GetNames()],
              'appliedSchemas': schemas, 'unrealAttributes': unreal_paths,
              'assetAttributes': assets, 'materialsAndShaders': materials,
              'meshesIncludingAbstractAndPrototypes': meshes, 'skeletons': skeletons,
              'pointInstancers': instances, 'defaultTimeRootBoundsSourceUnits':
              [{'path': str(p.GetPath()), 'bounds': bbox(cache.ComputeWorldBound(p))} for p in roots],
              'treeBaseFanTriangles': base, 'assemblyExpandedFanTrianglesSourceEstimate': expanded,
              'basePlusExpandedFanTrianglesSourceEstimate': base + expanded,
              'nativeTrianglesMeasured': False, 'windEvaluationPerformed': False,
              'sourceMaterialTextureAssetCount': len(assets)}
    del s, layer, prims
    gc.collect()
    return result

def main():
    destination = OUT / 'usd-source-inspection-r1.json'
    require(not destination.exists(), 'Preserve existing inspection; use a new version')
    receipt = json.loads((OUT / 'source-extraction-receipt.json').read_text())
    for row in receipt['files']:
        require(pin(row['path'])['sha256'] == row['sha256'] and Path(row['path']).stat().st_size == row['bytes'], 'Original extracted file changed')
    usd, wind = [], []
    for row in receipt['files']:
        p = Path(row['path'])
        if p.suffix == '.usd':
            r = inspect_stage(p)
            usd.append(r)
            print(json.dumps({'file': p.name, 'meshes': len(r['meshesIncludingAbstractAndPrototypes']),
                              'treeBaseTriangles': r['treeBaseFanTriangles'],
                              'expandedAssemblyEstimate': r['assemblyExpandedFanTrianglesSourceEstimate'],
                              'textureAssetInputs': len(r['assetAttributes'])}), flush=True)
        else:
            value = json.loads(p.read_text())
            wind.append({'source': pin(p), 'topLevelKeys': list(value),
                         'topLevelCollectionCounts': {k: len(v) for k, v in value.items() if isinstance(v, (list, dict))},
                         'firstRecords': {k: small(v[:1]) for k, v in value.items() if isinstance(v, list)}})
    for row in receipt['files']:
        require(pin(row['path'])['sha256'] == row['sha256'], 'Source changed during inspection')
    result = {'schema': 'brezi-original-licensed-english-oak-usd-inspection-r1',
              'owner': 'scripts/unreal/megaplants-english-oak-inspect-r1.py',
              'status': 'original-source-cpu-usd-inspected-native-pilot-pending',
              'extractReceipt': pin(OUT / 'source-extraction-receipt.json'),
              'inspector': pin(__file__), 'python': pin(sys.executable),
              'pythonVersion': sys.version, 'openUsdVersion': list(Usd.GetVersion()),
              'usdLayers': usd, 'dynamicWind': wind,
              'allOriginalFilesUnchanged': True, 'unrealExecuted': False,
              'missingTextureReplacementsCreated': False, 'nativeAssetsCreated': False,
              'appearanceAccepted': False, 'performanceAccepted': False,
              'fullRealismAccepted': False}
    destination.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({'inspection': pin(destination)}))

if __name__ == '__main__':
    main()
