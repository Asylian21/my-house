"""Room overlay guards execute without starting Unreal or Blender."""
import copy
import importlib.util
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('room_import', Path(__file__).with_name('realism-room-details-import.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class RoomDetailTests(unittest.TestCase):
    def fixture(self):
        flags = {name: True for name in M.RENDER_FLAGS}
        passes = {name: True for name in M.PASS_FLAGS}
        original = {id_: {'tags': [id_], 'components': [{'path': id_ + '.component', 'mesh': id_ + '.mesh', 'materials': ['old'],
                    'visible': True, 'hiddenInGame': False, 'renderFlags': flags, 'passFlags': passes, 'transform': [1, 2, 3],
                    'collision': 'QUERY_ONLY', 'mobility': 'MOVABLE' if id_ in M.MOTION_IDS else 'STATIC', 'attachParent': None}]}
                    for id_ in M.SOURCE_IDS}
        changes = [{'sourceId': id_, 'actor': id_, 'component': id_ + '.component',
                    'before': {'visible': True, 'hiddenInGame': False, 'renderFlags': flags, 'passFlags': passes},
                    'after': {'visible': id_ in M.MOTION_IDS, 'hiddenInGame': id_ not in M.MOTION_IDS,
                              'passFlags': {name: False for name in M.PASS_FLAGS} if id_ in M.MOTION_IDS else passes,
                              'renderFlags': {name: False for name in M.RENDER_FLAGS}}} for id_ in M.HIDDEN_IDS]
        return original, changes

    def test_moving_source_visibility_retained_countertop_untouched(self):
        before, changes = self.fixture()
        expected = M.expected_witness(before, changes)
        self.assertEqual(expected['DOM_00740'], before['DOM_00740'])
        for id_ in M.HIDDEN_IDS:
            component = expected[id_]['components'][0]
            self.assertEqual(component['visible'], id_ in M.MOTION_IDS)
            self.assertEqual(component['hiddenInGame'], id_ not in M.MOTION_IDS)
            self.assertEqual(component['passFlags'], {name: id_ not in M.MOTION_IDS for name in M.PASS_FLAGS})
            for key in ('collision','mobility','mesh','materials','transform','attachParent'):
                self.assertEqual(component[key], before[id_]['components'][0][key])
        self.assertFalse(before[M.HIDDEN_IDS[0]]['components'][0]['hiddenInGame'])

    def test_disabling_door_visibility_or_hiding_countertop_fails(self):
        for mutate in [lambda changes: changes.append({**changes[0], 'sourceId': 'DOM_00740'}),
                       lambda changes: changes[3]['after'].update(visible=False),
                       lambda changes: changes[3]['after'].update(hiddenInGame=True),
                       lambda changes: changes[3]['after']['passFlags'].update(render_in_depth_pass=True)]:
            before, changes = self.fixture()
            mutate(changes)
            with self.assertRaises(RuntimeError):
                M.expected_witness(before, changes)

    def test_protected_witness_rejects_material_collision_motion_or_tag_change(self):
        before, changes = self.fixture()
        expected = M.expected_witness(before, changes)
        for field, value in [('materials', ['new']), ('collision', 'NO_COLLISION'), ('mobility', 'STATIC'),
                             ('transform', [5, 6, 7]), ('attachParent', 'different')]:
            after = copy.deepcopy(expected)
            after[M.MOTION_IDS[0]]['components'][0][field] = value
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                M.verify_witness(expected, after, [])
        after = copy.deepcopy(expected)
        after[M.MOTION_IDS[0]]['tags'] = []
        with self.assertRaises(RuntimeError):
            M.verify_witness(expected, after, [])

    def test_only_room_namespace_and_map_can_change(self):
        content = Path('/project/Content')
        before = {str(content / M.MAP_FILE): 'map', str(content / 'Brezi/Realism/Fixtures/Sink.uasset'): 'old'}
        after = {**before, str(content / M.MAP_FILE): 'new', str(content / 'Brezi/Realism/RoomDetails/New.uasset'): 'new'}
        M.validate_changes(before, after, content)
        for path in ['Brezi/Realism/Fixtures/Sink.uasset', 'Brezi/Realism/Other/New.uasset', 'Brezi/Realism/RoomDetails/script.py']:
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                M.validate_changes(before, {**after, str(content / path): 'changed'}, content)

    def test_new_visual_actor_requires_owner_no_source_tag_no_collision(self):
        before, _ = self.fixture()
        new = {'tags': [M.TAG], 'components': [{'collision': 'NO_COLLISION', 'navigation': False}]}
        M.verify_witness(before, {**before, 'new': new}, ['new'])
        for tags in [[], [M.TAG, 'DOM_00941']]:
            with self.assertRaises(RuntimeError):
                M.verify_witness(before, {**before, 'new': {**new, 'tags': tags}}, ['new'])

    def test_failed_restore_archives_evidence_and_refuses_running_or_drifted_state(self):
        for state in ('ready', 'running', 'drifted'):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp).resolve()
                source, output = root / 'source', root / 'target'
                content = output / 'Project/BreziTwin/Content'
                donor = source / 'Project/BreziTwin/Content'
                for folder in (content, donor):
                    (folder / 'Brezi/Maps').mkdir(parents=True)
                    (folder / M.MAP_FILE).write_bytes(b'original map')
                before = M.inventory(content)
                (output / 'realism-room-details-checkpoint').mkdir()
                (output / 'realism-room-details-checkpoint/Brezi.umap').write_bytes(b'original map')
                (content / M.MAP_FILE).write_bytes(b'failed map')
                new = content / 'Brezi/Realism/RoomDetails/New.uasset'
                new.parent.mkdir(parents=True)
                new.write_bytes(b'failed new mesh')
                M.write(output / 'realism-room-details-report.json', {'status': 'failed', 'output': str(output), 'sourceOutput': str(source),
                    'nativeProcessId': 123, 'beforeAssetHashes': before, 'failedContentHashes': M.inventory(content)})
                M.write(output / 'performance-source.json', {'content': before})
                if state == 'drifted':
                    new.write_bytes(b'changed later')
                prior = M.inventory(output)
                helper = SimpleNamespace(checked_paths=lambda source, output: (Path(source), output))
                with patch.object(M, 'module', return_value=helper), patch.object(M.os, 'kill', side_effect=None if state == 'running' else ProcessLookupError):
                    if state == 'ready':
                        M.restore(output)
                        self.assertEqual(M.inventory(content), before)
                        self.assertFalse((output / 'realism-room-details-report.json').exists())
                        history = list((output / 'realism-room-details-history').iterdir())
                        self.assertEqual(len(history), 1)
                        self.assertEqual((history[0] / 'failed-Brezi.umap').read_bytes(), b'failed map')
                        self.assertEqual((history[0] / 'failed-assets/Brezi/Realism/RoomDetails/New.uasset').read_bytes(), b'failed new mesh')
                    else:
                        with self.assertRaises(RuntimeError):
                            M.restore(output)
                        self.assertEqual(M.inventory(output), prior)


if __name__ == '__main__':
    unittest.main()
