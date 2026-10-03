#!/usr/bin/env python3
"""Isolated safety tests; never access the real Dom QA sandbox."""
import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("cleanup_qa_png", Path(__file__).with_name("cleanup-qa-png.py"))
QA = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QA)


class QaPngSafety(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name).resolve()
        self.project, self.qa = root / "project", root / "qa"
        self.project.mkdir(); self.qa.mkdir()
        self.audit = self.project / "audit"; self.audit.mkdir()
        self.patch = patch.multiple(QA, PROJECT=self.project, QA_ROOT=self.qa, AUDIT_ROOT=self.audit)
        self.patch.start()
        self.addCleanup(self.patch.stop); self.addCleanup(self.temporary.cleanup)
        self.target = self.qa / "session" / "capture.png"
        self.target.parent.mkdir(); self.target.write_bytes(b"exact-original-png")
        self.mirror = self.project / "durable.png"; self.mirror.write_bytes(self.target.read_bytes())
        self.receipt = self.audit / "reader-proof.json"; self.receipt.write_text('{"review":"retired"}')
        self.log = self.target.parent / "runtime.json"; self.log.write_text('{"retain":"receipt"}')
        self.row = QA.metadata(self.target)
        self.row.update(category="durable-mirror", mirrorPath=str(self.mirror), reason="SHA-exact durable repository copy")
        self.proposal = {"schemaVersion":1, "status":"qa-exact-png-retirement-proposed-no-deletion",
                         "qaRoot":str(self.qa), "qaRootResolved":str(self.qa),
                         "qaRootUid":os.getuid(), "qaRootInode":self.qa.stat().st_ino,
                         "deletedFiles":0, "files":[self.row],
                         "retainedFiles":{str(self.mirror):{"sha256":QA.sha(self.mirror),"bytes":self.mirror.stat().st_size}},
                         "inputReports":[{"path":str(self.receipt),"sha256":QA.sha(self.receipt)}]}

    def test_exact_mirror_plan_is_read_only(self):
        self.assertEqual(QA.plan(self.proposal,set()),[self.row])
        self.assertTrue(self.target.exists())

    def test_protected_target_refused(self):
        with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,{str(self.target)})

    def test_root_inode_binding_refuses_replacement(self):
        self.proposal["qaRootInode"]+=1
        with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,set())

    def test_non_png_refused(self):
        other=self.target.with_suffix(".json"); other.write_bytes(self.target.read_bytes())
        self.proposal["files"][0]={**QA.metadata(other),"category":"durable-mirror","mirrorPath":str(self.mirror),"reason":"no"}
        with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,set())

    def test_external_target_refused(self):
        self.proposal["files"][0]={**self.row,"path":str(self.mirror)}
        with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,set())

    def test_duplicate_target_refused(self):
        self.proposal["files"].append(dict(self.row))
        with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,set())

    def test_changed_same_size_png_refused(self):
        before=self.target.stat(); self.target.write_bytes(b"x"*before.st_size)
        os.utime(self.target,ns=(before.st_atime_ns,before.st_mtime_ns))
        with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,set())

    def test_changed_mirror_refused(self):
        self.mirror.write_bytes(b"different")
        with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,set())

    def test_unprotected_mirror_refused(self):
        self.proposal["retainedFiles"]={str(self.log):{"sha256":QA.sha(self.log),"bytes":self.log.stat().st_size}}
        with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,set())

    def test_changed_proof_refused(self):
        self.receipt.write_text("{}")
        with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,set())

    def test_symlink_target_refused(self):
        self.target.unlink();self.target.symlink_to(self.mirror)
        with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,set())

    def test_symlink_parent_refused(self):
        other=self.qa/"aliased";other.symlink_to(self.target.parent,target_is_directory=True)
        self.proposal["files"][0]={**self.row,"path":str(other/"capture.png")}
        with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,set())

    def test_owner_refused(self):
        with patch.object(QA.os,"getuid",return_value=os.getuid()+1):
            with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,set())

    def test_study_requires_reader_and_retirement_proof(self):
        self.row.update(category="retired-study-frame",retainedFramePaths=[str(self.mirror)])
        with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,set())
        self.add_study_proofs()
        self.assertEqual(QA.plan(self.proposal,set()),[self.row])

    def add_study_proofs(self):
        reader=self.audit/"reader.json";retirement=self.audit/"retirement.json"
        reader.write_text(json.dumps({"status":"active-authored-reader-audit-complete-no-deletion",
                                      "qaRoot":str(self.qa),"historicalFrameTargets":[str(self.target)]}))
        retirement.write_text(json.dumps({"status":"exact-historical-generated-png-retirement-proposed-no-deletion",
                                          "qaRoot":str(self.qa),"targets":[dict(self.row)]}))
        self.proposal["inputReports"].extend({"path":str(p),"sha256":QA.sha(p)} for p in [reader,retirement])
        self.row.update(readerAuditProofPath=str(reader),retirementProofPath=str(retirement))

    def test_study_arbitrary_pinned_json_refused(self):
        self.row.update(category="retired-study-frame",retainedFramePaths=[str(self.mirror)],
                        readerAuditProofPath=str(self.receipt),retirementProofPath=str(self.receipt))
        with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,set())

    def test_study_exact_audit_target_membership_required(self):
        self.row.update(category="retired-study-frame",retainedFramePaths=[str(self.mirror)])
        self.add_study_proofs()
        reader=Path(self.row["readerAuditProofPath"])
        r=json.loads(reader.read_text());r["historicalFrameTargets"]=[];reader.write_text(json.dumps(r))
        for entry in self.proposal["inputReports"]:
            if entry["path"]==str(reader):entry["sha256"]=QA.sha(reader)
        with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,set())

    def test_selected_study_originals_required(self):
        self.row.update(category="retired-study-frame",readerAuditProofPath=str(self.receipt),
                        retirementProofPath=str(self.receipt),retainedFramePaths=[])
        with self.assertRaises(QA.Unsafe):QA.plan(self.proposal,set())

    def test_remaining_receipt_preserved_and_only_png_unlinked(self):
        preserved=QA.preserved_inventory({str(self.target)})
        QA.unlink_exact(self.row)
        self.assertFalse(self.target.exists());self.assertTrue(self.target.parent.is_dir())
        self.assertEqual(QA.preserved_inventory({str(self.target)}),preserved)
        self.assertTrue(self.log.exists());self.assertTrue(self.mirror.exists())

    def test_freshness_rechecked_immediately_before_unlink(self):
        self.target.write_bytes(b"changed")
        with self.assertRaises(QA.Unsafe):QA.unlink_exact(self.row)
        self.assertTrue(self.target.exists())

    def test_report_cannot_escape_or_overwrite(self):
        with self.assertRaises(QA.Unsafe):QA.save_new(self.project/"outside.json",{})
        QA.save_new(self.audit/"fresh.json",{})
        with self.assertRaises(QA.Unsafe):QA.save_new(self.audit/"fresh.json",{})

    def run_cli(self, execute=False, activity=None):
        helper=self.project/"helper.py";helper.write_text("# isolated guard fixture")
        tests=self.project/"tests.py";tests.write_text("# isolated tests fixture")
        proposal_path=self.audit/"proposal.json";proposal_path.write_text(json.dumps(self.proposal))
        protected=self.audit/"protected.json"
        protected.write_text(json.dumps({"files":{str(Path(QA.__file__).resolve()):{"sha256":QA.sha(Path(QA.__file__))},
                            str(helper):{"sha256":QA.sha(helper)},str(tests):{"sha256":QA.sha(tests)}}}))
        final=self.audit/"final.json";final.write_text('{"files":{}}')
        report=self.audit/"result.json"
        argv=["cleanup-qa-png.py","--report",str(report)]
        for label,path in [("proposal",proposal_path),("protected-inventory",protected),("final-inventory",final)]:
            argv.extend(["--"+label,str(path),"--"+label+"-sha256",QA.sha(path)])
        if execute:argv.append("--execute")
        guard=SimpleNamespace(Unsafe=QA.Unsafe,verify_retention=lambda *args:None,verify_protection=lambda *args:[],
                              activity=activity or (lambda *args:{"openHandles":[],"processes":[]}),
                              space=lambda:{"availableBytes":1000})
        spec=SimpleNamespace(loader=SimpleNamespace(exec_module=lambda *args:None))
        with patch.multiple(QA,HELPER_PATH=helper,TEST_PATH=tests),patch.object(QA.sys,"argv",argv),\
             patch.object(QA.importlib.util,"spec_from_file_location",return_value=spec),\
             patch.object(QA.importlib.util,"module_from_spec",return_value=guard),contextlib.redirect_stdout(io.StringIO()):
            result=QA.main()
        return result,json.loads(report.read_text())

    def test_cli_defaults_dry_run_and_records_preservation(self):
        code,report=self.run_cli()
        self.assertEqual(code,0);self.assertTrue(self.target.exists())
        self.assertEqual(report["removedFiles"],0);self.assertEqual(report["preservedNonPngCount"],1)
        self.assertTrue(report["protectedHashesUnchanged"])

    def test_cli_active_handle_refuses_before_first_unlink(self):
        code,report=self.run_cli(True,lambda *args:{"openHandles":[str(self.target)],"processes":[]})
        self.assertEqual(code,1);self.assertTrue(self.target.exists())
        self.assertEqual(report["removedFiles"],0);self.assertEqual(report["status"],"failed-closed")

    def test_cli_new_process_refuses_at_batch_guard(self):
        calls=[]
        def activity(*args):
            calls.append(1)
            return {"openHandles":[],"processes":["Dom"] if len(calls)>1 else []}
        code,report=self.run_cli(True,activity)
        self.assertEqual(code,1);self.assertTrue(self.target.exists());self.assertEqual(report["removedFiles"],0)

    def test_cli_partial_completion_report_preserves_receipt(self):
        for number in range(1,26):
            path=self.target.parent/("capture-"+str(number)+".png");path.write_bytes(self.target.read_bytes())
            self.proposal["files"].append({**QA.metadata(path),"category":"durable-mirror",
                                          "mirrorPath":str(self.mirror),"reason":"Exact mirror"})
        calls=[]
        def activity(*args):
            calls.append(1)
            return {"openHandles":[],"processes":["Dom"] if len(calls)>2 else []}
        code,report=self.run_cli(True,activity)
        self.assertEqual(code,1);self.assertEqual(report["removedFiles"],25)
        self.assertTrue(report["preservedQAFilesUnchanged"]);self.assertTrue(self.log.exists())
        self.assertTrue(self.target.parent.is_dir())


if __name__=="__main__":unittest.main()
