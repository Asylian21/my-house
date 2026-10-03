"""Six targeted measured-node/private-binding repair fixtures; no UE calls."""
import copy
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
ROOT=Path(__file__).resolve().parents[2]
def load(name,file):
    s=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
n=load('_r39_r2_native_fixture','exterior-neighbor-props-native-r39-r2.py')
prior=load('_r39_frozen_mock_types','test_exterior_neighbor_props_native_r39.py')

class CalibrationContracts(unittest.TestCase):
    BUNDLE=None
    @classmethod
    def setUpClass(cls):
        if cls.BUNDLE is None:cls.BUNDLE=n.g.load_contract(validate_current=False)
        cls.b=cls.BUNDLE;cls.parts={p['key']:p for rows in cls.b['source']['parts'].values()for p in rows}
    def rejection(self,fn,*args):
        with self.assertRaises(RuntimeError):fn(*args)
    def poses(self):return {key:prior.Transform(n.g.native_node_translation(part))for key,part in self.parts.items()}
    def test_01_original_parts_stay_frozen_and_calibrated_route_is_exact_f64(self):
        coil=self.parts['garden_hose_wall_mounted_01:1'];source=coil['sourceNodeTranslationMeters']
        wanted=[100*source[0],100*source[2],100*source[1]]
        self.assertEqual(n.g.native_node_translation(coil),wanted)
        self.assertEqual(wanted,[-1.3036099262535572,6.431593745946884,-5.608365684747696])
        self.assertNotEqual(wanted,coil['proposedNativeNodeTranslationCm'])
        self.assertEqual(coil['proposedNativeNodeTranslationCm'],[-1.3036099672317505,6.431593894958496,-5.608365535736084])
        immutable=n.g.c.load_source();self.assertEqual(self.b['source'],immutable)
    def test_02_actual_checkpoint_pose_matches_f64_and_f32_route_rejects(self):
        part=self.parts['garden_hose_wall_mounted_01:1'];row=self.b['source']['proposal']['placements'][0]
        root=n.authored_root(prior.FAKE,row);node=self.poses()[part['key']];world=prior.Math.compose_transforms(node,root)
        actual=n.transform_value(world)
        self.assertTrue(n.validate_intended_pose(row,part,n.transform_value(root),n.transform_value(node),actual,actual))
        wrong=n.transform_value(node);wrong[0]=part['proposedNativeNodeTranslationCm']
        self.rejection(n.validate_intended_pose,row,part,n.transform_value(root),wrong,actual,actual)
        bad=n.transform_value(node);bad[0][0]+=1e-12
        self.rejection(n.validate_intended_pose,row,part,n.transform_value(root),bad,actual,actual)
    def test_03_complete_hose_identity_binds_calibrated_pose_not_label(self):
        parts=self.b['source']['parts'][n.g.MODEL_IDS[0]];u=SimpleNamespace(StaticMeshComponent=object,TriangleID=prior.d.Id);actors=[];inventory=[]
        for i,p in enumerate(parts):
            path='/Game/Temp.Observed_'+str(i);component=prior.d.Component(prior.d.Mesh(p),path+'.SMC');pose=[n.g.native_node_translation(p),[0.,0.,0.,1.],[1.,1.,1.]]
            actor=prior.d.Actor(path,component,prior.Transform(pose[0]));actor.get_editor_property=lambda k,c=component:c if k=='root_component'else None
            component.get_owner=lambda a=actor:a;actors.append(actor)
            inventory.append({'actor':path,'parent':None,'class':'/Script/Engine.StaticMeshActor','label':'untrusted_label',
                'components':[],'primitiveComponents':[component.get_path_name()],'transform':pose})
        meshes,bindings,_=n.bind_imported_parts(u,parts,actors,{'objects':inventory});self.assertEqual(len(meshes),2)
        self.assertTrue(all(not r['sourceLabelsUsedForIdentity']for r in bindings))
        wrong=copy.deepcopy(inventory);wrong[1]['transform'][0]=parts[1]['proposedNativeNodeTranslationCm']
        self.rejection(n.bind_imported_parts,u,parts,actors,{'objects':wrong})
    def test_04_eight_source_assembly_poses_measure_with_f64_coil(self):
        values,proof=n.measure(prior.FAKE,self.b,self.poses());self.assertEqual(sum(len(v)for v in values.values()),8)
        self.assertTrue(n.validate_measurement_receipt(self.b,proof))
        coil=proof['garden_hose_wall_mounted_01:1'];expected=n.g.native_node_translation(self.parts[coil['part']])
        self.assertEqual(coil['originalImportedNodeValues'][0][0],expected)
        wrong=copy.deepcopy(proof);wrong[coil['part']]['originalImportedNodeValues'][0][0]=self.parts[coil['part']]['proposedNativeNodeTranslationCm']
        self.rejection(n.validate_measurement_receipt,self.b,wrong)
    def test_05_private_material_binding_adapter_keeps_frozen_kernels_and_three_key_packet(self):
        maps=n.material_module();self.assertIs(maps.binding_guard(),n.g)
        packet=n.material_packet(self.b);self.assertEqual(set(packet),{'source','base','binding'});self.assertIs(packet['source'],self.b['source'])
        self.assertIs(maps.validate_binding(packet,self.b['binding']),self.b['source'])
        wrong=copy.deepcopy(self.b['binding']);wrong['schemaVersion']=1
        self.rejection(maps.validate_binding,packet,wrong)
        evidence=n.material_adapter_evidence();self.assertEqual(evidence['source']['sha256'],n.MATERIAL_SHA)
        self.assertTrue(evidence['onlyPrivateModuleBindingLoaderChanged']);self.assertFalse(evidence['originalModulesOrSourceFilesMutated'])
    def test_06_material_build_roundtrip_uses_actual_repair_binding_without_old_recipe_changes(self):
        fixtures=load('_r39_frozen_material_mocks','test_exterior_neighbor_props_materials_r39.py');u=fixtures.MockNative();maps=n.material_module();packet=n.material_packet(self.b)
        objects,report=maps.build_materials(u,packet,self.b['binding'],u.graph)
        self.assertEqual(maps.verify_materials(u,packet,self.b['binding'],report,u.graph),objects)
        self.assertEqual(report['nativeBinding'],self.b['binding']);self.assertEqual(report['owner'],'scripts/unreal/exterior-neighbor-props-materials-r39.py')
        self.assertEqual(len(report['newPackageAssets']),14)
        self.assertTrue(all(row['instancedStaticMeshUsage']for row in report['materials'].values()))
        self.assertFalse(report['nativeAppearanceAccepted'])

if __name__=='__main__':unittest.main(verbosity=2)
