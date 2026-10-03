"""Ten changed combined-consumer contracts; mocked UObject calls are not UE proof."""
import copy,importlib.util,unittest
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[2]
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
n=module('_r46_native_fixture',ROOT/'scripts/unreal/exterior-burkea-clay-native-r46.py');g=n.g
r=g.module('_r46_roof_fixture',g.ROOF,g.ROOF_SHA)
old_fixture=module('_r46_mock_classes_only',ROOT/'scripts/unreal/test_exterior_context_parcel_boundary_materials_r43.py')
class RoofMock(old_fixture.MockNative):
    def __init__(self):
        super().__init__();self.MaterialExpressionMultiply=type('MaterialExpressionMultiply',(old_fixture.Properties,),{})
        create=self.MaterialEditingLibrary.create_material_expression
        def expression(material,cls,x,y):
            node=create(material,cls,x,y);node.get_class=lambda:SimpleNamespace(get_name=lambda:cls.__name__)
            getter=node.get_editor_property
            node.get_editor_property=lambda key: 'SamplerSourceMode.SSM_FROM_TEXTURE_ASSET'if key=='sampler_source'else getter(key)
            return node
        self.MaterialEditingLibrary.create_material_expression=expression
        self.MaterialEditingLibrary.get_material_expressions=lambda material:material.nodes
        def save(obj,only_if_is_dirty=False):self.saved.append(obj.path);return True
        self.EditorAssetLibrary.save_loaded_asset=save
    def graph(self,u,material):
        result=super().graph(u,material)
        for row,node in zip(result['nodes'],material.nodes):
            if row['class']=='MaterialExpressionMultiply':
                row['inputs']=[[port,node.inputs[port][0].values['desc'],node.inputs[port][1]]for port in ('A','B')]
        result['flags']=r.policy().api().material_policy(material);return result

class Contracts(unittest.TestCase):
    BUNDLE=None
    @classmethod
    def setUpClass(cls):cls.bundle=cls.BUNDLE if cls.BUNDLE is not None else g.load_contract()
    def mock_build(self):
        u=RoofMock();material,report=r.build_materials(u,self.bundle,self.bundle['binding'],u.graph);return u,material,report
    def test_exact_actual72_114_packet_and_private_leaf_route(self):
        b=self.bundle;self.assertEqual(set(b),{'source','base','binding'})
        self.assertEqual({k:len(v)for k,v in b['base']['materialReaderDispatch'].items()},{'basic':60,'neighbor':9,'tree':3})
        h=n.helpers(b);self.assertIn('moduleOrderWitness',h);leaf,p=n.private_leaf_adapter(b);self.assertTrue(leaf.require_native_binding(p))
        bad=copy.copy(p);bad['source']=b['source']
        with self.assertRaises(RuntimeError):leaf.require_native_binding(bad)
    def test_combined_counterfactual_is_only_five_exact_slots(self):
        b=self.bundle;before=b['base']['savedWitness'];after=g.expected_counterfactual(before,b)
        changed=[a for a in before if g.digest(before[a])!=g.digest(after[a])];self.assertEqual(len(changed),5)
        for actor in set(before)-set(changed):g.exact(before[actor],after[actor],'Undeclared original actor changed')
        leaf=g.leaf_math();c=next(c for c in after[leaf.ACTOR]['components']if c['path']==leaf.COMPONENT)
        self.assertEqual(c['overrideMaterials'],[None,leaf.OWN_MATERIAL]);self.assertEqual(len(after),5371)
    def test_historical_target_pose_or_mesh_mutation_rejected(self):
        bad=copy.deepcopy(self.bundle['base']['savedWitness']);target=self.bundle['source']['roof']['proposal']['targets'][0]
        bad[target['actor']]['components'][0]['mesh']='wrong'
        with self.assertRaises(RuntimeError):g.expected_counterfactual(bad,self.bundle)
    def test_two_graph_three_texture_package_delta_rejects_extra_or_old_asset_edit(self):
        b=self.bundle;before=b['base']['content'];after=copy.deepcopy(before)
        after['Brezi/Maps/Brezi.umap']={'sha256':'f'*64,'bytes':1}
        for a in g.expected_packages(b['source']):after[a.split('.')[0].replace('/Game/','')+'.uasset']={'sha256':'e'*64,'bytes':1}
        self.assertEqual(len(g.validate_content_delta(before,after,b['source'])['newRelativeFiles']),5)
        bad=copy.deepcopy(after);bad['unexpected.uasset']={'sha256':'d'*64,'bytes':1}
        with self.assertRaises(RuntimeError):g.validate_content_delta(before,bad,b['source'])
        bad=copy.deepcopy(after);k=next(k for k in before if k!='Brezi/Maps/Brezi.umap');bad[k]={'sha256':'d'*64,'bytes':1}
        with self.assertRaises(RuntimeError):g.validate_content_delta(before,bad,b['source'])
    def test_unrecorded_original3_aux_usage_and_complete_texture_schema(self):
        b=self.bundle['base'];missing=[v for v in b['materialRecords'].values()if not v['usagePreviouslyRecorded']]
        self.assertEqual(len(missing),3);self.assertTrue(all(v['aux']is None and v['recordedUsage']=={}for v in missing))
        self.assertEqual(len(b['textureRecords']),114)
        for row in b['textureRecords'].values():self.assertEqual(len(row['snapshot']['values']),24);self.assertNotIn('partialSnapshot',row)
    def test_roof_binding_denied_before_any_asset_access(self):
        class NoAssetAccess:
            def __getattr__(self,key):raise AssertionError('UObject reached before binding')
        bad=copy.deepcopy(self.bundle['binding']);bad['candidateProject']='wrong'
        with self.assertRaises(RuntimeError):r.build_materials(NoAssetAccess(),self.bundle,bad,None)
    def test_mock_roof_roundtrip_four_saves_and_original_normal_chain(self):
        u,material,report=self.mock_build();self.assertIs(r.verify_materials(u,self.bundle,self.bundle['binding'],report,u.graph),material)
        self.assertEqual(len(u.tasks),3);self.assertEqual(len(u.saved),4);self.assertEqual(len(report['material']['graph']['nodes']),8)
        self.assertTrue(u.assets[report['textures']['normalGL']['asset']].values['flip_green_channel'])
        self.assertEqual(report['material']['graphAudit']['photoUvScale'],[.25,-.25])
        self.assertEqual(report['material']['graphAudit']['decodedTangentNormalSign'],[1,-1,1])
    def test_all_five_roof_flags_mutations_reject(self):
        u,material,report=self.mock_build()
        for key,value in {'blend_mode':'wrong','shading_model':'wrong','two_sided':True,'tangent_space_normal':False,'use_material_attributes':True}.items():
            original=material.values[key];material.values[key]=value
            with self.subTest(key=key),self.assertRaises((RuntimeError,ValueError)):r.verify_materials(u,self.bundle,self.bundle['binding'],report,u.graph)
            material.values[key]=original
    def test_saved_texture_and_metadata_mutations_reject(self):
        u,material,report=self.mock_build();t=u.assets[report['textures']['normalGL']['asset']]
        t.values['flip_green_channel']=False
        with self.assertRaises((RuntimeError,ValueError)):r.verify_materials(u,self.bundle,self.bundle['binding'],report,u.graph)
        t.values['flip_green_channel']=True;t.tags['BreziSourceLicense']='wrong'
        with self.assertRaises(RuntimeError):r.verify_materials(u,self.bundle,self.bundle['binding'],report,u.graph)
    def test_shader_uv_sign_channel_and_evidence_mutations_reject(self):
        u,material,report=self.mock_build();source=self.bundle['source']['roof']['proposal'];graph=report['material']['graph']
        for role,key,value in [('uv','v_tiling',.25),('reflectionSign','constant',[1,1,1,1])]:
            bad=copy.deepcopy(graph);next(v for v in bad['nodes']if v['role'].endswith(':'+role))['values'][key]=value
            with self.subTest(role=role),self.assertRaises(RuntimeError):r.kernel().validate_graph(bad,source)
        bad=copy.deepcopy(graph);bad['roots']['ROUGHNESS'][-1]='G'
        with self.assertRaises(RuntimeError):r.kernel().validate_graph(bad,source)
        bad=copy.deepcopy(report);bad['nativeAppearanceAccepted']=True
        with self.assertRaises(RuntimeError):r.verify_materials(u,self.bundle,self.bundle['binding'],bad,u.graph)
if __name__=='__main__':unittest.main()
