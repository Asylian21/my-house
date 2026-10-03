"""Exact frozen R8 inputs and independent receipt acceptance/rejection boundaries.

Old immutable QA bytes are timing fixtures only. No test audits an old native
project against shared sources, launches Unreal, or claims native appearance.
"""
from copy import deepcopy
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('fine_greenery_evidence',HERE/'exterior-greenery-fine-audit.py')
audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
R7=ROOT/'output/unreal/exterior-20260930-r7'
R7_SUITE=ROOT/'output/unreal/exterior-validation-20260930-r1/qa/after-exterior-r7-artifacts-1790792235158/summary.json'
R6A=ROOT/'output/unreal/exterior-validation-20260930-r1/qa/after-exterior-r6a-1790787880169/exterior-garden-day-retina-cinematic-static-24839dc5-9439-4725-9633-d6a44953ccd5'


class FineGreeneryEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plans={k:audit.read(ROOT/'output/unreal'/p)for k,(p,_)in audit.PLANS.items()}
        cls.r7_suite=audit.read(R7_SUITE)
        first=Path(cls.r7_suite['results'][0]['evidence'])
        cls.runtime=audit.read(first/'runtime.json');cls.qa=audit.read(first/'qa.json')

    def fine_report(self):
        plan=self.plans['lawn']
        return {'inputFiles':{p['path']:p['sha256']for p in [plan['coverageReceipt'],plan['boundaryCoverageReceipt']]},
            'naturalLawn':{'audit':plan['audit'],'coverageReceipt':plan['coverageReceipt'],
                'boundaryCoverageReceipt':plan['boundaryCoverageReceipt']}}

    def floor_report(self):
        plan=self.plans['substrate'];path,hash_value=audit.PLANS['substrate'];path=str(ROOT/'output/unreal'/path)
        validation={'status':'verified-source-grove-substrate','sourceDomainAreaM2':plan['audit']['domainAreaM2']}
        ids=[m['id']for m in plan['meshes']]
        report={'inputFiles':{path:hash_value},'groveSubstrate':{'plan':path,'planSha256':hash_value,
            'regionId':'village_nearest_grove','audit':plan['audit'],'validation':validation,
            'sourceGroundUnchanged':True,'hiddenOriginalActors':0,'meshIds':ids,
            'savedReadback':{'status':'verified-saved-grove-substrate','meshes':53,
                'allNewVisualsNoCollision':True,'nativeMeshBindingsVerifiedAfterReload':True}},
            'geometry':{'actors':{mid:'/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.TEST_'+mid for mid in ids},
                'meshes':{mid:'/Game/Brezi/Exterior20260926/Geometry/TEST/'+mid+'.'+mid for mid in ids}}}
        return report,validation

    def test_final_five_plans_library_and_independent_coverage_bytes_are_exact(self):
        for name,value in [('geometry-manifest.json',audit.MASTER_SHA),('material-manifest.json',audit.MATERIAL_SHA),
                ('asset-manifest.json',audit.ASSET_SHA)]:self.assertEqual(audit.sha(audit.ASSETS/name),value)
        for path,value in audit.PLANS.values():self.assertEqual(audit.sha(ROOT/'output/unreal'/path),value)
        for path,value in [audit.LAWN_COVERAGE,audit.LAWN_BOUNDARY]:self.assertEqual(audit.sha(ROOT/'output/unreal'/path),value)
        library=audit.read(audit.ASSETS/'geometry-manifest.json')
        self.assertEqual(len(library['meshes']),96);self.assertEqual(len({r['id']for r in library['meshes']}),96)
        self.assertEqual(sum(len(r['lods'])for r in library['meshes']),288)
        self.assertEqual(len(audit.read(audit.ASSETS/'material-manifest.json')),24)

    def test_frozen_actual_fine_count_budget_and_external_boundary_receipt(self):
        result=audit.fine_lawn_receipts(self.fine_report(),self.plans['lawn'])
        self.assertEqual(result['allInstancesTriangleBudgetByLod'],[19842432,14132224,11277120])
        self.assertEqual(result['boundaryCoverage'],self.plans['lawn']['boundaryCoverageReceipt'])

    def test_missing_or_forged_boundary_pin_is_rejected_even_with_correct_main_cover(self):
        for change in ('missing','wrongHash','unsealed'):
            report=self.fine_report();report['naturalLawn']=deepcopy(report['naturalLawn'])
            if change=='missing':report['naturalLawn'].pop('boundaryCoverageReceipt')
            elif change=='wrongHash':report['naturalLawn']['boundaryCoverageReceipt']['sha256']='0'*64
            else:report['inputFiles'].pop(self.plans['lawn']['boundaryCoverageReceipt']['path'])
            with self.assertRaisesRegex(RuntimeError,'boundaryCoverageReceipt'):audit.fine_lawn_receipts(report,self.plans['lawn'])

    def test_exact_unflared_scope_rejects_old_conical_collar_population(self):
        validation={'status':'verified-source-grove-ecology','instances':24773,'groups':130,'qualityDetailGroups':130,'basalGroups':0}
        report={'canopyEcology':{'validation':validation}}
        audit.unflared_scope(report,self.plans['ecology'],validation)
        original=audit.read(ROOT/'output/unreal/exterior-canopy-ecology-20260930-r3/canopy-ecology-plan.json')
        with self.assertRaisesRegex(RuntimeError,'unflared ecology source/count'):audit.unflared_scope(report,original,validation)
        unsafe={**self.plans['ecology'],'ecologyPlacements':[{'ecologyFamily':'flare'}]}
        with self.assertRaisesRegex(RuntimeError,'unflared ecology source/count'):audit.unflared_scope(report,unsafe,validation)

    def test_actual_substrate_schema_requires_53_saved_unique_bindings_and_no_collision(self):
        report,validation=self.floor_report();result=audit.substrate_readback(report,self.plans['substrate'],validation)
        self.assertEqual((result['meshes'],result['vertices'],result['triangles']),(53,216024,406669))
        for change in ('missingMesh','sharedActor','wrongCollisionReadback'):
            report,validation=self.floor_report();ids=report['groveSubstrate']['meshIds']
            if change=='missingMesh':report['geometry']['meshes'].pop(ids[0])
            elif change=='sharedActor':report['geometry']['actors'][ids[0]]=report['geometry']['actors'][ids[1]]
            else:report['groveSubstrate']['savedReadback']['allNewVisualsNoCollision']=False
            with self.assertRaisesRegex(RuntimeError,'Substrate'):audit.substrate_readback(report,self.plans['substrate'],validation)

    def test_wrong_substrate_source_pin_and_hidden_original_ground_are_rejected(self):
        for change in ('oldHash','hiddenGround'):
            report,validation=self.floor_report()
            if change=='oldHash':report['groveSubstrate']['planSha256']='0'*64
            else:report['groveSubstrate']['hiddenOriginalActors']=1
            with self.assertRaisesRegex(RuntimeError,'substrate|Substrate'):audit.substrate_readback(report,self.plans['substrate'],validation)

    def test_exact_observed_embedded_vs_offline_polygon_sum_delta_is_bounded_and_recorded(self):
        native={'sourceDomainAreaM2':3055.2104873854855,'triangles':406669,'sourceGroundUnchanged':True,'sha':'a'*64}
        recomputed={**native,'sourceDomainAreaM2':3055.210487385485}
        result=audit.substrate_validation_comparison(native,recomputed)
        self.assertTrue(result['countsHashesFlagsAndAllOtherFieldsExactlyCanonical'])
        leaf=result['boundedNumericalLeaves'][0]
        self.assertEqual(leaf['path'],'validation.sourceDomainAreaM2');self.assertEqual(leaf['absoluteTolerance'],1e-9)
        self.assertEqual(leaf['absoluteDifference'],4.547473508864641e-13)

    def test_numeric_area_bound_rejects_larger_nonfinite_and_wrong_typed_claims(self):
        recomputed={'sourceDomainAreaM2':3055.210487385485,'triangles':406669}
        for value in (3055.210487385485+1e-8,float('nan'),float('inf'),3055,True):
            with self.assertRaisesRegex(RuntimeError,'explicit recomputation tolerance'):
                audit.substrate_validation_comparison({**recomputed,'sourceDomainAreaM2':value},recomputed)

    def test_numeric_sum_exception_never_relaxes_counts_flags_hashes_or_keys(self):
        recomputed={'sourceDomainAreaM2':3055.210487385485,'triangles':406669,'sourceGroundUnchanged':True,'sha':'a'*64}
        for key,value in [('triangles',406670),('sourceGroundUnchanged',1),('sha','b'*64),('extra',True)]:
            with self.assertRaisesRegex(RuntimeError,'validation differs|keys differ'):
                audit.substrate_validation_comparison({**recomputed,key:value},recomputed)

    def test_old_r7_import_and_package_rejected_before_any_live_source_read(self):
        with patch.object(audit,'read',side_effect=AssertionError('Old live project must not be read')):
            for call in [lambda:audit.audit_import(R7),lambda:audit.audit_package(R7)]:
                with self.assertRaisesRegex(RuntimeError,'only the exact R8 candidate'):call()

    def test_old_r7_suite_and_duplicate_or_missing_views_cannot_be_relabelled_r8(self):
        with self.assertRaisesRegex(RuntimeError,'older suites'):audit.qa_identity(self.r7_suite,audit.SOURCE,'f'*64)
        summary=deepcopy(self.r7_suite);summary['source']=str(audit.SOURCE);summary['packageReportSha256']='f'*64
        audit.qa_identity(summary,audit.SOURCE,'f'*64)
        for change in ('missing','duplicate'):
            unsafe=deepcopy(summary)
            if change=='missing':unsafe['results'].pop()
            else:unsafe['results'][0]['scene']=unsafe['results'][1]['scene']
            with self.assertRaisesRegex(RuntimeError,'six-view'):audit.qa_identity(unsafe,audit.SOURCE,'f'*64)

    def test_actual_r7_foreground_intervals_eligible_without_visual_or_performance_acceptance(self):
        result=audit.timing_evidence(self.runtime,self.qa)
        self.assertTrue(result['timingValid']);self.assertFalse(result['performanceAccepted'])
        self.assertEqual(result['sampleCount'],300);self.assertEqual(result['applicationForegroundSamples'],300)
        self.assertEqual(result['gameWindowActiveSamples'],300);self.assertEqual(result['sceneViewportKeyboardFocusSamples'],300)

    def test_partial_window_or_application_focus_invalid_in_strict_and_artifact_modes(self):
        for field in ('applicationForegroundSamples','gameWindowActiveSamples'):
            runtime,qa=deepcopy(self.runtime),deepcopy(self.qa)
            runtime['focusDuringBenchmark'][field]=299;qa['foreground']=runtime['focusDuringBenchmark']
            with self.assertRaisesRegex(RuntimeError,'Timing invalid'):audit.timing_evidence(runtime,qa)
            result=audit.timing_evidence(runtime,qa,True)
            self.assertTrue(result['timingInvalid']);self.assertFalse(result['performanceAccepted'])

    def test_actual_locked_old_qa_has_explicit_invalid_artifact_timing(self):
        runtime,qa=audit.read(R6A/'runtime.json'),audit.read(R6A/'qa.json')
        with self.assertRaisesRegex(RuntimeError,'Timing invalid'):audit.timing_evidence(runtime,qa)
        result=audit.timing_evidence(runtime,qa,True)
        self.assertTrue(result['timingInvalid']);self.assertFalse(result['timingValid']);self.assertFalse(result['performanceAccepted'])
        self.assertIn('cannot establish',result['timingInvalidReason'])

    def test_old_r7_material_39_and_texture_70_receipt_is_not_r8(self):
        # This count guard runs before checking current shared pipeline bytes.
        with self.assertRaisesRegex(RuntimeError,'recipe/texture count'):
            audit.audit_materials(R7,audit.read(R7/'exterior-import-report.json'))


if __name__=='__main__':unittest.main()
