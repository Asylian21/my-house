"""Exercise actual package recovery with temporary byte-addressed asset trees.

These tests never import Unreal or touch the active project. They verify the
security/data-preservation boundary, not the material implementation.
"""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('photoreal_import',Path(__file__).with_name('photoreal-import.py'))
M=importlib.util.module_from_spec(spec);spec.loader.exec_module(M)


class PhotorealCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
        self.root_patch=patch.object(M,'ROOT',self.root);self.root_patch.start()
        self.output=self.root/'output/unreal/photoreal-test';self.content=self.output/'Project/BreziTwin/Content/Brezi'
        self.map=self.file('Maps/Brezi.umap',b'accepted-closed-map')
        self.mesh=self.file('Geometry/Wall.uasset',b'protected-source-geometry')
        self.collision=self.file('Geometry/HiddenCollision.uasset',b'protected-collision')
        self.material=self.file('ModelRefresh/Materials/M_Wall.uasset',b'protected-source-material')
        self.bulk=self.file('Archviz/Textures/T_Wood.ubulk',b'protected-original-scan-data')
        self.baseline=M.inventory(self.content)
        self.checkpoint=self.output/'photoreal-checkpoint';self.checkpoint.mkdir()
        self.backup=self.checkpoint/'Brezi.umap';self.backup.write_bytes(self.map.read_bytes())
        self.state={'owner':M.OWNER,'status':'in-progress','nativeProcessId':123456789,'baselineInventory':self.baseline}

    def tearDown(self):
        self.root_patch.stop();self.temp.cleanup()

    def file(self,relative,content):
        path=self.content/relative;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(content);return path

    def record_failure(self):
        self.map.write_bytes(b'partially-authored-map')
        self.added=self.file('Photoreal/Exterior/Materials/M_Wood.uasset',b'owned-new-material')
        self.state.update(status='failed-recoverable',failedInventory=M.inventory(self.content))
        M.write(self.checkpoint/'state.json',self.state)

    def restore(self):
        with patch.object(M.os,'kill',side_effect=ProcessLookupError):M.restore(self.output)

    def assert_failed_without_changes(self,pattern):
        before=M.inventory(self.content)
        state=(self.checkpoint/'state.json').read_bytes()
        with self.assertRaisesRegex(RuntimeError,pattern):self.restore()
        self.assertEqual(M.inventory(self.content),before)
        self.assertEqual((self.checkpoint/'state.json').read_bytes(),state)

    def test_map_and_owned_additions_are_allowed(self):
        self.record_failure()
        self.file('Photoreal/Exterior/Textures/T_Grain.uexp',b'owned-export')
        self.file('Photoreal/Exterior/Textures/T_Grain.ubulk',b'owned-bulk')
        M.validate_changes(self.baseline,M.inventory(self.content),self.content)

    def test_every_existing_package_class_remains_immutable(self):
        for path in [self.mesh,self.collision,self.material,self.bulk]:
            original=path.read_bytes()
            with self.subTest(path=path.name):
                path.write_bytes(b'protected-package-mutation')
                with self.assertRaisesRegex(RuntimeError,'Protected package changed'):
                    M.validate_changes(self.baseline,M.inventory(self.content),self.content)
            path.write_bytes(original)

    def test_deleting_source_geometry_is_rejected(self):
        self.mesh.unlink()
        with self.assertRaisesRegex(RuntimeError,'Removed a baseline asset'):
            M.validate_changes(self.baseline,M.inventory(self.content),self.content)

    def test_new_assets_require_exact_photoreal_namespace(self):
        for relative in ['Geometry/Unrelated.uasset','Maps/Other.umap','PhotorealSibling/M_Wood.uasset','Archviz/Textures/Extra.ubulk']:
            with self.subTest(path=relative):
                path=self.file(relative,b'unknown-package')
                with self.assertRaisesRegex(RuntimeError,'New asset outside Photoreal'):
                    M.validate_changes(self.baseline,M.inventory(self.content),self.content)
                path.unlink()

    def test_recovery_restores_map_deletes_only_owned_additions(self):
        self.record_failure();self.restore()
        self.assertEqual(M.inventory(self.content),self.baseline)
        self.assertFalse(self.added.exists())
        self.assertEqual(self.mesh.read_bytes(),b'protected-source-geometry')
        self.assertEqual(M.read(self.checkpoint/'state.json')['status'],'restored')

    def test_recovery_refuses_later_map_or_asset_drift(self):
        for target in ['map','new']:
            with self.subTest(target=target):
                self.record_failure()
                path=self.map if target=='map' else self.added
                path.write_bytes(b'unknown-concurrent-later-write')
                self.assert_failed_without_changes('Assets changed after failure')

    def test_recovery_refuses_protected_mutation_recorded_in_failed_inventory(self):
        self.mesh.write_bytes(b'invalid-altered-source');self.record_failure()
        self.assert_failed_without_changes('Protected package changed')

    def test_recovery_refuses_new_unknown_package_even_if_failure_inventory_matches(self):
        self.file('Geometry/Unrelated.uasset',b'not-owned');self.record_failure()
        self.assert_failed_without_changes('New asset outside Photoreal')

    def test_recovery_refuses_changed_checkpoint_map(self):
        self.record_failure();self.backup.write_bytes(b'not-the-accepted-map')
        self.assert_failed_without_changes('Backup map differs')

    def test_recovery_refuses_live_native_process_before_mutation(self):
        self.record_failure();before=M.inventory(self.content)
        with patch.object(M.os,'kill',return_value=None),self.assertRaisesRegex(RuntimeError,'Native process is still running'):
            M.restore(self.output)
        self.assertEqual(M.inventory(self.content),before)

    def test_successful_or_unknown_checkpoint_is_never_rolled_back(self):
        self.record_failure()
        for status in ['complete','in-progress','failed-protected-drift']:
            with self.subTest(status=status):
                self.state['status']=status;M.write(self.checkpoint/'state.json',self.state)
                self.assert_failed_without_changes('No recoverable recorded failure')

    def test_restore_cannot_target_directory_outside_output_unreal(self):
        with self.assertRaisesRegex(RuntimeError,'Output outside workspace'):
            M.restore(self.root/'other-project')


if __name__=='__main__':unittest.main()
