"""Nine focused mutations of the actual selected R39 source/binding packet.

No native calls or historical generator replay. A combined suite can supply
the once-validated bundle through GuardContracts.BUNDLE.
"""
import copy
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
s = importlib.util.spec_from_file_location('r39_guard_fixture', ROOT/'scripts/unreal/exterior-neighbor-props-guards-r39.py')
g = importlib.util.module_from_spec(s)
s.loader.exec_module(g)


class GuardContracts(unittest.TestCase):
    BUNDLE = None

    @classmethod
    def setUpClass(cls):
        if cls.BUNDLE is None:
            # Compact recorded input only; the final producer independently
            # runs load_contract and the frozen saved checker once.
            r = g.read(g.BASE_REPORT)
            records, textures = g.complete_materials(r)
            cls.BUNDLE = {'source': g.c.load_source(), 'binding': g.expected_binding(),
                'base': {'report': r, 'savedWitness': g.read(g.checked(r['savedActorWitness'])),
                    'content': g.read(g.checked(r['afterContentInventory'])),
                    'protected': g.read(g.checked(r['protectedProjectProof'])),
                    'parentReport': g.read(g.checked(r['baseNativeReport'])),
                    'materialRecords': records, 'textureRecords': textures}}
        cls.b = cls.BUNDLE
        cls.clone = g.read(g.CLONE)
        cls.image = g.read(g.IMAGE_DECISION)
        cls.terminal = g.read(g.BASE_PROCESS)
        cls.audit = g.read(g.BASE_AUDIT)

    def rejection(self, f, *args):
        with self.assertRaises(RuntimeError):
            f(*args)

    def test_exact_binding_and_wrong_selected_pid(self):
        self.assertTrue(g.require_native_binding(self.b['binding']))
        wrong = copy.deepcopy(self.b['binding']); wrong['selectedNativeProcessId'] = 66232
        self.rejection(g.require_native_binding, wrong)

    def test_binding_cannot_promote_or_change_old_actor_scope(self):
        for field, value in (('activeOutputPromoted', True), ('candidateProject', '/tmp/foreign')):
            wrong = copy.deepcopy(self.b['binding']); wrong[field] = value
            self.rejection(g.require_native_binding, wrong)
        wrong = copy.deepcopy(self.b['binding']); wrong['scope']['changedOldActors'] = 1
        self.rejection(g.require_native_binding, wrong)

    def test_clone_schema_and_native_pending_boundary(self):
        base = self.b['base']
        g.validate_clone_header(self.clone, self.b['binding'], base['content'], base['protected'])
        for field, value in (('schemaVersion', 2), ('nativeExecuted', True), ('wholeOriginalPropsNativePending', False)):
            wrong = copy.deepcopy(self.clone); wrong[field] = value
            self.rejection(g.validate_clone_header, wrong, self.b['binding'], base['content'], base['protected'])

    def test_clone_binary_content_is_protected_and_full_rows_exact(self):
        base = self.b['base']; wrong = copy.deepcopy(self.clone)
        candidates = [r for r in wrong['files'] if '/Binaries/' in r['destination'] and '/Content/' in r['destination']]
        self.assertTrue(candidates)
        candidates[0]['sha256'] = '0'*64
        self.rejection(g.validate_clone_header, wrong, self.b['binding'], base['content'], base['protected'])

    def test_failed_wrong_owner_and_wrong_saved_census_reject(self):
        r = self.b['base']['report']
        g.validate_base_header(r, self.image, self.terminal, self.audit)
        for field, value in (('nativeApplied', False), ('owner', 'old-failed.py'), ('schemaVersion', 1)):
            wrong = copy.deepcopy(r); wrong[field] = value
            self.rejection(g.validate_base_header, wrong, self.image, self.terminal, self.audit)
        wrong = copy.deepcopy(r); wrong['actualCounts']['fullHismInstances'] -= 1
        self.rejection(g.validate_base_header, wrong, self.image, self.terminal, self.audit)

    def test_complete_hose_and_source_wall_reference_are_required(self):
        base = self.b['base']
        g.validate_placements(self.b['source'], base['savedWitness'], base['parentReport'])
        wrong = copy.deepcopy(self.b['source']); wrong['parts']['garden_hose_wall_mounted_01'].pop()
        self.rejection(g.validate_placements, wrong, base['savedWitness'], base['parentReport'])
        changed = copy.deepcopy(base['savedWitness'])
        actor = self.b['source']['proposal']['placements'][0]['wallFit']['referenceWallActor']
        changed[actor]['transform'][0][0] += 1
        self.rejection(g.validate_placements, self.b['source'], changed, base['parentReport'])

    def test_full_original_actor_is_not_a_replaceable_counterfactual_base(self):
        before = copy.deepcopy(self.b['base']['savedWitness'])
        actor = next(iter(before)); before[actor]['hidden'] = not before[actor]['hidden']
        self.rejection(g.expected_counterfactual, before, {})

    def test_visible_texture_fields_and_unrecorded_new_usage_limits(self):
        base = self.b['base']; records, textures = base['materialRecords'], base['textureRecords']
        g.validate_material_records(records, textures)
        wrong = copy.deepcopy(textures); row = next(iter(wrong.values()))
        row['values']['compression_none'] = False; del row['values']['filter']
        self.rejection(g.validate_material_records, records, wrong)
        wrong = copy.deepcopy(records)
        row = next(v for v in wrong.values() if not v['usageRecordedInSelectedNativeReceipt'])
        row['usage'] = {'instancedStaticMeshes': True, 'nanite': False}
        self.rejection(g.validate_material_records, wrong, textures)

    def test_exact_package_delta_rejects_foreign_namespace_and_old_asset_edit(self):
        before = self.b['base']['content']; assets = g.expected_new_packages(self.b['source'])
        after = copy.deepcopy(before); after['Brezi/Maps/Brezi.umap'] = {'sha256': '1'*64, 'bytes': 100}
        for a in assets:
            after[a.split('.')[0].removeprefix('/Game/')+'.uasset'] = {'sha256': '2'*64, 'bytes': 100}
        self.assertTrue(g.validate_content_delta(before, after, assets)['onlyOriginalMapChanged'])
        wrong = copy.deepcopy(after); extra = next(k for k in wrong if k not in before)
        wrong['Brezi/Foreign.uasset'] = wrong.pop(extra)
        self.rejection(g.validate_content_delta, before, wrong, assets)
        wrong = copy.deepcopy(after); old = next(k for k in before if k != 'Brezi/Maps/Brezi.umap')
        wrong[old]['sha256'] = '3'*64
        self.rejection(g.validate_content_delta, before, wrong, assets)


if __name__ == '__main__':
    unittest.main(verbosity=2)
