"""One bounded repair of accepted world-space material normals.

Native commandlet requires BREZI_ARCHVIZ_OUTPUT and the hash-verified archive
normal-refresh-history/before-two-sided-fix. It never saves the map or imports
an asset. Only accepted local-to-world Normal roots gain TwoSidedSign.
After a caught failure and process exit, ordinary Python --restore-failed
restores the backed-up accepted materials/receipts, not the geometry baseline.
"""
import copy
import importlib.util
import json
import os
import shutil
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/archviz-normal-refresh.py'
WRITER='scripts/unreal/archviz-materials.py'


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value


core=load('normal_refresh_core',ROOT/'scripts/unreal/archviz-import.py')
require,sha,read,write,relative=core.require,core.sha,core.read,core.write,core.relative


def assert_packages(before,after,allowed):
    require(before.keys()==after.keys(),'Normal repair changed native package inventory')
    require(all(name in allowed or after[name]==digest for name,digest in before.items()),
            'Normal repair changed protected map/geometry/avatar/light/texture packages')


def preflight(output):
    output,project,geometry,content,_=core.paths(output)
    history=output/'normal-refresh-history/before-two-sided-fix'
    prior_file=history/'archviz-import-report.json';current_file=output/'archviz-import-report.json'
    require(prior_file.read_bytes()==current_file.read_bytes(),'Expected archived successful archviz receipt is not current')
    previous=read(prior_file)
    require(previous['status']=='archviz-import-validated' and previous['savedReloaded'],
            'Normal repair requires successful accepted archviz assets')
    host_file=history/'archviz-import-process.json'
    require(host_file.read_bytes()==(output/'archviz-import-process.json').read_bytes(),'Prior native process binding differs')
    host=read(host_file);process_file=Path(host['processFile'])
    require(host['reportSha256']==sha(prior_file) and sha(process_file)==host['processFileSha256'],
            'Prior native process does not bind archived report')
    process=read(process_file)
    parse=lambda value:core.datetime.fromisoformat(value.replace('Z','+00:00'))
    require(process['code']==0 and parse(process['startedAt'])<=parse(previous['generatedAt'])<=parse(process['endedAt']),
            'Prior native process was not successful and contemporaneous')
    core.check_pins(previous['inputFiles']);core.check_pins(previous['receiptPins'])
    archived_pins={relative(prior_file):sha(prior_file),relative(host_file):sha(host_file),
                   relative(process_file):host['processFileSha256']}
    for name,digest in previous['pipelineFiles'].items():
        old=history/'pipeline'/name
        require(old.is_file() and sha(old)==digest,'Archived accepted pipeline bytes differ: '+name)
        archived_pins[relative(old)]=digest
        if name!=WRITER:require(sha(ROOT/name)==digest,'Only the material normal recipe may change: '+name)
    require(sha(ROOT/WRITER)!=previous['pipelineFiles'][WRITER],'Expected explicit normal recipe change is absent')
    expected={**previous['finalAssetHashes'],relative(content/'Maps/Brezi.umap'):previous['mapFileSha256']}
    require(core.inventory(content)==expected,'Current packages differ from accepted archviz receipt')
    for name in ('archviz-materials-report.json','archviz-lighting-report.json','avatar-import-report.json'):
        require((history/name).read_bytes()==(output/name).read_bytes(),'Archived prior helper receipt differs: '+name)
        archived_pins[relative(history/name)]=sha(history/name)
    return output,project,geometry,content,history,previous,expected,archived_pins


def restore_failed(output):
    output,project,geometry,content,_=core.paths(output)
    history=output/'normal-refresh-history/before-two-sided-fix'
    state=read(history/'normal-refresh-checkpoint.json')
    require(state['owner']==OWNER and state['status']=='failed-recoverable','No caught material-normal failure can be restored')
    try:os.kill(state['nativeProcessId'],0)
    except ProcessLookupError:pass
    else:raise RuntimeError('Native repair process must exit before material restoration')
    core.check_pins(state['inputFiles']);core.check_pins(state['archivedPins'])
    require(core.inventory(content)==state['failedInventory'],'Packages changed after failed material repair')
    assert_packages(state['beforeInventory'],state['failedInventory'],state['allowedPackages'])
    for name,entry in state['backups'].items():
        path=(ROOT/name).resolve();backup=(ROOT/entry['path']).resolve()
        require(name in state['allowedPackages'] and path.is_relative_to(content)
            and backup.is_relative_to(history/'packages') and sha(backup)==state['beforeInventory'][name],
            'Normal repair backup path/hash differs')
    for name,digest in state['failedReceipts'].items():require(sha(ROOT/name)==digest,'Receipt changed after failed repair')
    for name,entry in state['backups'].items():shutil.copy2(ROOT/entry['path'],ROOT/name)
    for name in ('archviz-import-report.json','archviz-materials-report.json'):
        shutil.copy2(history/name,output/name)
    require(core.inventory(content)==state['beforeInventory'],'Restored material inventory differs')
    state.update(status='restored-accepted-archviz',restoredAt=core.now());write(history/'normal-refresh-checkpoint.json',state)
    print('BREZI_NORMAL_REFRESH_RESTORED')


def main():
    import unreal as u
    output,project,geometry,content,history,previous,before,archive_pins=preflight(os.environ['BREZI_ARCHVIZ_OUTPUT'])
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project,'Wrong isolated native project')
    sys.path.insert(0,str(ROOT/'scripts/unreal'))
    materials=load('normal_refresh_current_materials',ROOT/WRITER)
    # Run the exact accepted validator from the archived source. Its sole path
    # remapping resolves its own old code pin to those same verified bytes.
    # Suppress only its report write; all payload/geometry checks execute.
    old_path=history/'pipeline'/WRITER
    old=load('normal_refresh_accepted_materials',old_path)
    old.ROOT=ROOT;old.INPUTS=ROOT/'scripts/unreal/archviz-material-inputs.json'
    old.write_receipt=lambda geometry,report:None
    old_report=copy.deepcopy(previous['archvizMaterials'])
    old_digest=old_report['pipelineFiles'].pop(WRITER)
    require(old_digest==sha(old_path),'Accepted material validator pin differs')
    old_report['pipelineFiles'][relative(old_path)]=old_digest
    import import_scene as base
    import archviz_lighting as lighting
    from hidden_collision import verify_hidden_collision_contract
    from doors import verify_doors_contract
    source=load('normal_refresh_source',ROOT/'scripts/unreal/model-refresh-import.py');source.unreal=u
    baseline=read(output/'model-refresh-import-report.json')
    base.GEOMETRY=geometry;base.REPORT=copy.deepcopy(baseline)
    scene,_,records,_=base.verify_inputs();source.validate_current_source(scene,records)
    actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
    require(u.EditorLoadingAndSavingUtils.new_blank_map(False),'Could not unload startup map')
    require(levels.load_level(core.MAP),'Could not load accepted archviz map')
    old.verify_archviz_materials(scene,geometry,old_report)
    source.verify_reloaded_world(base,actors,records,baseline['materials'],previous['archvizMaterials'])
    lighting.verify_archviz_lighting(scene,actors);core.verify_avatar(u,previous['avatar'])
    verify_hidden_collision_contract(scene,geometry);verify_doors_contract(scene,geometry);base.measure_final_collision(actors)
    slots=[slot for slot,entry in previous['archvizMaterials']['materials'].items() if entry['recipe']['normalSpace']=='local']
    require(len(slots)==28,'Unexpected current world-space normal repair coverage')
    allowed=set()
    for slot in slots:
        package=content.parent/previous['archvizMaterials']['materials'][slot]['asset'].split('.',1)[0].removeprefix('/Game/')
        allowed.update(relative(package.with_suffix(ext)) for ext in ('.uasset','.uexp','.ubulk') if package.with_suffix(ext).is_file())
    checkpoint_file=history/'normal-refresh-checkpoint.json'
    if checkpoint_file.exists():require(read(checkpoint_file)['status']=='restored-accepted-archviz','Existing repair checkpoint has not been restored')
    backups={}
    for name in sorted(allowed):
        target=history/'packages'/(ROOT/name).relative_to(content);target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists():require(sha(target)==before[name],'Prior material backup differs')
        else:shutil.copy2(ROOT/name,target)
        backups[name]={'path':relative(target),'sha256':before[name]}
    state={'schemaVersion':1,'owner':OWNER,'status':'pending','nativeProcessId':os.getpid(),'startedAt':core.now(),
        'beforeInventory':before,'allowedPackages':sorted(allowed),'backups':backups,'inputFiles':previous['inputFiles'],
        'archivedPins':archive_pins,'previousReportSha256':sha(history/'archviz-import-report.json')}
    write(checkpoint_file,state)
    report_path=output/'archviz-normal-refresh-report.json'
    result={'schemaVersion':1,'owner':OWNER,'status':'pending','startedAt':core.now(),
        'previousReportSha256':state['previousReportSha256'],'sourceManifestSha256':previous['sourceManifestSha256'],
        'sourceGlbSha256':previous['sourceGlbSha256'],'materialSlots':slots,'mapModified':False,'geometryReimported':False,
        'pipelineFiles':{WRITER:sha(ROOT/WRITER),OWNER:sha(__file__)},'nativeRenderedVerified':False}
    write(report_path,result)
    try:
        detail=materials.repair_world_normal_facing(scene,geometry,previous['archvizMaterials'])
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False),'Could not unload material-repaired world')
        require(levels.load_level(core.MAP),'Could not reopen material-repaired world')
        detail=materials.verify_archviz_materials(scene,geometry,detail)
        require(detail['worldNormalFacing']['verifiedMaterialCount']==28
            and detail['worldNormalFacing']['tangentMaterialCount']==7,'Saved world-normal correction coverage differs')
        successor=copy.deepcopy(previous)
        successor['archvizMaterials']=detail
        successor['savedReadback']=source.verify_reloaded_world(base,actors,records,baseline['materials'],detail)
        lighting_readback=lighting.verify_archviz_lighting(scene,actors)
        require(lighting_readback==previous['archvizLighting'],'Material repair changed native lights')
        require(core.verify_avatar(u,previous['avatar'])==previous['avatarReadback'],'Material repair changed avatar binding')
        successor['hiddenCollision']=verify_hidden_collision_contract(scene,geometry)
        successor['doors']=verify_doors_contract(scene,geometry);base.measure_final_collision(actors)
        require(base.REPORT['finalCollisionComponents']==previous['finalCollisionComponents'],'Material repair changed collision coverage')
        current=core.inventory(content);assert_packages(before,current,allowed)
        changed=sorted(name for name in before if current[name]!=before[name])
        require(set(changed)==allowed,'Some expected normal materials were not persisted or another package changed')
        core.check_pins(previous['inputFiles']);core.check_pins(archive_pins);core.check_pins(result['pipelineFiles'])
        result.update(status='archviz-normal-refresh-validated',generatedAt=core.now(),savedReloaded=True,
            worldNormalFacing=detail['worldNormalFacing'],changedMaterialPackages=changed,
            mapFileSha256=previous['mapFileSha256'],protectedPackagesUnchanged=True,
            protectedPackageCount=len(before)-len(allowed),inputFiles={**previous['inputFiles'],**archive_pins})
        write(report_path,result)
        successor.update(generatedAt=core.now(),startedAt=result['startedAt'],nativeRenderedVerified=False,
            previousArchvizReportSha256=state['previousReportSha256'],normalFacingRefresh={
                'report':relative(report_path),'sha256':sha(report_path),'worldNormalMaterialCount':28})
        successor['pipelineFiles'].update(result['pipelineFiles'])
        successor['inputFiles'].update(archive_pins)
        successor['receiptPins'][relative(output/'archviz-materials-report.json')]=sha(output/'archviz-materials-report.json')
        successor['receiptPins'][relative(report_path)]=sha(report_path)
        successor['finalAssetHashes']={name:digest for name,digest in current.items() if name!=relative(content/'Maps/Brezi.umap')}
        write(output/'archviz-import-report.json',successor)
        state.update(status='complete',completedAt=core.now(),successorReportSha256=sha(output/'archviz-import-report.json'))
        write(checkpoint_file,state)
        u.log('BREZI_NORMAL_REFRESH '+json.dumps({'status':result['status'],'worldNormalMaterialCount':28,'mapUnchanged':True}))
    except Exception as error:
        result.update(status='failed',generatedAt=core.now(),error=str(error));write(report_path,result)
        current=core.inventory(content)
        try:
            assert_packages(before,current,allowed)
            state.update(status='failed-recoverable',failedInventory=current,error=str(error),
                failedReceipts={relative(output/name):sha(output/name) for name in ('archviz-import-report.json','archviz-materials-report.json')})
        except Exception as integrity:state.update(status='failed-protected-drift',error=str(error),integrityError=str(integrity))
        write(checkpoint_file,state);raise


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--restore-failed':restore_failed(sys.argv[2])
    else:main()
