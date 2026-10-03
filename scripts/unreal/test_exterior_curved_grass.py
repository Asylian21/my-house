"""Meaningful CPU rejection fixtures for bounded original R20 grass pilot."""
import copy
import importlib.util
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.dont_write_bytecode = True
spec = importlib.util.spec_from_file_location('test_curved_grass_native', ROOT/'scripts/unreal/exterior-curved-grass-native.py')
n = importlib.util.module_from_spec(spec); spec.loader.exec_module(n)
g, m = n.guard, n.maps


class OriginalGrassGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.originals = g.original_meshes()
        cls.geometry = g.converted_geometry(cls.originals)
        cls.placements, cls.prototypes, cls.camera = n.load_selection_inputs()
        cls.candidates = g.source_candidates(cls.placements, cls.prototypes, cls.camera)
        cls.selected = g.select_roots(cls.candidates, cls.geometry)
        cls.report = g.read(g.BASE/'exterior-import-report.json')

    def test_original_three_shapes_and_full_pilot_cost(self):
        proof = g.validate_geometry(self.geometry, self.originals)
        self.assertEqual(proof['pilotTriangleCostsByLod'], [41104]*3)
        self.assertEqual([r['triangles'] for r in self.geometry], [833, 653, 340])
        self.assertTrue(all(not r['displayNodeTransformApplied'] for r in self.geometry))

    def test_correct_reflected_axis_and_no_display_offsets(self):
        for row in self.geometry:
            for source, native in zip(row['positionMetersYUp'], row['expectedNativeVerticesCm']):
                self.assertEqual(native, [g.f32(source[0]*100), g.f32(source[2]*100), g.f32(source[1]*100)])
            self.assertEqual(min(p[1] for p in row['positionMetersYUp']), 0.)
            self.assertEqual(row['normalYUp'], self.originals[row['kind']]['originalNormalsYUp'])

    def test_original_tangent_frames_are_real_uv_derivatives(self):
        for row in self.geometry:
            self.assertFalse(row['tangentProof']['providerTangentsPresent'])
            self.assertEqual(row['tangentProof']['fallbackFrames'], 0)
            self.assertLess(max(abs(g.dot(normal, tangent[:3])) for normal,tangent in zip(row['normalYUp'],row['tangentYUp'])), 2e-7)
            # Measured original UV charts have negative handedness throughout;
            # an arbitrary demand for both signs would misclassify valid frames.
            self.assertEqual(set(t[3] for t in row['tangentYUp']), {-1.0})

    def test_source_position_mutation_rejected(self):
        rows = copy.deepcopy(self.geometry); rows[1]['positionMetersYUp'][0][0] += .4
        with self.assertRaises(RuntimeError): g.validate_geometry(rows, self.originals)

    def test_source_normal_mutation_rejected(self):
        rows = copy.deepcopy(self.geometry); rows[0]['normalYUp'][0][1] *= -1
        with self.assertRaises(RuntimeError): g.validate_geometry(rows, self.originals)

    def test_source_glb_and_corrupt_winding_rejected(self):
        with tempfile.TemporaryDirectory(prefix='brezi-r20-guard-') as temp:
            path = Path(temp)/'original.glb'; g.write_glb(path,self.geometry); g.decode_glb(path,self.geometry)
            rows = copy.deepcopy(self.geometry); rows[0]['indices'][0:3] = list(reversed(rows[0]['indices'][0:3]))
            with self.assertRaises(RuntimeError): g.decode_glb(path,rows)

    def test_actual_retained_root_mix_radius_and_height(self):
        audit = g.validate_selection(self.selected,self.placements,self.prototypes,self.camera,self.geometry)
        self.assertEqual(len(self.candidates),190)
        self.assertEqual(audit['selectedRoots'],64); self.assertEqual(audit['netPopulationChange'],0)
        self.assertLessEqual(audit['maximumNewScaledVertexRadiusCm'],14.)
        for row in self.selected:
            self.assertEqual(row['newSourceRow']['positionCm'],row['originalSourceRow']['positionCm'])
            self.assertEqual(row['newSourceRow']['yawDeg'],row['originalSourceRow']['yawDeg'])
            self.assertEqual(len(set(row['newSourceRow']['scale'])),1)

    def test_selected_root_coordinate_change_rejected(self):
        rows = copy.deepcopy(self.selected); rows[0]['newSourceRow']['positionCm'][0] += 1
        with self.assertRaises(RuntimeError): g.validate_selection(rows,self.placements,self.prototypes,self.camera,self.geometry)

    def test_crown_escape_and_nonuniform_scaling_rejected(self):
        rows = copy.deepcopy(self.selected); rows[0]['newSourceRow']['scale'][0] *= 2
        with self.assertRaises(RuntimeError): g.validate_selection(rows,self.placements,self.prototypes,self.camera,self.geometry)

    def test_wrong_member_count_rejected(self):
        with self.assertRaises(RuntimeError): g.validate_selection(self.selected[:-1],self.placements,self.prototypes,self.camera,self.geometry)

    def test_descending_remove_at_swap_preserves_members_exactly(self):
        self.assertEqual(g.retained_swap_indices(8,[1,5]),[0,6,2,3,4,7])
        for count in (1,4,12):
            removed = [i for i in range(count) if i%3 == 0]
            result = g.retained_swap_indices(count,removed)
            self.assertEqual(set(result),set(range(count))-set(removed))
        with self.assertRaises(RuntimeError): g.retained_swap_indices(8,[1,1])
        with self.assertRaises(RuntimeError): g.retained_swap_indices(8,[8])

    def test_counterfactual_changes_only_selected_count_and_hash(self):
        # Explicit synthetic instance arrays exercise deletion semantics;
        # they are never presented as captured native transforms.
        groups = {k:copy.deepcopy(self.report['geometry']['groups'][k]) for k in {r['groupId'] for r in self.selected}}
        before, arrays = {}, {}
        for key,row in groups.items():
            values = [[[float(i),0.,0.],[0.,0.,0.,1.],[1.,1.,1.]] for i in range(row['instances'])]
            arrays[key] = values; row['transformsSha256'] = g.digest(values)
            before[row['actor']] = {'protectedLight':7,'components':[{'mesh':row['mesh'],'path':row['actor']+'.Instances',
                'instanceCount':row['instances'],'orderedInstanceTransformsSha256':g.digest(values),'instanceCullCm':[7200,9000]}]}
        expected, changes = g.expected_original_witness(before,self.selected,arrays,groups)
        self.assertEqual(sum(len(c['removedOriginalIndices']) for c in changes),64)
        for change in changes:
            actor = expected[change['actor']]
            self.assertEqual(actor['protectedLight'],7); self.assertEqual(actor['components'][0]['instanceCullCm'],[7200,9000])
            self.assertEqual(set(change['retainedOriginalIndicesInNativeOrder']),set(range(change['originalInstances']))-set(change['removedOriginalIndices']))
        arrays[next(iter(arrays))][0][0][0] += .1
        with self.assertRaises(RuntimeError): g.expected_original_witness(before,self.selected,arrays,groups)

    def test_original_sidecar_alpha_cannot_be_rgb_jpeg(self):
        recipe = m.canonical_recipe(); self.assertTrue(m.validate_recipe(recipe)['explicitSeparateAlphaPngRequired'])
        changed = copy.deepcopy(recipe); changed['explicitOpacitySource']='albedo.A'
        with self.assertRaises(RuntimeError): m.validate_recipe(changed)
        changed = copy.deepcopy(recipe); changed['maps']['alpha']=changed['maps']['albedo']
        with self.assertRaises(RuntimeError): m.validate_recipe(changed)

    def test_wrong_gl_normal_or_ao_albedo_recipe_rejected(self):
        for key,value in [('nativeNormalGreenFlip',False),('aoMultipliedIntoBaseColor',True),('providerMetallicFactor',1.)]:
            recipe=m.canonical_recipe(); recipe[key]=value
            with self.assertRaises(RuntimeError): m.validate_recipe(recipe)

    def test_asset_delta_cannot_overwrite_old_mesh_or_add_other_package(self):
        packages=[g.PREFIX+'/Test/Owned'+str(i) for i in range(11)]
        before={n.MAP_FILE:{'sha256':'a','bytes':1},'Original.uasset':{'sha256':'b','bytes':2}}
        after=copy.deepcopy(before);after[n.MAP_FILE]={'sha256':'c','bytes':3}
        after.update({p.removeprefix('/Game/')+'.uasset':{'sha256':'d','bytes':4} for p in packages})
        self.assertEqual(n.validate_asset_delta(before,after,packages)['newUassetPackages'],11)
        bad=copy.deepcopy(after);bad['Original.uasset']['sha256']='changed'
        with self.assertRaises(RuntimeError):n.validate_asset_delta(before,bad,packages)
        bad=copy.deepcopy(after);bad['Foreign.uasset']={'sha256':'z','bytes':5}
        with self.assertRaises(RuntimeError):n.validate_asset_delta(before,bad,packages)


if __name__ == '__main__': unittest.main(verbosity=2)
