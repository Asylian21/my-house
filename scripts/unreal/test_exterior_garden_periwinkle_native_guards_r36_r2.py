"""Twelve immutable source/control fixtures plus R2 provenance mutations.

The geometry/matrix fixtures are inherited byte-exact from the frozen R1
fixture module. The combined writer suite supplies one already-validated real
R34 packet; these additions never claim an actual R36 import or measurement.
"""
import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load(name, filename):
 spec = importlib.util.spec_from_file_location(name, ROOT/'scripts/unreal'/filename)
 value = importlib.util.module_from_spec(spec)
 spec.loader.exec_module(value)
 return value


g = load('r36_r2_actual_guard', 'exterior-garden-periwinkle-native-guards-r36-r2.py')
history = load('r36_r2_immutable_source_fixtures', 'test_exterior_garden_periwinkle_native_guards_r36.py')
fixtures = history.fixtures


class Guards(history.Guards):
 @classmethod
 def setUpClass(cls):
  cls.b = g.validate_source()
  cls.m = fixtures(cls.b)

 def test_01_actual_r34_scope_and_clone(self):
  super().test_01_actual_r34_scope_and_clone()
  clone_path = g.CANDIDATE/'garden-periwinkle-project-clone.json'
  clone = g.read(clone_path)
  self.assertEqual(g.validate_clone(self.b['base'])['sha256'], g.CLONE_SHA)
  self.assertEqual(g.CANDIDATE.name, 'exterior-20261002-r36b')
  self.assertEqual(g.original.CANDIDATE.name, 'exterior-20261002-r36a')
  for key, value in (('schemaVersion', 2), ('nativePreflightPending', False),
                     ('project', str(g.original.CANDIDATE/'Project/BreziTwin')),
                     ('sourceProposal', g.pin(g.PROPOSAL)), ('nativeExecuted', True)):
   altered = copy.deepcopy(clone)
   altered[key] = value
   with self.assertRaises(RuntimeError):
    g.validate_clone_header(altered, self.b['base'], g.CANDIDATE/'Project/BreziTwin')
  report = g.read(g.FAILED_REPORT)
  terminal = g.read(g.FAILED/'garden-periwinkle-native-r1-process.json')
  raw = g.read(g.FAILED/'garden-periwinkle-native-r1.log.json')
  audit = g.read(g.FAILURE_AUDIT)
  g.validate_failure_header(report, terminal, raw, audit)
  for target, key, value in ((report, 'nativeApplied', True), (report, 'status', 'running'),
                            (raw, 'code', 0), (terminal, 'sourcePinsUnchangedAfterNative', False),
                            (audit, 'originalMapByteExact', False),
                            (audit, 'newNativeActorOrGeometryDecodeByThisCpuAudit', True)):
   rows = [copy.deepcopy(row) for row in (report, terminal, raw, audit)]
   rows[(report, terminal, raw, audit).index(target)][key] = value
   with self.assertRaises(RuntimeError):g.validate_failure_header(*rows)

 def test_02_original_all_attributes_and_mesh_names(self):
  super().test_02_original_all_attributes_and_mesh_names()
  models = self.b['source']['models']
  bindings = g.source_triangle_count_bindings(models)
  self.assertEqual(len(bindings), 6)
  self.assertEqual(sum(bindings), 34350)
  wrong = copy.deepcopy(models)
  wrong[g.MODELS[0]]['triangles'] = wrong[g.MODELS[1]]['triangles']
  with self.assertRaises(RuntimeError):g.source_triangle_count_bindings(wrong)
  evidence = g.import_identity_evidence()
  self.assertFalse(evidence['persistedPartialMeshDiagnosticAvailable'])
  self.assertFalse(evidence['sixMeshIdentityVerifiedByThisSourceReceipt'])
  self.assertFalse(evidence['nativeOriginalNodeLabelIdentityObserved'])
  self.assertIs(g.expected_original, g.original.expected_original)
  self.assertIs(g.validate_measurements, g.original.validate_measurements)
  self.assertIs(g.source_footprints, g.original.source_footprints)
  p = g.read(g.original.PLAN)
  p.update(schemaVersion=2, owner='scripts/unreal/exterior-garden-periwinkle-native-study-r36-r2.py',
   nativeOwner='scripts/unreal/exterior-garden-periwinkle-native-r36-r2.py',
   status='source-ready-exact-saved-r34-whole384-original-periwinkle-native-r2-pending',
   candidateOutput=str(g.CANDIDATE), projectClone=g.pin(g.CANDIDATE/'garden-periwinkle-project-clone.json'),
   immutableSourceGuard=g.pin(g.ORIGINAL_GUARD), repairSchema=g.REPAIR_SCHEMA, importIdentityEvidence=evidence)
  clone_pin = p['projectClone']
  g.validate_plan_header(p, self.b, clone_pin, evidence)
  for key, value in (('schemaVersion', 1), ('nativeOwner', 'scripts/unreal/exterior-garden-periwinkle-native-r36.py'),
                     ('candidateOutput', str(g.original.CANDIDATE)),
                     ('repairSchema', 'unknown-repair'), ('importIdentityEvidence', {})):
   wrong = copy.deepcopy(p)
   wrong[key] = value
   with self.assertRaises(RuntimeError):g.validate_plan_header(wrong, self.b, clone_pin, evidence)


if __name__ == '__main__':unittest.main(verbosity=2)
