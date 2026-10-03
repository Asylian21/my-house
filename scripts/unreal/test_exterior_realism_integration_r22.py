"""Meaningful CPU counterfactual scope/overlap rejection using actual donors."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2];sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('r22_test_actual_guard',ROOT/'scripts/unreal/exterior-realism-integration-guards-r22.py')
g=importlib.util.module_from_spec(s);s.loader.exec_module(g)
b=g.load_donors()
grass=g.module('r22_test_exact_grass','exterior-curved-grass-native-r4.py')
values=g.read(g.check_pin(b['reports']['grass']['originalMembersBefore']))


def compose(reports=None,before=None):
    r=reports or b['reports']
    return g.compose_original_fields(before or b['before'],b['base'],r['leaf'],r['visibility'],r['neighbors'],r['grass'],
        b['grassSelected'],values,grass.guard)


class IntegrationScope(unittest.TestCase):
    def test_actual_six_saved_donors_and74_disjoint_packages(self):
        self.assertEqual(set(b['reports']),{'leaf','visibility','neighbors','grass','foreground','roof'})
        self.assertEqual(len({r['relativeContentPath']for r in b['packages']}),74)
        self.assertEqual(len(b['templates']),40);self.assertEqual(len(b['before']),5306)

    def test_original_full_field_counterfactual_and_visibility_overlap(self):
        expected,audit=compose();self.assertEqual(expected,b['expectedOriginal'])
        self.assertEqual(audit['retainedCullInstances'],501826);self.assertEqual(audit['grassRemovedMembers'],64)
        self.assertEqual(sum(r['instances']for r in b['originalGeometryAfter']['groups'].values()),631962)

    def test_leaf_slot0_bark_change_rejected(self):
        reports=copy.deepcopy(b['reports']);reports['leaf']['componentBindings'][0]['slot']=0
        with self.assertRaises(RuntimeError):compose(reports)

    def test_unknown_or_duplicate_leaf_scope_rejected(self):
        reports=copy.deepcopy(b['reports']);reports['leaf']['componentBindings'][0]=reports['leaf']['componentBindings'][1]
        with self.assertRaises(RuntimeError):compose(reports)

    def test_visibility_unknown_or_duplicate_scope_rejected(self):
        reports=copy.deepcopy(b['reports']);reports['visibility']['componentCullOverrides'][0]=reports['visibility']['componentCullOverrides'][1]
        with self.assertRaises(RuntimeError):compose(reports)

    def test_visibility_unapproved_distance_rejected(self):
        reports=copy.deepcopy(b['reports']);reports['visibility']['componentCullOverrides'][0]['afterCullCm']=[18000,100000]
        with self.assertRaises(RuntimeError):compose(reports)

    def test_grass_membership_changed_rejected(self):
        reports=copy.deepcopy(b['reports']);reports['grass']['originalMemberChanges'][0]['retainedInstances']-=1
        with self.assertRaises(RuntimeError):compose(reports)

    def test_neighbor_extra_original_partition_rejected(self):
        reports=copy.deepcopy(b['reports']);reports['neighbors']['componentChanges'][0]['sourceMeshId']='unapproved-building'
        with self.assertRaises(RuntimeError):compose(reports)

    def test_four_roof_component_scope_is_only_effective_slot_override(self):
        templates=g.added_templates(b['before'],b['reports'])
        for delta in b['reports']['roof']['componentMaterialOverrides']:
            row=templates['neighbors:'+delta['sourceMeshId']];c=g.component({row['sourceActor']:row['witness']},row['sourceActor'],delta['componentName'])
            self.assertEqual(c['mesh'],delta['mesh']);self.assertEqual(c['materials'],[delta['afterMaterial']]);self.assertEqual(c['overrideMaterials'],[delta['afterMaterial']])
        reports=copy.deepcopy(b['reports']);reports['roof']['componentMaterialOverrides'][0]['sourceMeshId']='unapproved-roof'
        with self.assertRaises(RuntimeError):g.added_templates(b['before'],reports)

    def test_new_actor_paths_cannot_collide_or_omit_actor(self):
        paths={k:v['sourceActor']+'__r22test'for k,v in b['templates'].items()}
        # Different donors reuse their own fresh-map names; canonical new IDs
        # are mapped independently and cannot collide in the combined map.
        paths={k:'/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.R22Test_'+str(i)for i,k in enumerate(paths)}
        self.assertEqual(len(g.compose_all_expected(b['expectedOriginal'],b['templates'],paths)),5346)
        paths[next(iter(paths))]=next(iter(b['before']))
        with self.assertRaises(RuntimeError):g.compose_all_expected(b['expectedOriginal'],b['templates'],paths)

    def test_original_architecture_policy_is_preserved_in_full_witness(self):
        expected,_=compose();changed={k for k in b['before']if b['before'][k]!=expected[k]}
        declared={r['actor']for r in b['reports']['leaf']['componentBindings']}|{r['actor']for r in b['reports']['visibility']['componentCullOverrides']}|{r['actor']for r in b['reports']['neighbors']['componentChanges']}
        declared|={b['base']['geometry']['groups'][r['groupId']]['actor']for r in b['reports']['grass']['originalMemberChanges']}
        self.assertEqual(changed,declared)
        for path in set(b['before'])-declared:self.assertEqual(expected[path],b['before'][path])

    def test_content_and_original_asset_delta_rejects_extra_native_mutation(self):
        before=b['content'];after=copy.deepcopy(before)
        after.update({r['relativeContentPath']:{'sha256':r['sha256'],'bytes':r['bytes']}for r in b['packages']})
        after['Brezi/Maps/Brezi.umap']={'sha256':'0'*64,'bytes':1};after['Data/viewpoints.json']={'sha256':'1'*64,'bytes':2}
        self.assertEqual(g.validate_content(before,after,b['packages'],'1'*64)['newUassetPackages'],74)
        key=next(k for k in before if k not in('Brezi/Maps/Brezi.umap','Data/viewpoints.json'))
        after[key]={'sha256':'2'*64,'bytes':3}
        with self.assertRaises(RuntimeError):g.validate_content(before,after,b['packages'],'1'*64)


if __name__=='__main__':unittest.main(verbosity=2)
