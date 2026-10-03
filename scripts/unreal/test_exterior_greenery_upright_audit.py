"""Exact frozen R9 inputs and independent receipt acceptance/rejection boundaries.

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
spec=importlib.util.spec_from_file_location('fine_greenery_evidence',HERE/'exterior-greenery-upright-audit.py')
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

    def test_frozen_actual_upright_count_budget_and_external_boundary_receipt(self):
        result=audit.upright_lawn_receipts(self.fine_report(),self.plans['lawn'])
        self.assertEqual(result['allInstancesTriangleBudgetByLod'],[18571200,18571200,18571200])
        self.assertEqual(result['boundaryCoverage'],self.plans['lawn']['boundaryCoverageReceipt'])

    def test_missing_or_forged_boundary_pin_is_rejected_even_with_correct_main_cover(self):
        for change in ('missing','wrongHash','unsealed'):
            report=self.fine_report();report['naturalLawn']=deepcopy(report['naturalLawn'])
            if change=='missing':report['naturalLawn'].pop('boundaryCoverageReceipt')
            elif change=='wrongHash':report['naturalLawn']['boundaryCoverageReceipt']['sha256']='0'*64
            else:report['inputFiles'].pop(self.plans['lawn']['boundaryCoverageReceipt']['path'])
            with self.assertRaisesRegex(RuntimeError,'boundaryCoverageReceipt'):audit.upright_lawn_receipts(report,self.plans['lawn'])

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
                with self.assertRaisesRegex(RuntimeError,'only the exact R9a candidate'):call()

    def test_rejected_r8_import_and_package_are_excluded_before_live_reads(self):
        prior=ROOT/'output/unreal/exterior-20260930-r8'
        with patch.object(audit,'read',side_effect=AssertionError('Sealed R8 project must not be read')):
            for call in [lambda:audit.audit_import(prior),lambda:audit.audit_package(prior)]:
                with self.assertRaisesRegex(RuntimeError,'only the exact R9a candidate'):call()

    def test_failed_r9_native_import_cannot_be_relabelled_as_r9a(self):
        prior=ROOT/'output/unreal/exterior-20260930-r9'
        with patch.object(audit,'read',side_effect=AssertionError('Failed R9 source must not be reused')):
            with self.assertRaisesRegex(RuntimeError,'only the exact R9a candidate'):
                audit.audit_import(prior)

    def test_old_fine_owner_and_static_coverage_cannot_pass_upright_policy(self):
        for key,value in [('owner','scripts/unreal/exterior-lawn-fine.py'),('status','PASS_STATIC_FINE_MANAGED_GEOMETRY_NOT_NATIVE_ACCEPTED')]:
            unsafe=deepcopy(self.plans['lawn'])
            if key=='owner':unsafe[key]=value
            else:unsafe['audit'][key]=value
            with self.assertRaisesRegex(RuntimeError,'upright lawn source policy'):
                audit.upright_lawn_receipts(self.fine_report(),unsafe)

    def test_old_r7_suite_and_duplicate_or_missing_views_cannot_be_relabelled_r9(self):
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

    def test_old_r7_material_39_and_texture_70_receipt_is_not_r9(self):
        # This count guard runs before checking current shared pipeline bytes.
        with self.assertRaisesRegex(RuntimeError,'recipe/texture count'):
            audit.audit_materials(R7,audit.read(R7/'exterior-import-report.json'))

    def encoding_fixture(self):
        proof={'path':str(ROOT/'output/unreal'/audit.ENCODING_PROOF[0]),'sha256':audit.ENCODING_PROOF[1]}
        records={'canopy_floor_litter':{'recipe':{'sourceEncodingOverride':'sRGB','sourceEncodingProof':proof}}}
        textures={'floor':{'role':'albedo','sourceSha256':audit.FLOOR_ALBEDO_SHA,'sourceEncodingOverride':'sRGB','sourceEncodingReadback':'TSE_S_RGB'},
                  'normal':{'role':'normal','sourceSha256':'f'*64,'sourceEncodingOverride':'None','sourceEncodingReadback':'TSE_NONE'}}
        return records,textures,{proof['path']:proof['sha256']}

    def test_exact_native_encoding_proof_requires_corrected_floor_only(self):
        records,textures,inputs=self.encoding_fixture()
        result=audit.floor_encoding(records,textures,inputs)
        self.assertEqual(result['correctedFloorAlbedos'],1)
        self.assertTrue(result['otherTextureSourceInterpretationsUnchanged'])
        for change in ('oldFloor','wrongReadback','otherTexture','missingProof','duplicateFloor'):
            records,textures,inputs=self.encoding_fixture()
            if change=='oldFloor':textures['floor']['sourceEncodingOverride']='None'
            elif change=='wrongReadback':textures['floor']['sourceEncodingReadback']='TSE_NONE'
            elif change=='otherTexture':textures['normal']['sourceEncodingOverride']='sRGB'
            elif change=='missingProof':inputs.clear()
            else:textures['duplicate']=deepcopy(textures['floor'])
            with self.assertRaisesRegex(RuntimeError,'Floor source encoding'):
                audit.floor_encoding(records,textures,inputs)

    def test_equal_source_bytes_with_different_encoding_cannot_alias(self):
        recipe={'normalConvention':'OpenGL','sourceEncodingOverride':'sRGB'};spec={'sha256':audit.FLOOR_ALBEDO_SHA}
        corrected=audit.texture_identity('albedo',spec,recipe)
        original=audit.texture_identity('albedo',spec,{**recipe,'sourceEncodingOverride':'None'})
        self.assertEqual(corrected,original+'_srcsrgb')
        with self.assertRaisesRegex(RuntimeError,'Unproven texture source encoding'):
            audit.texture_identity('albedo',{'sha256':'f'*64},recipe)

    def test_missing_canonical_native_helper_cannot_escape_by_omitting_hash(self):
        report={'pipelineFiles':{str(HERE/name):audit.sha(HERE/name)for name in audit.PIPELINE_NAMES}}
        audit.required_pipeline(report)
        for name in ('exterior-import.py','exterior-materials.py','exterior-lawn-native.py','exterior-canopy-native.py'):
            unsafe=deepcopy(report);unsafe['pipelineFiles'].pop(str(HERE/name))
            with self.assertRaisesRegex(RuntimeError,'Canonical native pipeline dependency'):
                audit.required_pipeline(unsafe)

    def test_legacy_saved_transform_hash_matches_pinned_native_inspection(self):
        # Immutable R8 hidden groups are golden schema/state fixtures only;
        # this does not audit or launch its old project against new helpers.
        prior=audit.read(ROOT/'output/unreal/exterior-20260930-r8/exterior-import-report.json')
        hidden={r['legacyLawnGroup']:r for r in prior['naturalLawn']['hiddenOriginalGroups']}
        proof=ROOT/'output/unreal'/audit.LEGACY_INSPECTION[0]
        report={'inputFiles':{str(proof):audit.LEGACY_INSPECTION[1]}}
        result=audit.legacy_inspection_state(report,hidden)
        self.assertEqual(result['orderedSavedNativeTransformsCompared'],40437)
        unsafe=deepcopy(hidden);next(iter(unsafe.values()))['preserved']['orderedInstanceTransformsSha256']='f'*64
        with self.assertRaisesRegex(RuntimeError,'immutable inspection'):
            audit.legacy_inspection_state(report,unsafe)


if __name__=='__main__':unittest.main()
