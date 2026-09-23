"""Scope and exported-container checks for bounded visual geometry details."""
import importlib.util
import json
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('photoreal_geometry', Path(__file__).with_name('photoreal-geometry.py'))
geometry = importlib.util.module_from_spec(spec); spec.loader.exec_module(geometry)


class GeometryScopeTests(unittest.TestCase):
    def record(self, **updates):
        result = {'enabled':True,'name':'KITCHEN-RUN · dubový blok','group':'Interior',
                  'materialNames':['Kitchen 2026 · prírodný dub'],'triangles':12,'metadata':{}}
        result.update(updates)
        return result

    def test_dynamic_doors_are_never_visual_replacements(self):
        self.assertIsNone(geometry.recipe(self.record(metadata={'doorMotion':'HINGED'})))
        self.assertIsNone(geometry.recipe(self.record(name='GARAGE-DOOR · sekcia 1 z 8', group='Roof', materialNames=['real-roof-edge'])))

    def test_archived_geometry_is_not_resurrected(self):
        self.assertIsNone(geometry.recipe(self.record(enabled=False)))

    def test_roof_finish_name_does_not_replace_door_leaf(self):
        self.assertIsNone(geometry.recipe(self.record(name='Bočná výplň · plné krídlo otvárané von',group='Roof',materialNames=['real-roof-edge'])))

    def test_sofa_frame_is_not_treated_as_loose_cushion(self):
        rec = self.record(name='LIVING-103-SOFA-L · TAILORED · ležadlo · čalúnený rám',
                          materialNames=['Living warm sofa | real-interior-upholstery'], triangles=1200)
        self.assertIsNone(geometry.recipe(rec))

    def test_final_glb_has_exact_material_slot_order_and_bound_envelopes(self):
        folder = ROOT/'output/unreal/photoreal-20260923/photoreal-geometry'
        if not (folder/'geometry-report.json').exists():
            self.skipTest('Run the Blender detail export for the optional artifact audit')
        report = json.loads((folder/'geometry-report.json').read_text())
        binary = (folder/'photoreal-details.glb').read_bytes()
        magic,version,length = struct.unpack_from('<III',binary)
        self.assertEqual((magic,version,length),(0x46546c67,2,len(binary)))
        count,kind = struct.unpack_from('<II',binary,12)
        self.assertEqual(kind,0x4e4f534a)
        glb = json.loads(binary[20:20+count])
        nodes = {n['name']:n for n in glb['nodes']}
        self.assertEqual(set(nodes),{r['id'] for r in report['objects']})
        self.assertEqual(report['glbSha256'],geometry.sha(folder/'photoreal-details.glb'))
        self.assertLessEqual(report['roundtripErrorMm'],.05)
        for record in report['objects']:
            node = nodes[record['id']]
            self.assertEqual(node['extras']['photoreal_source_id'],record['sourceId'])
            self.assertNotIn('source_object_id',node['extras'])
            mesh = glb['meshes'][node['mesh']]
            indices = dict.fromkeys(p['material'] for p in mesh['primitives'])
            self.assertEqual([glb['materials'][i]['name'] for i in indices],record['materialSlots'])
            self.assertLessEqual(record['outwardEnvelopeMm'],1.1)
            self.assertLessEqual(record.get('maxDeformationMm',0),5.5)


if __name__ == '__main__':
    unittest.main()
