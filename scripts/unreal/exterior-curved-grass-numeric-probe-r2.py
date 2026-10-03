"""Comprehensive read-only R20 numeric probe. No map/scene/asset APIs."""
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-curved-grass-numeric-probe-r2.py'
PLAN = ROOT/'output/unreal/exterior-curved-grass-20261002-r1-study/curved-grass-plan.json'
PLAN_SHA = 'f43f3d224c9d43d70091a910e5618052fa942bb593ac55d3cc900eace8a8aa68'
NATIVE_SHA = 'e7b0158a78055b08836ccbedb62dc244717a3fedbe3c9cc7b9a8e513b5173f99'
PROBE_R1_SHA = '0065aab8bfe8e75cfb8cf62c015d5c725a07050865c1187fca5debb94ebebbec'
sys.dont_write_bytecode = True


def load(name, filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/filename)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


n = load('r20_numeric_r2_frozen_native', 'exterior-curved-grass-native.py')
g = n.guard
p = load('r20_numeric_r2_frozen_diff', 'exterior-curved-grass-numeric-probe-r1.py')
g.require(g.sha(PLAN)==PLAN_SHA and g.sha(ROOT/n.OWNER)==NATIVE_SHA
          and g.sha(ROOT/p.OWNER)==PROBE_R1_SHA,'Frozen comprehensive probe inputs changed')


def flat(values):
    result=[]
    for value in values:
        if isinstance(value,list):result.extend(flat(value))
        else:result.append(value)
    return result


def binary_equal(a,b,fmt):
    a,b=flat(a),flat(b)
    return len(a)==len(b) and struct.pack('<'+fmt*len(a),*a)==struct.pack('<'+fmt*len(b),*b)


def main():
    output=Path(os.environ['BREZI_CURVED_GRASS_NUMERIC_PROBE_OUTPUT']).resolve()
    g.require(output.is_relative_to(ROOT/'output/unreal') and output.name=='curved-grass-numeric-probe-r2.json'
              and not output.exists(),'Fresh comprehensive numeric-only output required')
    plan=g.read(PLAN)
    for key in ('geometry','rootSelection','materialRecipe'):g.check_pin(plan[key])
    for row in plan['sourceInputs'].values():g.check_pin(row)
    saved_rows=g.read(plan['geometry']['path'])['meshes']
    derived_rows=g.converted_geometry(g.original_meshes())
    saved_selection=g.read(plan['rootSelection']['path'])
    placements,prototypes,camera=n.load_selection_inputs()
    derived_selection=g.select_roots(g.source_candidates(placements,prototypes,camera),derived_rows)
    report=g.read(g.check_pin(plan['baseNativeReport']))
    saved={'geometry':saved_rows,'selection':saved_selection,'camera':plan['camera'],
        'materialRecipe':g.read(plan['materialRecipe']['path']),'audit':plan['audit']}
    derived={'geometry':derived_rows,'selection':derived_selection,'camera':camera,
        'materialRecipe':n.maps.canonical_recipe(),'audit':n.canonical_audit(report)}
    delta=sorted(p.differences(saved,derived),key=lambda row:row['path'])
    numeric=[row for row in delta if row['kind']=='number']
    attributes={}
    fields=('positionMetersYUp','normalYUp','uv0','indices','tangentYUp','expectedNativeVerticesCm','expectedNativeNormals')
    for a,b in zip(saved_rows,derived_rows):
        attributes[a['id']]={field:{'exactDecodedEquality':a[field]==b[field],
            'float32OrU32BinaryEqual':binary_equal(a[field],b[field],'I' if field=='indices' else 'f'),
            'recursiveDifferences':len(p.differences(a[field],b[field]))} for field in fields}
    controls=('groupId','instanceIndex','oldMasterId','originalSourceRow','authoredHeightCm',
        'newMasterId','kind','uniformScale','newSourceRow','allVertexWholeCrownSafetyRadiusCm','originalExclusionCrownRadiusCm')
    selection_controls={'savedCount':len(saved_selection),'derivedCount':len(derived_selection),
        'exactIdentityRootXYZYawScaleHeightControls':all({key:a[key] for key in controls}=={key:b[key] for key in controls}
            for a,b in zip(saved_selection,derived_selection)) and len(saved_selection)==len(derived_selection),
        'numericDerivedFieldsComparedSeparately':['cameraDistanceCm','originalAllLodRadiusCm','scaledAllVertexRadiusCm']}
    g.write(output,{'schema':'brezi-original-curved-grass-numeric-probe-r2','owner':OWNER,
        'status':'read-only-comprehensive-numeric-comparison-completed','nativeProcessId':os.getpid(),
        'pythonVersion':sys.version,'pythonExecutable':sys.executable,'selectedPlan':g.pin(PLAN),
        'probeSource':g.pin(ROOT/OWNER),'frozenProbeR1':g.pin(ROOT/p.OWNER),'frozenNative':g.pin(ROOT/n.OWNER),
        'savedDigest':g.digest(saved),'derivedDigest':g.digest(derived),'mismatchCount':len(delta),
        'numericMismatchCount':len(numeric),'nonNumericMismatchCount':len(delta)-len(numeric),
        'maximumNumericAbsoluteDifference':max((row['absoluteDifference'] for row in numeric),default=0.),
        'maximumDoubleUlpDifference':max((row['doubleUlps'] for row in numeric),default=0),
        'numericFloat32UnequalCount':sum(not row['float32Equal'] for row in numeric),
        'mismatches':delta[:300],'mismatchListTruncated':len(delta)>300,'geometryAttributeComparisons':attributes,
        'selectionControls':selection_controls,'materialRecipeExactlyEqual':saved['materialRecipe']==derived['materialRecipe'],
        'cameraExactlyEqual':saved['camera']==derived['camera'],'auditExactlyEqual':saved['audit']==derived['audit'],
        'sceneOpened':False,'nativeAssetsTouched':False,'mapModified':False,'gpuLaunch':False,
        'geometryAcceptanceGateChanged':False,'nativeGeometryVerified':False,'nativeAppearanceAccepted':False})
    print(json.dumps({'output':g.pin(output),'mismatchCount':len(delta),'nonNumericMismatchCount':len(delta)-len(numeric),
        'maximumDoubleUlpDifference':max((row['doubleUlps'] for row in numeric),default=0),
        'numericFloat32UnequalCount':sum(not row['float32Equal'] for row in numeric),
        'selectionControlsExact':selection_controls['exactIdentityRootXYZYawScaleHeightControls'],
        'sceneOpened':False,'nativeAssetsTouched':False}))


if __name__=='__main__':main()
