#!/usr/bin/env python3
"""Retire exact, proven historical repository PNGs; dry-run by default.

The earlier QA mirror-retirement proof stays immutable. Only separately
reviewed PNG files are unlinked; directories and every sibling file remain.
"""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PROJECT / "output/unreal"
AUDIT_ROOT = REPOSITORY_ROOT / "performance-20261003-r1/storage-audit"
MAIN_HELPER = PROJECT / "scripts/unreal/cleanup-generated.py"
QA_HELPER = PROJECT / "scripts/unreal/cleanup-qa-png.py"
TEST_SOURCE = PROJECT / "scripts/unreal/test_cleanup_repository_png.py"


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


QA = load_module("qa_png_primitives", QA_HELPER)
Unsafe, require, sha, metadata, regular = QA.Unsafe, QA.require, QA.sha, QA.metadata, QA.regular


def retained_regular(name):
    path=Path(name)
    return regular(name, QA.QA_ROOT if QA.underneath(path,QA.QA_ROOT) else PROJECT)


def plan(proposal, protected, initial, original, prior):
    require(proposal.get("status") == "repository-exact-study-png-retirement-proposed-no-deletion"
            and proposal.get("schemaVersion") == 1 and proposal.get("deletedFiles", 0) == 0,
            "Wrong repository retirement proposal")
    require(proposal.get("repositoryRoot") == str(REPOSITORY_ROOT) and REPOSITORY_ROOT.resolve() == REPOSITORY_ROOT,
            "Wrong repository boundary")
    inputs = {row["path"]: QA.read_bound(regular(row["path"], PROJECT), row["sha256"])
              for row in proposal["inputReports"]}
    require(proposal["readerAuditProofPath"] in inputs and proposal["retirementProofPath"] in inputs,
            "Missing exact reader/retirement proofs")
    reader, retirement = inputs[proposal["readerAuditProofPath"]], inputs[proposal["retirementProofPath"]]
    require(reader.get("status") == "repository-png-indirect-reader-retirement-verified-no-deletion"
            and reader.get("allCandidatesHistoricalEvidenceOnly") is True
            and reader.get("currentProjectDependencyIntersections") == []
            and reader.get("currentRuntimeDependencyIntersections") == []
            and reader.get("currentRebuildDependencyIntersections") == [], "Unclosed current readers")
    require(retirement.get("status") == "exact-repository-historical-png-retirement-proposed-no-deletion",
            "Unexpected retirement proof")
    old_proposal = QA.read_bound(regular(proposal["priorQaProposalPath"], AUDIT_ROOT), proposal["priorQaProposalSha256"])
    old_execution = QA.read_bound(regular(proposal["priorQaExecutionPath"], AUDIT_ROOT), proposal["priorQaExecutionSha256"])
    require(old_execution.get("status") == "exact-qa-pngs-retired-protection-verified"
            and old_execution.get("failureCount") == 0
            and old_execution.get("proposalSha256") == proposal["priorQaProposalSha256"]
            and old_execution.get("durableOriginalHashesUnchanged") is True,
            "Previous QA mirror retirement was not fully verified")
    mirrors = {row["mirrorPath"]: row for row in old_proposal["files"] if row["category"] == "durable-mirror"}
    completed = {row["path"]: row for row in old_execution["results"]}
    targets = proposal["files"]
    names = [row["path"] for row in targets]
    require(targets and len(names) == len(set(names)), "Empty or duplicate repository targets")
    require(not set(names).intersection(protected) and not set(names).intersection(initial)
            and not set(names).intersection(original), "Repository target is a current/original/source pin")
    require(set(names).issubset(reader.get("historicalPngTargets", [])), "Target absent from exact reader closure")
    retirement_rows = {row["path"]: row for row in retirement.get("targets", [])}
    retained = proposal["retainedFiles"]
    require(retained and not set(names).intersection(retained), "Target intersects retained gallery/current originals")
    for name, expected in retained.items():
        p = retained_regular(name)
        if QA.underneath(p,QA.QA_ROOT):
            old=old_proposal.get("retainedFiles",{}).get(name,{})
            require(old.get("sha256") == expected["sha256"] and old.get("bytes") == expected["bytes"],
                    "External QA keeper was not pinned in the exact previous proposal")
        require(p.stat().st_size == expected["bytes"] and sha(p) == expected["sha256"], "Retained reader/gallery input changed")
    for row in targets:
        p = regular(row["path"], REPOSITORY_ROOT)
        require(p.suffix.lower() == ".png" and row.get("reason"), "Only justified PNG retirement permitted")
        require(metadata(p) == {key: row[key] for key in ("path", "sha256", "bytes", "inode", "mtimeNs", "uid")},
                "Repository PNG metadata/hash changed")
        require(row["path"] in mirrors and row["path"] in prior
                and prior[row["path"]]["sha256"] == row["sha256"], "Not an explicitly earlier-protected QA mirror")
        raw = mirrors[row["path"]]
        require(raw["sha256"] == row["sha256"] and raw["bytes"] == row["bytes"]
                and completed.get(raw["path"], {}).get("sha256") == row["sha256"], "Native duplicate provenance differs")
        require(retirement_rows.get(row["path"], {}).get("sha256") == row["sha256"]
                and retirement_rows[row["path"]].get("bytes") == row["bytes"], "Target absent from hashed retirement proof")
    return targets


def siblings_inventory(rows):
    targets = {row["path"] for row in rows}
    result = {}
    for folder in {Path(row["path"]).parent for row in rows}:
        for base,directories,files in os.walk(folder,followlinks=False):
            require(not any((Path(base)/name).is_symlink() for name in directories), "Symlink in a selected PNG parent")
            for name in files:
                p=regular(str(Path(base)/name),REPOSITORY_ROOT)
                if str(p) not in targets:result[str(p)] = metadata(p)
    return result


def unlink_exact(row):
    p = regular(row["path"], REPOSITORY_ROOT)
    require(metadata(p) == {key: row[key] for key in ("path", "sha256", "bytes", "inode", "mtimeNs", "uid")},
            "Repository PNG changed immediately before unlink")
    regular(str(p), REPOSITORY_ROOT)
    require(metadata(p, False) == {key: row[key] for key in ("path", "bytes", "inode", "mtimeNs", "uid")},
            "Repository PNG changed during final hash")
    p.unlink()


def validate_report(path):
    require(path.is_absolute() and path.resolve() == path and QA.underneath(path, AUDIT_ROOT)
            and path != AUDIT_ROOT and path.parent.is_dir() and not path.exists(), "Report is not fresh in the exact audit directory")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("proposal", "protected-inventory", "final-inventory", "prior-protected-inventory", "initial-protected-inventory", "original-inventory"):
        parser.add_argument("--" + name, type=Path, required=True)
        parser.add_argument("--" + name + "-sha256", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    report = {"schemaVersion":1, "status":"planning", "createdAtEpoch":time.time(), "executeRequested":args.execute,
              "directoriesRemoved":0, "removedFiles":0, "removedLogicalBytes":0, "failureCount":0,
              "originalReportsRewritten":False, "results":[],
              "physicalSpaceCaveat":"APFS shared extents/concurrent activity can differ from logical deletion"}
    guard = None
    preserved = None
    try:
        validate_report(args.report)
        inputs = {}
        for name in ("proposal", "protected_inventory", "final_inventory", "prior_protected_inventory", "initial_protected_inventory", "original_inventory"):
            path = getattr(args,name);digest = getattr(args,name+"_sha256")
            inputs[name] = QA.read_bound(regular(str(path), AUDIT_ROOT), digest)
        proposal, protection, final = inputs["proposal"], inputs["protected_inventory"], inputs["final_inventory"]
        source_hashes = {}
        for path in [Path(__file__).resolve(),TEST_SOURCE,MAIN_HELPER,QA_HELPER]:
            source_hashes[str(path)] = sha(path)
            require(protection["files"].get(str(path), {}).get("sha256") == source_hashes[str(path)], "Executor/guard/tests source is not freshly pinned")
        guard = load_module("main_cleanup_guard", MAIN_HELPER)
        guard.verify_retention(final,None)
        require(not guard.verify_protection(protection,final), "Current source/app closure differs")
        rows = plan(proposal, set(protection["files"])|set(final["files"]), inputs["initial_protected_inventory"]["files"],
                    inputs["original_inventory"]["files"], inputs["prior_protected_inventory"]["files"])
        tracked = guard.tracked_files()
        require(not {Path(row["path"]) for row in rows}.intersection(tracked), "Git-tracked PNG retirement refused")
        preserved = siblings_inventory(rows)
        report.update({"plannedFiles":len(rows), "plannedLogicalBytes":sum(row["bytes"] for row in rows),
                       "sourceHashes":source_hashes, "proposalSha256":args.proposal_sha256,
                       "boundInputs":{key:{"path":str(getattr(args,key)),"sha256":getattr(args,key+"_sha256")} for key in inputs},
                       "preservedSiblingFiles":preserved, "protectedFiles":len(protection["files"]), "before":guard.space()})
        paths = [Path(row["path"]).parent for row in rows]
        report["activity"] = guard.activity(paths)
        require(not report["activity"]["openHandles"] and not report["activity"]["processes"], "Repository PNG targets are active")
        if args.execute:
            for index,row in enumerate(rows):
                if index%25 == 0:
                    active = guard.activity(paths)
                    require(not active["openHandles"] and not active["processes"], "Repository PNG targets became active")
                    require(all(sha(Path(name)) == value for name,value in source_hashes.items()), "Executor source changed")
                    require(all(sha(Path(value["path"])) == value["sha256"] for value in report["boundInputs"].values()), "Reviewed plan/protection changed")
                    require(all(sha(Path(value["path"])) == value["sha256"] for value in proposal["inputReports"]), "Immutable reader/retirement provenance changed")
                unlink_exact(row)
                report["results"].append({"path":row["path"],"sha256":row["sha256"],"bytes":row["bytes"],"reason":row["reason"]})
                report["removedFiles"] += 1;report["removedLogicalBytes"] += row["bytes"]
        else:
            plan(proposal,set(protection["files"])|set(final["files"]),inputs["initial_protected_inventory"]["files"],
                 inputs["original_inventory"]["files"],inputs["prior_protected_inventory"]["files"])
        require(siblings_inventory(rows) == preserved, "Untouched sibling files changed")
        require(not guard.verify_protection(protection,final), "Protected current source/app changed")
        require(all(sha(Path(name)) == value for name,value in source_hashes.items()), "Executor source changed")
        require(all(sha(Path(value["path"])) == value["sha256"] for value in report["boundInputs"].values()), "Reviewed plan/protection changed")
        require(all(sha(retained_regular(name)) == value["sha256"] and Path(name).stat().st_size == value["bytes"]
                    for name,value in proposal["retainedFiles"].items()), "Retained current/gallery/reader PNG changed")
        report.update({"status":"exact-repository-study-pngs-retired-protection-verified" if args.execute else "repository-png-dry-run-reviewed-no-deletion",
                       "protectedHashesUnchanged":True,"siblingFilesUnchanged":True,"retainedReaderHashesUnchanged":True})
    except (OSError,Unsafe,guard.Unsafe if guard else Unsafe,subprocess.SubprocessError,ValueError,KeyError) as error:
        report.update(status="failed-closed",failureCount=1,error=str(error))
        if guard and report["removedFiles"]:
            report["afterProtectionFailures"] = guard.verify_protection(protection,final)
        if preserved is not None:
            try:report["siblingFilesUnchanged"] = siblings_inventory(rows) == preserved
            except (OSError,Unsafe) as verification_error:report["siblingVerificationError"] = str(verification_error)
    if guard and "before" in report:
        report["after"] = guard.space();report["observedAvailableByteChange"] = report["after"]["availableBytes"]-report["before"]["availableBytes"]
    report["completedAtEpoch"] = time.time()
    validate_report(args.report)
    with args.report.open("x") as stream:json.dump(report,stream,indent=2);stream.write("\n")
    print(json.dumps({key:report.get(key) for key in ("status","plannedFiles","removedFiles","failureCount","error")},indent=2))
    return 1 if report["failureCount"] else 0


if __name__ == "__main__":sys.exit(main())
