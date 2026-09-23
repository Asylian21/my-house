"""Small independent regression checks for lawn coverage and authored blades."""
import importlib.util
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest
from types import SimpleNamespace

SPEC = importlib.util.spec_from_file_location('lawn_geometry', Path(__file__).with_name('lawn-geometry.py'))
G = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(G)


class LawnGeometryTests(unittest.TestCase):
    def test_compilation_barrier_and_screen_checks_are_strict(self):
        calls = []
        level = SimpleNamespace(get_outer=lambda: 'editor-world')
        native = SimpleNamespace(LevelEditorSubsystem='level', get_editor_subsystem=lambda _: SimpleNamespace(get_current_level=lambda: level),
                                 SystemLibrary=SimpleNamespace(execute_console_command=lambda world, cmd: calls.append((world, cmd)),
                                                               get_console_variable_int_value=lambda _: 0))
        G.finish_static_mesh_compilation(native, True)
        self.assertEqual(calls, [('editor-world', 'Editor.AsyncStaticMeshCompilation 0'),
                                 ('editor-world', 'Editor.AsyncStaticMeshCompilationFinishAll')])
        subsystem = SimpleNamespace(get_lod_screen_sizes=lambda _: [1., .02500000037252903, .007000000216066837])
        mesh = SimpleNamespace(get_path_name=lambda: '/Game/Grass')
        self.assertEqual(len(G.checked_lod_screens(subsystem, mesh)), 3)
        subsystem.get_lod_screen_sizes = lambda _: [1., .5, .25]
        with self.assertRaisesRegex(RuntimeError, r'/Game/Grass actual=\[1.0, 0.5, 0.25\]'):
            G.checked_lod_screens(subsystem, mesh)

    def test_commandlet_loads_owner_module_before_subsystem_use(self):
        loaded = []
        static, asset = object(), object()
        native = SimpleNamespace(StaticMeshEditorSubsystem='static', AssetEditorSubsystem='asset')
        native.get_editor_subsystem = lambda kind: asset if kind == 'asset' else static if loaded else None
        native.load_module = loaded.append
        self.assertIs(G.static_mesh_subsystem(native), static)
        self.assertEqual(loaded, ['StaticMeshEditor'])
        self.assertIs(G.static_mesh_subsystem(native), static)
        self.assertEqual(loaded, ['StaticMeshEditor'])
        native.get_editor_subsystem = lambda kind: static if kind == 'static' else None
        with self.assertRaisesRegex(RuntimeError, 'AssetEditorSubsystem unavailable'):
            G.static_mesh_subsystem(native)

    def test_blades_are_curved_tapered_and_bounded_in_all_lods(self):
        for variant in range(4):
            for lod in range(3):
                p = G.prototype(variant, lod)
                self.assertEqual(len(p['faces']), [256, 64, 24][lod])
                self.assertEqual(sum(uv[1] == 1 for uv in p['uv0']), 2*[64, 32, 12][lod])
                self.assertGreaterEqual(p['boundsMm']['min'][2], 0)
                self.assertGreater(p['boundsMm']['max'][2], 28)
                self.assertLessEqual(p['boundsMm']['max'][2], 45)
                self.assertTrue(all(abs(sum(n*n for n in normal)-1) < 1e-10 for normal in p['normals']))
                self.assertTrue(all(0 <= value <= 1 for uv in p['uv0'] for value in uv))
                # Actual near-LOD leaves have a bent, elevated midsection and
                # a narrow clipped tip; they are not flat rectangular cards.
                for record in p['bladeRanges']:
                    start, stride = record['vertexOffset'], record['vertexCount']
                    left, right = p['verticesMm'][start:start+2]
                    root = [(a+b)/2 for a, b in zip(left, right)]
                    ta, tb = p['verticesMm'][start+stride-2:start+stride]
                    tip = [(a+b)/2 for a, b in zip(ta, tb)]
                    self.assertGreater(math.dist(root[:2], tip[:2]), 10)
                    self.assertLess(math.dist(ta, tb), math.dist(left, right))
                    self.assertTrue(all(seed == p['uv1'][start] for seed in p['uv1'][start:start+stride]))
                    if lod == 0 and not record['short']:
                        self.assertEqual(record['segments'], 3)
                        a, b = p['verticesMm'][start+2:start+4]
                        mid = [(x+y)/2 for x, y in zip(a, b)]
                        self.assertGreater(math.dist(mid, [2*x/3+y/3 for x, y in zip(root, tip)]), 3)

    def test_patch_density_and_directions_avoid_isolated_crowns(self):
        self.assertGreaterEqual(G.LOD_BLADES[0]*1e6/G.SPACING_MM**2, 17000)
        self.assertLessEqual(G.GRID_JITTER, .18)
        for variant in range(4):
            params = G.blade_parameters(variant)
            self.assertEqual(len(params), 64)
            self.assertGreater(sum(math.hypot(*p['root']) > 30 for p in params), 20)
            directions = {int((p['angle']+math.pi)/(math.pi/2)) % 4 for p in params}
            self.assertEqual(directions, {0, 1, 2, 3})
            self.assertTrue(all(1.3 <= p['width'] <= 2.8 and 16 <= p['height'] <= 45 for p in params))
            self.assertEqual(sum(p['short'] for p in params), 32)
            lods = [G.prototype(variant, lod) for lod in range(3)]
            seeds = {r['bladeIndex']: lods[0]['uv1'][r['vertexOffset']] for r in lods[0]['bladeRanges']}
            for lod in lods[1:]:
                for r in lod['bladeRanges']:
                    self.assertEqual(lod['uv1'][r['vertexOffset']], seeds[r['bladeIndex']])

    def test_diagonal_triangle_seam_is_not_a_boundary(self):
        faces = [[(0, 0, 0), (1000, 0, 0), (1000, 1000, 0)],
                 [(0, 0, 0), (1000, 1000, 0), (0, 1000, 0)]]
        boundary = [((0, 0), (1000, 0)), ((1000, 0), (1000, 1000)),
                    ((1000, 1000), (0, 1000)), ((0, 1000), (0, 0))]
        distance, _ = G.clearance((500, 500), faces, boundary, [])
        self.assertEqual(distance, 500)
        self.assertLess(G.clearance((-1, 500), faces, boundary, [])[0], 0)

    def test_exclusion_interior_and_full_tuft_radius(self):
        faces = [[(0, 0, 0), (1000, 0, 0), (1000, 1000, 0)],
                 [(0, 0, 0), (1000, 1000, 0), (0, 1000, 0)]]
        boundary = [((0, 0), (1000, 0)), ((1000, 0), (1000, 1000)),
                    ((1000, 1000), (0, 1000)), ((0, 1000), (0, 0))]
        exclusion = {'id': 'deck', 'polygonSourceMm': [[400, 400], [600, 400], [600, 600], [400, 600]],
                     'boundsMm': [400, 400, 600, 600]}
        self.assertLess(G.clearance((500, 500), faces, boundary, [exclusion])[0], 0)
        self.assertEqual(G.clearance((375, 500), faces, boundary, [exclusion])[0], 25)
        # A root alone fits, but a 30mm radius tuft would intrude on the deck.
        self.assertLess(G.clearance((375, 500), faces, boundary, [exclusion])[0], 30)
        self.assertEqual(G.clearance((400, 500), faces, boundary, [exclusion])[0], -1)

    def test_glb_has_exact_root_tip_uv_and_one_coordinate_conversion(self):
        p = G.prototype(0, 0)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'test.glb'
            G.write_glb(path, [p])
            data = path.read_bytes()
        magic, version, length = struct.unpack_from('<III', data)
        self.assertEqual((magic, version, length), (0x46546c67, 2, len(data)))
        jl = struct.unpack_from('<I', data, 12)[0]
        doc = json.loads(data[20:20+jl])
        binary = data[28+jl:]
        attrs = doc['meshes'][0]['primitives'][0]['attributes']
        def unpack(name, dim):
            accessor = doc['accessors'][attrs[name]]
            view = doc['bufferViews'][accessor['bufferView']]
            values = struct.unpack_from('<'+'f'*(accessor['count']*dim), binary, view['byteOffset'])
            return [values[i:i+dim] for i in range(0, len(values), dim)]
        positions, uv, uv1 = unpack('POSITION', 3), unpack('TEXCOORD_0', 2), unpack('TEXCOORD_1', 2)
        for native, source in zip(positions, p['verticesMm']):
            x, z, neg_y = native
            self.assertLess(math.dist([1000*x, -1000*neg_y, 1000*z], source), .00001)
        for actual, expected in zip(uv, p['uv0']):
            self.assertLess(math.dist(actual, expected), 1e-7)
        for actual, expected in zip(uv1, p['uv1']):
            self.assertLess(math.dist(actual, expected), 1e-7)
        self.assertEqual(doc['materials'][0]['doubleSided'], True)
        self.assertNotIn('alphaMode', doc['materials'][0])

    def test_transformed_bounds_preserve_unreal_handedness(self):
        box = {'min': [0, 0, 0], 'max': [10, 20, 30]}
        got = G.transformed_bounds(box, [1000, 2000, -65], 90, [1, 1, .5])
        self.assertEqual(got['min'], [98., -201., -6.5])
        self.assertEqual(got['max'], [100., -200., -5.])

    def test_current_semantic_exclusions_match_current_export(self):
        path = G.ROOT/'output/unreal/lawn-archviz-20260923-r1/geometry'
        if not path.is_dir():
            self.skipTest('Current geometry artifact unavailable')
        scene, faces, boundary, exclusions, extras = G.source_context(path)
        self.assertEqual(len(faces), 27)
        self.assertEqual(len(boundary), 23)
        self.assertEqual(set(extras), {f'DOM_{i:05}' for i in range(1958, 1967)})
        self.assertEqual(set(extras.values()), set(G.EXTRA_SEMANTICS))
        self.assertTrue(any(e['id'] == 'POOL-DECK-OUTER-ENVELOPE' for e in exclusions))
        self.assertLess(G.clearance([0, -5000], faces, boundary, exclusions)[0], 0)  # House.
        self.assertLess(G.clearance([-4200, 4000], faces, boundary, exclusions)[0], 0)  # Pool surround.
        self.assertGreater(G.clearance([-8000, 8500], faces, boundary, exclusions)[0], 100)


if __name__ == '__main__':
    unittest.main()
