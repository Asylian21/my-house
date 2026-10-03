"""Twelve changed-contract fixtures; mocks prove routes, never UE acceptance."""
import copy
import importlib.util
import math
from pathlib import Path
from types import SimpleNamespace
import unittest
ROOT=Path(__file__).resolve().parents[2]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,ROOT/path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
n=load('_r39_native_tests','scripts/unreal/exterior-neighbor-props-native-r39.py')
d=load('_r39_prior_mock_types','scripts/unreal/test_exterior_neighbor_props_r39_draft.py')

class Field:
    def __init__(self,axes,values):
        self.axes=axes
        for k,v in zip(axes,values):setattr(self,k,v)
    def set_editor_property(self,k,v):setattr(self,k,v)
class Transform:
    def __init__(self,t=None,q=None,s=None):
        self.translation=Field('xyz',t or [0.,0.,0.]);self.rotation=Field('xyzw',q or [0.,0.,0.,1.]);self.scale3d=Field('xyz',s or [1.,1.,1.])
    def get_editor_property(self,k):return getattr(self,k)
    def set_editor_property(self,k,v):setattr(self,k,v)
class Math:
    @staticmethod
    def transform_location(root,p):
        q=root.rotation;s=root.scale3d;v=root.translation
        x,y,z=p.x*s.x,p.y*s.y,p.z*s.z;co=1-2*q.z*q.z;si=2*q.z*q.w
        return Field('xyz',[v.x+co*x-si*y,v.y+si*x+co*y,v.z+z])
    @staticmethod
    def compose_transforms(node,root):
        p=Math.transform_location(root,node.translation)
        return Transform([p.x,p.y,p.z],[getattr(root.rotation,k)for k in 'xyzw'],[getattr(root.scale3d,k)for k in 'xyz'])
class Stored:
    def __init__(self,t):
        v=n.transform_value(t);q=t.rotation;scale=t.scale3d;co=1-2*q.z*q.z;si=2*q.z*q.w
        self.planes={'x_plane':Field('xyzw',[co*scale.x,si*scale.x,0.,0.]),
            'y_plane':Field('xyzw',[-si*scale.y,co*scale.y,0.,0.]),'z_plane':Field('xyzw',[0.,0.,scale.z,0.]),
            'w_plane':Field('xyzw',v[0]+[1.])}
    def get_editor_property(self,k):return SimpleNamespace(**self.planes)
class Transient:
    def __init__(self):self.rows=[]
    def get_path_name(self):return '/Engine/Transient.MockHISM'
    def get_editor_property(self,k):return None if k=='static_mesh'else[Stored(t)for t in self.rows]
    def add_instance(self,t,world):self.rows.append(copy.deepcopy(t));return len(self.rows)-1
    def get_instance_transform(self,i,world):return self.rows[i]
    def clear_instances(self):self.rows=[]
    def get_instance_count(self):return len(self.rows)
FAKE=SimpleNamespace(Transform=Transform,HierarchicalInstancedStaticMeshComponent=Transient,new_object=lambda cls:cls(),MathLibrary=Math)

class NativeContracts(unittest.TestCase):
    BUNDLE=None
    @classmethod
    def setUpClass(cls):
        if cls.BUNDLE is None:cls.BUNDLE=n.g.load_contract(validate_current=False)
        cls.b=cls.BUNDLE;cls.parts={p['key']:p for rows in cls.b['source']['parts'].values()for p in rows}
    def rejection(self,f,*args):
        with self.assertRaises(RuntimeError):f(*args)
    def poses(self):return {k:Transform(p['proposedNativeNodeTranslationCm'])for k,p in self.parts.items()}
    def test_01_actual_frozen_parent_packet_helpers(self):
        base=self.b['base'];original=base['native'];calls=[]
        helper={k:object()for k in ('cleanNative','existing','rural','meshHelper','materials','treeMaterials','moduleOrderWitness')}
        base['native']=SimpleNamespace(helpers=lambda packet:(calls.append(packet)or helper))
        try:
            self.assertIs(n.helpers(self.b),helper);self.assertIs(calls[0]['base']['report'],base['parentReport'])
            wrong={**self.b,'base':{**base,'readerPacket':{'base':{'report':base['report']}}}}
            self.rejection(n.helpers,wrong)
        finally:base['native']=original
    def test_02_all_original_four_complete_corner_identities(self):
        u=SimpleNamespace(TriangleID=d.Id)
        for part in self.parts.values():
            row=n.full_part_identity(u,d.Mesh(part),part);self.assertEqual(row['triangles'],part['triangles']);self.assertFalse(row['sourceIdentityFromCountAlone'])
        self.assertEqual(sum(p['triangles']for p in self.parts.values()),26601)
    def test_03_count_cannot_accept_reversed_or_changed_uv_source(self):
        part=next(iter(self.parts.values()));rows=n.expected_corners(part)
        changed=copy.deepcopy(rows);face=list(changed[0]);face[1],face[2]=face[2],face[1];changed[0]=n.cyclic(face)
        self.rejection(n.validate_corner_rows,part,changed)
        changed=copy.deepcopy(rows);face=list(changed[0]);face[0]=(*face[0][:3],face[0][3]+.125,face[0][4]);changed[0]=n.cyclic(face)
        self.rejection(n.validate_corner_rows,part,changed)
    def test_04_whole_hose_binding_cannot_drop_or_hide_coil_translation(self):
        parts=self.b['source']['parts'][n.g.MODEL_IDS[0]];u=SimpleNamespace(StaticMeshComponent=object,TriangleID=d.Id)
        actors=[];inventory=[]
        for i,p in enumerate(parts):
            path='/Game/Temp.Source_'+str(i);component=d.Component(d.Mesh(p),path+'.SMC');pose=[p['proposedNativeNodeTranslationCm'],[0.,0.,0.,1.],[1.,1.,1.]]
            actor=d.Actor(path,component,Transform(pose[0]));actor.get_editor_property=lambda k,c=component:c if k=='root_component'else None
            component.get_owner=lambda a=actor:a
            actors.append(actor);inventory.append({'actor':path,'parent':None,'components':[],
                'class':'/Script/Engine.StaticMeshActor','label':'arbitrary','primitiveComponents':[component.get_path_name()],'transform':pose})
        meshes,bindings,_=n.bind_imported_parts(u,parts,actors,{'objects':inventory});self.assertEqual(len(meshes),2)
        wrong=copy.deepcopy(inventory);wrong[1]['transform'][0]=[0.,0.,0.]
        self.rejection(n.bind_imported_parts,u,parts,actors,{'objects':wrong})
        self.rejection(n.bind_imported_parts,u,parts,actors[:1],{'objects':inventory[:1]})
        actors[1].component.get_owner=lambda:None
        self.rejection(n.bind_imported_parts,u,parts,actors,{'objects':inventory})
    def test_05_eight_composed_poses_bind_six_authored_assemblies(self):
        values,proof=n.measure(FAKE,self.b,self.poses());self.assertEqual(sum(len(v)for v in values.values()),8)
        self.assertTrue(n.validate_measurement_receipt(self.b,proof));self.assertEqual(len(set(x for m in proof.values()for x in m['assemblyRootIds'])),6)
        coil=proof['garden_hose_wall_mounted_01:1'];root=coil['assemblyInputValues'][0];point=coil['composedInputValues'][0][0]
        self.assertNotEqual(point,root[0]);self.assertEqual(point[2],root[0][2]+self.parts[coil['part']]['proposedNativeNodeTranslationCm'][2])
    def test_06_authored_xyz_yaw_scale_and_part_pose_tampering_reject(self):
        _,proof=n.measure(FAKE,self.b,self.poses());key=next(iter(proof))
        for field,index in [('assemblyInputValues',0),('originalImportedNodeValues',0),('composedInputValues',0)]:
            wrong=copy.deepcopy(proof);wrong[key][field][index][0][0]+=.1;self.rejection(n.validate_measurement_receipt,self.b,wrong)
        wrong=copy.deepcopy(proof);wrong[key]['assemblyInputValues'][0][1][2]+=.01;self.rejection(n.validate_measurement_receipt,self.b,wrong)
        wrong=copy.deepcopy(proof);wrong[key]['assemblyInputValues'][0][2][0]=2.;self.rejection(n.validate_measurement_receipt,self.b,wrong)
    def test_07_actual_independent_composition_guard_not_added_witness_only(self):
        row=self.b['source']['proposal']['placements'][0];part=self.parts['garden_hose_wall_mounted_01:1'];root=n.authored_root(FAKE,row);node=self.poses()[part['key']]
        got=Math.compose_transforms(node,root);expected=n.transform_value(got)
        self.assertTrue(n.validate_intended_pose(row,part,n.transform_value(root),n.transform_value(node),n.transform_value(got),expected))
        wrong=copy.deepcopy(expected);wrong[0][2]+=1;self.rejection(n.validate_intended_pose,row,part,n.transform_value(root),n.transform_value(node),wrong,expected)
    def test_08_raw_matrix_translation_and_signed_zero_are_exact(self):
        _,proof=n.measure(FAKE,self.b,self.poses());key=next(iter(proof));wrong=copy.deepcopy(proof)
        wrong[key]['storedMatrices'][0][3][0]+=.01;self.rejection(n.validate_measurement_receipt,self.b,wrong)
        self.rejection(n.exact,[0.],[-0.],'signed zero differs')
    def test_09_template_relocation_full_counterfactual_preserves_all_old_fields(self):
        _,proof=n.measure(FAKE,self.b,self.poses());before=self.b['base']['savedWitness'];added={}
        for i,(key,part)in enumerate(self.parts.items()):
            path='/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.MockNew_'+str(i)
            mesh=n.g.PREFIX+'/Geometry/StaticMeshes/'+key.replace(':','_')+'.own'
            added[path]=n.added_expected(self.b,key,path,mesh,'/Game/Owned.Material',proof[key])
        expected=n.g.expected_counterfactual(before,added);self.assertEqual(len(expected),5368)
        self.assertEqual({k:v for k,v in expected.items()if k in before},before)
        for row in added.values():self.assertEqual(row['components'][0]['overrideMaterials'],[]);self.assertEqual(row['tags'],sorted(row['tags']))
    def test_10_old_raw_all_components_gate_rejects_one_changed_hash(self):
        wanted=self.b['base']['rawControls'];base=self.b['base'];original=base['native']
        base['native']=SimpleNamespace(raw_instance_controls=lambda u,w:{**wanted,'new':{'instances':8}})
        try:self.assertEqual(n.original_raw(None,self.b,{}),wanted)
        finally:base['native']=original
        wrong=copy.deepcopy(wanted);next(iter(wrong.values()))['rawMatrixBinary64Sha256']='0'*64
        base['native']=SimpleNamespace(raw_instance_controls=lambda u,w:wrong)
        try:self.rejection(n.original_raw,None,self.b,{})
        finally:base['native']=original
    def test_11_all97_texture_snapshot_fields_are_compared_without_hidden_property(self):
        records=self.b['base']['textureRecords'];h={'materials':SimpleNamespace(texture_snapshot=lambda u,t:records[t])}
        u=SimpleNamespace(Texture2D=str,EditorAssetLibrary=SimpleNamespace(load_asset=lambda a:a))
        self.assertEqual(n.old_texture_witness(u,self.b,h),records)
        first=next(iter(records));wrong=copy.deepcopy(records[first]);wrong['values']['lod_bias']+=1
        h['materials'].texture_snapshot=lambda u,t:wrong if t==first else records[t]
        self.rejection(n.old_texture_witness,u,self.b,h)
    def test_12_exact21_original_namespace_packages_and_primary_transform_api(self):
        assets=n.g.expected_new_packages(self.b['source']);self.assertEqual(len(assets),21)
        self.assertEqual(sum('/Geometry/'in x for x in assets),4);self.assertEqual(sum('/Pipeline/'in x for x in assets),3)
        self.assertTrue(all(Path(p['path']).is_file()for p in n.primary_api().values()))

if __name__=='__main__':unittest.main(verbosity=2)
