"""R35 stdlib source/byte/counterfactual guards; synthetic frames are CPU fixtures.

These tests never claim fresh native instance/alpha/seed-range readback.
"""
import copy
import importlib.util
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('r35_test_owned_guards', ROOT/'scripts/unreal/exterior-context-yard-repair-guards-r35.py')
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)


def fixture_control(group):
    """Identity-rotation fixtures, not actual recovered UE frames."""
    rows = group['sourceRows']; n = len(rows)
    recovered = [[list(r['positionCm']), [0.0, 0.0, 0.0, 1.0], [1.0, 1.0, 1.0]] for r in rows]
    matrices = [[[1.0, 0.0, 0.0, 0.0], [0.0, 1.0, 0.0, 0.0], [0.0, 0.0, 1.0, 0.0], list(r['positionCm'])+[1.0]] for r in rows]
    return {'groupId':group['groupId'], 'actor':group['actor'], 'component':group['component'], 'mesh':group['mesh'],
            'instanceCount':n, 'rootIds':[group['groupId']+':'+str(i) for i in range(n)], 'sourceRootIndices':list(range(n)),
            'recoveredValues':recovered, 'storedMatrices':matrices, 'mainRandomSeed':19421, 'numCustomDataFloats':0,
            'customData':[], 'additionalRandomSeedsReadbackAvailable':False, 'seedRangesReconstructed':False}


class RepairGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle = g.validate_source()
        cls.proposal = cls.bundle['proposal']
        cls.coverage = g.checked(cls.proposal['repairBHardUnionCoverage']['variant'])
        cls.original_glb = g.check_pin(g.checked(cls.bundle['base']['report']['sourceStudy'])['sourceGlb'])
        cls.patched_glb = g.check_pin(cls.proposal['repairBHardUnionCoverage']['sourceGlbVariant'])
        cls.group = copy.deepcopy(next(iter(cls.bundle['ecologyGroups'].values())))
        cls.control = fixture_control(cls.group)
        cls.group['originalSavedOrderedTransformsSha256'] = g.digest(cls.control['recoveredValues'])

    def rejected(self, fn, *args):
        with self.assertRaises((RuntimeError, ValueError, KeyError, TypeError)):
            fn(*args)

    def test_actual_frozen_source_and_stdlib_gate(self):
        b = self.bundle
        self.assertEqual((len(b['ecologyGroups']), len(b['ecologySourceModels'])), (8, 8))
        self.assertEqual(sum(v['originalInstances'] for v in b['ecologyGroups'].values()), 1953)
        self.assertEqual(sum(len(v['selectedSourceIndices']) for v in b['ecologyGroups'].values()), 34)
        self.assertEqual(b['base']['independentSavedProof']['nativeProcessId'], 5443)
        self.assertEqual(sum(len(v['indices'])//3 for v in b['floorRecords'].values()), 4519)
        self.assertFalse(any(k == 'shapely' or k.startswith('shapely.') for k in sys.modules))

    def test_exact_serialized_uv1_r_byte_patch(self):
        self.assertTrue(g.validate_coverage_bytes(self.coverage, self.original_glb, self.patched_glb))
        self.assertEqual(self.coverage['binaryChannelProof']['changedByteCount'], 2207)
        self.assertEqual(sum(p['changedCoverageVertices'] for p in self.coverage['variants']), 628)

    def test_uv1_g_mutation_rejected(self):
        row = copy.deepcopy(self.coverage)
        row['variants'][0]['proposedUv1F32'][0][1] += .125
        self.rejected(g.validate_coverage_bytes, row, self.original_glb, self.patched_glb)

    def test_source_position_byte_mutation_rejected(self):
        data = bytearray(self.patched_glb.read_bytes())
        jo = 20; length = struct.unpack_from('<I', data, 12)[0]
        doc = json.loads(data[jo:jo+length]); bo = jo+length+8
        node = next(n for n in doc['nodes'] if n['name'] == self.coverage['variants'][0]['meshId']+'_LOD0')
        primitive = doc['meshes'][node['mesh']]['primitives'][0]
        a = doc['accessors'][primitive['attributes']['POSITION']]; v = doc['bufferViews'][a['bufferView']]
        offset = bo+v.get('byteOffset',0)+a.get('byteOffset',0)
        data[offset] ^= 1
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'position-mutation.glb'; path.write_bytes(data)
            self.rejected(g.validate_coverage_bytes, self.coverage, self.original_glb, path)

    def test_two_custom_codes_only(self):
        original = self.bundle['materialVariant']
        self.assertTrue(g.validate_graph_variant(original))
        for mutate in ('third_node', 'texture_route', 'wrong_coefficient'):
            row = copy.deepcopy(original)
            if mutate == 'third_node': row['proposedGraph']['nodes'][0]['role'] += ':foreign'
            elif mutate == 'texture_route': row['proposedGraph']['nodes'][0]['values']['texture'] = '/Game/Foreign.Texture'
            else:
                n = next(n for n in row['proposedGraph']['nodes'] if n['role'] == 'BreziExterior:near-terrain-normal-strength')
                n['values']['code'] = 'return .66*Near;'
            self.rejected(g.validate_graph_variant, row)

    def test_swap_remove_then_only_existing_survivor_order(self):
        self.assertEqual(g.swap_remove_order(8, [1, 3, 6]), [0, 5, 2, 7, 4])
        self.assertEqual([i for i in range(8) if i not in [1,3,6]], [0,2,4,5,7])
        for bad in ([3,1], [1,1], [-1], [8], [True]): self.rejected(g.swap_remove_order, 8, bad)

    def test_raw_survivors_main_seed_and_signed_zero_exact(self):
        row = copy.deepcopy(self.control); row['storedMatrices'][0][0][1] = -0.0
        desired = g.expected_control(row, self.group['selectedSourceIndices'])
        keep = [i for i in range(row['instanceCount']) if i not in self.group['selectedSourceIndices']]
        self.assertEqual(desired['mainRandomSeed'], row['mainRandomSeed'])
        self.assertEqual(desired['sourceRootIndices'], keep)
        g.exact(desired['storedMatrices'], [row['storedMatrices'][i] for i in keep])
        self.rejected(g.exact, [0.0], [-0.0])
        for key, value in [('numCustomDataFloats',1),('customData',[.3]),('additionalRandomSeedsReadbackAvailable',True),('seedRangesReconstructed',True)]:
            bad = copy.deepcopy(row); bad[key] = value
            self.rejected(g.expected_control, bad, self.group['selectedSourceIndices'])

    def test_exact_control_root_identity_and_source_xyz(self):
        self.assertTrue(g.validate_native_controls(self.control, self.group, self.bundle))
        for field in ('rootIds','sourceRootIndices','storedMatrices','recoveredValues'):
            row = copy.deepcopy(self.control)
            if field == 'rootIds': row[field][0] += ':invented'
            elif field == 'sourceRootIndices': row[field][0] = 1
            elif field == 'storedMatrices': row[field][0][3][0] += .01
            else: row[field][0][0][0] += .01
            self.rejected(g.validate_native_controls, row, self.group, self.bundle)

    def test_triangle_line_point_and_hole_support(self):
        domain = {'type':'Polygon','coordinates':[[[0,0],[10,0],[10,10],[0,10],[0,0]], [[3,3],[3,7],[7,7],[7,3],[3,3]]]}
        for tri in ([[1,1],[2,1],[1,2]], [[-1,5],[2,5],[2,5]], [[0,5],[0,5],[0,5]], [[-20,-20],[30,-20],[5,30]]):
            self.assertTrue(g.source_support_intersects(tri, domain))
        for tri in ([[4,4],[6,4],[5,6]], [[4,5],[6,5],[6,5]], [[5,5],[5,5],[5,5]], [[11,11],[12,11],[11,12]]):
            self.assertFalse(g.source_support_intersects(tri, domain))
        self.rejected(g.source_support_intersects, [[float('nan'),0],[0,0],[0,0]], domain)

    def test_all_lod_support_guard_through_recorded_fixture_matrix(self):
        group = {'groupId':'fixture','actor':'actor','component':'Instances','mesh':'mesh','modelId':'m','originalInstances':1,
                 'sourceRows':[{'positionCm':[0.0,0.0,0.0]}], 'selectedSourceIndices':[0]}
        control = fixture_control(group); group['originalSavedOrderedTransformsSha256'] = g.digest(control['recoveredValues'])
        part = {'positionsCm':[[1.,1.,0.],[2.,1.,0.],[1.,2.,0.]],'indices':[0,1,2]}
        bundle = {'ecologySourceModels':{'m':{'lods':[{'level':i,'parts':[part]}for i in range(3)]}},
                  'hardFootprints':{'hard':{'type':'Polygon','coordinates':[[[0,0],[3,0],[3,3],[0,3],[0,0]]]}}}
        result = g.native_support_checks(control,group,bundle)
        self.assertEqual(len(result[0]['lods']),3); self.assertFalse(result[0]['alphaVisiblePixelIdentityClaimed'])
        outside = copy.deepcopy(bundle); outside['hardFootprints']['hard']['coordinates'] = [[[10,10],[13,10],[13,13],[10,13],[10,10]]]
        self.rejected(g.native_support_checks,control,group,outside)

    def test_actual_whole_scene_counterfactual_synthetic_frame_scope(self):
        # Full actual actor policies, with explicitly synthetic fresh frame arrays
        # substituted only for testing the strict scope/filter algorithm.
        b = dict(self.bundle); b['base'] = dict(b['base']); b['base']['witness'] = copy.deepcopy(b['base']['witness'])
        b['ecologyGroups'] = copy.deepcopy(b['ecologyGroups']); b['nativeEcologyControls'] = {}
        for key, group in b['ecologyGroups'].items():
            c = fixture_control(group); b['nativeEcologyControls'][key] = c
            group['originalSavedOrderedTransformsSha256'] = g.digest(c['recoveredValues'])
            g.component(b['base']['witness'][group['actor']],group['component'])['orderedInstanceTransformsSha256'] = group['originalSavedOrderedTransformsSha256']
        paths = {key:g.PREFIX+'/Geometry/'+key+'.'+key for key in b['floorRecords']}
        expected = g.expected_counterfactual(b['base']['witness'],b,paths,g.MATERIAL)
        affected = {r['actor']for r in b['ecologyGroups'].values()} | {r['actor']for r in b['floorTargets'].values()} | {b['backdropTarget']['actualActor']}
        self.assertEqual(len(expected),5360)
        for actor,row in b['base']['witness'].items():
            if actor not in affected: self.assertEqual(expected[actor],row)
        for r in b['floorTargets'].values():
            a=g.component(expected[r['actor']],r['component']); o=g.component(b['base']['witness'][r['actor']],r['component'])
            self.assertEqual(a['materials'],o['materials']); self.assertEqual(a['overrideMaterials'],o['overrideMaterials'])
            a=dict(a);a['mesh']=o['mesh'];self.assertEqual(a,o)
        self.rejected(g.expected_counterfactual,b['base']['witness'],b,paths,'/Game/Foreign.M')
        changed=copy.deepcopy(b['base']['witness']);next(iter(changed.values()))['label']+='foreign'
        self.rejected(g.expected_counterfactual,changed,b,paths,g.MATERIAL)

    def test_content_exact_six_package_map_only_delta(self):
        before=self.bundle['base']['content']; after=copy.deepcopy(before)
        paths=[g.PREFIX+'/Pipeline/'+k+'.'+k for k in ('Assets','Materials','Level')]+[g.MATERIAL]+[g.PREFIX+'/Geometry/'+k+'.'+k for k in self.bundle['floorRecords']]
        after['Brezi/Maps/Brezi.umap']={'sha256':'1'*64,'bytes':1}
        for p in paths:after[p.split('.')[0].removeprefix('/Game/')+'.uasset']={'sha256':'2'*64,'bytes':2}
        self.assertEqual(g.validate_content(before,after,paths)['savedContentFiles'],4092)
        foreign=copy.deepcopy(after); key=next(k for k in before if k!='Brezi/Maps/Brezi.umap');foreign[key]={'sha256':'3'*64,'bytes':3}
        self.rejected(g.validate_content,before,foreign,paths)
        self.rejected(g.validate_content,before,after,paths[:-1])


if __name__ == '__main__': unittest.main(verbosity=2)
