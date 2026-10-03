"""Only changed R43 geometry/template/packet contracts; no UObject proof."""
import copy,importlib.util,struct,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def mod(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
n=mod('_r43_fixture_native',ROOT/'scripts/unreal/exterior-context-parcel-boundary-native-r43.py');g=n.g;s=mod('_r43_fixture_export',ROOT/'scripts/unreal/exterior-context-parcel-boundary-native-study-r43.py')
class Contracts(unittest.TestCase):
 BUNDLE=None
 @classmethod
 def setUpClass(cls):cls.b=cls.BUNDLE or g.load_contract()
 def test01_complete_source_export_and_written_arrays(self):
  rows=self.b['source']['exportRows'];self.assertEqual([len(r['indices'])//3 for r in rows],[3256,9308,2]);self.assertEqual(s.verify_glb(s.encode_glb(rows),rows)['encodedTriangles'],12566)
 def test02_attribute_and_winding_mutations_reject(self):
  for field,index in [('gltfPositions',0),('gltfNormals',0),('uv0',0),('indices',0)]:
   row=copy.deepcopy(self.b['source']['exportRows'][0]);row[field][index]=row[field][index]+1 if field=='indices'else [v+.01 for v in row[field][index]]
   with self.assertRaises(RuntimeError):g.validate_export(row,self.b['source']['geometry']['meshes'][0])
 def test03_full_corner_identity_is_not_count_identity(self):
  row=self.b['source']['exportRows'][0];corners=n.expected_corners(row);self.assertEqual(len(corners),3256);altered=copy.deepcopy(row);altered['uv0'][0][0]+=.1;self.assertNotEqual(n.expected_corners(altered),corners);reversed_row=copy.deepcopy(row);reversed_row['indices'][:3]=reversed_row['indices'][:3][::-1];self.assertNotEqual(n.expected_corners(reversed_row),corners)
 def test04_source_normals_and_gltf_front_winding(self):
  for r in self.b['source']['exportRows']:
   for at in range(0,len(r['indices']),3):
    ids=r['indices'][at:at+3];p=[r['gltfPositions'][i]for i in ids];a=[p[1][k]-p[0][k]for k in range(3)];b=[p[2][k]-p[0][k]for k in range(3)];cross=[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]];self.assertGreater(sum(cross[k]*r['gltfNormals'][ids[0]][k]for k in range(3)),0)
 def test05_template_three_actor_counterfactual(self):
  before=self.b['base']['savedWitness'];added={}
  for role in g.MATERIAL_ROLES:
   path='/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.fixture_boundary_'+role;added[path]=g.added_expected(self.b,role,path,g.PREFIX+'/Geometry/StaticMeshes/boundary_'+role+'_r43.boundary_'+role+'_r43',g.PREFIX+'/Materials/M_boundary_'+role+'_r43.M_boundary_'+role+'_r43');g.exact(added[path]['transform'],g.IDENTITY,'identity differs');self.assertEqual(added[path]['components'][0]['collision'],'<CollisionEnabled.NO_COLLISION: 0>')
  expected=g.expected_counterfactual(before,added);self.assertEqual(len(expected),5371);self.assertEqual(g.digest({k:expected[k]for k in before}),g.digest(before));self.assertFalse(added[next(k for k in added if k.endswith('gravel'))]['components'][0]['renderFlags']['cast_shadow'])
 def test06_package_delta_rejects_redirector_or_old_change(self):
  before=copy.deepcopy(self.b['base']['content']);after=copy.deepcopy(before);after['Brezi/Maps/Brezi.umap']={'sha256':'a'*64,'bytes':1}
  for a in g.expected_new_packages():after[a.split('.')[0].replace('/Game/','')+'.uasset']={'sha256':'b'*64,'bytes':1}
  self.assertEqual(len(g.validate_content_delta(before,after)['newRelativeFiles']),15);after['Brezi/extra.uasset']={'sha256':'c'*64,'bytes':1}
  with self.assertRaises(RuntimeError):g.validate_content_delta(before,after)
 def test07_new_original_texture_partial_authentication(self):
  report=self.b['base']['report'];snapshot=next(iter(next(iter(report['materialReport']['materials'].values()))['textures'].values()))['snapshot'];full={'size':snapshot['pixels'],'sourceEncoding':snapshot['sourceEncoding'],'alphaCoverageThresholds':snapshot['alphaCoverageThresholds'],'values':{k:v for k,v in snapshot.items()if k not in ('pixels','sourceEncoding','alphaCoverageThresholds')}};g.texture_subset(full,snapshot);full['values']['srgb']=not full['values']['srgb']
  with self.assertRaises(RuntimeError):g.texture_subset(full,snapshot)
 def test08_actual_base_packet_and_signed_zero(self):
  h=n.helpers(self.b);self.assertIn('cleanNative',h);self.assertEqual(len(self.b['base']['materialRecords']),69);self.assertEqual(len(self.b['base']['textureRecords']),108);self.assertEqual(len(self.b['base']['rawControls']),2325)
  with self.assertRaises(RuntimeError):g.exact([0.],[-0.],'signedzero differs')
if __name__=='__main__':unittest.main()
