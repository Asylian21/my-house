"""CPU acceptance guards for room visuals, additive worktop fills and door binding."""
import copy
import importlib.util
from pathlib import Path
import unittest

SPEC = importlib.util.spec_from_file_location('room_details', Path(__file__).with_name('realism-room-details-geometry.py'))
ROOM = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(ROOM)


def fixture_scene():
    boxes = {
        938: ([8847, -2695, 80], [9417, -2669, 930]),
        939: ([9202, -2720, 825], [9352, -2704, 885]),
        940: ([8952, -2733, 825], [9012, -2709, 885]),
        941: ([8897, -2748, 265], [9367, -2698, 735]),
        942: ([8942, -2768, 310], [9322, -2726, 690]),
        943: ([9291.9, -2785.5, 486], [9366.9, -2730.5, 514]),
        1225: ([4081, -346, 540.5], [4261, -166, 585.5]),
        1226: ([4091, -336, 680], [4251, -176, 840]),
        740: ([8181, 2080, 880], [10821, 3000, 900]),
        759: ([8891, 2190, 700], [9491, 2590, 703]),
    }
    for n in range(938, 944): boxes[n+6] = tuple([[x, y, z+890] for x, y, z in boxes[n]])
    objects = []
    for id_, (name, material) in ROOM.EXPECTED.items():
        metadata = {'doorId': ROOM.MOTION_IDS[id_], 'doorMotion': 'HINGED', 'doorSubject': 'APPLIANCE_DOOR'} if id_ in ROOM.MOTION_IDS else {}
        objects.append({'id': id_, 'name': name, 'enabled': True, 'instances': 1, 'metadata': metadata,
                        'boundsMm': dict(zip(('min', 'max'), boxes[int(id_.split('_')[-1])])),
                        'materialNames': [material], 'materialSlots': ['MAT_test']})
    return {'activeDesign': {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'},
            'house': {'placement': {'streetSetbackMm': 3000, 'eastSetbackMm': 3000}}, 'objects': objects}


def doors(scene):
    records = ROOM.source_records(scene)
    def native_bounds(id_):
        b = records[id_]['boundsMm']
        return {'min': [b['min'][0]/10, -b['max'][1]/10, b['min'][2]/10],
                'max': [b['max'][0]/10, -b['min'][1]/10, b['max'][2]/10]}
    return {'doors': [{'id': door_id, 'kind': 'HINGED', 'subject': 'APPLIANCE_DOOR', 'architectural': False,
                      'members': [{'sourceObjectId': id_, 'sourceName': records[id_]['name'],
                                   'hidden': False, 'collision': id_ in ('DOM_00941', 'DOM_00947'),
                                   'runtimeTag': 'BreziDoorMember='+id_, 'closedBoundsCm': native_bounds(id_)}
                                  for id_, id_of_door in ROOM.MOTION_IDS.items() if id_of_door == door_id]}
                     for door_id in sorted(set(ROOM.MOTION_IDS.values()))]}


class RoomDetailsGeometryTests(unittest.TestCase):
    def test_closed_bounded_geometry_preserves_source(self):
        scene = fixture_scene(); original = copy.deepcopy(scene)
        _, rows = ROOM.build_geometry(scene)
        self.assertEqual(scene, original)
        self.assertEqual(len(rows), 18)
        self.assertLess(sum(r['triangles'] for r in rows), 90000)
        self.assertEqual({id_ for r in rows for id_ in r['hiddenSourceIds']}, set(ROOM.HIDE_IDS))
        for row in rows:
            self.assertEqual(row['nonManifoldEdges'], 0)
            self.assertLess(row['outwardEnvelopeMm'], 1e-8)
        self.assertEqual({r['motionSourceId'] for r in rows if r['motionSourceId']}, set(ROOM.MOTION_IDS))

    def test_only_four_additive_fills_leave_countertop_visible(self):
        _, rows = ROOM.build_geometry(fixture_scene())
        patches = [r for r in rows if r['mode'] == 'additive']
        self.assertEqual(len(patches), 4)
        for row in patches:
            self.assertEqual(row['sourceIds'], ['DOM_00740'])
            self.assertEqual(row['hiddenSourceIds'], [])
            self.assertEqual(row['materialBindings'], [{'sourceId': 'DOM_00740', 'sourceSlot': 0}])
            self.assertAlmostEqual(row['visualBoundsMm']['max'][2]-row['visualBoundsMm']['min'][2], 20)
            self.assertLessEqual(row['visualBoundsMm']['max'][0]-row['visualBoundsMm']['min'][0], 22.001)

    def test_moving_door_source_contract_fails_closed(self):
        scene = fixture_scene(); records = ROOM.source_records(scene)
        self.assertEqual(set(ROOM.validate_doors(doors(scene), records)), set(ROOM.MOTION_IDS))
        for change in ('missing', 'hidden', 'architectural', 'tag', 'bounds'):
            contract = doors(scene)
            if change == 'missing': contract['doors'][0]['members'].pop()
            if change == 'hidden': contract['doors'][0]['members'][0]['hidden'] = True
            if change == 'architectural': contract['doors'][0]['architectural'] = True
            if change == 'tag': contract['doors'][0]['members'][0]['runtimeTag'] = 'ordinary-static'
            if change == 'bounds': contract['doors'][0]['members'][0]['closedBoundsCm']['min'][0] += 1
            with self.subTest(change=change), self.assertRaises(RuntimeError): ROOM.validate_doors(contract, records)

    def test_unrelated_static_movable_or_design_identity_rejected(self):
        for change in ('name', 'material', 'door', 'design', 'setback'):
            scene = fixture_scene()
            if change == 'name': scene['objects'][0]['name'] = 'Another appliance'
            if change == 'material': scene['objects'][0]['materialNames'] = ['Oak']
            if change == 'door': scene['objects'][0]['metadata']['doorMotion'] = 'HINGED'
            if change == 'design': scene['activeDesign']['variant'] = 'A'
            if change == 'setback': scene['house']['placement']['streetSetbackMm'] = 2500
            with self.subTest(change=change), self.assertRaises(RuntimeError): ROOM.build_geometry(scene)

    def test_translation_tracks_source_and_keeps_motion_identity(self):
        scene = fixture_scene(); _, before = ROOM.build_geometry(scene)
        for r in scene['objects']:
            for key in ('min', 'max'): r['boundsMm'][key] = [v+d for v, d in zip(r['boundsMm'][key], (123, -456, 78))]
        _, after = ROOM.build_geometry(scene)
        for a, b in zip(before, after):
            self.assertEqual(a['motionSourceId'], b['motionSourceId'])
            for key in ('min', 'max'):
                for i, delta in enumerate((123, -456, 78)):
                    self.assertAlmostEqual(b['visualBoundsMm'][key][i]-a['visualBoundsMm'][key][i], delta, places=8)

    def test_globe_support_is_inside_combined_lamp_envelope(self):
        meshes, rows = ROOM.build_geometry(fixture_scene())
        base = next(m for m in meshes if m.id == 'RD_BOY_LAMP_BASE')
        self.assertTrue(any(586 < v[2] < 680 for v in base.vertices), 'The authored 94.5 mm gap must receive a physical support')
        row = next(r for r in rows if r['id'] == base.id)
        self.assertEqual(row['materialBindings'], [{'sourceId': 'DOM_01225', 'sourceSlot': 0}])
        self.assertEqual(row['hiddenSourceIds'], ['DOM_01225'])


if __name__ == '__main__': unittest.main()
