"""Bounded real-source R24 tangent extension and adversarial CPU checks."""
from copy import deepcopy
import importlib.util
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
s = importlib.util.spec_from_file_location('r24_tangent_source',ROOT/'scripts/unreal/exterior-original-tree-tangent-study.py')
m = importlib.util.module_from_spec(s); s.loader.exec_module(m)


class OriginalTreeTangentSource(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = m.read(m.OUTPUT/'original-tree-tangent-supplement-r2.json')
        cls.proof = m.read(m.check_pin(cls.plan['tangentProof']))
        cls.r1 = m.read(m.R1/'candidate-original-tree.gltf')
        cls.doc = m.read(m.check_pin(cls.plan['candidateDescriptor']))
        cls.counts = [62772,1698569,15937]
        cls.byte_count = sum(cls.counts)*16
        cls.original = m.read(m.source.REFERENCE/'tree_small_02/tree_small_02_2k.gltf')
        cls.binary = (m.source.REFERENCE/'tree_small_02/tree_small_02.bin').read_bytes()

    def validate(self, value):
        m.validate_descriptor(value,self.r1,m.OUTPUT,self.counts,self.byte_count)

    def test_actual_three_parts_append_only_derived_attributes(self):
        self.validate(self.doc)
        self.assertEqual(self.proof['sourceTriangles'],2062487)
        self.assertEqual(self.byte_count,28436448)
        self.assertEqual(self.doc['materials'],self.r1['materials'])
        self.assertEqual(self.doc['nodes'],self.r1['nodes'])
        self.assertFalse(self.proof['providerTangentsPresent'])
        self.assertFalse(self.proof['nativeNormalTangentReadbackAvailable'])
        self.assertIsNone(self.plan['pendingNativeBase']['selectedNativeReport'])

    def test_branch_uv_substitution_and_khr_loss_rejected(self):
        for mode in ('uv','khr'):
            doc = deepcopy(self.doc)
            if mode == 'uv': doc['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_1'] = doc['meshes'][0]['primitives'][0]['attributes']['TEXCOORD_0']
            else: del doc['materials'][0]['normalTexture']['extensions']
            with self.subTest(mode=mode), self.assertRaises(ValueError): self.validate(doc)

    def test_index_rewrite_and_derived_accessor_substitution_rejected(self):
        for mode in ('index','tangent'):
            doc = deepcopy(self.doc); p = doc['meshes'][0]['primitives']
            if mode == 'index': p[0]['indices'] = p[1]['indices']
            else: p[0]['attributes']['TANGENT'] = p[1]['attributes']['TANGENT']
            with self.subTest(mode=mode), self.assertRaises(ValueError): self.validate(doc)

    def test_original_normal_rewrite_and_extra_root_rejected(self):
        for mode in ('normal','root'):
            doc = deepcopy(self.doc)
            if mode == 'normal': doc['meshes'][0]['primitives'][0]['attributes']['NORMAL'] = doc['meshes'][0]['primitives'][1]['attributes']['NORMAL']
            else: doc['nodes'].append(deepcopy(doc['nodes'][0]))
            with self.subTest(mode=mode), self.assertRaises(ValueError): self.validate(doc)

    def test_source_corner_frame_conflict_and_false_typed_status_rejected(self):
        report = m.read(m.check_pin(self.proof['parts'][0]['perCornerMikkReport']))
        m.validate_mikk_report(report,62772,284442)
        for key,value in [('sharedIndexBinary32CornerConflicts',1),('sharedIndexHandednessConflicts',1),('unreferencedVertices',1),('mikkSucceeded',1),('nativeOrGpuExecuted',True)]:
            row = deepcopy(report); row[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError): m.validate_mikk_report(row,62772,284442)

    def test_native_material_basis_is_explicit_uv1_without_uv_rewrite(self):
        materials = m.read(m.check_pin(self.plan['materialProposal']))
        branch = materials[0]['nativeProposal']['normalTangentBasis']
        self.assertEqual(branch['texCoord'],1)
        self.assertEqual(branch['KHRTextureTransform'],{'offset':[0,.40000009536743164],'scale':[3,.5999999046325684]})
        self.assertTrue(branch['derivedAttribute']); self.assertFalse(branch['providerTangentAttribute'])
        self.assertFalse(branch['nativeTangentBasisVerified']); self.assertFalse(branch['nativeImportRecomputeTangents'])
        source_materials = m.read(m.R1/'original-tree-material-proposal.json')
        rows = deepcopy(self.proof['parts']); rows[0]['normalTextureTexCoord'] = 0
        with self.assertRaises(ValueError): m.material_proposal(source_materials,rows)

    def test_nonfinite_nonunit_and_invalid_handedness_tangents_rejected(self):
        primitive = self.original['meshes'][0]['primitives'][2]
        data = m.check_pin(self.proof['parts'][2]['derivedTangents']).read_bytes()
        for tangent in [(float('nan'),0.,0.,1.),(4.,4.,4.,1.),(1.,0.,0.,0.)]:
            altered = struct.pack('<ffff',*tangent)+data[16:]
            with self.subTest(tangent=tangent), self.assertRaises(ValueError): m.tangent_metrics(self.binary,self.original,primitive,altered)

    def test_actual_mikk_rejects_incompatible_shared_vertex_without_reindexing(self):
        # Two indexed triangles share one vertex with opposite UV handedness.
        # Mikk's per-corner frames cannot be represented by one original vec4.
        points = [(0.,0.,0.),(1.,0.,0.),(0.,1.,0.),(1.,0.,0.),(0.,-1.,0.)]
        normals = [(0.,0.,1.)]*5; uvs = [(0.,0.),(1.,0.),(0.,1.),(1.,0.),(0.,-1.)]
        raw = b''.join(struct.pack('<fff',*v) for v in points+normals)+b''.join(struct.pack('<ff',*v) for v in uvs)+struct.pack('<6H',0,1,2,0,3,4)
        executable = m.check_pin(m.read(m.check_pin(self.plan['cpuBuildReceipt']))['executable'])
        with tempfile.TemporaryDirectory(prefix='r24-mikk-conflict-') as directory:
            d = Path(directory); path = d/'source.bin'; path.write_bytes(raw)
            args = [str(executable),str(path),'5','6','0','60','120','160','12','12','8','2','2','1','1','0','0',str(d/'t.bin'),str(d/'report.json')]
            result = subprocess.run(args,capture_output=True,text=True)
            self.assertEqual(result.returncode,3,result.stderr)
            report = m.read(d/'report.json'); self.assertGreater(report['sharedIndexHandednessConflicts'],0)
            self.assertFalse((d/'t.bin').exists()); self.assertEqual(path.read_bytes(),raw)

    def test_all_frozen_r1_and_provider_inputs_rehash_unchanged(self):
        for name,row in self.plan['inputFiles'].items():
            with self.subTest(input=name): m.check_pin(row)
        self.assertEqual(m.sha(m.R1/'original-tree-source-plan.json'),m.R1_SHA)


if __name__ == '__main__': unittest.main(verbosity=2)
