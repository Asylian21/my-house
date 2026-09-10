"""Filesystem restoration tests; no existing output cache or native assets touched."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

import restore_inputs as helper


class RestoreFurnitureInputsTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="brezi-furniture-input-test-")
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.destination = self.base / "study"
        self.data = helper.checked_file(helper.INPUT)

    def test_canonical_snapshot_matches_existing_contract(self):
        self.assertEqual(len(self.data), 69631)
        self.assertEqual(hashlib.sha256(self.data).hexdigest(), helper.CANDIDATE_SHA)
        self.assertEqual(len(json.loads(self.data)["scope"]["photoOverrideIds"]), 9)

    def test_missing_destination_restores_exact_bytes(self):
        result = helper.restore(self.destination)
        self.assertEqual(result["action"], "restored-recipe")
        self.assertFalse(result["nativeImportPerformed"])
        self.assertEqual((self.destination / "candidate.json").read_bytes(), self.data)
        self.assertEqual([p.name for p in self.destination.iterdir()], ["candidate.json"])

    def test_existing_valid_file_retains_inode_and_mtime(self):
        helper.restore(self.destination)
        target = self.destination / "candidate.json"
        before = target.stat()
        result = helper.restore(self.destination)
        after = target.stat()
        self.assertEqual(result["action"], "verified-existing")
        self.assertEqual((before.st_ino, before.st_mtime_ns), (after.st_ino, after.st_mtime_ns))

    def test_conflicting_same_size_file_is_not_replaced(self):
        self.destination.mkdir()
        target = self.destination / "candidate.json"
        different = bytes([self.data[0] ^ 1]) + self.data[1:]
        target.write_bytes(different)
        with self.assertRaisesRegex(ValueError, "bytes differ"):
            helper.restore(self.destination)
        self.assertEqual(target.read_bytes(), different)

    def test_truncated_file_is_not_replaced(self):
        self.destination.mkdir()
        target = self.destination / "candidate.json"
        target.write_bytes(b"partial")
        with self.assertRaisesRegex(ValueError, "byte count"):
            helper.restore(self.destination)
        self.assertEqual(target.read_bytes(), b"partial")

    def test_existing_and_dangling_target_symlinks_are_rejected(self):
        self.destination.mkdir()
        outside = self.base / "outside.json"
        target = self.destination / "candidate.json"
        for exists in (False, True):
            with self.subTest(existing_target=exists):
                if exists:
                    outside.write_bytes(self.data)
                target.symlink_to(outside)
                with self.assertRaisesRegex(ValueError, "symlink"):
                    helper.restore(self.destination)
                self.assertTrue(target.is_symlink())
                self.assertEqual(outside.exists(), exists)
                target.unlink()

    def test_symlink_destination_directory_is_rejected(self):
        outside = self.base / "outside"
        outside.mkdir()
        self.destination.symlink_to(outside, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlink"):
            helper.restore(self.destination)
        self.assertEqual(list(outside.iterdir()), [])

    def test_directory_at_file_path_is_rejected(self):
        (self.destination / "candidate.json").mkdir(parents=True)
        with self.assertRaisesRegex(ValueError, "regular file"):
            helper.restore(self.destination)

    def test_bad_canonical_snapshot_fails_before_destination_creation(self):
        bad = self.base / "bad-input.json"
        bad.write_bytes(bytes([self.data[0] ^ 1]) + self.data[1:])
        with mock.patch.object(helper, "INPUT", bad):
            with self.assertRaisesRegex(ValueError, "bytes differ"):
                helper.restore(self.destination)
        self.assertFalse(self.destination.exists())

    def test_symlink_canonical_snapshot_is_rejected(self):
        link = self.base / "input-link.json"
        link.symlink_to(helper.INPUT)
        with mock.patch.object(helper, "INPUT", link):
            with self.assertRaisesRegex(ValueError, "symlink"):
                helper.restore(self.destination)
        self.assertFalse(self.destination.exists())

    def test_concurrent_conflict_is_not_overwritten_and_temporary_is_removed(self):
        def competitor(source, target):
            Path(target).write_bytes(b"competing writer")
            raise FileExistsError()
        with mock.patch.object(helper.os, "link", side_effect=competitor):
            with self.assertRaises(ValueError):
                helper.restore(self.destination)
        self.assertEqual((self.destination / "candidate.json").read_bytes(), b"competing writer")
        self.assertEqual([p.name for p in self.destination.iterdir()], ["candidate.json"])

    def test_concurrent_identical_publication_is_verified(self):
        def competitor(source, target):
            Path(target).write_bytes(self.data)
            raise FileExistsError()
        with mock.patch.object(helper.os, "link", side_effect=competitor):
            result = helper.restore(self.destination)
        self.assertEqual(result["action"], "verified-concurrent-existing")
        self.assertEqual([p.name for p in self.destination.iterdir()], ["candidate.json"])

    def test_cli_runs_from_another_working_directory(self):
        result = subprocess.run([sys.executable, str(Path(helper.__file__).resolve()),
                                 "--destination", str(self.destination)], cwd=self.base,
                                capture_output=True, text=True, check=True,
                                env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["sha256"], helper.CANDIDATE_SHA)
        self.assertEqual(receipt["action"], "restored-recipe")


if __name__ == "__main__":
    unittest.main(verbosity=2)
