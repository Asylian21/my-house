"""Five saved-consumer contract mutations; no historical test/producer replay."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path);m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m);return m
c = module('_r32_checker_fixture', ROOT/'scripts/unreal/exterior-burkea-clay-editor-check-r32.py')


class SavedMaterialContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = c.module('_r32_fixture_guard', c.GUARD, c.GUARD_SHA)
        cls.r = c.read(c.REPORT);cls.plan = c.read(c.PLAN);cls.pf = c.read(c.PREFLIGHT)
        cls.bundle = c.saved_bundle(cls.g)
        cls.built = c.read(c.checked(cls.r['newMaterialReport']))
        cls.new = c.read(c.checked(cls.r['savedNewMaterialReadback']))
        cls.leaf = cls.g.leaf_math()

    def test_actual_header_and_wrong_scope(self):
        c.report_header(self.r, self.plan, self.pf, self.bundle, self.g)
        for mutate in ('savedActors', 'newTextureObjects', 'changedMaterialSlots'):
            r = copy.deepcopy(self.r);r['actualCounts'][mutate] += 1
            with self.assertRaises(RuntimeError): c.report_header(r, self.plan, self.pf, self.bundle, self.g)

    def test_leaf_strength_and_inherited_usage_mutations(self):
        old = self.bundle['base']['materialRecords'][self.leaf.LEAF]
        source = self.bundle['source']['leaf'];built = self.built['leaf'];saved = self.new['leaf']
        c.validate_leaf(built, saved, old, source, self.g)
        changed = copy.deepcopy(built);changed['newArtisticEncodedF32'] = changed['oldEncodedF32']
        with self.assertRaises(RuntimeError): c.validate_leaf(changed, saved, old, source, self.g)
        changed = copy.deepcopy(built);changed['usage']['nanite'] = False
        with self.assertRaises(RuntimeError): c.validate_leaf(changed, saved, old, source, self.g)

    def test_roof_uv_normal_and_map_role_mutations(self):
        source = self.bundle['source']['roof'];built = self.built['roof'];saved = self.new['roof']
        c.validate_roof(built, saved, source, self.bundle, self.g)
        for suffix, key, value in [('uv','v_tiling',.25), ('reflectionSign','constant',[1.,1.,1.,1.])]:
            changed = copy.deepcopy(built)
            node = next(n for n in changed['material']['graph']['nodes'] if n['role'].endswith(':'+suffix))
            node['values'][key] = value
            # Rehashing a corrupt receipt must not replace source recipe proof.
            changed['material']['graphSha256'] = c.digest(changed['material']['graph'])
            with self.assertRaises(RuntimeError): c.validate_roof(changed, saved, source, self.bundle, self.g)
        changed = copy.deepcopy(built);changed['textures']['normalGL']['source'] = changed['textures']['roughness']['source']
        with self.assertRaises(RuntimeError): c.validate_roof(changed, saved, source, self.bundle, self.g)

    def test_full_old_graph_route_and_texture_policy(self):
        before = c.read(c.checked(self.r['originalAssetWitnessBefore']))
        mapping = {self.r['originalAssetWitnessBefore']['path']: before,
                   self.r['originalAssetWitnessSaved']['path']: before}
        def read(row): return mapping[str(row)]
        # Pin/hash I/O is supplied by the production CLI; this fixture mutates
        # the complete actual payload to exercise semantic source checks only.
        with patch.object(c,'checked',side_effect=lambda row:Path(row['path'])), patch.object(c,'read',side_effect=read):
            c.validate_old_assets(self.r, self.bundle)
            asset = next(k for k,v in before['graphs'].items() if v['reader']=='neighbor')
            before['graphs'][asset]['reader'] = 'basic'
            with self.assertRaises(RuntimeError): c.validate_old_assets(self.r, self.bundle)
            before['graphs'][asset]['reader'] = 'neighbor'
            texture = next(iter(before['textures']));before['textures'][texture]['snapshot']['values']['srgb'] = not before['textures'][texture]['snapshot']['values']['srgb']
            with self.assertRaises(RuntimeError): c.validate_old_assets(self.r, self.bundle)

    def test_scene_raw_signed_zero_mutation(self):
        names = ['beforeActorWitness','expectedActorWitness','savedActorWitness','rawInstanceControlsBefore','rawInstanceControlsSaved']
        mapping = {self.r[key]['path']:c.read(c.checked(self.r[key])) for key in names}
        with patch.object(c,'checked',side_effect=lambda row:Path(row['path'])), patch.object(c,'read',side_effect=lambda row:mapping[str(row)]):
            c.validate_scene(self.r,self.plan,self.bundle,self.g)
            raw = mapping[self.r['rawInstanceControlsSaved']['path']]
            row = next(v for v in raw.values() if v['numCustomDataFloats']==0)
            row['numCustomDataFloats'] = -0.0
            with self.assertRaises(RuntimeError): c.validate_scene(self.r,self.plan,self.bundle,self.g)


if __name__ == '__main__': unittest.main()
