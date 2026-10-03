"""Eight CPU source/contract fixtures; never native or appearance evidence."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('r29_cpu_scope',ROOT/'scripts/unreal/exterior-original-tree-group-guards-r29.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)


class Scope(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.source,cls.roots,cls.full=g.source();cls.base=g.actual_base();cls.donor=g.saved_tree()
  cls.measurement={'rootIds':g.IDS[:],'recoveredValues':[[r['originalSourceRow']['positionCm'],[0.,0.,0.,1.],[r['fit']['uniformScale']]*3]for r in cls.roots]}
  cls.after=copy.deepcopy(cls.base['content']);cls.after.update({r['relativeContentPath']:{'sha256':r['sha256'],'bytes':r['bytes']}for r in cls.donor['packages']});cls.after['Brezi/Maps/Brezi.umap']={'sha256':'0'*64,'bytes':1}

 def test_actual_four_unique_whole_source_roots(self):
  self.assertEqual([r['rootId']for r in self.roots],g.IDS);self.assertEqual(len(set(g.IDS)),4)
  self.assertEqual(sum(r['fit']['allTransformedSourceVertices']for r in self.roots),7109112)
  self.assertTrue(all(r['fit']['circleRadiusCm']<r['originalSourceRow']['radiusCm']for r in self.roots))

 def test_whole_retirement_changes_only_two_counter_fields(self):
  after=g.empty_original(self.base['witness'],self.base['targetActor']);row=after[self.base['targetActor']];row['components'][0]['instanceCount']=4
  row['components'][0]['orderedInstanceTransformsSha256']=self.base['targetWitness']['components'][0]['orderedInstanceTransformsSha256']
  self.assertEqual(after,self.base['witness'])

 def test_partial_or_foreign_original_group_rejected(self):
  for field,value in [('label','foreign-group'),('instanceCount',3)]:
   before=copy.deepcopy(self.base['witness']);r=before[self.base['targetActor']]
   if field=='label':r[field]=value
   else:r['components'][0][field]=value
   with self.assertRaises(RuntimeError):g.empty_original(before,self.base['targetActor'])

 def test_duplicate_replacement_identity_rejected(self):
  m=copy.deepcopy(self.measurement);m['rootIds'][3]=m['rootIds'][0]
  with self.assertRaises(RuntimeError):g.added_expected(self.donor['template'],self.donor['templateActor'],'/Fixture/New',m,[100000,125000])

 def test_declared_counts_keep_population_and_empty_old_component(self):
  expected=g.empty_original(self.base['witness'],self.base['targetActor']);path='/Fixture/NEW-R29-Source-Only'
  expected[path]=g.added_expected(self.donor['template'],self.donor['templateActor'],path,self.measurement,[100000,125000])
  components=[c for a in expected.values()for c in a['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
  self.assertEqual((len(expected),len(components),sum(c['instanceCount']for c in components)),(5351,2313,676957))
  self.assertEqual(expected[path]['tags'],sorted(['BreziGenerated',g.TAG]));self.assertNotIn('BreziExterior20260926',expected[path]['tags'])

 def test_package_closure_accepts_only_exact17_plus_map(self):
  proof=g.validate_content(self.base['content'],self.after,self.donor['packages']);self.assertEqual(proof['copiedPackages'],17)
  changed=copy.deepcopy(self.after);changed['Data/viewpoints.json']={'sha256':'1'*64,'bytes':1}
  with self.assertRaises(RuntimeError):g.validate_content(self.base['content'],changed,self.donor['packages'])

 def test_extra_or_changed_native_package_rejected(self):
  foreign=copy.deepcopy(self.after);foreign['Foreign/extra.uasset']={'sha256':'0'*64,'bytes':1}
  with self.assertRaises(RuntimeError):g.validate_content(self.base['content'],foreign,self.donor['packages'])
  changed=copy.deepcopy(self.after);changed[self.donor['packages'][0]['relativeContentPath']]['sha256']='1'*64
  with self.assertRaises(RuntimeError):g.validate_content(self.base['content'],changed,self.donor['packages'])

 def test_observed_binary64_control_signed_zero_changes_rejected(self):
  with self.assertRaises(RuntimeError):g.exact({'matrix':[[0.]]},{'matrix':[[-0.]]})


if __name__=='__main__':unittest.main(verbosity=2)
