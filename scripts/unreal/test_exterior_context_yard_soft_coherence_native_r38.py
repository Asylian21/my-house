"""Bounded actual binding/counterfactual/reader fixtures; no Unreal execution."""
import copy
import importlib.util
from pathlib import Path
import types
import unittest
P=Path(__file__).with_name('exterior-context-yard-soft-coherence-native-r38.py')
s=importlib.util.spec_from_file_location('r38_final_test_native',P);n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
g=n.g


class FinalScope(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.b=g.load_contract()

    def test_actual_same_path_fresh_target_and_initial_clone(self):
        g.validate_clone(self.b);g.require_native_binding(self.b['binding'])
        self.assertEqual(self.b['targets']['substrate']['actor'],g.DONOR668)
        self.assertEqual(len(self.b['base']['before']),5364)

    def test_invented_binding_and_changed_target_rejected_before_unreal(self):
        for change in ('nativeOwner','selectedNativeProcessId','originalMesh','originalMaterial'):
            binding=copy.deepcopy(self.b['binding'])
            if change in ('originalMesh','originalMaterial'):binding['targetRefs']['substrate'][change]='foreign'
            else:binding[change]='foreign'
            with self.assertRaises(ValueError):g.require_native_binding(binding)

    def test_full_counterfactual_changes_only_two_slot_arrays(self):
        before,expected=self.b['base']['before'],self.b['expected']
        self.assertEqual({p for p in before if before[p]!=expected[p]},{g.ACTOR197,g.DONOR668})
        for role,target in self.b['targets'].items():
            old=copy.deepcopy(before[target['actor']]);new=expected[target['actor']]
            c=old['components'][0];c['materials'][0]=g.ASSETS[role]
            if c['overrideMaterials']:c['overrideMaterials'][0]=g.ASSETS[role]
            else:c['overrideMaterials']=[g.ASSETS[role]]
            self.assertEqual(old,new)

    def test_exact_three_packages_and_map_delta(self):
        base=self.b['base']['content'];current=copy.deepcopy(base)
        current['Brezi/Maps/Brezi.umap']={'bytes':1,'sha256':'0'*64}
        for asset in [*g.ASSETS.values(),g.MASK_ASSET]:current[asset.split('.')[0].replace('/Game/','')+'.uasset']={'bytes':1,'sha256':'1'*64}
        self.assertEqual(g.validate_content_delta(base,current)['newPackages'],3)
        current['foreign.uasset']={'bytes':1,'sha256':'2'*64}
        with self.assertRaises(ValueError):g.validate_content_delta(base,current)

    def test_complete_reader_packet_and_native_graph_adaptation(self):
        h=n.helpers(self.b);records=n.graph_records(self.b)
        self.assertEqual(len(records),64)
        self.assertEqual({k:sum(v['route']==k for v in records.values())for k in ('basic','neighbor','tree')},{'basic':52,'neighbor':9,'tree':3})
        self.assertTrue(h['moduleOrderWitness']['cachePreservedAcrossReusedHelpers'])
        g.validate_native_graphs(self.b['graphs'],self.b['nativeGraphs'])
        bad=copy.deepcopy(self.b['nativeGraphs']);bad['backdrop']['nodes'][0]['values']['foreign']=1
        with self.assertRaises(ValueError):g.validate_native_graphs(self.b['graphs'],bad)

    def test_actual_graph_hash_and_dispatch_mutations_rejected(self):
        original=self.b['base']['report']['materialReadback']['graphs'];asset=next(iter(original));old=original[asset]['graphSha256']
        try:
            original[asset]['graphSha256']='0'*64
            with self.assertRaises(ValueError):n.graph_records(self.b)
        finally:original[asset]['graphSha256']=old

    def test_two_slot_apply_has_no_mesh_or_instance_setter(self):
        calls=[]
        class Component:
            def __init__(self,row):self.row=row
            def get_editor_property(self,key):
                if key!='static_mesh':raise AssertionError(key)
                return types.SimpleNamespace(get_path_name=lambda:self.row['originalMesh'])
            def get_material(self,slot):return types.SimpleNamespace(get_path_name=lambda:self.row['originalMaterial'])
            def set_material(self,slot,material):calls.append((self.row['actor'],slot,material))
        values={'backdrop':'newA','substrate':'newB'}
        lookup=lambda u,actor,name:Component(next(t for t in self.b['targets'].values()if t['actor']==actor))
        n.apply_two_slots(object(),self.b,{'cleanNative':types.SimpleNamespace(component_lookup=lookup)},values)
        self.assertEqual(calls,[(g.ACTOR197,0,'newA'),(g.DONOR668,0,'newB')])

    def test_raw_hash_preserves_binary64_signed_zero_without_transform_api(self):
        class Prop:
            def __init__(self,**kw):self.__dict__.update(kw)
            def get_editor_property(self,key):return getattr(self,key)
        matrix=Prop(**{plane:Prop(x=0.,y=0.,z=0.,w=0.)for plane in ('x_plane','y_plane','z_plane','w_plane')})
        class Component:
            def get_path_name(self):return 'actor.c'
            def get_name(self):return 'c'
            def get_instance_count(self):return 1
            def get_editor_property(self,key):
                if key=='AdditionalRandomSeeds':raise AttributeError(key)
                return {'per_instance_sm_data':[Prop(transform=matrix)],'instancing_random_seed':17,
                    'num_custom_data_floats':0,'per_instance_sm_custom_data':[]}[key]
        c=Component();actor=types.SimpleNamespace(get_path_name=lambda:'actor',get_components_by_class=lambda kind:[c])
        subsystem=types.SimpleNamespace(get_all_level_actors=lambda:[actor])
        u=types.SimpleNamespace(EditorActorSubsystem=object(),InstancedStaticMeshComponent=object(),get_editor_subsystem=lambda kind:subsystem)
        witness={'actor':{'components':[{'name':'c','instanceCount':1}]}}
        a=n.raw_instance_controls(u,witness);matrix.x_plane.x=-0.;b=n.raw_instance_controls(u,witness)
        self.assertNotEqual(a['actor.c']['rawMatrixBinary64Sha256'],b['actor.c']['rawMatrixBinary64Sha256'])
        self.assertEqual(a['actor.c']['mainRandomSeed'],17)
        self.assertFalse(a['actor.c']['additionalRandomSeeds']['available'])


if __name__=='__main__':unittest.main()
