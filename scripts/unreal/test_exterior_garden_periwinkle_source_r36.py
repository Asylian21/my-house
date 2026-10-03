"""Six bounded source/whole-attribute fixtures; no Unreal or visibility proof."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
s=importlib.util.spec_from_file_location('r36_source_fixture',ROOT/'scripts/unreal/exterior-garden-periwinkle-study-r36.py')
m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


class SourceFixtures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=m.read(m.OUT/'periwinkle-source-plan.json');cls.report=m.read(m.REPORT)
        cls.garden=m.read(m.GARDEN);cls.r34=m.read(m.R34);cls.doc,cls.bin,cls.models=m.decode_provider()
    def rejected_decode(self,doc,bin_data=None):
        old=m.ASSETS
        try:
            with tempfile.TemporaryDirectory()as d:
                m.ASSETS=Path(d);(m.ASSETS/'periwinkle_plant_2k.gltf').write_text(json.dumps(doc))
                (m.ASSETS/'periwinkle_plant.bin').write_bytes(self.bin if bin_data is None else bin_data)
                with self.assertRaises(RuntimeError):m.decode_provider()
        finally:m.ASSETS=old
    def test_actual_four_low_groups_384_and_all_protected_identity(self):
        low,flowers,heroes,groups=m.current_source(self.report,self.garden,self.r34)
        self.assertEqual([g['currentRootCount']for g in groups],[58,47,146,133])
        self.assertEqual((len(low),len(flowers),len(heroes)),(384,41,12))
        self.assertEqual(set(r['id']for r in low),set(p['rootId']for p in self.plan['proposedPlacements']))
        self.assertEqual(set(p['rootId']for p in self.r34['proposedPlacements']),set(self.plan['preservedR34FernRootIds']))
        self.assertEqual(len(self.plan['preservedR34FernRootIds']),36)
        bad=copy.deepcopy(self.r34);first=next(k for k in bad['originalGardenGroupBindings']if k.startswith('EX_groundcover_'))
        bad['originalGardenGroupBindings'].pop(first)
        with self.assertRaises(RuntimeError):m.current_source(self.report,self.garden,bad)
    def test_export_original_bin_all_six_attrs_indices_and_display_only(self):
        raw=(m.OUT/'periwinkle-whole-originals.glb').read_bytes();self.assertEqual(raw,m.export_original_glb(self.doc,self.bin))
        length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);bin_at=20+length+8
        self.assertEqual(raw[bin_at:bin_at+len(self.bin)],self.bin)
        self.assertEqual(doc['accessors'],self.doc['accessors']);self.assertEqual(doc['bufferViews'],self.doc['bufferViews']);self.assertEqual(doc['meshes'],self.doc['meshes'])
        self.assertTrue(all('translation'not in n for n in doc['nodes']))
        wanted={'POSITION','NORMAL','TEXCOORD_0','TEXCOORD_1','COLOR_0','COLOR_1'}
        self.assertTrue(all(set(p['attributes'])==wanted for mesh in doc['meshes']for p in mesh['primitives']))
        self.assertEqual(sum(v['sourceTriangles']for v in self.models.values()),34350)
    def test_legacy_attribute_trimming_is_rejected(self):
        for attribute in ('TEXCOORD_1','COLOR_0','COLOR_1'):
            doc=copy.deepcopy(self.doc);doc['meshes'][0]['primitives'][0]['attributes'].pop(attribute)
            self.rejected_decode(doc)
    def test_source_color0_unity_assumption_mutation_rejects(self):
        doc=self.doc;i=doc['meshes'][0]['primitives'][0]['attributes']['COLOR_0'];a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']]
        data=bytearray(self.bin);offset=v.get('byteOffset',0)+a.get('byteOffset',0);data[offset]=254
        self.rejected_decode(doc,bytes(data))
    def test_declared_contact_uniform_height_and_full_mask_counts(self):
        counts={k:0 for k in self.models};vertices=triangles=0
        for p in self.plan['proposedPlacements']:
            model=self.models[p['model']];counts[p['model']]+=1;vertices+=model['sourceVertices'];triangles+=model['sourceTriangles']
            self.assertGreater(p['uniformScale'],0);self.assertEqual(p['scale'],[p['uniformScale']]*3)
            self.assertEqual(p['positionCm'][:2],p['originalRow']['positionCm'][:2]);self.assertEqual(p['yawDeg'],p['originalRow']['yawDeg'])
            self.assertEqual(p['positionCm'][2],p['sourceContactPositionCm'][2]-p['uniformScale']*model['originalNativeF32BottomCm'])
            self.assertLessEqual(p['radiusCm'],.99*p['originalRow']['radiusCm']);self.assertGreater(p['bedBoundaryClearanceCm'],0);self.assertGreater(p['stepBoundaryClearanceCm'],0)
            self.assertTrue(p['allFullSourceVerticesInsideOriginalBed']and p['fullCircleExcludesOriginalSteps'])
        self.assertEqual(counts,self.plan['providerModelCounts']);self.assertTrue(all(v>0 for v in counts.values()))
        self.assertEqual(vertices,self.plan['sourceVerticesInsideBedsChecked']);self.assertEqual(triangles,2105220)
        helper=m.module('r36_fixture_steps','exterior-garden-composition-step-guards-r3.py')
        bad=copy.deepcopy(self.garden['sourceStepTrianglesCm']);bad['DOM_01961'][0][0][0]+=.01
        with self.assertRaises(RuntimeError):helper.validated_steps(bad)
    def test_frozen_input_original_optics_and_source_support_limits(self):
        self.assertTrue(all(m.sha(p)==h for p,h in self.plan['inputFiles'].items()))
        recipe=m.read(m.OUT/'material-recipe.json');support=m.read(m.OUT/'source-camera-support.json')
        self.assertEqual(recipe['sourceOriginalAlphaMode'],'BLEND');self.assertEqual(recipe['proposedEngineBlendMode'],'MASKED')
        self.assertEqual((recipe['clipValue'],recipe['subsurfaceCalibration'],recipe['metallic']),(.5,.08,0))
        self.assertEqual(len(recipe['maps']),5);self.assertEqual(support['oldTriangleSupportPixels'],112203);self.assertEqual(support['newTriangleSupportPixels'],89853)
        self.assertFalse(support['alphaPixelsMeasured']);self.assertFalse(support['plantHouseTerrainOcclusionVerified'])
        self.assertTrue(all(self.plan[k]is False for k in ('nativeApplied','gpuExecuted','nativeExecuted','nativeGeometryVerified','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified')))


if __name__=='__main__':unittest.main(verbosity=2)
