"""Read-only eight local compositions and unowned meshless instance observations.

The only proposed write calibration affects a NEW local value struct scalar when
zero compares numerically equal but has the wrong exact binary64 sign. No actor,
asset, import, registration, or map setter is available in this diagnostic.
"""
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighbor-props-transform-composition-diagnostic-r2.py'
SOURCE_HELPER = ROOT/'scripts/unreal/exterior-neighbor-props-transform-constructor-diagnostic-r1.py'
SOURCE_HELPER_SHA = '3987fe832bb22fb4369efb62597b26758f9ea50d022605057753cf282d3fb97c'
s = importlib.util.spec_from_file_location('_r39_readonly_constructor_observation_helpers', SOURCE_HELPER)
d = importlib.util.module_from_spec(s);s.loader.exec_module(d)
require, pin, read, binary64 = d.require, d.pin, d.read, d.binary64
require(pin(SOURCE_HELPER)['sha256'] == SOURCE_HELPER_SHA, 'Frozen first read-only source changed')
OUTPUT = ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-transform-composition-diagnostic-r2'
REPORT = OUTPUT/'transform-composition-report.json'
OBSERVED = d.OUTPUT/'transform-constructor-report.json'
OBSERVED_SHA = 'b53382a4a2aa91e49a248832a8d35d01f90fb84dd68bafccfa98a772907a105c'
OBSERVED_LAUNCH = ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-transform-diagnostic-launch-r1'
OBSERVED_PROCESS = OBSERVED_LAUNCH/'transform-constructor-diagnostic-r1-process.json'
OBSERVED_PROCESS_SHA = '92fbd5d3061409433b7c5f39c39dcef5091ca8d589507a4b84e678aa3991065e'
OBSERVED_RAW = OBSERVED_LAUNCH/'transform-constructor-diagnostic-r1.log.json'
OBSERVED_RAW_SHA = '4b5d18e376f5e8bacdb2603a27dc25905a6b9ffca44a74511da926cdda9d6167'
OBSERVED_AUDIT = OBSERVED_LAUNCH/'root-readonly-diagnostic-current-byte-audit-r2.json'
OBSERVED_AUDIT_SHA = '567d86745a2f56427abbcf0c1303117ad3aff436cd0fa8c961a93db9fbe572ce'


def binary_equal(a, b):
    return struct.pack('<d', float(a)) == struct.pack('<d', float(b))


def value(v):
    return [[float(getattr(v.translation, k)) for k in 'xyz'],
            [float(getattr(v.rotation, k)) for k in 'xyzw'],
            [float(getattr(v.scale3d, k)) for k in 'xyz']]


def mismatch_paths(a, b, path=''):
    if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)) and not isinstance(b, bool):
        return [] if binary_equal(a,b) else [{'path': path, 'actual': binary64(a), 'expected': binary64(b)}]
    require(isinstance(a,list) and isinstance(b,list) and len(a)==len(b), 'Recorded numeric array shape differs: '+path)
    return [item for i,(x,y) in enumerate(zip(a,b)) for item in mismatch_paths(x,y,path+'/'+str(i))]


def packed(a):
    return [packed(v) for v in a] if isinstance(a,list) else binary64(a)


def write_new_local_scalar(wrapped, axis, requested, events):
    """Only new local fields; positive/negative zeros still compare bit-exactly."""
    requested=float(requested);require(math.isfinite(requested), 'Finite authored local input required')
    before=float(wrapped.get_editor_property(axis))
    row={'axis':axis,'before':binary64(before),'requested':binary64(requested),
         'newLocalWrapperType':type(wrapped).__name__,'zeroBitMismatchIntermediateUsed':False}
    if before==0. and requested==0. and not binary_equal(before,requested):
        wrapped.set_editor_property(axis,1.)
        intermediate=float(wrapped.get_editor_property(axis))
        row.update(zeroBitMismatchIntermediateUsed=True, finiteIntermediateRequested=binary64(1.),
                   finiteIntermediateObserved=binary64(intermediate))
        require(binary_equal(intermediate,1.), 'Exact new-local finite intermediate write was not observed')
    wrapped.set_editor_property(axis,requested)
    row['after']=binary64(float(wrapped.get_editor_property(axis)))
    row['requestedBitsObservedExact']=binary_equal(row['after']['value'],requested)
    events.append(row)
    require(row['requestedBitsObservedExact'], 'Exact requested local field bits were not observed: '+axis)


def new_transform(u,wanted):
    t=u.Transform();events=[]
    for key,axes,numbers in zip(('translation','rotation','scale3d'),('xyz','xyzw','xyz'),wanted):
        local=t.get_editor_property(key);steps=[]
        for axis,n in zip(axes,numbers):write_new_local_scalar(local,axis,n,steps)
        t.set_editor_property(key,local)
        events.append({'property':key,'scalarWrites':steps,'afterTransformCopyBack':d.struct_info(t.get_editor_property(key),axes)})
    got=value(t)
    return t, {'expectedValues':wanted,'actualValues':got,'binary64Actual':packed(got),
               'exactMismatchPaths':mismatch_paths(got,wanted),'newLocalScalarEvents':events,
               'onlyZeroBitMismatchUsesIntermediate':True,'allOtherValuesWrittenWithoutAdaptation':True}


def instance_value(component,index):
    got=component.get_instance_transform(index,False)
    if isinstance(got,tuple):
        require(got[0] is True, 'Actual transient instance getter failed');got=got[1]
    return got


def matrix(component,index):
    v=component.get_editor_property('per_instance_sm_data')[index].get_editor_property('transform')
    return [[float(getattr(getattr(v,p),axis)) for axis in 'xyzw'] for p in ('x_plane','y_plane','z_plane','w_plane')]


def main():
    import unreal as u
    require(Path(os.environ['BREZI_NEIGHBOR_PROPS_COMPOSITION_DIAGNOSTIC_OUTPUT']).resolve()==OUTPUT
            and Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==d.PROJECT,
            'Exact fresh observation output and failed original-preserved R39b project required')
    require(not OUTPUT.exists(), 'Never overwrite a read-only observation')
    require(pin(OBSERVED)['sha256']==OBSERVED_SHA, 'Exact actually closed six-root observation changed')
    observed=read(OBSERVED)
    require(observed['status']=='completed-read-only-six-authored-transform-observations'
            and observed['nativeProcessId']==56781 and observed['fullConstructorRowsObserved']==6
            and observed['sourceInputsUnchanged'] is True,
            'Actually closed exact constructor observations required')
    for path,wanted in ((OBSERVED_PROCESS,OBSERVED_PROCESS_SHA),(OBSERVED_RAW,OBSERVED_RAW_SHA),(OBSERVED_AUDIT,OBSERVED_AUDIT_SHA)):
        require(pin(path)['sha256']==wanted, 'Exact read-only diagnostic terminal/current-byte evidence changed')
    terminal,raw,post=read(OBSERVED_PROCESS),read(OBSERVED_RAW),read(OBSERVED_AUDIT)
    require(raw['pid']==56781 and raw['code']==0 and raw['signal'] is None
            and terminal['reportSha256']==OBSERVED_SHA and terminal['sourcePinsUnchangedAfterNative'] is True
            and len(terminal['sourcePinsBeforeNative'])==14,
            'Actually closed source-exact first read-only diagnostic required')
    require(post['nativeReport']==pin(OBSERVED) and post['nativeProcess']==pin(OBSERVED_PROCESS)
            and post['rawNativeProcess']==pin(OBSERVED_RAW) and post['exitCode']==0
            and post['candidateOriginal4235FilesExact'] is True and post['all21PriorOwnedPartialPackageBytesExact'] is True
            and post['all14DiagnosticSourcePinsExact'] is True and post['newContentPackages']==0
            and post['mapAndProtectedFilesUnchanged'] is True
            and post['all6ObservedMismatchOnlyQuaternionYMinusZeroAgainstPlusZero'] is True,
            'First read-only diagnostic preserved all prior scene/package bytes')
    proposal=read(d.SOURCE);rows=proposal['placements'];require(len(rows)==6, 'Exactly six original assembly inputs required')
    prior={r['assembly']['id']:r for r in observed['rows']}
    for row in rows:
        old=prior[row['id']];diff=old['exactMismatchAxes']
        require(len(diff)==1 and diff[0]['axis']=='rotation.y'
                and diff[0]['actual']['binary64LittleEndian']=='0000000000000080'
                and diff[0]['expected']['binary64LittleEndian']=='0000000000000000'
                and 'constructorObservationError' not in old,
                'Only the actually recorded local zero-bit setter boundary may be calibrated')
    audit=read(d.AUDIT);require(pin(d.AUDIT)['sha256']==d.AUDIT_SHA
            and audit['originalMapByteExact'] is True and audit['oldNativeActorMutationOrMapSaveReached'] is False,
            'Failed map unchanged actual root audit required')
    part_rows={};checkpoints=[]
    for model,row in audit['completedImportFullPartIdentityCheckpoints'].items():
        require(pin(row['path'])==row,'Exact original imported-part checkpoint changed')
        checkpoint=read(row['path']);checkpoints.append(row)
        for part in checkpoint['parts']:
            key=part['sourcePart'];require(key.startswith(model+':') and key not in part_rows,'Unique observed original source part required')
            part_rows[key]=part
    require(set(part_rows)=={'garden_hose_wall_mounted_01:0','garden_hose_wall_mounted_01:1','planter_pot_clay:0','watering_can_metal_01:0'}
            and sum(p['triangles'] for p in part_rows.values())==26601,
            'All four prior full part observations required; no new geometry acceptance')
    property_access=d.ENGINE/'Source/Runtime/CoreUObject/Private/UObject/PropertyAccessUtil.cpp'
    require('AreRealNumbersIdentical' in property_access.read_text() and 'SetPropertyValue_DirectSingle' in property_access.read_text(),
            'Installed numeric-identical direct-setter route changed')
    primary={**d.primary_api(),'numericIdenticalSetter':pin(property_access)}
    evidence={'priorReadOnlyConstructorReport':pin(OBSERVED),'priorReadOnlyConstructorSource':pin(SOURCE_HELPER),
              'priorReadOnlyConstructorProcess':pin(OBSERVED_PROCESS),'priorReadOnlyConstructorRaw':pin(OBSERVED_RAW),
              'priorReadOnlyConstructorCurrentByteAudit':pin(OBSERVED_AUDIT),
              'sourceProposal':pin(d.SOURCE),'failedNativeReport':pin(d.FAILED),'failedNativeProcess':pin(d.PROCESS),
              'failedRawProcess':pin(d.RAW),'rootFailureByteAudit':pin(d.AUDIT)}
    for key,p,wanted in [('sourceProposal',d.SOURCE,d.SOURCE_SHA),('failedNativeReport',d.FAILED,d.FAILED_SHA),
        ('failedNativeProcess',d.PROCESS,d.PROCESS_SHA),('failedRawProcess',d.RAW,d.RAW_SHA)]:
        require(pin(p)['sha256']==wanted,'Exact closed source/failure evidence changed: '+key)
    files={**terminal['sourcePinsBeforeNative'],**{r['path']:r['sha256'] for r in [*evidence.values(),*primary.values(),*checkpoints,pin(ROOT/OWNER)]}}
    require(all(pin(path)['sha256']==wanted for path,wanted in files.items()),'Exact read-only inputs changed before observation')
    OUTPUT.mkdir()
    report={'schema':'brezi-eight-local-original-prop-compositions-readonly-diagnostic-r39-r2','schemaVersion':2,
        'owner':OWNER,'status':'running','nativeProcessId':os.getpid(),'project':str(d.PROJECT),
        'startedAt':datetime.now(timezone.utc).isoformat(),'evidence':evidence,'originalImportedPartCheckpoints':checkpoints,
        'primaryApi':primary,'inputFiles':files,'sixRootConstructors':{},'sourceNodes':{},'compositions':{},'observationErrors':[],
        'newLocalValueStructsAndUnownedMeshlessHismOnly':True,'sceneActorsAssetsOrMapsMutated':False,
        'assetsImportedOrSaved':False,'levelLoadedCreatedOrSaved':False,'componentRegisteredOrAttached':False,
        'newGeometryAttributeDecodePerformed':False,'sourceGeometryOrPhotoPixelsEdited':False,
        'nativeMemoryOwnershipClaimedFromPythonObjectIds':False,'epsilonOrToleranceRelaxationProposed':False,
        'historicalExactFunctionOrZeroConventionsGloballyChanged':False,
        'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'activeOutputPromoted':False}
    def persist():REPORT.write_text(json.dumps(report,sort_keys=True,indent=2,allow_nan=False)+'\n')
    persist();roots={};nodes={}
    for row in rows:
        key=row['id']
        try:
            expected=d.expected_input(row);wanted=[expected[k] for k in ('translation','rotation','scale3d')]
            roots[key],receipt=new_transform(u,wanted);receipt['authoredAssemblyInputs']={k:row[k] for k in ('id','modelId','positionCm','yawDegrees','uniformScale')}
            report['sixRootConstructors'][key]=receipt
        except Exception as e:report['observationErrors'].append({'stage':'new-local-root','assembly':key,'type':type(e).__name__,'error':str(e)})
        persist()
    for key,part in sorted(part_rows.items()):
        try:
            wanted=part['actualImportedNodePose'];nodes[key],receipt=new_transform(u,wanted)
            receipt['actualImportedSourcePart']=part;receipt['createdLocalValueComparedToPriorActuallyImportedPose']=True
            report['sourceNodes'][key]=receipt
        except Exception as e:report['observationErrors'].append({'stage':'new-local-source-node','part':key,'type':type(e).__name__,'error':str(e)})
        persist()
    for key,part in sorted(part_rows.items()):
        component=None
        try:
            model=key.rsplit(':',1)[0];selected=[r for r in rows if r['modelId']==model]
            require(key in nodes and all(r['id'] in roots for r in selected), 'All local input constructors must have been recorded')
            component=u.new_object(u.HierarchicalInstancedStaticMeshComponent)
            require(component and component.get_path_name().startswith('/Engine/Transient.')
                    and component.get_editor_property('static_mesh') is None and component.get_owner() is None,
                    'Unowned meshless transient HISM only')
            result={'part':key,'assemblyRootIds':[],'assemblyInputValues':[],'originalImportedNodeValues':[],
                'independentRootTransformPointValues':[],'composedInputValues':[],'recoveredValues':[],'storedMatrices':[],
                'inputMismatchPaths':[],'recoveredMismatchPaths':[],'matrixTranslationMismatchPaths':[],
                'transientPath':component.get_path_name(),'unownedMeshless':True,'registeredOrAttached':False}
            report['compositions'][key]=result;persist()
            for row in selected:
                root,node=roots[row['id']],nodes[key]
                composed=u.MathLibrary.compose_transforms(node,root)
                point=u.MathLibrary.transform_location(root,node.translation)
                independent=[[float(getattr(point,k)) for k in 'xyz'],value(root)[1],value(root)[2]]
                got=value(composed);index=component.add_instance(composed,False)
                require(index==len(result['assemblyRootIds']),'Exact ordered transient index required')
                result['assemblyRootIds'].append(row['id']);result['assemblyInputValues'].append(value(root))
                result['originalImportedNodeValues'].append(value(node));result['composedInputValues'].append(got)
                result['independentRootTransformPointValues'].append(independent)
                result['inputMismatchPaths'].append(mismatch_paths(got,independent))
                recovered=value(instance_value(component,index));stored=matrix(component,index)
                result['recoveredValues'].append(recovered);result['storedMatrices'].append(stored)
                result['recoveredMismatchPaths'].append(mismatch_paths(recovered,got))
                result['matrixTranslationMismatchPaths'].append(mismatch_paths(stored[3][:3],got[0]))
                persist()
            result['actualInstanceCount']=component.get_instance_count()
            result['composedInputsBinary64']=packed(result['composedInputValues'])
            result['recoveredValuesBinary64']=packed(result['recoveredValues']);result['storedMatricesBinary64']=packed(result['storedMatrices'])
            persist()
        except Exception as e:
            report['observationErrors'].append({'stage':'composition-and-transient','part':key,'type':type(e).__name__,'error':str(e)})
        finally:
            if component is not None:
                try:
                    component.clear_instances()
                    report['compositions'].setdefault(key,{})['transientInstancesAfterClear']=component.get_instance_count()
                    require(component.get_instance_count()==0,'No transient observations may remain')
                except Exception as e:report['observationErrors'].append({'stage':'transient-clear','part':key,'type':type(e).__name__,'error':str(e)})
            persist()
    require(all(pin(path)['sha256']==wanted for path,wanted in files.items()),'Exact read-only source changed')
    report.update(status='completed-read-only-eight-original-part-composition-observations',
        completedAt=datetime.now(timezone.utc).isoformat(),sourceInputsUnchanged=True,
        fullRootConstructorsObserved=len(report['sixRootConstructors']),fullSourceNodesObserved=len(report['sourceNodes']),
        composedMembersObserved=sum(len(r.get('assemblyRootIds',[])) for r in report['compositions'].values()))
    persist();print(json.dumps({'report':pin(REPORT),'status':report['status'],'composedMembersObserved':report['composedMembersObserved'],
                                'observationErrors':len(report['observationErrors'])}),flush=True)


if __name__=='__main__':main()
