#!/usr/bin/env python3
"""Repository PNG safety tests run entirely in isolated temporary directories."""
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SPEC=importlib.util.spec_from_file_location('repository_png_cleanup',Path(__file__).with_name('cleanup-repository-png.py'))
REPO=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(REPO)


class RepositoryPngSafety(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.project=Path(self.temp.name).resolve()/"project";self.root=self.project/"output/unreal"
        self.audit=self.root/"audit";self.audit.mkdir(parents=True)
        self.patcher=patch.multiple(REPO,PROJECT=self.project,REPOSITORY_ROOT=self.root,AUDIT_ROOT=self.audit)
        self.patcher.start();self.addCleanup(self.patcher.stop)
        self.target=self.root/"old-study/qa/capture.png";self.target.parent.mkdir(parents=True);self.target.write_bytes(b"rendered-native-png")
        self.keeper=self.root/"approved.png";self.keeper.write_bytes(b"approved-other-png")
        self.receipt=self.target.parent/"qa.json";self.receipt.write_text('{"originalReceipt":true}')
        self.row={**REPO.metadata(self.target),"reason":"Unreferenced retired historical native study"}
        self.raw="/dedicated-old-qa/Saved/Diagnostics/scene.png"
        self.reader=self.audit/"reader.json";self.retirement=self.audit/"retirement.json"
        self.reader.write_text(json.dumps({"status":"repository-png-indirect-reader-retirement-verified-no-deletion",
            "historicalPngTargets":[str(self.target)],"allCandidatesHistoricalEvidenceOnly":True,
            "currentProjectDependencyIntersections":[],"currentRuntimeDependencyIntersections":[],"currentRebuildDependencyIntersections":[]}))
        self.retirement.write_text(json.dumps({"status":"exact-repository-historical-png-retirement-proposed-no-deletion","targets":[self.row]}))
        self.oldproposal=self.audit/"old-qa-proposal.json"
        self.oldproposal.write_text(json.dumps({"files":[{"path":self.raw,"mirrorPath":str(self.target),"sha256":self.row["sha256"],"bytes":self.row["bytes"],"category":"durable-mirror"}]}))
        self.oldexecution=self.audit/"old-qa-execution.json"
        self.oldexecution.write_text(json.dumps({"status":"exact-qa-pngs-retired-protection-verified","failureCount":0,
            "proposalSha256":REPO.sha(self.oldproposal),"durableOriginalHashesUnchanged":True,
            "results":[{"path":self.raw,"sha256":self.row["sha256"]}]}))
        self.proposal={"schemaVersion":1,"status":"repository-exact-study-png-retirement-proposed-no-deletion",
            "repositoryRoot":str(self.root),"deletedFiles":0,"files":[self.row],
            "inputReports":[{"path":str(p),"sha256":REPO.sha(p)} for p in [self.reader,self.retirement]],
            "readerAuditProofPath":str(self.reader),"retirementProofPath":str(self.retirement),
            "priorQaProposalPath":str(self.oldproposal),"priorQaProposalSha256":REPO.sha(self.oldproposal),
            "priorQaExecutionPath":str(self.oldexecution),"priorQaExecutionSha256":REPO.sha(self.oldexecution),
            "retainedFiles":{str(self.keeper):{"sha256":REPO.sha(self.keeper),"bytes":self.keeper.stat().st_size}}}
        self.prior={str(self.target):{"sha256":self.row["sha256"],"bytes":self.row["bytes"]}}

    def plan(self,protected=(),initial=(),original=()):
        return REPO.plan(self.proposal,set(protected),set(initial),set(original),self.prior)

    def test_exact_closed_historical_proof_dry_plan(self):
        self.assertEqual(self.plan(),[self.row]);self.assertTrue(self.target.exists())

    def test_current_initial_original_pins_all_refused(self):
        for role in ["protected","initial","original"]:
            with self.subTest(role=role),self.assertRaises(REPO.Unsafe):self.plan(**{role:[str(self.target)]})

    def test_non_png_refused(self):
        other=self.target.with_suffix(".json");other.write_bytes(self.target.read_bytes())
        self.proposal["files"]=[{**self.row,**REPO.metadata(other)}]
        with self.assertRaises(REPO.Unsafe):self.plan()

    def test_outside_repository_refused(self):
        self.row["path"]=str(self.project/"source.png")
        with self.assertRaises(REPO.Unsafe):self.plan()

    def test_duplicate_refused(self):
        self.proposal["files"].append(dict(self.row))
        with self.assertRaises(REPO.Unsafe):self.plan()

    def test_same_size_content_mutation_refused(self):
        info=self.target.stat();self.target.write_bytes(b"x"*info.st_size);os.utime(self.target,ns=(info.st_atime_ns,info.st_mtime_ns))
        with self.assertRaises(REPO.Unsafe):self.plan()

    def test_symlink_refused(self):
        self.target.unlink();self.target.symlink_to(self.keeper)
        with self.assertRaises(REPO.Unsafe):self.plan()

    def test_foreign_owner_refused(self):
        with patch.object(REPO.QA.os,"getuid",return_value=os.getuid()+1):
            with self.assertRaises(REPO.Unsafe):self.plan()

    def test_current_indirect_reader_refused(self):
        r=json.loads(self.reader.read_text());r["currentRuntimeDependencyIntersections"]=[str(self.target)]
        self.reader.write_text(json.dumps(r));self.proposal["inputReports"][0]["sha256"]=REPO.sha(self.reader)
        with self.assertRaises(REPO.Unsafe):self.plan()

    def test_unverified_previous_qa_pass_refused(self):
        r=json.loads(self.oldexecution.read_text());r["failureCount"]=1;self.oldexecution.write_text(json.dumps(r))
        self.proposal["priorQaExecutionSha256"]=REPO.sha(self.oldexecution)
        with self.assertRaises(REPO.Unsafe):self.plan()

    def test_unlisted_native_mirror_refused(self):
        self.oldproposal.write_text('{"files":[]}');self.proposal["priorQaProposalSha256"]=REPO.sha(self.oldproposal)
        r=json.loads(self.oldexecution.read_text());r["proposalSha256"]=self.proposal["priorQaProposalSha256"]
        self.oldexecution.write_text(json.dumps(r));self.proposal["priorQaExecutionSha256"]=REPO.sha(self.oldexecution)
        with self.assertRaises(REPO.Unsafe):self.plan()

    def test_retirement_membership_hash_required(self):
        r=json.loads(self.retirement.read_text());r["targets"][0]["sha256"]="0"*64
        self.retirement.write_text(json.dumps(r));self.proposal["inputReports"][1]["sha256"]=REPO.sha(self.retirement)
        with self.assertRaises(REPO.Unsafe):self.plan()

    def test_exact_previous_qa_keeper_allowed_retained_only(self):
        qa=self.project.parent/"dedicatedqa";qa.mkdir();keeper=qa/"raw.png";keeper.write_bytes(b"unique-raw-png")
        record={"sha256":REPO.sha(keeper),"bytes":keeper.stat().st_size}
        self.proposal["retainedFiles"][str(keeper)]=record
        old=json.loads(self.oldproposal.read_text());old["retainedFiles"]={str(keeper):record}
        self.oldproposal.write_text(json.dumps(old));self.proposal["priorQaProposalSha256"]=REPO.sha(self.oldproposal)
        prior=json.loads(self.oldexecution.read_text());prior["proposalSha256"]=REPO.sha(self.oldproposal)
        self.oldexecution.write_text(json.dumps(prior));self.proposal["priorQaExecutionSha256"]=REPO.sha(self.oldexecution)
        with patch.object(REPO.QA,"QA_ROOT",qa):self.assertEqual(self.plan(),[self.row])

    def test_foreign_external_retained_file_refused(self):
        other=self.project.parent/"foreign.png";other.write_bytes(b"foreign")
        self.proposal["retainedFiles"][str(other)]={"sha256":REPO.sha(other),"bytes":other.stat().st_size}
        with self.assertRaises(REPO.Unsafe):self.plan()

    def test_external_qa_keeper_requires_previous_exact_pin(self):
        qa=self.project.parent/"dedicatedqa";qa.mkdir();keeper=qa/"unlisted.png";keeper.write_bytes(b"unlisted")
        self.proposal["retainedFiles"][str(keeper)]={"sha256":REPO.sha(keeper),"bytes":keeper.stat().st_size}
        with patch.object(REPO.QA,"QA_ROOT",qa):
            with self.assertRaises(REPO.Unsafe):self.plan()

    def test_qa_root_png_deletion_refused(self):
        qa=self.project.parent/"dedicatedqa";qa.mkdir();raw=qa/"raw.png";raw.write_bytes(b"authored-raw")
        with patch.object(REPO.QA,"QA_ROOT",qa):
            with self.assertRaises(REPO.Unsafe):REPO.unlink_exact(REPO.metadata(raw))
        self.assertTrue(raw.exists())

    def test_only_png_unlinked_sibling_child_and_directory_retained(self):
        child=self.target.parent/"details";child.mkdir();(child/"log.json").write_text('{}')
        before=REPO.siblings_inventory([self.row]);REPO.unlink_exact(self.row)
        self.assertFalse(self.target.exists());self.assertTrue(self.receipt.exists());self.assertTrue(child.exists())
        self.assertEqual(REPO.siblings_inventory([self.row]),before)

    def test_immediate_unlink_freshness_guard(self):
        self.target.write_bytes(b"changed")
        with self.assertRaises(REPO.Unsafe):REPO.unlink_exact(self.row)
        self.assertTrue(self.target.exists())

    def run_cli(self,execute=False,activity=None,tracked=()):
        main=self.project/"guard.py";qa=self.project/"qa-guard.py";test=self.project/"test.py"
        for p in [main,qa,test]:p.write_text("# temporary isolated fixture")
        proposal=self.audit/"proposal.json";proposal.write_text(json.dumps(self.proposal))
        protection=self.audit/"protection.json"
        protection.write_text(json.dumps({"files":{str(p):{"sha256":REPO.sha(p)} for p in [Path(REPO.__file__).resolve(),main,qa,test]}}))
        final=self.audit/"final.json";final.write_text('{"files":{}}')
        prior=self.audit/"prior.json";prior.write_text(json.dumps({"files":self.prior}))
        initial=self.audit/"initial.json";initial.write_text('{"files":{}}')
        original=self.audit/"original.json";original.write_text('{"files":{}}')
        report=self.audit/"result.json";argv=["cleanup-repository-png.py","--report",str(report)]
        for flag,p in [("proposal",proposal),("protected-inventory",protection),("final-inventory",final),("prior-protected-inventory",prior),("initial-protected-inventory",initial),("original-inventory",original)]:
            argv.extend(["--"+flag,str(p),"--"+flag+"-sha256",REPO.sha(p)])
        if execute:argv.append("--execute")
        guard=SimpleNamespace(Unsafe=REPO.Unsafe,verify_retention=lambda *args:None,verify_protection=lambda *args:[],
            activity=activity or (lambda *args:{"openHandles":[],"processes":[]}),space=lambda:{"availableBytes":1000},
            tracked_files=lambda:set(tracked))
        with patch.multiple(REPO,MAIN_HELPER=main,QA_HELPER=qa,TEST_SOURCE=test),patch.object(REPO.sys,"argv",argv),\
             patch.object(REPO,"load_module",return_value=guard),contextlib.redirect_stdout(io.StringIO()):code=REPO.main()
        return code,json.loads(report.read_text())

    def test_cli_defaults_to_dry_run(self):
        code,r=self.run_cli();self.assertEqual(code,0);self.assertEqual(r["removedFiles"],0);self.assertTrue(self.target.exists())

    def test_cli_tracked_image_refused(self):
        code,r=self.run_cli(True,tracked=[self.target]);self.assertEqual(code,1);self.assertEqual(r["removedFiles"],0)

    def test_cli_active_handle_refused(self):
        code,r=self.run_cli(True,lambda *args:{"openHandles":[str(self.target)],"processes":[]})
        self.assertEqual(code,1);self.assertEqual(r["removedFiles"],0);self.assertTrue(self.target.exists())

    def test_cli_late_process_refused(self):
        calls=[]
        def activity(*args):
            calls.append(1);return {"openHandles":[],"processes":["Dom"] if len(calls)>1 else []}
        code,r=self.run_cli(True,activity);self.assertEqual(code,1);self.assertEqual(r["removedFiles"],0)

    def test_fresh_report_boundary_refuses_escape(self):
        with self.assertRaises(REPO.Unsafe):REPO.validate_report(self.project/"outside.json")


if __name__=="__main__":unittest.main()
