"""Read-only numeric R20 probe. No map, scene, asset or material API calls."""
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-curved-grass-numeric-probe-r1.py'
GEOMETRY = ROOT/'output/unreal/exterior-curved-grass-20261002-r1-study/geometry-manifest.json'
GEOMETRY_SHA = 'dbcdd923db3e108af02f8ccb34ced8519e19f2792e64c6f18fd01b2c461b03e3'
GUARD_SHA = '20e6dba5af91ce0ca5ffbe3d817ed4ceb6b0267a5fdfa4cda8329355d89a567d'
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('r20_numeric_frozen_guard', ROOT/'scripts/unreal/exterior-curved-grass-guards.py')
g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
g.require(g.sha(ROOT/g.OWNER) == GUARD_SHA and g.sha(GEOMETRY) == GEOMETRY_SHA, 'Frozen source probe inputs changed')


def ordered_double(value):
    bits = struct.unpack('<Q', struct.pack('<d', float(value)))[0]
    return (~bits & ((1 << 64)-1)) if bits >> 63 else bits | (1 << 63)


def differences(saved, derived, path='$', result=None):
    result = [] if result is None else result
    if isinstance(saved, dict) and isinstance(derived, dict):
        if set(saved) != set(derived): result.append({'path':path,'kind':'object-keys','savedKeys':sorted(saved),'derivedKeys':sorted(derived)})
        for key in saved.keys() & derived.keys(): differences(saved[key], derived[key], path+'.'+key, result)
    elif isinstance(saved,list) and isinstance(derived,list):
        if len(saved) != len(derived): result.append({'path':path,'kind':'array-length','saved':len(saved),'derived':len(derived)})
        for index,(a,b) in enumerate(zip(saved,derived)): differences(a,b,path+'['+str(index)+']',result)
    elif type(saved) is not type(derived):
        result.append({'path':path,'kind':'type','savedType':type(saved).__name__,'derivedType':type(derived).__name__})
    elif saved != derived:
        if isinstance(saved,(int,float)) and not isinstance(saved,bool):
            a,b=float(saved),float(derived)
            result.append({'path':path,'kind':'number','saved':saved,'derived':derived,'absoluteDifference':abs(a-b),
                'doubleUlps':abs(ordered_double(a)-ordered_double(b)), 'savedFloat32':g.f32(a),'derivedFloat32':g.f32(b),
                'float32Equal':g.f32(a)==g.f32(b)})
        else: result.append({'path':path,'kind':'non-numeric','saved':saved,'derived':derived})
    return result


def main():
    output = Path(os.environ['BREZI_CURVED_GRASS_NUMERIC_PROBE_OUTPUT']).resolve()
    g.require(output.is_relative_to(ROOT/'output/unreal') and output.name == 'curved-grass-numeric-probe-r1.json'
              and not output.exists(), 'Fresh numeric-only probe output required')
    saved = g.read(GEOMETRY)['meshes']
    derived = g.converted_geometry(g.original_meshes())
    delta = sorted(differences(saved,derived),key=lambda row:row['path'])
    fields = ('positionMetersYUp','normalYUp','uv0','indices','tangentYUp',
              'expectedNativeVerticesCm','expectedNativeNormals')
    attributes = {}
    for a,b in zip(saved,derived):
        attributes[a['id']] = {field:{'exactDecodedEquality':a[field]==b[field],
            'recursiveDifferences':len(differences(a[field],b[field]))} for field in fields}
    numeric = [row for row in delta if row['kind']=='number']
    result = {'schema':'brezi-original-curved-grass-numeric-probe-r1','owner':OWNER,
        'status':'read-only-numeric-comparison-completed','nativeProcessId':os.getpid(),
        'pythonVersion':sys.version,'pythonExecutable':sys.executable,'geometry':g.pin(GEOMETRY),
        'frozenGuard':g.pin(ROOT/g.OWNER),'probeSource':g.pin(ROOT/OWNER),
        'savedRowsDigest':g.digest(saved),'derivedRowsDigest':g.digest(derived),
        'mismatchCount':len(delta),'numericMismatchCount':len(numeric),'nonNumericMismatchCount':len(delta)-len(numeric),
        'maximumNumericAbsoluteDifference':max((row['absoluteDifference'] for row in numeric),default=0.),
        'maximumDoubleUlpDifference':max((row['doubleUlps'] for row in numeric),default=0),
        'numericFloat32UnequalCount':sum(not row['float32Equal'] for row in numeric),
        'mismatches':delta[:200],'mismatchListTruncated':len(delta)>200,'geometryAttributeComparisons':attributes,
        'sceneOpened':False,'nativeAssetsTouched':False,'mapModified':False,'gpuLaunch':False,
        'geometryAcceptanceGateChanged':False,'nativeGeometryVerified':False,'nativeAppearanceAccepted':False}
    g.write(output,result)
    print(json.dumps({'output':g.pin(output),'mismatchCount':len(delta),
        'nonNumericMismatchCount':result['nonNumericMismatchCount'], 'maximumDoubleUlpDifference':result['maximumDoubleUlpDifference'],
        'numericFloat32UnequalCount':result['numericFloat32UnequalCount'],'sceneOpened':False,'nativeAssetsTouched':False}))


if __name__=='__main__':main()
