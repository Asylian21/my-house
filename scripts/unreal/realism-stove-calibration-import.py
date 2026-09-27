"""Single material/slot flame emission calibration over immutable R6 Content."""
import copy
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/realism-stove-calibration-import.py'
PREFIX = '/Game/Brezi/Realism/StoveCalibration'
MAP = '/Game/Brezi/Maps/Brezi'
MAP_FILE = 'Brezi/Maps/Brezi.umap'

def helper_module():
    spec=importlib.util.spec_from_file_location('frozen_room_witness', ROOT/'scripts/unreal/realism-room-details-import.py')
    value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value

helper=helper_module()
require,sha,read,write,now,digest,module,inventory=(getattr(helper,name) for name in
    ('require','sha','read','write','now','digest','module','inventory'))
witness=helper.witness


def validate_changes(before,after,content,complete=False):
    content=Path(content).resolve();target=content/'Brezi/Realism/StoveCalibration/Materials/M_Stove_Flames_512.uasset'
    require(before.keys()<=after.keys(),'Original Content removed')
    for path,value in before.items():
        require(path==str(content/MAP_FILE) or after[path]==value,'Original Content changed: '+path)
    added=after.keys()-before.keys()
    require(added<={str(target)} and (not complete or added=={str(target)}),'Calibration may add exactly one owned material package')


def expected_witness(original,changes):
    require(len(changes)==1,'Calibration must change exactly one material slot')
    change=changes[0];result=copy.deepcopy(original)
    require(change['actor'] in result and change['slot']==0,'Unexpected calibration actor or slot')
    found=[c for c in result[change['actor']]['components'] if c['path']==change['component']]
    require(len(found)==1 and found[0]['materials']==[change['before']],'Original flame binding differs')
    require(change['before']=='/Game/Brezi/Realism/Stove/Materials/M_Stove_Flames.M_Stove_Flames','Unexpected source flame material')
    require(change['after']==PREFIX+'/Materials/M_Stove_Flames_512.M_Stove_Flames_512','Unexpected calibrated material')
    found[0]['materials']=[change['after']]
    return result


def verify_witness(expected,actual):
    require(expected==actual,'Calibration changed geometry, lights, glass, exposure, collision, actors or unrelated bindings')


def restore(output):
    output = Path(output).resolve()
    report = read(output / 'realism-stove-calibration-report.json')
    require(report['status'] == 'failed', 'No failed stove attempt')
    base = module('fixture_restore_paths', 'performance-optimize.py')
    source, output = base.checked_paths(report['sourceOutput'], output)
    require(report['output'] == str(output), 'Failed stove report belongs elsewhere')
    try:
        os.kill(report['nativeProcessId'], 0)
    except ProcessLookupError:
        pass
    else:
        raise RuntimeError('Native stove process is still running')
    content = output / 'Project/BreziTwin/Content'
    current = inventory(content)
    require(current == report['failedContentHashes'], 'Stove Content drift after failure')
    before = report['beforeAssetHashes']
    validate_changes(before, current, content)
    backup = output / 'realism-stove-calibration-checkpoint/Brezi.umap'
    require(sha(backup) == before[str(content / MAP_FILE)], 'Stove map backup drift')
    require(read(output / 'performance-source.json')['content'] == before, 'Inherited stove source drift')
    donor = source / 'Project/BreziTwin/Content'
    require(inventory(donor) == {str(donor / Path(p).relative_to(content)): value for p, value in before.items()}, 'Stove donor changed')
    history = output / 'realism-stove-calibration-history' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    history.mkdir(parents=True)
    shutil.copy2(content / MAP_FILE, history / 'failed-Brezi.umap')
    shutil.copy2(backup, content / MAP_FILE)
    for path in current.keys() - before.keys():
        target = history / 'failed-assets' / Path(path).relative_to(content)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(path, str(target))
    require(inventory(content) == before, 'Stove restoration not exact')
    for name in ['realism-stove-calibration-report.json', 'realism-stove-calibration-process.json', 'realism-stove-calibration.log', 'realism-stove-calibration.log.json', 'realism-stove-calibration-checkpoint']:
        path = output / name
        if path.exists():
            shutil.move(str(path), str(history / name))
    write(history / 'restoration.json', {'status': 'stove-calibration-failure-restored', 'generatedAt': now(), 'contentHashes': before})
    print(json.dumps({'status': 'stove-calibration-failure-restored', 'history': str(history)}))


def main():
    import unreal as u
    base=module('calibration_geometry_witness','performance-optimize.py')
    require(all(os.environ.get(k) for k in ('BREZI_MODEL_OUTPUT','BREZI_PERFORMANCE_SOURCE')),'Explicit inherited project required')
    source,output=base.checked_paths(ROOT/os.environ['BREZI_PERFORMANCE_SOURCE'],ROOT/os.environ['BREZI_MODEL_OUTPUT'])
    project=output/'Project/BreziTwin';content=project/'Content';before=inventory(content)
    require(Path(u.Paths.project_dir()).resolve()==project,'Wrong calibration project')
    provenance=read(output/'performance-source.json')
    require(provenance['status']=='verified-scene-inherited' and provenance['donor']==str(source)
            and provenance['content']==before,'Unverified calibration inheritance')
    names=('realism-stove-calibration-report.json','realism-stove-report.json','realism-furniture-report.json',
           'realism-room-details-report.json','realism-fixtures-report.json','realism-import-report.json',
           'performance-scene-report.json','nanite-study-report.json')
    require(not any((output/name).exists() for name in names),'Calibration requires fresh inherited output')
    donor=source/'Project/BreziTwin/Content';source_before=inventory(donor)
    require({str(content/Path(p).relative_to(donor)):value for p,value in source_before.items()}==before,'Calibration donor differs')
    material=module('stove_calibration_material','realism-stove-calibration-material.py')
    pipeline={str(ROOT/'scripts/unreal'/name):sha(ROOT/'scripts/unreal'/name) for name in
              ('realism-stove-calibration-import.py','realism-stove-calibration-material.py','realism-room-details-import.py',
               'realism-fixtures-import.py','performance-optimize.py','performance_scene_policy.py')}
    inputs={str(p):sha(p) for p in sorted((output/'geometry').rglob('*')) if p.is_file()}
    report={'schemaVersion':1,'owner':OWNER,'status':'pending','startedAt':now(),'nativeProcessId':os.getpid(),
            'project':str(project),'output':str(output),'sourceOutput':str(source),'beforeAssetHashes':before,
            'pipelineFiles':pipeline,'inputFiles':inputs,'emissionBefore':3,'emissionAfter':512,'renderedVerified':False}
    checkpoint=output/'realism-stove-calibration-checkpoint';checkpoint.mkdir(exist_ok=False)
    shutil.copy2(content/MAP_FILE,checkpoint/'Brezi.umap')
    write(output/'realism-stove-calibration-report.json',report)
    try:
        actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
        require(levels.load_level(MAP),'Cannot load calibration baseline')
        original=witness(base,u,actors)
        report['material']=material.apply(u,actors,output)
        report['bindingChanges']=report['material']['bindingChanges']
        expected=expected_witness(original,report['bindingChanges']);authored=witness(base,u,actors)
        verify_witness(expected,authored)
        require(levels.save_current_level(),'Cannot save calibration map')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False),'Cannot unload calibration map')
        require(levels.load_level(MAP),'Cannot reload calibration map')
        reloaded=witness(base,u,actors);verify_witness(expected,reloaded)
        require(authored==reloaded,'Saved calibration witness differs')
        report['savedMaterialReadback']=material.verify(u,actors,report['material'])
        for field in ('pipelineFiles','inputFiles'):
            for path,value in report['material'].get(field,{}).items():
                absolute=str((ROOT/path).resolve())
                require(sha(absolute)==value,'Calibration input changed: '+absolute)
                require(absolute not in report[field] or report[field][absolute]==value,'Conflicting calibration pin')
                report[field][absolute]=value
        after=inventory(content);validate_changes(before,after,content,complete=True)
        require(source_before==inventory(donor),'Calibration donor changed')
        for path,value in {**report['pipelineFiles'],**report['inputFiles']}.items():
            require(sha(path)==value,'Calibration input changed during authoring')
        report.update(status='realism-stove-calibration-validated',savedReloaded=True,protectedContentUnchanged=True,
                      sourceGeometryCollisionAndTransformsPreserved=True,originalMaterialsPreserved=True,
                      originalLightingExposureAndGlassPreserved=True,originalActorCount=len(original),finalActorCount=len(reloaded),
                      protectedActorWitnessSha256=digest(expected),savedProtectedActorWitnessSha256=digest(reloaded),
                      authoredActorWitnessSha256=digest(authored),savedActorWitnessSha256=digest(reloaded),
                      afterAssetHashes=after,newAssets=sorted(after.keys()-before.keys()),
                      changedAssets=[{'path':p,'beforeSha256':before[p],'afterSha256':after[p]} for p in before if before[p]!=after[p]])
        u.log('BREZI_REALISM_STOVE_CALIBRATION validated')
    except Exception as error:
        report.update(status='failed',error=str(error),failedContentHashes=inventory(content));raise
    finally:
        report['generatedAt']=now();write(output/'realism-stove-calibration-report.json',report)


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--restore':restore(sys.argv[2])
    else:main()
