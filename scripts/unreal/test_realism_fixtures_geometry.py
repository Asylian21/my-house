"""CPU regressions for fixture source boundaries and closed replacement geometry."""
import copy
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).with_name('realism-fixtures-geometry.py')
SPEC = importlib.util.spec_from_file_location('realism_fixtures_geometry', MODULE)
FIXTURES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(FIXTURES)


def scene():
    boxes = {
        'DOM_00759': ([8891, 2190, 700], [9491, 2590, 703]),
        'DOM_00760': ([8889, 2190, 700], [8893, 2590, 898]),
        'DOM_00761': ([9489, 2190, 700], [9493, 2590, 898]),
        'DOM_00762': ([8891, 2188, 700], [9491, 2192, 898]),
        'DOM_00763': ([8891, 2588, 700], [9491, 2592, 898]),
        'DOM_00764': ([9156, 2355, 703.5], [9226, 2425, 706.5]),
        'DOM_00765': ([9179, 2440.96899, 900], [9203, 2677, 1231.71425]),
        'DOM_00766': ([9213, 2660, 920], [9221, 2670, 1005]),
    }
    records = [{'id': id_, 'name': name, 'enabled': True, 'metadata': {},
                'boundsMm': dict(zip(('min', 'max'), boxes[id_])),
                'materialNames': [material], 'materialSlots': ['MAT_fixture']}
               for id_, (name, material) in FIXTURES.EXPECTED.items()]
    # A similarly named cabinet is deliberately out of scope.
    records.append({'id': 'DOM_00745', 'name': 'KITCHEN-RUN · ostrovček · drezová skrinka', 'enabled': True})
    return {'activeDesign': {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'},
            'house': {'placement': {'streetSetbackMm': 3000, 'eastSetbackMm': 3000}}, 'objects': records}


class FixtureGeometryTests(unittest.TestCase):
    def test_closed_geometry_respects_source_envelopes_and_excludes_cabinet(self):
        source = scene()
        previous = copy.deepcopy(source)
        meshes, report = FIXTURES.build_geometry(source)
        self.assertEqual(source, previous, 'Visual refinement must not modify source records')
        self.assertEqual({m.id for m in meshes}, {'RF_SINK_BOWL', 'RF_SINK_DRAIN', 'RF_SINK_SPOUT', 'RF_SINK_LEVER'})
        self.assertEqual({id_ for m in meshes for id_ in m.source_ids}, set(FIXTURES.EXPECTED))
        for row in report:
            self.assertEqual(row['nonManifoldEdges'], 0)
            self.assertEqual(row['outwardEnvelopeMm'], 0)
            self.assertGreater(row['minimumTriangleAreaMm2'], 0)
        self.assertLess(sum(row['triangles'] for row in report), 45000)

    def test_geometry_follows_source_placement_instead_of_hard_coded_world_position(self):
        source = scene()
        _, original = FIXTURES.build_geometry(source)
        delta = (1200, -900, 75)
        for record in source['objects']:
            if 'boundsMm' in record:
                for key in ('min', 'max'):
                    record['boundsMm'][key] = [x+d for x, d in zip(record['boundsMm'][key], delta)]
        _, moved = FIXTURES.build_geometry(source)
        for a, b in zip(original, moved):
            for key in ('min', 'max'):
                for i in range(3):
                    self.assertAlmostEqual(b['visualBoundsMm'][key][i]-a['visualBoundsMm'][key][i], delta[i], places=8)

    def test_source_identity_material_and_design_drift_fail_closed(self):
        for field in ('identity', 'material', 'design', 'setback', 'missing', 'duplicate'):
            source = scene()
            if field == 'identity': source['objects'][0]['name'] = 'Another fixture'
            if field == 'material': source['objects'][0]['materialNames'] = ['Oak']
            if field == 'design': source['activeDesign']['variant'] = 'A'
            if field == 'setback': source['house']['placement']['eastSetbackMm'] = 2500
            if field == 'missing': source['objects'].pop(0)
            if field == 'duplicate': source['objects'].append(source['objects'][0])
            with self.subTest(field=field), self.assertRaises(RuntimeError):
                FIXTURES.build_geometry(source)

    def test_outward_expansion_is_detected(self):
        source = scene()
        meshes, _ = FIXTURES.build_geometry(source)
        mesh = meshes[0]
        mesh.vertices[0] = (100000, *mesh.vertices[0][1:])
        with self.assertRaisesRegex(RuntimeError, 'outside authoritative source envelope'):
            FIXTURES.check_mesh(mesh, FIXTURES.source_records(source))

    def test_open_or_degenerate_surfaces_are_detected(self):
        source = scene()
        meshes, _ = FIXTURES.build_geometry(source)
        mesh = meshes[2]
        mesh.faces.pop()
        with self.assertRaisesRegex(RuntimeError, 'closed manifold edges'):
            FIXTURES.check_mesh(mesh, FIXTURES.source_records(source))
        mesh.faces.append((0, 0, 1))
        with self.assertRaisesRegex(RuntimeError, 'Degenerate fixture triangle'):
            FIXTURES.check_mesh(mesh, FIXTURES.source_records(source))

    def test_material_slots_refer_to_current_scene_finishes(self):
        _, report = FIXTURES.build_geometry(scene())
        drain = next(row for row in report if row['id'] == 'RF_SINK_DRAIN')
        self.assertEqual(drain['materialBindings'], [{'sourceId': 'DOM_00759', 'sourceSlot': 0},
                                                    {'sourceId': 'DOM_00764', 'sourceSlot': 0}])
        spout = next(row for row in report if row['id'] == 'RF_SINK_SPOUT')
        self.assertAlmostEqual(spout['visualBoundsMm']['max'][0]-spout['visualBoundsMm']['min'][0], 24)
        self.assertEqual(spout['expectedWorldBoundsCm']['min'][1], -spout['visualBoundsMm']['max'][1]/10)


if __name__ == '__main__':
    unittest.main()
