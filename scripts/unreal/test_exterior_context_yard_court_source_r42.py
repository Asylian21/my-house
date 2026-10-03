"""Four bounded actual-source R42 contracts; no Unreal or historical replay."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('r42_new_court_source',ROOT/'scripts/unreal/exterior-context-yard-court-study-r42.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)


class CourtSourceContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bundle=p.load_source();cls.mesh=p.proposed_mesh(cls.bundle)

    def test_01_concave_notch_and_all_f32_triangle_support_stay_in_exact_court(self):
        court=p.shape(self.bundle['court']['domainCm']);entry=p.shape(self.bundle['entry']['domainCm'])
        mesh=self.mesh
        for offset in range(0,len(mesh['indices']),3):
            face=p.Polygon([mesh['verticesCm'][i][:2]for i in mesh['indices'][offset:offset+3]])
            self.assertTrue(court.covers(face));self.assertEqual(face.intersection(entry).area,0.)
        self.assertLessEqual(len(mesh['indices'])//3,p.MAX_TRIANGLES)
        self.assertTrue(all(p.native_coordinate(v)==v for row in mesh['verticesCm']for v in row))
        bad=copy.deepcopy(mesh);bad['verticesCm'][0][:2]=[6500.,26000.]
        self.assertFalse(court.covers(p.Point(bad['verticesCm'][0][:2])))

    def test_02_shared_entry_has_no_raised_ridge_and_actual_edge_is_two_to_three_cm(self):
        near=[r for r in self.mesh['sourceGroundWitnesses']if r['entryDistanceCm']<=12.]
        self.assertGreater(len(near),0)
        self.assertTrue(all(r['authoredReliefCm']==.06 for r in near))
        maximum=max(r['decodedSourceReliefCm']for r in self.mesh['sourceGroundWitnesses'])
        self.assertGreater(maximum,2.);self.assertLess(maximum,3.)
        self.assertEqual(self.mesh['collision'],'NoCollision')
        self.assertFalse(self.mesh['sharedEntryInterfaceRaisedEdgeProposed'])

    def test_03_all_exclusions_and_thirteen_original_shrub_envelopes_are_clear(self):
        union=p.shape(self.mesh['projectedTriangleUnionCm'])
        for domain in self.bundle['masks'].values():self.assertEqual(union.intersection(p.shape(domain)).area,0.)
        self.assertEqual(len(self.bundle['layout']['planting']),13)
        for row in self.bundle['layout']['planting']:
            crown=p.Point(row['positionCm'][:2]).buffer(row['radialEnvelopeCm'])
            self.assertEqual(union.intersection(crown).area,0.)
        self.assertEqual(self.bundle['court']['sourceAreaM2'],9.817431384870023)
        self.assertEqual(self.bundle['entry']['sourceAreaM2'],6.638567479134447)

    def test_04_metric_original_photo_and_existing_witness_are_reference_only(self):
        material=p.material_proposal(self.bundle)
        self.assertEqual(material['license'],'CC0-1.0');self.assertEqual(material['physicalTileCm'],180.)
        self.assertEqual(set(material['originalMaps']),{'diffuse','normal','roughness'})
        self.assertFalse(material['sourcePhotoPixelsEdited']);self.assertFalse(material['nativeSharedTextureObjectAvailabilityVerified'])
        self.assertTrue(self.mesh['originalCourtStillRetainedUnderAndOutsideOverlay'])
        self.assertFalse(self.mesh['nativeExportPerformed']);self.assertFalse(self.mesh['nativeApplied'])
        self.assertEqual(self.bundle['actor']['label'],'context_yard_r28_service_court')
        self.assertEqual(self.bundle['actor']['transform'],[[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]])


if __name__=='__main__':unittest.main(verbosity=2)
