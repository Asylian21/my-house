"""Pinned source and native-state rejection tests; no editor or asset writes."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import struct
import tempfile
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('exterior_lawn_native_tests', HERE/'exterior-lawn-native.py')
M = importlib.util.module_from_spec(spec); spec.loader.exec_module(M)
NATURAL = M.ROOT/'output/unreal/exterior-lawn-natural-20260930-r1'
REPORT = M.ROOT/'output/unreal/realism-20260926-r5/photoreal-import-report.json'
RURAL = M.ROOT/'output/unreal/realism-20260926-r5/rural-import-report.json'
RURAL_PLAN = M.ROOT/'output/unreal/rural-context-20260923-r4/geometry/rural-context-geometry.json'
INSPECTION = M.ROOT/'output/unreal/lawn-native-inspection-20260930-r1.json'


def read(path):
    return json.loads(Path(path).read_text())


def transform(p=(0.,0.,0.), yaw=0., scale=(1.,1.,1.)):
    a = math.radians(yaw)/2
    return NS(translation=NS(**dict(zip('xyz',p))), rotation=NS(x=0.,y=0.,z=math.sin(a),w=math.cos(a)),
              scale3d=NS(**dict(zip('xyz',scale))))


class Asset:
    def __init__(self,path): self.path=path; self.material=None
    def get_path_name(self): return self.path
    def get_material(self,index): return self.material


class HISM:
    def __init__(self,key,rows):
        path='/Game/Brezi/Photoreal/Lawn/Meshes/lawn-prototypes/StaticMeshes/'+key+'_LOD0.'+key+'_LOD0'
        self.mesh=Asset(path); self.material=Asset(M.LEGACY_MATERIAL); self.mesh.material=self.material
        self.rows=[transform(r['positionUnrealCm'],r['yawDegreesUnreal'],r['scale']) for r in rows]
        self.props={flag:True for flag in M.RENDER_FLAGS}
        self.props.update(hidden_in_game=False,can_ever_affect_navigation=False,generate_overlap_events=False,
                          instance_start_cull_distance=1500,instance_end_cull_distance=2500)
        self.visible=True; self.world=transform(); self.collision='NO_COLLISION'; self.profile='NoCollision'
        self.material_count=1; self.mutations=0; self.actor=None
    def get_path_name(self): return self.actor.path+'.Instances'
    def get_name(self): return 'Instances'
    def get_owner(self): return self.actor
    def get_editor_property(self,name): return self.mesh if name=='static_mesh' else self.props[name]
    def set_editor_property(self,name,value): self.props[name]=value; self.mutations+=1
    def get_instance_count(self): return len(self.rows)
    def get_instance_transform(self,index,world): return (True,self.rows[index])
    def get_world_transform(self): return self.world
    def get_material(self,index): return self.material
    def get_num_materials(self): return self.material_count
    def get_collision_enabled(self): return self.collision
    def get_collision_profile_name(self): return self.profile
    def is_component_tick_enabled(self): return False
    def is_visible(self): return self.visible
    def set_visibility(self,value,propagate): self.visible=value; self.mutations+=1
    def set_hidden_in_game(self,value,propagate): self.props['hidden_in_game']=value; self.mutations+=1


class Actor:
    def __init__(self,path,component):
        self.path=path; self.component=component; component.actor=self; self.world=transform();self.root_component=component
        self.tags={M.LEGACY_TAG,'BreziPhotorealSource:DOM_00001'}; self.density=True
    def get_path_name(self): return self.path
    def get_editor_property(self,name): return self.component if name=='instances' else None
    def actor_has_tag(self,tag): return tag in self.tags
    def get_component_by_class(self,kind): return self.component
    def get_actor_transform(self): return self.world
    def is_actor_tick_enabled(self): return False
    def get_detail_density_scaling(self): return self.density
    def set_detail_density_scaling(self,value): self.density=value; return True


class PinnedNaturalLawn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=read(NATURAL/'lawn-natural-plan.json')
        cls.manifest=read(NATURAL/'geometry-manifest.json')

    def validate(self,plan=None,manifest=None):
        return M.validated_groups(plan or self.plan,manifest or self.manifest,
                                 self.plan['sourceSceneSha256'],self.plan['sourceObjSha256'])

    def test_actual_all_lods_and_24918_crowns_are_safe(self):
        groups=self.validate()
        self.assertEqual((len(groups),sum(len(g['instances']) for g in groups)),(80,24918))
        self.assertEqual({g['meshId'] for g in groups},M.FAMILY)
        self.assertTrue(all(g['role']=='grass' and g['qualityDetail'] is True and g['cullEndCm']==4000 for g in groups))
        self.assertTrue(all(set(r)=={'positionCm','yawDeg','scale'} for g in groups for r in g['instances']))
        self.assertEqual(self.manifest['meshes'][0]['lodScreenSizes'],[1.,.025,.007])

    def test_design_source_and_render_scope_rejections(self):
        mutations=[
            lambda p:p['activeDesign'].update(variant='A'),
            lambda p:p['housePlacement'].update(eastSetbackMm=2999),
            lambda p:p.update(sourceObjSha256='0'*64),
            lambda p:p.update(generatorSha256='0'*64),
            lambda p:p['inputFiles'].pop(str(M.ROOT/'scripts/unreal/lawn-geometry.py')),
            lambda p:p.update(sourceLawnId='DOM_00002'),
            lambda p:p.update(lodScreenSizes=[1.,.15,.04]),
            lambda p:p['renderingPolicy'].update(windDisplacementCm=1),
            lambda p:p['replacementPolicy'].update(meadowYardAndGardenUntouched=False),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                plan=copy.deepcopy(self.plan); mutate(plan)
                with self.assertRaises(RuntimeError):self.validate(plan)

    def test_nonuniform_large_nonfinite_or_elevated_placements_rejected(self):
        cases=[('scale',[1.,1.,1.01]),('scale',[1.26]*3),('scale',[float('nan')]*3),
               ('positionCm',[0.,0.,-6.4]),('yawDeg',float('inf')),('yawDeg',True)]
        for field,value in cases:
            with self.subTest(field=field,value=value):
                plan=copy.deepcopy(self.plan); plan['groups'][0]['instances'][0][field]=value
                with self.assertRaisesRegex(RuntimeError,'placement/scale/elevation'):self.validate(plan)

    def test_measured_crown_height_and_spatial_identity_cannot_be_claimed(self):
        for field in ('radiusCm','actualHeightCm','enclosingRadiusMm','clearanceMm'):
            with self.subTest(field=field):
                plan=copy.deepcopy(self.plan); plan['groups'][0]['instances'][0][field]-=1
                with self.assertRaisesRegex(RuntimeError,'envelope|crown'):self.validate(plan)
        plan=copy.deepcopy(self.plan); plan['groups'][0]['id']='EX_lawn_natural_forged'
        with self.assertRaisesRegex(RuntimeError,'spatial group'):self.validate(plan)

    def test_forged_domain_still_cannot_escape_actual_ground(self):
        plan=copy.deepcopy(self.plan)
        box=[[-100000.,-100000.],[100000.,-100000.],[100000.,100000.],[-100000.,100000.],[-100000.,-100000.]]
        plan['lawnDomainSourceMm']=json.dumps({'type':'MultiPolygon','coordinates':[[box]]})
        row=plan['groups'][0]['instances'][0]; row['positionCm']=[9000.,9000.,-6.5]
        plan['groups'][0]['id']='EX_lawn_natural_4_4_'+plan['groups'][0]['meshId'].removeprefix('lawn_natural_')
        row['clearanceMm']=10000.
        with self.assertRaisesRegex(RuntimeError,'actual source ground'):self.validate(plan)

    def test_keep_union_ignores_internal_seam_but_retains_exterior_step(self):
        polygons=read(RURAL_PLAN)['managedLawnKeepPolygonsCm'];edges=M._union_boundary(polygons)
        # A blade can span the shared join. The exposed part of the same
        # horizontal line remains a real boundary of the L-shaped lawn union.
        shared=[-800.,-40.];exposed=[-1400.,-40.]
        self.assertGreater(min(M._distance(shared,a,b)for a,b in edges),75.)
        self.assertAlmostEqual(min(M._distance(exposed,a,b)for a,b in edges),0.)

    def test_actual_binary_out_of_range_triangle_indices_rejected(self):
        raw=bytearray(Path(self.manifest['meshes'][0]['glbPath']).read_bytes())
        n,kind=struct.unpack_from('<II',raw,12); data=json.loads(raw[20:20+n]); binary_start=20+n+8
        primitive=data['meshes'][data['nodes'][0]['mesh']]['primitives'][0]
        a=data['accessors'][primitive['indices']]; v=data['bufferViews'][a['bufferView']]
        fmt={5121:'B',5123:'H',5125:'I'}[a['componentType']]
        struct.pack_into('<'+fmt,raw,binary_start+v.get('byteOffset',0)+a.get('byteOffset',0),65535)
        with tempfile.TemporaryDirectory(dir=M.ROOT/'output/unreal',prefix='lawn-native-test-') as temporary:
            path=Path(temporary)/'unsafe.glb';path.write_bytes(raw)
            with self.assertRaisesRegex(RuntimeError,'actual triangle indices'):M._glb_geometry(path)


class NativeIdentityAndReload(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=read(REPORT);cls.rural=read(RURAL);cls.rural_plan=read(RURAL_PLAN)
        cls.full_geometry,cls.actual_trimmed,cls.actual_pin,cls.actual_trim_proof=M._trimmed_legacy_placement(cls.report,cls.rural,cls.rural_plan)

    def setUp(self):
        self.geometry=copy.deepcopy(self.full_geometry);self.pin=self.actual_pin;self.placements={};self.native=[]
        self.trim_proof=copy.deepcopy(self.actual_trim_proof)
        for key in M.LEGACY_GROUPS:
            rows=self.actual_trimmed[key]['instances'][:2]
            self.placements[key]={'id':key,'instances':copy.deepcopy(rows)}
            self.native.append(Actor(self.geometry['groups'][key]['actor'],HISM(key,rows)))
            entry=self.trim_proof['groups'][key]
            entry.update(kept=len(rows),transformsSha256=M.digest(M._rural_values([M._transform(v) for v in self.native[-1].component.rows])))
        self.actors=NS(get_all_level_actors=lambda:self.native)
        self.u=NS(HierarchicalInstancedStaticMeshComponent=HISM,CollisionEnabled=NS(NO_COLLISION='NO_COLLISION'))

    def hide(self):
        # Keep rejection fixtures compact; full historical membership and the
        # actual native inspection are exercised separately without this patch.
        with patch.object(M,'_trimmed_legacy_placement',return_value=(self.geometry,self.placements,self.pin,self.trim_proof)):
            return M.hide_original_lawn(self.u,self.actors,self.report,self.rural,self.rural_plan)

    def test_actual_legacy_pin_contains_exact_four_receipt_bound_groups(self):
        geometry,placements,pin=M._legacy_placement(self.report)
        self.assertEqual(sum(len(v['instances']) for v in placements.values()),98344)
        self.assertEqual({v['variant'] for v in geometry['groups'].values()},{0,1,2,3})
        self.assertEqual(M.sha(pin['path']),pin['sha256'])
        geometry,selected,pin,proof=M._trimmed_legacy_placement(self.report,self.rural,self.rural_plan)
        self.assertEqual([len(selected[k]['instances']) for k in M.LEGACY_GROUPS],[10118,10153,10147,10019])
        self.assertEqual(proof['retainedInstances'],40437)
        self.assertEqual(proof['removedByHistoricalRuralImport'],57907)

    def test_actual_native_readonly_inspection_has_exact_trimmed_sequence(self):
        inspection=read(INSPECTION)
        self.assertTrue(inspection['contentUnchanged']);self.assertEqual(inspection['nativeLawnInstanceCount'],40437)
        self.assertEqual(inspection['sourceSha256'],M.sha(HERE/'exterior-lawn-inspect.py'))
        observed={r['actor']:r for r in inspection['taggedLawnActors']}
        self.native=[]
        for key in M.LEGACY_GROUPS:
            actor_path=self.full_geometry['groups'][key]['actor'];values=observed[actor_path]['orderedInstanceTransforms']
            component=HISM(key,self.actual_trimmed[key]['instances'])
            component.rows=[NS(translation=NS(**dict(zip('xyz',v['p']))),rotation=NS(**dict(zip('xyzw',v['q']))),
                               scale3d=NS(**dict(zip('xyz',v['s']))))for v in values]
            self.native.append(Actor(actor_path,component))
            self.assertEqual(M.digest(M._rural_values(values)),self.actual_trim_proof['groups'][key]['transformsSha256'])
        changes=M.hide_original_lawn(self.u,self.actors,self.report,self.rural,self.rural_plan)
        result=M.verify_hidden_lawn(self.u,self.actors,changes)
        self.assertEqual(result['instances'],40437)

    def test_trim_receipt_domain_and_membership_changes_are_rejected(self):
        rural=copy.deepcopy(self.rural);rural['managedLawn']['keepPolygonsCm'][0][0][0]+=1
        with self.assertRaisesRegex(RuntimeError,'historical saved receipt'):M._trimmed_legacy_placement(self.report,rural,self.rural_plan)
        plan=copy.deepcopy(self.rural_plan);plan['managedLawnKeepPolygonsCm'][0][0][0]+=1
        with self.assertRaisesRegex(RuntimeError,'plan/photoreal pin'):M._trimmed_legacy_placement(self.report,self.rural,plan)
        rural=copy.deepcopy(self.rural);rural['managedLawn']['groups'][self.native[0].path]['kept']+=1
        with self.assertRaisesRegex(RuntimeError,'historical saved receipt'):M._trimmed_legacy_placement(self.report,rural,self.rural_plan)

    def test_hide_and_saved_readback_preserve_instances_assets_and_collision(self):
        before=[M._preserved(self.u,a,a.component)[0] for a in self.native]
        meshes=[a.component.mesh for a in self.native]
        changes=self.hide()
        self.assertEqual([r['preserved'] for r in changes],before)
        result=M.verify_hidden_lawn(self.u,self.actors,changes)
        self.assertEqual((result['actors'],result['instances']),(4,8))
        self.assertTrue(result['hiddenDetailDensityScalingDisabled'])
        self.assertEqual([a.component.mesh for a in self.native],meshes)
        self.assertTrue(all(not a.density and not a.component.visible and a.component.props['hidden_in_game'] for a in self.native))
        self.assertTrue(all(not a.component.props[k] for a in self.native for k in M.RENDER_FLAGS))
        self.assertEqual([M._preserved(self.u,a,a.component)[0] for a in self.native],before)

    def test_wrong_actor_inventory_rejected_before_any_mutation(self):
        self.native[3].path+='Unreviewed'
        with self.assertRaisesRegex(RuntimeError,'actor/tag inventory'):self.hide()
        self.assertTrue(all(a.density and a.component.visible and a.component.mutations==0 for a in self.native))

    def test_wrong_mesh_material_count_scale_and_parent_rejected_atomically(self):
        mutations=[
            lambda a:setattr(a.component.mesh,'path','/Game/Shared/Wrong.Wrong'),
            lambda a:setattr(a.component.material,'path','/Game/Shared/Wrong.Wrong'),
            lambda a:a.component.rows.pop(),
            lambda a:setattr(a.component.rows[0].scale3d,'z',2.),
            lambda a:setattr(a.component.rows[0].translation,'x',9999.),
            lambda a:setattr(a.world.translation,'x',1.),
            lambda a:setattr(a.component,'collision','QUERY_AND_PHYSICS'),
            lambda a:a.tags.remove('BreziPhotorealSource:DOM_00001'),
            lambda a:setattr(a,'root_component',None),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                self.setUp(); mutate(self.native[3])
                with self.assertRaises(RuntimeError):self.hide()
                self.assertTrue(all(a.density and a.component.visible and a.component.mutations==0 for a in self.native))

    def test_reload_rejects_identity_and_render_drift(self):
        mutations=[
            lambda a:setattr(a.component.rows[0].translation,'x',42.),
            lambda a:a.component.rows.pop(),
            lambda a:setattr(a.component.material,'path','/Game/Wrong.Wrong'),
            lambda a:setattr(a.component,'collision','QUERY_AND_PHYSICS'),
            lambda a:setattr(a.component,'visible',True),
            lambda a:setattr(a,'density',True),
            lambda a:a.component.props.update(cast_shadow=True),
            lambda a:a.component.props.update(instance_end_cull_distance=9999),
        ]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                self.setUp();changes=self.hide();mutate(self.native[0])
                with self.assertRaises(RuntimeError):M.verify_hidden_lawn(self.u,self.actors,changes)


class ManagedNaturalLawn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        folder=M.ROOT/'output/unreal/exterior-lawn-natural-20260930-r2b'
        cls.plan=read(folder/'lawn-natural-plan.json');cls.manifest=read(folder/'geometry-manifest.json')

    def validate(self,plan):
        return M.validated_groups(plan,self.manifest,self.plan['sourceSceneSha256'],self.plan['sourceObjSha256'])

    def test_actual_successor_all_crowns_fit_pinned_managed_union(self):
        groups=self.validate(self.plan)
        self.assertEqual(sum(len(g['instances'])for g in groups),self.plan['audit']['instances'])
        self.assertEqual(len(groups),self.plan['audit']['groups'])
        self.assertLess(self.plan['audit']['instances'],24918)
        self.assertEqual(self.plan['owner'],M.MANAGED_GENERATOR)

    def test_managed_plan_and_source_domain_claims_cannot_change(self):
        changes=[lambda p:p['managedLawnPlan'].update(sha256='0'*64),
                 lambda p:p['managedLawnKeepPolygonsCm'][0][0].__setitem__(0,0),
                 lambda p:p.update(sourceLawnDomainSourceMm='{}')]
        for change in changes:
            with self.subTest(change=change):
                plan=copy.deepcopy(self.plan);change(plan)
                with self.assertRaises(RuntimeError):self.validate(plan)

    def test_forged_declared_domain_cannot_restore_unmanaged_r1_root(self):
        plan=copy.deepcopy(self.plan);original=read(NATURAL/'lawn-natural-plan.json')
        polygons=plan['managedLawnKeepPolygonsCm']
        outside=next(r for r in original['lawnPlacements']if not any(M._inside_ring(r['positionCm'][:2],p)for p in polygons))
        group=next(g for g in plan['groups']if g['meshId']==outside['meshId']);group['instances'][0]=copy.deepcopy(outside)
        group['instances'][0].pop('meshId')
        p=outside['positionCm'];group['id']='EX_lawn_natural_'+str(math.floor(p[0]/2000))+'_'+str(math.floor(p[1]/2000))+'_'+outside['meshId'].removeprefix('lawn_natural_')
        plan['groups']=[group]
        plan['lawnDomainSourceMm']=original['lawnDomainSourceMm']
        with self.assertRaisesRegex(RuntimeError,'actual managed keep union'):self.validate(plan)




class ContinuousManagedLawn(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory=M.ROOT/'output/unreal/exterior-lawn-natural-20260930-r3d'
        cls.plan=read(directory/'lawn-natural-plan.json');cls.manifest=read(directory/'geometry-manifest.json')
        cls.meshes={r['id']:r for r in cls.manifest['meshes']}
        cls.decoded=M._glb_geometry(cls.manifest['meshes'][0]['glbPath']);cls.managed=M._managed_domain(cls.plan)

    def validate(self,plan=None,manifest=None):
        return M.validated_groups(plan or self.plan,manifest or self.manifest,
                                 self.plan['sourceSceneSha256'],self.plan['sourceObjSha256'])

    def claims(self,plan=None,meshes=None,decoded=None):
        return M._coverage_claims(plan or self.plan,meshes or self.meshes,decoded or self.decoded,self.managed)

    def test_actual_continuous_managed_52013_crowns_and_36_leaf_all_lod_inventory(self):
        groups=self.validate()
        self.assertEqual((len(groups),sum(len(g['instances'])for g in groups)),(40,52013))
        self.assertEqual(self.plan['audit']['allInstancesTriangleBudgetByLod'],[17476368,14979744,7489872])
        self.assertEqual(self.plan['coverageReceipt'],self.manifest['coverageReceipt'])
        self.assertTrue(all(g['id'].startswith('EX_lawn_natural_')for g in groups))

    def test_measured_area_blade_density_scale_and_population_budget_claims_rejected(self):
        cases=[('exactAllowedDomainM2',144.),('densityPatchesPerM2',360.),('bladesPerM2EveryLod',12000.),
               ('heightScaleStandardDeviation',.1),('sixtyMmLatticePhaseAmplitudeXY',[0.,0.]),
               ('heightScaleRange',[.9,1.03]),('allInstancesTriangleBudgetByLod',[17476368,14979744,1]),
               ('nearTriangleBudget',20000001),('allLodGeometryVertices',17999)]
        for key,value in cases:
            with self.subTest(key=key):
                plan=copy.deepcopy(self.plan);plan['audit'][key]=value
                with self.assertRaisesRegex(RuntimeError,'area|density|budget'):self.claims(plan)

    def test_declared_managed_area_cannot_be_forged_with_larger_domain(self):
        plan=copy.deepcopy(self.plan);domain=json.loads(plan['lawnDomainSourceMm'])
        ring=domain['coordinates'][0] if domain['type']=='Polygon' else domain['coordinates'][0][0]
        for ring in ([domain['coordinates']] if domain['type']=='Polygon' else domain['coordinates']):
            for points in ring:
                for point in points:point[0]*=1.01
        plan['lawnDomainSourceMm']=json.dumps(domain)
        plan['audit']['exactAllowedDomainM2']=M._polygon_area(domain)/1e6
        with self.assertRaisesRegex(RuntimeError,'managed area'):self.claims(plan)

    def test_lod_topology_leaf_loss_and_external_coverage_claim_rejected(self):
        meshes=copy.deepcopy(self.meshes);next(iter(meshes.values()))['lods'][2]['blades']=35
        with self.assertRaisesRegex(RuntimeError,'leaf inventory'):self.claims(meshes=meshes)
        plan=copy.deepcopy(self.plan);plan['coverageReceipt']['sha256']='0'*64
        with self.assertRaisesRegex(RuntimeError,'pin|bundle'):self.claims(plan)
        plan=copy.deepcopy(self.plan);plan['audit']['physicalCoverage']['windows'][0]['lods'][2]['projectedCoverage']=.95
        with self.assertRaisesRegex(RuntimeError,'bundle|coverage'):self.claims(plan)

    def test_coverage_owner_is_not_broad_generator_or_domain_exception(self):
        plan=copy.deepcopy(self.plan);plan['owner']='scripts/unreal/unknown-lawn.py'
        with self.assertRaisesRegex(RuntimeError,'generator/schema'):self.validate(plan)
        plan=copy.deepcopy(self.plan);plan['replacementPolicy']['unmanagedRuralGroundcoverPreserved']=False
        with self.assertRaisesRegex(RuntimeError,'scope'):self.validate(plan)
        plan=copy.deepcopy(self.plan);plan['groups'][0]['id']=plan['groups'][0]['id'].replace('EX_lawn_natural_','EX_lawn_coverage_')
        with self.assertRaisesRegex(RuntimeError,'HISM'):self.validate(plan)


if __name__=='__main__':unittest.main()
