"""Adversarial CPU-only tests. No native acceptance receipt is changed."""
import copy
import hashlib
import importlib.util
import sys
from unittest import mock
import json
import math
import struct
import tempfile
import unittest
from pathlib import Path

import identity_policy as identity
BASE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('validate_capture', BASE / 'validate_capture.py')
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)
POLICY_PATH = BASE.parent / 'Resources/receiver-identity-policy.json'
CONTRACT_PATH = BASE.parent / 'Resources/receiver-contract.json'



class PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ref = validator.ref
        cls.policy = identity.IdentityPolicy(CONTRACT_PATH, POLICY_PATH, cls.ref)
        cls.meta = json.loads((BASE.parent / 'Resources/receiver-identity-test-fixture.json').read_text())
        cls.index = cls.meta['photonIndex']
        floor = next(o for o in cls.policy.contract['receiverObjects'] if o['id'] == identity.FLOOR_ID)
        lo, hi = floor['boundsMm']['min'], floor['boundsMm']['max']
        ap = lo[0]/1000, -hi[1]/1000, (hi[0]-lo[0])/1000, (hi[1]-lo[1])/1000
        nx,ny=cls.meta['launchSize']
        cls.origin=(ap[0]+(cls.index%nx+.5)*ap[2]/nx,ap[1]+(cls.index//nx+.5)*ap[3]/ny,cls.policy.contract['waterMeanPlaneMetres'])
        incident=cls.ref.unit(cls.meta['sunRayDirection'])
        cls.direction,_=cls.ref.refract(incident,cls.ref.normal(cls.origin[0],cls.origin[1],cls.meta['shaderTimeSeconds'],cls.policy.contract['authoredWaves']))
        cls.photon=struct.unpack('<12f',bytes.fromhex(cls.meta['photonRecordHex']))
        cls.expected=cls.policy.bvh.first(cls.origin,cls.direction)[0][0]
        cls.a=cls.policy.triangles[cls.expected]
        cls.b=cls.policy.triangles[int(cls.photon[10])]

    def explain(self, photon=None, expected=None):
        return self.policy.explain(self.origin,self.direction,photon or self.photon,self.expected if expected is None else expected)

    def test_actual_source_pair_is_explained_without_rewriting_identity(self):
        proof=self.explain()
        self.assertEqual(proof['outcome'],'listed-f32-ambiguous-nonfloor-identity')
        self.assertFalse(proof['sourceIdentityRewritten'])
        self.assertFalse(proof['productionUseAllowed'])
        self.assertLessEqual(proof['sourcePlaneSeparationMetres'],proof['planeQuantizationBoundMetres'])
        self.assertLess(max(proof['pointBudgetMetres']),identity.MAX_POINT_ERROR_METRES)

    def test_packet_energy_and_identity_bytes_are_preserved(self):
        packet=list(self.photon);before=struct.pack('<12f',*packet)
        self.explain(packet)
        self.assertEqual(struct.pack('<12f',*packet),before)

    def test_foreign_triangle_is_rejected(self):
        p=list(self.photon);p[10]=0;p[9]=0
        with self.assertRaisesRegex(ValueError,'foreign triangle'):self.explain(p)

    def test_incorrect_object_id_for_reviewed_triangle_is_rejected(self):
        p=list(self.photon);p[9]=self.policy.object_ids.index('DOM_01724')
        with self.assertRaisesRegex(ValueError,'belongs to another object'):self.explain(p)

    def test_hit_outside_calculated_quantization_bound_is_rejected(self):
        proof=self.explain();p=list(self.photon);p[0]+=10*proof['pointBudgetMetres'][0]
        with self.assertRaisesRegex(ValueError,'outside source-derived'):self.explain(p)

    def test_ray_outside_candidate_triangle_footprints_is_rejected(self):
        origin=(self.origin[0],-9,self.origin[2])
        with self.assertRaisesRegex(ValueError,'footprints'):
            identity.classify_pair(origin,self.direction,self.photon,self.a,self.b,self.policy.classes)

    def test_different_signed_normal_is_rejected(self):
        b=copy.deepcopy(self.b);b['verticesMetres'][1],b['verticesMetres'][2]=b['verticesMetres'][2],b['verticesMetres'][1]
        with self.assertRaisesRegex(ValueError,'signed source normals'):identity.pair_certificate(self.a,b,self.policy.classes)

    def test_different_receiver_class_is_rejected(self):
        classes=dict(self.policy.classes);classes[self.b['objectId']]='floor-atlas'
        with self.assertRaisesRegex(ValueError,'receiver class'):identity.pair_certificate(self.a,self.b,classes)

    def test_floor_identity_cannot_be_reclassified_even_with_spoofed_role(self):
        b=copy.deepcopy(self.b);b['objectId']=identity.FLOOR_ID
        classes={**self.policy.classes,identity.FLOOR_ID:identity.TERMINAL}
        with self.assertRaisesRegex(ValueError,'floor receiver'):identity.pair_certificate(self.a,b,classes)

    def test_adjacent_float32_plane_is_rejected_despite_tiny_distance(self):
        b=copy.deepcopy(self.b)
        for v in b['verticesMetres']:v[0]+=identity.ulp32(v[0])
        with self.assertRaisesRegex(ValueError,'same uploaded float32'):identity.pair_certificate(self.a,b,self.policy.classes)

    def test_claimed_cpu_hit_cannot_skip_actual_nearest_source_triangle(self):
        with self.assertRaisesRegex(ValueError,'not the independent source first hit'):self.explain(expected=54)

    def test_floor_packet_status_is_never_allowed(self):
        p=list(self.photon);p[3]=0
        with self.assertRaisesRegex(ValueError,'nonfloor status'):self.explain(p)

    def test_path_length_outside_bound_is_rejected(self):
        p=list(self.photon);p[7]+=.0001
        with self.assertRaisesRegex(ValueError,'path lies outside'):self.explain(p)

    def test_nonfinite_photon_is_rejected(self):
        p=list(self.photon);p[7]=math.nan
        with self.assertRaisesRegex(ValueError,'invalid photon'):self.explain(p)

    def test_grazing_case_is_not_generalized(self):
        direction=(.1,0,-math.sqrt(.99))
        with self.assertRaisesRegex(ValueError,'grazing'):
            identity.classify_pair(self.origin,direction,self.photon,self.a,self.b,self.policy.classes)

    def test_foreign_contract_bytes_are_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            c=copy.deepcopy(self.policy.contract);c['triangles'][0]['verticesMetres'][0][0]+=.000001
            p=Path(d)/'contract.json';p.write_text(json.dumps(c))
            with self.assertRaisesRegex(ValueError,'unreviewed receiver contract'):
                identity.IdentityPolicy(p,POLICY_PATH,self.ref)

    def test_original_unexplained_threshold_is_preserved(self):
        self.assertEqual(self.policy.policy['unexplainedMismatchThreshold'],.001)
        self.assertEqual(validator.UNEXPLAINED_IDENTITY_THRESHOLD,.001)
        self.assertFalse(self.policy.policy['floorEquivalenceAllowed'])

    def test_policy_pins_match_exact_reviewed_bytes(self):
        sha=hashlib.sha256(POLICY_PATH.read_bytes()).hexdigest()
        self.assertEqual(identity.REVIEWED_POLICY_SHA256,sha)
        self.assertEqual(validator.REVIEWED_IDENTITY_POLICY_SHA256,sha)

    def test_helper_rejects_external_policy_candidate_expansion(self):
        policy=copy.deepcopy(self.policy.policy)
        policy['reviewedDirectedPairs'].append([55,0])
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'expanded.json';path.write_text(json.dumps(policy))
            with self.assertRaisesRegex(ValueError,'Unreviewed identity policy bytes'):
                identity.IdentityPolicy(CONTRACT_PATH,path,self.ref)

    def test_helper_rejects_even_semantically_identical_policy_reformatting(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'changed.json';path.write_bytes(POLICY_PATH.read_bytes()+b' ')
            with self.assertRaisesRegex(ValueError,'Unreviewed identity policy bytes'):
                identity.IdentityPolicy(CONTRACT_PATH,path,self.ref)

    def test_validator_has_independent_pin_when_helper_pin_changes(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'Resources').mkdir();changed=POLICY_PATH.read_bytes()+b' '
            (root/'Resources/receiver-identity-policy.json').write_bytes(changed)
            with mock.patch.object(validator,'BASE',root/'Tools'), mock.patch.object(validator.identity,'REVIEWED_POLICY_SHA256',hashlib.sha256(changed).hexdigest()):
                with self.assertRaisesRegex(AssertionError,'Unreviewed identity policy bytes in validator'):
                    validator.load_identity_policy(CONTRACT_PATH)

    def test_validator_rejects_pin_disagreement(self):
        with mock.patch.object(validator.identity,'REVIEWED_POLICY_SHA256','0'*64):
            with self.assertRaisesRegex(AssertionError,'pins disagree'):
                validator.load_identity_policy(CONTRACT_PATH)

    def test_brdf_material_identity_is_not_a_supported_equivalence_class(self):
        classes={k:'same-material' for k in self.policy.classes}
        with self.assertRaisesRegex(ValueError,'receiver class'):
            identity.pair_certificate(self.a,self.b,classes)

    def test_reverse_pair_is_not_implicitly_accepted(self):
        self.assertNotIn((int(self.photon[10]),self.expected),self.policy.pairs)
        self.assertEqual(len(self.policy.pairs),20)
        self.assertEqual(len(self.policy.candidate_indices),12)


if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(PolicyTests)
    result=unittest.TextTestRunner(stream=sys.stderr,verbosity=2).run(suite)
    print(json.dumps({'status':'CPU-identity-policy-tests-passed' if result.wasSuccessful() else 'failed',
                      'testsRun':result.testsRun,'nativeBuildOrGPUExecuted':False}))
    raise SystemExit(0 if result.wasSuccessful() else 1)
