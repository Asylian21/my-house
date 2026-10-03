"""Root-launched read-only original-map + transient64 HISM transform probe; no saves."""
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-curved-grass-transform-probe-r2.py'
FAILED=ROOT/'output/unreal/exterior-20261002-r20c'
VALUES=FAILED/'curved-grass-original-members-before.json'
VALUES_SHA='35341d3070ef626549b1b335cf8f353667ab157520f03cff4bd591942856f420'
REPORT_SHA='2f2429dfdb6aa5565450281d91561a232af070dfbd2f2957643d0ea36143a18d'
NATIVE_SHA='c221d0caea0bcf5a9e086df115ae813657a47665b7525eb0f389c7673d239a2a'
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('r20_probe_frozen_native_r3',ROOT/'scripts/unreal/exterior-curved-grass-native-r3.py')
n=importlib.util.module_from_spec(spec);spec.loader.exec_module(n)
g=n.guard;require,read,write,sha,pin,digest=g.require,g.read,g.write,g.sha,g.pin,g.digest


def value(transform):
    return [n.vec(transform.translation),n.vec(transform.rotation,'xyzw'),n.vec(transform.scale3d)]


def rotation_metrics(a,b):
    aligned=[v*(-1 if sum(x*y for x,y in zip(a,b))<0 else 1)for v in b]
    na,nb=math.sqrt(sum(v*v for v in a)),math.sqrt(sum(v*v for v in aligned))
    x,y,z,w=[v/na for v in a];X,Y,Z,W=[v/nb for v in aligned]
    relative=[-W*x+X*w-Y*z+Z*y,-W*y+X*z+Y*w-Z*x,-W*z-X*y+Y*x+Z*w,W*w+X*x+Y*y+Z*z]
    return {'signAlignedRecovered':aligned,'maximumSignEquivalentComponentDifference':max(abs(x-y)for x,y in zip(a,aligned)),
        'relativeRotationAngleDegrees':math.degrees(2*math.atan2(math.sqrt(sum(v*v for v in relative[:3])),abs(relative[3]))),
        'originalQuaternionUnitLengthError':abs(na-1),'recoveredQuaternionUnitLengthError':abs(nb-1)}


def modeled_matrix(transform):
    # Explicit mathematical reconstruction only. Direct actual storage is read
    # separately when the reflected FMatrix property exposes row planes.
    t,q,s=transform;x,y,z,w=q;xx,yy,zz=x*x*2,y*y*2,z*z*2;xy,xz,yz=x*y*2,x*z*2,y*z*2;wx,wy,wz=w*x*2,w*y*2,w*z*2
    return [[(1-yy-zz)*s[0],(xy+wz)*s[0],(xz-wy)*s[0],0.],
        [(xy-wz)*s[1],(1-xx-zz)*s[1],(yz+wx)*s[1],0.],
        [(xz+wy)*s[2],(yz-wx)*s[2],(1-xx-yy)*s[2],0.],t+[1.]]


def actual_matrix_rows(component):
    try:
        storage=component.get_editor_property('per_instance_sm_data');result=[]
        for row in storage:
            matrix=row.get_editor_property('transform')
            result.append([[float(getattr(getattr(matrix,plane),axis))for axis in 'xyzw']
                for plane in ('x_plane','y_plane','z_plane','w_plane')])
        return {'available':True,'rows':result,'readback':'Actual reflected PerInstanceSMData.Transform row planes.'}
    except Exception as error:
        return {'available':False,'reason':str(error),'modeledMatricesAreNativeReadback':False}


def main():
    import unreal as u
    output=Path(os.environ['BREZI_CURVED_GRASS_TRANSFORM_PROBE_OUTPUT']).resolve()
    require(output==FAILED/'curved-grass-transform-numeric-probe-r2.json' and not output.exists(),'Fresh own failed-candidate transform probe output required')
    require(sha(VALUES)==VALUES_SHA and sha(FAILED/'curved-grass-native-report-r3.json')==REPORT_SHA
            and sha(ROOT/n.OWNER)==NATIVE_SHA,'Frozen actual failing native inputs changed')
    require(sha(ROOT/'scripts/unreal/exterior-curved-grass-transform-probe-r1.py')=='bfb99df42cb504c951deabb0e809686a249661f816b7df0ba4c1c77815ed518d'
            and sha(FAILED/'curved-grass-transform-numeric-probe-r1.json')=='7d02225974bf1cb1a2a0d9f89937a887b54eb753f2ce1376ccdeb250c4cb387c',
            'Preserved initial reconstructed-quaternion diagnostic changed')
    plan_path=ROOT/'output/unreal/exterior-curved-grass-20261002-r1-study/curved-grass-plan.json';plan=read(plan_path)
    base_report,content_before,_,evidence,rows,selected,_=n.validate_plan(plan,plan_path)
    project=FAILED/'Project/BreziTwin';map_file=project/'Content/Brezi/Maps/Brezi.umap'
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project,'Wrong probe project')
    require(sha(map_file)==content_before['Brezi/Maps/Brezi.umap']['sha256'],'Original map changed before read-only probe')
    map_sha_before=sha(map_file)
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem);require(levels.load_level(n.MAP),'Cannot read original untouched candidate map')
    importer,_=n.g.frozen_modules(evidence);before_witness=n.g.native_witness(u,importer)
    require(len(before_witness)==5306,'Original full actor population changed')
    old_values,chosen,_=n.capture_original_instances(u,base_report,selected)
    require(old_values==read(VALUES),'Actual original native wrappers differ from frozen before-values')
    meshes={r['id']:r for r in rows};originals=g.original_meshes()
    expected_indices={group:len(old_values[group])for group in {r['groupId']for r in selected}}
    components=[];observations=[];storage={}
    for kind in g.MASTERS:
        members=[r for r in selected if r['kind']==kind];component=u.new_object(u.HierarchicalInstancedStaticMeshComponent)
        require(component and component.get_path_name().startswith('/Engine/Transient.'),'Transient unowned HISM required')
        require(component.get_editor_property('static_mesh') is None,'Probe must never bind/read a native asset')
        components.append(component);transforms=[];inputs=[]
        for row in members:
            old=old_values[row['groupId']][row['instanceIndex']]
            original=chosen[(row['groupId'],row['instanceIndex'])]
            transform=u.Transform();transform.set_editor_property('translation',original.translation)
            transform.set_editor_property('rotation',original.rotation);transform.set_editor_property('scale3d',u.Vector(*([row['uniformScale']]*3)))
            require(value(transform)[0]==old[0] and value(transform)[1]==old[1] and value(transform)[2]==[row['uniformScale']]*3,
                    'Probe input must exactly match actual R3 native-wrapper copying; no reconstructed quaternion')
            inputs.append(value(transform));transforms.append(transform)
        require(list(component.add_instances(transforms,True,False,False))==list(range(len(members))),'Transient HISM insertion order/count differs')
        storage[kind]=actual_matrix_rows(component)
        for index,(row,pre)in enumerate(zip(members,inputs)):
            old=old_values[row['groupId']][row['instanceIndex']];actual=g.native_instance_value(component,index);mesh=meshes[row['newMasterId']]
            radius=max(math.hypot(p[0]*actual[2][0],p[1]*actual[2][1])for p in mesh['expectedNativeVerticesCm'])
            height=mesh['rootedHeightCm']*actual[2][2]
            model_input=modeled_matrix(pre);model_output=modeled_matrix(actual)
            actual_footprint=None
            if storage[kind]['available']:
                matrix=storage[kind]['rows'][index]
                local=[[sum(p[j]*matrix[j][axis]for j in range(3))for axis in range(3)]for p in mesh['expectedNativeVerticesCm']]
                actual_footprint={'allVertexRadiusCm':max(math.hypot(p[0],p[1])for p in local),
                    'heightCm':max(p[2]for p in local),'actualNativeStoredDoubleMatrix':matrix,
                    'actualNativeStoredMatrixFloat32Projection':[[g.f32(v)for v in r]for r in matrix],
                    'float32ProjectionIsGpuReadback':False}
            observations.append({'groupId':row['groupId'],'originalIndex':row['instanceIndex'],'kind':kind,'newMasterId':row['newMasterId'],
                'originalNativeValue':old,'preInsertionValue':pre,'recoveredNativeValue':actual,
                'preInsertionRootXYZExact':pre[0]==old[0],'preInsertionRotationExactCopy':pre[1]==old[1],
                'preInsertionUniformScaleExact':pre[2]==[row['uniformScale']]*3,'rootXYZExactAfterInsertion':actual[0]==old[0],
                'rotation':rotation_metrics(old[1],actual[1]),'requestedUniformScale':row['uniformScale'],
                'scaleAbsoluteComponentDifferences':[abs(v-row['uniformScale'])for v in actual[2]],
                'maximumScaleComponentDifference':max(abs(v-row['uniformScale'])for v in actual[2]),
                'originalSourceYawDeg':row['originalSourceRow']['yawDeg'],'authoredHeightCm':row['authoredHeightCm'],
                'sourceRootedNativeFloat32HeightCm':mesh['rootedHeightCm'],
                'rootedNativeHeightVsOriginalProviderCm':mesh['rootedHeightCm']-originals[kind]['originalHeightCm'],
                'decodedAllVertexRadiusCm':radius,'originalSourceScaledRadiusCm':row['scaledAllVertexRadiusCm'],
                'radiusDifferenceCm':radius-row['scaledAllVertexRadiusCm'],'decodedHeightCm':height,
                'heightDifferenceCm':height-row['authoredHeightCm'],'fullVertexRadiusAtMost14Cm':radius<=14.,
                'actualStoredMatrixFullVertexFootprint':actual_footprint,
                'modeledPreInsertionDoubleMatrix':model_input,'modeledRecoveredDoubleMatrix':model_output,
                'modeledPreInsertionFloat32Matrix':[[g.f32(v)for v in r]for r in model_input],
                'modeledRecoveredFloat32Matrix':[[g.f32(v)for v in r]for r in model_output],
                'modeledMatricesAreActualNativeStorageReadback':False})
    require(len(observations)==64,'Complete64 transform measurements required')
    for c in components:c.clear_instances()
    after_witness=n.g.native_witness(u,importer)
    require(after_witness==before_witness and sha(map_file)==map_sha_before,'Read-only transient probe modified original actor/map bytes')
    state={'schema':'brezi-curved-grass-readonly-map-transient-transform-numeric-probe-r2','owner':OWNER,
        'status':'actual-transient-64-hism-transform-comparison-completed','nativeProcessId':os.getpid(),
        'sourceProbe':pin(ROOT/OWNER),'sourceNativeHelper':pin(ROOT/n.OWNER),'originalMembersBefore':pin(VALUES),
        'failedNativeReport':pin(FAILED/'curved-grass-native-report-r3.json'),'originalPlan':pin(plan_path),
        'preservedUnfaithfulConstructorProbe':pin(FAILED/'curved-grass-transform-numeric-probe-r1.json'),
        'inputRotationSource':'Actual selected original u.Transform.rotation copied directly, identical to R3 apply_scene; no u.Quat constructor.',
        'initialConstructorProbeUsedForAcceptance':False,
        'originalGeometry':plan['geometry'],'originalSourceGlb':plan['sourceGlb'],'rootSelection':plan['rootSelection'],
        'sourceGLBFloat32AttributeProof':g.decode_glb(g.check_pin(plan['sourceGlb']),rows),
        'transientComponents':3,'transientInstances':64,'originalNativeGroupCounts':expected_indices,
        'allPreInsertionRootXYZExact':all(r['preInsertionRootXYZExact']for r in observations),
        'allPreInsertionRotationExactCopies':all(r['preInsertionRotationExactCopy']for r in observations),
        'allPreInsertionUniformScalesExact':all(r['preInsertionUniformScaleExact']for r in observations),
        'allRootXYZExactAfterInsertion':all(r['rootXYZExactAfterInsertion']for r in observations),
        'maximumQuaternionComponentDifference':max(r['rotation']['maximumSignEquivalentComponentDifference']for r in observations),
        'maximumRotationAngleDegrees':max(r['rotation']['relativeRotationAngleDegrees']for r in observations),
        'maximumUniformScaleComponentDifference':max(r['maximumScaleComponentDifference']for r in observations),
        'maximumAbsoluteHeightDifferenceCm':max(abs(r['heightDifferenceCm'])for r in observations),
        'maximumAbsoluteRadiusDifferenceCm':max(abs(r['radiusDifferenceCm'])for r in observations),
        'maximumDecodedAllVertexRadiusCm':max(r['decodedAllVertexRadiusCm']for r in observations),
        'allFullVertexRadiiAtMost14Cm':all(r['fullVertexRadiusAtMost14Cm']for r in observations),
        'nativeStoredMatrixReadback':storage,'matrixStorageSourceType':'Installed primary current struct declares FMatrix; FMatrix44f is a deprecated/render representation.',
        'engineSourceEvidence':{name:pin(Path('/Users/Shared/Epic Games/UE_5.8/Engine')/relative)for name,relative in {
            'instanceStruct':'Source/Runtime/Engine/Classes/Components/InstancedStaticMeshComponent.h',
            'instanceMatrixStorageAndGetTransform':'Source/Runtime/Engine/Private/InstancedStaticMesh.cpp',
            'hismInsertion':'Source/Runtime/Engine/Private/HierarchicalInstancedStaticMesh.cpp',
            'newObjectDefaultTransientPackage':'Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyCore.cpp'}.items()},
        'observations':observations,'mapOpenedByProbe':True,'originalMapReadOnly':True,'originalActorWitnessUnchanged':True,
        'originalActorWitnessBeforeSha256':digest(before_witness),'originalActorWitnessAfterSha256':digest(after_witness),
        'originalMapSha256':map_sha_before,'actorSpawned':False,'newTransientComponentsRegistered':False,
        'nativeAssetsLoadedReadOnlyAsMapReferences':True,'nativeAssetWrites':False,'mapSaved':False,'gpuLaunch':False,'numericAcceptanceGateChanged':False,
        'nativeAppearanceAccepted':False,'performanceAccepted':False}
    write(output,state);print(json.dumps({'probe':pin(output),'rows':64,'maximumRotationAngleDegrees':state['maximumRotationAngleDegrees'],
        'maximumUniformScaleComponentDifference':state['maximumUniformScaleComponentDifference'],
        'maximumAbsoluteHeightDifferenceCm':state['maximumAbsoluteHeightDifferenceCm'],'allRootXYZExact':state['allRootXYZExactAfterInsertion'],
        'allFullVertexRadiiAtMost14Cm':state['allFullVertexRadiiAtMost14Cm']}))


if __name__=='__main__':main()
