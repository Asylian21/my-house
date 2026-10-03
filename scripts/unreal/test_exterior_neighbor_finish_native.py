"""CPU adversarial R18 guards against real frozen R1 source and GLB payloads."""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]


def module(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m


guard=module('test_neighbor_guard','exterior-neighbor-finish-guards.py')
native=module('test_neighbor_native','exterior-neighbor-finish-native.py')
materials=module('test_neighbor_materials','exterior-neighbor-finish-materials.py')
diagnostic=module('test_neighbor_diagnostic','exterior-neighbor-finish-diagnostic.py')


class SourceGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle=guard.validated_candidate();cls.plan=cls.bundle['plan'];cls.data=cls.bundle['geometry'];cls.recipes=cls.bundle['recipes']
        cls.village=guard.read(ROOT/'output/unreal/exterior-buildings-20260926-r2/building-plan.json')
        cls.neighborhood=guard.read(ROOT/'output/unreal/exterior-context-20260930-r3/neighborhood-details.json')
        cls.context=guard.read(ROOT/'output/unreal/exterior-context-20260927-r8/context-plan.json')

    def validate(self,data=None,plan=None,recipes=None):return guard.validate_candidate_data(plan or self.plan,data or self.data,recipes or self.recipes,self.village,self.neighborhood,self.context)

    def test_actual_frozen_cut_wall_and_source_budget(self):
        r=self.validate();self.assertEqual((r['candidateMeshes'],r['candidateTriangles'],r['retiredOldTriangles'],r['windowCount']),(32,5095,919,35))
        self.assertLess(r['wallAreaErrorCm2'],.01);self.assertFalse(r['nativeGeometryDecoded']);self.assertFalse(r['fullPhotorealismAccepted'])
        self.assertEqual(set(self.bundle['originalChunks']),set(guard.PARTITIONS))

    def test_removing_a_gutter_instead_of_old_window_is_rejected(self):
        d=copy.deepcopy(self.data);p=next(p for p in d['sourceTrianglePartitions'] if p['sourceMeshId']=='neighborhood_0_2_wire');original=self.bundle['originalChunks'][p['sourceMeshId']]
        wrong=p['retainedTriangleOrdinals'][0];p['removedTriangleOrdinals']=sorted(p['removedTriangleOrdinals'][1:]+[wrong]);p['retainedTriangleOrdinals']=[i for i in range(p['sourceTriangles']) if i not in set(p['removedTriangleOrdinals'])]
        remainder=next(m for m in d['unchangedRemainderMeshes'] if m['id']==p['sourceMeshId']);remainder['indices']=[i for n in p['retainedTriangleOrdinals'] for i in original['indices'][n*3:n*3+3]];p['replacementRemainderSha256']=guard.digest(remainder)
        with self.assertRaisesRegex(ValueError,'exactly the35 old windows'):self.validate(d)

    def test_reordered_retained_source_triangles_are_rejected(self):
        d=copy.deepcopy(self.data);m=next(m for m in d['unchangedRemainderMeshes'] if m['indices']);m['indices'][:6]=m['indices'][3:6]+m['indices'][:3]
        p=next(p for p in d['sourceTrianglePartitions'] if p['sourceMeshId']==m['id']);p['replacementRemainderSha256']=guard.digest(m)
        with self.assertRaisesRegex(ValueError,'ordered triangles changed'):self.validate(d)

    def test_rebound_boolean_count_and_acceptance_are_rejected(self):
        for key,value in [('schemaVersion',True),('candidateTriangles',True),('nativeApplied',0),('fullPhotorealismAccepted',True)]:
            with self.subTest(key=key):
                p=copy.deepcopy(self.plan);p[key]=value
                with self.assertRaises(ValueError):self.validate(plan=p)

    def test_changed_original_window_bay_is_rejected(self):
        d=copy.deepcopy(self.data);d['windows'][0]['leftCm']+=.1
        with self.assertRaisesRegex(ValueError,'Source window bay'):self.validate(d)

    def test_solid_wall_behind_window_is_rejected(self):
        d=copy.deepcopy(self.data);w=d['windows'][0];m=next(m for m in d['candidateMeshes'] if m['role']=='wall' and m['buildingSourceId']==w['buildingSourceId']);idx=m['indices'][:3]
        a,t,o=w['originCm'],w['tangent'],w['outward'];l,r,z,b=w['leftCm']+1,w['rightCm']-1,w['bottomCm']+1,w['topCm']-1
        pts=[[a[0]+t[0]*x,a[1]+t[1]*x,h] for x,h in [(l,z),(r,b),(r,z)]]
        for i,p in zip(idx,pts):m['verticesCm'][i]=p;m['normals'][i]=o+[0.];m['tangents'][i]=t+[0.];m['uvs'][i]=[guard.dot([p[k]-a[k] for k in (0,1)],t)/100,p[2]/100]
        with self.assertRaisesRegex(ValueError,'covers actual window opening'):self.validate(d)

    def test_nonfinite_or_boolean_geometry_is_rejected(self):
        for value in [float('nan'),True]:
            d=copy.deepcopy(self.data);d['candidateMeshes'][0]['verticesCm'][0][0]=value
            with self.subTest(value=str(value)),self.assertRaises(ValueError):self.validate(d)

    def test_original_roof_and_reach_are_guarded(self):
        d=copy.deepcopy(self.data);m=next(m for m in d['candidateMeshes'] if m['role']=='roof');m['verticesCm'][0][0]+=1000
        with self.assertRaisesRegex(ValueError,'visual reach'):self.validate(d)

    def test_photographic_roof_and_metal_glass_false_claim_rejected(self):
        r=copy.deepcopy(self.recipes);r['neighbor_roof_red']['evidence']='PHOTOGRAPHIC_CERAMIC'
        with self.assertRaisesRegex(ValueError,'photographic roof'):self.validate(recipes=r)
        r=copy.deepcopy(self.recipes);r['neighbor_window_dielectric']['metallic']=1
        with self.assertRaisesRegex(ValueError,'metallic glazing'):self.validate(recipes=r)

    def test_actual37_glb_float32_roundtrip_and_corruption(self):
        rows=native.export_records(self.bundle)
        with tempfile.TemporaryDirectory(prefix='neighbor-r18-cpu-') as td:
            p=Path(td)/'overlay.glb';native.write_glb(p,rows);proof=native.decode_glb(p,rows)
            self.assertEqual((proof['meshCount'],proof['triangles']),(37,6815));self.assertTrue(proof['sourceCandidateNormalTangentExportVerified']);self.assertFalse(proof['nativeGeometryDecoded'])
            content=bytearray(p.read_bytes());length,_=struct.unpack_from('<II',content,12);document=json.loads(content[20:20+length]);a=document['accessors'][document['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0']];offset=20+length+8+document['bufferViews'][a['bufferView']]['byteOffset'];struct.pack_into('<f',content,offset,99.);p.write_bytes(content)
            with self.assertRaisesRegex(ValueError,'metric UV0 differs'):native.decode_glb(p,rows)


class ReceiptGuards(unittest.TestCase):
    def fixture(self):
        before={};changes=[]
        for i,identity in enumerate(guard.PARTITIONS):
            actor='/Game/Map.Actor'+str(i);component={'name':'mesh','mesh':'/Game/Old/'+identity,'visible':True,'hiddenInGame':False,'navigation':False,'overrideMaterials':[None],
                       'neighborRenderPolicy':{'cast_shadow':True,'cast_hidden_shadow':False},'drawPolicy':{'ld_max_draw_distance':65000},'instanceCullCm':[0,0]}
            before[actor]={'actorTick':False,'components':[component]};hide=identity.endswith('darkroof')
            changes.append({'sourceMeshId':identity,'actor':actor,'componentName':'mesh','beforeMesh':component['mesh'],'afterMesh':component['mesh'] if hide else guard.PREFIX+'/Geometry/neighbor_r18_retained_'+identity,
                            'operation':'hide-empty-source-chunk' if hide else 'replace-with-retained-source-chunk','changedFields':['visible','hiddenInGame','cast_shadow','cast_hidden_shadow'] if hide else ['mesh']})
        added=['/Game/Map.New'+str(i) for i in range(32)];after=guard.expected_original_witness(before,changes);after.update({p:{'owned':True} for p in added});return before,changes,after,added

    def test_only_six_explicit_components_plus32_actors_are_allowed(self):
        before,changes,after,added=self.fixture();proof=guard.verify_original_witness(before,after,changes,added)
        self.assertEqual((proof['addedActors'],proof['affectedComponents']),(32,6));self.assertTrue(proof['allWitnessedOriginalPoliciesPreserved'])
        after['/Game/Map.Foreign']={}
        with self.assertRaisesRegex(ValueError,'addition/removal'):guard.verify_original_witness(before,after,changes,added)

    def test_material_override_cull_tick_and_navigation_are_protected(self):
        for property in ['overrideMaterials','instanceCullCm','navigation','actorTick']:
            before,changes,after,added=self.fixture();actor=next(iter(before))
            if property=='actorTick':after[actor][property]=True
            else:after[actor]['components'][0][property]=True
            with self.subTest(property=property),self.assertRaisesRegex(ValueError,'policy changed'):guard.verify_original_witness(before,after,changes,added)

    def test_empty_roof_cannot_normalize_more_fields(self):
        before,changes,after,added=self.fixture();c=next(c for c in changes if c['operation']=='hide-empty-source-chunk');c['changedFields'].append('navigation')
        with self.assertRaisesRegex(ValueError,'field scope'):guard.expected_original_witness(before,changes)

    def test_exact_content_scope_and_typed_view_delta(self):
        before={'Brezi/Maps/Brezi.umap':'a','Data/viewpoints.json':'b','Brezi/Old.uasset':'c'};package='Brezi/NeighborFinish20261001R18/Geometry/M';after={**before,'Brezi/Maps/Brezi.umap':'d',package+'.uasset':'e'}
        guard.validate_content_delta(before,after,allowed_packages={package})
        after['Data/viewpoints.json']='new'
        with self.assertRaisesRegex(ValueError,'bytes changed'):guard.validate_content_delta(before,after,allowed_packages={package})
        supplemental={'originalViewpoints':{'sha256':'b'},'appendedViewpoints':{'sha256':'new'}};guard.validate_content_delta(before,after,supplemental,{package})
        after['Brezi/Old.uasset']='changed'
        with self.assertRaisesRegex(ValueError,'bytes changed'):guard.validate_content_delta(before,after,supplemental,{package})

    def test_unlisted_same_namespace_native_asset_is_rejected(self):
        p='Brezi/NeighborFinish20261001R18/Foreign.uasset'
        with self.assertRaisesRegex(ValueError,'Unexpected new'):guard.validate_content_delta({}, {p:'h'},allowed_packages=set())

    def test_glass_and_worldposition_native_flags_are_snapshotted(self):
        class Expression:
            def get_editor_property(self,k):return {'desc':'aging','world_position_shader_offset':'WPT_DEFAULT'}[k]
        class Library:
            @staticmethod
            def get_material_expressions(m):return [Expression()]
            @staticmethod
            def get_material_property_input_node(m,p):return None
        class U:
            MaterialEditingLibrary=Library;MaterialExpressionWorldPosition=Expression
            class MaterialProperty:MP_REFRACTION='refraction'
        class M:
            def get_editor_property(self,k):return {'refraction_method':'RM_INDEX_OF_REFRACTION','translucency_lighting_mode':'TLM_SURFACE_PER_PIXEL_LIGHTING'}[k]
        r=materials.graph_snapshot(U,M(),lambda u,m:{'nodes':[{'role':'aging','values':{}}],'roots':{},'flags':{}})
        self.assertEqual(r['flags']['refraction_method'],'RM_INDEX_OF_REFRACTION');self.assertEqual(r['nodes'][0]['values']['world_position_shader_offset'],'WPT_DEFAULT')

    def test_one_appended_camera_preserves_original_root_and_views(self):
        original=guard.read(diagnostic.BASE/'Content/Data/viewpoints.json');v={'id':diagnostic.VIEW_ID,'eyeCm':[1,2,3]};after=diagnostic.append_payload(original,v)
        self.assertEqual(after['views'][:-1],original['views']);self.assertEqual({k:v for k,v in after.items() if k!='views'},{k:v for k,v in original.items() if k!='views'})
        with self.assertRaisesRegex(ValueError,'already exists'):diagnostic.append_payload(after,v)

    def test_glass_native_scalar_readback_does_not_guess_source_float(self):
        roles={'METALLIC':('dielectric-metallic',0.),'ROUGHNESS':('roughness-base',materials.stored_float(.12)),
               'OPACITY':('proposed-thin-glass-opacity',materials.stored_float(.08)),'REFRACTION':('proposed-glass-ior',1.5)}
        graph={'roots':{r:[materials.TAG+k,''] for r,(k,v) in roles.items()},'nodes':[{'role':materials.TAG+k,'values':{'r':v}} for k,v in roles.values()],
               'flags':{'refraction_method':'IOR','blend_mode':'TRANSLUCENT','translucency_lighting_mode':'SURFACE'}}
        self.assertEqual(materials.glass_optical_values(graph)['opacity'],materials.stored_float(.08));graph['nodes'][0]['values']['r']=1.
        with self.assertRaisesRegex(ValueError,'scalar values differ'):materials.glass_optical_values(graph)


if __name__=='__main__':unittest.main(verbosity=2)
