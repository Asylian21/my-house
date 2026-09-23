"""CPU contracts: semantic scoping, true pinned inputs and seam continuity."""
import copy
import importlib.util
import json
import math
from pathlib import Path
from types import SimpleNamespace
import unittest

SPEC=importlib.util.spec_from_file_location('lawn_materials',Path(__file__).with_name('lawn-materials.py'))
M=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(M)


def source_scene():
    return {'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},
        'materials':{'MAT_9382':{'name':'real-grass','alpha':1,'metallic':0},
                     'MAT_0081':{'name':'real-plant-grass','alpha':1,'metallic':0}},
        'objects':[{'id':'DOM_93726','sourceId':'stable-parcel','name':'Maintained parcel','group':'Landscape','enabled':True,
                    'instances':1,'materialSlots':['MAT_9382'],'boundsMm':{'min':[-16146,-10800,-65],'max':[15987,13697,-65]},
                    'metadata':{'walkSurfaceId':'parcel-6012-26'}},
                   {'id':'DOM_00111','sourceId':'ornament','name':'Decorative grass','group':'Landscape','enabled':True,
                    'instances':1,'materialSlots':['MAT_0081']} ]}


class SelectionAndAssets(unittest.TestCase):
    def test_semantic_selection_ignores_historical_ordinals_and_ornamental_grass(self):
        targets=M.select_targets(source_scene())
        self.assertEqual([(x['id'],x['sourceSlot']) for x in targets],[('DOM_93726','MAT_9382')])

    def test_shared_grass_on_neighbor_is_not_silently_edited(self):
        scene=source_scene();neighbor=copy.deepcopy(scene['objects'][0]);neighbor['id']='DOM_NEIGHBOR'
        neighbor['metadata']['walkSurfaceId']='neighbor-plot';scene['objects'].append(neighbor)
        with self.assertRaisesRegex(RuntimeError,'escaped'):M.select_targets(scene)

    def test_duplicate_missing_and_sloped_ground_require_review(self):
        for case in ('duplicate','missing','slope','archive'):
            with self.subTest(case=case):
                scene=source_scene()
                if case=='duplicate':scene['objects'].append(copy.deepcopy(scene['objects'][0]))
                if case=='missing':scene['objects'][0]['enabled']=False
                if case=='slope':scene['objects'][0]['boundsMm']['max'][2]=0
                if case=='archive':scene['activeDesign']['variant']='A'
                with self.assertRaises(RuntimeError):M.select_targets(scene)

    def test_real_input_files_match_hashes_bytes_and_jpeg_dimensions(self):
        inputs=M.load_inputs()
        self.assertFalse(inputs['provider']['scanClaim'])
        self.assertEqual(inputs['provider']['approximateTileMetres'],[1.4,1.4])
        self.assertEqual({tuple(M.jpeg_size(M.ROOT/x['path'])) for x in inputs['maps'].values()},{(4096,4096)})
        self.assertGreater(inputs['maps']['albedo']['meanLinearRGB'][1],inputs['maps']['albedo']['meanLinearRGB'][0])


class TextureContinuity(unittest.TestCase):
    @staticmethod
    def evaluate(uv):
        weights,phases=M.sample_plan(uv)
        # A nontrivial smooth tile catches mismatched shared vertex phases. A
        # constant texture would trivially pass even with visibly broken joins.
        return sum(w*(math.sin(2*math.pi*p[0])+.37*math.cos(4*math.pi*p[1])+.17*math.sin(2*math.pi*(p[0]+p[1])))
                   for w,p in zip(weights,phases))

    def test_same_value_across_diagonal_and_integer_lattice_boundaries(self):
        epsilon=1e-7
        boundaries=[((.3,.7),(1,-1)), ((-.7,.7),(1,0)), ((1.,.37),(1,0)),
                    ((-.43,-2.),(0,1)), ((-3.,-4.),(1,1)), ((12.,9.),(1,-1))]
        # Include both halves of triangles and negative world coordinates.
        for point,direction in boundaries:
            with self.subTest(point=point):
                left=tuple(v-epsilon*d for v,d in zip(point,direction));right=tuple(v+epsilon*d for v,d in zip(point,direction))
                self.assertLess(abs(self.evaluate(left)-self.evaluate(right)),2e-5)

    def test_weights_form_convex_partition_and_no_whole_tile_repeat(self):
        for uv in [(-3.2,-7.8),(-.0001,.99999),(.9,.8),(0.,0.),(27.25,31.5)]:
            weights,_=M.sample_plan(uv)
            self.assertAlmostEqual(sum(weights),1,12);self.assertTrue(all(0<=v<=1 for v in weights))
        original=self.evaluate((.318,.741))
        repeated=[self.evaluate((.318+i,.741+j)) for i,j in [(1,0),(0,1),(3,4),(19,-11)]]
        self.assertTrue(all(abs(original-v)>1e-4 for v in repeated))

    def test_invalid_world_sampling_is_rejected(self):
        for uv in [(float('nan'),1),(1,float('inf')),(100001,1),(1,)]:
            with self.assertRaises(RuntimeError):M.sample_plan(uv)


class ProtectedGround(unittest.TestCase):
    def component(self):
        self.actor=SimpleNamespace(hidden=False,tags=['DOM_93726','SourceGeometry'])
        self.actor.get_editor_property=lambda key:getattr(self.actor,key)
        self.mesh=SimpleNamespace(get_path_name=lambda:'/Game/Source/SM_Parcel.SM_Parcel',get_num_triangles=lambda _:27,get_num_sections=lambda _:1)
        self.transform=SimpleNamespace(scale3d=SimpleNamespace(x=1,y=1,z=1),translation=SimpleNamespace(x=0,y=0,z=-6.5),rotation=SimpleNamespace(x=0,y=0,z=0,w=1))
        self.part=SimpleNamespace(visible=True,hidden_in_game=False,static_mesh=self.mesh,component_tags=['Canonical'],collision='QueryAndPhysics',profile='BlockAll',response='Block')
        self.part.get_editor_property=lambda key:getattr(self.part,key)
        self.part.get_owner=lambda:self.actor;self.part.is_visible=lambda:self.part.visible
        self.part.get_world_transform=lambda:self.transform
        self.part.get_collision_enabled=lambda:self.part.collision;self.part.get_collision_profile_name=lambda:self.part.profile
        self.part.get_collision_response_to_channel=lambda _:self.part.response
        self.u=SimpleNamespace(SystemLibrary=SimpleNamespace(get_component_bounds=lambda _:(SimpleNamespace(x=0,y=0,z=-6.5),SimpleNamespace(x=1600,y=1200,z=0),2000)),
                               CollisionChannel=SimpleNamespace(ECC_PAWN=1,ECC_VISIBILITY=2,ECC_MAX=3))
        return self.part

    def test_hidden_ground_never_produces_retained_witness(self):
        for field,owner in [('visible','component'),('hidden_in_game','component'),('hidden','actor')]:
            self.component();setattr(self.actor if owner=='actor' else self.part,field,field!='visible')
            with self.assertRaisesRegex(RuntimeError,'hidden'):M.geometry_witness(self.u,{'parcel':self.part})

    def test_source_collision_response_tags_and_transform_drift_change_witness(self):
        self.component();before=M.geometry_witness(self.u,{'parcel':self.part})
        self.part.response='Ignore';self.assertNotEqual(before,M.geometry_witness(self.u,{'parcel':self.part}))
        self.part.response='Block';self.actor.tags.append('Changed');self.assertNotEqual(before,M.geometry_witness(self.u,{'parcel':self.part}))
        self.actor.tags.pop();self.transform.translation.x=1;self.assertNotEqual(before,M.geometry_witness(self.u,{'parcel':self.part}))


if __name__=='__main__':unittest.main()
