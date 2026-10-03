#!/usr/bin/env python3
"""Remove only explicitly audited generated paths; the default is a dry run.

The source/app protection snapshot must be fresh after legitimate implementation
changes. --refresh-protection-to writes a replacement snapshot and a change log;
it cannot delete anything. Immutable historical receipts are never rewritten.
Optional runtime pruning retains summaries and selected original stills, and
records that the historical full sequence is no longer present.
"""
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import stat
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

PROJECT = Path(__file__).resolve().parents[2]
DEFAULT_AUDIT = PROJECT / "output/unreal/performance-20261003-r1/storage-audit/storage-audit.json"
FRAME = re.compile(r"frame-(\d+)\.png$")
PREDECESSOR_PROJECTS = (
    "exterior-20261002-r43b", "exterior-20261002-r46a",
    "exterior-20261002-r46a-burkea-clay-two-camera-candidate-r32", "dom-app-20261003-r1",
    "dom-app-20261003-performance-r1", "dom-app-20261003-performance-r2")
FINAL_PROJECT = "output/unreal/dom-app-20261003-performance-r3/Project/BreziTwin"
POST_PACKAGE_XCODE_REBINDS = {
    FINAL_PROJECT + "/Intermediate/ProjectFilesMac/BreziTwin (Mac).xcodeproj/project.pbxproj": (
        "97cf5a74b121d7df10b3122ddcfc675c0003341b77cab51575841c1d2ebfc1e8",
        "4820225e02c53a78c91902f70c697c179316bda533314eac6a059bc61f5e3a77"),
    FINAL_PROJECT + "/Intermediate/ProjectFilesMac/BreziTwin (Mac).xcodeproj/xcshareddata/xcschemes/BreziTwin.xcscheme": (
        "9552ad38f9be551fc6d555fb9dad28984e9cf94f1a4a4933d87f8319ab1744dc",
        "c1f6be1b6acca40a46a52d1ae56351dc7e371680ed4eb6bb39c355a823188b20")}


class Unsafe(RuntimeError):
    pass


def require(condition, reason):
    if not condition:
        raise Unsafe(reason)


def digest(path):
    result = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b""):
            result.update(block)
    return result.hexdigest()


def read_json(path):
    return json.loads(Path(path).read_text())


def save_new(path, value):
    path = Path(path)
    require(not path.exists() and not path.is_symlink(), "Report already exists: " + str(path))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x") as stream:
        json.dump(value, stream, indent=2)
        stream.write("\n")


def underneath(path, parent):
    return path == parent or parent in path.parents


def canonical(path, boundary, allow_missing=False):
    path = Path(os.path.abspath(path))
    boundary = boundary.resolve()
    require(path != boundary and underneath(path, boundary), "Unbounded cleanup target: " + str(path))
    require(path.resolve() == path, "Symlink or noncanonical cleanup path: " + str(path))
    current = boundary
    for part in path.relative_to(boundary).parts:
        current = current / part
        if allow_missing and not current.exists():
            break
        require(not current.is_symlink(), "Symlink cleanup ancestor: " + str(current))
        require(current.stat().st_uid == os.getuid(), "Foreign-owned cleanup path: " + str(current))
    return path


def tracked_files():
    result = subprocess.run(["git", "ls-files", "-z"], cwd=PROJECT, check=True, capture_output=True)
    return {PROJECT / name for name in result.stdout.decode().split("\0") if name}


def inventory(path):
    """Metadata includes inode/time/size to detect changes before unlinking."""
    records = []
    require(path.is_dir() and not path.is_symlink(), "Not a real cleanup directory: " + str(path))
    for base, directories, files in os.walk(path, followlinks=False):
        for name in directories + files:
            entry = Path(base) / name
            metadata = entry.lstat()
            require(metadata.st_uid == os.getuid(), "Foreign-owned cleanup entry: " + str(entry))
            require(not stat.S_ISLNK(metadata.st_mode), "Symlink in cleanup target: " + str(entry))
            require(stat.S_ISREG(metadata.st_mode) or stat.S_ISDIR(metadata.st_mode),
                    "Special file in cleanup target: " + str(entry))
            require(not getattr(metadata, "st_flags", 0) & (stat.UF_IMMUTABLE | stat.SF_IMMUTABLE),
                    "Immutable cleanup entry: " + str(entry))
            if stat.S_ISREG(metadata.st_mode):
                records.append({"path": str(entry), "inode": metadata.st_ino,
                                "bytes": metadata.st_size, "mtimeNs": metadata.st_mtime_ns,
                                "allocatedReferenceBytes": metadata.st_blocks * 512})
    return sorted(records, key=lambda row: row["path"])


def verify_protection(protected, final):
    failures = []
    for name, expected in protected["files"].items():
        path = Path(name)
        if not path.is_file() or path.is_symlink():
            failures.append({"path": name, "reason": "Missing or symlink protected file"})
        elif digest(path) != expected["sha256"]:
            failures.append({"path": name, "reason": "Protected SHA256 changed"})
    for name in final["files"]:
        path = Path(name)
        if not path.is_file() or path.is_symlink():
            failures.append({"path": name, "reason": "Missing or symlink final dependency"})
    return failures


def fresh_current_bindings(expected_project=None):
    """Rebind only a natively verified installed payload; no source retirement."""
    selection = PROJECT / "output/unreal/dom-app-current.json"
    if not selection.exists():
        return {}, None
    current = read_json(selection)
    require(current["status"] == "dom-installed-native-visually-verified", "Current app is not natively verified")
    app = Path(current["appPath"])
    require(app == Path("/Applications/Dom.app"), "Unexpected installed Dom path")
    receipt = Path(current["packageReceiptPath"])
    require(digest(receipt) == current["packageReceiptSha256"], "Current installed package receipt changed")
    packaged = read_json(receipt)
    require(packaged["status"] == "dom-final-exterior-standalone-package-validated"
            and packaged["activeDesign"] == "C/B/B", "Invalid current package")
    if expected_project is not None:
        require(Path(packaged["project"]) == expected_project, "Installed app is not the requested final project")
    payload = {row["path"]: row for row in inventory(app)}
    actual = {str(Path(name).relative_to(app)): digest(name) for name in payload}
    require(actual == packaged["bundle"]["payloadHashes"], "Current installed payload differs from exact new receipt")
    subprocess.run(["codesign", "--verify", "--deep", "--strict", str(app)], check=True, capture_output=True)
    bindings = {str(app / name): {"sha256": sha, "bytes": (app / name).stat().st_size}
                for name, sha in actual.items()}
    for path in [selection, receipt, PROJECT / "output/unreal/exterior-final-current.json"]:
        bindings[str(path)] = {"sha256": digest(path), "bytes": path.stat().st_size}
    return bindings, packaged


def authored_files(packaged=None):
    """Include new files created by authorized work, never caches or history."""
    roots = [PROJECT / name for name in ("app", "lib", "docs", "scripts", "tests", "versions", "public", "arch-docs",
             "foundation-analysis/inputs", "foundation-analysis/results", "foundation-analysis/archive",
             "unreal/BreziTwin/Source", "unreal/BreziTwin/Config", "unreal/BreziTwin/Build", "unreal/BreziTwin/Plugins")]
    extra = [path for path in PROJECT.iterdir() if path.is_file() and not path.is_symlink()]
    if packaged:
        project = canonical(packaged["project"], PROJECT)
        roots.extend(project / name for name in ("Source", "Config", "Content", "Build"))
        extra.append(project / "BreziTwin.uproject")
        # Flat native executable/target/modules support relocatable rebuilds. The
        # nested .app is a duplicate build product and is deliberately excluded.
        binaries = project / "Binaries"
        if binaries.exists():
            for folder, directories, files in os.walk(binaries, followlinks=False):
                directories[:] = [name for name in directories if not name.endswith(".app")]
                extra.extend(Path(folder) / name for name in files)
    result = set(extra)
    for root in roots:
        if not root.exists():
            continue
        for folder, directories, files in os.walk(root, followlinks=False):
            directories[:] = [name for name in directories if name not in
                              ("Intermediate", "Binaries", "Saved", "DerivedDataCache", "__pycache__")]
            result.update(Path(folder) / name for name in files if not (Path(folder) / name).is_symlink())
    return result


def rehash_final_closure(final, destination):
    files, metadata, mismatches = {}, {}, []
    packet = final.get("sourcePacketPath")
    if packet:
        require(digest(packet) == final["sourcePacketSha256"], "Immutable final dependency packet changed")
    for name, expected in final["files"].items():
        path = Path(name)
        require(path.is_file() and not path.is_symlink(), "Missing immutable final dependency: " + name)
        before = path.stat()
        current = {"sha256": digest(path), "bytes": path.stat().st_size}
        after = path.stat()
        require((before.st_ino, before.st_size, before.st_mtime_ns) == (after.st_ino, after.st_size, after.st_mtime_ns),
                "Historical dependency changed during full hash: " + name)
        files[name] = current
        metadata[name] = {"inode": after.st_ino, "bytes": after.st_size, "mtimeNs": after.st_mtime_ns}
        if current["sha256"] != expected:
            mismatches.append({"path": name, "expectedHistoricalSha256": expected, **current})
    save_new(destination, {"schemaVersion": 1, "createdAtEpoch": time.time(),
                          "basis": "Fresh full per-file SHA256 of immutable prior final closure before planned retirement",
                          "fileCount": len(files), "files": files, "historicalFileMetadata": metadata,
                          "historicalHashMismatches": mismatches,
                          "allHistoricalExpectedHashesExact": not mismatches})
    require(not mismatches, "Immutable final closure hash mismatch; inspect " + str(destination))
    return files


def retirement_roots():
    return {PROJECT / "output/unreal" / name / "Project/BreziTwin" for name in PREDECESSOR_PROJECTS}


def final_project():
    """An exact override remains bound to installed receipt/selector in prepare."""
    path = canonical(PROJECT / os.environ.get("DOM_FINAL_PROJECT", FINAL_PROJECT), PROJECT)
    relative = str(path.relative_to(PROJECT))
    require(re.fullmatch(r"output/unreal/dom-app-20261003-performance-r\d+/Project/BreziTwin", relative),
            "Final project must be one exact performance build Project")
    require(path not in retirement_roots(), "A retired candidate cannot be the current final project")
    return path


def prior_proof(final, fresh_path):
    """Authenticate every original pin before any predecessor can be retired."""
    fresh = read_json(fresh_path)
    require(fresh.get("allHistoricalExpectedHashesExact") is True
            and not fresh.get("historicalHashMismatches"), "Prior closure was not freshly exact")
    require(set(fresh["files"]) == set(final["files"]), "Prior fresh closure does not cover all original pins")
    require(set(fresh.get("historicalFileMetadata", {})) == set(final["files"]),
            "Prior proof lacks per-file inode/mtime stability metadata; take a new full snapshot")
    require(all(fresh["files"][name]["sha256"] == expected for name, expected in final["files"].items()),
            "Prior fresh closure contradicts immutable original pins")
    if final.get("sourcePacketPath"):
        require(digest(final["sourcePacketPath"]) == final["sourcePacketSha256"], "Immutable prior packet changed")
    return fresh


def retained_input_files(report_paths, retired_roots):
    """Explicitly retain audited unique raw originals outside obsolete Projects."""
    files, reports = {}, []
    for name in report_paths:
        report_path = canonical(name, PROJECT)
        report = read_json(report_path)
        require(report.get("status") == "r5-whole-project-retirement-proven-no-deletion",
                "Unexpected retained-input proof status")
        require(report.get("legacyProject") == str(PROJECT / "output/unreal/exterior-20260930-r5/Project/BreziTwin"),
                "Retained-input proof is not the audited obsolete r5 Project")
        require(report.get("deletedFiles") == 0 and report.get("retainedInputs"), "Missing original-input proof")
        protected = {}
        for path_name, row in report["retainedInputs"].items():
            path = canonical(path_name, PROJECT)
            require(not any(underneath(path, parent) for parent in retired_roots)
                    and not underneath(path, Path(report["legacyProject"])), "Original-input proof points into retired Project")
            require(path.is_file() and not path.is_symlink() and digest(path) == row["sha256"]
                    and path.stat().st_size == row["bytes"], "Retained original input changed: " + str(path))
            protected[str(path)] = {"sha256": row["sha256"], "bytes": row["bytes"]}
        files.update(protected)
        files[str(report_path)] = {"sha256": digest(report_path), "bytes": report_path.stat().st_size}
        reports.append({"path": str(report_path), "sha256": files[str(report_path)]["sha256"],
                        "retainedInputs": protected})
    return files, reports


def current_compiler_pins(game):
    """Only the exact independently audited r3 generated Xcode pair can rebind."""
    pins, rebinds = {}, []
    for name, original in game["sourcePins"].items():
        path = Path(name)
        require(path.is_file() and not path.is_symlink(), "Missing/symlink current compiled source pin: " + name)
        current = digest(path)
        if current != original:
            relative = str(path.relative_to(PROJECT)) if underneath(path, PROJECT) else None
            require(POST_PACKAGE_XCODE_REBINDS.get(relative) == (original, current),
                    "Current compiled source pin changed outside exact audited generated Xcode pair: " + name)
            rebinds.append({"path": name, "nativeBuildInputSha256": original,
                           "postPackagingSha256": current, "bytes": path.stat().st_size,
                           "reason": "UAT regenerated this exact Xcode packaging input after native compilation"})
        pins[name] = current
    return pins, rebinds


def validate_xcode_rebind(game, packaged, current_project, rebinds):
    if not rebinds:
        return None
    require(len(rebinds) == 2, "Audited generated Xcode rebind must be the complete exact pair")
    target = read_json(game["targetReceipt"])
    require(target.get("TargetName") == "BreziTwin" and target.get("Platform") == "Mac"
            and target.get("Configuration") == "Shipping", "Rebound Xcode inputs lack valid current Shipping target")
    xcode = current_project / "Intermediate/ProjectFilesMac/BreziTwin (Mac).xcodeproj"
    project_file, scheme_file = xcode / "project.pbxproj", xcode / "xcshareddata/xcschemes/BreziTwin.xcscheme"
    subprocess.run(["plutil", "-lint", str(project_file)], check=True, capture_output=True, text=True)
    scheme = ET.parse(scheme_file).getroot()
    require(scheme.tag == "Scheme" and scheme.find("ArchiveAction").get("buildConfiguration") == "Shipping",
            "Rebound Xcode scheme does not archive Shipping")
    references = scheme.findall(".//BuildableReference")
    require(references and all(row.get("BlueprintName") == "BreziTwin"
                              and row.get("BuildableName") == "BreziTwin.app"
                              and row.get("ReferencedContainer") == "container:BreziTwin (Mac).xcodeproj" for row in references),
            "Rebound Xcode scheme target identity changed")
    require('BreziTwin_Shipping.xcconfig' in project_file.read_text(), "Rebound Xcode project lacks Shipping configuration")
    ended = datetime.fromisoformat(game["endedAt"].replace("Z", "+00:00")).timestamp()
    packaged_at = datetime.fromisoformat(packaged["createdAt"].replace("Z", "+00:00")).timestamp()
    require(all(ended < Path(row["path"]).stat().st_mtime <= packaged_at for row in rebinds),
            "Generated Xcode input changed outside the audited post-build packaging interval")
    log = current_project.parents[1] / "package.log"
    text = log.read_text()
    require("Writing xcode workspace " + str(current_project / "Intermediate/ProjectFiles/BreziTwin_Mac_BreziTwin.xcworkspace") in text
            and "Writing project files... 100%" in text, "Missing exact UAT Xcode regeneration provenance")
    return {"packageLogPath": str(log), "packageLogSha256": digest(log),
            "nativeBuildEndedAt": game["endedAt"], "packageCreatedAt": packaged["createdAt"],
            "currentShippingSchemeValidated": True, "currentShippingTargetValidated": True,
            "immutableNativeBuildReceiptRewritten": False, "reboundGeneratedInputs": rebinds}


def prepare_retention(final, fresh_path, destination, original_path, retained_input_reports=()):
    """Fresh current closure replaces only explicitly retired old Projects."""
    fresh = prior_proof(final, fresh_path)
    current_project = final_project()
    bindings, packaged = fresh_current_bindings(current_project)
    require(packaged is not None, "Single-final retention requires a verified installed app")
    require(Path(packaged["project"]) == current_project, "Unexpected current final project")
    accepted_path = PROJECT / "output/unreal/exterior-final-current.json"
    accepted = read_json(accepted_path)
    require(accepted["activeDesign"] == "C/B/B" and accepted["streetAndRightSetbackMm"] == 3000,
            "Current design/setbacks changed")
    descriptor = current_project / "BreziTwin.uproject"
    current_map = current_project / "Content/Brezi/Maps/Brezi.umap"
    require(accepted["launchProject"] == accepted["savedProject"] == str(descriptor)
            and accepted["launchMap"]["path"] == accepted["savedMap"]["path"] == str(current_map),
            "Current saved/launch selector has not been rebound to the one final project")
    map_sha = digest(current_map)
    require(map_sha == accepted["launchMap"]["sha256"] == accepted["savedMap"]["sha256"]
            == packaged["selection"]["launchMap"]["sha256"], "Current accepted map differs from installed package")
    clone = read_json(current_project.parents[1] / "source-clone.json")
    require(digest(current_project.parents[1] / "source-clone.json") == packaged["sourceCloneReceiptSha256"],
            "Current source clone receipt changed")
    expected = {str(current_project / group / relative): sha
                for group, rows in clone["sourceHashes"].items() if group != "Binaries"
                for relative, sha in rows.items()}
    expected.update({str(current_project / "Source" / relative): sha
                     for relative, sha in packaged["renderSourceHashes"].items()})
    expected[str(current_project / "Source/BreziTwin/BreziStartupEntry.cpp")] = digest(PROJECT / "scripts/unreal/dom-startup-entry.cpp")
    for group in ("Source", "Config", "Content"):
        actual_names = {row["path"] for row in inventory(current_project / group)}
        expected_names = {name for name in expected if underneath(Path(name), current_project / group)}
        require(actual_names == expected_names, "Unexpected/missing current authoring " + group + " file")
    require(all(digest(name) == sha for name, sha in expected.items()), "Current authored scene/source differs from approved clone/overlay")
    require(digest(descriptor) == clone["descriptorSha256"], "Current final descriptor changed")
    game_receipt = current_project.parents[1] / "model-game-build.json"
    require(digest(game_receipt) == packaged["nativeGameBuildReceiptSha256"], "Current game build receipt changed")
    game = read_json(game_receipt)
    require(game["status"] == "model-game-build-validated" and game["gameConfiguration"] == "Shipping",
            "Current native game build not validated Shipping")
    compiler_pins, compiler_rebinds = current_compiler_pins(game)
    compiler_rebind_proof = validate_xcode_rebind(game, packaged, current_project, compiler_rebinds)
    require(digest(game["rawExecutable"]) == game["rawExecutableSha256"]
            and digest(game["targetReceipt"]) == game["targetReceiptSha256"], "Current rebuild executable/target changed")
    roots = retirement_roots()
    additional_inputs, input_reports = retained_input_files(retained_input_reports, roots)
    files = {name: row for name, row in fresh["files"].items()
             if not any(underneath(Path(name), parent) for parent in roots)}
    retained_prior = dict(files)
    for path in authored_files(packaged):
        require(path.is_file() and not path.is_symlink(), "Missing/symlink current authoring file: " + str(path))
        files[str(path)] = {"sha256": digest(path), "bytes": path.stat().st_size}
    files.update({name: {"sha256": sha, "bytes": Path(name).stat().st_size} for name, sha in expected.items()})
    compiled_generated = {}
    for name, sha in compiler_pins.items():
        path = Path(name)
        if underneath(path, PROJECT):
            require(path.is_file() and not path.is_symlink(), "Current compiled source pin is not a regular project file")
            record = {"sha256": sha, "bytes": path.stat().st_size}
            files[name] = record
            if underneath(path, current_project / "Intermediate"):
                compiled_generated[name] = record
    files[str(game_receipt)] = {"sha256": digest(game_receipt), "bytes": game_receipt.stat().st_size}
    if compiler_rebind_proof:
        log = Path(compiler_rebind_proof["packageLogPath"])
        files[str(log)] = {"sha256": compiler_rebind_proof["packageLogSha256"], "bytes": log.stat().st_size}
    files.update(bindings)
    files.update(additional_inputs)
    require(not any(any(underneath(Path(name), parent) for parent in roots) for name in files),
            "Current closure still points into a retired predecessor")
    retired_pins = {name: row for name, row in fresh["files"].items() if name not in retained_prior}
    manifest = {"schemaVersion": 1, "status": "single-final-current-closure-and-retirement-verified",
                "createdAtEpoch": time.time(), "basis": "User-authorized retirement of historical full scene replay; immutable receipts retained",
                "priorFreshClosurePath": str(fresh_path), "priorFreshClosureSha256": digest(fresh_path),
                "priorOriginalInventoryPath": str(original_path), "priorOriginalInventorySha256": digest(original_path),
                "priorOriginalFileCount": len(final["files"]), "retiredProjectRoots": sorted(str(p) for p in roots),
                "retiredOriginalPins": retired_pins, "retainedOriginalPins": retained_prior,
                "currentProject": str(current_project), "currentMap": {"path": str(current_map), "sha256": map_sha},
                "currentSelectionSha256": digest(accepted_path),
                "currentAppSelectionSha256": digest(PROJECT / "output/unreal/dom-app-current.json"),
                "currentPackageReceiptPath": read_json(PROJECT / "output/unreal/dom-app-current.json")["packageReceiptPath"],
                "currentDeclaredSourceFiles": len(expected), "currentDeclaredSourceExact": True,
                "currentGeneratedCompileInputs": compiled_generated,
                "postPackagingGeneratedInputRebind": compiler_rebind_proof,
                "additionalRetainedInputReports": input_reports,
                "fileCount": len(files), "files": files,
                "historicalReplayRetired": True, "immutableHistoricalReportsRewritten": False, "deletedFiles": 0}
    save_new(destination, manifest)
    return {"path": str(destination), "files": len(files), "retiredOriginalPins": len(retired_pins),
            "retainedOriginalPins": len(retained_prior)}


def verify_retention(manifest, final):
    require(manifest.get("status") == "single-final-current-closure-and-retirement-verified"
            and manifest.get("currentDeclaredSourceExact") is True, "Unverified retention manifest")
    roots = retirement_roots()
    require(Path(manifest["currentProject"]) == final_project(), "Retention manifest is bound to another final project")
    require(set(manifest["retiredProjectRoots"]) == {str(p) for p in roots}, "Unbounded predecessor retirement roots")
    require(digest(manifest["priorOriginalInventoryPath"]) == manifest["priorOriginalInventorySha256"],
            "Prior immutable inventory changed")
    if final is None:
        final = read_json(manifest["priorOriginalInventoryPath"])
    require(final["files"] == read_json(manifest["priorOriginalInventoryPath"])["files"],
            "Wrong original inventory for retention proof")
    require(digest(manifest["priorFreshClosurePath"]) == manifest["priorFreshClosureSha256"], "Prior fresh proof changed")
    fresh = prior_proof(final, manifest["priorFreshClosurePath"])
    retained = {name: row for name, row in fresh["files"].items()
                if not any(underneath(Path(name), parent) for parent in roots)}
    retired = {name: row for name, row in fresh["files"].items() if name not in retained}
    require(retained == manifest["retainedOriginalPins"] and retired == manifest["retiredOriginalPins"],
            "Manifest lost or broadened an original pin")
    require(all(manifest["files"].get(name) == row for name, row in retained.items()), "Retained original pins not protected")
    for report in manifest.get("additionalRetainedInputReports", []):
        require(digest(report["path"]) == report["sha256"], "Retained original-input report changed")
        require(all(manifest["files"].get(name) == row for name, row in report["retainedInputs"].items()),
                "Retained original-input report lost a protected pin")
    require(not any(any(underneath(Path(name), parent) for parent in roots) for name in manifest["files"]),
            "Current closure has a retired-root dependency")
    for name in retired:
        path = Path(name)
        if path.exists() or path.is_symlink():
            require(path.is_file() and not path.is_symlink(), "Historical pin became a symlink/special file")
            current = path.stat()
            require({"inode": current.st_ino, "bytes": current.st_size, "mtimeNs": current.st_mtime_ns}
                    == fresh["historicalFileMetadata"][name], "Historical pin changed since full snapshot: " + name)
    require(digest(PROJECT / "output/unreal/exterior-final-current.json") == manifest["currentSelectionSha256"]
            and digest(PROJECT / "output/unreal/dom-app-current.json") == manifest["currentAppSelectionSha256"],
            "Current final bindings changed after retention proof")
    require(not verify_protection(manifest, {"files": {}}), "Retained current source/app hash changed")
    return roots


def refresh_protection(old, destination, freshly_hashed_final=None, retention=None, original_final=None):
    files, changes, retired = {}, [], []
    bindings, packaged = fresh_current_bindings()
    app = Path("/Applications/Dom.app")
    retired_roots = verify_retention(retention, original_final) if retention else set()
    retired_sources = []
    for name, expected in old["files"].items():
        path = Path(name)
        if any(underneath(path, parent) for parent in retired_roots):
            require(name in retention["retiredOriginalPins"]
                    and expected["sha256"] == retention["retiredOriginalPins"][name]["sha256"],
                    "Unproven historical source retirement: " + name)
            retired_sources.append({"path": name, "previous": expected})
            continue
        if underneath(path, app) and bindings and name not in bindings:
            retired.append({"path": name, "previous": expected,
                            "reason": "Old installed-payload resource absent from exact newly verified current package"})
            continue
        require(path.is_file() and not path.is_symlink(), "Cannot refresh missing protection: " + name)
        current = bindings.get(name) or {"sha256": digest(path), "bytes": path.stat().st_size}
        files[name] = current
        if current != expected:
            changes.append({"path": name, "before": expected, "after": current})
    additions = []
    for path in authored_files(packaged):
        require(path.is_file() and not path.is_symlink(), "Not a regular authored file: " + str(path))
        name = str(path)
        if name not in files:
            files[name] = {"sha256": digest(path), "bytes": path.stat().st_size}
            additions.append(name)
    for name, record in bindings.items():
        if name not in files:
            additions.append(name)
        files[name] = record
    files.update(retention["files"] if retention else (freshly_hashed_final or {}))
    save_new(destination, {"schemaVersion": 1, "createdAtEpoch": time.time(),
                          "basis": "Explicit fresh before-cleanup snapshot after authorized work",
                          "fileCount": len(files), "files": files, "authorizedWorkChanges": changes,
                          "authorizedInstalledPayloadRetirements": retired, "newlyProtectedPaths": additions,
                          "sourceRetirementsAllowed": bool(retention),
                          "authorizedHistoricalProjectRetirements": retired_sources,
                          "retiredProjectRoots": sorted(str(p) for p in retired_roots),
                          "installedReceiptBinding": packaged.get("status") if packaged else None})
    return {"path": str(destination), "protectedFiles": len(files), "changedSinceAudit": changes,
            "authorizedInstalledPayloadRetirements": retired,
            "authorizedHistoricalProjectRetirements": len(retired_sources), "newlyProtectedPaths": len(additions)}


def ancestors():
    ids = {os.getpid()}
    parent = os.getppid()
    while parent > 1 and parent not in ids:
        ids.add(parent)
        result = subprocess.run(["ps", "-p", str(parent), "-o", "ppid="], capture_output=True, text=True)
        try:
            parent = int(result.stdout.strip())
        except ValueError:
            break
    return ids


def activity(paths):
    """Fresh native/process/open-handle check; unrelated project activity is allowed."""
    ignored = ancestors()
    result = subprocess.run(["lsof", "-nP", "-F", "pn"], capture_output=True, text=True, timeout=30)
    require(result.returncode in (0, 1), "lsof could not establish cleanup idleness: " + result.stderr[:500])
    require(not re.search(r"permission denied|operation not permitted", result.stderr, re.I),
            "Open-handle inventory incomplete: " + result.stderr[:500])
    handles, pid = [], None
    for line in result.stdout.splitlines():
        if line.startswith("p"):
            pid = int(line[1:])
        elif line.startswith("n/") and pid not in ignored:
            name = line[1:]
            if any(name == str(path) or name.startswith(str(path) + "/") for path in paths):
                handles.append({"pid": pid, "path": name})
    processes = []
    result = subprocess.run(["ps", "-axo", "pid=,command="], check=True, capture_output=True, text=True)
    for line in result.stdout.splitlines():
        fields = line.strip().split(maxsplit=1)
        if len(fields) != 2 or int(fields[0]) in ignored:
            continue
        if any(str(path) in fields[1] for path in paths):
            processes.append({"pid": int(fields[0]), "command": fields[1]})
    return {"checkedAtEpoch": time.time(), "openHandles": handles, "processes": processes}


def space():
    volume = os.statvfs(PROJECT)
    result = subprocess.run(["df", "-k", str(PROJECT)], check=True, capture_output=True, text=True)
    return {"availableBytes": volume.f_bavail * volume.f_frsize, "dfKiB": result.stdout.strip()}


def check_intersections(path, pins, tracked):
    hits = [str(pin) for pin in pins if underneath(pin, path)]
    hits += [str(pin) for pin in tracked if underneath(pin, path)]
    require(not hits, "Protected or tracked cleanup intersection: " + json.dumps(hits[:8]))


def check_retired_authoring_target(path, final):
    """A whole old r5 scene also needs retained originals and no active fallback."""
    r5 = PROJECT / "output/unreal/exterior-20260930-r5/Project/BreziTwin"
    if path != r5:
        return
    require(final.get("status") == "single-final-current-closure-and-retirement-verified",
            "Whole old r5 Project retirement needs the verified single-final closure")
    proofs = final.get("additionalRetainedInputReports", [])
    require(any(read_json(row["path"]).get("legacyProject") == str(r5) for row in proofs),
            "Whole old r5 Project retirement lacks retained raw-original/geometry proof")
    selector = read_json(PROJECT / "output/unreal/model-refresh-current.json")
    require(selector.get("status") == "superseded-by-installed-dom",
            "Historical model-refresh fallback must be explicitly superseded before whole Project retirement")


def runtime_selection(path, pins, tracked, keep_frames):
    path = canonical(path, PROJECT / "output/unreal/runtime")
    require(path.parent == PROJECT / "output/unreal/runtime", "Choose one exact historical runtime session")
    require(re.match(r"(?:motion-(?:taa|smaa|tsr|tsr100)-|flame-shape-.*-sequence-)", path.name),
            "Runtime pruning accepts only old motion/flame sequence sessions")
    check_intersections(path, pins, tracked)
    files = inventory(path)
    frames = [row for row in files if FRAME.fullmatch(Path(row["path"]).name)
              and Path(row["path"]).parent == path]
    require(len(frames) > 4, "Not a complete historical screenshot sequence")
    frames.sort(key=lambda row: int(FRAME.fullmatch(Path(row["path"]).name).group(1)))
    retain = {frames[0]["path"], frames[-1]["path"]}
    retain.update(row["path"] for row in frames
                  if int(FRAME.fullmatch(Path(row["path"]).name).group(1)) in keep_frames)
    # Current accepted proof and application/icon references must not name this session.
    for receipt in [PROJECT / "output/unreal/exterior-final-current.json",
                    PROJECT / "output/unreal/dom-app-current.json",
                    PROJECT / "unreal/BreziTwin/Build/Mac/Resources/Dom-icon-source.json"]:
        if receipt.exists():
            require(str(path) not in receipt.read_text(), "Runtime sequence belongs to current final proof")
    return {"path": str(path), "kind": "historical-sequence-interior-frames",
            "files": [row for row in frames if row["path"] not in retain],
            "retainedFrames": sorted(retain), "summaryFilesPreserved": True,
            "limit": "Old full-sequence stepping viewers will have intentionally retired middle frames; immutable receipts retained"}


def project_trash_selection(path, pins, tracked):
    """Explicit Dom-only trash batch, never the user's entire Trash."""
    boundary = Path.home() / ".Trash"
    path = canonical(path, boundary)
    require(path.parent == boundary and re.fullmatch(r"Dom-old-apps-\d{8}-r\d+", path.name),
            "Only one explicitly named Dom-old-apps batch may be selected")
    check_intersections(path, pins, tracked)
    bundles, nonbundle_files = [], []
    for folder, directories, files in os.walk(path, followlinks=False):
        entry = Path(folder)
        if entry.name.endswith(".app"):
            metadata = plistlib.loads((entry / "Contents/Info.plist").read_bytes())
            require(metadata.get("CFBundleIdentifier") == "local.brezi.twin",
                    "Trash batch contains a foreign application: " + str(entry))
            bundles.append(str(entry))
            directories[:] = []
        else:
            nonbundle_files.extend(str(entry / name) for name in files)
    require(bundles and not nonbundle_files, "Dom trash batch contains unreviewed non-application files")
    return {"path": str(path), "kind": "generated-directory", "files": inventory(path),
            "scope": "Explicit project-specific retired local.brezi.twin application batch",
            "retiredBundles": bundles}


def current_intermediate_selection(pins, tracked, final):
    """Keep the tiny current native compiler input closure, remove only outputs."""
    require(final.get("status") == "single-final-current-closure-and-retirement-verified",
            "Current Intermediate compaction requires the verified single-final manifest")
    require(Path(final["currentProject"]) == final_project(), "Intermediate belongs to another final project")
    path = canonical(final_project() / "Intermediate", PROJECT)
    inputs = final.get("currentGeneratedCompileInputs", {})
    require(inputs and all(underneath(Path(name), path) and Path(name) in pins for name in inputs),
            "Current generated compiler inputs are not all explicitly protected")
    game_path = path.parents[2] / "model-game-build.json"
    require(final["files"][str(game_path)]["sha256"] == digest(game_path), "Current native compiler receipt changed")
    game = read_json(game_path)
    compiler_pins, rebinds = current_compiler_pins(game)
    require(rebinds == (final.get("postPackagingGeneratedInputRebind") or {}).get("reboundGeneratedInputs", []),
            "Current generated input rebind changed after retention proof")
    actual_inputs = {name: {"sha256": sha, "bytes": Path(name).stat().st_size}
                     for name, sha in compiler_pins.items() if underneath(Path(name), path)}
    require(actual_inputs == inputs, "Current native generated input set changed")
    rows = inventory(path)
    retain = {row["path"] for row in rows if Path(row["path"]) in pins or Path(row["path"]) in tracked}
    require(set(inputs) <= retain, "Current generated compile inputs missing from Intermediate")
    return {"path": str(path), "kind": "generated-intermediate-output-files", "files": [row for row in rows if row["path"] not in retain],
            "retainedCompileInputPaths": sorted(inputs), "retainedProtectedPaths": sorted(retain),
            "generatedCompileInputBytes": sum(row["bytes"] for row in inputs.values()),
            "scope": "Exact current final Intermediate tree; retain native UHT/PCH/response/Xcode input pins, prune other outputs"}


def apply_target(target):
    path = Path(target["path"])
    boundary = Path.home() / ".Trash" if target.get("retiredBundles") else PROJECT
    canonical(path, boundary)
    expected = target["files"]
    current = inventory(path)
    if target["kind"] == "generated-directory":
        require(current == expected, "Cleanup metadata changed since fresh plan: " + str(path))
    else:
        current_by_path = {row["path"]: row for row in current}
        require(all(current_by_path.get(row["path"]) == row for row in expected),
                "Historical sequence changed since fresh plan: " + str(path))
    active = activity([path])
    require(not active["openHandles"] and not active["processes"],
            "Cleanup target became active: " + str(path))
    failures, removed, logical = [], 0, 0
    for row in expected:
        entry = Path(row["path"])
        try:
            require(entry.resolve() == entry, "Cleanup entry ancestor became a symlink: " + str(entry))
            metadata = entry.lstat()
            require(not entry.is_symlink() and stat.S_ISREG(metadata.st_mode)
                    and metadata.st_ino == row["inode"] and metadata.st_size == row["bytes"]
                    and metadata.st_mtime_ns == row["mtimeNs"], "Entry changed before unlink: " + str(entry))
            entry.unlink()
            removed += 1
            logical += row["bytes"]
        except (OSError, Unsafe) as error:
            failures.append({"path": str(entry), "error": str(error)})
            break  # Fail closed, report partial completion honestly.
    if target["kind"] == "generated-directory" and not failures:
        try:
            for base, directories, _ in os.walk(path, topdown=False, followlinks=False):
                for name in directories:
                    (Path(base) / name).rmdir()
            path.rmdir()
        except OSError as error:
            failures.append({"path": str(path), "error": str(error)})
    if target["kind"] == "historical-sequence-interior-frames" and not failures:
        try:
            save_new(path / ("sequence-retention-" + str(time.time_ns()) + ".json"), {
                "schemaVersion": 1, "status": "historical-full-sequence-retired-selected-original-stills-retained",
                "createdAtEpoch": time.time(), "removedFrames": expected,
                "retainedFrames": target["retainedFrames"], "originalSummariesUnchanged": True})
        except (OSError, Unsafe) as error:
            failures.append({"path": str(path), "error": str(error)})
    if target["kind"] == "generated-intermediate-output-files" and not failures:
        try:
            for base, directories, _ in os.walk(path, topdown=False, followlinks=False):
                for name in directories:
                    folder = Path(base) / name
                    if not any(folder.iterdir()):
                        folder.rmdir()
            save_new(path.parents[2] / ("generated-compile-input-retention-" + str(time.time_ns()) + ".json"), {
                "schemaVersion": 1, "status": "current-compiler-inputs-retained-generated-outputs-pruned",
                "createdAtEpoch": time.time(), "removedOutputs": expected,
                "retainedCompileInputPaths": target["retainedCompileInputPaths"]})
        except (OSError, Unsafe) as error:
            failures.append({"path": str(path), "error": str(error)})
    return {"path": str(path), "removedFiles": removed, "removedLogicalBytes": logical,
            "failureCount": len(failures), "failures": failures}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, default=DEFAULT_AUDIT)
    parser.add_argument("--protected-inventory", type=Path)
    parser.add_argument("--final-inventory", type=Path)
    parser.add_argument("--root", action="append", default=[], help="Exact audited root; repeat to narrow scope")
    parser.add_argument("--phase2-generated", action="store_true", help="Allow exact audited phase2 generated roots")
    parser.add_argument("--runtime-sequence", action="append", default=[], help="Optional exact old sequence root")
    parser.add_argument("--project-trash-root", action="append", default=[], help="Optional exact Dom-old-apps batch, never all Trash")
    parser.add_argument("--compact-current-intermediate", action="store_true", help="Prune current Intermediate outputs but retain verified compiler input pins")
    parser.add_argument("--keep-frame", action="append", type=int, default=[32, 52])
    parser.add_argument("--execute", action="store_true", help="Actually unlink only freshly validated planned files")
    parser.add_argument("--refresh-protection-to", type=Path, help="Write fresh protection snapshot; cannot execute")
    parser.add_argument("--rehash-final-closure-to", type=Path, help="Heavy full14k SHA256 report; run after GPU work, never combined with execution")
    parser.add_argument("--prepare-retention-manifest-to", type=Path, help="Hash and bind one final project after selector/install QA; no deletion")
    parser.add_argument("--prior-fresh-closure", type=Path, help="Exact full original14256 SHA report for predecessor retirement")
    parser.add_argument("--retained-input-report", action="append", type=Path, default=[],
                        help="Explicit audited r5 raw-original/geometry retention proof; only used while preparing a manifest")
    parser.add_argument("--retention-manifest", type=Path, help="Verified single-final manifest for explicit source protection rebind")
    parser.add_argument("--report", type=Path, help="Fresh report destination; existing evidence cannot be overwritten")
    args = parser.parse_args()
    require(not (args.execute and (args.refresh_protection_to or args.rehash_final_closure_to or args.prepare_retention_manifest_to)),
            "Protection refresh/full hashing and deletion are separate operations")
    require(not args.retention_manifest or args.refresh_protection_to,
            "Retention manifest is only used for an explicit no-deletion protection rebind")
    require(not args.prepare_retention_manifest_to or (args.prior_fresh_closure and not args.refresh_protection_to
                                                     and not args.rehash_final_closure_to),
            "Retention preparation needs a completed separate original full-hash proof")
    require(not args.retained_input_report or args.prepare_retention_manifest_to,
            "Retained input reports are only consumed by no-deletion manifest preparation")
    report_path = args.report or args.audit.parent / ("cleanup-" + ("execute-" if args.execute else "dry-run-") + str(time.time_ns()) + ".json")
    report = {"schemaVersion": 1, "status": "planning", "executeRequested": args.execute,
              "createdAtEpoch": time.time(), "auditPath": str(args.audit), "targets": [],
              "results": [], "failureCount": 0,
              "physicalSpaceCaveat": "APFS shared extents and concurrent activity mean observed free-space change differs from logical deletion"}
    try:
        require(not report_path.exists(), "Report already exists")
        audit = read_json(args.audit)
        protected_path = args.protected_inventory or Path(audit["protectedInventory"])
        final_path = args.final_inventory or Path(audit["recordedFinalDependencyInventory"])
        protected, final = read_json(protected_path), read_json(final_path)
        report.update({"auditSha256": digest(args.audit), "protectedInventoryPath": str(protected_path),
                       "protectedInventorySha256": digest(protected_path), "protectedFiles": len(protected["files"]),
                       "finalInventorySha256": digest(final_path), "finalDependencyPaths": len(final["files"])})
        if args.prepare_retention_manifest_to:
            report["retentionPreparation"] = prepare_retention(final, args.prior_fresh_closure,
                                                              args.prepare_retention_manifest_to, final_path,
                                                              args.retained_input_report)
            report["status"] = "single-final-retention-manifest-written-no-deletion"
        elif args.refresh_protection_to or args.rehash_final_closure_to:
            fresh_final = rehash_final_closure(final, args.rehash_final_closure_to) if args.rehash_final_closure_to else None
            if args.rehash_final_closure_to:
                report["freshFinalClosureReport"] = str(args.rehash_final_closure_to)
            if args.refresh_protection_to:
                retention = read_json(args.retention_manifest) if args.retention_manifest else None
                report["protectionRefresh"] = refresh_protection(protected, args.refresh_protection_to,
                                                                fresh_final, retention, final)
            report["status"] = "fresh-protection-snapshot-written-no-deletion"
        else:
            if final.get("status") == "single-final-current-closure-and-retirement-verified":
                verify_retention(final, None)
            failures = verify_protection(protected, final)
            report["protectionFailures"] = failures
            require(not failures, "Protection snapshot differs; inspect failures and refresh only after authorized work")
            allowed = {row["path"]: row for row in audit["safeAllowlist"]}
            if args.phase2_generated:
                allowed.update({row["path"]: row for row in audit["phase2"]["additionalGeneratedRootCandidates"]})
            choices = args.root or ([] if args.runtime_sequence or args.project_trash_root or args.compact_current_intermediate else list(allowed))
            require(len(choices) == len(set(choices)), "Duplicate cleanup root")
            pins = {Path(name) for name in protected["files"]} | {Path(name) for name in final["files"]}
            tracked = tracked_files()
            for name in choices:
                path = canonical(name, PROJECT, allow_missing=True)
                require(str(path) in allowed, "Target is not in exact audited allowlist: " + str(path))
                check_intersections(path, pins, tracked)
                check_retired_authoring_target(path, final)
                if not path.exists():
                    report.setdefault("alreadyAbsent", []).append(str(path))
                    continue
                files = inventory(path)
                row = allowed[str(path)]
                require(len(files) == row["files"] and sum(item["bytes"] for item in files) == row["logicalBytes"],
                        "Audit root changed; generate a fresh audit before execution: " + str(path))
                report["targets"].append({"path": str(path), "kind": "generated-directory", "files": files})
            for name in args.runtime_sequence:
                report["targets"].append(runtime_selection(name, pins, tracked, set(args.keep_frame)))
            for name in args.project_trash_root:
                report["targets"].append(project_trash_selection(name, pins, tracked))
            if args.compact_current_intermediate:
                report["targets"].append(current_intermediate_selection(pins, tracked, final))
            paths = [Path(row["path"]) for row in report["targets"]]
            require(len(paths) == len(set(paths)), "Duplicate target")
            require(not any(a != b and underneath(a, b) for a in paths for b in paths), "Nested cleanup targets")
            report["activity"] = activity(paths)
            require(not report["activity"]["openHandles"] and not report["activity"]["processes"],
                    "A selected cleanup target is active")
            report["before"] = space()
            report["plannedFiles"] = sum(len(row["files"]) for row in report["targets"])
            report["plannedLogicalBytes"] = sum(item["bytes"] for row in report["targets"] for item in row["files"])
            if args.execute:
                for target in report["targets"]:
                    result = apply_target(target)
                    report["results"].append(result)
                    require(result["failureCount"] == 0, "Cleanup stopped after a deletion failure")
                report["afterProtectionFailures"] = verify_protection(protected, final)
                require(not report["afterProtectionFailures"], "A protected file changed during cleanup")
                report["status"] = "exact-generated-targets-cleaned-protection-verified"
            else:
                report["status"] = "dry-run-reviewed-no-deletion"
            report["after"] = space()
            report["observedAvailableByteChange"] = report["after"]["availableBytes"] - report["before"]["availableBytes"]
    except (OSError, Unsafe, subprocess.SubprocessError, ValueError, KeyError) as error:
        report["status"] = "failed-closed"
        report["failureCount"] = max(1, sum(row.get("failureCount", 0) for row in report["results"]))
        report["error"] = str(error)
        if "before" in report:
            report["after"] = space()
            report["observedAvailableByteChange"] = report["after"]["availableBytes"] - report["before"]["availableBytes"]
    report["removedFiles"] = sum(row["removedFiles"] for row in report["results"])
    report["removedLogicalBytes"] = sum(row["removedLogicalBytes"] for row in report["results"])
    if args.execute and report["removedFiles"] and "afterProtectionFailures" not in report:
        report["afterProtectionFailures"] = verify_protection(protected, final)
        if report["afterProtectionFailures"]:
            report["failureCount"] += len(report["afterProtectionFailures"])
            report["status"] = "failed-closed"
    report["completedAtEpoch"] = time.time()
    save_new(report_path, report)
    print(json.dumps({"status": report["status"], "report": str(report_path),
                      "plannedFiles": report.get("plannedFiles", 0), "removedFiles": report["removedFiles"],
                      "failureCount": report["failureCount"], "error": report.get("error")}, indent=2))
    return 1 if report["failureCount"] else 0


if __name__ == "__main__":
    sys.exit(main())
