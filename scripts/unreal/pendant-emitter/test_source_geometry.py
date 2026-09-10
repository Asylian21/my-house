"""Source geometry and fallback-policy regressions, not native API/render proof."""
import copy
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace as NS
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


geo=load('pendant_geometry',HERE/'source_geometry.py')
writer=load('pendant_writer',HERE/'pendant_emitter.py')
SOURCE=[[(0.,0.,0.),(10.,0.,0.),(0.,10.,0.)],[(10.,0.,0.),(10.,10.,0.),(0.,10.,0.)]]


def native(source):return [[(v[0]/10,-v[1]/10,v[2]/10) for v in t] for t in source]


class GeometryTests(unittest.TestCase):
    def proof(self,triangles,source=SOURCE):return geo.compare_triangles(triangles,source,geo.area(source))

    def test_exact_geometry_matches_with_unit_and_handedness_conversion(self):
        p=self.proof(native(SOURCE));self.assertEqual(p['maximumVertexErrorMm'],0);self.assertTrue(p['sourceAreaVerified'])
        self.assertFalse(p['renderFallbackAreaReadback']);self.assertFalse(p['canonicalPhotometryRenormalized'])

    def test_reordering_and_cyclic_corner_rotation_preserve_geometry(self):
        triangles=native(SOURCE)[::-1];triangles=[t[1:]+t[:1] for t in triangles]
        self.assertTrue(self.proof(triangles)['canonicalTriangleConnectivityAndWindingVerified'])

    def test_reversed_winding_fails(self):
        triangles=native(SOURCE);triangles[0].reverse()
        with self.assertRaisesRegex(RuntimeError,'winding'):self.proof(triangles)

    def test_duplicate_face_or_different_connectivity_fails(self):
        original=native(SOURCE)
        for triangles in ([original[0],original[0]],[[original[0][0],original[1][1],original[0][2]],original[1]]):
            with self.assertRaisesRegex(RuntimeError,'connectivity'):self.proof(triangles)

    def test_missing_triangle_fails(self):
        with self.assertRaisesRegex(RuntimeError,'count'):self.proof(native(SOURCE)[:1])

    def test_small_float_translation_is_measured_without_snapping_area(self):
        triangles=[[(x+.00015,y,z) for x,y,z in t] for t in native(SOURCE)]
        proof=self.proof(triangles);self.assertAlmostEqual(proof['maximumVertexErrorMm'],.0015)

    def test_vertex_just_outside_bound_fails(self):
        triangles=native(SOURCE);triangles[0][0]=(.000201,0.,0.)
        with self.assertRaisesRegex(RuntimeError,'unique canonical'):self.proof(triangles)

    def test_nonfinite_vertex_and_wrong_area_fail(self):
        triangles=native(SOURCE);triangles[0][0]=(float('nan'),0.,0.)
        with self.assertRaisesRegex(RuntimeError,'Nonfinite'):self.proof(triangles)
        with self.assertRaisesRegex(RuntimeError,'area'):geo.compare_triangles(native(SOURCE),SOURCE,geo.area(SOURCE)+geo.AREA_TOLERANCE_M2*2)

    def test_ambiguous_nearby_source_vertices_fail(self):
        source=copy.deepcopy(SOURCE);source[1][0]=(.001,0.,0.)
        with self.assertRaisesRegex(RuntimeError,'unique canonical'):self.proof(native(source),source)

    def test_zero_area_pole_faces_are_retained_in_multiplicity(self):
        source=SOURCE+[[(0.,0.,0.),(0.,0.,0.),(10.,0.,0.)]]
        self.assertEqual(self.proof(native(source),source)['triangleCount'],3)


class Properties:
    def __init__(self,**values):self.values=values
    def get_editor_property(self,key):return self.values[key]


class ScalarReadbackTests(unittest.TestCase):
    def setUp(self):
        self.calls=[];self.positions=native(SOURCE)
        def instance(triangle,corner):self.calls.append((triangle,corner));return (triangle,corner)
        self.description=NS(get_triangle_count=lambda:len(SOURCE),is_triangle_valid=lambda i:0<=i<len(SOURCE),
            get_triangle_vertex_instance=instance,is_vertex_instance_valid=lambda i:True,
            get_vertex_instance_vertex=lambda i:i,is_vertex_valid=lambda i:True,
            get_vertex_position=lambda i:NS(**dict(zip(('x','y','z'),self.positions[i[0]][i[1]]))))
        self.mesh=NS(get_static_mesh_description=lambda lod:self.description)
        self.ref=NS(source_triangles=lambda path:SOURCE,AREA_M2=geo.area(SOURCE))
        self.u=NS(TriangleID=lambda id_value:id_value)

    def test_readback_uses_all_three_scalar_corners_in_source_order(self):
        proof=geo.read_and_verify(self.u,self.mesh,self.ref,Path('.'))
        self.assertEqual(self.calls,[(t,c) for t in range(2) for c in range(3)])
        self.assertTrue(proof['canonicalTriangleConnectivityAndWindingVerified'])

    def test_missing_source_ids_or_vertex_instances_fail_closed(self):
        for field in ('is_triangle_valid','is_vertex_instance_valid','is_vertex_valid'):
            old=getattr(self.description,field);setattr(self.description,field,lambda _:False)
            with self.assertRaises(RuntimeError):geo.read_and_verify(self.u,self.mesh,self.ref,Path('.'))
            setattr(self.description,field,old)

    def test_source_count_mismatch_does_not_read_partial_geometry(self):
        self.description.get_triangle_count=lambda:1
        with self.assertRaises(RuntimeError):geo.read_and_verify(self.u,self.mesh,self.ref,Path('.'))
        self.assertEqual(self.calls,[])


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.actor=object();self.meta={};self.overrides=[];self.calls=[]
        self.source=NS(get_path_name=lambda:'/Game/Brezi/Geometry/brezi-twin/Materials/MAT_0046.MAT_0046')
        self.settings=Properties(enabled=True,fallback_percent_triangles=1.,fallback_relative_error=0.,keep_percent_triangles=1.,trim_relative_error=0.,fallback_target='Percent')
        self.triangles=2600
        self.mesh=Properties(nanite_settings=self.settings,static_materials=[object()])
        self.mesh.get_path_name=lambda:'/Game/Brezi/Geometry/brezi-twin/StaticMeshes/DOM_01375.DOM_01375'
        self.mesh.get_num_triangles=lambda lod:self.triangles
        self.mesh.get_num_tex_coords=lambda lod:1;self.mesh.get_num_sections=lambda lod:1;self.mesh.get_material=lambda slot:self.source
        self.component=Properties(static_mesh=self.mesh,affect_dynamic_indirect_lighting=True,visible_in_ray_tracing=True,emissive_light_source=False)
        self.effective=self.source;self.component.get_material=lambda slot:self.effective
        self.component.get_num_materials=lambda:1;self.component.get_collision_enabled=lambda:'NoCollision'
        self.component.get_world_transform=lambda:NS(translation=NS(x=0,y=0,z=0),rotation=NS(x=0,y=0,z=0,w=1),scale3d=NS(x=1,y=1,z=1))
        self.u=NS(NaniteFallbackTarget=NS(AUTO='Auto',PERCENT_TRIANGLES='Percent'),CollisionEnabled=NS(NO_COLLISION='NoCollision'),
                  SystemLibrary=NS(get_component_bounds=lambda c:(NS(x=925,y=-395,z=198.5),NS(x=10,y=10,z=10),0)),
                  EditorAssetLibrary=NS(get_metadata_tag=lambda actor,key:self.meta.get(key,'')))
        self.ref=NS(ID='DOM_01375',SLOT='MAT_0046');self.common=NS(overrides=lambda c:self.overrides)
        self.contract={'record':{'boundsMm':{'min':[9150,3850,1885],'max':[9350,4050,2085]}},'scene':{'materials':{}}}

    def check(self,legacy=False,geometry_error=False):
        def verify(*args):
            self.calls.append('source-proof')
            if geometry_error:raise RuntimeError('source geometry mismatch')
            return {'sourceAreaVerified':True}
        with patch.dict(sys.modules,{'materials':NS(_resolve_slot=lambda *args:'MAT_0046')}),patch.object(writer,'load',return_value=NS(read_and_verify=verify)):
            return writer.source_guard(self.u,self.ref,self.common,{'DOM_01375':(self.actor,self.component)},self.contract,Path('.'),allow_legacy_auto=legacy)[1]

    def test_full_policy_accepts_only_source_or_degenerate_removed_render_count(self):
        for count in (2600,2704):
            self.triangles=count;p=self.check();self.assertTrue(p['fullNormalFallbackPolicyVerified']);self.assertFalse(p['legacyAutoMigrationValidated'])
        self.triangles=256
        with self.assertRaisesRegex(RuntimeError,'fallback target/topology'):self.check()

    def test_auto_rejected_outside_explicit_predeletion(self):
        self.settings.values['fallback_target']='Auto';self.triangles=256
        with self.assertRaisesRegex(RuntimeError,'fallback target/topology'):self.check()
        self.assertEqual(self.calls,['source-proof'])

    def test_auto_migration_requires_source_proof_before_acceptance(self):
        self.settings.values['fallback_target']='Auto';self.triangles=256
        p=self.check(True);self.assertTrue(p['legacyAutoMigrationValidated']);self.assertFalse(p['fullNormalFallbackPolicyVerified'])
        with self.assertRaisesRegex(RuntimeError,'source geometry mismatch'):self.check(True,True)

    def test_active_stale_foreign_override_or_untracked_flag_blocks_auto(self):
        self.settings.values['fallback_target']='Auto';self.triangles=256
        for key,value in ((writer.PRIOR,'{}'),(writer.REVISION_TAG,'revision')):
            self.meta={key:value}
            with self.assertRaisesRegex(RuntimeError,'untouched source'):self.check(True)
        self.meta={};self.overrides=['manual']
        with self.assertRaisesRegex(RuntimeError,'untouched source'):self.check(True)
        self.overrides=[];self.effective=object()
        with self.assertRaisesRegex(RuntimeError,'untouched source'):self.check(True)
        self.effective=self.source;self.component.values['emissive_light_source']=True
        with self.assertRaisesRegex(RuntimeError,'untouched source'):self.check(True)

    def test_other_target_and_source_reduction_are_not_migration(self):
        self.settings.values['fallback_target']='RelativeError'
        with self.assertRaisesRegex(RuntimeError,'fallback target/topology'):self.check(True)
        self.settings.values['fallback_target']='Percent'
        for key,value in (('keep_percent_triangles',.5),('trim_relative_error',.1),('fallback_percent_triangles',.5),('fallback_relative_error',.1)):
            prior=self.settings.values[key];self.settings.values[key]=value
            with self.assertRaisesRegex(RuntimeError,'policy differs'):self.check()
            self.settings.values[key]=prior


if __name__=='__main__':unittest.main(verbosity=2)
