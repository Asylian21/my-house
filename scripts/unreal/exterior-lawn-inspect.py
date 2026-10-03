"""Read-only native lawn identity inspection; writes one fresh external receipt.

Run in an isolated project with UnrealEditor-Cmd. No native asset, actor,
component, instance or map is saved or modified by this script.
"""
import hashlib
import json
import math
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parents[2]
MAP='/Game/Brezi/Maps/Brezi'
TAG='BreziPhotorealLawn'


def require(ok,message):
    if not ok:raise RuntimeError(message)


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk:=stream.read(1024*1024):h.update(chunk)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def native_transform(value):
    if isinstance(value,tuple):
        require(len(value)==2 and value[0] is True,'Cannot read native instance transform')
        value=value[1]
    result={key:[float(getattr(vector,axis)) for axis in axes] for key,vector,axes in
            [('p',value.translation,'xyz'),('q',value.rotation,'xyzw'),('s',value.scale3d,'xyz')]}
    require(all(math.isfinite(v) for values in result.values() for v in values),'Non-finite native transform')
    return result


def path(value):
    return value.get_path_name() if value else None


def inventory(content):
    return {str(p.relative_to(content)):sha(p) for p in sorted(content.rglob('*')) if p.is_file()}


def expected_placements(report):
    geometry=report['lawn']['geometry']; pins=geometry['inputFiles']
    reports=[p for p,h in pins.items() if p.endswith('/lawn-geometry/geometry-report.json')
             and h==geometry['geometryReportSha256']]
    require(len(reports)==1,'Historical geometry receipt ambiguity')
    receipt=(ROOT/reports[0]).resolve();require(sha(receipt)==geometry['geometryReportSha256'],'Historical geometry receipt drift')
    placement=receipt.parent/'placement.json';key=str(placement.relative_to(ROOT))
    value=pins.get(str(placement),pins.get(key));require(value and sha(placement)==value,'Historical placement drift')
    data=json.loads(placement.read_text())
    return geometry,{r['id']:r['instances'] for r in data['groups']},{'path':str(placement),'sha256':value}


def comparison(values,expected):
    # Diagnose ordered identity only. A mismatch never authorizes removing,
    # rebinding or hiding an actor; semantic reconciliation is a later step.
    n=min(len(values),len(expected));pe=se=qe=0.;matches=0
    for actual,row in zip(values,expected):
        angle=math.radians(row['yawDegreesUnreal'])/2; q=[0.,0.,math.sin(angle),math.cos(angle)]
        p=max(abs(a-b) for a,b in zip(actual['p'],row['positionUnrealCm']))
        s=max(abs(a-b) for a,b in zip(actual['s'],row['scale']))
        r=min(max(abs(a-sign*b) for a,b in zip(actual['q'],q)) for sign in (1,-1))
        pe=max(pe,p);se=max(se,s);qe=max(qe,r);matches+=int(p<.002 and s<2e-6 and r<2e-5)
    return {'expectedInstances':len(expected),'observedInstances':len(values),'comparedOrderedInstances':n,
            'orderedMatchesWithinOriginalNativeTolerance':matches,'maximumPositionErrorCm':pe,
            'maximumScaleError':se,'maximumQuaternionError':qe,
            'exactOrderedIdentityWithinOriginalNativeTolerance':len(values)==len(expected)==matches}


def main():
    import unreal as u
    output=Path(os.environ['BREZI_LAWN_INSPECT_OUTPUT']).resolve()
    report_path=Path(os.environ['BREZI_LAWN_INSPECT_EXPECTED_REPORT']).resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(),'Inspection receipt must be a fresh output/unreal path')
    require(report_path.is_relative_to(ROOT) and report_path.is_file(),'Missing expected historical receipt')
    expected_report=json.loads(report_path.read_text());geometry,placements,placement_pin=expected_placements(expected_report)
    project=Path(u.Paths.project_dir()).resolve();content=project/'Content'
    require(project.is_relative_to(ROOT/'output/unreal') and content.is_dir(),'Inspection requires an isolated output project')
    before=inventory(content)
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    require(levels.load_level(MAP),'Cannot load inspection map')
    result={'schemaVersion':1,'owner':'scripts/unreal/exterior-lawn-inspect.py','sourceSha256':sha(__file__),
            'status':'native-read-only-lawn-inspection','recordedAtUtc':datetime.now(timezone.utc).isoformat(),
            'processId':os.getpid(),'engineVersion':u.SystemLibrary.get_engine_version(),'project':str(project),'map':MAP,
            'expectedPhotorealReport':{'path':str(report_path),'sha256':sha(report_path)},'expectedSourcePlacement':placement_pin,
            'expectedLegacyGroups':geometry['groups'],'taggedLawnActors':[],'receiptNamedActors':[],
            'otherLawnMeshActors':[],'allHismInventory':[]}
    wanted={r['actor']:key for key,r in geometry['groups'].items()}
    for actor in sorted(actors.get_all_level_actors(),key=lambda a:a.get_path_name()):
        actor_path=actor.get_path_name();tagged=actor.actor_has_tag(TAG)
        for component in actor.get_components_by_class(u.HierarchicalInstancedStaticMeshComponent):
            mesh=component.get_editor_property('static_mesh');mesh_path=path(mesh);count=component.get_instance_count()
            summary={'actor':actor_path,'component':component.get_path_name(),'mesh':mesh_path,'instances':count,
                     'actorTags':list(map(str,actor.get_editor_property('tags'))),
                     'materials':[path(component.get_material(i)) for i in range(component.get_num_materials())]}
            result['allHismInventory'].append(summary)
            lawn_mesh=mesh is not None and mesh.get_name().startswith('LawnTuft')
            if not (tagged or actor_path in wanted or lawn_mesh):continue
            values=[native_transform(component.get_instance_transform(i,False)) for i in range(count)]
            row={**summary,'actorClass':actor.get_class().get_path_name(),'componentClass':component.get_class().get_path_name(),
                 'meshMaterials':[path(m.get_editor_property('material_interface')) for m in mesh.get_editor_property('static_materials')] if mesh else [],
                 'actorTransform':native_transform(actor.get_actor_transform()),'componentWorldTransform':native_transform(component.get_world_transform()),
                 'orderedInstanceTransformsSha256':digest(values),'orderedInstanceTransforms':values,
                 'visible':bool(component.is_visible()),'hiddenInGame':bool(component.get_editor_property('hidden_in_game')),
                 'collision':str(component.get_collision_enabled()),'collisionProfile':str(component.get_collision_profile_name()),
                 'navigation':bool(component.get_editor_property('can_ever_affect_navigation')),
                 'overlap':bool(component.get_editor_property('generate_overlap_events')),
                 'densityScaling':bool(actor.get_detail_density_scaling()) if hasattr(actor,'get_detail_density_scaling') else None,
                 'ownerRootIdentity':component.get_owner()==actor and actor.root_component==component,
                 'cullDistancesCm':[int(component.get_editor_property(k)) for k in ('instance_start_cull_distance','instance_end_cull_distance')],
                 'renderFlags':{k:bool(component.get_editor_property(k)) for k in ('cast_shadow','cast_hidden_shadow',
                     'affect_distance_field_lighting','affect_dynamic_indirect_lighting','affect_indirect_lighting_while_hidden','visible_in_ray_tracing')},
                 'expectedGroupAtActorPath':wanted.get(actor_path),
                 'orderedComparisonsByHistoricalGroup':{key:comparison(values,rows) for key,rows in placements.items()}}
            if tagged:result['taggedLawnActors'].append(row)
            elif actor_path in wanted:result['receiptNamedActors'].append(row)
            else:result['otherLawnMeshActors'].append(row)
    require(before==inventory(content),'Read-only inspection changed Content bytes')
    require(sha(report_path)==result['expectedPhotorealReport']['sha256'],'Historical receipt drift during inspection')
    result['contentUnchanged']=True;result['contentFileCount']=len(before);result['contentInventorySha256']=digest(before)
    result['nativeLawnActorCount']=len(result['taggedLawnActors']);result['nativeLawnInstanceCount']=sum(r['instances'] for r in result['taggedLawnActors'])
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as stream:json.dump(result,stream,indent=2,allow_nan=False);stream.write('\n')
    u.log('BREZI_LAWN_INSPECT '+json.dumps({'receipt':str(output),'taggedActors':result['nativeLawnActorCount'],
          'taggedInstances':result['nativeLawnInstanceCount'],'ContentUnchanged':True}))


if __name__=='__main__':main()
