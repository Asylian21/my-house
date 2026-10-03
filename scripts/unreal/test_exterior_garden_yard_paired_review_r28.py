"""Pure changed-contract fixtures; no images, source replay, Unreal or capture claim."""
import copy
import importlib.util
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

P = Path(__file__).with_name('exterior-garden-yard-paired-review-r28.py')
S = importlib.util.spec_from_file_location('garden_yard_pair_r28', P)
M = importlib.util.module_from_spec(S)
S.loader.exec_module(M)


def request():
    result = {'schema': M.SCHEMA, 'schemaVersion': 1,
              'status': 'actual-closed-captures-and-two-original-image-reviews-bound', 'panels': {}}
    for view in M.VIEWS:
        close = view == M.VIEWS[2]
        result['panels'][view] = {
            'baseline': copy.deepcopy(M.BASELINES[view]),
            'candidate': {'suitePath': str(M.V/'qa/fixture-not-an-actual-capture/editor-pilot-suite.json'),
                          'suiteSha256': 'a'*64, 'originalPngSha256': 'b'*64, 'originalRuntimeSha256': 'c'*64,
                          'source': str(M.CLOSE if close else M.DIRECT), 'processId': 123,
                          'owner': 'scripts/unreal/exterior-editor-qa-r28-close.mjs' if close else 'scripts/unreal/exterior-editor-qa-r28.mjs'},
            'visualReview': {who: {'viewedEveryOriginalInThisPanel': True, 'observations': ['Synthetic fixture observation'],
                                  'limits': ['Synthetic fixture; no actual original image review'], 'boundedVisibleGain': False}
                             for who in ('root', 'independent')}}
    return result


def case():
    pp = {'observedMainViews': 2702, 'viewFamilyFrameNumber': 2702,
          'renderThreadPreExposure': {'exposureEV': 12.0},
          'renderThreadAntiAliasing': {'method': 4, 'observedRenderThreadSamples': 2702,
                                      'projectionJitterX': .01, 'projectionJitterY': .02},
          'fixedSetting': 1.0}
    return {'case': {'sourceCamera': {'id': M.VIEWS[0], 'eyeCm': [1, 2, 3], 'horizontalFovDegrees': 62}},
            'runtime': {'walking': {'presentationCamera': {'locationCm': [1, 2, 3]}},
                        'renderSettings': {'quality': 3}, 'lighting': {'directional': 1},
                        'exteriorLighting': {'sky': 1}, 'finalViewPostProcessSettings': pp}}


class Contract(unittest.TestCase):
    def test_known_request_is_only_schema_validation_not_capture_acceptance(self):
        r = request()
        self.assertIs(M.validate_request(r), r)
        self.assertFalse(Path(r['panels'][M.VIEWS[0]]['candidate']['suitePath']).exists())

    def test_null_actual_capture_is_rejected(self):
        r = request()
        r['panels'][M.VIEWS[0]]['candidate']['processId'] = None
        with self.assertRaisesRegex(RuntimeError, 'Actual closed process identity'):
            M.validate_request(r)

    def test_candidate_overview_cannot_claim_a_pair_gain(self):
        r = request()
        r['panels'][M.VIEWS[1]]['visualReview']['root']['boundedVisibleGain'] = True
        with self.assertRaisesRegex(RuntimeError, 'Candidate-only overview'):
            M.validate_request(r)

    def test_unmatched_historical_comparator_and_missing_peer_reject(self):
        r = request()
        r['panels'][M.VIEWS[1]]['baseline'] = copy.deepcopy(M.BASELINES[M.VIEWS[0]])
        with self.assertRaisesRegex(RuntimeError, 'Fixed known comparator'):
            M.validate_request(r)
        r = request()
        r['panels'][M.VIEWS[2]]['visualReview']['independent']['viewedEveryOriginalInThisPanel'] = False
        with self.assertRaisesRegex(RuntimeError, 'Actual bounded visual review'):
            M.validate_request(r)

    def test_wrong_source_and_unmatched_camera_reject(self):
        r = request()
        r['panels'][M.VIEWS[0]]['candidate']['source'] = str(M.CLOSE)
        with self.assertRaisesRegex(RuntimeError, 'Known actual R37 R28 source'):
            M.validate_request(r)
        a = case()
        b = copy.deepcopy(a)
        b['case']['sourceCamera']['eyeCm'][0] += 1
        with self.assertRaisesRegex(RuntimeError, 'Unmatched camera'):
            M.compare(a, b)

    def test_exposure_and_static_pp_differences_are_not_hidden(self):
        a = case()
        b = copy.deepcopy(a)
        b['runtime']['finalViewPostProcessSettings']['renderThreadPreExposure']['exposureEV'] = 12.1
        b['runtime']['finalViewPostProcessSettings']['fixedSetting'] = .5
        result = M.compare(a, b)
        self.assertAlmostEqual(result['exposure']['deltaEV'], .1)
        self.assertFalse(result['exposure']['fixedExposureComparison'])
        self.assertEqual(result['staticPostProcessSettingDifferences'], [{'path': 'fixedSetting', 'before': 1.0, 'after': .5}])
        self.assertFalse(result['individualMaterialOrGeometryPixelCauseIsolated'])
        self.assertFalse(result['performanceComparisonAccepted'])
        self.assertEqual(len(M.difference(0.0, -0.0)), 1)

    def test_exact_observed_stdout_append_is_not_whole_log_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()/'stdout.log'
            prefix = b'original process fixture\n'
            start = b'Opening shared memory\n'
            end = b'\nDaemon is exiting without errors.\n'
            append = start+b'x'*(855-len(start)-len(end))+end
            path.write_bytes(prefix+append)
            suite = {'path': str(Path(directory).resolve()/'suite.json'), 'sha256': 'a'*64, 'bytes': 4}
            recorded = {'sha256': hashlib.sha256(prefix).hexdigest(), 'bytes': len(prefix)}
            case_row = {'stdoutPath': str(path), 'rawLogHashes': {'stdout': recorded}, 'processId': 123, 'view': M.VIEWS[0]}
            row = {'stdoutPath': str(path), 'suite': suite, 'view': M.VIEWS[0], 'processId': 123,
                   'recordedAtProcessClosure': recorded, 'current': M.pin(path),
                   'append': {'sha256': hashlib.sha256(append).hexdigest(), 'bytes': 855, 'text': append.decode()}}
            proof = M.original_log(case_row, suite, 'stdout', {str(path): row})
            self.assertTrue(proof['recordedPrefixExact'])
            self.assertFalse(proof['wholeLogUnchanged'])
            self.assertEqual(proof['observedLaterAppend']['bytes'], 855)
            altered = bytearray(prefix+append)
            altered[0] ^= 1
            path.write_bytes(altered)
            row['current'] = M.pin(path)  # Even a newly observed full hash cannot excuse a changed original prefix.
            with self.assertRaisesRegex(RuntimeError, 'Recorded stdout prefix'):
                M.original_log(case_row, suite, 'stdout', {str(path): row})

    def test_unobserved_or_other_case_stdout_append_rejects(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory).resolve()/'stdout.log'
            prefix = b'original fixture\n'
            path.write_bytes(prefix+b'later output')
            suite = {'path': str(Path(directory).resolve()/'suite.json'), 'sha256': 'a'*64, 'bytes': 4}
            recorded = {'sha256': hashlib.sha256(prefix).hexdigest(), 'bytes': len(prefix)}
            case_row = {'stdoutPath': str(path), 'rawLogHashes': {'stdout': recorded}, 'processId': 123, 'view': M.VIEWS[0]}
            with self.assertRaisesRegex(RuntimeError, 'Unexpected original runtime log change'):
                M.original_log(case_row, suite, 'stdout', {})
            other = {'stdoutPath': str(path), 'suite': suite, 'processId': 124, 'view': M.VIEWS[0],
                     'recordedAtProcessClosure': recorded, 'current': M.pin(path)}
            with self.assertRaisesRegex(RuntimeError, 'Exactly pinned same-case'):
                M.original_log(case_row, suite, 'stdout', {str(path): other})

    def test_root_review_binds_all_three_actual_capture_identities_without_promotion(self):
        observed = {'path': str(M.ROOT_REVIEW), 'sha256': M.ROOT_REVIEW_SHA, 'bytes': 123}
        panels = []
        captures = []
        for i, view in enumerate(M.VIEWS):
            after = {key: {'path': key+str(i), 'sha256': str(i)*64, 'bytes': 1}
                     for key in ('suite', 'process', 'originalPng', 'originalRuntime')}
            after['case'] = {'processId': 100+i}
            panels.append({'candidate': after})
            captures.append({**{key: after[key] for key in ('suite', 'process', 'originalPng', 'originalRuntime')},
                             'view': view, 'nativePid': 100+i, 'rootSessionClosedExitCode': 0,
                             'originalWholePngViewedByRoot': True})
        row = {'schema': 'brezi-root-r37-actual-image-base-selection-for-r38-only',
               'status': 'selected-saved-r37b-only-as-next-scoped-ground-pilot-base', 'selectedNativeBase': str(M.DIRECT),
               'selectedNativeReport': {'sha256': M.NATIVE_SHA}, 'selectedCurrentByteAudit': {'sha256': M.AUDIT_SHA},
               'selectedNativeProcessId': 54956, 'actualCameraCaptures': captures,
               **{key: False for key in ('fullPhotorealismAccepted', 'nativeAppearanceAccepted', 'performanceAccepted',
                                          'shippingVerified', 'packageVerified', 'activeOutputPromoted', 'photoPixelsEdited')}}
        with patch.object(M, 'fixed', return_value=observed), patch.object(M, 'read', return_value=row):
            self.assertEqual(M.root_review({'rootOriginalImageReviewReceipt': observed}, panels), observed)
            captures[1]['originalPng']['bytes'] += 1
            # Avoid shared synthetic dictionaries accidentally mutating both witness and expected panel.
            panels[1]['candidate']['originalPng'] = dict(captures[1]['originalPng'], bytes=1)
            with self.assertRaisesRegex(RuntimeError, 'Root capture/PID'):
                M.root_review({'rootOriginalImageReviewReceipt': observed}, panels)
            captures[1]['originalPng']['bytes'] = 1
            row['activeOutputPromoted'] = True
            with self.assertRaisesRegex(RuntimeError, 'cannot promote global acceptance'):
                M.root_review({'rootOriginalImageReviewReceipt': observed}, panels)


if __name__ == '__main__':
    unittest.main()
