"""Five focused saved R43b/R2 contract cases; no producer or native calls."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('_r31_saved_boundary_test',
    ROOT/'scripts/unreal/exterior-context-parcel-boundary-editor-check-r31.py')
c = importlib.util.module_from_spec(spec)
spec.loader.exec_module(c)


class SavedBoundaryContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = c.read(c.REPORT)
        cls.plan = c.read(c.PLAN)
        cls.source = c.read(c.g.SOURCE)
        cls.preflight = c.read(c.PREFLIGHT)
        cls.bundle = {'base': {'template': cls.plan['newActorTemplate'],
            'savedWitness': {c.g.TEMPLATE: cls.plan['newActorTemplate']}}}
        cls.spawn = c.read(c.checked(cls.report['newActorSpawnObservations']))
        cls.rows = c.g.export_rows(c.read(c.checked(cls.source['geometry'])))

    def test_actual_header_rejects_failed_or_old_contract(self):
        c.report_header(self.report, self.plan, self.source, self.preflight)
        for key, value in (('status', 'running'), ('schemaVersion', 1),
                           ('repairSchema', 'foreign-repair')):
            bad = dict(self.report); bad[key] = value
            with self.assertRaises(RuntimeError):
                c.report_header(bad, self.plan, self.source, self.preflight)

    def test_class_spawn_keeps_exact_identity_and_fresh_owner(self):
        c.validate_spawn(self.spawn, self.bundle, self.report['newOwnedActors'])
        for mutate in (
            lambda row: row['actorTransform'][0].__setitem__(0, -0.0),
            lambda row: row.__setitem__('existingSourceActorReturned', True),
        ):
            bad = copy.deepcopy(self.spawn); mutate(bad['actualObservations'][0])
            with self.assertRaises(RuntimeError):
                c.validate_spawn(bad, self.bundle, self.report['newOwnedActors'])

    def test_added_actor_links_proved_master_and_source_template(self):
        role = 'wood'; row = self.report['newOwnedActors'][role]
        expected = c.new_actor_expected(self.bundle, role, row,
            self.report['nativeGeometryReadback'][role], self.report['materialReport']['materials'][role])
        self.assertEqual(expected['components'][0]['mesh'], row['mesh'])
        self.assertEqual(expected['components'][0]['materials'], [row['material']])
        for key, value in (('mesh', '/Game/foreign.foreign'), ('createdByObservedClassSpawn', False)):
            bad = dict(row); bad[key] = value
            with self.assertRaises(RuntimeError):
                c.new_actor_expected(self.bundle, role, bad,
                    self.report['nativeGeometryReadback'][role], self.report['materialReport']['materials'][role])

    def test_full_corner_hash_rejects_same_count_uv_or_winding_change(self):
        records = self.report['nativeGeometryReadback']
        c.validate_geometry(records, self.rows)
        n = c.module('_r31_corner_mutation_case', c.NATIVE, c.NATIVE_SHA)
        for kind in ('uv', 'winding'):
            changed = copy.deepcopy(self.rows)
            row = changed[0]
            if kind == 'uv':
                row['uv0'][row['indices'][0]][0] += 0.125
            else:
                row['indices'][1], row['indices'][2] = row['indices'][2], row['indices'][1]
            self.assertEqual(len(row['indices']), len(self.rows[0]['indices']))
            bad = copy.deepcopy(records)
            bad[row['material']]['fullOrderedNativeF32PositionUv0SectionWindingSha256'] = c.digest(n.expected_corners(row))
            with self.assertRaises(RuntimeError):
                c.validate_geometry(bad, self.rows)

    def test_original_photo_policy_rejects_normal_and_roughness_tampering(self):
        built = self.report['materialReport']
        c.validate_materials(built, self.source, self.plan['binding'])
        for channel, field, value in (('normal', 'flip_green_channel', False),
                                      ('roughness', 'srgb', True)):
            bad = copy.deepcopy(built)
            bad['materials']['wood']['textures'][channel]['snapshot']['values'][field] = value
            with self.assertRaises(RuntimeError):
                c.validate_materials(bad, self.source, self.plan['binding'])


if __name__ == '__main__':
    unittest.main(verbosity=2)
