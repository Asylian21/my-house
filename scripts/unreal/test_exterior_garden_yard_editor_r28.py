"""Focused R37R2 saved-checker mutations; no Unreal or historical producers."""
import copy
import importlib.util
from pathlib import Path
import struct
from unittest.mock import patch
import unittest

ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('r28_owned_checker_fixtures',ROOT/'scripts/unreal/exterior-garden-yard-editor-check-r28.py')
c=importlib.util.module_from_spec(s);s.loader.exec_module(c)


class SavedScope(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.r,cls.plan,cls.bundle,cls.packet=c.load_actual(c.REPORT)
  cls.pf=c.side(cls.r['sourcePreflight']);cls.h=c.n.helpers(cls.plan,cls.bundle)
  cls.saved=c.side(cls.r['savedActorWitness'])

 def test_01_copied_owner_or_unearned_acceptance_rejected(self):
  for key,value in(('owner','scripts/unreal/exterior-garden-yard-integration-native-r37.py'),
                    ('schemaVersion',1),('fullPhotorealismAccepted',True),('nativeProcessId',54957)):
   bad=copy.deepcopy(self.r);bad[key]=value
   with self.assertRaises(RuntimeError):c.header(bad,self.plan,self.pf,self.bundle)

 def test_02_unrelated_saved_actor_change_rejected(self):
  bad=copy.deepcopy(self.saved)
  actor=next(p for p in bad if p not in self.bundle['donors']['inventory']['changedOriginalActorTargets']
             and p not in self.r['newActorMapping'].values())
  bad[actor]['hidden']=not bad[actor]['hidden'];side=c.side
  with patch.object(c,'side',side_effect=lambda row:bad if row==self.r['savedActorWitness']else side(row)):
   with self.assertRaises(RuntimeError):c.counterfactual(self.r,self.bundle)

 def test_03_missing_graph_diagnostic_rejected(self):
  bad=copy.deepcopy(self.r);bad['materialGraphDiagnosticFiles']['saved'].pop()
  with self.assertRaises(RuntimeError):c.graph_diagnostics(bad,self.bundle)

 def test_04_neighbor_reader_or_full_graph_field_downgrade_rejected(self):
  pin=next(p for p in self.r['materialGraphDiagnosticFiles']['before']if c.side(p)['reader']=='neighbor')
  original=c.side(pin);side=c.side
  for change in ('reader','roots'):
   bad=copy.deepcopy(original)
   if change=='reader':bad['reader']='basic'
   else:bad['actualCompleteGraph']['roots'].pop('REFRACTION')
   with patch.object(c,'side',side_effect=lambda row,bad=bad:bad if row==pin else side(row)):
    with self.assertRaises(RuntimeError):c.graph_diagnostics(self.r,self.bundle)

 def test_05_raw_matrix_signed_zero_change_rejected(self):
  rows=c.side(self.r['newGroupNativeControlsSaved']);bad=copy.deepcopy(rows)
  actor=next(iter(bad));matrix=bad[actor]['storedMatrices'][0]
  location=next((i,j)for i,row in enumerate(matrix)for j,v in enumerate(row)if v==0.)
  i,j=location;matrix[i][j]=-0. if struct.pack('<d',matrix[i][j])==struct.pack('<d',0.)else 0.
  side=c.side
  with patch.object(c,'side',side_effect=lambda row:bad if row==self.r['newGroupNativeControlsSaved']else side(row)):
   with self.assertRaises(RuntimeError):c.new_and_retained(self.r,self.bundle,self.packet,self.h,self.saved)

 def test_06_undeclared_retirement_index_rejected(self):
  bad=copy.deepcopy(self.r);bad['actualRemoveReadback'][0]['removedOriginalSourceIndices'].append(0)
  with self.assertRaises(RuntimeError):c.new_and_retained(bad,self.bundle,self.packet,self.h,self.saved)

 def test_07_corner_hash_mutation_rejected_without_native_decode(self):
  bad=copy.deepcopy(self.r);key=next(iter(bad['geometryReadback']['ground']))
  bad['geometryReadback']['ground'][key]['nativeOrderedF32PositionUv0Uv1CornerSha256']='0'*64
  with self.assertRaises(RuntimeError):c.geometry(bad,self.bundle,self.packet,self.h)

 def test_08_native_recorded_footprint_radius_or_height_mutation_rejected(self):
  for key in ('actualAllNativeLodRadiusCm','actualAbovePivotHeightCm'):
   bad=copy.deepcopy(self.r);bad['geometryReadback']['newLowRootFootprints'][0][key]+=1e-9
   with self.assertRaises(RuntimeError):c.geometry(bad,self.bundle,self.packet,self.h)

 def test_09_original_grass_signed_zero_mutation_rejected(self):
  old=c.side(self.r['protectedControlsBefore']);bad=copy.deepcopy(old)
  grass=next(iter(bad['original8949Grass'].values()))
  self.assertEqual(grass['numCustomDataFloats'],0)
  # Numeric dict equality accepts int0 == float-0.0. Canonical proof rejects
  # this type/sign drift; raw matrix values already have binary64 SHA witnesses.
  grass['numCustomDataFloats']=-0.
  side=c.side
  with patch.object(c,'side',side_effect=lambda row:bad if row in (self.r['protectedControlsBefore'],self.r['protectedControlsSaved'])else side(row)):
   with self.assertRaises(RuntimeError):c.protected(self.r,self.bundle,self.bundle['before'],self.saved)


if __name__=='__main__':unittest.main(verbosity=2)
