"""Deletion-safety regressions use isolated temporary directories only."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location("cleanup", Path(__file__).with_name("cleanup-generated.py"))
cleanup = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cleanup)


class CleanupSafety(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name).resolve()
        self.cache = self.root / "cache"
        self.cache.mkdir()
        (self.cache / "generated.bin").write_bytes(b"regenerable")

    def tearDown(self):
        self.temp.cleanup()

    def test_boundary_and_symlink_ancestors_rejected(self):
        with self.assertRaises(cleanup.Unsafe):
            cleanup.canonical(self.root, self.root)
        with self.assertRaises(cleanup.Unsafe):
            cleanup.canonical(self.root.parent / "outside", self.root, allow_missing=True)
        link = self.root / "linked"
        link.symlink_to(self.cache, target_is_directory=True)
        with self.assertRaises(cleanup.Unsafe):
            cleanup.canonical(link / "generated.bin", self.root)

    def test_symlink_and_special_cleanup_entries_rejected(self):
        (self.cache / "source-link").symlink_to(self.root / "source")
        with self.assertRaises(cleanup.Unsafe):
            cleanup.inventory(self.cache)
        (self.cache / "source-link").unlink()
        import os
        os.mkfifo(self.cache / "pipe")
        with self.assertRaises(cleanup.Unsafe):
            cleanup.inventory(self.cache)

    def test_tracked_and_protected_intersections_rejected(self):
        source = self.cache / "generated.bin"
        with self.assertRaises(cleanup.Unsafe):
            cleanup.check_intersections(self.cache, {source}, set())
        with self.assertRaises(cleanup.Unsafe):
            cleanup.check_intersections(self.cache, set(), {source})

    def test_changed_candidate_never_unlinked(self):
        target = {"path": str(self.cache), "kind": "generated-directory", "files": cleanup.inventory(self.cache)}
        source = self.cache / "generated.bin"
        source.write_bytes(b"new build became active")
        with patch.object(cleanup, "PROJECT", self.root):
            with self.assertRaises(cleanup.Unsafe):
                cleanup.apply_target(target)
        self.assertEqual(source.read_bytes(), b"new build became active")

    def test_active_handle_never_unlinked(self):
        target = {"path": str(self.cache), "kind": "generated-directory", "files": cleanup.inventory(self.cache)}
        with patch.object(cleanup, "PROJECT", self.root), patch.object(cleanup, "activity", return_value={"openHandles": [1], "processes": []}):
            with self.assertRaises(cleanup.Unsafe):
                cleanup.apply_target(target)
        self.assertTrue((self.cache / "generated.bin").is_file())

    def test_only_exact_planned_tree_removed(self):
        source = self.root / "source"
        source.write_bytes(b"must survive")
        target = {"path": str(self.cache), "kind": "generated-directory", "files": cleanup.inventory(self.cache)}
        with patch.object(cleanup, "PROJECT", self.root), patch.object(cleanup, "activity", return_value={"openHandles": [], "processes": []}):
            result = cleanup.apply_target(target)
        self.assertEqual(result["removedFiles"], 1)
        self.assertFalse(self.cache.exists())
        self.assertEqual(source.read_bytes(), b"must survive")

    def test_protection_hash_drift_and_missing_final_dependency_rejected(self):
        source = self.root / "source"
        source.write_bytes(b"before")
        protection = {"files": {str(source): {"sha256": cleanup.digest(source)}}}
        source.write_bytes(b"after")
        failures = cleanup.verify_protection(protection, {"files": {str(self.root / "missing-final"): "hash"}})
        self.assertEqual(len(failures), 2)

    def test_default_cli_is_dry_run_and_writes_zero_deletions(self):
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        source = self.root / "source"
        source.write_bytes(b"protected")
        protection = self.root / "protected.json"
        protection.write_text(json.dumps({"files": {str(source): {"sha256": cleanup.digest(source)}}}))
        final = self.root / "final.json"
        final.write_text(json.dumps({"files": {str(source): cleanup.digest(source)}}))
        audit = self.root / "audit.json"
        files = cleanup.inventory(self.cache)
        audit.write_text(json.dumps({"protectedInventory": str(protection), "recordedFinalDependencyInventory": str(final),
                                     "safeAllowlist": [{"path": str(self.cache), "files": len(files),
                                                        "logicalBytes": sum(row["bytes"] for row in files)}]}))
        report = self.root / "dry-run.json"
        with patch.object(cleanup, "PROJECT", self.root), patch.object(cleanup, "activity", return_value={"openHandles": [], "processes": []}), patch("sys.argv", ["cleanup", "--audit", str(audit), "--report", str(report)]):
            self.assertEqual(cleanup.main(), 0)
        result = json.loads(report.read_text())
        self.assertEqual(result["status"], "dry-run-reviewed-no-deletion")
        self.assertEqual(result["removedFiles"], 0)
        self.assertTrue((self.cache / "generated.bin").is_file())

    def test_runtime_only_middle_frames_removed_summaries_unchanged(self):
        session = self.root / "output/unreal/runtime/motion-tsr-historical"
        session.mkdir(parents=True)
        for index in range(6):
            (session / ("frame-%03d.png" % index)).write_bytes(bytes([index]))
        summary = session / "motion-qa.json"
        summary.write_text('{"status":"old-success"}')
        with patch.object(cleanup, "PROJECT", self.root), patch.object(cleanup, "activity", return_value={"openHandles": [], "processes": []}):
            target = cleanup.runtime_selection(session, set(), set(), {2})
            result = cleanup.apply_target(target)
        self.assertEqual(result["removedFiles"], 3)
        self.assertEqual([file.name for file in sorted(session.glob("frame-*.png"))], ["frame-000.png", "frame-002.png", "frame-005.png"])
        self.assertEqual(summary.read_text(), '{"status":"old-success"}')
        self.assertEqual(len(list(session.glob("sequence-retention-*.json"))), 1)

    def test_existing_evidence_report_never_overwritten(self):
        source = self.root / "report.json"
        source.write_text("original proof")
        with self.assertRaises(cleanup.Unsafe):
            cleanup.save_new(source, {"changed": True})
        self.assertEqual(source.read_text(), "original proof")

    def test_global_trash_and_foreign_bundle_rejected(self):
        fake_home = self.root / "home"
        trash = fake_home / ".Trash"
        trash.mkdir(parents=True)
        batch = trash / "Dom-old-apps-20261003-r1"
        bundle = batch / "Foreign.app/Contents"
        bundle.mkdir(parents=True)
        import plistlib
        (bundle / "Info.plist").write_bytes(plistlib.dumps({"CFBundleIdentifier": "foreign.needed-app"}))
        with patch.object(cleanup.Path, "home", return_value=fake_home):
            with self.assertRaises(cleanup.Unsafe):
                cleanup.project_trash_selection(trash, set(), set())
            with self.assertRaises(cleanup.Unsafe):
                cleanup.project_trash_selection(batch, set(), set())

    def test_refresh_records_authorized_changes_without_deletion(self):
        source = self.root / "source"
        source.write_bytes(b"before work")
        previous = {"files": {str(source): {"sha256": cleanup.digest(source), "bytes": source.stat().st_size}}}
        source.write_bytes(b"authorized implementation")
        report = self.root / "fresh.json"
        with patch.object(cleanup, "PROJECT", self.root):
            result = cleanup.refresh_protection(previous, report)
        self.assertEqual(len(result["changedSinceAudit"]), 1)
        self.assertEqual(json.loads(report.read_text())["files"][str(source)]["sha256"], cleanup.digest(source))
        self.assertTrue((self.cache / "generated.bin").exists())

    def test_partial_deletion_failure_reports_actual_removed_count(self):
        (self.cache / "second.bin").write_bytes(b"second")
        target = {"path": str(self.cache), "kind": "generated-directory", "files": cleanup.inventory(self.cache)}
        original = cleanup.Path.unlink

        def fail_second(path):
            if path.name == "second.bin":
                raise PermissionError("simulated refusal")
            return original(path)

        with patch.object(cleanup, "PROJECT", self.root), patch.object(cleanup, "activity", return_value={"openHandles": [], "processes": []}), patch.object(cleanup.Path, "unlink", fail_second):
            result = cleanup.apply_target(target)
        self.assertEqual(result["removedFiles"], 1)
        self.assertEqual(result["failureCount"], 1)
        self.assertTrue((self.cache / "second.bin").exists())

    def retention_fixture(self):
        """No live project/app reads: all proof, pins and selectors are temporary."""
        output = self.root / "output/unreal"
        output.mkdir(parents=True)
        (self.root / cleanup.FINAL_PROJECT).mkdir(parents=True)
        for name in ("exterior-final-current.json", "dom-app-current.json"):
            (output / name).write_text('{}')
        retained = self.root / "licensed-original.dat"
        retained.write_bytes(b"keep licensed original")
        retired = output / cleanup.PREDECESSOR_PROJECTS[0] / "Project/BreziTwin/Content/old.dat"
        row = {"sha256": cleanup.digest(retained), "bytes": retained.stat().st_size}
        final = {"files": {str(retained): row["sha256"], str(retired): "historical-scene-hash"}}
        prior = self.root / "immutable-prior.json"
        prior.write_text(json.dumps(final))
        fresh = self.root / "fresh-prior.json"
        historical = {"sha256": "historical-scene-hash", "bytes": 123}
        fresh.write_text(json.dumps({"files": {str(retained): row, str(retired): historical},
                                     "historicalFileMetadata": {str(retained): {"inode": retained.stat().st_ino,
                                         "bytes": retained.stat().st_size, "mtimeNs": retained.stat().st_mtime_ns},
                                         str(retired): {"inode": 1, "bytes": 123, "mtimeNs": 1}},
                                     "allHistoricalExpectedHashesExact": True, "historicalHashMismatches": []}))
        with patch.object(cleanup, "PROJECT", self.root):
            roots = cleanup.retirement_roots()
        manifest = {"status": "single-final-current-closure-and-retirement-verified",
                    "currentProject": str(self.root / cleanup.FINAL_PROJECT),
                    "currentDeclaredSourceExact": True, "retiredProjectRoots": sorted(str(p) for p in roots),
                    "priorOriginalInventoryPath": str(prior), "priorOriginalInventorySha256": cleanup.digest(prior),
                    "priorFreshClosurePath": str(fresh), "priorFreshClosureSha256": cleanup.digest(fresh),
                    "retainedOriginalPins": {str(retained): row}, "retiredOriginalPins": {str(retired): historical},
                    "files": {str(retained): row},
                    "currentSelectionSha256": cleanup.digest(output / "exterior-final-current.json"),
                    "currentAppSelectionSha256": cleanup.digest(output / "dom-app-current.json")}
        return final, manifest, retained, retired, row

    def test_retention_can_only_rebind_exact_proven_predecessor_pin(self):
        final, manifest, retained, retired, row = self.retention_fixture()
        old = {"files": {str(retained): row, str(retired): manifest["retiredOriginalPins"][str(retired)]}}
        destination = self.root / "new-protection.json"
        with patch.object(cleanup, "PROJECT", self.root), patch.object(cleanup, "fresh_current_bindings", return_value=({}, None)):
            result = cleanup.refresh_protection(old, destination, retention=manifest, original_final=final)
        self.assertEqual(result["authorizedHistoricalProjectRetirements"], 1)
        fresh = json.loads(destination.read_text())
        self.assertNotIn(str(retired), fresh["files"])
        self.assertIn(str(retained), fresh["files"])
        self.assertTrue(retained.exists())

    def test_retention_rejects_parent_or_missing_retained_original(self):
        final, manifest, retained, retired, row = self.retention_fixture()
        manifest["retiredProjectRoots"][0] = str(self.root / "output/unreal")
        with patch.object(cleanup, "PROJECT", self.root):
            with self.assertRaises(cleanup.Unsafe):
                cleanup.verify_retention(manifest, final)
        manifest["retiredProjectRoots"] = [str(self.root / "output/unreal" / name / "Project/BreziTwin")
                                           for name in cleanup.PREDECESSOR_PROJECTS]
        manifest["files"] = {}
        with patch.object(cleanup, "PROJECT", self.root):
            with self.assertRaises(cleanup.Unsafe):
                cleanup.verify_retention(manifest, final)

    def test_retention_rejects_current_hash_drift_and_unproven_source(self):
        final, manifest, retained, retired, row = self.retention_fixture()
        retained.write_bytes(b"changed original")
        with patch.object(cleanup, "PROJECT", self.root):
            with self.assertRaises(cleanup.Unsafe):
                cleanup.verify_retention(manifest, final)
        retained.write_bytes(b"keep licensed original")
        unproven = retired.parent / "not-in-original-closure.cpp"
        old = {"files": {str(unproven): {"sha256": "other", "bytes": 5}}}
        with patch.object(cleanup, "PROJECT", self.root), patch.object(cleanup, "fresh_current_bindings", return_value=({}, None)):
            with self.assertRaises(cleanup.Unsafe):
                cleanup.refresh_protection(old, self.root / "must-not-exist.json", retention=manifest, original_final=final)
        self.assertFalse((self.root / "must-not-exist.json").exists())

    def current_final_fixture(self):
        final, manifest, retained, retired, row = self.retention_fixture()
        project = self.root / cleanup.FINAL_PROJECT
        for name in ("Source/BreziTwin", "Config", "Content/Brezi/Maps", "Binaries/Mac"):
            (project / name).mkdir(parents=True)
        startup = self.root / "scripts/unreal/dom-startup-entry.cpp"
        startup.parent.mkdir(parents=True)
        startup.write_bytes(b"approved startup entry")
        authored_startup = project / "Source/BreziTwin/BreziStartupEntry.cpp"
        authored_startup.write_bytes(startup.read_bytes())
        config = project / "Config/DefaultEngine.ini"
        config.write_bytes(b"full design configuration")
        current_map = project / "Content/Brezi/Maps/Brezi.umap"
        current_map.write_bytes(b"accepted unchanged C/B/B map")
        descriptor = project / "BreziTwin.uproject"
        descriptor.write_text('{}')
        executable = project / "Binaries/Mac/BreziTwin"
        executable.write_bytes(b"approved native Shipping executable")
        target = project / "Binaries/Mac/BreziTwin-Mac-Shipping.target"
        target.write_text('{}')
        source_hashes = {"Source": {"BreziTwin/BreziStartupEntry.cpp": cleanup.digest(authored_startup)},
                         "Config": {"DefaultEngine.ini": cleanup.digest(config)},
                         "Content": {"Brezi/Maps/Brezi.umap": cleanup.digest(current_map)}}
        clone = project.parents[1] / "source-clone.json"
        clone.write_text(json.dumps({"sourceHashes": source_hashes, "descriptorSha256": cleanup.digest(descriptor)}))
        game_receipt = project.parents[1] / "model-game-build.json"
        game_receipt.write_text(json.dumps({"status": "model-game-build-validated", "gameConfiguration": "Shipping",
                                           "sourcePins": {str(authored_startup): cleanup.digest(authored_startup)},
                                           "rawExecutable": str(executable), "rawExecutableSha256": cleanup.digest(executable),
                                           "targetReceipt": str(target), "targetReceiptSha256": cleanup.digest(target)}))
        map_row = {"path": str(current_map), "sha256": cleanup.digest(current_map)}
        accepted = self.root / "output/unreal/exterior-final-current.json"
        accepted.write_text(json.dumps({"activeDesign": "C/B/B", "streetAndRightSetbackMm": 3000,
                                       "savedProject": str(descriptor), "launchProject": str(descriptor),
                                       "savedMap": map_row, "launchMap": map_row}))
        package = {"project": str(project), "selection": {"launchMap": map_row}, "renderSourceHashes": {},
                   "sourceCloneReceiptSha256": cleanup.digest(clone), "nativeGameBuildReceiptSha256": cleanup.digest(game_receipt)}
        package_receipt = project.parents[1] / "dom-package.json"
        package_receipt.write_text(json.dumps(package))
        (self.root / "output/unreal/dom-app-current.json").write_text(json.dumps({"packageReceiptPath": str(package_receipt)}))
        return final, manifest, package, project

    def test_prepare_retention_proves_one_final_closure_without_deletion(self):
        final, manifest, package, project = self.current_final_fixture()
        report = self.root / "current-retention.json"
        with patch.object(cleanup, "PROJECT", self.root), patch.object(cleanup, "fresh_current_bindings", return_value=({}, package)):
            cleanup.prepare_retention(final, manifest["priorFreshClosurePath"], report, manifest["priorOriginalInventoryPath"])
        prepared = json.loads(report.read_text())
        self.assertEqual(prepared["status"], "single-final-current-closure-and-retirement-verified")
        self.assertEqual(prepared["deletedFiles"], 0)
        self.assertEqual(len(prepared["retiredOriginalPins"]), 1)
        self.assertIn(str(project / "Content/Brezi/Maps/Brezi.umap"), prepared["files"])
        self.assertTrue((self.cache / "generated.bin").exists())

    def test_prepare_retention_rejects_extra_asset_and_wrong_compiled_binary(self):
        final, manifest, package, project = self.current_final_fixture()
        extra = project / "Content/unapproved.uasset"
        extra.write_bytes(b"unapproved")
        report = self.root / "must-not-exist.json"
        with patch.object(cleanup, "PROJECT", self.root), patch.object(cleanup, "fresh_current_bindings", return_value=({}, package)):
            with self.assertRaises(cleanup.Unsafe):
                cleanup.prepare_retention(final, manifest["priorFreshClosurePath"], report, manifest["priorOriginalInventoryPath"])
            extra.unlink()
            (project / "Binaries/Mac/BreziTwin").write_bytes(b"wrong compiled binary")
            with self.assertRaises(cleanup.Unsafe):
                cleanup.prepare_retention(final, manifest["priorFreshClosurePath"], report, manifest["priorOriginalInventoryPath"])
        self.assertFalse(report.exists())

    def test_current_intermediate_compaction_retains_compiler_inputs(self):
        final, manifest, package, project = self.current_final_fixture()
        generated = project / "Intermediate/Build/generated.h"
        generated.parent.mkdir(parents=True)
        generated.write_bytes(b"required regenerated compiler input")
        object_file = generated.with_suffix(".o")
        object_file.write_bytes(b"regenerable cached object")
        game_path = project.parents[1] / "model-game-build.json"
        game = json.loads(game_path.read_text())
        game["sourcePins"][str(generated)] = cleanup.digest(generated)
        game_path.write_text(json.dumps(game))
        package["nativeGameBuildReceiptSha256"] = cleanup.digest(game_path)
        report = self.root / "current-retention.json"
        with patch.object(cleanup, "PROJECT", self.root), patch.object(cleanup, "fresh_current_bindings", return_value=({}, package)):
            cleanup.prepare_retention(final, manifest["priorFreshClosurePath"], report, manifest["priorOriginalInventoryPath"])
            prepared = json.loads(report.read_text())
            pins = {Path(name) for name in prepared["files"]}
            selection = cleanup.current_intermediate_selection(pins, set(), prepared)
            self.assertEqual([row["path"] for row in selection["files"]], [str(object_file)])
            with patch.object(cleanup, "activity", return_value={"openHandles": [], "processes": []}):
                removed = cleanup.apply_target(selection)
        self.assertEqual(removed["removedFiles"], 1)
        self.assertTrue(generated.exists())
        self.assertFalse(object_file.exists())
        self.assertEqual(len(list(project.parents[1].glob("generated-compile-input-retention-*.json"))), 1)

    def test_current_intermediate_compaction_needs_pinned_verified_inputs(self):
        with patch.object(cleanup, "PROJECT", self.root):
            with self.assertRaises(cleanup.Unsafe):
                cleanup.current_intermediate_selection(set(), set(), {"files": {}})

    def test_retention_rejects_historical_pin_changed_after_full_snapshot(self):
        final, manifest, retained, retired, row = self.retention_fixture()
        retired.parent.mkdir(parents=True)
        retired.write_bytes(b"new historical work after the snapshot")
        with patch.object(cleanup, "PROJECT", self.root):
            with self.assertRaises(cleanup.Unsafe):
                cleanup.verify_retention(manifest, final)
        self.assertTrue(retired.exists())

    def test_final_project_override_cannot_select_foreign_or_retired_tree(self):
        foreign = self.root / "foreign-project"
        foreign.mkdir()
        retired = self.root / "output/unreal/dom-app-20261003-performance-r1/Project/BreziTwin"
        retired.mkdir(parents=True)
        for override in (str(foreign), str(retired)):
            with patch.object(cleanup, "PROJECT", self.root), patch.dict(cleanup.os.environ, {"DOM_FINAL_PROJECT": override}):
                with self.assertRaises(cleanup.Unsafe):
                    cleanup.final_project()

    def test_audited_raw_originals_are_bound_and_changed_originals_rejected(self):
        original = self.root / "licensed-original.png"
        original.write_bytes(b"retained original image")
        proof = self.root / "original-proof.json"
        proof.write_text(json.dumps({
            "status": "r5-whole-project-retirement-proven-no-deletion", "deletedFiles": 0,
            "legacyProject": str(self.root / "output/unreal/exterior-20260930-r5/Project/BreziTwin"),
            "retainedInputs": {str(original): {"sha256": cleanup.digest(original), "bytes": original.stat().st_size}}}))
        with patch.object(cleanup, "PROJECT", self.root):
            files, reports = cleanup.retained_input_files([proof], cleanup.retirement_roots())
            self.assertIn(str(original), files)
            self.assertIn(str(proof), files)
            self.assertEqual(reports[0]["retainedInputs"][str(original)], files[str(original)])
            original.write_bytes(b"changed original after audit")
            with self.assertRaises(cleanup.Unsafe):
                cleanup.retained_input_files([proof], cleanup.retirement_roots())

    def test_audited_raw_original_cannot_be_under_retired_scene(self):
        retired = self.root / "output/unreal/exterior-20260930-r5/Project/BreziTwin/Content/only.uasset"
        retired.parent.mkdir(parents=True)
        retired.write_bytes(b"cannot retire sole input")
        proof = self.root / "original-proof.json"
        proof.write_text(json.dumps({
            "status": "r5-whole-project-retirement-proven-no-deletion", "deletedFiles": 0,
            "legacyProject": str(retired.parents[1]),
            "retainedInputs": {str(retired): {"sha256": cleanup.digest(retired), "bytes": retired.stat().st_size}}}))
        with patch.object(cleanup, "PROJECT", self.root):
            with self.assertRaises(cleanup.Unsafe):
                cleanup.retained_input_files([proof], cleanup.retirement_roots())

    def test_whole_r5_retirement_requires_original_proof_and_superseded_fallback(self):
        r5 = self.root / "output/unreal/exterior-20260930-r5/Project/BreziTwin"
        selector = self.root / "output/unreal/model-refresh-current.json"
        selector.parent.mkdir(parents=True)
        selector.write_text(json.dumps({"status": "current-model-visually-reviewed"}))
        proof = self.root / "original-proof.json"
        proof.write_text(json.dumps({"legacyProject": str(r5)}))
        final = {"status": "single-final-current-closure-and-retirement-verified",
                 "additionalRetainedInputReports": [{"path": str(proof)}]}
        with patch.object(cleanup, "PROJECT", self.root):
            with self.assertRaises(cleanup.Unsafe):
                cleanup.check_retired_authoring_target(r5, {"files": {}})
            with self.assertRaises(cleanup.Unsafe):
                cleanup.check_retired_authoring_target(r5, {**final, "additionalRetainedInputReports": []})
            with self.assertRaises(cleanup.Unsafe):
                cleanup.check_retired_authoring_target(r5, final)
            selector.write_text(json.dumps({"status": "superseded-by-installed-dom"}))
            cleanup.check_retired_authoring_target(r5, final)

    def test_only_exact_audited_generated_xcode_pair_rebinds(self):
        paths = [self.root / name for name in cleanup.POST_PACKAGE_XCODE_REBINDS]
        source = self.root / "Source/authored.cpp"
        source.parent.mkdir()
        source.write_bytes(b"compiled source unchanged")
        pins = {str(source): cleanup.digest(source)}
        approved = {}
        for path in paths:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"before native build")
            before = cleanup.digest(path)
            pins[str(path)] = before
            path.write_bytes(b"UAT regenerated exact file")
            approved[str(path.relative_to(self.root))] = (before, cleanup.digest(path))
        with patch.object(cleanup, "PROJECT", self.root), patch.object(cleanup, "POST_PACKAGE_XCODE_REBINDS", approved):
            current, rebinds = cleanup.current_compiler_pins({"sourcePins": pins})
            self.assertEqual(len(rebinds), 2)
            self.assertEqual(current[str(source)], pins[str(source)])
            source.write_bytes(b"unrelated authored code drift")
            with self.assertRaises(cleanup.Unsafe):
                cleanup.current_compiler_pins({"sourcePins": pins})
            source.write_bytes(b"compiled source unchanged")
            paths[0].write_bytes(b"unapproved third generated value")
            with self.assertRaises(cleanup.Unsafe):
                cleanup.current_compiler_pins({"sourcePins": pins})

    def test_xcode_rebind_requires_shipping_target_scheme_and_uat_interval(self):
        import os
        project = self.root / cleanup.FINAL_PROJECT
        xcode = project / "Intermediate/ProjectFilesMac/BreziTwin (Mac).xcodeproj"
        scheme = xcode / "xcshareddata/xcschemes/BreziTwin.xcscheme"
        scheme.parent.mkdir(parents=True)
        pbx = xcode / "project.pbxproj"
        pbx.write_text('{ configuration = "BreziTwin_Shipping.xcconfig"; }')
        scheme.write_text('<Scheme><ArchiveAction buildConfiguration="Shipping"/><BuildableReference BlueprintName="BreziTwin" BuildableName="BreziTwin.app" ReferencedContainer="container:BreziTwin (Mac).xcodeproj"/></Scheme>')
        target = project / "target.json"
        target.write_text(json.dumps({"TargetName": "BreziTwin", "Platform": "Mac", "Configuration": "Shipping"}))
        log = project.parents[1] / "package.log"
        log.write_text("Writing xcode workspace " + str(project / "Intermediate/ProjectFiles/BreziTwin_Mac_BreziTwin.xcworkspace") + "\nWriting project files... 100%")
        for path in (pbx, scheme):
            os.utime(path, (10, 10))
        game = {"targetReceipt": str(target), "endedAt": "1970-01-01T00:00:09+00:00"}
        packaged = {"createdAt": "1970-01-01T00:00:11+00:00"}
        rows = [{"path": str(path)} for path in (pbx, scheme)]
        proof = cleanup.validate_xcode_rebind(game, packaged, project, rows)
        self.assertTrue(proof["currentShippingSchemeValidated"])
        os.utime(scheme, (12, 12))
        with self.assertRaises(cleanup.Unsafe):
            cleanup.validate_xcode_rebind(game, packaged, project, rows)
        target.write_text(json.dumps({"TargetName": "BreziTwin", "Platform": "Mac", "Configuration": "Development"}))
        with self.assertRaises(cleanup.Unsafe):
            cleanup.validate_xcode_rebind(game, packaged, project, rows)


if __name__ == "__main__":
    unittest.main()
