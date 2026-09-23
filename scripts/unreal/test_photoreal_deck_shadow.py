import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('deck_shadow', Path(__file__).with_name('photoreal-deck-shadow.py'))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


class DeckShadowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene = json.loads((ROOT/'output/unreal/photoreal-20260923-r3/geometry/scene.json').read_text())

    def test_semantic_selection_ignores_source_ordinals_and_excludes_hatch_structure(self):
        selected = m.select_targets(self.scene)
        self.assertEqual(len(selected), 4)
        self.assertEqual(sorted(r['triangles'] for r in selected), [420, 768, 852, 936])
        scene = copy.deepcopy(self.scene)
        for i, row in enumerate(scene['objects']):
            row['id'] = 'REORDERED_'+str(3000-i)
        other = m.select_targets(scene)
        self.assertEqual({r['entityId'] for r in selected}, {r['entityId'] for r in other})
        self.assertTrue(all(r['id'].startswith('REORDERED_') for r in other))

    def test_changed_design_duplicate_and_board_thickness_rejected(self):
        scene = copy.deepcopy(self.scene)
        scene['activeDesign']['variant'] = 'A'
        with self.assertRaises(RuntimeError):
            m.select_targets(scene)
        scene = copy.deepcopy(self.scene)
        selected_id = m.select_targets(scene)[0]['id']
        row = next(r for r in scene['objects'] if r['id'] == selected_id)
        scene['objects'].append(copy.deepcopy(row))
        with self.assertRaises(RuntimeError):
            m.select_targets(scene)
        scene['objects'].pop()
        row['boundsMm']['max'][2] += 10
        with self.assertRaises(RuntimeError):
            m.select_targets(scene)

    def context(self):
        targets = m.select_targets(self.scene)
        u = SimpleNamespace(NaniteFallbackTarget=SimpleNamespace(PERCENT_TRIANGLES='percent'))
        parts = {r['id']: SimpleNamespace(get_editor_property=lambda _: False) for r in targets}
        states = {r['id']: {'mesh': 'source/'+r['id'], 'component': 'StaticMeshComponent0',
                   'triangles': r['triangles'], 'visible': True, 'hiddenInGame': False,
                   'actorHidden': False,
                   'nanite': {'enabled': r['triangles'] >= 512, 'fallback_target': 'percent',
                              'fallback_percent_triangles': 1.0, 'fallback_relative_error': 0.0}}
                  for r in targets}
        return u, targets, parts, states

    def test_only_existing_nanite_boards_get_raster_override_and_no_state_mutation(self):
        u, targets, parts, states = self.context()
        before = copy.deepcopy(states)
        rows = m.correction_plan(u, targets, parts, states)
        self.assertEqual(states, before)
        self.assertEqual(sum(r['afterDisallowNanite'] for r in rows), 3)
        self.assertFalse(next(r for r in rows if r['triangles'] == 420)['afterDisallowNanite'])
        self.assertTrue(all(r['beforeDisallowNanite'] is False for r in rows))

    def test_reduced_fallback_and_changed_triangle_count_are_not_accepted(self):
        u, targets, parts, states = self.context()
        row = next(s for s in states.values() if s['nanite']['enabled'])
        row['nanite']['fallback_percent_triangles'] = .5
        with self.assertRaisesRegex(RuntimeError, 'full-resolution'):
            m.correction_plan(u, targets, parts, states)
        row['nanite']['fallback_percent_triangles'] = 1.0
        row['triangles'] -= 1
        with self.assertRaisesRegex(RuntimeError, 'source state'):
            m.correction_plan(u, targets, parts, states)

    def test_existing_override_is_not_silently_reapplied(self):
        u, targets, parts, states = self.context()
        parts[targets[0]['id']].get_editor_property = lambda _: True
        with self.assertRaisesRegex(RuntimeError, 'already exists'):
            m.correction_plan(u, targets, parts, states)


if __name__ == '__main__':
    unittest.main()
