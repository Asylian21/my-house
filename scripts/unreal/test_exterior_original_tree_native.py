"""CPU-only checks for the unconsumed R24 native draft and actual R1/R2."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch
import contextlib
import io

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('r24_draft_guard_tests',ROOT/'scripts/unreal/exterior-original-tree-guards.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
materials=g.module('r24_draft_material_tests','exterior-original-tree-materials.py')
native=g.module('r24_draft_native_tests','exterior-original-tree-native.py')


class OriginalNativeDraft(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.b=g.load_source()

    def test_actual_source_three_sections_and_owned_tangent_input(self):
        self.assertEqual([r['triangles']for r in self.b['proof']['parts']],[94814,1939380,28293])
        self.assertFalse(self.b['proof']['nativeNormalTangentReadbackAvailable'])
        self.assertEqual(materials.validate_recipes(self.b['recipes'],self.b)['textures'],10)

    def test_import_staging_preserves_all_original_primitive_attributes(self):
        doc=g.import_descriptor(self.b,ROOT/'output/unreal/r24-unit-fixture')
        self.assertEqual(doc['meshes'],self.b['descriptor']['meshes'])
        self.assertEqual(doc['materials'],self.b['descriptor']['materials'])
        self.assertEqual(doc['accessors'],self.b['descriptor']['accessors'])
        self.assertEqual(doc['nodes'][0]['scale'],[1.,1.,1.])
        self.assertEqual(doc['nodes'][0]['translation'],[0.,0.,0.])
        self.assertNotEqual(doc['nodes'][0],self.b['descriptor']['nodes'][0])

    def test_uniform_source_fit_declared_in_single_instance_contract(self):
        contract=g.placement_contract(self.b)
        self.assertEqual(contract['instanceUniformScale'],[1.6605209183502103]*3)
        self.assertAlmostEqual(contract['instanceOriginOffsetCm'][2],4.002494116152138)
        self.assertTrue(contract['sourceAttributeBakeDisabled'])
        self.assertFalse(contract['nativeMatrixProjectionIsGpuReadback'])
        b=deepcopy(self.b);b['descriptor']['nodes'][0]['scale'][0]*=.99
        with self.assertRaises(RuntimeError):g.placement_contract(b)

    def test_original_uv1_basis_substitution_rejected(self):
        recipes=deepcopy(self.b['recipes']);recipes[0]['uvSet']=0
        with self.assertRaises(RuntimeError):materials.validate_recipes(recipes,self.b)

    def test_provider_alpha_graph_conversion_or_ao_route_change_rejected(self):
        for field,value in [('blendMode','BLEND'),('opacityMask',None),('occlusionRoot','ARM.R')]:
            recipes=deepcopy(self.b['recipes']);recipes[1]['nativeProposal'][field]=value
            with self.subTest(field=field),self.assertRaises(RuntimeError):materials.validate_recipes(recipes,self.b)

    def test_native_basis_acceptance_or_recomputed_tangent_claim_rejected(self):
        for field in ('nativeImportRecomputeTangents','nativeTangentBasisVerified'):
            recipes=deepcopy(self.b['recipes']);recipes[0]['nativeProposal']['normalTangentBasis'][field]=True
            with self.subTest(field=field),self.assertRaises(RuntimeError):materials.validate_recipes(recipes,self.b)

    def test_native_enum_prefixes_resolve_before_assets_and_ambiguity_rejects(self):
        u=types.SimpleNamespace(MaterialUsage=types.SimpleNamespace(MATUSAGE_NANITE='nanite'),
            MaterialShadingModel=types.SimpleNamespace(MSM_DEFAULT_LIT='lit'),
            TextureSourceEncoding=types.SimpleNamespace(TSE_SRGB='srgb'))
        self.assertEqual(materials.enum(u,'MaterialUsage','NANITE'),'nanite')
        self.assertEqual(materials.enum(u,'MaterialShadingModel','DEFAULTLIT'),'lit')
        self.assertEqual(materials.enum(u,'TextureSourceEncoding','TSESRGB'),'srgb')
        u.MaterialUsage.NANITE='another'
        with self.assertRaises(RuntimeError):materials.enum(u,'MaterialUsage','NANITE')

    def test_source_corner_hash_rejects_mirrored_winding_and_changed_uv1(self):
        binary=self.b['binaryPath'].read_bytes();primitive=self.b['original']['meshes'][0]['primitives'][0]
        face=next(g.source_corners(self.b['original'],binary,primitive));normal=g.corner_hash([face])
        mirrored=[face[0],face[2],face[1]]
        self.assertNotEqual(normal,g.corner_hash([g.cyclic(mirrored)]))
        changed=list(face);changed[0]=(*changed[0][:5],changed[0][5]+.001,changed[0][6])
        self.assertNotEqual(normal,g.corner_hash([g.cyclic(changed)]))

    def test_source_corner_cyclic_rotation_is_allowed_without_reversal(self):
        binary=self.b['binaryPath'].read_bytes();primitive=self.b['original']['meshes'][0]['primitives'][0]
        face=next(g.source_corners(self.b['original'],binary,primitive))
        self.assertEqual(g.cyclic(list(face)),g.cyclic(list(face[1:]+face[:1])))

    def test_running_or_failed_future_base_never_creates_a_placeholder(self):
        # Only the actually successful closed R22c R3 is an eligible base.
        with self.assertRaises(RuntimeError):g.load_saved_base(ROOT/'output/unreal/fake-future-r22.json')
        with self.assertRaises(RuntimeError):g.load_saved_base(ROOT/'output/unreal/exterior-20261002-r22b/realism-integration-native-report-r2.json')

    def test_deterministic_sample_exact_counts_endpoints_and_identity(self):
        counts=[94814,1939380,28293];samples=[g.sample_triangle_indices(n,k)for n,k in zip(counts,g.SAMPLE_COUNTS)]
        self.assertEqual(sum(map(len,samples)),4096)
        self.assertEqual([(r[0],r[-1])for r in samples],[(0,n-1)for n in counts])
        self.assertTrue(all(r==sorted(set(r))for r in samples))
        with self.assertRaises(RuntimeError):g.sample_triangle_indices(20,21)

    def test_sample_hash_rejects_identity_permutation_uv1_and_winding_changes(self):
        binary=self.b['binaryPath'].read_bytes();primitive=self.b['original']['meshes'][0]['primitives'][1]
        face=g.source_face(self.b['original'],binary,primitive,1000)
        receipt=g.sampled_corner_hash([(1000,face)])
        self.assertNotEqual(receipt,g.sampled_corner_hash([(1001,face)]))
        changed=list(face);changed[0]=(*changed[0][:5],changed[0][5]+.005,changed[0][6])
        self.assertNotEqual(receipt,g.sampled_corner_hash([(1000,changed)]))
        self.assertNotEqual(receipt,g.sampled_corner_hash([(1000,[face[0],face[2],face[1]])]))
        self.assertEqual(receipt,g.sampled_corner_hash([(1000,list(face[1:]+face[:1]))]))
        with self.assertRaises(RuntimeError):g.sampled_corner_hash([(1000,face),(1000,face)])

    def test_random_source_sample_matches_original_stream_order(self):
        binary=self.b['binaryPath'].read_bytes();primitive=self.b['original']['meshes'][0]['primitives'][0]
        stream=g.source_corners(self.b['original'],binary,primitive)
        for index in range(12):self.assertEqual(next(stream),g.source_face(self.b['original'],binary,primitive,index))

    def test_original_actor_delta_only_exact_selected_root_retirement(self):
        report=g.read(g.BASE_REPORT);before=g.read(g.check_pin(report['savedActorWitness']))
        remaining=[[[1.,2.,3.],[0.,0.,0.,1.],[1.,1.,1.]]for _ in range(3)]
        expected=g.expected_original(before,self.b['selection'],remaining)
        original=self.b['selection']['originalNativeActor'];self.assertEqual(expected[original]['components'][0]['instanceCount'],3)
        after=deepcopy(expected);after['new-owned-tree']={'components':[]}
        g.validate_actor_delta(before,expected,after,'new-owned-tree')
        after[original]['components'][0]['instanceCullCm'][1]+=1
        with self.assertRaises(RuntimeError):g.validate_actor_delta(before,expected,after,'new-owned-tree')
        after=deepcopy(expected);after['new-owned-tree']={'components':[]};after['second-extra']={}
        with self.assertRaises(RuntimeError):g.validate_actor_delta(before,expected,after,'new-owned-tree')

    def test_saved_native_dispatch_uses_actual_report_owner_not_historical_r1(self):
        report=g.read(g.BASE_REPORT)
        self.assertEqual(report['owner'],g.BASE_NATIVE_OWNER)
        self.assertEqual(g.sha(ROOT/report['owner']),g.BASE_NATIVE_SHA)
        composed=types.SimpleNamespace(helpers=lambda bundle:{'frozenFirst':True})
        base={'nativeHelper':ROOT/report['owner'],'nativeHelperPin':g.pin(ROOT/report['owner']),
            'report':report,'guard':types.SimpleNamespace(validate_plan=lambda:(None,{}))}
        with patch.object(native.guard,'module',side_effect=[composed,object()])as dispatch:
            result=native.helpers(base)
            self.assertTrue(result['frozenFirst'])
            self.assertEqual(dispatch.call_args_list[0].args[1],'exterior-realism-integration-native-r22-r3.py')
        base['report']=dict(report,owner='scripts/unreal/exterior-realism-integration-native-r22.py')
        with self.assertRaises(RuntimeError):native.helpers(base)

    def test_native_sample_scope_uv1_section_census_and_honest_limit(self):
        binary=self.b['binaryPath'].read_bytes();parts=[];faces={};offset=0
        for section,(primitive,n,k)in enumerate(zip(self.b['original']['meshes'][0]['primitives'],[94814,1939380,28293],g.SAMPLE_COUNTS)):
            indices=g.sample_triangle_indices(n,k)
            pairs=[(j,g.source_face(self.b['original'],binary,primitive,j))for j in indices]
            parts.append({'section':section,'material':str(section),'triangles':n,'sampleTriangleIndices':indices,
                **g.sampled_corner_hash(pairs),'orderedFloat32PositionUV0UV1CornersSha256':'source-only-hash'})
            faces.update({offset+j:face for j,face in pairs});offset+=n
        def xyz(values):return types.SimpleNamespace(**dict(zip('xyz',values)))
        class Description:
            def __init__(self):self.calls=0;self.bad_uv=False;self.bad_section_count=False
            def get_triangle_count(self):return 2062487
            def get_polygon_count(self):return 2062487
            def get_polygon_group_count(self):return 3
            def get_vertex_count(self):return 1777278
            def get_vertex_instance_count(self):return 6187461
            def get_num_polygon_group_polygons(self,value):return [94814,1939380,28293][value.id_value]+(1 if self.bad_section_count else 0)
            def get_triangle_polygon_group(self,value):
                self.calls+=1;index=value.id_value
                return types.SimpleNamespace(id_value=0 if index<94814 else 1 if index<2034194 else 2)
            def get_triangle_vertex_instance(self,value,corner):self.calls+=1;return(value.id_value,corner)
            def get_vertex_instance_vertex(self,value):self.calls+=1;return value
            def get_vertex_position(self,value):self.calls+=1;return xyz(faces[value[0]][value[1]][:3])
            def get_vertex_instance_uv(self,value,channel):
                self.calls+=1;uv=list(faces[value[0]][value[1]][3+channel*2:5+channel*2])
                if self.bad_uv and channel==1:uv[0]+=.005
                return types.SimpleNamespace(x=uv[0],y=uv[1])
        d=Description()
        mesh=types.SimpleNamespace(get_static_mesh_description=lambda _:d,get_num_lods=lambda:1,
            get_editor_property=lambda _:[1,2,3],get_bounds=lambda:types.SimpleNamespace(origin=xyz([0,0,4]),box_extent=xyz([5,7,5])),
            get_num_sections=lambda _:3,get_path_name=lambda:'/Game/Test.Tree',get_num_triangles=lambda _:2062487)
        u=types.SimpleNamespace(TriangleID=lambda **v:types.SimpleNamespace(**v),PolygonGroupID=lambda **v:types.SimpleNamespace(**v))
        preflight={'nativeExpectedSections':parts,'nativeExpectedSourceBounds':{'minimumCm':[-5,-7,-1],'maximumCm':[5,7,9]},
            'nativeReadbackContract':{'sourceBoundsCompatibilityCapCm':.002}}
        with contextlib.redirect_stdout(io.StringIO()):proof=native.native_mesh_proof(u,mesh,preflight)
        self.assertEqual(d.calls,65536)
        self.assertEqual(proof['sampledNativeTriangles'],4096)
        self.assertEqual(proof['unsampledNativeTriangles'],2058391)
        self.assertFalse(proof['nativeFullPositionUV0UV1CornerReadbackPerformed'])
        self.assertFalse(proof['nativeNormalTangentReadbackAvailable'])
        d.bad_uv=True
        with self.assertRaises(RuntimeError):native.native_mesh_proof(u,mesh,preflight)
        d.bad_uv=False;d.bad_section_count=True
        with self.assertRaises(RuntimeError):native.native_mesh_proof(u,mesh,preflight)

    def test_source_exclusions_and_single_retirement_are_exact(self):
        self.assertEqual(set(self.b['maskProof']['exclusions']),{'protected','subject','roads','buildings','cultivatedGround','managedLawn'})
        self.assertEqual(self.b['selection']['retiredOriginalIndex'],0)
        self.assertEqual(self.b['selection']['retainedSourceRootIds'],['village_nearest_grove_11','village_nearest_grove_27','village_nearest_grove_30'])
        self.assertTrue(all(r['completeTriangleClearanceLowerBoundCm']>75 for r in self.b['maskProof']['exclusions'].values()))


if __name__=='__main__':unittest.main(verbosity=2)
