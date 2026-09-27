"""Host checks for physically oriented grain and the narrow material boundary."""
import copy
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('furniture_grain', Path(__file__).with_name('realism-furniture-grain.py'))
M = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(M)


class FurnitureGrainTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.proposal = M.read(M.PROPOSAL)
        cls.scene = M.read(M.ROOT/'output/unreal/realism-20260926-r4/geometry/scene.json')
        cls.photoreal = M.read(M.ROOT/'output/unreal/realism-20260926-r4/photoreal-import-report.json')

    def test_actual_pinned_native_evidence_passes_preflight(self):
        proposal, rows, pins = M.preflight(M.ROOT/'output/unreal/realism-20260926-r4')
        self.assertEqual(len(rows), 11)
        self.assertEqual(proposal['baselineMaterialBindingCount'], 110)
        self.assertTrue(any(path.endswith('photoreal-import-report.json') for path in pins))

    def test_only_two_custom_prefixes_change_all_finish_and_edges_retained(self):
        before = self.proposal['sourceMaterialGraph']
        for axis in ('X', 'Y'):
            after = M.expected_graph(before, axis)
            changed = []
            for old, new in zip(before['nodes'], after['nodes']):
                if old != new:
                    changed.append((old['class'], old['role']))
                    self.assertEqual(old['inputs'], new['inputs'])
                    self.assertEqual(old['values']['output_type'], new['values']['output_type'])
                    self.assertEqual(old['values']['code'][len(M.BASIS):],
                                     new['values']['code'][len(M.frame_prefix(axis)):])
            self.assertEqual(changed, [('MaterialExpressionCustom', role) for role in M.ROLES])
            self.assertEqual({k:v for k,v in before.items() if k != 'nodes'},
                             {k:v for k,v in after.items() if k != 'nodes'})
            texture = [n for n in before['nodes'] if n['class'] == 'MaterialExpressionTextureSample'
                       and n['role'] == M.ROLES[1]][0]
            self.assertIn(texture, after['nodes'])
        self.assertEqual(before, self.proposal['sourceMaterialGraph'])

    def test_long_faces_follow_member_axis_and_normal_handedness(self):
        cross = lambda a,b: (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
        normals = [tuple(sign if i == axis else 0 for i in range(3)) for axis in range(3) for sign in (-1,1)]
        for axis in ('X', 'Y'):
            frame = M.study.FRAMES[axis]
            self.assertEqual(cross(frame[0], frame[1]), frame[2])
            for normal in normals:
                t,v = M.study.basis(normal, axis)
                self.assertEqual(cross(t,v), normal)
                self.assertEqual(M.study.dot(t,v), 0)
                if M.study.dot(normal, frame[2]) == 0:
                    self.assertEqual(abs(M.study.dot(v,frame[2])), 1)
            prefix = M.frame_prefix(axis)
            self.assertIn('float3 worldN=normalize(NormalWS);', prefix)
            self.assertTrue(prefix.endswith('N=worldN;\n'))
            self.assertIn('T=F0*T.x+F1*T.y+F2*T.z;', prefix)
            self.assertIn('V=F0*V.x+F1*V.y+F2*V.z;', prefix)

    def test_wrong_code_or_duplicate_custom_role_fails_closed(self):
        graph = self.proposal['sourceMaterialGraph']
        for mutation in ('prefix', 'duplicate', 'missing'):
            changed = copy.deepcopy(graph)
            target = next(n for n in changed['nodes'] if n['class'] == 'MaterialExpressionCustom' and n['role'] == M.ROLES[0])
            if mutation == 'prefix':
                target['values']['code'] = 'return float2(0,0);'
            elif mutation == 'duplicate':
                changed['nodes'].append(copy.deepcopy(target))
            else:
                changed['nodes'].remove(target)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                M.expected_graph(changed, 'X')
        with self.assertRaises(ValueError):
            M.expected_graph(graph, 'Z')

    def test_semantic_allowlist_rejects_axis_material_and_ph_target_drift(self):
        for field,value in [('worldGrainAxis', 'X'), ('materialSlot', 1), ('baselineMaterial', '/Game/Other'),
                            ('nativeVisualActor', '/Game/Wrong'), ('nativeVisualMesh', '/Game/Wrong')]:
            proposal = copy.deepcopy(self.proposal)
            proposal['objects'][0][field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                M.validate_proposal(proposal, self.scene, self.photoreal)
        duplicate = copy.deepcopy(self.proposal)
        duplicate['objects'][1] = duplicate['objects'][0]
        with self.assertRaises(ValueError):
            M.validate_proposal(duplicate, self.scene, self.photoreal)

    def test_other_materials_do_not_enter_protected_oak_population(self):
        class Asset:
            def __init__(self, path): self.path = path
            def get_path_name(self): return self.path
        class Component(Asset):
            def __init__(self, path, materials): super().__init__(path); self.materials = [Asset(m) for m in materials]
            def get_num_materials(self): return len(self.materials)
            def get_material(self, index): return self.materials[index]
        index = {key:(Asset(key),Component(key+'.c',materials)) for key,materials in
                 [('oak', ['/Game/Oak']), ('upholstery', ['/Game/Cloth']), ('mixed', ['/Game/Metal','/Game/Oak'])]}
        rows = M.material_bindings(index, {'/Game/Oak'})
        self.assertEqual([(r['actor'],r['slot']) for r in rows], [('mixed',1),('oak',0)])
        index['new'] = (Asset('new'), Component('new.c', ['/Game/Cloth']))
        self.assertEqual(rows, M.material_bindings(index, {'/Game/Oak'}))


if __name__ == '__main__':
    unittest.main()
