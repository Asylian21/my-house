"""Root-only read-only original map probe; writes only own diagnostic output.

All matrix setter experiments use unowned, unregistered transient components.
Original map/actors/assets/Config/Source/Binaries are never edited or saved.
"""
import importlib.util
import os
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-realism-grass-coverage-probe-r1.py'
s=importlib.util.spec_from_file_location('coverage_raw_matrix_probe_guard',ROOT/'scripts/unreal/exterior-realism-grass-coverage-probe-guards-r1.py')
guard=importlib.util.module_from_spec(s);s.loader.exec_module(guard)
n=guard.n
require,read,write,sha,pin,digest,now=(getattr(guard,k)for k in ('require','read','write','sha','pin','digest','now'))
REPORT='original-grass-raw-matrix-probe.json'
PLANES=('x_plane','y_plane','z_plane','w_plane')


def matrix_values(matrix):return [[float(getattr(getattr(matrix,plane),axis))for axis in 'xyzw']for plane in PLANES]
def matrices(component):return [matrix_values(row.get_editor_property('transform'))for row in component.get_editor_property('per_instance_sm_data')]


def reconstructed_data(source,values):
    """Use actual native wrapper types, avoiding float32 u.Matrix/u.Plane aliases."""
    matrix_type=type(source.get_editor_property('transform'));matrix=matrix_type()
    original=source.get_editor_property('transform')
    for key,row in zip(PLANES,values):
        plane=type(getattr(original,key))()
        for axis,value in zip('xyzw',row):plane.set_editor_property(axis,value)
        matrix.set_editor_property(key,plane)
    result=type(source)();result.set_editor_property('transform',matrix)
    require(guard.binary64_equal(matrix_values(result.get_editor_property('transform')),values),
        'Actual wrapper-type reconstruction changed a native binary64 matrix coordinate')
    return result


def transient_test(u,source_rows,raw_values,original_values,native_value,reconstructed=False):
    component=u.new_object(u.HierarchicalInstancedStaticMeshComponent)
    require(component and component.get_path_name().startswith('/Engine/Transient.')and component.get_owner()is None
        and component.get_editor_property('static_mesh')is None,'Unowned transient HISM without any mesh/actor required')
    rows=[reconstructed_data(source,values)for source,values in zip(source_rows,raw_values)]if reconstructed else source_rows
    component.set_editor_property('per_instance_sm_data',rows)
    stored=matrices(component)
    recovered=[native_value(component,index)for index in range(len(rows))]
    return {'transientPath':component.get_path_name(),'ownerIsNone':True,'nativeAssetBound':False,
        'instanceCount':component.get_instance_count(),'rawMatrixBinary64Sha256':guard.binary64_matrix_hash(stored),
        'allMatrixCoordinatesBinary64Exact':guard.binary64_equal(stored,raw_values),
        'allRecoveredNativeFramesExactlyOriginal':guard.binary64_equal(recovered,original_values),
        'orderedRecoveredNativeFramesSha256':digest(recovered),'usedOriginalWrappedRows':not reconstructed,
        'usedActualNativeWrapperTypes':reconstructed,'componentRegistrationRequested':False,'actorSpawnRequested':False},component


def main():
    import unreal as u
    path=Path(os.environ['BREZI_REALISM_GRASS_COVERAGE_PROBE_PLAN']).resolve()
    require(path==guard.PLAN and sha(path)==os.environ['BREZI_REALISM_GRASS_COVERAGE_PROBE_PLAN_SHA256'],'Probe plan changed')
    plan,bundle,original=guard.validate_plan(path);output=Path(os.environ['BREZI_REALISM_GRASS_COVERAGE_PROBE_OUTPUT']).resolve()
    require(output==guard.OUTPUT and not(output/REPORT).exists(),'Only fresh own immutable probe output eligible')
    output.mkdir(parents=True,exist_ok=True);project=n.guard.BASE/'Project/BreziTwin'
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project,'Only original unchanged R16 may be read')
    before_content=n.g.inventory(project/'Content');before_protected=n.g.project_proof(project)
    require(before_content==bundle['content']and before_protected==bundle['protected'],'Original R16 native project changed before read-only probe')
    h=n.helpers(bundle)  # actual frozen-first order before every current helper
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem);require(levels.load_level(n.MAP),'Cannot load original R16 map for read-only observation')
    before=n.full_witness(u,h);require(before==bundle['before']and len(before)==5306,'Original full5306 actor witness changed')
    grass=h['grass'];values,_,components=grass.capture_original_instances(u,bundle['base'],bundle['grassSelected'])
    guard.validate_original_values(values,bundle['base'],original)
    observations={};raw_groups={};transients=[]
    for group in sorted(guard.GROUP_COUNTS):
        component=components[group];data=component.get_editor_property('per_instance_sm_data')
        raw=[matrix_values(row.get_editor_property('transform'))for row in data]
        require(len(raw)==guard.GROUP_COUNTS[group]and component.get_instance_count()==len(raw),'All original ordered matrix rows required')
        control={'groupId':group,'actor':bundle['base']['geometry']['groups'][group]['actor'],'component':component.get_path_name(),
            'count':len(raw),'matrixBinary64Sha256':guard.binary64_matrix_hash(raw),'matrixCanonicalJsonSha256':digest(raw),
            'orderedNativeFramesSha256':digest(values[group]),'nativeMatrixType':str(type(data[0].get_editor_property('transform'))),
            'nativePlaneType':str(type(data[0].get_editor_property('transform').x_plane)),'nativeInstanceDataType':str(type(data[0])),
            'originalCullCm':[component.get_editor_property(k)for k in ('instance_start_cull_distance','instance_end_cull_distance')],
            'instancingRandomSeed':int(component.get_editor_property('instancing_random_seed')),
            'additionalRandomSeeds':[{'startInstanceIndex':int(row.get_editor_property('start_instance_index')),
                'randomSeed':int(row.get_editor_property('random_seed'))}for row in component.get_editor_property('additional_random_seeds')],
            'numCustomDataFloats':int(component.get_editor_property('num_custom_data_floats')),
            'customData':[float(v)for v in component.get_editor_property('per_instance_sm_custom_data')]}
        for mode in ('wrappedCopy','doubleTypeReconstruction'):
            try:
                result,transient=transient_test(u,data,raw,values[group],grass.guard.native_instance_value,mode=='doubleTypeReconstruction');transients.append(transient)
                control[mode]={'available':True,**result}
            except Exception as error:control[mode]={'available':False,'error':str(error)}
        observations[group]=control;raw_groups[group]=raw
    for group,component in components.items():
        require(guard.binary64_equal(matrices(component),raw_groups[group]),'Original raw matrix bits changed in memory: '+group)
        control=observations[group]
        require(component.get_instance_count()==control['count']
            and int(component.get_editor_property('instancing_random_seed'))==control['instancingRandomSeed']
            and int(component.get_editor_property('num_custom_data_floats'))==control['numCustomDataFloats']
            and [float(v)for v in component.get_editor_property('per_instance_sm_custom_data')]==control['customData']
            and [{'startInstanceIndex':int(row.get_editor_property('start_instance_index')),
                'randomSeed':int(row.get_editor_property('random_seed'))}for row in component.get_editor_property('additional_random_seeds')]==control['additionalRandomSeeds'],
            'Original per-instance custom data/random seed controls changed in memory: '+group)
    require(n.full_witness(u,h)==before and n.g.inventory(project/'Content')==before_content
        and n.g.project_proof(project)==before_protected,'Read-only probe changed original scene/project bytes')
    guard.validate_plan(path)
    matrix_file=output/'original-four-grass-group-raw-matrices.json';write(matrix_file,raw_groups)
    witness_file=output/'original-r16-full-actor-witness.json';write(witness_file,before)
    ready=all(row[mode].get('available')and row[mode].get('allMatrixCoordinatesBinary64Exact')
        and row[mode].get('allRecoveredNativeFramesExactlyOriginal')for row in observations.values()for mode in ('wrappedCopy','doubleTypeReconstruction'))
    state={'schema':guard.SCHEMA,'owner':OWNER,'status':'verified-read-only-original-r16-four-group-raw-matrix-capture',
        'completedAt':now(),'nativeProcessId':os.getpid(),'sourceProject':str(project),'output':str(output),'selectedPlan':pin(path),
        'originalBaseNativeReport':plan['baseNativeReport'],'originalMembers':plan['originalMembers'],'inputFiles':plan['inputFiles'],
        'engineSourceEvidence':plan['engineSourceEvidence'],'groups':observations,'groupCount':4,'instanceCount':8949,
        'rawMatrices':pin(matrix_file),'originalActorWitness':pin(witness_file),'originalActorWitnessSha256':digest(before),
        'sourceContentInventorySha256':digest(before_content),'sourceProtectedProjectSha256':digest(before_protected),
        'original5306ActorsUnchanged':True,'original8949RawMatricesAndInstanceControlsUnchangedBeforeAfter':True,'original3975ContentUnchanged':True,'original132ProtectedFilesUnchanged':True,
        'sourceAssetsMutated':False,'sourceMapSaved':False,'sourceActorOrComponentMutationPerformed':False,
        'transientComponentPropertyWritesPerformed':True,'componentRegistrationRequested':False,'actorSpawnRequested':False,
        'rawMatrixRestorationReady':ready,'futureRestorationCullPolicyCm':[18000,24000],
        'restorationApplied':False,'nativeAppearanceAccepted':False,'performanceAccepted':False,'fullPhotorealismAccepted':False,
        'shippingPackageProduced':False,'originalR22cCandidateNeverMutated':True,'moduleOrderWitness':h['moduleOrderWitness']}
    write(output/REPORT,state);print(__import__('json').dumps({'report':pin(output/REPORT),'groups':4,'instances':8949,
        'rawMatrixRestorationReady':ready,'originalSceneUnchanged':True,'nativeAppearanceAccepted':False}))


if __name__=='__main__':main()
