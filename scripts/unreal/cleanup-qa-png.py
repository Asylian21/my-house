#!/usr/bin/env python3
"""Retire an exactly reviewed set of Dom QA PNGs. Dry-run by default.

No directory is removed. The QA root, durable mirrors, all remaining files,
current source/app protection, and immutable proposal inputs are checked.
"""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

PROJECT = Path(__file__).resolve().parents[2]
AUDIT_ROOT = PROJECT / "output/unreal/performance-20261003-r1/storage-audit"
QA_ROOT = Path("/Users/davidzita/Library/Containers/local.brezi.twin/Data/Library/Application Support/BreziTwin/QA")
HELPER_PATH = PROJECT / "scripts/unreal/cleanup-generated.py"
TEST_PATH = PROJECT / "scripts/unreal/test_cleanup_qa_png.py"


class Unsafe(RuntimeError):
    pass


def require(condition, message):
    if not condition:
        raise Unsafe(message)


def underneath(path, parent):
    return path == parent or parent in path.parents


def sha(path):
    value = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            value.update(chunk)
    return value.hexdigest()


def regular(name, boundary):
    path = Path(name)
    require(path.is_absolute() and path == path.resolve(), "Non-canonical or symlink path: " + str(path))
    require(underneath(path, boundary) and path != boundary, "Path escaped its exact boundary: " + str(path))
    for folder in [boundary, *path.parents]:
        if not underneath(folder, boundary):
            break
        info = folder.lstat()
        require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid(), "Unsafe parent ownership/type: " + str(folder))
    info = path.lstat()
    require(stat.S_ISREG(info.st_mode) and info.st_uid == os.getuid(), "Unsafe file ownership/type: " + str(path))
    require(not (getattr(info, "st_flags", 0) & (getattr(stat, "UF_IMMUTABLE", 0) | getattr(stat, "SF_IMMUTABLE", 0))),
            "Immutable file: " + str(path))
    return path


def metadata(path, hashed=True):
    info = path.stat()
    value = {"path": str(path), "bytes": info.st_size, "inode": info.st_ino,
             "mtimeNs": info.st_mtime_ns, "uid": info.st_uid}
    if hashed:
        value["sha256"] = sha(path)
    return value


def read_bound(path, expected_sha):
    require(path.is_file() and not path.is_symlink() and path.resolve() == path, "Invalid input report path")
    require(sha(path) == expected_sha, "Reviewed input SHA changed: " + str(path))
    return json.loads(path.read_text())


def validate_qa_root(proposal):
    require(proposal.get("qaRoot") == str(QA_ROOT) and QA_ROOT.resolve() == QA_ROOT
            and proposal.get("qaRootResolved") == str(QA_ROOT), "Wrong QA boundary")
    info = QA_ROOT.lstat()
    require(stat.S_ISDIR(info.st_mode) and info.st_uid == os.getuid() == proposal.get("qaRootUid")
            and info.st_ino == proposal.get("qaRootInode"), "QA root ownership/inode changed")


def plan(proposal, pins):
    require(proposal.get("schemaVersion") == 1
            and proposal.get("status") == "qa-exact-png-retirement-proposed-no-deletion", "Unreviewable proposal status")
    validate_qa_root(proposal)
    require(proposal.get("deletedFiles", 0) == 0, "Proposal already executed")
    inputs = {}
    for row in proposal.get("inputReports", []):
        path = regular(row["path"], PROJECT)
        inputs[str(path)] = read_bound(path, row["sha256"])
    require(inputs, "No immutable reader/retirement provenance")
    retained = proposal.get("retainedFiles", {})
    require(retained, "No durable originals pinned")
    for name, record in retained.items():
        path = regular(name, QA_ROOT if underneath(Path(name), QA_ROOT) else PROJECT)
        require(path.stat().st_size == record["bytes"] and sha(path) == record["sha256"], "Retained original differs: " + name)
    rows = proposal.get("files", [])
    require(rows, "Empty PNG retirement proposal")
    names = [row["path"] for row in rows]
    require(len(names) == len(set(names)), "Duplicate PNG target")
    require(not set(names).intersection(retained) and not set(names).intersection(pins), "PNG target intersects protected originals")
    validated = []
    for row in rows:
        path = regular(row["path"], QA_ROOT)
        require(path.suffix.lower() == ".png", "Non-PNG deletion refused")
        require(row.get("reason"), "Missing concrete retirement reason")
        require(metadata(path) == {key: row[key] for key in ("path", "bytes", "inode", "mtimeNs", "uid", "sha256")},
                "PNG metadata or hash changed: " + str(path))
        category = row.get("category")
        if category == "durable-mirror":
            mirror = row.get("mirrorPath")
            require(mirror in retained and underneath(Path(mirror), PROJECT), "Mirror is not a protected durable project file")
            require(Path(mirror).suffix.lower() == ".png" and retained[mirror]["sha256"] == row["sha256"]
                    and retained[mirror]["bytes"] == row["bytes"], "Mirror is not an exact PNG duplicate")
        elif category == "retired-study-frame":
            require(row.get("readerAuditProofPath") in inputs and row.get("retirementProofPath") in inputs,
                    "Historical frame lacks exact reader/retirement proof")
            reader = inputs[row["readerAuditProofPath"]]
            retirement = inputs[row["retirementProofPath"]]
            require(reader.get("status") == "active-authored-reader-audit-complete-no-deletion"
                    and reader.get("qaRoot") == str(QA_ROOT)
                    and row["path"] in reader.get("historicalFrameTargets", []),
                    "Historical frame is outside the exact completed reader audit")
            require(retirement.get("status") == "exact-historical-generated-png-retirement-proposed-no-deletion"
                    and retirement.get("qaRoot") == str(QA_ROOT)
                    and any(value.get("path") == row["path"] and value.get("sha256") == row["sha256"]
                            and value.get("bytes") == row["bytes"] and value.get("category") == category
                            for value in retirement.get("targets", [])),
                    "Historical frame is outside the exact hashed retirement audit")
            originals = row.get("retainedFramePaths", [])
            require(originals and all(name in retained and Path(name).suffix.lower() == ".png" for name in originals),
                    "Historical sequence lost its selected original frames")
        else:
            raise Unsafe("Unknown PNG retirement category")
        validated.append(row)
    return validated


def preserved_inventory(target_names):
    result = {}
    require(QA_ROOT.is_dir() and QA_ROOT.resolve() == QA_ROOT, "QA root changed")
    for base, directories, files in os.walk(QA_ROOT, followlinks=False):
        for name in directories:
            folder = Path(base) / name
            require(not folder.is_symlink() and folder.stat().st_uid == os.getuid(), "Unsafe QA directory")
        for name in files:
            path = regular(str(Path(base) / name), QA_ROOT)
            if str(path) not in target_names:
                result[str(path)] = metadata(path)
    return result


def unlink_exact(row):
    path = regular(row["path"], QA_ROOT)
    expected = {key: row[key] for key in ("path", "bytes", "inode", "mtimeNs", "uid", "sha256")}
    require(metadata(path) == expected, "PNG changed immediately before unlink: " + str(path))
    # Repeat inexpensive metadata checks after hashing before the actual unlink.
    regular(str(path), QA_ROOT)
    require(metadata(path, hashed=False) == {key: expected[key] for key in ("path", "bytes", "inode", "mtimeNs", "uid")},
            "PNG changed during final hash")
    path.unlink()


def validate_report_path(path):
    require(path.is_absolute() and path.resolve() == path and underneath(path, AUDIT_ROOT)
            and path != AUDIT_ROOT and not path.exists() and path.parent.is_dir(),
            "Report must be fresh inside the exact audit directory")


def save_new(path, value):
    validate_report_path(path)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ("proposal", "protected-inventory", "final-inventory"):
        parser.add_argument("--" + name, required=True, type=Path)
        parser.add_argument("--" + name + "-sha256", required=True)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    report = {"schemaVersion": 1, "status": "planning", "createdAtEpoch": time.time(),
              "executeRequested": args.execute, "qaRoot": str(QA_ROOT), "directoriesRemoved": 0,
              "removedFiles": 0, "removedLogicalBytes": 0, "failureCount": 0,
              "physicalSpaceCaveat": "APFS shared extents and concurrent activity can differ from logical deletion",
              "originalReceiptsRewritten": False, "results": []}
    helper = None
    protected = final = preserved = None
    try:
        validate_report_path(args.report)
        proposal = read_bound(regular(str(args.proposal), AUDIT_ROOT), args.proposal_sha256)
        protected = read_bound(regular(str(args.protected_inventory), AUDIT_ROOT), args.protected_inventory_sha256)
        final = read_bound(regular(str(args.final_inventory), AUDIT_ROOT), args.final_inventory_sha256)
        require(protected["files"].get(str(Path(__file__).resolve()), {}).get("sha256") == sha(Path(__file__).resolve()),
                "Executor source is not bound to fresh protection")
        require(protected["files"].get(str(HELPER_PATH), {}).get("sha256") == sha(HELPER_PATH), "Main helper changed")
        require(protected["files"].get(str(TEST_PATH), {}).get("sha256") == sha(TEST_PATH), "Safety tests are not in fresh protection")
        spec = importlib.util.spec_from_file_location("dom_cleanup_guard", HELPER_PATH)
        helper = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(helper)
        helper.verify_retention(final, None)
        failures = helper.verify_protection(protected, final)
        require(not failures, "Current source/app protection changed")
        pins = set(protected["files"]) | set(final["files"])
        rows = plan(proposal, pins)
        names = {row["path"] for row in rows}
        preserved = preserved_inventory(names)
        report.update({"proposalPath": str(args.proposal), "proposalSha256": args.proposal_sha256,
                       "protectedInventoryPath": str(args.protected_inventory), "protectedInventorySha256": args.protected_inventory_sha256,
                       "finalInventoryPath": str(args.final_inventory), "finalInventorySha256": args.final_inventory_sha256,
                       "plannedFiles": len(rows), "plannedLogicalBytes": sum(row["bytes"] for row in rows),
                       "preservedQAFileCount": len(preserved), "preservedNonPngCount": sum(Path(name).suffix.lower() != ".png" for name in preserved),
                       "preservedQAFileInventory": preserved, "protectedFileCount": len(protected["files"]),
                       "sourceSha256": sha(Path(__file__).resolve()), "before": helper.space()})
        active = helper.activity([QA_ROOT])
        report["activity"] = active
        require(not active["openHandles"] and not active["processes"], "QA sandbox or Dom process is active")
        if args.execute:
            for index, row in enumerate(rows):
                if index % 25 == 0:
                    validate_qa_root(proposal)
                    active = helper.activity([QA_ROOT])
                    require(not active["openHandles"] and not active["processes"], "QA sandbox became active")
                    # Recheck immutable reviewed plan and source before each small batch.
                    require(sha(args.proposal) == args.proposal_sha256
                            and sha(Path(__file__).resolve()) == report["sourceSha256"], "Reviewed plan/source changed")
                    require(all(sha(Path(value["path"])) == value["sha256"] for value in proposal["inputReports"]),
                            "Immutable retirement provenance changed")
                unlink_exact(row)
                report["results"].append({"path": row["path"], "bytes": row["bytes"], "sha256": row["sha256"],
                                          "category": row["category"], "reason": row["reason"]})
                report["removedFiles"] += 1
                report["removedLogicalBytes"] += row["bytes"]
        else:
            # Recheck exact targets after all preservation/activity guards even for a dry-run.
            plan(proposal, pins)
        require(preserved_inventory(names) == preserved, "A retained QA file changed")
        validate_qa_root(proposal)
        require(sha(args.proposal) == args.proposal_sha256 and sha(Path(__file__).resolve()) == report["sourceSha256"],
                "Reviewed plan/source changed")
        require(all(sha(Path(row["path"])) == row["sha256"] for row in proposal["inputReports"]), "Immutable provenance changed")
        require(not helper.verify_protection(protected, final), "Current protected source/app changed")
        plan_retained = proposal["retainedFiles"]
        require(all(regular(name, QA_ROOT if underneath(Path(name), QA_ROOT) else PROJECT).stat().st_size == value["bytes"]
                    and sha(Path(name)) == value["sha256"] for name, value in plan_retained.items()), "Durable original changed")
        report.update({"preservedQAFilesUnchanged": True, "protectedHashesUnchanged": True,
                       "durableOriginalHashesUnchanged": True,
                       "status": "exact-qa-pngs-retired-protection-verified" if args.execute else "qa-png-dry-run-reviewed-no-deletion"})
    except (OSError, Unsafe, helper.Unsafe if helper else Unsafe, subprocess.SubprocessError, ValueError, KeyError) as error:
        report.update(status="failed-closed", failureCount=1, error=str(error))
        if helper and protected is not None and report["removedFiles"]:
            report["afterProtectionFailures"] = helper.verify_protection(protected, final)
        if preserved is not None:
            try:
                report["preservedQAFilesUnchanged"] = preserved_inventory(set(row["path"] for row in proposal["files"])) == preserved
            except (OSError, Unsafe) as preserved_error:
                report["preservedQAVerificationError"] = str(preserved_error)
    if helper and "before" in report:
        report["after"] = helper.space()
        report["observedAvailableByteChange"] = report["after"]["availableBytes"] - report["before"]["availableBytes"]
    report["completedAtEpoch"] = time.time()
    save_new(args.report, report)
    print(json.dumps({key: report.get(key) for key in ("status", "plannedFiles", "removedFiles", "failureCount", "error")}, indent=2))
    return 1 if report["failureCount"] else 0


if __name__ == "__main__":
    sys.exit(main())
