"""Bounded CPU controls for command/receipt policy; no native process launch."""
from pathlib import Path
import tempfile,unittest
from unittest.mock import patch
import native_process as H
import phase_runner as F
import accept_build as A

class Tests(unittest.TestCase):
 def test_nested_xcode_failure_beats_uat_success(self):
  self.assertTrue(F.log_findings('** BUILD FAILED **\nBUILD SUCCESSFUL\nAutomationTool exiting with ExitCode=0'))
  self.assertTrue(F.log_findings('The following build commands failed:\nBUILD SUCCESSFUL'))
  self.assertFalse(F.log_findings('Missing cached shader map for material M, compiling.\nSuccess - 0 error(s)\nBUILD SUCCESSFUL'))
 def test_monolithic_local_definition_is_required(self):
  words=['RegisterFloorCausticsProvider_RenderThread','UnregisterFloorCausticsProvider_RenderThread','CreateBreziFloorCausticsDiagnostic','CreateBreziCausticsTransport']
  text='\n'.join('0000000000 t _'+w for w in words);self.assertEqual(len(A.defined_provider_symbols(text)),4)
  with self.assertRaises(RuntimeError):A.defined_provider_symbols(text.replace(' t ',' U '))
  with self.assertRaises(RuntimeError):A.defined_provider_symbols('\n'.join(text.splitlines()[:-1]))
 def test_candidate_marker_and_project_containment(self):
  with tempfile.TemporaryDirectory() as d:
   E=Path(d).resolve();P=E/'project';P.mkdir();(P/'BreziTwin.uproject').write_text('{}');R=E/'.brezi-managed/runs'
   with self.assertRaises(RuntimeError):F.paths(E,P,R)
   (E/'.brezi-isolated-engine').write_text(str(E));self.assertEqual(F.paths(E,P,R),(E,P,R))
   with self.assertRaises(RuntimeError):F.paths(E,P,E/'not-managed')
   (E/'.brezi-isolated-engine').write_text('/other')
   with self.assertRaises(RuntimeError):F.paths(E,P,R)
 def test_ownership_phase_policy(self):
  self.assertFalse(H.process_issues('game-build','clang++','clang++ -c a.cpp')[0])
  self.assertTrue(H.process_issues('game-graph','clang++','clang++ -c a.cpp')[0])
  self.assertFalse(H.process_issues('game-graph','clang++','clang++ --version')[0])
  self.assertTrue(H.process_issues('archive','ShaderCompileWorker','worker')[0])
  self.assertFalse(H.process_issues('archive','xcodebuild','xcodebuild build')[0])
  self.assertTrue(H.process_issues('cook','BreziTwin','app')[0])
  self.assertFalse(H.process_issues('cook','metal','metal shader.metal')[0])
 def test_archive_flag_is_single_quoted_value(self):
  with tempfile.TemporaryDirectory(prefix='space in ') as d:
   E=Path(d).resolve();P=E/'project';R=E/'.brezi-managed/runs';cook=R/'cook/receipt.json';cook.parent.mkdir(parents=True);cook.write_text('{}')
   fake={'cookOutput':str(cook.parent/'cooked')}
   with patch.object(F,'paths',return_value=(E,P,R)),patch.object(F,'read',return_value=fake),patch.object(F,'input_pins',return_value={}):
    cfg=F.plan(E,P,R,'archive','test',{}, {'source':'x'}, {'editor':'x'}, {'game':'x'},cook)
   value=[x for x in cfg['argv'] if x.startswith('-xcodebuildoptions=')]
   self.assertEqual(len(value),1);self.assertIn('-derivedDataPath "',value[0]);self.assertTrue(value[0].endswith('"'))
   self.assertNotIn('/usr/bin/sandbox-exec',cfg['argv']);self.assertIn('-skipbuild',cfg['argv']);self.assertIn('-skipcook',cfg['argv'])
 def test_graph_plan_and_edit_detection(self):
  with tempfile.TemporaryDirectory() as d:
   E=Path(d).resolve();P=E/'project';R=E/'.brezi-managed/runs'
   with patch.object(F,'paths',return_value=(E,P,R)),patch.object(F,'input_pins',return_value={}):
    cfg=F.plan(E,P,R,'editor-graph','test',{'tools':'x'},{'source':'x'})
    self.assertIn('-MaxParallelActions=4',cfg['argv']);self.assertTrue(any(x.startswith('-WriteOutdatedActions=') for x in cfg['argv']))
    self.assertFalse(any('xcodebuildoptions' in x for x in cfg['argv']))
    self.assertEqual(F.execute(cfg,True)['status'],'preflight-only-not-executed')
    cfg['argv'].append('-Unreviewed')
    with self.assertRaisesRegex(RuntimeError,'Plan command/configuration drift'):F.execute(cfg,True)
 def test_generated_app_is_not_source_input(self):
  with tempfile.TemporaryDirectory() as d:
   P=Path(d).resolve();(P/'Plugins').mkdir();(P/'BreziTwin.uproject').write_text('{}')
   q=P/'Binaries/Mac/BreziTwin.app/Contents/Info.plist';q.parent.mkdir(parents=True);q.write_text('first')
   before=F.project_pins(P);q.write_text('stage changed app');self.assertEqual(before,F.project_pins(P))
   source=P/'Source/C.cpp';source.parent.mkdir();source.write_text('current');self.assertNotEqual(before,F.project_pins(P))
 def test_external_xcode_baseline_is_not_candidate(self):
  from types import SimpleNamespace
  rows=[{'pid':321,'state':'S','executable':'/Applications/Xcode.app/xcodebuild'}]
  cfg={'engineRoot':'/candidate/UE','projectRoot':'/candidate/UE/project'}
  with patch.object(H,'command',return_value='xcodebuild -project /unrelated/App.xcodeproj test'),patch.object(H.subprocess,'run',return_value=SimpleNamespace(stdout='n/unrelated\n')):
   H.reject_conflicts(rows,cfg)
  with patch.object(H,'command',return_value='xcodebuild -project /candidate/UE/project/App.xcodeproj'):
   with self.assertRaisesRegex(RuntimeError,'candidate build'):H.reject_conflicts(rows,cfg)
  with patch.object(H,'command',return_value=''),patch.object(H.subprocess,'run',return_value=SimpleNamespace(stdout='')):
   with self.assertRaisesRegex(RuntimeError,'Cannot classify'):H.reject_conflicts(rows,cfg)
 def test_rejects_changed_source_and_linked_input(self):
  with tempfile.TemporaryDirectory() as d:
   root=Path(d).resolve();q=root/'input';q.write_text('a');pins={str(q):H.sha(q)};F.check(pins);q.write_text('b')
   with self.assertRaises(RuntimeError):F.check(pins)
   link=root/'alias';link.symlink_to(q)
   with self.assertRaises(RuntimeError):F.path(link)
if __name__=='__main__':unittest.main()
