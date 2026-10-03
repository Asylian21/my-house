"""Two targeted future-mapping guards; no accepted base or native API calls."""
import copy
import importlib.util
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('r38_mapping_only_r2', HERE/'exterior-context-yard-soft-coherence-native-r38-r2-draft.py')
n = importlib.util.module_from_spec(spec);spec.loader.exec_module(n)


class MappingGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = n.g.load_contract()
        targets = cls.bundle['plan']['targets']
        cls.before = {n.g.ACTOR197: targets['backdropOriginalActor197']['historicalWitness'],
            n.g.DONOR668: targets['substrateDonorActor668']['historicalWitness']}
        # Pure fixture: these historic source shapes are not a selected R37 base.
        cls.binding = {'selectedReport': {'newActorMapping': {n.g.DONOR668: n.g.DONOR668}},
            'selectedCompositionBeforeWitness': {n.g.ACTOR197: cls.before[n.g.ACTOR197]},
            'targetWitnesses': {'backdrop': cls.before[n.g.ACTOR197], 'substrate': cls.before[n.g.DONOR668]}}

    def test_same_donor_and_fresh_actor_path_is_allowed_with_provenance(self):
        refs = n.resolve_future_targets(self.before, self.binding)
        self.assertEqual(refs['substrate']['actor'], n.g.DONOR668)
        expected = n.g.counterfactual_two_slots(self.before, refs)
        self.assertEqual(expected[n.g.DONOR668]['components'][0]['materials'][0], n.g.ASSETS['substrate'])
        self.assertEqual(expected[n.g.DONOR668]['transform'], self.before[n.g.DONOR668]['transform'])
        with self.assertRaises(RuntimeError):
            n.apply_overlay(object(), {}, self.bundle, self.binding)

    def test_missing_before_absence_mapping_or_exact_saved_identity_rejected(self):
        for mutation in ('already-original', 'wrong-saved-witness', 'alias-backdrop', 'missing-mapping'):
            bad = copy.deepcopy(self.binding)
            if mutation == 'already-original': bad['selectedCompositionBeforeWitness'][n.g.DONOR668] = self.before[n.g.DONOR668]
            elif mutation == 'wrong-saved-witness': bad['targetWitnesses']['substrate']['label'] = 'invented'
            elif mutation == 'alias-backdrop': bad['selectedReport']['newActorMapping'][n.g.DONOR668] = n.g.ACTOR197
            else: bad['selectedReport']['newActorMapping'] = {}
            with self.assertRaises(ValueError):n.resolve_future_targets(self.before, bad)


if __name__ == '__main__':unittest.main()
