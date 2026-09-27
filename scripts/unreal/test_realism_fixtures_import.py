"""Fixture-only native migration guards; no Blender/Unreal process is launched."""
import copy
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('fixture_import', Path(__file__).with_name('realism-fixtures-import.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class FixtureTests(unittest.TestCase):
    def fixture(self):
        flags = {name: True for name in M.RENDER_FLAGS}
        before = {id_: {'tags': [id_], 'components': [{'path': id_ + '.component', 'mesh': id_ + '.mesh', 'materials': ['steel'],
                   'visible': True, 'hiddenInGame': False, 'renderFlags': flags, 'transform': [1, 2, 3], 'collision': 'QUERY_ONLY'}]} for id_ in M.SOURCE_IDS}
        changes = [{'sourceId': id_, 'actor': id_, 'component': id_ + '.component',
                    'before': {'visible': True, 'hiddenInGame': False, 'renderFlags': flags},
                    'after': {'visible': False, 'hiddenInGame': True, 'renderFlags': {name: False for name in M.RENDER_FLAGS}}} for id_ in M.SOURCE_IDS]
        return before, changes

    def test_only_exact_eight_component_render_properties_change(self):
        before, changes = self.fixture()
        expected = M.expected_witness(before, changes)
        self.assertTrue(before[M.SOURCE_IDS[0]]['components'][0]['visible'])
        M.verify_witness(expected, expected, [])
        for field, value in [('mesh', 'other'), ('transform', [2, 3, 4]), ('collision', 'NONE'), ('materials', ['other'])]:
            changed = copy.deepcopy(expected)
            changed[M.SOURCE_IDS[0]]['components'][0][field] = value
            with self.subTest(field=field), self.assertRaisesRegex(RuntimeError, 'Original geometry'):
                M.verify_witness(expected, changed, [])

    def test_bounded_fabric_binding_deltas_are_applied_without_other_mutations(self):
        before, changes = self.fixture()
        before['cloth'] = {'tags': ['old'], 'components': [{'path': 'cloth.component', 'materials': ['old-cloth']}]}
        delta = {'actor': 'cloth', 'component': 'cloth.component', 'slot': 0, 'before': 'old-cloth', 'after': '/Game/Brezi/Realism/Fabric/M.M'}
        expected = M.expected_witness(before, changes, [delta])
        self.assertEqual(expected['cloth']['components'][0]['materials'], [delta['after']])
        self.assertEqual(before['cloth']['components'][0]['materials'], ['old-cloth'])
        for key, value in [('before', 'stale'), ('after', '/Game/Foreign.M'), ('slot', 3)]:
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                M.expected_witness(before, changes, [{**delta, key: value}])

    def test_visibility_scope_and_repeated_source_must_fail(self):
        before, changes = self.fixture()
        with self.assertRaisesRegex(RuntimeError, 'scope'):
            M.expected_witness(before, changes[:-1])
        changes[0]['component'] = changes[1]['component']
        with self.assertRaises(RuntimeError):
            M.expected_witness(before, changes)

    def test_new_visuals_require_owner_tag_and_no_collision_or_navigation(self):
        original, _ = self.fixture()
        new = {'tags': [M.TAG], 'components': [{'collision': 'NO_COLLISION', 'navigation': False}]}
        M.verify_witness(original, {**original, 'new': new}, ['new'])
        for value in [{'tags': [], 'components': []}, {'tags': [M.TAG], 'components': [{'collision': 'NO_COLLISION', 'navigation': True}]}]:
            with self.assertRaises(RuntimeError):
                M.verify_witness(original, {**original, 'new': value}, ['new'])

    def test_only_map_and_new_fixture_fabric_packages_can_change(self):
        content = Path('/project/Content')
        before = {str(content / M.MAP_FILE): 'map', str(content / 'Brezi/Realism/Materials/Old.uasset'): 'protected'}
        after = {**before, str(content / M.MAP_FILE): 'new-map', str(content / 'Brezi/Realism/Fixtures/New.uasset'): 'new',
                 str(content / 'Brezi/Realism/Fabric/New.uasset'): 'fabric'}
        M.validate_changes(before, after, content)
        for path in ['Brezi/Realism/Materials/Old.uasset', 'Brezi/Realism/Other/New.uasset', 'Brezi/Realism/Fixtures/file.py']:
            with self.subTest(path=path), self.assertRaises(RuntimeError):
                M.validate_changes(before, {**after, str(content / path): 'changed'}, content)


if __name__ == '__main__':
    unittest.main()
