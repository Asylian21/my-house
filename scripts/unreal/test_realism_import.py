"""Fail-closed additive authoring boundaries; no Unreal process is launched."""
import copy
import importlib.util
from pathlib import Path
import json
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location('realism_import', Path(__file__).with_name('realism-import.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class RealismImportTests(unittest.TestCase):
    def before(self):
        return {'actor': {'tags': ['DOM_001'], 'transform': [1, 2, 3], 'components': [
            {'path': 'component', 'mesh': '/Game/Source.Mesh', 'materials': ['/Game/Old.Old'],
             'collision': 'QUERY_AND_PHYSICS', 'orderedInstanceTransformsSha256': 'instances'}]}}

    def delta(self):
        return [{'actor': 'actor', 'component': 'component', 'slot': 0,
                 'before': '/Game/Old.Old', 'after': '/Game/Brezi/Realism/M.M'}]

    def test_only_declared_material_slot_changes_are_allowed(self):
        original = self.before()
        expected = M.expected_witness(original, self.delta())
        self.assertEqual(original, self.before())
        M.verify_witness(expected, expected, [])
        for key, value in [('mesh', 'changed'), ('collision', 'NONE'), ('orderedInstanceTransformsSha256', 'changed')]:
            actual = copy.deepcopy(expected)
            actual['actor']['components'][0][key] = value
            with self.subTest(key=key), self.assertRaisesRegex(RuntimeError, 'Protected actor'):
                M.verify_witness(expected, actual, [])

    def test_unknown_duplicate_stale_and_outside_material_bindings_rejected(self):
        for key, value in [('actor', 'foreign'), ('component', 'foreign'), ('slot', 2), ('before', 'stale'), ('after', '/Game/Source.M')]:
            changes = self.delta()
            changes[0][key] = value
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                M.expected_witness(self.before(), changes)
        with self.assertRaisesRegex(RuntimeError, 'Duplicate'):
            M.expected_witness(self.before(), self.delta() + self.delta())

    def test_added_actors_must_be_owned_reported_and_collisionless(self):
        original = self.before()
        new = {'tags': [M.TAG], 'components': [{'collision': 'NO_COLLISION', 'navigation': False}]}
        M.verify_witness(original, {**original, 'cloud': new}, ['cloud'])
        for changed in [{'tags': [], 'components': []}, {'tags': [M.TAG, 'DOM_2'], 'components': []},
                        {'tags': [M.TAG], 'components': [{'collision': 'NO_COLLISION', 'navigation': True}]}]:
            with self.assertRaises(RuntimeError):
                M.verify_witness(original, {**original, 'cloud': changed}, ['cloud'])
        with self.assertRaisesRegex(RuntimeError, 'Unreported'):
            M.verify_witness(original, {**original, 'cloud': new}, [])

    def test_content_allows_only_map_and_new_owned_packages(self):
        content = Path('/project/Content')
        before = {str(content / M.MAP_FILE): 'map', str(content / 'mesh.uasset'): 'mesh'}
        after = {**before, str(content / M.MAP_FILE): 'new', str(content / 'Brezi/Realism/M.uasset'): 'new'}
        M.validate_changes(before, after, content)
        for changed in [{**after, str(content / 'mesh.uasset'): 'changed'}, {**after, str(content / 'Foreign.uasset'): 'x'},
                        {**after, str(content / 'Brezi/Realism/file.py'): 'x'}, {k: v for k, v in after.items() if k != str(content / 'mesh.uasset')}]:
            with self.assertRaises(RuntimeError):
                M.validate_changes(before, changed, content)

    def restore_fixture(self, tmp):
        source, output = Path(tmp).resolve() / 'donor', Path(tmp).resolve() / 'candidate'
        content = output / 'Project/BreziTwin/Content'
        donor = source / 'Project/BreziTwin/Content'
        for base in (content, donor):
            (base / 'Brezi/Maps').mkdir(parents=True)
            (base / M.MAP_FILE).write_bytes(b'original map')
            (base / 'mesh.uasset').write_bytes(b'original mesh')
        before = M.inventory(content)
        (output / 'realism-checkpoint').mkdir()
        (output / 'realism-checkpoint/Brezi.umap').write_bytes(b'original map')
        (content / M.MAP_FILE).write_bytes(b'failed map')
        (content / 'Brezi/Realism').mkdir()
        (content / 'Brezi/Realism/M.uasset').write_bytes(b'new material')
        report = {'status': 'failed', 'sourceOutput': str(source), 'output': str(output),
                  'project': str(output / 'Project/BreziTwin'), 'nativeProcessId': 123,
                  'beforeAssetHashes': before, 'failedContentHashes': M.inventory(content)}
        M.write(output / 'realism-import-report.json', report)
        M.write(output / 'performance-source.json', {'content': before})
        return output, content, before

    def test_failed_restore_preserves_failed_map_assets_report_and_restores_exact_content(self):
        with tempfile.TemporaryDirectory() as tmp:
            output, content, before = self.restore_fixture(tmp)
            helper = SimpleNamespace(checked_paths=lambda source, target: (Path(source), target))
            with patch.object(M, 'module', return_value=helper), patch.object(M.os, 'kill', side_effect=ProcessLookupError):
                M.restore(output)
            self.assertEqual(M.inventory(content), before)
            self.assertFalse((output / 'realism-import-report.json').exists())
            self.assertFalse((output / 'realism-checkpoint').exists())
            history = list((output / 'realism-history').iterdir())
            self.assertEqual(len(history), 1)
            self.assertEqual((history[0] / 'failed-Brezi.umap').read_bytes(), b'failed map')
            self.assertEqual((history[0] / 'failed-assets/Brezi/Realism/M.uasset').read_bytes(), b'new material')
            self.assertEqual(json.loads((history[0] / 'realism-import-report.json').read_text())['status'], 'failed')

    def test_restore_refuses_live_process_or_changed_content_without_mutation(self):
        for active in (True, False):
            with self.subTest(active=active), tempfile.TemporaryDirectory() as tmp:
                output, content, _ = self.restore_fixture(tmp)
                if not active:
                    (content / 'Brezi/Realism/M.uasset').write_bytes(b'drifted material')
                prior = M.inventory(output)
                helper = SimpleNamespace(checked_paths=lambda source, target: (Path(source), target))
                with patch.object(M, 'module', return_value=helper), patch.object(M.os, 'kill', side_effect=None if active else ProcessLookupError):
                    with self.assertRaisesRegex(RuntimeError, 'still running|changed after'):
                        M.restore(output)
                self.assertEqual(M.inventory(output), prior)


if __name__ == '__main__':
    unittest.main()
