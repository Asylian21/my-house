"""Exact per-root native serialization witness for the frozen R20 geometry.

The faithful UE probe copied the original wrapped Transform exactly. Its actual
stored FMatrix and recovered Transform are the reference for each of 64 roots;
this module accepts no quaternion, scale, position or matrix epsilon.
"""
import importlib.util
import math
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-curved-grass-transform-guards-r4.py'
PROBE=ROOT/'output/unreal/exterior-20261002-r20c/curved-grass-transform-numeric-probe-r2.json'
PROBE_SHA='0c4463a9599498167bec818ba5e913b660db32aaad2ca910148a6f63dc9d6497'
PROBE_SOURCE_SHA='d0607c3b13c482013c8af0ac58a28779e82b2ef100a9d5851f20b1e1b5791e1c'
PROBE_PID=42431
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('r20_r4_frozen_numeric_guard',ROOT/'scripts/unreal/exterior-curved-grass-guards-r2.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
require,read,sha,pin,check_pin,digest=guard.require,guard.read,guard.sha,guard.pin,guard.check_pin,guard.digest


def numeric_bytes(value):
    if isinstance(value,list):
        return b'['+b''.join(numeric_bytes(v)for v in value)+b']'
    require(type(value) is float and math.isfinite(value),'Finite native double values required')
    return struct.pack('<d',value)


def exact_numeric(actual,expected,message):
    require(numeric_bytes(actual)==numeric_bytes(expected),message)


def policy():
    return {'owner':OWNER,'referenceProbe':pin(PROBE),'referenceNativeProcessId':PROBE_PID,
        'strictPerRootInputAndStoredMatrixAndRecoveredTransformBinary64':True,
        'quaternionEpsilon':None,'scaleEpsilon':None,'matrixEpsilon':None,'positionEpsilon':None,
        'originalRootXYZExact':True,'inputRotationCopiedFromOriginalWrappedTransformExactly':True,
        'allVertexRadiusMaximumCm':14.,'sourceAuthoredHeightAndUniformScaleUnchanged':True,
        'initialUnfaithfulConstructorProbeUsedForAcceptance':False,
        'float32ProjectionIsGpuReadback':False}


def probe_process():
    process=PROBE.parent/'curved-grass-transform-probe-r2-process.json';p=read(process)
    raw=PROBE.parent/'curved-grass-transform-probe-r2.log.json';log=PROBE.parent/'curved-grass-transform-probe-r2.log'
    require(Path(p['processFile'])==raw and Path(p['logFile'])==log
        and sha(raw)==p['processFileSha256'] and sha(log)==p['logSha256'] and p['reportSha256']==PROBE_SHA,
        'Faithful actual probe process/log/report closure changed')
    run=read(raw);args=run['args']
    require(run['pid']==PROBE_PID and run['code']==0
        and Path(run['command']).name=='UnrealEditor-Cmd'
        and args[0]==str(PROBE.parent/'Project/BreziTwin/BreziTwin.uproject')
        and '-nullrhi' in [v.lower()for v in args] and '-run=pythonscript' in [v.lower()for v in args]
        and '-script='+str(ROOT/'scripts/unreal/exterior-curved-grass-transform-probe-r2.py') in args,
        'Not the measured faithful native commandlet process')
    require(p['sourcePinsUnchangedAfterNative'] is True and len(p['sourcePinsBeforeNative'])==99
        and p['controllerSha256BeforeNative']==p['controllerSha256AfterNative']==sha(p['controller']),
        'Faithful probe source/controller closure differs')
    for path,h in p['sourcePinsBeforeNative'].items():require(sha(path)==h,'Faithful probe source changed: '+path)
    return process,p


def validate_observations(probe,selected,rows,original_values):
    require(probe['schema']=='brezi-curved-grass-readonly-map-transient-transform-numeric-probe-r2'
        and probe['owner']=='scripts/unreal/exterior-curved-grass-transform-probe-r2.py'
        and probe['status']=='actual-transient-64-hism-transform-comparison-completed'
        and probe['nativeProcessId']==PROBE_PID and probe['transientComponents']==3 and probe['transientInstances']==64,
        'Faithful probe type/count/owner differs')
    true_flags=('allPreInsertionRootXYZExact','allPreInsertionRotationExactCopies','allPreInsertionUniformScalesExact',
        'allRootXYZExactAfterInsertion','allFullVertexRadiiAtMost14Cm','mapOpenedByProbe','originalMapReadOnly',
        'originalActorWitnessUnchanged','nativeAssetsLoadedReadOnlyAsMapReferences')
    false_flags=('initialConstructorProbeUsedForAcceptance','actorSpawned','newTransientComponentsRegistered',
        'nativeAssetWrites','mapSaved','gpuLaunch','numericAcceptanceGateChanged','nativeAppearanceAccepted','performanceAccepted')
    require(all(probe[k] is True for k in true_flags)and all(probe[k] is False for k in false_flags),
        'Faithful probe input/read-only/acceptance scope differs')
    require(probe['originalActorWitnessBeforeSha256']==probe['originalActorWitnessAfterSha256'],
        'Probe changed an original actor')
    observations=probe['observations'];masters={r['id']:r for r in rows}
    expected=[r for kind in guard.MASTERS for r in selected if r['kind']==kind]
    require(len(observations)==len(expected)==64 and len({(r['groupId'],r['instanceIndex'])for r in selected})==64,
        'Exactly64 unique immutable selected source roots required')
    lookup={};counts={kind:0 for kind in guard.MASTERS}
    for observed,source in zip(observations,expected):
        key=(source['groupId'],source['instanceIndex']);kind=source['kind'];mesh=masters[source['newMasterId']]
        require((observed['groupId'],observed['originalIndex'],observed['kind'],observed['newMasterId'])
            ==(key[0],key[1],kind,source['newMasterId']),'Per-root probe identity/order changed')
        old=original_values[key[0]][key[1]]
        exact_numeric(observed['originalNativeValue'],old,'Measured original native root differs')
        exact_numeric(observed['preInsertionValue'],[old[0],old[1],[source['uniformScale']]*3],
            'Measured probe did not copy exact native wrapped XYZ/rotation/source height scale')
        actual=observed['recoveredNativeValue'];exact_numeric(actual[0],old[0],'Measured native root XYZ differs')
        require(all(observed[k] is True for k in ('preInsertionRootXYZExact','preInsertionRotationExactCopy',
            'preInsertionUniformScaleExact','rootXYZExactAfterInsertion','fullVertexRadiusAtMost14Cm')),
            'An individual faithful root control failed')
        require(observed['requestedUniformScale']==source['uniformScale']
            and observed['authoredHeightCm']==source['authoredHeightCm']
            and observed['originalSourceYawDeg']==source['originalSourceRow']['yawDeg']
            and observed['sourceRootedNativeFloat32HeightCm']==mesh['rootedHeightCm']
            and observed['originalSourceScaledRadiusCm']==source['scaledAllVertexRadiusCm'],
            'Source root yaw/height/geometry/radius controls changed')
        require(observed['decodedAllVertexRadiusCm']<=14.,'Measured complete crown exceeds old14cm envelope')
        storage=probe['nativeStoredMatrixReadback'][kind]
        require(storage['available'] is True and len(storage['rows'])==sum(r['kind']==kind for r in selected),
            'Actual64 stored FMatrix row-plane readback required')
        footprint=observed['actualStoredMatrixFullVertexFootprint']
        require(footprint and footprint['float32ProjectionIsGpuReadback'] is False and footprint['allVertexRadiusCm']<=14.,
            'Actual stored-matrix complete vertex envelope not proven')
        exact_numeric(footprint['actualNativeStoredDoubleMatrix'],storage['rows'][counts[kind]],
            'Per-root actual stored matrix is not its actual component row')
        require(footprint['actualNativeStoredMatrixFloat32Projection']==[[guard.f32(v)for v in row]
            for row in footprint['actualNativeStoredDoubleMatrix']], 'Stored-matrix F32 projection differs')
        lookup[key]=observed;counts[kind]+=1
    require(set(counts)==set(probe['nativeStoredMatrixReadback'])and counts=={'small_a':24,'small_b':24,'tall_c':16},
        'Measured actual original3 shape populations differ')
    return lookup


def validated_probe(selected,rows):
    require(sha(PROBE)==PROBE_SHA,'Pinned actual faithful probe changed')
    probe=read(PROBE);probe_process()
    require(check_pin(probe['sourceProbe'])==ROOT/'scripts/unreal/exterior-curved-grass-transform-probe-r2.py'
        and probe['sourceProbe']['sha256']==PROBE_SOURCE_SHA,'Faithful probe source differs')
    for key in ('sourceNativeHelper','originalMembersBefore','failedNativeReport','originalPlan',
        'preservedUnfaithfulConstructorProbe','originalGeometry','originalSourceGlb','rootSelection'):
        check_pin(probe[key])
    for entry in probe['engineSourceEvidence'].values():check_pin(entry)
    plan=read(check_pin(probe['originalPlan']))
    require(probe['originalGeometry']==plan['geometry'] and probe['originalSourceGlb']==plan['sourceGlb']
        and probe['rootSelection']==plan['rootSelection'] and selected==read(check_pin(plan['rootSelection'])),
        'Probe/source immutable payload binding changed')
    require(probe['sourceGLBFloat32AttributeProof']==guard.decode_glb(check_pin(plan['sourceGlb']),rows),
        'Actual source float32 geometry/UV/N/T/index proof differs')
    original=read(check_pin(probe['originalMembersBefore']))
    return probe,validate_observations(probe,selected,rows,original)


def transform_value(transform):
    return [[float(getattr(transform.translation,a))for a in 'xyz'],
        [float(getattr(transform.rotation,a))for a in 'xyzw'],[float(getattr(transform.scale3d,a))for a in 'xyz']]


def stored_matrix(component,index):
    # Already proven exposed by actual UE5.8 faithful probe for all64 rows.
    data=component.get_editor_property('per_instance_sm_data')[index]
    matrix=data.get_editor_property('transform')
    return [[float(getattr(getattr(matrix,plane),axis))for axis in 'xyzw']
        for plane in ('x_plane','y_plane','z_plane','w_plane')]


def verify_input(row,original_value,transform,reference):
    require((row['groupId'],row['instanceIndex'])==(reference['groupId'],reference['originalIndex']),
        'Wrong exact measured native root reference')
    exact_numeric(original_value,reference['originalNativeValue'],'Original selected native frame changed')
    actual=transform_value(transform)
    exact_numeric(actual,reference['preInsertionValue'],'Native input XYZ/rotation/uniformScale changed from faithful copy')
    exact_numeric(actual,[original_value[0],original_value[1],[row['uniformScale']]*3],
        'Original native XYZ/rotation/source authored height not copied exactly')


def verify_root(row,original_value,actual,mesh,matrix,reference):
    require((row['groupId'],row['instanceIndex'],row['newMasterId'])
        ==(reference['groupId'],reference['originalIndex'],reference['newMasterId']), 'Wrong native64 measured row')
    exact_numeric(original_value,reference['originalNativeValue'],'Original root changed after measured proof')
    exact_numeric(actual,reference['recoveredNativeValue'],'Native recovered root does not exactly match its faithful measured Transform')
    exact_numeric(matrix,reference['actualStoredMatrixFullVertexFootprint']['actualNativeStoredDoubleMatrix'],
        'Native stored FMatrix does not exactly match its faithful measured row')
    exact_numeric(actual[0],original_value[0],'Original native root XYZ changed')
    radius=max(math.hypot(p[0]*actual[2][0],p[1]*actual[2][1])for p in mesh['expectedNativeVerticesCm'])
    local=[[sum(p[j]*matrix[j][axis]for j in range(3))for axis in range(3)]for p in mesh['expectedNativeVerticesCm']]
    matrix_radius=max(math.hypot(p[0],p[1])for p in local);height=mesh['rootedHeightCm']*actual[2][2]
    require(radius<=14. and matrix_radius<=14.,'Actual complete grass footprint exceeds original14cm envelope')
    # Height and yaw are unchanged source inputs. Exact stored/recovered doubles
    # above bind serialization to the measured native operation, without a
    # separately widened bound on its mathematically derived height difference.
    require(row['authoredHeightCm']==reference['authoredHeightCm']
        and row['uniformScale']==reference['requestedUniformScale']
        and mesh['rootedHeightCm']==reference['sourceRootedNativeFloat32HeightCm'],
        'Authored height/source float32 geometry changed')
    return {'groupId':row['groupId'],'originalIndex':row['instanceIndex'],'newMasterId':row['newMasterId'],
        'originalNativeValue':original_value,'savedNativeValue':actual,'actualStoredDoubleMatrix':matrix,
        'nativeRootXYZExact':True,'nativeInputRotationCopiedExactly':True,
        'recoveredTransformExactMeasuredBinary64':True,'storedMatrixExactMeasuredBinary64':True,
        'referenceProbe':pin(PROBE),'referenceOriginalIndex':reference['originalIndex'],
        'decodedAllVertexRadiusCm':radius,'actualStoredMatrixAllVertexRadiusCm':matrix_radius,
        'decodedHeightCm':height,'authoredHeightCm':row['authoredHeightCm'],
        'heightDifferenceCm':height-row['authoredHeightCm'],
        'decodedQuaternionMaximumComponentRoundoff':reference['rotation']['maximumSignEquivalentComponentDifference'],
        'decodedRotationAngleDegrees':reference['rotation']['relativeRotationAngleDegrees'],
        'maximumUniformScaleComponentDifference':reference['maximumScaleComponentDifference']}


def verify_saved_groups(u,groups,selected,rows,original_values,lookup):
    actors={a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    meshes={r['id']:r for r in rows};proofs=[]
    for kind in guard.MASTERS:
        key='EX_curved_grass_r20_'+kind;group=groups[key];actor=actors[group['actor']]
        component=actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        members=[r for r in selected if r['kind']==kind]
        require(component and component.get_instance_count()==len(members),'Saved own3 root group/count differs')
        for index,row in enumerate(members):
            old=original_values[row['groupId']][row['instanceIndex']]
            proofs.append(verify_root(row,old,guard.native_instance_value(component,index),meshes[row['newMasterId']],
                stored_matrix(component,index),lookup[(row['groupId'],row['instanceIndex'])]))
    require(len(proofs)==64,'Saved exact64 measured transform/storage proofs required')
    return proofs
